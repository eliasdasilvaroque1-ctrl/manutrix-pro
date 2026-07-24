import fs from 'fs';
import path from 'path';
import vm from 'vm';

const makeHeaders = (headers = {}) => ({
  get: (name) => headers[name.toLowerCase()] || headers[name] || null,
});

const makeRequest = (url, options = {}) => ({
  url,
  method: options.method || 'GET',
  mode: options.mode || 'same-origin',
  destination: options.destination || '',
  headers: makeHeaders(options.headers),
});

const makeResponse = (status = 200, headers = {}) => ({
  ok: status >= 200 && status < 300,
  status,
  headers: makeHeaders(headers),
  clone: jest.fn(function clone() { return this; }),
});

const loadServiceWorker = () => {
  const source = fs.readFileSync(path.join(__dirname, '..', 'public', 'service-worker.js'), 'utf8');
  const listeners = {};
  const cachePut = jest.fn();
  const cacheAddAll = jest.fn(() => Promise.resolve());
  const cacheDelete = jest.fn(() => Promise.resolve(true));
  const cacheMatch = jest.fn(() => Promise.resolve(undefined));
  const cachesMock = {
    open: jest.fn(() => Promise.resolve({ addAll: cacheAddAll, put: cachePut })),
    keys: jest.fn(() => Promise.resolve(['maintrix-v4', 'maintrix-api-v4', 'maintrix-v5', 'maintrix-v6'])),
    delete: cacheDelete,
    match: cacheMatch,
  };
  const fetchMock = jest.fn();
  const selfMock = {
    location: { origin: 'https://maintrix.test' },
    clients: { claim: jest.fn() },
    skipWaiting: jest.fn(),
    addEventListener: (type, listener) => { listeners[type] = listener; },
  };

  vm.runInNewContext(source, {
    self: selfMock,
    caches: cachesMock,
    fetch: fetchMock,
    URL,
    Response,
    Promise,
  });

  return { listeners, fetchMock, cachePut, cacheDelete, cacheMatch, cachesMock };
};

const dispatchFetch = async (sw, request, response) => {
  sw.fetchMock.mockResolvedValue(response);
  let responsePromise;
  sw.listeners.fetch({
    request,
    respondWith: (promise) => { responsePromise = promise; },
  });
  expect(responsePromise).toBeDefined();
  await responsePromise;
  await Promise.resolve();
};

describe('service-worker cache bypass rules', () => {
  it('does not cache /api/public/organizations', async () => {
    const sw = loadServiceWorker();
    await dispatchFetch(
      sw,
      makeRequest('https://maintrix.test/api/public/organizations', { mode: 'cors', headers: { accept: 'application/json' } }),
      makeResponse(200, { 'content-type': 'application/json' })
    );
    expect(sw.cachePut).not.toHaveBeenCalled();
    expect(sw.cacheMatch).not.toHaveBeenCalled();
  });

  it('does not cache same-origin /organizations endpoints', async () => {
    const sw = loadServiceWorker();
    await dispatchFetch(
      sw,
      makeRequest('https://maintrix.test/organizations'),
      makeResponse(200, { 'content-type': 'application/json' })
    );
    expect(sw.cachePut).not.toHaveBeenCalled();
    expect(sw.cacheMatch).not.toHaveBeenCalled();
  });

  it('does not cache 404 responses', async () => {
    const sw = loadServiceWorker();
    await dispatchFetch(
      sw,
      makeRequest('https://maintrix.test/icon-192.png', { destination: 'image' }),
      makeResponse(404, { 'content-type': 'image/png' })
    );
    expect(sw.cachePut).not.toHaveBeenCalled();
  });

  it('does not cache 500 responses', async () => {
    const sw = loadServiceWorker();
    await dispatchFetch(
      sw,
      makeRequest('https://maintrix.test/icon-512.png', { destination: 'image' }),
      makeResponse(500, { 'content-type': 'image/png' })
    );
    expect(sw.cachePut).not.toHaveBeenCalled();
  });

  it('removes old caches during activate', async () => {
    const sw = loadServiceWorker();
    let waitPromise;
    sw.listeners.activate({ waitUntil: (promise) => { waitPromise = promise; } });
    await waitPromise;
    expect(sw.cacheDelete).toHaveBeenCalledWith('maintrix-v4');
    expect(sw.cacheDelete).toHaveBeenCalledWith('maintrix-api-v4');
    expect(sw.cacheDelete).toHaveBeenCalledWith('maintrix-v5');
    expect(sw.cacheDelete).not.toHaveBeenCalledWith('maintrix-v6');
  });
});
