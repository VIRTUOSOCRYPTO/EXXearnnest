import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Avatar } from './ui/avatar';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Label } from './ui/label';
import { toast } from './ui/toast';
import { Users, UserPlus, Gift, Copy, Clock, CheckCircle, Star } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

const Friends = () => {
  const [friends, setFriends] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [inviteStats, setInviteStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [invitePhone, setInvitePhone] = useState('');
  const [referralCode, setReferralCode] = useState('');
  const [acceptCode, setAcceptCode] = useState('');
  const [showAcceptModal, setShowAcceptModal] = useState(false);

  useEffect(() => {
    fetchFriends();
    fetchInvitations();
  }, []);

  const fetchFriends = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/friends`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setFriends(data.friends);
      }
    } catch (error) {
      console.error('Error fetching friends:', error);
    }
  };

  const fetchInvitations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/friends/invitations`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setInvitations(data.sent_invitations);
        setInviteStats(data.invitation_stats);
      }
    } catch (error) {
      console.error('Error fetching invitations:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendInvitation = async () => {
    if (!inviteEmail && !invitePhone) {
      toast({
        title: "Error",
        description: "Please provide either email or phone number",
        variant: "destructive"
      });
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/friends/invite`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          email: inviteEmail || null,
          phone: invitePhone || null
        })
      });

      const data = await response.json();

      if (response.ok) {
        setReferralCode(data.referral_code);
        setInviteEmail('');
        setInvitePhone('');
        toast({
          title: "Invitation Sent!",
          description: `Referral code: ${data.referral_code}. ${data.invites_left} invites remaining this month.`
        });
        fetchInvitations();
      } else {
        throw new Error(data.detail || 'Failed to send invitation');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const acceptInvitation = async () => {
    if (!acceptCode.trim()) {
      toast({
        title: "Error",
        description: "Please enter a referral code",
        variant: "destructive"
      });
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/friends/accept-invitation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ referral_code: acceptCode })
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Friend Added!",
          description: `You earned ${data.points_earned} points for joining!`
        });
        setAcceptCode('');
        setShowAcceptModal(false);
        fetchFriends();
      } else {
        throw new Error(data.detail || 'Failed to accept invitation');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: "Referral code copied to clipboard"
    });
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getAvatarImage = (avatar) => {
    const avatarMap = {
      boy: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face",
      man: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face",
      girl: "https://images.unsplash.com/photo-1494790108755-2616c27b87bb?w=100&h=100&fit=crop&crop=face",
      woman: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face",
      grandfather: "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=100&h=100&fit=crop&crop=face",
      grandmother: "https://images.unsplash.com/photo-1547036967-23d11aacaee0?w=100&h=100&fit=crop&crop=face"
    };
    return avatarMap[avatar] || avatarMap.boy;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded mb-4 w-1/3"></div>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="h-64 bg-gray-200 rounded-lg"></div>
              <div className="h-64 bg-gray-200 rounded-lg"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Friends Network</h1>
            <p className="text-gray-600">Connect with friends and earn rewards together</p>
          </div>
          <div className="flex gap-3">
            <Dialog open={showInviteModal} onOpenChange={setShowInviteModal}>
              <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700">
                  <UserPlus className="w-4 h-4 mr-2" />
                  Invite Friend
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Invite a Friend</DialogTitle>
                  <DialogDescription>
                    Send an invitation to earn points when they join EarnNest
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="friend@example.com"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="phone">Phone Number</Label>
                    <Input
                      id="phone"
                      type="tel"
                      placeholder="+91 98765 43210"
                      value={invitePhone}
                      onChange={(e) => setInvitePhone(e.target.value)}
                    />
                  </div>
                  <p className="text-sm text-gray-500">
                    Provide either email or phone number to send invitation
                  </p>
                  {referralCode && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-sm font-medium text-green-800 mb-2">Referral Code Generated:</p>
                      <div className="flex items-center gap-2">
                        <code className="bg-white px-2 py-1 rounded border font-mono text-sm">
                          {referralCode}
                        </code>
                        <Button 
                          size="sm" 
                          variant="ghost"
                          onClick={() => copyToClipboard(referralCode)}
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                      </div>
                      <p className="text-xs text-green-600 mt-1">
                        Share this code with your friend to join!
                      </p>
                    </div>
                  )}
                  <Button onClick={sendInvitation} className="w-full">
                    Send Invitation
                  </Button>
                </div>
              </DialogContent>
            </Dialog>

            <Dialog open={showAcceptModal} onOpenChange={setShowAcceptModal}>
              <DialogTrigger asChild>
                <Button variant="outline">
                  <Gift className="w-4 h-4 mr-2" />
                  Join via Code
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Accept Friend Invitation</DialogTitle>
                  <DialogDescription>
                    Enter a referral code to become friends and earn welcome points
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="acceptCode">Referral Code</Label>
                    <Input
                      id="acceptCode"
                      placeholder="EARNXXXX123456"
                      value={acceptCode}
                      onChange={(e) => setAcceptCode(e.target.value.toUpperCase())}
                    />
                  </div>
                  <Button onClick={acceptInvitation} className="w-full">
                    Accept Invitation
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Stats Overview */}
        {inviteStats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-blue-600">{friends.length}</div>
                <p className="text-sm text-gray-600">Total Friends</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-green-600">{inviteStats.total_successful}</div>
                <p className="text-sm text-gray-600">Successful Invites</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-purple-600">{inviteStats.remaining}</div>
                <p className="text-sm text-gray-600">Invites Left</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-orange-600">{inviteStats.bonus_points_earned}</div>
                <p className="text-sm text-gray-600">Points Earned</p>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Friends List */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Your Friends ({friends.length})
                </CardTitle>
                <CardDescription>
                  Friends you've connected with on EarnNest
                </CardDescription>
              </CardHeader>
              <CardContent>
                {friends.length === 0 ? (
                  <div className="text-center py-8">
                    <Users className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No friends yet</h3>
                    <p className="text-gray-600 mb-4">
                      Invite friends to connect and earn rewards together
                    </p>
                    <Button onClick={() => setShowInviteModal(true)}>
                      <UserPlus className="w-4 h-4 mr-2" />
                      Invite Your First Friend
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {friends.map((friend) => (
                      <div key={friend.friend_id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
                        <div className="flex items-center gap-3">
                          <Avatar>
                            <img 
                              src={getAvatarImage(friend.avatar)} 
                              alt={friend.full_name}
                              className="w-10 h-10 rounded-full object-cover"
                            />
                          </Avatar>
                          <div>
                            <h4 className="font-medium text-gray-900">{friend.full_name}</h4>
                            <p className="text-sm text-gray-600">{friend.university || 'No university set'}</p>
                            <div className="flex items-center gap-4 mt-1">
                              <span className="text-xs text-gray-500">
                                Level {friend.level} • {friend.badges_count} badges
                              </span>
                              <Badge variant="outline" className="text-xs">
                                {friend.current_streak} day streak
                              </Badge>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-green-600">
                            ₹{friend.total_earnings.toLocaleString()}
                          </p>
                          <p className="text-xs text-gray-500">Total earnings</p>
                          {friend.friendship_points > 0 && (
                            <div className="flex items-center gap-1 mt-1">
                              <Star className="w-3 h-3 text-yellow-500" />
                              <span className="text-xs text-gray-600">
                                {friend.friendship_points} friendship points
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Invitations Panel */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Sent Invitations</CardTitle>
                <CardDescription>
                  Track your referral invitations
                </CardDescription>
              </CardHeader>
              <CardContent>
                {invitations.length === 0 ? (
                  <div className="text-center py-6">
                    <UserPlus className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                    <p className="text-gray-600">No invitations sent yet</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {invitations.slice(0, 5).map((invitation) => (
                      <div key={invitation.id} className="p-3 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm font-medium">
                            {invitation.invitee_email || invitation.invitee_phone}
                          </p>
                          <Badge 
                            variant={
                              invitation.status === 'accepted' ? 'success' :
                              invitation.status === 'expired' ? 'destructive' : 'secondary'
                            }
                          >
                            {invitation.status === 'accepted' && <CheckCircle className="w-3 h-3 mr-1" />}
                            {invitation.status === 'expired' && <Clock className="w-3 h-3 mr-1" />}
                            {invitation.status}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
                            {invitation.referral_code}
                          </code>
                          <Button 
                            size="sm" 
                            variant="ghost"
                            onClick={() => copyToClipboard(invitation.referral_code)}
                          >
                            <Copy className="w-3 h-3" />
                          </Button>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          Sent {formatDate(invitation.invited_at)}
                        </p>
                      </div>
                    ))}
                    {invitations.length > 5 && (
                      <p className="text-xs text-gray-500 text-center mt-2">
                        And {invitations.length - 5} more invitations...
                      </p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Invitation Limits */}
            {inviteStats && (
              <Card className="mt-4">
                <CardHeader>
                  <CardTitle className="text-sm">Monthly Invitation Limit</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-600">Used this month</span>
                    <span className="text-sm font-medium">
                      {inviteStats.monthly_sent} / {inviteStats.monthly_limit}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ 
                        width: `${Math.min(100, (inviteStats.monthly_sent / inviteStats.monthly_limit) * 100)}%` 
                      }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Unlock more invites through achievements and milestones
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Friends;
