import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Avatar } from './ui/avatar';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Label } from './ui/label';
import { toast } from '../hooks/use-toast';
import { useAuth } from '../App';
import { 
  Users, 
  UserPlus, 
  Gift, 
  Copy, 
  Clock, 
  CheckCircle, 
  Star,
  ShareIcon,
  CurrencyRupeeIcon,
  UsersIcon,
  GiftIcon,
  ClipboardIcon,
  CheckIcon,
  ArrowUpIcon,
  CalendarIcon,
  TrophyIcon,
  SparklesIcon
} from 'lucide-react';
import {
  ShareIcon as HeroShareIcon,
  CurrencyRupeeIcon as HeroCurrencyRupeeIcon,
  UsersIcon as HeroUsersIcon,
  GiftIcon as HeroGiftIcon,
  ClipboardIcon as HeroClipboardIcon,
  CheckIcon as HeroCheckIcon,
  ArrowUpIcon as HeroArrowUpIcon,
  CalendarIcon as HeroCalendarIcon,
  TrophyIcon as HeroTrophyIcon,
  SparklesIcon as HeroSparklesIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const FriendsAndReferrals = () => {
  // Friends state
  const [friends, setFriends] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [inviteStats, setInviteStats] = useState(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [invitePhone, setInvitePhone] = useState('');
  const [referralCode, setReferralCode] = useState('');
  const [acceptCode, setAcceptCode] = useState('');
  const [showAcceptModal, setShowAcceptModal] = useState(false);

  // Referrals state
  const [referralData, setReferralData] = useState(null);
  const [stats, setStats] = useState(null);
  const [copying, setCopying] = useState(false);
  const [copied, setCopied] = useState(false);

  // General state
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('friends'); // friends, referrals
  const { user } = useAuth();

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchFriends(),
        fetchInvitations(),
        fetchReferralData()
      ]);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Friends functions
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
        setInvitations(data.invitations);
        setInviteStats(data.stats);
      }
    } catch (error) {
      console.error('Error fetching invitations:', error);
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

      if (response.ok) {
        const data = await response.json();
        setReferralCode(data.referral_code);
        setInviteEmail('');
        setInvitePhone('');
        fetchInvitations();
        toast({
          title: "Invitation Sent!",
          description: `Referral code: ${data.referral_code}`
        });
      } else {
        const error = await response.json();
        toast({
          title: "Error",
          description: error.detail || "Failed to send invitation",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error sending invitation:', error);
      toast({
        title: "Error",
        description: "Failed to send invitation",
        variant: "destructive"
      });
    }
  };

  const copyReferralCode = async (code) => {
    try {
      await navigator.clipboard.writeText(code);
      toast({
        title: "Copied!",
        description: "Referral code copied to clipboard"
      });
    } catch (error) {
      console.error('Error copying code:', error);
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
        body: JSON.stringify({
          referral_code: acceptCode.trim()
        })
      });

      if (response.ok) {
        setAcceptCode('');
        setShowAcceptModal(false);
        fetchFriends();
        toast({
          title: "Success!",
          description: "Friend invitation accepted successfully!"
        });
      } else {
        const error = await response.json();
        toast({
          title: "Error",
          description: error.detail || "Failed to accept invitation",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error accepting invitation:', error);
      toast({
        title: "Error",
        description: "Failed to accept invitation",
        variant: "destructive"
      });
    }
  };

  // Referrals functions
  const fetchReferralData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [linkResponse, statsResponse] = await Promise.all([
        fetch(`${API}/referrals/my-link`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }),
        fetch(`${API}/referrals/stats`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
      ]);

      if (linkResponse.ok && statsResponse.ok) {
        const linkData = await linkResponse.json();
        const statsData = await statsResponse.json();
        setReferralData(linkData);
        setStats(statsData);
      }
    } catch (error) {
      console.error('Error fetching referral data:', error);
    }
  };

  const copyReferralLink = async () => {
    if (!referralData?.referral_link) return;
    
    setCopying(true);
    try {
      await navigator.clipboard.writeText(referralData.referral_link);
      setCopied(true);
      toast({
        title: "Copied!",
        description: "Referral link copied to clipboard"
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy link:', error);
      toast({
        title: "Error",
        description: "Failed to copy referral link",
        variant: "destructive"
      });
    } finally {
      setCopying(false);
    }
  };

  const shareViaWhatsApp = () => {
    const message = `Hey! Join me on EarnNest and start earning money while managing your finances. Use my referral link: ${referralData.referral_link}`;
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
  };

  const shareViaEmail = () => {
    const subject = 'Join EarnNest - Start Earning Today!';
    const body = `Hi there!\n\nI've been using EarnNest to manage my finances and earn money, and I think you'd love it too!\n\nJoin me using this referral link: ${referralData.referral_link}\n\nYou'll get rewards for signing up, and I'll get rewarded too when you join. It's a win-win!\n\nBest regards,\n${user?.full_name}`;
    
    const mailtoUrl = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.location.href = mailtoUrl;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Friends & Referrals</h1>
          <p className="text-gray-600 mt-2">Build your network and earn rewards together</p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
        <Button
          onClick={() => setActiveTab('friends')}
          variant={activeTab === 'friends' ? 'default' : 'ghost'}
          className="px-6"
        >
          <Users className="w-4 h-4 mr-2" />
          Friends Network
        </Button>
        <Button
          onClick={() => setActiveTab('referrals')}
          variant={activeTab === 'referrals' ? 'default' : 'ghost'}
          className="px-6"
        >
          <Gift className="w-4 h-4 mr-2" />
          Refer & Earn
        </Button>
      </div>

      {/* Friends Tab */}
      {activeTab === 'friends' && (
        <div className="space-y-6">
          {/* Friends Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Friends</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{friends.length}</div>
                <p className="text-xs text-muted-foreground">Active friendships</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Invitations Sent</CardTitle>
                <UserPlus className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{inviteStats?.monthly_sent || 0}</div>
                <p className="text-xs text-muted-foreground">This month ({inviteStats?.monthly_limit || 15} limit)</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                <Star className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{inviteStats?.success_rate || 0}%</div>
                <p className="text-xs text-muted-foreground">Invitation acceptance</p>
              </CardContent>
            </Card>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-4">
            <Dialog open={showInviteModal} onOpenChange={setShowInviteModal}>
              <DialogTrigger asChild>
                <Button className="flex items-center gap-2">
                  <UserPlus className="w-4 h-4" />
                  Invite Friends
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Invite a Friend</DialogTitle>
                  <DialogDescription>
                    Send an invitation to your friend via email or phone
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="email">Email (optional)</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="friend@example.com"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="phone">Phone (optional)</Label>
                    <Input
                      id="phone"
                      type="tel"
                      placeholder="+91 9876543210"
                      value={invitePhone}
                      onChange={(e) => setInvitePhone(e.target.value)}
                    />
                  </div>
                  <Button onClick={sendInvitation} className="w-full">
                    Send Invitation
                  </Button>
                  {referralCode && (
                    <div className="p-4 bg-green-50 rounded-lg">
                      <p className="text-sm font-medium text-green-800 mb-2">Referral Code Generated:</p>
                      <div className="flex items-center gap-2">
                        <code className="flex-1 bg-white px-3 py-2 rounded border text-green-700 font-mono">
                          {referralCode}
                        </code>
                        <Button
                          onClick={() => copyReferralCode(referralCode)}
                          variant="outline"
                          size="sm"
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </DialogContent>
            </Dialog>

            <Dialog open={showAcceptModal} onOpenChange={setShowAcceptModal}>
              <DialogTrigger asChild>
                <Button variant="outline" className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Accept Invitation
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Accept Friend Invitation</DialogTitle>
                  <DialogDescription>
                    Enter the referral code from your friend
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="acceptCode">Referral Code</Label>
                    <Input
                      id="acceptCode"
                      placeholder="Enter referral code"
                      value={acceptCode}
                      onChange={(e) => setAcceptCode(e.target.value)}
                    />
                  </div>
                  <Button onClick={acceptInvitation} className="w-full">
                    Accept Invitation
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Friends List */}
          <Card>
            <CardHeader>
              <CardTitle>Your Friends</CardTitle>
              <CardDescription>Connected friends on EarnNest</CardDescription>
            </CardHeader>
            <CardContent>
              {friends.length === 0 ? (
                <div className="text-center py-8">
                  <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No friends yet</h3>
                  <p className="text-gray-600 mb-4">Start inviting friends to build your network!</p>
                  <Button onClick={() => setShowInviteModal(true)}>
                    <UserPlus className="w-4 h-4 mr-2" />
                    Invite Your First Friend
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {friends.map((friend) => (
                    <div key={friend.user_id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center space-x-3">
                        <Avatar className="w-10 h-10">
                          <img
                            src={`https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop&crop=face`}
                            alt={friend.full_name}
                            className="w-full h-full object-cover rounded-full"
                          />
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {friend.full_name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {friend.university}
                          </p>
                        </div>
                      </div>
                      <div className="mt-3 space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-gray-500">Streak:</span>
                          <span className="font-medium">{friend.current_streak} days</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-gray-500">Earnings:</span>
                          <span className="font-medium">₹{friend.total_earnings?.toLocaleString() || 0}</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-gray-500">Points:</span>
                          <span className="font-medium">{friend.total_points || 0}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Sent Invitations */}
          {invitations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Sent Invitations</CardTitle>
                <CardDescription>Track your friend invitations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {invitations.map((invitation) => (
                    <div key={invitation.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">
                          {invitation.email || invitation.phone}
                        </p>
                        <p className="text-sm text-gray-500">
                          Code: {invitation.referral_code}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={invitation.status === 'accepted' ? 'default' : 'secondary'}>
                          {invitation.status}
                        </Badge>
                        <Button
                          onClick={() => copyReferralCode(invitation.referral_code)}
                          variant="ghost"
                          size="sm"
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Referrals Tab */}
      {activeTab === 'referrals' && (
        <div className="space-y-6">
          {/* Referral Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Referrals</CardTitle>
                <HeroUsersIcon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-emerald-600">
                  {stats?.total_referrals || 0}
                </div>
                <p className="text-xs text-muted-foreground flex items-center">
                  <HeroArrowUpIcon className="h-3 w-3 mr-1" />
                  {stats?.successful_referrals || 0} successful
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Earnings</CardTitle>
                <HeroCurrencyRupeeIcon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  ₹{stats?.total_earnings || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  ₹{stats?.pending_earnings || 0} pending
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
                <HeroTrophyIcon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {stats?.conversion_rate || 0}%
                </div>
                <p className="text-xs text-muted-foreground">
                  Sign-up to active user
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">This Month</CardTitle>
                <HeroCalendarIcon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-600">
                  {stats?.recent_referrals?.length || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  New referrals
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Referral Link Section */}
          {referralData && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <HeroGiftIcon className="h-5 w-5" />
                  Your Referral Link
                </CardTitle>
                <CardDescription>
                  Share this link with friends to earn rewards when they join
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Input
                    value={referralData.referral_link || ''}
                    readOnly
                    className="font-mono text-sm"
                  />
                  <Button
                    onClick={copyReferralLink}
                    disabled={copying}
                    className="flex-shrink-0"
                  >
                    {copied ? (
                      <HeroCheckIcon className="h-4 w-4" />
                    ) : (
                      <HeroClipboardIcon className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                
                <div className="flex space-x-3">
                  <Button 
                    onClick={shareViaWhatsApp}
                    className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
                  >
                    <HeroShareIcon className="h-4 w-4" />
                    WhatsApp
                  </Button>
                  <Button 
                    onClick={shareViaEmail}
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    <HeroShareIcon className="h-4 w-4" />
                    Email
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recent Referrals */}
          {stats?.recent_referrals && stats.recent_referrals.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Referrals</CardTitle>
                <CardDescription>Your latest successful referrals</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stats.recent_referrals.map((referral, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">{referral.referred_user_name}</p>
                        <p className="text-sm text-gray-500">
                          Joined on {new Date(referral.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <Badge className="bg-green-100 text-green-800">
                        +₹{referral.reward_amount}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Referral Program Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HeroSparklesIcon className="h-5 w-5" />
                How It Works
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <HeroShareIcon className="h-6 w-6 text-blue-600" />
                  </div>
                  <h3 className="font-semibold mb-2">1. Share Your Link</h3>
                  <p className="text-sm text-gray-600">
                    Share your unique referral link with friends via WhatsApp, email, or social media
                  </p>
                </div>
                
                <div className="text-center">
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <HeroUsersIcon className="h-6 w-6 text-green-600" />
                  </div>
                  <h3 className="font-semibold mb-2">2. Friend Joins</h3>
                  <p className="text-sm text-gray-600">
                    Your friend signs up using your link and starts using EarnNest
                  </p>
                </div>
                
                <div className="text-center">
                  <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <HeroCurrencyRupeeIcon className="h-6 w-6 text-emerald-600" />
                  </div>
                  <h3 className="font-semibold mb-2">3. Earn Rewards</h3>
                  <p className="text-sm text-gray-600">
                    Both you and your friend earn rewards when they complete their first transaction
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default FriendsAndReferrals;
