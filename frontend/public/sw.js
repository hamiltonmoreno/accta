// v4: cache-first passa a aplicar-se SÓ a /static/* (assets com hash de
// conteúdo, onde `immutable` é seguro e a mudança troca o nome do ficheiro).
// Ícones de nome fixo na raiz (/logo192.png, /favicon.ico, …) deixam de ser
// pinados pelo SW e passam a respeitar o Cache-Control HTTP (revalidável) — uma
// troca de logo propaga-se sem novo deploy do SW. O bump purga a cache v3.
const CACHE_NAME = 'accta-wallet-v5';

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

  // Cache-first SÓ para /static/* (assets com hash de conteúdo, imutáveis por
  // nome). Ícones/manifest de raiz NÃO entram aqui — vão à rede e respeitam o
  // Cache-Control HTTP, para que uma troca de logo propague sem novo SW.
  if (url.origin === self.location.origin && url.pathname.startsWith('/static/')) {
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

// Web Push: o backend dispara um payload JSON { title, body, url }. Mostramos a
// notificação na bandeja do SO (funciona com a app fechada no Android/desktop e
// no iOS 16.4+ quando o PWA está na Tela de Início).
self.addEventListener('push', (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = { body: event.data && event.data.text ? event.data.text() : '' };
  }
  const title = data.title || 'ACCTA';
  const options = {
    body: data.body || '',
    icon: '/logo192.png',
    badge: '/logo192.png',
    data: { url: data.url || '/' },
  };
  // Só agrupa (substitui na bandeja) se o backend mandar um `tag` explícito.
  // Sem tag, cada notificação aparece como entrada separada — senão um comunicado
  // seguido de um evento colapsavam num só e o utilizador perdia o primeiro.
  if (data.tag) options.tag = data.tag;
  event.waitUntil(self.registration.showNotification(title, options));
});

// Clique na notificação: foca uma janela já aberta da app (navegando para o
// link) ou abre uma nova.
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      for (const client of windowClients) {
        if ('focus' in client) {
          client.navigate(targetUrl).catch(() => {});
          return client.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(targetUrl);
      return undefined;
    })
  );
});
