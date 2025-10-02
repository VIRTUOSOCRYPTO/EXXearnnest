// Service Worker for Push Notifications - EarnNest App
const CACHE_NAME = 'earnest-push-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/icons/achievement-icon.png',
  '/icons/badge-icon.png',
  '/icons/streak-icon.png',
  '/icons/friend-icon.png'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
  console.log('Service worker installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  console.log('Service worker activating...');
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Push event - handle incoming push notifications
self.addEventListener('push', (event) => {
  console.log('Push event received:', event);
  
  const defaultOptions = {
    icon: '/icons/achievement-icon.png',
    badge: '/icons/badge-icon.png',
    vibrate: [200, 100, 200],
    requireInteraction: false,
    actions: [
      {
        action: 'view',
        title: '👀 View'
      },
      {
        action: 'dismiss',
        title: '✖️ Dismiss'
      }
    ]
  };

  let notificationData;
  
  try {
    notificationData = event.data ? event.data.json() : {};
  } catch (error) {
    console.error('Failed to parse notification data:', error);
    notificationData = {
      title: 'EarnNest',
      body: 'You have a new achievement!',
      ...defaultOptions
    };
  }

  const options = {
    ...defaultOptions,
    ...notificationData,
    data: notificationData.data || {}
  };

  event.waitUntil(
    self.registration.showNotification(
      notificationData.title || 'EarnNest Achievement',
      options
    )
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event.notification);
  
  event.notification.close();
  
  const data = event.notification.data || {};
  let url = '/';

  // Determine URL based on notification type
  if (data.type === 'milestone_achievement') {
    url = '/gamification';
    if (data.achievement_id) {
      url += `?celebrate=${data.achievement_id}`;
    }
  } else if (data.type === 'streak_reminder') {
    url = '/transaction';
  } else if (data.type === 'friend_achievement') {
    url = '/gamification';
  } else if (data.url) {
    url = data.url;
  }

  // Handle different actions
  if (event.action === 'view') {
    // Open the app with appropriate URL
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then((clientList) => {
        // Check if app is already open
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.focus();
            client.navigate(url);
            return;
          }
        }
        
        // Open new window if app not open
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
    );
  } else if (event.action === 'share' && data.type === 'milestone_achievement') {
    // Handle share action for achievements
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then((clientList) => {
        if (clientList.length > 0) {
          // Send message to app to trigger share modal
          clientList[0].postMessage({
            type: 'SHARE_ACHIEVEMENT',
            payload: data
          });
          clientList[0].focus();
        }
      })
    );
  } else if (event.action === 'dismiss') {
    // Just close the notification (already done above)
    return;
  } else {
    // Default click - open app
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then((clientList) => {
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.focus();
            if (url !== '/') {
              client.navigate(url);
            }
            return;
          }
        }
        
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
    );
  }

  // Send click data to app for tracking
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      if (clientList.length > 0) {
        clientList[0].postMessage({
          type: 'NOTIFICATION_CLICK',
          payload: data
        });
      }
    })
  );
});

// Background sync for offline notifications
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-achievements') {
    event.waitUntil(syncAchievements());
  }
});

async function syncAchievements() {
  try {
    // Sync pending celebrations when coming back online
    const token = await getStoredToken();
    if (!token) return;

    const response = await fetch('/api/gamification/celebrations/pending', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.ok) {
      const data = await response.json();
      
      // Show notifications for pending celebrations
      for (const celebration of data.celebrations) {
        await self.registration.showNotification(
          celebration.title || 'Achievement Unlocked!',
          {
            body: celebration.message,
            icon: '/icons/achievement-icon.png',
            badge: '/icons/badge-icon.png',
            data: {
              type: 'milestone_achievement',
              achievement_id: celebration.achievement_id,
              url: '/gamification'
            },
            actions: [
              {
                action: 'view',
                title: 'View Achievement'
              },
              {
                action: 'share',
                title: 'Share'
              }
            ],
            requireInteraction: celebration.priority === 'high'
          }
        );
      }
    }
  } catch (error) {
    console.error('Failed to sync achievements:', error);
  }
}

async function getStoredToken() {
  // Get token from IndexedDB or other storage
  try {
    const db = await openDB();
    const transaction = db.transaction(['tokens'], 'readonly');
    const store = transaction.objectStore('tokens');
    const result = await store.get('authToken');
    return result?.token;
  } catch (error) {
    console.error('Failed to get stored token:', error);
    return null;
  }
}

// Message event - handle messages from app
self.addEventListener('message', (event) => {
  console.log('Service worker received message:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Fetch event - network requests (optional caching strategy)
self.addEventListener('fetch', (event) => {
  // Only handle GET requests and ignore chrome-extension requests
  if (event.request.method !== 'GET' || event.request.url.startsWith('chrome-extension://')) {
    return;
  }

  // Cache-first strategy for static assets
  if (event.request.url.includes('/static/') || event.request.url.includes('/icons/')) {
    event.respondWith(
      caches.match(event.request)
        .then((response) => {
          return response || fetch(event.request);
        })
    );
  }
});
