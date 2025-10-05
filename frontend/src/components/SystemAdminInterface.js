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
  Activity, BarChart3, TrendingUp, AlertTriangle, Search
} from 'lucide-react';
import useAdminWebSocket from '../hooks/useAdminWebSocket';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SystemAdminInterface = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("requests");
  
  // Real-time notifications for admin requests
  const { isConnected: wsConnected } = useAdminWebSocket({
    onAdminRequestSubmitted: (message) => {
      // Auto-refresh admin requests when new request comes in
      fetchAdminRequests();
      
      // Show toast notification
      if (window.showToast) {
        window.showToast({
          type: 'info',
          title: 'New Admin Request',
          message: message.message
        });
      }
    },
    onConnect: () => console.log('System admin WebSocket connected'),
    onError: (error) => console.error('System admin WebSocket error:', error)
  });

  // Admin Requests State
  const [adminRequests, setAdminRequests] = useState([]);
  const [requestsLoading, setRequestsLoading] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [showRequestModal, setShowRequestModal] = useState(false);

  // Campus Admins State
  const [campusAdmins, setCampusAdmins] = useState([]);
  const [adminsLoading, setAdminsLoading] = useState(false);
  const [adminsSummary, setAdminsSummary] = useState(null);

  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logsSummary, setLogsSummary] = useState(null);

  // Review State
  const [reviewDecision, setReviewDecision] = useState('approve');
  const [reviewNotes, setReviewNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [reviewing, setReviewing] = useState(false);

  // Filters
  const [requestStatusFilter, setRequestStatusFilter] = useState('');
  const [adminStatusFilter, setAdminStatusFilter] = useState('');
  const [logSeverityFilter, setLogSeverityFilter] = useState('');

  useEffect(() => {
    checkSystemAdminAccess();
  }, []);

  useEffect(() => {
    if (activeTab === "requests") {
      fetchAdminRequests();
    } else if (activeTab === "admins") {
      fetchCampusAdmins();
    } else if (activeTab === "audit") {
      fetchAuditLogs();
    }
  }, [activeTab, requestStatusFilter, adminStatusFilter, logSeverityFilter]);

  const checkSystemAdminAccess = async () => {
    try {
      // Try to fetch admin requests - this will fail if not system admin
      await axios.get(`${API}/system-admin/requests?limit=1`);
      setLoading(false);
    } catch (error) {
      console.error('System admin access check failed:', error);
      if (error.response?.status === 403) {
        alert('You do not have system administrator privileges.');
      }
      setLoading(false);
    }
  };

  const fetchAdminRequests = async () => {
    try {
      setRequestsLoading(true);
      const params = new URLSearchParams();
      if (requestStatusFilter) params.append('status', requestStatusFilter);
      
      const response = await axios.get(`${API}/system-admin/requests?${params}`);
      setAdminRequests(response.data.requests || []);
    } catch (error) {
      console.error('Error fetching admin requests:', error);
    } finally {
      setRequestsLoading(false);
    }
  };

  const fetchCampusAdmins = async () => {
    try {
      setAdminsLoading(true);
      const params = new URLSearchParams();
      if (adminStatusFilter) params.append('status', adminStatusFilter);
      
      const response = await axios.get(`${API}/system-admin/admins?${params}`);
      setCampusAdmins(response.data.admins || []);
      setAdminsSummary(response.data.summary);
    } catch (error) {
      console.error('Error fetching campus admins:', error);
    } finally {
      setAdminsLoading(false);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      setLogsLoading(true);
      const params = new URLSearchParams();
      if (logSeverityFilter) params.append('severity', logSeverityFilter);
      
      const response = await axios.get(`${API}/system-admin/audit-logs?${params}`);
      setAuditLogs(response.data.audit_logs || []);
      setLogsSummary(response.data.summary);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    } finally {
      setLogsLoading(false);
    }
  };

  const reviewAdminRequest = async () => {
    if (!selectedRequest) return;

    if (reviewDecision === 'reject' && !rejectionReason.trim()) {
      alert('Please provide a rejection reason');
      return;
    }

    try {
      setReviewing(true);
      
      const reviewData = {
        decision: reviewDecision,
        review_notes: reviewNotes,
        rejection_reason: reviewDecision === 'reject' ? rejectionReason : undefined,
        can_create_inter_college: reviewDecision === 'approve' ? selectedRequest.requested_admin_type === 'college_admin' : false,
        max_competitions_per_month: reviewDecision === 'approve' ? (selectedRequest.requested_admin_type === 'college_admin' ? 10 : 5) : undefined,
        expires_in_months: 12
      };

      await axios.post(`${API}/system-admin/requests/${selectedRequest.id}/review`, reviewData);
      
      alert(`Admin request ${reviewDecision}d successfully!`);
      setShowRequestModal(false);
      setSelectedRequest(null);
      setReviewNotes('');
      setRejectionReason('');
      fetchAdminRequests();
      
    } catch (error) {
      console.error('Review error:', error);
      alert(error.response?.data?.detail || 'Failed to review request');
    } finally {
      setReviewing(false);
    }
  };

  const updateAdminPrivileges = async (adminId, action, reason) => {
    try {
      await axios.put(`${API}/system-admin/admins/${adminId}/privileges`, {
        admin_id: adminId,
        action: action,
        reason: reason
      });
      
      alert(`Admin privileges ${action}d successfully!`);
      fetchCampusAdmins();
      
    } catch (error) {
      console.error('Update privileges error:', error);
      alert(error.response?.data?.detail || 'Failed to update privileges');
    }
  };

  const getStatusBadge = (status, type = 'request') => {
    const configs = {
      request: {
        pending: { color: 'bg-yellow-500', text: 'Pending', icon: Clock },
        under_review: { color: 'bg-blue-500', text: 'Under Review', icon: Eye },
        approved: { color: 'bg-green-500', text: 'Approved', icon: CheckCircle },
        rejected: { color: 'bg-red-500', text: 'Rejected', icon: X }
      },
      admin: {
        active: { color: 'bg-green-500', text: 'Active', icon: CheckCircle },
        suspended: { color: 'bg-yellow-500', text: 'Suspended', icon: AlertCircle },
        revoked: { color: 'bg-red-500', text: 'Revoked', icon: X }
      },
      severity: {
        info: { color: 'bg-blue-500', text: 'Info', icon: AlertCircle },
        warning: { color: 'bg-yellow-500', text: 'Warning', icon: AlertTriangle },
        error: { color: 'bg-red-500', text: 'Error', icon: X },
        critical: { color: 'bg-red-800', text: 'Critical', icon: AlertTriangle }
      }
    };

    const config = configs[type][status] || configs[type]['pending'];
    const IconComponent = config.icon;

    return (
      <Badge className={`${config.color} text-white`}>
        <IconComponent className="w-3 h-3 mr-1" />
        {config.text}
      </Badge>
    );
  };

  const renderAdminRequests = () => (
    <div className="space-y-6">
      {/* Filter Controls */}
      <Card>
        <CardContent className="p-4">
          <div className="flex space-x-4">
            <select 
              value={requestStatusFilter}
              onChange={(e) => setRequestStatusFilter(e.target.value)}
              className="px-3 py-2 border rounded-lg"
            >
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="under_review">Under Review</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
            <Button 
              variant="outline" 
              onClick={fetchAdminRequests}
              disabled={requestsLoading}
            >
              <Search className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Requests List */}
      {requestsLoading ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Clock className="w-8 h-8 animate-spin mx-auto mb-4" />
            <p>Loading admin requests...</p>
          </CardContent>
        </Card>
      ) : adminRequests.length > 0 ? (
        <div className="grid grid-cols-1 gap-4">
          {adminRequests.map((request) => (
            <Card key={request.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="font-semibold">{request.full_name}</h3>
                      {getStatusBadge(request.status)}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                      <div className="space-y-1">
                        <p className="flex items-center">
                          <GraduationCap className="w-4 h-4 mr-1" />
                          {request.college_name}
                        </p>
                        <p className="flex items-center">
                          <Mail className="w-4 h-4 mr-1" />
                          {request.email}
                        </p>
                        {request.institutional_email && (
                          <p className="flex items-center">
                            <Shield className="w-4 h-4 mr-1" />
                            {request.institutional_email} 
                            {request.email_verified && <CheckCircle className="w-3 h-3 text-green-600 ml-1" />}
                          </p>
                        )}
                      </div>
                      
                      <div className="space-y-1">
                        <p className="flex items-center">
                          <User className="w-4 h-4 mr-1" />
                          {request.requested_admin_type.replace('_', ' ').toUpperCase()}
                        </p>
                        {request.club_name && (
                          <p className="flex items-center">
                            <Building className="w-4 h-4 mr-1" />
                            {request.club_name}
                          </p>
                        )}
                        <p className="flex items-center">
                          <Calendar className="w-4 h-4 mr-1" />
                          {new Date(request.submission_date).toLocaleDateString()}
                        </p>
                      </div>
                    </div>

                    {request.user_details && (
                      <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm">
                        <p><strong>User Stats:</strong> Active since {new Date(request.user_details.created_at).toLocaleDateString()}</p>
                        <p><strong>University:</strong> {request.user_details.university || 'Not specified'}</p>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex flex-col space-y-2 ml-4">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        setSelectedRequest(request);
                        setShowRequestModal(true);
                      }}
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      Review
                    </Button>
                    
                    {request.status === 'pending' && (
                      <>
                        <Button 
                          size="sm"
                          className="bg-green-600 hover:bg-green-700"
                          onClick={() => {
                            setSelectedRequest(request);
                            setReviewDecision('approve');
                            setShowRequestModal(true);
                          }}
                        >
                          <Check className="w-4 h-4 mr-1" />
                          Approve
                        </Button>
                        <Button 
                          size="sm"
                          variant="destructive"
                          onClick={() => {
                            setSelectedRequest(request);
                            setReviewDecision('reject');
                            setShowRequestModal(true);
                          }}
                        >
                          <X className="w-4 h-4 mr-1" />
                          Reject
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-8 text-center">
            <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No Admin Requests</h3>
            <p className="text-gray-500">No admin requests match the current filters</p>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderCampusAdmins = () => (
    <div className="space-y-6">
      {/* Summary Cards */}
      {adminsSummary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-green-600">{adminsSummary.total_active}</p>
              <p className="text-sm text-gray-600">Active Admins</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-yellow-600">{adminsSummary.total_suspended}</p>
              <p className="text-sm text-gray-600">Suspended</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-blue-600">{adminsSummary.club_admins}</p>
              <p className="text-sm text-gray-600">Club Admins</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-purple-600">{adminsSummary.college_admins}</p>
              <p className="text-sm text-gray-600">College Admins</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filter Controls */}
      <Card>
        <CardContent className="p-4">
          <div className="flex space-x-4">
            <select 
              value={adminStatusFilter}
              onChange={(e) => setAdminStatusFilter(e.target.value)}
              className="px-3 py-2 border rounded-lg"
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
              <option value="revoked">Revoked</option>
            </select>
            <Button 
              variant="outline" 
              onClick={fetchCampusAdmins}
              disabled={adminsLoading}
            >
              <Search className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Admins List */}
      {adminsLoading ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Clock className="w-8 h-8 animate-spin mx-auto mb-4" />
            <p>Loading campus admins...</p>
          </CardContent>
        </Card>
      ) : campusAdmins.length > 0 ? (
        <div className="grid grid-cols-1 gap-4">
          {campusAdmins.map((admin) => (
            <Card key={admin.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="font-semibold">{admin.user_details?.full_name || 'Unknown'}</h3>
                      {getStatusBadge(admin.status, 'admin')}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                      <div className="space-y-1">
                        <p className="flex items-center">
                          <GraduationCap className="w-4 h-4 mr-1" />
                          {admin.college_name}
                        </p>
                        <p className="flex items-center">
                          <User className="w-4 h-4 mr-1" />
                          {admin.admin_type.replace('_', ' ').toUpperCase()}
                        </p>
                        {admin.club_name && (
                          <p className="flex items-center">
                            <Building className="w-4 h-4 mr-1" />
                            {admin.club_name}
                          </p>
                        )}
                      </div>
                      
                      <div className="space-y-1">
                        <p className="flex items-center">
                          <Trophy className="w-4 h-4 mr-1" />
                          {admin.activity_metrics.total_competitions} competitions
                        </p>
                        <p className="flex items-center">
                          <Award className="w-4 h-4 mr-1" />
                          {admin.activity_metrics.total_challenges} challenges
                        </p>
                        <p className="flex items-center">
                          <Users className="w-4 h-4 mr-1" />
                          {admin.activity_metrics.participants_managed} participants
                        </p>
                      </div>
                    </div>

                    <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm">
                      <p><strong>Appointed:</strong> {new Date(admin.appointed_at).toLocaleDateString()}</p>
                      <p><strong>Days Active:</strong> {admin.activity_metrics.days_active}</p>
                      {admin.expires_at && (
                        <p><strong>Expires:</strong> {new Date(admin.expires_at).toLocaleDateString()}</p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex flex-col space-y-2 ml-4">
                    {admin.status === 'active' && (
                      <Button 
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          const reason = prompt('Reason for suspension:');
                          if (reason) updateAdminPrivileges(admin.id, 'suspend', reason);
                        }}
                      >
                        <Flag className="w-4 h-4 mr-1" />
                        Suspend
                      </Button>
                    )}
                    
                    {admin.status === 'suspended' && (
                      <Button 
                        size="sm"
                        className="bg-green-600 hover:bg-green-700"
                        onClick={() => {
                          const reason = prompt('Reason for reactivation:');
                          if (reason) updateAdminPrivileges(admin.id, 'reactivate', reason);
                        }}
                      >
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Reactivate
                      </Button>
                    )}
                    
                    <Button 
                      size="sm"
                      variant="destructive"
                      onClick={() => {
                        if (window.confirm('Are you sure you want to revoke admin privileges?')) {
                          const reason = prompt('Reason for revocation:');
                          if (reason) updateAdminPrivileges(admin.id, 'revoke', reason);
                        }
                      }}
                    >
                      <X className="w-4 h-4 mr-1" />
                      Revoke
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-8 text-center">
            <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No Campus Admins</h3>
            <p className="text-gray-500">No campus admins match the current filters</p>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderAuditLogs = () => (
    <div className="space-y-6">
      {/* Summary Cards */}
      {logsSummary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Object.entries(logsSummary.severity_counts).map(([severity, count]) => (
            <Card key={severity}>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold">{count}</p>
                <p className="text-sm text-gray-600 capitalize">{severity} Events</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Filter Controls */}
      <Card>
        <CardContent className="p-4">
          <div className="flex space-x-4">
            <select 
              value={logSeverityFilter}
              onChange={(e) => setLogSeverityFilter(e.target.value)}
              className="px-3 py-2 border rounded-lg"
            >
              <option value="">All Severity</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="critical">Critical</option>
            </select>
            <Button 
              variant="outline" 
              onClick={fetchAuditLogs}
              disabled={logsLoading}
            >
              <Search className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Logs List */}
      {logsLoading ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Clock className="w-8 h-8 animate-spin mx-auto mb-4" />
            <p>Loading audit logs...</p>
          </CardContent>
        </Card>
      ) : auditLogs.length > 0 ? (
        <div className="space-y-3">
          {auditLogs.map((log) => (
            <Card key={log.id} className="hover:shadow-sm transition-shadow">
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="font-medium">{log.action_description}</h4>
                      {getStatusBadge(log.severity, 'severity')}
                    </div>
                    
                    <div className="text-sm text-gray-600 space-y-1">
                      <p><strong>Action Type:</strong> {log.action_type}</p>
                      <p><strong>Admin:</strong> {log.admin_details?.full_name || 'System'}</p>
                      <p><strong>Target:</strong> {log.target_type} ({log.target_id})</p>
                      <p><strong>Time:</strong> {new Date(log.timestamp).toLocaleString()}</p>
                      {log.ip_address && <p><strong>IP:</strong> {log.ip_address}</p>}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-8 text-center">
            <Activity className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No Audit Logs</h3>
            <p className="text-gray-500">No audit logs match the current filters</p>
          </CardContent>
        </Card>
      )}
    </div>
  );

  if (loading) {
    return (
      <Card className="w-full max-w-6xl mx-auto">
        <CardContent className="p-8">
          <div className="flex items-center justify-center space-x-4">
            <Clock className="w-6 h-6 animate-spin" />
            <p>Loading system admin interface...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-r from-red-600 to-purple-600 text-white">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Shield className="w-8 h-8 mr-3" />
              <div>
                <h1 className="text-2xl font-bold">System Administrator</h1>
                <p className="text-red-100">Manage campus admin requests, privileges, and system audit</p>
              </div>
            </div>
            
            {/* Real-time Status */}
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-red-400'}`} />
              <span className="text-white text-sm">
                {wsConnected ? 'Live Updates' : 'Offline'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Interface */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="requests">Admin Requests</TabsTrigger>
          <TabsTrigger value="admins">Campus Admins</TabsTrigger>
          <TabsTrigger value="audit">Audit Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="requests">
          {renderAdminRequests()}
        </TabsContent>

        <TabsContent value="admins">
          {renderCampusAdmins()}
        </TabsContent>

        <TabsContent value="audit">
          {renderAuditLogs()}
        </TabsContent>
      </Tabs>

      {/* Review Request Modal */}
      <Dialog open={showRequestModal} onOpenChange={setShowRequestModal}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <FileText className="w-6 h-6 mr-2" />
              Review Admin Request
            </DialogTitle>
          </DialogHeader>

          {selectedRequest && (
            <div className="space-y-6">
              {/* Request Details */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Request Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p><strong>Name:</strong> {selectedRequest.full_name}</p>
                  <p><strong>College:</strong> {selectedRequest.college_name}</p>
                  <p><strong>Email:</strong> {selectedRequest.email}</p>
                  {selectedRequest.institutional_email && (
                    <p><strong>Institutional Email:</strong> {selectedRequest.institutional_email}</p>
                  )}
                  <p><strong>Admin Type:</strong> {selectedRequest.requested_admin_type.replace('_', ' ')}</p>
                  {selectedRequest.club_name && (
                    <p><strong>Club:</strong> {selectedRequest.club_name}</p>
                  )}
                  <p><strong>Submitted:</strong> {new Date(selectedRequest.submission_date).toLocaleString()}</p>
                </CardContent>
              </Card>

              {/* Review Form */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Review Decision</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Decision</label>
                    <select 
                      value={reviewDecision}
                      onChange={(e) => setReviewDecision(e.target.value)}
                      className="w-full p-3 border rounded-lg"
                    >
                      <option value="approve">Approve Request</option>
                      <option value="reject">Reject Request</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Review Notes</label>
                    <textarea
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      className="w-full p-3 border rounded-lg h-24"
                      placeholder="Add any notes about this decision..."
                    />
                  </div>

                  {reviewDecision === 'reject' && (
                    <div>
                      <label className="block text-sm font-medium mb-2">Rejection Reason *</label>
                      <textarea
                        value={rejectionReason}
                        onChange={(e) => setRejectionReason(e.target.value)}
                        className="w-full p-3 border rounded-lg h-24"
                        placeholder="Provide a clear reason for rejection..."
                        required
                      />
                    </div>
                  )}

                  <div className="flex justify-end space-x-4">
                    <Button 
                      variant="outline" 
                      onClick={() => setShowRequestModal(false)}
                      disabled={reviewing}
                    >
                      Cancel
                    </Button>
                    <Button 
                      onClick={reviewAdminRequest}
                      disabled={reviewing}
                      className={reviewDecision === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
                    >
                      {reviewing ? (
                        <>
                          <Clock className="w-4 h-4 mr-2 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>
                          {reviewDecision === 'approve' ? (
                            <Check className="w-4 h-4 mr-2" />
                          ) : (
                            <X className="w-4 h-4 mr-2" />
                          )}
                          {reviewDecision === 'approve' ? 'Approve' : 'Reject'} Request
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SystemAdminInterface;
