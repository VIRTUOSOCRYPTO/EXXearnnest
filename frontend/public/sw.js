// Service Worker for EarnNest PWA
// Provides offline capability, caching, and background sync

const CACHE_NAME = 'earnnest-v1.2.0';
const OFFLINE_URL = '/offline.html';

// Resources to cache for offline functionality
const STATIC_CACHE_URLS = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/offline.html',
  '/manifest.json',
  // Add critical pages for offline access
  '/dashboard',
  '/transactions',
  '/analytics',
  '/profile'
];

// API endpoints to cache responses
const API_CACHE_URLS = [
  '/api/user/profile',
  '/api/auth/trending-skills',
  '/api/auth/avatars',
  '/api/categories',
  '/api/emergency-types'
];

// Dynamic content that should be network-first
const NETWORK_FIRST_URLS = [
  '/api/transactions',
  '/api/analytics',
  '/api/budgets',
  '/api/financial-goals',
  '/api/gamification',
  '/api/notifications'
];

// Install event - cache static resources
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker installing...');
  
  event.waitUntil(
    (async () => {
      try {
        const cache = await caches.open(CACHE_NAME);
        console.log('📦 Caching static resources...');
        
        // Cache static resources with error handling
        for (const url of STATIC_CACHE_URLS) {
          try {
            await cache.add(url);
          } catch (error) {
            console.warn(`Failed to cache ${url}:`, error);
          }
        }
        
        // Force activation of new service worker
        self.skipWaiting();
        console.log('✅ Service Worker installed successfully');
        
      } catch (error) {
        console.error('❌ Service Worker installation failed:', error);
      }
    })()
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('🚀 Service Worker activating...');
  
  event.waitUntil(
    (async () => {
      try {
        // Take control of all pages immediately
        await self.clients.claim();
        
        // Clean up old caches
        const cacheNames = await caches.keys();
        await Promise.all(
          cacheNames
            .filter(cacheName => cacheName !== CACHE_NAME)
            .map(cacheName => {
              console.log(`🗑️ Deleting old cache: ${cacheName}`);
              return caches.delete(cacheName);
            })
        );
        
        console.log('✅ Service Worker activated successfully');
        
      } catch (error) {
        console.error('❌ Service Worker activation failed:', error);
      }
    })()
  );
});

// Fetch event - handle network requests with caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests and chrome-extension requests
  if (request.method !== 'GET' || url.protocol === 'chrome-extension:') {
    return;
  }
  
  // Handle different caching strategies based on URL patterns
  if (isStaticResource(url)) {
    // Cache-first strategy for static resources
    event.respondWith(handleStaticResource(request));
  } else if (isAPIRequest(url)) {
    // Network-first strategy for API requests
    event.respondWith(handleAPIRequest(request));
  } else if (isNavigationRequest(request)) {
    // Network-first with offline fallback for navigation
    event.respondWith(handleNavigationRequest(request));
  }
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('🔄 Background sync triggered:', event.tag);
  
  if (event.tag === 'background-transaction-sync') {
    event.waitUntil(syncOfflineTransactions());
  } else if (event.tag === 'background-analytics-sync') {
    event.waitUntil(syncOfflineAnalytics());
  }
});

// Push notification handling
self.addEventListener('push', (event) => {
  console.log('📬 Push notification received');
  
  const options = {
    body: event.data ? event.data.text() : 'New notification from EarnNest',
    icon: '/icons/icon-192.png',
    badge: '/icons/badge-72.png',
    tag: 'earnnest-notification',
    actions: [
      {
        action: 'view',
        title: 'View',
        icon: '/icons/view.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/icons/dismiss.png'
      }
    ],
    data: {
      url: '/notifications'
    }
  };
  
  event.waitUntil(
    self.registration.showNotification('EarnNest', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('🔔 Notification clicked:', event.action);
  
  event.notification.close();
  
  event.waitUntil(
    (async () => {
      const clients = await self.clients.matchAll({ type: 'window' });
      
      // If app is already open, focus it
      for (const client of clients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          await client.focus();
          if (event.action === 'view') {
            client.postMessage({ action: 'navigate', url: '/notifications' });
          }
          return;
        }
      }
      
      // If app is not open, open it
      if (self.clients.openWindow) {
        const targetUrl = event.action === 'view' 
          ? '/notifications' 
          : '/dashboard';
        await self.clients.openWindow(targetUrl);
      }
    })()
  );
});

// Helper Functions

function isStaticResource(url) {
  return url.pathname.startsWith('/static/') ||
         url.pathname.endsWith('.css') ||
         url.pathname.endsWith('.js') ||
         url.pathname.endsWith('.png') ||
         url.pathname.endsWith('.jpg') ||
         url.pathname.endsWith('.svg') ||
         url.pathname.endsWith('.woff2') ||
         STATIC_CACHE_URLS.includes(url.pathname);
}

function isAPIRequest(url) {
  return url.pathname.startsWith('/api/');
}

function isNavigationRequest(request) {
  return request.mode === 'navigate' || 
         (request.method === 'GET' && request.headers.get('accept').includes('text/html'));
}

async function handleStaticResource(request) {
  try {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      console.log('📋 Serving from cache:', request.url);
      return cachedResponse;
    }
    
    // If not in cache, fetch and cache
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      await cache.put(request, networkResponse.clone());
      console.log('💾 Cached new resource:', request.url);
    }
    
    return networkResponse;
    
  } catch (error) {
    console.error('❌ Static resource fetch failed:', error);
    
    // Return offline fallback for critical resources
    if (request.url.includes('main.css')) {
      return new Response('/* Offline mode - styles unavailable */', {
        headers: { 'Content-Type': 'text/css' }
      });
    }
    
    throw error;
  }
}

async function handleAPIRequest(request) {
  const url = new URL(request.url);
  
  try {
    // Network-first for dynamic content
    if (NETWORK_FIRST_URLS.some(pattern => url.pathname.includes(pattern))) {
      return await handleNetworkFirst(request);
    }
    
    // Cache-first for static API responses
    if (API_CACHE_URLS.includes(url.pathname)) {
      return await handleCacheFirst(request);
    }
    
    // Default to network-only for other API requests
    return await fetch(request);
    
  } catch (error) {
    console.error('❌ API request failed:', error);
    
    // Return cached response if available
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      console.log('📋 Serving stale API response from cache:', request.url);
      return cachedResponse;
    }
    
    // Return offline response for critical endpoints
    if (url.pathname.includes('/user/profile')) {
      return new Response(JSON.stringify({
        error: 'Offline',
        message: 'Profile data unavailable offline'
      }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    throw error;
  }
}

async function handleNavigationRequest(request) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    return networkResponse;
    
  } catch (error) {
    console.log('📱 Network unavailable, serving offline page');
    
    // Serve offline page
    const cache = await caches.open(CACHE_NAME);
    const offlineResponse = await cache.match(OFFLINE_URL);
    
    if (offlineResponse) {
      return offlineResponse;
    }
    
    // Fallback offline page
    return new Response(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>EarnNest - Offline</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body { 
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            text-align: center; 
            padding: 2rem; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
          }
          .container { max-width: 400px; }
          h1 { margin-bottom: 1rem; }
          p { margin-bottom: 2rem; opacity: 0.9; }
          button { 
            background: rgba(255,255,255,0.2); 
            border: 1px solid rgba(255,255,255,0.3);
            color: white; 
            padding: 1rem 2rem; 
            border-radius: 8px; 
            cursor: pointer;
            font-size: 1rem;
          }
          button:hover { background: rgba(255,255,255,0.3); }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>📱 You're Offline</h1>
          <p>EarnNest is not available right now. Please check your internet connection and try again.</p>
          <button onclick="window.location.reload()">Try Again</button>
        </div>
      </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

async function handleNetworkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache successful responses
      const cache = await caches.open(CACHE_NAME);
      await cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
    
  } catch (error) {
    // Fall back to cache
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    throw error;
  }
}

async function handleCacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    // Update cache in background
    fetch(request).then(response => {
      if (response.ok) {
        cache.put(request, response);
      }
    }).catch(() => {
      // Ignore background update errors
    });
    
    return cachedResponse;
  }
  
  // If not cached, fetch and cache
  const networkResponse = await fetch(request);
  if (networkResponse.ok) {
    await cache.put(request, networkResponse.clone());
  }
  
  return networkResponse;
}

async function syncOfflineTransactions() {
  try {
    console.log('🔄 Syncing offline transactions...');
    
    // Get offline transactions from IndexedDB
    const offlineTransactions = await getOfflineData('transactions');
    
    for (const transaction of offlineTransactions) {
      try {
        const response = await fetch('/api/transactions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${transaction.token}`
          },
          body: JSON.stringify(transaction.data)
        });
        
        if (response.ok) {
          await removeOfflineData('transactions', transaction.id);
          console.log('✅ Transaction synced:', transaction.id);
        }
        
      } catch (error) {
        console.error('❌ Transaction sync failed:', transaction.id, error);
      }
    }
    
  } catch (error) {
    console.error('❌ Offline sync failed:', error);
  }
}

async function syncOfflineAnalytics() {
  try {
    console.log('📊 Syncing offline analytics...');
    
    // Get offline analytics from IndexedDB
    const offlineAnalytics = await getOfflineData('analytics');
    
    for (const event of offlineAnalytics) {
      try {
        const response = await fetch('/api/analytics/events', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(event.data)
        });
        
        if (response.ok) {
          await removeOfflineData('analytics', event.id);
        }
        
      } catch (error) {
        console.error('❌ Analytics sync failed:', error);
      }
    }
    
  } catch (error) {
    console.error('❌ Analytics sync failed:', error);
  }
}

// Placeholder functions for IndexedDB operations
// These would be implemented with proper IndexedDB logic
async function getOfflineData(store) {
  // Implementation would use IndexedDB to get offline data
  return [];
}

async function removeOfflineData(store, id) {
  // Implementation would remove synced data from IndexedDB
}

console.log('🎯 EarnNest Service Worker loaded successfully');
