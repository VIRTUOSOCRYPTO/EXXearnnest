import { useState, useEffect, useCallback, useRef } from 'react';

const useWebSocket = (channel = 'default', options = {}) => {
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [notifications, setNotifications] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5
  } = options;

  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8001';
      const token = localStorage.getItem('token');
      
      if (!token) {
        console.log('No token available for WebSocket connection');
        return;
      }

      wsRef.current = new WebSocket(`${wsUrl}/ws/${channel}?token=${token}`);

      wsRef.current.onopen = () => {
        setConnectionStatus('Connected');
        setIsConnected(true);
        setReconnectAttempts(0);
        
        console.log(`WebSocket connected to ${channel} channel`);
        
        if (onConnect) {
          onConnect();
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);
          
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

      wsRef.current.onclose = () => {
        setConnectionStatus('Disconnected');
        setIsConnected(false);
        
        console.log(`WebSocket disconnected from ${channel} channel`);
        
        if (onDisconnect) {
          onDisconnect();
        }

        // Auto-reconnect logic
        if (autoReconnect && reconnectAttempts < maxReconnectAttempts) {
          setReconnectAttempts(prev => prev + 1);
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Attempting to reconnect... (${reconnectAttempts + 1}/${maxReconnectAttempts})`);
            connect();
          }, reconnectInterval);
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
  }, [channel, onMessage, onConnect, onDisconnect, onError, autoReconnect, reconnectInterval, maxReconnectAttempts, reconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    setConnectionStatus('Disconnected');
    setIsConnected(false);
  }, []);

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

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      disconnect();
    };
  }, [disconnect]);

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
