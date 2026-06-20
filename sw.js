const CACHE_NAME = 'techsai-cache-v5'; // Bumped version to force cache update
const ASSETS = [
  // ONLY cache static assets that never change based on login state
  '/static/css/styles.css',
  '/static/css/chat.css',
  '/static/js/main.js',
  '/static/js/chat.js',
  '/manifest.json',
  '/icon.png',
  '/icon2.png',
  '/static/favicon.ico',
  '/static/chatgpt.png',
  '/static/deepseek.png',
  '/static/gemini.png',
  '/static/metaai.png',
  '/static/nvidia.png',
  '/static/qwen.png',
  '/static/sarvam.png',
  '/static/Mistral.png'
];

// Install Service Worker and cache core static assets cleanly
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.all(
        ASSETS.map(url => {
          return cache.add(url).catch(err => console.log('Skipped caching:', url, err));
        })
      );
    })
  );
  self.skipWaiting(); // Force activation instantly
});

// Clean up old caches on activation
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch Assets Smartly
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);

  // 1. ABSOLUTE EXCLUSIONS: Skip caching entirely for these routes
  if (
    url.pathname === '/' || 
    url.pathname.startsWith('/login') || 
    url.pathname.startsWith('/signup') || 
    url.pathname.startsWith('/chat') || 
    url.pathname.startsWith('/logout')
  ) {
    return; // Let the browser make a normal network request to Flask
  }

  // 2. Cache-First Strategy ONLY for static images, JS, and CSS files
  e.respondWith(
    caches.match(e.request).then((response) => {
      return response || fetch(e.request);
    })
  );
});
