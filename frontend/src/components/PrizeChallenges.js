import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Progress } from './ui/progress';
import { Gift, Clock, Zap, Star, Target, Award, TrendingUp, Calendar, Users, DollarSign, Trophy, Crown } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PrizeChallenges = () => {
  const { user } = useAuth();
  const [challenges, setChallenges] = useState([]);
  const [selectedChallenge, setSelectedChallenge] = useState(null);
  const [leaderboard, setLeaderboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [activeTab, setActiveTab] = useState("all");

  useEffect(() => {
    fetchChallenges();
  }, []);

  const fetchChallenges = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/prize-challenges`);
      setChallenges(response.data.challenges || []);
    } catch (error) {
      console.error('Error fetching challenges:', error);
    } finally {
      setLoading(false);
    }
  };

  const joinChallenge = async (challengeId) => {
    try {
      setJoining(true);
      const response = await axios.post(`${API}/prize-challenges/${challengeId}/join`);
      
      // Update the challenge status locally
      setChallenges(prev => prev.map(challenge => 
        challenge.id === challengeId 
          ? { ...challenge, is_participating: true, current_participants: (challenge.current_participants || 0) + 1 }
          : challenge
      ));

      alert(`Successfully joined challenge! ${response.data.message}`);
    } catch (error) {
      console.error('Join challenge error:', error);
      alert(error.response?.data?.detail || 'Failed to join challenge');
    } finally {
      setJoining(false);
    }
  };

  const fetchLeaderboard = async (challengeId) => {
    try {
      const response = await axios.get(`${API}/prize-challenges/${challengeId}/leaderboard`);
      setLeaderboard(response.data);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    }
  };

  const getChallengeIcon = (challengeType) => {
    switch (challengeType) {
      case 'flash': return <Zap className="w-5 h-5" />;
      case 'weekly': return <Calendar className="w-5 h-5" />;
      case 'monthly': return <Target className="w-5 h-5" />;
      case 'seasonal': return <Star className="w-5 h-5" />;
      default: return <Gift className="w-5 h-5" />;
    }
  };

  const getChallengeTypeColor = (challengeType) => {
    switch (challengeType) {
      case 'flash': return 'bg-orange-500';
      case 'weekly': return 'bg-blue-500';
      case 'monthly': return 'bg-purple-500';
      case 'seasonal': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'easy': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'hard': return 'bg-orange-100 text-orange-800';
      case 'extreme': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPrizeTypeIcon = (prizeType) => {
    switch (prizeType) {
      case 'monetary': return <DollarSign className="w-4 h-4" />;
      case 'scholarship': return <Award className="w-4 h-4" />;
      case 'points': return <Star className="w-4 h-4" />;
      case 'badge': return <Crown className="w-4 h-4" />;
      default: return <Gift className="w-4 h-4" />;
    }
  };

  const formatTimeRemaining = (seconds) => {
    if (seconds <= 0) return "Ended";
    
    const days = Math.floor(seconds / (24 * 3600));
    const hours = Math.floor((seconds % (24 * 3600)) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h remaining`;
    if (hours > 0) return `${hours}h ${minutes}m remaining`;
    return `${minutes}m remaining`;
  };

  const filteredChallenges = challenges.filter(challenge => {
    switch (activeTab) {
      case "participating":
        return challenge.is_participating;
      case "available":
        return challenge.can_join;
      case "active":
        return challenge.is_active;
      case "flash":
        return challenge.challenge_type === "flash";
      default:
        return true;
    }
  });

  const ChallengeCard = ({ challenge }) => (
    <Card className="hover:shadow-lg transition-shadow duration-200 border-l-4 border-l-purple-500 relative overflow-hidden">
      {challenge.challenge_type === 'flash' && (
        <div className="absolute top-0 right-0 bg-orange-500 text-white px-2 py-1 text-xs font-bold transform rotate-12 translate-x-2 -translate-y-2">
          ⚡ FLASH
        </div>
      )}
      
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <CardTitle className="text-xl font-bold text-gray-800 mb-2 flex items-center gap-2">
              {getChallengeIcon(challenge.challenge_type)}
              {challenge.title}
            </CardTitle>
            <p className="text-gray-600 text-sm mb-3">{challenge.description}</p>
            <div className="flex flex-wrap gap-2">
              <Badge className={`${getChallengeTypeColor(challenge.challenge_type)} text-white`}>
                {challenge.challenge_type}
              </Badge>
              <Badge className={getDifficultyColor(challenge.difficulty_level)}>
                {challenge.difficulty_level}
              </Badge>
              <Badge variant="outline" className="flex items-center gap-1">
                {getPrizeTypeIcon(challenge.prize_type)}
                {challenge.prize_type}
              </Badge>
              {challenge.is_participating && (
                <Badge variant="default" className="bg-emerald-500">
                  <Users className="w-3 h-3 mr-1" />
                  Participating
                </Badge>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-purple-600">
              ₹{(challenge.total_prize_value || 0).toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">Prize Value</div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <Target className="w-5 h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-sm font-medium">Target</div>
            <div className="text-xs text-gray-600">
              {challenge.target_value} {challenge.target_metric}
            </div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <Users className="w-5 h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-sm font-medium">Participants</div>
            <div className="text-xs text-gray-600">
              {challenge.current_participants || 0}
              {challenge.max_participants ? `/${challenge.max_participants}` : ''}
            </div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <Clock className="w-5 h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-sm font-medium">Time Left</div>
            <div className="text-xs text-gray-600">
              {formatTimeRemaining(challenge.time_to_end_seconds)}
            </div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <TrendingUp className="w-5 h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-sm font-medium">Category</div>
            <div className="text-xs text-gray-600">{challenge.challenge_category}</div>
          </div>
        </div>

        {/* Progress bar for participating challenges */}
        {challenge.is_participating && challenge.user_participation && (
          <div className="mb-4 p-3 bg-purple-50 rounded-lg border border-purple-200">
            <div className="flex justify-between text-sm mb-2">
              <span>Your Progress</span>
              <span>{challenge.user_participation.progress_percentage?.toFixed(1) || 0}%</span>
            </div>
            <Progress 
              value={challenge.user_participation.progress_percentage || 0} 
              className="h-2 mb-2"
            />
            <div className="text-xs text-gray-600">
              {challenge.user_participation.current_progress || 0} / {challenge.target_value} {challenge.target_metric}
            </div>
          </div>
        )}

        {/* Entry requirements */}
        {challenge.requirements_details && Object.keys(challenge.requirements_details).length > 0 && (
          <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="text-sm font-medium mb-2">Entry Requirements:</div>
            <div className="space-y-1">
              {challenge.requirements_details.level && (
                <div className="text-xs flex justify-between">
                  <span>Minimum Level:</span>
                  <span className={challenge.requirements_details.level.current >= challenge.requirements_details.level.required ? 'text-green-600' : 'text-red-600'}>
                    {challenge.requirements_details.level.current}/{challenge.requirements_details.level.required}
                  </span>
                </div>
              )}
              {challenge.requirements_details.streak && (
                <div className="text-xs flex justify-between">
                  <span>Minimum Streak:</span>
                  <span className={challenge.requirements_details.streak.current >= challenge.requirements_details.streak.required ? 'text-green-600' : 'text-red-600'}>
                    {challenge.requirements_details.streak.current}/{challenge.requirements_details.streak.required} days
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="space-y-2 mb-4">
          <div className="flex justify-between text-sm">
            <span>Start: {new Date(challenge.start_date).toLocaleDateString()}</span>
            <span>End: {new Date(challenge.end_date).toLocaleDateString()}</span>
          </div>
        </div>

        <div className="flex gap-2">
          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => {
                  setSelectedChallenge(challenge);
                  fetchLeaderboard(challenge.id);
                }}
              >
                <Trophy className="w-4 h-4 mr-2" />
                View Leaderboard
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Trophy className="w-5 h-5" />
                  {selectedChallenge?.title} - Leaderboard
                </DialogTitle>
              </DialogHeader>
              {leaderboard && <LeaderboardContent leaderboard={leaderboard} />}
            </DialogContent>
          </Dialog>

          {challenge.can_join && (
            <Button
              onClick={() => joinChallenge(challenge.id)}
              disabled={joining}
              className="flex-1 bg-purple-600 hover:bg-purple-700"
            >
              <Gift className="w-4 h-4 mr-2" />
              {joining ? 'Joining...' : 'Join Challenge'}
            </Button>
          )}

          {!challenge.meets_requirements && !challenge.is_participating && (
            <Button
              disabled
              variant="outline"
              className="flex-1"
            >
              Requirements Not Met
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const LeaderboardContent = ({ leaderboard }) => (
    <div className="space-y-6">
      {/* Challenge Info */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-4 rounded-lg border">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="font-bold text-purple-600 text-lg">
              ₹{(leaderboard.challenge.total_prize_value || 0).toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">Total Prize</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-purple-600 text-lg">
              {leaderboard.total_participants || 0}
            </div>
            <div className="text-sm text-gray-600">Participants</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-purple-600 text-lg">
              {leaderboard.challenge.target_value}
            </div>
            <div className="text-sm text-gray-600">{leaderboard.challenge.target_metric}</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-purple-600 text-lg">
              {formatTimeRemaining((new Date(leaderboard.challenge.end_date) - new Date()) / 1000)}
            </div>
            <div className="text-sm text-gray-600">Time Left</div>
          </div>
        </div>
      </div>

      {/* Leaderboard */}
      <div>
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Trophy className="w-5 h-5 text-yellow-500" />
          Leaderboard
        </h3>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {leaderboard.leaderboard?.map((participant, index) => (
            <div
              key={participant.user_id}
              className={`p-4 rounded-lg border ${
                participant.is_current_user 
                  ? 'bg-purple-50 border-purple-200' 
                  : 'bg-gray-50'
              }`}
            >
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                    index === 0 ? 'bg-yellow-400 text-yellow-900' : 
                    index === 1 ? 'bg-gray-300 text-gray-700' : 
                    index === 2 ? 'bg-orange-300 text-orange-900' : 'bg-gray-200 text-gray-600'
                  }`}>
                    {participant.rank}
                  </div>
                  <div>
                    <div className="font-medium flex items-center gap-2">
                      {participant.user_name}
                      {participant.is_current_user && (
                        <Badge variant="outline" className="text-xs">You</Badge>
                      )}
                      {participant.is_completed && (
                        <Badge className="bg-green-500 text-xs">✓ Completed</Badge>
                      )}
                    </div>
                    <div className="text-sm text-gray-600">{participant.campus}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-purple-600">
                    {participant.current_progress || 0}
                  </div>
                  <div className="text-xs text-gray-500">
                    {participant.progress_percentage?.toFixed(1) || 0}% complete
                  </div>
                </div>
              </div>
              
              {/* Progress bar */}
              <div className="mt-3">
                <Progress value={participant.progress_percentage || 0} className="h-2" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* User Stats */}
      {leaderboard.user_stats?.is_participating && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border">
          <h4 className="font-semibold mb-2">Your Performance</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-600">Current Rank</div>
              <div className="font-bold text-blue-600">
                #{leaderboard.user_stats.rank || 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Progress</div>
              <div className="font-bold text-purple-600">
                {leaderboard.user_stats.entry?.progress_percentage?.toFixed(1) || 0}%
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading challenges...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <Gift className="w-8 h-8 text-purple-600" />
          <h1 className="text-3xl font-bold text-gray-800">Prize-Based Challenges</h1>
        </div>
        <p className="text-gray-600 text-lg">
          Participate in exciting challenges and win amazing prizes!
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge variant="outline" className="bg-blue-50 border-blue-200">
            Level: {user?.level || 1}
          </Badge>
          <Badge variant="outline" className="bg-green-50 border-green-200">
            Streak: {user?.current_streak || 0} days
          </Badge>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:grid-cols-5">
          <TabsTrigger value="all">All Challenges</TabsTrigger>
          <TabsTrigger value="available">Available</TabsTrigger>
          <TabsTrigger value="participating">My Challenges</TabsTrigger>
          <TabsTrigger value="active">Active Now</TabsTrigger>
          <TabsTrigger value="flash">⚡ Flash</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4 mt-6">
          {filteredChallenges.length === 0 ? (
            <div className="text-center py-12">
              <Gift className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No challenges available</h3>
              <p className="text-gray-500">Check back later for new exciting challenges!</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredChallenges.map((challenge) => (
                <ChallengeCard key={challenge.id} challenge={challenge} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="available" className="space-y-4 mt-6">
          {filteredChallenges.length === 0 ? (
            <div className="text-center py-12">
              <Target className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No available challenges</h3>
              <p className="text-gray-500">Work on improving your level and streak to unlock more challenges!</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredChallenges.map((challenge) => (
                <ChallengeCard key={challenge.id} challenge={challenge} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="participating" className="space-y-4 mt-6">
          {filteredChallenges.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No active participations</h3>
              <p className="text-gray-500">Join challenges to track your progress here!</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredChallenges.map((challenge) => (
                <ChallengeCard key={challenge.id} challenge={challenge} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="active" className="space-y-4 mt-6">
          {filteredChallenges.length === 0 ? (
            <div className="text-center py-12">
              <Clock className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No active challenges</h3>
              <p className="text-gray-500">Stay tuned for upcoming active challenges!</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredChallenges.map((challenge) => (
                <ChallengeCard key={challenge.id} challenge={challenge} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="flash" className="space-y-4 mt-6">
          {filteredChallenges.length === 0 ? (
            <div className="text-center py-12">
              <Zap className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No flash challenges</h3>
              <p className="text-gray-500">Flash challenges appear for limited time with exciting rewards!</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredChallenges.map((challenge) => (
                <ChallengeCard key={challenge.id} challenge={challenge} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PrizeChallenges;
