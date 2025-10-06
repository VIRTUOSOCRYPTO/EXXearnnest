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
  const [activeTab, setActiveTab] = useState('friends'); // friends, referrals, activity
  const { user } = useAuth();

  // **NEW: Real-time activity state**
  const [recentActivity, setRecentActivity] = useState([]);
  const [liveStats, setLiveStats] = useState(null);
  const [activityLoading, setActivityLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchAllData();
  }, []);

  // **NEW: Auto-refresh functionality for real-time updates**
  useEffect(() => {
    if (!autoRefresh) return;

    const refreshInterval = setInterval(() => {
      fetchLiveStats();
      if (activeTab === 'activity') {
        fetchRecentActivity();
      }
      // Refresh friends list every 30 seconds to catch new automatic connections
      fetchFriends();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(refreshInterval);
  }, [activeTab, autoRefresh]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchFriends(),
        fetchInvitations(),
        fetchReferralData(),
        fetchLiveStats(),
        fetchRecentActivity()
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
        setFriends(data.friends || []);
      } else {
        // If API fails, ensure friends is still an array
        setFriends([]);
      }
    } catch (error) {
      console.error('Error fetching friends:', error);
      // Ensure friends is always an array on error
      setFriends([]);
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
        setInvitations(data.invitations || []);
        setInviteStats(data.stats || null);
      } else {
        // If API fails, ensure invitations is still an array
        setInvitations([]);
        setInviteStats(null);
      }
    } catch (error) {
      console.error('Error fetching invitations:', error);
      // Ensure invitations is always an array on error
      setInvitations([]);
      setInviteStats(null);
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

  const shareReferralLink = async () => {
    const shareTitle = 'Join EarnAura - Start Earning Today!';
    const shareText = `Hey! Join me on EarnAura and start earning money while managing your finances. Use my referral link to get started and we both earn rewards!`;
    const shareUrl = referralData.referral_link;

    // Check if Web Share API is supported
    if (navigator.share) {
      try {
        await navigator.share({
          title: shareTitle,
          text: shareText,
          url: shareUrl,
        });
        toast({
          title: "Shared Successfully!",
          description: "Your referral link has been shared"
        });
      } catch (error) {
        if (error.name !== 'AbortError') {
          // Fallback if share was cancelled or failed
          console.error('Error sharing:', error);
          fallbackShare();
        }
      }
    } else {
      // Fallback for browsers that don't support Web Share API
      fallbackShare();
    }
  };

  const fallbackShare = () => {
    // Copy to clipboard as fallback
    copyReferralLink();
    toast({
      title: "Link Copied!",
      description: "Referral link copied to clipboard. You can now paste it anywhere to share."
    });
  };

  // **NEW: Real-time activity functions**
  const fetchRecentActivity = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/friends/recent-activity`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setRecentActivity(data.recent_activities || []);
      } else {
        // If API fails, ensure recentActivity is still an array
        setRecentActivity([]);
      }
    } catch (error) {
      console.error('Error fetching recent activity:', error);
      // Ensure recentActivity is always an array on error
      setRecentActivity([]);
    }
  };

  const fetchLiveStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/friends/live-stats`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setLiveStats(data || null);
      } else {
        // If API fails, set to null
        setLiveStats(null);
      }
    } catch (error) {
      console.error('Error fetching live stats:', error);
      // Set to null on error
      setLiveStats(null);
    }
  };

  const toggleAutoRefresh = () => {
    setAutoRefresh(!autoRefresh);
    if (!autoRefresh) {
      fetchAllData(); // Immediately refresh when turning on
    }
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMinutes = Math.floor((now - time) / (1000 * 60));
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
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

      {/* Tab Navigation & Controls */}
      <div className="flex items-center justify-between">
        <div className="overflow-x-auto scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0 w-full">
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit min-w-full sm:min-w-0">
            <Button
              onClick={() => setActiveTab('friends')}
              variant={activeTab === 'friends' ? 'default' : 'ghost'}
              className={`${activeTab === 'friends' ? 'btn-primary flex items-center gap-2 text-xs sm:text-sm px-3 sm:px-6 py-2 sm:py-3' : 'px-3 sm:px-6 text-xs sm:text-sm'} whitespace-nowrap flex-shrink-0`}
            >
              <Users className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
              <span className="hidden xs:inline">Friends Network</span>
              <span className="xs:hidden">Friends</span>
              {liveStats?.friends_count > 0 && (
                <Badge variant="secondary" className="ml-1 sm:ml-2 text-xs">{liveStats.friends_count}</Badge>
              )}
            </Button>
            <Button
              onClick={() => setActiveTab('referrals')}
              variant={activeTab === 'referrals' ? 'default' : 'ghost'}
              className={`${activeTab === 'referrals' ? 'btn-primary flex items-center gap-2 text-xs sm:text-sm px-3 sm:px-6 py-2 sm:py-3' : 'px-3 sm:px-6 text-xs sm:text-sm'} whitespace-nowrap flex-shrink-0`}
            >
              <Gift className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
              <span className="hidden xs:inline">Refer & Earn</span>
              <span className="xs:hidden">Refer</span>
              {liveStats?.total_referrals > 0 && (
                <Badge variant="secondary" className="ml-1 sm:ml-2 text-xs">{liveStats.total_referrals}</Badge>
              )}
            </Button>
            <Button
              onClick={() => setActiveTab('activity')}
              variant={activeTab === 'activity' ? 'default' : 'ghost'}
              className={`${activeTab === 'activity' ? 'btn-primary flex items-center gap-2 text-xs sm:text-sm px-3 sm:px-6 py-2 sm:py-3' : 'px-3 sm:px-6 text-xs sm:text-sm'} whitespace-nowrap flex-shrink-0`}
            >
              <Clock className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
              <span className="hidden xs:inline">Activity</span>
              <span className="xs:hidden">Activity</span>
              {liveStats?.recent_friend_activities > 0 && (
                <Badge variant="secondary" className="ml-1 sm:ml-2 text-xs">{liveStats.recent_friend_activities}</Badge>
              )}
            </Button>
          </div>
        </div>

        {/* **NEW: Auto-refresh Controls** */}
        <div className="flex items-center space-x-3">
          <Button
            onClick={toggleAutoRefresh}
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            className="flex items-center space-x-2"
          >
            <span className={`w-2 h-2 rounded-full ${autoRefresh ? 'bg-green-500' : 'bg-gray-400'}`}></span>
            <span>{autoRefresh ? 'Live' : 'Paused'}</span>
          </Button>
          <Button
            onClick={fetchAllData}
            variant="outline"
            size="sm"
          >
            <ArrowUpIcon className="w-4 h-4" />
          </Button>
          {liveStats?.last_updated && (
            <span className="text-xs text-gray-500">
              Updated {formatTimeAgo(liveStats.last_updated)}
            </span>
          )}
        </div>
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
                <div className="text-2xl font-bold">{friends ? friends.length : 0}</div>
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
                <Button className="btn-primary flex items-center gap-2 text-sm sm:text-base px-4 sm:px-6 py-2 sm:py-3">
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
                  <Button onClick={sendInvitation} className="btn-primary flex items-center gap-2 text-sm sm:text-base px-4 sm:px-6 py-2 sm:py-3 w-full">
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
                  <Button onClick={acceptInvitation} className="btn-primary flex items-center gap-2 text-sm sm:text-base px-4 sm:px-6 py-2 sm:py-3 w-full">
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
              <CardDescription>Connected friends on EarnAura</CardDescription>
            </CardHeader>
            <CardContent>
              {!friends || friends.length === 0 ? (
                <div className="text-center py-8">
                  <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No friends yet</h3>
                  <p className="text-gray-600 mb-4">Start inviting friends to build your network!</p>
                  <Button onClick={() => setShowInviteModal(true)} className="btn-primary flex items-center gap-2 text-sm sm:text-base px-4 sm:px-6 py-2 sm:py-3">
                    <UserPlus className="w-4 h-4" />
                    Invite Your First Friend
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {friends && friends.map((friend) => (
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
                        
                        {/* Challenge Friend Button */}
                        <div className="mt-3 pt-2 border-t">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="w-full text-xs"
                            onClick={() => window.location.href = '/challenges?tab=friend_challenges&challenge_friend=' + friend.user_id}
                          >
                            <TrophyIcon className="w-3 h-3 mr-1" />
                            Challenge Friend
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Sent Invitations */}
          {invitations && invitations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Sent Invitations</CardTitle>
                <CardDescription>Track your friend invitations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {invitations && invitations.map((invitation) => (
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
                
                <div className="flex justify-center">
                  <Button 
                    onClick={shareReferralLink}
                    className="btn-primary flex items-center gap-2 text-sm sm:text-base px-4 sm:px-6 py-2 sm:py-3"
                  >
                    <HeroShareIcon className="h-4 w-4" />
                    Share
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
                    Share your unique referral link with friends anywhere - social media, messaging apps, email, or any platform
                  </p>
                </div>
                
                <div className="text-center">
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <HeroUsersIcon className="h-6 w-6 text-green-600" />
                  </div>
                  <h3 className="font-semibold mb-2">2. Friend Joins</h3>
                  <p className="text-sm text-gray-600">
                    Your friend signs up using your link and starts using EarnAura
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

      {/* **NEW: Live Activity Tab** */}
      {activeTab === 'activity' && (
        <div className="space-y-6">
          {/* Network Stats Overview */}
          {recentActivity && recentActivity.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Network Size</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-600">{liveStats?.friends_count || 0}</div>
                  <p className="text-xs text-gray-500">Connected friends</p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Total Referrals</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-emerald-600">{liveStats?.total_referrals || 0}</div>
                  <p className="text-xs text-gray-500">People joined via your link</p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-purple-600">{liveStats?.recent_friend_activities || 0}</div>
                  <p className="text-xs text-gray-500">Friend activities today</p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Auto-Refresh</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${autoRefresh ? 'text-green-600' : 'text-gray-400'}`}>
                    {autoRefresh ? 'ON' : 'OFF'}
                  </div>
                  <p className="text-xs text-gray-500">Real-time updates</p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Live Activity Feed */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Live Friend Activity
                </CardTitle>
                <Button 
                  onClick={fetchRecentActivity} 
                  variant="outline" 
                  size="sm"
                  disabled={activityLoading}
                >
                  {activityLoading ? 'Updating...' : 'Refresh'}
                </Button>
              </div>
              <CardDescription>
                See what your friends are achieving in real-time
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!recentActivity || recentActivity.length === 0 ? (
                <div className="text-center py-12">
                  <Users className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-600 mb-2">No Recent Activity</h3>
                  <p className="text-gray-500 mb-4">
                    Share your referral link to connect with friends and see their achievements here!
                  </p>
                  <Button 
                    onClick={() => setActiveTab('referrals')}
                    className="bg-emerald-600 hover:bg-emerald-700"
                  >
                    <Gift className="w-4 h-4 mr-2" />
                    Start Referring Friends
                  </Button>
                </div>
              ) : (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {recentActivity && recentActivity.map((activity, index) => (
                    <div key={index} className="flex items-start space-x-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                      <Avatar className="w-10 h-10">
                        <img 
                          src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${activity.friend_avatar}`}
                          alt={activity.friend_name}
                        />
                      </Avatar>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <h4 className="font-semibold text-gray-900 truncate">
                            {activity.friend_name}
                          </h4>
                          <span className="text-lg">{activity.emoji}</span>
                          <Badge variant="outline" className="text-xs">
                            {activity.type.replace('_', ' ')}
                          </Badge>
                        </div>
                        
                        <p className="text-sm text-gray-600 mt-1">
                          {activity.activity}
                        </p>
                        
                        {activity.description && (
                          <p className="text-xs text-gray-500 mt-1">
                            {activity.description}
                          </p>
                        )}
                      </div>
                      
                      <div className="text-right">
                        <span className="text-xs text-gray-400">
                          {formatTimeAgo(activity.timestamp)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Automatic Connection Info */}
          <Card className="border-emerald-200 bg-emerald-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-emerald-800">
                <SparklesIcon className="h-5 w-5" />
                Automatic Friend Connections
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-emerald-700">
                <h4 className="font-semibold mb-2">🎉 New Feature: Instant Friendships!</h4>
                <p className="text-sm leading-relaxed">
                  When someone registers using your referral code, you automatically become friends! 
                  No more manual invitation acceptance - instant connection and both users get bonus points. 
                  Watch this activity feed to see your network grow in real-time.
                </p>
                
                <div className="mt-4 p-3 bg-white rounded-lg border border-emerald-200">
                  <div className="flex items-center space-x-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                    <span>Automatic friendship creation ✅</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm mt-1">
                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                    <span>Instant bonus points for both users ✅</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm mt-1">
                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                    <span>Real-time activity updates ✅</span>
                  </div>
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
