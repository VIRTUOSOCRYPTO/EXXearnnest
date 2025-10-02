const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// VAPID public key for push notifications
const VAPID_PUBLIC_KEY = 'BF8Q8WvFz-K-T1n_Xz_8t1XMGx5G7_8vY2_I-4LW_9_O-5P-R7k_Y1vJ2_M3_N8d'; // Replace with your actual VAPID public key

class PushNotificationService {
  constructor() {
    this.registration = null;
    this.subscription = null;
    this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
    this.token = localStorage.getItem('token');
  }

  async initialize() {
    if (!this.isSupported) {
      console.warn('Push notifications not supported');
      return false;
    }

    try {
      // Register service worker
      this.registration = await navigator.serviceWorker.register('/sw.js');
      console.log('Service worker registered:', this.registration);
      
      // Wait for service worker to be ready
      await navigator.serviceWorker.ready;
      
      return true;
    } catch (error) {
      console.error('Service worker registration failed:', error);
      return false;
    }
  }

  async requestPermission() {
    if (!this.isSupported) {
      return false;
    }

    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }

  async subscribe() {
    if (!this.registration || !this.token) {
      console.warn('Service worker not registered or user not authenticated');
      return false;
    }

    try {
      // Check if already subscribed
      const existingSubscription = await this.registration.pushManager.getSubscription();
      if (existingSubscription) {
        this.subscription = existingSubscription;
        return await this.sendSubscriptionToBackend(existingSubscription);
      }

      // Create new subscription
      const subscription = await this.registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
      });

      this.subscription = subscription;
      return await this.sendSubscriptionToBackend(subscription);
      
    } catch (error) {
      console.error('Failed to subscribe to push notifications:', error);
      return false;
    }
  }

  async sendSubscriptionToBackend(subscription) {
    try {
      const response = await fetch(`${API}/notifications/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.token}`
        },
        body: JSON.stringify(subscription.toJSON())
      });

      if (response.ok) {
        console.log('Push subscription sent to backend');
        localStorage.setItem('pushNotificationEnabled', 'true');
        return true;
      } else {
        console.error('Failed to send subscription to backend:', response.statusText);
        return false;
      }
    } catch (error) {
      console.error('Error sending subscription to backend:', error);
      return false;
    }
  }

  async unsubscribe() {
    if (!this.subscription) {
      return true;
    }

    try {
      await this.subscription.unsubscribe();
      this.subscription = null;
      localStorage.removeItem('pushNotificationEnabled');
      console.log('Unsubscribed from push notifications');
      return true;
    } catch (error) {
      console.error('Failed to unsubscribe:', error);
      return false;
    }
  }

  async updatePreferences(preferences) {
    if (!this.token) {
      return false;
    }

    try {
      const response = await fetch(`${API}/notifications/preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.token}`
        },
        body: JSON.stringify(preferences)
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to update notification preferences:', error);
      return false;
    }
  }

  async getPreferences() {
    if (!this.token) {
      return null;
    }

    try {
      const response = await fetch(`${API}/notifications/preferences`, {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      });

      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('Failed to get notification preferences:', error);
      return null;
    }
  }

  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  isEnabled() {
    return localStorage.getItem('pushNotificationEnabled') === 'true';
  }

  getPermissionStatus() {
    if (!this.isSupported) {
      return 'not-supported';
    }
    return Notification.permission;
  }

  // Show local notification (for testing or immediate feedback)
  showLocalNotification(title, options = {}) {
    if (Notification.permission === 'granted') {
      return new Notification(title, {
        icon: '/icons/achievement-icon.png',
        badge: '/icons/badge-icon.png',
        ...options
      });
    }
    return null;
  }

  // Setup notification click handlers
  setupNotificationHandlers() {
    if (!this.isSupported) return;

    navigator.serviceWorker.addEventListener('message', (event) => {
      if (event.data && event.data.type === 'NOTIFICATION_CLICK') {
        const data = event.data.payload;
        
        // Handle different notification types
        switch (data.type) {
          case 'milestone_achievement':
            window.location.href = '/gamification';
            break;
          case 'streak_reminder':
            window.location.href = '/transaction';
            break;
          case 'friend_achievement':
            window.location.href = '/gamification';
            break;
          default:
            window.location.href = '/';
        }
      }
    });
  }

  // Test notification (for development/testing)
  async sendTestNotification() {
    if (!this.isEnabled()) {
      console.warn('Push notifications not enabled');
      return false;
    }

    try {
      const response = await fetch(`${API}/gamification/trigger-milestone-check`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to send test notification:', error);
      return false;
    }
  }

  // Schedule daily reminders based on user preferences
  async scheduleDailyReminders(reminderTime = "19:00") {
    const preferences = await this.getPreferences();
    if (!preferences || !preferences.daily_reminders) {
      return false;
    }

    // Update preferences with new reminder time
    return await this.updatePreferences({
      ...preferences,
      reminder_time: reminderTime
    });
  }
}

// Create singleton instance
const pushNotificationService = new PushNotificationService();

export default pushNotificationService;
