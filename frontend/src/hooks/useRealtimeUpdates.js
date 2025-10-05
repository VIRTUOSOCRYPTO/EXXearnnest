import { useEffect, useCallback, useRef } from 'react';

const useRealtimeUpdates = (onUpdate) => {
  const intervalRef = useRef(null);
  const lastUpdateRef = useRef(Date.now());

  const startPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Poll every 30 seconds for live updates
    intervalRef.current = setInterval(() => {
      if (onUpdate) {
        onUpdate();
        lastUpdateRef.current = Date.now();
      }
    }, 30000);
  }, [onUpdate]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const forceUpdate = useCallback(() => {
    if (onUpdate) {
      onUpdate();
      lastUpdateRef.current = Date.now();
    }
  }, [onUpdate]);

  useEffect(() => {
    startPolling();
    
    // Handle page visibility changes
    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopPolling();
      } else {
        // Force update when page becomes visible again
        forceUpdate();
        startPolling();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      stopPolling();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [startPolling, stopPolling, forceUpdate]);

  return {
    forceUpdate,
    lastUpdate: lastUpdateRef.current,
    isActive: !!intervalRef.current
  };
};

export default useRealtimeUpdates;
