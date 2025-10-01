import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
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
      const leaderboardTypes = ['savings', 'points', 'streak', 'goals'];
      const leaderboardData = {};
      
      for (const type of leaderboardTypes) {
        const response = await axios.get(`${API}/gamification/leaderboards/${type}?limit=5`);
        leaderboardData[type] = response.data;
      }
      
      setLeaderboards(leaderboardData);
    } catch (error) {
      console.error('Error fetching leaderboards:', error);
    }
  };

  const shareAchievement = async (achievementId) => {
    try {
      await axios.post(`${API}/gamification/achievements/${achievementId}/share`);
      // Refresh achievements to show shared status
      fetchGamificationData();
    } catch (error) {
      console.error('Error sharing achievement:', error);
    }
  };

  const getRarityColor = (rarity) => {
    const colors = {
      bronze: 'text-amber-600 bg-amber-50',
      silver: 'text-gray-600 bg-gray-50',
      gold: 'text-yellow-600 bg-yellow-50',
      platinum: 'text-purple-600 bg-purple-50',
      legendary: 'text-red-600 bg-red-50'
    };
    return colors[rarity] || colors.bronze;
  };

  const getLevelProgress = (level, experience) => {
    const currentLevelXP = (level - 1) * 100;
    const nextLevelXP = level * 100;
    const progress = ((experience - currentLevelXP) / 100) * 100;
    return Math.min(Math.max(progress, 0), 100);
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-48 bg-gray-200 rounded-xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center mb-4">
          <div className="relative">
            <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-green-600 rounded-full flex items-center justify-center">
              <TrophyIcon className="w-8 h-8 text-white" />
            </div>
            <div className="absolute -top-2 -right-2 bg-yellow-500 text-white text-xs font-bold px-2 py-1 rounded-full">
              {profile?.level}
            </div>
          </div>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Your EarnNest Journey 🚀
        </h1>
        <p className="text-xl text-emerald-600 font-semibold mb-2">
          {profile?.title} • Level {profile?.level}
        </p>
        <div className="max-w-md mx-auto bg-gray-200 rounded-full h-3 mb-4">
          <div 
            className="bg-gradient-to-r from-emerald-500 to-green-600 h-3 rounded-full transition-all duration-300"
            style={{ width: `${getLevelProgress(profile?.level, profile?.experience_points)}%` }}
          ></div>
        </div>
        <p className="text-sm text-gray-600">
          {profile?.experience_points} XP • {100 - (profile?.experience_points % 100)} XP to next level
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="flex justify-center mb-8">
        <div className="bg-white rounded-xl p-1 shadow-lg">
          {[
            { id: 'overview', label: 'Overview', icon: ChartBarIcon },
            { id: 'badges', label: 'Badges', icon: TrophyIcon },
            { id: 'leaderboards', label: 'Rankings', icon: UsersIcon },
            { id: 'achievements', label: 'Achievements', icon: StarIcon }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 rounded-lg font-medium transition-all flex items-center space-x-2 ${
                activeTab === tab.id
                  ? 'bg-emerald-500 text-white shadow-md'
                  : 'text-gray-600 hover:text-emerald-600'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              <span>{tab.label}</span>
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
              <span className="text-2xl font-bold text-gray-900">
                {profile?.total_badges}
              </span>
            </div>
            <h3 className="font-semibold text-gray-700">Badges Earned</h3>
            <p className="text-sm text-gray-500">Keep collecting!</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <FireIcon className="w-8 h-8 text-red-500" />
              <span className="text-2xl font-bold text-gray-900">
                {profile?.current_streak}
              </span>
            </div>
            <h3 className="font-semibold text-gray-700">Day Streak</h3>
            <p className="text-sm text-gray-500">Keep it going!</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <SparklesIcon className="w-8 h-8 text-purple-500" />
              <span className="text-2xl font-bold text-gray-900">
                {profile?.experience_points}
              </span>
            </div>
            <h3 className="font-semibold text-gray-700">Experience Points</h3>
            <p className="text-sm text-gray-500">Level {profile?.level}</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <ShareIcon className="w-8 h-8 text-blue-500" />
              <span className="text-2xl font-bold text-gray-900">
                {profile?.achievements_shared}
              </span>
            </div>
            <h3 className="font-semibold text-gray-700">Achievements Shared</h3>
            <p className="text-sm text-gray-500">Community engagement</p>
          </div>
        </div>
      )}

      {/* Badges Tab */}
      {activeTab === 'badges' && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Your Badge Collection</h2>
            <div className="text-sm text-gray-600">
              {profile?.total_badges} badges earned
            </div>
          </div>
          
          {profile?.badges?.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {profile.badges.map((badge, index) => (
                <div key={index} className="bg-gray-50 rounded-xl p-6 text-center">
                  <div className="text-4xl mb-3">{badge.icon}</div>
                  <div className={`inline-block px-3 py-1 rounded-full text-xs font-semibold mb-3 ${getRarityColor(badge.rarity)}`}>
                    {badge.rarity.toUpperCase()}
                  </div>
                  <h3 className="font-bold text-gray-900 mb-2">{badge.name}</h3>
                  <p className="text-sm text-gray-600 mb-3">{badge.description}</p>
                  <div className="text-xs text-gray-500">
                    Earned {new Date(badge.earned_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <TrophyIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No badges yet!</h3>
              <p className="text-gray-600">Start saving money and tracking expenses to earn your first badges.</p>
            </div>
          )}
        </div>
      )}

      {/* Leaderboards Tab */}
      {activeTab === 'leaderboards' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {Object.entries(leaderboards).map(([type, data]) => (
            <div key={type} className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-900 capitalize">
                  {type} Leaderboard
                </h3>
                <div className="text-sm text-gray-600">
                  Your rank: #{data.user_rank || 'Unranked'}
                </div>
              </div>
              
              <div className="space-y-4">
                {data.rankings?.map((ranking, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                        index === 0 ? 'bg-yellow-100 text-yellow-800' :
                        index === 1 ? 'bg-gray-100 text-gray-800' :
                        index === 2 ? 'bg-amber-100 text-amber-800' :
                        'bg-gray-50 text-gray-700'
                      }`}>
                        {ranking.rank}
                      </div>
                      <div>
                        <div className="font-semibold text-gray-900">{ranking.full_name}</div>
                        <div className="text-xs text-gray-500">{ranking.title} • Level {ranking.level}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-gray-900">
                        {type === 'savings' ? `₹${ranking.score.toLocaleString()}` : ranking.score}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Achievements Tab */}
      {activeTab === 'achievements' && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Recent Achievements</h2>
            <div className="text-sm text-gray-600">
              {achievements.length} achievements
            </div>
          </div>
          
          {achievements.length > 0 ? (
            <div className="space-y-4">
              {achievements.map((achievement, index) => (
                <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="text-3xl">{achievement.icon}</div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{achievement.title}</h3>
                      <p className="text-sm text-gray-600">{achievement.description}</p>
                      <div className="flex items-center space-x-2 mt-2">
                        <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full">
                          +{achievement.points_earned} XP
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(achievement.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {!achievement.is_shared && (
                    <button
                      onClick={() => shareAchievement(achievement.id)}
                      className="px-4 py-2 bg-emerald-500 text-white text-sm rounded-lg hover:bg-emerald-600 transition-colors flex items-center space-x-2"
                    >
                      <ShareIcon className="w-4 h-4" />
                      <span>Share</span>
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <StarIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No achievements yet!</h3>
              <p className="text-gray-600">Start your financial journey to unlock achievements.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GamificationProfile;
