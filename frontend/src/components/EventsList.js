import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import EventOverviewModal from './EventOverviewModal';
import { 
  CalendarDays, 
  MapPin, 
  Users, 
  Award, 
  Tag, 
  Clock, 
  Globe, 
  Building,
  Video,
  Plus,
  Filter,
  Search
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const EventsList = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [eventOverviewOpen, setEventOverviewOpen] = useState(false);
  const [filters, setFilters] = useState({
    event_type: '',
    status: '',
    club: '',
    visibility: '',
    search: ''
  });

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

  const eventTypes = [
    { value: 'hackathon', label: 'Hackathon' },
    { value: 'workshop', label: 'Workshop' },
    { value: 'coding_competition', label: 'Coding Competition' },
    { value: 'tech_talk', label: 'Tech Talk' },
    { value: 'seminar', label: 'Seminar' },
    { value: 'conference', label: 'Conference' },
    { value: 'club_meeting', label: 'Club Meeting' },
    { value: 'project_showcase', label: 'Project Showcase' }
  ];

  const statusOptions = [
    { value: 'upcoming', label: 'Upcoming' },
    { value: 'ongoing', label: 'Ongoing' },
    { value: 'past', label: 'Past' },
    { value: 'registration_open', label: 'Registration Open' }
  ];

  useEffect(() => {
    fetchEvents();
  }, [filters]);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      
      // Build query parameters
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      const response = await axios.get(`${API}/college-events?${params}`);
      setEvents(response.data.events || []);
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEventStatusBadge = (event) => {
    const now = new Date();
    const startDate = new Date(event.start_date);
    const endDate = new Date(event.end_date);
    const regDeadline = event.registration_deadline ? new Date(event.registration_deadline) : null;
    
    // Check manual admin override first, default to true if not set
    // Using registration_required field (backend model field name)
    const registrationEnabled = event.registration_required !== undefined ? event.registration_required : true;

    if (now < startDate) {
      // Check if manually disabled by admin
      if (!registrationEnabled) {
        return <Badge variant="secondary">Registration Closed</Badge>;
      }
      // Check date-based registration status
      if (regDeadline && now <= regDeadline) {
        return <Badge className="bg-green-500">Registration Open</Badge>;
      } else if (regDeadline && now > regDeadline) {
        return <Badge variant="secondary">Registration Closed</Badge>;
      } else {
        // No deadline set, registration is open until event starts
        return <Badge className="bg-green-500">Registration Open</Badge>;
      }
    } else if (now >= startDate && now <= endDate) {
      return <Badge className="bg-orange-500">Ongoing</Badge>;
    } else {
      return <Badge variant="outline" className="bg-gray-100">Past Event</Badge>;
    }
  };

  const getTimeRemaining = (targetDate) => {
    const now = new Date();
    const target = new Date(targetDate);
    const diff = target - now;
    
    if (diff <= 0) return "Started/Ended";
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    
    if (days > 0) return `${days} days ${hours}h remaining`;
    return `${hours}h remaining`;
  };

  const filteredEvents = events.filter(event => {
    switch (activeTab) {
      case "registered":
        return event.is_registered;
      case "my_college":
        return event.visibility === 'college_only' || 
               (event.visibility === 'selected_colleges' && event.selected_colleges?.includes(user?.university));
      case "upcoming":
        return new Date(event.start_date) > new Date();
      case "ongoing":
        const now = new Date();
        return new Date(event.start_date) <= now && new Date(event.end_date) >= now;
      default:
        return true;
    }
  });

  const EventCard = ({ event }) => (
    <Card className="hover:shadow-lg transition-shadow duration-200 border-l-4 border-l-green-500">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">{eventTypeIcons[event.event_type] || '📅'}</span>
              <CardTitle className="text-lg sm:text-xl font-bold text-gray-800 break-words leading-relaxed">
                {event.title}
              </CardTitle>
            </div>
            <p className="text-gray-600 text-sm mb-3 break-words leading-relaxed">{event.description}</p>
            <div className="flex flex-wrap gap-2">
              {getEventStatusBadge(event)}
              {event.is_registered && (
                <Badge className="bg-emerald-500">
                  <Users className="w-3 h-3 mr-1" />
                  Registered
                </Badge>
              )}
              <Badge variant="outline" className="bg-blue-50">
                {eventTypes.find(type => type.value === event.event_type)?.label}
              </Badge>
              {event.visibility === 'all_colleges' && (
                <Badge variant="outline" className="bg-purple-50">
                  <Globe className="w-3 h-3 mr-1" />
                  All Colleges
                </Badge>
              )}
            </div>
          </div>
          
          {event.prizes?.first_prize > 0 && (
            <div className="text-left sm:text-right flex-shrink-0">
              <div className="text-xl sm:text-2xl font-bold text-green-600 break-words">
                ₹{(event.prizes.first_prize || 0).toLocaleString()}
              </div>
              <div className="text-sm text-gray-500 whitespace-nowrap">First Prize</div>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <CalendarDays className="w-5 h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-sm font-medium mb-1">Start Date</div>
            <div className="text-xs text-gray-600 break-words leading-tight">
              {new Date(event.start_date).toLocaleDateString()}
            </div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <Clock className="w-5 h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-sm font-medium mb-1">Duration</div>
            <div className="text-xs text-gray-600 break-words leading-tight">
              {Math.ceil((new Date(event.end_date) - new Date(event.start_date)) / (1000 * 60 * 60 * 24))} days
            </div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <Users className="w-5 h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-sm font-medium mb-1">Registered</div>
            <div className="text-xs text-gray-600 break-words leading-tight">
              {event.registered_count || 0}
              {event.max_participants && `/${event.max_participants}`}
            </div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            {event.is_virtual ? (
              <>
                <Video className="w-5 h-5 mx-auto mb-1 text-gray-600" />
                <div className="text-sm font-medium mb-1">Virtual</div>
                <div className="text-xs text-gray-600 break-words leading-tight">Online Event</div>
              </>
            ) : (
              <>
                <MapPin className="w-5 h-5 mx-auto mb-1 text-gray-600" />
                <div className="text-sm font-medium mb-1">Venue</div>
                <div className="text-xs text-gray-600 break-words leading-tight">
                  {event.venue || 'TBD'}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Event Details */}
        <div className="space-y-2 mb-4">
          {event.organizer_name && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Organizer:</span>
              <span className="font-medium">{event.organizer_name}</span>
            </div>
          )}
          {event.club_name && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Club:</span>
              <span className="font-medium">{event.club_name}</span>
            </div>
          )}
          {event.registration_deadline && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Registration Ends:</span>
              <span className="font-medium">
                {new Date(event.registration_deadline).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>

        {/* Tags */}
        {event.tags && event.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-4">
            {event.tags.slice(0, 3).map((tag, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                <Tag className="w-3 h-3 mr-1" />
                {tag}
              </Badge>
            ))}
            {event.tags.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{event.tags.length - 3} more
              </Badge>
            )}
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            className="w-full"
            onClick={() => {
              setSelectedEvent(event);
              setEventOverviewOpen(true);
            }}
          >
            View Details
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading events...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <CalendarDays className="w-8 h-8 text-green-600" />
            <h1 className="text-3xl font-bold text-gray-800">College Events</h1>
          </div>
          {/* Check if user can create events (admin level) */}
          {user && (user.is_admin || user.is_super_admin || user.admin_level !== 'user') && (
            <Button
              onClick={() => navigate('/events/create')}
              className="bg-green-600 hover:bg-green-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Event
            </Button>
          )}
        </div>
        <p className="text-gray-600 text-lg">
          Discover and participate in exciting events across colleges and universities
        </p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Filter className="w-5 h-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Search</label>
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  className="pl-10 w-full p-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  placeholder="Search events..."
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Event Type</label>
              <select
                value={filters.event_type}
                onChange={(e) => setFilters(prev => ({ ...prev, event_type: e.target.value }))}
                className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              >
                <option value="">All Types</option>
                {eventTypes.map((type) => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Status</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              >
                <option value="">All Status</option>
                {statusOptions.map((status) => (
                  <option key={status.value} value={status.value}>{status.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Visibility</label>
              <select
                value={filters.visibility}
                onChange={(e) => setFilters(prev => ({ ...prev, visibility: e.target.value }))}
                className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              >
                <option value="">All Events</option>
                <option value="college_only">My College Only</option>
                <option value="all_colleges">All Colleges</option>
                <option value="selected_colleges">Selected Colleges</option>
              </select>
            </div>

            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => setFilters({ event_type: '', status: '', club: '', visibility: '', search: '' })}
                className="w-full"
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="all">All Events</TabsTrigger>
          <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
          <TabsTrigger value="ongoing">Ongoing</TabsTrigger>
          <TabsTrigger value="my_college">My College</TabsTrigger>
          <TabsTrigger value="registered">Registered</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4 mt-6">
          {filteredEvents.length === 0 ? (
            <div className="text-center py-12">
              <CalendarDays className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No events found</h3>
              <p className="text-gray-500">Check back later for new events or adjust your filters!</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredEvents.map((event) => (
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
              <p className="text-gray-500">Stay tuned for upcoming events!</p>
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
              <p className="text-gray-500">Check out upcoming events to participate!</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredEvents.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="my_college" className="space-y-4 mt-6">
          {filteredEvents.length === 0 ? (
            <div className="text-center py-12">
              <Building className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No college events</h3>
              <p className="text-gray-500">No events from your college or selected colleges!</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredEvents.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="registered" className="space-y-4 mt-6">
          {filteredEvents.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No registered events</h3>
              <p className="text-gray-500">Register for events to track them here!</p>
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
      
      {/* Event Overview Modal */}
      <EventOverviewModal
        open={eventOverviewOpen}
        onClose={() => {
          setEventOverviewOpen(false);
          setSelectedEvent(null);
        }}
        event={selectedEvent}
      />
    </div>
  );
};

export default EventsList;
