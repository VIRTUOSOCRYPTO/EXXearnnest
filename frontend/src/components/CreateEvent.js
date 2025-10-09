import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { CalendarDays, MapPin, Users, Award, Tag, Link, Globe, Building, Clock } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CreateEvent = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    event_type: 'tech_talk',
    start_date: '',
    end_date: '',
    registration_deadline: '',
    venue: '',
    virtual_meeting_link: '',
    is_virtual: false,
    visibility: 'all_colleges',
    selected_colleges: [],
    registration_enabled: true,
    max_participants: 100,
    organizer_name: user?.name || '',
    organizer_contact: user?.email || '',
    club_name: '',
    prizes: {
      first_prize: 0,
      second_prize: 0,
      third_prize: 0,
      participation_certificates: true
    },
    tags: [],
    attachments: []
  });

  const eventTypes = [
    { value: 'hackathon', label: 'Hackathon', icon: '💻', description: 'Coding competition' },
    { value: 'workshop', label: 'Workshop', icon: '🛠️', description: 'Hands-on learning session' },
    { value: 'coding_competition', label: 'Coding Competition', icon: '🏆', description: 'Programming contest' },
    { value: 'tech_talk', label: 'Tech Talk', icon: '🎙️', description: 'Technical presentation' },
    { value: 'seminar', label: 'Seminar', icon: '📚', description: 'Educational seminar' },
    { value: 'conference', label: 'Conference', icon: '🎯', description: 'Professional conference' },
    { value: 'club_meeting', label: 'Club Meeting', icon: '👥', description: 'Regular club activities' },
    { value: 'project_showcase', label: 'Project Showcase', icon: '📽️', description: 'Display student projects' }
  ];

  const clubs = [
    'IEEE Student Branch',
    'Photonics Society',
    'Robotics Club',
    'Computer Science Society',
    'Entrepreneurship Cell',
    'Drama Society',
    'Music Club',
    'Sports Committee',
    'Other'
  ];

  const visibilityOptions = [
    { value: 'college_only', label: 'My College Only', icon: Building, description: 'Only students from your college can see and register' },
    { value: 'all_colleges', label: 'All Colleges', icon: Globe, description: 'Open to students from all registered colleges' },
    { value: 'selected_colleges', label: 'Selected Colleges', icon: Users, description: 'Choose specific colleges to invite' }
  ];

  const handleInputChange = (field, value) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }
  };

  const handleTagAdd = (tag) => {
    if (tag && !formData.tags.includes(tag)) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tag.trim()]
      }));
    }
  };

  const handleTagRemove = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!user) {
      alert('Please log in to create events');
      return;
    }

    // Validate required fields
    if (!formData.title || !formData.description || !formData.start_date || !formData.end_date) {
      alert('Please fill in all required fields');
      return;
    }

    // Validate dates
    const startDate = new Date(formData.start_date);
    const endDate = new Date(formData.end_date);
    const regDeadline = formData.registration_deadline ? new Date(formData.registration_deadline) : null;

    if (startDate >= endDate) {
      alert('End date must be after start date');
      return;
    }

    if (regDeadline && regDeadline >= startDate) {
      alert('Registration deadline must be before event start date');
      return;
    }

    try {
      setCreating(true);
      
      const response = await axios.post(`${API}/college-events`, formData, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      alert('Event created successfully! 🎉');
      navigate('/events');
    } catch (error) {
      console.error('Error creating event:', error);
      alert(error.response?.data?.detail || 'Failed to create event');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <CalendarDays className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-800">Create College Event</h1>
        </div>
        <p className="text-gray-600 text-lg">
          Organize exciting events for students across colleges and universities
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarDays className="w-5 h-5" />
              Event Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Event Title *</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter a compelling event title"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Description *</label>
              <textarea
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                rows={4}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe your event in detail..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Event Type *</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {eventTypes.map((type) => (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => handleInputChange('event_type', type.value)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      formData.event_type === type.value
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-lg mb-1">{type.icon}</div>
                    <div className="font-medium text-sm">{type.label}</div>
                    <div className="text-xs text-gray-500">{type.description}</div>
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Schedule & Venue */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Schedule & Venue
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Start Date & Time *</label>
                <input
                  type="datetime-local"
                  value={formData.start_date}
                  onChange={(e) => handleInputChange('start_date', e.target.value)}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">End Date & Time *</label>
                <input
                  type="datetime-local"
                  value={formData.end_date}
                  onChange={(e) => handleInputChange('end_date', e.target.value)}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Registration Deadline</label>
                <input
                  type="datetime-local"
                  value={formData.registration_deadline}
                  onChange={(e) => handleInputChange('registration_deadline', e.target.value)}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="isVirtual"
                  checked={formData.is_virtual}
                  onChange={(e) => handleInputChange('is_virtual', e.target.checked)}
                  className="w-4 h-4 text-blue-600"
                />
                <label htmlFor="isVirtual" className="text-sm font-medium">Virtual Event</label>
              </div>

              {formData.is_virtual ? (
                <div>
                  <label className="block text-sm font-medium mb-2">Meeting Link</label>
                  <input
                    type="url"
                    value={formData.virtual_meeting_link}
                    onChange={(e) => handleInputChange('virtual_meeting_link', e.target.value)}
                    className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="https://zoom.us/j/123456789 or Google Meet link"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium mb-2">Venue Address</label>
                  <input
                    type="text"
                    value={formData.venue}
                    onChange={(e) => handleInputChange('venue', e.target.value)}
                    className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter the physical venue address"
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Visibility & Registration */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="w-5 h-5" />
              Visibility & Registration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-3">Event Visibility</label>
              <div className="space-y-3">
                {visibilityOptions.map((option) => (
                  <div
                    key={option.value}
                    className={`p-4 rounded-lg border cursor-pointer transition-all ${
                      formData.visibility === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleInputChange('visibility', option.value)}
                  >
                    <div className="flex items-center gap-3">
                      <input
                        type="radio"
                        name="visibility"
                        checked={formData.visibility === option.value}
                        onChange={() => handleInputChange('visibility', option.value)}
                        className="text-blue-600"
                      />
                      <option.icon className="w-5 h-5 text-blue-600" />
                      <div>
                        <div className="font-medium">{option.label}</div>
                        <div className="text-sm text-gray-500">{option.description}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="registrationEnabled"
                  checked={formData.registration_enabled}
                  onChange={(e) => handleInputChange('registration_enabled', e.target.checked)}
                  className="w-4 h-4 text-blue-600"
                />
                <label htmlFor="registrationEnabled" className="text-sm font-medium">Enable Registration</label>
              </div>

              {formData.registration_enabled && (
                <div>
                  <label className="block text-sm font-medium mb-2">Maximum Participants</label>
                  <input
                    type="number"
                    value={formData.max_participants}
                    onChange={(e) => handleInputChange('max_participants', parseInt(e.target.value) || 0)}
                    className="w-full md:w-48 p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="1"
                    max="10000"
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Organizer & Club Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Organizer Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Organizer Name</label>
                <input
                  type="text"
                  value={formData.organizer_name}
                  onChange={(e) => handleInputChange('organizer_name', e.target.value)}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Your name or organization"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Contact Information</label>
                <input
                  type="text"
                  value={formData.organizer_contact}
                  onChange={(e) => handleInputChange('organizer_contact', e.target.value)}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Email or phone number"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Club/Organization</label>
              <select
                value={formData.club_name}
                onChange={(e) => handleInputChange('club_name', e.target.value)}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select Club/Organization</option>
                {clubs.map((club) => (
                  <option key={club} value={club}>{club}</option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Prizes (Optional) */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="w-5 h-5" />
              Prizes & Recognition (Optional)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">First Prize (₹)</label>
                <input
                  type="number"
                  value={formData.prizes.first_prize}
                  onChange={(e) => handleInputChange('prizes.first_prize', parseInt(e.target.value) || 0)}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Second Prize (₹)</label>
                <input
                  type="number"
                  value={formData.prizes.second_prize}
                  onChange={(e) => handleInputChange('prizes.second_prize', parseInt(e.target.value) || 0)}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Third Prize (₹)</label>
                <input
                  type="number"
                  value={formData.prizes.third_prize}
                  onChange={(e) => handleInputChange('prizes.third_prize', parseInt(e.target.value) || 0)}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  min="0"
                />
              </div>
            </div>

            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="participationCertificates"
                checked={formData.prizes.participation_certificates}
                onChange={(e) => handleInputChange('prizes.participation_certificates', e.target.checked)}
                className="w-4 h-4 text-blue-600"
              />
              <label htmlFor="participationCertificates" className="text-sm font-medium">Participation Certificates</label>
            </div>
          </CardContent>
        </Card>

        {/* Tags */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Tag className="w-5 h-5" />
              Tags
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Add Tags (Press Enter to add)</label>
                <input
                  type="text"
                  placeholder="Type a tag and press Enter"
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleTagAdd(e.target.value);
                      e.target.value = '';
                    }
                  }}
                />
              </div>
              {formData.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map((tag, index) => (
                    <Badge
                      key={index}
                      variant="secondary"
                      className="cursor-pointer hover:bg-red-100"
                      onClick={() => handleTagRemove(tag)}
                    >
                      {tag} ×
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Submit Button */}
        <div className="flex gap-4">
          <Button
            type="submit"
            disabled={creating}
            className="flex-1 bg-blue-600 hover:bg-blue-700 py-3 text-lg"
          >
            {creating ? 'Creating Event...' : 'Create Event 🎉'}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/events')}
            className="px-8 py-3"
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
};

export default CreateEvent;
