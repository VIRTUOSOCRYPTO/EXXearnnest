import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { CalendarDays, MapPin, Users, Award, Tag, Link, Globe, Building, Clock, ArrowLeft, Save } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const EditEvent = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
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

  useEffect(() => {
    fetchEventDetails();
  }, [id]);

  const fetchEventDetails = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/events/${id}`);
      const event = response.data.event;
      
      // Convert date strings to format suitable for datetime-local input
      const formatDateForInput = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toISOString().slice(0, 16);
      };

      setFormData({
        title: event.title || '',
        description: event.description || '',
        event_type: event.event_type || 'tech_talk',
        start_date: formatDateForInput(event.start_date),
        end_date: formatDateForInput(event.end_date),
        registration_deadline: formatDateForInput(event.registration_deadline),
        venue: event.venue || '',
        virtual_meeting_link: event.virtual_meeting_link || '',
        is_virtual: event.is_virtual || false,
        visibility: event.visibility || 'all_colleges',
        selected_colleges: event.selected_colleges || [],
        registration_enabled: event.registration_enabled !== undefined ? event.registration_enabled : true,
        max_participants: event.max_participants || 100,
        organizer_name: event.organizer_name || user?.name || '',
        organizer_contact: event.organizer_contact || user?.email || '',
        club_name: event.club_name || '',
        prizes: {
          first_prize: event.prizes?.first_prize || 0,
          second_prize: event.prizes?.second_prize || 0,
          third_prize: event.prizes?.third_prize || 0,
          participation_certificates: event.prizes?.participation_certificates !== undefined ? event.prizes.participation_certificates : true
        },
        tags: event.tags || [],
        attachments: event.attachments || []
      });
    } catch (error) {
      console.error('Error fetching event:', error);
      alert('Failed to load event details. You may not have permission to edit this event.');
      navigate('/my-events');
    } finally {
      setLoading(false);
    }
  };

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

    // Validation
    if (!formData.title.trim()) {
      alert('Please enter an event title');
      return;
    }

    if (!formData.description.trim()) {
      alert('Please enter an event description');
      return;
    }

    if (!formData.start_date || !formData.end_date) {
      alert('Please select start and end dates');
      return;
    }

    if (new Date(formData.end_date) < new Date(formData.start_date)) {
      alert('End date must be after start date');
      return;
    }

    if (!formData.is_virtual && !formData.venue.trim()) {
      alert('Please enter a venue or select virtual event');
      return;
    }

    try {
      setUpdating(true);
      await axios.put(`${API}/events/${id}`, formData);
      alert('Event updated successfully!');
      navigate('/my-events');
    } catch (error) {
      console.error('Update error:', error);
      alert(error.response?.data?.detail || 'Failed to update event. Please try again.');
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading event details...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate('/my-events')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to My Events
          </Button>
          
          <div className="flex items-center gap-3 mb-4">
            <CalendarDays className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-800">Edit Event</h1>
          </div>
          <p className="text-gray-600">Update your event details and save changes.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Event Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Event Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter event title"
                  required
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  rows="4"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Describe your event..."
                  required
                />
              </div>

              {/* Event Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Event Type <span className="text-red-500">*</span>
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {eventTypes.map((type) => (
                    <div
                      key={type.value}
                      onClick={() => handleInputChange('event_type', type.value)}
                      className={`p-3 border-2 rounded-lg cursor-pointer transition-all ${
                        formData.event_type === type.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-300'
                      }`}
                    >
                      <div className="text-2xl mb-1">{type.icon}</div>
                      <div className="text-sm font-medium">{type.label}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Club Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Club/Organization
                </label>
                <select
                  value={formData.club_name}
                  onChange={(e) => handleInputChange('club_name', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select Club</option>
                  {clubs.map((club) => (
                    <option key={club} value={club}>{club}</option>
                  ))}
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Date & Time */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Date & Time
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date & Time <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.start_date}
                    onChange={(e) => handleInputChange('start_date', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Date & Time <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.end_date}
                    onChange={(e) => handleInputChange('end_date', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Registration Deadline
                </label>
                <input
                  type="datetime-local"
                  value={formData.registration_deadline}
                  onChange={(e) => handleInputChange('registration_deadline', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </CardContent>
          </Card>

          {/* Venue */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="w-5 h-5" />
                Venue Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <input
                  type="checkbox"
                  id="is_virtual"
                  checked={formData.is_virtual}
                  onChange={(e) => handleInputChange('is_virtual', e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="is_virtual" className="text-sm font-medium text-gray-700">
                  This is a virtual event
                </label>
              </div>

              {!formData.is_virtual && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Venue <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.venue}
                    onChange={(e) => handleInputChange('venue', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter venue location"
                    required={!formData.is_virtual}
                  />
                </div>
              )}

              {formData.is_virtual && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Virtual Meeting Link
                  </label>
                  <input
                    type="url"
                    value={formData.virtual_meeting_link}
                    onChange={(e) => handleInputChange('virtual_meeting_link', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="https://meet.google.com/..."
                  />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Registration Settings */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Registration Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="registration_enabled"
                  checked={formData.registration_enabled}
                  onChange={(e) => handleInputChange('registration_enabled', e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="registration_enabled" className="text-sm font-medium text-gray-700">
                  Enable online registration
                </label>
              </div>

              {formData.registration_enabled && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Maximum Participants
                  </label>
                  <input
                    type="number"
                    value={formData.max_participants}
                    onChange={(e) => handleInputChange('max_participants', parseInt(e.target.value))}
                    min="1"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              )}

              {/* Visibility */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Event Visibility
                </label>
                <div className="space-y-3">
                  {visibilityOptions.map((option) => {
                    const Icon = option.icon;
                    return (
                      <div
                        key={option.value}
                        onClick={() => handleInputChange('visibility', option.value)}
                        className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                          formData.visibility === option.value
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-blue-300'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <Icon className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                          <div>
                            <div className="font-medium text-gray-900">{option.label}</div>
                            <div className="text-sm text-gray-600 mt-1">{option.description}</div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Prizes */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="w-5 h-5" />
                Prizes & Recognition
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    First Prize (₹)
                  </label>
                  <input
                    type="number"
                    value={formData.prizes.first_prize}
                    onChange={(e) => handleInputChange('prizes.first_prize', parseInt(e.target.value) || 0)}
                    min="0"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Second Prize (₹)
                  </label>
                  <input
                    type="number"
                    value={formData.prizes.second_prize}
                    onChange={(e) => handleInputChange('prizes.second_prize', parseInt(e.target.value) || 0)}
                    min="0"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Third Prize (₹)
                  </label>
                  <input
                    type="number"
                    value={formData.prizes.third_prize}
                    onChange={(e) => handleInputChange('prizes.third_prize', parseInt(e.target.value) || 0)}
                    min="0"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="participation_certificates"
                  checked={formData.prizes.participation_certificates}
                  onChange={(e) => handleInputChange('prizes.participation_certificates', e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="participation_certificates" className="text-sm font-medium text-gray-700">
                  Provide participation certificates
                </label>
              </div>
            </CardContent>
          </Card>

          {/* Tags */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Tag className="w-5 h-5" />
                Tags
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-3">
                <input
                  type="text"
                  placeholder="Add tags (press Enter)"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleTagAdd(e.target.value);
                      e.target.value = '';
                    }
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="flex flex-wrap gap-2">
                {formData.tags.map((tag, index) => (
                  <Badge key={index} variant="secondary" className="px-3 py-1">
                    {tag}
                    <button
                      type="button"
                      onClick={() => handleTagRemove(tag)}
                      className="ml-2 text-gray-500 hover:text-gray-700"
                    >
                      ×
                    </button>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Submit Button */}
          <div className="flex gap-3 justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/my-events')}
              disabled={updating}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={updating}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Save className="w-4 h-4 mr-2" />
              {updating ? 'Updating...' : 'Update Event'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditEvent;
