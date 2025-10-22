import { create } from 'zustand';

const useNotificationStore = create((set, get) => ({
  notifications: [],
  unreadCount: 0,
  isConnected: false,
  
  addNotification: (notification) => {
    set((state) => ({
      notifications: [notification, ...state.notifications].slice(0, 50), // Keep last 50
      unreadCount: state.unreadCount + 1
    }));
  },
  
  markAsRead: (notificationId) => {
    set((state) => ({
      notifications: state.notifications.map(n => 
        n.id === notificationId ? { ...n, read: true } : n
      ),
      unreadCount: Math.max(0, state.unreadCount - 1)
    }));
  },
  
  markAllAsRead: () => {
    set((state) => ({
      notifications: state.notifications.map(n => ({ ...n, read: true })),
      unreadCount: 0
    }));
  },
  
  setConnected: (isConnected) => set({ isConnected }),
  
  clearNotifications: () => set({ notifications: [], unreadCount: 0 }),
}));

export default useNotificationStore;
