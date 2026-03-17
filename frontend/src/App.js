import { useState, useEffect, createContext, useContext, useRef, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, useParams, useSearchParams } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { 
  Home, ClipboardCheck, Box, User, Settings, LogOut, 
  AlertTriangle, CheckCircle, XCircle, Clock, Wrench, Package,
  ChevronRight, ChevronLeft, Search, Plus, QrCode, Camera, ArrowLeft,
  Activity, TrendingUp, BarChart3, Gauge, Bell, Menu, X, Play, Pause,
  MapPin, Calendar, FileText, Image, Upload, RefreshCw, Wifi, WifiOff,
  Zap, Target, Layers, Filter, MoreVertical, Eye, Edit, Trash2,
  Phone, Mail, Building, Hash, Thermometer, Volume2, Droplet, Cog
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
    const handleOnline = () => { setIsOnline(true); toast.success('Conexão restaurada'); };
    const handleOffline = () => { setIsOnline(false); toast.warning('Modo offline ativado'); };
    
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
      <WifiOff size={18} />
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
    <nav className="fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur-sm border-t border-slate-800 z-40 pb-safe md:hidden" data-testid="bottom-nav">
      <div className="flex items-center justify-around h-16">
        {navItems.map((item, idx) => {
          if (item.icon === null) {
            return (
              <button
                key={idx}
                onClick={() => navigate(item.path)}
                className="scan-button pulse-glow"
                data-testid="scan-nav-button"
              >
                <QrCode size={28} />
              </button>
            );
          }
          
          const Icon = item.icon;
          const isActive = location.pathname === item.path || 
            (item.path !== '/' && location.pathname.startsWith(item.path));
          
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

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  
  const menuItems = [
    { icon: Home, label: 'Dashboard', path: '/' },
    { icon: Box, label: 'Ativos', path: '/ativos' },
    { icon: ClipboardCheck, label: 'Inspeções', path: '/inspecoes' },
    { icon: Target, label: 'Ronda', path: '/ronda' },
    { icon: Wrench, label: 'Ordens de Serviço', path: '/os' },
    { icon: Package, label: 'Estoque', path: '/estoque' },
    { icon: BarChart3, label: 'Relatórios', path: '/relatorios' },
  ];
  
  return (
    <aside className="hidden md:flex flex-col w-64 bg-slate-900 border-r border-slate-800 h-screen sticky top-0">
      <div className="p-4 border-b border-slate-800">
        <h1 className="text-2xl font-bold text-emerald-400 tracking-wider">MANUTRIX</h1>
        <p className="text-xs text-slate-500 mt-1">Gestão de Manutenção Industrial</p>
      </div>
      
      <nav className="flex-1 p-4 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path || 
            (item.path !== '/' && location.pathname.startsWith(item.path));
          
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive 
                  ? 'bg-emerald-500/10 text-emerald-400 border-l-2 border-emerald-500' 
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
      
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
            <User size={20} className="text-emerald-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-slate-200 truncate">{user?.nome}</p>
            <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
          </div>
        </div>
        <button 
          onClick={() => { logout(); navigate('/login'); }}
          className="w-full flex items-center gap-2 px-4 py-2 text-red-400 hover:bg-red-500/10 rounded-lg"
        >
          <LogOut size={18} />
          <span>Sair</span>
        </button>
      </div>
    </aside>
  );
};

const StatusBadge = ({ status, size = 'md' }) => {
  const statusConfig = {
    operacional: { class: 'status-good', label: 'Operacional', icon: CheckCircle },
    falha: { class: 'status-critical', label: 'Falha', icon: XCircle },
    manutencao: { class: 'status-warning', label: 'Manutenção', icon: Wrench },
    inspecao_pendente: { class: 'status-warning', label: 'Inspeção Pend.', icon: Clock },
    parado_programado: { class: 'status-warning', label: 'Parado Prog.', icon: Pause },
    aberta: { class: 'status-warning', label: 'Aberta', icon: Clock },
    iniciada: { class: 'status-good', label: 'Iniciada', icon: Play },
    pausada: { class: 'status-warning', label: 'Pausada', icon: Pause },
    concluida: { class: 'status-good', label: 'Concluída', icon: CheckCircle },
    cancelada: { class: 'status-critical', label: 'Cancelada', icon: XCircle },
    em_andamento: { class: 'status-warning', label: 'Em Andamento', icon: Activity },
    com_pendencias: { class: 'status-critical', label: 'Com Pendências', icon: AlertTriangle },
  };
  
  const config = statusConfig[status] || { class: 'status-warning', label: status, icon: Clock };
  const Icon = config.icon;
  
  return (
    <span className={`${config.class} inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium`} data-testid={`status-${status}`}>
      <Icon size={size === 'sm' ? 12 : 14} />
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

const KPICard = ({ value, label, icon: Icon, trend, color = 'emerald', subtitle }) => {
  const colorClasses = {
    emerald: 'text-emerald-400',
    amber: 'text-amber-400',
    red: 'text-red-400',
    blue: 'text-blue-400',
  };
  
  return (
    <div className="kpi-card group hover:border-slate-700 transition-all" data-testid={`kpi-${label.toLowerCase().replace(/\s/g, '-')}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className={`kpi-value ${colorClasses[color]}`}>{value}</p>
          <p className="kpi-label">{label}</p>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-2 rounded-lg bg-slate-800 ${colorClasses[color]} group-hover:scale-110 transition-transform`}>
          <Icon size={20} />
        </div>
      </div>
      {trend !== undefined && (
        <div className="flex items-center gap-1 mt-2 text-xs text-slate-400">
          <TrendingUp size={14} className={trend >= 0 ? 'text-emerald-400' : 'text-red-400'} />
          <span>{trend >= 0 ? '+' : ''}{trend}% vs mês anterior</span>
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

const EmptyState = ({ icon: Icon, title, description, action, actionLabel }) => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4">
      <Icon size={32} className="text-slate-500" />
    </div>
    <h3 className="text-lg text-slate-300 font-semibold mb-2">{title}</h3>
    <p className="text-slate-500 max-w-sm mb-4">{description}</p>
    {action && (
      <button onClick={action} className="btn-primary rounded-lg">
        {actionLabel}
      </button>
    )}
  </div>
);

const NotificationBell = () => {
  const [count, setCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const [countRes, listRes] = await Promise.all([
          api.get('/notificacoes/count'),
          api.get('/notificacoes?lida=false')
        ]);
        setCount(countRes.data.count);
        setNotifications(listRes.data.slice(0, 5));
      } catch (error) {
        console.error('Error fetching notifications');
      }
    };
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);
  
  const markAsRead = async (id) => {
    await api.put(`/notificacoes/${id}/lida`);
    setCount(prev => Math.max(0, prev - 1));
    setNotifications(prev => prev.filter(n => n.id !== id));
  };
  
  return (
    <div className="relative">
      <button 
        onClick={() => setShowDropdown(!showDropdown)}
        className="p-2 bg-slate-800 rounded-lg relative"
        data-testid="notifications-button"
      >
        <Bell size={22} className="text-slate-400" />
        {count > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-xs flex items-center justify-center text-white">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>
      
      {showDropdown && (
        <div className="absolute right-0 mt-2 w-80 bg-slate-900 border border-slate-800 rounded-lg shadow-xl z-50">
          <div className="p-3 border-b border-slate-800 flex items-center justify-between">
            <span className="font-semibold text-slate-200">Notificações</span>
            {count > 0 && (
              <button 
                onClick={async () => {
                  await api.put('/notificacoes/marcar-todas-lidas');
                  setCount(0);
                  setNotifications([]);
                }}
                className="text-xs text-emerald-400"
              >
                Marcar todas como lidas
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.length > 0 ? (
              notifications.map(notif => (
                <div 
                  key={notif.id}
                  className="p-3 border-b border-slate-800 hover:bg-slate-800/50 cursor-pointer"
                  onClick={() => {
                    markAsRead(notif.id);
                    if (notif.link) navigate(notif.link);
                    setShowDropdown(false);
                  }}
                >
                  <p className="text-sm text-slate-200">{notif.titulo}</p>
                  <p className="text-xs text-slate-500 mt-1">{notif.mensagem}</p>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-slate-500">
                Nenhuma notificação
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// QR Scanner Component with real camera
const QRScanner = ({ onScan, onClose }) => {
  const videoRef = useRef(null);
  const [error, setError] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [flashOn, setFlashOn] = useState(false);
  const streamRef = useRef(null);
  
  useEffect(() => {
    let animationId;
    
    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { 
            facingMode: 'environment',
            width: { ideal: 1280 },
            height: { ideal: 720 }
          }
        });
        
        streamRef.current = stream;
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
          setScanning(true);
          
          // Start scanning loop
          const scanLoop = async () => {
            if (videoRef.current && videoRef.current.readyState === videoRef.current.HAVE_ENOUGH_DATA) {
              try {
                // Create canvas for frame capture
                const canvas = document.createElement('canvas');
                canvas.width = videoRef.current.videoWidth;
                canvas.height = videoRef.current.videoHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(videoRef.current, 0, 0);
                
                // Try to detect QR code using BarcodeDetector if available
                if ('BarcodeDetector' in window) {
                  const barcodeDetector = new window.BarcodeDetector({ formats: ['qr_code'] });
                  const barcodes = await barcodeDetector.detect(canvas);
                  if (barcodes.length > 0) {
                    onScan(barcodes[0].rawValue);
                    return;
                  }
                }
              } catch (e) {
                // Continue scanning
              }
            }
            animationId = requestAnimationFrame(scanLoop);
          };
          
          scanLoop();
        }
      } catch (err) {
        setError('Não foi possível acessar a câmera. Verifique as permissões.');
        console.error('Camera error:', err);
      }
    };
    
    startCamera();
    
    return () => {
      if (animationId) cancelAnimationFrame(animationId);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, [onScan]);
  
  const toggleFlash = async () => {
    if (streamRef.current) {
      const track = streamRef.current.getVideoTracks()[0];
      const capabilities = track.getCapabilities?.();
      if (capabilities?.torch) {
        await track.applyConstraints({ advanced: [{ torch: !flashOn }] });
        setFlashOn(!flashOn);
      }
    }
  };
  
  return (
    <div className="fixed inset-0 bg-slate-950 z-50 flex flex-col">
      <div className="flex items-center justify-between p-4">
        <button onClick={onClose} className="p-2 bg-slate-800 rounded-lg">
          <X size={24} className="text-slate-400" />
        </button>
        <h2 className="text-lg text-slate-200">Escanear QR Code</h2>
        <button onClick={toggleFlash} className={`p-2 rounded-lg ${flashOn ? 'bg-amber-500' : 'bg-slate-800'}`}>
          <Zap size={24} className={flashOn ? 'text-slate-900' : 'text-slate-400'} />
        </button>
      </div>
      
      <div className="flex-1 relative overflow-hidden">
        {error ? (
          <div className="flex flex-col items-center justify-center h-full p-4 text-center">
            <Camera size={48} className="text-slate-500 mb-4" />
            <p className="text-red-400 mb-4">{error}</p>
            <button onClick={onClose} className="btn-secondary rounded-lg">
              Voltar
            </button>
          </div>
        ) : (
          <>
            <video 
              ref={videoRef}
              className="w-full h-full object-cover"
              playsInline
              muted
            />
            {/* Scan overlay */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-64 h-64 border-2 border-emerald-500 rounded-lg relative">
                <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-emerald-400 rounded-tl-lg"></div>
                <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-emerald-400 rounded-tr-lg"></div>
                <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-emerald-400 rounded-bl-lg"></div>
                <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-emerald-400 rounded-br-lg"></div>
                {scanning && (
                  <div className="absolute inset-0 overflow-hidden">
                    <div className="w-full h-1 bg-emerald-500 animate-scan"></div>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
      
      <div className="p-4 text-center">
        <p className="text-slate-400 text-sm">Posicione o QR Code dentro da área de leitura</p>
      </div>
    </div>
  );
};

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
      toast.info('Dados já existem');
    }
  };
  
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4" data-testid="login-page">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 mb-4">
            <Cog size={32} className="text-emerald-400" />
          </div>
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
          <div className="text-slate-600 text-xs mt-2 space-y-1">
            <p>Admin: admin@manutrix.com / admin123</p>
            <p>Técnico: tecnico@manutrix.com / tecnico123</p>
          </div>
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
  
  const osPendentes = (stats?.ordens_servico?.abertas || 0) + 
                      (stats?.ordens_servico?.em_andamento || 0) + 
                      (stats?.ordens_servico?.pausadas || 0);
  
  return (
    <div className="space-y-6" data-testid="dashboard-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl text-slate-100">Olá, {user?.nome?.split(' ')[0]}</h1>
          <p className="text-slate-400">Bem-vindo ao MANUTRIX</p>
        </div>
        <NotificationBell />
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
          onClick={() => navigate('/ronda')}
          className="btn-secondary rounded-lg py-4 flex items-center justify-center gap-2"
          data-testid="quick-ronda-button"
        >
          <Target size={24} />
          <span>Iniciar Ronda</span>
        </button>
      </div>
      
      {/* KPIs Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
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
          subtitle="Tempo médio de reparo"
        />
        <KPICard 
          value={kpis?.backlog_total || 0}
          label="Backlog"
          icon={Layers}
          color={kpis?.backlog_total > 10 ? 'red' : 'emerald'}
        />
      </div>
      
      {/* Alerts */}
      {(stats?.ativos?.em_falha > 0 || stats?.estoque_critico > 0) && (
        <div className="space-y-2">
          {stats?.ativos?.em_falha > 0 && (
            <div className="card-industrial p-4 border-red-500/50 flex items-center gap-3 cursor-pointer hover:bg-red-500/5" onClick={() => navigate('/ativos?status=falha')}>
              <AlertTriangle className="text-red-500" size={24} />
              <div>
                <p className="text-red-400 font-semibold">{stats.ativos.em_falha} Ativo(s) em Falha</p>
                <p className="text-xs text-slate-500">Atenção imediata necessária</p>
              </div>
            </div>
          )}
          {stats?.estoque_critico > 0 && (
            <div className="card-industrial p-4 border-amber-500/50 hazard-stripes flex items-center gap-3 cursor-pointer hover:bg-amber-500/5" onClick={() => navigate('/estoque?critico=true')}>
              <Package className="text-amber-500" size={24} />
              <div>
                <p className="text-amber-400 font-semibold">{stats.estoque_critico} Itens em Estoque Crítico</p>
                <p className="text-xs text-slate-500">Verificar necessidade de reposição</p>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Stats Cards */}
      <div className="space-y-3">
        <h2 className="text-lg text-slate-300 font-semibold">Visão Geral</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="card-industrial p-4 cursor-pointer hover:border-slate-700" onClick={() => navigate('/ativos')} data-testid="stats-ativos">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-500/10 rounded-lg">
                  <Box size={24} className="text-emerald-400" />
                </div>
                <div>
                  <p className="text-slate-100 font-semibold">{stats?.ativos?.total || 0} Ativos</p>
                  <p className="text-sm text-slate-400">
                    {stats?.ativos?.operacionais || 0} operacionais
                  </p>
                </div>
              </div>
              <ChevronRight className="text-slate-600" />
            </div>
          </div>
          
          <div className="card-industrial p-4 cursor-pointer hover:border-slate-700" onClick={() => navigate('/os')} data-testid="stats-os">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-amber-500/10 rounded-lg">
                  <Wrench size={24} className="text-amber-400" />
                </div>
                <div>
                  <p className="text-slate-100 font-semibold">{osPendentes} OS Pendentes</p>
                  <p className="text-sm text-slate-400">
                    {stats?.ordens_servico?.concluidas_hoje || 0} concluídas hoje
                  </p>
                </div>
              </div>
              <ChevronRight className="text-slate-600" />
            </div>
          </div>
          
          <div className="card-industrial p-4 cursor-pointer hover:border-slate-700" onClick={() => navigate('/inspecoes')} data-testid="stats-inspecoes">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/10 rounded-lg">
                  <ClipboardCheck size={24} className="text-blue-400" />
                </div>
                <div>
                  <p className="text-slate-100 font-semibold">{stats?.inspecoes?.hoje || 0} Inspeções Hoje</p>
                  <p className="text-sm text-slate-400">
                    {stats?.inspecoes?.pendentes || 0} em andamento
                  </p>
                </div>
              </div>
              <ChevronRight className="text-slate-600" />
            </div>
          </div>
        </div>
      </div>
      
      {/* OS by Priority */}
      {stats?.ordens_servico?.por_prioridade && (
        <div className="card-industrial p-4">
          <h3 className="text-sm text-slate-400 mb-3">OS por Prioridade</h3>
          <div className="flex gap-2">
            {['A', 'B', 'C', 'D'].map(p => (
              <div key={p} className={`flex-1 text-center p-2 rounded-lg ${
                p === 'A' ? 'bg-red-500/10' : 
                p === 'B' ? 'bg-amber-500/10' : 
                p === 'C' ? 'bg-emerald-500/10' : 'bg-slate-800'
              }`}>
                <p className={`text-2xl font-bold ${
                  p === 'A' ? 'text-red-400' : 
                  p === 'B' ? 'text-amber-400' : 
                  p === 'C' ? 'text-emerald-400' : 'text-slate-400'
                }`}>
                  {stats.ordens_servico.por_prioridade[p] || 0}
                </p>
                <p className="text-xs text-slate-500">{p === 'A' ? 'Crítica' : p === 'B' ? 'Alta' : p === 'C' ? 'Média' : 'Baixa'}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Ativos Page
const AtivosPage = () => {
  const [ativos, setAtivos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterCriticidade, setFilterCriticidade] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  useEffect(() => {
    const status = searchParams.get('status');
    if (status) setFilterStatus(status);
  }, [searchParams]);
  
  useEffect(() => {
    const fetchAtivos = async () => {
      try {
        let url = '/ativos';
        const params = [];
        if (filterStatus) params.push(`status=${filterStatus}`);
        if (filterCriticidade) params.push(`criticidade=${filterCriticidade}`);
        if (params.length) url += '?' + params.join('&');
        
        const response = await api.get(url);
        setAtivos(response.data);
      } catch (error) {
        toast.error('Erro ao carregar ativos');
      } finally {
        setLoading(false);
      }
    };
    fetchAtivos();
  }, [filterStatus, filterCriticidade]);
  
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
      
      {/* Filters */}
      <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-2">
        <select 
          value={filterStatus} 
          onChange={(e) => setFilterStatus(e.target.value)}
          className="input-industrial px-3 py-2 text-sm"
        >
          <option value="">Todos Status</option>
          <option value="operacional">Operacional</option>
          <option value="falha">Em Falha</option>
          <option value="manutencao">Em Manutenção</option>
        </select>
        <select 
          value={filterCriticidade} 
          onChange={(e) => setFilterCriticidade(e.target.value)}
          className="input-industrial px-3 py-2 text-sm"
        >
          <option value="">Todas Criticidades</option>
          <option value="A">Crítica (A)</option>
          <option value="B">Alta (B)</option>
          <option value="C">Média (C)</option>
          <option value="D">Baixa (D)</option>
        </select>
      </div>
      
      {loading ? (
        <LoadingSkeleton rows={5} />
      ) : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((ativo) => (
            <div
              key={ativo.id}
              className="card-industrial p-4 cursor-pointer hover:border-slate-700 transition-all active:scale-[0.99]"
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
                    {ativo.fabricante && (
                      <p className="text-xs text-slate-500">{ativo.fabricante} {ativo.modelo}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <PriorityBadge priority={ativo.criticidade} />
                  <ChevronRight className="text-slate-600" />
                </div>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <StatusBadge status={ativo.status} size="sm" />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Box}
          title="Nenhum ativo encontrado"
          description="Não há ativos que correspondam aos filtros selecionados."
        />
      )}
    </div>
  );
};

// Ativo Detail Page (simplified for space)
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
        <div className="flex-1">
          <p className="font-mono text-emerald-400 text-sm">{ativo.tag}</p>
          <h1 className="text-xl text-slate-100">{ativo.nome}</h1>
        </div>
      </div>
      
      <div className="flex gap-2 flex-wrap">
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
        <h2 className="text-lg text-slate-300">Informações Técnicas</h2>
        
        <div className="grid grid-cols-2 gap-3 text-sm">
          {ativo.fabricante && (
            <div>
              <span className="text-slate-500 block">Fabricante</span>
              <span className="text-slate-200">{ativo.fabricante}</span>
            </div>
          )}
          {ativo.modelo && (
            <div>
              <span className="text-slate-500 block">Modelo</span>
              <span className="text-slate-200">{ativo.modelo}</span>
            </div>
          )}
          {ativo.potencia && (
            <div>
              <span className="text-slate-500 block">Potência</span>
              <span className="text-slate-200">{ativo.potencia}</span>
            </div>
          )}
          {ativo.rpm && (
            <div>
              <span className="text-slate-500 block">RPM</span>
              <span className="text-slate-200">{ativo.rpm}</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Recent History */}
      {(ativo.ordens_servico_recentes?.length > 0 || ativo.inspecoes_recentes?.length > 0) && (
        <div className="card-industrial p-4">
          <h2 className="text-lg text-slate-300 mb-3">Histórico Recente</h2>
          <div className="space-y-2">
            {ativo.ordens_servico_recentes?.slice(0, 3).map(os => (
              <div key={os.id} className="flex items-center justify-between p-2 bg-slate-800/50 rounded-lg">
                <div>
                  <p className="text-sm text-slate-200">OS #{os.numero}</p>
                  <p className="text-xs text-slate-500">{os.titulo}</p>
                </div>
                <StatusBadge status={os.status} size="sm" />
              </div>
            ))}
            {ativo.inspecoes_recentes?.slice(0, 2).map(insp => (
              <div key={insp.id} className="flex items-center justify-between p-2 bg-slate-800/50 rounded-lg">
                <div>
                  <p className="text-sm text-slate-200">Inspeção</p>
                  <p className="text-xs text-slate-500">{new Date(insp.created_at).toLocaleDateString('pt-BR')}</p>
                </div>
                <StatusBadge status={insp.status} size="sm" />
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Actions */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => navigate(`/inspecoes/nova?ativo=${ativo.id}`)}
          className="btn-primary rounded-lg py-4 flex items-center justify-center gap-2"
          data-testid="iniciar-inspecao-button"
        >
          <ClipboardCheck size={20} />
          <span>Inspeção</span>
        </button>
        <button
          onClick={() => navigate(`/os/nova?ativo=${ativo.id}`)}
          className="btn-secondary rounded-lg py-4 flex items-center justify-center gap-2"
          data-testid="criar-os-button"
        >
          <Wrench size={20} />
          <span>Nova OS</span>
        </button>
      </div>
    </div>
  );
};

// Ronda Page
const RondaPage = () => {
  const [areas, setAreas] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchAreas = async () => {
      try {
        const response = await api.get('/rondas');
        setAreas(response.data);
      } catch (error) {
        toast.error('Erro ao carregar áreas');
      } finally {
        setLoading(false);
      }
    };
    fetchAreas();
  }, []);
  
  if (loading) return <LoadingSkeleton rows={4} />;
  
  return (
    <div className="space-y-4" data-testid="ronda-page">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/')} className="p-2 bg-slate-800 rounded-lg md:hidden">
          <ArrowLeft size={22} className="text-slate-400" />
        </button>
        <h1 className="text-2xl text-slate-100">Modo Ronda</h1>
      </div>
      
      <p className="text-slate-400">Selecione uma área para iniciar a ronda de inspeção</p>
      
      <div className="space-y-3">
        {areas.map(({ area, total_ativos }) => (
          <div
            key={area.id}
            className="card-industrial p-4 cursor-pointer hover:border-emerald-500/50 transition-all"
            onClick={() => navigate(`/ronda/${area.id}`)}
            data-testid={`ronda-area-${area.nome}`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: area.cor || '#10b981' }}></div>
                <div>
                  <p className="text-slate-100 font-semibold">{area.nome}</p>
                  <p className="text-sm text-slate-500">{total_ativos} ativos</p>
                </div>
              </div>
              <ChevronRight className="text-slate-600" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Ronda Execução Page
const RondaExecucaoPage = () => {
  const { areaId } = useParams();
  const [ronda, setRonda] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchRonda = async () => {
      try {
        const response = await api.get(`/ronda/${areaId}`);
        setRonda(response.data);
      } catch (error) {
        toast.error('Erro ao carregar ronda');
        navigate('/ronda');
      } finally {
        setLoading(false);
      }
    };
    fetchRonda();
  }, [areaId, navigate]);
  
  if (loading) return <LoadingSkeleton rows={4} />;
  if (!ronda || ronda.ativos.length === 0) {
    return (
      <EmptyState
        icon={Target}
        title="Nenhum ativo nesta área"
        description="Esta área não possui ativos cadastrados para inspeção."
        action={() => navigate('/ronda')}
        actionLabel="Voltar"
      />
    );
  }
  
  const currentAtivo = ronda.ativos[currentIndex];
  
  const goNext = () => {
    if (currentIndex < ronda.ativos.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };
  
  const goPrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };
  
  return (
    <div className="space-y-4" data-testid="ronda-execucao-page">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/ronda')} className="p-2 bg-slate-800 rounded-lg">
            <ArrowLeft size={22} className="text-slate-400" />
          </button>
          <div>
            <p className="text-sm text-slate-500">Ronda: {ronda.area_nome}</p>
            <p className="text-slate-200">{currentIndex + 1} de {ronda.total_ativos}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500">Progresso</p>
          <p className="text-emerald-400 font-semibold">{Math.round((currentIndex / ronda.total_ativos) * 100)}%</p>
        </div>
      </div>
      
      {/* Progress bar */}
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div 
          className="h-full bg-emerald-500 transition-all duration-300"
          style={{ width: `${((currentIndex + 1) / ronda.total_ativos) * 100}%` }}
        ></div>
      </div>
      
      {/* Current Asset Card */}
      <div className="card-industrial p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="font-mono text-emerald-400">{currentAtivo.ativo.tag}</p>
            <h2 className="text-xl text-slate-100">{currentAtivo.ativo.nome}</h2>
          </div>
          <PriorityBadge priority={currentAtivo.ativo.criticidade} />
        </div>
        
        <div className="flex gap-2 mb-4">
          <StatusBadge status={currentAtivo.ativo.status} />
          {currentAtivo.inspecao_pendente && (
            <span className="px-2 py-1 bg-amber-500/10 text-amber-400 rounded text-xs">
              Inspeção pendente
            </span>
          )}
        </div>
        
        {currentAtivo.ativo.fabricante && (
          <p className="text-sm text-slate-500 mb-4">
            {currentAtivo.ativo.fabricante} - {currentAtivo.ativo.modelo}
          </p>
        )}
        
        <button
          onClick={() => navigate(`/inspecoes/nova?ativo=${currentAtivo.ativo.id}`)}
          className="btn-primary w-full rounded-lg py-4"
          data-testid="iniciar-inspecao-ronda"
        >
          <ClipboardCheck size={20} className="inline mr-2" />
          Iniciar Inspeção
        </button>
      </div>
      
      {/* Navigation */}
      <div className="flex gap-3">
        <button
          onClick={goPrev}
          disabled={currentIndex === 0}
          className="btn-secondary flex-1 rounded-lg disabled:opacity-50"
        >
          <ChevronLeft size={20} className="inline mr-1" />
          Anterior
        </button>
        <button
          onClick={goNext}
          disabled={currentIndex === ronda.ativos.length - 1}
          className="btn-secondary flex-1 rounded-lg disabled:opacity-50"
        >
          Próximo
          <ChevronRight size={20} className="inline ml-1" />
        </button>
      </div>
      
      {/* Quick list */}
      <div className="card-industrial p-4">
        <p className="text-sm text-slate-400 mb-2">Ativos na ronda</p>
        <div className="flex gap-2 overflow-x-auto hide-scrollbar">
          {ronda.ativos.map((item, idx) => (
            <button
              key={item.ativo.id}
              onClick={() => setCurrentIndex(idx)}
              className={`px-3 py-2 rounded-lg text-xs whitespace-nowrap ${
                idx === currentIndex 
                  ? 'bg-emerald-500 text-slate-950' 
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {item.ativo.tag}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

// Inspeções Page (simplified)
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
      ) : inspecoes.length > 0 ? (
        <div className="space-y-2">
          {inspecoes.map((inspecao) => (
            <div
              key={inspecao.id}
              className="card-industrial p-4 cursor-pointer hover:border-slate-700"
              onClick={() => navigate(`/inspecoes/${inspecao.id}`)}
              data-testid={`inspecao-card-${inspecao.id}`}
            >
              <div className="flex items-center justify-between">
                <div>
                  {inspecao.ativo && (
                    <p className="font-mono text-emerald-400 text-sm">{inspecao.ativo.tag}</p>
                  )}
                  <p className="text-slate-100">{inspecao.rota?.nome || 'Inspeção'}</p>
                  <p className="text-xs text-slate-500">
                    {new Date(inspecao.created_at).toLocaleDateString('pt-BR')} às {new Date(inspecao.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={inspecao.status} size="sm" />
                  <ChevronRight className="text-slate-600" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={ClipboardCheck}
          title="Nenhuma inspeção"
          description="Comece criando sua primeira inspeção."
          action={() => navigate('/inspecoes/nova')}
          actionLabel="Nova Inspeção"
        />
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
  const [searchParams] = useSearchParams();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ativosRes, rotasRes] = await Promise.all([
          api.get('/ativos'),
          api.get('/rotas-inspecao')
        ]);
        setAtivos(ativosRes.data);
        setRotas(rotasRes.data);
        
        const ativoParam = searchParams.get('ativo');
        if (ativoParam) {
          setSelectedAtivo(ativoParam);
        }
        
        // Auto-select first route if only one
        if (rotasRes.data.length === 1) {
          setSelectedRota(rotasRes.data[0].id);
        }
      } catch (error) {
        toast.error('Erro ao carregar dados');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [searchParams]);
  
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
  
  const selectedRotaData = rotas.find(r => r.id === selectedRota);
  
  return (
    <div className="space-y-4" data-testid="nova-inspecao-page">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 bg-slate-800 rounded-lg">
          <ArrowLeft size={22} className="text-slate-400" />
        </button>
        <h1 className="text-xl text-slate-100">Nova Inspeção</h1>
      </div>
      
      <div className="card-industrial p-4 space-y-4">
        <div>
          <label className="block text-sm text-slate-400 mb-2">Ativo *</label>
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
          <label className="block text-sm text-slate-400 mb-2">Rota de Inspeção *</label>
          <select
            value={selectedRota}
            onChange={(e) => setSelectedRota(e.target.value)}
            className="input-industrial w-full px-4"
            data-testid="select-rota"
          >
            <option value="">Selecione uma rota...</option>
            {rotas.map((rota) => (
              <option key={rota.id} value={rota.id}>
                {rota.nome} ({rota.itens?.length || 0} itens)
              </option>
            ))}
          </select>
        </div>
        
        {selectedRotaData && (
          <div className="p-3 bg-slate-800/50 rounded-lg">
            <p className="text-sm text-slate-300 mb-2">{selectedRotaData.descricao || 'Checklist de inspeção'}</p>
            <div className="flex gap-4 text-xs text-slate-500">
              <span><Clock size={14} className="inline mr-1" /> ~{selectedRotaData.tempo_estimado_minutos || 15} min</span>
              <span><FileText size={14} className="inline mr-1" /> {selectedRotaData.itens?.length || 0} itens</span>
            </div>
          </div>
        )}
        
        <button
          onClick={handleSubmit}
          disabled={submitting || !selectedAtivo || !selectedRota}
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
  const [currentItem, setCurrentItem] = useState(0);
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const inspecaoRes = await api.get(`/inspecoes/${id}`);
        setInspecao(inspecaoRes.data);
        
        if (inspecaoRes.data.rota) {
          setRota(inspecaoRes.data.rota);
          
          // Initialize respostas
          const initial = {};
          inspecaoRes.data.rota.itens?.forEach(item => {
            initial[item.id] = { valor: null, conforme: true, observacao: '' };
          });
          setRespostas(initial);
        }
      } catch (error) {
        toast.error('Erro ao carregar inspeção');
        navigate('/inspecoes');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, navigate]);
  
  const handleResposta = (itemId, field, value) => {
    setRespostas(prev => ({
      ...prev,
      [itemId]: { ...prev[itemId], [field]: value }
    }));
  };
  
  const handleFinalizar = async () => {
    if (!rota) return;
    
    const respostasArray = rota.itens.map(item => ({
      item_id: item.id,
      valor: respostas[item.id]?.valor,
      conforme: respostas[item.id]?.conforme ?? true,
      observacao: respostas[item.id]?.observacao || ''
    }));
    
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
        toast.warning(`Inspeção concluída com ${response.data.total_nao_conformes} pendência(s). ${response.data.os_geradas.length} OS gerada(s) automaticamente.`);
      } else {
        toast.success(`Inspeção concluída em ${response.data.duracao_minutos || 0} minutos!`);
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
        <div className="card-industrial p-6 text-center">
          <StatusBadge status={inspecao.status} />
          <p className="text-slate-400 mt-4">Esta inspeção já foi finalizada</p>
          {inspecao.duracao_minutos && (
            <p className="text-sm text-slate-500 mt-2">Duração: {inspecao.duracao_minutos} minutos</p>
          )}
        </div>
      </div>
    );
  }
  
  const totalItems = rota.itens.length;
  const answeredItems = Object.values(respostas).filter(r => r.valor !== null).length;
  
  return (
    <div className="space-y-4 pb-24" data-testid="inspecao-execucao-page">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/inspecoes')} className="p-2 bg-slate-800 rounded-lg">
            <ArrowLeft size={22} className="text-slate-400" />
          </button>
          <div>
            <p className="font-mono text-emerald-400 text-sm">{inspecao.ativo?.tag}</p>
            <h1 className="text-lg text-slate-100">{rota.nome}</h1>
          </div>
        </div>
        <div className="text-right">
          <p className="text-emerald-400 font-semibold">{answeredItems}/{totalItems}</p>
          <p className="text-xs text-slate-500">respondidos</p>
        </div>
      </div>
      
      {/* Progress */}
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div 
          className="h-full bg-emerald-500 transition-all"
          style={{ width: `${(answeredItems / totalItems) * 100}%` }}
        ></div>
      </div>
      
      {/* Checklist Items */}
      <div className="space-y-3">
        {rota.itens.map((item, idx) => (
          <div key={item.id} className={`card-industrial p-4 ${respostas[item.id]?.valor !== null ? 'border-emerald-500/30' : ''}`} data-testid={`checklist-item-${idx}`}>
            <div className="flex items-start gap-3">
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                respostas[item.id]?.valor !== null 
                  ? 'bg-emerald-500 text-slate-950' 
                  : 'bg-slate-800 text-slate-400'
              }`}>
                {idx + 1}
              </span>
              <div className="flex-1">
                <p className="text-slate-200">{item.descricao}</p>
                {item.categoria && <span className="text-xs text-slate-500">{item.categoria}</span>}
                {item.obrigatorio && <span className="text-xs text-red-400 ml-2">*</span>}
                
                {/* Response Input */}
                <div className="mt-3">
                  {item.tipo_resposta === 'boolean' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          handleResposta(item.id, 'valor', true);
                          handleResposta(item.id, 'conforme', true);
                        }}
                        className={`flex-1 py-3 rounded-lg border transition-all ${
                          respostas[item.id]?.valor === true
                            ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400'
                            : 'border-slate-700 text-slate-400 hover:border-slate-600'
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
                        className={`flex-1 py-3 rounded-lg border transition-all ${
                          respostas[item.id]?.valor === false
                            ? 'bg-red-500/20 border-red-500 text-red-400'
                            : 'border-slate-700 text-slate-400 hover:border-slate-600'
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
                      <div className="flex gap-2">
                        <input
                          type="number"
                          step="0.1"
                          placeholder={item.valor_esperado ? `Esperado: ${item.valor_esperado}` : 'Valor'}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value);
                            handleResposta(item.id, 'valor', val);
                            if (item.tolerancia_min !== null && item.tolerancia_max !== null) {
                              handleResposta(item.id, 'conforme', val >= item.tolerancia_min && val <= item.tolerancia_max);
                            }
                          }}
                          className="input-industrial flex-1 px-4"
                          data-testid={`item-${idx}-numero`}
                        />
                        {item.unidade && (
                          <span className="input-industrial px-4 flex items-center text-slate-400 min-w-[60px]">
                            {item.unidade}
                          </span>
                        )}
                      </div>
                      {item.tolerancia_min !== null && (
                        <p className="text-xs text-slate-500 mt-1">
                          Tolerância: {item.tolerancia_min} - {item.tolerancia_max} {item.unidade}
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
                  
                  {item.tipo_resposta === 'selecao' && item.opcoes && (
                    <select
                      onChange={(e) => handleResposta(item.id, 'valor', e.target.value)}
                      className="input-industrial w-full px-4"
                      data-testid={`item-${idx}-selecao`}
                    >
                      <option value="">Selecione...</option>
                      {item.opcoes.map((op, i) => (
                        <option key={i} value={op}>{op}</option>
                      ))}
                    </select>
                  )}
                </div>
                
                {/* Observation for NOK */}
                {respostas[item.id]?.valor === false && item.tipo_resposta === 'boolean' && (
                  <div className="mt-3">
                    <textarea
                      placeholder="Descreva a falha encontrada (obrigatório para NOK)"
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
      <div className="fixed bottom-16 left-0 right-0 p-4 bg-slate-950/95 backdrop-blur-sm border-t border-slate-800 md:bottom-0">
        <button
          onClick={handleFinalizar}
          disabled={submitting}
          className="btn-primary w-full rounded-lg"
          data-testid="finalizar-inspecao-button"
        >
          {submitting ? 'Finalizando...' : `Finalizar Inspeção (${answeredItems}/${totalItems})`}
        </button>
      </div>
    </div>
  );
};

// OS Page
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
          { value: 'pausada', label: 'Pausadas' },
          { value: 'concluida', label: 'Concluídas' },
        ].map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-4 py-2 rounded-lg whitespace-nowrap transition-all ${
              filter === f.value
                ? 'bg-emerald-500 text-slate-950 font-semibold'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
            data-testid={`filter-${f.value}`}
          >
            {f.label}
          </button>
        ))}
      </div>
      
      {loading ? (
        <LoadingSkeleton rows={5} />
      ) : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((os) => (
            <div
              key={os.id}
              className="card-industrial p-4 cursor-pointer hover:border-slate-700 transition-all"
              onClick={() => navigate(`/os/${os.id}`)}
              data-testid={`os-card-${os.numero}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-mono text-emerald-400 text-sm">#{os.numero}</p>
                    {os.ativo && (
                      <span className="text-xs text-slate-500">{os.ativo.tag}</span>
                    )}
                  </div>
                  <p className="text-slate-100">{os.titulo}</p>
                  {os.tecnico && (
                    <p className="text-xs text-slate-500 mt-1">
                      <User size={12} className="inline mr-1" />
                      {os.tecnico.nome}
                    </p>
                  )}
                </div>
                <ChevronRight className="text-slate-600" />
              </div>
              <div className="mt-2 flex items-center gap-2 flex-wrap">
                <StatusBadge status={os.status} size="sm" />
                <PriorityBadge priority={os.prioridade} />
                <span className="text-xs text-slate-500 capitalize">{os.tipo}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Wrench}
          title="Nenhuma OS encontrada"
          description="Não há ordens de serviço com este filtro."
        />
      )}
    </div>
  );
};

// OS Detail Page
const OSDetailPage = () => {
  const { id } = useParams();
  const [os, setOs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const osRes = await api.get(`/ordens-servico/${id}`);
        setOs(osRes.data);
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
      const result = await api.post(`/ordens-servico/${id}/finalizar`, []);
      toast.success(`OS finalizada! Tempo efetivo: ${result.data.tempo_efetivo_minutos || 0} minutos`);
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
        <div className="flex-1">
          <p className="font-mono text-emerald-400 text-sm">#{os.numero}</p>
          <h1 className="text-xl text-slate-100">{os.titulo}</h1>
        </div>
      </div>
      
      <div className="flex gap-2 flex-wrap">
        <StatusBadge status={os.status} />
        <PriorityBadge priority={os.prioridade} />
        <span className="px-2 py-1 bg-slate-800 rounded text-xs text-slate-300 capitalize">{os.tipo}</span>
      </div>
      
      {/* Ativo Info */}
      {os.ativo && (
        <div 
          className="card-industrial p-4 cursor-pointer hover:border-slate-700"
          onClick={() => navigate(`/ativos/${os.ativo.id}`)}
          data-testid="os-ativo-card"
        >
          <p className="text-xs text-slate-500 mb-1">Ativo</p>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-mono text-emerald-400 text-sm">{os.ativo.tag}</p>
              <p className="text-slate-200">{os.ativo.nome}</p>
            </div>
            <ChevronRight className="text-slate-600" />
          </div>
        </div>
      )}
      
      {/* Tecnico */}
      {os.tecnico && (
        <div className="card-industrial p-4">
          <p className="text-xs text-slate-500 mb-1">Técnico Responsável</p>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <User size={20} className="text-emerald-400" />
            </div>
            <div>
              <p className="text-slate-200">{os.tecnico.nome}</p>
              <p className="text-xs text-slate-500">{os.tecnico.email}</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Description */}
      {os.descricao && (
        <div className="card-industrial p-4">
          <p className="text-xs text-slate-500 mb-1">Descrição</p>
          <p className="text-slate-200 whitespace-pre-wrap">{os.descricao}</p>
        </div>
      )}
      
      {/* Dates */}
      <div className="card-industrial p-4 space-y-2 text-sm">
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
          <div className="flex justify-between border-t border-slate-800 pt-2 mt-2">
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
              className="btn-primary w-full rounded-lg flex items-center justify-center gap-2"
              data-testid="iniciar-os-button"
            >
              <Play size={20} />
              {updating ? 'Atualizando...' : 'Iniciar OS'}
            </button>
          )}
          
          {os.status === 'iniciada' && (
            <>
              <button
                onClick={handleFinalizar}
                disabled={updating}
                className="btn-primary w-full rounded-lg flex items-center justify-center gap-2"
                data-testid="finalizar-os-button"
              >
                <CheckCircle size={20} />
                {updating ? 'Finalizando...' : 'Finalizar OS'}
              </button>
              <button
                onClick={() => handleStatusChange('pausada')}
                disabled={updating}
                className="btn-secondary w-full rounded-lg flex items-center justify-center gap-2"
                data-testid="pausar-os-button"
              >
                <Pause size={20} />
                Pausar OS
              </button>
            </>
          )}
          
          {os.status === 'pausada' && (
            <button
              onClick={() => handleStatusChange('iniciada')}
              disabled={updating}
              className="btn-primary w-full rounded-lg flex items-center justify-center gap-2"
              data-testid="retomar-os-button"
            >
              <Play size={20} />
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
  const [tecnicos, setTecnicos] = useState([]);
  const [formData, setFormData] = useState({
    ativo_id: '',
    titulo: '',
    descricao: '',
    tipo: 'manual',
    prioridade: 'C',
    tecnico_id: ''
  });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ativosRes, tecnicosRes] = await Promise.all([
          api.get('/ativos'),
          api.get('/users/tecnicos')
        ]);
        setAtivos(ativosRes.data);
        setTecnicos(tecnicosRes.data);
        
        const ativoParam = searchParams.get('ativo');
        if (ativoParam) {
          setFormData(prev => ({ ...prev, ativo_id: ativoParam }));
        }
      } catch (error) {
        toast.error('Erro ao carregar dados');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [searchParams]);
  
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
        <button onClick={() => navigate(-1)} className="p-2 bg-slate-800 rounded-lg">
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
          
          <div>
            <label className="block text-sm text-slate-400 mb-2">Técnico Responsável</label>
            <select
              value={formData.tecnico_id}
              onChange={(e) => setFormData({ ...formData, tecnico_id: e.target.value })}
              className="input-industrial w-full px-4"
              data-testid="os-tecnico"
            >
              <option value="">Não atribuído</option>
              {tecnicos.map((tec) => (
                <option key={tec.id} value={tec.id}>
                  {tec.nome}
                </option>
              ))}
            </select>
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

// Scanner Page
const ScannerPage = () => {
  const [showScanner, setShowScanner] = useState(false);
  const [manualCode, setManualCode] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  
  const handleScan = async (code) => {
    setShowScanner(false);
    setLoading(true);
    
    try {
      const response = await api.get(`/ativos/qr/${code}`);
      toast.success(`Ativo encontrado: ${response.data.tag}`);
      navigate(`/ativos/${response.data.id}`);
    } catch (error) {
      toast.error('Ativo não encontrado com este QR Code');
    } finally {
      setLoading(false);
    }
  };
  
  const handleManualSearch = async () => {
    if (!manualCode.trim()) return;
    
    setLoading(true);
    try {
      // Try QR code first
      try {
        const response = await api.get(`/ativos/qr/${manualCode}`);
        navigate(`/ativos/${response.data.id}`);
        return;
      } catch {}
      
      // Try TAG
      const response = await api.get(`/ativos/tag/${manualCode}`);
      navigate(`/ativos/${response.data.id}`);
    } catch (error) {
      toast.error('Ativo não encontrado');
    } finally {
      setLoading(false);
    }
  };
  
  if (showScanner) {
    return <QRScanner onScan={handleScan} onClose={() => setShowScanner(false)} />;
  }
  
  return (
    <div className="space-y-6" data-testid="scanner-page">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 bg-slate-800 rounded-lg">
          <ArrowLeft size={22} className="text-slate-400" />
        </button>
        <h1 className="text-xl text-slate-100">Identificar Ativo</h1>
      </div>
      
      {/* Camera Button */}
      <button
        onClick={() => setShowScanner(true)}
        className="w-full card-industrial p-8 flex flex-col items-center justify-center gap-4 hover:border-emerald-500/50 transition-all"
        data-testid="open-scanner-button"
      >
        <div className="w-24 h-24 rounded-full bg-emerald-500/10 flex items-center justify-center">
          <Camera size={48} className="text-emerald-400" />
        </div>
        <div className="text-center">
          <p className="text-lg text-slate-200">Escanear QR Code</p>
          <p className="text-sm text-slate-500">Aponte a câmera para o código do ativo</p>
        </div>
      </button>
      
      <div className="flex items-center gap-4">
        <div className="flex-1 h-px bg-slate-800"></div>
        <span className="text-slate-500 text-sm">ou</span>
        <div className="flex-1 h-px bg-slate-800"></div>
      </div>
      
      {/* Manual Input */}
      <div className="card-industrial p-4 space-y-4">
        <p className="text-sm text-slate-400">Buscar por código ou TAG</p>
        <div className="flex gap-2">
          <input
            type="text"
            value={manualCode}
            onChange={(e) => setManualCode(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === 'Enter' && handleManualSearch()}
            placeholder="Ex: BOM-001"
            className="input-industrial flex-1 px-4 font-mono"
            data-testid="manual-qr-input"
          />
          <button
            onClick={handleManualSearch}
            disabled={loading || !manualCode.trim()}
            className="btn-primary rounded-lg px-6"
            data-testid="search-qr-button"
          >
            {loading ? <RefreshCw size={20} className="animate-spin" /> : <Search size={20} />}
          </button>
        </div>
      </div>
    </div>
  );
};

// Estoque Page
const EstoquePage = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCritico, setShowCritico] = useState(false);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  useEffect(() => {
    const critico = searchParams.get('critico');
    if (critico === 'true') setShowCritico(true);
  }, [searchParams]);
  
  useEffect(() => {
    const fetchEstoque = async () => {
      try {
        const url = showCritico ? '/estoque?critico=true' : '/estoque';
        const response = await api.get(url);
        setItems(response.data);
      } catch (error) {
        toast.error('Erro ao carregar estoque');
      } finally {
        setLoading(false);
      }
    };
    fetchEstoque();
  }, [showCritico]);
  
  const filtered = items.filter(i =>
    i.nome.toLowerCase().includes(search.toLowerCase()) ||
    i.sku.toLowerCase().includes(search.toLowerCase())
  );
  
  return (
    <div className="space-y-4" data-testid="estoque-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl text-slate-100">Estoque</h1>
        <button className="p-2 bg-emerald-500 rounded-lg">
          <Plus size={22} className="text-slate-950" />
        </button>
      </div>
      
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={20} />
        <input
          type="text"
          placeholder="Buscar por nome ou SKU..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-industrial w-full pl-10 pr-4"
        />
      </div>
      
      <div className="flex gap-2">
        <button
          onClick={() => setShowCritico(false)}
          className={`px-4 py-2 rounded-lg ${!showCritico ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 text-slate-300'}`}
        >
          Todos
        </button>
        <button
          onClick={() => setShowCritico(true)}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 ${showCritico ? 'bg-amber-500 text-slate-950' : 'bg-slate-800 text-slate-300'}`}
        >
          <AlertTriangle size={16} />
          Crítico
        </button>
      </div>
      
      {loading ? (
        <LoadingSkeleton rows={5} />
      ) : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((item) => {
            const isCritico = item.saldo <= item.estoque_minimo;
            return (
              <div
                key={item.id}
                className={`card-industrial p-4 ${isCritico ? 'border-amber-500/50' : ''}`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-mono text-emerald-400 text-sm">{item.sku}</p>
                    <p className="text-slate-200">{item.nome}</p>
                    {item.categoria && (
                      <p className="text-xs text-slate-500">{item.categoria}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className={`text-xl font-bold ${isCritico ? 'text-amber-400' : 'text-slate-200'}`}>
                      {item.saldo}
                    </p>
                    <p className="text-xs text-slate-500">{item.unidade}</p>
                  </div>
                </div>
                {isCritico && (
                  <div className="mt-2 flex items-center gap-2 text-amber-400 text-xs">
                    <AlertTriangle size={14} />
                    Abaixo do mínimo ({item.estoque_minimo})
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={Package}
          title="Nenhum item encontrado"
          description="Não há itens no estoque com este filtro."
        />
      )}
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
        <button 
          onClick={() => navigate('/minhas-os')}
          className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-800/50"
        >
          <div className="flex items-center gap-3">
            <Wrench size={20} className="text-slate-400" />
            <span className="text-slate-200">Minhas OS</span>
          </div>
          <ChevronRight className="text-slate-600" />
        </button>
        
        <button className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-800/50">
          <div className="flex items-center gap-3">
            <Settings size={20} className="text-slate-400" />
            <span className="text-slate-200">Configurações</span>
          </div>
          <ChevronRight className="text-slate-600" />
        </button>
        
        <button 
          onClick={() => { logout(); navigate('/login'); }}
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
        <div className="text-center">
          <Cog size={48} className="text-emerald-400 animate-spin mx-auto" />
          <p className="text-slate-400 mt-4">Carregando...</p>
        </div>
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
    <div className="min-h-screen bg-slate-950 flex">
      <Sidebar />
      <div className="flex-1 flex flex-col min-h-screen">
        <OfflineBanner />
        <main className="flex-1 pb-20 md:pb-4 px-4 pt-4 max-w-4xl mx-auto w-full">
          {children}
        </main>
        <BottomNav />
      </div>
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
          
          <Route path="/" element={<ProtectedRoute><AppLayout><DashboardPage /></AppLayout></ProtectedRoute>} />
          <Route path="/ativos" element={<ProtectedRoute><AppLayout><AtivosPage /></AppLayout></ProtectedRoute>} />
          <Route path="/ativos/:id" element={<ProtectedRoute><AppLayout><AtivoDetailPage /></AppLayout></ProtectedRoute>} />
          <Route path="/inspecoes" element={<ProtectedRoute><AppLayout><InspecoesPage /></AppLayout></ProtectedRoute>} />
          <Route path="/inspecoes/nova" element={<ProtectedRoute><AppLayout><NovaInspecaoPage /></AppLayout></ProtectedRoute>} />
          <Route path="/inspecoes/:id" element={<ProtectedRoute><AppLayout><InspecaoExecucaoPage /></AppLayout></ProtectedRoute>} />
          <Route path="/ronda" element={<ProtectedRoute><AppLayout><RondaPage /></AppLayout></ProtectedRoute>} />
          <Route path="/ronda/:areaId" element={<ProtectedRoute><AppLayout><RondaExecucaoPage /></AppLayout></ProtectedRoute>} />
          <Route path="/os" element={<ProtectedRoute><AppLayout><OSPage /></AppLayout></ProtectedRoute>} />
          <Route path="/os/nova" element={<ProtectedRoute><AppLayout><NovaOSPage /></AppLayout></ProtectedRoute>} />
          <Route path="/os/:id" element={<ProtectedRoute><AppLayout><OSDetailPage /></AppLayout></ProtectedRoute>} />
          <Route path="/scanner" element={<ProtectedRoute><AppLayout><ScannerPage /></AppLayout></ProtectedRoute>} />
          <Route path="/estoque" element={<ProtectedRoute><AppLayout><EstoquePage /></AppLayout></ProtectedRoute>} />
          <Route path="/perfil" element={<ProtectedRoute><AppLayout><ProfilePage /></AppLayout></ProtectedRoute>} />
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster position="top-center" richColors />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
