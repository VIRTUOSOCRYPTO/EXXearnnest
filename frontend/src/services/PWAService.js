/**
 * Progressive Web App Service
 * Handles PWA functionality, offline support, and mobile optimizations
 */

class PWAService {
  constructor() {
    this.isOnline = navigator.onLine;
    this.serviceWorkerRegistration = null;
    this.deferredPrompt = null;
    this.offlineData = new Map();
    
    this.init();
  }

  async init() {
    // Register service worker
    await this.registerServiceWorker();
    
    // Setup offline detection
    this.setupOfflineDetection();
    
    // Setup install prompt
    this.setupInstallPrompt();
    
    // Setup push notifications
    this.setupPushNotifications();
    
    // Initialize offline storage
    this.initOfflineStorage();
    
    console.log('🎯 PWA Service initialized');
  }

  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js', {
          scope: '/',
          updateViaCache: 'none'
        });
        
        this.serviceWorkerRegistration = registration;
        
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                this.showUpdateNotification();
              }
            });
          }
        });
        
        console.log('✅ Service Worker registered:', registration.scope);
        
        // Check for updates every 30 minutes
        setInterval(() => {
          registration.update();
        }, 30 * 60 * 1000);
        
      } catch (error) {
        console.error('❌ Service Worker registration failed:', error);
      }
    }
  }

  setupOfflineDetection() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.showConnectionStatus('online');
      this.syncOfflineData();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.showConnectionStatus('offline');
    });
  }

  setupInstallPrompt() {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
      this.showInstallButton();
    });

    window.addEventListener('appinstalled', () => {
      console.log('✅ PWA installed successfully');
      this.hideInstallButton();
      this.trackEvent('pwa_installed');
    });
  }

  async setupPushNotifications() {
    if ('Notification' in window && 'serviceWorker' in navigator && 'PushManager' in window) {
      try {
        const permission = await Notification.requestPermission();
        if (permission === 'granted' && this.serviceWorkerRegistration) {
          await this.subscribeToPushNotifications();
        }
      } catch (error) {
        console.error('❌ Push notification setup failed:', error);
      }
    }
  }

  async subscribeToPushNotifications() {
    try {
      const subscription = await this.serviceWorkerRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlB64ToUint8Array('your-vapid-public-key') // Replace with actual key
      });

      // Send subscription to server
      await fetch('/api/push-notifications/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(subscription)
      });

      console.log('✅ Push notifications subscribed');
    } catch (error) {
      console.error('❌ Push notification subscription failed:', error);
    }
  }

  urlB64ToUint8Array(base64String) {
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

  initOfflineStorage() {
    // Initialize IndexedDB for offline data storage
    if ('indexedDB' in window) {
      const request = indexedDB.open('EarnNestOffline', 1);
      
      request.onerror = () => {
        console.error('❌ IndexedDB failed to open');
      };
      
      request.onsuccess = (event) => {
        this.offlineDB = event.target.result;
        console.log('✅ Offline storage initialized');
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Create object stores for offline data
        if (!db.objectStoreNames.contains('transactions')) {
          const transactionStore = db.createObjectStore('transactions', { keyPath: 'id', autoIncrement: true });
          transactionStore.createIndex('timestamp', 'timestamp', { unique: false });
        }
        
        if (!db.objectStoreNames.contains('analytics')) {
          db.createObjectStore('analytics', { keyPath: 'id', autoIncrement: true });
        }
        
        if (!db.objectStoreNames.contains('sync_queue')) {
          db.createObjectStore('sync_queue', { keyPath: 'id', autoIncrement: true });
        }
      };
    }
  }

  async installPWA() {
    if (this.deferredPrompt) {
      this.deferredPrompt.prompt();
      const { outcome } = await this.deferredPrompt.userChoice;
      
      if (outcome === 'accepted') {
        console.log('✅ User accepted PWA install');
        this.trackEvent('pwa_install_accepted');
      } else {
        console.log('❌ User declined PWA install');
        this.trackEvent('pwa_install_declined');
      }
      
      this.deferredPrompt = null;
      this.hideInstallButton();
    }
  }

  showInstallButton() {
    const installButton = document.getElementById('pwa-install-btn');
    if (installButton) {
      installButton.style.display = 'block';
      installButton.addEventListener('click', () => this.installPWA());
    }
  }

  hideInstallButton() {
    const installButton = document.getElementById('pwa-install-btn');
    if (installButton) {
      installButton.style.display = 'none';
    }
  }

  showConnectionStatus(status) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
      statusElement.className = `connection-status ${status}`;
      statusElement.textContent = status === 'online' ? '🟢 Online' : '🔴 Offline';
      
      setTimeout(() => {
        statusElement.className = 'connection-status hidden';
      }, 3000);
    }
  }

  showUpdateNotification() {
    const notification = document.createElement('div');
    notification.className = 'update-notification';
    notification.innerHTML = `
      <div class="update-content">
        <span>🔄 New version available!</span>
        <button onclick="pwaService.updateApp()" class="update-btn">Update</button>
        <button onclick="this.parentElement.parentElement.remove()" class="dismiss-btn">×</button>
      </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      if (notification.parentElement) {
        notification.remove();
      }
    }, 10000);
  }

  async updateApp() {
    if (this.serviceWorkerRegistration && this.serviceWorkerRegistration.waiting) {
      this.serviceWorkerRegistration.waiting.postMessage({ action: 'skipWaiting' });
      window.location.reload();
    }
  }

  // Offline data management
  async saveOfflineTransaction(transactionData) {
    if (!this.isOnline && this.offlineDB) {
      try {
        const transaction = this.offlineDB.transaction(['transactions'], 'readwrite');
        const store = transaction.objectStore('transactions');
        
        const offlineTransaction = {
          ...transactionData,
          timestamp: Date.now(),
          synced: false,
          token: localStorage.getItem('token')
        };
        
        await store.add(offlineTransaction);
        
        // Schedule background sync
        if (this.serviceWorkerRegistration && this.serviceWorkerRegistration.sync) {
          await this.serviceWorkerRegistration.sync.register('background-transaction-sync');
        }
        
        console.log('💾 Transaction saved offline');
        return true;
        
      } catch (error) {
        console.error('❌ Failed to save offline transaction:', error);
        return false;
      }
    }
    return false;
  }

  async syncOfflineData() {
    if (this.isOnline && this.offlineDB) {
      try {
        const transaction = this.offlineDB.transaction(['transactions'], 'readonly');
        const store = transaction.objectStore('transactions');
        const request = store.getAll();
        
        request.onsuccess = async () => {
          const offlineTransactions = request.result.filter(t => !t.synced);
          
          for (const txn of offlineTransactions) {
            try {
              const response = await fetch('/api/transactions', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${txn.token}`
                },
                body: JSON.stringify({
                  type: txn.type,
                  amount: txn.amount,
                  category: txn.category,
                  description: txn.description
                })
              });
              
              if (response.ok) {
                // Mark as synced
                const updateTransaction = this.offlineDB.transaction(['transactions'], 'readwrite');
                const updateStore = updateTransaction.objectStore('transactions');
                txn.synced = true;
                await updateStore.put(txn);
                
                console.log('✅ Offline transaction synced:', txn.id);
              }
              
            } catch (error) {
              console.error('❌ Sync failed for transaction:', txn.id, error);
            }
          }
        };
        
      } catch (error) {
        console.error('❌ Offline sync failed:', error);
      }
    }
  }

  // Mobile-specific optimizations
  enableMobileOptimizations() {
    // Prevent zoom on input focus (iOS Safari)
    const metaViewport = document.querySelector('meta[name="viewport"]');
    if (metaViewport) {
      metaViewport.setAttribute('content', 
        'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no'
      );
    }
    
    // Add mobile-specific CSS classes
    document.body.classList.add('mobile-optimized');
    
    // Setup touch gestures
    this.setupTouchGestures();
    
    // Setup haptic feedback
    this.setupHapticFeedback();
    
    // Optimize for mobile keyboards
    this.optimizeForMobileKeyboard();
  }

  setupTouchGestures() {
    let startX, startY, distanceX, distanceY;
    
    document.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
    });
    
    document.addEventListener('touchmove', (e) => {
      if (!startX || !startY) return;
      
      distanceX = e.touches[0].clientX - startX;
      distanceY = e.touches[0].clientY - startY;
    });
    
    document.addEventListener('touchend', () => {
      if (Math.abs(distanceX) > Math.abs(distanceY)) {
        if (Math.abs(distanceX) > 100) {
          // Horizontal swipe
          if (distanceX > 0) {
            this.handleSwipeRight();
          } else {
            this.handleSwipeLeft();
          }
        }
      } else {
        if (Math.abs(distanceY) > 100) {
          // Vertical swipe
          if (distanceY > 0) {
            this.handleSwipeDown();
          } else {
            this.handleSwipeUp();
          }
        }
      }
      
      startX = startY = distanceX = distanceY = null;
    });
  }

  handleSwipeRight() {
    // Navigate back
    const event = new CustomEvent('swipeRight');
    window.dispatchEvent(event);
  }

  handleSwipeLeft() {
    // Navigate forward or open menu
    const event = new CustomEvent('swipeLeft');
    window.dispatchEvent(event);
  }

  handleSwipeDown() {
    // Refresh content
    const event = new CustomEvent('swipeDown');
    window.dispatchEvent(event);
  }

  handleSwipeUp() {
    // Show more content or quick actions
    const event = new CustomEvent('swipeUp');
    window.dispatchEvent(event);
  }

  setupHapticFeedback() {
    // Simulate haptic feedback on supported devices
    this.hapticFeedback = (type = 'medium') => {
      if ('vibrate' in navigator) {
        const patterns = {
          light: [10],
          medium: [20],
          heavy: [30],
          success: [10, 50, 10],
          error: [50, 100, 50]
        };
        
        navigator.vibrate(patterns[type] || patterns.medium);
      }
    };
  }

  optimizeForMobileKeyboard() {
    // Adjust viewport when keyboard appears
    const inputs = document.querySelectorAll('input, textarea');
    
    inputs.forEach(input => {
      input.addEventListener('focus', () => {
        // Scroll element into view
        setTimeout(() => {
          input.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
      });
    });
  }

  // Performance monitoring
  trackEvent(eventName, data = {}) {
    if (this.isOnline) {
      fetch('/api/analytics/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          event: eventName,
          timestamp: Date.now(),
          ...data
        })
      }).catch(() => {
        // Store offline for later sync
        this.saveOfflineAnalytics(eventName, data);
      });
    } else {
      this.saveOfflineAnalytics(eventName, data);
    }
  }

  async saveOfflineAnalytics(eventName, data) {
    if (this.offlineDB) {
      try {
        const transaction = this.offlineDB.transaction(['analytics'], 'readwrite');
        const store = transaction.objectStore('analytics');
        
        await store.add({
          event: eventName,
          data,
          timestamp: Date.now(),
          synced: false
        });
        
      } catch (error) {
        console.error('❌ Failed to save offline analytics:', error);
      }
    }
  }

  // Utility methods
  isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone ||
           document.referrer.includes('android-app://');
  }

  isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  }

  supportsNotifications() {
    return 'Notification' in window;
  }

  supportsPushMessaging() {
    return 'serviceWorker' in navigator && 'PushManager' in window;
  }
}

// Create global PWA service instance
const pwaService = new PWAService();

// Export for use in React components
export default pwaService;
