const CACHE_NAME = 'techsai-cache-v2';
const ASSETS = [
  '/',                     // Home page route
  '/login',                // Your Login page web route (replaces /templates/login.html)
  '/signup',               // Your Signup page web route (replaces /templates/signup.html)
  '/chat/',                // Your Main chat application route
  '/static/css/styles.css',
  '/static/js/main.js',
  '/manifest.json',
  '/icon.png',
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

// Install Service Worker and cache assets cleanly
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Safely map and add assets so a single missing file won't break the whole app
      return Promise.all(
        ASSETS.map(url => {
          return cache.add(url).catch(err => console.log('Skipped caching:', url, err));
        })
      );
    })
  );
});

// Fetch assets from cache, fallback to network
self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => {
      return response || fetch(e.request);
    })
  );
});
