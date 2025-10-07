import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import SocialSharing from './SocialSharing';
import EnhancedCelebration from './EnhancedCelebration';
import pushNotificationService from '../services/pushNotificationService';
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
  ArrowUpIcon,
  GiftIcon
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
  const [pendingCelebrations, setPendingCelebrations] = useState([]);
  const [currentCelebration, setCurrentCelebration] = useState(null);
  const [celebrationIndex, setCelebrationIndex] = useState(0);
  const [socialProof, setSocialProof] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(Date.now());
  const { user } = useAuth();

  useEffect(() => {
    fetchGamificationData();
    checkPendingCelebrations();
    initializePushNotifications();
  }, []);

  // Auto-refresh data every 30 seconds for live updates
  useEffect(() => {
    const interval = setInterval(() => {
      fetchGamificationData(false);
      fetchLeaderboards();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Check URL for celebration parameter
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const celebrateId = urlParams.get('celebrate');
    if (celebrateId && achievements.length > 0) {
      const achievement = achievements.find(a => a.id === celebrateId);
      if (achievement) {
        setCurrentCelebration({
          ...achievement,
          type: 'achievement'
        });
      }
    }
  }, [achievements]);

  const fetchGamificationData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      }
      
      const token = localStorage.getItem('token');
      const headers = { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      const [profileRes, achievementsRes, socialProofRes] = await Promise.all([
        axios.get(`${API}/gamification/profile?enhanced=true`, { headers }),
        axios.get(`${API}/gamification/achievements?limit=20`, { headers }),
        axios.get(`${API}/gamification/social-proof`, { headers }).catch(() => ({ data: null }))
      ]);

      setProfile(profileRes.data);
      setAchievements(achievementsRes.data?.achievements || []);
      setSocialProof(socialProofRes.data);
      setLastUpdate(Date.now());
      
      // Check for pending celebrations from enhanced profile
      if (profileRes.data.pending_celebrations && profileRes.data.pending_celebrations.length > 0) {
        setPendingCelebrations(profileRes.data.pending_celebrations);
        setCurrentCelebration(profileRes.data.pending_celebrations[0]);
      }
      
      // Fetch leaderboards with live data
      await fetchLeaderboards();
      
    } catch (error) {
      console.error('Error fetching gamification data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const checkPendingCelebrations = async () => {
    try {
      const response = await axios.get(`${API}/gamification/celebrations/pending`);
      const celebrations = response.data.celebrations;
      
      if (celebrations.length > 0) {
        setPendingCelebrations(celebrations);
        setCurrentCelebration({
          ...celebrations[0],
          celebrationIndex: 0,
          totalCelebrations: celebrations.length
        });
      }
    } catch (error) {
      console.error('Error fetching pending celebrations:', error);
    }
  };

  const initializePushNotifications = async () => {
    try {
      await pushNotificationService.initialize();
      pushNotificationService.setupNotificationHandlers();
      
      // Listen for notification clicks
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.addEventListener('message', (event) => {
          if (event.data.type === 'SHARE_ACHIEVEMENT') {
            const achievementData = event.data.payload;
            setSelectedAchievement(achievementData);
            setShowSocialSharing(true);
          }
        });
      }
    } catch (error) {
      console.error('Failed to initialize push notifications:', error);
    }
  };

  const fetchLeaderboards = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      const [savingsRes, streakRes, pointsRes] = await Promise.all([
        axios.get(`${API}/gamification/leaderboards/savings?period=weekly&limit=15`, { headers }),
        axios.get(`${API}/gamification/leaderboards/streak?period=weekly&limit=15`, { headers }),
        axios.get(`${API}/gamification/leaderboards/points?period=weekly&limit=15`, { headers })
      ]);

      setLeaderboards({
        savings: savingsRes.data?.rankings || [],
        streak: streakRes.data?.rankings || [],
        points: pointsRes.data?.rankings || []
      });
    } catch (error) {
      console.error('Error fetching leaderboards:', error);
      // Set empty arrays as fallback
      setLeaderboards({
        savings: [],
        streak: [],
        points: []
      });
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

  const handleCelebrationNext = () => {
    const nextIndex = celebrationIndex + 1;
    
    if (nextIndex < pendingCelebrations.length) {
      // Show next celebration
      setCelebrationIndex(nextIndex);
      setCurrentCelebration({
        ...pendingCelebrations[nextIndex],
        celebrationIndex: nextIndex,
        totalCelebrations: pendingCelebrations.length
      });
    } else {
      // No more celebrations
      setCurrentCelebration(null);
      setPendingCelebrations([]);
      setCelebrationIndex(0);
    }
  };

  const handleCelebrationClose = () => {
    setCurrentCelebration(null);
    setPendingCelebrations([]);
    setCelebrationIndex(0);
  };

  const formatStreakProgress = (current, target) => {
    const percentage = Math.min((current / target) * 100, 100);
    return {
      percentage,
      remaining: Math.max(0, target - current)
    };
  };

  const getSocialProofMessage = () => {
    if (!socialProof || !socialProof.social_messages) return null;
    
    const messages = socialProof.social_messages;
    if (messages.length === 0) return null;
    
    return messages[Math.floor(Math.random() * messages.length)];
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
        {/* Enhanced Header with Live Updates */}
        <div className="text-center mb-6 sm:mb-8">
          <div className="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 lg:p-8 shadow-lg mb-4 sm:mb-6 overflow-hidden">
            <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 sm:gap-6 mb-4 sm:mb-6">
              <div className="relative flex-shrink-0">
                <div className="w-20 sm:w-24 h-20 sm:h-24 bg-gradient-to-br from-emerald-500 to-green-600 rounded-full flex items-center justify-center shadow-xl">
                  <TrophyIcon className="w-10 sm:w-12 h-10 sm:h-12 text-white" />
                </div>
                {profile?.current_streak > 0 && (
                  <div className="absolute -top-1 sm:-top-2 -right-1 sm:-right-2 bg-orange-500 text-white text-xs sm:text-sm font-bold rounded-full w-6 sm:w-8 h-6 sm:h-8 flex items-center justify-center">
                    {profile.current_streak}
                  </div>
                )}
              </div>
              
              <div className="flex-1 min-w-0 text-center sm:text-left">
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2 truncate">
                  {user?.full_name || 'User'}
                </h1>
                
                <div className="flex items-center justify-center sm:justify-start mb-3 sm:mb-4">
                  <SparklesIcon className="w-4 sm:w-5 h-4 sm:h-5 text-emerald-500 mr-2" />
                  <span className="text-emerald-600 font-semibold text-sm sm:text-base">
                    {profile?.level_name || 'Saver'} • Level {profile?.level || 1}
                  </span>
                  <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">LIVE</span>
                </div>

                <p className="text-lg sm:text-xl text-gray-700 font-medium mb-3 sm:mb-4">
                  Your EarnAura Journey 🚀
                </p>
                
                <div className="flex items-center justify-center sm:justify-start gap-2 text-xs text-gray-500 mb-3">
                  <span>Last updated: {new Date(lastUpdate).toLocaleTimeString()}</span>
                  <button
                    onClick={() => fetchGamificationData(true)}
                    disabled={refreshing}
                    className={`p-1 rounded-full transition-all ${refreshing ? 'animate-spin' : 'hover:bg-gray-100'}`}
                  >
                    <ArrowUpIcon className="w-3 h-3" />
                  </button>
                </div>

                {/* Enhanced Progress Bar */}
                <div className="bg-gray-200 rounded-full h-2 sm:h-3 mb-2 max-w-xs sm:max-w-md mx-auto sm:mx-0">
                  <div 
                    className="bg-gradient-to-r from-emerald-500 to-green-600 h-2 sm:h-3 rounded-full transition-all duration-700"
                    style={{ width: `${Math.min(((profile?.experience_points || 0) % 100), 100)}%` }}
                  ></div>
                </div>
                <p className="text-xs sm:text-sm text-gray-600">
                  {profile?.experience_points || 0} XP • {Math.max(0, 100 - ((profile?.experience_points || 0) % 100))} XP to next level
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Navigation Tabs - More Responsive */}
        <div className="flex justify-center mb-6 sm:mb-8">
          <div className="bg-white rounded-lg sm:rounded-xl p-1 shadow-lg flex flex-row overflow-x-auto max-w-full">
            {[
              { id: 'overview', label: 'Overview', icon: ChartBarIcon },
              { id: 'badges', label: 'Badges', icon: TrophyIcon },
              { id: 'leaderboards', label: 'Live Rankings', icon: UsersIcon },
              { id: 'achievements', label: 'Achievements', icon: StarIcon }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-2 sm:px-4 py-1 sm:py-2 rounded-lg font-medium transition-all flex items-center space-x-1 sm:space-x-2 whitespace-nowrap flex-shrink-0 text-xs sm:text-sm ${
                  activeTab === tab.id
                    ? 'bg-emerald-500 text-white shadow-md'
                    : 'text-gray-600 hover:text-emerald-600'
                }`}
              >
                <tab.icon className="w-3 sm:w-4 h-3 sm:h-4" />
                <span className="hidden md:inline">{tab.label}</span>
                <span className="md:hidden">{tab.label.split(' ')[0]}</span>
                {tab.id === 'leaderboards' && (
                  <span className="text-xs bg-red-100 text-red-700 px-1 rounded-full ml-1">LIVE</span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Overview Tab - Enhanced Phase 1 */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Social Proof Messages */}
            {socialProof && getSocialProofMessage() && (
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-4">
                <div className="flex items-center">
                  <GiftIcon className="w-5 h-5 text-blue-600 mr-2" />
                  <span className="text-blue-800 font-medium">{getSocialProofMessage()}</span>
                </div>
              </div>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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
                <p className="text-sm text-gray-500">
                  {profile?.streak_milestones?.progress_to_next?.days_remaining > 0 
                    ? `${profile.streak_milestones.progress_to_next.days_remaining} days to next milestone`
                    : 'At milestone!'
                  }
                </p>
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

            {/* Streak Progress Card */}
            {profile?.streak_milestones && (
              <div className="bg-white rounded-xl p-6 shadow-lg">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-gray-900 flex items-center">
                    <FireIcon className="w-6 h-6 text-orange-500 mr-2" />
                    Streak Progress
                  </h3>
                  <span className="text-sm text-gray-500">
                    Next: {profile.streak_milestones.next_milestone} days
                  </span>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>Progress to next milestone</span>
                    <span className="font-medium">
                      {profile.streak_milestones.progress_to_next.current} / {profile.streak_milestones.progress_to_next.target} days
                    </span>
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className="bg-gradient-to-r from-orange-500 to-red-500 h-3 rounded-full transition-all duration-700"
                      style={{ width: `${profile.streak_milestones.progress_to_next.percentage}%` }}
                    ></div>
                  </div>
                  
                  <div className="text-center">
                    <span className="text-sm text-gray-600">
                      {profile.streak_milestones.progress_to_next.days_remaining === 0 
                        ? "🎉 Milestone reached!" 
                        : `${profile.streak_milestones.progress_to_next.days_remaining} days to go!`
                      }
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Social Proof Stats */}
            {socialProof && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Friends Leaderboard */}
                {socialProof.friends_leaderboard && socialProof.friends_leaderboard.length > 0 && (
                  <div className="bg-white rounded-xl p-6 shadow-lg">
                    <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                      <UsersIcon className="w-6 h-6 text-purple-500 mr-2" />
                      Friends Leaderboard
                    </h3>
                    
                    <div className="space-y-2">
                      {socialProof.friends_leaderboard.slice(0, 5).map((friend, index) => (
                        <div 
                          key={friend.user_id} 
                          className={`flex items-center justify-between p-2 rounded-lg ${
                            friend.is_current_user ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center space-x-3">
                            <span className={`text-sm font-bold w-6 h-6 rounded-full flex items-center justify-center ${
                              index === 0 ? 'bg-yellow-100 text-yellow-800' :
                              index === 1 ? 'bg-gray-100 text-gray-800' :
                              index === 2 ? 'bg-orange-100 text-orange-800' :
                              'bg-gray-50 text-gray-600'
                            }`}>
                              {index + 1}
                            </span>
                            <span className={`font-medium ${friend.is_current_user ? 'text-blue-900' : 'text-gray-900'}`}>
                              {friend.name}
                            </span>
                          </div>
                          
                          <div className="text-right">
                            <div className="text-sm font-medium text-gray-900">{friend.points} XP</div>
                            <div className="text-xs text-gray-500">{friend.streak} day streak</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Achievement Statistics */}
                <div className="bg-white rounded-xl p-6 shadow-lg">
                  <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                    <TrophyIcon className="w-6 h-6 text-yellow-500 mr-2" />
                    Community Stats
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Today's Achievements</span>
                      <span className="font-bold text-yellow-600">{socialProof.daily_achievements || 0}</span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Weekly Milestones</span>
                      <span className="font-bold text-orange-600">{socialProof.weekly_milestones || 0}</span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Active Friends</span>
                      <span className="font-bold text-purple-600">{socialProof.friends_achievements?.length || 0}</span>
                    </div>

                    {/* Popular Achievements */}
                    {socialProof.popular_achievements && socialProof.popular_achievements.length > 0 && (
                      <div className="pt-3 border-t">
                        <p className="text-sm font-medium text-gray-700 mb-2">Trending This Week:</p>
                        <div className="space-y-1">
                          {socialProof.popular_achievements.slice(0, 3).map((achievement, index) => (
                            <div key={index} className="flex items-center justify-between text-sm">
                              <span className="text-gray-600 flex items-center">
                                <span className="mr-1">{achievement.icon}</span>
                                {achievement._id}
                              </span>
                              <span className="text-gray-500">{achievement.count}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Special Perks Display */}
            {profile?.special_perks && profile.special_perks.length > 0 && (
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-xl p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                  <GiftIcon className="w-6 h-6 text-purple-500 mr-2" />
                  Unlocked Perks
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {profile.special_perks.map((perk, index) => (
                    <div key={index} className="bg-white rounded-lg p-4 shadow-sm">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                          <span className="text-purple-600 text-sm">✨</span>
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-900 capitalize">
                            {perk.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </h4>
                          <p className="text-sm text-gray-600">
                            {perk === 'referral_boost' && 'Extra referral rewards'}
                            {perk === 'profile_highlight' && 'Featured profile status'}
                            {perk === 'priority_support' && 'Priority customer support'}
                            {perk === 'exclusive_features' && 'Access to beta features'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
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

        {/* Enhanced Live Leaderboards Tab */}
        {activeTab === 'leaderboards' && (
          <div className="space-y-4 sm:space-y-6">
            {/* Live Rankings Header */}
            <div className="bg-gradient-to-r from-emerald-50 to-blue-50 rounded-xl p-4 border border-emerald-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  <h2 className="font-bold text-gray-900 text-lg sm:text-xl">Live Rankings</h2>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">LIVE</span>
                  <span className="text-xs text-gray-500">
                    Updated: {new Date(lastUpdate).toLocaleTimeString()}
                  </span>
                  {refreshing && <div className="w-3 h-3 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent"></div>}
                </div>
              </div>
            </div>

            {/* Enhanced Savings Leaderboard */}
            <div className="bg-white rounded-xl p-4 sm:p-6 shadow-lg overflow-hidden">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg sm:text-xl font-bold text-gray-900 flex items-center">
                  <TrophyIcon className="w-5 sm:w-6 h-5 sm:h-6 text-yellow-500 mr-2" />
                  Top Savers This Week
                </h3>
                <button
                  onClick={fetchLeaderboards}
                  className="text-xs text-emerald-600 hover:text-emerald-700 font-medium"
                >
                  Refresh
                </button>
              </div>
              <div className="space-y-2 sm:space-y-3 max-h-96 overflow-y-auto">
                {leaderboards.savings?.length > 0 ? (
                  leaderboards.savings.slice(0, 10).map((user, index) => (
                    <div 
                      key={index} 
                      className={`flex items-center justify-between p-2 sm:p-3 rounded-lg transition-colors ${
                        user.is_current_user ? 'bg-emerald-50 border border-emerald-200' : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
                        <div className={`w-6 sm:w-8 h-6 sm:h-8 rounded-full flex items-center justify-center text-white font-bold text-xs sm:text-sm ${
                          index === 0 ? 'bg-yellow-500' : 
                          index === 1 ? 'bg-gray-400' : 
                          index === 2 ? 'bg-orange-600' : 'bg-gray-300'
                        }`}>
                          {index + 1}
                        </div>
                        <span className={`font-medium text-sm sm:text-base truncate ${
                          user.is_current_user ? 'text-emerald-900' : 'text-gray-900'
                        }`}>
                          {user.full_name}{user.is_current_user ? ' (You)' : ''}
                        </span>
                      </div>
                      <span className="font-bold text-emerald-600 text-sm sm:text-base">
                        ₹{(user.score || 0).toLocaleString()}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <TrophyIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p className="text-sm">No rankings available yet</p>
                    <p className="text-xs">Start saving to join the leaderboard!</p>
                  </div>
                )}
              </div>
            </div>

            {/* Enhanced Streak Leaderboard */}
            <div className="bg-white rounded-xl p-4 sm:p-6 shadow-lg overflow-hidden">
              <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-4 flex items-center">
                <FireIcon className="w-5 sm:w-6 h-5 sm:h-6 text-orange-500 mr-2" />
                Longest Streaks
              </h3>
              <div className="space-y-2 sm:space-y-3 max-h-96 overflow-y-auto">
                {leaderboards.streak?.length > 0 ? (
                  leaderboards.streak.slice(0, 10).map((user, index) => (
                    <div 
                      key={index} 
                      className={`flex items-center justify-between p-2 sm:p-3 rounded-lg transition-colors ${
                        user.is_current_user ? 'bg-orange-50 border border-orange-200' : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
                        <div className={`w-6 sm:w-8 h-6 sm:h-8 rounded-full flex items-center justify-center text-white font-bold text-xs sm:text-sm ${
                          index === 0 ? 'bg-yellow-500' : 
                          index === 1 ? 'bg-gray-400' : 
                          index === 2 ? 'bg-orange-600' : 'bg-gray-300'
                        }`}>
                          {index + 1}
                        </div>
                        <span className={`font-medium text-sm sm:text-base truncate ${
                          user.is_current_user ? 'text-orange-900' : 'text-gray-900'
                        }`}>
                          {user.full_name}{user.is_current_user ? ' (You)' : ''}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <FireIcon className="w-4 h-4 text-orange-500" />
                        <span className="font-bold text-orange-600 text-sm sm:text-base">
                          {user.score || 0} days
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <FireIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p className="text-sm">No streaks yet</p>
                    <p className="text-xs">Start your daily streak today!</p>
                  </div>
                )}
              </div>
            </div>

            {/* Points Leaderboard */}
            <div className="bg-white rounded-xl p-4 sm:p-6 shadow-lg overflow-hidden">
              <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-4 flex items-center">
                <StarIcon className="w-5 sm:w-6 h-5 sm:h-6 text-purple-500 mr-2" />
                Top Point Earners
              </h3>
              <div className="space-y-2 sm:space-y-3 max-h-96 overflow-y-auto">
                {leaderboards.points?.length > 0 ? (
                  leaderboards.points.slice(0, 10).map((user, index) => (
                    <div 
                      key={index} 
                      className={`flex items-center justify-between p-2 sm:p-3 rounded-lg transition-colors ${
                        user.is_current_user ? 'bg-purple-50 border border-purple-200' : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
                        <div className={`w-6 sm:w-8 h-6 sm:h-8 rounded-full flex items-center justify-center text-white font-bold text-xs sm:text-sm ${
                          index === 0 ? 'bg-yellow-500' : 
                          index === 1 ? 'bg-gray-400' : 
                          index === 2 ? 'bg-orange-600' : 'bg-gray-300'
                        }`}>
                          {index + 1}
                        </div>
                        <span className={`font-medium text-sm sm:text-base truncate ${
                          user.is_current_user ? 'text-purple-900' : 'text-gray-900'
                        }`}>
                          {user.full_name}{user.is_current_user ? ' (You)' : ''}
                        </span>
                      </div>
                      <span className="font-bold text-purple-600 text-sm sm:text-base">
                        {(user.score || 0).toLocaleString()} XP
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <StarIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p className="text-sm">No points yet</p>
                    <p className="text-xs">Complete activities to earn XP!</p>
                  </div>
                )}
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

      {/* Enhanced Celebration Modal - Phase 1 */}
      {currentCelebration && (
        <EnhancedCelebration
          celebration={currentCelebration}
          onClose={handleCelebrationClose}
          onNext={pendingCelebrations.length > celebrationIndex + 1 ? handleCelebrationNext : null}
        />
      )}

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
