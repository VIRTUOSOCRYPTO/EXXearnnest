import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Calendar, Clock, CheckCircle, XCircle, AlertCircle, 
  Trophy, Award, Users, ExternalLink, User
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MyRegistrations = () => {
  const { user } = useAuth();
  const [registrations, setRegistrations] = useState({
    college_events: [],
    prize_challenges: [],
    inter_college_competitions: []
  });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    fetchMyRegistrations();
  }, []);

  const fetchMyRegistrations = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/my-registrations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setRegistrations({
        college_events: response.data.college_events || [],
        prize_challenges: response.data.prize_challenges || [],
        inter_college_competitions: response.data.inter_college_competitions || []
      });
    } catch (error) {
      console.error('Error fetching registrations:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { 
        color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
        icon: Clock,
        label: 'Pending Review'
      },
      approved: { 
        color: 'bg-green-100 text-green-800 border-green-300',
        icon: CheckCircle,
        label: 'Approved'
      },
      rejected: { 
        color: 'bg-red-100 text-red-800 border-red-300',
        icon: XCircle,
        label: 'Rejected'
      },
      active: { 
        color: 'bg-blue-100 text-blue-800 border-blue-300',
        icon: CheckCircle,
        label: 'Active'
      }
    };

    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <Badge className={`${config.color} border`}>
        <Icon className="w-3 h-3 mr-1" />
        {config.label}
      </Badge>
    );
  };

  const getEventTypeIcon = (type) => {
    const icons = {
      college_events: Calendar,
      prize_challenges: Award,
      inter_college_competitions: Trophy
    };
    return icons[type] || Calendar;
  };

  const getRegistrationTypeIcon = (regType) => {
    return regType === 'group' ? Users : User;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const renderRegistrationCard = (registration, eventType) => {
    const eventDetails = registration.event_details || registration.challenge_details || registration.competition_details || {};
    const EventIcon = getEventTypeIcon(eventType);
    const RegTypeIcon = getRegistrationTypeIcon(registration.registration_type);

    return (
      <Card key={registration.id} className="mb-4 hover:shadow-lg transition-shadow">
        <CardContent className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <EventIcon className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-semibold">{eventDetails.title || 'Event'}</h3>
                <div className="flex items-center gap-1">
                  <RegTypeIcon className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-600 capitalize">{registration.registration_type}</span>
                </div>
              </div>
              
              {eventDetails.description && (
                <p className="text-gray-600 text-sm mb-3 line-clamp-2">{eventDetails.description}</p>
              )}
              
              <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>Registered: {formatDate(registration.registration_date)}</span>
                </div>
                
                {eventDetails.start_date && (
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>Event Date: {formatDate(eventDetails.start_date)}</span>
                  </div>
                )}
                
                {eventType === 'prize_challenges' && eventDetails.total_prize_value && (
                  <div className="flex items-center gap-1">
                    <Award className="w-4 h-4" />
                    <span>Prize: ₹{eventDetails.total_prize_value.toLocaleString()}</span>
                  </div>
                )}
                
                {eventType === 'inter_college_competitions' && eventDetails.eligible_universities && (
                  <div className="flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    <span>{eventDetails.eligible_universities.length} Universities</span>
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex flex-col items-end gap-2">
              {getStatusBadge(registration.status)}
              
              {eventDetails.id && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const routes = {
                      college_events: `/events/${eventDetails.id}`,
                      prize_challenges: `/prize-challenges/${eventDetails.id}`,
                      inter_college_competitions: `/inter-college-competitions/${eventDetails.id}`
                    };
                    window.location.href = routes[eventType] || '#';
                  }}
                >
                  <ExternalLink className="w-3 h-3 mr-1" />
                  View Event
                </Button>
              )}
            </div>
          </div>

          {/* Registration Details */}
          <div className="border-t pt-4 mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              {registration.registration_type === 'group' ? (
                <>
                  <div>
                    <span className="font-medium">Team Name:</span>
                    <span className="ml-2">{registration.team_name}</span>
                  </div>
                  <div>
                    <span className="font-medium">Team Leader:</span>
                    <span className="ml-2">{registration.team_leader_name}</span>
                  </div>
                  <div>
                    <span className="font-medium">Team Size:</span>
                    <span className="ml-2">{registration.team_size} members</span>
                  </div>
                  <div>
                    <span className="font-medium">College:</span>
                    <span className="ml-2">{registration.college || registration.user_college}</span>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <span className="font-medium">Name:</span>
                    <span className="ml-2">{registration.full_name || registration.user_name}</span>
                  </div>
                  <div>
                    <span className="font-medium">USN:</span>
                    <span className="ml-2">{registration.usn}</span>
                  </div>
                  <div>
                    <span className="font-medium">College:</span>
                    <span className="ml-2">{registration.college || registration.user_college}</span>
                  </div>
                  <div>
                    <span className="font-medium">Branch:</span>
                    <span className="ml-2">{registration.branch} - {registration.semester} Semester</span>
                  </div>
                </>
              )}
            </div>

            {registration.rejection_reason && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 text-red-800">
                  <AlertCircle className="w-4 h-4" />
                  <span className="font-medium">Rejection Reason:</span>
                </div>
                <p className="text-red-700 text-sm mt-1">{registration.rejection_reason}</p>
              </div>
            )}

            {registration.approved_at && registration.status === 'approved' && (
              <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 text-green-800">
                  <CheckCircle className="w-4 h-4" />
                  <span className="font-medium">Approved on {formatDate(registration.approved_at)}</span>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  const getAllRegistrations = () => {
    return [
      ...registrations.college_events.map(reg => ({ ...reg, eventType: 'college_events' })),
      ...registrations.prize_challenges.map(reg => ({ ...reg, eventType: 'prize_challenges' })),
      ...registrations.inter_college_competitions.map(reg => ({ ...reg, eventType: 'inter_college_competitions' }))
    ].sort((a, b) => new Date(b.registration_date) - new Date(a.registration_date));
  };

  const getTabStats = (type) => {
    if (type === 'all') {
      const all = getAllRegistrations();
      return {
        total: all.length,
        pending: all.filter(r => r.status === 'pending').length,
        approved: all.filter(r => r.status === 'approved').length
      };
    }
    
    const regs = registrations[type] || [];
    return {
      total: regs.length,
      pending: regs.filter(r => r.status === 'pending').length,
      approved: regs.filter(r => r.status === 'approved').length
    };
  };

  if (loading) {
    return (
      <Card className="w-full max-w-6xl mx-auto">
        <CardContent className="p-8">
          <div className="flex items-center justify-center space-x-4">
            <Clock className="w-6 h-6 animate-spin" />
            <span className="text-gray-600">Loading your registrations...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <User className="w-6 h-6" />
            <div>
              <h1 className="text-2xl font-bold">My Registrations</h1>
              <p className="text-gray-600 text-sm">View and track all your event registrations</p>
            </div>
          </CardTitle>
        </CardHeader>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{getAllRegistrations().length}</div>
            <div className="text-sm text-gray-600">Total Registrations</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-yellow-600">
              {getAllRegistrations().filter(r => r.status === 'pending').length}
            </div>
            <div className="text-sm text-gray-600">Pending Review</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">
              {getAllRegistrations().filter(r => r.status === 'approved').length}
            </div>
            <div className="text-sm text-gray-600">Approved</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-red-600">
              {getAllRegistrations().filter(r => r.status === 'rejected').length}
            </div>
            <div className="text-sm text-gray-600">Rejected</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Card>
        <CardContent className="p-0">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="all" className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                All ({getTabStats('all').total})
              </TabsTrigger>
              <TabsTrigger value="college_events" className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                Events ({getTabStats('college_events').total})
              </TabsTrigger>
              <TabsTrigger value="prize_challenges" className="flex items-center gap-2">
                <Award className="w-4 h-4" />
                Challenges ({getTabStats('prize_challenges').total})
              </TabsTrigger>
              <TabsTrigger value="inter_college_competitions" className="flex items-center gap-2">
                <Trophy className="w-4 h-4" />
                Competitions ({getTabStats('inter_college_competitions').total})
              </TabsTrigger>
            </TabsList>

            <div className="p-6">
              <TabsContent value="all">
                {getAllRegistrations().length > 0 ? (
                  getAllRegistrations().map(registration => 
                    renderRegistrationCard(registration, registration.eventType)
                  )
                ) : (
                  <div className="text-center py-12">
                    <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-600">No registrations yet</h3>
                    <p className="text-gray-500">Start by registering for events, challenges, or competitions!</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="college_events">
                {registrations.college_events.length > 0 ? (
                  registrations.college_events.map(registration => 
                    renderRegistrationCard(registration, 'college_events')
                  )
                ) : (
                  <div className="text-center py-12">
                    <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-600">No college events registered</h3>
                    <p className="text-gray-500">Explore upcoming college events and register now!</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="prize_challenges">
                {registrations.prize_challenges.length > 0 ? (
                  registrations.prize_challenges.map(registration => 
                    renderRegistrationCard(registration, 'prize_challenges')
                  )
                ) : (
                  <div className="text-center py-12">
                    <Award className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-600">No prize challenges registered</h3>
                    <p className="text-gray-500">Join exciting prize challenges and compete for rewards!</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="inter_college_competitions">
                {registrations.inter_college_competitions.length > 0 ? (
                  registrations.inter_college_competitions.map(registration => 
                    renderRegistrationCard(registration, 'inter_college_competitions')
                  )
                ) : (
                  <div className="text-center py-12">
                    <Trophy className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-600">No competitions registered</h3>
                    <p className="text-gray-500">Register for inter-college competitions and represent your college!</p>
                  </div>
                )}
              </TabsContent>
            </div>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default MyRegistrations;
