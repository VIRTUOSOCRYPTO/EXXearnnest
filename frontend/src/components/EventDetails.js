import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import RegistrationModal from './RegistrationModal';
import { 
  CalendarDays, 
  MapPin, 
  Users, 
  Award, 
  Tag, 
  Clock, 
  Globe, 
  Building,
  Video,
  Mail,
  Phone,
  Link as LinkIcon,
  ArrowLeft,
  Edit,
  Trash2,
  UserCheck
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const EventDetails = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [registering, setRegistering] = useState(false);
  const [loadingParticipants, setLoadingParticipants] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [registrationModalOpen, setRegistrationModalOpen] = useState(false);

  const eventTypeIcons = {
    hackathon: '💻',
    workshop: '🛠️',
    coding_competition: '🏆',
    tech_talk: '🎙️',
    seminar: '📚',
    conference: '🎯',
    club_meeting: '👥',
    project_showcase: '📽️'
  };

  useEffect(() => {
    fetchEventDetails();
  }, [id]);

  const fetchEventDetails = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/college-events/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEvent(response.data);
    } catch (error) {
      console.error('Error fetching event details:', error);
      if (error.response?.status === 404) {
        navigate('/events');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchParticipants = async () => {
    try {
      setLoadingParticipants(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/college-events/${id}/participants`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setParticipants(response.data.participants || []);
    } catch (error) {
      console.error('Error fetching participants:', error);
      alert('Failed to load participants list');
    } finally {
      setLoadingParticipants(false);
    }
  };

  const registerForEvent = async () => {
    try {
      setRegistering(true);
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/college-events/${id}/register`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Update the event status locally
      setEvent(prev => ({ 
        ...prev, 
        is_registered: true, 
        registered_count: (prev.registered_count || 0) + 1 
      }));

      alert(`Successfully registered! ${response.data.message}`);
    } catch (error) {
      console.error('Registration error:', error);
      alert(error.response?.data?.detail || 'Failed to register for event');
    } finally {
      setRegistering(false);
    }
  };

  const deleteEvent = async () => {
    if (!window.confirm('Are you sure you want to delete this event? This action cannot be undone.')) {
      return;
    }

    try {
      setDeleting(true);
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/college-events/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('Event deleted successfully!');
      navigate('/events');
    } catch (error) {
      console.error('Delete error:', error);
      alert(error.response?.data?.detail || 'Failed to delete event');
    } finally {
      setDeleting(false);
    }
  };

  const canManageEvent = (event) => {
    return user && (
      event.creator_id === user.id || 
      user.is_admin || 
      user.is_super_admin ||
      user.admin_level === 'super_admin'
    );
  };

  const getEventStatusBadge = (event) => {
    const now = new Date();
    const startDate = new Date(event.start_date);
    const endDate = new Date(event.end_date);
    const regDeadline = event.registration_deadline ? new Date(event.registration_deadline) : null;
    
    // Check manual admin override first, default to true if not set
    // Using registration_required field (backend model field name)
    const registrationEnabled = event.registration_required !== undefined ? event.registration_required : true;

    if (now < startDate) {
      // Check if manually disabled by admin
      if (!registrationEnabled) {
        return <Badge variant="secondary">Registration Closed</Badge>;
      }
      // Check date-based registration status
      if (regDeadline && now <= regDeadline) {
        return <Badge className="bg-green-500">Registration Open</Badge>;
      } else if (regDeadline && now > regDeadline) {
        return <Badge variant="secondary">Registration Closed</Badge>;
      } else {
        // No deadline set, registration is open until event starts
        return <Badge className="bg-green-500">Registration Open</Badge>;
      }
    } else if (now >= startDate && now <= endDate) {
      return <Badge className="bg-orange-500">Ongoing</Badge>;
    } else {
      return <Badge variant="outline" className="bg-gray-100">Past Event</Badge>;
    }
  };

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-IN', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading event details...</p>
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="text-center py-12">
          <h3 className="text-xl font-semibold text-gray-600 mb-2">Event not found</h3>
          <p className="text-gray-500 mb-4">The event you're looking for doesn't exist.</p>
          <Button onClick={() => navigate('/events')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Events
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="outline"
          onClick={() => navigate('/events')}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Events
        </Button>

        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-3xl">{eventTypeIcons[event.event_type] || '📅'}</span>
              <h1 className="text-3xl font-bold text-gray-800">{event.title}</h1>
            </div>
            <div className="flex flex-wrap gap-2 mb-4">
              {getEventStatusBadge(event)}
              {event.is_registered && (
                <Badge className="bg-emerald-500">
                  <UserCheck className="w-3 h-3 mr-1" />
                  Registered
                </Badge>
              )}
              {event.visibility === 'all_colleges' && (
                <Badge variant="outline" className="bg-purple-50">
                  <Globe className="w-3 h-3 mr-1" />
                  All Colleges
                </Badge>
              )}
            </div>
          </div>

          {/* Action buttons for creators/admins */}
          {canManageEvent(event) && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => navigate(`/events/${event.id}/edit`)}
                title="Edit Event"
              >
                <Edit className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                onClick={deleteEvent}
                disabled={deleting}
                className="border-red-200 text-red-600 hover:bg-red-50"
                title="Delete Event"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Event Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Event Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 leading-relaxed whitespace-pre-line">{event.description}</p>
            </CardContent>
          </Card>

          {/* Rules and Guidelines */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="w-5 h-5" />
                Rules & Guidelines
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Rules */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">📋 Event Rules</h3>
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li>• Participants must arrive 15 minutes before the event start time</li>
                    <li>• Valid college ID is mandatory for entry</li>
                    <li>• Registration is mandatory and non-transferable</li>
                    <li>• Participants must follow the college dress code</li>
                    <li>• Late entries will not be allowed</li>
                    <li>• Decision of judges will be final and binding</li>
                    {event.event_type === 'hackathon' && (
                      <>
                        <li>• Team size should be 2-4 members</li>
                        <li>• Laptops and chargers are mandatory</li>
                        <li>• Internet will be provided by the organizers</li>
                      </>
                    )}
                    {event.event_type === 'coding_competition' && (
                      <>
                        <li>• Individual participation only</li>
                        <li>• Use of external resources is not allowed</li>
                        <li>• Plagiarism will lead to disqualification</li>
                      </>
                    )}
                  </ul>
                </div>
              </div>

              {/* Do's */}
              <div>
                <h3 className="text-lg font-semibold text-green-800 mb-3">✅ Do's</h3>
                <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li>• Bring your student ID card and registration confirmation</li>
                    <li>• Maintain discipline and decorum throughout the event</li>
                    <li>• Follow organizer instructions promptly</li>
                    <li>• Network and collaborate with fellow participants</li>
                    <li>• Ask questions if you have any doubts</li>
                    <li>• Keep your workspace clean and organized</li>
                    {event.event_type === 'workshop' && (
                      <>
                        <li>• Bring notebook and pen for taking notes</li>
                        <li>• Actively participate in discussions</li>
                      </>
                    )}
                    {event.is_virtual && (
                      <>
                        <li>• Ensure stable internet connection</li>
                        <li>• Join the meeting 5 minutes early</li>
                        <li>• Keep your microphone muted when not speaking</li>
                      </>
                    )}
                  </ul>
                </div>
              </div>

              {/* Don'ts */}
              <div>
                <h3 className="text-lg font-semibold text-red-800 mb-3">❌ Don'ts</h3>
                <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li>• Don't use mobile phones during the event</li>
                    <li>• Don't engage in any form of cheating or plagiarism</li>
                    <li>• Don't disturb other participants</li>
                    <li>• Don't leave the venue without informing organizers</li>
                    <li>• Don't bring outside food and drinks</li>
                    <li>• Don't indulge in any inappropriate behavior</li>
                    {event.event_type === 'coding_competition' && (
                      <>
                        <li>• Don't access unauthorized websites</li>
                        <li>• Don't communicate with external sources</li>
                      </>
                    )}
                    {!event.is_virtual && (
                      <li>• Don't bring valuables - organizers are not responsible for loss</li>
                    )}
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Schedule */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Schedule
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Event Starts</label>
                  <p className="font-medium">{formatDateTime(event.start_date)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Event Ends</label>
                  <p className="font-medium">{formatDateTime(event.end_date)}</p>
                </div>
              </div>
              
              {event.registration_deadline && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Registration Deadline</label>
                  <p className="font-medium">{formatDateTime(event.registration_deadline)}</p>
                </div>
              )}

              <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
                <CalendarDays className="w-5 h-5 text-blue-600" />
                <span className="text-blue-800 font-medium">
                  Duration: {Math.ceil((new Date(event.end_date) - new Date(event.start_date)) / (1000 * 60 * 60 * 24))} days
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Venue */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {event.is_virtual ? (
                  <>
                    <Video className="w-5 h-5" />
                    Virtual Event
                  </>
                ) : (
                  <>
                    <MapPin className="w-5 h-5" />
                    Venue
                  </>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {event.is_virtual ? (
                <div className="space-y-3">
                  <p className="text-gray-700">This is a virtual event conducted online.</p>
                  {event.virtual_meeting_link && (
                    <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                      <div className="font-medium text-green-800 mb-1">Meeting Link</div>
                      <a
                        href={event.virtual_meeting_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-green-600 hover:text-green-700 underline break-all"
                      >
                        {event.virtual_meeting_link}
                      </a>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <p className="text-gray-700">{event.venue || 'Venue to be announced'}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Prizes */}
          {(event.prizes?.first_prize > 0 || event.prizes?.second_prize > 0 || event.prizes?.third_prize > 0 || event.prizes?.participation_certificates) && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="w-5 h-5" />
                  Prizes & Recognition
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {event.prizes?.first_prize > 0 && (
                    <div className="text-center p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                      <div className="text-2xl mb-2">🥇</div>
                      <div className="font-bold text-lg text-yellow-700">
                        ₹{event.prizes.first_prize.toLocaleString()}
                      </div>
                      <div className="text-sm text-yellow-600">First Prize</div>
                    </div>
                  )}
                  
                  {event.prizes?.second_prize > 0 && (
                    <div className="text-center p-4 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="text-2xl mb-2">🥈</div>
                      <div className="font-bold text-lg text-gray-700">
                        ₹{event.prizes.second_prize.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-600">Second Prize</div>
                    </div>
                  )}
                  
                  {event.prizes?.third_prize > 0 && (
                    <div className="text-center p-4 bg-orange-50 rounded-lg border border-orange-200">
                      <div className="text-2xl mb-2">🥉</div>
                      <div className="font-bold text-lg text-orange-700">
                        ₹{event.prizes.third_prize.toLocaleString()}
                      </div>
                      <div className="text-sm text-orange-600">Third Prize</div>
                    </div>
                  )}
                </div>
                
                {event.prizes?.participation_certificates && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-center gap-2 text-blue-800">
                      <Award className="w-4 h-4" />
                      <span className="font-medium">Participation certificates for all attendees</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Registration Section */}
          {event.registration_enabled && !event.is_registered && 
           event.registered_count < (event.max_participants || Infinity) &&
           (!event.registration_deadline || new Date(event.registration_deadline) > new Date()) && (
            <Card className="border-2 border-green-200 bg-green-50">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl text-green-800 flex items-center justify-center gap-2">
                  <Users className="w-8 h-8" />
                  Ready to Join?
                </CardTitle>
                <p className="text-green-700">Register now to secure your spot in {event.title}</p>
              </CardHeader>
              <CardContent className="text-center">
                <div className="mb-6">
                  <div className="text-3xl font-bold text-green-600 mb-2">
                    {event.registered_count || 0}
                    {event.max_participants && `/${event.max_participants}`}
                  </div>
                  <div className="text-sm text-gray-600">Participants Registered</div>
                  {event.max_participants && (
                    <div className="mt-2 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${Math.min(((event.registered_count || 0) / event.max_participants) * 100, 100)}%` }}
                      />
                    </div>
                  )}
                </div>
                
                <Button
                  onClick={() => setRegistrationModalOpen(true)}
                  size="lg"
                  className="w-full max-w-md bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-8 text-lg"
                >
                  <Users className="w-5 h-5 mr-2" />
                  Register Now
                </Button>
                
                {event.registration_deadline && (
                  <p className="mt-4 text-sm text-gray-600">
                    Registration closes on {new Date(event.registration_deadline).toLocaleDateString()}
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Already Registered */}
          {event.is_registered && (
            <Card className="border-2 border-green-200 bg-green-50">
              <CardContent className="text-center py-8">
                <div className="text-6xl mb-4">✅</div>
                <h3 className="text-xl font-bold text-green-800 mb-2">You're Registered!</h3>
                <p className="text-green-700">Thank you for registering for {event.title}</p>
                <p className="text-sm text-gray-600 mt-2">
                  You'll receive updates and reminders via email.
                </p>
              </CardContent>
            </Card>
          )}

          {/* Tags */}
          {event.tags && event.tags.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Tag className="w-5 h-5" />
                  Tags
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {event.tags.map((tag, index) => (
                    <Badge key={index} variant="outline" className="text-sm">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Registration */}
          {event.registration_enabled && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Registration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {event.registered_count || 0}
                    {event.max_participants && `/${event.max_participants}`}
                  </div>
                  <div className="text-sm text-gray-500">Registered Participants</div>
                </div>

                {!event.is_registered && 
                 event.registered_count < (event.max_participants || Infinity) &&
                 (!event.registration_deadline || new Date(event.registration_deadline) > new Date()) ? (
                  <Button
                    onClick={() => setRegistrationModalOpen(true)}
                    className="w-full bg-green-600 hover:bg-green-700"
                  >
                    <Users className="w-4 h-4 mr-2" />
                    Register Now
                  </Button>
                ) : event.is_registered ? (
                  <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
                    <UserCheck className="w-6 h-6 mx-auto mb-1 text-green-600" />
                    <div className="font-medium text-green-800">You're Registered!</div>
                  </div>
                ) : event.registered_count >= (event.max_participants || Infinity) ? (
                  <div className="text-center p-3 bg-red-50 rounded-lg border border-red-200">
                    <div className="font-medium text-red-800">Registration Full</div>
                  </div>
                ) : (
                  <div className="text-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="font-medium text-gray-800">Registration Closed</div>
                  </div>
                )}

                {/* Participants List for Admins */}
                {canManageEvent(event) && (
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={fetchParticipants}
                      >
                        View Participants
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>Registered Participants</DialogTitle>
                      </DialogHeader>
                      {loadingParticipants ? (
                        <div className="text-center py-8">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-4"></div>
                          <p>Loading participants...</p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {participants.length === 0 ? (
                            <p className="text-center text-gray-500 py-4">No participants yet</p>
                          ) : (
                            participants.map((participant, index) => (
                              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                <div>
                                  <div className="font-medium">{participant.name}</div>
                                  <div className="text-sm text-gray-500">{participant.email}</div>
                                  <div className="text-xs text-gray-400">{participant.college}</div>
                                </div>
                                <Badge variant="outline">
                                  {new Date(participant.registered_at).toLocaleDateString()}
                                </Badge>
                              </div>
                            ))
                          )}
                        </div>
                      )}
                    </DialogContent>
                  </Dialog>
                )}
              </CardContent>
            </Card>
          )}

          {/* Organizer Information */}
          <Card>
            <CardHeader>
              <CardTitle>Organizer Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {event.organizer_name && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Organizer</label>
                  <p className="font-medium">{event.organizer_name}</p>
                </div>
              )}

              {event.club_name && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Club/Organization</label>
                  <p className="font-medium">{event.club_name}</p>
                </div>
              )}

              {event.organizer_contact && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Contact</label>
                  <p className="font-medium break-all">{event.organizer_contact}</p>
                </div>
              )}

              {event.college && (
                <div>
                  <label className="text-sm font-medium text-gray-500">College</label>
                  <p className="font-medium">{event.college}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Event Info */}
          <Card>
            <CardHeader>
              <CardTitle>Event Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-500">Event Type</label>
                <p className="font-medium capitalize">{event.event_type.replace('_', ' ')}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">Visibility</label>
                <p className="font-medium capitalize">
                  {event.visibility === 'college_only' ? 'College Only' : 
                   event.visibility === 'all_colleges' ? 'All Colleges' : 
                   'Selected Colleges'}
                </p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">Created</label>
                <p className="font-medium">
                  {new Date(event.created_at).toLocaleDateString()}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Registration Modal */}
      {registrationModalOpen && (
        <RegistrationModal
          open={registrationModalOpen}
          onClose={() => {
            setRegistrationModalOpen(false);
            // Refresh event data after registration
            fetchEventDetails();
          }}
          eventId={event.id}
          eventTitle={event.title}
          eventType="college_event"
        />
      )}
    </div>
  );
};

export default EventDetails;
