import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Progress } from './ui/progress';
import { Gift, Clock, Zap, Star, Target, Award, TrendingUp, Calendar, Users, DollarSign, Trophy, Crown, Edit, Trash2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Utility function to format target metrics
const formatTargetMetric = (target_metric, target_value = null) => {
  const metricLabels = {
    'savings_amount': 'Savings Amount',
    'transaction_count': 'Transactions',
    'streak_days': 'Streak Days',
    'goals_completed': 'Goals Completed',
    'achievement_points': 'Achievement Points',
    'monthly_income': 'Monthly Income'
  };
  
  const label = metricLabels[target_metric] || target_metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  
  if (target_value && (target_metric.includes('savings') || target_metric.includes('amount') || target_metric.includes('income'))) {
    return `₹${target_value.toLocaleString()}`;
  } else if (target_value) {
    return `${target_value} ${label}`;
  }
  
  return label;
};

const PrizeChallenges = () => {
  const { user } = useAuth();
  const [challenges, setChallenges] = useState([]);
  const [selectedChallenge, setSelectedChallenge] = useState(null);
  const [leaderboard, setLeaderboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  const [editingChallenge, setEditingChallenge] = useState(null);
  const [deleting, setDeleting] = useState(false);
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

      alert(`Successfully registered! ${response.data.message || 'You have been registered for this challenge.'}`);
    } catch (error) {
      console.error('Join challenge error:', error);
      alert(error.response?.data?.detail || 'Failed to register for challenge');
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

  const updateChallenge = async (challengeId, updatedData) => {
    try {
      const response = await axios.put(`${API}/prize-challenges/${challengeId}`, updatedData);
      
      // Update the challenge in the local state
      setChallenges(prev => prev.map(challenge => 
        challenge.id === challengeId 
          ? { ...challenge, ...response.data.challenge }
          : challenge
      ));
      
      alert('Challenge updated successfully!');
      setEditingChallenge(null);
    } catch (error) {
      console.error('Update error:', error);
      alert(error.response?.data?.detail || 'Failed to update challenge');
    }
  };

  const deleteChallenge = async (challengeId) => {
    if (!window.confirm('Are you sure you want to delete this challenge? This action cannot be undone.')) {
      return;
    }

    try {
      setDeleting(true);
      await axios.delete(`${API}/prize-challenges/${challengeId}`);
      
      // Remove the challenge from local state
      setChallenges(prev => prev.filter(challenge => challenge.id !== challengeId));
      
      alert('Challenge deleted successfully!');
    } catch (error) {
      console.error('Delete error:', error);
      alert(error.response?.data?.detail || 'Failed to delete challenge');
    } finally {
      setDeleting(false);
    }
  };

  // Check if user can edit/delete challenge (creator or super admin)
  const canManageChallenge = (challenge) => {
    return user && (
      challenge.creator_id === user.id || 
      user.is_admin || 
      user.is_super_admin ||
      user.admin_level === 'super_admin'
    );
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
      case "all":
        return true;
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
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg sm:text-xl font-bold text-gray-800 mb-3 flex items-center gap-2 flex-wrap break-words leading-relaxed">
              <span className="flex-shrink-0">{getChallengeIcon(challenge.challenge_type)}</span>
              <span className="break-words">{challenge.title}</span>
            </CardTitle>
            <p className="text-gray-600 text-sm mb-3 break-words leading-relaxed">{challenge.description}</p>
            <div className="flex flex-wrap gap-2">
              <Badge className={`${getChallengeTypeColor(challenge.challenge_type)} text-white flex-shrink-0`}>
                {challenge.challenge_type}
              </Badge>
              <Badge className={`${getDifficultyColor(challenge.difficulty_level)} flex-shrink-0`}>
                {challenge.difficulty_level}
              </Badge>
              <Badge variant="outline" className="flex items-center gap-1 flex-shrink-0">
                {getPrizeTypeIcon(challenge.prize_type)}
                <span className="whitespace-nowrap">{challenge.prize_type}</span>
              </Badge>
              {challenge.is_participating && (
                <Badge variant="default" className="bg-emerald-500 flex-shrink-0">
                  <Users className="w-3 h-3 mr-1" />
                  <span className="whitespace-nowrap">Participating</span>
                </Badge>
              )}
            </div>
          </div>
          <div className="text-left sm:text-right flex-shrink-0">
            <div className="text-xl sm:text-2xl font-bold text-purple-600 break-words">
              ₹{(challenge.total_prize_value || 0).toLocaleString()}
            </div>
            <div className="text-sm text-gray-500 whitespace-nowrap">Prize Value</div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3 mb-4">
          <div className="text-center p-2 sm:p-3 bg-gray-50 rounded-lg">
            <Target className="w-4 h-4 sm:w-5 sm:h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-xs sm:text-sm font-medium mb-1">Target</div>
            <div className="text-xs text-gray-600 break-words leading-tight">
              {formatTargetMetric(challenge.target_metric, challenge.target_value)}
            </div>
          </div>
          <div className="text-center p-2 sm:p-3 bg-gray-50 rounded-lg">
            <Users className="w-4 h-4 sm:w-5 sm:h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-xs sm:text-sm font-medium mb-1">Participants</div>
            <div className="text-xs text-gray-600 break-words leading-tight">
              {challenge.current_participants || 0}
              {challenge.max_participants ? `/${challenge.max_participants}` : ''}
            </div>
          </div>
          <div className="text-center p-2 sm:p-3 bg-gray-50 rounded-lg">
            <Clock className="w-4 h-4 sm:w-5 sm:h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-xs sm:text-sm font-medium mb-1">Time Left</div>
            <div className="text-xs text-gray-600 break-words leading-tight">
              {formatTimeRemaining(challenge.time_to_end_seconds)}
            </div>
          </div>
          <div className="text-center p-2 sm:p-3 bg-gray-50 rounded-lg">
            <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-xs sm:text-sm font-medium mb-1">Category</div>
            <div className="text-xs text-gray-600 break-words leading-tight">{challenge.challenge_category}</div>
          </div>
        </div>

        {/* Progress bar for participating challenges */}
        {challenge.is_participating && challenge.user_participation && (
          <div className="mb-4 p-3 bg-purple-50 rounded-lg border border-purple-200">
            <div className="flex justify-between text-xs sm:text-sm mb-2 gap-2">
              <span className="break-words">Your Progress</span>
              <span className="whitespace-nowrap">{challenge.user_participation.progress_percentage?.toFixed(1) || 0}%</span>
            </div>
            <Progress 
              value={challenge.user_participation.progress_percentage || 0} 
              className="h-2 mb-2"
            />
            <div className="text-xs text-gray-600 break-words leading-relaxed">
              {challenge.user_participation.current_progress || 0} / {formatTargetMetric(challenge.target_metric, challenge.target_value)}
            </div>
          </div>
        )}

        {/* Entry requirements */}
        {challenge.requirements_details && Object.keys(challenge.requirements_details).length > 0 && (
          <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="text-xs sm:text-sm font-medium mb-2 break-words">Entry Requirements:</div>
            <div className="space-y-2">
              {challenge.requirements_details.level && (
                <div className="text-xs flex justify-between gap-2 flex-wrap">
                  <span className="break-words">Minimum Level:</span>
                  <span className={`whitespace-nowrap ${challenge.requirements_details.level.current >= challenge.requirements_details.level.required ? 'text-green-600' : 'text-red-600'}`}>
                    {challenge.requirements_details.level.current}/{challenge.requirements_details.level.required}
                  </span>
                </div>
              )}
              {challenge.requirements_details.streak && (
                <div className="text-xs flex justify-between gap-2 flex-wrap">
                  <span className="break-words">Minimum Streak:</span>
                  <span className={`whitespace-nowrap ${challenge.requirements_details.streak.current >= challenge.requirements_details.streak.required ? 'text-green-600' : 'text-red-600'}`}>
                    {challenge.requirements_details.streak.current}/{challenge.requirements_details.streak.required} days
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="space-y-2 mb-4">
          <div className="flex flex-col sm:flex-row sm:justify-between text-xs sm:text-sm gap-1">
            <span className="break-words">Start: {new Date(challenge.start_date).toLocaleDateString()}</span>
            <span className="break-words">End: {new Date(challenge.end_date).toLocaleDateString()}</span>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-2">
          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="outline"
                className="w-full sm:flex-1"
                onClick={() => {
                  setSelectedChallenge(challenge);
                  fetchLeaderboard(challenge.id);
                }}
              >
                <Trophy className="w-4 h-4 mr-2 flex-shrink-0" />
                <span className="whitespace-nowrap">View Leaderboard</span>
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2 flex-wrap break-words leading-relaxed pr-8">
                  <Trophy className="w-5 h-5 flex-shrink-0" />
                  <span className="break-words">{selectedChallenge?.title} - Leaderboard</span>
                </DialogTitle>
              </DialogHeader>
              {leaderboard && <LeaderboardContent leaderboard={leaderboard} />}
            </DialogContent>
          </Dialog>

          {/* Registration button logic */}
          {challenge.is_participating ? (
            <Button
              disabled
              className="w-full sm:flex-1 bg-emerald-500 cursor-not-allowed opacity-75"
            >
              <Users className="w-4 h-4 mr-2 flex-shrink-0" />
              <span className="whitespace-nowrap">Already Registered</span>
            </Button>
          ) : challenge.can_join ? (
            <Button
              onClick={() => joinChallenge(challenge.id)}
              disabled={joining}
              className="w-full sm:flex-1 bg-purple-600 hover:bg-purple-700"
            >
              <Gift className="w-4 h-4 mr-2 flex-shrink-0" />
              <span className="whitespace-nowrap">{joining ? 'Registering...' : 'Register Now'}</span>
            </Button>
          ) : !challenge.meets_requirements ? (
            <Button
              disabled
              variant="outline"
              className="w-full sm:flex-1"
            >
              <span className="break-words text-center w-full">Requirements Not Met</span>
            </Button>
          ) : challenge.time_to_start_seconds > 0 ? (
            <Button
              disabled
              variant="outline"
              className="w-full sm:flex-1"
            >
              <Clock className="w-4 h-4 mr-2 flex-shrink-0" />
              <span className="whitespace-nowrap">Opens Soon</span>
            </Button>
          ) : challenge.time_to_end_seconds <= 0 ? (
            <Button
              disabled
              variant="outline"
              className="w-full sm:flex-1"
            >
              <span className="whitespace-nowrap">Challenge Ended</span>
            </Button>
          ) : (
            <Button
              disabled
              variant="outline"
              className="w-full sm:flex-1"
            >
              <span className="whitespace-nowrap">Not Available</span>
            </Button>
          )}

          {/* Edit/Delete buttons for creators and super admins */}
          {canManageChallenge(challenge) && (
            <>
              <Button
                variant="outline"
                onClick={() => setEditingChallenge(challenge)}
                className="flex-shrink-0"
                title="Edit Challenge"
              >
                <Edit className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                onClick={() => deleteChallenge(challenge.id)}
                disabled={deleting}
                className="flex-shrink-0 border-red-200 text-red-600 hover:bg-red-50"
                title="Delete Challenge"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const EditChallengeDialog = ({ challenge, onSave, onCancel }) => {
    const [formData, setFormData] = useState({
      title: challenge.title || '',
      description: challenge.description || '',
      challenge_type: challenge.challenge_type || 'weekly',
      challenge_category: challenge.challenge_category || 'savings',
      difficulty_level: challenge.difficulty_level || 'medium',
      target_metric: challenge.target_metric || 'savings_amount',
      target_value: challenge.target_value || '',
      start_date: challenge.start_date ? new Date(challenge.start_date).toISOString().slice(0, 16) : '',
      end_date: challenge.end_date ? new Date(challenge.end_date).toISOString().slice(0, 16) : '',
      duration_hours: challenge.duration_hours || 0,
      max_participants: challenge.max_participants || '',
      entry_requirements: challenge.entry_requirements || {
        min_level: 1,
        min_savings: 0,
        required_badges: []
      },
      prize_type: challenge.prize_type || 'cash',
      total_prize_value: challenge.total_prize_value || '',
      prize_structure: challenge.prize_structure || {
        first: 40,
        second: 30,
        third: 20,
        participation: 10
      }
    });

    const handleSubmit = (e) => {
      e.preventDefault();
      onSave(challenge.id, formData);
    };

    return (
      <Dialog open={true} onOpenChange={onCancel}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Edit className="w-5 h-5" />
              Edit Challenge
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Challenge Title *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Challenge Category *</label>
                <select
                  value={formData.challenge_category}
                  onChange={(e) => setFormData({ ...formData, challenge_category: e.target.value })}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  required
                >
                  <option value="">Select Category</option>
                  <option value="savings">💰 Savings Challenge</option>
                  <option value="budgeting">📊 Budgeting Challenge</option>
                  <option value="earning">💼 Earning Challenge</option>
                  <option value="investment">📈 Investment Challenge</option>
                  <option value="streak">🔥 Streak Challenge</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Description *</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                required
              />
            </div>

            {/* Challenge Type and Difficulty */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Challenge Type *</label>
                <select
                  value={formData.challenge_type}
                  onChange={(e) => setFormData({ ...formData, challenge_type: e.target.value })}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  required
                >
                  <option value="">Select Type</option>
                  <option value="daily">⚡ Daily Challenge</option>
                  <option value="weekly">📅 Weekly Challenge</option>
                  <option value="monthly">🗓️ Monthly Challenge</option>
                  <option value="flash">💥 Flash Challenge</option>
                  <option value="seasonal">🌟 Seasonal Challenge</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Difficulty Level *</label>
                <select
                  value={formData.difficulty_level}
                  onChange={(e) => setFormData({ ...formData, difficulty_level: e.target.value })}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  required
                >
                  <option value="beginner">🌱 Beginner</option>
                  <option value="easy">😊 Easy</option>
                  <option value="medium">🎯 Medium</option>
                  <option value="hard">💪 Hard</option>
                  <option value="extreme">🔥 Extreme</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Max Participants</label>
                <input
                  type="number"
                  value={formData.max_participants}
                  onChange={(e) => setFormData({ ...formData, max_participants: e.target.value })}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Leave empty for unlimited"
                  min="1"
                />
              </div>
            </div>

            {/* Target and Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Target Metric *</label>
                <select
                  value={formData.target_metric}
                  onChange={(e) => setFormData({ ...formData, target_metric: e.target.value })}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  required
                >
                  <option value="">Select Metric</option>
                  <option value="savings_amount">💵 Savings Amount (₹)</option>
                  <option value="transaction_count">💳 Transaction Count</option>
                  <option value="streak_days">🔥 Streak Days</option>
                  <option value="goals_completed">🎯 Goals Completed</option>
                  <option value="monthly_income">💼 Monthly Income</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Target Value *</label>
                <input
                  type="number"
                  value={formData.target_value}
                  onChange={(e) => setFormData({ ...formData, target_value: e.target.value })}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="e.g., 5000"
                  required
                />
              </div>
            </div>

            {/* Dates */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Challenge Start *</label>
                <input
                  type="datetime-local"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Challenge End *</label>
                <input
                  type="datetime-local"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  required
                />
              </div>
            </div>

            {/* Prize Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Prize Type *</label>
                <select
                  value={formData.prize_type}
                  onChange={(e) => setFormData({ ...formData, prize_type: e.target.value })}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  required
                >
                  <option value="">Select Prize Type</option>
                  <option value="cash">💰 Cash Prize</option>
                  <option value="voucher">🎫 Vouchers</option>
                  <option value="badge">🏆 Badges & Recognition</option>
                  <option value="points">⭐ Achievement Points</option>
                  <option value="mixed">🎁 Mixed Rewards</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Total Prize Value (₹) *</label>
                <input
                  type="number"
                  value={formData.total_prize_value}
                  onChange={(e) => setFormData({ ...formData, total_prize_value: e.target.value })}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  min="0"
                  required
                />
              </div>
            </div>

            {/* Prize Distribution */}
            <div>
              <label className="block text-sm font-medium mb-2">Prize Distribution (%)</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">First Place (%)</label>
                  <input
                    type="number"
                    value={formData.prize_structure.first}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      prize_structure: { 
                        ...formData.prize_structure, 
                        first: parseInt(e.target.value) || 0 
                      } 
                    })}
                    className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    min="0"
                    max="100"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Second Place (%)</label>
                  <input
                    type="number"
                    value={formData.prize_structure.second}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      prize_structure: { 
                        ...formData.prize_structure, 
                        second: parseInt(e.target.value) || 0 
                      } 
                    })}
                    className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    min="0"
                    max="100"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Third Place (%)</label>
                  <input
                    type="number"
                    value={formData.prize_structure.third}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      prize_structure: { 
                        ...formData.prize_structure, 
                        third: parseInt(e.target.value) || 0 
                      } 
                    })}
                    className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    min="0"
                    max="100"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Participation (%)</label>
                  <input
                    type="number"
                    value={formData.prize_structure.participation}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      prize_structure: { 
                        ...formData.prize_structure, 
                        participation: parseInt(e.target.value) || 0 
                      } 
                    })}
                    className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    min="0"
                    max="100"
                  />
                </div>
              </div>
            </div>

            {/* Entry Requirements */}
            <div>
              <label className="block text-sm font-medium mb-2">Entry Requirements</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Minimum Level</label>
                  <input
                    type="number"
                    value={formData.entry_requirements.min_level}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      entry_requirements: { 
                        ...formData.entry_requirements, 
                        min_level: parseInt(e.target.value) || 1 
                      } 
                    })}
                    className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    min="1"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Minimum Savings (₹)</label>
                  <input
                    type="number"
                    value={formData.entry_requirements.min_savings}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      entry_requirements: { 
                        ...formData.entry_requirements, 
                        min_savings: parseInt(e.target.value) || 0 
                      } 
                    })}
                    className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    min="0"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" className="flex-1 bg-purple-600 hover:bg-purple-700">
                Save Changes
              </Button>
              <Button type="button" variant="outline" onClick={onCancel} className="flex-1">
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    );
  };

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
      {/* Edit Challenge Dialog */}
      {editingChallenge && (
        <EditChallengeDialog 
          challenge={editingChallenge}
          onSave={updateChallenge}
          onCancel={() => setEditingChallenge(null)}
        />
      )}

      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4 flex-wrap">
          <Gift className="w-6 h-6 sm:w-8 sm:h-8 text-purple-600 flex-shrink-0" />
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-800 break-words leading-tight">Prize-Based Challenges</h1>
        </div>
        <p className="text-gray-600 text-base sm:text-lg break-words leading-relaxed mb-3">
          Participate in exciting challenges and win amazing prizes!
        </p>
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" className="bg-blue-50 border-blue-200 whitespace-nowrap">
            Level: {user?.level || 1}
          </Badge>
          <Badge variant="outline" className="bg-green-50 border-green-200 whitespace-nowrap">
            Streak: {user?.current_streak || 0} days
          </Badge>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <div className="overflow-x-auto scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0">
          <TabsList className="inline-flex w-auto min-w-full sm:w-auto gap-2">
            <TabsTrigger value="all" className="text-xs sm:text-sm whitespace-nowrap flex-shrink-0">All Challenges</TabsTrigger>
            <TabsTrigger value="available" className="text-xs sm:text-sm whitespace-nowrap flex-shrink-0">Available</TabsTrigger>
            <TabsTrigger value="participating" className="text-xs sm:text-sm whitespace-nowrap flex-shrink-0">My Challenges</TabsTrigger>
            <TabsTrigger value="active" className="text-xs sm:text-sm whitespace-nowrap flex-shrink-0">Active Now</TabsTrigger>
            <TabsTrigger value="flash" className="text-xs sm:text-sm whitespace-nowrap flex-shrink-0">⚡ Flash</TabsTrigger>
          </TabsList>
        </div>

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
