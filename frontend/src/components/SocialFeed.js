import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SocialFeed = () => {
  const [activities, setActivities] = useState([]);
  const [peerComparison, setPeerComparison] = useState(null);
  const [peerMessages, setPeerMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAllFeedData();
  }, []);

  const fetchAllFeedData = async () => {
    await Promise.all([
      fetchFriendActivities(),
      fetchPeerComparison(),
      fetchPeerMessages()
    ]);
  };

  const fetchFriendActivities = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/social/friend-activity-feed`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setActivities(response.data.activities);
    } catch (error) {
      setError('Failed to load friend activities');
      console.error('Social feed error:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPeerComparison = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/social/peer-comparison`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setPeerComparison(response.data);
    } catch (error) {
      console.error('Peer comparison error:', error);
    }
  };

  const fetchPeerMessages = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/social/peer-messages`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setPeerMessages(response.data.notifications || []);
    } catch (error) {
      console.error('Peer messages error:', error);
    }
  };

  const getAvatarImage = (avatar) => {
    const avatarMap = {
      'boy': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face',
      'man': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face',
      'girl': 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face',
      'woman': 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=100&h=100&fit=crop&crop=face',
      'grandfather': 'https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=100&h=100&fit=crop&crop=face',
      'grandmother': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&h=100&fit=crop&crop=face'
    };
    return avatarMap[avatar] || avatarMap['man'];
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'transaction': return '💰';
      case 'achievement': return '🏆';
      case 'milestone': return '🎯';
      default: return '📱';
    }
  };

  const getActivityColor = (type) => {
    switch (type) {
      case 'transaction': return 'bg-green-100 border-green-200';
      case 'achievement': return 'bg-yellow-100 border-yellow-200';
      case 'milestone': return 'bg-purple-100 border-purple-200';
      default: return 'bg-gray-100 border-gray-200';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="flex space-x-4">
              <div className="rounded-full bg-gray-300 h-12 w-12"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-300 rounded w-3/4"></div>
                <div className="h-3 bg-gray-300 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            👫 Friend Activity Feed
          </h2>
          <p className="text-gray-600 mt-2">See what your friends are up to!</p>
        </div>

        {/* Peer Comparison Section */}
        {peerComparison && (
          <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              📊 How You Compare to Your Peers
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg p-4 border border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Your Savings Rate</p>
                    <p className="text-2xl font-bold text-blue-600">{peerComparison.user_savings_rate}%</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Peer Average</p>
                    <p className="text-lg font-semibold text-gray-700">{peerComparison.peer_average_rate}%</p>
                  </div>
                </div>
                <div className="mt-3">
                  <div className="bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        peerComparison.user_savings_rate >= peerComparison.peer_average_rate 
                          ? 'bg-green-500' 
                          : 'bg-orange-500'
                      }`}
                      style={{ 
                        width: `${Math.min(100, Math.max(10, peerComparison.user_savings_rate))}%` 
                      }}
                    ></div>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-lg p-4 border border-blue-200">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">
                    {peerComparison.status === 'leading' ? '🚀' : 
                     peerComparison.status === 'catching_up' ? '📈' : '⚡'}
                  </span>
                  <div>
                    <p className="font-semibold text-gray-900">{peerComparison.comparison_message}</p>
                    <p className="text-sm text-gray-600">{peerComparison.motivation_level} motivation</p>
                  </div>
                </div>
                {peerComparison.university_context && (
                  <p className="text-xs text-blue-600 mt-2">{peerComparison.university_context}</p>
                )}
              </div>
            </div>

            {peerComparison.actionable_tips && peerComparison.actionable_tips.length > 0 && (
              <div className="mt-4 p-3 bg-white rounded-lg border border-blue-200">
                <p className="text-sm font-medium text-gray-900 mb-2">💡 Quick Tips for You:</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {peerComparison.actionable_tips.slice(0, 2).map((tip, index) => (
                    <p key={index} className="text-xs text-gray-600 bg-blue-50 px-2 py-1 rounded">
                      {tip}
                    </p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Peer Messages Section */}
        {peerMessages.length > 0 && (
          <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-green-50 to-emerald-50">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              🔥 Social Pressure Alerts
            </h3>
            <div className="space-y-3">
              {peerMessages.slice(0, 3).map((message, index) => (
                <div key={index} className="bg-white rounded-lg p-4 border border-green-200 flex items-center gap-3">
                  <span className="text-2xl">{message.icon}</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{message.message}</p>
                    {message.action_text && (
                      <button 
                        className="text-xs text-green-600 hover:text-green-700 font-medium mt-1"
                        onClick={() => message.action_url && (window.location.href = message.action_url)}
                      >
                        {message.action_text} →
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="divide-y divide-gray-200">
          {activities.length === 0 ? (
            <div className="p-8 text-center">
              <div className="text-6xl mb-4">👥</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No friend activities yet</h3>
              <p className="text-gray-500">Connect with friends to see their financial journey!</p>
            </div>
          ) : (
            activities.map((activity, index) => (
              <div key={index} className={`p-4 hover:bg-gray-50 transition-colors ${getActivityColor(activity.type)} border-l-4`}>
                <div className="flex items-start space-x-3">
                  <img
                    src={getAvatarImage(activity.user_avatar)}
                    alt={activity.user_name}
                    className="w-10 h-10 rounded-full object-cover"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl">{getActivityIcon(activity.type)}</span>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          <span className="font-semibold">{activity.user_name}</span> {activity.action}
                        </p>
                        <p className="text-sm text-gray-600">{activity.details}</p>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{formatTimestamp(activity.timestamp)}</p>
                  </div>
                  {activity.amount && (
                    <div className="text-right">
                      <span className="text-lg font-bold text-green-600">
                        ₹{activity.amount.toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {activities.length > 0 && (
          <div className="p-4 bg-gray-50 text-center">
            <button 
              onClick={fetchAllFeedData}
              className="text-green-600 hover:text-green-700 font-medium"
            >
              🔄 Refresh Feed
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SocialFeed;
