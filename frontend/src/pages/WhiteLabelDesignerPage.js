import { useState, useEffect, useRef } from "react";
import { Palette, Eye, Upload, CheckCircle, RefreshCw, Sparkles, Lock, Building2, Menu, Home, Box, BarChart3, Layers, Settings, LogOut, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { api, useAuth, BACKEND_URL } from "@/lib/api";
import { normalizeError, ROLE_LABELS } from "@/lib/constants";
import { Loading, PageContainer, PageHeader, FormInput } from "@/components/shared";

const PRESET_THEMES = [
  { id: 'industrial_dark', name: 'Industrial Dark', colors: { cor_primaria: '#10b981', cor_secundaria: '#3b82f6', cor_fundo: '#020617', cor_texto: '#e2e8f0', cor_destaque: '#f59e0b', cor_menu: '#0f172a', cor_login: '#020617', cor_header: '#0f172a' } },
  { id: 'midnight_steel', name: 'Midnight Steel', colors: { cor_primaria: '#6366f1', cor_secundaria: '#ec4899', cor_fundo: '#09090b', cor_texto: '#e4e4e7', cor_destaque: '#f59e0b', cor_menu: '#18181b', cor_login: '#09090b', cor_header: '#18181b' } },
  { id: 'corp_blue', name: 'Corporativo Azul', colors: { cor_primaria: '#2563eb', cor_secundaria: '#7c3aed', cor_fundo: '#0f172a', cor_texto: '#e2e8f0', cor_destaque: '#f59e0b', cor_menu: '#1e3a5f', cor_login: '#0c1524', cor_header: '#1e3a5f' } },
  { id: 'corp_green', name: 'Corporativo Verde', colors: { cor_primaria: '#16a34a', cor_secundaria: '#0891b2', cor_fundo: '#052e16', cor_texto: '#dcfce7', cor_destaque: '#facc15', cor_menu: '#14532d', cor_login: '#022c22', cor_header: '#14532d' } },
  { id: 'custom', name: 'Personalizado', colors: null },
];

const ColorField = ({ label, value, onChange }) => (
  <div className="flex items-center gap-3">
    <div className="relative">
      <input type="color" value={value || '#000000'} onChange={e => onChange(e.target.value)}
        className="w-10 h-10 rounded-lg border border-slate-700 cursor-pointer bg-transparent p-0.5" />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-xs text-slate-400">{label}</p>
      <input type="text" value={value || ''} onChange={e => onChange(e.target.value)}
        className="input-industrial w-full px-2 text-xs h-8 font-mono" placeholder="#000000" />
    </div>
  </div>
);

const AssetUploader = ({ label, currentUrl, orgId, assetType, onUploaded }) => {
  const [uploading, setUploading] = useState(false);
  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await api.post(`/master/organizations/${orgId}/upload/${assetType}`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      onUploaded(res.data.url);
      toast.success(`${label} enviado!`);
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setUploading(false); }
  };
  return (
    <div className="space-y-2">
      <p className="text-xs text-slate-400 font-medium">{label}</p>
      <div className="flex items-center gap-3">
        {currentUrl ? (
          <img src={currentUrl.startsWith('http') ? currentUrl : `${BACKEND_URL}${currentUrl}`} alt={label}
            className="w-16 h-16 rounded-lg object-contain bg-slate-800 border border-slate-700 p-1" />
        ) : (
          <div className="w-16 h-16 rounded-lg border-2 border-dashed border-slate-700 flex items-center justify-center">
            <Image size={20} className="text-slate-600" />
          </div>
        )}
        <label className="flex-1">
          <span className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg cursor-pointer inline-flex items-center gap-2 transition-colors">
            <Upload size={14} /> {uploading ? 'Enviando...' : 'Upload'}
          </span>
          <input type="file" accept="image/*" onChange={handleFile} className="hidden" disabled={uploading} />
        </label>
      </div>
    </div>
  );
};

// Mini preview components
const PreviewLogin = ({ cfg }) => {
  const t = cfg.tema || {};
  const i = cfg.identidade || {};
  const wpUrl = i.wallpaper_url ? (i.wallpaper_url.startsWith('http') ? i.wallpaper_url : `${BACKEND_URL}${i.wallpaper_url}`) : null;
  return (
    <div className="rounded-lg overflow-hidden border border-slate-700 relative" style={{ backgroundColor: t.cor_login || '#020617', minHeight: 200 }}>
      {wpUrl && (
        <div className="absolute inset-0 opacity-20 pointer-events-none" style={{ backgroundImage: `url(${wpUrl})`, backgroundSize: 'cover' }} />
      )}
      <div className="p-4 text-center relative">
        {i.logo_url ? (
          <img src={i.logo_url?.startsWith('http') ? i.logo_url : `${BACKEND_URL}${i.logo_url}`} alt="" className="h-8 mx-auto mb-2 object-contain" />
        ) : (
          <div className="w-8 h-8 rounded-lg mx-auto mb-2 flex items-center justify-center" style={{ backgroundColor: `${t.cor_primaria || '#10b981'}20` }}>
            <Cog size={16} style={{ color: t.cor_primaria || '#10b981' }} />
          </div>
        )}
        <p className="text-sm font-bold" style={{ color: t.cor_primaria || '#10b981' }}>{i.nome_empresa || 'Empresa'}</p>
        <p className="text-[9px] text-slate-500 mt-0.5">{i.texto_login || 'Bem-vindo'}</p>
        <div className="mt-3 space-y-1.5">
          <div className="h-6 rounded bg-slate-800/60 border border-slate-700" />
          <div className="h-6 rounded bg-slate-800/60 border border-slate-700" />
          <div className="h-6 rounded text-[9px] text-white flex items-center justify-center font-semibold" style={{ backgroundColor: t.cor_primaria || '#10b981' }}>Entrar</div>
        </div>
        {i.mostrar_powered_by && <p className="text-[7px] text-slate-600 mt-2">Powered by MAINTRIX</p>}
      </div>
    </div>
  );
};

const PreviewSidebar = ({ cfg }) => {
  const t = cfg.tema || {};
  const i = cfg.identidade || {};
  const items = ['Central', 'Dashboard', 'Ativos', 'OS', 'Inspeções'];
  return (
    <div className="rounded-lg overflow-hidden border border-slate-700 h-full" style={{ backgroundColor: t.cor_menu || '#0f172a', minHeight: 200 }}>
      <div className="p-3 border-b border-slate-800/50">
        {i.logo_branca_url || i.logo_url ? (
          <img src={(i.logo_branca_url || i.logo_url)?.startsWith('http') ? (i.logo_branca_url || i.logo_url) : `${BACKEND_URL}${i.logo_branca_url || i.logo_url}`} alt="" className="h-5 object-contain mb-1" />
        ) : null}
        <p className="text-xs font-bold truncate" style={{ color: t.cor_primaria || '#10b981' }}>{i.nome_empresa || 'Empresa'}</p>
        <p className="text-[7px] text-slate-500">{i.subtitulo || ''}</p>
      </div>
      <div className="p-2 space-y-0.5">
        {items.map((item, idx) => (
          <div key={item} className="flex items-center gap-2 px-2 py-1.5 rounded text-[9px]"
            style={idx === 0 ? { backgroundColor: `${t.cor_primaria || '#10b981'}15`, color: t.cor_primaria || '#10b981', borderLeft: `2px solid ${t.cor_primaria || '#10b981'}` } : { color: '#94a3b8', borderLeft: '2px solid transparent' }}>
            <div className="w-3 h-3 rounded bg-current opacity-40" />
            {item}
          </div>
        ))}
      </div>
    </div>
  );
};

const PreviewCard = ({ cfg }) => {
  const t = cfg.tema || {};
  return (
    <div className="rounded-lg border border-slate-700 p-3" style={{ backgroundColor: t.cor_fundo || '#020617' }}>
      <div className="flex items-center gap-2 mb-2">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${t.cor_primaria || '#10b981'}20` }}>
          <Box size={14} style={{ color: t.cor_primaria || '#10b981' }} />
        </div>
        <div>
          <p className="text-xs font-semibold" style={{ color: t.cor_texto || '#e2e8f0' }}>Motor Britador</p>
          <p className="text-[9px] font-mono" style={{ color: t.cor_primaria || '#10b981' }}>MT-02</p>
        </div>
      </div>
      <div className="flex gap-1">
        <span className="text-[8px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">Operacional</span>
        <span className="text-[8px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">2 OS</span>
      </div>
    </div>
  );
};

const WhiteLabelDesignerPage = () => {
  const [orgs, setOrgs] = useState([]);
  const [selectedOrgId, setSelectedOrgId] = useState(null);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeSection, setActiveSection] = useState('identidade');
  const [showNewOrg, setShowNewOrg] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const { user } = useAuth();
  const configReqVer = useRef(0);

  const loadOrgs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/master/organizations');
      setOrgs(res.data);
      if (res.data.length > 0) {
        setSelectedOrgId(prev => prev || res.data[0].id);
      }
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadOrgs(); }, [loadOrgs]);

  useEffect(() => {
    if (!selectedOrgId) { setConfig(null); return; }
    const ver = ++configReqVer.current;
    (async () => {
      try {
        const res = await api.get(`/master/organizations/${selectedOrgId}/config`);
        if (configReqVer.current === ver) setConfig(res.data);
      } catch (err) { if (configReqVer.current === ver) toast.error(normalizeError(err)); }
    })();
  }, [selectedOrgId]);

  const updateConfig = (path, value) => {
    setConfig(prev => {
      const clone = JSON.parse(JSON.stringify(prev));
      const parts = path.split('.');
      let obj = clone;
      for (let i = 0; i < parts.length - 1; i++) {
        if (!obj[parts[i]]) obj[parts[i]] = {};
        obj = obj[parts[i]];
      }
      obj[parts[parts.length - 1]] = value;
      return clone;
    });
  };

  const applyTheme = (theme) => {
    if (!theme.colors) return;
    Object.entries(theme.colors).forEach(([key, val]) => {
      updateConfig(`tema.${key}`, val);
    });
    toast.success(`Tema "${theme.name}" aplicado!`);
  };

  const handleSave = async () => {
    if (!config || !selectedOrgId) return;
    setSaving(true);
    try {
      const payload = {
        ...config.identidade,
        ...config.tema,
        subdominio: config.dominio?.subdominio || '',
        dominio_customizado: config.dominio?.dominio_customizado || '',
      };
      await api.put(`/master/organizations/${selectedOrgId}/config`, payload);
      toast.success('Configuração salva com sucesso!');
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setSaving(false); }
  };

  const handleCreateOrg = async () => {
    if (!newOrgName.trim()) { toast.error('Nome é obrigatório'); return; }
    try {
      const res = await api.post('/master/organizations', { nome: newOrgName.trim() });
      toast.success(`Empresa "${newOrgName}" criada!`);
      setNewOrgName('');
      setShowNewOrg(false);
      await loadOrgs();
      setSelectedOrgId(res.data.id);
    } catch (err) { toast.error(normalizeError(err)); }
  };

  const handleAssetUploaded = (field, url) => {
    updateConfig(`identidade.${field}`, url);
  };

  if (loading) return <Loading rows={6} />;

  const sections = [
    { id: 'identidade', label: 'Identidade', icon: Building2 },
    { id: 'cores', label: 'Cores', icon: Palette },
    { id: 'login', label: 'Login', icon: Lock },
    { id: 'dominios', label: 'Domínios', icon: MapPin },
    { id: 'temas', label: 'Temas', icon: Sparkles },
  ];

  return (
    <div className="space-y-6 animate-fadeInUp" data-testid="white-label-designer">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-primary" data-testid="wl-page-title">Designer de Marca</h1>
          <p className="text-sm text-slate-500">Configure a identidade visual de cada empresa</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setShowNewOrg(true)} className="btn-primary flex items-center gap-2 text-sm" data-testid="wl-new-org-btn">
            <Plus size={16} /> Nova Empresa
          </button>
          <button onClick={handleSave} disabled={saving || !config} className="btn-primary flex items-center gap-2 text-sm" data-testid="wl-save-btn">
            <Save size={16} /> {saving ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </div>

      {/* New Org Modal */}
      {showNewOrg && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowNewOrg(false)}>
          <div className="glass-card p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()} data-testid="wl-new-org-modal">
            <h2 className="text-lg font-bold text-slate-100">Nova Empresa</h2>
            <FormInput label="Nome da Empresa">
              <input value={newOrgName} onChange={e => setNewOrgName(e.target.value)} className="input-industrial w-full px-4"
                placeholder="Ex: ASTEC, Vale, Gerdau..." data-testid="wl-new-org-name" autoFocus />
            </FormInput>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowNewOrg(false)} className="btn-secondary text-sm">Cancelar</button>
              <button onClick={handleCreateOrg} className="btn-primary text-sm" data-testid="wl-new-org-confirm">Criar Empresa</button>
            </div>
          </div>
        </div>
      )}

      {/* Org Selector */}
      <div className="flex items-center gap-3 overflow-x-auto pb-2 custom-scrollbar" data-testid="wl-org-selector">
        {orgs.map(org => (
          <button key={org.id} onClick={() => setSelectedOrgId(org.id)}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-all whitespace-nowrap ${
              selectedOrgId === org.id ? 'border-brand bg-brand-10' : 'border-slate-800 bg-slate-900/50 hover:border-slate-600'
            }`} data-testid={`wl-org-${org.id}`}>
            {org.config?.identidade?.logo_url ? (
              <img src={org.config.identidade.logo_url.startsWith('http') ? org.config.identidade.logo_url : `${BACKEND_URL}${org.config.identidade.logo_url}`}
                alt="" className="w-8 h-8 rounded-lg object-contain bg-slate-800 p-0.5" />
            ) : (
              <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold"
                style={{ backgroundColor: org.config?.tema?.cor_primaria || '#10b981' }}>
                {(org.nome || 'E').substring(0, 2).toUpperCase()}
              </div>
            )}
            <div className="text-left">
              <p className={`text-sm font-semibold ${selectedOrgId === org.id ? 'text-brand' : 'text-slate-200'}`}>{org.nome}</p>
              <p className="text-[10px] text-slate-500">{org.config?.dominio?.subdominio ? `${org.config.dominio.subdominio}.maintrix.com.br` : 'Sem subdomínio'}</p>
            </div>
          </button>
        ))}
      </div>

      {config && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Config Panel */}
          <div className="lg:col-span-2 space-y-4">
            {/* Section Tabs */}
            <div className="flex gap-1 overflow-x-auto pb-1" data-testid="wl-section-tabs">
              {sections.map(s => {
                const Icon = s.icon;
                return (
                  <button key={s.id} onClick={() => setActiveSection(s.id)}
                    className={`px-4 py-2 rounded-lg text-xs font-medium flex items-center gap-2 whitespace-nowrap transition-all ${
                      activeSection === s.id ? 'bg-brand-20 text-brand border border-brand-30' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                    }`} data-testid={`wl-tab-${s.id}`}>
                    <Icon size={14} /> {s.label}
                  </button>
                );
              })}
            </div>

            {/* Identity Section */}
            {activeSection === 'identidade' && (
              <div className="glass-card p-6 space-y-5" data-testid="wl-section-identidade">
                <h3 className="section-title"><Building2 size={16} /> Identidade</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormInput label="Nome da Empresa">
                    <input value={config.identidade?.nome_empresa || ''} onChange={e => updateConfig('identidade.nome_empresa', e.target.value)}
                      className="input-industrial w-full px-4" data-testid="wl-nome-empresa" />
                  </FormInput>
                  <FormInput label="Nome de Exibição">
                    <input value={config.identidade?.nome_sistema || ''} onChange={e => updateConfig('identidade.nome_sistema', e.target.value)}
                      className="input-industrial w-full px-4" data-testid="wl-nome-sistema" />
                  </FormInput>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormInput label="Slogan / Subtítulo">
                    <input value={config.identidade?.subtitulo || ''} onChange={e => updateConfig('identidade.subtitulo', e.target.value)}
                      className="input-industrial w-full px-4" placeholder="Powered by MAINTRIX" data-testid="wl-subtitulo" />
                  </FormInput>
                  <FormInput label="Rodapé">
                    <input value={config.identidade?.rodape || ''} onChange={e => updateConfig('identidade.rodape', e.target.value)}
                      className="input-industrial w-full px-4" placeholder="© 2026 Empresa" data-testid="wl-rodape" />
                  </FormInput>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-900/50 border border-slate-800">
                  <input type="checkbox" checked={config.identidade?.mostrar_powered_by !== false}
                    onChange={e => updateConfig('identidade.mostrar_powered_by', e.target.checked)}
                    className="w-5 h-5 rounded border-slate-600 bg-slate-800 accent-brand" data-testid="wl-powered-by" />
                  <div>
                    <p className="text-sm text-slate-200">Mostrar "Powered by MAINTRIX"</p>
                    <p className="text-[10px] text-slate-500">Exibe a marca MAINTRIX no rodapé do login e em relatórios</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <AssetUploader label="Logo Principal" currentUrl={config.identidade?.logo_url} orgId={selectedOrgId} assetType="logo" onUploaded={url => handleAssetUploaded('logo_url', url)} />
                  <AssetUploader label="Logo Branca" currentUrl={config.identidade?.logo_branca_url} orgId={selectedOrgId} assetType="logo_branca" onUploaded={url => handleAssetUploaded('logo_branca_url', url)} />
                  <AssetUploader label="Favicon" currentUrl={config.identidade?.favicon_url} orgId={selectedOrgId} assetType="favicon" onUploaded={url => handleAssetUploaded('favicon_url', url)} />
                  <AssetUploader label="Wallpaper" currentUrl={config.identidade?.wallpaper_url} orgId={selectedOrgId} assetType="wallpaper" onUploaded={url => handleAssetUploaded('wallpaper_url', url)} />
                </div>
              </div>
            )}

            {/* Colors Section */}
            {activeSection === 'cores' && (
              <div className="glass-card p-6 space-y-5" data-testid="wl-section-cores">
                <h3 className="section-title"><Palette size={16} /> Cores</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  <ColorField label="Cor Primária" value={config.tema?.cor_primaria} onChange={v => updateConfig('tema.cor_primaria', v)} />
                  <ColorField label="Cor Secundária" value={config.tema?.cor_secundaria} onChange={v => updateConfig('tema.cor_secundaria', v)} />
                  <ColorField label="Cor do Menu" value={config.tema?.cor_menu} onChange={v => updateConfig('tema.cor_menu', v)} />
                  <ColorField label="Cor do Header" value={config.tema?.cor_header} onChange={v => updateConfig('tema.cor_header', v)} />
                  <ColorField label="Cor da Tela de Login" value={config.tema?.cor_login} onChange={v => updateConfig('tema.cor_login', v)} />
                  <ColorField label="Cor de Fundo" value={config.tema?.cor_fundo} onChange={v => updateConfig('tema.cor_fundo', v)} />
                  <ColorField label="Cor do Texto" value={config.tema?.cor_texto} onChange={v => updateConfig('tema.cor_texto', v)} />
                  <ColorField label="Cor de Destaque" value={config.tema?.cor_destaque} onChange={v => updateConfig('tema.cor_destaque', v)} />
                </div>
              </div>
            )}

            {/* Login Section */}
            {activeSection === 'login' && (
              <div className="glass-card p-6 space-y-5" data-testid="wl-section-login">
                <h3 className="section-title"><Lock size={16} /> Tela de Login</h3>
                <FormInput label="Texto de Boas-vindas">
                  <input value={config.identidade?.texto_login || ''} onChange={e => updateConfig('identidade.texto_login', e.target.value)}
                    className="input-industrial w-full px-4" placeholder="Bem-vindo ao sistema de gestão" data-testid="wl-texto-login" />
                </FormInput>
                <FormInput label="Mensagem Institucional">
                  <textarea value={config.identidade?.texto_institucional || ''} onChange={e => updateConfig('identidade.texto_institucional', e.target.value)}
                    className="input-industrial w-full px-4 py-3 min-h-[100px] resize-y" placeholder="Texto adicional na tela de login..." data-testid="wl-texto-institucional" />
                </FormInput>
                <AssetUploader label="Imagem de Fundo do Login" currentUrl={config.identidade?.wallpaper_url} orgId={selectedOrgId} assetType="wallpaper" onUploaded={url => handleAssetUploaded('wallpaper_url', url)} />
                <ColorField label="Cor de Fundo do Login" value={config.tema?.cor_login} onChange={v => updateConfig('tema.cor_login', v)} />
              </div>
            )}

            {/* Domains Section */}
            {activeSection === 'dominios' && (
              <div className="glass-card p-6 space-y-5" data-testid="wl-section-dominios">
                <h3 className="section-title"><MapPin size={16} /> Domínios</h3>
                <FormInput label="Subdomínio">
                  <div className="flex items-center gap-2">
                    <input value={config.dominio?.subdominio || ''} onChange={e => updateConfig('dominio.subdominio', e.target.value)}
                      className="input-industrial flex-1 px-4" placeholder="astec" data-testid="wl-subdominio" />
                    <span className="text-sm text-slate-500 whitespace-nowrap">.maintrix.com.br</span>
                  </div>
                </FormInput>
                <FormInput label="Domínio Customizado">
                  <input value={config.dominio?.dominio_customizado || ''} onChange={e => updateConfig('dominio.dominio_customizado', e.target.value)}
                    className="input-industrial w-full px-4" placeholder="manutencao.astec.com.br" data-testid="wl-dominio" />
                </FormInput>
                {config.dominio?.subdominio && (
                  <div className="p-3 bg-brand-10 border border-brand-30 rounded-lg">
                    <p className="text-xs text-slate-400">URL de Acesso:</p>
                    <p className="text-sm font-mono text-brand">{config.dominio.subdominio}.maintrix.com.br</p>
                  </div>
                )}
              </div>
            )}

            {/* Themes Section */}
            {activeSection === 'temas' && (
              <div className="glass-card p-6 space-y-5" data-testid="wl-section-temas">
                <h3 className="section-title"><Sparkles size={16} /> Temas Prontos</h3>
                <p className="text-xs text-slate-500">Selecione um tema base. Depois ajuste cada cor individualmente na aba "Cores".</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {PRESET_THEMES.filter(t => t.colors).map(theme => (
                    <button key={theme.id} onClick={() => applyTheme(theme)}
                      className="p-4 rounded-xl border border-slate-700 hover:border-brand transition-all text-left group"
                      data-testid={`wl-theme-${theme.id}`}>
                      <p className="text-sm font-semibold text-slate-200 mb-2">{theme.name}</p>
                      <div className="flex gap-1">
                        {Object.values(theme.colors).slice(0, 5).map((color, i) => (
                          <div key={i} className="w-6 h-6 rounded-full border border-slate-600" style={{ backgroundColor: color }} />
                        ))}
                      </div>
                      <div className="mt-3 rounded-lg overflow-hidden h-20" style={{ backgroundColor: theme.colors.cor_fundo }}>
                        <div className="flex h-full">
                          <div className="w-1/4 h-full p-1" style={{ backgroundColor: theme.colors.cor_menu }}>
                            <div className="w-full h-1 rounded mb-1" style={{ backgroundColor: theme.colors.cor_primaria, opacity: 0.6 }} />
                            <div className="w-full h-1 rounded mb-1 bg-slate-600 opacity-30" />
                            <div className="w-full h-1 rounded bg-slate-600 opacity-30" />
                          </div>
                          <div className="flex-1 p-2 flex flex-col gap-1">
                            <div className="h-2 w-2/3 rounded" style={{ backgroundColor: theme.colors.cor_texto, opacity: 0.3 }} />
                            <div className="flex gap-1 flex-1">
                              <div className="flex-1 rounded border border-slate-700/30" style={{ backgroundColor: `${theme.colors.cor_primaria}15` }} />
                              <div className="flex-1 rounded border border-slate-700/30" style={{ backgroundColor: `${theme.colors.cor_secundaria}15` }} />
                            </div>
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right: Live Preview */}
          <div className="space-y-4" data-testid="wl-preview-panel">
            <h3 className="section-title"><Eye size={16} /> Preview em Tempo Real</h3>
            <div className="space-y-3">
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Login</p>
                <PreviewLogin cfg={config} />
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Sidebar</p>
                <PreviewSidebar cfg={config} />
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Cartão do Ativo</p>
                <PreviewCard cfg={config} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};



// ============== QR CODE LABEL GENERATOR ==============

const QR_LABEL_SIZES = [
  { id: '50x30', name: '50×30mm', w: 200, h: 120, qrSize: 70, fontSize: 8, tagSize: 10 },
  { id: '60x40', name: '60×40mm', w: 240, h: 160, qrSize: 90, fontSize: 9, tagSize: 12 },
  { id: '80x50', name: '80×50mm', w: 320, h: 200, qrSize: 120, fontSize: 10, tagSize: 14 },
  { id: 'a4', name: 'A4 (Prontuário)', w: 595, h: 842, qrSize: 200, fontSize: 12, tagSize: 18 },
];

const QRLabelModal = ({ ativo, onClose }) => {
  const { branding } = useBranding() || {};
  const b = branding || {};
  const [selectedSize, setSelectedSize] = useState('80x50');
  const labelRef = useRef(null);

  const size = QR_LABEL_SIZES.find(s => s.id === selectedSize) || QR_LABEL_SIZES[2];
  const portalUrl = `${window.location.origin}/portal/equipamento/${ativo.id}`;

  const handlePrint = () => {
    const el = labelRef.current;
    if (!el) return;
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`<!DOCTYPE html><html><head><style>
      @media print { body { margin: 0; } .label { page-break-after: always; } }
      body { font-family: 'Inter', Arial, sans-serif; margin: 0; padding: 20px; }
    </style></head><body>${el.outerHTML}</body></html>`);
    printWindow.document.close();
    printWindow.print();
  };

  const isA4 = selectedSize === 'a4';

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="glass-card p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto space-y-4" onClick={e => e.stopPropagation()} data-testid="qr-label-modal">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-100">Etiqueta QR Code</h2>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-800 rounded-lg"><X size={18} className="text-slate-400" /></button>
        </div>

        {/* Size selector */}
        <div className="flex gap-2 flex-wrap">
          {QR_LABEL_SIZES.map(s => (
            <button key={s.id} onClick={() => setSelectedSize(s.id)}
              className={`px-3 py-2 rounded-lg text-xs font-medium border transition-all ${selectedSize === s.id ? 'bg-brand-20 text-brand border-brand-30' : 'border-slate-700 text-slate-400 hover:text-slate-200'}`}
              data-testid={`qr-size-${s.id}`}>
              {s.name}
            </button>
          ))}
        </div>

        {/* Label Preview */}
        <div className="flex justify-center py-4">
          <div ref={labelRef} className="label bg-white rounded-lg shadow-lg overflow-hidden" style={{ width: isA4 ? 400 : size.w * 1.5, padding: isA4 ? 24 : 0 }}>
            {isA4 ? (
              /* A4 Prontuário */
              <div style={{ fontFamily: 'Inter, Arial, sans-serif', color: '#1e293b' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: `3px solid ${b.cor_primaria}`, paddingBottom: 12, marginBottom: 16 }}>
                  {b.logo_url ? <img src={b.logo_url?.startsWith('http') ? b.logo_url : `${BACKEND_URL}${b.logo_url}`} alt="" style={{ height: 40, objectFit: 'contain' }} /> : <span style={{ fontSize: 18, fontWeight: 700, color: b.cor_primaria }}>{b.nome_empresa}</span>}
                  <span style={{ fontSize: 10, color: '#64748b' }}>Prontuário do Equipamento</span>
                </div>
                <div style={{ textAlign: 'center', marginBottom: 16 }}>
                  <QRCodeSVG value={portalUrl} size={size.qrSize} level="H" bgColor="white" fgColor={b.cor_primaria || '#000'} />
                </div>
                <div style={{ textAlign: 'center', marginBottom: 8 }}>
                  <p style={{ fontSize: 24, fontWeight: 800, fontFamily: 'monospace', color: b.cor_primaria }}>{ativo.tag}</p>
                  <p style={{ fontSize: 16, fontWeight: 600 }}>{ativo.nome}</p>
                </div>
                <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse', marginTop: 12 }}>
                  <tbody>
                    {[['Área', ativo.sector?.nome || '—'], ['Tipo', ativo.tipo_equipamento || '—'], ['Fabricante', ativo.fabricante || '—'], ['Modelo', ativo.modelo || '—'], ['Nº Série', ativo.numero_serie || '—'], ['Status', ativo.status || 'Operacional']].map(([k, v]) => (
                      <tr key={k}><td style={{ padding: '4px 8px', fontWeight: 600, color: '#64748b', borderBottom: '1px solid #e2e8f0', width: 100 }}>{k}</td><td style={{ padding: '4px 8px', borderBottom: '1px solid #e2e8f0' }}>{v}</td></tr>
                    ))}
                  </tbody>
                </table>
                {b.mostrar_powered_by && <p style={{ textAlign: 'center', fontSize: 8, color: '#94a3b8', marginTop: 16 }}>Powered by MAINTRIX</p>}
              </div>
            ) : (
              /* Compact Label */
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 8, fontFamily: 'Inter, Arial, sans-serif', height: size.h * 1.5, backgroundColor: 'white' }}>
                <div style={{ textAlign: 'center', flexShrink: 0 }}>
                  <QRCodeSVG value={portalUrl} size={size.qrSize} level="M" bgColor="white" fgColor="#000" />
                </div>
                <div style={{ flex: 1, minWidth: 0, overflow: 'hidden' }}>
                  {b.logo_url ? <img src={b.logo_url?.startsWith('http') ? b.logo_url : `${BACKEND_URL}${b.logo_url}`} alt="" style={{ height: size.fontSize * 2, objectFit: 'contain', marginBottom: 2 }} /> : <p style={{ fontSize: size.fontSize, fontWeight: 700, color: b.cor_primaria, marginBottom: 2 }}>{b.nome_empresa}</p>}
                  <p style={{ fontSize: size.tagSize, fontWeight: 800, fontFamily: 'monospace', color: '#0f172a', lineHeight: 1.1 }}>{ativo.tag}</p>
                  <p style={{ fontSize: size.fontSize, color: '#334155', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{ativo.nome}</p>
                  {b.mostrar_powered_by && <p style={{ fontSize: Math.max(6, size.fontSize - 3), color: '#94a3b8', marginTop: 2 }}>Powered by MAINTRIX</p>}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-3 justify-center">
          <button onClick={handlePrint} className="btn-primary flex items-center gap-2 text-sm" data-testid="qr-print-btn">
            <Download size={16} /> Imprimir Etiqueta
          </button>
        </div>
      </div>
    </div>
  );
};


// ============== PORTAL CONSULTA EQUIPAMENTOS (VISUALIZADOR) ==============


export default WhiteLabelDesignerPage;
