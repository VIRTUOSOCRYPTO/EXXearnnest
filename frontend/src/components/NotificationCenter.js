import React, { useState, useEffect } from 'react';
import axios from '../utils/axiosConfig';
import { NotificationSkeleton } from './ui/skeleton';

const NotificationCenter = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, unread, read
  const [typeFilter, setTypeFilter] = useState('all'); // all, transaction, goal, leaderboard, etc.
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    fetchNotifications();
  }, [filter, typeFilter, page]);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const params = {
        page,
        limit: 20
      };
      
      if (filter === 'unread') {
        params.unread_only = true;
      } else if (filter === 'read') {
        params.read_only = true;
      }
      
      if (typeFilter !== 'all') {
        params.type = typeFilter;
      }

      const response = await axios.get('/api/notifications', { params });
      
      if (page === 1) {
        setNotifications(response.data.notifications || []);
      } else {
        setNotifications(prev => [...prev, ...(response.data.notifications || [])]);
      }
      
      setHasMore(response.data.has_more || false);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await axios.put(`/api/notifications/${notificationId}/read`);
      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      );
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await axios.put('/api/notifications/mark-all-read');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  };

  const deleteNotification = async (notificationId) => {
    try {
      await axios.delete(`/api/notifications/${notificationId}`);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  const clearAll = async () => {
    if (!window.confirm('Are you sure you want to clear all notifications?')) {
      return;
    }
    
    try {
      await axios.delete('/api/notifications/clear-all');
      setNotifications([]);
    } catch (error) {
      console.error('Error clearing notifications:', error);
    }
  };

  const getNotificationIcon = (type) => {
    const icons = {
      transaction_income: '💰',
      transaction_expense: '💸',
      goal_progress: '🎯',
      goal_completed: '✅',
      leaderboard_update: '🏆',
      top_rank_achieved: '🥇',
      budget_alert: '⚠️',
      budget_exceeded: '🚨',
      challenge_completed: '🎉',
      challenge_progress: '📈',
      streak_milestone: '🔥',
      friend_activity: '👥',
      registration_approved: '✅',
      registration_rejected: '❌',
      default: '🔔'
    };
    return icons[type] || icons.default;
  };

  const getPriorityColor = (priority) => {
    const colors = {
      high: 'border-l-4 border-red-500 bg-red-50',
      medium: 'border-l-4 border-yellow-500 bg-yellow-50',
      low: 'border-l-4 border-blue-500 bg-blue-50'
    };
    return colors[priority] || colors.low;
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
    
    return date.toLocaleDateString();
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">
                🔔 Notification Center
              </h1>
              <p className="text-gray-600 mt-1">
                {unreadCount > 0 ? `${unreadCount} unread notification${unreadCount !== 1 ? 's' : ''}` : 'All caught up!'}
              </p>
            </div>
            <div className="flex gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Mark all read
                </button>
              )}
              <button
                onClick={clearAll}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
              >
                Clear all
              </button>
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            {/* Read/Unread Filter */}
            <div className="flex gap-2">
              <button
                onClick={() => { setFilter('all'); setPage(1); }}
                className={`px-4 py-2 rounded-lg transition ${
                  filter === 'all'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                All
              </button>
              <button
                onClick={() => { setFilter('unread'); setPage(1); }}
                className={`px-4 py-2 rounded-lg transition ${
                  filter === 'unread'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Unread
              </button>
              <button
                onClick={() => { setFilter('read'); setPage(1); }}
                className={`px-4 py-2 rounded-lg transition ${
                  filter === 'read'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Read
              </button>
            </div>

            {/* Type Filter */}
            <select
              value={typeFilter}
              onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="all">All Types</option>
              <option value="transaction_income">Income</option>
              <option value="transaction_expense">Expense</option>
              <option value="goal_progress">Goals</option>
              <option value="leaderboard_update">Leaderboards</option>
              <option value="budget_alert">Budget Alerts</option>
              <option value="challenge_completed">Challenges</option>
              <option value="friend_activity">Friends</option>
            </select>
          </div>
        </div>

        {/* Notifications List */}
        <div className="space-y-3">
          {loading && page === 1 ? (
            <NotificationSkeleton count={5} />
          ) : notifications.length === 0 ? (
            <div className="bg-white rounded-xl shadow-lg p-12 text-center">
              <div className="text-6xl mb-4">🔕</div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">No notifications</h3>
              <p className="text-gray-600">You're all caught up! Check back later for updates.</p>
            </div>
          ) : (
            <>
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`bg-white rounded-xl shadow-md p-4 transition hover:shadow-lg ${
                    !notification.is_read ? 'ring-2 ring-purple-500' : ''
                  } ${getPriorityColor(notification.priority || 'low')}`}
                >
                  <div className="flex items-start gap-4">
                    {/* Icon */}
                    <div className="text-3xl flex-shrink-0">
                      {getNotificationIcon(notification.type)}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="font-semibold text-gray-800 text-lg">
                          {notification.title}
                        </h3>
                        {!notification.is_read && (
                          <span className="w-2 h-2 bg-purple-600 rounded-full flex-shrink-0 mt-2"></span>
                        )}
                      </div>
                      <p className="text-gray-600 mt-1">{notification.message}</p>
                      <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                        <span>{formatTime(notification.created_at)}</span>
                        {notification.priority === 'high' && (
                          <span className="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-semibold">
                            High Priority
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2">
                      {!notification.is_read && (
                        <button
                          onClick={() => markAsRead(notification.id)}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                        >
                          Mark read
                        </button>
                      )}
                      <button
                        onClick={() => deleteNotification(notification.id)}
                        className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}

              {/* Load More */}
              {hasMore && (
                <div className="text-center py-6">
                  <button
                    onClick={() => setPage(p => p + 1)}
                    disabled={loading}
                    className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50"
                  >
                    {loading ? 'Loading...' : 'Load More'}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default NotificationCenter;
