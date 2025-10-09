import React, { useState } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Plus, Trash2, Upload, User, Users } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const RegistrationModal = ({ open, onClose, eventId, eventType, eventTitle }) => {
  const [registrationType, setRegistrationType] = useState('individual');
  const [loading, setLoading] = useState(false);
  const [studentIdFile, setStudentIdFile] = useState(null);
  const [studentIdUrl, setStudentIdUrl] = useState('');
  
  // Individual registration state
  const [individualData, setIndividualData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    college: '',
    usn: '',
    semester: '',
    year: '',
    branch: '',
    section: ''
  });
  
  // Group registration state
  const [groupData, setGroupData] = useState({
    team_name: '',
    team_leader_name: '',
    team_leader_email: '',
    team_leader_phone: '',
    team_leader_usn: '',
    team_leader_semester: '',
    team_leader_year: '',
    team_leader_branch: '',
    team_size: 2,
    team_members: [
      { name: '', email: '', phone: '', usn: '', semester: '', year: '', branch: '' }
    ]
  });
  
  const handleIndividualChange = (field, value) => {
    setIndividualData(prev => ({ ...prev, [field]: value }));
  };
  
  const handleGroupChange = (field, value) => {
    setGroupData(prev => ({ ...prev, [field]: value }));
  };
  
  const handleMemberChange = (index, field, value) => {
    const newMembers = [...groupData.team_members];
    newMembers[index][field] = value;
    setGroupData(prev => ({ ...prev, team_members: newMembers }));
  };
  
  const addTeamMember = () => {
    if (groupData.team_members.length < 4) {  // Max 5 total including leader
      setGroupData(prev => ({
        ...prev,
        team_members: [...prev.team_members, { name: '', email: '', phone: '', usn: '', semester: '', year: '', branch: '' }],
        team_size: prev.team_size + 1
      }));
    }
  };
  
  const removeTeamMember = (index) => {
    if (groupData.team_members.length > 1) {
      const newMembers = groupData.team_members.filter((_, i) => i !== index);
      setGroupData(prev => ({
        ...prev,
        team_members: newMembers,
        team_size: prev.team_size - 1
      }));
    }
  };
  
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API}/upload/student-id`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setStudentIdUrl(response.data.file_url);
      setStudentIdFile(file);
      alert('Student ID uploaded successfully!');
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload student ID');
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      
      // Prepare registration data
      const registrationData = {
        registration_type: registrationType,
        ...(registrationType === 'individual' ? {
          ...individualData,
          student_id_card_url: studentIdUrl
        } : {
          ...groupData,
          college: individualData.college || groupData.team_leader_name
        })
      };
      
      // Determine endpoint based on event type
      let endpoint = '';
      if (eventType === 'college_event') {
        endpoint = `/college-events/${eventId}/register-detailed`;
      } else if (eventType === 'prize_challenge') {
        endpoint = `/prize-challenges/${eventId}/register-detailed`;
      } else if (eventType === 'inter_college') {
        endpoint = `/inter-college/competitions/${eventId}/register-detailed`;
      }
      
      const response = await axios.post(`${API}${endpoint}`, registrationData);
      
      alert(response.data.message || 'Registration submitted successfully!');
      onClose();
      window.location.reload(); // Refresh to show updated status
    } catch (error) {
      console.error('Registration error:', error);
      const errorMsg = error.response?.data?.detail || 'Registration failed';
      if (typeof errorMsg === 'object' && errorMsg.errors) {
        alert('Registration failed:\n' + errorMsg.errors.join('\n'));
      } else {
        alert(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">
            Register for {eventTitle}
          </DialogTitle>
        </DialogHeader>
        
        <Tabs value={registrationType} onValueChange={setRegistrationType}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="individual" className="flex items-center gap-2">
              <User className="w-4 h-4" />
              Individual
            </TabsTrigger>
            <TabsTrigger value="group" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Group
            </TabsTrigger>
          </TabsList>
          
          <form onSubmit={handleSubmit}>
            {/* Individual Registration */}
            <TabsContent value="individual" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Full Name *</Label>
                  <Input
                    value={individualData.full_name}
                    onChange={(e) => handleIndividualChange('full_name', e.target.value)}
                    required
                  />
                </div>
                <div>
                  <Label>Email *</Label>
                  <Input
                    type="email"
                    value={individualData.email}
                    onChange={(e) => handleIndividualChange('email', e.target.value)}
                    required
                  />
                </div>
                <div>
                  <Label>Phone Number *</Label>
                  <Input
                    type="tel"
                    value={individualData.phone_number}
                    onChange={(e) => handleIndividualChange('phone_number', e.target.value)}
                    required
                  />
                </div>
                <div>
                  <Label>USN/Roll Number *</Label>
                  <Input
                    value={individualData.usn}
                    onChange={(e) => handleIndividualChange('usn', e.target.value)}
                    required
                  />
                </div>
                <div>
                  <Label>College *</Label>
                  <Input
                    value={individualData.college}
                    onChange={(e) => handleIndividualChange('college', e.target.value)}
                    required
                  />
                </div>
                <div>
                  <Label>Branch/Department *</Label>
                  <Input
                    value={individualData.branch}
                    onChange={(e) => handleIndividualChange('branch', e.target.value)}
                    required
                  />
                </div>
                <div>
                  <Label>Section</Label>
                  <Input
                    value={individualData.section}
                    onChange={(e) => handleIndividualChange('section', e.target.value)}
                  />
                </div>
                <div>
                  <Label>Semester *</Label>
                  <Input
                    type="number"
                    min="1"
                    max="8"
                    value={individualData.semester}
                    onChange={(e) => handleIndividualChange('semester', parseInt(e.target.value))}
                    required
                  />
                </div>
                <div>
                  <Label>Year *</Label>
                  <Input
                    type="number"
                    min="1"
                    max="4"
                    value={individualData.year}
                    onChange={(e) => handleIndividualChange('year', parseInt(e.target.value))}
                    required
                  />
                </div>
              </div>
              
              {/* Student ID Upload */}
              <div className="space-y-2">
                <Label>Student ID Card (Optional)</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="file"
                    accept=".jpg,.jpeg,.png,.pdf"
                    onChange={handleFileUpload}
                    className="flex-1"
                  />
                  {studentIdFile && (
                    <span className="text-sm text-green-600">✓ Uploaded</span>
                  )}
                </div>
              </div>
            </TabsContent>
            
            {/* Group Registration */}
            <TabsContent value="group" className="space-y-6">
              {/* Team Info */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Team Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <Label>Team Name *</Label>
                    <Input
                      value={groupData.team_name}
                      onChange={(e) => handleGroupChange('team_name', e.target.value)}
                      required
                    />
                  </div>
                </div>
              </div>
              
              {/* Team Leader Info */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Team Leader Details</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Leader Name *</Label>
                    <Input
                      value={groupData.team_leader_name}
                      onChange={(e) => handleGroupChange('team_leader_name', e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <Label>Leader Email *</Label>
                    <Input
                      type="email"
                      value={groupData.team_leader_email}
                      onChange={(e) => handleGroupChange('team_leader_email', e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <Label>Leader Phone *</Label>
                    <Input
                      type="tel"
                      value={groupData.team_leader_phone}
                      onChange={(e) => handleGroupChange('team_leader_phone', e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <Label>Leader USN *</Label>
                    <Input
                      value={groupData.team_leader_usn}
                      onChange={(e) => handleGroupChange('team_leader_usn', e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <Label>Leader Branch *</Label>
                    <Input
                      value={groupData.team_leader_branch}
                      onChange={(e) => handleGroupChange('team_leader_branch', e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <Label>Leader Semester *</Label>
                    <Input
                      type="number"
                      min="1"
                      max="8"
                      value={groupData.team_leader_semester}
                      onChange={(e) => handleGroupChange('team_leader_semester', parseInt(e.target.value))}
                      required
                    />
                  </div>
                  <div>
                    <Label>Leader Year *</Label>
                    <Input
                      type="number"
                      min="1"
                      max="4"
                      value={groupData.team_leader_year}
                      onChange={(e) => handleGroupChange('team_leader_year', parseInt(e.target.value))}
                      required
                    />
                  </div>
                </div>
              </div>
              
              {/* Team Members */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="font-semibold text-lg">Team Members ({groupData.team_members.length})</h3>
                  {groupData.team_members.length < 4 && (
                    <Button type="button" onClick={addTeamMember} size="sm" variant="outline">
                      <Plus className="w-4 h-4 mr-2" />
                      Add Member
                    </Button>
                  )}
                </div>
                
                {groupData.team_members.map((member, index) => (
                  <div key={index} className="border rounded-lg p-4 space-y-3">
                    <div className="flex justify-between items-center">
                      <h4 className="font-medium">Member {index + 1}</h4>
                      {groupData.team_members.length > 1 && (
                        <Button
                          type="button"
                          onClick={() => removeTeamMember(index)}
                          size="sm"
                          variant="ghost"
                          className="text-red-600"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <Input
                        placeholder="Name *"
                        value={member.name}
                        onChange={(e) => handleMemberChange(index, 'name', e.target.value)}
                        required
                      />
                      <Input
                        placeholder="Email *"
                        type="email"
                        value={member.email}
                        onChange={(e) => handleMemberChange(index, 'email', e.target.value)}
                        required
                      />
                      <Input
                        placeholder="Phone *"
                        type="tel"
                        value={member.phone}
                        onChange={(e) => handleMemberChange(index, 'phone', e.target.value)}
                        required
                      />
                      <Input
                        placeholder="USN *"
                        value={member.usn}
                        onChange={(e) => handleMemberChange(index, 'usn', e.target.value)}
                        required
                      />
                      <Input
                        placeholder="Branch *"
                        value={member.branch}
                        onChange={(e) => handleMemberChange(index, 'branch', e.target.value)}
                        required
                      />
                      <Input
                        placeholder="Semester *"
                        type="number"
                        min="1"
                        max="8"
                        value={member.semester}
                        onChange={(e) => handleMemberChange(index, 'semester', parseInt(e.target.value))}
                        required
                      />
                      <Input
                        placeholder="Year *"
                        type="number"
                        min="1"
                        max="4"
                        value={member.year}
                        onChange={(e) => handleMemberChange(index, 'year', parseInt(e.target.value))}
                        required
                      />
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>
            
            <div className="flex justify-end gap-2 mt-6">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? 'Submitting...' : 'Submit Registration'}
              </Button>
            </div>
          </form>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

export default RegistrationModal;
