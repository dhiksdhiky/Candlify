/**
 * Candlify v2 Service Worker
 * Strategy: Network-First with Cache Fallback (Sesuai Panduan pwa_config.md)
 */

const CACHE_NAME = 'candlify-v2-2.5.0';

const urlsToCache = [
  './',
  './index.html',
  './manifest.json',
  './favicon.ico',
  './css/style.css',
  './js/chart.js',
  './js/klinecharts.min.js',
  './js/marked.min.js',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

// Install Event: Simpan aset statis awal ke cache
self.addEventListener('install', event => {
  self.skipWaiting(); // Memaksa SW baru untuk langsung aktif
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

// Activate Event: Bersihkan cache versi lama
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
    ))
  );
  self.clients.claim(); // Langsung kontrol semua tab yang terbuka
});

// Fetch Event: Hanya tangani HTTP GET
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Jangan simpan API calls di Service Worker (biarkan backend in-memory TTL & CDN yang handle)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(JSON.stringify({
          success: false,
          error: 'Anda sedang offline dan data pasar belum tersedia di cache.'
        }), {
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
    return;
  }

  // Network-First untuk file statis dengan Fallback ke Cache
  event.respondWith(
    fetch(event.request)
      .then(response => {
        if (response && response.status === 200 && response.type === 'basic') {
          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseToCache));
        }
        return response;
      })
      .catch(() => {
        return caches.match(event.request).then(cachedResponse => {
          if (cachedResponse) return cachedResponse;
          // Fallback navigasi ke index.html jika offline
          if (event.request.mode === 'navigate') {
            return caches.match('./index.html');
          }
        });
      })
  );
});
