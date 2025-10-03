import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Avatar } from './ui/avatar';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Label } from './ui/label';
import { Checkbox } from './ui/checkbox';
import { toast } from '../hooks/use-toast';
import { useAuth } from '../App';
import { 
  Users, 
  Plus, 
  Target, 
  Calendar, 
  Trophy, 
  Clock, 
  MapPin, 
  TrendingUp,
  CheckCircle2,
  Star,
  Crown,
  FireIcon as Fire,
  CalendarIcon,
  ShareIcon,
  PlusIcon,
  UserGroupIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  XMarkIcon,
  ArrowTopRightOnSquareIcon,
  PencilIcon,
  TrashIcon
} from 'lucide-react';
import {
  TrophyIcon,
  FireIcon,
  CalendarIcon as HeroCalendarIcon,
  ShareIcon as HeroShareIcon,
  PlusIcon as HeroPlusIcon,
  UserGroupIcon as HeroUserGroupIcon,
  ChartBarIcon as HeroChartBarIcon,
  ClockIcon as HeroClockIcon,
  CheckCircleIcon as HeroCheckCircleIcon,
  XMarkIcon as HeroXMarkIcon,
  ArrowTopRightOnSquareIcon as HeroArrowTopRightOnSquareIcon,
  PencilIcon as HeroPencilIcon,
  TrashIcon as HeroTrashIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AllChallenges = () => {
  // Individual Challenges State
  const [challenges, setChallenges] = useState([]);
  const [myChallenges, setMyChallenges] = useState([]);
  const [myCreatedChallenges, setMyCreatedChallenges] = useState([]);
  const [selectedChallenge, setSelectedChallenge] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingChallenge, setEditingChallenge] = useState(null);
  const [showShareModal, setShowShareModal] = useState(false);
  const [joining, setJoining] = useState(null);

  // Individual Friend Challenges State (NEW)
  const [friendChallenges, setFriendChallenges] = useState([]);
  const [showFriendChallengeModal, setShowFriendChallengeModal] = useState(false);
  const [friends, setFriends] = useState([]);
  const [friendChallengeData, setFriendChallengeData] = useState({
    friend_id: '',
    challenge_type: 'savings_race',
    target_amount: '',
    duration_days: 7,
    title: '',
    description: '',
    stakes: 'Bragging rights!'
  });

  // Group Challenges State
  const [groupChallenges, setGroupChallenges] = useState([]);
  const [showGroupCreateModal, setShowGroupCreateModal] = useState(false);
  const [showGroupDetailsModal, setShowGroupDetailsModal] = useState(false);
  const [selectedGroupChallenge, setSelectedGroupChallenge] = useState(null);
  
  // General State
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('individual'); // individual, group, friend_challenges
  const { user } = useAuth();

  // Individual Challenge Form Data
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'savings',
    target_amount: '',
    duration_days: 30,
    visibility: 'public',
    max_participants: 10
  });

  // Group Challenge Form Data
  const [groupFormData, setGroupFormData] = useState({
    title: '',
    description: '',
    challenge_type: 'group_savings',
    target_amount_per_person: '',
    duration_days: 30,
    max_participants: 5,
    university_only: false
  });

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchIndividualChallenges(),
        fetchGroupChallenges(),
        fetchFriendChallenges(),
        fetchFriends()
      ]);
    } catch (error) {
      console.error('Error fetching challenges:', error);
    } finally {
      setLoading(false);
    }
  };

  // Individual Challenges Functions
  const fetchIndividualChallenges = async () => {
    try {
      const token = localStorage.getItem('token');
      const [challengesRes, myChallengesRes, myCreatedRes] = await Promise.all([
        fetch(`${API}/challenges`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API}/challenges/my-challenges`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API}/challenges/my-created`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      
      if (challengesRes.ok && myChallengesRes.ok && myCreatedRes.ok) {
        const challengesData = await challengesRes.json();
        const myChallengesData = await myChallengesRes.json();
        const myCreatedData = await myCreatedRes.json();
        
        setChallenges(challengesData.challenges || []);
        setMyChallenges(myChallengesData.challenges || []);
        setMyCreatedChallenges(myCreatedData.challenges || []);
      }
    } catch (error) {
      console.error('Error fetching individual challenges:', error);
    }
  };

  const createIndividualChallenge = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/challenges`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...formData,
          target_amount: parseFloat(formData.target_amount)
        })
      });

      if (response.ok) {
        toast({
          title: "Success!",
          description: "Challenge created successfully!"
        });
        setShowCreateModal(false);
        setFormData({
          title: '',
          description: '',
          category: 'savings',
          target_amount: '',
          duration_days: 30,
          visibility: 'public',
          max_participants: 10
        });
        fetchIndividualChallenges();
      } else {
        const error = await response.json();
        toast({
          title: "Error",
          description: error.detail || "Failed to create challenge",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error creating challenge:', error);
      toast({
        title: "Error",
        description: "Failed to create challenge",
        variant: "destructive"
      });
    }
  };

  const joinIndividualChallenge = async (challengeId) => {
    setJoining(challengeId);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/challenges/${challengeId}/join`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        toast({
          title: "Success!",
          description: "Joined challenge successfully!"
        });
        fetchIndividualChallenges();
      } else {
        const error = await response.json();
        toast({
          title: "Error",
          description: error.detail || "Failed to join challenge",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error joining challenge:', error);
      toast({
        title: "Error",
        description: "Failed to join challenge",
        variant: "destructive"
      });
    } finally {
      setJoining(null);
    }
  };

  // Individual Friend Challenges Functions (NEW)
  const fetchFriendChallenges = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/individual-challenges/my-challenges`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setFriendChallenges(data.challenges || []);
      }
    } catch (error) {
      console.error('Error fetching friend challenges:', error);
    }
  };

  const fetchFriends = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/friends`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setFriends(data.friends || []);
      }
    } catch (error) {
      console.error('Error fetching friends:', error);
    }
  };

  const createFriendChallenge = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/individual-challenges/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...friendChallengeData,
          target_amount: parseFloat(friendChallengeData.target_amount)
        })
      });

      if (response.ok) {
        const result = await response.json();
        toast({
          title: "Challenge Sent!",
          description: result.message || "Friend challenge created successfully!"
        });
        setShowFriendChallengeModal(false);
        setFriendChallengeData({
          friend_id: '',
          challenge_type: 'savings_race',
          target_amount: '',
          duration_days: 7,
          title: '',
          description: '',
          stakes: 'Bragging rights!'
        });
        fetchFriendChallenges();
      } else {
        const error = await response.json();
        toast({
          title: "Error",
          description: error.detail || "Failed to create friend challenge",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error creating friend challenge:', error);
      toast({
        title: "Error",
        description: "Failed to create friend challenge",
        variant: "destructive"
      });
    }
  };

  const respondToFriendChallenge = async (challengeId, action) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/individual-challenges/${challengeId}/respond`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ action }) // 'accept' or 'decline'
      });

      if (response.ok) {
        const result = await response.json();
        toast({
          title: action === 'accept' ? "Challenge Accepted!" : "Challenge Declined",
          description: result.message || `You have ${action}ed the challenge.`
        });
        fetchFriendChallenges();
      } else {
        const error = await response.json();
        toast({
          title: "Error",
          description: error.detail || `Failed to ${action} challenge`,
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error(`Error ${action}ing challenge:`, error);
      toast({
        title: "Error",
        description: `Failed to ${action} challenge`,
        variant: "destructive"
      });
    }
  };

  // Group Challenges Functions
  const fetchGroupChallenges = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/group-challenges`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setGroupChallenges(data.challenges || []);
      }
    } catch (error) {
      console.error('Error fetching group challenges:', error);
    }
  };

  const createGroupChallenge = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/group-challenges`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...groupFormData,
          target_amount_per_person: parseFloat(groupFormData.target_amount_per_person)
        })
      });

      if (response.ok) {
        toast({
          title: "Success!",
          description: "Group challenge created successfully!"
        });
        setShowGroupCreateModal(false);
        setGroupFormData({
          title: '',
          description: '',
          challenge_type: 'group_savings',
          target_amount_per_person: '',
          duration_days: 30,
          max_participants: 5,
          university_only: false
        });
        fetchGroupChallenges();
      } else {
        const error = await response.json();
        toast({
          title: "Error",
          description: error.detail || "Failed to create group challenge",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error creating group challenge:', error);
      toast({
        title: "Error",
        description: "Failed to create group challenge",
        variant: "destructive"
      });
    }
  };

  const joinGroupChallenge = async (challengeId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/group-challenges/${challengeId}/join`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        toast({
          title: "Success!",
          description: "Joined group challenge successfully!"
        });
        fetchGroupChallenges();
      } else {
        const error = await response.json();
        toast({
          title: "Error",
          description: error.detail || "Failed to join group challenge",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error joining group challenge:', error);
      toast({
        title: "Error",
        description: "Failed to join group challenge",
        variant: "destructive"
      });
    }
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
          <h1 className="text-3xl font-bold text-gray-900">Challenges</h1>
          <p className="text-gray-600 mt-2">Compete individually or with groups to achieve your financial goals</p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
        <Button
          onClick={() => setActiveTab('individual')}
          variant={activeTab === 'individual' ? 'default' : 'ghost'}
          className="px-6"
        >
          <Trophy className="w-4 h-4 mr-2" />
          Individual Challenges
        </Button>
        <Button
          onClick={() => setActiveTab('friend_challenges')}
          variant={activeTab === 'friend_challenges' ? 'default' : 'ghost'}
          className="px-6"
        >
          <Star className="w-4 h-4 mr-2" />
          Friend Challenges
        </Button>
        <Button
          onClick={() => setActiveTab('group')}
          variant={activeTab === 'group' ? 'default' : 'ghost'}
          className="px-6"
        >
          <Users className="w-4 h-4 mr-2" />
          Group Challenges
        </Button>
      </div>

      {/* Individual Challenges Tab */}
      {activeTab === 'individual' && (
        <div className="space-y-6">
          {/* Action Button */}
          <div className="flex justify-end">
            <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
              <DialogTrigger asChild>
                <Button className="flex items-center gap-2">
                  <Plus className="w-4 h-4" />
                  Create Challenge
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create New Challenge</DialogTitle>
                  <DialogDescription>
                    Create a personal challenge to motivate yourself
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="title">Challenge Title</Label>
                    <Input
                      id="title"
                      placeholder="e.g., Save ₹50,000 in 3 months"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      placeholder="Describe your challenge goals and motivation"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="category">Category</Label>
                      <Select value={formData.category} onValueChange={(value) => setFormData({ ...formData, category: value })}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="savings">Savings</SelectItem>
                          <SelectItem value="investment">Investment</SelectItem>
                          <SelectItem value="budgeting">Budgeting</SelectItem>
                          <SelectItem value="income">Income</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="target_amount">Target Amount (₹)</Label>
                      <Input
                        id="target_amount"
                        type="number"
                        placeholder="50000"
                        value={formData.target_amount}
                        onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="duration">Duration (days)</Label>
                      <Input
                        id="duration"
                        type="number"
                        placeholder="30"
                        value={formData.duration_days}
                        onChange={(e) => setFormData({ ...formData, duration_days: parseInt(e.target.value) })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="max_participants">Max Participants</Label>
                      <Input
                        id="max_participants"
                        type="number"
                        placeholder="10"
                        value={formData.max_participants}
                        onChange={(e) => setFormData({ ...formData, max_participants: parseInt(e.target.value) })}
                      />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="visibility">Visibility</Label>
                    <Select value={formData.visibility} onValueChange={(value) => setFormData({ ...formData, visibility: value })}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select visibility" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="public">Public</SelectItem>
                        <SelectItem value="private">Private</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button onClick={createIndividualChallenge} className="w-full">
                    Create Challenge
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Individual Challenges Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {challenges.length === 0 ? (
              <div className="col-span-full text-center py-12">
                <Trophy className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No challenges available</h3>
                <p className="text-gray-600 mb-4">Be the first to create a challenge!</p>
                <Button onClick={() => setShowCreateModal(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create First Challenge
                </Button>
              </div>
            ) : (
              challenges.map((challenge) => (
                <Card key={challenge.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <Badge variant={challenge.category === 'savings' ? 'default' : 'secondary'}>
                        {challenge.category}
                      </Badge>
                      <Badge variant="outline">
                        {challenge.status}
                      </Badge>
                    </div>
                    <CardTitle className="text-lg">{challenge.title}</CardTitle>
                    <CardDescription>{challenge.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Target:</span>
                        <span className="font-semibold">₹{challenge.target_amount?.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Duration:</span>
                        <span className="font-semibold">{challenge.duration_days} days</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Participants:</span>
                        <span className="font-semibold">{challenge.current_participants}/{challenge.max_participants}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Created by:</span>
                        <span className="font-semibold">{challenge.creator_name}</span>
                      </div>
                      
                      <Button 
                        onClick={() => joinIndividualChallenge(challenge.id)}
                        disabled={joining === challenge.id}
                        className="w-full"
                      >
                        {joining === challenge.id ? 'Joining...' : 'Join Challenge'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>

          {/* My Challenges Section */}
          {myChallenges.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">My Challenges</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {myChallenges.map((challenge) => (
                  <Card key={challenge.id} className="border-emerald-200 bg-emerald-50">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <Badge className="bg-emerald-600">
                          {challenge.category}
                        </Badge>
                        <Badge variant="outline">
                          {challenge.status}
                        </Badge>
                      </div>
                      <CardTitle className="text-lg">{challenge.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <div className="flex justify-between text-sm mb-2">
                            <span>Progress</span>
                            <span>{challenge.progress_percentage}%</span>
                          </div>
                          <Progress value={challenge.progress_percentage} className="h-2" />
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-500">Current:</span>
                          <span className="font-semibold">₹{challenge.current_amount?.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-500">Target:</span>
                          <span className="font-semibold">₹{challenge.target_amount?.toLocaleString()}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Group Challenges Tab */}
      {activeTab === 'group' && (
        <div className="space-y-6">
          {/* Action Button */}
          <div className="flex justify-end">
            <Dialog open={showGroupCreateModal} onOpenChange={setShowGroupCreateModal}>
              <DialogTrigger asChild>
                <Button className="flex items-center gap-2">
                  <Plus className="w-4 h-4" />
                  Create Group Challenge
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create Group Challenge</DialogTitle>
                  <DialogDescription>
                    Create a challenge for teams to compete together
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="group_title">Challenge Title</Label>
                    <Input
                      id="group_title"
                      placeholder="e.g., Team Savings Challenge"
                      value={groupFormData.title}
                      onChange={(e) => setGroupFormData({ ...groupFormData, title: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label htmlFor="group_description">Description</Label>
                    <Textarea
                      id="group_description"
                      placeholder="Describe the group challenge"
                      value={groupFormData.description}
                      onChange={(e) => setGroupFormData({ ...groupFormData, description: e.target.value })}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="challenge_type">Challenge Type</Label>
                      <Select 
                        value={groupFormData.challenge_type} 
                        onValueChange={(value) => setGroupFormData({ ...groupFormData, challenge_type: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="group_savings">Group Savings</SelectItem>
                          <SelectItem value="group_streak">Group Streak</SelectItem>
                          <SelectItem value="group_goals">Group Goals</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="target_per_person">Target per Person (₹)</Label>
                      <Input
                        id="target_per_person"
                        type="number"
                        placeholder="10000"
                        value={groupFormData.target_amount_per_person}
                        onChange={(e) => setGroupFormData({ ...groupFormData, target_amount_per_person: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="group_duration">Duration (days)</Label>
                      <Input
                        id="group_duration"
                        type="number"
                        placeholder="30"
                        value={groupFormData.duration_days}
                        onChange={(e) => setGroupFormData({ ...groupFormData, duration_days: parseInt(e.target.value) })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="group_max_participants">Max Participants</Label>
                      <Input
                        id="group_max_participants"
                        type="number"
                        placeholder="5"
                        value={groupFormData.max_participants}
                        onChange={(e) => setGroupFormData({ ...groupFormData, max_participants: parseInt(e.target.value) })}
                      />
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="university_only"
                      checked={groupFormData.university_only}
                      onCheckedChange={(checked) => setGroupFormData({ ...groupFormData, university_only: checked })}
                    />
                    <Label htmlFor="university_only">University students only</Label>
                  </div>
                  <Button onClick={createGroupChallenge} className="w-full">
                    Create Group Challenge
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Group Challenges Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {groupChallenges.length === 0 ? (
              <div className="col-span-full text-center py-12">
                <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No group challenges available</h3>
                <p className="text-gray-600 mb-4">Create the first group challenge!</p>
                <Button onClick={() => setShowGroupCreateModal(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create First Group Challenge
                </Button>
              </div>
            ) : (
              groupChallenges.map((challenge) => (
                <Card key={challenge.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <Badge variant={challenge.challenge_type === 'group_savings' ? 'default' : 'secondary'}>
                        {challenge.challenge_type.replace('group_', '')}
                      </Badge>
                      <Badge variant="outline">
                        {challenge.status}
                      </Badge>
                    </div>
                    <CardTitle className="text-lg">{challenge.title}</CardTitle>
                    <CardDescription>{challenge.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Target per person:</span>
                        <span className="font-semibold">₹{challenge.target_amount_per_person?.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Duration:</span>
                        <span className="font-semibold">{challenge.duration_days} days</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Participants:</span>
                        <span className="font-semibold">{challenge.current_participants}/{challenge.max_participants}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Created by:</span>
                        <span className="font-semibold">{challenge.creator_name}</span>
                      </div>
                      {challenge.university_only && (
                        <div className="flex items-center gap-2">
                          <MapPin className="w-4 h-4 text-blue-500" />
                          <span className="text-sm text-blue-600">University students only</span>
                        </div>
                      )}
                      
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Group Progress</span>
                          <span>{challenge.group_progress_percentage}%</span>
                        </div>
                        <Progress value={challenge.group_progress_percentage} className="h-2" />
                      </div>
                      
                      <div className="flex gap-2">
                        <Button 
                          onClick={() => joinGroupChallenge(challenge.id)}
                          className="flex-1"
                          disabled={challenge.current_participants >= challenge.max_participants}
                        >
                          {challenge.current_participants >= challenge.max_participants ? 'Full' : 'Join'}
                        </Button>
                        <Button 
                          onClick={() => {
                            setSelectedGroupChallenge(challenge);
                            setShowGroupDetailsModal(true);
                          }}
                          variant="outline"
                          size="sm"
                        >
                          Details
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* Friend Challenges Tab */}
      {activeTab === 'friend_challenges' && (
        <div className="space-y-6">
          {/* Action Button */}
          <div className="flex justify-end">
            <Dialog open={showFriendChallengeModal} onOpenChange={setShowFriendChallengeModal}>
              <DialogTrigger asChild>
                <Button className="flex items-center gap-2">
                  <Star className="w-4 h-4" />
                  Challenge a Friend
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Challenge a Friend</DialogTitle>
                  <DialogDescription>
                    Send a 1-on-1 challenge to one of your friends
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="friend_select">Select Friend</Label>
                    <Select 
                      value={friendChallengeData.friend_id} 
                      onValueChange={(value) => setFriendChallengeData({ ...friendChallengeData, friend_id: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Choose a friend to challenge" />
                      </SelectTrigger>
                      <SelectContent>
                        {friends.map((friend) => (
                          <SelectItem key={friend.user_id} value={friend.user_id}>
                            <div className="flex items-center gap-2">
                              <span>{friend.full_name}</span>
                              {friend.university && (
                                <span className="text-xs text-gray-500">• {friend.university}</span>
                              )}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="challenge_title">Challenge Title</Label>
                    <Input
                      id="challenge_title"
                      placeholder="e.g., Save ₹5,000 in 7 days"
                      value={friendChallengeData.title}
                      onChange={(e) => setFriendChallengeData({ ...friendChallengeData, title: e.target.value })}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="challenge_type">Challenge Type</Label>
                      <Select 
                        value={friendChallengeData.challenge_type} 
                        onValueChange={(value) => setFriendChallengeData({ ...friendChallengeData, challenge_type: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="savings_race">💰 Savings Race</SelectItem>
                          <SelectItem value="streak_battle">🔥 Streak Battle</SelectItem>
                          <SelectItem value="expense_limit">📊 Expense Limit</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="target_amount">Target Amount (₹)</Label>
                      <Input
                        id="target_amount"
                        type="number"
                        placeholder="5000"
                        value={friendChallengeData.target_amount}
                        onChange={(e) => setFriendChallengeData({ ...friendChallengeData, target_amount: e.target.value })}
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="duration_days">Duration (Days)</Label>
                    <Select 
                      value={friendChallengeData.duration_days.toString()} 
                      onValueChange={(value) => setFriendChallengeData({ ...friendChallengeData, duration_days: parseInt(value) })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select duration" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="3">3 Days</SelectItem>
                        <SelectItem value="7">1 Week</SelectItem>
                        <SelectItem value="14">2 Weeks</SelectItem>
                        <SelectItem value="30">1 Month</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      placeholder="Add some motivation or details about the challenge..."
                      value={friendChallengeData.description}
                      onChange={(e) => setFriendChallengeData({ ...friendChallengeData, description: e.target.value })}
                    />
                  </div>

                  <div>
                    <Label htmlFor="stakes">Stakes</Label>
                    <Input
                      id="stakes"
                      placeholder="e.g., Loser buys coffee!"
                      value={friendChallengeData.stakes}
                      onChange={(e) => setFriendChallengeData({ ...friendChallengeData, stakes: e.target.value })}
                    />
                  </div>

                  <div className="flex gap-3">
                    <Button variant="outline" onClick={() => setShowFriendChallengeModal(false)} className="flex-1">
                      Cancel
                    </Button>
                    <Button 
                      onClick={createFriendChallenge} 
                      className="flex-1"
                      disabled={!friendChallengeData.friend_id || !friendChallengeData.title}
                    >
                      Send Challenge
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Friend Challenges List */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {friendChallenges.length > 0 ? (
              friendChallenges.map((challenge) => (
                <Card key={challenge.challenge_id} className="border-l-4 border-l-yellow-400">
                  <CardContent className="p-4">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold">{challenge.title}</h3>
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Clock className="w-3 h-3" />
                            <span>{challenge.duration_days} days</span>
                          </div>
                        </div>
                        <Badge 
                          variant={
                            challenge.status === 'pending' ? 'secondary' : 
                            challenge.status === 'active' ? 'default' : 
                            challenge.status === 'completed' ? 'outline' : 'destructive'
                          }
                        >
                          {challenge.status}
                        </Badge>
                      </div>

                      {challenge.description && (
                        <p className="text-sm text-gray-600">{challenge.description}</p>
                      )}

                      <div className="flex justify-between text-sm">
                        <span>Target: ₹{challenge.target_amount?.toLocaleString()}</span>
                        <span>Stakes: {challenge.stakes}</span>
                      </div>

                      {challenge.status === 'active' && (
                        <div className="grid grid-cols-2 gap-4 pt-2 border-t">
                          <div className="text-center">
                            <p className="text-lg font-semibold">{challenge.challenger_progress}%</p>
                            <p className="text-xs text-gray-500">You</p>
                          </div>
                          <div className="text-center">
                            <p className="text-lg font-semibold">{challenge.challenged_progress}%</p>
                            <p className="text-xs text-gray-500">Friend</p>
                          </div>
                        </div>
                      )}

                      {challenge.status === 'pending' && challenge.challenged_id === user?.user_id && (
                        <div className="flex gap-2 pt-2">
                          <Button 
                            size="sm" 
                            onClick={() => respondToFriendChallenge(challenge.challenge_id, 'accept')}
                            className="flex-1"
                          >
                            Accept
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={() => respondToFriendChallenge(challenge.challenge_id, 'decline')}
                            className="flex-1"
                          >
                            Decline
                          </Button>
                        </div>
                      )}

                      {challenge.winner && (
                        <div className="pt-2 border-t text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Trophy className="w-4 h-4 text-yellow-500" />
                            <span className="font-semibold text-yellow-700">
                              {challenge.winner === user?.user_id ? 'You Won!' : 'Friend Won!'}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <div className="col-span-full text-center py-12">
                <Star className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                <h3 className="text-lg font-semibold text-gray-500 mb-2">No Friend Challenges Yet</h3>
                <p className="text-gray-400 mb-4">Challenge your friends to make saving more fun!</p>
                <Button onClick={() => setShowFriendChallengeModal(true)}>
                  <Star className="w-4 h-4 mr-2" />
                  Send Your First Challenge
                </Button>
              </div>
            )}
          </div>

          {friends.length === 0 && (
            <div className="text-center py-8 bg-gray-50 rounded-lg">
              <Users className="w-12 h-12 mx-auto text-gray-300 mb-3" />
              <h3 className="text-lg font-semibold text-gray-500 mb-2">No Friends Yet</h3>
              <p className="text-gray-400 mb-4">Add friends first to start challenging them!</p>
              <Button variant="outline" onClick={() => window.location.href = '/friends'}>
                <Users className="w-4 h-4 mr-2" />
                Manage Friends
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Group Challenge Details Modal */}
      <Dialog open={showGroupDetailsModal} onOpenChange={setShowGroupDetailsModal}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          {selectedGroupChallenge && (
            <>
              <DialogHeader>
                <DialogTitle className="text-2xl">{selectedGroupChallenge.title}</DialogTitle>
                <DialogDescription>{selectedGroupChallenge.description}</DialogDescription>
              </DialogHeader>
              <div className="space-y-6">
                {/* Challenge Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <Target className="w-8 h-8 mx-auto mb-2 text-blue-500" />
                    <p className="text-2xl font-bold">₹{selectedGroupChallenge.target_amount_per_person?.toLocaleString()}</p>
                    <p className="text-sm text-gray-500">Target per person</p>
                  </div>
                  <div className="text-center">
                    <Users className="w-8 h-8 mx-auto mb-2 text-green-500" />
                    <p className="text-2xl font-bold">{selectedGroupChallenge.current_participants}/{selectedGroupChallenge.max_participants}</p>
                    <p className="text-sm text-gray-500">Participants</p>
                  </div>
                  <div className="text-center">
                    <Calendar className="w-8 h-8 mx-auto mb-2 text-purple-500" />
                    <p className="text-2xl font-bold">{selectedGroupChallenge.duration_days}</p>
                    <p className="text-sm text-gray-500">Days</p>
                  </div>
                  <div className="text-center">
                    <TrendingUp className="w-8 h-8 mx-auto mb-2 text-orange-500" />
                    <p className="text-2xl font-bold">{selectedGroupChallenge.group_progress_percentage}%</p>
                    <p className="text-sm text-gray-500">Progress</p>
                  </div>
                </div>

                {/* Participants List */}
                {selectedGroupChallenge.participants && selectedGroupChallenge.participants.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Participants</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {selectedGroupChallenge.participants.map((participant, index) => (
                          <div key={participant.user_id} className="flex items-center justify-between p-3 border rounded-lg">
                            <div className="flex items-center space-x-3">
                              <Avatar className="w-10 h-10">
                                <img
                                  src={`https://images.unsplash.com/photo-${1472099645785 + index}-5658abf4ff4e?w=40&h=40&fit=crop&crop=face`}
                                  alt={participant.full_name}
                                  className="w-full h-full object-cover rounded-full"
                                />
                              </Avatar>
                              <div>
                                <p className="font-medium">{participant.full_name}</p>
                                <p className="text-sm text-gray-500">{participant.university}</p>
                              </div>
                              {index === 0 && <Crown className="w-5 h-5 text-yellow-500" />}
                            </div>
                            <div className="text-right">
                              <p className="font-semibold">{participant.individual_progress_percentage}%</p>
                              <p className="text-sm text-gray-500">₹{participant.current_amount?.toLocaleString()}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AllChallenges;
