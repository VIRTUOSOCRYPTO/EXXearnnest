import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  CalendarDays, 
  MapPin, 
  Users, 
  Award, 
  Clock, 
  Globe, 
  Building,
  Video,
  Plus,
  Edit,
  Trash2,
  Eye,
  BarChart3
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MyEvents = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [activeTab, setActiveTab] = useState("all");

  const eventTypeIcons = {
    hackathon: '💻',
    workshop: '🛠️',
    coding_competition: '🏆',
    tech_talk: '🎙️',
    seminar: '📚',
    conference: '🎯',
    club_meeting: '👥',
    project_showcase: '📽️'
  };

  useEffect(() => {
    fetchMyEvents();
  }, []);

  const fetchMyEvents = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/my-events`);
      setEvents(response.data.events || []);
    } catch (error) {
      console.error('Error fetching my events:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteEvent = async (eventId) => {
    if (!window.confirm('Are you sure you want to delete this event? This action cannot be undone.')) {
      return;
    }

    try {
      setDeleting(true);
      await axios.delete(`${API}/college-events/${eventId}`);
      
      // Remove the event from local state
      setEvents(prev => prev.filter(event => event.id !== eventId));
      
      alert('Event deleted successfully!');
    } catch (error) {
      console.error('Delete error:', error);
      alert(error.response?.data?.detail || 'Failed to delete event');
    } finally {
      setDeleting(false);
    }
  };

  const getEventStatusBadge = (event) => {
    const now = new Date();
    const startDate = new Date(event.start_date);
    const endDate = new Date(event.end_date);
    const regDeadline = event.registration_deadline ? new Date(event.registration_deadline) : null;

    if (now < startDate) {
      if (regDeadline && now <= regDeadline) {
        return <Badge className="bg-green-500">Registration Open</Badge>;
      } else if (regDeadline && now > regDeadline) {
        return <Badge variant="secondary">Registration Closed</Badge>;
      } else {
        return <Badge variant="outline" className="bg-blue-100">Upcoming</Badge>;
      }
    } else if (now >= startDate && now <= endDate) {
      return <Badge className="bg-orange-500">Ongoing</Badge>;
    } else {
      return <Badge variant="outline" className="bg-gray-100">Past Event</Badge>;
    }
  };

  const filteredEvents = events.filter(event => {
    const now = new Date();
    const startDate = new Date(event.start_date);
    const endDate = new Date(event.end_date);

    switch (activeTab) {
      case "upcoming":
        return startDate > now;
      case "ongoing":
        return startDate <= now && endDate >= now;
      case "past":
        return endDate < now;
      default:
        return true;
    }
  });

  const EventCard = ({ event }) => (
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">{eventTypeIcons[event.event_type] || '📅'}</span>
              <CardTitle className="text-lg font-bold text-gray-800 break-words">
                {event.title}
              </CardTitle>
            </div>
            <p className="text-gray-600 text-sm mb-3 line-clamp-2">{event.description}</p>
            <div className="flex flex-wrap gap-2">
              {getEventStatusBadge(event)}
              {event.visibility === 'all_colleges' && (
                <Badge variant="outline" className="bg-purple-50">
                  <Globe className="w-3 h-3 mr-1" />
                  All Colleges
                </Badge>
              )}
              {event.is_virtual && (
                <Badge variant="outline" className="bg-blue-50">
                  <Video className="w-3 h-3 mr-1" />
                  Virtual
                </Badge>
              )}
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/events/${event.id}`)}
              title="View Details"
            >
              <Eye className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/events/${event.id}/edit`)}
              title="Edit Event"
            >
              <Edit className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => deleteEvent(event.id)}
              disabled={deleting}
              className="border-red-200 text-red-600 hover:bg-red-50"
              title="Delete Event"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div className="text-center p-2 bg-gray-50 rounded-lg">
            <CalendarDays className="w-4 h-4 mx-auto mb-1 text-gray-600" />
            <div className="text-xs font-medium mb-1">Start Date</div>
            <div className="text-xs text-gray-600">
              {new Date(event.start_date).toLocaleDateString()}
            </div>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded-lg">
            <Clock className="w-4 h-4 mx-auto mb-1 text-gray-600" />
            <div className="text-xs font-medium mb-1">Duration</div>
            <div className="text-xs text-gray-600">
              {Math.ceil((new Date(event.end_date) - new Date(event.start_date)) / (1000 * 60 * 60 * 24))} days
            </div>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded-lg">
            <Users className="w-4 h-4 mx-auto mb-1 text-gray-600" />
            <div className="text-xs font-medium mb-1">Registered</div>
            <div className="text-xs text-gray-600">
              {event.registered_count || 0}
              {event.max_participants && `/${event.max_participants}`}
            </div>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded-lg">
            {event.prizes?.first_prize > 0 ? (
              <>
                <Award className="w-4 h-4 mx-auto mb-1 text-gray-600" />
                <div className="text-xs font-medium mb-1">Prize</div>
                <div className="text-xs text-gray-600">
                  ₹{event.prizes.first_prize.toLocaleString()}
                </div>
              </>
            ) : (
              <>
                <BarChart3 className="w-4 h-4 mx-auto mb-1 text-gray-600" />
                <div className="text-xs font-medium mb-1">Type</div>
                <div className="text-xs text-gray-600 capitalize">
                  {event.event_type.replace('_', ' ')}
                </div>
              </>
            )}
          </div>
        </div>

        <div className="space-y-1 mb-3">
          {event.organizer_name && (
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Organizer:</span>
              <span className="font-medium">{event.organizer_name}</span>
            </div>
          )}
          {event.club_name && (
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Club:</span>
              <span className="font-medium">{event.club_name}</span>
            </div>
          )}
          {event.registration_deadline && (
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Registration Ends:</span>
              <span className="font-medium">
                {new Date(event.registration_deadline).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            className="flex-1 text-sm"
            onClick={() => navigate(`/events/${event.id}`)}
          >
            <Eye className="w-3 h-3 mr-1" />
            View Details
          </Button>
          <Button
            className="flex-1 text-sm bg-green-600 hover:bg-green-700"
            onClick={() => navigate(`/events/${event.id}/edit`)}
          >
            <Edit className="w-3 h-3 mr-1" />
            Edit Event
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  // Check if user has admin privileges to create events
  const canCreateEvents = user && (user.is_admin || user.is_super_admin || user.admin_level !== 'user');

  if (!canCreateEvents) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center py-12">
          <CalendarDays className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-600 mb-2">Access Restricted</h3>
          <p className="text-gray-500 mb-4">You need admin privileges to create and manage events.</p>
          <Button onClick={() => navigate('/events')}>
            View All Events
          </Button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your events...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <CalendarDays className="w-8 h-8 text-green-600" />
            <h1 className="text-3xl font-bold text-gray-800">My Events</h1>
          </div>
          <Button
            onClick={() => navigate('/events/create')}
            className="bg-green-600 hover:bg-green-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create New Event
          </Button>
        </div>
        <p className="text-gray-600 text-lg">
          Manage all the events you've created and organized
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{events.length}</div>
            <div className="text-sm text-gray-500">Total Events</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">
              {filteredEvents.filter(e => new Date(e.start_date) > new Date()).length}
            </div>
            <div className="text-sm text-gray-500">Upcoming Events</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-orange-600">
              {filteredEvents.filter(e => {
                const now = new Date();
                return new Date(e.start_date) <= now && new Date(e.end_date) >= now;
              }).length}
            </div>
            <div className="text-sm text-gray-500">Ongoing Events</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">
              {events.reduce((sum, event) => sum + (event.registered_count || 0), 0)}
            </div>
            <div className="text-sm text-gray-500">Total Registrations</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="all">All Events</TabsTrigger>
          <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
          <TabsTrigger value="ongoing">Ongoing</TabsTrigger>
          <TabsTrigger value="past">Past</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4 mt-6">
          {events.length === 0 ? (
            <div className="text-center py-12">
              <CalendarDays className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No events created</h3>
              <p className="text-gray-500 mb-4">Start organizing events for your college community!</p>
              <Button
                onClick={() => navigate('/events/create')}
                className="bg-green-600 hover:bg-green-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Event
              </Button>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {events.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="upcoming" className="space-y-4 mt-6">
          {filteredEvents.length === 0 ? (
            <div className="text-center py-12">
              <Clock className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No upcoming events</h3>
              <p className="text-gray-500">Create new events to engage your community!</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredEvents.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="ongoing" className="space-y-4 mt-6">
          {filteredEvents.length === 0 ? (
            <div className="text-center py-12">
              <Award className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No ongoing events</h3>
              <p className="text-gray-500">Your active events will appear here.</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredEvents.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="past" className="space-y-4 mt-6">
          {filteredEvents.length === 0 ? (
            <div className="text-center py-12">
              <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No past events</h3>
              <p className="text-gray-500">Your completed events will appear here for reference.</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredEvents.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MyEvents;
