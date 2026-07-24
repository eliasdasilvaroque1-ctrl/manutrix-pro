import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { api, BACKEND_URL } from './api';

const BrandingContext = createContext(null);

const DEFAULT_BRANDING = {
  nome_empresa: 'CMMS',
  nome_sistema: 'CMMS',
  subtitulo: 'Sistema de Gestão de Manutenção',
  logo_url: null,
  logo_branca_url: null,
  favicon_url: null,
  texto_login: 'Bem-vindo ao sistema de gestão de manutenção',
  rodape: '',
  mostrar_powered_by: true,
  cor_primaria: '#10b981',
  cor_secundaria: '#3b82f6',
  cor_fundo: '#020617',
  cor_texto: '#e2e8f0',
  cor_destaque: '#f59e0b',
  cor_menu: '#0f172a',
  cor_login: '#020617',
  cor_header: '#0f172a',
  organization_id: null,
};

// Hostnames that should NOT trigger subdomain detection
const SKIP_SUBDOMAIN_PATTERNS = [
  'localhost', '127.0.0.1', 'preview', 'emergentagent', 'vercel', 'railway', 'netlify',
];


export function normalizeOrganizations(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.organizations)) return payload.organizations;
  return [];
}

function isCustomerSubdomain(hostname) {
  const parts = hostname.split('.');
  if (parts.length < 3) return false;
  const sub = parts[0].toLowerCase();
  if (sub === 'www' || sub === 'app') return false;
  // Skip if hostname contains known non-customer patterns
  const full = hostname.toLowerCase();
  if (SKIP_SUBDOMAIN_PATTERNS.some(p => full.includes(p))) return false;
  // Only pure alphanumeric subdomains (customer identifiers)
  if (!/^[a-z0-9]+$/.test(sub)) return false;
  return sub;
}

export const BrandingProvider = ({ children }) => {
  const [branding, setBranding] = useState(DEFAULT_BRANDING);
  const [orgId, setOrgId] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const requestVersion = useRef(0);

  // Load available organizations (public, no auth)
  const loadOrganizations = useCallback(async () => {
    try {
      const res = await api.get('/public/organizations');
      setOrganizations(normalizeOrganizations(res.data));
    } catch { setOrganizations([]); }
  }, []);

  // Load branding for a specific org (with request versioning to avoid races)
  const loadBranding = useCallback(async (identifier, priority = 'normal') => {
    if (!identifier) return;
    const version = ++requestVersion.current;
    try {
      const res = await api.get(`/public/branding/${identifier}`);
      // Only apply if this is still the latest request (prevents race conditions)
      if (requestVersion.current !== version) return;
      const data = res.data;
      if (!data.organization_id && priority !== 'high') {
        // Fallback/unknown org — only apply if no real branding is pending
        setLoaded(true);
        return;
      }
      const ident = data.identidade || {};
      const tema = data.tema || {};
      const merged = {
        ...DEFAULT_BRANDING,
        nome_empresa: ident.nome_empresa || ident.nome_sistema || DEFAULT_BRANDING.nome_empresa,
        nome_sistema: ident.nome_sistema || DEFAULT_BRANDING.nome_sistema,
        subtitulo: ident.subtitulo || '',
        logo_url: ident.logo_url,
        logo_branca_url: ident.logo_branca_url,
        favicon_url: ident.favicon_url,
        wallpaper_url: ident.wallpaper_url,
        wallpaper_aplicacao: ident.wallpaper_aplicacao || 'somente_login',
        wallpaper_intensidade: ident.wallpaper_intensidade ?? 10,
        wallpaper_blur: ident.wallpaper_blur || 'sem',
        texto_login: ident.texto_login || DEFAULT_BRANDING.texto_login,
        rodape: ident.rodape || DEFAULT_BRANDING.rodape,
        mostrar_powered_by: ident.mostrar_powered_by !== false,
        cor_primaria: tema.cor_primaria || DEFAULT_BRANDING.cor_primaria,
        cor_secundaria: tema.cor_secundaria || DEFAULT_BRANDING.cor_secundaria,
        cor_fundo: tema.cor_fundo || DEFAULT_BRANDING.cor_fundo,
        cor_texto: tema.cor_texto || DEFAULT_BRANDING.cor_texto,
        cor_destaque: tema.cor_destaque || DEFAULT_BRANDING.cor_destaque,
        cor_menu: tema.cor_menu || DEFAULT_BRANDING.cor_menu,
        cor_login: tema.cor_login || DEFAULT_BRANDING.cor_login,
        cor_header: tema.cor_header || DEFAULT_BRANDING.cor_header,
        organization_id: data.organization_id,
      };
      setBranding(merged);
      applyCSS(merged);
      applyFavicon(merged.favicon_url);
      document.title = merged.nome_empresa || 'CMMS';
    } catch {
      if (requestVersion.current === version) {
        // Only reset to defaults if no subsequent request superseded this one
        setLoaded(true);
      }
    }
    if (requestVersion.current === version) setLoaded(true);
  }, []);

  // Load from authenticated user's org — HIGH priority, always wins over subdomain
  const loadFromUser = useCallback(async (user) => {
    if (user?.organization_id) {
      setOrgId(user.organization_id);
      await loadBranding(user.organization_id, 'high');
    }
  }, [loadBranding]);

  // Select org (from login selector)
  const selectOrg = useCallback((id) => {
    setOrgId(id);
    loadBranding(id, 'high');
  }, [loadBranding]);

  // Auto-detect from subdomain (only on initial mount, only for real customer subdomains)
  useEffect(() => {
    const hostname = window.location.hostname;
    const customerSub = isCustomerSubdomain(hostname);
    
    if (customerSub) {
      loadBranding(customerSub);
    } else {
      // Not a customer subdomain — check if user is already authenticated
      const storedUser = sessionStorage.getItem('maintrix_user');
      if (storedUser) {
        try {
          const user = JSON.parse(storedUser);
          if (user?.organization_id) {
            loadBranding(user.organization_id, 'high');
          } else {
            setLoaded(true);
          }
        } catch { setLoaded(true); }
      } else {
        setLoaded(true);
      }
    }
    loadOrganizations();
  }, [loadBranding, loadOrganizations]);

  return (
    <BrandingContext.Provider value={{
      branding, orgId, organizations, loaded,
      loadBranding, loadFromUser, selectOrg, loadOrganizations,
      setBranding,
    }}>
      {children}
    </BrandingContext.Provider>
  );
};

export const useBranding = () => useContext(BrandingContext);

// Apply CSS variables to :root
function applyCSS(b) {
  const root = document.documentElement;
  // Core brand colors (from org White Label)
  root.style.setProperty('--brand-primary', b.cor_primaria);
  root.style.setProperty('--brand-secondary', b.cor_secundaria);
  root.style.setProperty('--brand-bg', b.cor_fundo);
  root.style.setProperty('--brand-text', b.cor_texto);
  root.style.setProperty('--brand-accent', b.cor_destaque);
  root.style.setProperty('--brand-menu', b.cor_menu);
  root.style.setProperty('--brand-login', b.cor_login);
  root.style.setProperty('--brand-header', b.cor_header);

  // Theme Engine — Industrial Dark (only theme for RC1)
  // Future themes (Industrial Light, Executive, Mining) will override these values
  const theme = THEMES['industrial_dark'];
  root.style.setProperty('--brand-surface', theme.surface);
  root.style.setProperty('--brand-surface-hover', theme.surfaceHover);
  root.style.setProperty('--brand-border', theme.border);
  root.style.setProperty('--brand-text-primary', theme.textPrimary);
  root.style.setProperty('--brand-text-secondary', theme.textSecondary);
}

// Theme Engine — Pre-defined themes with explicit values (no calculations)
const THEMES = {
  industrial_dark: {
    surface: '#0f172a',
    surfaceHover: '#1e293b',
    border: '#1e293b',
    textPrimary: '#e2e8f0',
    textSecondary: '#94a3b8',
  },
  // Future:
  // industrial_light: { surface: '#ffffff', surfaceHover: '#f1f5f9', border: '#e2e8f0', textPrimary: '#111827', textSecondary: '#6b7280' },
  // executive: { surface: '#1a1a2e', surfaceHover: '#25253d', border: '#2d2d4a', textPrimary: '#e0e0e0', textSecondary: '#9e9eb8' },
  // mining: { surface: '#1c1917', surfaceHover: '#292524', border: '#44403c', textPrimary: '#f5f5f4', textSecondary: '#a8a29e' },
};

function applyFavicon(url) {
  if (!url) return;
  const fullUrl = url.startsWith('http') ? url : `${BACKEND_URL}${url}`;
  let link = document.querySelector("link[rel~='icon']");
  if (!link) { link = document.createElement('link'); link.rel = 'icon'; document.head.appendChild(link); }
  link.href = fullUrl;
}
