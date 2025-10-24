import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Users, Filter, Download, CheckCircle, XCircle, Clock, 
  Search, Calendar, Building, Award, Trophy, User, Eye, Phone, 
  Mail, Hash, GraduationCap, MapPin, FileText, IdCard
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const RegistrationManagement = ({ eventId, eventType, eventTitle }) => {
  const { user } = useAuth();
  const [registrations, setRegistrations] = useState([]);
  const [filteredRegistrations, setFilteredRegistrations] = useState([]);
  const [collegeStats, setCollegeStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedCollege, setSelectedCollege] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [approvalModal, setApprovalModal] = useState({ open: false, registration: null, action: null });
  const [rejectionReason, setRejectionReason] = useState('');
  const [detailsModal, setDetailsModal] = useState({ open: false, registration: null });
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrevious, setHasPrevious] = useState(false);
  const [statusCounts, setStatusCounts] = useState({ pending: 0, approved: 0, rejected: 0 });
  const itemsPerPage = 50;

  useEffect(() => {
    if (eventId && eventType) {
      fetchRegistrations();
    }
  }, [eventId, eventType, currentPage, selectedCollege, selectedStatus, selectedType]);

  useEffect(() => {
    // Reset to page 1 when filters change
    if (currentPage !== 1) {
      setCurrentPage(1);
    }
  }, [selectedCollege, selectedStatus, selectedType, searchTerm]);
  
  useEffect(() => {
    // Apply search filter when search term or registrations change
    applySearchFilter(registrations);
  }, [searchTerm, registrations]);

  const fetchRegistrations = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Build query params
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: itemsPerPage.toString()
      });
      
      if (selectedCollege !== 'all') params.append('college', selectedCollege);
      if (selectedStatus !== 'all') params.append('status', selectedStatus);
      if (selectedType !== 'all') params.append('registration_type', selectedType);
      
      // Use super-admin endpoint if user is super admin, otherwise use club-admin endpoint
      const endpoint = user?.admin_level === 'super_admin' ? 'super-admin' : 'club-admin';
      
      const response = await axios.get(`${API}/${endpoint}/registrations/${eventType}/${eventId}?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setRegistrations(response.data.registrations || []);
      setCollegeStats(response.data.college_statistics || {});
      setTotalCount(response.data.total_count || 0);
      setTotalPages(response.data.total_pages || 1);
      setHasNext(response.data.has_next || false);
      setHasPrevious(response.data.has_previous || false);
      setStatusCounts(response.data.status_counts || { pending: 0, approved: 0, rejected: 0 });
      
      // Apply client-side search filter
      applySearchFilter(response.data.registrations || []);
    } catch (error) {
      console.error('Error fetching registrations:', error);
      alert('Failed to fetch registrations. Please check your permissions.');
    } finally {
      setLoading(false);
    }
  };

  const applySearchFilter = (regs) => {
    if (!searchTerm) {
      setFilteredRegistrations(regs);
      return;
    }
    
    const filtered = regs.filter(reg => 
      (reg.full_name || reg.user_name || reg.team_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (reg.email || reg.user_email || reg.team_leader_email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (reg.phone || reg.user_phone || reg.team_leader_phone || '').toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    setFilteredRegistrations(filtered);
  };

  const handleApproveReject = async (registration, action) => {
    if (action === 'reject' && !rejectionReason.trim()) {
      alert('Please provide a reason for rejection');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const requestData = {
        registration_id: registration.id,
        action: action,
        reason: action === 'reject' ? rejectionReason : undefined
      };

      // Use super-admin endpoint if user is super admin, otherwise use club-admin endpoint
      const endpoint = user?.admin_level === 'super_admin' ? 'super-admin' : 'club-admin';

      await axios.post(`${API}/${endpoint}/registrations/${eventType}/approve-reject`, requestData, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      // Update local state
      setRegistrations(prev => prev.map(reg => 
        reg.id === registration.id 
          ? { ...reg, status: action === 'approve' ? 'approved' : 'rejected', rejection_reason: rejectionReason }
          : reg
      ));

      setApprovalModal({ open: false, registration: null, action: null });
      setRejectionReason('');
      
      alert(`Registration ${action === 'approve' ? 'approved' : 'rejected'} successfully`);
    } catch (error) {
      console.error('Error processing registration:', error);
      alert('Failed to process registration. Please try again.');
    }
  };

  const exportRegistrations = async (format = 'csv') => {
    try {
      const token = localStorage.getItem('token');
      
      // Build query params to get ALL registrations for export (not paginated)
      const params = new URLSearchParams({
        format: format
      });
      
      if (selectedCollege !== 'all') params.append('college', selectedCollege);
      if (selectedStatus !== 'all') params.append('status', selectedStatus);
      if (selectedType !== 'all') params.append('registration_type', selectedType);
      
      // Use super-admin endpoint if user is super admin, otherwise use club-admin endpoint
      const endpoint = user?.admin_level === 'super_admin' ? 'super-admin' : 'club-admin';
      
      const response = await axios.get(`${API}/${endpoint}/registrations/${eventType}/${eventId}/export?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data.download_url) {
        // Open the download URL in a new tab
        window.open(response.data.download_url, '_blank');
        alert(`Export successful! ${response.data.total_registrations} registrations exported to ${format.toUpperCase()}.`);
      } else {
        alert(`Export successful! ${response.data.total_registrations} registrations exported.`);
      }
    } catch (error) {
      console.error('Error exporting registrations:', error);
      alert('Failed to export registrations. Please try again.');
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { color: 'bg-yellow-500', icon: Clock },
      approved: { color: 'bg-green-500', icon: CheckCircle },
      rejected: { color: 'bg-red-500', icon: XCircle }
    };

    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <Badge className={`${config.color} text-white`}>
        <Icon className="w-3 h-3 mr-1" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const getTypeIcon = (type) => {
    return type === 'group' ? <Users className="w-4 h-4" /> : <User className="w-4 h-4" />;
  };

  if (loading) {
    return (
      <Card className="w-full max-w-7xl mx-auto">
        <CardContent className="p-8">
          <div className="flex items-center justify-center space-x-4">
            <Clock className="w-6 h-6 animate-spin" />
            <span className="text-gray-600">Loading registrations...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Users className="w-6 h-6" />
              <div>
                <h1 className="text-2xl font-bold">Registration Management</h1>
                <p className="text-gray-600 text-sm">{eventTitle}</p>
              </div>
            </div>
            <Button onClick={exportRegistrations} className="bg-green-600 hover:bg-green-700">
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
          </CardTitle>
        </CardHeader>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-blue-600">{totalCount}</div>
            <div className="text-sm text-gray-600">Total Registrations</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-yellow-600">
              {statusCounts.pending}
            </div>
            <div className="text-sm text-gray-600">Pending</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-green-600">
              {statusCounts.approved}
            </div>
            <div className="text-sm text-gray-600">Approved</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-red-600">
              {statusCounts.rejected}
            </div>
            <div className="text-sm text-gray-600">Rejected</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex-1 min-w-60">
              <Input
                placeholder="Search by name, email, or Phone Number..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full"
              />
            </div>
            
            <Select value={selectedCollege} onValueChange={setSelectedCollege}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by College" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Colleges</SelectItem>
                {Object.keys(collegeStats).map(college => (
                  <SelectItem key={college} value={college}>
                    {college} ({collegeStats[college].total})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedStatus} onValueChange={setSelectedStatus}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>

            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="individual">Individual</SelectItem>
                <SelectItem value="group">Group</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* College Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building className="w-5 h-5" />
            College-wise Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(collegeStats).map(([college, stats]) => (
              <div key={college} className="p-4 border rounded-lg bg-gray-50">
                <h4 className="font-semibold text-lg mb-2">{college}</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Total:</span>
                    <span className="font-medium">{stats.total}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Individual:</span>
                    <span className="text-blue-600">{stats.individual}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Group:</span>
                    <span className="text-purple-600">{stats.group}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Approved:</span>
                    <span className="text-green-600">{stats.approved}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Registrations Table */}
      <Card>
        <CardHeader>
          <CardTitle>Registrations ({filteredRegistrations.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Type</th>
                  <th className="text-left p-3">Name/Team</th>
                  <th className="text-left p-3">Email</th>
                  <th className="text-left p-3">College</th>
                  <th className="text-left p-3">Phone Number</th>
                  <th className="text-left p-3">Status</th>
                  <th className="text-left p-3">Date</th>
                  <th className="text-left p-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRegistrations.map((registration) => (
                  <tr key={registration.id} className="border-b hover:bg-gray-50">
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        {getTypeIcon(registration.registration_type)}
                        <span className="capitalize">{registration.registration_type}</span>
                      </div>
                    </td>
                    <td className="p-3">
                      <div>
                        <div className="font-medium">
                          {registration.registration_type === 'group' 
                            ? registration.team_name 
                            : (registration.full_name || registration.user_name)
                          }
                        </div>
                        {registration.registration_type === 'group' && (
                          <div className="text-sm text-gray-600">
                            Leader: {registration.team_leader_name}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="p-3">
                      {registration.email || registration.user_email || registration.team_leader_email}
                    </td>
                    <td className="p-3">
                      {registration.college || registration.user_college || registration.campus_name}
                    </td>
                    <td className="p-3">
                      {registration.phone || registration.user_phone || registration.team_leader_phone || 'N/A'}
                    </td>
                    <td className="p-3">
                      {getStatusBadge(registration.status)}
                      {registration.rejection_reason && (
                        <div className="text-xs text-red-600 mt-1">
                          {registration.rejection_reason}
                        </div>
                      )}
                    </td>
                    <td className="p-3 text-sm">
                      {new Date(registration.registration_date).toLocaleDateString()}
                    </td>
                    <td className="p-3">
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setDetailsModal({ open: true, registration })}
                          className="border-blue-500 text-blue-600 hover:bg-blue-50"
                        >
                          <Eye className="w-3 h-3 mr-1" />
                          View Details
                        </Button>
                        {registration.status === 'pending' && (
                          <>
                            <Button
                              size="sm"
                              onClick={() => setApprovalModal({ open: true, registration, action: 'approve' })}
                              className="bg-green-600 hover:bg-green-700"
                            >
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setApprovalModal({ open: true, registration, action: 'reject' })}
                              className="border-red-500 text-red-600 hover:bg-red-50"
                            >
                              <XCircle className="w-3 h-3 mr-1" />
                              Reject
                            </Button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredRegistrations.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No registrations found matching the current filters.
              </div>
            )}
          </div>
          
          {/* Pagination Controls */}
          {totalCount > 0 && (
            <div className="mt-6 flex items-center justify-between border-t pt-4">
              <div className="text-sm text-gray-600">
                Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, totalCount)} of {totalCount} registrations
              </div>
              
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={!hasPrevious}
                  className="disabled:opacity-50"
                >
                  Previous
                </Button>
                
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    
                    return (
                      <Button
                        key={pageNum}
                        variant={currentPage === pageNum ? "default" : "outline"}
                        size="sm"
                        onClick={() => setCurrentPage(pageNum)}
                        className={currentPage === pageNum ? "bg-blue-600" : ""}
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={!hasNext}
                  className="disabled:opacity-50"
                >
                  Next
                </Button>
              </div>
              
              <div className="text-sm text-gray-600">
                Page {currentPage} of {totalPages}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Approval/Rejection Modal */}
      <Dialog open={approvalModal.open} onOpenChange={(open) => !open && setApprovalModal({ open: false, registration: null, action: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {approvalModal.action === 'approve' ? 'Approve Registration' : 'Reject Registration'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {approvalModal.registration && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium mb-2">Registration Details:</h4>
                <div className="space-y-1 text-sm">
                  <div><strong>Name:</strong> {
                    approvalModal.registration.registration_type === 'group' 
                      ? `${approvalModal.registration.team_name} (${approvalModal.registration.team_leader_name})`
                      : (approvalModal.registration.full_name || approvalModal.registration.user_name)
                  }</div>
                  <div><strong>Email:</strong> {approvalModal.registration.email || approvalModal.registration.user_email || approvalModal.registration.team_leader_email}</div>
                  <div><strong>College:</strong> {approvalModal.registration.college || approvalModal.registration.user_college}</div>
                </div>
              </div>
            )}

            {approvalModal.action === 'reject' && (
              <div>
                <label className="block text-sm font-medium mb-2">Rejection Reason *</label>
                <Input
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="Please provide a reason for rejection..."
                  className="w-full"
                />
              </div>
            )}

            <div className="flex gap-3 pt-4">
              <Button
                onClick={() => handleApproveReject(approvalModal.registration, approvalModal.action)}
                className={approvalModal.action === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
              >
                {approvalModal.action === 'approve' ? 'Confirm Approval' : 'Confirm Rejection'}
              </Button>
              <Button
                variant="outline"
                onClick={() => setApprovalModal({ open: false, registration: null, action: null })}
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Registration Details Modal */}
      <Dialog open={detailsModal.open} onOpenChange={(open) => !open && setDetailsModal({ open: false, registration: null })}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Eye className="w-5 h-5" />
              Registration Details
            </DialogTitle>
          </DialogHeader>
          {detailsModal.registration && (
            <div className="space-y-6">
              {/* Status Badge */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <span className="text-sm text-gray-600">Registration Status</span>
                  <div className="mt-1">{getStatusBadge(detailsModal.registration.status)}</div>
                </div>
                <div className="text-right">
                  <span className="text-sm text-gray-600">Registration Date</span>
                  <div className="mt-1 font-medium">
                    {new Date(detailsModal.registration.registration_date).toLocaleDateString('en-IN', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </div>
                </div>
              </div>

              {/* Registration Type */}
              <div className="p-4 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  {getTypeIcon(detailsModal.registration.registration_type)}
                  <h3 className="font-semibold text-lg capitalize">
                    {detailsModal.registration.registration_type} Registration
                  </h3>
                </div>
              </div>

              {detailsModal.registration.registration_type === 'individual' ? (
                // Individual Registration Details
                <div className="space-y-4">
                  <h3 className="font-semibold text-lg border-b pb-2">Personal Information</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <User className="w-5 h-5 text-blue-600 mt-1" />
                      <div>
                        <div className="text-sm text-gray-600">Full Name</div>
                        <div className="font-medium">{detailsModal.registration.full_name || detailsModal.registration.user_name}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <Mail className="w-5 h-5 text-blue-600 mt-1" />
                      <div>
                        <div className="text-sm text-gray-600">Email</div>
                        <div className="font-medium break-all">{detailsModal.registration.email || detailsModal.registration.user_email}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <Phone className="w-5 h-5 text-blue-600 mt-1" />
                      <div>
                        <div className="text-sm text-gray-600">Phone Number</div>
                        <div className="font-medium">{detailsModal.registration.phone || detailsModal.registration.user_phone || 'N/A'}</div>
                      </div>
                    </div>
                  </div>

                  <h3 className="font-semibold text-lg border-b pb-2 mt-6">Academic Information</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <Building className="w-5 h-5 text-blue-600 mt-1" />
                      <div>
                        <div className="text-sm text-gray-600">College</div>
                        <div className="font-medium">{detailsModal.registration.college || detailsModal.registration.user_college}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <GraduationCap className="w-5 h-5 text-blue-600 mt-1" />
                      <div>
                        <div className="text-sm text-gray-600">Branch/Department</div>
                        <div className="font-medium">{detailsModal.registration.branch || detailsModal.registration.department || 'N/A'}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <Calendar className="w-5 h-5 text-blue-600 mt-1" />
                      <div>
                        <div className="text-sm text-gray-600">Semester</div>
                        <div className="font-medium">{detailsModal.registration.semester || 'N/A'}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <Calendar className="w-5 h-5 text-blue-600 mt-1" />
                      <div>
                        <div className="text-sm text-gray-600">Year</div>
                        <div className="font-medium">{detailsModal.registration.year || 'N/A'}</div>
                      </div>
                    </div>

                    {detailsModal.registration.section && (
                      <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                        <FileText className="w-5 h-5 text-blue-600 mt-1" />
                        <div>
                          <div className="text-sm text-gray-600">Section</div>
                          <div className="font-medium">{detailsModal.registration.section}</div>
                        </div>
                      </div>
                    )}

                    {detailsModal.registration.student_id_url && (
                      <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg col-span-2">
                        <IdCard className="w-5 h-5 text-blue-600 mt-1" />
                        <div className="flex-1">
                          <div className="text-sm text-gray-600">Student ID Card</div>
                          <a 
                            href={detailsModal.registration.student_id_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline font-medium"
                          >
                            View Document
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                // Group Registration Details
                <div className="space-y-4">
                  <h3 className="font-semibold text-lg border-b pb-2">Team Information</h3>
                  
                  <div className="flex items-start gap-3 p-4 bg-blue-50 border-2 border-blue-200 rounded-lg">
                    <Trophy className="w-6 h-6 text-blue-600 mt-1" />
                    <div>
                      <div className="text-sm text-gray-600">Team Name</div>
                      <div className="font-bold text-xl text-blue-900">{detailsModal.registration.team_name}</div>
                    </div>
                  </div>

                  <h3 className="font-semibold text-lg border-b pb-2 mt-6">Team Leader Information</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <User className="w-5 h-5 text-blue-600 mt-1" />
                      <div>
                        <div className="text-sm text-gray-600">Leader Name</div>
                        <div className="font-medium">{detailsModal.registration.team_leader_name}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <Mail className="w-5 h-5 text-blue-600 mt-1" />
                      <div>
                        <div className="text-sm text-gray-600">Leader Email</div>
                        <div className="font-medium break-all">{detailsModal.registration.team_leader_email}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <Phone className="w-5 h-5 text-blue-600 mt-1" />
                      <div>
                        <div className="text-sm text-gray-600">Leader Phone</div>
                        <div className="font-medium">{detailsModal.registration.team_leader_phone || 'N/A'}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <Hash className="w-5 h-5 text-blue-600 mt-1" />
                      <div>
                        <div className="text-sm text-gray-600">Leader USN</div>
                        <div className="font-medium">{detailsModal.registration.team_leader_usn || 'N/A'}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <Building className="w-5 h-5 text-blue-600 mt-1" />
                      <div>
                        <div className="text-sm text-gray-600">College</div>
                        <div className="font-medium">{detailsModal.registration.campus_name || detailsModal.registration.college}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <Users className="w-5 h-5 text-blue-600 mt-1" />
                      <div>
                        <div className="text-sm text-gray-600">Team Size</div>
                        <div className="font-medium">{detailsModal.registration.team_size || (detailsModal.registration.team_members?.length || 0)} members</div>
                      </div>
                    </div>
                  </div>

                  {detailsModal.registration.team_members && detailsModal.registration.team_members.length > 0 && (
                    <>
                      <h3 className="font-semibold text-lg border-b pb-2 mt-6">Team Members</h3>
                      <div className="space-y-3">
                        {detailsModal.registration.team_members.map((member, index) => (
                          <div key={index} className="p-4 border rounded-lg bg-gray-50">
                            <div className="flex items-center gap-2 mb-3">
                              <User className="w-4 h-4 text-gray-600" />
                              <span className="font-semibold">Member {index + 1}</span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                              <div>
                                <span className="text-gray-600">Name:</span>
                                <span className="ml-2 font-medium">{member.name || 'N/A'}</span>
                              </div>
                              <div>
                                <span className="text-gray-600">USN:</span>
                                <span className="ml-2 font-medium">{member.usn || 'N/A'}</span>
                              </div>
                              <div>
                                <span className="text-gray-600">Email:</span>
                                <span className="ml-2 font-medium break-all">{member.email || 'N/A'}</span>
                              </div>
                              <div>
                                <span className="text-gray-600">Phone:</span>
                                <span className="ml-2 font-medium">{member.phone || 'N/A'}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Rejection Reason if rejected */}
              {detailsModal.registration.rejection_reason && (
                <div className="p-4 bg-red-50 border-2 border-red-200 rounded-lg">
                  <div className="flex items-start gap-3">
                    <XCircle className="w-5 h-5 text-red-600 mt-1" />
                    <div>
                      <div className="text-sm font-semibold text-red-900">Rejection Reason</div>
                      <div className="text-sm text-red-800 mt-1">{detailsModal.registration.rejection_reason}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4 border-t">
                {detailsModal.registration.status === 'pending' && (
                  <>
                    <Button
                      onClick={() => {
                        setDetailsModal({ open: false, registration: null });
                        setApprovalModal({ open: true, registration: detailsModal.registration, action: 'approve' });
                      }}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Approve Registration
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setDetailsModal({ open: false, registration: null });
                        setApprovalModal({ open: true, registration: detailsModal.registration, action: 'reject' });
                      }}
                      className="border-red-500 text-red-600 hover:bg-red-50"
                    >
                      <XCircle className="w-4 h-4 mr-2" />
                      Reject Registration
                    </Button>
                  </>
                )}
                <Button
                  variant="outline"
                  onClick={() => setDetailsModal({ open: false, registration: null })}
                  className="ml-auto"
                >
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RegistrationManagement;
