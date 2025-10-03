import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { 
  BellIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  TrophyIcon,
  UsersIcon,
  FireIcon,
  GiftIcon,
  ClockIcon,
  LightBulbIcon,
  StarIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const Notifications = () => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch notifications on component mount
  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/notifications`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications || []);
      } else {
        throw new Error('Failed to fetch notifications');
      }
    } catch (error) {
      console.error('Error fetching notifications:', error);
      setError('Failed to load notifications');
      // Set some sample notifications for demo purposes including Phase 1 features
      setNotifications([
        {
          id: 1,
          type: 'daily_tip',
          title: 'Daily Financial Tip 💡',
          message: 'Today\'s tip: Cook at home for 1 week and save ₹1,400+! Check your dashboard for the full tip.',
          created_at: new Date().toISOString(),
          is_read: false,
          icon: 'lightbulb',
          action_url: '/dashboard'
        },
        {
          id: 2,
          type: 'individual_challenge_invite',
          title: 'Friend Challenge Received! 🥊',
          message: 'Rahul has challenged you to a Savings Race: Save ₹5,000 in 7 days. Stakes: Loser buys coffee!',
          created_at: new Date(Date.now() - 3600000).toISOString(),
          is_read: false,
          icon: 'star',
          action_url: '/challenges?tab=friend_challenges'
        },
        {
          id: 3,
          type: 'peer_comparison',
          title: 'Peer Comparison Update ✨',
          message: 'You\'re saving 15% more than your university peers! Keep it up - you\'re in the top 25%.',
          created_at: new Date(Date.now() - 7200000).toISOString(),
          is_read: false,
          icon: 'peer_comparison',
          action_url: '/social-feed'
        },
        {
          id: 4,
          type: 'milestone_achieved',
          title: 'Milestone Achieved! 🎉',
          message: 'Congratulations! You\'ve saved ₹10,000 this month.',
          created_at: new Date(Date.now() - 86400000).toISOString(),
          is_read: false,
          icon: 'trophy'
        },
        {
          id: 5,
          type: 'friend_joined',
          title: 'Friend Joined EarnNest',
          message: 'Your friend Priya has joined EarnNest using your referral link!',
          created_at: new Date(Date.now() - 172800000).toISOString(),
          is_read: false,
          icon: 'users'
        },
        {
          id: 6,
          type: 'budget_alert',
          title: 'Budget Alert',
          message: 'You\'ve spent 80% of your Entertainment budget this month.',
          created_at: new Date(Date.now() - 259200000).toISOString(),
          is_read: true,
          icon: 'exclamation'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/notifications/${notificationId}/read`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        setNotifications(notifications.map(notification => 
          notification.id === notificationId 
            ? { ...notification, is_read: true }
            : notification
        ));
      }
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/notifications/mark-all-read`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        setNotifications(notifications.map(notification => 
          ({ ...notification, is_read: true })
        ));
      }
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  const getNotificationIcon = (type, icon) => {
    const iconClass = "w-6 h-6";
    
    switch (icon || type) {
      case 'trophy':
      case 'milestone_achieved':
        return <TrophyIcon className={`${iconClass} text-yellow-500`} />;
      case 'users':
      case 'friend_joined':
        return <UsersIcon className={`${iconClass} text-blue-500`} />;
      case 'fire':
      case 'challenge':
      case 'streak_reminder':
        return <FireIcon className={`${iconClass} text-red-500`} />;
      case 'gift':
      case 'reward':
        return <GiftIcon className={`${iconClass} text-purple-500`} />;
      case 'exclamation':
      case 'budget_alert':
        return <ExclamationCircleIcon className={`${iconClass} text-amber-500`} />;
      case 'lightbulb':
      case 'daily_tip':
        return <LightBulbIcon className={`${iconClass} text-blue-500`} />;
      case 'star':
      case 'individual_challenge_invite':
      case 'individual_challenge':
        return <StarIcon className={`${iconClass} text-purple-500`} />;
      case 'peer_comparison':
        return <SparklesIcon className={`${iconClass} text-green-500`} />;
      default:
        return <BellIcon className={`${iconClass} text-gray-500`} />;
    }
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${diffInHours}h ago`;
    } else {
      const diffInDays = Math.floor(diffInHours / 24);
      return `${diffInDays}d ago`;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading notifications...</p>
        </div>
      </div>
    );
  }

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold gradient-text mb-2">Notifications</h1>
              <p className="text-gray-600">
                {unreadCount > 0 
                  ? `You have ${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}`
                  : 'All caught up! No new notifications'
                }
              </p>
            </div>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="px-4 py-2 text-sm font-medium text-emerald-600 bg-emerald-50 hover:bg-emerald-100 rounded-lg transition-colors"
              >
                Mark all as read
              </button>
            )}
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        )}

        {/* Notifications List */}
        <div className="space-y-4">
          {notifications.length === 0 ? (
            <div className="text-center py-12">
              <BellIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No notifications yet</h3>
              <p className="text-gray-600">
                We'll notify you when there's something important to share!
              </p>
            </div>
          ) : (
            notifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-4 rounded-lg border transition-all duration-200 cursor-pointer ${
                  notification.is_read
                    ? 'bg-white border-gray-200 hover:border-gray-300'
                    : 'bg-blue-50 border-blue-200 hover:border-blue-300'
                }`}
                onClick={() => {
                  if (!notification.is_read) {
                    markAsRead(notification.id);
                  }
                  if (notification.action_url) {
                    window.location.href = notification.action_url;
                  }
                }}
              >
                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div className="flex-shrink-0 mt-1">
                    {getNotificationIcon(notification.type, notification.icon)}
                  </div>
                  
                  {/* Content */}
                  <div className="flex-grow">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className={`font-medium mb-1 ${
                          notification.is_read ? 'text-gray-900' : 'text-gray-900 font-semibold'
                        }`}>
                          {notification.title}
                        </h4>
                        <p className="text-gray-600 text-sm leading-relaxed">
                          {notification.message}
                        </p>
                        <div className="flex items-center gap-4 mt-2">
                          <span className="text-xs text-gray-500">
                            {formatTimeAgo(notification.created_at)}
                          </span>
                          {!notification.is_read && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              New
                            </span>
                          )}
                          {notification.action_url && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              Click to view →
                            </span>
                          )}
                        </div>
                      </div>
                      
                      {/* Read status indicator */}
                      {notification.is_read && (
                        <CheckCircleIcon className="w-5 h-5 text-green-500 flex-shrink-0 mt-1" />
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer info */}
        {notifications.length > 0 && (
          <div className="mt-8 text-center">
            <p className="text-sm text-gray-500">
              Notifications are automatically cleaned up after 30 days
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Notifications;
