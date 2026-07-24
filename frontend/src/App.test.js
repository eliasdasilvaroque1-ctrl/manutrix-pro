import React from 'react';
import { act } from 'react';
import { createRoot } from 'react-dom/client';
import { LoginPage } from './App';
import { AppProviders } from './app/AppProviders';

jest.mock('axios', () => {
  const mockApi = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
    defaults: { headers: { common: {} } },
  };
  global.__MAINTRIX_API_MOCK__ = mockApi;
  return { create: () => mockApi, get: jest.fn(), post: jest.fn() };
});

jest.mock('react-router-dom', () => ({
  useNavigate: () => jest.fn(),
  useLocation: () => ({}),
  useParams: () => ({}),
  useSearchParams: () => [new URLSearchParams(), jest.fn()],
  BrowserRouter: ({ children }) => <>{children}</>,
  Routes: ({ children }) => <>{children}</>,
  Route: () => null,
  Navigate: () => null,
}), { virtual: true });

jest.mock('sonner', () => ({ toast: { error: jest.fn(), success: jest.fn(), info: jest.fn() }, Toaster: () => null }));
jest.mock('./components/ui/sonner', () => ({ Toaster: () => null }));

jest.mock('qrcode.react', () => ({ QRCodeSVG: () => <svg data-testid="qr-code" /> }));

jest.mock('./lib/offlineQueue', () => ({
  queueOperation: jest.fn(),
  getPendingCount: jest.fn(() => Promise.resolve(0)),
  syncPendingOperations: jest.fn(() => Promise.resolve()),
  registerServiceWorker: jest.fn(),
  cacheData: jest.fn(() => Promise.resolve()),
  getCachedData: jest.fn(() => Promise.resolve(null)),
  queuePhoto: jest.fn(() => Promise.resolve()),
}));

const flush = () => act(() => new Promise((resolve) => setTimeout(resolve, 0)));

beforeAll(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
});

beforeEach(() => {
  global.__MAINTRIX_API_MOCK__.get.mockReset();
  global.__MAINTRIX_API_MOCK__.post.mockReset();
  window.history.pushState({}, '', '/login');
  sessionStorage.clear();
  localStorage.clear();
  document.body.innerHTML = '<div id="root"></div>';
});

const renderLogin = async (organizationsPayload) => {
  global.__MAINTRIX_API_MOCK__.get.mockImplementation((url) => {
    if (url === '/public/organizations') return Promise.resolve({ data: organizationsPayload });
    if (url.startsWith('/public/branding/')) return Promise.resolve({ data: {} });
    return Promise.resolve({ data: {} });
  });
  await act(async () => {
    createRoot(document.getElementById('root')).render(<AppProviders><LoginPage /></AppProviders>);
  });
  await flush();
  expect(document.querySelector('[data-testid="login-page"]')).not.toBeNull();
};

describe('LoginPage provider and organizations guards', () => {
  it('renders login fields inside the application providers', async () => {
    await renderLogin([{ id: 'org-1', nome: 'ASTEC' }]);
    await flush();
    expect(document.querySelector('input[type="email"]')).not.toBeNull();
    expect(document.querySelector('input[type="password"]')).not.toBeNull();
    expect(document.body.textContent).toContain('Entrar');
    expect(global.__MAINTRIX_API_MOCK__.get).toHaveBeenCalledWith('/public/organizations');
  });

  it.each([
    ['array', [{ id: 'org-1', nome: 'ASTEC' }]],
    ['object', { detail: 'erro' }],
    ['null', null],
    ['undefined', undefined],
  ])('does not crash when organizations is %s', async (_label, payload) => {
    await renderLogin(payload);
    expect(document.querySelector('input[type="email"]')).not.toBeNull();
    expect(document.querySelector('input[type="password"]')).not.toBeNull();
  });
});
