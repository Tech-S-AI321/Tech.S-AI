const CACHE_NAME = 'pwa-cache-v1';
const ASSETS = [
  '/',
  '/templates/home.html',
  '/templates/login.html',
  '/templates/signup.html',
  '/templates/chat.html',
  '/css/styles.css',
  '/js/main.js',
  '/manifest.json',
  '/static/icon.png',
  '/static/favicon.ico',
  '/static/chatgpt.png',
  '/static/deepseek.png',
  '/static/gemini.png',
  '/static/metaai.png',
  '/static/nvidia.png',
  '/static/qwen.png',
  '/static/sarvam.png',
  '/static/Zai.png'
];

// Install Service Worker and cache assets
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
});

// Fetch assets from cache if offline
self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => {
      return response || fetch(e.request);
    })
  );
});