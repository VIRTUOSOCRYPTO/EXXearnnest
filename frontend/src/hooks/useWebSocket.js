import { useState, useEffect, useCallback, useRef } from 'react';

const useWebSocket = (channel = 'default', options = {}) => {
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [notifications, setNotifications] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const heartbeatIntervalRef = useRef(null);

  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    autoReconnect = true,
    reconnectInterval = 1000, // Initial reconnect interval: 1 second
    maxReconnectAttempts = 10, // Increased for better resilience
    heartbeatInterval = 30000, // Send heartbeat every 30 seconds
    maxReconnectInterval = 30000 // Max exponential backoff: 30 seconds
  } = options;

  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Cleanup function to properly close WebSocket and clear timers
  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
    
    if (wsRef.current) {
      // Remove event listeners to prevent memory leaks
      wsRef.current.onopen = null;
      wsRef.current.onmessage = null;
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      
      // Close connection if open
      if (wsRef.current.readyState === WebSocket.OPEN || 
          wsRef.current.readyState === WebSocket.CONNECTING) {
        wsRef.current.close(1000, 'Component unmounting');
      }
      
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      // Get the backend URL and convert to WebSocket URL
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const wsUrl = backendUrl.replace('https://', 'wss://').replace('http://', 'ws://');
      const token = localStorage.getItem('token');
      
      if (!token) {
        console.log('No token available for WebSocket connection');
        return;
      }

      // Use correct WebSocket endpoint format matching backend (must include /api prefix for K8s ingress)
      const userId = JSON.parse(atob(token.split('.')[1])).user_id;
      wsRef.current = new WebSocket(`${wsUrl}/api/ws/${channel}/${userId}?token=${token}`);

      wsRef.current.onopen = () => {
        setConnectionStatus('Connected');
        setIsConnected(true);
        setReconnectAttempts(0);
        
        console.log(`WebSocket connected to ${channel} channel`);
        
        // Start heartbeat to keep connection alive
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }
        
        heartbeatIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, heartbeatInterval);
        
        if (onConnect) {
          onConnect();
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);
          
          // Don't process pong messages as notifications
          if (message.type === 'pong') {
            return;
          }
          
          // Add to notifications if it's a notification type
          if (message.type === 'notification' || message.notification_type) {
            setNotifications(prev => [message, ...prev.slice(0, 49)]); // Keep last 50
          }
          
          if (onMessage) {
            onMessage(message);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        setConnectionStatus('Disconnected');
        setIsConnected(false);
        
        // Clear heartbeat interval
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }
        
        console.log(`WebSocket disconnected from ${channel} channel (code: ${event.code})`);
        
        if (onDisconnect) {
          onDisconnect();
        }

        // Auto-reconnect logic with exponential backoff (only if not a normal closure)
        if (autoReconnect && reconnectAttempts < maxReconnectAttempts && event.code !== 1000) {
          setReconnectAttempts(prev => prev + 1);
          
          // Calculate exponential backoff: min(reconnectInterval * 2^attempts, maxReconnectInterval)
          const backoffDelay = Math.min(
            reconnectInterval * Math.pow(2, reconnectAttempts),
            maxReconnectInterval
          );
          
          console.log(`WebSocket reconnecting in ${backoffDelay}ms... (Attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Attempting to reconnect... (${reconnectAttempts + 1}/${maxReconnectAttempts})`);
            connect();
          }, backoffDelay);
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          console.error(`Max reconnect attempts (${maxReconnectAttempts}) reached. Giving up.`);
          setConnectionStatus('Failed');
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('Error');
        
        if (onError) {
          onError(error);
        }
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('Error');
      
      if (onError) {
        onError(error);
      }
    }
  }, [channel, onMessage, onConnect, onDisconnect, onError, autoReconnect, reconnectInterval, maxReconnectAttempts, reconnectAttempts, heartbeatInterval]);

  const disconnect = useCallback(() => {
    cleanup();
    setConnectionStatus('Disconnected');
    setIsConnected(false);
  }, [cleanup]);

  const sendMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  const markNotificationAsRead = useCallback((notificationId) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === notificationId 
          ? { ...notification, is_read: true }
          : notification
      )
    );
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Connect on mount if token is available
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      connect();
    }

    // Network status monitoring - reconnect when network comes back online
    const handleOnline = () => {
      console.log('Network connection restored, attempting to reconnect WebSocket...');
      setReconnectAttempts(0); // Reset attempts when network is back
      if (!isConnected && token) {
        connect();
      }
    };

    const handleOffline = () => {
      console.log('Network connection lost');
      setConnectionStatus('Offline');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Cleanup on unmount - CRITICAL FOR PREVENTING MEMORY LEAKS
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      cleanup();
    };
  }, [connect, cleanup, isConnected]);

  return {
    connectionStatus,
    notifications,
    sendMessage,
    markNotificationAsRead,
    clearNotifications,
    isConnected,
    lastMessage,
    connect,
    disconnect
  };
};

export default useWebSocket;
