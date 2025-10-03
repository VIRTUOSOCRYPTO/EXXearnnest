import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import pushNotificationService from '../services/pushNotificationService';
import {
  BellIcon,
  BellSlashIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  FireIcon,
  UsersIcon,
  TrophyIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const NotificationSettings = () => {
  const [preferences, setPreferences] = useState({
    streak_reminders: true,
    milestone_achievements: true,
    friend_activities: true,
    daily_reminders: true,
    reminder_time: "19:00"
  });
  const [permissionStatus, setPermissionStatus] = useState('default');
  const [isEnabled, setIsEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testNotificationSent, setTestNotificationSent] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    loadNotificationSettings();
  }, []);

  const loadNotificationSettings = async () => {
    try {
      setLoading(true);
      
      // Initialize push notification service
      await pushNotificationService.initialize();
      
      // Get current permission status
      const status = pushNotificationService.getPermissionStatus();
      setPermissionStatus(status);
      setIsEnabled(pushNotificationService.isEnabled());
      
      // Load user preferences
      const userPreferences = await pushNotificationService.getPreferences();
      if (userPreferences) {
        setPreferences(userPreferences);
      }
      
    } catch (error) {
      console.error('Failed to load notification settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEnableNotifications = async () => {
    try {
      setSaving(true);
      
      // Request permission
      const granted = await pushNotificationService.requestPermission();
      if (!granted) {
        alert('Please enable notifications in your browser settings to receive updates about your achievements and streaks.');
        return;
      }
      
      // Subscribe to push notifications
      const subscribed = await pushNotificationService.subscribe();
      if (subscribed) {
        setPermissionStatus('granted');
        setIsEnabled(true);
        
        // Send welcome notification
        pushNotificationService.showLocalNotification(
          '🎉 Notifications Enabled!',
          {
            body: 'You\'ll now receive updates about your streaks and achievements.',
            icon: '/icons/achievement-icon.png'
          }
        );
      }
      
    } catch (error) {
      console.error('Failed to enable notifications:', error);
      alert('Failed to enable notifications. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDisableNotifications = async () => {
    try {
      setSaving(true);
      
      const unsubscribed = await pushNotificationService.unsubscribe();
      if (unsubscribed) {
        setIsEnabled(false);
      }
      
    } catch (error) {
      console.error('Failed to disable notifications:', error);
      alert('Failed to disable notifications. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handlePreferenceChange = async (key, value) => {
    try {
      const newPreferences = { ...preferences, [key]: value };
      setPreferences(newPreferences);
      
      // Save to backend
      if (isEnabled) {
        setSaving(true);
        await pushNotificationService.updatePreferences(newPreferences);
        setSaving(false);
      }
      
    } catch (error) {
      console.error('Failed to update preferences:', error);
      // Revert the change
      setPreferences(preferences);
      setSaving(false);
    }
  };

  const handleTestNotification = async () => {
    try {
      if (!isEnabled) {
        alert('Please enable notifications first.');
        return;
      }
      
      // Show local test notification
      pushNotificationService.showLocalNotification(
        '🧪 Test Notification',
        {
          body: 'This is a test notification from EarnAura!',
          icon: '/icons/achievement-icon.png',
          requireInteraction: false
        }
      );
      
      setTestNotificationSent(true);
      setTimeout(() => setTestNotificationSent(false), 3000);
      
    } catch (error) {
      console.error('Failed to send test notification:', error);
      alert('Failed to send test notification.');
    }
  };

  const getPermissionStatusInfo = () => {
    switch (permissionStatus) {
      case 'granted':
        return {
          icon: CheckCircleIcon,
          color: 'text-green-600',
          bg: 'bg-green-50',
          message: 'Notifications are enabled'
        };
      case 'denied':
        return {
          icon: XCircleIcon,
          color: 'text-red-600',
          bg: 'bg-red-50',
          message: 'Notifications are blocked. Please enable them in your browser settings.'
        };
      case 'not-supported':
        return {
          icon: ExclamationTriangleIcon,
          color: 'text-orange-600',
          bg: 'bg-orange-50',
          message: 'Push notifications are not supported by your browser.'
        };
      default:
        return {
          icon: BellSlashIcon,
          color: 'text-gray-600',
          bg: 'bg-gray-50',
          message: 'Click to enable notifications'
        };
    }
  };

  const statusInfo = getPermissionStatusInfo();
  const StatusIcon = statusInfo.icon;

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <BellIcon className="w-6 h-6 mr-2 text-blue-600" />
          Notification Settings
        </h2>
        <p className="text-gray-600 mt-1">
          Stay updated with your progress and achievements
        </p>
      </div>

      {/* Permission Status */}
      <div className={`p-4 rounded-lg ${statusInfo.bg} border border-gray-200`}>
        <div className="flex items-center">
          <StatusIcon className={`w-5 h-5 ${statusInfo.color} mr-2`} />
          <span className={`font-medium ${statusInfo.color}`}>
            {statusInfo.message}
          </span>
        </div>
      </div>

      {/* Enable/Disable Toggle */}
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center">
          <BellIcon className="w-5 h-5 text-gray-600 mr-3" />
          <div>
            <h3 className="font-medium text-gray-900">Push Notifications</h3>
            <p className="text-sm text-gray-600">
              Receive notifications about your achievements and streaks
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          {testNotificationSent && (
            <span className="text-green-600 text-sm font-medium">
              ✓ Test sent!
            </span>
          )}
          
          {isEnabled && (
            <button
              onClick={handleTestNotification}
              className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
            >
              Test
            </button>
          )}
          
          <button
            onClick={isEnabled ? handleDisableNotifications : handleEnableNotifications}
            disabled={saving || permissionStatus === 'not-supported'}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              isEnabled
                ? 'bg-red-100 text-red-700 hover:bg-red-200'
                : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
            } ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {saving ? 'Updating...' : isEnabled ? 'Disable' : 'Enable'}
          </button>
        </div>
      </div>

      {/* Notification Preferences */}
      {isEnabled && (
        <div className="space-y-4">
          <h3 className="font-semibold text-gray-900">Notification Types</h3>
          
          {/* Streak Reminders */}
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center">
              <FireIcon className="w-5 h-5 text-orange-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">Streak Reminders</h4>
                <p className="text-sm text-gray-600">
                  Get reminded to maintain your daily streak
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.streak_reminders}
                onChange={(e) => handlePreferenceChange('streak_reminders', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Milestone Achievements */}
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center">
              <TrophyIcon className="w-5 h-5 text-yellow-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">Achievement Notifications</h4>
                <p className="text-sm text-gray-600">
                  Celebrate when you earn badges and reach milestones
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.milestone_achievements}
                onChange={(e) => handlePreferenceChange('milestone_achievements', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Friend Activities */}
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center">
              <UsersIcon className="w-5 h-5 text-purple-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">Friend Activities</h4>
                <p className="text-sm text-gray-600">
                  See when your friends achieve milestones
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.friend_activities}
                onChange={(e) => handlePreferenceChange('friend_activities', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Daily Reminders */}
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center">
              <ClockIcon className="w-5 h-5 text-blue-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">Daily Reminders</h4>
                <p className="text-sm text-gray-600">
                  Daily reminder to track your finances
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.daily_reminders}
                onChange={(e) => handlePreferenceChange('daily_reminders', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Reminder Time */}
          {preferences.daily_reminders && (
            <div className="p-3 border rounded-lg bg-blue-50">
              <div className="flex items-center justify-between">
                <label className="font-medium text-gray-900">
                  Reminder Time
                </label>
                <input
                  type="time"
                  value={preferences.reminder_time}
                  onChange={(e) => handlePreferenceChange('reminder_time', e.target.value)}
                  className="px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <p className="text-sm text-gray-600 mt-1">
                Best time for daily tracking reminders
              </p>
            </div>
          )}
        </div>
      )}

      {/* Browser Support Info */}
      {permissionStatus === 'not-supported' && (
        <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
          <p className="text-orange-700">
            <strong>Browser not supported:</strong> Your browser doesn't support push notifications. 
            Try using a modern browser like Chrome, Firefox, or Safari for the best experience.
          </p>
        </div>
      )}

      {/* Permission Denied Info */}
      {permissionStatus === 'denied' && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 mb-2">
            <strong>Notifications blocked:</strong> To receive notifications, please:
          </p>
          <ol className="text-red-700 text-sm list-decimal list-inside space-y-1">
            <li>Click the lock icon in your browser's address bar</li>
            <li>Select "Allow" for notifications</li>
            <li>Refresh this page and try again</li>
          </ol>
        </div>
      )}
    </div>
  );
};

export default NotificationSettings;
