import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Progress } from './ui/progress';
import { 
  Trophy, Users, Calendar, Award, Target, Medal, Star, 
  Plus, Settings, BarChart3, Clock, CheckCircle, AlertCircle,
  FileText, GraduationCap, Building, User, Shield, Activity,
  TrendingUp, UserCheck, Flag, Eye, Edit, Trash, AlertTriangle,
  Check, X, Ban, ClipboardList
} from 'lucide-react';
import RegistrationManagement from './RegistrationManagement';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CampusAdminDashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [competitions, setCompetitions] = useState([]);
  const [challenges, setChallenges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  // Moderation state
  const [showModerationModal, setShowModerationModal] = useState(false);
  const [selectedParticipant, setSelectedParticipant] = useState(null);
  const [moderationAction, setModerationAction] = useState('warn');
  const [moderationReason, setModerationReason] = useState('');

  // Club Admin Management State
  const [clubAdminRequests, setClubAdminRequests] = useState([]);
  const [myClubAdmins, setMyClubAdmins] = useState([]);
  const [clubAdminsLoading, setClubAdminsLoading] = useState(false);
  const [selectedClubRequest, setSelectedClubRequest] = useState(null);
  const [showClubRequestModal, setShowClubRequestModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteForm, setInviteForm] = useState({
    user_id: '',
    club_name: '',
    club_type: 'student_organization',
    permissions: ['create_events'],
    max_events_per_month: 3,
    expires_in_months: 6
  });

  // College Events Management State
  const [collegeEvents, setCollegeEvents] = useState([]);
  const [collegeEventsData, setCollegeEventsData] = useState({ total: 0 });
  const [collegeEventsLoading, setCollegeEventsLoading] = useState(false);
  const [collegeEventFilters, setCollegeEventFilters] = useState({
    status: '',
    event_type: ''
  });
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [eventRegistrations, setEventRegistrations] = useState([]);
  const [registrationsLoading, setRegistrationsLoading] = useState(false);
  const [showRegistrationsModal, setShowRegistrationsModal] = useState(false);

  // Registration Management State
  const [allEvents, setAllEvents] = useState([]);
  const [selectedEventForRegistrations, setSelectedEventForRegistrations] = useState({ id: '', type: '', title: '' });

  useEffect(() => {
    fetchDashboardData();
    fetchCompetitions();
    fetchChallenges();
    
    // Set up auto-refresh every 30 seconds for live data updates
    const interval = setInterval(() => {
      fetchDashboardData();
      fetchCompetitions();
      fetchChallenges();
      // Also refresh college events if we're on that tab
      if (activeTab === "college-events") {
        fetchCollegeEvents();
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === "club-admins") {
      fetchClubAdminRequests();
      fetchMyClubAdmins();
    } else if (activeTab === "college-events") {
      fetchCollegeEvents();
    } else if (activeTab === "registrations") {
      fetchAllEventsForRegistrations();
    }
  }, [activeTab]);

  useEffect(() => {
    fetchCollegeEvents();
  }, [collegeEventFilters]);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/campus-admin/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      if (error.response?.status === 403) {
        alert('You do not have campus admin privileges. Please apply for admin access first.');
      }
    }
  };

  const fetchCompetitions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/campus-admin/competitions`, {
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
      const response = await axios.get(`${API}/campus-admin/challenges`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setChallenges(response.data.challenges || []);
    } catch (error) {
      console.error('Error fetching challenges:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCollegeEvents = async () => {
    try {
      setCollegeEventsLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams();
      if (collegeEventFilters.status) params.append('status', collegeEventFilters.status);
      if (collegeEventFilters.event_type) params.append('event_type', collegeEventFilters.event_type);
      
      const response = await axios.get(`${API}/campus-admin/college-events?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setCollegeEvents(response.data.events || []);
      setCollegeEventsData({ 
        total: response.data.total || 0,
        college_name: response.data.college_name
      });
    } catch (error) {
      console.error('Error fetching college events:', error);
      if (error.response?.status === 403) {
        alert('You do not have campus admin privileges for college events.');
      }
    } finally {
      setCollegeEventsLoading(false);
    }
  };

  const fetchAllEventsForRegistrations = async () => {
    try {
      setRegistrationsLoading(true);
      const token = localStorage.getItem('token');
      
      // Campus Admin: Fetch only college events created by campus admin
      const eventsRes = await axios.get(`${API}/campus-admin/college-events`, {
        headers: { 'Authorization': `Bearer ${token}` }
      }).catch(() => ({ data: { events: [] } }));

      const collegeEvents = eventsRes.data.events || [];

      // Format events for dropdown - Campus Admin sees only their college events
      const formattedEvents = collegeEvents.map(e => ({
        id: e.id,
        type: 'college_event',
        title: e.title,
        name: e.title
      }));

      setAllEvents(formattedEvents);
      
      // Auto-select first event if available
      if (formattedEvents.length > 0 && !selectedEventForRegistrations.id) {
        setSelectedEventForRegistrations(formattedEvents[0]);
      }
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setRegistrationsLoading(false);
    }
  };

  const fetchEventRegistrations = async (eventId, statusFilter = '') => {
    try {
      setRegistrationsLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      
      const response = await axios.get(
        `${API}/campus-admin/college-events/${eventId}/registrations?${params}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      setEventRegistrations(response.data.registrations || []);
    } catch (error) {
      console.error('Error fetching event registrations:', error);
    } finally {
      setRegistrationsLoading(false);
    }
  };

  const handleViewEventRegistrations = async (event, statusFilter = '') => {
    setSelectedEvent(event);
    setShowRegistrationsModal(true);
    await fetchEventRegistrations(event.id, statusFilter);
  };

  const handleRegistrationAction = async (registration, action, reason = '') => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/campus-admin/college-events/${selectedEvent.id}/registrations/manage`,
        {
          registration_id: registration.id,
          action: action,
          reason: reason
        },
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      // Refresh registrations and events
      await fetchEventRegistrations(selectedEvent.id);
      await fetchCollegeEvents();
      
      alert(`Registration ${action}d successfully!`);
    } catch (error) {
      console.error(`Error ${action}ing registration:`, error);
      alert(`Failed to ${action} registration. Please try again.`);
    }
  };

  const getEventStatusColor = (status) => {
    switch (status) {
      case 'upcoming': return 'bg-blue-100 text-blue-800';
      case 'ongoing': return 'bg-green-100 text-green-800';
      case 'registration_open': return 'bg-purple-100 text-purple-800';
      case 'completed': return 'bg-gray-100 text-gray-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const moderateParticipant = async () => {
    if (!selectedParticipant || !moderationReason.trim()) {
      alert('Please provide a reason for moderation');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/campus-admin/competitions/${selectedParticipant.competition_id}/moderate`,
        {
          user_id: selectedParticipant.user_id,
          action: moderationAction,
          reason: moderationReason
        },
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      alert(`Participant ${moderationAction}ed successfully`);
      setShowModerationModal(false);
      setSelectedParticipant(null);
      setModerationReason('');
      
      // Refresh data
      fetchCompetitions();
      fetchDashboardData();
      
    } catch (error) {
      console.error('Moderation error:', error);
      alert(error.response?.data?.detail || 'Failed to moderate participant');
    }
  };

  // Club Admin Management Functions
  const fetchClubAdminRequests = async () => {
    try {
      setClubAdminsLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/campus-admin/club-admin-requests`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setClubAdminRequests(response.data.requests || []);
    } catch (error) {
      console.error('Error fetching club admin requests:', error);
    } finally {
      setClubAdminsLoading(false);
    }
  };

  const fetchMyClubAdmins = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/campus-admin/my-club-admins`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setMyClubAdmins(response.data.club_admins || []);
    } catch (error) {
      console.error('Error fetching my club admins:', error);
    }
  };

  const approveClubAdminRequest = async (requestId) => {
    try {
      const token = localStorage.getItem('token');
      const approvalData = {
        permissions: ['create_events', 'manage_participants'],
        max_events_per_month: 5,
        expires_in_months: 12,
        review_notes: 'Approved by campus admin'
      };

      await axios.post(`${API}/campus-admin/club-admin-requests/${requestId}/approve`, approvalData, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      // Refresh data
      fetchClubAdminRequests();
      fetchMyClubAdmins();
      setShowClubRequestModal(false);
      
      alert('Club admin request approved successfully!');
    } catch (error) {
      console.error('Error approving club admin request:', error);
      alert(error.response?.data?.detail || 'Failed to approve request');
    }
  };

  const rejectClubAdminRequest = async (requestId, reason) => {
    try {
      const token = localStorage.getItem('token');
      const rejectionData = {
        rejection_reason: reason,
        review_notes: 'Rejected by campus admin'
      };

      await axios.post(`${API}/campus-admin/club-admin-requests/${requestId}/reject`, rejectionData, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      // Refresh data
      fetchClubAdminRequests();
      setShowClubRequestModal(false);
      
      alert('Club admin request rejected successfully!');
    } catch (error) {
      console.error('Error rejecting club admin request:', error);
      alert(error.response?.data?.detail || 'Failed to reject request');
    }
  };

  const suspendClubAdmin = async (clubAdminId, reason) => {
    try {
      const token = localStorage.getItem('token');
      const suspensionData = {
        reason,
        suspension_days: 30
      };

      await axios.put(`${API}/campus-admin/club-admins/${clubAdminId}/suspend`, suspensionData, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      // Refresh data
      fetchMyClubAdmins();
      
      alert('Club admin suspended successfully!');
    } catch (error) {
      console.error('Error suspending club admin:', error);
      alert(error.response?.data?.detail || 'Failed to suspend club admin');
    }
  };

  const inviteClubAdmin = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/campus-admin/invite-club-admin`, inviteForm, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      // Refresh data and reset form
      fetchClubAdminRequests();
      setInviteForm({
        user_id: '',
        club_name: '',
        club_type: 'student_organization',
        permissions: ['create_events'],
        max_events_per_month: 3,
        expires_in_months: 6
      });
      setShowInviteModal(false);
      
      alert('Club admin invitation sent successfully!');
    } catch (error) {
      console.error('Error inviting club admin:', error);
      alert(error.response?.data?.detail || 'Failed to send invitation');
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { color: 'bg-green-500', text: 'Active' },
      upcoming: { color: 'bg-blue-500', text: 'Upcoming' },
      ended: { color: 'bg-gray-500', text: 'Ended' },
      draft: { color: 'bg-yellow-500', text: 'Draft' }
    };

    const config = statusConfig[status] || statusConfig.draft;
    
    return (
      <Badge className={`${config.color} text-white`}>
        {config.text}
      </Badge>
    );
  };

  const renderOverview = () => {
    if (!dashboardData) return null;

    const { admin_details, statistics, capabilities } = dashboardData;

    return (
      <div className="space-y-6">
        {/* Admin Info Header */}
        <Card className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-2">
                  {admin_details.admin_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Dashboard
                </h2>
                <p className="text-blue-100">{admin_details.college_name}</p>
                {admin_details.club_name && (
                  <p className="text-blue-200 text-sm">{admin_details.club_name}</p>
                )}
              </div>
              <Shield className="w-16 h-16 text-blue-200" />
            </div>
          </CardContent>
        </Card>

        {/* Statistics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Competitions</p>
                  <p className="text-3xl font-bold text-blue-600">{statistics.total_competitions}</p>
                </div>
                <Trophy className="w-8 h-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Challenges</p>
                  <p className="text-3xl font-bold text-green-600">{statistics.total_challenges}</p>
                </div>
                <Award className="w-8 h-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">This Month</p>
                  <p className="text-3xl font-bold text-purple-600">
                    {statistics.competitions_this_month + statistics.challenges_this_month}
                  </p>
                </div>
                <Calendar className="w-8 h-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Remaining Quota</p>
                  <p className="text-3xl font-bold text-orange-600">{statistics.remaining_monthly_quota}</p>
                </div>
                <Target className="w-8 h-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Monthly Quota Progress */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Monthly Creation Quota
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">
                  Used: {statistics.competitions_this_month + statistics.challenges_this_month} / {capabilities.max_competitions_per_month}
                </span>
                <span className="text-sm text-gray-600">
                  {statistics.remaining_monthly_quota} remaining
                </span>
              </div>
              <Progress 
                value={(statistics.competitions_this_month + statistics.challenges_this_month) / capabilities.max_competitions_per_month * 100}
                className="h-2"
              />
            </div>
          </CardContent>
        </Card>

        {/* Capabilities */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Settings className="w-5 h-5 mr-2" />
              Admin Capabilities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                {capabilities.can_create_intra_college ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-gray-400" />
                )}
                <span className={capabilities.can_create_intra_college ? "text-green-700" : "text-gray-500"}>
                  Manage College Events
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <Target className="w-5 h-5 text-blue-600" />
                <span className="text-blue-700">
                  Monthly Event Limit: {capabilities.max_competitions_per_month || 10}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Activity className="w-5 h-5 mr-2" />
                Recent Competitions
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboardData.recent_competitions?.length > 0 ? (
                <div className="space-y-3">
                  {dashboardData.recent_competitions.map((competition) => (
                    <div key={competition.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-sm">{competition.title}</p>
                        <p className="text-xs text-gray-600">
                          {new Date(competition.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      {getStatusBadge(competition.status)}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600 text-center py-4">No competitions created yet</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Star className="w-5 h-5 mr-2" />
                Recent Challenges
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboardData.recent_challenges?.length > 0 ? (
                <div className="space-y-3">
                  {dashboardData.recent_challenges.map((challenge) => (
                    <div key={challenge.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-sm">{challenge.title}</p>
                        <p className="text-xs text-gray-600">
                          {new Date(challenge.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      {getStatusBadge(challenge.status)}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600 text-center py-4">No challenges created yet</p>
              )}
            </CardContent>
          </Card>
        </div>

      </div>
    );
  };

  const renderCompetitions = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold">My Competitions</h3>
        <Button 
          className="bg-blue-600 hover:bg-blue-700"
          onClick={() => window.location.href = '/create-competition'}
          disabled={!dashboardData?.capabilities?.can_create_inter_college}
        >
          <Plus className="w-4 h-4 mr-2" />
          Create New
        </Button>
      </div>

      {competitions.length > 0 ? (
        <div className="grid grid-cols-1 gap-6">
          {competitions.map((competition) => (
            <Card key={competition.id}>
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="text-lg font-semibold mb-1">{competition.title}</h4>
                    <p className="text-gray-600 text-sm mb-2">{competition.description}</p>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span className="flex items-center">
                        <Users className="w-4 h-4 mr-1" />
                        {competition.current_participants || 0} participants
                      </span>
                      <span className="flex items-center">
                        <Building className="w-4 h-4 mr-1" />
                        {competition.participating_campuses || 0} campuses
                      </span>
                      <span className="flex items-center">
                        <Calendar className="w-4 h-4 mr-1" />
                        {new Date(competition.start_date).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  {getStatusBadge(competition.status)}
                </div>

                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => window.location.href = `/inter-college-competitions/${competition.id}`}
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    View
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => {
                      setSelectedParticipant({
                        competition_id: competition.id,
                        competition_title: competition.title
                      });
                      setShowModerationModal(true);
                    }}
                  >
                    <UserCheck className="w-4 h-4 mr-1" />
                    Moderate
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-8 text-center">
            <Trophy className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No Competitions Yet</h3>
            <p className="text-gray-500 mb-4">Create your first inter-college competition to get started</p>
            <Button 
              className="bg-blue-600 hover:bg-blue-700"
              onClick={() => window.location.href = '/create-competition'}
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Competition
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderChallenges = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold">My Challenges</h3>
        <Button 
          className="bg-green-600 hover:bg-green-700"
          onClick={() => window.location.href = '/create-challenge'}
        >
          <Plus className="w-4 h-4 mr-2" />
          Create New
        </Button>
      </div>

      {challenges.length > 0 ? (
        <div className="grid grid-cols-1 gap-6">
          {challenges.map((challenge) => (
            <Card key={challenge.id}>
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="text-lg font-semibold mb-1">{challenge.title}</h4>
                    <p className="text-gray-600 text-sm mb-2">{challenge.description}</p>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span className="flex items-center">
                        <Users className="w-4 h-4 mr-1" />
                        {challenge.current_participants || 0} participants
                      </span>
                      <span className="flex items-center">
                        <Award className="w-4 h-4 mr-1" />
                        ₹{challenge.total_prize_value?.toLocaleString()}
                      </span>
                      <span className="flex items-center">
                        <Calendar className="w-4 h-4 mr-1" />
                        {new Date(challenge.start_date).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  {getStatusBadge(challenge.status)}
                </div>

                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => window.location.href = `/prize-challenges/${challenge.id}`}
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    View
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-8 text-center">
            <Award className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No Challenges Yet</h3>
            <p className="text-gray-500 mb-4">Create your first prize challenge to engage students</p>
            <Button 
              className="bg-green-600 hover:bg-green-700"
              onClick={() => window.location.href = '/create-challenge'}
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Challenge
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderCollegeEvents = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold">College Events Management</h3>
        <div className="flex gap-2">
          <Button 
            variant="outline"
            onClick={fetchCollegeEvents}
            disabled={collegeEventsLoading}
          >
            {collegeEventsLoading ? "Loading..." : "Refresh"}
          </Button>
        </div>
      </div>

      {/* Events Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Events</p>
                <p className="text-2xl font-bold text-gray-900">{collegeEventsData.total || 0}</p>
              </div>
              <Calendar className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Events</p>
                <p className="text-2xl font-bold text-green-600">
                  {collegeEvents.filter(e => ['upcoming', 'ongoing', 'registration_open'].includes(e.status)).length}
                </p>
              </div>
              <Activity className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Registrations</p>
                <p className="text-2xl font-bold text-purple-600">
                  {collegeEvents.reduce((sum, e) => sum + (e.current_registrations || 0), 0)}
                </p>
              </div>
              <Users className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending Approvals</p>
                <p className="text-2xl font-bold text-orange-600">
                  {collegeEvents.reduce((sum, e) => sum + (e.pending_registrations || 0), 0)}
                </p>
              </div>
              <Clock className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Events List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>College Events ({collegeEvents.length})</span>
            <div className="flex gap-2">
              <select 
                className="px-3 py-1 border rounded text-sm"
                value={collegeEventFilters.status}
                onChange={(e) => setCollegeEventFilters({...collegeEventFilters, status: e.target.value})}
              >
                <option value="">All Status</option>
                <option value="upcoming">Upcoming</option>
                <option value="ongoing">Ongoing</option>
                <option value="registration_open">Registration Open</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
              <select 
                className="px-3 py-1 border rounded text-sm"
                value={collegeEventFilters.event_type}
                onChange={(e) => setCollegeEventFilters({...collegeEventFilters, event_type: e.target.value})}
              >
                <option value="">All Types</option>
                <option value="workshop">Workshop</option>
                <option value="hackathon">Hackathon</option>
                <option value="seminar">Seminar</option>
                <option value="competition">Competition</option>
                <option value="cultural">Cultural</option>
                <option value="sports">Sports</option>
              </select>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {collegeEventsLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-600 mt-2">Loading college events...</p>
            </div>
          ) : collegeEvents.length > 0 ? (
            <div className="space-y-4">
              {collegeEvents.map((event) => (
                <div key={event.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-semibold text-lg">{event.title}</h4>
                        <Badge className={getEventStatusColor(event.status)}>
                          {event.status.replace('_', ' ').toUpperCase()}
                        </Badge>
                        <Badge variant="outline">{event.event_type}</Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 mb-3">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          <span>{new Date(event.start_date).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Users className="h-4 w-4" />
                          <span>{event.current_registrations || 0} registrations</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          <span>{event.pending_registrations || 0} pending</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Building className="h-4 w-4" />
                          <span>{event.venue || 'TBA'}</span>
                        </div>
                      </div>
                      
                      {event.description && (
                        <p className="text-sm text-gray-700 mb-2 line-clamp-2">{event.description}</p>
                      )}
                      
                      <div className="text-xs text-gray-500">
                        Created by: {event.creator_name} • {event.can_manage ? 'You can manage this event' : 'External event'}
                      </div>
                    </div>
                    
                    <div className="flex gap-2 ml-4">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleViewEventRegistrations(event)}
                        disabled={!event.can_manage}
                        title={event.can_manage ? "View registrations" : "Cannot manage external events"}
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        Registrations ({event.current_registrations || 0})
                      </Button>
                      
                      {event.pending_registrations > 0 && event.can_manage && (
                        <Button
                          size="sm"
                          className="bg-orange-600 hover:bg-orange-700"
                          onClick={() => handleViewEventRegistrations(event, 'pending')}
                        >
                          <AlertCircle className="h-4 w-4 mr-1" />
                          Pending ({event.pending_registrations})
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">No college events found</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );

  const renderClubAdmins = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold">Club Admin Management</h3>
        <Button 
          className="bg-purple-600 hover:bg-purple-700"
          onClick={() => setShowInviteModal(true)}
        >
          <Plus className="w-4 h-4 mr-2" />
          Invite Club Admin
        </Button>
      </div>

      {/* Club Admin Requests */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            Pending Club Admin Requests
          </CardTitle>
        </CardHeader>
        <CardContent>
          {clubAdminsLoading ? (
            <div className="text-center py-4">
              <Clock className="w-6 h-6 animate-spin mx-auto" />
              <p className="text-gray-600 mt-2">Loading requests...</p>
            </div>
          ) : clubAdminRequests.length > 0 ? (
            <div className="space-y-4">
              {clubAdminRequests.map((request) => (
                <div key={request.id} className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="font-semibold">{request.full_name}</h4>
                        <Badge className={
                          request.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                          request.status === 'approved' ? 'bg-green-100 text-green-700' :
                          'bg-red-100 text-red-700'
                        }>
                          {request.status}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                        <div>
                          <p><strong>Club:</strong> {request.club_name}</p>
                          <p><strong>Email:</strong> {request.email}</p>
                        </div>
                        <div>
                          <p><strong>Type:</strong> {request.club_type}</p>
                          <p><strong>Submitted:</strong> {new Date(request.submitted_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                      {request.motivation && (
                        <p className="text-sm text-gray-700 mt-2 italic">"{request.motivation}"</p>
                      )}
                    </div>
                    
                    <div className="flex space-x-2">
                      {request.status === 'pending' && (
                        <>
                          <Button
                            size="sm"
                            className="bg-green-600 hover:bg-green-700"
                            onClick={() => approveClubAdminRequest(request.id)}
                          >
                            <Check className="w-4 h-4 mr-1" />
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              const reason = prompt('Enter rejection reason:');
                              if (reason) rejectClubAdminRequest(request.id, reason);
                            }}
                          >
                            <X className="w-4 h-4 mr-1" />
                            Reject
                          </Button>
                        </>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedClubRequest(request);
                          setShowClubRequestModal(true);
                        }}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        View Details
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No club admin requests found</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* My Club Admins */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Users className="w-5 h-5 mr-2" />
            My Club Admins ({myClubAdmins.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {myClubAdmins.length > 0 ? (
            <div className="space-y-4">
              {myClubAdmins.map((admin) => (
                <div key={admin.id} className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="font-semibold">{admin.user_details?.full_name}</h4>
                        <Badge className={
                          admin.status === 'active' ? 'bg-green-100 text-green-700' :
                          admin.status === 'suspended' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }>
                          {admin.status}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                        <div>
                          <p><strong>Club:</strong> {admin.club_name}</p>
                          <p><strong>Email:</strong> {admin.user_details?.email}</p>
                          <p><strong>Appointed:</strong> {new Date(admin.appointed_at).toLocaleDateString()}</p>
                        </div>
                        <div>
                          <p><strong>Events Created:</strong> {admin.events_created || 0}</p>
                          <p><strong>Max Events/Month:</strong> {admin.max_events_per_month}</p>
                          <p><strong>Expires:</strong> {new Date(admin.expires_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex space-x-2">
                      {admin.status === 'active' && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-red-600 border-red-300 hover:bg-red-50"
                          onClick={() => {
                            const reason = prompt('Enter suspension reason:');
                            if (reason) suspendClubAdmin(admin.id, reason);
                          }}
                        >
                          <Ban className="w-4 h-4 mr-1" />
                          Suspend
                        </Button>
                      )}
                      <Button size="sm" variant="outline">
                        <Settings className="w-4 h-4 mr-1" />
                        Manage
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No club admins under your management</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );

  if (loading) {
    return (
      <Card className="w-full max-w-6xl mx-auto">
        <CardContent className="p-8">
          <div className="flex items-center justify-center space-x-4">
            <Clock className="w-6 h-6 animate-spin" />
            <p>Loading campus admin dashboard...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!dashboardData) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-8 text-center">
          <AlertTriangle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-800 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-4">
            You do not have campus admin privileges. Please apply for admin access to manage competitions and challenges.
          </p>
          <Button 
            className="bg-blue-600 hover:bg-blue-700"
            onClick={() => window.location.href = '/campus-admin-request'}
          >
            <Shield className="w-4 h-4 mr-2" />
            Apply for Admin Access
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="college-events">College Events</TabsTrigger>
          <TabsTrigger value="registrations">Registrations</TabsTrigger>
          <TabsTrigger value="club-admins">Club Admins</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {renderOverview()}
        </TabsContent>

        <TabsContent value="college-events" className="space-y-6">
          {renderCollegeEvents()}
        </TabsContent>

        <TabsContent value="registrations" className="space-y-6">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-3">
                <ClipboardList className="w-6 h-6 text-blue-600" />
                <h2 className="text-xl font-semibold">Registration Management</h2>
              </div>
              <Button onClick={fetchAllEventsForRegistrations} variant="outline" size="sm">
                <Activity className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-4">
              <label className="block text-sm font-medium mb-2">Select College Event</label>
              <select
                value={selectedEventForRegistrations.id || ''}
                onChange={(e) => {
                  const event = allEvents.find(ev => ev.id === e.target.value);
                  if (event) {
                    setSelectedEventForRegistrations(event);
                  }
                }}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                <option value="">Select a college event...</option>
                {allEvents.map(event => (
                  <option key={`${event.type}-${event.id}`} value={event.id}>
                    {event.title}
                  </option>
                ))}
              </select>
            </div>

            {selectedEventForRegistrations.id ? (
              <RegistrationManagement 
                eventId={selectedEventForRegistrations.id}
                eventType={selectedEventForRegistrations.type}
                eventTitle={selectedEventForRegistrations.name}
              />
            ) : (
              <Card>
                <CardContent className="p-12 text-center">
                  <ClipboardList className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No College Event Selected</h3>
                  <p className="text-gray-600">
                    Select a college event from the dropdown above to view and manage registrations
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="club-admins" className="space-y-6">
          {renderClubAdmins()}
        </TabsContent>
      </Tabs>

      {/* Moderation Modal */}
      <Dialog open={showModerationModal} onOpenChange={setShowModerationModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <UserCheck className="w-6 h-6 mr-2" />
              Moderate Participant
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {selectedParticipant && (
              <p className="text-sm text-gray-600">
                Competition: {selectedParticipant.competition_title}
              </p>
            )}
            
            <div>
              <label className="block text-sm font-medium mb-2">Action</label>
              <select 
                value={moderationAction}
                onChange={(e) => setModerationAction(e.target.value)}
                className="w-full p-3 border rounded-lg"
              >
                <option value="warn">Issue Warning</option>
                <option value="disqualify">Disqualify Participant</option>
                <option value="reinstate">Reinstate Participant</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Reason *</label>
              <textarea
                value={moderationReason}
                onChange={(e) => setModerationReason(e.target.value)}
                className="w-full p-3 border rounded-lg h-24"
                placeholder="Provide a clear reason for this moderation action..."
                required
              />
            </div>
            
            <div className="flex justify-end space-x-4">
              <Button 
                variant="outline" 
                onClick={() => setShowModerationModal(false)}
              >
                Cancel
              </Button>
              <Button 
                onClick={moderateParticipant}
                className="bg-red-600 hover:bg-red-700"
                disabled={!moderationReason.trim()}
              >
                <Flag className="w-4 h-4 mr-2" />
                Apply Action
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Club Admin Request Details Modal */}
      {selectedClubRequest && (
        <Dialog open={showClubRequestModal} onOpenChange={setShowClubRequestModal}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Club Admin Request Details</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium">Applicant Information</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Name:</strong> {selectedClubRequest.full_name}</p>
                    <p><strong>Email:</strong> {selectedClubRequest.email}</p>
                    <p><strong>Phone:</strong> {selectedClubRequest.phone_number}</p>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium">Club Details</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Club Name:</strong> {selectedClubRequest.club_name}</p>
                    <p><strong>Club Type:</strong> {selectedClubRequest.club_type}</p>
                    <p><strong>Status:</strong> {selectedClubRequest.status}</p>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">Motivation</h4>
                <p className="text-sm text-gray-600 p-3 bg-gray-50 rounded">{selectedClubRequest.motivation}</p>
              </div>
              
              {selectedClubRequest.previous_experience && (
                <div>
                  <h4 className="font-medium mb-2">Previous Experience</h4>
                  <p className="text-sm text-gray-600 p-3 bg-gray-50 rounded">{selectedClubRequest.previous_experience}</p>
                </div>
              )}
              
              <div className="flex justify-end space-x-4 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowClubRequestModal(false)}
                >
                  Close
                </Button>
                {selectedClubRequest.status === 'pending' && (
                  <div className="flex space-x-2">
                    <Button
                      className="bg-green-600 hover:bg-green-700"
                      onClick={() => approveClubAdminRequest(selectedClubRequest.id)}
                    >
                      <Check className="w-4 h-4 mr-2" />
                      Approve
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        const reason = prompt('Enter rejection reason:');
                        if (reason) rejectClubAdminRequest(selectedClubRequest.id, reason);
                      }}
                    >
                      <X className="w-4 h-4 mr-2" />
                      Reject
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Invite Club Admin Modal */}
      <Dialog open={showInviteModal} onOpenChange={setShowInviteModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Invite Club Admin</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">User ID *</label>
              <input
                type="text"
                value={inviteForm.user_id}
                onChange={(e) => setInviteForm({...inviteForm, user_id: e.target.value})}
                className="w-full p-3 border rounded-lg"
                placeholder="Enter user ID to invite"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Club Name *</label>
              <input
                type="text"
                value={inviteForm.club_name}
                onChange={(e) => setInviteForm({...inviteForm, club_name: e.target.value})}
                className="w-full p-3 border rounded-lg"
                placeholder="Enter club name"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Club Type</label>
              <select
                value={inviteForm.club_type}
                onChange={(e) => setInviteForm({...inviteForm, club_type: e.target.value})}
                className="w-full p-3 border rounded-lg"
              >
                <option value="student_organization">Student Organization</option>
                <option value="academic_club">Academic Club</option>
                <option value="sports_club">Sports Club</option>
                <option value="cultural_club">Cultural Club</option>
                <option value="technical_club">Technical Club</option>
              </select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Max Events per Month</label>
                <input
                  type="number"
                  value={inviteForm.max_events_per_month}
                  onChange={(e) => setInviteForm({...inviteForm, max_events_per_month: parseInt(e.target.value)})}
                  className="w-full p-3 border rounded-lg"
                  min="1"
                  max="20"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Expires in Months</label>
                <input
                  type="number"
                  value={inviteForm.expires_in_months}
                  onChange={(e) => setInviteForm({...inviteForm, expires_in_months: parseInt(e.target.value)})}
                  className="w-full p-3 border rounded-lg"
                  min="1"
                  max="24"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Permissions</label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={inviteForm.permissions.includes('create_events')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setInviteForm({...inviteForm, permissions: [...inviteForm.permissions, 'create_events']});
                      } else {
                        setInviteForm({...inviteForm, permissions: inviteForm.permissions.filter(p => p !== 'create_events')});
                      }
                    }}
                    className="mr-2"
                  />
                  Create Events
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={inviteForm.permissions.includes('manage_participants')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setInviteForm({...inviteForm, permissions: [...inviteForm.permissions, 'manage_participants']});
                      } else {
                        setInviteForm({...inviteForm, permissions: inviteForm.permissions.filter(p => p !== 'manage_participants')});
                      }
                    }}
                    className="mr-2"
                  />
                  Manage Participants
                </label>
              </div>
            </div>
            
            <div className="flex justify-end space-x-4">
              <Button
                variant="outline"
                onClick={() => setShowInviteModal(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={inviteClubAdmin}
                className="bg-purple-600 hover:bg-purple-700"
                disabled={!inviteForm.user_id || !inviteForm.club_name}
              >
                <Plus className="w-4 h-4 mr-2" />
                Send Invitation
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Event Registrations Modal */}
      {selectedEvent && (
        <Dialog open={showRegistrationsModal} onOpenChange={setShowRegistrationsModal}>
          <DialogContent className="max-w-6xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                Registrations for "{selectedEvent.title}"
              </DialogTitle>
              <p className="text-sm text-gray-600">
                Manage registrations for this college event
              </p>
            </DialogHeader>
            
            <div className="space-y-4">
              {/* Registration Stats */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-blue-50 p-3 rounded">
                  <div className="text-sm text-blue-600">Total Registrations</div>
                  <div className="text-xl font-bold text-blue-800">{eventRegistrations.length}</div>
                </div>
                <div className="bg-green-50 p-3 rounded">
                  <div className="text-sm text-green-600">Approved</div>
                  <div className="text-xl font-bold text-green-800">
                    {eventRegistrations.filter(r => r.status === 'approved').length}
                  </div>
                </div>
                <div className="bg-orange-50 p-3 rounded">
                  <div className="text-sm text-orange-600">Pending</div>
                  <div className="text-xl font-bold text-orange-800">
                    {eventRegistrations.filter(r => r.status === 'pending').length}
                  </div>
                </div>
              </div>
              
              {/* Registrations List */}
              {registrationsLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="text-gray-600 mt-2">Loading registrations...</p>
                </div>
              ) : eventRegistrations.length > 0 ? (
                <div className="space-y-4">
                  {eventRegistrations.map((registration) => (
                    <div key={registration.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h4 className="font-semibold">{registration.user_name}</h4>
                            <Badge className={
                              registration.status === 'approved' ? 'bg-green-100 text-green-800' :
                              registration.status === 'pending' ? 'bg-orange-100 text-orange-800' :
                              'bg-red-100 text-red-800'
                            }>
                              {registration.status.toUpperCase()}
                            </Badge>
                            <Badge variant="outline">{registration.registration_type}</Badge>
                          </div>
                          
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm text-gray-600 mb-2">
                            <div><strong>Email:</strong> {registration.user_email}</div>
                            <div><strong>College:</strong> {registration.user_college}</div>
                            <div><strong>Phone:</strong> {registration.phone_number || 'N/A'}</div>
                            <div><strong>Year:</strong> {registration.year || 'N/A'}</div>
                            <div><strong>Branch:</strong> {registration.branch || 'N/A'}</div>
                          </div>
                          
                          {registration.registration_type === 'group' && (
                            <div className="mt-2 p-2 bg-gray-50 rounded">
                              <div className="text-sm">
                                <strong>Team:</strong> {registration.team_name} 
                                ({registration.team_size} members)
                              </div>
                              <div className="text-sm">
                                <strong>Leader:</strong> {registration.team_leader_name}
                              </div>
                            </div>
                          )}
                          
                          <div className="text-xs text-gray-500 mt-2">
                            Registered: {new Date(registration.registration_date).toLocaleString()}
                          </div>
                        </div>
                        
                        <div className="flex gap-2 ml-4">
                          {registration.status === 'pending' && (
                            <>
                              <Button
                                size="sm"
                                className="bg-green-600 hover:bg-green-700"
                                onClick={() => handleRegistrationAction(registration, 'approve')}
                              >
                                <Check className="h-4 w-4 mr-1" />
                                Approve
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="border-red-300 text-red-600 hover:bg-red-50"
                                onClick={() => {
                                  const reason = prompt('Please provide a reason for rejection:');
                                  if (reason) {
                                    handleRegistrationAction(registration, 'reject', reason);
                                  }
                                }}
                              >
                                <X className="h-4 w-4 mr-1" />
                                Reject
                              </Button>
                            </>
                          )}
                          
                          {registration.status === 'approved' && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="border-red-300 text-red-600 hover:bg-red-50"
                              onClick={() => {
                                const reason = prompt('Please provide a reason for rejection:');
                                if (reason) {
                                  handleRegistrationAction(registration, 'reject', reason);
                                }
                              }}
                            >
                              <Ban className="h-4 w-4 mr-1" />
                              Revoke
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No registrations found for this event</p>
                </div>
              )}
              
              <div className="flex justify-end">
                <Button
                  variant="outline"
                  onClick={() => setShowRegistrationsModal(false)}
                >
                  Close
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default CampusAdminDashboard;
