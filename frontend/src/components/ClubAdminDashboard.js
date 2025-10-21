import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import RegistrationManagement from './RegistrationManagement';
import { 
  Trophy, Users, Calendar, Award, Target, Shield, 
  AlertCircle, CheckCircle, Clock, Activity, TrendingUp,
  FileText, Building, Settings
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ClubAdminDashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [competitions, setCompetitions] = useState([]);
  const [challenges, setChallenges] = useState([]);
  const [collegeEvents, setCollegeEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedEvent, setSelectedEvent] = useState({ id: null, type: null, title: null });
  const [collegeRegistrations, setCollegeRegistrations] = useState({});

  useEffect(() => {
    fetchDashboardData();
    fetchCompetitions();
    fetchChallenges();
    fetchCollegeEvents();
    
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchDashboardData();
      fetchCompetitions();
      fetchChallenges();
      fetchCollegeEvents();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeTab === 'registrations' && !selectedEvent.id) {
      // Auto-select first available event when switching to registrations tab
      if (collegeEvents.length > 0) {
        const firstEvent = collegeEvents[0];
        setSelectedEvent({
          id: firstEvent.id,
          type: 'college_event',
          title: firstEvent.title
        });
      } else if (competitions.length > 0) {
        const firstCompetition = competitions[0];
        setSelectedEvent({
          id: firstCompetition.id,
          type: 'inter_college',
          title: firstCompetition.title
        });
      } else if (challenges.length > 0) {
        const firstChallenge = challenges[0];
        setSelectedEvent({
          id: firstChallenge.id,
          type: 'prize_challenge',
          title: firstChallenge.title
        });
      }
    }
  }, [activeTab, collegeEvents, competitions, challenges]);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/club-admin/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      if (error.response?.status === 403) {
        alert('You do not have club admin privileges. Please contact your campus admin for access.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchCompetitions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/club-admin/competitions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setCompetitions(response.data.competitions || []);
    } catch (error) {
      console.error('Error fetching competitions:', error);
    }
  };

  const fetchChallenges = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/club-admin/challenges`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setChallenges(response.data.challenges || []);
    } catch (error) {
      console.error('Error fetching challenges:', error);
    }
  };

  const fetchCollegeEvents = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/club-admin/college-events`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setCollegeEvents(response.data.events || []);
    } catch (error) {
      console.error('Error fetching college events:', error);
    }
  };

  if (loading) {
    return (
      <Card className="w-full max-w-6xl mx-auto">
        <CardContent className="p-8">
          <div className="flex items-center justify-center space-x-4">
            <Clock className="w-6 h-6 animate-spin" />
            <span className="text-gray-600">Loading dashboard...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className="w-full max-w-6xl mx-auto">
        <CardContent className="p-8">
          <div className="flex items-center justify-center space-x-4">
            <Clock className="w-6 h-6 animate-spin" />
            <span className="text-gray-600">Loading club admin dashboard...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!dashboardData) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-8 text-center">
          <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-800 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-4">
            You do not have club admin privileges. Please contact your campus admin for access.
          </p>
        </CardContent>
      </Card>
    );
  }

  const { admin_details, statistics, capabilities } = dashboardData;

  const getEventOptions = () => {
    const options = [];
    
    // Add college events first
    collegeEvents.forEach(event => {
      options.push({
        id: event.id,
        type: 'college_event',
        title: event.title,
        label: `College Event: ${event.title}`
      });
    });
    
    // Add competitions
    competitions.forEach(comp => {
      options.push({
        id: comp.id,
        type: 'inter_college',
        title: comp.title,
        label: `Competition: ${comp.title}`
      });
    });
    
    // Add challenges
    challenges.forEach(challenge => {
      options.push({
        id: challenge.id,
        type: 'prize_challenge',
        title: challenge.title,
        label: `Challenge: ${challenge.title}`
      });
    });
    
    return options;
  };

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Club Admin Dashboard</h1>
            <p className="text-purple-100">
              {admin_details.club_name} - {admin_details.college_name}
            </p>
          </div>
          <Shield className="w-16 h-16 opacity-50" />
        </div>
      </div>

      {/* Main Tabs */}
      <Card>
        <CardContent className="p-0">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="registrations" className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Registrations
              </TabsTrigger>
              <TabsTrigger value="colleges" className="flex items-center gap-2">
                <Building className="w-4 h-4" />
                Colleges
              </TabsTrigger>
              <TabsTrigger value="settings" className="flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Settings
              </TabsTrigger>
            </TabsList>

            <div className="p-6">
              <TabsContent value="overview" className="space-y-6 mt-0">

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Events
            </CardTitle>
            <Trophy className="w-5 h-5 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {statistics.total_events}
            </div>
            <p className="text-xs text-gray-500 mt-1">Competitions + Challenges</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Competitions
            </CardTitle>
            <Calendar className="w-5 h-5 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {statistics.total_competitions}
            </div>
            <p className="text-xs text-gray-500 mt-1">Inter-college events</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Challenges
            </CardTitle>
            <Award className="w-5 h-5 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {statistics.total_challenges}
            </div>
            <p className="text-xs text-gray-500 mt-1">Prize challenges</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Participants
            </CardTitle>
            <Users className="w-5 h-5 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {statistics.participants_managed}
            </div>
            <p className="text-xs text-gray-500 mt-1">Total managed</p>
          </CardContent>
        </Card>
                </div>

                {/* Monthly Quota Progress */}
                <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Target className="w-5 h-5 mr-2" />
            Monthly Event Creation Quota
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">
                Used: {statistics.events_this_month} / {capabilities.max_events_per_month}
              </span>
              <span className="text-sm text-gray-600">
                {statistics.remaining_monthly_quota} remaining
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-purple-600 h-2 rounded-full"
                style={{ width: `${(statistics.events_this_month / capabilities.max_events_per_month) * 100}%` }}
              />
            </div>
          </div>
        </CardContent>
                </Card>

                {/* Quick Actions */}
                <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Quick Actions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button 
            className="bg-blue-600 hover:bg-blue-700 w-full"
            onClick={() => window.location.href = '/create-college-event'}
          >
            <Calendar className="w-4 h-4 mr-2" />
            Create My College Event
          </Button>
          {statistics.remaining_monthly_quota === 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mt-4">
              <p className="text-sm text-yellow-800">
                <AlertCircle className="w-4 h-4 inline mr-2" />
                You've reached your monthly event creation limit. Limit resets next month.
              </p>
            </div>
          )}
        </CardContent>
                </Card>

                {/* Recent Competitions */}
                {competitions.length > 0 && (
                  <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="w-5 h-5" />
              Recent Competitions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {competitions.slice(0, 3).map((competition) => (
                <div key={competition.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-sm">{competition.title}</p>
                    <p className="text-xs text-gray-600">
                      {competition.current_participants || 0} participants • {new Date(competition.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Badge className={
                    competition.status === 'active' ? 'bg-green-500' :
                    competition.status === 'upcoming' ? 'bg-blue-500' :
                    'bg-gray-500'
                  }>
                    {competition.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
                  </Card>
                )}

                {/* Recent Challenges */}
                {challenges.length > 0 && (
                  <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="w-5 h-5" />
              Recent Challenges
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {challenges.slice(0, 3).map((challenge) => (
                <div key={challenge.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-sm">{challenge.title}</p>
                    <p className="text-xs text-gray-600">
                      ₹{challenge.total_prize_value?.toLocaleString()} • {challenge.current_participants || 0} participants
                    </p>
                  </div>
                  <Badge className={
                    challenge.status === 'active' ? 'bg-green-500' :
                    challenge.status === 'upcoming' ? 'bg-blue-500' :
                    'bg-gray-500'
                  }>
                    {challenge.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
                  </Card>
                )}

                {/* Info Banner */}
                <Card className="bg-purple-50 border-purple-200">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <CheckCircle className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-purple-900 mb-1">
                Club Admin Privileges Active
              </h3>
              <p className="text-purple-700 text-sm">
                You have been granted club admin privileges by your campus administrator. 
                You can create and manage competitions and challenges for {admin_details.club_name}.
              </p>
              <p className="text-purple-600 text-xs mt-2">
                Expires: {new Date(admin_details.expires_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="registrations" className="mt-0">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h2 className="text-xl font-semibold">Registration Management</h2>
                    <Select
                      value={selectedEvent.id || ''}
                      onValueChange={(value) => {
                        const option = getEventOptions().find(opt => opt.id === value);
                        setSelectedEvent(option || { id: null, type: null, title: null });
                      }}
                    >
                      <SelectTrigger className="w-80">
                        <SelectValue placeholder="Select an event to view registrations" />
                      </SelectTrigger>
                      <SelectContent>
                        {getEventOptions().map((option) => (
                          <SelectItem key={option.id} value={option.id}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {selectedEvent.id ? (
                    <RegistrationManagement 
                      eventId={selectedEvent.id}
                      eventType={selectedEvent.type}
                      eventTitle={selectedEvent.title}
                    />
                  ) : (
                    <Card>
                      <CardContent className="p-8 text-center">
                        <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-600">Select an Event</h3>
                        <p className="text-gray-500">Choose an event from the dropdown above to view and manage registrations</p>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="colleges" className="mt-0">
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <h2 className="text-xl font-semibold">College-wise Analytics</h2>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Top Participating Colleges</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {Object.entries(collegeRegistrations).slice(0, 5).map(([college, count]) => (
                            <div key={college} className="flex justify-between items-center">
                              <span className="text-sm font-medium">{college}</span>
                              <Badge variant="outline">{count} registrations</Badge>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Registration Trends</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-600 mb-2">
                            {Object.values(collegeRegistrations).reduce((a, b) => a + b, 0)}
                          </div>
                          <p className="text-sm text-gray-600">Total Registrations</p>
                          <div className="text-lg font-semibold text-green-600 mt-2">
                            {Object.keys(collegeRegistrations).length}
                          </div>
                          <p className="text-sm text-gray-600">Colleges Participating</p>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Quick Stats</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-sm">Active Competitions:</span>
                            <span className="font-medium">{competitions.filter(c => c.status === 'active').length}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm">Active Challenges:</span>
                            <span className="font-medium">{challenges.filter(c => c.status === 'active').length}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm">This Month Events:</span>
                            <span className="font-medium">{statistics?.events_this_month || 0}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>College Performance Overview</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-center py-8 text-gray-500">
                        <Building className="w-12 h-12 mx-auto mb-4" />
                        <p>Detailed college analytics will be available once more registration data is collected.</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="settings" className="mt-0">
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold">Club Admin Settings</h2>
                  
                  <Card>
                    <CardHeader>
                      <CardTitle>Admin Information</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm font-medium text-gray-600">Club Name</label>
                          <p className="text-lg">{admin_details.club_name}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-gray-600">College</label>
                          <p className="text-lg">{admin_details.college_name}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-gray-600">Admin Level</label>
                          <Badge className="bg-purple-100 text-purple-800">Club Admin</Badge>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-gray-600">Expires</label>
                          <p className="text-lg">{new Date(admin_details.expires_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Permissions & Capabilities</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 gap-4">
                        <div className="flex items-center justify-between p-3 border rounded-lg">
                          <span>Create College Events</span>
                          <Badge className='bg-green-100 text-green-800'>
                            Enabled
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between p-3 border rounded-lg">
                          <span>Monthly Event Limit</span>
                          <Badge variant="outline">{capabilities.max_events_per_month || 10}</Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </div>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default ClubAdminDashboard;
