import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Progress } from './ui/progress';
import { 
  Shield, Users, FileText, Settings, Eye, Check, X, 
  Clock, AlertCircle, CheckCircle, User, GraduationCap,
  Building, Mail, Phone, Calendar, Award, Trophy, Flag,
  Activity, BarChart3, TrendingUp, AlertTriangle, Search,
  UserCheck, Crown, Target, Bell, Filter, Download,
  Pause, Play, Ban, RotateCcw, Plus, Edit
} from 'lucide-react';
import useAdminWebSocket from '../hooks/useAdminWebSocket';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SuperAdminInterface = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");
  
  // Real-time notifications
  const { isConnected: wsConnected } = useAdminWebSocket({
    onAdminRequestSubmitted: (message) => {
      fetchDashboardData();
      fetchCampusAdminRequests();
      
      if (window.showToast) {
        window.showToast({
          type: 'info',
          title: 'New Admin Request',
          message: message.message
        });
      }
    },
    onConnect: () => console.log('Super admin WebSocket connected'),
    onError: (error) => console.error('Super admin WebSocket error:', error)
  });

  // Dashboard State
  const [dashboardData, setDashboardData] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);

  // Campus Admin Requests State
  const [adminRequests, setAdminRequests] = useState([]);
  const [requestsLoading, setRequestsLoading] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [showRequestModal, setShowRequestModal] = useState(false);

  // Campus Admin Oversight State
  const [campusAdmins, setCampusAdmins] = useState([]);
  const [adminsLoading, setAdminsLoading] = useState(false);
  const [selectedAdmin, setSelectedAdmin] = useState(null);
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [adminActivities, setAdminActivities] = useState([]);

  // Club Admin Visibility State
  const [clubAdmins, setClubAdmins] = useState([]);
  const [clubAdminsLoading, setClubAdminsLoading] = useState(false);

  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logFilters, setLogFilters] = useState({
    severity: '',
    action_type: '',
    date_range: ''
  });

  // Real-time Alerts State
  const [alerts, setAlerts] = useState([]);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [unreadAlerts, setUnreadAlerts] = useState(0);

  // Review State
  const [reviewDecision, setReviewDecision] = useState('approve');
  const [reviewNotes, setReviewNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [reviewing, setReviewing] = useState(false);

  // Competition Creation State
  const [showCompetitionForm, setShowCompetitionForm] = useState(false);
  const [competitionForm, setCompetitionForm] = useState({
    title: '',
    description: '',
    competition_type: 'hackathon',
    start_date: '',
    end_date: '',
    registration_start: '',
    registration_end: '',
    min_participants_per_campus: 10,
    max_participants_per_campus: 100,
    eligible_universities: [],
    min_user_level: 1,
    scoring_method: 'total',
    target_metric: 'projects_submitted',
    target_value: null,
    prize_pool: 0,
    prize_distribution: {
      first: 50,
      second: 30,
      third: 20
    },
    campus_reputation_points: {
      winner: 1000,
      runner_up: 500,
      participation: 100
    },
    participation_rewards: {}
  });
  const [creatingCompetition, setCreatingCompetition] = useState(false);

  // Challenge Creation State
  const [showChallengeForm, setShowChallengeForm] = useState(false);
  const [challengeForm, setChallengeForm] = useState({
    title: '',
    description: '',
    challenge_type: 'skill_based',
    challenge_category: 'individual',
    difficulty_level: 'medium',
    target_metric: 'completion_score',
    target_value: 100,
    start_date: '',
    end_date: '',
    duration_hours: 24,
    max_participants: 50,
    entry_requirements: {},
    prize_type: 'cash',
    total_prize_value: 0,
    prize_structure: {
      first: 50,
      second: 30,
      third: 20
    },
    scholarship_details: null,
    campus_reputation_rewards: {
      winner: 500,
      participation: 100
    }
  });
  const [creatingChallenge, setCreatingChallenge] = useState(false);

  useEffect(() => {
    checkSuperAdminAccess();
  }, []);

  useEffect(() => {
    if (activeTab === "dashboard") {
      fetchDashboardData();
    } else if (activeTab === "requests") {
      fetchCampusAdminRequests();
    } else if (activeTab === "oversight") {
      fetchCampusAdminsOversight();
    } else if (activeTab === "club-admins") {
      fetchClubAdminsOverview();
    } else if (activeTab === "competitions") {
      // Competition tab - no data fetching needed for now
    } else if (activeTab === "challenges") {
      // Challenge tab - no data fetching needed for now
    } else if (activeTab === "audit") {
      fetchAuditLogs();
    } else if (activeTab === "alerts") {
      fetchAlerts();
    }
  }, [activeTab, logFilters]);

  const checkSuperAdminAccess = async () => {
    try {
      await axios.get(`${API}/super-admin/dashboard`);
      setLoading(false);
    } catch (error) {
      console.error('Super admin access check failed:', error);
      if (error.response?.status === 403) {
        alert('You do not have super administrator privileges.');
      }
      setLoading(false);
    }
  };

  const fetchDashboardData = async () => {
    try {
      setDashboardLoading(true);
      const response = await axios.get(`${API}/super-admin/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setDashboardLoading(false);
    }
  };

  const fetchCampusAdminRequests = async () => {
    try {
      setRequestsLoading(true);
      const response = await axios.get(`${API}/super-admin/requests`);
      setAdminRequests(response.data.requests || []);
    } catch (error) {
      console.error('Error fetching admin requests:', error);
    } finally {
      setRequestsLoading(false);
    }
  };

  const fetchCampusAdminsOversight = async () => {
    try {
      setAdminsLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/super-admin/admins`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setCampusAdmins(response.data.admins || []);
    } catch (error) {
      console.error('Error fetching campus admins:', error);
      if (error.response?.status === 403) {
        alert('Super admin access required');
      }
    } finally {
      setAdminsLoading(false);
    }
  };

  const fetchClubAdminsOverview = async () => {
    try {
      setClubAdminsLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/super-admin/club-admins`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setClubAdmins(response.data.club_admins || []);
    } catch (error) {
      console.error('Error fetching club admins:', error);
      if (error.response?.status === 403) {
        alert('Super admin access required');
      }
    } finally {
      setClubAdminsLoading(false);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      setLogsLoading(true);
      const params = new URLSearchParams();
      Object.entries(logFilters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      const response = await axios.get(`${API}/super-admin/audit-logs?${params}`);
      setAuditLogs(response.data.audit_logs || []);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    } finally {
      setLogsLoading(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      setAlertsLoading(true);
      const response = await axios.get(`${API}/super-admin/alerts`);
      setAlerts(response.data.alerts || []);
      setUnreadAlerts(response.data.unread_count || 0);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setAlertsLoading(false);
    }
  };

  const reviewAdminRequest = async (requestId, decision) => {
    try {
      setReviewing(true);
      
      const payload = {
        decision,
        review_notes: reviewNotes,
        ...(decision === 'reject' && { rejection_reason: rejectionReason })
      };

      await axios.post(`${API}/super-admin/requests/${requestId}/review`, payload);
      
      // Refresh requests
      fetchCampusAdminRequests();
      fetchDashboardData();
      
      // Reset form and close modal
      setSelectedRequest(null);
      setShowRequestModal(false);
      setReviewNotes('');
      setRejectionReason('');
      
    } catch (error) {
      console.error('Error reviewing admin request:', error);
      alert('Failed to process request. Please try again.');
    } finally {
      setReviewing(false);
    }
  };

  const suspendCampusAdmin = async (adminId, reason, duration) => {
    try {
      await axios.put(`${API}/super-admin/campus-admins/${adminId}/suspend`, {
        reason,
        suspension_days: duration
      });
      
      fetchCampusAdminsOversight();
      fetchDashboardData();
      
    } catch (error) {
      console.error('Error suspending admin:', error);
      alert('Failed to suspend admin. Please try again.');
    }
  };

  const markAlertAsRead = async (alertId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/super-admin/alerts/${alertId}/read`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      fetchAlerts();
    } catch (error) {
      console.error('Error marking alert as read:', error);
    }
  };

  const handleCreateCompetition = async () => {
    setCreatingCompetition(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/inter-college/competitions`, competitionForm, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data.success) {
        alert('Competition created successfully!');
        setShowCompetitionForm(false);
        setCompetitionForm({
          title: '',
          description: '',
          competition_type: 'hackathon',
          start_date: '',
          end_date: '',
          registration_start: '',
          registration_end: '',
          min_participants_per_campus: 10,
          max_participants_per_campus: 100,
          eligible_universities: [],
          min_user_level: 1,
          scoring_method: 'total',
          target_metric: 'projects_submitted',
          target_value: null,
          prize_pool: 0,
          prize_distribution: { first: 50, second: 30, third: 20 },
          campus_reputation_points: { winner: 1000, runner_up: 500, participation: 100 },
          participation_rewards: {}
        });
      }
    } catch (error) {
      console.error('Error creating competition:', error);
      alert('Failed to create competition: ' + (error.response?.data?.detail || error.message));
    } finally {
      setCreatingCompetition(false);
    }
  };

  const handleCreateChallenge = async () => {
    setCreatingChallenge(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/prize-challenges`, challengeForm, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data.success) {
        alert('Challenge created successfully!');
        setShowChallengeForm(false);
        setChallengeForm({
          title: '',
          description: '',
          challenge_type: 'skill_based',
          challenge_category: 'individual',
          difficulty_level: 'medium',
          target_metric: 'completion_score',
          target_value: 100,
          start_date: '',
          end_date: '',
          duration_hours: 24,
          max_participants: 50,
          entry_requirements: {},
          prize_type: 'cash',
          total_prize_value: 0,
          prize_structure: { first: 50, second: 30, third: 20 },
          scholarship_details: null,
          campus_reputation_rewards: { winner: 500, participation: 100 }
        });
      }
    } catch (error) {
      console.error('Error creating challenge:', error);
      alert('Failed to create challenge: ' + (error.response?.data?.detail || error.message));
    } finally {
      setCreatingChallenge(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Super Admin Interface...</p>
        </div>
      </div>
    );
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-700';
      case 'warning': return 'bg-yellow-100 text-yellow-700';
      case 'error': return 'bg-orange-100 text-orange-700';
      default: return 'bg-blue-100 text-blue-700';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-700';
      case 'approved': return 'bg-green-100 text-green-700';
      case 'rejected': return 'bg-red-100 text-red-700';
      case 'active': return 'bg-green-100 text-green-700';
      case 'suspended': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Crown className="w-8 h-8 text-purple-600" />
                <h1 className="text-2xl font-bold text-gray-900">Super Admin Dashboard</h1>
              </div>
              {wsConnected && (
                <Badge className="bg-green-100 text-green-700">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-1"></div>
                  Live
                </Badge>
              )}
            </div>
            
            <div className="flex items-center space-x-4">
              {unreadAlerts > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setActiveTab("alerts")}
                  className="relative"
                >
                  <Bell className="w-4 h-4 mr-2" />
                  Alerts
                  <Badge className="absolute -top-2 -right-2 h-5 w-5 rounded-full bg-red-500 text-white text-xs">
                    {unreadAlerts}
                  </Badge>
                </Button>
              )}
              <div className="text-sm text-gray-600">
                Welcome, <span className="font-medium">{user?.full_name}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-8">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="requests">Admin Requests</TabsTrigger>
            <TabsTrigger value="oversight">Campus Admins</TabsTrigger>
            <TabsTrigger value="club-admins">Club Admins</TabsTrigger>
            <TabsTrigger value="competitions">Create Competition</TabsTrigger>
            <TabsTrigger value="challenges">Create Challenge</TabsTrigger>
            <TabsTrigger value="audit">Audit Logs</TabsTrigger>
            <TabsTrigger value="alerts">Alerts</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {dashboardLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
              </div>
            ) : dashboardData ? (
              <>
                {/* Metrics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-600">Total Campus Admins</p>
                          <p className="text-2xl font-bold text-gray-900">
                            {dashboardData.summary?.total_campus_admins || 0}
                          </p>
                        </div>
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <Users className="w-4 h-4 text-blue-600" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-600">Total Club Admins</p>
                          <p className="text-2xl font-bold text-gray-900">
                            {dashboardData.summary?.club_admins || 0}
                          </p>
                        </div>
                        <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                          <GraduationCap className="w-4 h-4 text-green-600" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-600">Pending Requests</p>
                          <p className="text-2xl font-bold text-gray-900">
                            {dashboardData.summary?.pending_requests || 0}
                          </p>
                        </div>
                        <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                          <Clock className="w-4 h-4 text-yellow-600" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-600">Unread Alerts</p>
                          <p className="text-2xl font-bold text-gray-900">
                            {dashboardData.summary?.unread_alerts || 0}
                          </p>
                        </div>
                        <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                          <Bell className="w-4 h-4 text-red-600" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Recent Activity */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Recent Admin Activity (24h)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {dashboardData.recent_activity?.slice(0, 5).map((activity, index) => (
                          <div key={index} className="flex items-center space-x-3">
                            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                            <div className="flex-1">
                              <p className="text-sm font-medium">{activity.action_description}</p>
                              <p className="text-xs text-gray-500">{activity.college_name}</p>
                            </div>
                            <div className="text-xs text-gray-400">
                              {new Date(activity.timestamp).toLocaleTimeString()}
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Top Performing Admins</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {dashboardData.top_performing_admins?.slice(0, 5).map((admin, index) => (
                          <div key={index} className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
                                <Trophy className="w-4 h-4 text-emerald-600" />
                              </div>
                              <div>
                                <p className="text-sm font-medium">{admin.admin_name}</p>
                                <p className="text-xs text-gray-500">{admin.college_name}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-bold text-emerald-600">{admin.success_rate}%</p>
                              <p className="text-xs text-gray-500">{admin.competitions_created} events</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">No dashboard data available</p>
              </div>
            )}
          </TabsContent>

          {/* Campus Admin Requests Tab */}
          <TabsContent value="requests" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Campus Admin Requests</h2>
              <Button onClick={fetchCampusAdminRequests} variant="outline" size="sm">
                <Search className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>

            {requestsLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
              </div>
            ) : (
              <div className="grid gap-4">
                {adminRequests.map((request) => (
                  <Card key={request.id} className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h3 className="font-semibold text-lg">{request.full_name}</h3>
                            <Badge className={getStatusColor(request.status)}>
                              {request.status}
                            </Badge>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                            <div>
                              <p><strong>College:</strong> {request.college_name}</p>
                              <p><strong>Admin Type:</strong> {request.admin_type}</p>
                            </div>
                            <div>
                              <p><strong>Email:</strong> {request.email}</p>
                              <p><strong>Submitted:</strong> {new Date(request.submitted_at).toLocaleDateString()}</p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex space-x-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedRequest(request);
                              setShowRequestModal(true);
                            }}
                          >
                            <Eye className="w-4 h-4 mr-2" />
                            Review
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                
                {adminRequests.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-gray-500">No admin requests found</p>
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          {/* Campus Admins Oversight Tab */}
          <TabsContent value="oversight" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Campus Admins Oversight</h2>
              <Button onClick={fetchCampusAdminsOversight} variant="outline" size="sm">
                <Activity className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>

            {adminsLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
              </div>
            ) : (
              <div className="grid gap-4">
                {campusAdmins.map((admin) => (
                  <Card key={admin.id}>
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h3 className="font-semibold text-lg">{admin.admin_name}</h3>
                            <Badge className={getStatusColor(admin.status)}>
                              {admin.status}
                            </Badge>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                            <div>
                              <p><strong>College:</strong> {admin.college_name}</p>
                              <p><strong>Admin Type:</strong> {admin.admin_type}</p>
                              <p><strong>Days Active:</strong> {admin.days_active}</p>
                            </div>
                            <div>
                              <p><strong>Success Rate:</strong> {admin.success_rate}%</p>
                              <p><strong>Competitions:</strong> {admin.competitions_created}</p>
                              <p><strong>Participants:</strong> {admin.participants_managed}</p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex space-x-2">
                          {admin.status === 'active' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => suspendCampusAdmin(admin.id, 'Administrative review', 30)}
                            >
                              <Pause className="w-4 h-4 mr-2" />
                              Suspend
                            </Button>
                          )}
                          <Button size="sm" variant="outline">
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                
                {campusAdmins.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-gray-500">No campus admins found</p>
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          {/* Club Admins Visibility Tab */}
          <TabsContent value="club-admins" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Club Admins Overview</h2>
              <Button onClick={fetchClubAdminsOverview} variant="outline" size="sm">
                <GraduationCap className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>

            {clubAdminsLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
              </div>
            ) : (
              <div className="grid gap-4">
                {clubAdmins.map((clubAdmin) => (
                  <Card key={clubAdmin.id}>
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h3 className="font-semibold text-lg">{clubAdmin.user_name}</h3>
                            <Badge className={getStatusColor(clubAdmin.status)}>
                              {clubAdmin.status}
                            </Badge>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                            <div>
                              <p><strong>Club:</strong> {clubAdmin.club_name}</p>
                              <p><strong>College:</strong> {clubAdmin.college_name}</p>
                              <p><strong>Appointed By:</strong> {clubAdmin.appointed_by_name}</p>
                            </div>
                            <div>
                              <p><strong>Events Created:</strong> {clubAdmin.events_created}</p>
                              <p><strong>Appointed:</strong> {new Date(clubAdmin.appointed_at).toLocaleDateString()}</p>
                              <p><strong>Expires:</strong> {new Date(clubAdmin.expires_at).toLocaleDateString()}</p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex space-x-2">
                          <Button size="sm" variant="outline">
                            <Eye className="w-4 h-4 mr-2" />
                            View Activity
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                
                {clubAdmins.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-gray-500">No club admins found</p>
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          {/* Audit Logs Tab */}
          <TabsContent value="audit" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Audit Logs</h2>
              <div className="flex space-x-2">
                <select
                  value={logFilters.severity}
                  onChange={(e) => setLogFilters({...logFilters, severity: e.target.value})}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="">All Severities</option>
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="error">Error</option>
                  <option value="critical">Critical</option>
                </select>
                <Button onClick={fetchAuditLogs} variant="outline" size="sm">
                  <Filter className="w-4 h-4 mr-2" />
                  Filter
                </Button>
              </div>
            </div>

            {logsLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
              </div>
            ) : (
              <div className="space-y-4">
                {auditLogs.map((log) => (
                  <Card key={log.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <Badge className={getSeverityColor(log.severity)}>
                              {log.severity}
                            </Badge>
                            <span className="text-sm text-gray-500">{log.action_type}</span>
                          </div>
                          <p className="text-sm">{log.action_description}</p>
                          <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                            <span>Admin: {log.admin_name}</span>
                            <span>College: {log.college_name}</span>
                            <span>IP: {log.ip_address}</span>
                            <span>{new Date(log.timestamp).toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                
                {auditLogs.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-gray-500">No audit logs found</p>
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          {/* Alerts Tab */}
          <TabsContent value="alerts" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Real-time Alerts</h2>
              <Button onClick={fetchAlerts} variant="outline" size="sm">
                <Bell className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>

            {alertsLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
              </div>
            ) : (
              <div className="space-y-4">
                {alerts.map((alert) => (
                  <Card key={alert.id} className={!alert.is_read ? 'bg-blue-50' : ''}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <Badge className={getSeverityColor(alert.severity)}>
                              {alert.severity}
                            </Badge>
                            {!alert.is_read && (
                              <Badge className="bg-blue-100 text-blue-700">New</Badge>
                            )}
                          </div>
                          <h3 className="font-medium">{alert.title}</h3>
                          <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                          <div className="mt-2 text-xs text-gray-500">
                            {new Date(alert.created_at).toLocaleString()}
                          </div>
                        </div>
                        
                        {!alert.is_read && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => markAlertAsRead(alert.id)}
                          >
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Mark Read
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
                
                {alerts.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-gray-500">No alerts found</p>
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          {/* Create Competition Tab */}
          <TabsContent value="competitions" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Create Inter-College Competition</h2>
              <div className="flex items-center space-x-2">
                <Trophy className="w-5 h-5 text-yellow-600" />
                <span className="text-sm text-gray-600">Competition Management</span>
              </div>
            </div>

            {!showCompetitionForm ? (
              <Card>
                <CardContent className="p-6">
                  <div className="text-center py-8">
                    <Trophy className="w-16 h-16 text-yellow-600 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold mb-2">Competition Creation</h3>
                    <p className="text-gray-600 mb-6">Create and manage inter-college competitions</p>
                    <Button 
                      className="bg-yellow-600 hover:bg-yellow-700"
                      onClick={() => setShowCompetitionForm(true)}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create New Competition
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Create Inter-College Competition</span>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setShowCompetitionForm(false)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Title *</label>
                      <input
                        type="text"
                        value={competitionForm.title}
                        onChange={(e) => setCompetitionForm({...competitionForm, title: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                        placeholder="Competition title"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Competition Type *</label>
                      <select
                        value={competitionForm.competition_type}
                        onChange={(e) => setCompetitionForm({...competitionForm, competition_type: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      >
                        <option value="hackathon">Hackathon</option>
                        <option value="coding_contest">Coding Contest</option>
                        <option value="project_showcase">Project Showcase</option>
                        <option value="business_plan">Business Plan</option>
                        <option value="case_study">Case Study</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Description *</label>
                    <textarea
                      value={competitionForm.description}
                      onChange={(e) => setCompetitionForm({...competitionForm, description: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      rows={3}
                      placeholder="Competition description"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Start Date *</label>
                      <input
                        type="datetime-local"
                        value={competitionForm.start_date}
                        onChange={(e) => setCompetitionForm({...competitionForm, start_date: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">End Date *</label>
                      <input
                        type="datetime-local"
                        value={competitionForm.end_date}
                        onChange={(e) => setCompetitionForm({...competitionForm, end_date: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Registration Start *</label>
                      <input
                        type="datetime-local"
                        value={competitionForm.registration_start}
                        onChange={(e) => setCompetitionForm({...competitionForm, registration_start: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Registration End *</label>
                      <input
                        type="datetime-local"
                        value={competitionForm.registration_end}
                        onChange={(e) => setCompetitionForm({...competitionForm, registration_end: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Target Metric *</label>
                      <select
                        value={competitionForm.target_metric}
                        onChange={(e) => setCompetitionForm({...competitionForm, target_metric: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      >
                        <option value="projects_submitted">Projects Submitted</option>
                        <option value="completion_rate">Completion Rate</option>
                        <option value="innovation_score">Innovation Score</option>
                        <option value="technical_score">Technical Score</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Prize Pool (₹) *</label>
                      <input
                        type="number"
                        value={competitionForm.prize_pool}
                        onChange={(e) => setCompetitionForm({...competitionForm, prize_pool: parseInt(e.target.value) || 0})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                        min="0"
                        placeholder="Total prize money"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Max Participants per Campus</label>
                      <input
                        type="number"
                        value={competitionForm.max_participants_per_campus}
                        onChange={(e) => setCompetitionForm({...competitionForm, max_participants_per_campus: parseInt(e.target.value)})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                        min="1"
                      />
                    </div>
                  </div>

                  {/* Prize distribution is handled automatically based on prize_pool */}

                  {/* Additional competition details can be added later */}

                  <div className="flex space-x-4 pt-4">
                    <Button 
                      className="flex-1 bg-yellow-600 hover:bg-yellow-700"
                      onClick={handleCreateCompetition}
                      disabled={creatingCompetition || !competitionForm.title || !competitionForm.description || !competitionForm.target_metric || competitionForm.prize_pool <= 0}
                    >
                      {creatingCompetition ? 'Creating...' : 'Create Competition'}
                    </Button>
                    <Button 
                      variant="outline"
                      className="flex-1"
                      onClick={() => setShowCompetitionForm(false)}
                      disabled={creatingCompetition}
                    >
                      Cancel
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Create Challenge Tab */}
          <TabsContent value="challenges" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Create Prize Challenge</h2>
              <div className="flex items-center space-x-2">
                <Award className="w-5 h-5 text-purple-600" />
                <span className="text-sm text-gray-600">Challenge Management</span>
              </div>
            </div>

            {!showChallengeForm ? (
              <Card>
                <CardContent className="p-6">
                  <div className="text-center py-8">
                    <Award className="w-16 h-16 text-purple-600 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold mb-2">Challenge Creation</h3>
                    <p className="text-gray-600 mb-6">Create and manage skill-based challenges</p>
                    <Button 
                      className="bg-purple-600 hover:bg-purple-700"
                      onClick={() => setShowChallengeForm(true)}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create New Challenge
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Create Prize Challenge</span>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setShowChallengeForm(false)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Title *</label>
                      <input
                        type="text"
                        value={challengeForm.title}
                        onChange={(e) => setChallengeForm({...challengeForm, title: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                        placeholder="Challenge title"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Type *</label>
                      <select
                        value={challengeForm.type}
                        onChange={(e) => setChallengeForm({...challengeForm, type: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      >
                        <option value="skill_based">Skill Based</option>
                        <option value="creative">Creative</option>
                        <option value="technical">Technical</option>
                        <option value="problem_solving">Problem Solving</option>
                        <option value="research">Research</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Description *</label>
                    <textarea
                      value={challengeForm.description}
                      onChange={(e) => setChallengeForm({...challengeForm, description: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      rows={3}
                      placeholder="Challenge description"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Difficulty Level *</label>
                      <select
                        value={challengeForm.difficulty_level}
                        onChange={(e) => setChallengeForm({...challengeForm, difficulty_level: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      >
                        <option value="beginner">Beginner</option>
                        <option value="intermediate">Intermediate</option>
                        <option value="advanced">Advanced</option>
                        <option value="expert">Expert</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Prize Amount (₹)</label>
                      <input
                        type="number"
                        value={challengeForm.prize_amount}
                        onChange={(e) => setChallengeForm({...challengeForm, prize_amount: parseInt(e.target.value) || 0})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                        min="0"
                        placeholder="Prize money"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Start Date *</label>
                      <input
                        type="datetime-local"
                        value={challengeForm.start_date}
                        onChange={(e) => setChallengeForm({...challengeForm, start_date: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">End Date *</label>
                      <input
                        type="datetime-local"
                        value={challengeForm.end_date}
                        onChange={(e) => setChallengeForm({...challengeForm, end_date: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Registration Deadline *</label>
                      <input
                        type="datetime-local"
                        value={challengeForm.registration_deadline}
                        onChange={(e) => setChallengeForm({...challengeForm, registration_deadline: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Max Participants</label>
                    <input
                      type="number"
                      value={challengeForm.max_participants}
                      onChange={(e) => setChallengeForm({...challengeForm, max_participants: parseInt(e.target.value)})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      min="1"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Skills Required</label>
                    <input
                      type="text"
                      value={challengeForm.skills_required.join(', ')}
                      onChange={(e) => setChallengeForm({
                        ...challengeForm, 
                        skills_required: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                      })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="Enter skills separated by commas (e.g., JavaScript, React, Node.js)"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Completion Criteria</label>
                    <textarea
                      value={challengeForm.completion_criteria}
                      onChange={(e) => setChallengeForm({...challengeForm, completion_criteria: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      rows={3}
                      placeholder="What needs to be accomplished to complete this challenge?"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Resources & Guidelines</label>
                    <textarea
                      value={challengeForm.resources}
                      onChange={(e) => setChallengeForm({...challengeForm, resources: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      rows={2}
                      placeholder="Helpful resources, links, or additional guidelines"
                    />
                  </div>

                  <div className="flex space-x-4 pt-4">
                    <Button 
                      className="flex-1 bg-purple-600 hover:bg-purple-700"
                      onClick={handleCreateChallenge}
                      disabled={creatingChallenge || !challengeForm.title || !challengeForm.description}
                    >
                      {creatingChallenge ? 'Creating...' : 'Create Challenge'}
                    </Button>
                    <Button 
                      variant="outline"
                      className="flex-1"
                      onClick={() => setShowChallengeForm(false)}
                      disabled={creatingChallenge}
                    >
                      Cancel
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Request Review Modal */}
      {selectedRequest && (
        <Dialog open={showRequestModal} onOpenChange={setShowRequestModal}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Review Admin Request</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium">Applicant Information</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Name:</strong> {selectedRequest.full_name}</p>
                    <p><strong>Email:</strong> {selectedRequest.email}</p>
                    <p><strong>Phone:</strong> {selectedRequest.phone_number}</p>
                    <p><strong>College:</strong> {selectedRequest.college_name}</p>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium">Request Details</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Admin Type:</strong> {selectedRequest.admin_type}</p>
                    <p><strong>Status:</strong> {selectedRequest.status}</p>
                    <p><strong>Submitted:</strong> {new Date(selectedRequest.submitted_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">Motivation</h4>
                <p className="text-sm text-gray-600 p-3 bg-gray-50 rounded">{selectedRequest.motivation}</p>
              </div>
              
              {selectedRequest.previous_experience && (
                <div>
                  <h4 className="font-medium mb-2">Previous Experience</h4>
                  <p className="text-sm text-gray-600 p-3 bg-gray-50 rounded">{selectedRequest.previous_experience}</p>
                </div>
              )}
              
              <div className="space-y-4">
                <div className="flex space-x-4">
                  <Button
                    className="flex-1"
                    onClick={() => reviewAdminRequest(selectedRequest.id, 'approve')}
                    disabled={reviewing}
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Approve
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => reviewAdminRequest(selectedRequest.id, 'reject')}
                    disabled={reviewing}
                  >
                    <X className="w-4 h-4 mr-2" />
                    Reject
                  </Button>
                </div>
                
                <textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Add review notes..."
                  className="w-full p-3 border border-gray-300 rounded-md text-sm"
                  rows={3}
                />
                
                <textarea
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="Rejection reason (if rejecting)..."
                  className="w-full p-3 border border-gray-300 rounded-md text-sm"
                  rows={2}
                />
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default SuperAdminInterface;
