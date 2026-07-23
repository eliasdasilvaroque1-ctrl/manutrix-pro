const CACHE_NAME = 'maintrix-v5';

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
];

// Install: cache app shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {});
    })
  );
  self.skipWaiting();
});

// Activate: clean all old Maintrix caches, including API caches from previous versions
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== CACHE_NAME)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// HOTFIX P0: Rotas públicas que NÃO devem ser cacheadas pelo Service Worker
const PUBLIC_ROUTES_NO_CACHE = ['/equipamento/', '/portal/'];
const STATIC_FILE_PATTERN = /\.(?:html|js|css|png|jpg|jpeg|svg|webp|ico|json|woff|woff2|ttf|map)$/i;

const offlineHtml = () => new Response(
  '<html><body style="background:#0f172a;color:#94a3b8;display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif"><div style="text-align:center"><h1 style="color:#10b981">MAINTRIX</h1><p>Sem conexão. Verifique sua internet e tente novamente.</p></div></body></html>',
  { headers: { 'Content-Type': 'text/html' } }
);

const isFetchOrXhr = (request) => {
  const requestedWith = request.headers.get('x-requested-with') || '';
  const accept = request.headers.get('accept') || '';
  return request.destination === '' && (
    requestedWith.toLowerCase() === 'xmlhttprequest' ||
    accept.includes('application/json') ||
    request.mode === 'cors'
  );
};

const isDynamicSameOriginEndpoint = (request, url) => (
  url.origin === self.location.origin &&
  request.destination === '' &&
  !STATIC_FILE_PATTERN.test(url.pathname)
);

const shouldBypassCache = (request, url) => (
  url.pathname.startsWith('/api/') ||
  url.pathname.includes('/organizations') ||
  isFetchOrXhr(request) ||
  isDynamicSameOriginEndpoint(request, url)
);

const isCacheableResponse = (response) => {
  if (!response || !response.ok || response.status >= 400) return false;
  return true;
};

// Fetch strategy: API/dynamic requests are network-only; static/app assets are network-first with cache fallback
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Only cache GET requests
  if (event.request.method !== 'GET') return;

  if (shouldBypassCache(event.request, url)) {
    event.respondWith(fetch(event.request));
    return;
  }

  // HOTFIX P0: Rotas públicas (QR Code) — network-only para navigation requests
  // Garante que o index.html mais recente é sempre servido do servidor
  if (event.request.mode === 'navigate' &&
      PUBLIC_ROUTES_NO_CACHE.some((p) => url.pathname.startsWith(p))) {
    event.respondWith(fetch(event.request).catch(() => offlineHtml()));
    return;
  }

  // Static/app assets: network-first with cache fallback
  if (url.origin === self.location.origin) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (isCacheableResponse(response)) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }
});

// Message handler for cache control
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
