import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import {
  TrophyIcon,
  FireIcon,
  CalendarIcon,
  ShareIcon,
  PlusIcon,
  UserGroupIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  XMarkIcon,
  ArrowTopRightOnSquareIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Challenges = () => {
  const [challenges, setChallenges] = useState([]);
  const [myChallenges, setMyChallenges] = useState([]);
  const [selectedChallenge, setSelectedChallenge] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [activeTab, setActiveTab] = useState('discover');
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [challengesRes, myChallengesRes] = await Promise.all([
        axios.get(`${API}/challenges`),
        axios.get(`${API}/challenges/my-challenges`)
      ]);
      
      setChallenges(challengesRes.data.challenges);
      setMyChallenges(myChallengesRes.data.my_challenges);
    } catch (error) {
      console.error('Error fetching challenges:', error);
    }
    setLoading(false);
  };

  const joinChallenge = async (challengeId) => {
    setJoining(challengeId);
    try {
      await axios.post(`${API}/challenges/${challengeId}/join`);
      await fetchData(); // Refresh data
    } catch (error) {
      console.error('Error joining challenge:', error);
      alert(error.response?.data?.detail || 'Failed to join challenge');
    }
    setJoining(null);
  };

  const fetchLeaderboard = async (challengeId) => {
    try {
      const response = await axios.get(`${API}/challenges/${challengeId}/leaderboard`);
      setLeaderboard(response.data);
      setSelectedChallenge(challengeId);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    }
  };

  const generateShareContent = async (challengeId, platform) => {
    try {
      const response = await axios.post(`${API}/challenges/${challengeId}/share`, null, {
        params: { share_type: platform }
      });
      
      const shareData = response.data[platform];
      
      if (platform === 'whatsapp') {
        window.open(shareData.url, '_blank');
      } else if (platform === 'twitter') {
        window.open(shareData.url, '_blank');
      } else if (platform === 'linkedin') {
        window.open(shareData.url, '_blank');
      } else if (platform === 'instagram') {
        // Copy to clipboard for Instagram
        navigator.clipboard.writeText(shareData.story_text);
        alert('Instagram story text copied to clipboard!');
      }
    } catch (error) {
      console.error('Error generating share content:', error);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDaysRemaining = (endDate) => {
    const days = Math.ceil((new Date(endDate) - new Date()) / (1000 * 60 * 60 * 24));
    return days > 0 ? `${days} days left` : 'Expired';
  };

  const getChallengeTypeIcon = (type) => {
    switch (type) {
      case 'savings':
        return <TrophyIcon className="w-5 h-5" />;
      case 'goals':
        return <CheckCircleIcon className="w-5 h-5" />;
      default:
        return <FireIcon className="w-5 h-5" />;
    }
  };

  const getChallengeTypeColor = (type) => {
    switch (type) {
      case 'savings':
        return 'text-green-600 bg-green-100';
      case 'goals':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-purple-600 bg-purple-100';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50 p-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-emerald-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading challenges...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Social Challenges</h1>
          <p className="text-gray-600 text-lg">
            Join monthly challenges, compete with friends, and build better financial habits together! 🚀
          </p>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-8 bg-gray-100 rounded-xl p-1">
          <button
            onClick={() => setActiveTab('discover')}
            className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-all ${
              activeTab === 'discover'
                ? 'bg-white text-emerald-600 shadow-sm'
                : 'text-gray-600 hover:text-emerald-600'
            }`}
          >
            <FireIcon className="w-5 h-5 inline mr-2" />
            Discover
          </button>
          <button
            onClick={() => setActiveTab('my-challenges')}
            className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-all ${
              activeTab === 'my-challenges'
                ? 'bg-white text-emerald-600 shadow-sm'
                : 'text-gray-600 hover:text-emerald-600'
            }`}
          >
            <TrophyIcon className="w-5 h-5 inline mr-2" />
            My Challenges ({myChallenges.length})
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="py-3 px-6 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 transition-colors"
          >
            <PlusIcon className="w-5 h-5 inline mr-2" />
            Create
          </button>
        </div>

        {/* Content */}
        {activeTab === 'discover' && (
          <div className="space-y-6">
            {challenges.length === 0 ? (
              <div className="text-center py-20">
                <FireIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-600 mb-2">No Active Challenges</h3>
                <p className="text-gray-500">Check back soon for new challenges!</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {challenges.map((challenge) => (
                  <div key={challenge.id} className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow p-6">
                    {/* Challenge Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className={`p-2 rounded-lg ${getChallengeTypeColor(challenge.challenge_type)}`}>
                        {getChallengeTypeIcon(challenge.challenge_type)}
                      </div>
                      <div className="text-right text-sm text-gray-500">
                        <div className="flex items-center">
                          <UserGroupIcon className="w-4 h-4 mr-1" />
                          {challenge.participant_count}
                        </div>
                      </div>
                    </div>

                    {/* Challenge Info */}
                    <h3 className="text-xl font-bold text-gray-900 mb-2">{challenge.title}</h3>
                    <p className="text-gray-600 mb-4 line-clamp-2">{challenge.description}</p>

                    {/* Target & Progress */}
                    <div className="mb-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700">
                          Target: {challenge.challenge_type === 'savings' ? formatCurrency(challenge.target_value) : `${challenge.target_value} goals`}
                        </span>
                        <span className="text-sm text-gray-500">
                          {challenge.is_joined ? `${((challenge.user_progress / challenge.target_value) * 100).toFixed(0)}%` : ''}
                        </span>
                      </div>
                      {challenge.is_joined && (
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-emerald-600 h-2 rounded-full transition-all"
                            style={{ width: `${Math.min(100, (challenge.user_progress / challenge.target_value) * 100)}%` }}
                          ></div>
                        </div>
                      )}
                    </div>

                    {/* Time Remaining */}
                    <div className="flex items-center text-sm text-gray-500 mb-4">
                      <ClockIcon className="w-4 h-4 mr-1" />
                      {formatDaysRemaining(challenge.end_date)}
                    </div>

                    {/* Actions */}
                    <div className="flex space-x-3">
                      {!challenge.is_joined ? (
                        <button
                          onClick={() => joinChallenge(challenge.id)}
                          disabled={joining === challenge.id}
                          className="flex-1 bg-emerald-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                        >
                          {joining === challenge.id ? 'Joining...' : 'Join Challenge'}
                        </button>
                      ) : (
                        <>
                          <button
                            onClick={() => fetchLeaderboard(challenge.id)}
                            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                          >
                            <ChartBarIcon className="w-4 h-4 inline mr-2" />
                            Leaderboard
                          </button>
                          <button
                            onClick={() => {
                              setSelectedChallenge(challenge.id);
                              setShowShareModal(true);
                            }}
                            className="bg-gray-100 text-gray-700 py-2 px-3 rounded-lg hover:bg-gray-200 transition-colors"
                          >
                            <ShareIcon className="w-4 h-4" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'my-challenges' && (
          <div className="space-y-6">
            {myChallenges.length === 0 ? (
              <div className="text-center py-20">
                <TrophyIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-600 mb-2">No Active Challenges</h3>
                <p className="text-gray-500 mb-4">You haven't joined any challenges yet.</p>
                <button
                  onClick={() => setActiveTab('discover')}
                  className="bg-emerald-600 text-white py-2 px-6 rounded-lg font-semibold hover:bg-emerald-700 transition-colors"
                >
                  Discover Challenges
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {myChallenges.map(({ challenge, participation, progress_percentage, user_rank, days_remaining, is_expired }) => (
                  <div key={challenge.id} className="bg-white rounded-xl shadow-lg p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <div className="flex items-center space-x-3 mb-2">
                          <div className={`p-2 rounded-lg ${getChallengeTypeColor(challenge.challenge_type)}`}>
                            {getChallengeTypeIcon(challenge.challenge_type)}
                          </div>
                          <div>
                            <h3 className="text-xl font-bold text-gray-900">{challenge.title}</h3>
                            <p className="text-gray-600">{challenge.description}</p>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-500 mb-1">Rank #{user_rank}</div>
                        <div className={`text-sm font-medium ${is_expired ? 'text-red-600' : 'text-emerald-600'}`}>
                          {is_expired ? 'Ended' : `${days_remaining} days left`}
                        </div>
                      </div>
                    </div>

                    {/* Progress */}
                    <div className="mb-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700">Progress</span>
                        <span className="text-sm text-gray-500">
                          {challenge.challenge_type === 'savings' 
                            ? `${formatCurrency(participation.current_progress)} / ${formatCurrency(challenge.target_value)}`
                            : `${participation.current_progress} / ${challenge.target_value} goals`
                          }
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full transition-all ${
                            participation.is_completed ? 'bg-green-600' : 'bg-emerald-600'
                          }`}
                          style={{ width: `${Math.min(100, progress_percentage)}%` }}
                        ></div>
                      </div>
                      <div className="text-right text-sm text-gray-500 mt-1">
                        {progress_percentage.toFixed(0)}% Complete
                      </div>
                    </div>

                    {/* Completion Status */}
                    {participation.is_completed && (
                      <div className="flex items-center space-x-2 mb-4 p-3 bg-green-50 rounded-lg">
                        <CheckCircleIcon className="w-5 h-5 text-green-600" />
                        <span className="text-green-800 font-semibold">Challenge Completed! 🎉</span>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex space-x-3">
                      <button
                        onClick={() => fetchLeaderboard(challenge.id)}
                        className="bg-blue-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                      >
                        <ChartBarIcon className="w-4 h-4 inline mr-2" />
                        View Leaderboard
                      </button>
                      <button
                        onClick={() => {
                          setSelectedChallenge(challenge.id);
                          setShowShareModal(true);
                        }}
                        className="bg-emerald-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-emerald-700 transition-colors"
                      >
                        <ShareIcon className="w-4 h-4 inline mr-2" />
                        Share Progress
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Leaderboard Modal */}
        {selectedChallenge && leaderboard.challenge && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900">{leaderboard.challenge.title}</h3>
                    <p className="text-gray-600">Leaderboard • {leaderboard.total_participants} participants</p>
                  </div>
                  <button
                    onClick={() => setSelectedChallenge(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>

                <div className="space-y-3">
                  {leaderboard.leaderboard.map((participant) => (
                    <div
                      key={participant.user_id}
                      className={`flex items-center justify-between p-4 rounded-lg ${
                        participant.is_current_user ? 'bg-emerald-50 border-2 border-emerald-200' : 'bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center space-x-4">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                          participant.rank === 1 ? 'bg-yellow-100 text-yellow-800' :
                          participant.rank === 2 ? 'bg-gray-100 text-gray-800' :
                          participant.rank === 3 ? 'bg-orange-100 text-orange-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {participant.rank}
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900">
                            {participant.user_name}
                            {participant.is_current_user && <span className="text-emerald-600 ml-2">(You)</span>}
                          </div>
                          <div className="text-sm text-gray-500">
                            {leaderboard.challenge.challenge_type === 'savings' 
                              ? formatCurrency(participant.progress)
                              : `${participant.progress} goals`
                            }
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">
                          {participant.progress_percentage.toFixed(0)}%
                        </div>
                        {participant.is_completed && (
                          <CheckCircleIcon className="w-5 h-5 text-green-600 ml-auto" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {leaderboard.user_rank && (
                  <div className="mt-6 p-4 bg-emerald-50 rounded-lg">
                    <p className="text-emerald-800 font-semibold">
                      Your Rank: #{leaderboard.user_rank} out of {leaderboard.total_participants} participants
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Share Modal */}
        {showShareModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl max-w-md w-full">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-bold text-gray-900">Share Your Progress</h3>
                  <button
                    onClick={() => setShowShareModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => generateShareContent(selectedChallenge, 'whatsapp')}
                    className="flex flex-col items-center p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
                  >
                    <div className="w-8 h-8 bg-green-600 rounded-lg mb-2 flex items-center justify-center">
                      <ShareIcon className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-sm font-medium text-green-800">WhatsApp</span>
                  </button>

                  <button
                    onClick={() => generateShareContent(selectedChallenge, 'instagram')}
                    className="flex flex-col items-center p-4 bg-pink-50 hover:bg-pink-100 rounded-lg transition-colors"
                  >
                    <div className="w-8 h-8 bg-pink-600 rounded-lg mb-2 flex items-center justify-center">
                      <ShareIcon className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-sm font-medium text-pink-800">Instagram</span>
                  </button>

                  <button
                    onClick={() => generateShareContent(selectedChallenge, 'twitter')}
                    className="flex flex-col items-center p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                  >
                    <div className="w-8 h-8 bg-blue-600 rounded-lg mb-2 flex items-center justify-center">
                      <ArrowTopRightOnSquareIcon className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-sm font-medium text-blue-800">Twitter</span>
                  </button>

                  <button
                    onClick={() => generateShareContent(selectedChallenge, 'linkedin')}
                    className="flex flex-col items-center p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                  >
                    <div className="w-8 h-8 bg-blue-700 rounded-lg mb-2 flex items-center justify-center">
                      <ArrowTopRightOnSquareIcon className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-sm font-medium text-blue-800">LinkedIn</span>
                  </button>
                </div>

                <p className="text-xs text-gray-500 mt-4 text-center">
                  Share your progress and inspire others to join the challenge!
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Create Challenge Modal */}
        <CreateChallengeModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            fetchData();
          }}
        />
      </div>
    </div>
  );
};

// Create Challenge Modal Component
const CreateChallengeModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    challenge_type: 'savings',
    target_value: '',
    duration_days: '30',
    reward_description: '',
    reward_points: '100',
    max_participants: '',
    is_campus_specific: false,
    university: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const submitData = {
        ...formData,
        target_value: parseFloat(formData.target_value),
        duration_days: parseInt(formData.duration_days),
        reward_points: parseInt(formData.reward_points),
        max_participants: formData.max_participants ? parseInt(formData.max_participants) : null
      };

      await axios.post(`${API}/challenges/create`, submitData);
      onSuccess();
    } catch (error) {
      console.error('Error creating challenge:', error);
      alert(error.response?.data?.detail || 'Failed to create challenge');
    }
    setLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit} className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-2xl font-bold text-gray-900">Create Challenge</h3>
            <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="e.g., Save ₹5000 in October"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                required
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                rows="3"
                placeholder="Describe the challenge and motivation..."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Challenge Type</label>
                <select
                  value={formData.challenge_type}
                  onChange={(e) => setFormData({ ...formData, challenge_type: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                >
                  <option value="savings">Savings Challenge</option>
                  <option value="goals">Goals Completion</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target Value {formData.challenge_type === 'savings' ? '(₹)' : '(Goals)'}
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  value={formData.target_value}
                  onChange={(e) => setFormData({ ...formData, target_value: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder={formData.challenge_type === 'savings' ? '5000' : '3'}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Duration (Days)</label>
                <input
                  type="number"
                  required
                  min="1"
                  max="365"
                  value={formData.duration_days}
                  onChange={(e) => setFormData({ ...formData, duration_days: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Participants (Optional)</label>
                <input
                  type="number"
                  min="2"
                  value={formData.max_participants}
                  onChange={(e) => setFormData({ ...formData, max_participants: e.target.value })}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="No limit"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Reward Description</label>
              <input
                type="text"
                required
                value={formData.reward_description}
                onChange={(e) => setFormData({ ...formData, reward_description: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="e.g., Savings Master Title + Badge"
              />
            </div>

            <div className="bg-yellow-50 p-4 rounded-lg">
              <p className="text-sm text-yellow-800">
                <strong>Note:</strong> User-created challenges require admin approval before becoming active. 
                Admin-created challenges go live immediately.
              </p>
            </div>
          </div>

          <div className="flex space-x-4 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-semibold transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-3 px-4 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 font-semibold transition-colors"
            >
              {loading ? 'Creating...' : 'Create Challenge'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Challenges;
