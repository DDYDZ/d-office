// D事务所 Service Worker — Offline PWA Support
// Version: v3 (force refresh to fix stale cache issues)
const CACHE_NAME = 'd-office-v3';
const ASSETS = [
  '/',
  '/index.html',
  '/manifest.json'
];

// Install — cache all assets
self.addEventListener('install', (event) => {
  console.log('📦 D事务所 SW v3 — installing...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    }).then(() => {
      console.log('📦 D事务所 SW v3 — installed, skipping waiting');
      return self.skipWaiting();
    })
  );
});

// Activate — clean ALL old caches aggressively
self.addEventListener('activate', (event) => {
  console.log('📦 D事务所 SW v3 — activating...');
  event.waitUntil(
    caches.keys().then((keys) => {
      console.log('📦 Found caches:', keys);
      return Promise.all(
        keys.map(key => {
          console.log('📦 Deleting old cache:', key);
          return caches.delete(key);
        })
      );
    }).then(() => {
      console.log('📦 D事务所 SW v3 — activated, claiming clients');
      return self.clients.claim();
    })
  );
});

// Fetch — network first, fallback to cache
self.addEventListener('fetch', (event) => {
  // Only handle GET requests for same-origin
  if (event.request.method !== 'GET') return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Cache fresh responses
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, clone);
        });
        return response;
      })
      .catch(() => {
        return caches.match(event.request).then((cached) => {
          return cached || new Response('Offline — please connect to internet to load.', {
            status: 503,
            headers: { 'Content-Type': 'text/plain; charset=utf-8' }
          });
        });
      })
  );
});
