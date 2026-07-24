jest.mock('axios', () => ({ create: () => ({ interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } }, get: jest.fn(), post: jest.fn(), defaults: { headers: { common: {} } } }) }));
jest.mock('./offlineQueue', () => ({ cacheData: jest.fn(), getCachedData: jest.fn() }));

import { resolveApiBaseUrl } from './api';

describe('resolveApiBaseUrl', () => {
  it('uses REACT_APP_API_URL as the primary variable', () => {
    expect(resolveApiBaseUrl({ REACT_APP_API_URL: 'https://api.maintrix.test', REACT_APP_BACKEND_URL: 'https://old.test' })).toBe('https://api.maintrix.test');
  });

  it('adds https:// when protocol is missing', () => {
    expect(resolveApiBaseUrl({ REACT_APP_API_URL: 'api.maintrix.test' })).toBe('https://api.maintrix.test');
  });

  it('removes trailing slashes', () => {
    expect(resolveApiBaseUrl({ REACT_APP_API_URL: 'https://api.maintrix.test///' })).toBe('https://api.maintrix.test');
  });

  it('accepts REACT_APP_BACKEND_URL as fallback', () => {
    expect(resolveApiBaseUrl({ REACT_APP_BACKEND_URL: 'backend.maintrix.test/' })).toBe('https://backend.maintrix.test');
  });

  it('does not create undefined URLs', () => {
    expect(resolveApiBaseUrl({ REACT_APP_API_URL: 'undefined' })).toBe('');
    expect(resolveApiBaseUrl({})).toBe('');
  });
});
