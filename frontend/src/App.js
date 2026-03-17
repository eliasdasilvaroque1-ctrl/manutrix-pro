import { useState, useEffect, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, useParams } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { 
  Home, ClipboardCheck, Box, User, Scan, Settings, LogOut, 
  AlertTriangle, CheckCircle, XCircle, Clock, Wrench, Package,
  ChevronRight, Search, Plus, QrCode, Camera, ArrowLeft,
  Activity, TrendingUp, BarChart3, Gauge, Bell, Menu, X
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

// API Client with auth
const api = axios.create({ baseURL: API });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('manutrix_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('manutrix_token');
      localStorage.removeItem('manutrix_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Offline Detection Hook
const useOnlineStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);
  
  return isOnline;
};

// Components
const OfflineBanner = () => {
  const isOnline = useOnlineStatus();
  
  if (isOnline) return null;
  
  return (
    <div className="offline-banner flex items-center justify-center gap-2" data-testid="offline-banner">
      <AlertTriangle size={18} />
      <span>Modo Offline - Dados serão sincronizados quando reconectar</span>
    </div>
  );
};

const BottomNav = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const navItems = [
    { icon: Home, label: 'Início', path: '/' },
    { icon: ClipboardCheck, label: 'Inspeções', path: '/inspecoes' },
    { icon: null, label: 'Scan', path: '/scanner' },
    { icon: Box, label: 'Ativos', path: '/ativos' },
    { icon: Wrench, label: 'OS', path: '/os' },
  ];
  
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-slate-900 border-t border-slate-800 z-40 md:hidden" data-testid="bottom-nav">
      <div className="flex items-center justify-around">
        {navItems.map((item, idx) => {
          if (item.icon === null) {
            return (
              <button
                key={idx}
                onClick={() => navigate(item.path)}
                className="scan-button"
                data-testid="scan-nav-button"
              >
                <QrCode size={28} />
              </button>
            );
          }
          
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <button
              key={idx}
              onClick={() => navigate(item.path)}
              className={`nav-item ${isActive ? 'active' : ''}`}
              data-testid={`nav-${item.label.toLowerCase()}`}
            >
              <Icon size={22} />
              <span className="text-xs mt-1">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};

const StatusBadge = ({ status, size = 'md' }) => {
  const statusConfig = {
    operacional: { class: 'status-good', label: 'Operacional', icon: CheckCircle },
    falha: { class: 'status-critical', label: 'Falha', icon: XCircle },
    manutencao: { class: 'status-warning', label: 'Manutenção', icon: Wrench },
    inspecao_pendente: { class: 'status-warning', label: 'Inspeção Pend.', icon: Clock },
    parado_programado: { class: 'status-warning', label: 'Parado Prog.', icon: Clock },
    aberta: { class: 'status-warning', label: 'Aberta', icon: Clock },
    iniciada: { class: 'status-good', label: 'Iniciada', icon: Activity },
    concluida: { class: 'status-good', label: 'Concluída', icon: CheckCircle },
    cancelada: { class: 'status-critical', label: 'Cancelada', icon: XCircle },
    em_andamento: { class: 'status-warning', label: 'Em Andamento', icon: Activity },
    com_pendencias: { class: 'status-critical', label: 'Com Pendências', icon: AlertTriangle },
  };
  
  const config = statusConfig[status] || { class: 'status-warning', label: status, icon: Clock };
  const Icon = config.icon;
  
  return (
    <span className={`${config.class} inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium`} data-testid={`status-${status}`}>
      <Icon size={14} />
      {config.label}
    </span>
  );
};

const PriorityBadge = ({ priority }) => {
  const config = {
    A: { class: 'priority-a', label: 'Crítica' },
    B: { class: 'priority-b', label: 'Alta' },
    C: { class: 'priority-c', label: 'Média' },
    D: { class: 'priority-d', label: 'Baixa' },
  };
  
  const c = config[priority] || config.C;
  
  return (
    <span className={`${c.class} border px-2 py-1 rounded text-xs font-medium`} data-testid={`priority-${priority}`}>
      {c.label}
    </span>
  );
};

const KPICard = ({ value, label, icon: Icon, trend, color = 'emerald' }) => {
  const colorClasses = {
    emerald: 'text-emerald-400',
    amber: 'text-amber-400',
    red: 'text-red-400',
    blue: 'text-blue-400',
  };
  
  return (
    <div className="kpi-card" data-testid={`kpi-${label.toLowerCase().replace(/\s/g, '-')}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className={`kpi-value ${colorClasses[color]}`}>{value}</p>
          <p className="kpi-label">{label}</p>
        </div>
        <div className={`p-2 rounded-lg bg-slate-800 ${colorClasses[color]}`}>
          <Icon size={20} />
        </div>
      </div>
      {trend && (
        <div className="flex items-center gap-1 mt-2 text-xs text-slate-400">
          <TrendingUp size={14} className={trend > 0 ? 'text-emerald-400' : 'text-red-400'} />
          <span>{trend > 0 ? '+' : ''}{trend}% vs mês anterior</span>
        </div>
      )}
    </div>
  );
};

const LoadingSkeleton = ({ rows = 3 }) => (
  <div className="space-y-3" data-testid="loading-skeleton">
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="card-industrial p-4 animate-pulse">
        <div className="h-4 bg-slate-800 rounded w-3/4 mb-2"></div>
        <div className="h-3 bg-slate-800 rounded w-1/2"></div>
      </div>
    ))}
  </div>
);

// Login Page
const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      login(response.data);
      toast.success('Login realizado com sucesso!');
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSeed = async () => {
    try {
      const response = await axios.post(`${API}/seed`);
      toast.success('Dados de demonstração criados!');
      console.log('Credenciais:', response.data.credentials);
    } catch (error) {
      toast.info('Dados já existem ou erro ao criar');
    }
  };
  
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4" data-testid="login-page">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-emerald-400 tracking-wider">MANUTRIX</h1>
          <p className="text-slate-400 mt-2">Sistema de Gestão de Manutenção Industrial</p>
        </div>
        
        <form onSubmit={handleSubmit} className="card-industrial p-6 space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-industrial w-full px-4"
              placeholder="seu@email.com"
              required
              data-testid="login-email"
            />
          </div>
          
          <div>
            <label className="block text-sm text-slate-400 mb-1">Senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-industrial w-full px-4"
              placeholder="••••••••"
              required
              data-testid="login-password"
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full rounded-md"
            data-testid="login-submit"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
        
        <div className="mt-4 text-center">
          <button
            onClick={handleSeed}
            className="text-slate-500 hover:text-slate-300 text-sm underline"
            data-testid="seed-data-button"
          >
            Criar dados de demonstração
          </button>
          <p className="text-slate-600 text-xs mt-2">
            Admin: admin@manutrix.com / admin123<br/>
            Técnico: tecnico@manutrix.com / tecnico123
          </p>
        </div>
      </div>
    </div>
  );
};

// Dashboard Page
const DashboardPage = () => {
  const [kpis, setKpis] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [kpisRes, statsRes] = await Promise.all([
          api.get('/kpis'),
          api.get('/dashboard/stats')
        ]);
        setKpis(kpisRes.data);
        setStats(statsRes.data);
      } catch (error) {
        toast.error('Erro ao carregar dados');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);
  
  if (loading) return <LoadingSkeleton rows={6} />;
  
  return (
    <div className="space-y-6" data-testid="dashboard-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl text-slate-100">Olá, {user?.nome?.split(' ')[0]}</h1>
          <p className="text-slate-400">Bem-vindo ao MANUTRIX</p>
        </div>
        <button className="p-2 bg-slate-800 rounded-lg" data-testid="notifications-button">
          <Bell size={22} className="text-slate-400" />
        </button>
      </div>
      
      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => navigate('/scanner')}
          className="btn-primary rounded-lg py-4 flex items-center justify-center gap-2"
          data-testid="quick-scan-button"
        >
          <QrCode size={24} />
          <span>Escanear QR</span>
        </button>
        <button
          onClick={() => navigate('/os/nova')}
          className="btn-secondary rounded-lg py-4 flex items-center justify-center gap-2"
          data-testid="quick-os-button"
        >
          <Plus size={24} />
          <span>Nova OS</span>
        </button>
      </div>
      
      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3">
        <KPICard 
          value={`${kpis?.disponibilidade_percent?.toFixed(1)}%`}
          label="Disponibilidade"
          icon={Gauge}
          color="emerald"
        />
        <KPICard 
          value={`${kpis?.taxa_conformidade_percent?.toFixed(1)}%`}
          label="Conformidade"
          icon={CheckCircle}
          color={kpis?.taxa_conformidade_percent >= 90 ? 'emerald' : 'amber'}
        />
        <KPICard 
          value={`${kpis?.mttr_horas?.toFixed(1)}h`}
          label="MTTR"
          icon={Clock}
          color="blue"
        />
        <KPICard 
          value={kpis?.backlog_total || 0}
          label="Backlog"
          icon={ClipboardCheck}
          color={kpis?.backlog_total > 10 ? 'red' : 'emerald'}
        />
      </div>
      
      {/* Stats Cards */}
      <div className="space-y-3">
        <h2 className="text-lg text-slate-300 font-semibold">Visão Geral</h2>
        
        <div className="card-industrial p-4" onClick={() => navigate('/ativos')} data-testid="stats-ativos">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-500/10 rounded-lg">
                <Box size={24} className="text-emerald-400" />
              </div>
              <div>
                <p className="text-slate-100 font-semibold">{stats?.ativos?.total || 0} Ativos</p>
                <p className="text-sm text-slate-400">
                  {stats?.ativos?.operacionais || 0} operacionais • {stats?.ativos?.em_falha || 0} em falha
                </p>
              </div>
            </div>
            <ChevronRight className="text-slate-600" />
          </div>
        </div>
        
        <div className="card-industrial p-4" onClick={() => navigate('/os')} data-testid="stats-os">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500/10 rounded-lg">
                <Wrench size={24} className="text-amber-400" />
              </div>
              <div>
                <p className="text-slate-100 font-semibold">
                  {(stats?.ordens_servico?.abertas || 0) + (stats?.ordens_servico?.em_andamento || 0)} OS Pendentes
                </p>
                <p className="text-sm text-slate-400">
                  {stats?.ordens_servico?.abertas || 0} abertas • {stats?.ordens_servico?.em_andamento || 0} em andamento
                </p>
              </div>
            </div>
            <ChevronRight className="text-slate-600" />
          </div>
        </div>
        
        <div className="card-industrial p-4" onClick={() => navigate('/inspecoes')} data-testid="stats-inspecoes">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <ClipboardCheck size={24} className="text-blue-400" />
              </div>
              <div>
                <p className="text-slate-100 font-semibold">{stats?.inspecoes_hoje || 0} Inspeções Hoje</p>
                <p className="text-sm text-slate-400">{kpis?.inspecoes_pendentes || 0} pendentes</p>
              </div>
            </div>
            <ChevronRight className="text-slate-600" />
          </div>
        </div>
        
        {stats?.estoque_critico > 0 && (
          <div className="card-industrial p-4 border-amber-500/50 hazard-stripes" onClick={() => navigate('/estoque')} data-testid="stats-estoque-critico">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-amber-500/10 rounded-lg">
                  <Package size={24} className="text-amber-400" />
                </div>
                <div>
                  <p className="text-amber-400 font-semibold">{stats.estoque_critico} Itens em Estoque Crítico</p>
                  <p className="text-sm text-slate-400">Verificar reposição</p>
                </div>
              </div>
              <ChevronRight className="text-amber-500" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Ativos Page
const AtivosPage = () => {
  const [ativos, setAtivos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchAtivos = async () => {
      try {
        const response = await api.get('/ativos');
        setAtivos(response.data);
      } catch (error) {
        toast.error('Erro ao carregar ativos');
      } finally {
        setLoading(false);
      }
    };
    fetchAtivos();
  }, []);
  
  const filtered = ativos.filter(a => 
    a.tag.toLowerCase().includes(search.toLowerCase()) ||
    a.nome.toLowerCase().includes(search.toLowerCase())
  );
  
  return (
    <div className="space-y-4" data-testid="ativos-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl text-slate-100">Ativos</h1>
        <button 
          onClick={() => navigate('/ativos/novo')}
          className="p-2 bg-emerald-500 rounded-lg"
          data-testid="add-ativo-button"
        >
          <Plus size={22} className="text-slate-950" />
        </button>
      </div>
      
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={20} />
        <input
          type="text"
          placeholder="Buscar por TAG ou nome..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-industrial w-full pl-10 pr-4"
          data-testid="search-ativos"
        />
      </div>
      
      {loading ? (
        <LoadingSkeleton rows={5} />
      ) : (
        <div className="space-y-2">
          {filtered.map((ativo) => (
            <div
              key={ativo.id}
              className="card-industrial p-4 cursor-pointer hover:border-slate-700 transition-colors"
              onClick={() => navigate(`/ativos/${ativo.id}`)}
              data-testid={`ativo-card-${ativo.tag}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    ativo.status === 'operacional' ? 'bg-emerald-500/10' :
                    ativo.status === 'falha' ? 'bg-red-500/10' : 'bg-amber-500/10'
                  }`}>
                    <Box size={24} className={
                      ativo.status === 'operacional' ? 'text-emerald-400' :
                      ativo.status === 'falha' ? 'text-red-400' : 'text-amber-400'
                    } />
                  </div>
                  <div>
                    <p className="font-mono text-emerald-400 text-sm">{ativo.tag}</p>
                    <p className="text-slate-100">{ativo.nome}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <PriorityBadge priority={ativo.criticidade} />
                  <ChevronRight className="text-slate-600" />
                </div>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <StatusBadge status={ativo.status} />
              </div>
            </div>
          ))}
          
          {filtered.length === 0 && (
            <div className="text-center py-8 text-slate-500">
              Nenhum ativo encontrado
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Ativo Detail Page
const AtivoDetailPage = () => {
  const { id } = useParams();
  const [ativo, setAtivo] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchAtivo = async () => {
      try {
        const response = await api.get(`/ativos/${id}`);
        setAtivo(response.data);
      } catch (error) {
        toast.error('Ativo não encontrado');
        navigate('/ativos');
      } finally {
        setLoading(false);
      }
    };
    fetchAtivo();
  }, [id, navigate]);
  
  if (loading) return <LoadingSkeleton rows={4} />;
  if (!ativo) return null;
  
  return (
    <div className="space-y-4" data-testid="ativo-detail-page">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/ativos')} className="p-2 bg-slate-800 rounded-lg">
          <ArrowLeft size={22} className="text-slate-400" />
        </button>
        <div>
          <p className="font-mono text-emerald-400 text-sm">{ativo.tag}</p>
          <h1 className="text-xl text-slate-100">{ativo.nome}</h1>
        </div>
      </div>
      
      <div className="flex gap-2">
        <StatusBadge status={ativo.status} />
        <PriorityBadge priority={ativo.criticidade} />
      </div>
      
      {/* QR Code */}
      <div className="card-industrial p-4 text-center">
        <p className="text-sm text-slate-400 mb-2">QR Code do Ativo</p>
        <div className="bg-white p-4 rounded-lg inline-block">
          <QrCode size={120} className="text-slate-900" />
        </div>
        <p className="font-mono text-xs text-slate-500 mt-2">{ativo.qr_code}</p>
      </div>
      
      {/* Info */}
      <div className="card-industrial p-4 space-y-3">
        <h2 className="text-lg text-slate-300">Informações</h2>
        
        {ativo.fabricante && (
          <div className="flex justify-between">
            <span className="text-slate-500">Fabricante</span>
            <span className="text-slate-200">{ativo.fabricante}</span>
          </div>
        )}
        {ativo.modelo && (
          <div className="flex justify-between">
            <span className="text-slate-500">Modelo</span>
            <span className="text-slate-200">{ativo.modelo}</span>
          </div>
        )}
        {ativo.ano_aquisicao && (
          <div className="flex justify-between">
            <span className="text-slate-500">Ano Aquisição</span>
            <span className="text-slate-200">{ativo.ano_aquisicao}</span>
          </div>
        )}
        {ativo.localizacao_fisica && (
          <div className="flex justify-between">
            <span className="text-slate-500">Localização</span>
            <span className="text-slate-200">{ativo.localizacao_fisica}</span>
          </div>
        )}
      </div>
      
      {/* Actions */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => navigate(`/inspecoes/nova?ativo=${ativo.id}`)}
          className="btn-primary rounded-lg py-4 flex items-center justify-center gap-2"
          data-testid="iniciar-inspecao-button"
        >
          <ClipboardCheck size={20} />
          <span>Iniciar Inspeção</span>
        </button>
        <button
          onClick={() => navigate(`/os/nova?ativo=${ativo.id}`)}
          className="btn-secondary rounded-lg py-4 flex items-center justify-center gap-2"
          data-testid="criar-os-button"
        >
          <Wrench size={20} />
          <span>Criar OS</span>
        </button>
      </div>
    </div>
  );
};

// Inspeções Page
const InspecoesPage = () => {
  const [inspecoes, setInspecoes] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchInspecoes = async () => {
      try {
        const response = await api.get('/inspecoes');
        setInspecoes(response.data);
      } catch (error) {
        toast.error('Erro ao carregar inspeções');
      } finally {
        setLoading(false);
      }
    };
    fetchInspecoes();
  }, []);
  
  return (
    <div className="space-y-4" data-testid="inspecoes-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl text-slate-100">Inspeções</h1>
        <button
          onClick={() => navigate('/inspecoes/nova')}
          className="p-2 bg-emerald-500 rounded-lg"
          data-testid="add-inspecao-button"
        >
          <Plus size={22} className="text-slate-950" />
        </button>
      </div>
      
      {loading ? (
        <LoadingSkeleton rows={5} />
      ) : (
        <div className="space-y-2">
          {inspecoes.map((inspecao) => (
            <div
              key={inspecao.id}
              className="card-industrial p-4 cursor-pointer hover:border-slate-700 transition-colors"
              onClick={() => navigate(`/inspecoes/${inspecao.id}`)}
              data-testid={`inspecao-card-${inspecao.id}`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-100">Inspeção #{inspecao.id.slice(0, 8)}</p>
                  <p className="text-sm text-slate-500">
                    {new Date(inspecao.created_at).toLocaleDateString('pt-BR')}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={inspecao.status} />
                  <ChevronRight className="text-slate-600" />
                </div>
              </div>
            </div>
          ))}
          
          {inspecoes.length === 0 && (
            <div className="text-center py-8 text-slate-500">
              Nenhuma inspeção encontrada
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Nova Inspeção Page
const NovaInspecaoPage = () => {
  const [ativos, setAtivos] = useState([]);
  const [rotas, setRotas] = useState([]);
  const [selectedAtivo, setSelectedAtivo] = useState('');
  const [selectedRota, setSelectedRota] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ativosRes, rotasRes] = await Promise.all([
          api.get('/ativos'),
          api.get('/rotas-inspecao')
        ]);
        setAtivos(ativosRes.data);
        setRotas(rotasRes.data);
        
        // Check URL params
        const params = new URLSearchParams(window.location.search);
        if (params.get('ativo')) {
          setSelectedAtivo(params.get('ativo'));
        }
      } catch (error) {
        toast.error('Erro ao carregar dados');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);
  
  const handleSubmit = async () => {
    if (!selectedAtivo || !selectedRota) {
      toast.error('Selecione um ativo e uma rota');
      return;
    }
    
    setSubmitting(true);
    try {
      const response = await api.post('/inspecoes', {
        ativo_id: selectedAtivo,
        rota_id: selectedRota,
        tecnico_id: user.id
      });
      toast.success('Inspeção iniciada!');
      navigate(`/inspecoes/${response.data.id}`);
    } catch (error) {
      toast.error('Erro ao criar inspeção');
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) return <LoadingSkeleton rows={4} />;
  
  return (
    <div className="space-y-4" data-testid="nova-inspecao-page">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/inspecoes')} className="p-2 bg-slate-800 rounded-lg">
          <ArrowLeft size={22} className="text-slate-400" />
        </button>
        <h1 className="text-xl text-slate-100">Nova Inspeção</h1>
      </div>
      
      <div className="card-industrial p-4 space-y-4">
        <div>
          <label className="block text-sm text-slate-400 mb-2">Ativo</label>
          <select
            value={selectedAtivo}
            onChange={(e) => setSelectedAtivo(e.target.value)}
            className="input-industrial w-full px-4"
            data-testid="select-ativo"
          >
            <option value="">Selecione um ativo...</option>
            {ativos.map((ativo) => (
              <option key={ativo.id} value={ativo.id}>
                {ativo.tag} - {ativo.nome}
              </option>
            ))}
          </select>
        </div>
        
        <div>
          <label className="block text-sm text-slate-400 mb-2">Rota de Inspeção</label>
          <select
            value={selectedRota}
            onChange={(e) => setSelectedRota(e.target.value)}
            className="input-industrial w-full px-4"
            data-testid="select-rota"
          >
            <option value="">Selecione uma rota...</option>
            {rotas.map((rota) => (
              <option key={rota.id} value={rota.id}>
                {rota.nome}
              </option>
            ))}
          </select>
        </div>
        
        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="btn-primary w-full rounded-lg"
          data-testid="iniciar-inspecao-submit"
        >
          {submitting ? 'Iniciando...' : 'Iniciar Inspeção'}
        </button>
      </div>
    </div>
  );
};

// Inspeção Execução Page
const InspecaoExecucaoPage = () => {
  const { id } = useParams();
  const [inspecao, setInspecao] = useState(null);
  const [rota, setRota] = useState(null);
  const [respostas, setRespostas] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const inspecaoRes = await api.get(`/inspecoes/${id}`);
        setInspecao(inspecaoRes.data);
        
        const rotaRes = await api.get('/rotas-inspecao');
        const rotaData = rotaRes.data.find(r => r.id === inspecaoRes.data.rota_id);
        setRota(rotaData);
        
        // Initialize respostas
        const initial = {};
        rotaData?.itens?.forEach(item => {
          initial[item.id] = { valor: null, conforme: true, observacao: '' };
        });
        setRespostas(initial);
      } catch (error) {
        toast.error('Erro ao carregar inspeção');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);
  
  const handleResposta = (itemId, field, value) => {
    setRespostas(prev => ({
      ...prev,
      [itemId]: { ...prev[itemId], [field]: value }
    }));
  };
  
  const handleFinalizar = async () => {
    if (!rota) return;
    
    // Build respostas array
    const respostasArray = rota.itens.map(item => ({
      item_id: item.id,
      valor: respostas[item.id]?.valor,
      conforme: respostas[item.id]?.conforme ?? true,
      observacao: respostas[item.id]?.observacao || ''
    }));
    
    // Check required items
    const missing = rota.itens.filter(item => 
      item.obrigatorio && respostas[item.id]?.valor === null
    );
    
    if (missing.length > 0) {
      toast.error(`Preencha todos os itens obrigatórios (${missing.length} faltando)`);
      return;
    }
    
    setSubmitting(true);
    try {
      const response = await api.post(`/inspecoes/${id}/finalizar`, {
        respostas: respostasArray
      });
      
      if (response.data.os_geradas?.length > 0) {
        toast.warning(`Inspeção concluída com ${response.data.total_nao_conformes} pendências. ${response.data.os_geradas.length} OS geradas.`);
      } else {
        toast.success('Inspeção concluída com sucesso!');
      }
      navigate('/inspecoes');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao finalizar inspeção');
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) return <LoadingSkeleton rows={6} />;
  if (!inspecao || !rota) return null;
  
  if (inspecao.status !== 'em_andamento') {
    return (
      <div className="space-y-4" data-testid="inspecao-finalizada">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/inspecoes')} className="p-2 bg-slate-800 rounded-lg">
            <ArrowLeft size={22} className="text-slate-400" />
          </button>
          <h1 className="text-xl text-slate-100">Inspeção</h1>
        </div>
        <div className="card-industrial p-4 text-center">
          <StatusBadge status={inspecao.status} />
          <p className="text-slate-400 mt-4">Esta inspeção já foi finalizada</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-4 pb-24" data-testid="inspecao-execucao-page">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/inspecoes')} className="p-2 bg-slate-800 rounded-lg">
          <ArrowLeft size={22} className="text-slate-400" />
        </button>
        <div>
          <h1 className="text-xl text-slate-100">{rota.nome}</h1>
          <p className="text-sm text-slate-500">{rota.itens.length} itens</p>
        </div>
      </div>
      
      {/* Checklist Items */}
      <div className="space-y-3">
        {rota.itens.map((item, idx) => (
          <div key={item.id} className="card-industrial p-4" data-testid={`checklist-item-${idx}`}>
            <div className="flex items-start gap-3">
              <span className="text-emerald-400 font-mono text-sm">{idx + 1}</span>
              <div className="flex-1">
                <p className="text-slate-200">{item.descricao}</p>
                {item.obrigatorio && <span className="text-xs text-red-400">* Obrigatório</span>}
                
                {/* Response Input */}
                <div className="mt-3">
                  {item.tipo_resposta === 'boolean' && (
                    <div className="flex gap-3">
                      <button
                        onClick={() => handleResposta(item.id, 'valor', true)}
                        className={`flex-1 py-3 rounded-lg border ${
                          respostas[item.id]?.valor === true
                            ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400'
                            : 'border-slate-700 text-slate-400'
                        }`}
                        data-testid={`item-${idx}-ok`}
                      >
                        <CheckCircle size={20} className="mx-auto mb-1" />
                        OK
                      </button>
                      <button
                        onClick={() => {
                          handleResposta(item.id, 'valor', false);
                          handleResposta(item.id, 'conforme', false);
                        }}
                        className={`flex-1 py-3 rounded-lg border ${
                          respostas[item.id]?.valor === false
                            ? 'bg-red-500/20 border-red-500 text-red-400'
                            : 'border-slate-700 text-slate-400'
                        }`}
                        data-testid={`item-${idx}-nok`}
                      >
                        <XCircle size={20} className="mx-auto mb-1" />
                        NOK
                      </button>
                    </div>
                  )}
                  
                  {item.tipo_resposta === 'numero' && (
                    <div>
                      <input
                        type="number"
                        placeholder={item.valor_esperado ? `Esperado: ${item.valor_esperado}` : 'Digite o valor'}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value);
                          handleResposta(item.id, 'valor', val);
                          if (item.tolerancia_min !== null && item.tolerancia_max !== null) {
                            handleResposta(item.id, 'conforme', val >= item.tolerancia_min && val <= item.tolerancia_max);
                          }
                        }}
                        className="input-industrial w-full px-4"
                        data-testid={`item-${idx}-numero`}
                      />
                      {item.tolerancia_min !== null && (
                        <p className="text-xs text-slate-500 mt-1">
                          Tolerância: {item.tolerancia_min} - {item.tolerancia_max}
                        </p>
                      )}
                    </div>
                  )}
                  
                  {item.tipo_resposta === 'texto' && (
                    <textarea
                      placeholder="Digite sua observação"
                      onChange={(e) => handleResposta(item.id, 'valor', e.target.value)}
                      className="input-industrial w-full px-4 py-3 min-h-[80px]"
                      data-testid={`item-${idx}-texto`}
                    />
                  )}
                </div>
                
                {/* Observation for NOK */}
                {respostas[item.id]?.valor === false && item.tipo_resposta === 'boolean' && (
                  <div className="mt-3">
                    <textarea
                      placeholder="Descreva a falha encontrada (obrigatório)"
                      onChange={(e) => handleResposta(item.id, 'observacao', e.target.value)}
                      className="input-industrial w-full px-4 py-3 min-h-[80px] border-red-500/50"
                      data-testid={`item-${idx}-observacao`}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Fixed Bottom Action */}
      <div className="fixed bottom-16 left-0 right-0 p-4 bg-slate-950 border-t border-slate-800 md:bottom-0">
        <button
          onClick={handleFinalizar}
          disabled={submitting}
          className="btn-primary w-full rounded-lg"
          data-testid="finalizar-inspecao-button"
        >
          {submitting ? 'Finalizando...' : 'Finalizar Inspeção'}
        </button>
      </div>
    </div>
  );
};

// Ordens de Serviço Page
const OSPage = () => {
  const [osList, setOsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchOS = async () => {
      try {
        const response = await api.get('/ordens-servico');
        setOsList(response.data);
      } catch (error) {
        toast.error('Erro ao carregar ordens de serviço');
      } finally {
        setLoading(false);
      }
    };
    fetchOS();
  }, []);
  
  const filtered = osList.filter(os => {
    if (filter === 'all') return true;
    return os.status === filter;
  });
  
  return (
    <div className="space-y-4" data-testid="os-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl text-slate-100">Ordens de Serviço</h1>
        <button
          onClick={() => navigate('/os/nova')}
          className="p-2 bg-emerald-500 rounded-lg"
          data-testid="add-os-button"
        >
          <Plus size={22} className="text-slate-950" />
        </button>
      </div>
      
      {/* Filters */}
      <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-2">
        {[
          { value: 'all', label: 'Todas' },
          { value: 'aberta', label: 'Abertas' },
          { value: 'iniciada', label: 'Iniciadas' },
          { value: 'concluida', label: 'Concluídas' },
        ].map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-4 py-2 rounded-lg whitespace-nowrap ${
              filter === f.value
                ? 'bg-emerald-500 text-slate-950'
                : 'bg-slate-800 text-slate-300'
            }`}
            data-testid={`filter-${f.value}`}
          >
            {f.label}
          </button>
        ))}
      </div>
      
      {loading ? (
        <LoadingSkeleton rows={5} />
      ) : (
        <div className="space-y-2">
          {filtered.map((os) => (
            <div
              key={os.id}
              className="card-industrial p-4 cursor-pointer hover:border-slate-700 transition-colors"
              onClick={() => navigate(`/os/${os.id}`)}
              data-testid={`os-card-${os.numero}`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-mono text-emerald-400 text-sm">#{os.numero}</p>
                  <p className="text-slate-100">{os.titulo}</p>
                </div>
                <ChevronRight className="text-slate-600" />
              </div>
              <div className="mt-2 flex items-center gap-2 flex-wrap">
                <StatusBadge status={os.status} />
                <PriorityBadge priority={os.prioridade} />
                <span className="text-xs text-slate-500">
                  {os.tipo.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
          
          {filtered.length === 0 && (
            <div className="text-center py-8 text-slate-500">
              Nenhuma ordem de serviço encontrada
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// OS Detail Page
const OSDetailPage = () => {
  const { id } = useParams();
  const [os, setOs] = useState(null);
  const [ativo, setAtivo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const osRes = await api.get(`/ordens-servico/${id}`);
        setOs(osRes.data);
        
        if (osRes.data.ativo_id) {
          const ativoRes = await api.get(`/ativos/${osRes.data.ativo_id}`);
          setAtivo(ativoRes.data);
        }
      } catch (error) {
        toast.error('OS não encontrada');
        navigate('/os');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, navigate]);
  
  const handleStatusChange = async (newStatus) => {
    setUpdating(true);
    try {
      const response = await api.put(`/ordens-servico/${id}`, { status: newStatus });
      setOs(response.data);
      toast.success('Status atualizado!');
    } catch (error) {
      toast.error('Erro ao atualizar status');
    } finally {
      setUpdating(false);
    }
  };
  
  const handleFinalizar = async () => {
    setUpdating(true);
    try {
      await api.post(`/ordens-servico/${id}/finalizar`, []);
      toast.success('Ordem de serviço finalizada!');
      navigate('/os');
    } catch (error) {
      toast.error('Erro ao finalizar OS');
    } finally {
      setUpdating(false);
    }
  };
  
  if (loading) return <LoadingSkeleton rows={4} />;
  if (!os) return null;
  
  return (
    <div className="space-y-4" data-testid="os-detail-page">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/os')} className="p-2 bg-slate-800 rounded-lg">
          <ArrowLeft size={22} className="text-slate-400" />
        </button>
        <div>
          <p className="font-mono text-emerald-400 text-sm">#{os.numero}</p>
          <h1 className="text-xl text-slate-100">{os.titulo}</h1>
        </div>
      </div>
      
      <div className="flex gap-2 flex-wrap">
        <StatusBadge status={os.status} />
        <PriorityBadge priority={os.prioridade} />
        <span className="px-2 py-1 bg-slate-800 rounded text-xs text-slate-300">
          {os.tipo.toUpperCase()}
        </span>
      </div>
      
      {/* Ativo Info */}
      {ativo && (
        <div 
          className="card-industrial p-4 cursor-pointer"
          onClick={() => navigate(`/ativos/${ativo.id}`)}
          data-testid="os-ativo-card"
        >
          <p className="text-sm text-slate-500 mb-1">Ativo</p>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-mono text-emerald-400 text-sm">{ativo.tag}</p>
              <p className="text-slate-200">{ativo.nome}</p>
            </div>
            <ChevronRight className="text-slate-600" />
          </div>
        </div>
      )}
      
      {/* Description */}
      {os.descricao && (
        <div className="card-industrial p-4">
          <p className="text-sm text-slate-500 mb-1">Descrição</p>
          <p className="text-slate-200">{os.descricao}</p>
        </div>
      )}
      
      {/* Dates */}
      <div className="card-industrial p-4 space-y-2">
        <div className="flex justify-between">
          <span className="text-slate-500">Criada em</span>
          <span className="text-slate-200">
            {new Date(os.created_at).toLocaleString('pt-BR')}
          </span>
        </div>
        {os.start_at && (
          <div className="flex justify-between">
            <span className="text-slate-500">Iniciada em</span>
            <span className="text-slate-200">
              {new Date(os.start_at).toLocaleString('pt-BR')}
            </span>
          </div>
        )}
        {os.finish_at && (
          <div className="flex justify-between">
            <span className="text-slate-500">Concluída em</span>
            <span className="text-slate-200">
              {new Date(os.finish_at).toLocaleString('pt-BR')}
            </span>
          </div>
        )}
        {os.tempo_efetivo_minutos && (
          <div className="flex justify-between">
            <span className="text-slate-500">Tempo efetivo</span>
            <span className="text-emerald-400 font-semibold">
              {Math.floor(os.tempo_efetivo_minutos / 60)}h {os.tempo_efetivo_minutos % 60}min
            </span>
          </div>
        )}
      </div>
      
      {/* Actions */}
      {os.status !== 'concluida' && os.status !== 'cancelada' && (
        <div className="space-y-3">
          {os.status === 'aberta' && (
            <button
              onClick={() => handleStatusChange('iniciada')}
              disabled={updating}
              className="btn-primary w-full rounded-lg"
              data-testid="iniciar-os-button"
            >
              {updating ? 'Atualizando...' : 'Iniciar OS'}
            </button>
          )}
          
          {os.status === 'iniciada' && (
            <>
              <button
                onClick={handleFinalizar}
                disabled={updating}
                className="btn-primary w-full rounded-lg"
                data-testid="finalizar-os-button"
              >
                {updating ? 'Finalizando...' : 'Finalizar OS'}
              </button>
              <button
                onClick={() => handleStatusChange('pausada')}
                disabled={updating}
                className="btn-secondary w-full rounded-lg"
                data-testid="pausar-os-button"
              >
                Pausar OS
              </button>
            </>
          )}
          
          {os.status === 'pausada' && (
            <button
              onClick={() => handleStatusChange('iniciada')}
              disabled={updating}
              className="btn-primary w-full rounded-lg"
              data-testid="retomar-os-button"
            >
              {updating ? 'Atualizando...' : 'Retomar OS'}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

// Nova OS Page
const NovaOSPage = () => {
  const [ativos, setAtivos] = useState([]);
  const [formData, setFormData] = useState({
    ativo_id: '',
    titulo: '',
    descricao: '',
    tipo: 'manual',
    prioridade: 'C'
  });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchAtivos = async () => {
      try {
        const response = await api.get('/ativos');
        setAtivos(response.data);
        
        const params = new URLSearchParams(window.location.search);
        if (params.get('ativo')) {
          setFormData(prev => ({ ...prev, ativo_id: params.get('ativo') }));
        }
      } catch (error) {
        toast.error('Erro ao carregar ativos');
      } finally {
        setLoading(false);
      }
    };
    fetchAtivos();
  }, []);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.ativo_id || !formData.titulo) {
      toast.error('Preencha os campos obrigatórios');
      return;
    }
    
    setSubmitting(true);
    try {
      await api.post('/ordens-servico', formData);
      toast.success('Ordem de serviço criada!');
      navigate('/os');
    } catch (error) {
      toast.error('Erro ao criar OS');
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) return <LoadingSkeleton rows={4} />;
  
  return (
    <div className="space-y-4" data-testid="nova-os-page">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/os')} className="p-2 bg-slate-800 rounded-lg">
          <ArrowLeft size={22} className="text-slate-400" />
        </button>
        <h1 className="text-xl text-slate-100">Nova Ordem de Serviço</h1>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="card-industrial p-4 space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Ativo *</label>
            <select
              value={formData.ativo_id}
              onChange={(e) => setFormData({ ...formData, ativo_id: e.target.value })}
              className="input-industrial w-full px-4"
              required
              data-testid="os-select-ativo"
            >
              <option value="">Selecione um ativo...</option>
              {ativos.map((ativo) => (
                <option key={ativo.id} value={ativo.id}>
                  {ativo.tag} - {ativo.nome}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-slate-400 mb-2">Título *</label>
            <input
              type="text"
              value={formData.titulo}
              onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
              className="input-industrial w-full px-4"
              placeholder="Ex: Troca de rolamento"
              required
              data-testid="os-titulo"
            />
          </div>
          
          <div>
            <label className="block text-sm text-slate-400 mb-2">Descrição</label>
            <textarea
              value={formData.descricao}
              onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
              className="input-industrial w-full px-4 py-3 min-h-[100px]"
              placeholder="Descreva o problema ou serviço..."
              data-testid="os-descricao"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-2">Tipo</label>
              <select
                value={formData.tipo}
                onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
                className="input-industrial w-full px-4"
                data-testid="os-tipo"
              >
                <option value="manual">Manual</option>
                <option value="preventiva">Preventiva</option>
                <option value="preditiva">Preditiva</option>
                <option value="emergencia">Emergência</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm text-slate-400 mb-2">Prioridade</label>
              <select
                value={formData.prioridade}
                onChange={(e) => setFormData({ ...formData, prioridade: e.target.value })}
                className="input-industrial w-full px-4"
                data-testid="os-prioridade"
              >
                <option value="A">Crítica (A)</option>
                <option value="B">Alta (B)</option>
                <option value="C">Média (C)</option>
                <option value="D">Baixa (D)</option>
              </select>
            </div>
          </div>
        </div>
        
        <button
          type="submit"
          disabled={submitting}
          className="btn-primary w-full rounded-lg"
          data-testid="criar-os-submit"
        >
          {submitting ? 'Criando...' : 'Criar Ordem de Serviço'}
        </button>
      </form>
    </div>
  );
};

// Scanner Page (QR Code)
const ScannerPage = () => {
  const [manualCode, setManualCode] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  
  const handleSearch = async () => {
    if (!manualCode) return;
    
    setLoading(true);
    try {
      const response = await api.get(`/ativos/qr/${manualCode}`);
      navigate(`/ativos/${response.data.id}`);
    } catch (error) {
      toast.error('Ativo não encontrado com este QR Code');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="space-y-6" data-testid="scanner-page">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/')} className="p-2 bg-slate-800 rounded-lg">
          <ArrowLeft size={22} className="text-slate-400" />
        </button>
        <h1 className="text-xl text-slate-100">Escanear QR Code</h1>
      </div>
      
      {/* Camera Placeholder */}
      <div className="card-industrial aspect-square flex flex-col items-center justify-center">
        <div className="w-48 h-48 border-2 border-dashed border-emerald-500/50 rounded-lg flex items-center justify-center">
          <Camera size={48} className="text-emerald-500/50" />
        </div>
        <p className="text-slate-500 mt-4">Aponte a câmera para o QR Code</p>
        <p className="text-slate-600 text-sm">ou digite o código manualmente abaixo</p>
      </div>
      
      {/* Manual Input */}
      <div className="card-industrial p-4 space-y-4">
        <p className="text-sm text-slate-400">Código Manual</p>
        <div className="flex gap-2">
          <input
            type="text"
            value={manualCode}
            onChange={(e) => setManualCode(e.target.value)}
            placeholder="Digite o código QR do ativo"
            className="input-industrial flex-1 px-4 font-mono"
            data-testid="manual-qr-input"
          />
          <button
            onClick={handleSearch}
            disabled={loading || !manualCode}
            className="btn-primary rounded-lg px-6"
            data-testid="search-qr-button"
          >
            {loading ? '...' : 'Buscar'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Profile Page
const ProfilePage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  return (
    <div className="space-y-4" data-testid="profile-page">
      <h1 className="text-2xl text-slate-100">Perfil</h1>
      
      <div className="card-industrial p-6 text-center">
        <div className="w-20 h-20 rounded-full bg-emerald-500/20 mx-auto flex items-center justify-center">
          <User size={40} className="text-emerald-400" />
        </div>
        <h2 className="text-xl text-slate-100 mt-4">{user?.nome}</h2>
        <p className="text-slate-500">{user?.email}</p>
        <span className="inline-block mt-2 px-3 py-1 bg-slate-800 rounded-full text-sm text-slate-300 capitalize">
          {user?.role}
        </span>
      </div>
      
      <div className="card-industrial divide-y divide-slate-800">
        <button className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-800/50" data-testid="settings-button">
          <div className="flex items-center gap-3">
            <Settings size={20} className="text-slate-400" />
            <span className="text-slate-200">Configurações</span>
          </div>
          <ChevronRight className="text-slate-600" />
        </button>
        
        <button 
          onClick={() => {
            logout();
            navigate('/login');
          }}
          className="w-full p-4 flex items-center gap-3 text-left text-red-400 hover:bg-slate-800/50"
          data-testid="logout-button"
        >
          <LogOut size={20} />
          <span>Sair</span>
        </button>
      </div>
    </div>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-emerald-400">Carregando...</div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

// Layout
const AppLayout = ({ children }) => {
  return (
    <div className="min-h-screen bg-slate-950">
      <OfflineBanner />
      <main className="pb-20 md:pb-4 px-4 pt-4 max-w-2xl mx-auto">
        {children}
      </main>
      <BottomNav />
    </div>
  );
};

// Auth Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const storedUser = localStorage.getItem('manutrix_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);
  
  const login = (data) => {
    localStorage.setItem('manutrix_token', data.access_token);
    localStorage.setItem('manutrix_user', JSON.stringify(data.user));
    setUser(data.user);
  };
  
  const logout = () => {
    localStorage.removeItem('manutrix_token');
    localStorage.removeItem('manutrix_user');
    setUser(null);
  };
  
  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Main App
function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          
          <Route path="/" element={
            <ProtectedRoute>
              <AppLayout><DashboardPage /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/ativos" element={
            <ProtectedRoute>
              <AppLayout><AtivosPage /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/ativos/:id" element={
            <ProtectedRoute>
              <AppLayout><AtivoDetailPage /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/inspecoes" element={
            <ProtectedRoute>
              <AppLayout><InspecoesPage /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/inspecoes/nova" element={
            <ProtectedRoute>
              <AppLayout><NovaInspecaoPage /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/inspecoes/:id" element={
            <ProtectedRoute>
              <AppLayout><InspecaoExecucaoPage /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/os" element={
            <ProtectedRoute>
              <AppLayout><OSPage /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/os/nova" element={
            <ProtectedRoute>
              <AppLayout><NovaOSPage /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/os/:id" element={
            <ProtectedRoute>
              <AppLayout><OSDetailPage /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/scanner" element={
            <ProtectedRoute>
              <AppLayout><ScannerPage /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/perfil" element={
            <ProtectedRoute>
              <AppLayout><ProfilePage /></AppLayout>
            </ProtectedRoute>
          } />
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster position="top-center" richColors />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
