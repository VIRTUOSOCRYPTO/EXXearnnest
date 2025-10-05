import { useCallback } from 'react';
import useWebSocket from './useWebSocket';

const useAdminWebSocket = (options = {}) => {
  const handleAdminMessage = useCallback((message) => {
    console.log('Admin WebSocket message:', message);
    
    // Handle admin-specific message types
    if (message.type === 'admin_request_submitted') {
      // Show high-priority notification for new admin requests
      if (options.onAdminRequestSubmitted) {
        options.onAdminRequestSubmitted(message);
      }
    }
    
    // Call the original onMessage handler if provided
    if (options.onMessage) {
      options.onMessage(message);
    }
  }, [options]);

  const {
    connectionStatus,
    notifications,
    sendMessage,
    markNotificationAsRead,
    clearNotifications,
    isConnected,
    lastMessage
  } = useWebSocket('admin', {
    ...options,
    onMessage: handleAdminMessage
  });

  const getPendingRequestsCount = useCallback(() => {
    sendMessage({
      type: 'get_pending_requests'
    });
  }, [sendMessage]);

  const subscribeToAdminUpdates = useCallback(() => {
    sendMessage({
      type: 'subscribe_admin_updates'
    });
  }, [sendMessage]);

  return {
    connectionStatus,
    notifications,
    sendMessage,
    markNotificationAsRead,
    clearNotifications,
    isConnected,
    lastMessage,
    
    // Admin-specific methods
    getPendingRequestsCount,
    subscribeToAdminUpdates
  };
};

export default useAdminWebSocket;
