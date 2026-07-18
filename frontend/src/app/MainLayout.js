import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Home, Box, Wrench, ClipboardCheck, QrCode, LayoutDashboard, BarChart3, Users, Target, Package, Cog, Calendar, Shield, FileText, BookOpen, Layers, Factory, Search, Palette, Trash2, ChevronLeft, ChevronRight, User, LogOut, AlertCircle, WifiOff, RefreshCw, Clock } from "lucide-react";
import { toast } from "sonner";
import { useAuth, api } from "../lib/api";
import { useBranding } from "../lib/branding";
import { ROLE_LABELS } from "../lib/constants";
import { getPendingCount, syncPendingOperations } from "../lib/offlineQueue";

const NetworkStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingCount, setPendingCount] = useState(0);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const updateOnline = () => setIsOnline(true);
    const updateOffline = () => setIsOnline(false);
    window.addEventListener('online', updateOnline);
    window.addEventListener('offline', updateOffline);
    return () => { window.removeEventListener('online', updateOnline); window.removeEventListener('offline', updateOffline); };
  }, []);

  useEffect(() => {
    const checkPending = async () => {
      try { const c = await getPendingCount(); setPendingCount(c); } catch {}
    };
    checkPending();
    const interval = setInterval(checkPending, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isOnline && pendingCount > 0) {
      const doSync = async () => {
        setSyncing(true);
        try {
          const result = await syncPendingOperations(api);
          const total = result.synced + result.photos;
          if (total > 0) toast.success(`${total} item(ns) sincronizado(s)${result.photos ? ` (${result.photos} foto(s))` : ''}`);
          if (result.failed > 0) toast.error(`${result.failed} operação(ões) falharam — nova tentativa em breve`);
          const c = await getPendingCount();
          setPendingCount(c);
        } catch {}
        setSyncing(false);
      };
      const timer = setTimeout(doSync, 2000);
      return () => clearTimeout(timer);
    }
  }, [isOnline, pendingCount]);

  if (isOnline && pendingCount === 0) return null;

  return (
    <div className={`fixed top-0 left-0 right-0 z-[60] px-4 py-1.5 text-center text-xs font-medium ${isOnline ? 'bg-amber-500/90 text-black' : 'bg-red-600/90 text-white'}`} data-testid="network-status">
      {!isOnline && <><WifiOff size={12} className="inline mr-1" /> Offline — operações serão sincronizadas ao reconectar</>}
      {isOnline && syncing && <><RefreshCw size={12} className="inline mr-1 animate-spin" /> Sincronizando {pendingCount} operação(ões)...</>}
      {isOnline && !syncing && pendingCount > 0 && <><Clock size={12} className="inline mr-1" /> {pendingCount} operação(ões) pendente(s)</>}
    </div>
  );
};

const Sidebar = ({ collapsed, setCollapsed }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { branding } = useBranding() || {};
  const b = branding || {};
  
  const role = user?.role || 'visualizador';
  const isAdmin = role === 'admin' || role === 'master';
  const isMaster = role === 'master';
  const isExecucao = ['tec_mecanico', 'tec_eletrico', 'instrumentista', 'lubrificador', 'tecnico', 'inspetor'].includes(role);
  const isOperacional = isExecucao || role === 'operador';
  const isPCM = role === 'pcm';
  const isSupervisor = role === 'supervisor';
  const isGerente = role === 'gerente';
  const isVisualizador = role === 'visualizador' || role === 'viewer';
  
  const menuGroups = isVisualizador ? [
    { label: 'CONSULTA', items: [{ icon: Search, label: 'Portal de Equipamentos', path: '/consulta' }] },
  ] : isGerente ? [
    { label: 'GESTÃO', items: [
      { icon: LayoutDashboard, label: 'Central de Trabalho', path: '/' },
      { icon: BarChart3, label: 'Dashboard', path: '/dashboard' },
      { icon: Wrench, label: 'Ordens de Serviço', path: '/os' },
      { icon: Box, label: 'Ativos', path: '/ativos' },
      { icon: Shield, label: 'Auditoria', path: '/admin/auditoria' },
    ] },
  ] : [
    { label: 'PRINCIPAL', items: [
      { icon: LayoutDashboard, label: isOperacional ? 'Minha Jornada' : 'Central de Trabalho', path: '/' },
      ...(isOperacional ? [{ icon: Target, label: 'Minha Área', path: '/minha-area' }] : []),
      ...(!isOperacional ? [{ icon: BarChart3, label: 'Dashboard', path: '/dashboard' }] : []),
      ...(!isOperacional ? [{ icon: Users, label: 'Equipe', path: '/equipe' }] : []),
    ] },
    { label: 'OPERAÇÃO', items: [
      { icon: Box, label: 'Ativos', path: '/ativos' },
      ...(isOperacional ? [{ icon: Wrench, label: 'Minhas OS', path: '/os' }] : []),
      ...(!isOperacional ? [{ icon: Wrench, label: 'Ordens de Serviço', path: '/os' }] : []),
      { icon: ClipboardCheck, label: 'Inspeções', path: '/inspecoes' },
      ...(isOperacional ? [{ icon: AlertCircle, label: 'Solicitar Serviço', path: '/solicitar' }] : []),
      ...(isOperacional ? [{ icon: QrCode, label: 'Scanner', path: '/scanner' }] : []),
      ...(isOperacional ? [{ icon: Target, label: 'Ronda', path: '/ronda' }] : []),
    ] },
    ...(!isOperacional ? [{ label: 'INFRAESTRUTURA', items: [
      ...(isAdmin ? [{ icon: Factory, label: 'Unidades', path: '/unidades' }] : []),
      { icon: Layers, label: 'Áreas', path: '/setores' },
    ] }] : []),
    { label: 'MATERIAIS', items: [
      { icon: Package, label: 'Estoque', path: '/estoque' },
      ...(!isOperacional ? [{ icon: Cog, label: 'Sobressalentes', path: '/sobressalentes' }] : []),
      ...(!isOperacional ? [{ icon: Calendar, label: 'Paradas', path: '/paradas' }] : []),
    ] },
    ...(['admin','master','pcm','supervisor'].includes(role) ? [{ label: 'PCM', items: [
      ...(['admin','master','pcm'].includes(role) ? [{ icon: BookOpen, label: 'Biblioteca Corporativa', path: '/biblioteca' }] : []),
      { icon: FileText, label: 'Dossiê / Pesquisa', path: '/dossie' },
    ] }] : []),
    ...(isAdmin || isPCM || isSupervisor ? [{ label: 'ADMIN', items: [
      ...(isAdmin ? [{ icon: Users, label: 'Usuários', path: '/admin/usuarios' }] : []),
      ...(isAdmin || isPCM ? [{ icon: ClipboardCheck, label: 'Planos de Inspeção', path: '/admin/templates' }] : []),
      ...(isAdmin || isPCM ? [{ icon: FileText, label: 'Documentos e Formulários', path: '/config/documentos' }] : []),
      ...(isAdmin || isPCM ? [{ icon: Layers, label: 'Construtor Visual', path: '/config/construtor' }] : []),
      { icon: Shield, label: 'Auditoria', path: '/admin/auditoria' },
      ...(isAdmin ? [{ icon: Cog, label: 'Configurações', path: '/admin/config' }] : []),
      ...(isMaster ? [{ icon: Palette, label: 'White Label', path: '/master/white-label' }] : []),
      ...(isMaster ? [{ icon: Trash2, label: 'Limpeza', path: '/master/cleanup' }] : []),
    ] }] : []),
  ];
  
  return (
    <aside className={`hidden md:flex flex-col backdrop-blur-sm border-r border-slate-800 h-screen sticky top-0 transition-all duration-300 ${collapsed ? 'w-16' : 'w-64'}`}
      style={{ backgroundColor: b.cor_menu || 'var(--brand-menu)' }} data-testid="sidebar">
      <div className={`p-4 border-b border-slate-800 flex items-center ${collapsed ? 'justify-center' : 'justify-between'}`}>
        {!collapsed && (
          <div className="flex items-center gap-3 min-w-0">
            {b.logo_branca_url || b.logo_url ? (
              <img src={b.logo_branca_url || b.logo_url} alt={b.nome_empresa} className="h-8 w-auto object-contain flex-shrink-0" data-testid="sidebar-logo" />
            ) : null}
            <div className="min-w-0">
              <h1 className="text-xl font-bold tracking-wider truncate" style={{ color: b.cor_primaria || 'var(--brand-primary)' }} data-testid="sidebar-brand-name">{b.nome_empresa || 'CMMS'}</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider truncate">{b.subtitulo || 'Sistema de Gestão'}</p>
            </div>
          </div>
        )}
        <button onClick={() => setCollapsed(!collapsed)} className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors flex-shrink-0">
          {collapsed ? <ChevronRight size={18} className="text-slate-400" /> : <ChevronLeft size={18} className="text-slate-400" />}
        </button>
      </div>
      <nav className="flex-1 py-4 overflow-y-auto custom-scrollbar">
        {menuGroups.map((group, idx) => (
          <div key={idx} className="mb-4">
            {!collapsed && <p className="px-4 mb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">{group.label}</p>}
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
              return (
                <button key={item.path} onClick={() => navigate(item.path)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 transition-all ${collapsed ? 'justify-center' : ''}`}
                  style={isActive ? { backgroundColor: `${b.cor_primaria || 'var(--brand-primary)'}15`, color: b.cor_primaria || 'var(--brand-primary)', borderLeft: `2px solid ${b.cor_primaria || 'var(--brand-primary)'}` } : { color: '#94a3b8', borderLeft: '2px solid transparent' }}
                  onMouseEnter={e => { if (!isActive) { e.currentTarget.style.backgroundColor = 'rgba(30,41,59,0.5)'; e.currentTarget.style.color = '#e2e8f0'; }}}
                  onMouseLeave={e => { if (!isActive) { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = '#94a3b8'; }}}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon size={20} />
                  {!collapsed && <span className="text-sm">{item.label}</span>}
                </button>
              );
            })}
          </div>
        ))}
      </nav>
      <div className={`p-4 border-t border-slate-800 ${collapsed ? 'items-center' : ''}`}>
        {!collapsed && (
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${b.cor_primaria || 'var(--brand-primary)'}20` }}>
              <User size={18} style={{ color: b.cor_primaria || 'var(--brand-primary)' }} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-slate-200 truncate">{user?.nome}</p>
              <p className="text-xs text-slate-500">{ROLE_LABELS[user?.role] || user?.role}</p>
            </div>
          </div>
        )}
        <button onClick={() => navigate('/sobre')} className={`w-full flex items-center gap-2 px-3 py-2 text-slate-400 hover:bg-surface-hover rounded-lg transition-colors ${collapsed ? 'justify-center' : ''}`} title={collapsed ? 'Sobre' : undefined} data-testid="sidebar-about">
          <AlertCircle size={18} />{!collapsed && <span className="text-sm">Sobre</span>}
        </button>
        <button onClick={() => { logout(); navigate('/login'); }} className={`w-full flex items-center gap-2 px-3 py-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors ${collapsed ? 'justify-center' : ''}`} title={collapsed ? 'Sair' : undefined}>
          <LogOut size={18} />{!collapsed && <span className="text-sm">Sair</span>}
        </button>
      </div>
    </aside>
  );
};

const BottomNav = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { branding } = useBranding() || {};
  const b = branding || {};
  const items = [
    { icon: Home, label: 'Central', path: '/' },
    { icon: ClipboardCheck, label: 'Inspeções', path: '/inspecoes' },
    { icon: QrCode, label: 'Scan', path: '/scanner', special: true },
    { icon: Box, label: 'Ativos', path: '/ativos' },
    { icon: Wrench, label: 'OS', path: '/os' },
  ];
  return (
    <nav className="fixed bottom-0 left-0 right-0 backdrop-blur-sm border-t border-slate-800 z-40 pb-safe md:hidden" style={{ backgroundColor: `${b.cor_menu || 'var(--brand-menu)'}f2` }} data-testid="bottom-nav">
      <div className="flex items-center justify-around h-16">
        {items.map((item, idx) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
          if (item.special) return <button key={idx} onClick={() => navigate(item.path)} className="scan-button pulse-glow" style={{ backgroundColor: b.cor_primaria || 'var(--brand-primary)' }}><Icon size={26} /></button>;
          return <button key={idx} onClick={() => navigate(item.path)} className="nav-item" style={isActive ? { color: b.cor_primaria || 'var(--brand-primary)' } : {}}><Icon size={20} /><span className="text-[10px] mt-1">{item.label}</span></button>;
        })}
      </div>
    </nav>
  );
};

const MainLayout = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { branding } = useBranding() || {};
  const b = branding || {};
  return (
    <div className="min-h-screen flex" style={{ backgroundColor: b.cor_fundo || 'var(--brand-bg)' }}>
      <NetworkStatus />
      <Sidebar collapsed={sidebarCollapsed} setCollapsed={setSidebarCollapsed} />
      <div className="flex-1 flex flex-col min-h-screen">
        <main className="flex-1 pb-20 md:pb-4 px-4 pt-4 max-w-6xl mx-auto w-full">{children}</main>
        <footer className="hidden md:flex items-center justify-center gap-4 py-2 text-[10px] text-slate-600 border-t border-surface/30" data-testid="app-footer">
          <a href="/termos" className="hover:text-slate-400 transition-colors">Termos de Uso</a><span>|</span>
          <a href="/privacidade" className="hover:text-slate-400 transition-colors">Privacidade</a><span>|</span>
          <a href="/sobre" className="hover:text-slate-400 transition-colors">Sobre</a><span>|</span>
          <span>v5.2.0-RC1</span>
        </footer>
        <BottomNav />
      </div>
    </div>
  );
};

export default MainLayout;
