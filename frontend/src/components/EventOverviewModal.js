import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import RegistrationModal from './RegistrationModal';
import { 
  CalendarDays, 
  MapPin, 
  Users, 
  Award, 
  Clock, 
  Globe, 
  Building,
  Video,
  Mail,
  Phone,
  ArrowLeft,
  UserPlus
} from 'lucide-react';

const EventOverviewModal = ({ open, onClose, event }) => {
  const [registrationModalOpen, setRegistrationModalOpen] = useState(false);

  if (!event) return null;

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

  const getEventStatusBadge = (event) => {
    const now = new Date();
    const startDate = new Date(event.start_date);
    const endDate = new Date(event.end_date);
    const regDeadline = event.registration_deadline ? new Date(event.registration_deadline) : null;

    if (now < startDate) {
      if (regDeadline && now <= regDeadline) {
        return <Badge className="bg-green-500">Registration Open</Badge>;
      } else if (regDeadline && now > regDeadline) {
        return <Badge variant="secondary">Registration Closed</Badge>;
      } else {
        return <Badge variant="outline" className="bg-blue-100">Upcoming</Badge>;
      }
    } else if (now >= startDate && now <= endDate) {
      return <Badge className="bg-orange-500">Ongoing</Badge>;
    } else {
      return <Badge variant="outline" className="bg-gray-100">Past Event</Badge>;
    }
  };

  const canRegister = () => {
    const now = new Date();
    const regDeadline = event.registration_deadline ? new Date(event.registration_deadline) : null;
    
    return event.registration_enabled && 
           !event.is_registered && 
           event.registered_count < (event.max_participants || Infinity) &&
           (!regDeadline || now <= regDeadline);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">{eventTypeIcons[event.event_type] || '📅'}</span>
              <DialogTitle className="text-2xl font-bold text-gray-800">
                {event.title}
              </DialogTitle>
            </div>
            <div className="flex flex-wrap gap-2 mb-4">
              {getEventStatusBadge(event)}
              {event.is_registered && (
                <Badge className="bg-emerald-500">
                  <Users className="w-3 h-3 mr-1" />
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
          </DialogHeader>

          <div className="space-y-6">
            {/* Prize Information */}
            {event.prizes?.first_prize > 0 && (
              <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-4 rounded-lg border-l-4 border-l-yellow-500">
                <div className="flex items-center gap-2 mb-2">
                  <Award className="w-5 h-5 text-yellow-600" />
                  <h3 className="text-lg font-semibold text-yellow-800">Prize Pool</h3>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">
                      ₹{(event.prizes.first_prize || 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-yellow-700">🥇 First Prize</div>
                  </div>
                  {event.prizes.second_prize > 0 && (
                    <div className="text-center">
                      <div className="text-xl font-bold text-gray-600">
                        ₹{event.prizes.second_prize.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-700">🥈 Second Prize</div>
                    </div>
                  )}
                  {event.prizes.third_prize > 0 && (
                    <div className="text-center">
                      <div className="text-lg font-bold text-orange-600">
                        ₹{event.prizes.third_prize.toLocaleString()}
                      </div>
                      <div className="text-sm text-orange-700">🥉 Third Prize</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Event Description */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-800">Event Description</h3>
              <p className="text-gray-600 leading-relaxed">
                {event.description || "Join us for an exciting event that brings together students and professionals from various backgrounds."}
              </p>
            </div>

            {/* Event Rules */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-800">Event Rules</h3>
              <div className="bg-blue-50 p-4 rounded-lg">
                {event.rules ? (
                  <div className="space-y-2">
                    {event.rules.split('\n').map((rule, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <span className="text-blue-600 font-bold min-w-[20px]">{index + 1}.</span>
                        <span className="text-blue-800">{rule}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-2 text-blue-800">
                    <div className="flex items-start gap-2">
                      <span className="text-blue-600 font-bold min-w-[20px]">1.</span>
                      <span>All participants must register before the deadline.</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-blue-600 font-bold min-w-[20px]">2.</span>
                      <span>Valid student ID is required for verification.</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-blue-600 font-bold min-w-[20px]">3.</span>
                      <span>Follow the event schedule and guidelines provided by organizers.</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-blue-600 font-bold min-w-[20px]">4.</span>
                      <span>Respect all participants and maintain professional conduct.</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Event Details Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <CalendarDays className="w-6 h-6 mx-auto mb-2 text-gray-600" />
                <div className="text-sm font-medium mb-1">Start Date</div>
                <div className="text-xs text-gray-600">
                  {formatDate(event.start_date)}
                </div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <Clock className="w-6 h-6 mx-auto mb-2 text-gray-600" />
                <div className="text-sm font-medium mb-1">Duration</div>
                <div className="text-xs text-gray-600">
                  {Math.ceil((new Date(event.end_date) - new Date(event.start_date)) / (1000 * 60 * 60 * 24))} days
                </div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <Users className="w-6 h-6 mx-auto mb-2 text-gray-600" />
                <div className="text-sm font-medium mb-1">Registered</div>
                <div className="text-xs text-gray-600">
                  {event.registered_count || 0}
                  {event.max_participants && `/${event.max_participants}`}
                </div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                {event.is_virtual ? (
                  <>
                    <Video className="w-6 h-6 mx-auto mb-2 text-gray-600" />
                    <div className="text-sm font-medium mb-1">Virtual</div>
                    <div className="text-xs text-gray-600">Online Event</div>
                  </>
                ) : (
                  <>
                    <MapPin className="w-6 h-6 mx-auto mb-2 text-gray-600" />
                    <div className="text-sm font-medium mb-1">Venue</div>
                    <div className="text-xs text-gray-600">
                      {event.venue || 'TBD'}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* College Address */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-800">College Address</h3>
              <div className="bg-green-50 p-4 rounded-lg border-l-4 border-l-green-500">
                <div className="flex items-start gap-3">
                  <Building className="w-5 h-5 text-green-600 mt-1" />
                  <div className="space-y-1">
                    <div className="font-medium text-green-800">
                      {event.college_name || event.organizer_name || 'Event Organizer'}
                    </div>
                    <div className="text-green-700">
                      {event.college_address || event.venue || 'Address will be provided upon registration'}
                    </div>
                    {(event.organizer_email || event.contact_email) && (
                      <div className="flex items-center gap-2 text-green-600">
                        <Mail className="w-4 h-4" />
                        <span className="text-sm">{event.organizer_email || event.contact_email}</span>
                      </div>
                    )}
                    {(event.organizer_phone || event.contact_phone) && (
                      <div className="flex items-center gap-2 text-green-600">
                        <Phone className="w-4 h-4" />
                        <span className="text-sm">{event.organizer_phone || event.contact_phone}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Additional Event Information */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <h4 className="font-medium text-gray-700">Event Details</h4>
                {event.organizer_name && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Organizer:</span>
                    <span className="font-medium">{event.organizer_name}</span>
                  </div>
                )}
                {event.club_name && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Club:</span>
                    <span className="font-medium">{event.club_name}</span>
                  </div>
                )}
                {event.registration_deadline && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Registration Deadline:</span>
                    <span className="font-medium">
                      {new Date(event.registration_deadline).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>
              
              {event.tags && event.tags.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-gray-700">Tags</h4>
                  <div className="flex flex-wrap gap-1">
                    {event.tags.map((tag, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 mt-8 pt-6 border-t">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>

            {canRegister() && (
              <Button
                onClick={() => setRegistrationModalOpen(true)}
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                <UserPlus className="w-4 h-4 mr-2" />
                Register Now
              </Button>
            )}

            {event.is_registered && (
              <Button
                disabled
                className="flex-1 bg-emerald-500"
              >
                <Users className="w-4 h-4 mr-2" />
                Already Registered
              </Button>
            )}

            {!canRegister() && !event.is_registered && (
              <Button
                disabled
                variant="secondary"
                className="flex-1"
              >
                Registration Closed
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Registration Modal */}
      <RegistrationModal
        open={registrationModalOpen}
        onClose={() => setRegistrationModalOpen(false)}
        eventId={event.id}
        eventType="college_event"
        eventTitle={event.title}
      />
    </>
  );
};

export default EventOverviewModal;
