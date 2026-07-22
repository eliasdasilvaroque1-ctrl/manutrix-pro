import axios from "axios";
import { createContext, useContext } from "react";
import { cacheData, getCachedData } from "./offlineQueue";

/** Extrai mensagem segura de erro de API (string). Nunca retorna objeto/array para JSX. */
export const safeErrorMsg = (err, fallback = 'Erro ao processar operação') => {
  const detail = err?.response?.data?.detail;
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map(d => {
      if (typeof d === 'object' && d !== null) {
        const loc = (d.loc || []).filter(l => !['body','query','path','header'].includes(l));
        const field = loc[loc.length - 1] || '';
        const msg = typeof d.msg === 'string' ? d.msg : String(d.msg || 'valor inválido');
        return field ? `${field}: ${msg}` : msg;
      }
      return String(d);
    }).join('; ') || fallback;
  }
  if (typeof detail === 'object') return typeof detail.msg === 'string' ? detail.msg : fallback;
  return String(detail);
};


export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";
export const API = `${BACKEND_URL}/api`;

// Auth Context
export const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

// Field-critical routes that should be cached for offline reads
const CACHEABLE_PREFIXES = [
  '/ativos', '/sectors', '/plantas', '/users/tecnicos',
  '/planos-inspecao', '/estoque', '/central', '/kpis', '/unidades',
  '/inspection-templates', '/rotas',
];

function isCacheable(url) {
  if (!url) return false;
  return CACHEABLE_PREFIXES.some(p => url.startsWith(p) || url.startsWith(`/api${p}`));
}

function cacheKeyFromUrl(url) {
  // Normalize: strip baseURL prefix if present
  const path = url.replace(/^https?:\/\/[^/]+/, '').replace(/^\/api/, '');
  return `offline:${path}`;
}

// API Client
export const api = axios.create({ baseURL: API });

// Auth token injection
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('maintrix_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Identifica se a URL é de um endpoint público (não exige autenticação)
function isPublicEndpoint(url) {
  if (!url) return false;
  const normalized = url.replace(/^https?:\/\/[^/]+/, '');
  return normalized.startsWith('/api/public/') || normalized.startsWith('/public/');
}

// Response interceptor: auto-cache successful GET responses
api.interceptors.response.use(
  (response) => {
    // Auto-cache GET responses for cacheable routes
    if (response.config?.method === 'get' && isCacheable(response.config.url)) {
      const key = cacheKeyFromUrl(response.config.url);
      cacheData(key, response.data).catch(() => {});
    }
    return response;
  },
  async (error) => {
    // 401 → force logout, MAS não para endpoints públicos
    if (error.response?.status === 401) {
      const requestUrl = error.config?.url || '';
      if (!isPublicEndpoint(requestUrl)) {
        sessionStorage.removeItem('maintrix_token');
        sessionStorage.removeItem('maintrix_user');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }

    // Network error on GET to cacheable route → return cached data
    const config = error.config;
    if (config?.method === 'get' && !error.response && isCacheable(config.url)) {
      const key = cacheKeyFromUrl(config.url);
      try {
        const cached = await getCachedData(key);
        if (cached !== null) {
          return { data: cached, status: 200, _fromCache: true, config };
        }
      } catch {}
    }

    return Promise.reject(error);
  }
);


/**
 * Open an authenticated PDF in a new tab using blob URL.
 * Sends Authorization header via axios, creates a blob URL, opens it.
 */
export async function openAuthenticatedPdf(endpoint, errorToast) {
  const toast = errorToast || ((msg) => alert(msg));
  try {
    const res = await api.get(endpoint, { responseType: 'blob', timeout: 120000 });
    const blob = new Blob([res.data], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const win = window.open(url, '_blank');
    if (win) {
      win.addEventListener('beforeunload', () => URL.revokeObjectURL(url));
    }
    setTimeout(() => URL.revokeObjectURL(url), 120000);
  } catch (err) {
    const status = err?.response?.status;
    if (status === 401) toast('Sua sessão expirou. Entre novamente.');
    else if (status === 403) toast('Você não tem permissão para imprimir este documento.');
    else if (status === 404) toast('Documento não encontrado.');
    else toast('Não foi possível gerar o PDF. Tente novamente.');
  }
}
