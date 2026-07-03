import { useState, useEffect, createContext, useContext, useRef, Fragment } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, useParams, useSearchParams } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { QRCodeSVG } from "qrcode.react";
import { 
  Home, ClipboardCheck, Box, User, Settings, LogOut, 
  AlertTriangle, CheckCircle, XCircle, Clock, Wrench, Package,
  ChevronRight, ChevronLeft, ChevronDown, Search, Plus, QrCode, Camera, ArrowLeft,
  Activity, TrendingUp, TrendingDown, BarChart3, Gauge, Bell, Menu, X, Play, Pause,
  MapPin, Calendar, FileText, Image, Upload, RefreshCw, Wifi, WifiOff,
  Zap, Target, Layers, Filter, MoreVertical, Eye, Edit, Trash2, Save,
  Phone, Mail, Building, Hash, Thermometer, Volume2, Droplet, Cog,
  DollarSign, Percent, AlertCircle, PieChart, Users, Warehouse, Tag,
  Shield, CheckSquare, Square, ChevronUp, LayoutDashboard, List, Download, Lock, Edit3, Copy, Factory,
  Building2, Palette, BookOpen, CheckCircle2, Sparkles, Send
} from "lucide-react";
import { BACKEND_URL, API, AuthContext, useAuth, api } from "@/lib/api";
import { BrandingProvider, useBranding } from "@/lib/branding";
import { queueOperation, getPendingCount, syncPendingOperations, registerServiceWorker, cacheData, getCachedData } from "@/lib/offlineQueue";
import axios from "axios";

// Register PWA Service Worker
registerServiceWorker();

// Global error normalizer — handles Pydantic validation arrays, objects, and strings
const FIELD_LABEL_MAP = {
  nome: 'Nome', ativo_id: 'Ativo', tipo: 'Tipo', disciplina: 'Disciplina',
  titulo: 'Título', descricao: 'Descrição', prioridade: 'Prioridade', email: 'Email',
  password: 'Senha', frequencia: 'Frequência', responsavel_id: 'Responsável',
  tipo_equipamento: 'Tipo Equipamento', categoria: 'Categoria', sector_id: 'Área',
  perguntas: 'Perguntas', checklist: 'Checklist',
};

const normalizeError = (error) => {
  const detail = error?.response?.data?.detail;
  if (!detail) return error?.message || 'Erro desconhecido';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map(d => {
      if (typeof d === 'object') {
        const loc = d.loc || [];
        const fieldName = loc[loc.length - 1];
        const label = FIELD_LABEL_MAP[fieldName] || fieldName;
        const msg = d.msg || '';
        if (fieldName && msg.toLowerCase().includes('required')) {
          return `Campo '${label}' é obrigatório`;
        }
        if (fieldName) return `${label}: ${msg}`;
        return msg || JSON.stringify(d);
      }
      return String(d);
    }).join('; ');
  }
  if (typeof detail === 'object') return detail.msg || JSON.stringify(detail);
  return String(detail);
};

// ============== COMPONENTS ==============

// Modal Component
const Modal = ({ isOpen, onClose, title, children, size = 'md' }) => {
  if (!isOpen) return null;
  
  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-2xl',
    lg: 'max-w-4xl',
    xl: 'max-w-6xl'
  };
  
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" data-testid="modal">
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose}></div>
      <div className="flex min-h-full items-center justify-center p-4">
        <div className={`relative w-full ${sizeClasses[size]} bg-slate-900 border border-slate-700 rounded-xl shadow-2xl animate-scaleIn`}>
          <div className="flex items-center justify-between p-4 border-b border-slate-800">
            <h2 className="text-xl font-bold text-slate-100">{title}</h2>
            <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
              <X size={20} className="text-slate-400" />
            </button>
          </div>
          <div className="p-4 max-h-[70vh] overflow-y-auto custom-scrollbar">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

// Form Input Component
const FormInput = ({ label, required, error, children }) => (
  <div className="space-y-1">
    <label className="block text-sm font-medium text-slate-400">
      {label} {required && <span className="text-red-400">*</span>}
    </label>
    {children}
    {error && <p className="text-xs text-red-400">{error}</p>}
  </div>
);

// Select Component
const Select = ({ value, onChange, options, placeholder, className = "" }) => (
  <select
    value={value}
    onChange={(e) => onChange(e.target.value)}
    className={`input-industrial w-full px-4 ${className}`}
  >
    <option value="">{placeholder || "Selecione..."}</option>
    {options.map((opt) => (
      <option key={opt.value} value={opt.value}>{opt.label}</option>
    ))}
  </select>
);

// Status Badge
const StatusBadge = ({ status, size = 'md' }) => {
  const config = {
    // Novo ciclo de vida OS
    solicitada: { class: 'bg-blue-500/10 text-blue-400 border-blue-500/30', label: 'Solicitada', icon: Clock },
    em_analise: { class: 'bg-purple-500/10 text-purple-400 border-purple-500/30', label: 'Em Análise', icon: Search },
    aguardando_aprovacao: { class: 'bg-amber-500/10 text-amber-400 border-amber-500/30', label: 'Aguard. Aprovação', icon: Shield },
    aguardando_material: { class: 'bg-orange-500/10 text-orange-400 border-orange-500/30', label: 'Aguard. Material', icon: Package },
    programada: { class: 'bg-purple-500/10 text-purple-400 border-purple-500/30', label: 'Programada', icon: Calendar },
    disponivel: { class: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30', label: 'Disponível', icon: CheckCircle },
    em_execucao: { class: 'bg-brand-10 text-emerald-400 border-emerald-500/30', label: 'Em Execução', icon: Play },
    pausada: { class: 'bg-amber-500/10 text-amber-400 border-amber-500/30', label: 'Pausada', icon: Pause },
    concluida: { class: 'bg-brand-10 text-emerald-400 border-emerald-500/30', label: 'Concluída', icon: CheckCircle },
    encerrada: { class: 'bg-slate-500/10 text-slate-400 border-slate-500/30', label: 'Encerrada', icon: Lock },
    cancelada: { class: 'bg-red-500/10 text-red-400 border-red-500/30', label: 'Cancelada', icon: XCircle },
    // Backward compat
    aberta: { class: 'bg-blue-500/10 text-blue-400 border-blue-500/30', label: 'Aberta', icon: Clock },
    planejada: { class: 'bg-purple-500/10 text-purple-400 border-purple-500/30', label: 'Planejada', icon: Calendar },
    // Inspeções
    pendente: { class: 'bg-amber-500/10 text-amber-400 border-amber-500/30', label: 'Pendente', icon: Clock },
    em_andamento: { class: 'bg-blue-500/10 text-blue-400 border-blue-500/30', label: 'Em Andamento', icon: Activity },
    com_pendencias: { class: 'bg-red-500/10 text-red-400 border-red-500/30', label: 'Com Pendências', icon: AlertTriangle },
    conforme: { class: 'bg-brand-10 text-emerald-400 border-emerald-500/30', label: 'Conforme', icon: CheckCircle },
    nao_conforme: { class: 'bg-red-500/10 text-red-400 border-red-500/30', label: 'Não Conforme', icon: XCircle },
  };
  
  const c = config[status] || { class: 'bg-slate-500/10 text-slate-400 border-slate-500/30', label: status, icon: Clock };
  const Icon = c.icon;
  
  return (
    <span className={`${c.class} border inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium`}>
      <Icon size={size === 'sm' ? 12 : 14} />
      {c.label}
    </span>
  );
};

// Priority Badge
const PriorityBadge = ({ priority }) => {
  const config = {
    critica: { class: 'bg-red-500/20 border-red-500 text-red-400', label: 'Crítica' },
    emergencia: { class: 'bg-red-500/20 border-red-500 text-red-400', label: 'Emergência' },
    alta: { class: 'bg-amber-500/20 border-amber-500 text-amber-400', label: 'Alta' },
    media: { class: 'bg-emerald-500/20 border-emerald-500 text-emerald-400', label: 'Média' },
    baixa: { class: 'bg-slate-500/20 border-slate-500 text-slate-400', label: 'Baixa' },
  };
  const c = config[priority] || config.media;
  return <span className={`${c.class} border px-2 py-1 rounded text-xs font-medium`}>{c.label}</span>;
};

// KPI Card
const KPICard = ({ value, label, icon: Icon, color = 'brand', subtitle, trend }) => {
  const colors = {
    brand: 'text-brand bg-brand-10',
    amber: 'text-amber-400 bg-amber-500/10',
    red: 'text-red-400 bg-red-500/10',
    blue: 'text-blue-400 bg-blue-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
  };
  
  return (
    <div className="glass-card p-4 hover:border-slate-600 transition-all group">
      <div className="flex items-start justify-between">
        <div>
          <p className={`text-2xl font-bold ${colors[color].split(' ')[0]}`}>{value}</p>
          <p className="text-sm text-slate-400 mt-1">{label}</p>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
        </div>
        <div className={`p-2 rounded-lg ${colors[color]} group-hover:scale-110 transition-transform`}>
          <Icon size={20} />
        </div>
      </div>
      {trend !== undefined && (
        <div className={`flex items-center gap-1 mt-2 text-xs ${trend >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
          {trend >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          <span>{trend >= 0 ? '+' : ''}{trend}% vs mês anterior</span>
        </div>
      )}
    </div>
  );
};

// Loading
const Loading = ({ rows = 3 }) => (
  <div className="space-y-3">
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="glass-card p-4 animate-pulse">
        <div className="h-4 bg-slate-700 rounded w-3/4 mb-2"></div>
        <div className="h-3 bg-slate-700 rounded w-1/2"></div>
      </div>
    ))}
  </div>
);

// Empty State
const EmptyState = ({ icon: Icon, title, description, action, actionLabel }) => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4">
      <Icon size={32} className="text-slate-500" />
    </div>
    <h3 className="text-lg text-slate-300 font-semibold mb-2">{title}</h3>
    <p className="text-slate-500 max-w-sm mb-4">{description}</p>
    {action && <button onClick={action} className="btn-primary">{actionLabel}</button>}
  </div>
);

// Confirm Dialog
const ConfirmDialog = ({ isOpen, onClose, onConfirm, title, message, confirmText = "Confirmar", danger = false }) => {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose}></div>
      <div className="relative bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-md w-full mx-4 animate-scaleIn">
        <h3 className="text-lg font-bold text-slate-100 mb-2">{title}</h3>
        <p className="text-slate-400 mb-6">{message}</p>
        <div className="flex gap-3 justify-end">
          <button onClick={onClose} className="btn-secondary">Cancelar</button>
          <button onClick={onConfirm} className={danger ? "btn-danger" : "btn-primary"}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};


// ============== NETWORK STATUS + SYNC ==============
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

  // Auto-sync when coming back online
  useEffect(() => {
    if (isOnline && pendingCount > 0) {
      const doSync = async () => {
        setSyncing(true);
        try {
          const result = await syncPendingOperations(api);
          if (result.synced > 0) toast.success(`${result.synced} operação(ões) sincronizada(s)`);
          if (result.failed > 0) toast.error(`${result.failed} operação(ões) falharam`);
          const c = await getPendingCount();
          setPendingCount(c);
        } catch {}
        setSyncing(false);
      };
      doSync();
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

// ============== CAMERA CAPTURE ==============
const CameraCapture = ({ onCapture, onClose }) => {
  const videoRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const startCamera = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
        });
        setStream(mediaStream);
        if (videoRef.current) videoRef.current.srcObject = mediaStream;
      } catch (err) {
        setError('Não foi possível acessar a câmera. Verifique as permissões.');
      }
    };
    startCamera();
    return () => { if (stream) stream.getTracks().forEach(t => t.stop()); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const takePhoto = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    canvas.getContext('2d').drawImage(videoRef.current, 0, 0);
    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `foto_${Date.now()}.jpg`, { type: 'image/jpeg' });
        onCapture(file);
      }
    }, 'image/jpeg', 0.85);
    if (stream) stream.getTracks().forEach(t => t.stop());
  };

  if (error) {
    return (
      <div className="fixed inset-0 z-[70] bg-black flex items-center justify-center">
        <div className="text-center p-6">
          <AlertCircle size={48} className="text-red-400 mx-auto mb-4" />
          <p className="text-white mb-4">{error}</p>
          <button onClick={onClose} className="btn-secondary">Fechar</button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-[70] bg-black flex flex-col" data-testid="camera-capture">
      <video ref={videoRef} autoPlay playsInline className="flex-1 object-cover" />
      <div className="absolute bottom-0 left-0 right-0 p-6 flex items-center justify-center gap-6 bg-gradient-to-t from-black/80">
        <button onClick={onClose} className="p-3 rounded-full bg-white/20 text-white" data-testid="camera-close">
          <X size={24} />
        </button>
        <button onClick={takePhoto} className="w-16 h-16 rounded-full bg-white border-4 border-white/30 hover:bg-gray-200 transition-all" data-testid="camera-shutter" />
        <div className="w-12" />
      </div>
    </div>
  );
};


// Notification Bell
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
      } catch (error) {}
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
  
  const markAllRead = async () => {
    await api.put('/notificacoes/marcar-todas-lidas');
    setCount(0);
    setNotifications([]);
  };
  
  const getNotifIcon = (tipo) => {
    const icons = {
      os_criada: Wrench,
      os_atrasada: AlertTriangle,
      os_atribuida: User,
      inspecao_pendente: ClipboardCheck,
      estoque_critico: Package,
      falha_detectada: AlertCircle,
      ativo_parado: XCircle,
    };
    return icons[tipo] || Bell;
  };
  
  return (
    <div className="relative">
      <button 
        onClick={() => setShowDropdown(!showDropdown)}
        className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg relative transition-colors"
        data-testid="notifications-button"
      >
        <Bell size={20} className="text-slate-400" />
        {count > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-xs flex items-center justify-center text-white font-bold animate-pulse">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>
      
      {showDropdown && (
        <div className="absolute right-0 mt-2 w-80 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-50 animate-fadeIn">
          <div className="p-3 border-b border-slate-800 flex items-center justify-between">
            <span className="font-semibold text-slate-200">Notificações</span>
            {count > 0 && (
              <button onClick={markAllRead} className="text-xs text-brand hover:underline">
                Marcar todas como lidas
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto custom-scrollbar">
            {notifications.length > 0 ? notifications.map(notif => {
              const Icon = getNotifIcon(notif.tipo);
              return (
                <div 
                  key={notif.id}
                  className="p-3 border-b border-slate-800 hover:bg-slate-800/50 cursor-pointer flex gap-3"
                  onClick={() => {
                    markAsRead(notif.id);
                    if (notif.link) navigate(notif.link);
                    setShowDropdown(false);
                  }}
                >
                  <div className="p-2 bg-slate-800 rounded-lg h-fit">
                    <Icon size={16} className="text-slate-400" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-200">{notif.titulo}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{notif.mensagem}</p>
                  </div>
                </div>
              );
            }) : (
              <div className="p-6 text-center text-slate-500">
                <Bell size={24} className="mx-auto mb-2 opacity-50" />
                <p>Nenhuma notificação</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ============== MODALS ==============

// Modal Novo Ativo
const ModalNovoAtivo = ({ isOpen, onClose, onSuccess, areas = [], editData = null }) => {
  const [loading, setLoading] = useState(false);
  const [pdfFiles, setPdfFiles] = useState([]);
  const [existingManuais, setExistingManuais] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [form, setForm] = useState({
    tag: '', nome: '', tipo_equipamento: '', fabricante: '', modelo: '', numero_serie: '',
    sector_id: '', observacoes: '',
    categoria_id: '', fabricante_id: '', modelo_id: '', familia: '', classe_equipamento: '', criticidade: ''
  });
  
  const [bibCategorias, setBibCategorias] = useState([]);
  const [bibFabricantes, setBibFabricantes] = useState([]);
  const [bibModelos, setBibModelos] = useState([]);
  
  useEffect(() => {
    if (isOpen) {
      api.get('/sectors').then(r => setSectors(r.data)).catch(() => {});
      api.get('/biblioteca/categorias').then(r => setBibCategorias(r.data.items || [])).catch(() => {});
      api.get('/biblioteca/fabricantes').then(r => setBibFabricantes(r.data.items || [])).catch(() => {});
      api.get('/biblioteca/modelos-mestre').then(r => setBibModelos(r.data.items || [])).catch(() => {});
    }
  }, [isOpen]);
  
  useEffect(() => {
    if (editData) {
      setForm({
        tag: editData.tag || '',
        nome: editData.nome || '',
        tipo_equipamento: editData.tipo_equipamento || '',
        fabricante: editData.fabricante || '',
        modelo: editData.modelo || '',
        numero_serie: editData.numero_serie || '',
        sector_id: editData.sector_id || '',
        observacoes: editData.observacoes || '',
        categoria_id: editData.categoria_id || '',
        fabricante_id: editData.fabricante_id || '',
        modelo_id: editData.modelo_id || '',
        familia: editData.familia || '',
        classe_equipamento: editData.classe_equipamento || '',
        criticidade: editData.criticidade || '',
      });
    } else {
      setForm({
        tag: '', nome: '', tipo_equipamento: '', fabricante: '', modelo: '', numero_serie: '',
        sector_id: '', observacoes: '',
        categoria_id: '', fabricante_id: '', modelo_id: '', familia: '', classe_equipamento: '', criticidade: ''
      });
    }
    setPdfFiles([]);
    if (editData?.id) {
      api.get(`/ativos/${editData.id}/manuais`).then(res => setExistingManuais(res.data)).catch(() => {});
    } else {
      setExistingManuais([]);
    }
  }, [editData, isOpen]);
  

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.nome || !form.sector_id) {
      toast.error(!form.sector_id ? 'Selecione a área' : 'Preencha o nome do ativo');
      return;
    }
    
    setLoading(true);
    try {
      const payload = {
        ...form,
      };
      
      if (editData) {
        await api.put(`/ativos/${editData.id}`, payload);
        // Upload new PDFs for existing ativo
        for (const file of pdfFiles) {
          const formData = new FormData();
          formData.append('file', file);
          await api.post(`/ativos/${editData.id}/manual`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
        }
        toast.success('Ativo atualizado com sucesso!');
      } else {
        const res = await api.post('/ativos', payload);
        // Upload PDFs for new ativo
        if (pdfFiles.length > 0 && res.data?.id) {
          for (const file of pdfFiles) {
            const formData = new FormData();
            formData.append('file', file);
            await api.post(`/ativos/${res.data.id}/manual`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
          }
        }
        toast.success('Ativo criado com sucesso!');
      }
      onSuccess();
      onClose();
    } catch (error) {
      toast.error(normalizeError(error));
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={editData ? "Editar Ativo" : "Novo Ativo"} size="lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Identificação */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-brand flex items-center gap-2">
            <Tag size={16} /> Identificação
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Área" required>
              <Select
                value={form.sector_id}
                onChange={(val) => setForm({...form, sector_id: val})}
                options={sectors.map(s => ({ value: s.id, label: s.nome }))}
                placeholder="Selecione a área..."
              />
            </FormInput>
            <FormInput label="TAG" required={false}>
              <input
                type="text"
                value={form.tag}
                onChange={(e) => setForm({...form, tag: e.target.value.toUpperCase()})}
                placeholder="Auto-gerado se vazio"
                className="input-industrial w-full px-4 font-mono"
              />
            </FormInput>
            <FormInput label="Nome do Ativo" required>
              <input
                type="text"
                value={form.nome}
                onChange={(e) => setForm({...form, nome: e.target.value})}
                placeholder="Ex: Bomba Centrífuga 01"
                className="input-industrial w-full px-4"
                required
              />
            </FormInput>
            {/* Classification fields */}
            <FormInput label="Categoria">
              <select value={form.categoria_id} onChange={(e) => setForm({...form, categoria_id: e.target.value})} className="input-industrial w-full px-4" data-testid="ativo-categoria">
                <option value="">Selecione...</option>
                {bibCategorias.map(c => <option key={c.id} value={c.id}>{c.nome}</option>)}
              </select>
            </FormInput>
            <FormInput label="Fabricante (Catálogo)">
              <select value={form.fabricante_id} onChange={(e) => { const fab = bibFabricantes.find(f => f.id === e.target.value); setForm({...form, fabricante_id: e.target.value, fabricante: fab?.nome || form.fabricante}); }} className="input-industrial w-full px-4" data-testid="ativo-fabricante-cat">
                <option value="">Selecione...</option>
                {bibFabricantes.map(f => <option key={f.id} value={f.id}>{f.nome}</option>)}
              </select>
            </FormInput>
            <FormInput label="Tipo de Equipamento" required>
              <input type="text" value={form.tipo_equipamento} onChange={(e) => setForm({...form, tipo_equipamento: e.target.value})} placeholder="Ex: Bomba, Motor, Compressor" className="input-industrial w-full px-4" required />
            </FormInput>
            <FormInput label="Fabricante">
              <input type="text" value={form.fabricante} onChange={(e) => setForm({...form, fabricante: e.target.value})} className="input-industrial w-full px-4" />
            </FormInput>
            <FormInput label="Modelo">
              <input type="text" value={form.modelo} onChange={(e) => setForm({...form, modelo: e.target.value})} className="input-industrial w-full px-4" />
            </FormInput>
            <FormInput label="Número de Série">
              <input type="text" value={form.numero_serie} onChange={(e) => setForm({...form, numero_serie: e.target.value})} className="input-industrial w-full px-4" />
            </FormInput>
            <FormInput label="Família">
              <input type="text" value={form.familia} onChange={(e) => setForm({...form, familia: e.target.value})} placeholder="Ex: Equipamentos Rotativos" className="input-industrial w-full px-4" />
            </FormInput>
            <FormInput label="Classe">
              <select value={form.classe_equipamento} onChange={(e) => setForm({...form, classe_equipamento: e.target.value})} className="input-industrial w-full px-4">
                <option value="">Selecione...</option>
                <option value="A">A — Crítico</option>
                <option value="B">B — Importante</option>
                <option value="C">C — Secundário</option>
              </select>
            </FormInput>
            <FormInput label="Criticidade">
              <select value={form.criticidade} onChange={(e) => setForm({...form, criticidade: e.target.value})} className="input-industrial w-full px-4" data-testid="ativo-criticidade">
                <option value="">Selecione...</option>
                <option value="critica">Crítica</option>
                <option value="alta">Alta</option>
                <option value="media">Média</option>
                <option value="baixa">Baixa</option>
              </select>
            </FormInput>
          </div>
        </div>
        
        {/* Manuais PDF */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wider flex items-center gap-2">
            <FileText size={16} /> Manuais Técnicos (PDF)
          </h3>
          
          {/* Existing manuals (edit mode) */}
          {existingManuais.length > 0 && (
            <div className="space-y-2">
              {existingManuais.map((m) => (
                <div key={m.id} className="flex items-center justify-between p-2 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <FileText size={16} className="text-red-400" />
                    <span className="text-sm text-slate-300">{m.filename}</span>
                    <span className="text-xs text-slate-600">{(m.size_bytes / 1024).toFixed(0)}KB</span>
                  </div>
                  <button type="button" onClick={() => window.open(`${BACKEND_URL}${m.url}`, '_blank')} className="text-xs text-blue-400 hover:text-blue-300">Abrir</button>
                </div>
              ))}
            </div>
          )}
          
          {/* New files to upload */}
          {pdfFiles.length > 0 && (
            <div className="space-y-2">
              {pdfFiles.map((f, idx) => (
                <div key={`pdf-${idx}-${f.name}`} className="flex items-center justify-between p-2 bg-brand-10 border border-brand-30 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Upload size={16} className="text-brand" />
                    <span className="text-sm text-slate-300">{f.name}</span>
                    <span className="text-xs text-slate-600">{(f.size / 1024).toFixed(0)}KB</span>
                  </div>
                  <button type="button" onClick={() => setPdfFiles(prev => prev.filter((_, i) => i !== idx))} className="text-xs text-red-400 hover:text-red-300">Remover</button>
                </div>
              ))}
            </div>
          )}
          
          <label className="flex items-center justify-center gap-2 p-4 border-2 border-dashed border-slate-700 rounded-lg cursor-pointer hover:border-blue-500/50 hover:bg-blue-500/5 transition-all">
            <Upload size={20} className="text-slate-500" />
            <span className="text-sm text-slate-400">Clique para adicionar PDF</span>
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={(e) => {
                const files = Array.from(e.target.files).filter(f => f.name.toLowerCase().endsWith('.pdf'));
                if (files.length > 0) setPdfFiles(prev => [...prev, ...files]);
                e.target.value = '';
              }}
              className="hidden"
            />
          </label>
        </div>
        
        {/* Observações */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <FileText size={16} /> Observações
          </h3>
          <textarea
            value={form.observacoes}
            onChange={(e) => setForm({...form, observacoes: e.target.value})}
            className="input-industrial w-full px-4 py-3 min-h-[100px]"
            placeholder="Observações adicionais..."
          />
        </div>
        
        {/* Actions */}
        <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancelar
          </button>
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
            {loading ? <RefreshCw size={18} className="animate-spin" /> : <Save size={18} />}
            {loading ? 'Salvando...' : 'Salvar Ativo'}
          </button>
        </div>
      </form>
    </Modal>
  );
};

// Modal Novo Estoque
const ModalNovoEstoque = ({ isOpen, onClose, onSuccess, editData = null }) => {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    sku: '', nome: '', descricao: '', categoria: 'outro',
    quantidade: 0, estoque_minimo: 0, estoque_maximo: '',
    unidade: 'UN', custo_unitario: 0, fornecedor: '',
    almoxarifado: 'Principal', prateleira: '', posicao: '',
    alertar_minimo: true, item_critico: false
  });
  
  useEffect(() => {
    if (editData) {
      setForm({
        sku: editData.sku || '',
        nome: editData.nome || '',
        descricao: editData.descricao || '',
        categoria: editData.categoria || 'outros',
        quantidade: editData.quantidade || 0,
        estoque_minimo: editData.estoque_minimo || 0,
        estoque_maximo: editData.estoque_maximo || '',
        unidade: editData.unidade || 'UN',
        custo_unitario: editData.custo_unitario || 0,
        fornecedor: editData.fornecedor || '',
        almoxarifado: editData.almoxarifado || 'Principal',
        prateleira: editData.prateleira || '',
        posicao: editData.posicao || '',
        alertar_minimo: editData.alertar_minimo ?? true,
        item_critico: editData.item_critico ?? false
      });
    } else {
      setForm({
        sku: '', nome: '', descricao: '', categoria: 'outro',
        quantidade: 0, estoque_minimo: 0, estoque_maximo: '',
        unidade: 'UN', custo_unitario: 0, fornecedor: '',
        almoxarifado: 'Principal', prateleira: '', posicao: '',
        alertar_minimo: true, item_critico: false
      });
    }
  }, [editData, isOpen]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.nome) {
      toast.error('Nome é obrigatório');
      return;
    }
    
    setLoading(true);
    try {
      const payload = {
        ...form,
        quantidade: parseFloat(form.quantidade) || 0,
        estoque_minimo: parseFloat(form.estoque_minimo) || 0,
        estoque_maximo: form.estoque_maximo ? parseFloat(form.estoque_maximo) : null,
        custo_unitario: parseFloat(form.custo_unitario) || 0,
      };
      
      if (editData) {
        await api.put(`/estoque/${editData.id}`, payload);
        toast.success('Item atualizado com sucesso!');
      } else {
        await api.post('/estoque', payload);
        toast.success('Item criado com sucesso!');
      }
      onSuccess();
      onClose();
    } catch (error) {
      toast.error(normalizeError(error));
    } finally {
      setLoading(false);
    }
  };
  
  const categorias = [
    { value: 'rolamento', label: 'Rolamento' },
    { value: 'lubrificante', label: 'Lubrificante' },
    { value: 'correia', label: 'Correia' },
    { value: 'vedacao', label: 'Vedação' },
    { value: 'filtro', label: 'Filtro' },
    { value: 'eletrico', label: 'Elétrico' },
    { value: 'mecanico', label: 'Mecânico' },
    { value: 'hidraulico', label: 'Hidráulico' },
    { value: 'pneumatico', label: 'Pneumático' },
    { value: 'instrumentacao', label: 'Instrumentação' },
    { value: 'outro', label: 'Outro' },
  ];
  
  const unidades = [
    { value: 'UN', label: 'Unidade (UN)' },
    { value: 'L', label: 'Litro (L)' },
    { value: 'KG', label: 'Quilograma (KG)' },
    { value: 'M', label: 'Metro (M)' },
    { value: 'PC', label: 'Peça (PC)' },
    { value: 'CX', label: 'Caixa (CX)' },
  ];
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={editData ? "Editar Item" : "Novo Item de Estoque"} size="lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Identificação */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-brand flex items-center gap-2">
            <Tag size={16} /> Identificação
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Código">
              <input
                type="text"
                value={form.sku}
                onChange={(e) => setForm({...form, sku: e.target.value.toUpperCase()})}
                placeholder="Auto-gerado se vazio"
                className="input-industrial w-full px-4 font-mono"
              />
            </FormInput>
            <FormInput label="Nome do Item" required>
              <input
                type="text"
                value={form.nome}
                onChange={(e) => setForm({...form, nome: e.target.value})}
                placeholder="Ex: Rolamento 6205-2RS"
                className="input-industrial w-full px-4"
                required
              />
            </FormInput>
            <FormInput label="Categoria">
              <Select
                value={form.categoria}
                onChange={(val) => setForm({...form, categoria: val})}
                options={categorias}
              />
            </FormInput>
            <FormInput label="Fornecedor">
              <input
                type="text"
                value={form.fornecedor}
                onChange={(e) => setForm({...form, fornecedor: e.target.value})}
                className="input-industrial w-full px-4"
              />
            </FormInput>
          </div>
          <FormInput label="Descrição">
            <textarea
              value={form.descricao}
              onChange={(e) => setForm({...form, descricao: e.target.value})}
              className="input-industrial w-full px-4 py-3"
              rows={2}
            />
          </FormInput>
        </div>
        
        {/* Controle */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wider flex items-center gap-2">
            <Package size={16} /> Controle de Estoque
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <FormInput label="Quantidade Atual">
              <input
                type="number"
                value={form.quantidade}
                onChange={(e) => setForm({...form, quantidade: e.target.value})}
                className="input-industrial w-full px-4"
                min="0"
              />
            </FormInput>
            <FormInput label="Estoque Mínimo">
              <input
                type="number"
                value={form.estoque_minimo}
                onChange={(e) => setForm({...form, estoque_minimo: e.target.value})}
                className="input-industrial w-full px-4"
                min="0"
              />
            </FormInput>
            <FormInput label="Estoque Máximo">
              <input
                type="number"
                value={form.estoque_maximo}
                onChange={(e) => setForm({...form, estoque_maximo: e.target.value})}
                className="input-industrial w-full px-4"
                min="0"
              />
            </FormInput>
            <FormInput label="Unidade">
              <Select
                value={form.unidade}
                onChange={(val) => setForm({...form, unidade: val})}
                options={unidades}
              />
            </FormInput>
          </div>
        </div>
        
        {/* Financeiro */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-2">
            <DollarSign size={16} /> Financeiro
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Custo Unitário (R$)">
              <input
                type="number"
                step="0.01"
                value={form.custo_unitario}
                onChange={(e) => setForm({...form, custo_unitario: e.target.value})}
                className="input-industrial w-full px-4"
                min="0"
              />
            </FormInput>
            <div className="flex items-end">
              <div className="glass-card p-3 w-full">
                <p className="text-xs text-slate-500">Valor Total em Estoque</p>
                <p className="text-lg font-bold text-brand">
                  R$ {((parseFloat(form.quantidade) || 0) * (parseFloat(form.custo_unitario) || 0)).toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Localização */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-2">
            <MapPin size={16} /> Localização
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <FormInput label="Almoxarifado">
              <input
                type="text"
                value={form.almoxarifado}
                onChange={(e) => setForm({...form, almoxarifado: e.target.value})}
                className="input-industrial w-full px-4"
              />
            </FormInput>
            <FormInput label="Prateleira">
              <input
                type="text"
                value={form.prateleira}
                onChange={(e) => setForm({...form, prateleira: e.target.value})}
                className="input-industrial w-full px-4"
                placeholder="Ex: A-01"
              />
            </FormInput>
            <FormInput label="Posição">
              <input
                type="text"
                value={form.posicao}
                onChange={(e) => setForm({...form, posicao: e.target.value})}
                className="input-industrial w-full px-4"
              />
            </FormInput>
          </div>
        </div>
        
        {/* Automação */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Zap size={16} /> Automação
          </h3>
          <div className="flex flex-wrap gap-6">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={form.alertar_minimo}
                onChange={(e) => setForm({...form, alertar_minimo: e.target.checked})}
                className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-brand focus:ring-brand"
              />
              <span className="text-slate-300">Alertar estoque mínimo</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={form.item_critico}
                onChange={(e) => setForm({...form, item_critico: e.target.checked})}
                className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-red-500 focus:ring-red-500"
              />
              <span className="text-slate-300">Item crítico</span>
            </label>
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
            {loading ? <RefreshCw size={18} className="animate-spin" /> : <Save size={18} />}
            {loading ? 'Salvando...' : 'Salvar Item'}
          </button>
        </div>
      </form>
    </Modal>
  );
};

// Modal Nova OS
const ModalNovaOS = ({ isOpen, onClose, onSuccess, ativos = [], tecnicos = [], editData = null, preSelectedAtivoId = null }) => {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    ativo_id: '', tipo: 'corretiva', disciplina: 'mecanica', prioridade: 'media',
    titulo: '', descricao: '', responsavel_id: '',
    data_planejada: '', custo_pecas: 0, custo_mao_obra: 0,
    causa_falha: '', equipamento_parado: false, horas_parada: null
  });
  
  useEffect(() => {
    if (editData) {
      setForm({
        ativo_id: editData.ativo_id || '',
        tipo: editData.tipo || 'corretiva',
        disciplina: editData.disciplina || 'mecanica',
        prioridade: editData.prioridade || 'media',
        titulo: editData.titulo || '',
        descricao: editData.descricao || '',
        responsavel_id: editData.responsavel_id || '',
        data_planejada: editData.data_planejada?.split('T')[0] || '',
        custo_pecas: editData.custo_pecas || 0,
        custo_mao_obra: editData.custo_mao_obra || 0,
        causa_falha: editData.causa_falha || '',
        equipamento_parado: editData.equipamento_parado || false,
        horas_parada: editData.horas_parada || null
      });
    } else {
      setForm({
        ativo_id: preSelectedAtivoId || '', tipo: 'corretiva', disciplina: 'mecanica', prioridade: 'media',
        titulo: '', descricao: '', responsavel_id: '', equipe: [],
        data_planejada: '', custo_pecas: 0, custo_mao_obra: 0,
        causa_falha: '', equipamento_parado: false, horas_parada: null
      });
    }
  }, [editData, isOpen, preSelectedAtivoId]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.ativo_id || !form.titulo || !form.disciplina) {
      toast.error('Preencha Ativo, Título e Disciplina');
      return;
    }
    
    setLoading(true);
    try {
      const payload = {
        ...form,
        custo_pecas: parseFloat(form.custo_pecas) || 0,
        custo_mao_obra: parseFloat(form.custo_mao_obra) || 0,
        horas_parada: form.horas_parada ? parseFloat(form.horas_parada) : null,
        data_planejada: form.data_planejada || null,
        responsavel_id: form.responsavel_id || null,
      };
      
      if (!navigator.onLine) {
        // Queue for offline sync
        await queueOperation({
          method: editData ? 'PUT' : 'POST',
          url: editData ? `/ordens-servico/${editData.id}` : '/ordens-servico',
          data: payload
        });
        toast.info('Sem conexão — OS salva localmente e será sincronizada');
        onSuccess();
        onClose();
      } else {
        if (editData) {
          await api.put(`/ordens-servico/${editData.id}`, payload);
          toast.success('OS atualizada com sucesso!');
        } else {
          await api.post('/ordens-servico', payload);
          toast.success('OS criada com sucesso!');
        }
        onSuccess();
        onClose();
      }
    } catch (error) {
      toast.error(normalizeError(error));
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={editData ? "Editar Ordem de Serviço" : "Nova Ordem de Serviço"} size="lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Identificação */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-brand flex items-center gap-2">
            <Wrench size={16} /> Dados da OS
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Ativo" required>
              {preSelectedAtivoId ? (
                <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
                  {(() => { const a = ativos.find(x => x.id === preSelectedAtivoId); return a ? (
                    <div>
                      {a.sector && <p className="text-xs text-slate-500 uppercase">{a.sector.nome}</p>}
                      <span className="font-mono text-brand text-sm">{a.tag}</span>
                      <span className="text-slate-300 text-sm ml-2">{a.nome}</span>
                    </div>
                  ) : <span className="text-slate-400">Ativo vinculado</span>; })()}
                </div>
              ) : (
                <Select
                  value={form.ativo_id}
                  onChange={(val) => setForm({...form, ativo_id: val})}
                  options={ativos.map(a => ({ value: a.id, label: `${a.sector?.nome || ''} • ${a.tag} - ${a.nome}` }))}
                  placeholder="Selecione o ativo..."
                />
              )}
            </FormInput>
            <FormInput label="Título" required>
              <input
                type="text"
                value={form.titulo}
                onChange={(e) => setForm({...form, titulo: e.target.value})}
                placeholder="Ex: Troca de rolamento"
                className="input-industrial w-full px-4"
                required
              />
            </FormInput>
            <FormInput label="Tipo">
              <Select
                value={form.tipo}
                onChange={(val) => setForm({...form, tipo: val})}
                options={[
                  { value: 'lubrificacao', label: 'Lubrificação' },
                  { value: 'limpeza_organizacao', label: 'Limpeza e Organização' },
                  { value: 'preventiva', label: 'Preventiva' },
                  { value: 'corretiva', label: 'Corretiva' },
                  { value: 'preparacao_material', label: 'Preparação de Material' },
                  { value: 'fabricacao_melhorias', label: 'Fabricação / Melhorias' },
                ]}
              />
            </FormInput>
            <FormInput label="Disciplina" required>
              <Select
                value={form.disciplina}
                onChange={(val) => setForm({...form, disciplina: val})}
                options={[
                  { value: 'mecanica', label: 'Mecânica' },
                  { value: 'eletrica', label: 'Elétrica' },
                  { value: 'instrumentacao', label: 'Instrumentação' },
                  { value: 'civil', label: 'Civil' },
                  { value: 'producao', label: 'Produção' },
                ]}
              />
            </FormInput>
            <FormInput label="Prioridade">
              <Select
                value={form.prioridade}
                onChange={(val) => setForm({...form, prioridade: val})}
                options={[
                  { value: 'baixa', label: 'Baixa' },
                  { value: 'media', label: 'Média' },
                  { value: 'alta', label: 'Alta' },
                  { value: 'critica', label: 'Crítica' },
                  { value: 'emergencia', label: 'Emergência' },
                ]}
              />
            </FormInput>
          </div>
          <FormInput label="Descrição">
            <textarea
              value={form.descricao}
              onChange={(e) => setForm({...form, descricao: e.target.value})}
              className="input-industrial w-full px-4 py-3 min-h-[100px]"
              placeholder="Descreva o problema ou serviço..."
            />
          </FormInput>
          
          {/* Campos de Falha */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <FormInput label={`Causa da Falha${form.tipo === 'corretiva' ? ' *' : ''}`}>
              <input type="text" value={form.causa_falha || ''} onChange={(e) => setForm({...form, causa_falha: e.target.value})} placeholder="Ex: Desgaste natural" className="input-industrial w-full px-4" required={form.tipo === 'corretiva'} data-testid="os-causa-falha" />
            </FormInput>
            <FormInput label="Equipamento Parado">
              <div className="flex items-center gap-4 h-10">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" name="eq_parado" checked={form.equipamento_parado === true} onChange={() => setForm({...form, equipamento_parado: true})} className="accent-red-500" data-testid="os-eq-parado-sim" />
                  <span className="text-sm text-red-400">Sim</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" name="eq_parado" checked={form.equipamento_parado === false} onChange={() => setForm({...form, equipamento_parado: false})} className="accent-brand" data-testid="os-eq-parado-nao" />
                  <span className="text-sm text-brand">Não</span>
                </label>
              </div>
            </FormInput>
            {form.equipamento_parado && (
              <FormInput label="Horas de Parada">
                <input type="number" step="0.5" min="0" value={form.horas_parada || ''} onChange={(e) => setForm({...form, horas_parada: parseFloat(e.target.value) || 0})} placeholder="Ex: 4.5" className="input-industrial w-full px-4" data-testid="os-horas-parada" />
              </FormInput>
            )}
          </div>
        </div>
        
        {/* Execução */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wider flex items-center gap-2">
            <Users size={16} /> Execução
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Responsável">
              <Select
                value={form.responsavel_id}
                onChange={(val) => setForm({...form, responsavel_id: val})}
                options={tecnicos.map(t => ({ value: t.id, label: t.nome }))}
                placeholder="Não atribuído"
              />
            </FormInput>
            <FormInput label="Executantes">
              <div className="space-y-1">
                <div className="flex flex-wrap gap-1 min-h-[40px]">
                  {(form.equipe || []).map(uid => {
                    const t = tecnicos.find(x => x.id === uid);
                    return t ? (
                      <span key={uid} className="bg-blue-500/20 text-blue-300 text-xs px-2 py-1 rounded flex items-center gap-1">
                        {t.nome} <button type="button" onClick={() => setForm({...form, equipe: form.equipe.filter(id => id !== uid)})} className="hover:text-red-400"><X size={12} /></button>
                      </span>
                    ) : null;
                  })}
                </div>
                <select onChange={e => {
                  if (e.target.value && !(form.equipe || []).includes(e.target.value)) {
                    setForm({...form, equipe: [...(form.equipe || []), e.target.value]});
                  }
                  e.target.value = '';
                }} className="input-industrial w-full px-3 text-sm">
                  <option value="">Adicionar executante...</option>
                  {tecnicos.filter(t => !(form.equipe || []).includes(t.id)).map(t => <option key={t.id} value={t.id}>{t.nome}</option>)}
                </select>
              </div>
            </FormInput>
            <FormInput label="Data Planejada">
              <input
                type="date"
                value={form.data_planejada}
                onChange={(e) => setForm({...form, data_planejada: e.target.value})}
                className="input-industrial w-full px-4"
              />
            </FormInput>
          </div>
        </div>
        
        {/* Financeiro */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-2">
            <DollarSign size={16} /> Estimativa de Custo
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <FormInput label="Custo Peças (R$)">
              <input
                type="number"
                step="0.01"
                value={form.custo_pecas}
                onChange={(e) => setForm({...form, custo_pecas: e.target.value})}
                className="input-industrial w-full px-4"
                min="0"
              />
            </FormInput>
            <FormInput label="Custo Mão de Obra (R$)">
              <input
                type="number"
                step="0.01"
                value={form.custo_mao_obra}
                onChange={(e) => setForm({...form, custo_mao_obra: e.target.value})}
                className="input-industrial w-full px-4"
                min="0"
              />
            </FormInput>
            <div className="flex items-end">
              <div className="glass-card p-3 w-full">
                <p className="text-xs text-slate-500">Custo Total Estimado</p>
                <p className="text-lg font-bold text-brand">
                  R$ {((parseFloat(form.custo_pecas) || 0) + (parseFloat(form.custo_mao_obra) || 0)).toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
            {loading ? <RefreshCw size={18} className="animate-spin" /> : <Save size={18} />}
            {loading ? 'Salvando...' : 'Salvar OS'}
          </button>
        </div>
      </form>
    </Modal>
  );
};

// Modal Nova Inspeção
const ModalNovaInspecao = ({ isOpen, onClose, onSuccess, ativos = [], rotas = [], tecnicos = [], preSelectedAtivoId = null }) => {
  const [loading, setLoading] = useState(false);
  const [planosDisponiveis, setPlanosDisponiveis] = useState([]);
  const [selectedPlano, setSelectedPlano] = useState(null);
  const [checklist, setChecklist] = useState([]);
  const [form, setForm] = useState({
    ativo_id: '', responsavel_id: '', executantes: [], data_planejada: '', observacoes: ''
  });
  const { user } = useAuth();
  
  useEffect(() => {
    if (isOpen) {
      setPlanosDisponiveis([]);
      setSelectedPlano(null);
      setChecklist([]);
      setForm({ ativo_id: preSelectedAtivoId || '', responsavel_id: user?.id || '', executantes: [], data_planejada: '', observacoes: '' });
    }
  }, [isOpen, user, preSelectedAtivoId]);

  // Load approved plans when ativo changes
  const loadPlanos = async (ativoId) => {
    if (!ativoId) { setPlanosDisponiveis([]); return; }
    try {
      const res = await api.get(`/planos-inspecao/por-ativo/${ativoId}`);
      setPlanosDisponiveis(res.data);
    } catch {
      setPlanosDisponiveis([]);
    }
  };

  useEffect(() => {
    const ativoId = preSelectedAtivoId || form.ativo_id;
    if (ativoId && isOpen) loadPlanos(ativoId);
  }, [form.ativo_id, preSelectedAtivoId, isOpen]);

  const handleAtivoChange = (ativoId) => {
    setForm(prev => ({...prev, ativo_id: ativoId}));
    setSelectedPlano(null);
    setChecklist([]);
  };

  const handleSelectPlano = (plano) => {
    setSelectedPlano(plano);
    const perguntas = (plano.perguntas || []).map(p => ({
      id: p.id || String(Date.now()),
      descricao: p.texto || p.descricao || '',
      tipo: p.tipo_campo || p.tipo || 'boolean',
      obrigatorio: p.obrigatoria ?? p.obrigatorio ?? true,
      unidade: p.unidade || '',
      conforme: null, valor: null, observacao: ''
    }));
    setChecklist(perguntas);
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.ativo_id) { toast.error('Selecione o ativo'); return; }
    if (!selectedPlano) { toast.error('Selecione um plano de inspeção'); return; }
    
    setLoading(true);
    try {
      const payload = {
        ativo_id: form.ativo_id,
        plano_id: selectedPlano.id,
        tipo: selectedPlano.tipo || selectedPlano.categoria || 'inspecao',
        disciplina: selectedPlano.disciplina || null,
        responsavel_id: form.responsavel_id || null,
        executantes: form.executantes || [],
        checklist: checklist,
        data_planejada: form.data_planejada || null,
        observacoes: form.observacoes || null,
      };

      if (!navigator.onLine) {
        await queueOperation({ method: 'POST', url: '/inspecoes', data: payload });
        toast.info('Sem conexão — inspeção salva localmente');
      } else {
        await api.post('/inspecoes', payload);
        toast.success('Execução criada com sucesso!');
      }
      onSuccess();
      onClose();
    } catch (error) {
      toast.error(normalizeError(error));
    } finally {
      setLoading(false);
    }
  };

  const selectedAtivo = ativos.find(a => a.id === form.ativo_id);
  const tipoLabels = { inspecao: 'Inspeção', preventiva: 'Preventiva', lubrificacao: 'Lubrificação', limpeza: 'Limpeza', melhoria: 'Melhoria', mecanica: 'Mecânica', eletrica: 'Elétrica' };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Nova Execução de Inspeção" size="lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Equipamento + Responsável */}
        <div className="glass-card p-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Ativo / Equipamento" required>
              {preSelectedAtivoId ? (
                <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
                  {(() => { const a = ativos.find(x => x.id === preSelectedAtivoId); return a ? (
                    <div>
                      {a.sector && <p className="text-xs text-slate-500 uppercase">{a.sector.nome}</p>}
                      <span className="font-mono text-brand text-sm">{a.tag}</span>
                      <span className="text-slate-300 text-sm ml-2">{a.nome}</span>
                    </div>
                  ) : <span className="text-slate-400">Ativo vinculado</span>; })()}
                </div>
              ) : (
                <Select value={form.ativo_id} onChange={(val) => handleAtivoChange(val)}
                  options={ativos.map(a => ({ value: a.id, label: `${a.sector?.nome || ''} • ${a.tag} - ${a.nome}` }))} placeholder="Selecione o equipamento..." />
              )}
            </FormInput>
            <FormInput label="Responsável">
              <Select value={form.responsavel_id} onChange={(val) => setForm({...form, responsavel_id: val})}
                options={tecnicos.map(t => ({ value: t.id, label: t.nome }))} placeholder="Selecione..." />
            </FormInput>
            <FormInput label="Data Planejada">
              <input type="date" value={form.data_planejada} onChange={(e) => setForm({...form, data_planejada: e.target.value})} className="input-industrial w-full px-4" />
            </FormInput>
          </div>
          {/* Executantes */}
          <FormInput label="Executantes">
            <div className="space-y-1">
              <div className="flex flex-wrap gap-1 min-h-[32px]">
                {(form.executantes || []).map(uid => {
                  const t = tecnicos.find(x => x.id === uid);
                  return t ? (
                    <span key={uid} className="bg-blue-500/20 text-blue-300 text-xs px-2 py-1 rounded flex items-center gap-1">
                      {t.nome} <button type="button" onClick={() => setForm({...form, executantes: form.executantes.filter(id => id !== uid)})} className="hover:text-red-400"><X size={12} /></button>
                    </span>
                  ) : null;
                })}
              </div>
              <select onChange={e => {
                if (e.target.value && !(form.executantes || []).includes(e.target.value)) {
                  setForm({...form, executantes: [...(form.executantes || []), e.target.value]});
                }
                e.target.value = '';
              }} className="input-industrial w-full px-3 text-sm" data-testid="inspecao-executantes-select">
                <option value="">Adicionar executante...</option>
                {tecnicos.filter(t => !(form.executantes || []).includes(t.id)).map(t => <option key={t.id} value={t.id}>{t.nome}</option>)}
              </select>
            </div>
          </FormInput>
        </div>

        {/* Planos Aprovados */}
        {form.ativo_id && (
          <div className="glass-card p-4 space-y-3">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
              Planos Aprovados ({planosDisponiveis.length})
            </h3>
            {planosDisponiveis.length === 0 ? (
              <div className="text-center py-6">
                <ClipboardCheck size={32} className="text-slate-600 mx-auto mb-2" />
                <p className="text-sm text-slate-500">Nenhum plano aprovado para este ativo.</p>
                <p className="text-xs text-slate-600 mt-1">O PCM precisa criar e aprovar planos antes de executar inspeções.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {planosDisponiveis.map(plano => (
                  <button key={plano.id} type="button"
                    onClick={() => handleSelectPlano(plano)}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      selectedPlano?.id === plano.id
                        ? 'border-emerald-500/50 bg-brand-10'
                        : 'border-slate-700 hover:border-slate-500 bg-slate-800/30'
                    }`}
                    data-testid={`plano-option-${plano.id}`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className={`font-medium text-sm ${selectedPlano?.id === plano.id ? 'text-emerald-400' : 'text-slate-200'}`}>{plano.nome}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 capitalize">{tipoLabels[plano.tipo] || plano.tipo}</span>
                          {plano.disciplina && <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 capitalize">{plano.disciplina}</span>}
                          <span className="text-xs text-slate-500">{(plano.perguntas || []).length} perguntas</span>
                          <span className="text-xs text-slate-600">v{plano.versao || 1}</span>
                          {plano._generico && <span className="text-xs px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400">Genérico</span>}
                        </div>
                      </div>
                      {selectedPlano?.id === plano.id && <CheckCircle2 size={20} className="text-brand" />}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Checklist Preview */}
        {selectedPlano && checklist.length > 0 && (
          <div className="glass-card p-4 space-y-3">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
              Checklist — {selectedPlano.nome} ({checklist.length} itens)
            </h3>
            <div className="max-h-48 overflow-y-auto space-y-1 custom-scrollbar">
              {checklist.map((item, idx) => (
                <div key={item.id || idx} className="flex items-center gap-2 text-xs text-slate-400 py-1 border-b border-slate-800/50">
                  <span className="text-slate-600 w-5">{idx + 1}.</span>
                  <span className="flex-1">{item.descricao}</span>
                  <span className="text-slate-600 capitalize">{item.tipo}</span>
                  {item.obrigatorio && <span className="text-red-400">*</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        <FormInput label="Observações">
          <textarea value={form.observacoes} onChange={(e) => setForm({...form, observacoes: e.target.value})} className="input-industrial w-full px-4 py-3 min-h-[60px]" placeholder="Observações adicionais..." />
        </FormInput>

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="submit" disabled={loading || !selectedPlano} className="btn-primary" data-testid="submit-inspecao">
            {loading ? 'Salvando...' : `Executar ${selectedPlano ? selectedPlano.nome : 'Inspeção'}`}
          </button>
        </div>
      </form>
    </Modal>
  );
};

// ============== SIDEBAR ==============

const Sidebar = ({ collapsed, setCollapsed }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { branding } = useBranding() || {};
  const b = branding || {};
  
  const role = user?.role || 'tecnico';
  const isAdmin = role === 'admin' || role === 'master';
  const isMaster = role === 'master';
  const isOperacional = ['tecnico', 'operador', 'inspetor'].includes(role);
  const isPCM = role === 'pcm';
  const isSupervisor = role === 'supervisor';
  const isGerente = role === 'gerente';
  
  const menuGroups = isGerente ? [
    {
      label: 'GESTÃO',
      items: [
        { icon: LayoutDashboard, label: 'Central de Trabalho', path: '/' },
        { icon: BarChart3, label: 'Dashboard', path: '/dashboard' },
        { icon: Wrench, label: 'Ordens de Serviço', path: '/os' },
        { icon: Box, label: 'Ativos', path: '/ativos' },
        { icon: Shield, label: 'Auditoria', path: '/admin/auditoria' },
      ]
    },
  ] : [
    {
      label: 'PRINCIPAL',
      items: [
        { icon: LayoutDashboard, label: isOperacional ? 'Minha Jornada' : 'Central de Trabalho', path: '/' },
        ...(!isOperacional ? [{ icon: BarChart3, label: 'Dashboard', path: '/dashboard' }] : []),
        ...(!isOperacional ? [{ icon: Users, label: 'Equipe', path: '/equipe' }] : []),
      ]
    },
    {
      label: 'OPERAÇÃO',
      items: [
        { icon: Box, label: 'Ativos', path: '/ativos' },
        ...(!isOperacional ? [{ icon: Wrench, label: 'Ordens de Serviço', path: '/os' }] : []),
        { icon: ClipboardCheck, label: 'Inspeções', path: '/inspecoes' },
        { icon: AlertTriangle, label: isOperacional ? 'Solicitar Serviço' : 'Anomalias', path: isOperacional ? '/solicitar' : '/anomalias' },
        ...(isOperacional ? [{ icon: QrCode, label: 'Scanner', path: '/scanner' }] : []),
        ...(isOperacional ? [{ icon: Target, label: 'Ronda', path: '/ronda' }] : []),
      ]
    },
    ...(!isOperacional ? [{
      label: 'INFRAESTRUTURA',
      items: [
        ...(isAdmin ? [{ icon: Factory, label: 'Unidades', path: '/unidades' }] : []),
        { icon: Layers, label: 'Áreas', path: '/setores' },
      ]
    }] : []),
    {
      label: 'MATERIAIS',
      items: [
        { icon: Package, label: 'Estoque', path: '/estoque' },
        ...(!isOperacional ? [{ icon: Cog, label: 'Sobressalentes', path: '/sobressalentes' }] : []),
        ...(!isOperacional ? [{ icon: Calendar, label: 'Paradas', path: '/paradas' }] : []),
      ]
    },
    ...(['admin','master','pcm'].includes(role) ? [{
      label: 'PCM',
      items: [
        { icon: BookOpen, label: 'Biblioteca', path: '/biblioteca' },
      ]
    }] : []),
    ...(isAdmin || isPCM || isSupervisor ? [{
      label: 'ADMIN',
      items: [
        ...(isAdmin ? [{ icon: Users, label: 'Usuários', path: '/admin/usuarios' }] : []),
        ...(isAdmin || isPCM ? [{ icon: ClipboardCheck, label: 'Planos de Inspeção', path: '/admin/templates' }] : []),
        { icon: Shield, label: 'Auditoria', path: '/admin/auditoria' },
        ...(isAdmin ? [{ icon: Cog, label: 'Configurações', path: '/admin/config' }] : []),
        ...(isMaster ? [{ icon: Palette, label: 'White Label', path: '/master/white-label' }] : []),
        ...(isMaster ? [{ icon: Trash2, label: 'Limpeza', path: '/master/cleanup' }] : []),
      ]
    }] : []),
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
            {!collapsed && (
              <p className="px-4 mb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">{group.label}</p>
            )}
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
              
              return (
                <button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 transition-all ${collapsed ? 'justify-center' : ''}`}
                  style={isActive ? {
                    backgroundColor: `${b.cor_primaria || 'var(--brand-primary)'}15`,
                    color: b.cor_primaria || 'var(--brand-primary)',
                    borderLeft: `2px solid ${b.cor_primaria || 'var(--brand-primary)'}`,
                  } : {
                    color: '#94a3b8',
                    borderLeft: '2px solid transparent',
                  }}
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
              <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
            </div>
          </div>
        )}
        <button 
          onClick={() => { logout(); navigate('/login'); }}
          className={`w-full flex items-center gap-2 px-3 py-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors ${collapsed ? 'justify-center' : ''}`}
          title={collapsed ? 'Sair' : undefined}
        >
          <LogOut size={18} />
          {!collapsed && <span className="text-sm">Sair</span>}
        </button>
      </div>
    </aside>
  );
};

// Mobile Bottom Nav
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
    <nav className="fixed bottom-0 left-0 right-0 backdrop-blur-sm border-t border-slate-800 z-40 pb-safe md:hidden"
      style={{ backgroundColor: `${b.cor_menu || 'var(--brand-menu)'}f2` }} data-testid="bottom-nav">
      <div className="flex items-center justify-around h-16">
        {items.map((item, idx) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
          
          if (item.special) {
            return (
              <button key={idx} onClick={() => navigate(item.path)} className="scan-button pulse-glow"
                style={{ backgroundColor: b.cor_primaria || 'var(--brand-primary)' }}>
                <Icon size={26} />
              </button>
            );
          }
          
          return (
            <button
              key={idx}
              onClick={() => navigate(item.path)}
              className="nav-item"
              style={isActive ? { color: b.cor_primaria || 'var(--brand-primary)' } : {}}
            >
              <Icon size={20} />
              <span className="text-[10px] mt-1">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};

// ============== PAGES ==============

// Login
const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState('selectOrg'); // selectOrg, login, forgot, reset, forceChange
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [tempToken, setTempToken] = useState('');
  const [orgSearch, setOrgSearch] = useState('');
  const { login } = useAuth();
  const { branding, organizations, selectOrg, orgId, loadOrganizations } = useBranding();
  const navigate = useNavigate();

  useEffect(() => { loadOrganizations(); }, [loadOrganizations]);

  // Auto-skip org selector if only 1 org or org already selected (subdomain)
  useEffect(() => {
    if (orgId) setView('login');
    else if (organizations.length === 1) { selectOrg(organizations[0].id); setView('login'); }
  }, [organizations, orgId, selectOrg]);

  const handleSelectOrg = (org) => {
    selectOrg(org.id);
    setView('login');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      if (response.data.user?.force_password_change) {
        setTempToken(response.data.access_token);
        setView('forceChange');
        toast.info('Você precisa trocar sua senha');
      } else {
        login(response.data);
        toast.success('Login realizado!');
        navigate('/');
      }
    } catch (error) {
      toast.error(normalizeError(error));
    } finally { setLoading(false); }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!email) { toast.error('Informe seu email'); return; }
    setLoading(true);
    try {
      const res = await axios.post(`${API}/auth/forgot-password`, { email });
      setResetToken(res.data.token || '');
      setView('reset');
      toast.success('Token de redefinição gerado!');
    } catch (error) { toast.error(normalizeError(error)); }
    finally { setLoading(false); }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (newPassword.length < 6) { toast.error('Senha deve ter pelo menos 6 caracteres'); return; }
    if (newPassword !== confirmPassword) { toast.error('As senhas não coincidem'); return; }
    setLoading(true);
    try {
      await axios.post(`${API}/auth/reset-password`, { token: resetToken, new_password: newPassword });
      toast.success('Senha redefinida! Faça login.');
      setView('login'); setNewPassword(''); setConfirmPassword('');
    } catch (error) { toast.error(normalizeError(error)); }
    finally { setLoading(false); }
  };

  const handleForceChange = async (e) => {
    e.preventDefault();
    if (newPassword.length < 6) { toast.error('Senha deve ter pelo menos 6 caracteres'); return; }
    if (newPassword !== confirmPassword) { toast.error('As senhas não coincidem'); return; }
    setLoading(true);
    try {
      await axios.post(`${API}/auth/change-password`, { new_password: newPassword }, { headers: { Authorization: `Bearer ${tempToken}` } });
      toast.success('Senha alterada! Faça login com a nova senha.');
      setView('login'); setPassword(''); setNewPassword(''); setConfirmPassword('');
    } catch (error) { toast.error(normalizeError(error)); }
    finally { setLoading(false); }
  };

  const filteredOrgs = organizations.filter(o =>
    !orgSearch || (o.nome || '').toLowerCase().includes(orgSearch.toLowerCase())
  );

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: branding.cor_login }} data-testid="login-page">
      <div className="w-full max-w-md">
        {/* Branding Header */}
        <div className="text-center mb-8">
          {branding.logo_url ? (
            <img src={branding.logo_url} alt={branding.nome_empresa} className="h-16 mx-auto mb-4 object-contain" data-testid="login-logo" />
          ) : (
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 border border-opacity-30" style={{ backgroundColor: branding.cor_primaria + '15', borderColor: branding.cor_primaria + '50' }}>
              <Cog size={32} style={{ color: branding.cor_primaria }} />
            </div>
          )}
          <h1 className="text-3xl font-bold tracking-wider" style={{ color: branding.cor_primaria }} data-testid="login-title">{branding.nome_empresa}</h1>
          <p className="text-slate-500 mt-1 text-sm">{view === 'selectOrg' ? 'Selecione sua empresa' : branding.texto_login}</p>
        </div>

        {/* ORG SELECTOR */}
        {view === 'selectOrg' && (
          <div className="glass-card p-6 space-y-4" data-testid="org-selector">
            {organizations.length > 5 && (
              <input value={orgSearch} onChange={e => setOrgSearch(e.target.value)} className="input-industrial w-full px-4" placeholder="Pesquisar empresa..." data-testid="org-search" />
            )}
            <div className="space-y-2 max-h-[400px] overflow-y-auto custom-scrollbar">
              {filteredOrgs.map(org => (
                <button key={org.id} onClick={() => handleSelectOrg(org)}
                  className="w-full flex items-center gap-4 p-4 rounded-lg border border-slate-800 hover:border-slate-600 bg-slate-900/50 transition-all text-left group"
                  data-testid={`org-option-${org.id}`}
                >
                  {org.logo_url ? (
                    <img src={org.logo_url} alt="" className="w-10 h-10 rounded-lg object-contain bg-slate-800 p-1" />
                  ) : (
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm" style={{ backgroundColor: org.cor_primaria || '#10b981' }}>
                      {(org.nome || 'M').substring(0, 2).toUpperCase()}
                    </div>
                  )}
                  <div className="flex-1">
                    <p className="text-slate-100 font-semibold group-hover:text-white">{org.nome}</p>
                    {org.subdominio && <p className="text-[10px] text-slate-600">{org.subdominio}.maintrix.com.br</p>}
                  </div>
                  <ChevronRight size={18} className="text-slate-600 group-hover:text-slate-400" />
                </button>
              ))}
              {filteredOrgs.length === 0 && <p className="text-center text-slate-500 py-4 text-sm">Nenhuma empresa encontrada</p>}
            </div>
          </div>
        )}

        {/* LOGIN */}
        {view === 'login' && (
          <form onSubmit={handleLogin} className="glass-card p-6 space-y-4" data-testid="login-form">
            <FormInput label="Email">
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-industrial w-full px-4" placeholder="seu@email.com" required data-testid="login-email" />
            </FormInput>
            <FormInput label="Senha">
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input-industrial w-full px-4" placeholder="Sua senha" required data-testid="login-password" />
            </FormInput>
            <button type="submit" disabled={loading} className="w-full py-3 rounded-lg font-semibold text-white transition-all" style={{ backgroundColor: branding.cor_primaria }} data-testid="login-submit">
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
            <div className="flex items-center justify-between">
              <button type="button" onClick={() => setView('forgot')} className="text-sm text-slate-400 hover:text-slate-200 transition-colors" data-testid="forgot-password-link">Esqueci minha senha</button>
              {organizations.length > 1 && <button type="button" onClick={() => { setView('selectOrg'); }} className="text-sm text-slate-500 hover:text-slate-300">Trocar empresa</button>}
            </div>
          </form>
        )}

        {/* FORGOT PASSWORD */}
        {view === 'forgot' && (
          <form onSubmit={handleForgotPassword} className="glass-card p-6 space-y-4" data-testid="forgot-form">
            <div className="text-center mb-2"><Lock size={32} className="mx-auto text-amber-400 mb-2" /><h2 className="text-lg font-semibold text-slate-200">Redefinir Senha</h2></div>
            <FormInput label="Email cadastrado"><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-industrial w-full px-4" placeholder="seu@email.com" required data-testid="forgot-email" /></FormInput>
            <button type="submit" disabled={loading} className="btn-primary w-full">{loading ? 'Enviando...' : 'Solicitar Redefinição'}</button>
            <button type="button" onClick={() => setView('login')} className="w-full text-sm text-slate-400 hover:text-slate-200 py-2">Voltar ao login</button>
          </form>
        )}

        {/* RESET PASSWORD */}
        {view === 'reset' && (
          <form onSubmit={handleResetPassword} className="glass-card p-6 space-y-4" data-testid="reset-form">
            <div className="text-center mb-2"><Shield size={32} className="mx-auto text-brand mb-2" /><h2 className="text-lg font-semibold text-slate-200">Nova Senha</h2></div>
            <FormInput label="Token"><input type="text" value={resetToken} onChange={(e) => setResetToken(e.target.value)} className="input-industrial w-full px-4 font-mono text-sm" required data-testid="reset-token" /></FormInput>
            <FormInput label="Nova Senha"><input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="input-industrial w-full px-4" required data-testid="reset-new-password" /></FormInput>
            <FormInput label="Confirmar"><input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="input-industrial w-full px-4" required /></FormInput>
            <button type="submit" disabled={loading} className="btn-primary w-full">{loading ? 'Redefinindo...' : 'Redefinir Senha'}</button>
            <button type="button" onClick={() => setView('login')} className="w-full text-sm text-slate-400 hover:text-slate-200 py-2">Voltar ao login</button>
          </form>
        )}

        {/* FORCE CHANGE */}
        {view === 'forceChange' && (
          <form onSubmit={handleForceChange} className="glass-card p-6 space-y-4" data-testid="force-change-form">
            <div className="text-center mb-2"><AlertTriangle size={32} className="mx-auto text-amber-400 mb-2" /><h2 className="text-lg font-semibold text-slate-200">Troca de Senha Obrigatória</h2></div>
            <FormInput label="Nova Senha"><input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="input-industrial w-full px-4" required /></FormInput>
            <FormInput label="Confirmar"><input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="input-industrial w-full px-4" required /></FormInput>
            <button type="submit" disabled={loading} className="btn-primary w-full">{loading ? 'Alterando...' : 'Alterar Senha e Entrar'}</button>
          </form>
        )}

        {/* Footer */}
        <div className="mt-6 text-center">
          {branding.mostrar_powered_by && <p className="text-[10px] text-slate-700">Powered by MAINTRIX</p>}
        </div>
      </div>
    </div>
  );
};

// Dashboard
// ============== CENTRAL DE TRABALHO (role-adaptive) ==============

const centralTitles = {
  master: 'Central Executiva',
  admin: 'Central Administrativa', 
  pcm: 'Central PCM',
  supervisor: 'Central Supervisor',
  tecnico: 'Central do Técnico',
  operador: 'Central Operacional',
  inspetor: 'Central do Inspetor',
  gerente: 'Painel Gerencial',
};

const prioColors = { emergencia: 'bg-red-500', alta: 'bg-orange-500', media: 'bg-amber-500', baixa: 'bg-blue-500' };
const prioLabels = { emergencia: 'Emergência', alta: 'Alta', media: 'Média', baixa: 'Baixa' };

const AtividadeCard = ({ item, tipo, navigate }) => {
  const isOS = tipo === 'os';
  const tag = item.ativo?.tag || '';
  const nome = item.ativo?.nome || '';
  const titulo = isOS ? item.titulo : (item.plano_nome || `${item.tipo || 'Inspeção'}`);
  const rota = isOS ? `/os/${item.id}` : `/inspecoes/${item.id}`;
  const prioColor = isOS ? (prioColors[item.prioridade] || 'bg-slate-600') : 'bg-emerald-500';
  const tipoLabel = isOS
    ? ({corretiva:'Corretiva',preventiva:'Preventiva',lubrificacao:'Lubrificação',inspecao:'Inspeção',emergencial:'Emergencial',calibracao:'Calibração',melhoria:'Melhoria'}[item.tipo] || item.tipo)
    : ({inspecao:'Inspeção',preventiva:'Preventiva',lubrificacao:'Lubrificação',limpeza:'Limpeza',mecanica:'Mecânica',eletrica:'Elétrica'}[item.tipo] || item.tipo || 'Inspeção');
  const tempoEstimado = item.tempo_estimado_minutos || item.duracao_estimada;

  return (
    <div
      className="flex items-center gap-3 p-3 rounded-lg border border-slate-800 hover:border-slate-600 bg-slate-900/50 cursor-pointer transition-all group active:scale-[0.99]"
      onClick={() => navigate(rota)}
      data-testid={`atividade-${item.id}`}
    >
      <div className={`w-1.5 h-12 rounded-full ${prioColor} shrink-0`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-brand text-xs">{tag}</span>
          <span className="text-slate-300 text-sm truncate">{nome}</span>
        </div>
        <p className="text-slate-100 text-sm font-medium truncate">{titulo}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 capitalize">{tipoLabel}</span>
          {item.disciplina && <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-500 capitalize">{item.disciplina}</span>}
          {isOS && item.numero && <span className="text-[10px] text-slate-600">#{item.numero}</span>}
          {tempoEstimado && <span className="text-[10px] text-slate-500 flex items-center gap-0.5"><Clock size={10} />{tempoEstimado >= 60 ? `${Math.floor(tempoEstimado/60)}h${tempoEstimado%60 > 0 ? (tempoEstimado%60)+'min' : ''}` : `${tempoEstimado}min`}</span>}
        </div>
      </div>
      <div className="text-right shrink-0">
        {item.data_planejada || item.data_programada ? (
          <span className="text-[10px] text-slate-500">{new Date(item.data_planejada || item.data_programada).toLocaleDateString('pt-BR')}</span>
        ) : null}
        <ChevronRight size={16} className="text-slate-700 group-hover:text-slate-400 transition-colors ml-auto" />
      </div>
    </div>
  );
};

const SectionBlock = ({ title, icon: Icon, count, color, children, defaultOpen = true }) => {
  const [open, setOpen] = useState(defaultOpen);
  if (count === 0) return null;
  return (
    <div className="space-y-2" data-testid={`section-${title.toLowerCase().replace(/\s/g,'-')}`}>
      <button onClick={() => setOpen(!open)} className="flex items-center gap-2 w-full text-left group">
        <div className={`w-6 h-6 rounded flex items-center justify-center ${color}`}>
          <Icon size={14} className="text-white" />
        </div>
        <span className="text-sm font-semibold text-slate-200 flex-1">{title}</span>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${color} text-white`}>{count}</span>
        <ChevronDown size={14} className={`text-slate-500 transition-transform ${open ? '' : '-rotate-90'}`} />
      </button>
      {open && <div className="space-y-1.5 ml-1">{children}</div>}
    </div>
  );
};

const CentralTrabalhoPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await api.get('/central');
        setData(res.data);
      } catch { toast.error('Erro ao carregar central'); }
      finally { setLoading(false); }
    };
    fetch();
    const interval = setInterval(fetch, 60000); // refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading) return <Loading rows={6} />;
  if (!data) return null;

  const role = data.role;
  const titulo = centralTitles[role] || 'Central de Trabalho';

  return (
    <div className="space-y-6" data-testid="central-trabalho">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">{titulo}</h1>
          <p className="text-sm text-slate-500">
            {data.user_nome}{data.turno ? ` • Turno ${data.turno}` : ''} • {new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-2xl font-bold text-slate-100">{data.total_atividades}</p>
            <p className="text-[10px] text-slate-500 uppercase">Atividades</p>
          </div>
          <button onClick={() => { setLoading(true); api.get('/central').then(r => setData(r.data)).finally(() => setLoading(false)); }} className="p-2 hover:bg-slate-800 rounded-lg transition-colors" data-testid="central-refresh">
            <RefreshCw size={18} className="text-slate-400" />
          </button>
        </div>
      </div>

      {/* Quick stats for supervisors/admin */}
      {data.resumo && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="glass-card p-3 text-center">
            <p className="text-xl font-bold text-slate-100">{data.resumo.total_os_abertas}</p>
            <p className="text-[10px] text-slate-500 uppercase">OS Abertas</p>
          </div>
          <div className="glass-card p-3 text-center">
            <p className="text-xl font-bold text-slate-100">{data.resumo.total_insp_pendentes}</p>
            <p className="text-[10px] text-slate-500 uppercase">Inspeções Pendentes</p>
          </div>
          <div className="glass-card p-3 text-center">
            <p className="text-xl font-bold text-slate-100">{data.resumo.total_ativos}</p>
            <p className="text-[10px] text-slate-500 uppercase">Ativos</p>
          </div>
          <div className="glass-card p-3 text-center">
            <p className="text-xl font-bold text-amber-400">{data.resumo.ativos_parados}</p>
            <p className="text-[10px] text-slate-500 uppercase">Parados</p>
          </div>
        </div>
      )}

      {/* Vencidas */}
      <SectionBlock title="Atividades Vencidas" icon={AlertTriangle} count={data.vencidas.total} color="bg-red-600" defaultOpen={true}>
        {data.vencidas.os.map(o => <AtividadeCard key={o.id} item={o} tipo="os" navigate={navigate} />)}
        {data.vencidas.inspecoes.map(i => <AtividadeCard key={i.id} item={i} tipo="inspecao" navigate={navigate} />)}
      </SectionBlock>

      {/* Em execução */}
      <SectionBlock title="Em Execução" icon={Play} count={data.em_execucao.total} color="bg-blue-600" defaultOpen={true}>
        {data.em_execucao.os.map(o => <AtividadeCard key={o.id} item={o} tipo="os" navigate={navigate} />)}
        {data.em_execucao.inspecoes.map(i => <AtividadeCard key={i.id} item={i} tipo="inspecao" navigate={navigate} />)}
      </SectionBlock>

      {/* Hoje */}
      <SectionBlock title="Para Hoje" icon={Calendar} count={data.hoje.total} color="bg-amber-600" defaultOpen={true}>
        {data.hoje.os.map(o => <AtividadeCard key={o.id} item={o} tipo="os" navigate={navigate} />)}
        {data.hoje.inspecoes.map(i => <AtividadeCard key={i.id} item={i} tipo="inspecao" navigate={navigate} />)}
      </SectionBlock>

      {/* Semana */}
      <SectionBlock title="Esta Semana" icon={Calendar} count={data.semana.total} color="bg-blue-500" defaultOpen={data.hoje.total === 0}>
        {data.semana.os.map(o => <AtividadeCard key={o.id} item={o} tipo="os" navigate={navigate} />)}
        {data.semana.inspecoes.map(i => <AtividadeCard key={i.id} item={i} tipo="inspecao" navigate={navigate} />)}
      </SectionBlock>

      {/* Sem data (backlog) */}
      <SectionBlock title="Sem Data Planejada" icon={Clock} count={data.sem_data.total} color="bg-slate-600" defaultOpen={false}>
        {data.sem_data.os.map(o => <AtividadeCard key={o.id} item={o} tipo="os" navigate={navigate} />)}
      </SectionBlock>

      {/* Role-specific: Planos pendentes */}
      {data.planos_pendentes && data.planos_pendentes.length > 0 && (
        <SectionBlock title="Planos Pendentes de Aprovação" icon={ClipboardCheck} count={data.planos_pendentes.length} color="bg-purple-600" defaultOpen={true}>
          {data.planos_pendentes.map(p => (
            <div key={p.id} className="flex items-center gap-3 p-3 rounded-lg border border-slate-800 bg-slate-900/50 cursor-pointer hover:border-slate-600" onClick={() => navigate('/admin/templates')} data-testid={`plano-pendente-${p.id}`}>
              <ClipboardCheck size={16} className="text-purple-400 shrink-0" />
              <div className="flex-1">
                <p className="text-sm text-slate-200">{p.nome}</p>
                <span className="text-[10px] text-slate-500">{(p.perguntas || []).length} perguntas • {p.tipo}</span>
              </div>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">{p.status}</span>
            </div>
          ))}
        </SectionBlock>
      )}

      {/* Role-specific: OS críticas */}
      {data.os_criticas && data.os_criticas.length > 0 && (
        <SectionBlock title="OS Críticas" icon={AlertCircle} count={data.os_criticas.length} color="bg-red-500" defaultOpen={true}>
          {data.os_criticas.map(o => <AtividadeCard key={o.id} item={o} tipo="os" navigate={navigate} />)}
        </SectionBlock>
      )}

      {/* Empty state */}
      {data.total_atividades === 0 && !data.resumo && (
        <div className="glass-card p-12 text-center">
          <CheckCircle size={48} className="text-emerald-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-200">Tudo em dia!</h3>
          <p className="text-sm text-slate-500 mt-1">Nenhuma atividade pendente no momento.</p>
        </div>
      )}
    </div>
  );
};


const DashboardPage = () => {
  const [kpis, setKpis] = useState(null);
  const [stats, setStats] = useState(null);
  const [trend, setTrend] = useState([]);
  const [loading, setLoading] = useState(true);
  const [drillModal, setDrillModal] = useState({ open: false, type: '', title: '', data: [] });
  const [drillLoading, setDrillLoading] = useState(false);
  const [sectors, setSectors] = useState([]);
  const [filterSector, setFilterSector] = useState('');
  const [osPorSetor, setOsPorSetor] = useState([]);
  const [osPorDisciplina, setOsPorDisciplina] = useState([]);
  const [ativosMaisFalhas, setAtivosMaisFalhas] = useState([]);
  const { user } = useAuth();
  const navigate = useNavigate();
  
  useEffect(() => {
    api.get('/sectors').then(r => setSectors(r.data)).catch(() => {});
  }, []);
  
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const params = {};
        if (filterSector) params.sector_id = filterSector;
        const [kpisRes, statsRes, trendRes, setorRes, discRes, falhasRes] = await Promise.all([
          api.get('/kpis', { params }),
          api.get('/dashboard/stats', { params }),
          api.get('/dashboard/trend', { params }),
          api.get('/dashboard/os-por-setor'),
          api.get('/dashboard/os-por-disciplina'),
          api.get('/dashboard/ativos-mais-falhas')
        ]);
        setKpis(kpisRes.data);
        setStats(statsRes.data);
        setTrend(trendRes.data);
        setOsPorSetor(setorRes.data);
        setOsPorDisciplina(discRes.data);
        setAtivosMaisFalhas(falhasRes.data);
      } catch (error) {
        toast.error('Erro ao carregar dashboard');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [filterSector]);

  const drillDown = async (type, title) => {
    setDrillLoading(true);
    setDrillModal({ open: true, type, title, data: [] });
    try {
      let data = [];
      if (type === 'backlog' || type === 'os_abertas') {
        const res = await api.get('/ordens-servico');
        data = res.data.filter(o => ['aberta','planejada','em_execucao','pausada'].includes(o.status));
      } else if (type === 'os_criticas') {
        const res = await api.get('/ordens-servico');
        data = res.data.filter(o => o.prioridade === 'critica' && !['concluida','cancelada'].includes(o.status));
      } else if (type === 'corretiva' || type === 'preventiva' || type === 'preditiva' || type === 'emergencia') {
        const res = await api.get('/ordens-servico');
        data = res.data.filter(o => o.tipo === type);
      } else if (type === 'mttr') {
        const res = await api.get('/ordens-servico');
        data = res.data.filter(o => o.status === 'concluida' && o.tempo_execucao_minutos);
      } else if (type === 'estoque_critico') {
        const res = await api.get('/estoque');
        data = res.data.filter(i => i.quantidade <= i.estoque_minimo);
      } else if (type === 'insp_pendentes') {
        const res = await api.get('/inspecoes');
        data = res.data.filter(i => i.status === 'pendente');
      } else if (type === 'nao_conformes') {
        const res = await api.get('/inspecoes');
        data = res.data.filter(i => i.resultado === 'nao_conforme');
      }
      setDrillModal(prev => ({ ...prev, data }));
    } catch { toast.error('Erro ao carregar detalhes'); }
    finally { setDrillLoading(false); }
  };

  const handleExport = async (entity, format) => {
    try {
      const res = await api.get(`/export/${entity}?format=${format}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${entity}_export.${format === 'excel' ? 'xlsx' : 'csv'}`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success(`${entity} exportado com sucesso`);
    } catch { toast.error('Erro ao exportar'); }
  };

  const getColor = (value, thresholds) => {
    if (value >= thresholds[0]) return 'text-emerald-400';
    if (value >= thresholds[1]) return 'text-amber-400';
    return 'text-red-400';
  };
  const getBg = (value, thresholds) => {
    if (value >= thresholds[0]) return 'border-emerald-500/30 bg-emerald-500/5';
    if (value >= thresholds[1]) return 'border-amber-500/30 bg-amber-500/5';
    return 'border-red-500/30 bg-red-500/5';
  };
  const getInverseColor = (value, thresholds) => {
    if (value <= thresholds[0]) return 'text-emerald-400';
    if (value <= thresholds[1]) return 'text-amber-400';
    return 'text-red-400';
  };
  const getInverseBg = (value, thresholds) => {
    if (value <= thresholds[0]) return 'border-emerald-500/30 bg-emerald-500/5';
    if (value <= thresholds[1]) return 'border-amber-500/30 bg-amber-500/5';
    return 'border-red-500/30 bg-red-500/5';
  };
  
  if (loading) return <Loading rows={8} />;
  if (!kpis || !stats) return null;
  
  const backlog = kpis.backlog_total || 0;
  const osAbertas = (stats?.ordens_servico?.abertas || 0) + (stats?.ordens_servico?.em_execucao || 0) + (stats?.ordens_servico?.pausadas || 0);
  const osCriticas = stats?.ordens_servico?.por_prioridade?.critica || 0;
  const estoqueCritico = stats?.estoque?.criticos || 0;
  const inspPendentes = stats?.inspecoes?.pendentes || 0;
  const naoConformes = stats?.inspecoes?.nao_conformes_mes || 0;
  
  // OS distribution from trend data (aggregated 6 months)
  const osTrendTotals = trend.reduce((acc, m) => ({
    corretiva: acc.corretiva + (m.corretivas || 0),
    preventiva: acc.preventiva + (m.preventivas || 0),
  }), { corretiva: 0, preventiva: 0 });
  
  const prevPercent = 0;
  const corrPercent = 0;
  
  const osTypes = [
    { name: 'Lubrificação', fill: '#06b6d4', key: 'lubrificacao' },
    { name: 'Limpeza', fill: '#8b5cf6', key: 'limpeza_organizacao' },
    { name: 'Preventiva', fill: '#10b981', key: 'preventiva' },
    { name: 'Corretiva', fill: '#ef4444', key: 'corretiva' },
    { name: 'Prep. Material', fill: '#f59e0b', key: 'preparacao_material' },
    { name: 'Fabricação', fill: '#3b82f6', key: 'fabricacao_melhorias' },
  ].map(t => ({ ...t, value: stats?.ordens_servico?.por_tipo?.[t.key] || osTrendTotals[t.key] || 0 }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100" data-testid="dashboard-title">Dashboard Operacional</h1>
          <p className="text-sm text-slate-500">Monitoramento em tempo real da confiabilidade e desempenho operacional dos ativos</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-1.5" data-testid="dashboard-filters">
            <Filter size={14} className="text-slate-500" />
            <select
              value={filterSector}
              onChange={(e) => setFilterSector(e.target.value)}
              className="bg-transparent text-sm text-slate-300 border-none outline-none cursor-pointer"
              data-testid="filter-sector"
            >
              <option value="">Todas as Áreas</option>
              {sectors.map(s => <option key={s.id} value={s.id}>{s.nome}</option>)}
            </select>
            {filterSector && (
              <button onClick={() => setFilterSector('')} className="text-xs text-red-400 hover:text-red-300 ml-1" data-testid="clear-filters">
                <X size={14} />
              </button>
            )}
          </div>
          <div className="relative group">
            <button className="btn-secondary flex items-center gap-2 text-sm" data-testid="export-data-btn">
              <Download size={16} /> Exportar Dados
            </button>
            <div className="absolute right-0 top-full mt-1 w-56 bg-slate-800 border border-slate-700 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 py-2">
              {[{label:'OS - Excel', e:'ordens-servico', f:'excel'}, {label:'OS - CSV', e:'ordens-servico', f:'excel'}, {label:'Ativos - Excel', e:'ativos', f:'excel'}, {label:'Inspeções - Excel', e:'inspecoes', f:'excel'}, {label:'Estoque - Excel', e:'estoque', f:'excel'}].map(item => (
                <button key={item.label} onClick={() => handleExport(item.e, item.f)} className="w-full px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 text-left flex items-center gap-2">
                  <FileText size={14} /> {item.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* BLOCO 1 - VISÃO EXECUTIVA */}
      <div>
        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Visão Executiva</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getBg(kpis.disponibilidade_percent, [90, 75])}`} onClick={() => navigate('/ativos')} data-testid="kpi-disponibilidade">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Disponibilidade</p>
            <p className={`text-4xl font-black tabular-nums ${getColor(kpis.disponibilidade_percent, [90, 75])}`}>{kpis.disponibilidade_percent}<span className="text-lg">%</span></p>
            <p className="text-xs text-slate-600 mt-1">{kpis.ativos_total} ativos cadastrados</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(backlog, [5, 15])}`} onClick={() => drillDown('backlog', 'Backlog de OS')} data-testid="kpi-backlog">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Backlog</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(backlog, [5, 15])}`}>{backlog}</p>
            <p className="text-xs text-slate-600 mt-1">ordens em aberto</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(osAbertas, [5, 15])}`} onClick={() => drillDown('os_abertas', 'OS Abertas')} data-testid="kpi-os-abertas">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">OS Abertas</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(osAbertas, [5, 15])}`}>{osAbertas}</p>
            <p className="text-xs text-slate-600 mt-1">aguardando execução</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(osCriticas, [0, 3])}`} onClick={() => drillDown('os_criticas', 'Ordens Críticas')} data-testid="kpi-os-criticas">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Ordens Críticas</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(osCriticas, [0, 3])}`}>{osCriticas}</p>
            <p className="text-xs text-slate-600 mt-1">prioridade máxima</p>
          </div>
        </div>
      </div>

      {/* BLOCO 2 - PERFORMANCE */}
      <div>
        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Performance</h2>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getBg(kpis.mtbf_horas, [500, 200])}`} onClick={() => drillDown('mttr', 'Histórico MTBF/MTTR')} data-testid="kpi-mtbf">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">MTBF</p>
            <p className={`text-4xl font-black tabular-nums ${getColor(kpis.mtbf_horas, [500, 200])}`}>{kpis.mtbf_horas}<span className="text-lg">h</span></p>
            <p className="text-xs text-slate-600 mt-1">tempo médio entre falhas</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(kpis.mttr_horas, [2, 8])}`} onClick={() => drillDown('mttr', 'Histórico MTTR')} data-testid="kpi-mttr">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">MTTR</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(kpis.mttr_horas, [2, 8])}`}>{kpis.mttr_horas}<span className="text-lg">h</span></p>
            <p className="text-xs text-slate-600 mt-1">tempo médio de reparo</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getBg(prevPercent, [60, 40])}`} onClick={() => drillDown('preventiva', 'OS Preventivas')} data-testid="kpi-prev-corr">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Preventiva vs Corretiva</p>
            <div className="flex items-end gap-3 mt-1">
              <div>
                <p className="text-3xl font-black text-brand tabular-nums">{prevPercent}<span className="text-sm">%</span></p>
                <p className="text-[10px] text-brand">preventiva</p>
              </div>
              <div>
                <p className="text-3xl font-black text-red-400 tabular-nums">{corrPercent}<span className="text-sm">%</span></p>
                <p className="text-[10px] text-red-600">corretiva</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* BLOCO 3 - RISCO OPERACIONAL */}
      <div>
        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Risco Operacional</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(estoqueCritico, [0, 3])}`} onClick={() => drillDown('estoque_critico', 'Estoque Crítico')} data-testid="kpi-estoque-critico">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Estoque Crítico</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(estoqueCritico, [0, 3])}`}>{estoqueCritico}</p>
            <p className="text-xs text-slate-600 mt-1">itens abaixo do mínimo</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(inspPendentes, [2, 8])}`} onClick={() => drillDown('insp_pendentes', 'Inspeções Pendentes')} data-testid="kpi-insp-pendentes">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Inspeções Pendentes</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(inspPendentes, [2, 8])}`}>{inspPendentes}</p>
            <p className="text-xs text-slate-600 mt-1">aguardando execução</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(naoConformes, [0, 3])}`} onClick={() => drillDown('nao_conformes', 'Não Conformidades')} data-testid="kpi-nao-conformes">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Não Conformidades</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(naoConformes, [0, 3])}`}>{naoConformes}</p>
            <p className="text-xs text-slate-600 mt-1">inspeções com falha</p>
          </div>
        </div>
      </div>

      {/* GRÁFICOS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico 1 - Tendência MTBF/MTTR */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-300">Tendência MTBF / MTTR</h3>
            {trend.some(m => m.is_estimated) && (
              <span className="text-[10px] px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded" data-testid="estimated-label">Dados estimados nos meses sem histórico</span>
            )}
          </div>
          <div className="h-64" data-testid="chart-trend">
            <TrendChart data={trend} />
          </div>
        </div>

        {/* Gráfico 2 - Distribuição OS */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-300">Distribuição de OS por Tipo</h3>
            {trend.some(m => m.is_estimated) && (
              <span className="text-[10px] px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded">Inclui estimativas</span>
            )}
          </div>
          <div className="h-64" data-testid="chart-os-dist">
            <OSDistChart data={osTypes} onBarClick={(key) => drillDown(key, `OS ${key.charAt(0).toUpperCase() + key.slice(1)}`)} />
          </div>
        </div>
      </div>
      
      {/* Row 3 — New Dashboard Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* OS por Área */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5" data-testid="chart-os-setor">
          <h3 className="text-sm font-bold text-slate-300 mb-4 flex items-center gap-2"><Layers size={16} className="text-brand" /> OS por Área</h3>
          <div className="space-y-2">
            {osPorSetor.length === 0 ? <p className="text-xs text-slate-600 text-center py-4">Sem dados</p> :
            osPorSetor.map((s, i) => (
              <div key={i} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: s.cor }} />
                <span className="text-xs text-slate-400 flex-1 truncate">{s.sector}</span>
                <span className="text-sm font-mono font-bold text-slate-200">{s.os_abertas}</span>
              </div>
            ))}
          </div>
        </div>
        
        {/* OS por Disciplina */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5" data-testid="chart-os-disciplina">
          <h3 className="text-sm font-bold text-slate-300 mb-4 flex items-center gap-2"><Wrench size={16} className="text-blue-400" /> OS por Disciplina</h3>
          <div className="space-y-2">
            {osPorDisciplina.map((d, i) => (
              <div key={i} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: d.cor }} />
                <span className="text-xs text-slate-400 flex-1">{d.disciplina}</span>
                <span className="text-sm font-mono font-bold text-slate-200">{d.count}</span>
              </div>
            ))}
          </div>
        </div>
        
        {/* Ativos com Mais Falhas */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5" data-testid="chart-ativos-falhas">
          <h3 className="text-sm font-bold text-slate-300 mb-4 flex items-center gap-2"><AlertTriangle size={16} className="text-red-400" /> Ativos com Mais Falhas</h3>
          <div className="space-y-2">
            {ativosMaisFalhas.length === 0 ? <p className="text-xs text-slate-600 text-center py-4">Nenhuma falha registrada</p> :
            ativosMaisFalhas.slice(0, 5).map((a, i) => (
              <div key={i} className="flex items-center gap-2 p-2 bg-slate-800/30 rounded-lg">
                <span className="text-xs font-mono text-brand w-16">{a.tag}</span>
                <span className="text-xs text-slate-400 flex-1 truncate">{a.nome}</span>
                <span className="text-xs text-slate-600">{a.sector}</span>
                <span className="text-sm font-mono font-bold text-red-400">{a.falhas}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Drill-Down Modal */}
      <Modal isOpen={drillModal.open} onClose={() => setDrillModal({open:false,type:'',title:'',data:[]})} title={drillModal.title} size="lg">
        {drillLoading ? <Loading rows={5} /> : (
          <div className="space-y-2 max-h-[60vh] overflow-y-auto custom-scrollbar">
            {drillModal.data.length === 0 ? (
              <p className="text-center text-slate-500 py-8">Nenhum registro encontrado</p>
            ) : drillModal.data.map((item, idx) => (
              <div key={item.id || idx} className="p-3 bg-slate-800/50 rounded-lg flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    {item.numero && <span className="font-mono text-xs text-blue-400">{item.numero}</span>}
                    {item.ativo && <span className="font-mono text-xs text-brand">{item.ativo.tag}</span>}
                    {item.tag && <span className="font-mono text-xs text-brand">{item.tag}</span>}
                    {item.sku && <span className="font-mono text-xs text-purple-400">{item.sku}</span>}
                    <span className="text-slate-100">{item.nome}</span>
                    {item.prioridade && <PriorityBadge priority={item.prioridade} />}
                    {item.severidade && <PriorityBadge priority={item.severidade} />}
                  </div>
                  <p className="text-sm text-slate-200">{item.titulo || item.nome || item.descricao || item.ativo?.nome || '—'}</p>
                  <p className="text-xs text-slate-500">
                    {item.tipo && <span className="capitalize mr-2">{item.tipo}</span>}
                    {item.status && <span className="capitalize mr-2">{item.status}</span>}
                    {item.tempo_execucao_minutos && <span>{item.tempo_execucao_minutos} min</span>}
                    {item.quantidade !== undefined && <span>Qtd: {item.quantidade} (min: {item.estoque_minimo})</span>}
                    {item.frequencia && <span className="capitalize">{item.frequencia}</span>}
                  </p>
                </div>
                <StatusBadge status={item.status || 'pendente'} size="sm" />
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
};

// Chart Components
const TrendChart = ({ data }) => {
  const { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } = require('recharts');
  const enriched = data.map(d => ({ ...d, mes_label: d.is_estimated ? `${d.mes}*` : d.mes }));
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={enriched} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="mes_label" tick={{ fill: '#94a3b8', fontSize: 12 }} stroke="#475569" />
        <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} stroke="#475569" />
        <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#e2e8f0' }} formatter={(value, name, props) => [value, `${name}${props.payload.is_estimated ? ' (estimado)' : ''}`]} />
        <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
        <Line type="monotone" dataKey="mtbf" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} name="MTBF (h)" />
        <Line type="monotone" dataKey="mttr" stroke="#ef4444" strokeWidth={2} dot={{ r: 4 }} name="MTTR (h)" />
      </LineChart>
    </ResponsiveContainer>
  );
};

const OSDistChart = ({ data, onBarClick }) => {
  const { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } = require('recharts');
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} stroke="#475569" />
        <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} stroke="#475569" allowDecimals={false} />
        <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#e2e8f0' }} />
        <Bar dataKey="value" radius={[6, 6, 0, 0]} cursor="pointer" onClick={(d) => onBarClick(d.key)}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

// Ativos Page
const AtivosPage = () => {
  const [ativos, setAtivos] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [osList, setOsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterSector, setFilterSector] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const fetchData = async () => {
    try {
      const params = {};
      if (filterSector) params.sector_id = filterSector;
      const [ativosRes, sectorsRes, osRes] = await Promise.all([
        api.get('/ativos', { params }),
        api.get('/sectors'),
        api.get('/ordens-servico')
      ]);
      setAtivos(ativosRes.data);
      setSectors(sectorsRes.data);
      setOsList(osRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };
  
  // A1: Compute dynamic status per ativo based on OS
  const getAtivoStatus = (ativoId) => {
    const ativoOS = osList.filter(os => os.ativo_id === ativoId && !['concluida','cancelada'].includes(os.status));
    if (ativoOS.some(os => os.equipamento_parado)) return { label: 'Parado', class: 'text-red-400 bg-red-500/10 border-red-500/30' };
    if (ativoOS.some(os => os.status === 'em_execucao')) return { label: 'Em Manutenção', class: 'text-amber-400 bg-amber-500/10 border-amber-500/30' };
    return { label: 'Operacional', class: 'text-emerald-400 bg-brand-10 border-emerald-500/30' };
  };

  // A2: Count open OS per ativo
  const getOsAbertasCount = (ativoId) => {
    return osList.filter(os => os.ativo_id === ativoId && !['concluida','cancelada'].includes(os.status)).length;
  };
  
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchData(); }, [filterSector]);
  
  const handleDelete = async () => {
    try {
      await api.delete(`/ativos/${deleteItem.id}`);
      toast.success('Ativo excluído!');
      setDeleteItem(null);
      fetchData();
    } catch (error) {
      toast.error('Erro ao excluir');
    }
  };
  
  const filtered = ativos.filter(a => {
    if (search) {
      const s = search.toLowerCase();
      return a.tag?.toLowerCase().includes(s) || a.nome?.toLowerCase().includes(s) || a.sector?.nome?.toLowerCase().includes(s);
    }
    return true;
  });
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-slate-100">Ativos</h1>
          <ExportButtons entity="ativos" />
        </div>
        {['admin','master'].includes(user?.role) && (
          <button onClick={() => { setEditItem(null); setShowModal(true); }} className="btn-primary flex items-center gap-2" data-testid="add-ativo-btn">
            <Plus size={20} /> Novo Ativo
          </button>
        )}
      </div>
      
      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por TAG, nome ou área..."
            className="input-industrial w-full pl-10 pr-4"
          />
        </div>
        <Select
          value={filterSector}
          onChange={setFilterSector}
          options={sectors.map(s => ({ value: s.id, label: s.nome }))}
          placeholder="Área"
          className="w-40"
        />
      </div>
      
      {loading ? <Loading rows={5} /> : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((ativo) => (
            <div key={ativo.id} className="glass-card p-4 hover:border-slate-600 transition-all group" data-testid={`ativo-card-${ativo.tag}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate(`/ativos/${ativo.id}`)}>
                  <div className="p-2 rounded-lg bg-brand-10">
                    <Box size={22} className="text-brand" />
                  </div>
                  <div>
                    {ativo.sector && <p className="text-xs text-slate-500 font-medium uppercase">{ativo.sector.nome}</p>}
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-brand text-sm">{ativo.tag}</span>
                      {/* A1: Status dinâmico */}
                      {(() => { const st = getAtivoStatus(ativo.id); return (
                        <span className={`${st.class} border text-[10px] px-1.5 py-0.5 rounded font-medium`} data-testid={`ativo-status-${ativo.tag}`}>{st.label}</span>
                      ); })()}
                      {/* A2: Contador OS abertas */}
                      {(() => { const c = getOsAbertasCount(ativo.id); return c > 0 ? (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/30 font-medium" data-testid={`ativo-os-count-${ativo.tag}`}>
                          <Wrench size={10} className="inline mr-0.5" />{c} OS
                        </span>
                      ) : null; })()}
                    </div>
                    <p className="text-slate-100">{ativo.nome}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {['admin','master'].includes(user?.role) && (
                    <div className="hidden group-hover:flex items-center gap-1">
                      <button onClick={() => { setEditItem(ativo); setShowModal(true); }} className="p-2 hover:bg-slate-700 rounded-lg">
                        <Edit size={16} className="text-slate-400" />
                      </button>
                      <button onClick={() => setDeleteItem(ativo)} className="p-2 hover:bg-red-500/10 rounded-lg">
                        <Trash2 size={16} className="text-red-400" />
                      </button>
                    </div>
                  )}
                  <ChevronRight className="text-slate-600" />
                </div>
              </div>
              <div className="mt-2 flex items-center gap-2 text-xs text-slate-500">
                {ativo.tipo_equipamento && <span className="bg-slate-800 px-2 py-0.5 rounded">{ativo.tipo_equipamento}</span>}
                {ativo.fabricante && <span>{ativo.fabricante}</span>}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon={Box} title="Nenhum ativo encontrado" description="Não há ativos com os filtros selecionados." action={() => setShowModal(true)} actionLabel="Criar Ativo" />
      )}
      
      <ModalNovoAtivo
        isOpen={showModal}
        onClose={() => { setShowModal(false); setEditItem(null); }}
        onSuccess={fetchData}
        editData={editItem}
      />
      
      <ConfirmDialog
        isOpen={!!deleteItem}
        onClose={() => setDeleteItem(null)}
        onConfirm={handleDelete}
        title="Excluir Ativo"
        message={`Tem certeza que deseja excluir o ativo "${deleteItem?.tag} - ${deleteItem?.nome}"?`}
        confirmText="Excluir"
        danger
      />
    </div>
  );
};

// Ativo Detail
const AtivoDetailPage = () => {
  const { id } = useParams();
  const [ativo, setAtivo] = useState(null);
  const [manuais, setManuais] = useState([]);
  const [historico, setHistorico] = useState([]);
  const [planosVinculados, setPlanosVinculados] = useState([]);
  const [saude, setSaude] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [activeTab, setActiveTab] = useState('prontuario');
  const [showBomModal, setShowBomModal] = useState(false);
  const [bomEdit, setBomEdit] = useState(null);
  const [bomForm, setBomForm] = useState({ nome: '', codigo: '', quantidade: 1, unidade: 'UN', observacoes: '' });
  const [bomSearch, setBomSearch] = useState(undefined);
  const [showDupModal, setShowDupModal] = useState(false);
  const [dupForm, setDupForm] = useState({ sector_id: '', tag: '', numero_serie: '' });
  const [dupSectors, setDupSectors] = useState([]);
  const [dupSaving, setDupSaving] = useState(false);
  const [showQRLabel, setShowQRLabel] = useState(false);
  const [histFilters, setHistFilters] = useState({ tipo: '', status: '', usuario_id: '', data_inicio: '', data_fim: '' });
  const [tecnicos, setTecnicos] = useState([]);
  const [timelineLimit, setTimelineLimit] = useState(20);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const fetchAtivo = async () => {
    try {
      const [ativoRes, manuaisRes, histRes, planosRes, saudeRes] = await Promise.all([
        api.get(`/ativos/${id}`),
        api.get(`/ativos/${id}/manuais`),
        api.get(`/ativos/${id}/historico`).catch(() => ({ data: [] })),
        api.get(`/planos-inspecao/por-ativo/${id}`).catch(() => ({ data: [] })),
        api.get(`/ativos/${id}/saude`).catch(() => ({ data: null })),
      ]);
      setAtivo(ativoRes.data);
      setManuais(manuaisRes.data);
      setHistorico(histRes.data);
      setPlanosVinculados(planosRes.data);
      setSaude(saudeRes.data);
    } catch (error) {
      toast.error('Ativo não encontrado');
      navigate('/ativos');
    } finally {
      setLoading(false);
    }
  };

  const fetchHistorico = async (filters = histFilters) => {
    try {
      const params = {};
      if (filters.tipo) params.tipo = filters.tipo;
      if (filters.status) params.status = filters.status;
      if (filters.usuario_id) params.usuario_id = filters.usuario_id;
      if (filters.data_inicio) params.data_inicio = filters.data_inicio;
      if (filters.data_fim) params.data_fim = filters.data_fim;
      const res = await api.get(`/ativos/${id}/historico`, { params });
      setHistorico(res.data);
    } catch { }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchAtivo(); api.get('/users/tecnicos').then(r => setTecnicos(r.data)).catch(() => {}); }, [id]);
  
  const handleUploadManual = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      await api.post(`/ativos/${id}/manual`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      toast.success('Documento carregado!');
      const res = await api.get(`/ativos/${id}/manuais`);
      setManuais(res.data);
    } catch (error) { toast.error(normalizeError(error)); }
    finally { setUploading(false); if (fileInputRef.current) fileInputRef.current.value = ''; }
  };

  const handleDeleteManual = async (manualId) => {
    try { await api.delete(`/manuais/${manualId}`); toast.success('Removido'); setManuais(prev => prev.filter(m => m.id !== manualId)); }
    catch (error) { toast.error(normalizeError(error)); }
  };

  if (loading) return <Loading rows={4} />;
  if (!ativo) return null;

  const criticidadeColors = { A: 'text-red-400 bg-red-500/10', B: 'text-amber-400 bg-amber-500/10', C: 'text-blue-400 bg-blue-500/10' };
  const statusColors = { operacional: 'text-emerald-400 bg-brand-10', parado: 'text-red-400 bg-red-500/10', manutencao: 'text-amber-400 bg-amber-500/10' };
  const tipoEventoConfig = {
    os: { color: 'border-blue-500', bg: 'bg-blue-500', icon: Wrench, label: 'OS' },
    inspecao: { color: 'border-emerald-500', bg: 'bg-emerald-500', icon: ClipboardCheck, label: 'Inspeção' },
    anomalia: { color: 'border-red-500', bg: 'bg-red-500', icon: AlertTriangle, label: 'Anomalia' },
    material: { color: 'border-amber-500', bg: 'bg-amber-500', icon: Package, label: 'Material' },
    parada: { color: 'border-purple-500', bg: 'bg-purple-500', icon: Calendar, label: 'Parada' },
  };

  const tabs = [
    { key: 'prontuario', label: 'Prontuário' },
    { key: 'timeline', label: `Timeline (${historico.length})` },
    { key: 'planos', label: `Planos (${planosVinculados.length})` },
    { key: 'os', label: `OS (${ativo.ordens_servico?.length || 0})` },
    { key: 'docs', label: `Docs (${manuais.length})` },
    { key: 'materiais', label: `BOM (${ativo.materiais?.length || 0})` },
  ];

  // Health card helper
  const SaudeItem = ({ label, data, icon: Icon, color }) => (
    <div className="flex items-center gap-3 p-2.5 rounded-lg bg-slate-800/30">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${color}`}>
        <Icon size={14} className="text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[10px] text-slate-500 uppercase">{label}</p>
        {data ? (
          <>
            <p className="text-xs text-slate-300">{new Date(data.data).toLocaleDateString('pt-BR')}</p>
            <p className="text-[10px] text-slate-500 truncate">{data.executor || '—'} {data.resultado ? `• ${data.resultado}` : ''}</p>
          </>
        ) : (
          <p className="text-xs text-slate-600">Nenhum registro</p>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-4" data-testid="prontuario-ativo">
      {/* ===== HEADER: Identificação ===== */}
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <button onClick={() => navigate('/ativos')} className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg"><ArrowLeft size={18} className="text-slate-400" /></button>
          <h1 className="text-xl font-bold text-slate-100">Prontuário do Ativo</h1>
          <div className="flex-1" />
          <button onClick={() => setShowQRLabel(true)} className="flex items-center gap-2 px-3 py-2 bg-brand-10 hover:bg-brand-20 text-brand rounded-lg text-xs font-medium transition-all" data-testid="qr-label-btn">
            <QrCode size={16} /> Etiqueta QR
          </button>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Left: Main info */}
          <div className="lg:col-span-2">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-xl bg-brand-20 flex items-center justify-center border border-slate-700 shrink-0">
                <Cog size={28} className="text-brand" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className="font-mono text-brand text-lg font-bold" data-testid="prontuario-tag">{ativo.tag}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[ativo.status] || 'text-slate-400 bg-slate-700'}`}>{ativo.status || 'Operacional'}</span>
                  {ativo.criticidade && <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${criticidadeColors[ativo.criticidade] || ''}`}>Crit. {ativo.criticidade}</span>}
                </div>
                <h2 className="text-lg text-slate-200 font-semibold" data-testid="prontuario-nome">{ativo.nome}</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-1 mt-3 text-sm">
                  <div><span className="text-slate-500">Área</span><p className="text-slate-300">{ativo.sector?.nome || '—'}</p></div>
                  <div><span className="text-slate-500">Tipo</span><p className="text-slate-300">{ativo.tipo_equipamento || '—'}</p></div>
                  <div><span className="text-slate-500">Fabricante</span><p className="text-slate-300">{ativo.fabricante || '—'}</p></div>
                  <div><span className="text-slate-500">Modelo</span><p className="text-slate-300">{ativo.modelo || '—'}</p></div>
                  <div><span className="text-slate-500">Nº Série</span><p className="text-slate-300">{ativo.numero_serie || '—'}</p></div>
                  <div><span className="text-slate-500">QR Code</span><p className="text-slate-300 font-mono text-xs">{ativo.qr_code?.substring(0,8) || '—'}</p></div>
                </div>
              </div>
            </div>
          </div>
          {/* Right: KPIs */}
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <p className="text-xl font-bold text-slate-100">{ativo.kpis?.total_os || 0}</p>
              <p className="text-[10px] text-slate-500 uppercase">Total OS</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <p className="text-xl font-bold text-blue-400">{ativo.kpis?.total_falhas || 0}</p>
              <p className="text-[10px] text-slate-500 uppercase">Falhas</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <p className="text-xl font-bold text-brand">{ativo.kpis?.disponibilidade_percent || 100}%</p>
              <p className="text-[10px] text-slate-500 uppercase">Disponibilidade</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <p className="text-xl font-bold text-amber-400">{ativo.kpis?.mtbf_horas || 0}h</p>
              <p className="text-[10px] text-slate-500 uppercase">MTBF</p>
            </div>
          </div>
        </div>
      </div>

      {/* ===== TABS ===== */}
      <div className="flex gap-1 bg-slate-900/50 rounded-lg p-1 overflow-x-auto">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)}
            className={`px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-all ${activeTab === t.key ? 'bg-brand-20 text-brand border border-brand-30' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'}`}
            data-testid={`tab-${t.key}`}
          >{t.label}</button>
        ))}
      </div>

      {/* ===== TAB: Prontuário (Saúde + Planos + OS resumo) ===== */}
      {activeTab === 'prontuario' && (
        <div className="space-y-4" data-testid="prontuario-tab">
          {/* Saúde do Equipamento */}
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2"><Activity size={16} className="text-brand" /> Saúde do Equipamento</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <SaudeItem label="Última Inspeção" data={saude?.ultima_inspecao} icon={ClipboardCheck} color="bg-emerald-600" />
              <SaudeItem label="Próxima Inspeção" data={saude?.proxima_inspecao} icon={Calendar} color="bg-blue-600" />
              <SaudeItem label="Última Preventiva" data={saude?.ultima_preventiva} icon={Shield} color="bg-purple-600" />
              <SaudeItem label="Próxima Preventiva" data={saude?.proxima_preventiva} icon={Calendar} color="bg-purple-500" />
              <SaudeItem label="Última Lubrificação" data={saude?.ultima_lubrificacao} icon={Droplet} color="bg-amber-600" />
              <SaudeItem label="Última OS" data={saude?.ultima_os} icon={Wrench} color="bg-blue-600" />
              <SaudeItem label="Última Anomalia" data={saude?.ultima_anomalia} icon={AlertTriangle} color="bg-red-600" />
              <div className="flex items-center gap-3 p-2.5 rounded-lg bg-slate-800/30">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-slate-600"><Clock size={14} className="text-white" /></div>
                <div><p className="text-[10px] text-slate-500 uppercase">MTTR</p><p className="text-xs text-slate-300">{ativo.kpis?.mttr_horas || 0}h</p></div>
              </div>
            </div>
          </div>

          {/* Planos Permanentes */}
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2"><ClipboardCheck size={16} className="text-brand" /> Planos Permanentes ({planosVinculados.length})</h3>
            {planosVinculados.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {planosVinculados.map(p => {
                  const discColors = { mecanica: 'bg-brand-20 text-brand', eletrica: 'bg-blue-500/20 text-blue-400', lubrificacao: 'bg-amber-500/20 text-amber-400', producao: 'bg-slate-500/20 text-slate-400', instrumentacao: 'bg-purple-500/20 text-purple-400' };
                  return (
                    <div key={p.id} className="p-3 rounded-lg border border-slate-800 bg-slate-800/30 hover:border-slate-600 transition-all" data-testid={`plano-perm-${p.id}`}>
                      <p className="text-sm text-slate-200 font-medium truncate">{p.nome}</p>
                      <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded capitalize ${discColors[p.disciplina] || 'bg-slate-700 text-slate-400'}`}>{p.disciplina}</span>
                        <span className="text-[10px] text-brand bg-brand-10 px-1.5 py-0.5 rounded">{p.status}</span>
                        <span className="text-[10px] text-slate-500">{(p.perguntas || []).length}q • v{p.versao || 1}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-slate-600 text-center py-4">Nenhum plano aprovado vinculado a este ativo.</p>
            )}
          </div>

          {/* OS Abertas resumo */}
          {(ativo.ordens_servico || []).filter(o => !['concluida','cancelada'].includes(o.status)).length > 0 && (
            <div className="glass-card p-4">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2"><Wrench size={16} className="text-blue-400" /> OS em Aberto</h3>
              <div className="space-y-2">
                {(ativo.ordens_servico || []).filter(o => !['concluida','cancelada'].includes(o.status)).map(o => (
                  <div key={o.id} className="flex items-center gap-3 p-2.5 rounded-lg border border-slate-800 bg-slate-800/30 cursor-pointer hover:border-slate-600" onClick={() => navigate(`/os/${o.id}`)}>
                    <div className={`w-1.5 h-10 rounded-full ${prioColors[o.prioridade] || 'bg-slate-600'}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-200 truncate">{o.titulo}</p>
                      <div className="flex items-center gap-2 text-[10px] text-slate-500">
                        <span>#{o.numero}</span>
                        <StatusBadge status={o.status} size="sm" />
                        <span className="capitalize">{o.disciplina}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Timeline preview (últimos 5) */}
          <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2"><Clock size={16} className="text-slate-400" /> Últimos Eventos</h3>
              <button onClick={() => setActiveTab('timeline')} className="text-xs text-brand hover:underline">Ver todos</button>
            </div>
            {historico.length > 0 ? (
              <div className="space-y-0">
                {historico.slice(0, 5).map((ev, idx) => {
                  const config = tipoEventoConfig[ev.tipo_evento] || tipoEventoConfig.os;
                  return (
                    <div key={ev.id || idx} className="flex gap-3 pb-3 last:pb-0">
                      <div className="flex flex-col items-center">
                        <div className={`w-7 h-7 rounded-full ${config.bg} flex items-center justify-center shrink-0`}>
                          <config.icon size={12} className="text-white" />
                        </div>
                        {idx < 4 && <div className="w-0.5 flex-1 bg-slate-800 mt-1" />}
                      </div>
                      <div className="flex-1 min-w-0 pb-1">
                        <p className="text-sm text-slate-200">{ev.titulo}</p>
                        <p className="text-xs text-slate-500 truncate">{ev.descricao}</p>
                        <div className="flex items-center gap-2 text-[10px] text-slate-600 mt-0.5">
                          {ev.data && <span>{new Date(ev.data).toLocaleDateString('pt-BR')}</span>}
                          {ev.usuario && <span>{ev.usuario}</span>}
                          {ev.status && <StatusBadge status={ev.status} size="sm" />}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-slate-600 text-center py-4">Nenhum evento registrado.</p>
            )}
          </div>
        </div>
      )}

      {/* ===== TAB: Timeline completa ===== */}
      {activeTab === 'timeline' && (
        <div className="space-y-3" data-testid="timeline-tab">
          {/* Filters */}
          <div className="glass-card p-3 flex flex-wrap items-center gap-2">
            <select value={histFilters.tipo} onChange={e => { const f = {...histFilters, tipo: e.target.value}; setHistFilters(f); fetchHistorico(f); }} className="input-industrial px-3 text-sm">
              <option value="">Todos tipos</option>
              <option value="os">OS</option>
              <option value="inspecao">Inspeção</option>
              <option value="anomalia">Anomalia</option>
              <option value="material">Material</option>
            </select>
            <select value={histFilters.status} onChange={e => { const f = {...histFilters, status: e.target.value}; setHistFilters(f); fetchHistorico(f); }} className="input-industrial px-3 text-sm">
              <option value="">Todos status</option>
              <option value="concluida">Concluída</option>
              <option value="aberta">Aberta</option>
              <option value="pendente">Pendente</option>
            </select>
            <span className="text-xs text-slate-500">{historico.length} eventos</span>
          </div>

          {/* Timeline */}
          {historico.length > 0 ? (
            <div className="glass-card p-4">
              <div className="space-y-0">
                {historico.slice(0, timelineLimit).map((ev, idx) => {
                  const config = tipoEventoConfig[ev.tipo_evento] || tipoEventoConfig.os;
                  const evDate = ev.data ? new Date(ev.data) : null;
                  const prevDate = idx > 0 && historico[idx-1].data ? new Date(historico[idx-1].data) : null;
                  const showDateSep = evDate && (!prevDate || evDate.toDateString() !== prevDate.toDateString());
                  return (
                    <div key={ev.id || idx}>
                      {showDateSep && (
                        <div className="flex items-center gap-3 py-2">
                          <div className="h-px flex-1 bg-slate-800" />
                          <span className="text-[10px] text-slate-500 font-medium uppercase">{evDate.toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'short' })}</span>
                          <div className="h-px flex-1 bg-slate-800" />
                        </div>
                      )}
                      <div className="flex gap-3 pb-3 last:pb-0">
                        <div className="flex flex-col items-center">
                          <div className={`w-8 h-8 rounded-full ${config.bg} flex items-center justify-center shrink-0`}>
                            <config.icon size={14} className="text-white" />
                          </div>
                          {idx < Math.min(historico.length, timelineLimit) - 1 && <div className="w-0.5 flex-1 bg-slate-800 mt-1" />}
                        </div>
                        <div className="flex-1 min-w-0 pb-1">
                          <div className="flex items-center gap-2">
                            <p className="text-sm text-slate-200 font-medium">{ev.titulo}</p>
                            {ev.status && <StatusBadge status={ev.status} size="sm" />}
                          </div>
                          <p className="text-xs text-slate-500 truncate">{ev.descricao}</p>
                          <div className="flex items-center gap-3 text-[10px] text-slate-600 mt-0.5">
                            {ev.data && <span>{new Date(ev.data).toLocaleString('pt-BR', {day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})}</span>}
                            {ev.usuario && <span className="flex items-center gap-1"><User size={10} />{ev.usuario}</span>}
                            {ev.tempo_minutos && <span className="flex items-center gap-1"><Clock size={10} />{ev.tempo_minutos}min</span>}
                            {ev.prioridade && <span className="capitalize">{prioLabels[ev.prioridade] || ev.prioridade}</span>}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
              {historico.length > timelineLimit && (
                <button onClick={() => setTimelineLimit(prev => prev + 20)} className="w-full mt-3 py-2 text-sm text-brand hover:bg-slate-800 rounded-lg transition-colors">
                  Carregar mais ({historico.length - timelineLimit} restantes)
                </button>
              )}
            </div>
          ) : (
            <div className="glass-card p-8 text-center">
              <Clock size={36} className="text-slate-600 mx-auto mb-2" />
              <p className="text-slate-500">Nenhum evento registrado para este ativo.</p>
            </div>
          )}
        </div>
      )}

      {/* ===== TAB: Planos ===== */}
      {activeTab === 'planos' && (
        <div className="space-y-3" data-testid="planos-tab">
          {planosVinculados.length > 0 ? (
            <div className="space-y-2">
              {planosVinculados.map(p => {
                const statusColor = p.status === 'aprovado' ? 'text-emerald-400 bg-brand-10 border-emerald-500/30' : 'text-amber-400 bg-amber-500/10 border-amber-500/30';
                const tipoLabels2 = { inspecao: 'Inspeção', preventiva: 'Preventiva', lubrificacao: 'Lubrificação', limpeza: 'Limpeza', melhoria: 'Melhoria' };
                return (
                  <div key={p.id} className="glass-card p-4" data-testid={`plano-vinculado-${p.id}`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <ClipboardCheck size={16} className="text-brand" />
                          <span className="text-slate-100 font-medium">{p.nome}</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded border ${statusColor}`}>{p.status || 'Rascunho'}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-slate-500 flex-wrap">
                          <span className="bg-slate-800 px-2 py-0.5 rounded capitalize">{tipoLabels2[p.tipo] || p.tipo}</span>
                          {p.disciplina && <span className="bg-slate-800 px-2 py-0.5 rounded capitalize">{p.disciplina}</span>}
                          <span>{(p.perguntas || []).length} perguntas</span>
                          <span>v{p.versao || 1}</span>
                          {p.updated_at && <span>Revisado: {new Date(p.updated_at).toLocaleDateString('pt-BR')}</span>}
                        </div>
                      </div>
                      <button onClick={() => navigate('/admin/templates')} className="p-2 hover:bg-slate-700 rounded-lg" title="Editar plano">
                        <Edit size={16} className="text-slate-400" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="glass-card p-8 text-center">
              <ClipboardCheck size={36} className="text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">Nenhum plano aprovado para este ativo.</p>
              {['admin','pcm','master','supervisor'].includes(user?.role) && (
                <button onClick={() => navigate('/admin/templates')} className="mt-3 btn-primary text-sm">Criar Plano</button>
              )}
            </div>
          )}
        </div>
      )}

      {/* ===== TAB: OS ===== */}
      {activeTab === 'os' && (
        <div className="space-y-3" data-testid="os-tab">
          {(ativo.ordens_servico || []).length > 0 ? (
            <>
              {['em_aberto', 'em_execucao', 'concluidas'].map(group => {
                const statuses = group === 'em_aberto' ? ['aberta','planejada'] : group === 'em_execucao' ? ['em_execucao','pausada'] : ['concluida'];
                const label = group === 'em_aberto' ? 'Em Aberto' : group === 'em_execucao' ? 'Em Execução' : 'Concluídas';
                const items = (ativo.ordens_servico || []).filter(o => statuses.includes(o.status));
                if (items.length === 0) return null;
                return (
                  <div key={group} className="glass-card p-4">
                    <h3 className="text-sm font-semibold text-slate-400 mb-2">{label} ({items.length})</h3>
                    <div className="space-y-2">
                      {items.map(o => (
                        <div key={o.id} className="flex items-center gap-3 p-2.5 rounded-lg border border-slate-800 bg-slate-800/30 cursor-pointer hover:border-slate-600" onClick={() => navigate(`/os/${o.id}`)}>
                          <div className={`w-1.5 h-10 rounded-full ${prioColors[o.prioridade] || 'bg-slate-600'}`} />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-slate-200 truncate">{o.titulo || `OS #${o.numero}`}</p>
                            <div className="flex items-center gap-2 text-[10px] text-slate-500">
                              <span>#{o.numero}</span>
                              <span className="capitalize">{o.tipo}</span>
                              <span className="capitalize">{o.disciplina}</span>
                              <StatusBadge status={o.status} size="sm" />
                              {o.data_planejada && <span>{new Date(o.data_planejada).toLocaleDateString('pt-BR')}</span>}
                            </div>
                          </div>
                          <ChevronRight size={16} className="text-slate-700" />
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </>
          ) : (
            <div className="glass-card p-8 text-center">
              <Wrench size={36} className="text-slate-600 mx-auto mb-2" />
              <p className="text-slate-500">Nenhuma OS registrada para este ativo.</p>
            </div>
          )}
        </div>
      )}

      {/* ===== TAB: Documentos ===== */}
      {activeTab === 'docs' && (
        <div className="space-y-3" data-testid="docs-tab">
          <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Documentos</h3>
              <label className="btn-primary text-sm cursor-pointer flex items-center gap-2">
                <Upload size={16} /> {uploading ? 'Enviando...' : 'Enviar'}
                <input ref={fileInputRef} type="file" className="hidden" onChange={handleUploadManual} disabled={uploading} />
              </label>
            </div>
            {manuais.length > 0 ? (
              <div className="space-y-2">
                {manuais.map(m => (
                  <div key={m.id} className="flex items-center gap-3 p-3 rounded-lg border border-slate-800 bg-slate-800/30">
                    <FileText size={20} className="text-blue-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-200 truncate">{m.nome}</p>
                      <p className="text-[10px] text-slate-500">{m.tipo_arquivo || 'PDF'} • {new Date(m.created_at).toLocaleDateString('pt-BR')}</p>
                    </div>
                    <div className="flex gap-1">
                      {m.url && <a href={m.url} target="_blank" rel="noreferrer" className="p-2 hover:bg-slate-700 rounded-lg"><Download size={14} className="text-blue-400" /></a>}
                      <button onClick={() => handleDeleteManual(m.id)} className="p-2 hover:bg-red-500/10 rounded-lg"><Trash2 size={14} className="text-red-400" /></button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-600 text-center py-4">Nenhum documento cadastrado.</p>
            )}
          </div>
        </div>
      )}

      {/* ===== TAB: BOM (Materiais) ===== */}
      {activeTab === 'materiais' && (
        <div className="space-y-3" data-testid="materiais-tab">
          <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Lista de Materiais (BOM)</h3>
              <button onClick={() => { setBomEdit(null); setBomForm({ nome: '', codigo: '', quantidade: 1, unidade: 'UN', observacoes: '' }); setShowBomModal(true); }} className="btn-primary text-sm flex items-center gap-2"><Plus size={16} /> Adicionar</button>
            </div>
            {(ativo.materiais || []).length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-slate-800 text-slate-500 text-xs uppercase">
                    <th className="text-left py-2 px-3">Código</th>
                    <th className="text-left py-2 px-3">Descrição</th>
                    <th className="text-right py-2 px-3">Qtd</th>
                    <th className="text-left py-2 px-3">Un</th>
                    <th className="text-right py-2 px-3">Ações</th>
                  </tr></thead>
                  <tbody>
                    {(ativo.materiais || []).filter(m => !bomSearch || (m.nome||'').toLowerCase().includes(bomSearch) || (m.codigo||'').toLowerCase().includes(bomSearch)).map(m => (
                      <tr key={m.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                        <td className="py-2 px-3 font-mono text-xs text-blue-400">{m.codigo || '—'}</td>
                        <td className="py-2 px-3 text-slate-300">{m.nome}</td>
                        <td className="py-2 px-3 text-right text-slate-300">{m.quantidade}</td>
                        <td className="py-2 px-3 text-slate-500">{m.unidade}</td>
                        <td className="py-2 px-3 text-right">
                          <button onClick={() => { setBomEdit(m); setBomForm({ nome: m.nome, codigo: m.codigo||'', quantidade: m.quantidade, unidade: m.unidade, observacoes: m.observacoes||'' }); setShowBomModal(true); }} className="p-1 hover:bg-slate-700 rounded"><Edit size={12} className="text-slate-400" /></button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-slate-600 text-center py-4">Nenhum material cadastrado.</p>
            )}
          </div>
        </div>
      )}

      {/* BOM Modal */}
      <Modal isOpen={showBomModal} onClose={() => { setShowBomModal(false); setBomEdit(null); }} title={bomEdit ? "Editar Material" : "Adicionar Material"} size="md">
        <form onSubmit={async (e) => {
          e.preventDefault();
          try {
            if (bomEdit) {
              await api.put(`/ativos/${id}/materiais/${bomEdit.id}`, bomForm);
              toast.success('Material atualizado!');
            } else {
              await api.post(`/ativos/${id}/materiais`, bomForm);
              toast.success('Material adicionado!');
            }
            setShowBomModal(false);
            setBomEdit(null);
            fetchAtivo();
          } catch (error) { toast.error(normalizeError(error)); }
        }} className="space-y-4">
          <FormInput label="Código"><input value={bomForm.codigo} onChange={e => setBomForm({...bomForm, codigo: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: ROL-6310" /></FormInput>
          <FormInput label="Descrição" required><input value={bomForm.nome} onChange={e => setBomForm({...bomForm, nome: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: Rolamento 6310 2RS" required /></FormInput>
          <div className="grid grid-cols-2 gap-4">
            <FormInput label="Quantidade"><input type="number" min="0" step="0.01" value={bomForm.quantidade} onChange={e => setBomForm({...bomForm, quantidade: parseFloat(e.target.value) || 0})} className="input-industrial w-full px-4" /></FormInput>
            <FormInput label="Unidade"><input value={bomForm.unidade} onChange={e => setBomForm({...bomForm, unidade: e.target.value})} className="input-industrial w-full px-4" placeholder="UN" /></FormInput>
          </div>
          <FormInput label="Observações"><input value={bomForm.observacoes} onChange={e => setBomForm({...bomForm, observacoes: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
          <div className="flex justify-end gap-2 pt-2"><button type="button" onClick={() => setShowBomModal(false)} className="btn-secondary">Cancelar</button><button type="submit" className="btn-primary">Salvar</button></div>
        </form>
      </Modal>

      {/* QR Label Modal */}
      {showQRLabel && ativo && <QRLabelModal ativo={ativo} onClose={() => setShowQRLabel(false)} />}
    </div>
  );
};

// ============== KANBAN BOARD ==============

const KanbanBoard = ({ columns, items, onMove, onCardClick, onEdit, onDelete }) => {
  const [draggedItem, setDraggedItem] = useState(null);
  const [dragOverCol, setDragOverCol] = useState(null);
  const touchRef = useRef(null);

  const handleDragStart = (e, os) => {
    if (os.status === 'concluida') { e.preventDefault(); return; }
    setDraggedItem(os);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', os.id);
  };

  const handleDragOver = (e, colId) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverCol(colId);
  };

  const handleDragLeave = () => { setDragOverCol(null); };

  const handleDrop = (e, colId) => {
    e.preventDefault();
    setDragOverCol(null);
    if (draggedItem && draggedItem.status !== colId && colId !== 'concluida') {
      onMove(draggedItem.id, colId);
    }
    setDraggedItem(null);
  };

  // Mobile touch support
  const handleTouchStart = (os) => {
    if (os.status === 'concluida') return;
    touchRef.current = os;
    setDraggedItem(os);
  };

  const handleTouchEnd = (colId) => {
    if (touchRef.current && touchRef.current.status !== colId && colId !== 'concluida') {
      onMove(touchRef.current.id, colId);
    }
    touchRef.current = null;
    setDraggedItem(null);
    setDragOverCol(null);
  };

  return (
    <div className="flex gap-3 overflow-x-auto pb-4 custom-scrollbar snap-x snap-mandatory" data-testid="kanban-board">
      {columns.map(col => {
        const colItems = items.filter(os => os.status === col.id);
        const isDragOver = dragOverCol === col.id && col.id !== 'concluida';
        return (
          <div
            key={col.id}
            className={`flex-shrink-0 w-56 md:w-64 rounded-xl border ${col.color} ${col.bg} flex flex-col snap-start ${isDragOver ? 'ring-2 ring-emerald-400/50' : ''}`}
            onDragOver={(e) => handleDragOver(e, col.id)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, col.id)}
            data-testid={`kanban-col-${col.id}`}
          >
            <div className="p-3 border-b border-slate-800/50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${col.badge}`} />
                <span className="text-sm font-semibold text-slate-300">{col.title}</span>
              </div>
              <span className="text-xs font-bold text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full">{colItems.length}</span>
            </div>
            <div className="p-2 flex-1 space-y-2 min-h-[120px] max-h-[60vh] overflow-y-auto custom-scrollbar">
              {colItems.map(os => {
                const tipoColors = {
                  corretiva: 'bg-red-500/15 text-red-400 border-red-500/30',
                  preventiva: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
                  lubrificacao: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
                  inspecao: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
                  fabricacao: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
                  preparacao_material: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
                  melhoria: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
                  emergencial: 'bg-red-600/20 text-red-300 border-red-500/40',
                  calibracao: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
                  instalacao: 'bg-teal-500/15 text-teal-400 border-teal-500/30',
                  reforma: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
                };
                const tipoClass = tipoColors[os.tipo] || 'bg-slate-500/15 text-slate-400 border-slate-500/30';
                const tipoLabel = (os.tipo || '').replace(/_/g, ' ');
                return (
                <div
                  key={os.id}
                  draggable={col.id !== 'concluida'}
                  onDragStart={(e) => handleDragStart(e, os)}
                  className={`rounded-lg bg-slate-900/80 border border-slate-700/50 hover:border-slate-600 cursor-grab active:cursor-grabbing transition-all group/card overflow-hidden ${
                    draggedItem?.id === os.id ? 'opacity-40' : ''
                  } ${col.id === 'concluida' ? 'cursor-default opacity-70' : ''} ${os.atrasada ? 'border-red-500/50' : ''}`}
                  data-testid={`kanban-card-${os.id}`}
                >
                  {/* Top: Area/Planta stripe */}
                  <div className="px-3 py-1.5 bg-slate-800/60 border-b border-slate-700/30">
                    {os.ativo?.planta_nome && <p className="text-[9px] text-slate-500 uppercase font-bold tracking-wider">{os.ativo.planta_nome}</p>}
                    <p className="text-[10px] text-slate-400 font-medium">{os.ativo?.sector?.nome || os.ativo?.area_nome || ''}</p>
                  </div>
                  <div className="p-2.5">
                    {/* TAG + Equipment name */}
                    <div className="flex items-center gap-1.5 mb-1.5">
                      {os.ativo?.tag && <span className="font-mono text-xs text-brand font-bold">{os.ativo.tag}</span>}
                      {os.ativo?.nome && <span className="text-[10px] text-slate-500 truncate">{os.ativo.nome}</span>}
                    </div>
                    {/* OS number + type */}
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <span className="font-mono text-xs text-slate-300 cursor-pointer hover:text-white hover:underline" onClick={() => onCardClick(os)}>OS #{os.numero}</span>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded border capitalize ${tipoClass}`}>{tipoLabel}</span>
                    </div>
                    {/* Title */}
                    <p className="text-sm text-slate-200 leading-tight cursor-pointer hover:text-white mb-2" onClick={() => onCardClick(os)}>{os.titulo}</p>
                    {/* Priority + Responsavel + Date */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <PriorityBadge priority={os.prioridade} />
                        {os.disciplina && <span className="text-[9px] px-1 py-0.5 rounded bg-slate-800 text-slate-500 capitalize">{os.disciplina}</span>}
                      </div>
                      {(onEdit || onDelete) && (
                        <div className="hidden group-hover/card:flex gap-0.5">
                          {onEdit && <button onClick={(e) => { e.stopPropagation(); onEdit(os); }} className="p-1 hover:bg-blue-500/10 rounded" title="Editar"><Edit3 size={12} className="text-blue-400" /></button>}
                          {onDelete && <button onClick={(e) => { e.stopPropagation(); onDelete(os); }} className="p-1 hover:bg-red-500/10 rounded" title="Excluir"><Trash2 size={12} className="text-red-400" /></button>}
                        </div>
                      )}
                    </div>
                    {/* Responsavel */}
                    {os.responsavel && <p className="text-[10px] text-slate-500 mt-1.5"><User size={10} className="inline mr-0.5 text-slate-600" />{os.responsavel.nome}</p>}
                    {/* Date + Late badge */}
                    <div className="flex items-center justify-between mt-1">
                      {os.data_planejada && <span className="text-[9px] text-slate-600"><Calendar size={9} className="inline mr-0.5" />{new Date(os.data_planejada).toLocaleDateString('pt-BR')}</span>}
                      {os.atrasada && <span className="text-[9px] px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 font-bold border border-red-500/30">ATRASADA</span>}
                    </div>
                  </div>
                  {/* Mobile quick-move buttons */}
                  {col.id !== 'concluida' && (
                    <div className="px-2.5 pb-2 flex gap-1 md:hidden" data-testid={`mobile-move-${os.id}`}>
                      {columns.filter(c => c.id !== col.id && c.id !== 'concluida').map(c => (
                        <button key={c.id} onClick={(e) => { e.stopPropagation(); onMove(os.id, c.id); }} className={`text-[9px] px-1.5 py-0.5 rounded ${c.bg} ${c.color} border`}>
                          {c.title.slice(0, 3)}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                );
              })}
              {colItems.length === 0 && (
                <div className="flex items-center justify-center h-20 text-slate-700 text-xs border border-dashed border-slate-800 rounded-lg">
                  {col.id === 'concluida' ? 'Concluídas' : 'Arraste OS aqui'}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// OS Page
const OSPage = () => {
  const [osList, setOsList] = useState([]);
  const [ativos, setAtivos] = useState([]);
  const [tecnicos, setTecnicos] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [plantas, setPlantas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [searchOS, setSearchOS] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [filterTipo, setFilterTipo] = useState('');
  const [filterArea, setFilterArea] = useState('');
  const [filterResponsavel, setFilterResponsavel] = useState('');
  const [filterDisciplina, setFilterDisciplina] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const [viewMode, setViewMode] = useState('kanban');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  
  useEffect(() => {
    if (searchParams.get('new') === 'true') setShowModal(true);
  }, [searchParams]);
  
  const fetchData = async () => {
    try {
      const [osRes, ativosRes, tecnicosRes, sectorsRes, plantasRes] = await Promise.all([
        api.get('/ordens-servico'),
        api.get('/ativos'),
        api.get('/users/tecnicos'),
        api.get('/sectors'),
        api.get('/plantas').catch(() => ({ data: [] }))
      ]);
      setOsList(osRes.data);
      setAtivos(ativosRes.data);
      setTecnicos(tecnicosRes.data);
      setSectors(sectorsRes.data);
      setPlantas(plantasRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => { fetchData(); }, []);
  
  const handleDelete = async () => {
    try {
      await api.delete(`/ordens-servico/${deleteItem.id}`);
      toast.success('OS excluída!');
      setDeleteItem(null);
      fetchData();
    } catch (error) {
      toast.error('Erro ao excluir');
    }
  };

  const handleKanbanMove = async (osId, newStatus) => {
    try {
      await api.patch(`/ordens-servico/${osId}/status`, { new_status: newStatus });
      setOsList(prev => prev.map(os => os.id === osId ? { ...os, status: newStatus } : os));
      toast.success(`OS movida para ${kanbanColumns.find(c => c.id === newStatus)?.title || newStatus}`);
    } catch (error) {
      toast.error(normalizeError(error));
      fetchData();
    }
  };
  
  const applyFilters = (list) => {
    return list.filter(os => {
      if (filter && os.status !== filter) return false;
      if (filterPriority && os.prioridade !== filterPriority) return false;
      if (filterTipo && os.tipo !== filterTipo) return false;
      if (filterDisciplina && os.disciplina !== filterDisciplina) return false;
      if (filterArea && os.ativo?.sector_id !== filterArea) return false;
      if (filterResponsavel && os.responsavel_id !== filterResponsavel) return false;
      if (searchOS) {
        const s = searchOS.toLowerCase();
        const matchNum = os.numero?.toLowerCase().includes(s);
        const matchTitulo = os.titulo?.toLowerCase().includes(s);
        const matchTag = os.ativo?.tag?.toLowerCase().includes(s);
        const matchNome = os.ativo?.nome?.toLowerCase().includes(s);
        if (!matchNum && !matchTitulo && !matchTag && !matchNome) return false;
      }
      return true;
    });
  };

  const filtered = applyFilters(osList);
  const kanbanItems = applyFilters(osList);
  const activeFilterCount = [filterPriority, filterTipo, filterArea, filterResponsavel, filterDisciplina].filter(Boolean).length;

  const kanbanColumns = [
    { id: 'solicitada', title: 'Solicitadas', color: 'border-blue-500/40', bg: 'bg-blue-500/5', badge: 'bg-blue-500' },
    { id: 'em_analise', title: 'Em Análise', color: 'border-purple-500/40', bg: 'bg-purple-500/5', badge: 'bg-purple-500' },
    { id: 'aguardando_aprovacao', title: 'Aguard. Aprovação', color: 'border-amber-500/40', bg: 'bg-amber-500/5', badge: 'bg-amber-500' },
    { id: 'programada', title: 'Programadas', color: 'border-cyan-500/40', bg: 'bg-cyan-500/5', badge: 'bg-cyan-500' },
    { id: 'disponivel', title: 'Disponíveis', color: 'border-teal-500/40', bg: 'bg-teal-500/5', badge: 'bg-teal-500' },
    { id: 'em_execucao', title: 'Em Execução', color: 'border-emerald-500/40', bg: 'bg-emerald-500/5', badge: 'bg-emerald-500' },
    { id: 'pausada', title: 'Pausadas', color: 'border-amber-500/40', bg: 'bg-amber-500/5', badge: 'bg-amber-500' },
    // Legacy compat
    { id: 'aberta', title: 'Abertas (legado)', color: 'border-blue-500/40', bg: 'bg-blue-500/5', badge: 'bg-blue-500', hidden: true },
    { id: 'planejada', title: 'Planejadas (legado)', color: 'border-purple-500/40', bg: 'bg-purple-500/5', badge: 'bg-purple-500', hidden: true },
  ];
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-slate-100">Ordens de Serviço</h1>
          <ExportButtons entity="ordens-servico" />
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-slate-800 rounded-lg p-0.5">
            <button onClick={() => setViewMode('kanban')} className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${viewMode === 'kanban' ? 'bg-brand-20 text-brand' : 'text-slate-400'}`} data-testid="view-kanban">
              <LayoutDashboard size={14} className="inline mr-1" />Kanban
            </button>
            <button onClick={() => setViewMode('list')} className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${viewMode === 'list' ? 'bg-brand-20 text-brand' : 'text-slate-400'}`} data-testid="view-list">
              <List size={14} className="inline mr-1" />Lista
            </button>
          </div>
          <button onClick={() => { setEditItem(null); setShowModal(true); }} className="btn-primary flex items-center gap-2" data-testid="add-os-btn">
            <Plus size={20} /> Nova OS
          </button>
        </div>
      </div>
      
      {/* Search + Filters */}
      <div className="space-y-2">
        <div className="flex flex-wrap gap-2 items-center">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
            <input
              type="text"
              value={searchOS}
              onChange={(e) => setSearchOS(e.target.value)}
              placeholder="Buscar por nº, título ou TAG do ativo..."
              className="input-industrial w-full pl-9 pr-4 text-sm"
              data-testid="os-search-input"
            />
            {searchOS && <button onClick={() => setSearchOS('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"><X size={14} /></button>}
          </div>
          <button onClick={() => setShowFilters(!showFilters)}
            className={`px-3 py-2 rounded-lg text-xs font-medium border transition-all flex items-center gap-1.5 ${showFilters || activeFilterCount > 0 ? 'bg-brand-20 text-brand border-brand-30' : 'border-slate-700 text-slate-400 hover:text-slate-300'}`}
            data-testid="os-toggle-filters"
          >
            <Filter size={14} />Filtros
            {activeFilterCount > 0 && <span className="bg-brand text-white text-[9px] w-4 h-4 rounded-full flex items-center justify-center">{activeFilterCount}</span>}
          </button>
          <div className="flex gap-1">
            {[
              { value: '', label: 'Todas' },
              { value: 'emergencia', label: 'Emerg.', cls: 'text-red-400 bg-red-500/10 border-red-500/30' },
              { value: 'alta', label: 'Alta', cls: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
              { value: 'media', label: 'Média', cls: 'text-emerald-400 bg-brand-10 border-emerald-500/30' },
              { value: 'baixa', label: 'Baixa', cls: 'text-slate-400 bg-slate-500/10 border-slate-500/30' },
            ].map(p => (
              <button key={p.value} onClick={() => setFilterPriority(p.value)}
                className={`px-2 py-1.5 rounded-lg text-[10px] font-medium border transition-all ${filterPriority === p.value ? (p.cls || 'bg-brand-20 text-brand border-brand-30') : 'border-slate-700 text-slate-500 hover:text-slate-300'}`}
                data-testid={`os-filter-priority-${p.value || 'all'}`}
              >{p.label}</button>
            ))}
          </div>
        </div>
        {/* Expanded filters panel */}
        {showFilters && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2 p-3 glass-card" data-testid="os-filters-panel">
            <select value={filterTipo} onChange={(e) => setFilterTipo(e.target.value)} className="input-industrial text-xs" data-testid="os-filter-tipo">
              <option value="">Tipo de OS</option>
              {['corretiva','preventiva','lubrificacao','inspecao','fabricacao','preparacao_material','melhoria','calibracao','instalacao','reforma','emergencial'].map(t => (
                <option key={t} value={t}>{t.replace(/_/g,' ')}</option>
              ))}
            </select>
            <select value={filterArea} onChange={(e) => setFilterArea(e.target.value)} className="input-industrial text-xs" data-testid="os-filter-area">
              <option value="">Área</option>
              {sectors.map(s => <option key={s.id} value={s.id}>{s.nome}</option>)}
            </select>
            <select value={filterResponsavel} onChange={(e) => setFilterResponsavel(e.target.value)} className="input-industrial text-xs" data-testid="os-filter-responsavel">
              <option value="">Responsável</option>
              {tecnicos.map(t => <option key={t.id} value={t.id}>{t.nome}</option>)}
            </select>
            <select value={filterDisciplina} onChange={(e) => setFilterDisciplina(e.target.value)} className="input-industrial text-xs" data-testid="os-filter-disciplina">
              <option value="">Disciplina</option>
              {['mecanica','eletrica','instrumentacao','civil','producao'].map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
            <button onClick={() => { setFilterPriority(''); setFilterTipo(''); setFilterArea(''); setFilterResponsavel(''); setFilterDisciplina(''); setSearchOS(''); }}
              className="text-xs text-slate-500 hover:text-brand flex items-center justify-center gap-1" data-testid="os-clear-all-filters">
              <X size={12} />Limpar filtros
            </button>
          </div>
        )}
      </div>

      {loading ? <Loading rows={5} /> : viewMode === 'kanban' ? (
        <KanbanBoard
          columns={kanbanColumns}
          items={kanbanItems}
          onMove={handleKanbanMove}
          onCardClick={(os) => navigate(`/os/${os.id}`)}
          onEdit={['admin','master','pcm'].includes(user?.role) ? (os) => { setEditItem(os); setShowModal(true); } : null}
          onDelete={['admin','master'].includes(user?.role) ? (os) => setDeleteItem(os) : null}
        />
      ) : (
        <>
          <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-2">
            {[
              { value: '', label: 'Todas' },
              { value: 'solicitada', label: 'Solicitadas' },
              { value: 'em_analise', label: 'Em Análise' },
              { value: 'aguardando_aprovacao', label: 'Aguard. Aprovação' },
              { value: 'aguardando_material', label: 'Aguard. Material' },
              { value: 'programada', label: 'Programadas' },
              { value: 'disponivel', label: 'Disponíveis' },
              { value: 'em_execucao', label: 'Em Execução' },
              { value: 'pausada', label: 'Pausadas' },
              { value: 'concluida', label: 'Concluídas' },
            ].map(f => (
              <button key={f.value} onClick={() => setFilter(f.value)} className={`px-4 py-2 rounded-lg whitespace-nowrap transition-all ${filter === f.value ? 'bg-brand text-slate-950 font-semibold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}>
                {f.label}
              </button>
            ))}
          </div>
          {filtered.length > 0 ? (
            <div className="space-y-2">
              {filtered.map((os) => (
                <div key={os.id} className="glass-card p-4 hover:border-slate-600 transition-all group">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 cursor-pointer" onClick={() => navigate(`/os/${os.id}`)}>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-brand">#{os.numero}</span>
                        {os.ativo && <span className="text-xs text-slate-500">{os.ativo.tag}</span>}
                        {os.atrasada && <span className="text-xs bg-red-500 text-white px-2 py-0.5 rounded">ATRASADA</span>}
                      </div>
                      <p className="text-slate-100">{os.titulo}</p>
                      {os.responsavel && <p className="text-xs text-slate-500"><User size={12} className="inline mr-1" />{os.responsavel.nome}</p>}
                    </div>
                    <div className="flex items-center gap-2">
                      {['admin','master','pcm'].includes(user?.role) && (
                        <div className="flex items-center gap-1">
                          <button onClick={(e) => { e.stopPropagation(); setEditItem(os); setShowModal(true); }} className="p-2 hover:bg-slate-700 rounded-lg" title="Editar" data-testid={`edit-os-${os.id}`}><Edit3 size={15} className="text-blue-400" /></button>
                          {['admin','master'].includes(user?.role) && <button onClick={(e) => { e.stopPropagation(); setDeleteItem(os); }} className="p-2 hover:bg-red-500/10 rounded-lg" title="Excluir" data-testid={`delete-os-${os.id}`}><Trash2 size={15} className="text-red-400" /></button>}
                        </div>
                      )}
                      <PriorityBadge priority={os.prioridade} />
                      <ChevronRight className="text-slate-600" />
                    </div>
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <StatusBadge status={os.status} size="sm" />
                    <span className="text-xs text-slate-500 capitalize">{os.tipo}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState icon={Wrench} title="Nenhuma OS encontrada" description="Crie uma nova ordem de serviço." action={() => setShowModal(true)} actionLabel="Nova OS" />
          )}
        </>
      )}
      
      <ModalNovaOS isOpen={showModal} onClose={() => { setShowModal(false); setEditItem(null); }} onSuccess={fetchData} ativos={ativos} tecnicos={tecnicos} editData={editItem} preSelectedAtivoId={searchParams.get('ativo') || null} />
      <ConfirmDialog isOpen={!!deleteItem} onClose={() => setDeleteItem(null)} onConfirm={handleDelete} title="Excluir OS" message={`Tem certeza que deseja excluir a OS #${deleteItem?.numero}?`} confirmText="Excluir" danger />
    </div>
  );
};

// OS Detail
const OSDetailPage = () => {
  const { id } = useParams();
  const [os, setOs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [historico, setHistorico] = useState([]);
  const [showConcluir, setShowConcluir] = useState(false);
  const [concluirForm, setConcluirForm] = useState({ servicos_realizados: '', tempo_execucao_minutos: '', observacoes: '' });
  const [materiais, setMateriais] = useState([]);
  const [estoqueItems, setEstoqueItems] = useState([]);
  const [showMatModal, setShowMatModal] = useState(false);
  const [matForm, setMatForm] = useState({ item_estoque_id: '', quantidade: '' });
  const [deleteMat, setDeleteMat] = useState(null);
  const [hhResumo, setHhResumo] = useState(null);
  const [hhStatus, setHhStatus] = useState(null);
  const [executantes, setExecutantes] = useState([]);
  const [tecnicos, setTecnicos] = useState([]);
  const [showExecModal, setShowExecModal] = useState(false);
  const [execForm, setExecForm] = useState({ user_id: '', funcao: 'executor' });
  const [osEventos, setOsEventos] = useState([]);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [timerRunning, setTimerRunning] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const fetchOS = async () => {
    try {
      const [osRes, histRes, matRes, hhRes, execRes, evtRes, tecRes] = await Promise.all([
        api.get(`/ordens-servico/${id}`),
        api.get(`/ordens-servico/${id}/historico`).catch(() => ({ data: [] })),
        api.get(`/ordens-servico/${id}/materiais`).catch(() => ({ data: [] })),
        api.get(`/hh/resumo/${id}`).catch(() => ({ data: { executantes: [], hh_total_liquida_min: 0 } })),
        api.get(`/os/${id}/executantes`).catch(() => ({ data: [] })),
        api.get(`/os/${id}/eventos`).catch(() => ({ data: [] })),
        api.get('/users/tecnicos').catch(() => ({ data: [] })),
      ]);
      setOs(osRes.data);
      setHistorico(histRes.data);
      setMateriais(matRes.data);
      setHhResumo(hhRes.data);
      setExecutantes(execRes.data);
      setOsEventos(evtRes.data);
      setTecnicos(tecRes.data);
      
      // Determine current HH status for this user
      const myHH = (hhRes.data?.executantes || []).find(e => e.user_id === user?.id);
      setHhStatus(myHH?.ultimo_evento || null);
      
      // Calculate running timer if currently working
      if (myHH?.ultimo_evento === 'iniciar' || myHH?.ultimo_evento === 'retornar') {
        setTimerRunning(true);
      } else {
        setTimerRunning(false);
      }
    } catch (error) {
      toast.error('OS não encontrada');
      navigate('/os');
    } finally {
      setLoading(false);
    }
  };
  
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchOS(); }, [id]);
  
  useEffect(() => {
    api.get('/estoque').then(r => setEstoqueItems(r.data)).catch(() => {});
  }, []);

  // Timer tick
  useEffect(() => {
    if (!timerRunning) return;
    const interval = setInterval(() => setTimerSeconds(s => s + 1), 1000);
    return () => clearInterval(interval);
  }, [timerRunning]);

  const handleHH = async (evento) => {
    try {
      await api.post(`/os/${id}/hh`, { os_id: id, evento });
      toast.success({ iniciar: 'Cronômetro iniciado!', pausar: 'Pausado', retornar: 'Retomado!', finalizar: 'Finalizado!' }[evento] || evento);
      setTimerSeconds(0);
      fetchOS();
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const handleAddExec = async () => {
    if (!execForm.user_id) { toast.error('Selecione um técnico'); return; }
    try {
      await api.post(`/os/${id}/executantes`, { os_id: id, ...execForm });
      toast.success('Executante adicionado!');
      setShowExecModal(false);
      setExecForm({ user_id: '', funcao: 'executor' });
      fetchOS();
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const handleRemoveExec = async (userId) => {
    try {
      await api.delete(`/os/${id}/executantes/${userId}`);
      toast.success('Executante removido');
      fetchOS();
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const formatTimer = (secs) => {
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = secs % 60;
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
  };
  
  const handleAction = async (action) => {
    if (action === 'concluir') { setShowConcluir(true); return; }
    setUpdating(true);
    try {
      await api.post(`/ordens-servico/${id}/${action}`);
      toast.success(`OS ${action === 'iniciar' ? 'iniciada' : 'pausada'}!`);
      fetchOS();
    } catch (error) {
      toast.error(normalizeError(error));
    } finally {
      setUpdating(false);
    }
  };

  const handleConcluir = async () => {
    if (!concluirForm.servicos_realizados.trim()) {
      toast.error('Preencha o serviço executado');
      return;
    }
    const tempo = parseInt(concluirForm.tempo_execucao_minutos);
    if (!tempo || tempo <= 0) {
      toast.error('Informe o tempo gasto (minutos)');
      return;
    }
    setUpdating(true);
    try {
      await api.post(`/ordens-servico/${id}/concluir`, {
        servicos_realizados: concluirForm.servicos_realizados.trim(),
        tempo_execucao_minutos: tempo,
        observacoes: concluirForm.observacoes || null,
      });
      toast.success('OS concluída com sucesso!');
      setShowConcluir(false);
      fetchOS();
    } catch (error) {
      toast.error(normalizeError(error));
    } finally {
      setUpdating(false);
    }
  };

  const handleAddMaterial = async () => {
    if (!matForm.item_estoque_id || !matForm.quantidade || parseFloat(matForm.quantidade) <= 0) {
      toast.error('Selecione o item e informe a quantidade'); return;
    }
    try {
      await api.post(`/ordens-servico/${id}/materiais`, {
        item_estoque_id: matForm.item_estoque_id,
        quantidade: parseFloat(matForm.quantidade)
      });
      toast.success('Material registrado!');
      setShowMatModal(false);
      setMatForm({ item_estoque_id: '', quantidade: '' });
      fetchOS();
      api.get('/estoque').then(r => setEstoqueItems(r.data)).catch(() => {});
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const handleRemoveMaterial = async () => {
    try {
      await api.delete(`/ordens-servico/${id}/materiais/${deleteMat.id}`);
      toast.success('Material devolvido ao estoque!');
      setDeleteMat(null);
      fetchOS();
      api.get('/estoque').then(r => setEstoqueItems(r.data)).catch(() => {});
    } catch (e) { toast.error(normalizeError(e)); }
  };
  
  if (loading) return <Loading rows={4} />;
  if (!os) return null;
  
  return (
    <div className="space-y-4" data-testid="os-detail-page">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/os')} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg">
          <ArrowLeft size={20} className="text-slate-400" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-brand">#{os.numero}</span>
            <StatusBadge status={os.status} size="sm" />
            <PriorityBadge priority={os.prioridade} />
          </div>
          <h1 className="text-xl font-bold text-slate-100">{os.titulo}</h1>
        </div>
      </div>
      
      {/* Ativo — Área + TAG + Equipamento */}
      {os.ativo && (
        <div className="glass-card p-4 cursor-pointer hover:border-slate-600" onClick={() => navigate(`/ativos/${os.ativo.id}`)} data-testid="os-ativo-card">
          <p className="text-xs text-slate-500 mb-1">Equipamento</p>
          <div className="flex items-center justify-between">
            <div>
              {os.ativo.sector && <p className="text-xs text-slate-500 uppercase font-medium">{os.ativo.sector.nome || os.ativo.sector_nome}</p>}
              <span className="font-mono text-brand">{os.ativo.tag}</span>
              <p className="text-slate-200">{os.ativo.nome}</p>
            </div>
            <ChevronRight className="text-slate-600" />
          </div>
        </div>
      )}
      
      {/* Info */}
      <div className="glass-card p-4 space-y-3" data-testid="os-info-card">
        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <div><span className="text-slate-500">Tipo</span><span className="text-slate-200 capitalize float-right">{os.tipo}</span></div>
          <div><span className="text-slate-500">Disciplina</span><span className="text-slate-200 capitalize float-right">{os.disciplina}</span></div>
          <div><span className="text-slate-500">Origem</span><span className="text-slate-200 capitalize float-right">{os.origem || 'manual'}</span></div>
          {os.data_planejada && <div><span className="text-slate-500">Data Planejada</span><span className="text-slate-200 float-right">{new Date(os.data_planejada + 'T00:00:00').toLocaleDateString('pt-BR')}</span></div>}
          {os.equipamento_parado && <div className="col-span-2 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-1.5 flex items-center gap-2"><AlertTriangle size={14} className="text-red-400" /><span className="text-red-400 text-xs font-semibold">EQUIPAMENTO PARADO</span>{os.horas_parada && <span className="text-red-300 text-xs ml-auto">{os.horas_parada}h de parada</span>}</div>}
        </div>

        {/* Justificativa (Solicitação) */}
        {os.justificativa && (
          <div className="border-t border-slate-800 pt-2">
            <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider mb-1">Justificativa da Solicitação</p>
            <p className="text-sm text-slate-300 bg-slate-900/50 rounded-lg px-3 py-2">{os.justificativa}</p>
          </div>
        )}

        {/* Aprovação */}
        {os.aprovacao?.necessaria && (
          <div className={`border-t border-slate-800 pt-2 p-3 rounded-lg ${os.aprovacao.status === 'aprovada' ? 'bg-emerald-500/5 border border-emerald-500/20' : os.aprovacao.status === 'rejeitada' ? 'bg-red-500/5 border border-red-500/20' : 'bg-amber-500/5 border border-amber-500/20'}`} data-testid="os-aprovacao">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider">Aprovação Gerencial</p>
              <StatusBadge status={os.aprovacao.status === 'aprovada' ? 'concluida' : os.aprovacao.status === 'rejeitada' ? 'cancelada' : 'aguardando_aprovacao'} size="sm" />
            </div>
            {os.aprovacao.aprovador_nome && <p className="text-xs text-slate-400">Aprovador: {os.aprovacao.aprovador_nome}</p>}
            {os.aprovacao.data && <p className="text-xs text-slate-500">Data: {new Date(os.aprovacao.data).toLocaleString('pt-BR')}</p>}
            {os.aprovacao.observacao && <p className="text-xs text-slate-300 mt-1 italic">"{os.aprovacao.observacao}"</p>}
            {/* Gerente action buttons */}
            {user?.role === 'gerente' && os.aprovacao.status === 'pendente' && os.status === 'aguardando_aprovacao' && (
              <div className="flex gap-2 mt-3" data-testid="os-aprovar-btns">
                <button onClick={async () => { try { await api.post(`/ordens-servico/${os.id}/aprovar`, { decisao: 'aprovada', observacao: '' }); toast.success('OS Aprovada!'); loadOS(); } catch(e) { toast.error(normalizeError(e)); }}} className="flex-1 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg text-sm font-semibold hover:bg-emerald-500/30 transition-all" data-testid="os-btn-aprovar"><CheckCircle size={14} className="inline mr-1" /> Aprovar</button>
                <button onClick={async () => { const obs = prompt('Motivo da rejeição:'); if (obs !== null) { try { await api.post(`/ordens-servico/${os.id}/aprovar`, { decisao: 'rejeitada', observacao: obs }); toast.success('OS Rejeitada'); loadOS(); } catch(e) { toast.error(normalizeError(e)); }}}} className="flex-1 py-2 bg-red-500/20 text-red-400 rounded-lg text-sm font-semibold hover:bg-red-500/30 transition-all" data-testid="os-btn-rejeitar"><XCircle size={14} className="inline mr-1" /> Rejeitar</button>
                <button onClick={async () => { const obs = prompt('Observação para revisão:'); if (obs !== null) { try { await api.post(`/ordens-servico/${os.id}/aprovar`, { decisao: 'revisao', observacao: obs }); toast.success('Enviada para revisão'); loadOS(); } catch(e) { toast.error(normalizeError(e)); }}}} className="flex-1 py-2 bg-amber-500/20 text-amber-400 rounded-lg text-sm font-semibold hover:bg-amber-500/30 transition-all"><Edit3 size={14} className="inline mr-1" /> Revisão</button>
              </div>
            )}
          </div>
        )}
        
        {/* Responsável + Executantes */}
        {os.responsavel && <div className="flex justify-between text-sm border-t border-slate-800 pt-2"><span className="text-slate-500">Responsável</span><span className="text-slate-200">{os.responsavel.nome}</span></div>}
        {(os.equipe?.length > 0) && (
          <div className="text-sm">
            <span className="text-slate-500 block mb-1">Executantes</span>
            <div className="flex flex-wrap gap-1">
              {os.equipe.map(uid => (
                <span key={uid} className="text-xs bg-slate-800 text-slate-300 px-2 py-1 rounded">{os.equipe_nomes?.[uid] || uid}</span>
              ))}
            </div>
          </div>
        )}
        
        {/* Rastreabilidade */}
        <div className="border-t border-slate-800 pt-2 space-y-2">
          <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider">Rastreabilidade</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
            <div><span className="text-slate-500">Criado por:</span> <span className="text-slate-300">{os.criado_por_nome || '—'}</span></div>
            <div><span className="text-slate-500">Data abertura:</span> <span className="text-slate-300">{os.data_abertura ? new Date(os.data_abertura).toLocaleString('pt-BR') : '—'}</span></div>
            <div><span className="text-slate-500">Planejado por:</span> <span className="text-slate-300">{os.planejado_por_nome || '—'}</span></div>
            <div><span className="text-slate-500">Data planejamento:</span> <span className="text-slate-300">{os.data_planejamento ? new Date(os.data_planejamento).toLocaleString('pt-BR') : '—'}</span></div>
            <div><span className="text-slate-500">Executado por:</span> <span className="text-slate-300">{os.iniciado_por_nome || '—'}</span></div>
            <div><span className="text-slate-500">Data execução:</span> <span className="text-slate-300">{os.data_inicio ? new Date(os.data_inicio).toLocaleString('pt-BR') : '—'}</span></div>
            <div><span className="text-slate-500">Concluído por:</span> <span className="text-slate-300">{os.concluido_por_nome || '—'}</span></div>
            <div><span className="text-slate-500">Data conclusão:</span> <span className="text-slate-300">{os.data_conclusao ? new Date(os.data_conclusao).toLocaleString('pt-BR') : '—'}</span></div>
            {os.alterado_por_nome && (
              <>
                <div><span className="text-slate-500">Última alteração por:</span> <span className="text-amber-400">{os.alterado_por_nome}</span></div>
                <div><span className="text-slate-500">Data alteração:</span> <span className="text-amber-400">{os.updated_at ? new Date(os.updated_at).toLocaleString('pt-BR') : '—'}</span></div>
              </>
            )}
          </div>
        </div>
        
        {/* Execução */}
        {(os.tempo_execucao_minutos || os.custo_pecas > 0 || os.custo_mao_obra > 0) && (
          <div className="border-t border-slate-800 pt-2 space-y-1">
            <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider">Execução</p>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {os.tempo_execucao_minutos && <div><span className="text-slate-500">Tempo:</span> <span className="text-brand font-semibold">{Math.floor(os.tempo_execucao_minutos / 60)}h {os.tempo_execucao_minutos % 60}min</span></div>}
              {os.custo_pecas > 0 && <div><span className="text-slate-500">Custo Peças:</span> <span className="text-slate-300">R$ {os.custo_pecas.toFixed(2)}</span></div>}
              {os.custo_mao_obra > 0 && <div><span className="text-slate-500">Custo M.O.:</span> <span className="text-slate-300">R$ {os.custo_mao_obra.toFixed(2)}</span></div>}
              {(os.custo_pecas > 0 || os.custo_mao_obra > 0) && <div><span className="text-slate-500">Custo Total:</span> <span className="text-slate-200 font-semibold">R$ {((os.custo_pecas || 0) + (os.custo_mao_obra || 0)).toFixed(2)}</span></div>}
            </div>
          </div>
        )}
      </div>
      
      {os.descricao && (
        <div className="glass-card p-4">
          <p className="text-xs text-slate-500 mb-1">Descrição</p>
          <p className="text-slate-200 whitespace-pre-wrap">{os.descricao}</p>
        </div>
      )}

      {/* ============ CRONÔMETRO HH ============ */}
      {!['concluida','cancelada'].includes(os.status) && (
        <div className="glass-card p-4" data-testid="hh-cronometro">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Clock size={16} /> Cronômetro HH
          </h3>
          {/* Timer display */}
          <div className="text-center mb-4">
            <p className={`text-4xl font-mono font-bold ${timerRunning ? 'text-emerald-400' : 'text-slate-500'}`} data-testid="hh-timer-display">
              {formatTimer(timerSeconds)}
            </p>
            <p className="text-xs text-slate-600 mt-1">
              {!hhStatus && 'Pronto para iniciar'}
              {hhStatus === 'iniciar' && 'Trabalhando...'}
              {hhStatus === 'retornar' && 'Trabalhando...'}
              {hhStatus === 'pausar' && 'Em pausa'}
              {hhStatus === 'finalizar' && 'Finalizado'}
            </p>
          </div>
          {/* Buttons */}
          <div className="flex gap-2 justify-center">
            {(!hhStatus || hhStatus === 'finalizar') && (
              <button onClick={() => handleHH('iniciar')} className="px-6 py-2.5 rounded-lg bg-brand-20 text-brand border border-brand-30 font-medium text-sm hover:brightness-110 flex items-center gap-2" data-testid="hh-iniciar">
                <Play size={18} /> Iniciar
              </button>
            )}
            {(hhStatus === 'iniciar' || hhStatus === 'retornar') && (
              <>
                <button onClick={() => handleHH('pausar')} className="px-5 py-2.5 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30 font-medium text-sm hover:bg-amber-500/30 flex items-center gap-2" data-testid="hh-pausar">
                  <Pause size={18} /> Pausar
                </button>
                <button onClick={() => handleHH('finalizar')} className="px-5 py-2.5 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30 font-medium text-sm hover:bg-blue-500/30 flex items-center gap-2" data-testid="hh-finalizar">
                  <CheckCircle size={18} /> Finalizar
                </button>
              </>
            )}
            {hhStatus === 'pausar' && (
              <>
                <button onClick={() => handleHH('retornar')} className="px-5 py-2.5 rounded-lg bg-brand-20 text-brand border border-brand-30 font-medium text-sm hover:brightness-110 flex items-center gap-2" data-testid="hh-retornar">
                  <Play size={18} /> Retornar
                </button>
                <button onClick={() => handleHH('finalizar')} className="px-5 py-2.5 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30 font-medium text-sm hover:bg-blue-500/30 flex items-center gap-2">
                  <CheckCircle size={18} /> Finalizar
                </button>
              </>
            )}
          </div>
          {/* HH Summary */}
          {hhResumo && hhResumo.executantes?.length > 0 && (
            <div className="mt-4 border-t border-slate-800 pt-3">
              <p className="text-xs text-slate-500 mb-2">Resumo HH por executante:</p>
              <div className="space-y-1.5">
                {hhResumo.executantes.map(e => (
                  <div key={e.user_id} className="flex items-center justify-between text-xs bg-slate-800/50 rounded px-3 py-2">
                    <span className="text-slate-300">{e.user_nome}</span>
                    <div className="flex gap-3">
                      <span className="text-brand">Líquida: {Math.floor(e.hh_liquida_min/60)}h{Math.round(e.hh_liquida_min%60)}m</span>
                      <span className="text-slate-500">Bruta: {Math.floor(e.hh_bruta_min/60)}h{Math.round(e.hh_bruta_min%60)}m</span>
                      {e.tempo_parado_min > 0 && <span className="text-amber-400">Parado: {Math.round(e.tempo_parado_min)}m</span>}
                    </div>
                  </div>
                ))}
                <div className="text-right text-xs text-slate-400 pt-1">
                  Total HH líquida: <span className="text-brand font-semibold">{Math.floor(hhResumo.hh_total_liquida_min/60)}h{Math.round(hhResumo.hh_total_liquida_min%60)}m</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============ EXECUTANTES DA OS ============ */}
      <div className="glass-card p-4" data-testid="os-executantes-section">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Users size={16} /> Equipe ({executantes.length})
          </h3>
          {!['concluida','cancelada'].includes(os.status) && ['admin','master','pcm','supervisor'].includes(user?.role) && (
            <button onClick={() => setShowExecModal(true)} className="text-xs btn-primary flex items-center gap-1" data-testid="add-exec-btn">
              <Plus size={14} /> Adicionar
            </button>
          )}
        </div>
        {executantes.length > 0 ? (
          <div className="space-y-1.5">
            {executantes.map(e => {
              const funcColors = { executor: 'text-emerald-400 bg-brand-10', apoio: 'text-blue-400 bg-blue-500/10', supervisor_exec: 'text-amber-400 bg-amber-500/10', inspetor_exec: 'text-cyan-400 bg-cyan-500/10', lider: 'text-purple-400 bg-purple-500/10' };
              const funcLabels = { executor: 'Executor', apoio: 'Apoio', supervisor_exec: 'Supervisor', inspetor_exec: 'Inspetor', lider: 'Líder' };
              return (
                <div key={e.user_id} className="flex items-center justify-between bg-slate-800/50 rounded-lg px-3 py-2" data-testid={`exec-${e.user_id}`}>
                  <div className="flex items-center gap-2">
                    <User size={14} className="text-slate-500" />
                    <span className="text-sm text-slate-300">{e.user_nome}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${funcColors[e.funcao] || 'text-slate-400 bg-slate-500/10'}`}>{funcLabels[e.funcao] || e.funcao}</span>
                  </div>
                  {!['concluida','cancelada'].includes(os.status) && ['admin','master','pcm','supervisor'].includes(user?.role) && (
                    <button onClick={() => handleRemoveExec(e.user_id)} className="p-1 hover:bg-red-500/10 rounded" data-testid={`remove-exec-${e.user_id}`}><X size={14} className="text-red-400" /></button>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-slate-600 text-center py-2">Nenhum executante atribuído</p>
        )}
      </div>

      {/* Modal Adicionar Executante */}
      <Modal isOpen={showExecModal} onClose={() => setShowExecModal(false)} title="Adicionar Executante">
        <div className="space-y-4">
          <FormInput label="Técnico" required>
            <select value={execForm.user_id} onChange={e => setExecForm({...execForm, user_id: e.target.value})} className="input-industrial w-full px-4" data-testid="exec-user-select">
              <option value="">Selecione...</option>
              {tecnicos.filter(t => !executantes.find(e => e.user_id === t.id)).map(t => (
                <option key={t.id} value={t.id}>{t.nome} ({t.role})</option>
              ))}
            </select>
          </FormInput>
          <FormInput label="Função">
            <select value={execForm.funcao} onChange={e => setExecForm({...execForm, funcao: e.target.value})} className="input-industrial w-full px-4" data-testid="exec-funcao-select">
              <option value="executor">Executor</option>
              <option value="apoio">Apoio</option>
              <option value="lider">Líder</option>
              <option value="supervisor_exec">Supervisor</option>
              <option value="inspetor_exec">Inspetor</option>
            </select>
          </FormInput>
          <div className="flex justify-end gap-2 pt-2">
            <button onClick={() => setShowExecModal(false)} className="btn-secondary">Cancelar</button>
            <button onClick={handleAddExec} className="btn-primary" data-testid="exec-save-btn">Adicionar</button>
          </div>
        </div>
      </Modal>

      {/* ============ TIMELINE DE EVENTOS ============ */}
      {osEventos.length > 0 && (
        <div className="glass-card p-4" data-testid="os-eventos-timeline">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Activity size={16} /> Timeline ({osEventos.length})
          </h3>
          <div className="space-y-1 max-h-[250px] overflow-y-auto">
            {osEventos.slice(-20).reverse().map((evt, idx) => {
              const evtColors = { trabalho_iniciado: 'border-emerald-500', pausa: 'border-amber-500', retorno: 'border-blue-500', os_concluida: 'border-brand', os_criada: 'border-slate-500', equipe_alterada: 'border-purple-500', campo_alterado: 'border-cyan-500' };
              const evtLabels = { trabalho_iniciado: 'Trabalho iniciado', pausa: 'Pausa', retorno: 'Retorno', os_concluida: 'Finalizado', os_criada: 'OS criada', equipe_alterada: 'Equipe alterada', campo_alterado: 'Campo alterado', material_utilizado: 'Material utilizado', foto_anexada: 'Foto anexada' };
              return (
                <div key={evt.id || idx} className={`flex items-start gap-2 text-xs border-l-2 ${evtColors[evt.tipo] || 'border-slate-700'} pl-3 py-1`}>
                  <div className="flex-1">
                    <span className="text-slate-300 font-medium">{evtLabels[evt.tipo] || evt.tipo}</span>
                    {evt.detalhes?.observacao && <span className="text-slate-500 ml-1">— {evt.detalhes.observacao}</span>}
                    <p className="text-slate-600">{evt.user_nome} · {new Date(evt.timestamp).toLocaleString('pt-BR')}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Serviço Executado (exibido quando concluída) */}
      {os.descricao_servico && (
        <div className="glass-card p-4 border-l-4 border-brand" data-testid="os-servico-executado">
          <p className="text-xs text-brand font-semibold uppercase mb-1">Serviço Executado</p>
          <p className="text-slate-200 whitespace-pre-wrap">{os.descricao_servico}</p>
        </div>
      )}

      {/* Observações */}
      {os.observacoes && (
        <div className="glass-card p-4" data-testid="os-observacoes">
          <p className="text-xs text-slate-500 mb-1">Observações</p>
          <p className="text-slate-200 whitespace-pre-wrap">{os.observacoes}</p>
        </div>
      )}

      {/* Causa da Falha */}
      {os.causa_falha && (
        <div className="glass-card p-4 border-l-4 border-red-500" data-testid="os-causa-falha">
          <p className="text-xs text-red-400 font-semibold uppercase mb-1">Causa da Falha</p>
          <p className="text-slate-200 whitespace-pre-wrap">{os.causa_falha}</p>
        </div>
      )}
      
      {/* Materiais Utilizados */}
      <div className="glass-card p-4" data-testid="os-materiais-section">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Package size={16} /> Materiais Utilizados ({materiais.length})
          </h3>
          {!['concluida','cancelada'].includes(os.status) && !['gerente'].includes(user?.role) && (
            <button onClick={() => setShowMatModal(true)} className="text-xs btn-primary flex items-center gap-1" data-testid="add-material-btn">
              <Plus size={14} /> Adicionar
            </button>
          )}
        </div>
        {materiais.length > 0 ? (
          <div className="space-y-2">
            {materiais.map(m => (
              <div key={m.id} className="flex items-center justify-between bg-slate-800/50 rounded-lg p-3 border border-slate-700/50" data-testid={`material-item-${m.id}`}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-brand text-sm">{m.codigo}</span>
                    <span className="text-slate-300 text-sm">{m.descricao}</span>
                  </div>
                  <p className="text-xs text-slate-500">
                    {m.quantidade} {m.unidade} • {m.local_estoque} • {m.usuario_nome} • {new Date(m.created_at).toLocaleString('pt-BR')}
                  </p>
                </div>
                {m.custo_total > 0 && <span className="text-sm text-slate-300 mx-2">R$ {m.custo_total.toFixed(2)}</span>}
                {!['concluida','cancelada'].includes(os.status) && ['admin','master','pcm','supervisor'].includes(user?.role) && (
                  <button onClick={() => setDeleteMat(m)} className="p-1.5 hover:bg-red-500/10 rounded" title="Devolver"><Trash2 size={14} className="text-red-400" /></button>
                )}
              </div>
            ))}
            <div className="text-right text-sm text-slate-400 pt-1 border-t border-slate-800">
              Total: <span className="text-slate-200 font-semibold">R$ {materiais.reduce((sum, m) => sum + (m.custo_total || 0), 0).toFixed(2)}</span>
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-600 text-center py-3">Nenhum material registrado</p>
        )}
      </div>

      {/* Modal Adicionar Material */}
      <Modal isOpen={showMatModal} onClose={() => setShowMatModal(false)} title="Adicionar Material" size="md">
        <div className="space-y-4">
          <FormInput label="Item do Estoque" required>
            <select value={matForm.item_estoque_id} onChange={e => setMatForm({...matForm, item_estoque_id: e.target.value})} className="input-industrial w-full px-4" data-testid="material-select">
              <option value="">Selecione...</option>
              {estoqueItems.filter(i => i.quantidade > 0).map(i => (
                <option key={i.id} value={i.id}>{i.sku} — {i.nome} (Disp: {i.quantidade} {i.unidade})</option>
              ))}
            </select>
          </FormInput>
          <FormInput label="Quantidade" required>
            <input type="number" step="0.01" min="0.01" value={matForm.quantidade} onChange={e => setMatForm({...matForm, quantidade: e.target.value})} className="input-industrial w-full px-4" data-testid="material-quantidade" />
          </FormInput>
          <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
            <button type="button" onClick={() => setShowMatModal(false)} className="btn-secondary">Cancelar</button>
            <button onClick={handleAddMaterial} className="btn-primary" data-testid="material-submit">Registrar Consumo</button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog isOpen={!!deleteMat} onClose={() => setDeleteMat(null)} onConfirm={handleRemoveMaterial}
        title="Devolver Material" message={`Devolver ${deleteMat?.quantidade} ${deleteMat?.unidade} de "${deleteMat?.codigo} - ${deleteMat?.descricao}" ao estoque?`}
        confirmText="Devolver" />

      {/* Registro Fotográfico */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass-card p-4">
          <PhotoUploader
            entityType="work_order"
            entityId={os.id}
            categoria="foto_antes"
            label="Foto Antes"
            required={['corretiva', 'falha'].includes(os.tipo)}
          />
        </div>
        <div className="glass-card p-4">
          <PhotoUploader
            entityType="work_order"
            entityId={os.id}
            categoria="foto_depois"
            label="Foto Depois"
            required={os.status === 'em_execucao'}
          />
        </div>
      </div>
      
      {/* Histórico Completo */}
      <div className="glass-card p-4" data-testid="os-historico">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
          <Activity size={16} /> Histórico Completo ({historico.length})
        </h3>
        {historico.length > 0 ? (
          <div className="space-y-2">
            {historico.map((h, idx) => (
              <div key={idx} className="flex items-start gap-3 text-sm border-l-2 border-slate-700 pl-3 py-1.5">
                <div className="flex-1">
                  <p className="text-slate-300">{h.details}</p>
                  <p className="text-xs text-slate-500">{h.user_nome} ({h.user_role}) · {new Date(h.created_at).toLocaleString('pt-BR')}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-600 text-center py-3">Nenhuma transição registrada</p>
        )}
      </div>
      
      {/* Actions — OS Detail */}
      {!['concluida', 'cancelada'].includes(os.status) && !['pcm','gerente'].includes(user?.role) && (
        <div className="space-y-2">
          {os.status === 'aberta' && (
            <button onClick={() => handleAction('iniciar')} disabled={updating} className="btn-primary w-full flex items-center justify-center gap-2" data-testid="os-iniciar-btn">
              <Play size={20} /> {updating ? 'Iniciando...' : 'Iniciar OS'}
            </button>
          )}
          {os.status === 'em_execucao' && (
            <>
              <button onClick={() => handleAction('concluir')} disabled={updating} className="btn-primary w-full flex items-center justify-center gap-2" data-testid="os-concluir-btn">
                <CheckCircle size={20} /> Concluir OS
              </button>
              <button onClick={() => handleAction('pausar')} disabled={updating} className="btn-secondary w-full flex items-center justify-center gap-2">
                <Pause size={20} /> Pausar
              </button>
            </>
          )}
          {os.status === 'pausada' && (
            <button onClick={() => handleAction('iniciar')} disabled={updating} className="btn-primary w-full flex items-center justify-center gap-2">
              <Play size={20} /> {updating ? 'Retomando...' : 'Retomar OS'}
            </button>
          )}
        </div>
      )}

      {/* Modal Concluir OS */}
      <Modal isOpen={showConcluir} onClose={() => setShowConcluir(false)} title="Concluir Ordem de Serviço" size="md">
        <div className="space-y-4">
          {/* Ativo info (read-only) */}
          {os.ativo && (
            <div className="bg-slate-800/50 rounded-lg p-3">
              {os.ativo.sector && <p className="text-xs text-slate-500 uppercase">{os.ativo.sector.nome || os.ativo.sector_nome}</p>}
              <span className="font-mono text-brand text-sm">{os.ativo.tag}</span>
              <span className="text-slate-300 text-sm ml-2">{os.ativo.nome}</span>
            </div>
          )}
          <FormInput label="Serviço Executado" required>
            <textarea
              value={concluirForm.servicos_realizados}
              onChange={(e) => setConcluirForm({...concluirForm, servicos_realizados: e.target.value})}
              className="input-industrial w-full px-4 py-3 min-h-[120px]"
              placeholder="Descreva o serviço realizado. Ex: Troca de correias, troca de rolamento, alinhamento..."
              data-testid="os-servico-input"
            />
          </FormInput>
          <FormInput label="Tempo Gasto (minutos)" required>
            <input
              type="number"
              min="1"
              value={concluirForm.tempo_execucao_minutos}
              onChange={(e) => setConcluirForm({...concluirForm, tempo_execucao_minutos: e.target.value})}
              className="input-industrial w-full px-4"
              placeholder="Ex: 60"
              data-testid="os-tempo-input"
            />
          </FormInput>
          <FormInput label="Observações">
            <textarea
              value={concluirForm.observacoes}
              onChange={(e) => setConcluirForm({...concluirForm, observacoes: e.target.value})}
              className="input-industrial w-full px-4 py-3 min-h-[60px]"
              placeholder="Observações adicionais..."
            />
          </FormInput>
          <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
            <button type="button" onClick={() => setShowConcluir(false)} className="btn-secondary">Cancelar</button>
            <button onClick={handleConcluir} disabled={updating} className="btn-primary flex items-center gap-2" data-testid="os-confirmar-conclusao">
              {updating ? <RefreshCw size={16} className="animate-spin" /> : <CheckCircle size={16} />}
              {updating ? 'Concluindo...' : 'Confirmar Conclusão'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

// Estoque Page
const EstoquePage = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCritico, setShowCritico] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const [expandedItem, setExpandedItem] = useState(null);
  const [expandedMovs, setExpandedMovs] = useState([]);
  const [loadingMovs, setLoadingMovs] = useState(false);
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  
  useEffect(() => {
    if (searchParams.get('critico') === 'true') setShowCritico(true);
  }, [searchParams]);
  
  const fetchData = async () => {
    try {
      const response = await api.get(`/estoque${showCritico ? '?critico=true' : ''}`);
      setItems(response.data);
    } catch (error) {
      toast.error('Erro ao carregar estoque');
    } finally {
      setLoading(false);
    }
  };
  
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchData(); }, [showCritico]);
  
  const handleDelete = async () => {
    try {
      await api.delete(`/estoque/${deleteItem.id}`);
      toast.success('Item excluído!');
      setDeleteItem(null);
      fetchData();
    } catch (error) {
      toast.error('Erro ao excluir');
    }
  };
  
  const filtered = search ? items.filter(i => 
    i.nome.toLowerCase().includes(search.toLowerCase()) || (i.sku || '').toLowerCase().includes(search.toLowerCase())
  ) : items;

  // E1: Toggle expand to show movimentações
  const toggleExpand = async (itemId) => {
    if (expandedItem === itemId) {
      setExpandedItem(null);
      setExpandedMovs([]);
      return;
    }
    setExpandedItem(itemId);
    setLoadingMovs(true);
    try {
      const res = await api.get(`/estoque/${itemId}`);
      setExpandedMovs(res.data.movimentacoes || []);
    } catch { setExpandedMovs([]); }
    finally { setLoadingMovs(false); }
  };

  const movTipoConfig = {
    entrada: { label: 'Entrada', class: 'text-emerald-400' },
    saida: { label: 'Saída', class: 'text-red-400' },
    devolucao: { label: 'Devolução', class: 'text-blue-400' },
    ajuste: { label: 'Ajuste', class: 'text-amber-400' },
  };
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-slate-100">Estoque</h1>
          <ExportButtons entity="estoque" />
        </div>
        <button onClick={() => { setEditItem(null); setShowModal(true); }} className="btn-primary flex items-center gap-2" data-testid="add-estoque-btn">
          <Plus size={20} /> Novo Item
        </button>
      </div>
      
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por nome ou código..."
            className="input-industrial w-full pl-10 pr-4"
          />
        </div>
        <button
          onClick={() => setShowCritico(!showCritico)}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 ${showCritico ? 'bg-red-500 text-white' : 'bg-slate-800 text-slate-300'}`}
        >
          <AlertTriangle size={18} /> Crítico
        </button>
      </div>
      
      {loading ? <Loading rows={5} /> : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((item) => (
            <div key={item.id} className={`glass-card hover:border-slate-600 transition-all group ${item.is_critico ? 'border-red-500/50' : ''}`}>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${item.is_critico ? 'bg-red-500/10' : 'bg-brand-10'}`}>
                      <Package size={20} className={item.is_critico ? 'text-red-400' : 'text-emerald-400'} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-brand text-sm">{item.sku}</span>
                        <span className="text-xs text-slate-500 px-2 py-0.5 bg-slate-800 rounded capitalize">{item.categoria}</span>
                      </div>
                      <p className="text-slate-100">{item.nome}</p>
                      {item.prateleira && <p className="text-xs text-slate-500"><MapPin size={12} className="inline mr-1" />{item.almoxarifado} - {item.prateleira}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {/* E1: Expand button */}
                    <button onClick={() => toggleExpand(item.id)} className="p-2 hover:bg-slate-700 rounded-lg transition-colors" title="Ver movimentações" data-testid={`expand-estoque-${item.id}`}>
                      {expandedItem === item.id ? <ChevronUp size={16} className="text-brand" /> : <ChevronDown size={16} className="text-slate-400" />}
                    </button>
                    {['admin','master'].includes(user?.role) && (
                      <div className="hidden group-hover:flex items-center gap-1">
                        <button onClick={() => { setEditItem(item); setShowModal(true); }} className="p-2 hover:bg-slate-700 rounded-lg" title="Editar">
                          <Edit3 size={15} className="text-blue-400" />
                        </button>
                        <button onClick={() => setDeleteItem(item)} className="p-2 hover:bg-red-500/10 rounded-lg" title="Excluir">
                          <Trash2 size={15} className="text-red-400" />
                        </button>
                      </div>
                    )}
                    <div className="text-right">
                      <p className={`text-xl font-bold ${item.is_critico ? 'text-red-400' : 'text-slate-200'}`}>{item.quantidade}</p>
                      <p className="text-xs text-slate-500">{item.unidade}</p>
                    </div>
                  </div>
                </div>
                {item.is_critico && (
                  <div className="mt-2 flex items-center gap-2 text-red-400 text-xs">
                    <AlertTriangle size={14} />
                    Estoque crítico (mín: {item.estoque_minimo})
                  </div>
                )}
              </div>
              {/* E1: Expandable movimentações */}
              {expandedItem === item.id && (
                <div className="border-t border-slate-800 px-4 py-3" data-testid={`movs-${item.id}`}>
                  <p className="text-xs text-slate-500 uppercase font-semibold mb-2">Últimas Movimentações</p>
                  {loadingMovs ? (
                    <div className="py-2 text-xs text-slate-600 animate-pulse">Carregando...</div>
                  ) : expandedMovs.length > 0 ? (
                    <div className="space-y-1.5">
                      {expandedMovs.slice(0, 5).map((mov, idx) => {
                        const cfg = movTipoConfig[mov.tipo] || { label: mov.tipo, class: 'text-slate-400' };
                        return (
                          <div key={mov.id || idx} className="flex items-center justify-between text-xs py-1 border-b border-slate-800/50 last:border-0">
                            <div className="flex items-center gap-2">
                              <span className={`font-medium w-16 ${cfg.class}`}>{cfg.label}</span>
                              <span className="text-slate-300">{mov.quantidade > 0 ? '+' : ''}{mov.quantidade} {item.unidade}</span>
                              {mov.motivo && <span className="text-slate-600 truncate max-w-[200px]">— {mov.motivo}</span>}
                            </div>
                            <span className="text-slate-600 shrink-0">{mov.created_at ? new Date(mov.created_at).toLocaleDateString('pt-BR', {day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}) : ''}</span>
                          </div>
                        );
                      })}
                      {expandedMovs.length > 5 && <p className="text-xs text-slate-600 text-center pt-1">+{expandedMovs.length - 5} movimentações anteriores</p>}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-600 py-1">Nenhuma movimentação registrada</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon={Package} title="Nenhum item encontrado" description="Adicione itens ao estoque." action={() => setShowModal(true)} actionLabel="Novo Item" />
      )}
      
      <ModalNovoEstoque
        isOpen={showModal}
        onClose={() => { setShowModal(false); setEditItem(null); }}
        onSuccess={fetchData}
        editData={editItem}
      />
      
      <ConfirmDialog
        isOpen={!!deleteItem}
        onClose={() => setDeleteItem(null)}
        onConfirm={handleDelete}
        title="Excluir Item"
        message={`Tem certeza que deseja excluir "${deleteItem?.sku || deleteItem?.nome}"?`}
        confirmText="Excluir"
        danger
      />
    </div>
  );
};

// Inspeções Page
const InspecoesPage = () => {
  const [inspecoes, setInspecoes] = useState([]);
  const [ativos, setAtivos] = useState([]);
  const [rotas, setRotas] = useState([]);
  const [tecnicos, setTecnicos] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [deleteItem, setDeleteItem] = useState(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterArea, setFilterArea] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  
  useEffect(() => {
    if (searchParams.get('new') === 'true') setShowModal(true);
  }, [searchParams]);
  
  const fetchData = async () => {
    try {
      const [inspRes, ativosRes, rotasRes, tecnicosRes, sectorsRes] = await Promise.all([
        api.get('/inspecoes'),
        api.get('/ativos'),
        api.get('/rotas-inspecao'),
        api.get('/users/tecnicos'),
        api.get('/sectors')
      ]);
      setInspecoes(inspRes.data);
      setAtivos(ativosRes.data);
      setRotas(rotasRes.data);
      setTecnicos(tecnicosRes.data);
      setSectors(sectorsRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => { fetchData(); }, []);
  
  const handleDelete = async () => {
    try {
      await api.delete(`/inspecoes/${deleteItem.id}`);
      toast.success('Inspeção excluída!');
      setDeleteItem(null);
      fetchData();
    } catch (error) {
      toast.error('Erro ao excluir');
    }
  };

  // I1 + I2: Filter logic
  const filteredInspecoes = inspecoes.filter(insp => {
    if (filterStatus && insp.status !== filterStatus) return false;
    if (filterArea && insp.ativo?.sector_id !== filterArea) return false;
    return true;
  });
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-slate-100">Inspeções</h1>
          <ExportButtons entity="inspecoes" />
        </div>
        <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2" data-testid="add-inspecao-btn">
          <Plus size={20} /> Nova Inspeção
        </button>
      </div>

      {/* I1: Filtro por status + I2: Filtro por área */}
      <div className="flex flex-wrap gap-2 items-center">
        <div className="flex gap-1 overflow-x-auto hide-scrollbar">
          {[
            { value: '', label: 'Todas' },
            { value: 'pendente', label: 'Pendentes' },
            { value: 'em_andamento', label: 'Em Andamento' },
            { value: 'concluida', label: 'Concluídas' },
            { value: 'com_pendencias', label: 'Com Pendências' },
          ].map(f => (
            <button key={f.value} onClick={() => setFilterStatus(f.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${filterStatus === f.value ? 'bg-brand-20 text-brand border border-brand-30' : 'border border-slate-700 text-slate-400 hover:text-slate-300'}`}
              data-testid={`insp-filter-status-${f.value || 'all'}`}
            >
              {f.label}
              {f.value && <span className="ml-1 text-slate-600">({inspecoes.filter(i => i.status === f.value).length})</span>}
            </button>
          ))}
        </div>
        <select
          value={filterArea}
          onChange={(e) => setFilterArea(e.target.value)}
          className="input-industrial px-3 text-sm"
          data-testid="insp-filter-area"
        >
          <option value="">Todas as Áreas</option>
          {sectors.map(s => <option key={s.id} value={s.id}>{s.nome}</option>)}
        </select>
        {(filterStatus || filterArea) && (
          <button onClick={() => { setFilterStatus(''); setFilterArea(''); }} className="text-xs text-slate-500 hover:text-brand" data-testid="insp-clear-filters">Limpar</button>
        )}
      </div>

      <p className="text-xs text-slate-500">{filteredInspecoes.length} inspeção(ões)</p>
      
      {loading ? <Loading rows={5} /> : filteredInspecoes.length > 0 ? (
        <div className="space-y-2">
          {filteredInspecoes.map((insp) => (
            <div key={insp.id} className="glass-card p-4 hover:border-slate-600 transition-all group">
              <div className="flex items-center justify-between">
                <div className="flex-1 cursor-pointer" onClick={() => navigate(`/inspecoes/${insp.id}`)}>
                  <div className="flex items-center gap-2 mb-1">
                    {insp.ativo && (
                      <div>
                        {insp.ativo.sector && <span className="text-[10px] text-slate-600 uppercase block">{insp.ativo.sector?.nome}</span>}
                        <span className="font-mono text-brand text-sm">{insp.ativo.tag}</span>
                        <span className="text-slate-400 text-xs ml-1">{insp.ativo.nome}</span>
                      </div>
                    )}
                    {insp.tipo === 'lubrificacao' ? (
                      <span className="text-xs px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded">Lubrificação</span>
                    ) : insp.frequencia ? (
                      <span className="text-xs px-2 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/30 rounded capitalize">{insp.frequencia}</span>
                    ) : null}
                  </div>
                  <p className="text-slate-100">
                    {insp.tipo === 'lubrificacao' 
                      ? `Lubrificação - ${insp.ativo?.nome || ''}` 
                      : insp.rota?.nome || `Inspeção ${insp.frequencia ? insp.frequencia.charAt(0).toUpperCase() + insp.frequencia.slice(1) : ''} - ${insp.ativo?.nome || ''}`
                    }
                  </p>
                  <p className="text-xs text-slate-500">
                    {new Date(insp.data_programada || insp.created_at).toLocaleDateString('pt-BR')} • {insp.responsavel?.nome}
                    {insp.tipo_lubrificante && ` • ${insp.tipo_lubrificante.replace(/_/g, ' ')}`}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {['admin','master','supervisor'].includes(user?.role) && (
                    <button onClick={() => setDeleteItem(insp)} className="p-2 hover:bg-red-500/10 rounded-lg opacity-0 group-hover:opacity-100" data-testid={`delete-inspecao-${insp.id}`}>
                      <Trash2 size={16} className="text-red-400" />
                    </button>
                  )}
                  <StatusBadge status={insp.status} size="sm" />
                  {insp.resultado && insp.resultado !== 'pendente' && (
                    <StatusBadge status={insp.resultado} size="sm" />
                  )}
                  <ChevronRight className="text-slate-600" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon={ClipboardCheck} title="Nenhuma inspeção encontrada" description={filterStatus || filterArea ? "Ajuste os filtros para ver resultados." : "Crie uma nova inspeção."} action={() => { if (!filterStatus && !filterArea) setShowModal(true); else { setFilterStatus(''); setFilterArea(''); } }} actionLabel={filterStatus || filterArea ? "Limpar Filtros" : "Nova Inspeção"} />
      )}
      
      <ModalNovaInspecao
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={fetchData}
        ativos={ativos}
        rotas={rotas}
        tecnicos={tecnicos}
        preSelectedAtivoId={searchParams.get('ativo') || null}
      />
      
      <ConfirmDialog
        isOpen={!!deleteItem}
        onClose={() => setDeleteItem(null)}
        onConfirm={handleDelete}
        title="Excluir Inspeção"
        message="Tem certeza que deseja excluir esta inspeção?"
        confirmText="Excluir"
        danger
      />
    </div>
  );
};

// Inspeção Detail / Execução
const InspecaoDetailPage = () => {
  const { id } = useParams();
  const [inspecao, setInspecao] = useState(null);
  const [checklist, setChecklist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const fetchInspecao = async () => {
    try {
      const response = await api.get(`/inspecoes/${id}`);
      setInspecao(response.data);
      setChecklist(response.data.checklist || []);
    } catch (error) {
      toast.error('Inspeção não encontrada');
      navigate('/inspecoes');
    } finally {
      setLoading(false);
    }
  };
  
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchInspecao(); }, [id]);
  
  const handleItemChange = (itemId, field, value) => {
    setChecklist(prev => prev.map(item => 
      item.id === itemId ? { ...item, [field]: value } : item
    ));
  };
  
  const handleIniciar = async () => {
    try {
      await api.post(`/inspecoes/${id}/iniciar`);
      toast.success('Inspeção iniciada!');
      fetchInspecao();
    } catch (error) {
      toast.error('Erro ao iniciar');
    }
  };
  
  const handleConcluir = async () => {
    const isItemFilled = (item) => {
      const t = item.tipo || 'boolean';
      if (t === 'boolean') return item.conforme !== null && item.conforme !== undefined;
      if (t === 'numero' || t === 'numerico') return item.resultado !== null && item.resultado !== undefined && item.resultado !== '';
      if (t === 'texto' || t === 'observacao') return item.resultado !== null && item.resultado !== undefined && item.resultado !== '';
      if (t === 'opcao' || t === 'temperatura' || t === 'vibracao') return item.resultado !== null && item.resultado !== undefined && item.resultado !== '';
      return item.resultado !== undefined;
    };
    const missing = checklist.filter(item => item.obrigatorio && !isItemFilled(item));
    if (missing.length > 0) {
      toast.error(`Preencha todos os itens obrigatórios (${missing.length} faltando)`);
      return;
    }
    
    setSubmitting(true);
    try {
      const result = await api.post(`/inspecoes/${id}/concluir`, {
        checklist,
        observacoes: ''
      });
      
      if (result.data.os_gerada_id) {
        toast.warning(`Inspeção não conforme - OS gerada automaticamente`);
      } else {
        toast.success(`Inspeção concluída em ${result.data.duracao_minutos || 0} minutos!`);
      }
      navigate('/inspecoes');
    } catch (error) {
      toast.error(normalizeError(error) || 'Erro ao concluir');
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) return <Loading rows={4} />;
  if (!inspecao) return null;
  
  const isFinished = ['concluida', 'com_pendencias'].includes(inspecao.status);
  const naoConformes = checklist.filter(i => i.conforme === false);
  const conformes = checklist.filter(i => i.conforme === true);
  
  return (
    <div className="space-y-4 pb-24" data-testid="inspecao-detail-page">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/inspecoes')} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg">
          <ArrowLeft size={20} className="text-slate-400" />
        </button>
        <div className="flex-1">
          {inspecao.ativo && (
            <div className="mb-1">
              {inspecao.ativo.sector && <p className="text-xs text-slate-500 uppercase">{inspecao.ativo.sector?.nome}</p>}
              <span className="font-mono text-brand">{inspecao.ativo.tag}</span>
              <span className="text-slate-300 ml-2">{inspecao.ativo.nome}</span>
            </div>
          )}
          <h1 className="text-lg font-bold text-slate-100">
            {inspecao.tipo === 'lubrificacao' 
              ? `Lubrificação - ${inspecao.ativo?.nome || ''}`
              : inspecao.rota?.nome || `Inspeção ${inspecao.frequencia ? inspecao.frequencia.charAt(0).toUpperCase() + inspecao.frequencia.slice(1) : ''} - ${inspecao.ativo?.nome || ''}`
            }
          </h1>
        </div>
        <div className="flex items-center gap-2">
          {inspecao.tipo === 'lubrificacao' && (
            <span className="text-xs px-2 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded">Lubrificação</span>
          )}
          <StatusBadge status={inspecao.status} />
          {inspecao.resultado && inspecao.resultado !== 'pendente' && <StatusBadge status={inspecao.resultado} />}
        </div>
      </div>

      {/* Dados Gerais */}
      <div className="glass-card p-4" data-testid="inspecao-dados-gerais">
        <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider mb-2">Dados Gerais</p>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div><span className="text-slate-500">Tipo:</span> <span className="text-slate-200 capitalize">{inspecao.tipo}</span></div>
          {inspecao.frequencia && <div><span className="text-slate-500">Frequência:</span> <span className="text-slate-200 capitalize">{inspecao.frequencia}</span></div>}
          {inspecao.ativo?.tipo_equipamento && <div><span className="text-slate-500">Tipo Equip.:</span> <span className="text-slate-200">{inspecao.ativo.tipo_equipamento}</span></div>}
          {inspecao.ativo?.fabricante && <div><span className="text-slate-500">Fabricante:</span> <span className="text-slate-200">{inspecao.ativo.fabricante}</span></div>}
          {inspecao.ativo?.modelo && <div><span className="text-slate-500">Modelo:</span> <span className="text-slate-200">{inspecao.ativo.modelo}</span></div>}
          {inspecao.ativo?.numero_serie && <div><span className="text-slate-500">Série:</span> <span className="text-slate-200 font-mono">{inspecao.ativo.numero_serie}</span></div>}
          {inspecao.duracao_minutos && <div><span className="text-slate-500">Duração:</span> <span className="text-brand font-semibold">{inspecao.duracao_minutos} min</span></div>}
        </div>
      </div>
      
      {/* Lubrificação Info */}
      {inspecao.tipo === 'lubrificacao' && (inspecao.tipo_lubrificante || inspecao.ponto_lubrificacao) && (
        <div className="glass-card p-4 space-y-2 border-amber-500/30">
          <h3 className="text-sm font-semibold text-amber-400 flex items-center gap-2"><Droplet size={16} /> Dados da Lubrificação</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {inspecao.tipo_lubrificante && <div><span className="text-slate-500">Lubrificante:</span> <span className="text-slate-200 capitalize">{inspecao.tipo_lubrificante.replace(/_/g, ' ')}</span></div>}
            {inspecao.quantidade_lubrificante && <div><span className="text-slate-500">Quantidade:</span> <span className="text-slate-200">{inspecao.quantidade_lubrificante}</span></div>}
            {inspecao.ponto_lubrificacao && <div><span className="text-slate-500">Ponto:</span> <span className="text-slate-200">{inspecao.ponto_lubrificacao}</span></div>}
            {inspecao.metodo_aplicacao && <div><span className="text-slate-500">Método:</span> <span className="text-slate-200 capitalize">{inspecao.metodo_aplicacao}</span></div>}
          </div>
          {inspecao.observacoes_lubrificacao && <p className="text-xs text-slate-400 mt-2">{inspecao.observacoes_lubrificacao}</p>}
        </div>
      )}
      
      {/* Rastreabilidade e Executantes */}
      <div className="glass-card p-4 space-y-3" data-testid="inspecao-rastreabilidade">
        {inspecao.responsavel && (
          <div className="flex justify-between text-sm"><span className="text-slate-500">Responsável</span><span className="text-slate-200">{inspecao.responsavel.nome}</span></div>
        )}
        {(inspecao.executantes?.length > 0) && (
          <div className="text-sm">
            <span className="text-slate-500 block mb-1">Executantes</span>
            <div className="flex flex-wrap gap-1">
              {inspecao.executantes.map(uid => (
                <span key={uid} className="text-xs bg-slate-800 text-slate-300 px-2 py-1 rounded">{inspecao.executantes_nomes?.[uid] || uid}</span>
              ))}
            </div>
          </div>
        )}
        <div className="border-t border-slate-800 pt-2 space-y-2">
          <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider">Rastreabilidade</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
            <div><span className="text-slate-500">Criado por:</span> <span className="text-slate-300">{inspecao.criado_por_nome || '—'}</span></div>
            <div><span className="text-slate-500">Data criação:</span> <span className="text-slate-300">{inspecao.created_at ? new Date(inspecao.created_at).toLocaleString('pt-BR') : '—'}</span></div>
            <div><span className="text-slate-500">Iniciado por:</span> <span className="text-slate-300">{inspecao.iniciado_por_nome || '—'}</span></div>
            <div><span className="text-slate-500">Data início:</span> <span className="text-slate-300">{inspecao.data_inicio ? new Date(inspecao.data_inicio).toLocaleString('pt-BR') : '—'}</span></div>
            <div><span className="text-slate-500">Concluído por:</span> <span className="text-slate-300">{inspecao.concluido_por_nome || '—'}</span></div>
            <div><span className="text-slate-500">Data conclusão:</span> <span className="text-slate-300">{inspecao.data_conclusao ? new Date(inspecao.data_conclusao).toLocaleString('pt-BR') : '—'}</span></div>
            {inspecao.alterado_por_nome && (
              <>
                <div><span className="text-slate-500">Última alteração por:</span> <span className="text-amber-400">{inspecao.alterado_por_nome}</span></div>
                <div><span className="text-slate-500">Data alteração:</span> <span className="text-amber-400">{inspecao.updated_at ? new Date(inspecao.updated_at).toLocaleString('pt-BR') : '—'}</span></div>
              </>
            )}
          </div>
        </div>
      </div>
      
      {/* Observações */}
      {inspecao.observacoes && (
        <div className="glass-card p-4" data-testid="inspecao-observacoes">
          <p className="text-xs text-slate-500 mb-1">Observações</p>
          <p className="text-slate-200 whitespace-pre-wrap">{inspecao.observacoes}</p>
        </div>
      )}

      {inspecao.status === 'pendente' && !['pcm','gerente'].includes(user?.role) && (
        <button onClick={handleIniciar} className="btn-primary w-full flex items-center justify-center gap-2" data-testid="inspecao-iniciar-btn">
          <Play size={20} /> Iniciar Inspeção
        </button>
      )}
      
      {/* Checklist */}
      {inspecao.status !== 'pendente' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm text-slate-400">Checklist</h3>
            <div className="flex items-center gap-3 text-xs text-slate-500">
              {isFinished && <span className="text-brand">{conformes.length} conforme(s)</span>}
              {isFinished && naoConformes.length > 0 && <span className="text-red-400">{naoConformes.length} não conforme(s)</span>}
              <span>{checklist.filter(i => {
                const t = i.tipo || 'boolean';
                return t === 'boolean' ? (i.conforme !== null && i.conforme !== undefined) : (i.resultado !== null && i.resultado !== undefined && i.resultado !== '');
              }).length}/{checklist.length} respondidos</span>
            </div>
          </div>
          
          {checklist.map((item, idx) => {
            const itemTipo = item.tipo || 'boolean';
            const isNumeric = itemTipo === 'numero' || itemTipo === 'numerico' || itemTipo === 'temperatura' || itemTipo === 'vibracao';
            const isOption = itemTipo === 'opcao';
            const isText = itemTipo === 'texto' || itemTipo === 'observacao';
            const isBool = itemTipo === 'boolean';
            const isFilled = isBool ? (item.conforme !== null && item.conforme !== undefined) : (item.resultado !== null && item.resultado !== undefined && item.resultado !== '');
            return (
            <div key={item.id} className={`glass-card p-4 ${isFilled ? 'border-emerald-500/30' : ''}`}>
              <div className="flex items-start gap-3">
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                  isFilled ? 'bg-brand text-slate-950' : 'bg-slate-800 text-slate-400'
                }`}>{idx + 1}</span>
                <div className="flex-1">
                  <p className="text-sm text-slate-200">{item.descricao} {item.obrigatorio && <span className="text-red-400">*</span>}</p>
                  {item.unidade && <span className="text-xs text-slate-500">{item.unidade}</span>}
                  
                  {!isFinished && isBool && (
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={() => {
                          handleItemChange(item.id, 'resultado', true);
                          handleItemChange(item.id, 'conforme', true);
                        }}
                        className={`flex-1 py-3 rounded-lg border transition-all ${
                          item.conforme === true ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400' : 'border-slate-700 text-slate-400'
                        }`}
                      >
                        <CheckCircle size={20} className="mx-auto mb-1" />
                        Conforme
                      </button>
                      <button
                        onClick={() => {
                          handleItemChange(item.id, 'resultado', false);
                          handleItemChange(item.id, 'conforme', false);
                        }}
                        className={`flex-1 py-3 rounded-lg border transition-all ${
                          item.conforme === false ? 'bg-red-500/20 border-red-500 text-red-400' : 'border-slate-700 text-slate-400'
                        }`}
                      >
                        <XCircle size={20} className="mx-auto mb-1" />
                        Não Conforme
                      </button>
                    </div>
                  )}
                  
                  {!isFinished && isNumeric && (
                    <div className="mt-3 flex gap-2">
                      <input
                        type="number"
                        step="0.1"
                        value={item.resultado ?? ''}
                        onChange={(e) => {
                          const val = e.target.value === '' ? '' : parseFloat(e.target.value);
                          handleItemChange(item.id, 'resultado', val);
                          if (item.tolerancia_min !== undefined && item.tolerancia_max !== undefined && val !== '') {
                            handleItemChange(item.id, 'conforme', val >= item.tolerancia_min && val <= item.tolerancia_max);
                          }
                        }}
                        placeholder={item.tolerancia_min !== undefined ? `${item.tolerancia_min} - ${item.tolerancia_max}` : 'Valor'}
                        className="input-industrial flex-1 px-4"
                      />
                      {item.unidade && <span className="input-industrial px-4 flex items-center text-slate-400">{item.unidade}</span>}
                    </div>
                  )}
                  
                  {!isFinished && isOption && (
                    <div className="flex gap-2 mt-3 flex-wrap">
                      {['Bom', 'Regular', 'Ruim', 'Crítico'].map(opt => (
                        <button key={opt} onClick={() => {
                          handleItemChange(item.id, 'resultado', opt);
                          handleItemChange(item.id, 'conforme', opt === 'Bom' || opt === 'Regular');
                        }} className={`px-4 py-2 rounded-lg border text-sm transition-all ${
                          item.resultado === opt
                            ? (opt === 'Bom' || opt === 'Regular' ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400' : 'bg-red-500/20 border-red-500 text-red-400')
                            : 'border-slate-700 text-slate-400 hover:border-slate-500'
                        }`}>{opt}</button>
                      ))}
                    </div>
                  )}
                  
                  {!isFinished && isText && (
                    <textarea
                      value={item.resultado || ''}
                      onChange={(e) => handleItemChange(item.id, 'resultado', e.target.value)}
                      className="input-industrial w-full px-4 py-3 mt-3"
                      placeholder="Digite aqui..."
                      rows={2}
                    />
                  )}
                  
                  {isFinished && (
                    <div className="mt-2">
                      {isBool && <StatusBadge status={item.conforme ? 'conforme' : 'nao_conforme'} size="sm" />}
                      {isNumeric && item.resultado !== undefined && (
                        <span className={`text-sm ${item.conforme ? 'text-emerald-400' : 'text-red-400'}`}>
                          {item.resultado} {item.unidade}
                          {item.tolerancia_min !== undefined && <span className="text-xs text-slate-500 ml-2">(Faixa: {item.tolerancia_min} - {item.tolerancia_max})</span>}
                        </span>
                      )}
                      {isOption && item.resultado && (
                        <span className={`text-sm px-2 py-1 rounded ${item.conforme ? 'text-emerald-400 bg-brand-10' : 'text-red-400 bg-red-500/10'}`}>{item.resultado}</span>
                      )}
                      {isText && item.resultado && (
                        <p className="text-sm text-slate-300 bg-slate-800/50 rounded p-2 mt-1">{item.resultado}</p>
                      )}
                      {item.observacao && (
                        <p className="text-xs text-red-400/80 mt-1 bg-red-500/5 rounded p-2 border border-red-500/20">{item.observacao}</p>
                      )}
                    </div>
                  )}
                  
                  {!isFinished && item.conforme === false && isBool && (
                    <textarea
                      value={item.observacao || ''}
                      onChange={(e) => handleItemChange(item.id, 'observacao', e.target.value)}
                      placeholder="Descreva a não conformidade..."
                      className="input-industrial w-full px-4 py-3 mt-3 border-red-500/50"
                      rows={2}
                    />
                  )}
                </div>
              </div>
            </div>
            );
          })}
        </div>
      )}
      
      {/* Resultado */}
      {isFinished && inspecao.resultado && (
        <div className={`glass-card p-4 ${inspecao.resultado === 'conforme' ? 'border-emerald-500' : 'border-red-500'}`}>
          <div className="flex items-center gap-3">
            {inspecao.resultado === 'conforme' ? (
              <CheckCircle size={24} className="text-brand" />
            ) : (
              <XCircle size={24} className="text-red-400" />
            )}
            <div>
              <p className={`font-semibold ${inspecao.resultado === 'conforme' ? 'text-emerald-400' : 'text-red-400'}`}>
                {inspecao.resultado === 'conforme' ? 'Inspeção Conforme' : 'Inspeção Não Conforme'}
              </p>
              {inspecao.duracao_minutos && (
                <p className="text-xs text-slate-500">Duração: {inspecao.duracao_minutos} minutos</p>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* OS Geradas */}
      {(inspecao.os_vinculadas?.length > 0 || inspecao.os_gerada) && (
        <div className="glass-card p-4" data-testid="inspecao-os-geradas">
          <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wider mb-2 flex items-center gap-2">
            <Wrench size={16} /> OS Geradas ({inspecao.os_vinculadas?.length || (inspecao.os_gerada ? 1 : 0)})
          </h3>
          <div className="space-y-2">
            {(inspecao.os_vinculadas || (inspecao.os_gerada ? [inspecao.os_gerada] : [])).map(os => (
              <div key={os.id} className="flex items-center justify-between bg-slate-800/50 rounded-lg p-3 cursor-pointer hover:bg-slate-800" onClick={() => navigate(`/os/${os.id}`)}>
                <div>
                  <span className="font-mono text-amber-400">#{os.numero}</span>
                  <span className="text-slate-300 text-sm ml-2">{os.titulo}</span>
                </div>
                <div className="flex items-center gap-2">
                  {os.responsavel_nome && <span className="text-xs text-slate-500">{os.responsavel_nome}</span>}
                  <StatusBadge status={os.status} size="sm" />
                  <ChevronRight size={16} className="text-slate-600" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Registro Fotográfico */}
      {inspecao.id && (
        <div className="glass-card p-4">
          <PhotoUploader
            entityType="inspection"
            entityId={inspecao.id}
            label="Registro Fotográfico"
            required={checklist.some(i => i.conforme === false)}
          />
        </div>
      )}
      
      {/* Histórico Completo */}
      {inspecao.historico?.length > 0 && (
        <div className="glass-card p-4" data-testid="inspecao-historico">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Activity size={16} /> Histórico ({inspecao.historico.length})
          </h3>
          <div className="space-y-2">
            {inspecao.historico.map((h, idx) => (
              <div key={idx} className="flex items-start gap-3 text-sm border-l-2 border-slate-700 pl-3 py-1.5">
                <div className="flex-1">
                  <p className="text-slate-300">{h.details}</p>
                  <p className="text-xs text-slate-500">{h.user_name} · {new Date(h.created_at).toLocaleString('pt-BR')}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action */}
      {inspecao.status === 'em_andamento' && !['pcm','gerente'].includes(user?.role) && (
        <div className="fixed bottom-16 left-0 right-0 p-4 bg-slate-950/95 backdrop-blur-sm border-t border-slate-800 md:bottom-0">
          <button
            onClick={handleConcluir}
            disabled={submitting}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {submitting ? <RefreshCw size={20} className="animate-spin" /> : <CheckCircle size={20} />}
            {submitting ? 'Finalizando...' : 'Concluir Inspeção'}
          </button>
        </div>
      )}
    </div>
  );
};

// Ronda Page — Full inspection workflow: Área → Equipamento → Inspeção
const RondaPage = () => {
  const [areas, setAreas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedArea, setSelectedArea] = useState(null);
  const [areaDetail, setAreaDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [selectedAtivo, setSelectedAtivo] = useState(null);
  const [tipoInspecao, setTipoInspecao] = useState(null);
  const [templates, setTemplates] = useState({});
  const [checklist, setChecklist] = useState([]);
  const [executing, setExecuting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [photos, setPhotos] = useState([]);
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Step 1: Load areas
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
  
  // Step 2: Select area → load equipments
  const selectArea = async (areaId) => {
    setLoadingDetail(true);
    setSelectedArea(areaId);
    setSelectedAtivo(null);
    setTipoInspecao(null);
    setExecuting(false);
    try {
      const response = await api.get(`/ronda/${areaId}`);
      setAreaDetail(response.data);
    } catch (error) {
      toast.error(normalizeError(error));
    } finally {
      setLoadingDetail(false);
    }
  };
  
  // Step 3: Select equipment → load approved plans
  const selectAtivo = async (ativo) => {
    setSelectedAtivo(ativo);
    setTipoInspecao(null);
    setExecuting(false);
    setChecklist([]);
    setPhotos([]);
    // Load approved plans for this asset
    try {
      const res = await api.get(`/planos-inspecao/por-ativo/${ativo.id}`);
      setTemplates(res.data || []);
    } catch {
      setTemplates([]);
    }
  };
  
  // Step 4: Select plan → load checklist from plan
  const selectTipo = (plano) => {
    setTipoInspecao(plano);
    const perguntas = (plano.perguntas || []).map(p => ({
      id: p.id || String(Math.random()),
      descricao: p.texto || p.descricao || '',
      tipo: p.tipo_campo || p.tipo || 'boolean',
      obrigatorio: p.obrigatoria ?? p.obrigatorio ?? true,
      unidade: p.unidade || '',
      tolerancia_min: p.valor_min ?? p.tolerancia_min ?? null,
      tolerancia_max: p.valor_max ?? p.tolerancia_max ?? null,
      valor: null, conforme: null, observacao: ''
    }));
    setChecklist(perguntas);
    setExecuting(true);
  };
  
  // Update checklist item
  const updateChecklistItem = (itemId, field, value) => {
    setChecklist(prev => prev.map(item => 
      item.id === itemId ? {...item, [field]: value} : item
    ));
  };
  
  // Step 5: Submit inspection (linked to plan)
  const submitInspecao = async () => {
    const obrigatorios = checklist.filter(i => i.obrigatorio);
    const incompletos = obrigatorios.filter(i => i.tipo === 'boolean' && i.conforme === null);
    if (incompletos.length > 0) {
      toast.error(`${incompletos.length} item(ns) obrigatório(s) não preenchido(s)`);
      return;
    }
    
    setSubmitting(true);
    try {
      const payload = {
        ativo_id: selectedAtivo.id,
        plano_id: tipoInspecao.id,
        tipo: tipoInspecao.tipo || tipoInspecao.categoria || 'inspecao',
        disciplina: tipoInspecao.disciplina || null,
        responsavel_id: user?.id,
        checklist: checklist,
        observacoes: null,
      };
      
      if (!navigator.onLine) {
        await queueOperation({ method: 'POST', url: '/inspecoes', data: payload });
        toast.info('Sem conexão — inspeção salva para sincronizar');
      } else {
        const res = await api.post('/inspecoes', payload);
        // Upload photos if any
        for (const photo of photos) {
          const formData = new FormData();
          formData.append('file', photo);
          formData.append('entity_type', 'inspection');
          formData.append('entity_id', res.data.id);
          await api.post('/attachments', formData, { headers: { 'Content-Type': 'multipart/form-data' } }).catch(() => {});
        }
        toast.success('Inspeção concluída!');
      }
      
      // Reset to equipment list
      setExecuting(false);
      setTipoInspecao(null);
      setSelectedAtivo(null);
      setChecklist([]);
      setPhotos([]);
      // Refresh area detail
      if (selectedArea) selectArea(selectedArea);
    } catch (error) {
      toast.error(normalizeError(error));
    } finally {
      setSubmitting(false);
    }
  };
  
  const handleCameraCapture = (file) => {
    setPhotos(prev => [...prev, file]);
    setShowCamera(false);
    toast.success('Foto capturada!');
  };
  
  // Back navigation
  const goBack = () => {
    if (executing) { setExecuting(false); setTipoInspecao(null); }
    else if (selectedAtivo) { setSelectedAtivo(null); }
    else if (selectedArea) { setSelectedArea(null); setAreaDetail(null); }
  };
  
  if (loading) return <Loading rows={4} />;
  
  // Camera overlay
  if (showCamera) return <CameraCapture onCapture={handleCameraCapture} onClose={() => setShowCamera(false)} />;
  
  return (
    <div className="space-y-4" data-testid="ronda-page">
      {/* Header with breadcrumb */}
      <div className="flex items-center gap-3">
        {(selectedArea || selectedAtivo || executing) && (
          <button onClick={goBack} className="p-2 rounded-lg hover:bg-slate-800 transition-all" data-testid="ronda-back-btn">
            <ArrowLeft size={20} className="text-slate-400" />
          </button>
        )}
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Target size={24} className="text-brand" /> Modo Ronda
          </h1>
          <p className="text-sm text-slate-500">
            {!selectedArea && 'Selecione uma área para iniciar'}
            {selectedArea && !selectedAtivo && `${areaDetail?.area_nome || ''} — Selecione o equipamento`}
            {selectedAtivo && !executing && `${selectedAtivo.tag} — Planos disponíveis`}
            {executing && `${selectedAtivo.tag} — ${tipoInspecao?.nome || 'Execução'}`}
          </p>
        </div>
      </div>
      
      {/* STEP 1: Area list */}
      {!selectedArea && (
        <div className="space-y-3" data-testid="ronda-areas">
          {areas.length === 0 ? (
            <EmptyState icon={Target} title="Nenhuma área cadastrada" description="Cadastre áreas para iniciar rondas" />
          ) : areas.map(({ area, total_ativos, inspecoes_pendentes }) => (
            <div
              key={area.id}
              className="glass-card p-4 cursor-pointer hover:border-brand transition-all active:scale-[0.99]"
              onClick={() => selectArea(area.id)}
              data-testid={`ronda-area-${area.codigo || area.id}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: (area.cor || '#10b981') + '20' }}>
                    <MapPin size={20} style={{ color: area.cor || '#10b981' }} />
                  </div>
                  <div>
                    <p className="text-slate-100 font-semibold">{area.nome}</p>
                    <p className="text-sm text-slate-500">{total_ativos} equipamentos</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {inspecoes_pendentes > 0 && (
                    <span className="bg-amber-500/20 text-amber-400 text-xs font-medium px-2 py-1 rounded-full">{inspecoes_pendentes} pendente{inspecoes_pendentes > 1 ? 's' : ''}</span>
                  )}
                  <ChevronRight className="text-slate-600" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* STEP 2: Equipment list */}
      {selectedArea && !selectedAtivo && (
        <div className="space-y-3" data-testid="ronda-equipamentos">
          {loadingDetail ? <Loading rows={3} /> : (
            areaDetail?.ativos?.length === 0 ? (
              <EmptyState icon={Box} title="Nenhum equipamento nesta área" description="Cadastre ativos para esta área" />
            ) : areaDetail?.ativos?.map(({ ativo, ultima_inspecao, tem_pendente, ordem }) => (
              <div
                key={ativo.id}
                className="glass-card p-4 cursor-pointer hover:border-brand transition-all active:scale-[0.99]"
                onClick={() => selectAtivo(ativo)}
                data-testid={`ronda-ativo-${ativo.tag}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-600 font-mono w-6">{ordem}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-brand text-sm">{ativo.tag}</span>
                        {tem_pendente && <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />}
                      </div>
                      <p className="text-slate-200 text-sm">{ativo.nome}</p>
                      <p className="text-xs text-slate-500">{ativo.tipo_equipamento}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    {ultima_inspecao ? (
                      <div className="text-xs text-slate-500">
                        <p>Última: {ultima_inspecao.tipo}</p>
                        <p>{new Date(ultima_inspecao.created_at).toLocaleDateString('pt-BR')}</p>
                      </div>
                    ) : (
                      <span className="text-xs text-amber-400">Nunca inspecionado</span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
      
      {/* STEP 3: Plan selection (from approved plans) */}
      {selectedAtivo && !executing && (
        <div className="space-y-4" data-testid="ronda-tipo-inspecao">
          <div className="glass-card p-4">
            <div className="flex items-center gap-3 mb-2">
              <span className="font-mono text-brand">{selectedAtivo.tag}</span>
              <span className="text-slate-200">{selectedAtivo.nome}</span>
            </div>
            <p className="text-xs text-slate-500">{selectedAtivo.tipo_equipamento} {selectedAtivo.fabricante ? `• ${selectedAtivo.fabricante}` : ''}</p>
          </div>
          
          <p className="text-sm text-slate-400 font-medium">Planos disponíveis para execução:</p>
          
          {Array.isArray(templates) && templates.length > 0 ? (
            <div className="grid grid-cols-1 gap-3">
              {templates.map(plano => {
                const tipoIcons = { mecanica: Cog, eletrica: Zap, lubrificacao: Droplet, preventiva: Shield, inspecao: ClipboardCheck, limpeza: Sparkles };
                const tipoColors = { mecanica: '#10b981', eletrica: '#3b82f6', lubrificacao: '#f59e0b', preventiva: '#8b5cf6', inspecao: '#10b981', limpeza: '#06b6d4' };
                const Icon = tipoIcons[plano.tipo] || tipoIcons[plano.disciplina] || ClipboardCheck;
                const color = tipoColors[plano.tipo] || tipoColors[plano.disciplina] || '#64748b';
                return (
                  <button
                    key={plano.id}
                    onClick={() => selectTipo(plano)}
                    className="glass-card p-5 text-left hover:border-brand transition-all active:scale-[0.99] flex items-center gap-4"
                    data-testid={`ronda-plano-${plano.id}`}
                  >
                    <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ backgroundColor: color + '20' }}>
                      <Icon size={24} style={{ color }} />
                    </div>
                    <div className="flex-1">
                      <p className="text-slate-100 font-semibold">{plano.nome}</p>
                      <p className="text-xs text-slate-500">{(plano.perguntas || []).length} perguntas • v{plano.versao || 1}</p>
                    </div>
                    <ChevronRight className="text-slate-600" />
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="glass-card p-8 text-center">
              <ClipboardCheck size={40} className="text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400 font-medium">Nenhum plano aprovado</p>
              <p className="text-xs text-slate-600 mt-1">O PCM precisa criar e aprovar planos para este ativo.</p>
            </div>
          )}
        </div>
      )}
      
      {/* STEP 4: Execute checklist */}
      {executing && (
        <div className="space-y-4" data-testid="ronda-checklist">
          <div className="glass-card p-3 flex items-center justify-between">
            <div>
              <span className="font-mono text-brand text-sm">{selectedAtivo.tag}</span>
              <span className="text-slate-400 text-sm ml-2">{selectedAtivo.nome}</span>
            </div>
            <span className="text-xs bg-slate-800 px-2 py-1 rounded">{tipoInspecao?.nome || ''}</span>
          </div>
          
          {/* Checklist items */}
          <div className="space-y-2">
            {checklist.map((item, idx) => (
              <div key={item.id} className="glass-card p-4 space-y-2" data-testid={`checklist-item-${idx}`}>
                <div className="flex items-start gap-2">
                  <span className="text-xs text-slate-600 font-mono w-6 pt-0.5">{idx + 1}</span>
                  <div className="flex-1">
                    <p className="text-sm text-slate-200">{item.descricao} {item.obrigatorio && <span className="text-red-400">*</span>}</p>
                    
                    {/* Boolean type: OK / NOK */}
                    {item.tipo === 'boolean' && (
                      <div className="flex gap-2 mt-2">
                        <button onClick={() => updateChecklistItem(item.id, 'conforme', true)} className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${item.conforme === true ? 'bg-brand-20 text-brand border border-emerald-500/50' : 'bg-slate-800/50 text-slate-500 border border-slate-700'}`}>
                          <CheckCircle size={16} className="inline mr-1" /> OK
                        </button>
                        <button onClick={() => updateChecklistItem(item.id, 'conforme', false)} className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${item.conforme === false ? 'bg-red-500/20 text-red-400 border border-red-500/50' : 'bg-slate-800/50 text-slate-500 border border-slate-700'}`}>
                          <XCircle size={16} className="inline mr-1" /> NOK
                        </button>
                      </div>
                    )}
                    
                    {/* Numeric type */}
                    {item.tipo === 'numerico' && (
                      <div className="flex items-center gap-2 mt-2">
                        <input type="number" step="0.1" value={item.valor || ''} onChange={(e) => updateChecklistItem(item.id, 'valor', e.target.value)} className="input-industrial flex-1 px-3 py-2 text-sm" placeholder={`${item.tolerancia_min || ''}${item.tolerancia_min ? ' - ' : ''}${item.tolerancia_max || ''} ${item.unidade || ''}`} />
                        {item.unidade && <span className="text-xs text-slate-500">{item.unidade}</span>}
                      </div>
                    )}
                    
                    {/* Option type */}
                    {item.tipo === 'opcao' && (
                      <div className="flex gap-1 mt-2 flex-wrap">
                        {['Bom', 'Regular', 'Ruim'].map(opt => (
                          <button key={opt} onClick={() => updateChecklistItem(item.id, 'valor', opt)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${item.valor === opt ? (opt === 'Bom' ? 'bg-brand-20 text-brand border border-emerald-500/50' : opt === 'Regular' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50' : 'bg-red-500/20 text-red-400 border border-red-500/50') : 'bg-slate-800/50 text-slate-500 border border-slate-700'}`}>
                            {opt}
                          </button>
                        ))}
                      </div>
                    )}
                    
                    {/* Text type */}
                    {item.tipo === 'texto' && (
                      <textarea value={item.valor || ''} onChange={(e) => updateChecklistItem(item.id, 'valor', e.target.value)} className="input-industrial w-full px-3 py-2 mt-2 text-sm min-h-[60px]" placeholder="Observações..." />
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* Photo capture */}
          <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-400"><Camera size={14} className="inline mr-1" /> Fotos ({photos.length})</p>
              <button onClick={() => setShowCamera(true)} className="btn-secondary text-sm flex items-center gap-1" data-testid="ronda-camera-btn">
                <Camera size={16} /> Tirar Foto
              </button>
            </div>
            {photos.length > 0 && (
              <div className="flex gap-2 flex-wrap">
                {photos.map((p, i) => (
                  <div key={i} className="w-16 h-16 rounded-lg overflow-hidden bg-slate-800">
                    <img src={URL.createObjectURL(p)} alt="" className="w-full h-full object-cover" />
                  </div>
                ))}
              </div>
            )}
          </div>
          
          {/* Submit */}
          <button onClick={submitInspecao} disabled={submitting} className="btn-primary w-full py-4 text-lg font-semibold flex items-center justify-center gap-2" data-testid="ronda-submit-btn">
            {submitting ? <><RefreshCw size={20} className="animate-spin" /> Salvando...</> : <><CheckCircle size={20} /> Concluir Inspeção</>}
          </button>
        </div>
      )}
    </div>
  );
};

// Scanner Page — Mobile-first QR scanner with jsQR fallback
const ScannerPage = () => {
  const [manualCode, setManualCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const scanningRef = useRef(false);
  const navigate = useNavigate();
  
  const resolveScannedValue = async (value) => {
    // Portal URL pattern: /portal/equipamento/{id} or /portal/tecnico/{id}
    const portalMatch = value.match(/\/portal\/equipamento\/([a-f0-9-]+)/i);
    if (portalMatch) { navigate(`/portal/tecnico/${portalMatch[1]}`); return; }
    const ativoMatch = value.match(/\/ativos\/([a-f0-9-]+)/i);
    if (ativoMatch) { navigate(`/portal/tecnico/${ativoMatch[1]}`); return; }
    try {
      const r = await api.get(`/ativos/qr/${encodeURIComponent(value)}`);
      navigate(`/portal/tecnico/${r.data.id}`); return;
    } catch {}
    try {
      const r = await api.get(`/ativos/tag/${value.toUpperCase()}`);
      navigate(`/ativos/${r.data.id}`); return;
    } catch {}
    toast.error('Ativo não encontrado para este código');
  };

  const handleSearch = async () => {
    if (!manualCode.trim()) return;
    setLoading(true);
    try { await resolveScannedValue(manualCode.trim()); }
    finally { setLoading(false); }
  };

  const startCamera = async () => {
    setCameraError('');
    setScanning(true);
    scanningRef.current = true;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      
      // Try native BarcodeDetector first
      if ('BarcodeDetector' in window) {
        const detector = new window.BarcodeDetector({ formats: ['qr_code'] });
        const scanNative = async () => {
          if (!scanningRef.current || !videoRef.current) return;
          try {
            const barcodes = await detector.detect(videoRef.current);
            if (barcodes.length > 0) {
              stopCamera();
              toast.success('QR Code detectado!');
              await resolveScannedValue(barcodes[0].rawValue);
              return;
            }
          } catch {}
          if (scanningRef.current) requestAnimationFrame(scanNative);
        };
        videoRef.current.onloadedmetadata = () => scanNative();
      } else {
        // Fallback: jsQR library
        const jsQR = (await import('jsqr')).default;
        const canvas = canvasRef.current;
        const ctx = canvas?.getContext('2d');
        const scanJsQR = () => {
          if (!scanningRef.current || !videoRef.current || !ctx) return;
          const video = videoRef.current;
          if (video.readyState === video.HAVE_ENOUGH_DATA) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const code = jsQR(imageData.data, imageData.width, imageData.height, { inversionAttempts: 'dontInvert' });
            if (code) {
              stopCamera();
              toast.success('QR Code detectado!');
              resolveScannedValue(code.data);
              return;
            }
          }
          if (scanningRef.current) requestAnimationFrame(scanJsQR);
        };
        setTimeout(scanJsQR, 500);
      }
    } catch (err) {
      setCameraError('Não foi possível acessar a câmera. Verifique as permissões.');
      setScanning(false);
    }
  };

  const stopCamera = () => {
    scanningRef.current = false;
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    setScanning(false);
  };

  useEffect(() => { return () => { scanningRef.current = false; stopCamera(); }; }, []);

  // Auto-start camera on mount for quick field use
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { startCamera(); }, []);
  
  return (
    <div className="space-y-4" data-testid="scanner-page">
      <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
        <QrCode size={28} className="text-brand" /> Identificar Ativo
      </h1>
      
      {scanning ? (
        <div className="glass-card p-3 space-y-3">
          <div className="relative rounded-xl overflow-hidden bg-black aspect-[4/3]">
            <video ref={videoRef} className="w-full h-full object-cover" playsInline muted />
            <canvas ref={canvasRef} className="hidden" />
            {/* Scan overlay */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="w-52 h-52 relative">
                <div className="absolute top-0 left-0 w-8 h-8 border-t-3 border-l-3 border-brand rounded-tl-lg" />
                <div className="absolute top-0 right-0 w-8 h-8 border-t-3 border-r-3 border-brand rounded-tr-lg" />
                <div className="absolute bottom-0 left-0 w-8 h-8 border-b-3 border-l-3 border-brand rounded-bl-lg" />
                <div className="absolute bottom-0 right-0 w-8 h-8 border-b-3 border-r-3 border-brand rounded-br-lg" />
                <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-brand animate-pulse" />
              </div>
            </div>
            <div className="absolute bottom-3 left-3 right-3 text-center">
              <p className="text-xs text-white/80 bg-black/50 rounded-full px-3 py-1 inline-block">Aponte para o QR Code do equipamento</p>
            </div>
          </div>
          {cameraError && <p className="text-sm text-amber-400 text-center">{cameraError}</p>}
          <button onClick={stopCamera} className="btn-secondary w-full flex items-center justify-center gap-2" data-testid="stop-camera-btn">
            <X size={20} /> Fechar Câmera
          </button>
        </div>
      ) : (
        <div className="glass-card p-8 flex flex-col items-center justify-center gap-4">
          <div className="w-20 h-20 rounded-full bg-brand-10 flex items-center justify-center">
            <Camera size={40} className="text-brand" />
          </div>
          <p className="text-sm text-slate-500">Câmera fechada</p>
          <button onClick={startCamera} className="btn-primary flex items-center gap-2" data-testid="open-camera-btn">
            <Camera size={20} /> Abrir Câmera
          </button>
        </div>
      )}
      
      <div className="flex items-center gap-4">
        <div className="flex-1 h-px bg-slate-800" />
        <span className="text-slate-500 text-sm">ou buscar por TAG</span>
        <div className="flex-1 h-px bg-slate-800" />
      </div>
      
      <div className="glass-card p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={manualCode}
            onChange={(e) => setManualCode(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Ex: BOM-001"
            className="input-industrial flex-1 px-4 font-mono text-lg"
            data-testid="manual-search-input"
          />
          <button onClick={handleSearch} disabled={loading} className="btn-primary px-6" data-testid="manual-search-btn">
            {loading ? <RefreshCw size={20} className="animate-spin" /> : <Search size={20} />}
          </button>
        </div>
      </div>
    </div>
  );
};


// ============== PHOTO UPLOADER COMPONENT ==============

const PhotoUploader = ({ entityType, entityId, categoria = 'foto', label = 'Fotos', required = false, onPhotoCountChange }) => {
  const [photos, setPhotos] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [fullscreenImg, setFullscreenImg] = useState(null);
  const fileInputRef = useRef(null);

  const fetchPhotos = async () => {
    if (!entityId) return;
    try {
      const res = await api.get(`/attachments/${entityType}/${entityId}`);
      const filtered = categoria ? res.data.filter(a => a.categoria === categoria) : res.data;
      setPhotos(filtered);
      onPhotoCountChange?.(filtered.length);
    } catch (err) { console.error(err); }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchPhotos(); }, [entityId, entityType]);

  const handleUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    setUploading(true);
    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('entity_type', entityType);
        formData.append('entity_id', entityId);
        formData.append('categoria', categoria);
        await api.post('/attachments', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      }
      toast.success(`${files.length} foto(s) enviada(s)`);
      fetchPhotos();
    } catch (e) {
      toast.error('Erro ao enviar foto');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/attachments/${id}`);
      fetchPhotos();
    } catch { toast.error('Erro ao remover'); }
  };

  return (
    <>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-slate-400 flex items-center gap-2">
            <Camera size={16} /> {label} {required && <span className="text-red-400">*</span>}
            {photos.length > 0 && <span className="text-xs text-slate-600">({photos.length})</span>}
          </h4>
        </div>

        {/* Photo Grid */}
        {photos.length > 0 && (
          <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
            {photos.map((p) => (
              <div key={p.id} className="relative group aspect-square rounded-lg overflow-hidden bg-slate-800 border border-slate-700">
                <img
                  src={`${BACKEND_URL}${p.file_url}`}
                  alt={p.filename}
                  className="w-full h-full object-cover cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => setFullscreenImg(`${BACKEND_URL}${p.file_url}`)}
                />
                <button
                  onClick={() => handleDelete(p.id)}
                  className="absolute top-1 right-1 p-1 bg-red-500/80 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X size={12} className="text-white" />
                </button>
                <p className="absolute bottom-0 left-0 right-0 bg-black/60 text-[10px] text-slate-300 px-1 py-0.5 truncate">
                  {new Date(p.created_at).toLocaleDateString('pt-BR')}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Upload Button */}
        <label className={`flex items-center justify-center gap-2 p-3 border-2 border-dashed rounded-lg cursor-pointer transition-all ${
          required && photos.length === 0 ? 'border-red-500/50 hover:border-red-400 bg-red-500/5' : 'border-slate-700 hover:border-brand hover:bg-brand-10'
        }`}>
          {uploading ? (
            <><RefreshCw size={18} className="animate-spin text-slate-400" /> <span className="text-sm text-slate-400">Enviando...</span></>
          ) : (
            <><Camera size={18} className="text-slate-500" /> <span className="text-sm text-slate-400">Tirar foto ou selecionar arquivo</span></>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            multiple
            onChange={handleUpload}
            className="hidden"
            disabled={uploading}
          />
        </label>
        {required && photos.length === 0 && (
          <p className="text-xs text-red-400">Foto obrigatória</p>
        )}
      </div>

      {/* Fullscreen Viewer */}
      {fullscreenImg && (
        <div className="fixed inset-0 z-[200] bg-black/95 flex items-center justify-center p-4" onClick={() => setFullscreenImg(null)}>
          <button className="absolute top-4 right-4 p-2 bg-slate-800 rounded-full" onClick={() => setFullscreenImg(null)}>
            <X size={24} className="text-white" />
          </button>
          <img src={fullscreenImg} alt="Fullscreen" className="max-w-full max-h-full object-contain rounded-lg" />
        </div>
      )}
    </>
  );
};

// ============== SOBRESSALENTES PAGE ==============

const CONDICAO_CONFIG = {
  novo: { label: 'Novo', class: 'text-emerald-400 bg-brand-10' },
  reformado: { label: 'Reformado', class: 'text-blue-400 bg-blue-500/10' },
  em_reforma: { label: 'Em Reforma', class: 'text-amber-400 bg-amber-500/10' },
  reservado: { label: 'Reservado', class: 'text-purple-400 bg-purple-500/10' },
  instalado: { label: 'Instalado', class: 'text-cyan-400 bg-cyan-500/10' },
  descartado: { label: 'Descartado', class: 'text-red-400 bg-red-500/10' },
};
const ORIGEM_OPTIONS = [
  { value: 'compra_nova', label: 'Compra Nova' },
  { value: 'reforma_interna', label: 'Reforma Interna' },
  { value: 'reforma_externa', label: 'Reforma Externa' },
  { value: 'transferencia', label: 'Transferência' },
];

const SobressalentesPage = () => {
  const [spares, setSpares] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const [form, setForm] = useState({ descricao: '', modelo: '', fabricante: '', status: 'estoque', localizacao: '', custo: '', origem: '', condicoes: { novo: 0, reformado: 0, em_reforma: 0, reservado: 0, instalado: 0, descartado: 0 } });
  const [saving, setSaving] = useState(false);
  const [showReformaModal, setShowReformaModal] = useState(null);
  const [reformaForm, setReformaForm] = useState({ empresa_reparadora: '', data_envio: '', data_retorno: '', observacao: '', valor: '' });
  const [reformas, setReformas] = useState([]);
  const { user } = useAuth();

  const fetchData = async () => {
    try {
      const res = await api.get('/sobressalentes');
      setSpares(res.data);
    } catch (e) { toast.error('Erro ao carregar sobressalentes'); }
    finally { setLoading(false); }
  };
  useEffect(() => { fetchData(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.descricao) { toast.error('Descrição é obrigatória'); return; }
    setSaving(true);
    try {
      const payload = { ...form, custo: form.custo ? parseFloat(form.custo) : null };
      if (editItem) {
        await api.put(`/sobressalentes/${editItem.id}`, payload);
        toast.success('Sobressalente atualizado!');
      } else {
        await api.post('/sobressalentes', payload);
        toast.success('Sobressalente criado!');
      }
      setShowModal(false);
      setEditItem(null);
      setForm({ descricao: '', modelo: '', fabricante: '', status: 'estoque', localizacao: '', custo: '', origem: '', condicoes: { novo: 0, reformado: 0, em_reforma: 0, reservado: 0, instalado: 0, descartado: 0 } });
      fetchData();
    } catch (e) { toast.error(normalizeError(e)); }
    finally { setSaving(false); }
  };

  const handleExport = async (fmt) => {
    try {
      const res = await api.get(`/export/sobressalentes?format=${fmt}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `sobressalentes_export.${fmt === 'excel' ? 'xlsx' : 'pdf'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Exportado com sucesso!');
    } catch { toast.error('Erro ao exportar'); }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/sobressalentes/${deleteItem.id}`);
      toast.success('Sobressalente excluído!');
      setDeleteItem(null);
      fetchData();
    } catch (error) { toast.error(normalizeError(error)); }
  };

  const handleEdit = (sp) => {
    setEditItem(sp);
    setForm({
      descricao: sp.descricao || '', modelo: sp.modelo || '', fabricante: sp.fabricante || '',
      status: sp.status || 'estoque', localizacao: sp.localizacao || '', custo: sp.custo ? String(sp.custo) : '',
      origem: sp.origem || '',
      condicoes: sp.condicoes || { novo: 0, reformado: 0, em_reforma: 0, reservado: 0, instalado: 0, descartado: 0 }
    });
    setShowModal(true);
  };

  const handleOpenReformas = async (sp) => {
    setShowReformaModal(sp);
    setReformaForm({ empresa_reparadora: '', data_envio: '', data_retorno: '', observacao: '', valor: '' });
    try {
      const res = await api.get(`/sobressalentes/${sp.id}/reformas`);
      setReformas(res.data);
    } catch { setReformas([]); }
  };

  const handleAddReforma = async () => {
    if (!reformaForm.empresa_reparadora) { toast.error('Empresa reparadora é obrigatória'); return; }
    try {
      await api.post(`/sobressalentes/${showReformaModal.id}/reformas`, {
        ...reformaForm, valor: reformaForm.valor ? parseFloat(reformaForm.valor) : null
      });
      toast.success('Reforma registrada!');
      setReformaForm({ empresa_reparadora: '', data_envio: '', data_retorno: '', observacao: '', valor: '' });
      const res = await api.get(`/sobressalentes/${showReformaModal.id}/reformas`);
      setReformas(res.data);
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const updateCondicao = (key, val) => {
    const v = Math.max(0, parseInt(val) || 0);
    setForm(prev => ({ ...prev, condicoes: { ...prev.condicoes, [key]: v } }));
  };

  const totalCondicoes = Object.values(form.condicoes || {}).reduce((s, v) => s + (v || 0), 0);

  const filtered = search ? spares.filter(s => s.descricao?.toLowerCase().includes(search.toLowerCase()) || s.tag?.toLowerCase().includes(search.toLowerCase())) : spares;

  const statusConfig = {
    estoque: { class: 'bg-brand-10 text-emerald-400', label: 'Em Estoque' },
    em_uso: { class: 'bg-blue-500/10 text-blue-400', label: 'Em Uso' },
    em_reforma: { class: 'bg-amber-500/10 text-amber-400', label: 'Em Reforma' },
    descartado: { class: 'bg-red-500/10 text-red-400', label: 'Descartado' },
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Sobressalentes</h1>
        <div className="flex gap-2">
          <button onClick={() => handleExport('excel')} className="btn-secondary flex items-center gap-2 text-sm" data-testid="spare-export-excel"><Download size={16} /> Excel</button>
          <button onClick={() => handleExport('pdf')} className="btn-secondary flex items-center gap-2 text-sm" data-testid="spare-export-pdf"><FileText size={16} /> PDF</button>
          {['admin','master','pcm'].includes(user?.role) && (
            <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2" data-testid="add-spare-btn"><Plus size={20} /> Novo</button>
          )}
        </div>
      </div>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar sobressalente..." className="input-industrial w-full pl-10 pr-4" />
      </div>
      {loading ? <Loading rows={5} /> : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((sp) => {
            const conds = sp.condicoes || {};
            const qtTotal = sp.quantidade_total || Object.values(conds).reduce((s, v) => s + (v || 0), 0);
            const activeConditions = Object.entries(conds).filter(([, v]) => v > 0);
            const origemLabel = ORIGEM_OPTIONS.find(o => o.value === sp.origem)?.label;
            return (
            <div key={sp.id} className="glass-card p-4 hover:border-slate-600 transition-all" data-testid={`spare-card-${sp.id}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="font-mono text-brand text-sm">{sp.tag || sp.codigo}</span>
                    {origemLabel && <span className="text-xs px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">{origemLabel}</span>}
                    {qtTotal > 0 && <span className="text-xs font-semibold text-slate-200 bg-slate-700 px-1.5 py-0.5 rounded">Qtd: {qtTotal}</span>}
                  </div>
                  <p className="text-slate-100 font-medium">{sp.descricao}</p>
                  <p className="text-xs text-slate-500">{[sp.fabricante, sp.modelo, sp.localizacao].filter(Boolean).join(' · ')}</p>
                  {sp.ativo_vinculado && <p className="text-xs text-blue-400 mt-0.5">Ativo: {sp.ativo_vinculado.tag} - {sp.ativo_vinculado.nome}</p>}
                  {/* Condições breakdown */}
                  {activeConditions.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {activeConditions.map(([k, v]) => (
                        <span key={k} className={`text-xs px-1.5 py-0.5 rounded ${CONDICAO_CONFIG[k]?.class || 'text-slate-400 bg-slate-800'}`}>
                          {CONDICAO_CONFIG[k]?.label || k}: {v}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex flex-col items-end gap-1">
                  {sp.custo > 0 && <p className="text-lg font-bold text-slate-200">R$ {sp.custo.toFixed(2)}</p>}
                  {['admin','master','pcm'].includes(user?.role) && (
                    <div className="flex items-center gap-1">
                      <button onClick={() => handleOpenReformas(sp)} className="p-2 hover:bg-amber-500/10 rounded-lg" title="Reformas" data-testid={`reforma-spare-${sp.id}`}><Wrench size={15} className="text-amber-400" /></button>
                      <button onClick={() => handleEdit(sp)} className="p-2 hover:bg-slate-700 rounded-lg" title="Editar" data-testid={`edit-spare-${sp.id}`}><Edit3 size={15} className="text-blue-400" /></button>
                      <button onClick={() => setDeleteItem(sp)} className="p-2 hover:bg-red-500/10 rounded-lg" title="Excluir" data-testid={`delete-spare-${sp.id}`}><Trash2 size={15} className="text-red-400" /></button>
                    </div>
                  )}
                </div>
              </div>
            </div>
            );
          })}
        </div>
      ) : <EmptyState icon={Cog} title="Nenhum sobressalente" description="Cadastre sobressalentes." />}

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditItem(null); }} title={editItem ? "Editar Sobressalente" : "Novo Sobressalente"} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormInput label="Descrição" required>
            <input value={form.descricao} onChange={(e) => setForm({...form, descricao: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: Redutor Falk 500" required />
          </FormInput>
          <div className="grid grid-cols-2 gap-4">
            <FormInput label="Fabricante"><input value={form.fabricante} onChange={(e) => setForm({...form, fabricante: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
            <FormInput label="Modelo"><input value={form.modelo} onChange={(e) => setForm({...form, modelo: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
            <FormInput label="Localização"><input value={form.localizacao} onChange={(e) => setForm({...form, localizacao: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: Almox A-01" /></FormInput>
            <FormInput label="Custo (R$)"><input type="number" step="0.01" value={form.custo} onChange={(e) => setForm({...form, custo: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
          </div>
          <FormInput label="Origem">
            <select value={form.origem} onChange={(e) => setForm({...form, origem: e.target.value})} className="input-industrial w-full px-4">
              <option value="">Selecione...</option>
              {ORIGEM_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </FormInput>
          {/* Condições por quantidade */}
          <div className="border-t border-slate-800 pt-3">
            <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider mb-2">Quantidade por Condição <span className="text-slate-300 normal-case">(Total: {totalCondicoes})</span></p>
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(CONDICAO_CONFIG).map(([key, cfg]) => (
                <div key={key} className="flex items-center gap-2">
                  <span className={`text-xs w-20 truncate ${cfg.class.split(' ')[0]}`}>{cfg.label}</span>
                  <input type="number" min="0" value={form.condicoes?.[key] || 0} onChange={(e) => updateCondicao(key, e.target.value)}
                    className="input-industrial w-16 px-2 text-center text-sm" data-testid={`condicao-${key}`} />
                </div>
              ))}
            </div>
          </div>
          <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Salvando...' : 'Salvar'}</button>
          </div>
        </form>
      </Modal>

      {/* Modal Histórico de Reformas */}
      <Modal isOpen={!!showReformaModal} onClose={() => setShowReformaModal(null)} title={`Reformas — ${showReformaModal?.tag || ''}`} size="lg">
        <div className="space-y-4">
          {['admin','master','pcm'].includes(user?.role) && (
            <div className="glass-card p-3 space-y-3">
              <p className="text-xs text-slate-500 uppercase font-semibold">Registrar Reforma</p>
              <div className="grid grid-cols-2 gap-3">
                <FormInput label="Empresa Reparadora" required>
                  <input value={reformaForm.empresa_reparadora} onChange={e => setReformaForm({...reformaForm, empresa_reparadora: e.target.value})} className="input-industrial w-full px-3 text-sm" data-testid="reforma-empresa" />
                </FormInput>
                <FormInput label="Valor (R$)">
                  <input type="number" step="0.01" value={reformaForm.valor} onChange={e => setReformaForm({...reformaForm, valor: e.target.value})} className="input-industrial w-full px-3 text-sm" />
                </FormInput>
                <FormInput label="Data Envio">
                  <input type="date" value={reformaForm.data_envio} onChange={e => setReformaForm({...reformaForm, data_envio: e.target.value})} className="input-industrial w-full px-3 text-sm" />
                </FormInput>
                <FormInput label="Data Retorno">
                  <input type="date" value={reformaForm.data_retorno} onChange={e => setReformaForm({...reformaForm, data_retorno: e.target.value})} className="input-industrial w-full px-3 text-sm" />
                </FormInput>
              </div>
              <FormInput label="Observação">
                <textarea value={reformaForm.observacao} onChange={e => setReformaForm({...reformaForm, observacao: e.target.value})} className="input-industrial w-full px-3 text-sm" rows={2} />
              </FormInput>
              <button onClick={handleAddReforma} className="btn-primary text-sm" data-testid="reforma-submit">Registrar</button>
            </div>
          )}
          {reformas.length > 0 ? (
            <div className="space-y-2">
              {reformas.map(r => (
                <div key={r.id} className="glass-card p-3 text-sm" data-testid={`reforma-item-${r.id}`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-slate-200 font-medium">{r.empresa_reparadora}</p>
                      <div className="flex gap-3 text-xs text-slate-500 mt-0.5">
                        {r.data_envio && <span>Envio: {new Date(r.data_envio + 'T00:00:00').toLocaleDateString('pt-BR')}</span>}
                        {r.data_retorno && <span>Retorno: {new Date(r.data_retorno + 'T00:00:00').toLocaleDateString('pt-BR')}</span>}
                        {r.valor && <span className="text-brand">R$ {r.valor.toFixed(2)}</span>}
                      </div>
                      {r.observacao && <p className="text-xs text-slate-400 mt-1">{r.observacao}</p>}
                      <p className="text-xs text-slate-600 mt-0.5">{r.usuario_nome} · {new Date(r.created_at).toLocaleString('pt-BR')}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : <p className="text-xs text-slate-600 text-center py-4">Nenhuma reforma registrada</p>}
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteItem}
        onClose={() => setDeleteItem(null)}
        onConfirm={handleDelete}
        title="Excluir Sobressalente"
        message={`Tem certeza que deseja excluir "${deleteItem?.tag} - ${deleteItem?.descricao}"?`}
        confirmText="Excluir"
        danger
      />

    </div>
  );
};


// ============== SOLICITAÇÃO DE SERVIÇO PAGE (OPERADOR) ==============

const SolicitacaoServicoPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [ativos, setAtivos] = useState([]);
  const [busca, setBusca] = useState('');
  const [selectedAtivo, setSelectedAtivo] = useState(null);
  const [form, setForm] = useState({ titulo: '', justificativa: '', prioridade: 'media', equipamento_parado: false });
  const [saving, setSaving] = useState(false);
  const [step, setStep] = useState(1); // 1=select ativo, 2=describe problem

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/ativos');
        setAtivos(res.data);
      } catch {}
    })();
  }, []);

  const filteredAtivos = busca.trim()
    ? ativos.filter(a => `${a.tag} ${a.nome}`.toLowerCase().includes(busca.toLowerCase()))
    : ativos.slice(0, 20);

  const handleSubmit = async () => {
    if (!selectedAtivo || !form.titulo.trim()) { toast.error('Preencha o equipamento e o problema'); return; }
    setSaving(true);
    try {
      const payload = {
        ativo_id: selectedAtivo.id,
        titulo: form.titulo.trim(),
        justificativa: form.justificativa.trim(),
        descricao: form.justificativa.trim(),
        prioridade: form.prioridade,
        tipo: 'corretiva',
        origem: 'operador',
        equipamento_parado: form.equipamento_parado,
      };
      const res = await api.post('/ordens-servico', payload);
      toast.success(`Solicitação #${res.data.numero} criada com sucesso!`);
      navigate('/');
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setSaving(false); }
  };

  return (
    <div className="space-y-4 animate-fadeInUp max-w-2xl mx-auto" data-testid="solicitar-servico-page">
      <div className="flex items-center gap-3">
        <button onClick={() => step === 1 ? navigate(-1) : setStep(1)} className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg">
          <ArrowLeft size={18} className="text-slate-400" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-slate-100">Nova Solicitação de Serviço</h1>
          <p className="text-xs text-slate-500">Descreva o problema encontrado</p>
        </div>
      </div>

      {/* Step indicator */}
      <div className="flex gap-2">
        <div className={`flex-1 h-1 rounded-full ${step >= 1 ? 'bg-brand' : 'bg-slate-800'}`} />
        <div className={`flex-1 h-1 rounded-full ${step >= 2 ? 'bg-brand' : 'bg-slate-800'}`} />
      </div>

      {step === 1 && (
        <div className="space-y-3" data-testid="solicitar-step1">
          <p className="text-sm text-slate-300 font-medium">Qual equipamento precisa de serviço?</p>
          <input value={busca} onChange={e => setBusca(e.target.value)} className="input-industrial w-full px-4"
            placeholder="Buscar por TAG ou nome..." data-testid="solicitar-busca-ativo" autoFocus />
          <div className="space-y-2 max-h-[50vh] overflow-y-auto">
            {filteredAtivos.map(a => (
              <button key={a.id} onClick={() => { setSelectedAtivo(a); setStep(2); }}
                className={`w-full glass-card p-4 text-left flex items-center gap-3 hover:border-brand transition-all ${selectedAtivo?.id === a.id ? 'border-brand bg-brand-10' : ''}`}
                data-testid={`solicitar-ativo-${a.id}`}>
                <div className="w-10 h-10 rounded-lg bg-brand-10 flex items-center justify-center shrink-0">
                  <Box size={18} className="text-brand" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-mono text-brand font-bold">{a.tag}</p>
                  <p className="text-sm text-slate-200 truncate">{a.nome}</p>
                  <p className="text-[10px] text-slate-500">{a.tipo_equipamento || ''}</p>
                </div>
                <ChevronRight size={16} className="text-slate-600 ml-auto shrink-0" />
              </button>
            ))}
          </div>
        </div>
      )}

      {step === 2 && selectedAtivo && (
        <div className="space-y-4" data-testid="solicitar-step2">
          {/* Selected ativo summary */}
          <div className="glass-card p-3 flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-brand-10 flex items-center justify-center shrink-0">
              <Box size={16} className="text-brand" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-mono text-brand font-bold">{selectedAtivo.tag}</p>
              <p className="text-xs text-slate-400">{selectedAtivo.nome}</p>
            </div>
            <button onClick={() => setStep(1)} className="text-xs text-brand ml-auto">Trocar</button>
          </div>

          <FormInput label="Qual o problema? *">
            <input value={form.titulo} onChange={e => setForm({...form, titulo: e.target.value})}
              className="input-industrial w-full px-4" placeholder="Ex: Vazamento na bomba, Iluminação queimada..."
              data-testid="solicitar-titulo" autoFocus />
          </FormInput>

          <FormInput label="Justificativa / Detalhes">
            <textarea value={form.justificativa} onChange={e => setForm({...form, justificativa: e.target.value})}
              className="input-industrial w-full px-4 py-3 min-h-[100px] resize-y"
              placeholder="Descreva o que você observou. Quando começou? Há risco de segurança? O equipamento parou?"
              data-testid="solicitar-justificativa" />
          </FormInput>

          <div className="grid grid-cols-2 gap-3">
            <FormInput label="Urgência">
              <select value={form.prioridade} onChange={e => setForm({...form, prioridade: e.target.value})}
                className="input-industrial w-full px-4" data-testid="solicitar-prioridade">
                <option value="baixa">Baixa — pode esperar</option>
                <option value="media">Média — próximos dias</option>
                <option value="alta">Alta — precisa logo</option>
                <option value="critica">Urgente — agora!</option>
              </select>
            </FormInput>
            <FormInput label="Equipamento Parado?">
              <div className="flex items-center gap-3 h-12">
                <button onClick={() => setForm({...form, equipamento_parado: true})}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-all ${form.equipamento_parado ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-slate-800 text-slate-400 border-slate-700'}`}
                  data-testid="solicitar-parado-sim">Sim</button>
                <button onClick={() => setForm({...form, equipamento_parado: false})}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-all ${!form.equipamento_parado ? 'bg-brand-20 text-brand border-brand-30' : 'bg-slate-800 text-slate-400 border-slate-700'}`}
                  data-testid="solicitar-parado-nao">Não</button>
              </div>
            </FormInput>
          </div>

          <button onClick={handleSubmit} disabled={saving || !form.titulo.trim()}
            className="w-full btn-primary py-4 text-lg font-bold flex items-center justify-center gap-2"
            data-testid="solicitar-enviar">
            <Send size={20} /> {saving ? 'Enviando...' : 'Enviar Solicitação'}
          </button>
        </div>
      )}
    </div>
  );
};


// ============== ANOMALIAS PAGE ==============

const ANOMALIA_STATUS = {
  aberta: { label: 'Aberta', color: 'text-red-400 bg-red-500/10' },
  em_analise: { label: 'Em Análise', color: 'text-amber-400 bg-amber-500/10' },
  os_gerada: { label: 'OS Gerada', color: 'text-blue-400 bg-blue-500/10' },
  aguardando_execucao: { label: 'Aguardando Execução', color: 'text-purple-400 bg-purple-500/10' },
  resolvida: { label: 'Resolvida', color: 'text-emerald-400 bg-brand-10' },
  encerrada: { label: 'Encerrada', color: 'text-slate-400 bg-slate-500/10' },
};

const AnomaliasPage = () => {
  const [anomalias, setAnomalias] = useState([]);
  const [ativos, setAtivos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ ativo_id: '', descricao: '', severidade: 'media', gerar_os: true });
  const [saving, setSaving] = useState(false);
  const [selected, setSelected] = useState(null); // anomalia detail
  const [editMode, setEditMode] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [comment, setComment] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const navigate = useNavigate();
  const { user } = useAuth();

  const fetchData = async () => {
    try {
      const [anomRes, ativosRes] = await Promise.all([api.get('/anomalias'), api.get('/ativos')]);
      setAnomalias(anomRes.data);
      setAtivos(ativosRes.data);
    } catch { toast.error('Erro ao carregar'); }
    finally { setLoading(false); }
  };
  useEffect(() => { fetchData(); }, []);

  const fetchDetail = async (id) => {
    try {
      const res = await api.get(`/anomalias/${id}`);
      setSelected(res.data);
    } catch { toast.error('Erro ao carregar detalhe'); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.ativo_id || !form.descricao) { toast.error('Preencha ativo e descrição'); return; }
    setSaving(true);
    try {
      const res = await api.post('/anomalias', form);
      toast.success(`Anomalia criada!${res.data.os_gerada_id ? ' OS gerada automaticamente.' : ''}`);
      setShowModal(false);
      setForm({ ativo_id: '', descricao: '', severidade: 'media', gerar_os: true });
      fetchData();
    } catch (e) { toast.error(normalizeError(e)); }
    finally { setSaving(false); }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await api.post(`/anomalias/${selected.id}/status`, { status: newStatus });
      toast.success(`Status alterado para ${ANOMALIA_STATUS[newStatus]?.label}`);
      fetchDetail(selected.id);
      fetchData();
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const handleEdit = async () => {
    try {
      await api.put(`/anomalias/${selected.id}`, editForm);
      toast.success('Anomalia atualizada!');
      setEditMode(false);
      fetchDetail(selected.id);
      fetchData();
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const handleComment = async () => {
    if (!comment.trim()) return;
    try {
      await api.post(`/anomalias/${selected.id}/comentarios`, { texto: comment });
      setComment('');
      fetchDetail(selected.id);
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const getNextStatuses = (current) => {
    const map = {
      aberta: ['em_analise'],
      em_analise: ['os_gerada', 'resolvida'],
      os_gerada: ['aguardando_execucao', 'resolvida'],
      aguardando_execucao: ['resolvida'],
      resolvida: ['encerrada'],
    };
    return map[current] || [];
  };

  const handleDelete = async () => {
    if (!window.confirm('Excluir esta anomalia? Esta ação não pode ser desfeita.')) return;
    try {
      await api.delete(`/anomalias/${selected.id}`);
      toast.success('Anomalia excluída');
      setSelected(null);
      fetchData();
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const handleReopen = async () => {
    try {
      await api.post(`/anomalias/${selected.id}/status`, { status: 'aberta' });
      toast.success('Anomalia reaberta');
      fetchDetail(selected.id);
      fetchData();
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const filtered = anomalias.filter(a => !filterStatus || a.status === filterStatus);

  // DETAIL VIEW
  if (selected) return (
    <div className="space-y-4" data-testid="anomalia-detail">
      <div className="flex items-center gap-3">
        <button onClick={() => setSelected(null)} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg"><ArrowLeft size={20} className="text-slate-400" /></button>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={`text-xs px-2 py-0.5 rounded ${ANOMALIA_STATUS[selected.status]?.color || ''}`}>{ANOMALIA_STATUS[selected.status]?.label}</span>
            <PriorityBadge priority={selected.severidade} />
          </div>
          <h1 className="text-lg font-bold text-slate-100 mt-1">Anomalia</h1>
        </div>
        {!editMode && selected.status !== 'encerrada' && user?.role !== 'tecnico' && (
          <button onClick={() => { setEditMode(true); setEditForm({ descricao: selected.descricao, severidade: selected.severidade }); }} className="btn-secondary text-sm flex items-center gap-1" data-testid="edit-anomalia"><Edit size={14} /> Editar</button>
        )}
      </div>

      {/* Ativo */}
      {selected.ativo && (
        <div className="glass-card p-4 cursor-pointer hover:border-slate-600" onClick={() => navigate(`/ativos/${selected.ativo_id}`)}>
          {selected.ativo.sector && <p className="text-xs text-slate-500 uppercase">{selected.ativo.sector?.nome}</p>}
          <span className="font-mono text-brand">{selected.ativo.tag}</span>
          <span className="text-slate-300 ml-2">{selected.ativo.nome}</span>
        </div>
      )}

      {/* Descrição (edit or view) */}
      {editMode ? (
        <div className="glass-card p-4 space-y-3">
          <FormInput label="Descrição"><textarea value={editForm.descricao} onChange={e => setEditForm({...editForm, descricao: e.target.value})} className="input-industrial w-full px-4 py-3 min-h-[80px]" /></FormInput>
          <FormInput label="Severidade"><Select value={editForm.severidade} onChange={v => setEditForm({...editForm, severidade: v})} options={[{value:'baixa',label:'Baixa'},{value:'media',label:'Média'},{value:'alta',label:'Alta'},{value:'critica',label:'Crítica'}]} /></FormInput>
          <div className="flex gap-2 justify-end"><button onClick={() => setEditMode(false)} className="btn-secondary text-sm">Cancelar</button><button onClick={handleEdit} className="btn-primary text-sm" data-testid="save-anomalia-edit">Salvar</button></div>
        </div>
      ) : (
        <div className="glass-card p-4">
          <p className="text-slate-200 whitespace-pre-wrap">{selected.descricao}</p>
          <p className="text-xs text-slate-500 mt-2">{new Date(selected.created_at).toLocaleDateString('pt-BR', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' })}</p>
          {selected.data_encerramento && <p className="text-xs text-slate-500">Encerrada em: {new Date(selected.data_encerramento).toLocaleDateString('pt-BR')}</p>}
        </div>
      )}

      {/* Status Actions */}
      {selected.status !== 'encerrada' && (
        <div className="flex gap-2 flex-wrap" data-testid="anomalia-actions">
          {getNextStatuses(selected.status).map(ns => (
            <button key={ns} onClick={() => handleStatusChange(ns)} className="btn-primary text-sm flex items-center gap-1" data-testid={`anomalia-status-${ns}`}>
              {ANOMALIA_STATUS[ns]?.label}
            </button>
          ))}
          {user?.role !== 'tecnico' && (
            <button onClick={() => handleStatusChange('encerrada')} className="btn-secondary text-sm flex items-center gap-1 border-slate-500/30" data-testid="anomalia-encerrar">Encerrar</button>
          )}
        </div>
      )}
      {selected.status === 'encerrada' && user?.role !== 'tecnico' && (
        <div className="flex gap-2" data-testid="anomalia-actions-closed">
          <button onClick={handleReopen} className="btn-primary text-sm flex items-center gap-1" data-testid="anomalia-reabrir">
            <RefreshCw size={14} /> Reabrir Anomalia
          </button>
        </div>
      )}

      {/* Excluir (admin/supervisor) */}
      {user?.role !== 'tecnico' && (
        <button onClick={handleDelete} className="text-xs text-red-400 hover:text-red-300 mt-2" data-testid="anomalia-excluir">
          <Trash2 size={12} className="inline mr-1" /> Excluir anomalia
        </button>
      )}

      {/* OS Gerada */}
      {selected.os_gerada_id && (
        <div className="glass-card p-3 border-blue-500/30 cursor-pointer" onClick={() => navigate(`/os/${selected.os_gerada_id}`)}>
          <span className="text-xs text-blue-400">OS Gerada</span> <ChevronRight size={14} className="inline text-slate-500" />
        </div>
      )}

      {/* Comentários */}
      <div className="glass-card p-4 space-y-3">
        <h3 className="text-sm font-semibold text-slate-400">Comentários</h3>
        {selected.comentarios?.length > 0 ? selected.comentarios.map(c => (
          <div key={c.id} className="bg-slate-800/50 rounded-lg p-3">
            <p className="text-sm text-slate-200">{c.texto}</p>
            <p className="text-xs text-slate-500 mt-1">{c.usuario_nome || 'Usuário'} • {new Date(c.created_at).toLocaleDateString('pt-BR', {day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})}</p>
          </div>
        )) : <p className="text-xs text-slate-600">Nenhum comentário</p>}
        {selected.status !== 'encerrada' && (
          <div className="flex gap-2">
            <input value={comment} onChange={e => setComment(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleComment()} className="input-industrial flex-1 px-3 text-sm" placeholder="Adicionar comentário..." data-testid="anomalia-comment-input" />
            <button onClick={handleComment} className="btn-primary text-sm px-3" data-testid="anomalia-comment-send">Enviar</button>
          </div>
        )}
      </div>

      {/* Histórico */}
      {selected.historico?.length > 0 && (
        <div className="glass-card p-4 space-y-2">
          <h3 className="text-sm font-semibold text-slate-400">Histórico</h3>
          {selected.historico.map(h => (
            <div key={h.id} className="flex items-center gap-2 text-xs text-slate-500 py-1 border-b border-slate-800/30">
              <Clock size={12} /> <span>{h.descricao}</span> <span className="ml-auto">{new Date(h.created_at).toLocaleDateString('pt-BR', {day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})}</span>
            </div>
          ))}
        </div>
      )}

      <PhotoUploader entityType="anomaly" entityId={selected.id} label="Fotos do Problema" />
    </div>
  );

  // LIST VIEW
  return (
    <div className="space-y-4" data-testid="anomalias-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Anomalias</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2" data-testid="add-anomalia-btn"><Plus size={20} /> Reportar Anomalia</button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        <button onClick={() => setFilterStatus('')} className={`px-3 py-1.5 rounded-lg text-xs border ${!filterStatus ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400' : 'border-slate-700 text-slate-400'}`}>Todas ({anomalias.length})</button>
        {Object.entries(ANOMALIA_STATUS).map(([k, v]) => {
          const count = anomalias.filter(a => a.status === k).length;
          return count > 0 ? (
            <button key={k} onClick={() => setFilterStatus(k)} className={`px-3 py-1.5 rounded-lg text-xs border ${filterStatus === k ? `${v.color} border-current` : 'border-slate-700 text-slate-400'}`}>{v.label} ({count})</button>
          ) : null;
        })}
      </div>

      {loading ? <Loading rows={5} /> : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((a) => (
            <div key={a.id} className="glass-card p-4 cursor-pointer hover:border-slate-600 transition-all" onClick={() => fetchDetail(a.id)} data-testid={`anomalia-card-${a.id}`}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  {a.ativo && (
                    <div className="mb-1">
                      {a.ativo.sector && <span className="text-[10px] text-slate-600 uppercase">{a.ativo.sector?.nome} • </span>}
                      <span className="font-mono text-brand text-sm">{a.ativo.tag}</span>
                      <span className="text-slate-400 text-xs ml-1">{a.ativo.nome}</span>
                    </div>
                  )}
                  <p className="text-slate-100 text-sm line-clamp-1">{a.descricao}</p>
                  <p className="text-xs text-slate-500 mt-1">{new Date(a.created_at).toLocaleDateString('pt-BR')}</p>
                </div>
                <div className="flex items-center gap-2 ml-3">
                  <span className={`text-xs px-2 py-0.5 rounded whitespace-nowrap ${ANOMALIA_STATUS[a.status]?.color || ''}`}>{ANOMALIA_STATUS[a.status]?.label || a.status}</span>
                  <PriorityBadge priority={a.severidade} />
                  <ChevronRight className="text-slate-600" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : <EmptyState icon={AlertTriangle} title="Nenhuma anomalia" description="Reporte anomalias detectadas nos equipamentos." action={() => setShowModal(true)} actionLabel="Reportar" />}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Reportar Anomalia" size="md">
        <form onSubmit={handleCreate} className="space-y-4">
          <FormInput label="Equipamento" required>
            <Select value={form.ativo_id} onChange={(v) => setForm({...form, ativo_id: v})} options={ativos.map(a => ({value: a.id, label: `${a.sector?.nome || ''} • ${a.tag} - ${a.nome}`}))} placeholder="Selecione..." />
          </FormInput>
          <FormInput label="Descrição da Anomalia" required>
            <textarea value={form.descricao} onChange={(e) => setForm({...form, descricao: e.target.value})} className="input-industrial w-full px-4 py-3 min-h-[100px]" placeholder="Descreva o problema encontrado..." required />
          </FormInput>
          <FormInput label="Severidade">
            <Select value={form.severidade} onChange={(v) => setForm({...form, severidade: v})} options={[{value:'baixa',label:'Baixa'},{value:'media',label:'Média'},{value:'alta',label:'Alta'},{value:'critica',label:'Crítica'}]} />
          </FormInput>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" checked={form.gerar_os} onChange={(e) => setForm({...form, gerar_os: e.target.checked})} className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-brand" />
            <span className="text-slate-300">Gerar OS automaticamente</span>
          </label>
          <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary" data-testid="submit-anomalia">{saving ? 'Criando...' : 'Reportar'}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

// ============== ASSISTENTE IA PAGE ==============

const AssistentePage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [ativoId, setAtivoId] = useState('');
  const [ativos, setAtivos] = useState([]);
  const [manuaisDisponiveis, setManuaisDisponiveis] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const fetchData = async () => {
      try { 
        const res = await api.get('/ativos'); 
        setAtivos(res.data);
        // Collect all manuals
        const manuaisPromises = res.data.map(a => api.get(`/ativos/${a.id}/manuais`).catch(() => ({ data: [] })));
        const manuaisResults = await Promise.all(manuaisPromises);
        const allManuais = [];
        manuaisResults.forEach((m, idx) => {
          m.data.forEach(manual => allManuais.push({ ...manual, ativo_tag: res.data[idx].tag, ativo_nome: res.data[idx].nome }));
        });
        setManuaisDisponiveis(allManuais);
      } catch (err) { console.error(err); }
    };
    fetchData();
  }, []);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);
    try {
      const res = await api.post('/assistente/chat', { message: userMsg, ativo_id: ativoId || null, session_id: sessionId || null });
      setSessionId(res.data.session_id);
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Erro ao processar. Tente novamente.' }]);
    } finally { setLoading(false); }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Assistente Técnico IA</h1>
          <p className="text-sm text-slate-500">Tire dúvidas sobre equipamentos e manutenção</p>
        </div>
        <button onClick={() => { setMessages([]); setSessionId(''); }} className="btn-secondary flex items-center gap-2"><RefreshCw size={16} /> Nova conversa</button>
      </div>

      <div className="glass-card p-3 mb-4">
        <FormInput label="Contexto do Equipamento (opcional)">
          <Select value={ativoId} onChange={(v) => setAtivoId(v)} options={[{value:'', label:'Geral (todos os manuais)'}, ...ativos.map(a => ({value: a.id, label: `${a.tag} - ${a.nome}`}))]} />
        </FormInput>
        {manuaisDisponiveis.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-800">
            <p className="text-xs text-slate-500 mb-2 flex items-center gap-1"><FileText size={12} /> {manuaisDisponiveis.length} manual(is) disponível(is) para a IA:</p>
            <div className="flex flex-wrap gap-2">
              {(ativoId ? manuaisDisponiveis.filter(m => m.ativo_id === ativoId) : manuaisDisponiveis).map(m => (
                <span key={m.id} className="text-xs px-2 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded">
                  {m.ativo_tag} - {m.filename}
                </span>
              ))}
              {ativoId && manuaisDisponiveis.filter(m => m.ativo_id === ativoId).length === 0 && (
                <span className="text-xs text-amber-400">Nenhum manual carregado para este ativo. Vá em Ativos > Detalhe > Enviar PDF.</span>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3 mb-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-20 h-20 rounded-full bg-brand-10 flex items-center justify-center mb-4"><Zap size={40} className="text-brand" /></div>
            <h3 className="text-lg text-slate-300 mb-2">Como posso ajudar?</h3>
            <p className="text-slate-500 max-w-md">Faça perguntas sobre manutenção, equipamentos, procedimentos técnicos. Se um manual estiver carregado no ativo, usarei como referência.</p>
            <div className="flex flex-wrap gap-2 mt-4 justify-center">
              {['Como verificar vibração?','Procedimento de lubrificação','Troubleshoot bomba centrífuga'].map(q => (
                <button key={q} onClick={() => { setInput(q); }} className="text-xs px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors">{q}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-3 rounded-xl text-sm whitespace-pre-wrap ${
              msg.role === 'user' ? 'bg-emerald-500/20 text-emerald-100 border border-emerald-500/30' : 'bg-slate-800 text-slate-200 border border-slate-700'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && <div className="flex justify-start"><div className="bg-slate-800 border border-slate-700 p-3 rounded-xl text-sm text-slate-400 animate-pulse">Pensando...</div></div>}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && !loading && handleSend()}
          placeholder="Digite sua dúvida técnica..."
          className="input-industrial flex-1 px-4"
          disabled={loading}
          data-testid="ai-chat-input"
        />
        <button onClick={handleSend} disabled={loading || !input.trim()} className="btn-primary px-6" data-testid="ai-chat-send">
          {loading ? <RefreshCw size={20} className="animate-spin" /> : <Zap size={20} />}
        </button>
      </div>
    </div>
  );
};


// ============== ADMIN TEMPLATES INSPEÇÃO ==============

const FIELD_TYPES = [
  { value: 'boolean', label: 'Conforme / Não Conforme' },
  { value: 'numerico', label: 'Número' },
  { value: 'temperatura', label: 'Temperatura' },
  { value: 'vibracao', label: 'Vibração' },
  { value: 'opcao', label: 'Opção (Bom/Regular/Ruim)' },
  { value: 'texto', label: 'Texto' },
  { value: 'observacao', label: 'Observação' },
];


// ============== PARADAS PROGRAMADAS ==============
const PARADA_TIPOS = [
  { value: 'preventiva', label: 'Preventiva' },
  { value: 'corretiva', label: 'Corretiva' },
  { value: 'grande_parada', label: 'Grande Parada' },
  { value: 'parada_geral', label: 'Parada Geral' },
];

const ParadasPage = () => {
  const [paradas, setParadas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const [detail, setDetail] = useState(null);
  const [areas, setAreas] = useState([]);
  const [osList, setOsList] = useState([]);
  const [tecnicos, setTecnicos] = useState([]);
  const [form, setForm] = useState({ area_id: '', data_inicio: '', data_fim: '', duracao_horas: '', tipo: 'preventiva', responsavel_id: '', descricao: '', observacoes: '', os_vinculadas: [] });
  const { user } = useAuth();

  const fetchData = () => {
    Promise.all([
      api.get('/paradas-programadas'),
      api.get('/sectors'),
      api.get('/ordens-servico'),
      api.get('/users/tecnicos')
    ]).then(([pRes, aRes, osRes, tRes]) => {
      setParadas(pRes.data);
      setAreas(aRes.data);
      setOsList(osRes.data);
      setTecnicos(tRes.data);
    }).catch(() => {}).finally(() => setLoading(false));
  };
  useEffect(() => { fetchData(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.area_id || !form.data_inicio) { toast.error('Área e data são obrigatórios'); return; }
    try {
      const payload = { ...form, duracao_horas: form.duracao_horas ? parseFloat(form.duracao_horas) : null };
      if (editItem) {
        await api.put(`/paradas-programadas/${editItem.id}`, payload);
        toast.success('Parada atualizada!');
      } else {
        await api.post('/paradas-programadas', payload);
        toast.success('Parada criada!');
      }
      setShowModal(false); setEditItem(null);
      setForm({ area_id: '', data_inicio: '', data_fim: '', duracao_horas: '', tipo: 'preventiva', responsavel_id: '', descricao: '', observacoes: '', os_vinculadas: [] });
      fetchData();
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const handleEdit = (p) => {
    setEditItem(p);
    setForm({ area_id: p.area_id || '', data_inicio: p.data_inicio?.split('T')[0] || '', data_fim: p.data_fim?.split('T')[0] || '', duracao_horas: p.duracao_horas || '', tipo: p.tipo || 'preventiva', responsavel_id: p.responsavel_id || '', descricao: p.descricao || '', observacoes: p.observacoes || '', os_vinculadas: p.os_vinculadas || [] });
    setShowModal(true);
  };

  const handleDelete = async () => {
    try { await api.delete(`/paradas-programadas/${deleteItem.id}`); toast.success('Excluída!'); setDeleteItem(null); fetchData(); } catch (e) { toast.error(normalizeError(e)); }
  };

  const openDetail = async (p) => {
    try { const res = await api.get(`/paradas-programadas/${p.id}`); setDetail(res.data); } catch { toast.error('Erro'); }
  };

  const toggleOS = (osId) => {
    setForm(prev => ({
      ...prev,
      os_vinculadas: prev.os_vinculadas.includes(osId) ? prev.os_vinculadas.filter(id => id !== osId) : [...prev.os_vinculadas, osId]
    }));
  };

  if (loading) return <Loading rows={4} />;

  // Detail view
  if (detail) return (
    <div className="space-y-4 pb-24" data-testid="parada-detail">
      <div className="flex items-center gap-3">
        <button onClick={() => setDetail(null)} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg"><ArrowLeft size={20} className="text-slate-400" /></button>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-slate-100">Parada {detail.numero}</h1>
          <p className="text-xs text-slate-500">{detail.area?.nome} — {PARADA_TIPOS.find(t => t.value === detail.tipo)?.label || detail.tipo}</p>
        </div>
        <StatusBadge status={detail.status} />
      </div>
      {/* Info */}
      <div className="glass-card p-4 space-y-2" data-testid="parada-info">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div><span className="text-slate-500">Área:</span> <span className="text-slate-200">{detail.area?.nome}</span></div>
          <div><span className="text-slate-500">Tipo:</span> <span className="text-slate-200 capitalize">{detail.tipo?.replace('_',' ')}</span></div>
          <div><span className="text-slate-500">Data Início:</span> <span className="text-slate-200">{detail.data_inicio ? new Date(detail.data_inicio + 'T00:00:00').toLocaleDateString('pt-BR') : '—'}</span></div>
          <div><span className="text-slate-500">Data Fim:</span> <span className="text-slate-200">{detail.data_fim ? new Date(detail.data_fim + 'T00:00:00').toLocaleDateString('pt-BR') : '—'}</span></div>
          <div><span className="text-slate-500">Duração:</span> <span className="text-brand font-semibold">{detail.duracao_horas ? `${detail.duracao_horas}h` : '—'}</span></div>
          <div><span className="text-slate-500">Responsável:</span> <span className="text-slate-200">{detail.responsavel_nome || '—'}</span></div>
          {detail.criado_por_nome && <div><span className="text-slate-500">Criado por:</span> <span className="text-slate-200">{detail.criado_por_nome}</span></div>}
        </div>
        {detail.descricao && <p className="text-sm text-slate-300 border-t border-slate-800 pt-2">{detail.descricao}</p>}
        {detail.observacoes && <p className="text-xs text-slate-400">{detail.observacoes}</p>}
      </div>
      {/* Indicadores */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="parada-indicadores">
        <div className="glass-card p-3 text-center"><p className="text-2xl font-bold text-blue-400">{detail.os_total}</p><p className="text-xs text-slate-500">OS Vinculadas</p></div>
        <div className="glass-card p-3 text-center"><p className="text-2xl font-bold text-brand">{detail.os_concluidas}</p><p className="text-xs text-slate-500">Concluídas</p></div>
        <div className="glass-card p-3 text-center"><p className="text-2xl font-bold text-amber-400">{detail.os_pendentes}</p><p className="text-xs text-slate-500">Pendentes</p></div>
        <div className="glass-card p-3 text-center"><p className="text-2xl font-bold text-slate-200">{detail.horas_executadas?.toFixed(1) || '0'}h</p><p className="text-xs text-slate-500">Horas Executadas</p></div>
      </div>
      {detail.custo_materiais > 0 && (
        <div className="glass-card p-3 text-center"><p className="text-xl font-bold text-brand">R$ {detail.custo_materiais.toFixed(2)}</p><p className="text-xs text-slate-500">Materiais Consumidos</p></div>
      )}
      {/* OS List */}
      {detail.os_detalhes?.length > 0 && (
        <div className="glass-card p-4" data-testid="parada-os-list">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">OS Vinculadas</h3>
          <div className="space-y-2">
            {detail.os_detalhes.map(os => (
              <div key={os.id} className="flex items-center justify-between bg-slate-800/50 rounded-lg p-3">
                <div><span className="font-mono text-blue-400">#{os.numero}</span> <span className="text-slate-300 text-sm ml-2">{os.titulo}</span></div>
                <div className="flex items-center gap-2">
                  {os.responsavel_nome && <span className="text-xs text-slate-500">{os.responsavel_nome}</span>}
                  <StatusBadge status={os.status} size="sm" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Paradas Programadas</h1>
          <p className="text-sm text-slate-500">{paradas.length} parada(s)</p>
        </div>
        {['admin','master','pcm'].includes(user?.role) && (
          <button onClick={() => { setEditItem(null); setForm({ area_id: '', data_inicio: '', data_fim: '', duracao_horas: '', tipo: 'preventiva', responsavel_id: '', descricao: '', observacoes: '', os_vinculadas: [] }); setShowModal(true); }} className="btn-primary flex items-center gap-2" data-testid="new-parada-btn"><Plus size={20} /> Nova Parada</button>
        )}
      </div>

      {paradas.length > 0 ? (
        <div className="space-y-2">
          {paradas.map(p => (
            <div key={p.id} className="glass-card p-4 cursor-pointer hover:border-slate-600" onClick={() => openDetail(p)} data-testid={`parada-card-${p.id}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-amber-400 font-semibold">{p.numero}</span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 capitalize">{p.tipo?.replace('_',' ')}</span>
                    <StatusBadge status={p.status} size="sm" />
                  </div>
                  <p className="text-slate-200">{p.descricao || p.area?.nome}</p>
                  <div className="flex items-center gap-4 mt-1 text-xs text-slate-500">
                    <span>{p.area?.nome}</span>
                    {p.data_inicio && <span>{new Date(p.data_inicio + 'T00:00:00').toLocaleDateString('pt-BR')}</span>}
                    {p.duracao_horas && <span>{p.duracao_horas}h</span>}
                    {p.responsavel_nome && <span>{p.responsavel_nome}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-3 text-center">
                  <div><p className="text-lg font-bold text-blue-400">{p.os_total}</p><p className="text-xs text-slate-600">OS</p></div>
                  <div><p className="text-lg font-bold text-brand">{p.os_concluidas}</p><p className="text-xs text-slate-600">OK</p></div>
                  {['admin','master','pcm'].includes(user?.role) && (
                    <div className="flex gap-1" onClick={e => e.stopPropagation()}>
                      <button onClick={() => handleEdit(p)} className="p-2 hover:bg-slate-700 rounded-lg" data-testid={`edit-parada-${p.id}`}><Edit3 size={14} className="text-blue-400" /></button>
                      <button onClick={() => setDeleteItem(p)} className="p-2 hover:bg-red-500/10 rounded-lg"><Trash2 size={14} className="text-red-400" /></button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : <EmptyState icon={Calendar} title="Nenhuma parada" description="Crie paradas programadas para planejar manutenção." actionLabel="Nova Parada" onAction={() => setShowModal(true)} />}

      {/* Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditItem(null); }} title={editItem ? "Editar Parada" : "Nova Parada Programada"} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <FormInput label="Área" required>
              <select value={form.area_id} onChange={e => setForm({...form, area_id: e.target.value})} className="input-industrial w-full px-4" required data-testid="parada-area">
                <option value="">Selecione...</option>
                {areas.map(a => <option key={a.id} value={a.id}>{a.nome}</option>)}
              </select>
            </FormInput>
            <FormInput label="Tipo">
              <select value={form.tipo} onChange={e => setForm({...form, tipo: e.target.value})} className="input-industrial w-full px-4" data-testid="parada-tipo">
                {PARADA_TIPOS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </FormInput>
            <FormInput label="Data Início" required>
              <input type="date" value={form.data_inicio} onChange={e => setForm({...form, data_inicio: e.target.value})} className="input-industrial w-full px-4" required />
            </FormInput>
            <FormInput label="Data Fim">
              <input type="date" value={form.data_fim} onChange={e => setForm({...form, data_fim: e.target.value})} className="input-industrial w-full px-4" />
            </FormInput>
            <FormInput label="Duração (horas)">
              <input type="number" step="0.5" value={form.duracao_horas} onChange={e => setForm({...form, duracao_horas: e.target.value})} className="input-industrial w-full px-4" />
            </FormInput>
            <FormInput label="Responsável">
              <select value={form.responsavel_id} onChange={e => setForm({...form, responsavel_id: e.target.value})} className="input-industrial w-full px-4">
                <option value="">Selecione...</option>
                {tecnicos.map(t => <option key={t.id} value={t.id}>{t.nome}</option>)}
              </select>
            </FormInput>
          </div>
          <FormInput label="Descrição">
            <input value={form.descricao} onChange={e => setForm({...form, descricao: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: Parada preventiva semestral" />
          </FormInput>
          <FormInput label="Observações">
            <textarea value={form.observacoes} onChange={e => setForm({...form, observacoes: e.target.value})} className="input-industrial w-full px-4" rows={2} />
          </FormInput>
          {/* OS Vinculadas */}
          <div>
            <p className="text-xs text-slate-500 uppercase font-semibold mb-2">OS Vinculadas ({form.os_vinculadas.length})</p>
            <div className="max-h-40 overflow-y-auto space-y-1 custom-scrollbar">
              {osList.filter(os => !['concluida','cancelada'].includes(os.status)).map(os => (
                <label key={os.id} className="flex items-center gap-2 text-sm p-1.5 rounded hover:bg-slate-800/50 cursor-pointer">
                  <input type="checkbox" checked={form.os_vinculadas.includes(os.id)} onChange={() => toggleOS(os.id)} className="rounded" />
                  <span className="font-mono text-blue-400 text-xs">#{os.numero}</span>
                  <span className="text-slate-300 truncate">{os.titulo}</span>
                  <StatusBadge status={os.status} size="sm" />
                </label>
              ))}
            </div>
          </div>
          <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
            <button type="submit" className="btn-primary">Salvar</button>
          </div>
        </form>
      </Modal>
      <ConfirmDialog isOpen={!!deleteItem} onClose={() => setDeleteItem(null)} onConfirm={handleDelete} title="Excluir Parada" message={`Excluir parada "${deleteItem?.numero}"?`} confirmText="Excluir" danger />
    </div>
  );
};



// ============== ASSISTENTE DE IMPORTAÇÃO DE PLANOS ==============

const PlanImportWizard = ({ onClose, onImported }) => {
  const [step, setStep] = useState(1);
  const [method, setMethod] = useState(null); // 'text', 'file'
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);
  const [parsing, setParsing] = useState(false);
  const [preview, setPreview] = useState(null);
  const [config, setConfig] = useState({ tipo: 'inspecao', disciplina: 'mecanica', ativo_id: '', save_as: 'plano', nome: '' });
  const [ativos, setAtivos] = useState([]);
  const [buscaAtivo, setBuscaAtivo] = useState('');
  const [saving, setSaving] = useState(false);
  const [editIdx, setEditIdx] = useState(null);

  useEffect(() => {
    (async () => { try { const r = await api.get('/ativos'); setAtivos(r.data); } catch {} })();
  }, []);

  const handleParse = async () => {
    setParsing(true);
    try {
      let result;
      if (method === 'text') {
        const res = await api.post('/planos-inspecao/parse-text', { text });
        result = res.data;
      } else if (file) {
        const fd = new FormData();
        fd.append('file', file);
        const res = await api.post('/planos-inspecao/parse-file', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
        result = res.data;
      }
      if (result) {
        setPreview(result);
        setStep(3);
      }
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setParsing(false); }
  };

  const handleSave = async () => {
    if (!preview?.perguntas?.length) { toast.error('Nenhuma pergunta para salvar'); return; }
    if (!config.nome.trim()) { toast.error('Nome do plano é obrigatório'); return; }
    setSaving(true);
    try {
      if (config.save_as === 'template') {
        // Save as master template (Biblioteca)
        const payload = {
          nome: config.nome, tipo_equipamento: '',
          descricao: `Importado via Assistente — ${preview.metadata.total_perguntas} perguntas`,
          itens: preview.perguntas.map((p, i) => ({
            texto: p.texto, tipo_campo: p.tipo_campo || 'conforme_nao_conforme',
            obrigatorio: p.obrigatorio !== false, ordem: i,
            limite_min: p.limite_min || '', limite_max: p.limite_max || '', unidade: p.unidade || '',
            grupo: p.grupo || '',
          })),
        };
        await api.post('/inspection-templates', payload);
        toast.success('Modelo Mestre salvo na Biblioteca!');
      } else {
        // Save as plan linked to ativo
        const payload = {
          nome: config.nome, tipo: config.tipo, disciplina: config.disciplina,
          ativo_id: config.ativo_id || null, frequencia: preview.frequencia || 'mensal',
          status: 'rascunho', force_override: false,
          perguntas: preview.perguntas.map((p, i) => ({
            texto: p.texto, tipo_campo: p.tipo_campo || 'conforme_nao_conforme',
            obrigatorio: p.obrigatorio !== false, ordem: i,
            limite_min: p.limite_min || '', limite_max: p.limite_max || '', unidade: p.unidade || '',
            grupo: p.grupo || '',
          })),
        };
        await api.post('/planos-inspecao', payload);
        toast.success(`Plano "${config.nome}" criado com ${preview.perguntas.length} perguntas!`);
      }
      onImported?.();
      onClose();
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object' && detail.action_required === 'duplicate_conflict') {
        toast.error(`Plano já existe: ${detail.existing_plan_nome}. Altere o nome ou use "Modelo Mestre".`);
      } else { toast.error(normalizeError(err)); }
    } finally { setSaving(false); }
  };

  const removeQuestion = (idx) => {
    setPreview(prev => ({
      ...prev,
      perguntas: prev.perguntas.filter((_, i) => i !== idx),
      metadata: { ...prev.metadata, total_perguntas: prev.metadata.total_perguntas - 1 },
    }));
  };

  const updateQuestion = (idx, field, value) => {
    setPreview(prev => ({
      ...prev,
      perguntas: prev.perguntas.map((p, i) => i === idx ? { ...p, [field]: value } : p),
    }));
  };

  const filteredAtivos = buscaAtivo ? ativos.filter(a => `${a.tag} ${a.nome}`.toLowerCase().includes(buscaAtivo.toLowerCase())).slice(0, 10) : [];

  const importMethods = [
    { id: 'text', icon: ClipboardCheck, label: 'Copiar e Colar', desc: 'Cole o texto do plano ou do ChatGPT' },
    { id: 'file', icon: FileText, label: 'Arquivo', desc: 'PDF, Excel, Word ou TXT' },
  ];

  const tipoLabels = { inspecao: 'Inspeção', preventiva: 'Preventiva', lubrificacao: 'Lubrificação', mecanica: 'Mecânica', eletrica: 'Elétrica', operacional: 'Operacional' };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="glass-card w-full max-w-3xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()} data-testid="plan-import-wizard">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between sticky top-0 bg-slate-900/95 backdrop-blur-sm z-10">
          <div>
            <h2 className="text-lg font-bold text-slate-100">Assistente de Importação</h2>
            <p className="text-xs text-slate-500">Importe planos em segundos — sem digitar pergunta por pergunta</p>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-800 rounded-lg"><X size={18} className="text-slate-400" /></button>
        </div>

        {/* Steps bar */}
        <div className="px-5 pt-4 flex gap-2">
          {['Método', 'Configurar', 'Preview', 'Salvar'].map((s, i) => (
            <div key={i} className={`flex-1 h-1 rounded-full transition-all ${step > i ? 'bg-brand' : step === i + 1 ? 'bg-brand/50' : 'bg-slate-800'}`} />
          ))}
        </div>

        <div className="p-5 space-y-4">
          {/* Step 1: Choose method */}
          {step === 1 && (
            <div className="space-y-3" data-testid="import-step1">
              <p className="text-sm text-slate-300 font-medium">Como deseja importar?</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {importMethods.map(m => {
                  const Icon = m.icon;
                  return (
                    <button key={m.id} onClick={() => { setMethod(m.id); setStep(2); }}
                      className="glass-card p-5 text-left hover:border-brand transition-all group"
                      data-testid={`import-method-${m.id}`}>
                      <div className="w-12 h-12 rounded-xl bg-brand-10 flex items-center justify-center mb-3 group-hover:bg-brand-20 transition-colors">
                        <Icon size={24} className="text-brand" />
                      </div>
                      <p className="text-sm font-bold text-slate-200">{m.label}</p>
                      <p className="text-xs text-slate-500 mt-1">{m.desc}</p>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Step 2: Input + Config */}
          {step === 2 && (
            <div className="space-y-4" data-testid="import-step2">
              <button onClick={() => setStep(1)} className="text-xs text-brand flex items-center gap-1"><ArrowLeft size={12} /> Voltar</button>

              {method === 'text' && (
                <div>
                  <p className="text-sm text-slate-300 font-medium mb-2">Cole o plano aqui</p>
                  <textarea value={text} onChange={e => setText(e.target.value)}
                    className="input-industrial w-full px-4 py-3 min-h-[200px] resize-y font-mono text-sm"
                    placeholder={"1. Verificar vazamentos\n2. Verificar ruído\n3. Verificar vibração\n4. Verificar temperatura dos rolamentos - máximo 80°C\n5. Verificar desgaste dos revestimentos\n\nOBS: Parar se temperatura > 90°C"}
                    data-testid="import-text-area" autoFocus />
                </div>
              )}

              {method === 'file' && (
                <div>
                  <p className="text-sm text-slate-300 font-medium mb-2">Envie o arquivo</p>
                  <label className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-slate-700 rounded-xl hover:border-brand cursor-pointer transition-all">
                    <Upload size={32} className="text-slate-500 mb-2" />
                    <p className="text-sm text-slate-400">{file ? file.name : 'Clique para selecionar'}</p>
                    <p className="text-[10px] text-slate-600 mt-1">PDF, Excel (.xlsx), Word (.docx) ou TXT</p>
                    <input type="file" accept=".pdf,.xlsx,.xls,.docx,.doc,.txt,.csv" onChange={e => setFile(e.target.files?.[0] || null)}
                      className="hidden" data-testid="import-file-input" />
                  </label>
                </div>
              )}

              {/* Config section */}
              <div className="glass-card p-4 space-y-3">
                <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider">Configuração</p>
                <div className="grid grid-cols-2 gap-3">
                  <FormInput label="Tipo do Plano">
                    <select value={config.tipo} onChange={e => setConfig({...config, tipo: e.target.value})} className="input-industrial w-full px-4" data-testid="import-tipo">
                      {Object.entries(tipoLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                  </FormInput>
                  <FormInput label="Disciplina">
                    <select value={config.disciplina} onChange={e => setConfig({...config, disciplina: e.target.value})} className="input-industrial w-full px-4" data-testid="import-disciplina">
                      <option value="mecanica">Mecânica</option>
                      <option value="eletrica">Elétrica</option>
                      <option value="instrumentacao">Instrumentação</option>
                      <option value="lubrificacao">Lubrificação</option>
                      <option value="producao">Produção / Operação</option>
                    </select>
                  </FormInput>
                </div>
                <FormInput label="Equipamento (opcional)">
                  <input value={buscaAtivo} onChange={e => setBuscaAtivo(e.target.value)} className="input-industrial w-full px-4"
                    placeholder="Buscar ativo por TAG ou nome..." data-testid="import-ativo-busca" />
                  {buscaAtivo && filteredAtivos.length > 0 && (
                    <div className="mt-1 max-h-32 overflow-y-auto bg-slate-900 border border-slate-700 rounded-lg">
                      {filteredAtivos.map(a => (
                        <button key={a.id} onClick={() => { setConfig({...config, ativo_id: a.id}); setBuscaAtivo(`${a.tag} — ${a.nome}`); }}
                          className="w-full px-3 py-2 text-left text-sm hover:bg-slate-800 flex items-center gap-2">
                          <span className="font-mono text-brand text-xs">{a.tag}</span>
                          <span className="text-slate-300">{a.nome}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </FormInput>
                <div className="flex gap-3">
                  <label className={`flex-1 p-3 rounded-lg border text-center cursor-pointer transition-all ${config.save_as === 'plano' ? 'border-brand bg-brand-10 text-brand' : 'border-slate-700 text-slate-400'}`}>
                    <input type="radio" name="save_as" value="plano" checked={config.save_as === 'plano'} onChange={() => setConfig({...config, save_as: 'plano'})} className="hidden" />
                    <p className="text-sm font-semibold">Criar Plano</p>
                    <p className="text-[10px]">Vinculado ao equipamento</p>
                  </label>
                  <label className={`flex-1 p-3 rounded-lg border text-center cursor-pointer transition-all ${config.save_as === 'template' ? 'border-brand bg-brand-10 text-brand' : 'border-slate-700 text-slate-400'}`}>
                    <input type="radio" name="save_as" value="template" checked={config.save_as === 'template'} onChange={() => setConfig({...config, save_as: 'template'})} className="hidden" />
                    <p className="text-sm font-semibold">Modelo Mestre</p>
                    <p className="text-[10px]">Salvar na Biblioteca</p>
                  </label>
                </div>
              </div>

              <button onClick={handleParse} disabled={parsing || (method === 'text' ? !text.trim() : !file)}
                className="w-full btn-primary py-3 text-sm font-bold flex items-center justify-center gap-2"
                data-testid="import-parse-btn">
                {parsing ? <><Cog size={16} className="animate-spin" /> Analisando...</> : <><Search size={16} /> Verificar e Importar</>}
              </button>
            </div>
          )}

          {/* Step 3: Preview */}
          {step === 3 && preview && (
            <div className="space-y-4" data-testid="import-step3">
              <button onClick={() => setStep(2)} className="text-xs text-brand flex items-center gap-1"><ArrowLeft size={12} /> Voltar</button>

              {/* Summary */}
              <div className="glass-card p-4 border-brand">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-brand-20 flex items-center justify-center">
                    <CheckCircle size={20} className="text-brand" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-200">Plano detectado</p>
                    <p className="text-xs text-slate-500">{tipoLabels[config.tipo] || config.tipo} • {config.disciplina}</p>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-2 text-center">
                  <div className="bg-slate-900/50 rounded-lg p-2">
                    <p className="text-lg font-bold text-brand">{preview.metadata.total_perguntas}</p>
                    <p className="text-[9px] text-slate-500">Perguntas</p>
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-2">
                    <p className="text-lg font-bold text-slate-200">{preview.metadata.total_observacoes || 0}</p>
                    <p className="text-[9px] text-slate-500">Observações</p>
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-2">
                    <p className="text-lg font-bold text-slate-200">{preview.metadata.total_limites || 0}</p>
                    <p className="text-[9px] text-slate-500">Limites</p>
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-2">
                    <p className="text-lg font-bold text-slate-200">{preview.metadata.frequencia_detectada || '—'}</p>
                    <p className="text-[9px] text-slate-500">Frequência</p>
                  </div>
                </div>
              </div>

              {/* Name */}
              <FormInput label="Nome do Plano *">
                <input value={config.nome} onChange={e => setConfig({...config, nome: e.target.value})}
                  className="input-industrial w-full px-4" placeholder="Ex: Inspeção Mecânica Diária — Britador"
                  data-testid="import-nome" />
              </FormInput>

              {/* Questions list */}
              <div className="space-y-1 max-h-[40vh] overflow-y-auto" data-testid="import-questions-list">
                {preview.perguntas.map((p, idx) => (
                  <div key={p.id || idx} className="flex items-center gap-2 p-2 rounded-lg bg-slate-900/50 group">
                    <span className="text-[10px] text-slate-600 w-6 text-center shrink-0">{idx + 1}</span>
                    {editIdx === idx ? (
                      <input value={p.texto} onChange={e => updateQuestion(idx, 'texto', e.target.value)}
                        onBlur={() => setEditIdx(null)} onKeyDown={e => e.key === 'Enter' && setEditIdx(null)}
                        className="flex-1 bg-transparent border-b border-brand text-sm text-slate-200 outline-none" autoFocus />
                    ) : (
                      <span className="flex-1 text-sm text-slate-300 cursor-pointer" onClick={() => setEditIdx(idx)}>{p.texto}</span>
                    )}
                    <span className="text-[9px] text-slate-600 bg-slate-800 px-1.5 py-0.5 rounded shrink-0">
                      {p.tipo_campo === 'numerico' ? '123' : p.tipo_campo === 'foto' ? '📷' : p.tipo_campo === 'texto' ? 'Aa' : '✓/✗'}
                    </span>
                    {p.limite_max && <span className="text-[9px] text-amber-400 shrink-0">≤{p.limite_max}{p.unidade || ''}</span>}
                    <button onClick={() => removeQuestion(idx)} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded transition-all">
                      <X size={12} className="text-red-400" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Observations */}
              {preview.observacoes?.length > 0 && (
                <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-3">
                  <p className="text-xs text-amber-400 font-semibold mb-1">Observações Detectadas</p>
                  {preview.observacoes.map((o, i) => <p key={i} className="text-xs text-slate-400">• {o}</p>)}
                </div>
              )}

              {/* IA Button (future) */}
              <button disabled className="w-full py-2 border border-dashed border-slate-700 rounded-lg text-xs text-slate-600 flex items-center justify-center gap-2">
                <Sparkles size={14} /> Melhorar com IA (disponível futuramente)
              </button>

              <div className="flex gap-3">
                <button onClick={() => { setEditIdx(null); setStep(4); }}
                  className="flex-1 btn-primary py-3 text-sm font-bold flex items-center justify-center gap-2"
                  data-testid="import-confirm-btn">
                  <Download size={16} /> Importar {preview.perguntas.length} perguntas
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Final save */}
          {step === 4 && (
            <div className="space-y-4 text-center py-6" data-testid="import-step4">
              <div className="w-16 h-16 rounded-full bg-brand-20 flex items-center justify-center mx-auto">
                <CheckCircle size={32} className="text-brand" />
              </div>
              <h3 className="text-lg font-bold text-slate-100">Pronto para salvar</h3>
              <div className="glass-card p-4 text-left space-y-2">
                <div className="flex justify-between text-sm"><span className="text-slate-500">Nome</span><span className="text-slate-200">{config.nome || '(sem nome)'}</span></div>
                <div className="flex justify-between text-sm"><span className="text-slate-500">Tipo</span><span className="text-slate-200 capitalize">{tipoLabels[config.tipo] || config.tipo}</span></div>
                <div className="flex justify-between text-sm"><span className="text-slate-500">Disciplina</span><span className="text-slate-200 capitalize">{config.disciplina}</span></div>
                <div className="flex justify-between text-sm"><span className="text-slate-500">Destino</span><span className="text-brand font-semibold">{config.save_as === 'template' ? 'Modelo Mestre (Biblioteca)' : 'Plano vinculado ao ativo'}</span></div>
                <div className="flex justify-between text-sm"><span className="text-slate-500">Perguntas</span><span className="text-slate-200 font-bold">{preview?.perguntas?.length}</span></div>
              </div>
              <div className="flex gap-3 pt-2">
                <button onClick={() => setStep(3)} className="flex-1 py-3 bg-slate-800 text-slate-300 rounded-lg text-sm font-medium hover:bg-slate-700">Voltar</button>
                <button onClick={handleSave} disabled={saving}
                  className="flex-1 btn-primary py-3 text-sm font-bold flex items-center justify-center gap-2"
                  data-testid="import-save-btn">
                  <Save size={16} /> {saving ? 'Salvando...' : 'Salvar Plano'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};


const AdminTemplatesPage = () => {
  const [templates, setTemplates] = useState([]);
  const [equipTypes, setEquipTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // null = list, object = editing
  const [form, setForm] = useState({ nome: '', tipo_equipamento: '', descricao: '', tipo: 'inspecao', disciplina: '', ativo_id: '', itens: [] });
  const [saving, setSaving] = useState(false);
  const [deleteItem, setDeleteItem] = useState(null);
  const [ativos, setAtivos] = useState([]);
  const [searchPlano, setSearchPlano] = useState('');
  const [filterDisciplina, setFilterDisciplina] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [showImportWizard, setShowImportWizard] = useState(false);
  const { user } = useAuth();

  const fetchData = async () => {
    try {
      const [tRes, eRes, aRes] = await Promise.all([
        api.get('/planos-inspecao'),
        api.get('/equipment-types').catch(() => ({ data: [] })),
        api.get('/ativos').catch(() => ({ data: [] }))
      ]);
      setTemplates(tRes.data);
      setEquipTypes(eRes.data);
      setAtivos(aRes.data);
    } catch { toast.error('Erro ao carregar planos'); }
    finally { setLoading(false); }
  };
  useEffect(() => { fetchData(); }, []);

  const openNew = () => {
    setForm({ nome: '', tipo_equipamento: '', descricao: '', tipo: 'inspecao', disciplina: '', ativo_id: '', itens: [] });
    setEditing('new');
  };

  const openEdit = (t) => {
    setForm({
      nome: t.nome, tipo_equipamento: t.tipo_equipamento || '', descricao: t.descricao || '',
      tipo: t.tipo || t.categoria || 'inspecao', disciplina: t.disciplina || '',
      ativo_id: t.ativo_id || '',
      itens: (t.perguntas || t.itens || []).map(p => ({
        id: p.id || `edit-${Date.now()}-${Math.random()}`,
        descricao: p.texto || p.descricao || '',
        tipo: p.tipo_campo || p.tipo || 'boolean',
        obrigatorio: p.obrigatoria ?? p.obrigatorio ?? true,
        unidade: p.unidade || '',
        tolerancia_min: p.valor_min ?? p.tolerancia_min ?? null,
        tolerancia_max: p.valor_max ?? p.tolerancia_max ?? null,
        limite_normal: p.limite_normal ?? null,
        limite_alerta: p.limite_alerta ?? null,
        limite_critico: p.limite_critico ?? null,
        foto_obrigatoria_nc: p.foto_obrigatoria_nc || false,
        periodicidade: p.periodicidade || null,
        opcoes: p.opcoes || null,
      }))
    });
    setEditing(t);
  };

  const handleDuplicate = async (t) => {
    try {
      await api.post(`/planos-inspecao`, {
        nome: `${t.nome} (Cópia)`,
        tipo: t.tipo || t.categoria || 'inspecao',
        tipo_equipamento: t.tipo_equipamento,
        categoria: t.categoria || t.tipo,
        disciplina: t.disciplina,
        ativo_id: t.ativo_id || null,
        perguntas: t.perguntas || []
      });
      toast.success('Plano duplicado!');
      fetchData();
    } catch { toast.error('Erro ao duplicar'); }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/planos-inspecao/${deleteItem.id}`);
      toast.success('Plano excluído!');
      setDeleteItem(null);
      fetchData();
    } catch { toast.error('Erro ao excluir'); }
  };

  const handleAprovar = async (plano) => {
    try {
      await api.patch(`/planos-inspecao/${plano.id}/aprovar`);
      toast.success(`Plano "${plano.nome}" aprovado para execução!`);
      fetchData();
    } catch (error) { toast.error(normalizeError(error)); }
  };

  const addItem = () => {
    setForm(prev => ({ ...prev, itens: [...prev.itens, { id: `new-${Date.now()}`, descricao: '', tipo: 'boolean', obrigatorio: true, unidade: '', tolerancia_min: null, tolerancia_max: null }] }));
  };

  const updateItem = (idx, field, value) => {
    setForm(prev => ({ ...prev, itens: prev.itens.map((it, i) => i === idx ? { ...it, [field]: value } : it) }));
  };

  const removeItem = (idx) => {
    setForm(prev => ({ ...prev, itens: prev.itens.filter((_, i) => i !== idx) }));
  };

  const handleSave = async (forceOverride = false) => {
    if (!form.nome) { toast.error("Campo 'Nome do Plano' é obrigatório"); return; }
    if (form.itens.length === 0) { toast.error('Adicione pelo menos uma pergunta'); return; }
    setSaving(true);
    try {
      const payload = {
        nome: form.nome,
        tipo: form.tipo || 'inspecao',
        tipo_equipamento: form.tipo_equipamento || null,
        categoria: form.tipo || 'inspecao',
        disciplina: form.disciplina || null,
        ativo_id: form.ativo_id || null,
        force_override: forceOverride,
        perguntas: form.itens.map((it, idx) => ({
          descricao: it.descricao, tipo: it.tipo, obrigatorio: it.obrigatorio, unidade: it.unidade,
          limite_normal: it.tolerancia_max || it.limite_normal, limite_alerta: it.limite_alerta, limite_critico: it.limite_critico,
          periodicidade: it.periodicidade, foto_obrigatoria_nc: it.foto_obrigatoria_nc || false, opcoes: it.opcoes, ordem: idx
        }))
      };
      if (editing === 'new') {
        await api.post('/planos-inspecao', payload);
        toast.success('Plano criado!');
      } else {
        await api.put(`/planos-inspecao/${editing.id}`, payload);
        toast.success('Plano atualizado!');
      }
      setEditing(null);
      fetchData();
    } catch (error) {
      // Handle duplicate conflict (409)
      const detail = error?.response?.data?.detail;
      if (error?.response?.status === 409 && detail?.action_required === 'duplicate_conflict') {
        const existingId = detail.existing_plan_id;
        const existingNome = detail.existing_plan_nome;
        const confirmed = window.confirm(
          `${detail.message}\n\nDeseja:\n• OK = Criar mesmo assim (substituir)\n• Cancelar = Abrir plano existente "${existingNome}"`
        );
        if (confirmed) {
          handleSave(true); // retry with force_override
        } else if (existingId) {
          // Open existing plan
          const existing = templates.find(t => t.id === existingId);
          if (existing) openEdit(existing);
        }
      } else {
        toast.error(normalizeError(error));
      }
    }
    finally { setSaving(false); }
  };

  if (loading) return <Loading rows={3} />;

  // Apply search and filters
  const filteredTemplates = templates.filter(t => {
    if (searchPlano) {
      const s = searchPlano.toLowerCase();
      const match = (t.nome || '').toLowerCase().includes(s)
        || (t.ativo_tag || '').toLowerCase().includes(s)
        || (t.ativo_nome || '').toLowerCase().includes(s)
        || (t.area_nome || '').toLowerCase().includes(s)
        || (t.tipo_equipamento || '').toLowerCase().includes(s)
        || (t.disciplina || '').toLowerCase().includes(s);
      if (!match) return false;
    }
    if (filterDisciplina && t.disciplina !== filterDisciplina) return false;
    if (filterStatus && t.status !== filterStatus) return false;
    return true;
  });

  // EDIT VIEW
  if (editing) return (
    <div className="space-y-4" data-testid="template-editor">
      <div className="flex items-center gap-3">
        <button onClick={() => setEditing(null)} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg"><ArrowLeft size={20} className="text-slate-400" /></button>
        <h1 className="text-xl font-bold text-slate-100">{editing === 'new' ? 'Novo Plano de Inspeção' : 'Editar Plano de Inspeção'}</h1>
      </div>

      <div className="glass-card p-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormInput label="Nome do Plano" required>
            <input value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: Inspeção Alimentador Vibratório" data-testid="template-nome" />
          </FormInput>
          <FormInput label="Tipo do Plano" required>
            <select value={form.tipo} onChange={e => setForm({...form, tipo: e.target.value})} className="input-industrial w-full px-4" data-testid="template-tipo-plano">
              <option value="inspecao">Inspeção</option>
              <option value="preventiva">Preventiva</option>
              <option value="lubrificacao">Lubrificação</option>
              <option value="limpeza">Limpeza</option>
              <option value="melhoria">Melhoria</option>
            </select>
          </FormInput>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FormInput label="Tipo de Equipamento">
            <input value={form.tipo_equipamento} onChange={e => setForm({...form, tipo_equipamento: e.target.value})} list="equip-types" className="input-industrial w-full px-4" placeholder="Ex: Alimentador Vibratório" data-testid="template-tipo" />
            <datalist id="equip-types">{equipTypes.map(t => <option key={t} value={t} />)}</datalist>
          </FormInput>
          <FormInput label="Disciplina">
            <select value={form.disciplina} onChange={e => setForm({...form, disciplina: e.target.value})} className="input-industrial w-full px-4" data-testid="template-disciplina">
              <option value="">Todas</option>
              <option value="mecanica">Mecânica</option>
              <option value="eletrica">Elétrica</option>
              <option value="instrumentacao">Instrumentação</option>
              <option value="civil">Civil</option>
              <option value="producao">Produção</option>
            </select>
          </FormInput>
          <FormInput label="Vincular a Ativo (opcional)">
            <select value={form.ativo_id} onChange={e => setForm({...form, ativo_id: e.target.value})} className="input-industrial w-full px-4" data-testid="template-ativo">
              <option value="">Plano genérico (sem ativo)</option>
              {ativos.map(a => <option key={a.id} value={a.id}>{`${a.sector?.nome || ''} \u203A ${a.tag} \u2014 ${a.nome} ${a.tipo_equipamento ? '(' + a.tipo_equipamento + ')' : ''} ${a.fabricante || ''}`}</option>)}
            </select>
          </FormInput>
        </div>
        <FormInput label="Descrição">
          <input value={form.descricao} onChange={e => setForm({...form, descricao: e.target.value})} className="input-industrial w-full px-4" placeholder="Descrição opcional" />
        </FormInput>
      </div>

      <div className="glass-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-brand">Itens do Checklist ({form.itens.length})</h3>
          <button onClick={addItem} className="btn-primary text-sm flex items-center gap-1" data-testid="add-checklist-item"><Plus size={16} /> Adicionar Item</button>
        </div>

        {form.itens.map((item, idx) => (
          <div key={item.id || idx} className="bg-slate-800/50 rounded-lg p-3 space-y-2" data-testid={`template-item-${idx}`}>
            <div className="flex items-start gap-2">
              <span className="text-xs text-slate-500 mt-2 w-6">{idx+1}.</span>
              <div className="flex-1 space-y-2">
                <input value={item.descricao} onChange={e => updateItem(idx, 'descricao', e.target.value)} className="input-industrial w-full px-3 text-sm" placeholder="Descrição do item (ex: Verificar vibração)" />
                <div className="flex gap-2 flex-wrap">
                  <select value={item.tipo} onChange={e => updateItem(idx, 'tipo', e.target.value)} className="input-industrial px-3 text-sm">
                    {FIELD_TYPES.map(ft => <option key={ft.value} value={ft.value}>{ft.label}</option>)}
                  </select>
                  {(item.tipo === 'numerico' || item.tipo === 'temperatura' || item.tipo === 'vibracao') && (
                    <>
                      <input type="text" value={item.unidade || ''} onChange={e => updateItem(idx, 'unidade', e.target.value)} className="input-industrial px-3 text-sm w-20" placeholder="Un." />
                      <input type="number" value={item.tolerancia_min ?? ''} onChange={e => updateItem(idx, 'tolerancia_min', e.target.value ? parseFloat(e.target.value) : null)} className="input-industrial px-3 text-sm w-20" placeholder="Mín" />
                      <input type="number" value={item.tolerancia_max ?? ''} onChange={e => updateItem(idx, 'tolerancia_max', e.target.value ? parseFloat(e.target.value) : null)} className="input-industrial px-3 text-sm w-20" placeholder="Máx" />
                    </>
                  )}
                  <label className="flex items-center gap-1 text-xs text-slate-400 cursor-pointer">
                    <input type="checkbox" checked={item.obrigatorio} onChange={e => updateItem(idx, 'obrigatorio', e.target.checked)} className="accent-brand" />
                    Obrigatório
                  </label>
                </div>
              </div>
              <button onClick={() => removeItem(idx)} className="p-1.5 hover:bg-red-500/10 rounded"><Trash2 size={14} className="text-red-400" /></button>
            </div>
          </div>
        ))}
        {form.itens.length === 0 && <p className="text-center text-slate-600 text-sm py-4">Nenhum item. Clique em "Adicionar Item" para começar.</p>}
      </div>

      <div className="flex gap-3 justify-end">
        <button onClick={() => setEditing(null)} className="btn-secondary">Cancelar</button>
        <button onClick={() => handleSave(false)} disabled={saving} className="btn-primary flex items-center gap-2" data-testid="save-template">
          {saving ? <RefreshCw size={16} className="animate-spin" /> : <Save size={16} />}
          {saving ? 'Salvando...' : 'Salvar Plano'}
        </button>
      </div>
    </div>
  );

  // LIST VIEW
  return (
    <div className="space-y-4" data-testid="templates-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Planos de Inspeção</h1>
          <p className="text-sm text-slate-500">Gerenciar perguntas por tipo de equipamento e por ativo</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowImportWizard(true)} className="flex items-center gap-2 px-4 py-2 bg-brand-10 hover:bg-brand-20 text-brand rounded-lg text-sm font-medium transition-all" data-testid="import-plan-btn"><Upload size={16} /> Importar</button>
          <button onClick={openNew} className="btn-primary flex items-center gap-2" data-testid="new-template-btn"><Plus size={20} /> Novo Plano</button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="glass-card p-3 flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[200px]">
          <input value={searchPlano} onChange={e => setSearchPlano(e.target.value)} className="input-industrial w-full px-3 text-sm" placeholder="Buscar plano, ativo, área..." data-testid="plano-search" />
        </div>
        <select value={filterDisciplina} onChange={e => setFilterDisciplina(e.target.value)} className="input-industrial px-3 text-sm" data-testid="plano-filter-disciplina">
          <option value="">Todas disciplinas</option>
          <option value="mecanica">Mecânica</option>
          <option value="eletrica">Elétrica</option>
          <option value="instrumentacao">Instrumentação</option>
          <option value="producao">Produção</option>
          <option value="lubrificacao">Lubrificação</option>
        </select>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="input-industrial px-3 text-sm" data-testid="plano-filter-status">
          <option value="">Todos status</option>
          <option value="aprovado">Aprovado</option>
          <option value="rascunho">Rascunho</option>
        </select>
        <span className="text-xs text-slate-500">{filteredTemplates.length} de {templates.length}</span>
      </div>

      {filteredTemplates.length > 0 ? (
        <div className="space-y-2">
          {filteredTemplates.map(t => {
            const isAprovado = t.status === 'aprovado';
            const statusLabel = isAprovado ? 'Aprovado' : (t.status === 'ativo' ? 'Ativo' : (t.status || 'Rascunho'));
            const statusColor = isAprovado ? 'text-emerald-400 bg-brand-10 border-emerald-500/30' : 'text-amber-400 bg-amber-500/10 border-amber-500/30';
            const tipoLabels = { inspecao: 'Inspeção', preventiva: 'Preventiva', lubrificacao: 'Lubrificação', limpeza: 'Limpeza', melhoria: 'Melhoria' };
            return (
            <div key={t.id} className="glass-card p-4 hover:border-slate-600 transition-all group" data-testid={`template-card-${t.id}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="cursor-pointer flex-1 min-w-0" onClick={() => openEdit(t)}>
                  {/* Hierarchy breadcrumb */}
                  {t.ativo_tag && (
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-600 mb-1 truncate">
                      {t.area_nome && <><span>{t.area_nome}</span><ChevronRight size={10} /></>}
                      <span className="text-brand/70 font-mono">{t.ativo_tag}</span>
                      <ChevronRight size={10} />
                      <span className="text-slate-500">{t.ativo_nome}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                    <ClipboardCheck size={16} className="text-brand shrink-0" />
                    <span className="text-slate-100 font-medium">{t.nome}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border ${statusColor}`}>{statusLabel}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500 flex-wrap">
                    <span className="bg-slate-800 px-2 py-0.5 rounded capitalize">{tipoLabels[t.tipo] || t.tipo || ''}</span>
                    {t.disciplina && <span className="bg-slate-800 px-2 py-0.5 rounded capitalize">{t.disciplina}</span>}
                    <span>{(t.perguntas || []).length} perguntas</span>
                    <span>v{t.versao || 1}</span>
                    {t.ativo_fabricante && <span className="text-slate-600">{t.ativo_fabricante}</span>}
                    {t.ativo_modelo && <span className="text-slate-600">{t.ativo_modelo}</span>}
                    {!t.ativo_id && <span className="px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">Genérico</span>}
                    {t.updated_at && <span className="text-slate-700">{new Date(t.updated_at).toLocaleDateString('pt-BR')}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  {!isAprovado && (t.perguntas || []).length > 0 && (
                    <button onClick={() => handleAprovar(t)} className="px-3 py-1.5 bg-brand-20 hover:brightness-110 text-brand text-xs font-medium rounded-lg border border-brand-30 transition-all" title="Aprovar para execução" data-testid={`aprovar-plano-${t.id}`}>
                      Aprovar
                    </button>
                  )}
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => openEdit(t)} className="p-2 hover:bg-slate-700 rounded-lg" title="Editar"><Edit size={16} className="text-slate-400" /></button>
                    <button onClick={() => handleDuplicate(t)} className="p-2 hover:bg-blue-500/10 rounded-lg" title="Duplicar"><Copy size={16} className="text-blue-400" /></button>
                    <button onClick={() => setDeleteItem(t)} className="p-2 hover:bg-red-500/10 rounded-lg" title="Excluir"><Trash2 size={16} className="text-red-400" /></button>
                  </div>
                </div>
              </div>
            </div>
            );
          })}
        </div>
      ) : (
        <EmptyState icon={ClipboardCheck} title="Nenhum plano" description="Crie planos de inspeção para cada tipo de equipamento" actionLabel="Novo Plano" onAction={openNew} />
      )}
      <ConfirmDialog isOpen={!!deleteItem} onClose={() => setDeleteItem(null)} onConfirm={handleDelete} title="Excluir Plano" message={`Excluir "${deleteItem?.nome}"?`} confirmText="Excluir" danger />
      {showImportWizard && <PlanImportWizard onClose={() => setShowImportWizard(false)} onImported={fetchData} />}
    </div>
  );
};


// ============== ADMIN USUARIOS PAGE ==============


// ============== AUDITORIA ==============

const AuditoriaPage = () => {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ entity_type: '', action: '', date_from: '', date_to: '' });
  const { user } = useAuth();

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.entity_type) params.entity_type = filters.entity_type;
      if (filters.action) params.action = filters.action;
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;
      const [logsRes, statsRes] = await Promise.all([
        api.get('/admin/audit-logs', { params }),
        api.get('/admin/audit-logs/stats').catch(() => ({ data: null }))
      ]);
      setLogs(logsRes.data);
      setStats(statsRes.data);
    } catch { toast.error('Erro ao carregar auditoria'); }
    finally { setLoading(false); }
  };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchLogs(); }, []);

  const handleExport = async (fmt) => {
    try {
      const res = await api.get(`/export/audit?format=${fmt}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `auditoria_export.${fmt === 'excel' ? 'xlsx' : 'pdf'}`);
      document.body.appendChild(link); link.click(); link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Exportado!');
    } catch { toast.error('Erro ao exportar'); }
  };

  const modules = ['auth', 'ativos', 'ordens_servico', 'inspecoes', 'anomalias', 'estoque', 'sobressalentes', 'security'];
  const actions = ['login', 'create', 'update', 'delete', 'status_change', 'access_denied', 'duplicate'];
  const actionColors = {
    login: 'text-blue-400 bg-blue-500/10', create: 'text-emerald-400 bg-brand-10',
    update: 'text-amber-400 bg-amber-500/10', delete: 'text-red-400 bg-red-500/10',
    status_change: 'text-purple-400 bg-purple-500/10', access_denied: 'text-red-400 bg-red-500/20',
    duplicate: 'text-blue-400 bg-blue-500/10',
  };

  return (
    <div className="space-y-4" data-testid="auditoria-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Auditoria</h1>
          <p className="text-sm text-slate-500">{stats ? `${stats.total} registros` : ''}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => handleExport('excel')} className="btn-secondary text-sm flex items-center gap-1" data-testid="audit-export-excel"><Download size={14} /> Excel</button>
          <button onClick={() => handleExport('pdf')} className="btn-secondary text-sm flex items-center gap-1"><FileText size={14} /> PDF</button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="flex gap-2 flex-wrap">
          {Object.entries(stats.by_module || {}).map(([mod, count]) => (
            <span key={mod} className="bg-slate-800/50 text-slate-400 text-xs px-2 py-1 rounded">{mod}: {count}</span>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="glass-card p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <select value={filters.entity_type} onChange={e => setFilters({...filters, entity_type: e.target.value})} className="input-industrial px-3 text-sm">
            <option value="">Todos os módulos</option>
            {modules.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
          <select value={filters.action} onChange={e => setFilters({...filters, action: e.target.value})} className="input-industrial px-3 text-sm">
            <option value="">Todas as operações</option>
            {actions.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
          <input type="date" value={filters.date_from} onChange={e => setFilters({...filters, date_from: e.target.value})} className="input-industrial px-3 text-sm" />
          <div className="flex gap-2">
            <input type="date" value={filters.date_to} onChange={e => setFilters({...filters, date_to: e.target.value})} className="input-industrial px-3 text-sm flex-1" />
            <button onClick={fetchLogs} className="btn-primary text-sm px-3" data-testid="audit-filter-btn">Filtrar</button>
          </div>
        </div>
      </div>

      {/* Logs */}
      {loading ? <Loading rows={8} /> : logs.length > 0 ? (
        <div className="space-y-1">
          {logs.map((log, idx) => (
            <div key={log.id || idx} className="glass-card px-4 py-3 flex items-center gap-3" data-testid={`audit-row-${idx}`}>
              <span className="text-xs text-slate-600 w-28 shrink-0">{(log.created_at || '').slice(0,16).replace('T',' ')}</span>
              <span className="text-xs text-slate-300 w-28 shrink-0 truncate">{log.user_nome}</span>
              <span className="text-[10px] text-slate-500 w-16 shrink-0">{log.user_role}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded w-20 text-center shrink-0 ${actionColors[log.action] || 'text-slate-400 bg-slate-800'}`}>{log.action}</span>
              <span className="text-xs text-slate-500 w-20 shrink-0">{log.entity_type}</span>
              <span className="text-xs text-slate-400 flex-1 truncate">{log.details}</span>
            </div>
          ))}
        </div>
      ) : <EmptyState icon={Shield} title="Nenhum registro" description="Logs de auditoria aparecerão aqui." />}
    </div>
  );
};


const AdminUsuariosPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [form, setForm] = useState({ nome: '', email: '', password: '', role: 'tecnico', telefone: '', disciplina_principal: '', disciplinas_secundarias: [], turno: '' });
  const [saving, setSaving] = useState(false);
  const [resetResult, setResetResult] = useState(null);
  const { user } = useAuth();

  const fetchUsers = async () => {
    try { const res = await api.get('/admin/users'); setUsers(res.data); }
    catch (e) { toast.error('Sem permissão'); }
    finally { setLoading(false); }
  };
  useEffect(() => { fetchUsers(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.nome || !form.email || !form.password) { toast.error('Preencha todos os campos obrigatórios'); return; }
    setSaving(true);
    try {
      await api.post('/admin/users', form);
      toast.success('Usuário criado!');
      setShowModal(false);
      setForm({ nome: '', email: '', password: '', role: 'tecnico', telefone: '', disciplina_principal: '', disciplinas_secundarias: [], turno: '' });
      fetchUsers();
    } catch (e) { toast.error(normalizeError(e)); }
    finally { setSaving(false); }
  };

  const handleDelete = async (uid) => {
    if (uid === user?.id) { toast.error('Não pode excluir a si mesmo'); return; }
    try { await api.delete(`/admin/users/${uid}`); toast.success('Removido'); fetchUsers(); } catch { toast.error('Erro'); }
  };

  const handleResetPassword = async (uid, nome) => {
    try {
      const res = await api.post(`/admin/users/${uid}/reset-password`);
      setResetResult({ nome, temp_password: res.data.temp_password });
      toast.success('Senha temporária gerada!');
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const handleEditUser = (u) => {
    setEditUser(u);
    setForm({ nome: u.nome, email: u.email, password: '', role: u.role, telefone: u.telefone || '',
      disciplina_principal: u.disciplina_principal || '', disciplinas_secundarias: u.disciplinas_secundarias || [], turno: u.turno || '' });
    setShowModal(true);
  };

  const handleSaveEdit = async () => {
    setSaving(true);
    try {
      await api.put(`/admin/users/${editUser.id}`, {
        nome: form.nome, email: form.email, role: form.role, telefone: form.telefone,
        disciplina_principal: form.disciplina_principal, disciplinas_secundarias: form.disciplinas_secundarias, turno: form.turno
      });
      toast.success('Usuário atualizado!');
      setShowModal(false);
      setEditUser(null);
      fetchUsers();
    } catch (e) { toast.error(normalizeError(e)); }
    finally { setSaving(false); }
  };

  const roleLabels = { master: 'Master', admin: 'Administrador', gerente: 'Gerente', pcm: 'PCM', supervisor: 'Supervisor', tecnico: 'Técnico', operador: 'Operador', inspetor: 'Inspetor', viewer: 'Visualizador' };
  const roleColors = { master: 'text-pink-400 bg-pink-500/10', admin: 'text-red-400 bg-red-500/10', gerente: 'text-purple-400 bg-purple-500/10', pcm: 'text-blue-400 bg-blue-500/10', supervisor: 'text-amber-400 bg-amber-500/10', tecnico: 'text-emerald-400 bg-brand-10', operador: 'text-teal-400 bg-teal-500/10', inspetor: 'text-cyan-400 bg-cyan-500/10', viewer: 'text-slate-400 bg-slate-500/10' };
  const disciplinaLabels = { mecanica: 'Mecânica', eletrica: 'Elétrica', instrumentacao: 'Instrumentação', operacao: 'Operação', civil: 'Civil', producao: 'Produção', lubrificacao: 'Lubrificação' };

  if (!['admin','master'].includes(user?.role)) return <EmptyState icon={Shield} title="Acesso Restrito" description="Apenas administradores podem gerenciar usuários." />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Gestão de Usuários</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2" data-testid="add-user-btn"><Plus size={20} /> Novo Usuário</button>
      </div>
      {loading ? <Loading rows={5} /> : (
        <div className="space-y-2">
          {users.map((u) => (
            <div key={u.id} className="glass-card p-4 flex items-center justify-between group">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-brand-20 flex items-center justify-center"><User size={20} className="text-brand" /></div>
                <div>
                  <p className="text-slate-100 font-medium">{u.nome}</p>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span>{u.email}</span>
                    {u.disciplina_principal && <span className="bg-slate-800 px-1.5 py-0.5 rounded capitalize">{disciplinaLabels[u.disciplina_principal] || u.disciplina_principal}</span>}
                    {u.turno && <span className="bg-slate-800 px-1.5 py-0.5 rounded">Turno {u.turno}</span>}
                  </div>
                  {u.force_password_change && <span className="text-[10px] text-amber-400">Troca de senha pendente</span>}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-3 py-1 rounded-full font-medium ${roleColors[u.role] || ''}`}>{roleLabels[u.role] || u.role}</span>
                {u.id !== user?.id && (
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => handleEditUser(u)} className="p-2 hover:bg-blue-500/10 rounded-lg" title="Editar"><Edit3 size={15} className="text-blue-400" /></button>
                    <button onClick={() => handleResetPassword(u.id, u.nome)} className="p-2 hover:bg-amber-500/10 rounded-lg" title="Redefinir senha"><Lock size={15} className="text-amber-400" /></button>
                    <button onClick={() => handleDelete(u.id)} className="p-2 hover:bg-red-500/10 rounded-lg" title="Excluir"><Trash2 size={15} className="text-red-400" /></button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditUser(null); }} title={editUser ? "Editar Usuário" : "Novo Usuário"} size="md">
        <form onSubmit={editUser ? (e) => { e.preventDefault(); handleSaveEdit(); } : handleSubmit} className="space-y-4">
          <FormInput label="Nome Completo" required><input value={form.nome} onChange={(e) => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-4" required /></FormInput>
          <div className="grid grid-cols-2 gap-4">
            <FormInput label="Email" required><input type="email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} className="input-industrial w-full px-4" required /></FormInput>
            {!editUser && <FormInput label="Senha" required><input type="password" value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} className="input-industrial w-full px-4" required /></FormInput>}
            {editUser && <FormInput label="Senha"><p className="text-xs text-slate-500 pt-3">Use "Redefinir senha" para alterar</p></FormInput>}
          </div>
          <div className="grid grid-cols-2 gap-4">
            <FormInput label="Perfil" required>
              <Select value={form.role} onChange={(v) => setForm({...form, role: v})} options={[
                {value:'admin',label:'Administrador'},{value:'gerente',label:'Gerente'},{value:'pcm',label:'PCM'},
                {value:'supervisor',label:'Supervisor'},{value:'tecnico',label:'Técnico'},{value:'inspetor',label:'Inspetor'},{value:'viewer',label:'Visualizador'}
              ]} />
            </FormInput>
            <FormInput label="Telefone"><input value={form.telefone} onChange={(e) => setForm({...form, telefone: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
          </div>
          <div className="glass-card p-3 text-xs text-slate-500">
            <p className="font-semibold text-slate-400 mb-1">Permissões por perfil:</p>
            <p><span className="text-red-400">Admin</span>: Controle total</p>
            <p><span className="text-purple-400">Gerente</span>: Dashboard e relatórios (somente leitura)</p>
            <p><span className="text-blue-400">PCM</span>: Gerencia OS, estoque, relatórios, exporta dados</p>
            <p><span className="text-brand">Técnico</span>: Preenche inspeções, abre anomalias</p>
          </div>
          <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Salvando...' : editUser ? 'Salvar Alterações' : 'Criar Usuário'}</button>
          </div>
        </form>
      </Modal>

      {/* Reset Password Result Modal */}
      <Modal isOpen={!!resetResult} onClose={() => setResetResult(null)} title="Senha Temporária Gerada" size="sm">
        <div className="space-y-4 text-center">
          <div className="w-16 h-16 mx-auto rounded-full bg-amber-500/10 flex items-center justify-center">
            <Lock size={32} className="text-amber-400" />
          </div>
          <p className="text-slate-300">Senha temporária para <strong className="text-slate-100">{resetResult?.nome}</strong>:</p>
          <div className="bg-slate-800 rounded-lg p-4 font-mono text-xl text-brand tracking-widest select-all" data-testid="temp-password">
            {resetResult?.temp_password}
          </div>
          <p className="text-xs text-amber-400">O usuário será obrigado a trocar a senha no próximo login.</p>
          <p className="text-xs text-slate-500">Copie e envie ao usuário de forma segura. Esta senha não será exibida novamente.</p>
          <button onClick={() => setResetResult(null)} className="btn-primary w-full">Entendido</button>
        </div>
      </Modal>
    </div>
  );
};

// ============== EXPORT BUTTONS COMPONENT ==============

const ExportButtons = ({ entity }) => {
  const { user } = useAuth();
  if (!['admin','master','pcm','gerente'].includes(user?.role)) return null;
  
  const handleExport = async (format) => {
    try {
      const res = await api.get(`/export/${entity}?format=${format}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `${entity}_export.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      link.click();
      window.URL.revokeObjectURL(url);
      toast.success(`Exportado em ${format.toUpperCase()}`);
    } catch (e) { toast.error('Erro ao exportar'); }
  };

  return (
    <div className="flex gap-1">
      <button onClick={() => handleExport('excel')} className="p-2 bg-brand-10 hover:bg-brand-20 text-brand rounded-lg transition-colors" title="Excel"><FileText size={16} /></button>
      <button onClick={() => handleExport('pdf')} className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors" title="PDF"><FileText size={16} /></button>
    </div>
  );
};

// ============== LAYOUT ==============

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen bg-slate-950 flex items-center justify-center"><Cog size={48} className="text-brand animate-spin" /></div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

// ============== SETORES PAGE ==============
const SetoresPage = () => {
  const [sectors, setSectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const [form, setForm] = useState({ codigo: '', nome: '', descricao: '', cor: '#10b981' });
  const [saving, setSaving] = useState(false);
  const { user } = useAuth();

  const fetchData = async () => {
    try {
      const sRes = await api.get('/sectors');
      setSectors(sRes.data);
    } catch { toast.error('Erro ao carregar áreas'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const openModal = (item = null) => {
    setEditItem(item);
    setForm(item 
      ? { codigo: item.codigo || '', nome: item.nome || '', descricao: item.descricao || '', cor: item.cor || '#10b981' }
      : { codigo: '', nome: '', descricao: '', cor: '#10b981' }
    );
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.codigo || !form.nome) { toast.error('Código e nome são obrigatórios'); return; }
    setSaving(true);
    try {
      if (editItem) {
        await api.put(`/sectors/${editItem.id}`, { nome: form.nome, descricao: form.descricao, cor: form.cor });
        toast.success('Área atualizada!');
      } else {
        await api.post('/sectors', form);
        toast.success('Área criada!');
      }
      setShowModal(false);
      fetchData();
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/sectors/${deleteItem.id}`);
      toast.success('Área excluída!');
      setDeleteItem(null);
      fetchData();
    } catch (err) { toast.error(normalizeError(err)); }
  };

  const handleToggle = async (sector) => {
    try {
      await api.patch(`/sectors/${sector.id}/toggle`);
      toast.success(sector.is_active ? 'Área desabilitada' : 'Área habilitada');
      fetchData();
    } catch (err) { toast.error('Erro ao alterar status'); }
  };

  const colors = ['#10b981','#3b82f6','#f59e0b','#8b5cf6','#ef4444','#ec4899','#06b6d4','#f97316'];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100" data-testid="setores-title">Áreas</h1>
          <p className="text-sm text-slate-500">Gerencie as áreas industriais</p>
        </div>
        {['admin','master'].includes(user?.role) && (
          <button onClick={() => openModal()} className="btn-primary flex items-center gap-2" data-testid="add-sector-btn">
            <Plus size={20} /> Nova Área
          </button>
        )}
      </div>

      <div className="flex items-center gap-3">
        <p className="text-sm text-slate-500">{sectors.length} áreas cadastradas</p>
      </div>

      {loading ? <Loading rows={3} /> : sectors.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sectors.map(s => (
            <div key={s.id} className="glass-card p-5 hover:border-slate-600 transition-all group" data-testid={`sector-card-${s.codigo}`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: s.cor || '#10b981' }} />
                  <div>
                    <span className="font-mono text-sm" style={{ color: s.cor || '#10b981' }}>{s.codigo}</span>
                    <p className="text-slate-100 font-medium">{s.nome}</p>
                  </div>
                </div>
                {['admin','master'].includes(user?.role) && (
                  <div className="hidden group-hover:flex items-center gap-1">
                    <button onClick={() => openModal(s)} className="p-2 hover:bg-slate-700 rounded-lg"><Edit size={16} className="text-slate-400" /></button>
                    <button onClick={() => handleToggle(s)} className={`p-2 rounded-lg ${s.is_active !== false ? 'hover:bg-yellow-500/10' : 'hover:bg-green-500/10'}`} title={s.is_active !== false ? 'Desabilitar' : 'Habilitar'}>
                      {s.is_active !== false ? <Pause size={16} className="text-yellow-400" /> : <Play size={16} className="text-green-400" />}
                    </button>
                    <button onClick={() => setDeleteItem(s)} className="p-2 hover:bg-red-500/10 rounded-lg"><Trash2 size={16} className="text-red-400" /></button>
                  </div>
                )}
              </div>
              {s.plant && <p className="text-xs text-slate-500 mb-2"><Building size={12} className="inline mr-1" />{s.plant.nome}</p>}
              {s.descricao && <p className="text-xs text-slate-500 mb-2">{s.descricao}</p>}
              <div className="flex items-center gap-1.5 text-sm text-slate-400">
                <Box size={14} /> <span>{s.asset_count || 0} ativos</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon={Layers} title="Nenhuma área encontrada" description="Crie áreas para organizar os ativos" action={() => openModal()} actionLabel="Nova Área" />
      )}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editItem ? "Editar Área" : "Nova Área"} size="sm">
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormInput label="Código" required>
            <input type="text" value={form.codigo} onChange={e => setForm({...form, codigo: e.target.value.toUpperCase()})} placeholder="Ex: UTIL, PROD" className="input-industrial w-full px-4 font-mono" required disabled={!!editItem} data-testid="sector-codigo-input" />
          </FormInput>
          <FormInput label="Nome" required>
            <input type="text" value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} placeholder="Ex: Utilidades" className="input-industrial w-full px-4" required data-testid="sector-nome-input" />
          </FormInput>
          <FormInput label="Descrição">
            <textarea value={form.descricao} onChange={e => setForm({...form, descricao: e.target.value})} className="input-industrial w-full px-4 min-h-[60px]" data-testid="sector-desc-input" />
          </FormInput>
          <FormInput label="Cor">
            <div className="flex items-center gap-2">
              {colors.map(c => (
                <button key={c} type="button" onClick={() => setForm({...form, cor: c})} className={`w-7 h-7 rounded-full border-2 transition-all ${form.cor === c ? 'border-white scale-110' : 'border-transparent'}`} style={{ backgroundColor: c }} />
              ))}
            </div>
          </FormInput>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary" data-testid="sector-save-btn">{saving ? 'Salvando...' : 'Salvar'}</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog isOpen={!!deleteItem} onClose={() => setDeleteItem(null)} onConfirm={handleDelete} title="Excluir Área" message={`Excluir a área "${deleteItem?.nome}"? Todos os ativos precisam ser movidos antes.`} confirmText="Excluir" danger />
    </div>
  );
};


// ============== UNIDADES PAGE ==============

const UnidadesPage = () => {
  const [unidades, setUnidades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const [form, setForm] = useState({ codigo: '', nome: '', descricao: '', endereco: '' });
  const [saving, setSaving] = useState(false);
  const { user } = useAuth();

  const fetchData = async () => {
    try {
      const res = await api.get('/unidades');
      setUnidades(res.data);
    } catch { toast.error('Erro ao carregar unidades'); }
    finally { setLoading(false); }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchData(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editItem) {
        await api.put(`/unidades/${editItem.id}`, form);
        toast.success('Unidade atualizada!');
      } else {
        await api.post('/unidades', form);
        toast.success('Unidade criada!');
      }
      setShowModal(false);
      setEditItem(null);
      setForm({ codigo: '', nome: '', descricao: '', endereco: '' });
      fetchData();
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/unidades/${deleteItem.id}`);
      toast.success('Unidade excluída!');
      setDeleteItem(null);
      fetchData();
    } catch (err) { toast.error(normalizeError(err)); }
  };

  return (
    <div className="space-y-4" data-testid="unidades-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Unidades</h1>
        {['admin','master'].includes(user?.role) && (
          <button onClick={() => { setEditItem(null); setForm({ codigo: '', nome: '', descricao: '', endereco: '' }); setShowModal(true); }} className="btn-primary flex items-center gap-2" data-testid="add-unidade-btn">
            <Plus size={20} /> Nova Unidade
          </button>
        )}
      </div>
      {loading ? <Loading rows={3} /> : unidades.length > 0 ? (
        <div className="space-y-2">
          {unidades.map(p => (
            <div key={p.id} className="glass-card p-4 hover:border-slate-600 transition-all group" data-testid={`unidade-card-${p.codigo}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-500/10"><Factory size={22} className="text-blue-400" /></div>
                  <div>
                    <span className="font-mono text-blue-400 text-sm">{p.codigo}</span>
                    <p className="text-slate-100 font-medium">{p.nome}</p>
                    {p.descricao && <p className="text-xs text-slate-500">{p.descricao}</p>}
                    {p.endereco && <p className="text-xs text-slate-600"><MapPin size={10} className="inline mr-1" />{p.endereco}</p>}
                  </div>
                </div>
                {['admin','master'].includes(user?.role) && (
                  <div className="hidden group-hover:flex items-center gap-1">
                    <button onClick={() => { setEditItem(p); setForm({ codigo: p.codigo, nome: p.nome, descricao: p.descricao || '', endereco: p.endereco || '' }); setShowModal(true); }} className="p-2 hover:bg-slate-700 rounded-lg"><Edit size={16} className="text-slate-400" /></button>
                    <button onClick={() => setDeleteItem(p)} className="p-2 hover:bg-red-500/10 rounded-lg"><Trash2 size={16} className="text-red-400" /></button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon={Factory} title="Nenhuma unidade cadastrada" description="Crie a primeira unidade da organização." action={() => setShowModal(true)} actionLabel="Nova Unidade" />
      )}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editItem ? 'Editar Unidade' : 'Nova Unidade'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormInput label="Código" required>
            <input value={form.codigo} onChange={e => setForm({...form, codigo: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: CEDRO" required data-testid="unidade-codigo-input" />
          </FormInput>
          <FormInput label="Nome" required>
            <input value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: Unidade Cedro" required data-testid="unidade-nome-input" />
          </FormInput>
          <FormInput label="Descrição">
            <textarea value={form.descricao} onChange={e => setForm({...form, descricao: e.target.value})} className="input-industrial w-full px-4 min-h-[60px]" />
          </FormInput>
          <FormInput label="Endereço">
            <input value={form.endereco} onChange={e => setForm({...form, endereco: e.target.value})} className="input-industrial w-full px-4" placeholder="Localização física" />
          </FormInput>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary" data-testid="unidade-save-btn">{saving ? 'Salvando...' : 'Salvar'}</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog isOpen={!!deleteItem} onClose={() => setDeleteItem(null)} onConfirm={handleDelete} title="Excluir Unidade" message={`Excluir a unidade "${deleteItem?.nome}"?`} confirmText="Excluir" danger />
    </div>
  );
};


// ============== BIBLIOTECA DE MODELOS PAGE ==============

const BibliotecaPage = () => {
  const [tab, setTab] = useState('categorias');
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [categorias, setCategorias] = useState([]);
  const [fabricantes, setFabricantes] = useState([]);
  const { user } = useAuth();

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = search ? `?search=${search}` : '';
      const res = await api.get(`/biblioteca/${tab}${params}`);
      setItems(res.data.items || res.data);
      setTotal(res.data.total || (res.data.items || res.data).length);
      if (tab === 'modelos-mestre' || tab === 'fabricantes') {
        const catRes = await api.get('/biblioteca/categorias');
        setCategorias(catRes.data.items || []);
      }
      if (tab === 'modelos-mestre') {
        const fabRes = await api.get('/biblioteca/fabricantes');
        setFabricantes(fabRes.data.items || []);
      }
    } catch { toast.error('Erro ao carregar dados'); }
    finally { setLoading(false); }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchData(); }, [tab, search]);

  const getEmptyForm = () => {
    if (tab === 'categorias') return { nome: '', descricao: '' };
    if (tab === 'fabricantes') return { nome: '', descricao: '', categoria_id: '', pais: '', website: '' };
    return { nome: '', modelo: '', categoria_id: '', fabricante_id: '', descricao: '' };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editItem) {
        await api.put(`/biblioteca/${tab}/${editItem.id}`, form);
        toast.success('Atualizado!');
      } else {
        await api.post(`/biblioteca/${tab}`, form);
        toast.success('Criado!');
      }
      setShowModal(false); setEditItem(null); setForm(getEmptyForm());
      fetchData();
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/biblioteca/${tab}/${deleteItem.id}`);
      toast.success('Excluído!');
      setDeleteItem(null);
      fetchData();
    } catch (err) { toast.error(normalizeError(err)); }
  };

  const tabs = [
    { id: 'categorias', label: 'Categorias', icon: Layers },
    { id: 'fabricantes', label: 'Fabricantes', icon: Factory },
    { id: 'modelos-mestre', label: 'Modelos Mestres', icon: BookOpen },
  ];

  return (
    <div className="space-y-4" data-testid="biblioteca-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Biblioteca de Modelos</h1>
        <button onClick={() => { setEditItem(null); setForm(getEmptyForm()); setShowModal(true); }} className="btn-primary flex items-center gap-2" data-testid="biblioteca-add-btn">
          <Plus size={20} /> Novo
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-800 pb-1">
        {tabs.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} onClick={() => { setTab(t.id); setSearch(''); }}
              className={`px-4 py-2 rounded-t-lg text-xs font-medium flex items-center gap-2 transition-all ${tab === t.id ? 'bg-slate-800 text-brand border-b-2 border-brand' : 'text-slate-500 hover:text-slate-300'}`}
              data-testid={`bib-tab-${t.id}`}
            ><Icon size={14} />{t.label}</button>
          );
        })}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar..." className="input-industrial w-full pl-9 pr-4 text-sm" data-testid="bib-search" />
      </div>

      <p className="text-xs text-slate-600">{total} registro(s)</p>

      {/* List */}
      {loading ? <Loading rows={5} /> : items.length > 0 ? (
        <div className="space-y-2">
          {items.map(item => (
            <div key={item.id} className="glass-card p-4 hover:border-slate-600 transition-all group">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-brand-10"><BookOpen size={20} className="text-brand" /></div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-brand text-xs">{item.codigo}</span>
                      {item.status === 'inativo' && <span className="text-[9px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/30">Inativo</span>}
                    </div>
                    <p className="text-slate-100 font-medium">{item.nome}</p>
                    <div className="flex gap-2 text-xs text-slate-500 mt-0.5">
                      {item.categoria_nome && <span className="bg-slate-800 px-1.5 py-0.5 rounded">{item.categoria_nome}</span>}
                      {item.fabricante_nome && <span className="bg-slate-800 px-1.5 py-0.5 rounded">{item.fabricante_nome}</span>}
                      {item.modelo && <span>Modelo: {item.modelo}</span>}
                      {item.versao && <span>v{item.versao}</span>}
                      {item.planos?.length > 0 && <span className="text-blue-400">{item.planos.length} plano(s)</span>}
                    </div>
                  </div>
                </div>
                <div className="hidden group-hover:flex items-center gap-1">
                  <button onClick={() => { setEditItem(item); setForm(tab === 'categorias' ? { nome: item.nome, descricao: item.descricao || '' } : tab === 'fabricantes' ? { nome: item.nome, descricao: item.descricao || '', categoria_id: item.categoria_id || '', pais: item.pais || '', website: item.website || '' } : { nome: item.nome, modelo: item.modelo || '', categoria_id: item.categoria_id || '', fabricante_id: item.fabricante_id || '', descricao: item.descricao || '' }); setShowModal(true); }} className="p-2 hover:bg-slate-700 rounded-lg"><Edit size={16} className="text-slate-400" /></button>
                  <button onClick={() => setDeleteItem(item)} className="p-2 hover:bg-red-500/10 rounded-lg"><Trash2 size={16} className="text-red-400" /></button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon={BookOpen} title={`Nenhum registro em ${tab}`} description="Crie o primeiro item." action={() => { setForm(getEmptyForm()); setShowModal(true); }} actionLabel="Criar" />
      )}

      {/* Modal */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editItem ? `Editar ${tab === 'categorias' ? 'Categoria' : tab === 'fabricantes' ? 'Fabricante' : 'Modelo Mestre'}` : `Novo ${tab === 'categorias' ? 'Categoria' : tab === 'fabricantes' ? 'Fabricante' : 'Modelo Mestre'}`}>
        <form onSubmit={handleSubmit} className="space-y-3">
          <FormInput label="Nome" required><input value={form.nome || ''} onChange={e => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-4" required data-testid="bib-nome" /></FormInput>
          {tab === 'fabricantes' && (
            <>
              <FormInput label="Categoria"><select value={form.categoria_id || ''} onChange={e => setForm({...form, categoria_id: e.target.value})} className="input-industrial w-full px-4"><option value="">Selecione...</option>{categorias.map(c => <option key={c.id} value={c.id}>{c.nome}</option>)}</select></FormInput>
              <FormInput label="País"><input value={form.pais || ''} onChange={e => setForm({...form, pais: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
            </>
          )}
          {tab === 'modelos-mestre' && (
            <>
              <FormInput label="Modelo"><input value={form.modelo || ''} onChange={e => setForm({...form, modelo: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: C125" data-testid="bib-modelo" /></FormInput>
              <FormInput label="Categoria"><select value={form.categoria_id || ''} onChange={e => setForm({...form, categoria_id: e.target.value})} className="input-industrial w-full px-4"><option value="">Selecione...</option>{categorias.map(c => <option key={c.id} value={c.id}>{c.nome}</option>)}</select></FormInput>
              <FormInput label="Fabricante"><select value={form.fabricante_id || ''} onChange={e => setForm({...form, fabricante_id: e.target.value})} className="input-industrial w-full px-4"><option value="">Selecione...</option>{fabricantes.map(f => <option key={f.id} value={f.id}>{f.nome}</option>)}</select></FormInput>
            </>
          )}
          <FormInput label="Descrição"><textarea value={form.descricao || ''} onChange={e => setForm({...form, descricao: e.target.value})} className="input-industrial w-full px-4 min-h-[60px]" /></FormInput>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary" data-testid="bib-save">{saving ? 'Salvando...' : 'Salvar'}</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog isOpen={!!deleteItem} onClose={() => setDeleteItem(null)} onConfirm={handleDelete} title="Excluir" message={`Excluir "${deleteItem?.nome}"? Esta ação não poderá ser desfeita.`} confirmText="Excluir" danger />
    </div>
  );
};


// ============== EQUIPE PAGE (Dashboard + Ranking + Produtividade) ==============

const EquipePage = () => {
  const [periodo, setPeriodo] = useState('semana');
  const [metricas, setMetricas] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  const fetchMetricas = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/metricas/equipe?periodo=${periodo}`);
      setMetricas(res.data);
    } catch { toast.error('Erro ao carregar métricas'); }
    finally { setLoading(false); }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchMetricas(); }, [periodo]);

  const formatHH = (min) => { const h = Math.floor(min/60); const m = Math.round(min%60); return `${h}h${m > 0 ? m + 'm' : ''}`; };
  const totalOS = metricas.reduce((s, m) => s + (m.os_total || 0), 0);
  const totalHH = metricas.reduce((s, m) => s + (m.hh_liquida_min || 0), 0);
  const totalInsp = metricas.reduce((s, m) => s + (m.inspecoes || 0), 0);

  return (
    <div className="space-y-4" data-testid="equipe-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Equipe</h1>
        <div className="flex gap-1">
          {[{v:'hoje',l:'Hoje'},{v:'semana',l:'Semana'},{v:'mes',l:'Mês'},{v:'ano',l:'Ano'}].map(p => (
            <button key={p.v} onClick={() => setPeriodo(p.v)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${periodo === p.v ? 'bg-brand-20 text-brand border border-brand-30' : 'border border-slate-700 text-slate-500 hover:text-slate-300'}`}
              data-testid={`equipe-periodo-${p.v}`}
            >{p.l}</button>
          ))}
        </div>
      </div>

      {/* KPI Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="glass-card p-4 text-center">
          <p className="text-3xl font-bold text-brand">{metricas.length}</p>
          <p className="text-xs text-slate-500">Técnicos Ativos</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-3xl font-bold text-blue-400">{totalOS}</p>
          <p className="text-xs text-slate-500">OS Executadas</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-3xl font-bold text-amber-400">{formatHH(totalHH)}</p>
          <p className="text-xs text-slate-500">HH Total</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-3xl font-bold text-cyan-400">{totalInsp}</p>
          <p className="text-xs text-slate-500">Inspeções</p>
        </div>
      </div>

      {/* Ranking */}
      {loading ? <Loading rows={5} /> : metricas.length > 0 ? (
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Ranking — {periodo === 'hoje' ? 'Hoje' : periodo === 'semana' ? 'Semana' : periodo === 'mes' ? 'Mês' : 'Ano'}</h3>
          <div className="space-y-2">
            {metricas.slice(0, 10).map((m, idx) => {
              const maxOS = metricas[0]?.os_total || 1;
              const pct = Math.min(100, ((m.os_total || 0) / maxOS) * 100);
              const medalColors = ['text-amber-400', 'text-slate-300', 'text-amber-600'];
              const tipos = m.os_por_tipo || {};
              return (
                <div key={m.user_id} className="group" data-testid={`ranking-${idx}`}>
                  <div className="flex items-center gap-3 py-2">
                    <span className={`text-lg font-bold w-8 text-center ${medalColors[idx] || 'text-slate-600'}`}>
                      {idx < 3 ? ['1º','2º','3º'][idx] : `${idx+1}º`}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <div>
                          <span className="text-sm text-slate-200 font-medium">{m.user_nome || 'Sem nome'}</span>
                          <span className="text-[10px] text-slate-600 ml-2 capitalize">{m.user_role}</span>
                        </div>
                        <span className="text-sm font-bold text-brand">{m.os_total || 0} OS</span>
                      </div>
                      {/* Progress bar */}
                      <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-brand rounded-full transition-all" style={{width: `${pct}%`}} />
                      </div>
                      {/* Detail metrics */}
                      <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5 text-[10px] text-slate-500">
                        <span>HH: <b className="text-slate-400">{formatHH(m.hh_liquida_min || 0)}</b></span>
                        <span>Solo: <b className="text-slate-400">{m.os_solo || 0}</b></span>
                        <span>Compartilhada: <b className="text-slate-400">{m.os_compartilhada || 0}</b></span>
                        {m.inspecoes > 0 && <span>Inspeções: <b className="text-cyan-400">{m.inspecoes}</b></span>}
                        {m.tempo_medio_os_min > 0 && <span>Tempo médio: <b className="text-slate-400">{formatHH(m.tempo_medio_os_min)}</b></span>}
                        {tipos.corretiva > 0 && <span className="text-red-400/70">Corr: {tipos.corretiva}</span>}
                        {tipos.preventiva > 0 && <span className="text-blue-400/70">Prev: {tipos.preventiva}</span>}
                        {tipos.lubrificacao > 0 && <span className="text-yellow-400/70">Lub: {tipos.lubrificacao}</span>}
                        {tipos.melhoria > 0 && <span className="text-brand/70">Melh: {tipos.melhoria}</span>}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <EmptyState icon={Users} title="Sem dados para o período" description="Nenhuma métrica registrada. As métricas são geradas automaticamente conforme as OS são concluídas." />
      )}

      {/* Individual cards (for tecnico viewing their own) */}
      {user?.role === 'tecnico' && metricas.find(m => m.user_id === user?.id) && (() => {
        const my = metricas.find(m => m.user_id === user.id);
        const tipos = my.os_por_tipo || {};
        return (
          <div className="glass-card p-4 border-l-4 border-brand" data-testid="minha-performance">
            <h3 className="text-sm font-semibold text-brand mb-3">Minha Performance</h3>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div><p className="text-2xl font-bold text-slate-200">{my.os_total}</p><p className="text-[10px] text-slate-500">OS Total</p></div>
              <div><p className="text-2xl font-bold text-slate-200">{formatHH(my.hh_liquida_min || 0)}</p><p className="text-[10px] text-slate-500">HH Líquida</p></div>
              <div><p className="text-2xl font-bold text-slate-200">{my.inspecoes || 0}</p><p className="text-[10px] text-slate-500">Inspeções</p></div>
            </div>
            <div className="mt-3 grid grid-cols-4 gap-2 text-center text-[10px]">
              {Object.entries(tipos).map(([tipo, count]) => (
                <div key={tipo} className="bg-slate-800/50 rounded p-1.5">
                  <p className="text-sm font-bold text-slate-300">{count}</p>
                  <p className="text-slate-600 capitalize">{tipo.replace(/_/g,' ')}</p>
                </div>
              ))}
            </div>
          </div>
        );
      })()}
    </div>
  );
};


// ============== WHITE LABEL DESIGNER PAGE ==============

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
  return (
    <div className="rounded-lg overflow-hidden border border-slate-700" style={{ backgroundColor: t.cor_login || '#020617', minHeight: 200 }}>
      {i.wallpaper_url && (
        <div className="absolute inset-0 opacity-20" style={{ backgroundImage: `url(${i.wallpaper_url})`, backgroundSize: 'cover' }} />
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

  const loadOrgs = async () => {
    setLoading(true);
    try {
      const res = await api.get('/master/organizations');
      setOrgs(res.data);
      if (res.data.length > 0 && !selectedOrgId) {
        setSelectedOrgId(res.data[0].id);
      }
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadOrgs(); }, []);

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
          <h1 className="text-2xl font-bold text-slate-100" data-testid="wl-page-title">Designer de Marca</h1>
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


// ============== PORTAL PÚBLICO DO EQUIPAMENTO (FASE 4) ==============

const PortalPublicoPage = () => {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('info');

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API}/public/ativo/${id}`);
        setData(res.data);
      } catch (err) {
        setError(err.response?.status === 404 ? 'Equipamento não encontrado' : 'Erro ao carregar dados');
      } finally { setLoading(false); }
    })();
  }, [id]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#020617' }}>
      <Cog size={48} className="text-brand animate-spin" />
    </div>
  );

  if (error || !data) return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: '#020617' }}>
      <div className="text-center">
        <AlertCircle size={48} className="text-red-400 mx-auto mb-4" />
        <p className="text-lg text-slate-300 font-semibold">{error || 'Equipamento não encontrado'}</p>
        <p className="text-sm text-slate-500 mt-2">Verifique o QR Code e tente novamente</p>
      </div>
    </div>
  );

  const { ativo, area, branding: brand, kpis, ultimas_inspecoes, ultimas_os, ultimas_manutencoes, manuais } = data;
  const b = brand || {};
  const statusMap = { operacional: { label: 'Operacional', cls: 'bg-emerald-500/10 text-emerald-400' }, parado: { label: 'Parado', cls: 'bg-red-500/10 text-red-400' }, manutencao: { label: 'Em Manutenção', cls: 'bg-amber-500/10 text-amber-400' } };
  const st = statusMap[ativo.status] || statusMap.operacional;

  const tabs = [
    { id: 'info', label: 'Informações', icon: Box },
    { id: 'historico', label: 'Histórico', icon: Clock },
    { id: 'manuais', label: 'Manuais', icon: FileText },
  ];

  const formatDate = (d) => d ? new Date(d).toLocaleDateString('pt-BR') : '—';

  return (
    <div className="min-h-screen" style={{ backgroundColor: b.cor_fundo || '#020617' }} data-testid="portal-publico">
      {/* Header */}
      <div className="border-b border-slate-800" style={{ backgroundColor: b.cor_menu || '#0f172a' }}>
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          {b.logo_url ? (
            <img src={b.logo_url?.startsWith('http') ? b.logo_url : `${BACKEND_URL}${b.logo_url}`} alt="" className="h-8 object-contain" />
          ) : (
            <span className="font-bold text-sm" style={{ color: b.cor_primaria || '#10b981' }}>{b.nome_empresa || 'CMMS'}</span>
          )}
          <span className="text-[10px] text-slate-500 uppercase tracking-wider">Portal do Equipamento</span>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-5">
        {/* Hero */}
        <div className="glass-card p-5">
          <div className="flex items-start gap-4">
            {ativo.foto_url ? (
              <img src={ativo.foto_url.startsWith('http') ? ativo.foto_url : `${BACKEND_URL}${ativo.foto_url}`}
                alt="" className="w-20 h-20 rounded-xl object-cover border border-slate-700 shrink-0" />
            ) : (
              <div className="w-20 h-20 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: `${b.cor_primaria || '#10b981'}15`, border: `1px solid ${b.cor_primaria || '#10b981'}30` }}>
                <Cog size={32} style={{ color: b.cor_primaria || '#10b981' }} />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="font-mono text-lg font-bold" style={{ color: b.cor_primaria || '#10b981' }} data-testid="portal-tag">{ativo.tag}</p>
              <h1 className="text-xl font-bold text-slate-100" data-testid="portal-nome">{ativo.nome}</h1>
              <p className="text-sm text-slate-400 mt-1">{ativo.tipo_equipamento}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${st.cls}`}>{st.label}</span>
                {area && <span className="text-xs text-slate-500"><MapPin size={12} className="inline mr-1" />{area}</span>}
              </div>
            </div>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-3 gap-3">
          <div className="glass-card p-3 text-center">
            <p className="text-2xl font-bold" style={{ color: b.cor_primaria || '#10b981' }}>{kpis.disponibilidade || 100}%</p>
            <p className="text-[10px] text-slate-500 uppercase">Disponibilidade</p>
          </div>
          <div className="glass-card p-3 text-center">
            <p className="text-2xl font-bold text-slate-100">{kpis.total_os}</p>
            <p className="text-[10px] text-slate-500 uppercase">Total OS</p>
          </div>
          <div className="glass-card p-3 text-center">
            <p className="text-2xl font-bold text-slate-100">{kpis.total_inspecoes}</p>
            <p className="text-[10px] text-slate-500 uppercase">Inspeções</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-900/50 rounded-lg p-1">
          {tabs.map(t => {
            const Icon = t.icon;
            return (
              <button key={t.id} onClick={() => setActiveTab(t.id)}
                className={`flex-1 px-3 py-2 rounded-md text-xs font-medium flex items-center justify-center gap-1.5 transition-all ${
                  activeTab === t.id ? 'bg-brand-20 text-brand' : 'text-slate-400'
                }`} data-testid={`portal-tab-${t.id}`}>
                <Icon size={14} /> {t.label}
              </button>
            );
          })}
        </div>

        {/* Tab: Info */}
        {activeTab === 'info' && (
          <div className="glass-card divide-y divide-slate-800" data-testid="portal-info-tab">
            {[
              ['Fabricante', ativo.fabricante],
              ['Modelo', ativo.modelo],
              ['Nº Série', ativo.numero_serie],
              ['Criticidade', ativo.criticidade],
              ['Área', area],
              ['Tipo', ativo.tipo_equipamento],
            ].filter(([,v]) => v).map(([label, value]) => (
              <div key={label} className="flex items-center justify-between px-4 py-3">
                <span className="text-sm text-slate-500">{label}</span>
                <span className="text-sm text-slate-200 font-medium">{value}</span>
              </div>
            ))}
          </div>
        )}

        {/* Tab: Histórico */}
        {activeTab === 'historico' && (
          <div className="space-y-3" data-testid="portal-historico-tab">
            {ultimas_inspecoes?.length > 0 && (
              <div className="glass-card p-4">
                <h3 className="section-title mb-3"><ClipboardCheck size={14} /> Últimas Inspeções</h3>
                <div className="space-y-2">
                  {ultimas_inspecoes.map((insp, i) => (
                    <div key={i} className="flex items-center justify-between text-sm p-2 rounded-lg bg-slate-900/50">
                      <div>
                        <p className="text-slate-200">{insp.plano_nome || insp.tipo || 'Inspeção'}</p>
                        <p className="text-[10px] text-slate-500">{formatDate(insp.data_conclusao || insp.created_at)}</p>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${insp.resultado === 'conforme' ? 'bg-emerald-500/10 text-emerald-400' : insp.resultado === 'nao_conforme' ? 'bg-red-500/10 text-red-400' : 'bg-slate-700 text-slate-400'}`}>
                        {insp.resultado || insp.status || '—'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {ultimas_os?.length > 0 && (
              <div className="glass-card p-4">
                <h3 className="section-title mb-3"><Wrench size={14} /> Últimas Ordens de Serviço</h3>
                <div className="space-y-2">
                  {ultimas_os.map((os, i) => (
                    <div key={i} className="flex items-center justify-between text-sm p-2 rounded-lg bg-slate-900/50">
                      <div>
                        <p className="text-slate-200">{os.titulo || os.tipo}</p>
                        <p className="text-[10px] text-slate-500">{os.numero && `#${os.numero} • `}{formatDate(os.data_conclusao || os.created_at)}</p>
                      </div>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-400">{os.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {(!ultimas_inspecoes?.length && !ultimas_os?.length) && (
              <div className="glass-card p-8 text-center">
                <Clock size={32} className="text-slate-600 mx-auto mb-2" />
                <p className="text-slate-500 text-sm">Nenhum histórico disponível</p>
              </div>
            )}
          </div>
        )}

        {/* Tab: Manuais */}
        {activeTab === 'manuais' && (
          <div className="space-y-2" data-testid="portal-manuais-tab">
            {manuais?.length > 0 ? manuais.map(m => (
              <a key={m.id} href={m.url?.startsWith('http') ? m.url : `${BACKEND_URL}${m.url}`}
                target="_blank" rel="noopener noreferrer"
                className="glass-card p-4 flex items-center gap-3 hover:border-brand transition-all block">
                <FileText size={20} style={{ color: b.cor_primaria || '#10b981' }} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-200 truncate">{m.nome || 'Manual'}</p>
                  <p className="text-[10px] text-slate-500">{m.tipo_arquivo || 'PDF'}</p>
                </div>
                <Download size={16} className="text-slate-500" />
              </a>
            )) : (
              <div className="glass-card p-8 text-center">
                <FileText size={32} className="text-slate-600 mx-auto mb-2" />
                <p className="text-slate-500 text-sm">Nenhum manual disponível</p>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="text-center pt-4 pb-8">
          {b.mostrar_powered_by && <p className="text-[10px] text-slate-700">Powered by MAINTRIX</p>}
        </div>
      </div>
    </div>
  );
};


// ============== PORTAL DO TÉCNICO (FASE 5) ==============

const PortalTecnicoPage = () => {
  const { id } = useParams();
  const [ativo, setAtivo] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { user } = useAuth();
  const { branding } = useBranding() || {};
  const b = branding || {};

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get(`/ativos/${id}`);
        setAtivo(res.data);
      } catch { toast.error('Ativo não encontrado'); navigate('/'); }
      finally { setLoading(false); }
    })();
  }, [id, navigate]);

  if (loading) return <Loading rows={4} />;
  if (!ativo) return null;

  const quickActions = [
    { icon: ClipboardCheck, label: 'Executar Inspeção', desc: 'Iniciar inspeção neste equipamento', action: () => navigate(`/inspecoes?ativo_id=${id}`) },
    { icon: Wrench, label: 'Solicitar Serviço', desc: 'Criar solicitação de manutenção', action: () => navigate(`/solicitar?ativo_id=${id}&ativo_tag=${ativo.tag}&ativo_nome=${ativo.nome}`) },
    { icon: AlertTriangle, label: 'Registrar Problema', desc: 'Reportar problema encontrado', action: () => navigate(`/solicitar?ativo_id=${id}&ativo_tag=${ativo.tag}`) },
    { icon: Camera, label: 'Adicionar Fotos', desc: 'Registrar foto do equipamento', action: () => navigate(`/ativos/${id}?tab=docs`) },
    { icon: Clock, label: 'Registrar HH', desc: 'Apontar hora trabalhada', action: () => navigate(`/os?ativo_id=${id}`) },
    { icon: Eye, label: 'Ver Prontuário', desc: 'Prontuário completo do ativo', action: () => navigate(`/ativos/${id}`) },
  ];

  return (
    <div className="space-y-5 animate-fadeInUp" data-testid="portal-tecnico">
      {/* Header */}
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <button onClick={() => navigate(-1)} className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg"><ArrowLeft size={18} className="text-slate-400" /></button>
          <h1 className="text-lg font-bold text-slate-100">Portal do Técnico</h1>
        </div>
        <div className="flex items-start gap-4">
          {ativo.foto_url ? (
            <img src={ativo.foto_url.startsWith('http') ? ativo.foto_url : `${BACKEND_URL}${ativo.foto_url}`}
              alt="" className="w-16 h-16 rounded-xl object-cover border border-slate-700 shrink-0" />
          ) : (
            <div className="w-16 h-16 rounded-xl bg-brand-20 flex items-center justify-center border border-slate-700 shrink-0">
              <Cog size={28} className="text-brand" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="font-mono text-brand text-lg font-bold">{ativo.tag}</p>
            <h2 className="text-lg text-slate-200 font-semibold">{ativo.nome}</h2>
            <p className="text-sm text-slate-500">{ativo.sector?.nome || ''} {ativo.tipo_equipamento ? `• ${ativo.tipo_equipamento}` : ''}</p>
          </div>
        </div>
      </div>

      {/* Quick Actions Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3" data-testid="portal-tecnico-actions">
        {quickActions.map((action, idx) => {
          const Icon = action.icon;
          return (
            <button key={idx} onClick={action.action}
              className="glass-card p-4 text-left hover:border-brand transition-all active:scale-[0.98] group"
              data-testid={`portal-action-${idx}`}>
              <div className="w-10 h-10 rounded-lg bg-brand-10 flex items-center justify-center mb-3 group-hover:bg-brand-20 transition-colors">
                <Icon size={20} className="text-brand" />
              </div>
              <p className="text-sm font-semibold text-slate-200">{action.label}</p>
              <p className="text-[10px] text-slate-500 mt-0.5">{action.desc}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
};


// ============== MASTER CLEANUP PAGE ==============

const MasterCleanupPage = () => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [adminActions, setAdminActions] = useState([]);
  const [confirmProd, setConfirmProd] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const { user } = useAuth();

  const fetchActions = async () => {
    try {
      const res = await api.get('/master/admin-actions');
      setAdminActions(res.data);
    } catch {}
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchActions(); }, []);

  const cleanableItems = [
    { key: 'ordens_servico', label: 'Ordens de Serviço', icon: Wrench },
    { key: 'inspecoes', label: 'Inspeções', icon: ClipboardCheck },
    { key: 'anomalias', label: 'Anomalias', icon: AlertTriangle },
    { key: 'paradas_programadas', label: 'Paradas Programadas', icon: Calendar },
    { key: 'audit_logs', label: 'Auditoria', icon: Shield },
    { key: 'notificacoes', label: 'Notificações', icon: Bell },
    { key: 'movimentacoes_estoque', label: 'Movimentações de Estoque', icon: Package },
    { key: 'attachments', label: 'Fotos e Uploads', icon: Image },
    { key: 'chat_history', label: 'Histórico de Chat', icon: FileText },
    { key: 'anomalia_historico', label: 'Histórico de Anomalias', icon: Activity },
    { key: 'anomalia_comentarios', label: 'Comentários de Anomalias', icon: FileText },
    { key: 'os_materiais', label: 'Materiais Utilizados em OS', icon: Package },
  ];

  const [selected, setSelected] = useState([]);

  const toggleSelect = (key) => {
    setSelected(prev => prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]);
  };

  const handleCleanup = async () => {
    if (selected.length === 0) { toast.error('Selecione pelo menos um item'); return; }
    setLoading(true);
    try {
      const res = await api.post(`/master/cleanup?${selected.map(s => `targets=${s}`).join('&')}`);
      setResults(res.data.deleted);
      toast.success('Limpeza concluída!');
      fetchActions();
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setLoading(false); }
  };

  const handlePrepareProduction = async () => {
    if (confirmText !== 'PREPARAR PRODUCAO') { toast.error('Digite exatamente: PREPARAR PRODUCAO'); return; }
    setLoading(true);
    try {
      const res = await api.post('/master/prepare-production');
      setResults(res.data.deleted);
      toast.success('Ambiente preparado para produção!');
      setConfirmProd(false);
      setConfirmText('');
      fetchActions();
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setLoading(false); }
  };

  if (user?.role !== 'master') return <div className="text-center text-red-400 mt-10">Acesso restrito ao Administrador Master.</div>;

  return (
    <div className="space-y-6" data-testid="master-cleanup-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Limpeza do Ambiente</h1>
          <p className="text-xs text-slate-500 mt-1">Remova dados de teste para preparar o ambiente de produção</p>
        </div>
        <button onClick={() => setConfirmProd(true)} className="px-4 py-2 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 text-sm font-medium hover:bg-red-500/30 transition-all" data-testid="prepare-production-btn">
          Preparar Ambiente para Produção
        </button>
      </div>

      {/* Selective cleanup */}
      <div className="glass-card p-4">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">Selecionar dados para limpar:</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          {cleanableItems.map(item => {
            const Icon = item.icon;
            const isSelected = selected.includes(item.key);
            return (
              <button key={item.key} onClick={() => toggleSelect(item.key)}
                className={`flex items-center gap-2 p-3 rounded-lg border text-left text-sm transition-all ${isSelected ? 'bg-red-500/10 border-red-500/30 text-red-300' : 'border-slate-700 text-slate-400 hover:border-slate-600'}`}
                data-testid={`cleanup-${item.key}`}
              >
                {isSelected ? <CheckSquare size={16} className="text-red-400 shrink-0" /> : <Square size={16} className="text-slate-600 shrink-0" />}
                <Icon size={14} className="shrink-0" />
                {item.label}
              </button>
            );
          })}
        </div>
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs text-slate-600">{selected.length} item(ns) selecionado(s)</p>
          <button onClick={handleCleanup} disabled={loading || selected.length === 0}
            className="px-4 py-2 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-medium hover:bg-red-500/30 disabled:opacity-50 transition-all" data-testid="cleanup-execute-btn">
            {loading ? 'Limpando...' : 'Executar Limpeza'}
          </button>
        </div>
      </div>

      {/* Results */}
      {results && (
        <div className="glass-card p-4" data-testid="cleanup-results">
          <h3 className="text-sm font-semibold text-brand mb-2">Resultado da Limpeza:</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {Object.entries(results).map(([key, count]) => (
              <div key={key} className="bg-slate-800/50 rounded-lg p-2 text-center">
                <p className="text-lg font-bold text-slate-200">{count}</p>
                <p className="text-[10px] text-slate-500 capitalize">{key.replace(/_/g, ' ')}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Admin actions log */}
      {adminActions.length > 0 && (
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-2">Histórico de Ações Administrativas</h3>
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {adminActions.map(a => (
              <div key={a.id} className="flex items-center justify-between py-2 border-b border-slate-800/50 last:border-0 text-xs">
                <div>
                  <span className="text-slate-400 font-medium">{a.user_nome}</span>
                  <span className="text-slate-600 mx-1">—</span>
                  <span className={`font-medium ${a.action === 'prepare_production' ? 'text-red-400' : 'text-amber-400'}`}>{a.action === 'prepare_production' ? 'Preparação Produção' : 'Limpeza'}</span>
                </div>
                <span className="text-slate-600">{new Date(a.created_at).toLocaleString('pt-BR')}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Prepare production confirmation modal */}
      <Modal isOpen={confirmProd} onClose={() => { setConfirmProd(false); setConfirmText(''); }} title="Preparar Ambiente para Produção">
        <div className="space-y-4">
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p className="text-sm text-red-300 font-medium">Esta ação não poderá ser desfeita.</p>
            <p className="text-xs text-red-400/80 mt-1">Todos os dados operacionais (OS, inspeções, anomalias, paradas, auditoria, fotos, notificações) serão permanentemente excluídos. Usuários, áreas, ativos, materiais e planos serão mantidos.</p>
          </div>
          <FormInput label="Para confirmar, digite: PREPARAR PRODUCAO">
            <input value={confirmText} onChange={e => setConfirmText(e.target.value)} className="input-industrial w-full px-4" placeholder="PREPARAR PRODUCAO" data-testid="confirm-production-input" />
          </FormInput>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setConfirmProd(false); setConfirmText(''); }} className="btn-secondary">Cancelar</button>
            <button onClick={handlePrepareProduction} disabled={loading || confirmText !== 'PREPARAR PRODUCAO'}
              className="px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-500 disabled:opacity-50 transition-all" data-testid="confirm-production-btn">
              {loading ? 'Processando...' : 'Confirmar'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};



// ============== ORG CONFIG PAGE ==============

const OrgConfigPage = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('identidade');
  const [saving, setSaving] = useState(false);
  const [numPreview, setNumPreview] = useState('');
  const { user } = useAuth();

  const fetchConfig = async () => {
    try {
      const res = await api.get('/org/config');
      setConfig(res.data);
    } catch { toast.error('Erro ao carregar configurações'); }
    finally { setLoading(false); }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchConfig(); }, []);

  const updateSection = async (section, data) => {
    setSaving(true);
    try {
      await api.put(`/org/config/${section}`, data);
      toast.success('Configurações salvas!');
      fetchConfig();
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setSaving(false); }
  };

  const fetchPreview = async (entidade, tipo) => {
    try {
      const res = await api.get(`/org/config/numeracao/preview?entidade=${entidade}&tipo=${tipo}`);
      setNumPreview(res.data.preview);
    } catch { setNumPreview(''); }
  };

  if (loading) return <Loading rows={5} />;
  if (!config) return <div className="text-red-400">Erro ao carregar configurações</div>;

  const tabs = [
    { id: 'identidade', label: 'Identidade', icon: Building2 },
    { id: 'tema', label: 'Tema', icon: Palette },
    { id: 'terminologia', label: 'Terminologia', icon: FileText },
    { id: 'numeracao', label: 'Numeração', icon: Hash },
    { id: 'preferencias', label: 'Preferências', icon: Settings },
  ];

  return (
    <div className="space-y-4" data-testid="org-config-page">
      <h1 className="text-2xl font-bold text-slate-100">Configurações da Organização</h1>
      
      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto hide-scrollbar border-b border-slate-800 pb-1">
        {tabs.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              className={`px-4 py-2 rounded-t-lg text-xs font-medium flex items-center gap-2 whitespace-nowrap transition-all ${activeTab === t.id ? 'bg-slate-800 text-brand border-b-2 border-brand' : 'text-slate-500 hover:text-slate-300'}`}
              data-testid={`config-tab-${t.id}`}
            ><Icon size={14} />{t.label}</button>
          );
        })}
      </div>

      {/* Identity Tab */}
      {activeTab === 'identidade' && (
        <IdentidadeTab config={config} onSave={(data) => updateSection('identidade', data)} saving={saving} />
      )}

      {/* Theme Tab */}
      {activeTab === 'tema' && (
        <TemaTab config={config} onSave={(data) => updateSection('tema', data)} saving={saving} />
      )}

      {/* Terminology Tab */}
      {activeTab === 'terminologia' && (
        <TerminologiaTab config={config} onSave={(data) => updateSection('terminologia', data)} saving={saving} />
      )}

      {/* Numbering Tab */}
      {activeTab === 'numeracao' && (
        <NumeracaoTab config={config} onSave={(data) => updateSection('numeracao', data)} saving={saving} onPreview={fetchPreview} preview={numPreview} />
      )}

      {/* Preferences Tab */}
      {activeTab === 'preferencias' && (
        <PreferenciasTab config={config} onSave={(data) => updateSection('preferencias', data)} saving={saving} />
      )}
    </div>
  );
};

// Sub-tabs as small components
const IdentidadeTab = ({ config, onSave, saving }) => {
  const [form, setForm] = useState(config?.identidade || {});
  return (
    <div className="glass-card p-4 space-y-4">
      <FormInput label="Nome do Sistema"><input value={form.nome_sistema || ''} onChange={e => setForm({...form, nome_sistema: e.target.value})} className="input-industrial w-full px-4" data-testid="config-nome-sistema" /></FormInput>
      <FormInput label="Subtítulo"><input value={form.subtitulo || ''} onChange={e => setForm({...form, subtitulo: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
      <FormInput label="Rodapé"><input value={form.rodape || ''} onChange={e => setForm({...form, rodape: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
      <FormInput label="Texto Institucional"><textarea value={form.texto_institucional || ''} onChange={e => setForm({...form, texto_institucional: e.target.value})} className="input-industrial w-full px-4 min-h-[80px]" /></FormInput>
      <div className="flex justify-end"><button onClick={() => onSave(form)} disabled={saving} className="btn-primary" data-testid="config-save-identidade">{saving ? 'Salvando...' : 'Salvar'}</button></div>
    </div>
  );
};

const TemaTab = ({ config, onSave, saving }) => {
  const [form, setForm] = useState(config?.tema || {});
  const cores = [
    { key: 'cor_primaria', label: 'Cor Primária' },
    { key: 'cor_secundaria', label: 'Cor Secundária' },
    { key: 'cor_fundo', label: 'Cor de Fundo' },
    { key: 'cor_texto', label: 'Cor de Texto' },
    { key: 'cor_destaque', label: 'Cor de Destaque' },
    { key: 'cor_sucesso', label: 'Cor de Sucesso' },
    { key: 'cor_alerta', label: 'Cor de Alerta' },
    { key: 'cor_erro', label: 'Cor de Erro' },
  ];
  return (
    <div className="glass-card p-4 space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {cores.map(c => (
          <div key={c.key}>
            <label className="text-xs text-slate-400 mb-1 block">{c.label}</label>
            <div className="flex items-center gap-2">
              <input type="color" value={form[c.key] || '#000000'} onChange={e => setForm({...form, [c.key]: e.target.value})} className="w-10 h-8 rounded border border-slate-700 cursor-pointer" data-testid={`config-color-${c.key}`} />
              <input value={form[c.key] || ''} onChange={e => setForm({...form, [c.key]: e.target.value})} className="input-industrial flex-1 px-2 text-xs font-mono" />
            </div>
          </div>
        ))}
      </div>
      {/* Preview */}
      <div className="p-4 rounded-lg border border-slate-700" style={{backgroundColor: form.cor_fundo, color: form.cor_texto}}>
        <p className="text-sm font-bold" style={{color: form.cor_primaria}}>Preview do Tema</p>
        <p className="text-xs mt-1">Texto normal com <span style={{color: form.cor_destaque}}>destaque</span>, <span style={{color: form.cor_sucesso}}>sucesso</span>, <span style={{color: form.cor_alerta}}>alerta</span> e <span style={{color: form.cor_erro}}>erro</span></p>
        <button className="mt-2 px-3 py-1 rounded text-xs text-white" style={{backgroundColor: form.cor_primaria}}>Botão Primário</button>
        <button className="mt-2 ml-2 px-3 py-1 rounded text-xs text-white" style={{backgroundColor: form.cor_secundaria}}>Botão Secundário</button>
      </div>
      <div className="flex justify-end"><button onClick={() => onSave(form)} disabled={saving} className="btn-primary" data-testid="config-save-tema">{saving ? 'Salvando...' : 'Salvar'}</button></div>
    </div>
  );
};

const TerminologiaTab = ({ config, onSave, saving }) => {
  const [form, setForm] = useState(config?.terminologia || {});
  const [search, setSearch] = useState('');
  const entries = Object.entries(form).filter(([k]) => !search || k.includes(search.toLowerCase()));
  return (
    <div className="glass-card p-4 space-y-3">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar termo..." className="input-industrial w-full pl-9 pr-4 text-sm" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-[400px] overflow-y-auto">
        {entries.map(([key, value]) => (
          <div key={key} className="flex items-center gap-2">
            <span className="text-[10px] text-slate-600 font-mono w-32 shrink-0 truncate">{key}</span>
            <input value={value} onChange={e => setForm({...form, [key]: e.target.value})} className="input-industrial flex-1 px-3 text-sm" data-testid={`term-${key}`} />
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-600">{entries.length} termos</p>
      <div className="flex justify-end"><button onClick={() => onSave(form)} disabled={saving} className="btn-primary" data-testid="config-save-terminologia">{saving ? 'Salvando...' : 'Salvar'}</button></div>
    </div>
  );
};

const NumeracaoTab = ({ config, onSave, saving, onPreview, preview }) => {
  const [form, setForm] = useState(config?.numeracao || {});
  const [prefixo, setPrefixo] = useState(config?.preferencias?.prefixo_empresa || '');
  const entidades = ['ordens_servico', 'inspecoes', 'anomalias', 'lubrificacoes', 'paradas_programadas'];
  
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { onPreview('ordens_servico', 'corretiva'); }, []);
  
  return (
    <div className="glass-card p-4 space-y-4">
      <FormInput label="Prefixo da Empresa">
        <input value={prefixo} onChange={e => setPrefixo(e.target.value)} className="input-industrial w-full px-4" placeholder="AST" data-testid="config-prefixo" />
        <p className="text-xs text-slate-600 mt-1">Será usado em todos os códigos operacionais</p>
      </FormInput>
      <div className="space-y-3">
        {entidades.map(ent => {
          const cfg = form[ent] || {};
          return (
            <div key={ent} className="p-3 bg-slate-800/50 rounded-lg">
              <p className="text-xs text-slate-400 font-medium capitalize mb-2">{ent.replace(/_/g, ' ')}</p>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-600">Padrão</label>
                  <input value={cfg.prefixo || ''} onChange={e => setForm({...form, [ent]: {...cfg, prefixo: e.target.value}})} className="input-industrial w-full px-2 text-xs font-mono" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-600">Dígitos</label>
                  <input type="number" min={3} max={10} value={cfg.digitos || 6} onChange={e => setForm({...form, [ent]: {...cfg, digitos: parseInt(e.target.value)}})} className="input-industrial w-full px-2 text-xs" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {preview && <div className="p-3 bg-brand-10 border border-brand-30 rounded-lg"><p className="text-xs text-slate-400">Preview:</p><p className="text-lg font-mono text-brand">{preview}</p></div>}
      <div className="flex justify-end gap-2">
        <button onClick={() => onPreview('ordens_servico', 'corretiva')} className="btn-secondary text-xs">Atualizar Preview</button>
        <button onClick={() => { onSave(form); if (prefixo) api.put('/org/config/preferencias', { prefixo_empresa: prefixo }); }} disabled={saving} className="btn-primary" data-testid="config-save-numeracao">{saving ? 'Salvando...' : 'Salvar'}</button>
      </div>
    </div>
  );
};

const PreferenciasTab = ({ config, onSave, saving }) => {
  const [form, setForm] = useState(config?.preferencias || {});
  return (
    <div className="glass-card p-4 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <FormInput label="Horário de Trabalho - Início"><input value={form.horario_trabalho?.inicio || '07:00'} onChange={e => setForm({...form, horario_trabalho: {...(form.horario_trabalho || {}), inicio: e.target.value}})} type="time" className="input-industrial w-full px-4" /></FormInput>
        <FormInput label="Horário de Trabalho - Fim"><input value={form.horario_trabalho?.fim || '17:00'} onChange={e => setForm({...form, horario_trabalho: {...(form.horario_trabalho || {}), fim: e.target.value}})} type="time" className="input-industrial w-full px-4" /></FormInput>
        <FormInput label="Fuso Horário">
          <select value={form.fuso_horario || 'America/Sao_Paulo'} onChange={e => setForm({...form, fuso_horario: e.target.value})} className="input-industrial w-full px-4">
            <option value="America/Sao_Paulo">São Paulo (BRT)</option>
            <option value="America/Manaus">Manaus (AMT)</option>
            <option value="America/Belem">Belém (BRT)</option>
            <option value="America/Cuiaba">Cuiabá (AMT)</option>
          </select>
        </FormInput>
        <FormInput label="Formato de Data">
          <select value={form.formato_data || 'DD/MM/YYYY'} onChange={e => setForm({...form, formato_data: e.target.value})} className="input-industrial w-full px-4">
            <option value="DD/MM/YYYY">DD/MM/YYYY</option>
            <option value="MM/DD/YYYY">MM/DD/YYYY</option>
            <option value="YYYY-MM-DD">YYYY-MM-DD</option>
          </select>
        </FormInput>
        <FormInput label="Unidade de Tempo">
          <select value={form.unidade_tempo || 'minutos'} onChange={e => setForm({...form, unidade_tempo: e.target.value})} className="input-industrial w-full px-4">
            <option value="minutos">Minutos</option>
            <option value="horas">Horas</option>
          </select>
        </FormInput>
        <FormInput label="Moeda">
          <select value={form.moeda || 'BRL'} onChange={e => setForm({...form, moeda: e.target.value})} className="input-industrial w-full px-4">
            <option value="BRL">R$ (Real)</option>
            <option value="USD">$ (Dólar)</option>
            <option value="EUR">€ (Euro)</option>
          </select>
        </FormInput>
      </div>
      {/* Turnos */}
      <div>
        <p className="text-sm text-slate-300 font-medium mb-2">Turnos</p>
        <div className="space-y-1">
          {(form.turnos || []).map((turno, idx) => (
            <div key={idx} className="flex items-center gap-2 text-xs">
              <input value={turno.nome} onChange={e => { const t = [...(form.turnos || [])]; t[idx] = {...t[idx], nome: e.target.value}; setForm({...form, turnos: t}); }} className="input-industrial flex-1 px-2" />
              <input type="time" value={turno.inicio} onChange={e => { const t = [...(form.turnos || [])]; t[idx] = {...t[idx], inicio: e.target.value}; setForm({...form, turnos: t}); }} className="input-industrial w-24 px-2" />
              <span className="text-slate-600">→</span>
              <input type="time" value={turno.fim} onChange={e => { const t = [...(form.turnos || [])]; t[idx] = {...t[idx], fim: e.target.value}; setForm({...form, turnos: t}); }} className="input-industrial w-24 px-2" />
              <button onClick={() => { const t = (form.turnos || []).filter((_,i) => i !== idx); setForm({...form, turnos: t}); }} className="text-red-400 hover:text-red-300"><X size={14} /></button>
            </div>
          ))}
          <button onClick={() => setForm({...form, turnos: [...(form.turnos || []), {nome: '', inicio: '06:00', fim: '14:00'}]})} className="text-xs text-brand hover:brightness-110 mt-1">+ Adicionar turno</button>
        </div>
      </div>
      <div className="flex justify-end"><button onClick={() => onSave(form)} disabled={saving} className="btn-primary" data-testid="config-save-preferencias">{saving ? 'Salvando...' : 'Salvar'}</button></div>
    </div>
  );
};


const AppLayout = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { branding } = useBranding() || {};
  const b = branding || {};
  
  return (
    <div className="min-h-screen flex" style={{ backgroundColor: b.cor_fundo || 'var(--brand-bg)' }}>
      <NetworkStatus />
      <Sidebar collapsed={sidebarCollapsed} setCollapsed={setSidebarCollapsed} />
      <div className="flex-1 flex flex-col min-h-screen">
        <main className="flex-1 pb-20 md:pb-4 px-4 pt-4 max-w-6xl mx-auto w-full">
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
    const storedUser = sessionStorage.getItem('maintrix_user');
    if (storedUser) setUser(JSON.parse(storedUser));
    setLoading(false);
  }, []);
  
  const login = (data) => {
    sessionStorage.setItem('maintrix_token', data.access_token);
    sessionStorage.setItem('maintrix_user', JSON.stringify(data.user));
    setUser(data.user);
  };
  
  const logout = () => {
    sessionStorage.removeItem('maintrix_token');
    sessionStorage.removeItem('maintrix_user');
    setUser(null);
  };
  
  return <AuthContext.Provider value={{ user, login, logout, loading }}>{children}</AuthContext.Provider>;
};

// Branding loader — runs after auth to apply org theme
const BrandingLoader = ({ children }) => {
  const { user } = useAuth();
  const { loadFromUser } = useBranding();
  useEffect(() => { if (user) loadFromUser(user); }, [user, loadFromUser]);
  return children;
};

// App
function App() {
  return (
    <BrandingProvider>
      <AuthProvider>
        <BrowserRouter>
          <BrandingLoader>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/" element={<ProtectedRoute><AppLayout><CentralTrabalhoPage /></AppLayout></ProtectedRoute>} />
              <Route path="/dashboard" element={<ProtectedRoute><AppLayout><DashboardPage /></AppLayout></ProtectedRoute>} />
              <Route path="/ativos" element={<ProtectedRoute><AppLayout><AtivosPage /></AppLayout></ProtectedRoute>} />
              <Route path="/ativos/:id" element={<ProtectedRoute><AppLayout><AtivoDetailPage /></AppLayout></ProtectedRoute>} />
              <Route path="/os" element={<ProtectedRoute><AppLayout><OSPage /></AppLayout></ProtectedRoute>} />
              <Route path="/os/:id" element={<ProtectedRoute><AppLayout><OSDetailPage /></AppLayout></ProtectedRoute>} />
              <Route path="/estoque" element={<ProtectedRoute><AppLayout><EstoquePage /></AppLayout></ProtectedRoute>} />
              <Route path="/inspecoes" element={<ProtectedRoute><AppLayout><InspecoesPage /></AppLayout></ProtectedRoute>} />
              <Route path="/inspecoes/:id" element={<ProtectedRoute><AppLayout><InspecaoDetailPage /></AppLayout></ProtectedRoute>} />
              <Route path="/ronda" element={<ProtectedRoute><AppLayout><RondaPage /></AppLayout></ProtectedRoute>} />
              <Route path="/scanner" element={<ProtectedRoute><AppLayout><ScannerPage /></AppLayout></ProtectedRoute>} />
              <Route path="/sobressalentes" element={<ProtectedRoute><AppLayout><SobressalentesPage /></AppLayout></ProtectedRoute>} />
              <Route path="/paradas" element={<ProtectedRoute><AppLayout><ParadasPage /></AppLayout></ProtectedRoute>} />
              <Route path="/anomalias" element={<ProtectedRoute><AppLayout><AnomaliasPage /></AppLayout></ProtectedRoute>} />
              <Route path="/solicitar" element={<ProtectedRoute><AppLayout><SolicitacaoServicoPage /></AppLayout></ProtectedRoute>} />
              <Route path="/assistente" element={<ProtectedRoute><AppLayout><AssistentePage /></AppLayout></ProtectedRoute>} />
              <Route path="/admin/usuarios" element={<ProtectedRoute><AppLayout><AdminUsuariosPage /></AppLayout></ProtectedRoute>} />
              <Route path="/admin/templates" element={<ProtectedRoute><AppLayout><AdminTemplatesPage /></AppLayout></ProtectedRoute>} />
              <Route path="/admin/auditoria" element={<ProtectedRoute><AppLayout><AuditoriaPage /></AppLayout></ProtectedRoute>} />
              <Route path="/setores" element={<ProtectedRoute><AppLayout><SetoresPage /></AppLayout></ProtectedRoute>} />
              <Route path="/plantas" element={<ProtectedRoute><AppLayout><UnidadesPage /></AppLayout></ProtectedRoute>} />
              <Route path="/unidades" element={<ProtectedRoute><AppLayout><UnidadesPage /></AppLayout></ProtectedRoute>} />
              <Route path="/admin/config" element={<ProtectedRoute><AppLayout><OrgConfigPage /></AppLayout></ProtectedRoute>} />
              <Route path="/equipe" element={<ProtectedRoute><AppLayout><EquipePage /></AppLayout></ProtectedRoute>} />
              <Route path="/biblioteca" element={<ProtectedRoute><AppLayout><BibliotecaPage /></AppLayout></ProtectedRoute>} />
              <Route path="/master/white-label" element={<ProtectedRoute><AppLayout><WhiteLabelDesignerPage /></AppLayout></ProtectedRoute>} />
              <Route path="/master/cleanup" element={<ProtectedRoute><AppLayout><MasterCleanupPage /></AppLayout></ProtectedRoute>} />
              <Route path="/portal/equipamento/:id" element={<PortalPublicoPage />} />
              <Route path="/portal/tecnico/:id" element={<ProtectedRoute><AppLayout><PortalTecnicoPage /></AppLayout></ProtectedRoute>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrandingLoader>
          <Toaster position="top-center" richColors />
        </BrowserRouter>
      </AuthProvider>
    </BrandingProvider>
  );
}

export default App;
