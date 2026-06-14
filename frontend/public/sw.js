// v3: purga a cache v2, que podia conter o fallback SPA (index.html) gravado no
// lugar de assets que davam 404 antes de existirem (ex.: /logo192.png servido
// como text/html). O bump força o activate a apagar a cache envenenada.
const CACHE_NAME = 'accta-wallet-v3';

const STATIC_ASSETS = [
  '/carteira',
  '/manifest.json',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).catch(() => {
      // Silently fail if caching fails during install
    })
  );
  self.skipWaiting();
});

// Activate event - clean old caches, including older wallet data caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Fetch event - serve from cache, fall back to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle GET requests
  if (request.method !== 'GET') return;

  // Never cache authenticated API responses or personal data.
  if (url.origin === self.location.origin && url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(request, { cache: 'no-store' }));
    return;
  }

  // For navigation requests (HTML pages), use network-first
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => {
        return caches.match('/carteira') || caches.match('/');
      })
    );
    return;
  }

  // For same-origin static assets, use cache-first
  if (url.origin === self.location.origin && url.pathname.match(/\.(js|css|png|jpg|jpeg|svg|ico|woff2?)$/)) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) return cachedResponse;
        return fetch(request).then((response) => {
          // Nunca cachear o fallback SPA (index.html) servido para um asset em
          // falta — era o que envenenava a cache (ex.: /logo192.png gravado como
          // text/html). Só cacheamos respostas reais do tipo esperado.
          const contentType = response && response.headers.get('content-type');
          if (!response || !response.ok || (contentType && contentType.includes('text/html'))) {
            return response;
          }
          const clonedResponse = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, clonedResponse);
          });
          return response;
        });
      })
    );
    return;
  }
});
