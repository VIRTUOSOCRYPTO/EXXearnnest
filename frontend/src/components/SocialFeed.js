import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SocialFeed = () => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchFriendActivities();
  }, []);

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
              onClick={fetchFriendActivities}
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
