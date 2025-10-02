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
import { toast } from './ui/toast';
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
  Crown
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

const GroupChallenges = () => {
  const [challenges, setChallenges] = useState([]);
  const [selectedChallenge, setSelectedChallenge] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    challenge_type: 'group_savings',
    target_amount_per_person: '',
    duration_days: 30,
    max_participants: 5,
    university_only: false
  });

  useEffect(() => {
    fetchGroupChallenges();
  }, []);

  const fetchGroupChallenges = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/group-challenges`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setChallenges(data.group_challenges);
      }
    } catch (error) {
      console.error('Error fetching group challenges:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchChallengeDetails = async (challengeId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/group-challenges/${challengeId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedChallenge(data);
        setShowDetailsModal(true);
      }
    } catch (error) {
      console.error('Error fetching challenge details:', error);
      toast({
        title: "Error",
        description: "Failed to load challenge details",
        variant: "destructive"
      });
    }
  };

  const createGroupChallenge = async () => {
    if (!formData.title || !formData.description || !formData.target_amount_per_person) {
      toast({
        title: "Error",
        description: "Please fill in all required fields",
        variant: "destructive"
      });
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/group-challenges`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...formData,
          target_amount_per_person: parseFloat(formData.target_amount_per_person)
        })
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Success!",
          description: "Group challenge created successfully"
        });
        setShowCreateModal(false);
        setFormData({
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
        throw new Error(data.detail || 'Failed to create challenge');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const joinGroupChallenge = async (challengeId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/group-challenges/${challengeId}/join`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Joined Challenge!",
          description: `Target: ₹${data.individual_target.toLocaleString()} in group of ${data.group_size}`
        });
        fetchGroupChallenges();
        if (selectedChallenge && selectedChallenge.challenge.id === challengeId) {
          fetchChallengeDetails(challengeId);
        }
      } else {
        throw new Error(data.detail || 'Failed to join challenge');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      month: 'short',
      day: 'numeric'
    });
  };

  const getChallengeTypeIcon = (type) => {
    switch (type) {
      case 'group_savings': return <Target className="w-5 h-5" />;
      case 'group_streak': return <TrendingUp className="w-5 h-5" />;
      case 'group_goals': return <Trophy className="w-5 h-5" />;
      default: return <Target className="w-5 h-5" />;
    }
  };

  const getChallengeTypeColor = (type) => {
    switch (type) {
      case 'group_savings': return 'bg-green-100 text-green-800';
      case 'group_streak': return 'bg-blue-100 text-blue-800';
      case 'group_goals': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
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
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 p-4">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded mb-4 w-1/3"></div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className="h-64 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Group Challenges</h1>
            <p className="text-gray-600">Join friends in savings challenges and compete together</p>
          </div>
          <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
            <DialogTrigger asChild>
              <Button className="bg-green-600 hover:bg-green-700">
                <Plus className="w-4 h-4 mr-2" />
                Create Challenge
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Create Group Challenge</DialogTitle>
                <DialogDescription>
                  Create a new savings challenge for your friends to join
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="title">Challenge Title</Label>
                  <Input
                    id="title"
                    placeholder="Summer Savings Challenge"
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Save for summer vacation together..."
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    rows={3}
                  />
                </div>
                <div>
                  <Label htmlFor="challenge_type">Challenge Type</Label>
                  <Select 
                    value={formData.challenge_type}
                    onValueChange={(value) => setFormData({...formData, challenge_type: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="group_savings">Group Savings</SelectItem>
                      <SelectItem value="group_streak">Group Streak</SelectItem>
                      <SelectItem value="group_goals">Group Goals</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="target_amount">Target Amount (₹)</Label>
                    <Input
                      id="target_amount"
                      type="number"
                      placeholder="5000"
                      value={formData.target_amount_per_person}
                      onChange={(e) => setFormData({...formData, target_amount_per_person: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="duration">Duration (Days)</Label>
                    <Input
                      id="duration"
                      type="number"
                      value={formData.duration_days}
                      onChange={(e) => setFormData({...formData, duration_days: parseInt(e.target.value)})}
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="max_participants">Max Participants</Label>
                  <Select 
                    value={formData.max_participants.toString()}
                    onValueChange={(value) => setFormData({...formData, max_participants: parseInt(value)})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                        <SelectItem key={num} value={num.toString()}>{num} members</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox 
                    id="university_only"
                    checked={formData.university_only}
                    onCheckedChange={(checked) => setFormData({...formData, university_only: checked})}
                  />
                  <Label htmlFor="university_only" className="text-sm">
                    Restrict to my university only
                  </Label>
                </div>
                <Button onClick={createGroupChallenge} className="w-full">
                  Create Challenge
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Challenges Grid */}
        {challenges.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <Users className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <h3 className="text-xl font-medium text-gray-900 mb-2">No Group Challenges Yet</h3>
              <p className="text-gray-600 mb-6">
                Create the first group challenge or wait for friends to create one
              </p>
              <Button onClick={() => setShowCreateModal(true)} className="bg-green-600 hover:bg-green-700">
                <Plus className="w-4 h-4 mr-2" />
                Create First Challenge
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {challenges.map((challenge) => (
              <Card 
                key={challenge.id} 
                className={`cursor-pointer transition-all hover:shadow-lg ${
                  challenge.is_joined ? 'ring-2 ring-green-200 bg-green-50' : 'hover:shadow-md'
                }`}
                onClick={() => fetchChallengeDetails(challenge.id)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Badge className={`${getChallengeTypeColor(challenge.challenge_type)} border-0`}>
                        {getChallengeTypeIcon(challenge.challenge_type)}
                        <span className="ml-1 capitalize">
                          {challenge.challenge_type.replace('group_', '')}
                        </span>
                      </Badge>
                      {challenge.is_joined && (
                        <Badge variant="secondary" className="bg-green-100 text-green-800">
                          <CheckCircle2 className="w-3 h-3 mr-1" />
                          Joined
                        </Badge>
                      )}
                    </div>
                    {challenge.is_campus_only && (
                      <Badge variant="outline" className="text-xs">
                        <MapPin className="w-3 h-3 mr-1" />
                        Campus Only
                      </Badge>
                    )}
                  </div>
                  <CardTitle className="text-lg leading-tight">{challenge.title}</CardTitle>
                  <CardDescription className="line-clamp-2">
                    {challenge.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Progress */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">Group Progress</span>
                      <span className="text-sm text-gray-600">
                        {challenge.progress_percentage}%
                      </span>
                    </div>
                    <Progress value={challenge.progress_percentage} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1">
                      ₹{challenge.total_progress_amount.toLocaleString()} of ₹{challenge.group_target_amount.toLocaleString()}
                    </p>
                  </div>

                  {/* Challenge Details */}
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="flex items-center gap-2">
                      <Target className="w-4 h-4 text-green-600" />
                      <span>₹{challenge.target_amount_per_person.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4 text-blue-600" />
                      <span>{challenge.current_participants}/{challenge.max_participants}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-purple-600" />
                      <span>{challenge.duration_days}d</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-orange-600" />
                      <span>
                        {new Date(challenge.end_date) > new Date() 
                          ? `${Math.ceil((new Date(challenge.end_date) - new Date()) / (1000 * 60 * 60 * 24))}d left`
                          : 'Ended'
                        }
                      </span>
                    </div>
                  </div>

                  {/* Creator Info */}
                  <div className="pt-2 border-t">
                    <p className="text-xs text-gray-500">
                      Created by <span className="font-medium">{challenge.creator_name}</span>
                      {challenge.creator_university && (
                        <span> • {challenge.creator_university}</span>
                      )}
                    </p>
                  </div>

                  {/* Action Button */}
                  <div className="pt-2">
                    {!challenge.is_joined && challenge.spots_remaining > 0 && new Date(challenge.end_date) > new Date() ? (
                      <Button 
                        onClick={(e) => {
                          e.stopPropagation();
                          joinGroupChallenge(challenge.id);
                        }}
                        className="w-full"
                        size="sm"
                      >
                        Join Challenge
                      </Button>
                    ) : challenge.is_joined ? (
                      <Button variant="outline" className="w-full" size="sm">
                        View Progress
                      </Button>
                    ) : challenge.spots_remaining === 0 ? (
                      <Button variant="ghost" className="w-full" size="sm" disabled>
                        Challenge Full
                      </Button>
                    ) : (
                      <Button variant="ghost" className="w-full" size="sm" disabled>
                        Challenge Ended
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Challenge Details Modal */}
        <Dialog open={showDetailsModal} onOpenChange={setShowDetailsModal}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            {selectedChallenge && (
              <>
                <DialogHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <DialogTitle className="text-xl">{selectedChallenge.challenge.title}</DialogTitle>
                      <DialogDescription className="mt-2">
                        {selectedChallenge.challenge.description}
                      </DialogDescription>
                    </div>
                    <Badge className={`${getChallengeTypeColor(selectedChallenge.challenge.challenge_type)} border-0`}>
                      {getChallengeTypeIcon(selectedChallenge.challenge.challenge_type)}
                      <span className="ml-1 capitalize">
                        {selectedChallenge.challenge.challenge_type.replace('group_', '')}
                      </span>
                    </Badge>
                  </div>
                </DialogHeader>

                <div className="space-y-6">
                  {/* Challenge Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        ₹{selectedChallenge.progress.total_amount.toLocaleString()}
                      </div>
                      <p className="text-xs text-gray-600">Total Saved</p>
                    </div>
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {selectedChallenge.progress.percentage}%
                      </div>
                      <p className="text-xs text-gray-600">Progress</p>
                    </div>
                    <div className="text-center p-3 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {selectedChallenge.progress.completed_count}
                      </div>
                      <p className="text-xs text-gray-600">Completed</p>
                    </div>
                    <div className="text-center p-3 bg-orange-50 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">
                        {selectedChallenge.days_remaining}
                      </div>
                      <p className="text-xs text-gray-600">Days Left</p>
                    </div>
                  </div>

                  {/* Overall Progress */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium">Group Progress</h4>
                      <span className="text-sm text-gray-600">
                        {selectedChallenge.progress.percentage}%
                      </span>
                    </div>
                    <Progress value={selectedChallenge.progress.percentage} className="h-3" />
                    <p className="text-sm text-gray-500 mt-1">
                      ₹{selectedChallenge.progress.total_amount.toLocaleString()} of ₹{selectedChallenge.progress.target_amount.toLocaleString()}
                    </p>
                  </div>

                  {/* Participants List */}
                  <div>
                    <h4 className="font-medium mb-3">
                      Participants ({selectedChallenge.participants.length}/{selectedChallenge.challenge.max_participants})
                    </h4>
                    <div className="space-y-3">
                      {selectedChallenge.participants
                        .sort((a, b) => b.progress_percentage - a.progress_percentage)
                        .map((participant, index) => (
                        <div key={participant.user_id} className="flex items-center justify-between p-3 border rounded-lg">
                          <div className="flex items-center gap-3">
                            {index === 0 && participant.progress_percentage === 100 && (
                              <Crown className="w-5 h-5 text-yellow-500" />
                            )}
                            <Avatar>
                              <img 
                                src={getAvatarImage(participant.avatar)} 
                                alt={participant.full_name}
                                className="w-10 h-10 rounded-full object-cover"
                              />
                            </Avatar>
                            <div>
                              <h5 className="font-medium">{participant.full_name}</h5>
                              <p className="text-sm text-gray-600">{participant.university || 'No university'}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <Badge 
                                  variant={participant.is_completed ? 'success' : 'secondary'}
                                  className="text-xs"
                                >
                                  {participant.is_completed ? (
                                    <>
                                      <CheckCircle2 className="w-3 h-3 mr-1" />
                                      Completed
                                    </>
                                  ) : (
                                    `${participant.progress_percentage}%`
                                  )}
                                </Badge>
                                {participant.points_earned > 0 && (
                                  <div className="flex items-center gap-1">
                                    <Star className="w-3 h-3 text-yellow-500" />
                                    <span className="text-xs text-gray-600">
                                      {participant.points_earned} pts
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-medium text-green-600">
                              ₹{participant.current_progress.toLocaleString()}
                            </p>
                            <p className="text-xs text-gray-500">
                              of ₹{participant.individual_target.toLocaleString()}
                            </p>
                            <div className="w-20 mt-1">
                              <Progress value={participant.progress_percentage} className="h-1" />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Join Button for non-participants */}
                  {!selectedChallenge.user_participation && selectedChallenge.spots_remaining > 0 && new Date(selectedChallenge.challenge.end_date) > new Date() && (
                    <Button 
                      onClick={() => {
                        joinGroupChallenge(selectedChallenge.challenge.id);
                        setShowDetailsModal(false);
                      }}
                      className="w-full"
                    >
                      Join This Challenge
                    </Button>
                  )}
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default GroupChallenges;
