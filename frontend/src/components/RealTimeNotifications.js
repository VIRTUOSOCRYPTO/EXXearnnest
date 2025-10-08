import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../App';
import useWebSocket from '../hooks/useWebSocket';
import { 
  BellIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  InformationCircleIcon,
  XMarkIcon,
  ShieldCheckIcon,
  DocumentArrowUpIcon,
  EnvelopeIcon,
  TrophyIcon,
  UsersIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';

const RealTimeNotifications = () => {
  const { user } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [toasts, setToasts] = useState([]);

  const handleNewNotification = useCallback((message) => {
    console.log('New real-time notification:', message);
    
    // Don't show system messages as toasts
    if (message.type === 'connection_established' || message.type === 'admin_connection_established') {
      return;
    }
    
    // Create toast notification for important messages
    if (message.priority === 'high') {
      const toast = {
        id: Date.now() + Math.random(),
        type: message.type,
        title: message.title || 'Notification',
        message: message.message,
        priority: message.priority,
        timestamp: new Date(),
        autoHide: message.priority !== 'high'
      };
      
      setToasts(prev => [toast, ...prev].slice(0, 5)); // Keep max 5 toasts
      
      // Auto-remove toast after 5 seconds for non-high priority
      if (toast.autoHide) {
        setTimeout(() => {
          setToasts(prev => prev.filter(t => t.id !== toast.id));
        }, 5000);
      }
    }
  }, []);

  const {
    connectionStatus,
    notifications,
    markNotificationAsRead,
    clearNotifications,
    isConnected
  } = useWebSocket('notifications', {
    onMessage: handleNewNotification,
    onConnect: () => console.log('Real-time notifications connected'),
    onDisconnect: () => console.log('Real-time notifications disconnected'),
    onError: (error) => console.error('Real-time notifications error:', error)
  });

  // Update unread count
  useEffect(() => {
    const unread = notifications.filter(n => !n.read).length;
    setUnreadCount(unread);
  }, [notifications]);

  const getNotificationIcon = (type) => {
    const iconMap = {
      admin_request_submitted: ShieldCheckIcon,
      admin_request_status_update: CheckCircleIcon,
      admin_privileges_granted: TrophyIcon,
      document_uploaded: DocumentArrowUpIcon,
      email_verification_update: EnvelopeIcon,
      system_maintenance: Cog6ToothIcon,
      default: InformationCircleIcon
    };
    
    return iconMap[type] || iconMap.default;
  };

  const getPriorityColor = (priority) => {
    const colorMap = {
      high: 'text-red-600 bg-red-50 border-red-200',
      medium: 'text-yellow-600 bg-yellow-50 border-yellow-200',
      low: 'text-blue-600 bg-blue-50 border-blue-200'
    };
    
    return colorMap[priority] || colorMap.medium;
  };

  const dismissToast = (toastId) => {
    setToasts(prev => prev.filter(t => t.id !== toastId));
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInSeconds = Math.floor((now - time) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  if (!user) return null;

  return (
    <>
      {/* Notification Bell */}
      <div className="relative">
        <button
          onClick={() => setShowNotifications(!showNotifications)}
          className="relative p-2 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          title="Notifications"
        >
          <BellIcon className="w-6 h-6 text-gray-600" />
          
          {/* Connection Status Indicator */}
          <div className={`absolute -top-1 -left-1 w-3 h-3 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`} title={`Real-time: ${connectionStatus}`} />
          
          {/* Unread Count Badge */}
          {unreadCount > 0 && (
            <div className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {unreadCount > 99 ? '99+' : unreadCount}
            </div>
          )}
        </button>

        {/* Notifications Dropdown */}
        {showNotifications && (
          <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-[60] max-h-96 overflow-y-auto">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="font-semibold text-gray-800">Notifications</h3>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-xs text-gray-500">{connectionStatus}</span>
                {notifications.length > 0 && (
                  <button
                    onClick={clearNotifications}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Clear All
                  </button>
                )}
              </div>
            </div>
            
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <BellIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>No notifications yet</p>
                  <p className="text-xs text-gray-400 mt-1">
                    You'll see real-time updates here
                  </p>
                </div>
              ) : (
                notifications.map((notification, index) => {
                  const IconComponent = getNotificationIcon(notification.type);
                  
                  return (
                    <div
                      key={index}
                      className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${
                        !notification.read ? 'bg-blue-50' : ''
                      }`}
                      onClick={() => {
                        if (!notification.read && notification.notification_id) {
                          markNotificationAsRead(notification.notification_id);
                        }
                      }}
                    >
                      <div className="flex items-start space-x-3">
                        <IconComponent className="w-5 h-5 text-gray-600 mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm text-gray-800">
                            {notification.title}
                          </p>
                          <p className="text-sm text-gray-600 mt-1">
                            {notification.message}
                          </p>
                          <div className="flex items-center justify-between mt-2">
                            <span className="text-xs text-gray-400">
                              {formatTimeAgo(notification.timestamp)}
                            </span>
                            {notification.priority && (
                              <span className={`text-xs px-2 py-1 rounded-full ${getPriorityColor(notification.priority)}`}>
                                {notification.priority}
                              </span>
                            )}
                          </div>
                        </div>
                        {!notification.read && (
                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2" />
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>

      {/* Toast Notifications */}
      <div className="fixed top-4 right-4 z-[70] space-y-2">
        {toasts.map((toast) => {
          const IconComponent = getNotificationIcon(toast.type);
          
          return (
            <div
              key={toast.id}
              className={`min-w-80 max-w-sm bg-white rounded-lg shadow-lg border-l-4 ${
                toast.priority === 'high' ? 'border-red-500' : 
                toast.priority === 'medium' ? 'border-yellow-500' : 'border-blue-500'
              } p-4 animate-slide-in-right`}
            >
              <div className="flex items-start">
                <IconComponent className={`w-5 h-5 mt-0.5 mr-3 ${
                  toast.priority === 'high' ? 'text-red-600' : 
                  toast.priority === 'medium' ? 'text-yellow-600' : 'text-blue-600'
                }`} />
                <div className="flex-1">
                  <p className="font-medium text-sm text-gray-800">
                    {toast.title}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {toast.message}
                  </p>
                </div>
                <button
                  onClick={() => dismissToast(toast.id)}
                  className="ml-2 text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Click outside to close notifications */}
      {showNotifications && (
        <div
          className="fixed inset-0 z-[55]"
          onClick={() => setShowNotifications(false)}
        />
      )}
    </>
  );
};

export default RealTimeNotifications;
