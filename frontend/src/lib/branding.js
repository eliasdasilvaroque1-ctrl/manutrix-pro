import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, BACKEND_URL } from './api';

const BrandingContext = createContext(null);

const DEFAULT_BRANDING = {
  nome_empresa: 'MAINTRIX',
  nome_sistema: 'MAINTRIX',
  subtitulo: 'Sistema de Gestão de Manutenção Industrial',
  logo_url: null,
  logo_branca_url: null,
  favicon_url: null,
  texto_login: 'Bem-vindo ao sistema de gestão de manutenção',
  rodape: '© 2026 MAINTRIX',
  mostrar_powered_by: false,
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

export const BrandingProvider = ({ children }) => {
  const [branding, setBranding] = useState(DEFAULT_BRANDING);
  const [orgId, setOrgId] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [loaded, setLoaded] = useState(false);

  // Load available organizations (public, no auth)
  const loadOrganizations = useCallback(async () => {
    try {
      const res = await api.get('/public/organizations');
      setOrganizations(res.data || []);
    } catch { setOrganizations([]); }
  }, []);

  // Load branding for a specific org
  const loadBranding = useCallback(async (identifier) => {
    if (!identifier) return;
    try {
      const res = await api.get(`/public/branding/${identifier}`);
      const data = res.data;
      const ident = data.identidade || {};
      const tema = data.tema || {};
      const merged = {
        ...DEFAULT_BRANDING,
        nome_empresa: ident.nome_empresa || ident.nome_sistema || 'MAINTRIX',
        nome_sistema: ident.nome_sistema || 'MAINTRIX',
        subtitulo: ident.subtitulo || '',
        logo_url: ident.logo_url,
        logo_branca_url: ident.logo_branca_url,
        favicon_url: ident.favicon_url,
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
      document.title = merged.nome_empresa || 'MAINTRIX';
    } catch {
      setBranding(DEFAULT_BRANDING);
      applyCSS(DEFAULT_BRANDING);
    }
    setLoaded(true);
  }, []);

  // Load from authenticated user's org
  const loadFromUser = useCallback(async (user) => {
    if (user?.organization_id) {
      setOrgId(user.organization_id);
      await loadBranding(user.organization_id);
    }
  }, [loadBranding]);

  // Select org (from login selector)
  const selectOrg = useCallback((id) => {
    setOrgId(id);
    loadBranding(id);
  }, [loadBranding]);

  // Auto-detect from subdomain
  useEffect(() => {
    const hostname = window.location.hostname;
    const parts = hostname.split('.');
    // Detect subdomain: astec.maintrix.com.br → "astec"
    if (parts.length >= 3 && parts[0] !== 'www' && parts[0] !== 'maintrix') {
      loadBranding(parts[0]);
    } else {
      setLoaded(true);
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
  root.style.setProperty('--brand-primary', b.cor_primaria);
  root.style.setProperty('--brand-secondary', b.cor_secundaria);
  root.style.setProperty('--brand-bg', b.cor_fundo);
  root.style.setProperty('--brand-text', b.cor_texto);
  root.style.setProperty('--brand-accent', b.cor_destaque);
  root.style.setProperty('--brand-menu', b.cor_menu);
  root.style.setProperty('--brand-login', b.cor_login);
  root.style.setProperty('--brand-header', b.cor_header);
}

function applyFavicon(url) {
  if (!url) return;
  const fullUrl = url.startsWith('http') ? url : `${BACKEND_URL}${url}`;
  let link = document.querySelector("link[rel~='icon']");
  if (!link) { link = document.createElement('link'); link.rel = 'icon'; document.head.appendChild(link); }
  link.href = fullUrl;
}
