const CACHE_NAME = 'maintrix-v4';
const API_CACHE = 'maintrix-api-v4';

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
];

// Field-critical API routes to cache for offline reads
const API_PREFIXES = [
  '/api/sectors',
  '/api/ativos',
  '/api/ordens-servico',
  '/api/inspecoes',
  '/api/planos-inspecao',
  '/api/inspection-templates',
  '/api/kpis',
  '/api/dashboard/',
  '/api/users',
  '/api/estoque',
  '/api/central',
  '/api/plantas',
  '/api/unidades',
  '/api/rotas',
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

// Activate: clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== CACHE_NAME && k !== API_CACHE)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// HOTFIX P0: Rotas públicas que NÃO devem ser cacheadas pelo Service Worker
const PUBLIC_ROUTES_NO_CACHE = ['/equipamento/', '/portal/'];

// Fetch strategy: network-first with cache fallback
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Only cache GET requests
  if (event.request.method !== 'GET') return;

  // HOTFIX P0: Rotas públicas (QR Code) — network-only para navigation requests
  // Garante que o index.html mais recente é sempre servido do servidor
  if (event.request.mode === 'navigate' &&
      PUBLIC_ROUTES_NO_CACHE.some((p) => url.pathname.startsWith(p))) {
    event.respondWith(
      fetch(event.request).catch(() => {
        // Fallback mínimo se totalmente offline — retorna o cache como última opção
        return caches.match(event.request).then((cached) => {
          return cached || new Response(
            '<html><body style="background:#0f172a;color:#94a3b8;display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif"><div style="text-align:center"><h1 style="color:#10b981">MAINTRIX</h1><p>Sem conexão. Verifique sua internet e tente novamente.</p></div></body></html>',
            { headers: { 'Content-Type': 'text/html' } }
          );
        });
      })
    );
    return;
  }

  // API requests: network-first, cache on success, fallback to cache
  if (API_PREFIXES.some((p) => url.pathname.startsWith(p))) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(API_CACHE).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Static/app assets: network-first with cache fallback
  if (url.origin === self.location.origin) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response.ok) {
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
