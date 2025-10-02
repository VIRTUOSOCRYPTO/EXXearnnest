import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import SocialSharing from './SocialSharing';
import {
  TrophyIcon,
  StarIcon,
  FireIcon,
  AcademicCapIcon,
  ChartBarIcon,
  UsersIcon,
  ShareIcon,
  SparklesIcon,
  CalendarIcon,
  ArrowUpIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const GamificationProfile = () => {
  const [profile, setProfile] = useState(null);
  const [leaderboards, setLeaderboards] = useState({});
  const [achievements, setAchievements] = useState([]);
  const [communityFeed, setCommunityFeed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [showSocialSharing, setShowSocialSharing] = useState(false);
  const [selectedAchievement, setSelectedAchievement] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    fetchGamificationData();
  }, []);

  const fetchGamificationData = async () => {
    try {
      const [profileRes, achievementsRes] = await Promise.all([
        axios.get(`${API}/gamification/profile`),
        axios.get(`${API}/gamification/achievements?limit=10`)
      ]);

      setProfile(profileRes.data);
      setAchievements(achievementsRes.data.achievements);
      
      // Fetch leaderboards
      await fetchLeaderboards();
      
    } catch (error) {
      console.error('Error fetching gamification data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLeaderboards = async () => {
    try {
      const [savingsRes, streakRes, pointsRes] = await Promise.all([
        axios.get(`${API}/gamification/leaderboards/savings?period=weekly&limit=10`),
        axios.get(`${API}/gamification/leaderboards/streak?period=weekly&limit=10`),
        axios.get(`${API}/gamification/leaderboards/points?period=weekly&limit=10`)
      ]);

      setLeaderboards({
        savings: savingsRes.data.leaderboard,
        streak: streakRes.data.leaderboard,
        points: pointsRes.data.leaderboard
      });
    } catch (error) {
      console.error('Error fetching leaderboards:', error);
    }
  };

  const shareAchievement = (achievement) => {
    setSelectedAchievement({
      title: achievement.title,
      description: achievement.description,
      type: achievement.type || 'achievement',
      icon: achievement.icon || '🎯',
      amount: achievement.amount || null
    });
    setShowSocialSharing(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50 flex items-center justify-center">
        <div className="bg-white rounded-xl p-8 shadow-lg">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
          <p className="text-center mt-4 text-gray-600">Loading your achievements...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50">
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="bg-white rounded-2xl p-8 shadow-lg mb-6">
            <div className="flex items-center justify-center mb-4">
              <div className="relative">
                <div className="w-24 h-24 bg-gradient-to-br from-emerald-500 to-green-600 rounded-full flex items-center justify-center shadow-xl">
                  <TrophyIcon className="w-12 h-12 text-white" />
                </div>
                {profile?.current_streak > 0 && (
                  <div className="absolute -top-2 -right-2 bg-orange-500 text-white text-sm font-bold rounded-full w-8 h-8 flex items-center justify-center">
                    {profile.current_streak}
                  </div>
                )}
              </div>
            </div>
            
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {user?.full_name || 'User'}
            </h1>
            
            <div className="flex items-center justify-center mb-4">
              <SparklesIcon className="w-5 h-5 text-emerald-500 mr-2" />
              <span className="text-emerald-600 font-semibold">
                {profile?.level_name || 'Saver'} • Level {profile?.level || 1}
              </span>
            </div>

            <p className="text-xl text-gray-700 font-medium mb-4">
              Your EarnAura Journey 🚀
            </p>

            {/* Progress Bar */}
            <div className="bg-gray-200 rounded-full h-3 mb-2 max-w-md mx-auto">
              <div 
                className="bg-gradient-to-r from-emerald-500 to-green-600 h-3 rounded-full transition-all duration-700"
                style={{ width: `${Math.min(((profile?.experience_points || 0) % 100), 100)}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600">
              {profile?.experience_points || 0} XP • {Math.max(0, 100 - ((profile?.experience_points || 0) % 100))} XP to next level
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-xl p-1 shadow-lg flex flex-row">
            {[
              { id: 'overview', label: 'Overview', icon: ChartBarIcon },
              { id: 'badges', label: 'Badges', icon: TrophyIcon },
              { id: 'leaderboards', label: 'Rankings', icon: UsersIcon },
              { id: 'achievements', label: 'Achievements', icon: StarIcon }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center space-x-2 whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-emerald-500 text-white shadow-md'
                    : 'text-gray-600 hover:text-emerald-600'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.label}</span>
                <span className="sm:hidden">{tab.label.substring(0, 4)}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <TrophyIcon className="w-8 h-8 text-yellow-500" />
                <span className="text-3xl font-bold text-gray-900">
                  {profile?.total_badges}
                </span>
              </div>
              <h3 className="font-semibold text-gray-700">Badges Earned</h3>
              <p className="text-sm text-gray-500">Keep collecting!</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <FireIcon className="w-8 h-8 text-orange-500" />
                <span className="text-3xl font-bold text-gray-900">
                  {profile?.current_streak}
                </span>
              </div>
              <h3 className="font-semibold text-gray-700">Day Streak</h3>
              <p className="text-sm text-gray-500">Keep it going!</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <StarIcon className="w-8 h-8 text-purple-500" />
                <span className="text-3xl font-bold text-gray-900">
                  {profile?.experience_points}
                </span>
              </div>
              <h3 className="font-semibold text-gray-700">XP Points</h3>
              <p className="text-sm text-gray-500">Level up!</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <ShareIcon className="w-8 h-8 text-blue-500" />
                <span className="text-3xl font-bold text-gray-900">
                  {profile?.achievements_shared}
                </span>
              </div>
              <h3 className="font-semibold text-gray-700">Achievements Shared</h3>
              <p className="text-sm text-gray-500">Inspire others!</p>
            </div>
          </div>
        )}

        {/* Badges Tab */}
        {activeTab === 'badges' && (
          <div className="bg-white rounded-xl p-6 shadow-lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Your Badges</h2>
              <span className="bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full text-sm font-medium">
                {profile?.total_badges} badges earned
              </span>
            </div>

            {profile?.badges?.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {profile.badges.map((badge, index) => (
                  <div key={index} className="bg-gray-50 rounded-xl p-4 text-center hover:bg-gray-100 transition-colors relative group">
                    <div className="text-4xl mb-2">{badge.icon || '🏆'}</div>
                    <h4 className="font-semibold text-gray-900 mb-1">{badge.name}</h4>
                    <p className="text-sm text-gray-600">{badge.description}</p>
                    {badge.earned_at && (
                      <p className="text-xs text-gray-400 mt-2">
                        Earned: {new Date(badge.earned_at).toLocaleDateString()}
                      </p>
                    )}
                    
                    {/* Share Button */}
                    <button
                      onClick={() => {
                        setSelectedAchievement({
                          title: badge.name,
                          description: badge.description,
                          type: 'badge_earned',
                          icon: badge.icon || '🏆'
                        });
                        setShowSocialSharing(true);
                      }}
                      className="absolute top-2 right-2 p-1.5 bg-white rounded-lg shadow-md opacity-0 group-hover:opacity-100 transition-opacity hover:bg-emerald-50"
                      title="Share this badge"
                    >
                      <ShareIcon className="w-4 h-4 text-emerald-600" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <TrophyIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No badges yet!</h3>
                <p className="text-gray-600">Start tracking your finances to earn your first badge.</p>
              </div>
            )}
          </div>
        )}

        {/* Leaderboards Tab */}
        {activeTab === 'leaderboards' && (
          <div className="space-y-6">
            {/* Savings Leaderboard */}
            <div className="bg-white rounded-xl p-6 shadow-lg">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                <TrophyIcon className="w-6 h-6 text-yellow-500 mr-2" />
                Top Savers This Week
              </h3>
              <div className="space-y-3">
                {leaderboards.savings?.slice(0, 5).map((user, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                        index === 0 ? 'bg-yellow-500' : index === 1 ? 'bg-gray-400' : index === 2 ? 'bg-orange-600' : 'bg-gray-300'
                      }`}>
                        {index + 1}
                      </div>
                      <span className="font-medium text-gray-900">{user.full_name}</span>
                    </div>
                    <span className="font-bold text-emerald-600">₹{user.total_saved?.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Streak Leaderboard */}
            <div className="bg-white rounded-xl p-6 shadow-lg">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                <FireIcon className="w-6 h-6 text-orange-500 mr-2" />
                Longest Streaks
              </h3>
              <div className="space-y-3">
                {leaderboards.streak?.slice(0, 5).map((user, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                        index === 0 ? 'bg-yellow-500' : index === 1 ? 'bg-gray-400' : index === 2 ? 'bg-orange-600' : 'bg-gray-300'
                      }`}>
                        {index + 1}
                      </div>
                      <span className="font-medium text-gray-900">{user.full_name}</span>
                    </div>
                    <span className="font-bold text-orange-600">{user.current_streak} days</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Achievements Tab */}
        {activeTab === 'achievements' && (
          <div className="bg-white rounded-xl p-6 shadow-lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Recent Achievements</h2>
              <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium">
                {achievements.length} unlocked
              </span>
            </div>

            {achievements.length > 0 ? (
              <div className="space-y-4">
                {achievements.map((achievement, index) => (
                  <div key={index} className="border border-gray-200 rounded-xl p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="text-3xl">{achievement.icon || '🎯'}</div>
                        <div>
                          <h4 className="font-semibold text-gray-900">{achievement.title}</h4>
                          <p className="text-gray-600">{achievement.description}</p>
                          <p className="text-sm text-gray-400">
                            Unlocked: {new Date(achievement.unlocked_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => shareAchievement(achievement)}
                        className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center space-x-2"
                      >
                        <ShareIcon className="w-4 h-4" />
                        <span>Share</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <StarIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No achievements yet!</h3>
                <p className="text-gray-600">Complete challenges and track your finances to unlock achievements.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Social Sharing Modal */}
      {showSocialSharing && selectedAchievement && (
        <SocialSharing 
          achievement={selectedAchievement}
          onClose={() => {
            setShowSocialSharing(false);
            setSelectedAchievement(null);
          }}
        />
      )}
    </div>
  );
};

export default GamificationProfile;
