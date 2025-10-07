import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Progress } from './ui/progress';
import { 
  Trophy, Users, Calendar, Award, Target, Medal, Star, 
  Upload, Mail, Shield, CheckCircle, AlertCircle, Clock,
  FileText, GraduationCap, Building, User
} from 'lucide-react';
import useWebSocket from '../hooks/useWebSocket';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CampusAdminRequest = () => {
  const { user } = useAuth();
  const [requestStatus, setRequestStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showRequestForm, setShowRequestForm] = useState(false);
  const [uploadingDocument, setUploadingDocument] = useState(false);
  const [statusUpdates, setStatusUpdates] = useState([]);
  
  // Real-time notifications for request status updates
  const { isConnected: wsConnected } = useWebSocket('notifications', {
    onMessage: (message) => {
      if (message.type === 'admin_request_status_update' || 
          message.type === 'admin_privileges_granted' ||
          message.type === 'document_uploaded' ||
          message.type === 'email_verification_update') {
        
        // Refresh request status
        fetchRequestStatus();
        
        // Add to status updates for display
        setStatusUpdates(prev => [message, ...prev].slice(0, 10));
        
        // Show immediate feedback to user
        if (message.title && message.message) {
          alert(message.title + '\n\n' + message.message);
        }
      }
    }
  });

  // Form data
  const [formData, setFormData] = useState({
    full_name: '',
    phone_number: '',
    college_name: '',
    institutional_email: '',
    club_name: '',
    club_type: 'student_organization',
    requested_admin_type: 'campus_admin',
    motivation: '',
    previous_experience: '',
    planned_activities: ''
  });

  // Email verification state
  const [emailVerificationResult, setEmailVerificationResult] = useState(null);
  const [verifyingEmail, setVerifyingEmail] = useState(false);

  useEffect(() => {
    fetchRequestStatus();
  }, []);

  const fetchRequestStatus = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/admin/campus/request/status`);
      setRequestStatus(response.data);
    } catch (error) {
      console.error('Error fetching request status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const verifyInstitutionalEmail = async () => {
    if (!formData.institutional_email) {
      alert('Please enter your institutional email first');
      return;
    }

    try {
      setVerifyingEmail(true);
      const response = await axios.post(`${API}/admin/campus/verify-email/${requestStatus?.request?.id}`, {});
      setEmailVerificationResult(response.data);
      
      if (response.data.auto_approved) {
        alert('Congratulations! Your request has been auto-approved based on your verified institutional email.');
        fetchRequestStatus();
      }
    } catch (error) {
      console.error('Email verification error:', error);
      alert(error.response?.data?.detail || 'Failed to verify email');
    } finally {
      setVerifyingEmail(false);
    }
  };

  const submitAdminRequest = async () => {
    // Validate required fields
    if (!formData.full_name || !formData.college_name || !formData.motivation) {
      alert('Please fill in all required fields (Name, College, Motivation)');
      return;
    }

    if (formData.motivation.length < 50) {
      alert('Please provide a more detailed motivation (at least 50 characters)');
      return;
    }

    try {
      setSubmitting(true);
      const response = await axios.post(`${API}/admin/campus/request`, formData);
      
      alert('Admin request submitted successfully! You will receive an email notification about the review status.');
      setShowRequestForm(false);
      fetchRequestStatus();
      
    } catch (error) {
      console.error('Submit request error:', error);
      alert(error.response?.data?.detail || 'Failed to submit admin request');
    } finally {
      setSubmitting(false);
    }
  };

  const uploadDocument = async (documentType, file) => {
    if (!file) return;

    try {
      setUploadingDocument(true);
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        `${API}/admin/campus/upload-document/${requestStatus.request.id}?document_type=${documentType}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      alert(`${documentType.replace('_', ' ')} uploaded successfully!`);
      fetchRequestStatus(); // Refresh to show uploaded documents
      
    } catch (error) {
      console.error('Document upload error:', error);
      alert(error.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploadingDocument(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { color: 'bg-yellow-500', text: 'Pending Review', icon: Clock },
      under_review: { color: 'bg-blue-500', text: 'Under Review', icon: AlertCircle },
      approved: { color: 'bg-green-500', text: 'Approved', icon: CheckCircle },
      rejected: { color: 'bg-red-500', text: 'Rejected', icon: AlertCircle }
    };

    const config = statusConfig[status] || statusConfig.pending;
    const IconComponent = config.icon;

    return (
      <Badge className={`${config.color} text-white`}>
        <IconComponent className="w-4 h-4 mr-1" />
        {config.text}
      </Badge>
    );
  };

  const renderRequestForm = () => (
    <Dialog open={showRequestForm} onOpenChange={setShowRequestForm}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <Trophy className="w-6 h-6 mr-2 text-yellow-600" />
            Request Campus Admin Privileges
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Personal Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-lg">
                <User className="w-5 h-5 mr-2" />
                Personal Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Full Name *</label>
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleInputChange}
                    className="w-full p-3 border rounded-lg"
                    placeholder="Your full name"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Phone Number</label>
                  <input
                    type="tel"
                    name="phone_number"
                    value={formData.phone_number}
                    onChange={handleInputChange}
                    className="w-full p-3 border rounded-lg"
                    placeholder="+91 9876543210"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* College Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-lg">
                <GraduationCap className="w-5 h-5 mr-2" />
                College & Club Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">College Name *</label>
                  <input
                    type="text"
                    name="college_name"
                    value={formData.college_name}
                    onChange={handleInputChange}
                    className="w-full p-3 border rounded-lg"
                    placeholder="Your college/university name"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Institutional Email</label>
                  <input
                    type="email"
                    name="institutional_email"
                    value={formData.institutional_email}
                    onChange={handleInputChange}
                    className="w-full p-3 border rounded-lg"
                    placeholder="yourname@college.edu.in"
                  />
                  <p className="text-xs text-gray-600 mt-1">
                    Use your official college email for automatic verification
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Club Name (Optional)</label>
                  <input
                    type="text"
                    name="club_name"
                    value={formData.club_name}
                    onChange={handleInputChange}
                    className="w-full p-3 border rounded-lg"
                    placeholder="Student club or organization"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Club Type</label>
                  <select
                    name="club_type"
                    value={formData.club_type}
                    onChange={handleInputChange}
                    className="w-full p-3 border rounded-lg"
                  >
                    <option value="student_organization">Student Organization</option>
                    <option value="academic_society">Academic Society</option>
                    <option value="cultural_club">Cultural Club</option>
                    <option value="sports_club">Sports Club</option>
                    <option value="technical_club">Technical Club</option>
                    <option value="social_service">Social Service</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Requested Admin Type</label>
                <select
                  name="requested_admin_type"
                  value={formData.requested_admin_type}
                  onChange={handleInputChange}
                  className="w-full p-3 border rounded-lg"
                >
                  <option value="campus_admin">Campus Admin - Oversee college-wide competitions and manage club admins</option>
                  <option value="club_admin">Club Admin - Manage specific club competitions and activities</option>
                </select>
                <p className="text-xs text-gray-600 mt-1">
                  Note: Each college can have maximum 5 Campus Admins and 10 Club Admins. Choose the role that best fits your responsibilities.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Motivation & Experience */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-lg">
                <FileText className="w-5 h-5 mr-2" />
                Motivation & Experience
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Why do you want to become a Campus Admin? *
                </label>
                <textarea
                  name="motivation"
                  value={formData.motivation}
                  onChange={handleInputChange}
                  className="w-full p-3 border rounded-lg h-32"
                  placeholder="Explain your motivation, goals, and how you plan to contribute to the campus community... (minimum 50 characters)"
                  required
                />
                <p className="text-xs text-gray-600 mt-1">
                  {formData.motivation.length}/1000 characters (minimum 50 required)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Previous Experience (Optional)</label>
                <textarea
                  name="previous_experience"
                  value={formData.previous_experience}
                  onChange={handleInputChange}
                  className="w-full p-3 border rounded-lg h-24"
                  placeholder="Any previous leadership or organizational experience..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Planned Activities (Optional)</label>
                <textarea
                  name="planned_activities"
                  value={formData.planned_activities}
                  onChange={handleInputChange}
                  className="w-full p-3 border rounded-lg h-24"
                  placeholder="What competitions or activities do you plan to organize?"
                />
              </div>
            </CardContent>
          </Card>

          {/* Submit Button */}
          <div className="flex justify-end space-x-4">
            <Button 
              variant="outline" 
              onClick={() => setShowRequestForm(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button 
              onClick={submitAdminRequest}
              disabled={submitting}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {submitting ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Trophy className="w-4 h-4 mr-2" />
                  Submit Request
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );

  if (loading) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-8">
          <div className="flex items-center justify-center space-x-4">
            <Clock className="w-6 h-6 animate-spin" />
            <p>Loading admin request status...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // No request exists - show application form
  if (!requestStatus?.has_request) {
    return (
      <div className="w-full max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <Card className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
          <CardContent className="p-8">
            <div className="flex items-center mb-4">
              <Trophy className="w-8 h-8 mr-3" />
              <div>
                <h1 className="text-2xl font-bold">Campus Admin Program</h1>
                <p className="text-blue-100">Lead your college community in competitions and challenges</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Benefits */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center mb-3">
                <Building className="w-6 h-6 text-blue-600 mr-2" />
                <h3 className="font-semibold">Campus Leadership</h3>
              </div>
              <p className="text-gray-600">Organize and manage inter-college competitions for your campus community</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center mb-3">
                <Award className="w-6 h-6 text-green-600 mr-2" />
                <h3 className="font-semibold">Recognition & Rewards</h3>
              </div>
              <p className="text-gray-600">Earn reputation points and special recognition for your contributions</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center mb-3">
                <Users className="w-6 h-6 text-purple-600 mr-2" />
                <h3 className="font-semibold">Community Impact</h3>
              </div>
              <p className="text-gray-600">Build and strengthen connections across college communities</p>
            </CardContent>
          </Card>
        </div>

        {/* Application Process */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="w-6 h-6 mr-2 text-blue-600" />
              Application Process
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <h4 className="font-semibold mb-2">1. Submit Application</h4>
                <p className="text-sm text-gray-600">Fill out the admin request form with your details</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Mail className="w-6 h-6 text-green-600" />
                </div>
                <h4 className="font-semibold mb-2">2. Email Verification</h4>
                <p className="text-sm text-gray-600">Verify with institutional email or upload documents</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Shield className="w-6 h-6 text-yellow-600" />
                </div>
                <h4 className="font-semibold mb-2">3. Admin Review</h4>
                <p className="text-sm text-gray-600">System admin reviews and validates your request</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Trophy className="w-6 h-6 text-purple-600" />
                </div>
                <h4 className="font-semibold mb-2">4. Get Started</h4>
                <p className="text-sm text-gray-600">Receive admin privileges and start organizing</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Apply Button */}
        <Card>
          <CardContent className="p-6 text-center">
            <Button 
              onClick={() => setShowRequestForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-lg px-8 py-3"
            >
              <Trophy className="w-5 h-5 mr-2" />
              Apply for Campus Admin
            </Button>
            <p className="text-sm text-gray-600 mt-2">
              Ready to lead your campus community? Start your application today!
            </p>
          </CardContent>
        </Card>

        {/* Render the request form dialog */}
        {renderRequestForm()}
      </div>
    );
  }

  // Request exists - show status and management
  const request = requestStatus.request;
  
  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Status Header */}
      <Card className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <CardContent className="p-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold mb-2">Campus Admin Request</h1>
              <p className="text-blue-100">Request ID: {request.id}</p>
              {/* Real-time Status Indicator */}
              <div className="flex items-center mt-2 space-x-2">
                <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-red-400'}`} />
                <span className="text-blue-100 text-sm">
                  {wsConnected ? 'Live updates enabled' : 'Live updates offline'}
                </span>
              </div>
            </div>
            {getStatusBadge(request.status)}
          </div>
        </CardContent>
      </Card>

      {/* Request Details */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <FileText className="w-6 h-6 mr-2" />
            Request Details
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-2">Personal Information</h4>
              <div className="space-y-2 text-sm">
                <p><span className="font-medium">College:</span> {request.college_name}</p>
                <p><span className="font-medium">Admin Type:</span> {request.requested_admin_type.replace('_', ' ')}</p>
                {request.club_name && (
                  <p><span className="font-medium">Club:</span> {request.club_name}</p>
                )}
                <p><span className="font-medium">Submitted:</span> {new Date(request.submission_date).toLocaleDateString()}</p>
              </div>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Verification Status</h4>
              <div className="space-y-2 text-sm">
                <div className="flex items-center">
                  {request.email_verified ? (
                    <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-yellow-600 mr-2" />
                  )}
                  <span>Email Verification: {request.email_verified ? 'Verified' : 'Pending'}</span>
                </div>
                <div className="flex items-center">
                  <FileText className="w-4 h-4 text-blue-600 mr-2" />
                  <span>Documents Uploaded: {request.documents_uploaded}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Review Notes */}
          {request.review_notes && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2 text-blue-800">Review Notes</h4>
              <p className="text-blue-700">{request.review_notes}</p>
            </div>
          )}

          {/* Rejection Reason */}
          {request.rejection_reason && (
            <div className="bg-red-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2 text-red-800">Rejection Reason</h4>
              <p className="text-red-700">{request.rejection_reason}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Document Upload (if needed) */}
      {request.status === 'pending' && request.verification_method !== 'email' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Upload className="w-6 h-6 mr-2" />
              Document Upload
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-gray-600 mb-4">
              Please upload the required documents to complete your verification:
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* College ID Upload */}
              <div className="border-2 border-dashed border-gray-300 p-4 rounded-lg text-center">
                <FileText className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <h4 className="font-semibold mb-2">College ID</h4>
                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                  onChange={(e) => uploadDocument('college_id', e.target.files[0])}
                  className="hidden"
                  id="college-id-upload"
                />
                <label
                  htmlFor="college-id-upload"
                  className="cursor-pointer text-blue-600 hover:text-blue-800"
                >
                  {uploadingDocument ? 'Uploading...' : 'Upload College ID'}
                </label>
              </div>

              {/* Club Registration Upload */}
              <div className="border-2 border-dashed border-gray-300 p-4 rounded-lg text-center">
                <Building className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <h4 className="font-semibold mb-2">Club Registration</h4>
                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                  onChange={(e) => uploadDocument('club_registration', e.target.files[0])}
                  className="hidden"
                  id="club-reg-upload"
                />
                <label
                  htmlFor="club-reg-upload"
                  className="cursor-pointer text-blue-600 hover:text-blue-800"
                >
                  {uploadingDocument ? 'Uploading...' : 'Upload Certificate'}
                </label>
              </div>

              {/* Faculty Endorsement Upload */}
              <div className="border-2 border-dashed border-gray-300 p-4 rounded-lg text-center">
                <GraduationCap className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <h4 className="font-semibold mb-2">Faculty Endorsement</h4>
                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                  onChange={(e) => uploadDocument('faculty_endorsement', e.target.files[0])}
                  className="hidden"
                  id="faculty-endorsement-upload"
                />
                <label
                  htmlFor="faculty-endorsement-upload"
                  className="cursor-pointer text-blue-600 hover:text-blue-800"
                >
                  {uploadingDocument ? 'Uploading...' : 'Upload Letter (Optional)'}
                </label>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Admin Dashboard Link */}
      {requestStatus.is_admin && (
        <Card className="bg-green-50 border-green-200">
          <CardContent className="p-6 text-center">
            <Trophy className="w-12 h-12 text-green-600 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-green-800 mb-2">
              Congratulations! You are a Campus Admin
            </h3>
            <p className="text-green-700 mb-4">
              Admin Type: {requestStatus.admin_details?.admin_type?.replace('_', ' ')}
            </p>
            <Button 
              className="bg-green-600 hover:bg-green-700"
              onClick={() => window.location.href = '/campus-admin-dashboard'}
            >
              <Shield className="w-4 h-4 mr-2" />
              Go to Admin Dashboard
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CampusAdminRequest;
