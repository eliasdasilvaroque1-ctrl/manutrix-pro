import { useState, useEffect, createContext, useContext, useRef, Fragment } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, useParams, useSearchParams } from "react-router-dom";
import axios from "axios";
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
  Shield, CheckSquare, Square, ChevronUp, LayoutDashboard, List, Download
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

// API Client
const api = axios.create({ baseURL: API });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('manutrix_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
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
    operacional: { class: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', label: 'Operacional', icon: CheckCircle },
    parado: { class: 'bg-red-500/10 text-red-400 border-red-500/30', label: 'Parado', icon: XCircle },
    manutencao: { class: 'bg-amber-500/10 text-amber-400 border-amber-500/30', label: 'Manutenção', icon: Wrench },
    desativado: { class: 'bg-slate-500/10 text-slate-400 border-slate-500/30', label: 'Desativado', icon: XCircle },
    aberta: { class: 'bg-blue-500/10 text-blue-400 border-blue-500/30', label: 'Aberta', icon: Clock },
    planejada: { class: 'bg-purple-500/10 text-purple-400 border-purple-500/30', label: 'Planejada', icon: Calendar },
    em_execucao: { class: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', label: 'Em Execução', icon: Play },
    pausada: { class: 'bg-amber-500/10 text-amber-400 border-amber-500/30', label: 'Pausada', icon: Pause },
    concluida: { class: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', label: 'Concluída', icon: CheckCircle },
    cancelada: { class: 'bg-red-500/10 text-red-400 border-red-500/30', label: 'Cancelada', icon: XCircle },
    pendente: { class: 'bg-amber-500/10 text-amber-400 border-amber-500/30', label: 'Pendente', icon: Clock },
    em_andamento: { class: 'bg-blue-500/10 text-blue-400 border-blue-500/30', label: 'Em Andamento', icon: Activity },
    com_pendencias: { class: 'bg-red-500/10 text-red-400 border-red-500/30', label: 'Com Pendências', icon: AlertTriangle },
    conforme: { class: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', label: 'Conforme', icon: CheckCircle },
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
    alta: { class: 'bg-amber-500/20 border-amber-500 text-amber-400', label: 'Alta' },
    media: { class: 'bg-emerald-500/20 border-emerald-500 text-emerald-400', label: 'Média' },
    baixa: { class: 'bg-slate-500/20 border-slate-500 text-slate-400', label: 'Baixa' },
  };
  const c = config[priority] || config.media;
  return <span className={`${c.class} border px-2 py-1 rounded text-xs font-medium`}>{c.label}</span>;
};

// KPI Card
const KPICard = ({ value, label, icon: Icon, color = 'emerald', subtitle, trend }) => {
  const colors = {
    emerald: 'text-emerald-400 bg-emerald-500/10',
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
              <button onClick={markAllRead} className="text-xs text-emerald-400 hover:underline">
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
  const [form, setForm] = useState({
    tag: '', nome: '', tipo_equipamento: '', fabricante: '', modelo: '', numero_serie: '',
    area_id: '', centro_custo: '', criticidade: 'media', status: 'operacional',
    mtbf_horas: '', mttr_horas: '', data_instalacao: '', garantia_ate: '',
    valor_aquisicao: '', depreciacao_anual: '', fornecedor: '', observacoes: ''
  });
  
  useEffect(() => {
    if (editData) {
      setForm({
        tag: editData.tag || '',
        nome: editData.nome || '',
        tipo_equipamento: editData.tipo_equipamento || '',
        fabricante: editData.fabricante || '',
        modelo: editData.modelo || '',
        numero_serie: editData.numero_serie || '',
        area_id: editData.area_id || '',
        centro_custo: editData.centro_custo || '',
        criticidade: editData.criticidade || 'media',
        status: editData.status || 'operacional',
        mtbf_horas: editData.mtbf_horas || '',
        mttr_horas: editData.mttr_horas || '',
        data_instalacao: editData.data_instalacao || '',
        garantia_ate: editData.garantia_ate || '',
        valor_aquisicao: editData.valor_aquisicao || '',
        depreciacao_anual: editData.depreciacao_anual || '',
        fornecedor: editData.fornecedor || '',
        observacoes: editData.observacoes || ''
      });
    } else {
      setForm({
        tag: '', nome: '', tipo_equipamento: '', fabricante: '', modelo: '', numero_serie: '',
        area_id: '', centro_custo: '', criticidade: 'media', status: 'operacional',
        mtbf_horas: '', mttr_horas: '', data_instalacao: '', garantia_ate: '',
        valor_aquisicao: '', depreciacao_anual: '', fornecedor: '', observacoes: ''
      });
    }
    setPdfFiles([]);
    // Load existing manuals for edit mode
    if (editData?.id) {
      api.get(`/ativos/${editData.id}/manuais`).then(res => setExistingManuais(res.data)).catch(() => {});
    } else {
      setExistingManuais([]);
    }
  }, [editData, isOpen]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.nome || !form.area_id) {
      toast.error('Preencha os campos obrigatórios');
      return;
    }
    
    setLoading(true);
    try {
      const payload = {
        ...form,
        mtbf_horas: form.mtbf_horas ? parseFloat(form.mtbf_horas) : null,
        mttr_horas: form.mttr_horas ? parseFloat(form.mttr_horas) : null,
        valor_aquisicao: form.valor_aquisicao ? parseFloat(form.valor_aquisicao) : null,
        depreciacao_anual: form.depreciacao_anual ? parseFloat(form.depreciacao_anual) : null,
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
      toast.error(error.response?.data?.detail || 'Erro ao salvar ativo');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={editData ? "Editar Ativo" : "Novo Ativo"} size="lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Identificação */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
            <Tag size={16} /> Identificação
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
            <FormInput label="Tipo de Equipamento">
              <input
                type="text"
                value={form.tipo_equipamento}
                onChange={(e) => setForm({...form, tipo_equipamento: e.target.value})}
                placeholder="Ex: Bomba, Motor, Compressor"
                className="input-industrial w-full px-4"
              />
            </FormInput>
            <FormInput label="Número de Série">
              <input
                type="text"
                value={form.numero_serie}
                onChange={(e) => setForm({...form, numero_serie: e.target.value})}
                className="input-industrial w-full px-4"
              />
            </FormInput>
            <FormInput label="Fabricante">
              <input
                type="text"
                value={form.fabricante}
                onChange={(e) => setForm({...form, fabricante: e.target.value})}
                className="input-industrial w-full px-4"
              />
            </FormInput>
            <FormInput label="Modelo">
              <input
                type="text"
                value={form.modelo}
                onChange={(e) => setForm({...form, modelo: e.target.value})}
                className="input-industrial w-full px-4"
              />
            </FormInput>
          </div>
        </div>
        
        {/* Operacional */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wider flex items-center gap-2">
            <Settings size={16} /> Operacional
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Área" required>
              <Select
                value={form.area_id}
                onChange={(val) => setForm({...form, area_id: val})}
                options={areas.map(a => ({ value: a.id, label: a.nome }))}
                placeholder="Selecione a área..."
              />
            </FormInput>
            <FormInput label="Centro de Custo">
              <input
                type="text"
                value={form.centro_custo}
                onChange={(e) => setForm({...form, centro_custo: e.target.value})}
                className="input-industrial w-full px-4"
              />
            </FormInput>
            <FormInput label="Criticidade">
              <Select
                value={form.criticidade}
                onChange={(val) => setForm({...form, criticidade: val})}
                options={[
                  { value: 'baixa', label: 'Baixa' },
                  { value: 'media', label: 'Média' },
                  { value: 'alta', label: 'Alta' },
                  { value: 'critica', label: 'Crítica' },
                ]}
              />
            </FormInput>
            <FormInput label="Status">
              <Select
                value={form.status}
                onChange={(val) => setForm({...form, status: val})}
                options={[
                  { value: 'operacional', label: 'Operacional' },
                  { value: 'parado', label: 'Parado' },
                  { value: 'manutencao', label: 'Em Manutenção' },
                  { value: 'desativado', label: 'Desativado' },
                ]}
              />
            </FormInput>
          </div>
        </div>
        
        {/* Manutenção */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-2">
            <Wrench size={16} /> Manutenção
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="MTBF (horas)">
              <input
                type="number"
                value={form.mtbf_horas}
                onChange={(e) => setForm({...form, mtbf_horas: e.target.value})}
                className="input-industrial w-full px-4"
                placeholder="Tempo médio entre falhas"
              />
            </FormInput>
            <FormInput label="MTTR (horas)">
              <input
                type="number"
                value={form.mttr_horas}
                onChange={(e) => setForm({...form, mttr_horas: e.target.value})}
                className="input-industrial w-full px-4"
                placeholder="Tempo médio de reparo"
              />
            </FormInput>
            <FormInput label="Data de Instalação">
              <input
                type="date"
                value={form.data_instalacao}
                onChange={(e) => setForm({...form, data_instalacao: e.target.value})}
                className="input-industrial w-full px-4"
              />
            </FormInput>
            <FormInput label="Garantia até">
              <input
                type="date"
                value={form.garantia_ate}
                onChange={(e) => setForm({...form, garantia_ate: e.target.value})}
                className="input-industrial w-full px-4"
              />
            </FormInput>
          </div>
        </div>
        
        {/* Financeiro */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-2">
            <DollarSign size={16} /> Financeiro
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <FormInput label="Valor de Aquisição (R$)">
              <input
                type="number"
                step="0.01"
                value={form.valor_aquisicao}
                onChange={(e) => setForm({...form, valor_aquisicao: e.target.value})}
                className="input-industrial w-full px-4"
              />
            </FormInput>
            <FormInput label="Depreciação Anual (%)">
              <input
                type="number"
                step="0.01"
                value={form.depreciacao_anual}
                onChange={(e) => setForm({...form, depreciacao_anual: e.target.value})}
                className="input-industrial w-full px-4"
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
                <div key={idx} className="flex items-center justify-between p-2 bg-emerald-500/5 border border-emerald-500/20 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Upload size={16} className="text-emerald-400" />
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
    sku: '', nome: '', descricao: '', categoria: 'outros',
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
        sku: '', nome: '', descricao: '', categoria: 'outros',
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
      toast.error(error.response?.data?.detail || 'Erro ao salvar item');
    } finally {
      setLoading(false);
    }
  };
  
  const categorias = [
    { value: 'rolamento', label: 'Rolamento' },
    { value: 'lubrificante', label: 'Lubrificante' },
    { value: 'eletrica', label: 'Elétrica' },
    { value: 'mecanica', label: 'Mecânica' },
    { value: 'instrumentacao', label: 'Instrumentação' },
    { value: 'vedacao', label: 'Vedação' },
    { value: 'filtro', label: 'Filtro' },
    { value: 'correia', label: 'Correia' },
    { value: 'outros', label: 'Outros' },
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
          <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
            <Tag size={16} /> Identificação
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="SKU">
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
                <p className="text-lg font-bold text-emerald-400">
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
                className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-emerald-500 focus:ring-emerald-500"
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
const ModalNovaOS = ({ isOpen, onClose, onSuccess, ativos = [], tecnicos = [], editData = null }) => {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    ativo_id: '', tipo: 'corretiva', prioridade: 'media',
    titulo: '', descricao: '', responsavel_id: '',
    data_planejada: '', custo_pecas: 0, custo_mao_obra: 0
  });
  
  useEffect(() => {
    if (editData) {
      setForm({
        ativo_id: editData.ativo_id || '',
        tipo: editData.tipo || 'corretiva',
        prioridade: editData.prioridade || 'media',
        titulo: editData.titulo || '',
        descricao: editData.descricao || '',
        responsavel_id: editData.responsavel_id || '',
        data_planejada: editData.data_planejada?.split('T')[0] || '',
        custo_pecas: editData.custo_pecas || 0,
        custo_mao_obra: editData.custo_mao_obra || 0
      });
    } else {
      setForm({
        ativo_id: '', tipo: 'corretiva', prioridade: 'media',
        titulo: '', descricao: '', responsavel_id: '',
        data_planejada: '', custo_pecas: 0, custo_mao_obra: 0
      });
    }
  }, [editData, isOpen]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.ativo_id || !form.titulo) {
      toast.error('Preencha os campos obrigatórios');
      return;
    }
    
    setLoading(true);
    try {
      const payload = {
        ...form,
        custo_pecas: parseFloat(form.custo_pecas) || 0,
        custo_mao_obra: parseFloat(form.custo_mao_obra) || 0,
        data_planejada: form.data_planejada || null,
        responsavel_id: form.responsavel_id || null,
      };
      
      if (editData) {
        await api.put(`/ordens-servico/${editData.id}`, payload);
        toast.success('OS atualizada com sucesso!');
      } else {
        await api.post('/ordens-servico', payload);
        toast.success('OS criada com sucesso!');
      }
      onSuccess();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar OS');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={editData ? "Editar Ordem de Serviço" : "Nova Ordem de Serviço"} size="lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Identificação */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
            <Wrench size={16} /> Dados da OS
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Ativo" required>
              <Select
                value={form.ativo_id}
                onChange={(val) => setForm({...form, ativo_id: val})}
                options={ativos.map(a => ({ value: a.id, label: `${a.tag} - ${a.nome}` }))}
                placeholder="Selecione o ativo..."
              />
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
                  { value: 'preventiva', label: 'Preventiva' },
                  { value: 'corretiva', label: 'Corretiva' },
                  { value: 'preditiva', label: 'Preditiva' },
                  { value: 'emergencia', label: 'Emergência' },
                  { value: 'falha', label: 'Falha' },
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
                <p className="text-lg font-bold text-emerald-400">
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
const ModalNovaInspecao = ({ isOpen, onClose, onSuccess, ativos = [], rotas = [], tecnicos = [] }) => {
  const [loading, setLoading] = useState(false);
  const [tipoTab, setTipoTab] = useState('checklist');
  const [form, setForm] = useState({
    ativo_id: '', responsavel_id: '', frequencia: 'diaria',
    data_programada: '', hora_programada: '',
    // Lubrificação
    tipo_lubrificante: '', quantidade_lubrificante: '', ponto_lubrificacao: '',
    metodo_aplicacao: '', observacoes_lubrificacao: ''
  });
  const { user } = useAuth();
  
  useEffect(() => {
    if (isOpen) {
      setTipoTab('checklist');
      setForm({
        ativo_id: '', responsavel_id: user?.id || '', frequencia: 'diaria',
        data_programada: '', hora_programada: '',
        tipo_lubrificante: '', quantidade_lubrificante: '', ponto_lubrificacao: '',
        metodo_aplicacao: '', observacoes_lubrificacao: ''
      });
    }
  }, [isOpen, user]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.ativo_id || !form.responsavel_id) {
      toast.error('Selecione ativo e responsável');
      return;
    }
    if (tipoTab === 'lubrificacao' && !form.tipo_lubrificante) {
      toast.error('Informe o tipo de lubrificante');
      return;
    }
    
    setLoading(true);
    try {
      const dataProgramada = form.data_programada && form.hora_programada
        ? `${form.data_programada}T${form.hora_programada}:00`
        : form.data_programada || null;

      const payload = {
        ativo_id: form.ativo_id,
        responsavel_id: form.responsavel_id,
        tipo: tipoTab,
        frequencia: tipoTab === 'checklist' ? form.frequencia : null,
        data_programada: dataProgramada,
        tipo_lubrificante: tipoTab === 'lubrificacao' ? form.tipo_lubrificante : null,
        quantidade_lubrificante: tipoTab === 'lubrificacao' ? form.quantidade_lubrificante : null,
        ponto_lubrificacao: tipoTab === 'lubrificacao' ? form.ponto_lubrificacao : null,
        metodo_aplicacao: tipoTab === 'lubrificacao' ? form.metodo_aplicacao : null,
        observacoes_lubrificacao: tipoTab === 'lubrificacao' ? form.observacoes_lubrificacao : null,
      };

      await api.post('/inspecoes', payload);
      toast.success(tipoTab === 'lubrificacao' ? 'Lubrificação criada com sucesso!' : 'Inspeção criada com sucesso!');
      onSuccess();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar');
    } finally {
      setLoading(false);
    }
  };

  const selectedAtivo = ativos.find(a => a.id === form.ativo_id);
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Nova Inspeção / Lubrificação" size="lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Tabs */}
        <div className="flex bg-slate-800/50 rounded-lg p-1 gap-1">
          <button
            type="button"
            onClick={() => setTipoTab('checklist')}
            className={`flex-1 py-2.5 px-4 rounded-md text-sm font-medium transition-all flex items-center justify-center gap-2 ${
              tipoTab === 'checklist' 
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
            data-testid="tab-inspecao"
          >
            <ClipboardCheck size={18} /> Inspeção
          </button>
          <button
            type="button"
            onClick={() => setTipoTab('lubrificacao')}
            className={`flex-1 py-2.5 px-4 rounded-md text-sm font-medium transition-all flex items-center justify-center gap-2 ${
              tipoTab === 'lubrificacao' 
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
            data-testid="tab-lubrificacao"
          >
            <Droplet size={18} /> Lubrificação
          </button>
        </div>

        {/* Equipamento + Responsável (comum) */}
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
            <Box size={16} /> Equipamento
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Ativo / Equipamento" required>
              <Select
                value={form.ativo_id}
                onChange={(val) => setForm({...form, ativo_id: val})}
                options={ativos.map(a => ({ value: a.id, label: `${a.tag} - ${a.nome}` }))}
                placeholder="Selecione o equipamento..."
              />
            </FormInput>
            <FormInput label="Responsável" required>
              <Select
                value={form.responsavel_id}
                onChange={(val) => setForm({...form, responsavel_id: val})}
                options={tecnicos.map(t => ({ value: t.id, label: t.nome }))}
                placeholder="Selecione o responsável..."
              />
            </FormInput>
          </div>
          {selectedAtivo && (
            <div className="flex items-center gap-3 p-2 bg-slate-800/50 rounded-lg">
              <StatusBadge status={selectedAtivo.status} size="sm" />
              <PriorityBadge priority={selectedAtivo.criticidade} />
              {selectedAtivo.area && <span className="text-xs text-slate-500">{selectedAtivo.area.nome}</span>}
            </div>
          )}
        </div>

        {/* === ABA INSPEÇÃO === */}
        {tipoTab === 'checklist' && (
          <div className="glass-card p-4 space-y-4">
            <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wider flex items-center gap-2">
              <Calendar size={16} /> Frequência e Programação
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <FormInput label="Frequência" required>
                <Select
                  value={form.frequencia}
                  onChange={(val) => setForm({...form, frequencia: val})}
                  options={[
                    { value: 'diaria', label: 'Diária' },
                    { value: 'quinzenal', label: 'Quinzenal' },
                    { value: 'mensal', label: 'Mensal' },
                  ]}
                />
              </FormInput>
              <FormInput label="Data Programada">
                <input
                  type="date"
                  value={form.data_programada}
                  onChange={(e) => setForm({...form, data_programada: e.target.value})}
                  className="input-industrial w-full px-4"
                />
              </FormInput>
              <FormInput label="Hora">
                <input
                  type="time"
                  value={form.hora_programada}
                  onChange={(e) => setForm({...form, hora_programada: e.target.value})}
                  className="input-industrial w-full px-4"
                />
              </FormInput>
            </div>
            {/* Preview do checklist */}
            <div className="mt-2 p-3 bg-slate-800/30 rounded-lg">
              <p className="text-xs text-slate-500 mb-2">Checklist gerado automaticamente ({
                form.frequencia === 'diaria' ? '5 itens' : form.frequencia === 'quinzenal' ? '7 itens' : '9 itens'
              }):</p>
              <div className="flex flex-wrap gap-2">
                {form.frequencia === 'diaria' && ['Vibração', 'Temperatura', 'Ruído', 'Vazamentos', 'Observações'].map(i => (
                  <span key={i} className="text-xs px-2 py-1 bg-slate-700 rounded text-slate-300">{i}</span>
                ))}
                {form.frequencia === 'quinzenal' && ['Vibração', 'Temperatura', 'Ruído', 'Vazamentos', 'Nível óleo', 'Fixações', 'Observações'].map(i => (
                  <span key={i} className="text-xs px-2 py-1 bg-slate-700 rounded text-slate-300">{i}</span>
                ))}
                {form.frequencia === 'mensal' && ['Vibração (mm/s)', 'Temperatura (°C)', 'Ruído', 'Vazamentos', 'Nível óleo', 'Alinhamento', 'Fixações', 'Correias', 'Observações'].map(i => (
                  <span key={i} className="text-xs px-2 py-1 bg-slate-700 rounded text-slate-300">{i}</span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* === ABA LUBRIFICAÇÃO === */}
        {tipoTab === 'lubrificacao' && (
          <>
            <div className="glass-card p-4 space-y-4">
              <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                <Droplet size={16} /> Dados da Lubrificação
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormInput label="Tipo de Lubrificante" required>
                  <Select
                    value={form.tipo_lubrificante}
                    onChange={(val) => setForm({...form, tipo_lubrificante: val})}
                    options={[
                      { value: 'oleo_mineral', label: 'Óleo Mineral' },
                      { value: 'oleo_sintetico', label: 'Óleo Sintético' },
                      { value: 'graxa_base_litio', label: 'Graxa Base Lítio' },
                      { value: 'graxa_base_calcio', label: 'Graxa Base Cálcio' },
                      { value: 'graxa_poliureia', label: 'Graxa Poliureia' },
                      { value: 'oleo_hidraulico', label: 'Óleo Hidráulico' },
                      { value: 'oleo_engrenagem', label: 'Óleo de Engrenagem' },
                      { value: 'fluido_corte', label: 'Fluido de Corte' },
                      { value: 'outro', label: 'Outro' },
                    ]}
                    placeholder="Selecione o lubrificante..."
                  />
                </FormInput>
                <FormInput label="Quantidade">
                  <input
                    type="text"
                    value={form.quantidade_lubrificante}
                    onChange={(e) => setForm({...form, quantidade_lubrificante: e.target.value})}
                    placeholder="Ex: 200ml, 50g"
                    className="input-industrial w-full px-4"
                  />
                </FormInput>
                <FormInput label="Ponto de Lubrificação">
                  <input
                    type="text"
                    value={form.ponto_lubrificacao}
                    onChange={(e) => setForm({...form, ponto_lubrificacao: e.target.value})}
                    placeholder="Ex: Rolamento lado acoplamento"
                    className="input-industrial w-full px-4"
                  />
                </FormInput>
                <FormInput label="Método de Aplicação">
                  <Select
                    value={form.metodo_aplicacao}
                    onChange={(val) => setForm({...form, metodo_aplicacao: val})}
                    options={[
                      { value: 'manual', label: 'Manual (engraxadeira)' },
                      { value: 'bomba', label: 'Bomba de lubrificação' },
                      { value: 'banho', label: 'Banho de óleo' },
                      { value: 'spray', label: 'Spray' },
                      { value: 'gotejamento', label: 'Gotejamento' },
                      { value: 'automatico', label: 'Sistema automático' },
                    ]}
                    placeholder="Método..."
                  />
                </FormInput>
              </div>
            </div>

            <div className="glass-card p-4 space-y-4">
              <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wider flex items-center gap-2">
                <Calendar size={16} /> Programação
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormInput label="Data Programada" required>
                  <input
                    type="date"
                    value={form.data_programada}
                    onChange={(e) => setForm({...form, data_programada: e.target.value})}
                    className="input-industrial w-full px-4"
                  />
                </FormInput>
                <FormInput label="Hora Programada">
                  <input
                    type="time"
                    value={form.hora_programada}
                    onChange={(e) => setForm({...form, hora_programada: e.target.value})}
                    className="input-industrial w-full px-4"
                  />
                </FormInput>
              </div>
            </div>

            <div className="glass-card p-4 space-y-4">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <FileText size={16} /> Observações
              </h3>
              <textarea
                value={form.observacoes_lubrificacao}
                onChange={(e) => setForm({...form, observacoes_lubrificacao: e.target.value})}
                className="input-industrial w-full px-4 py-3 min-h-[80px]"
                placeholder="Informações adicionais sobre a lubrificação..."
              />
            </div>
          </>
        )}
        
        <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2" data-testid="submit-inspecao-btn">
            {loading ? <RefreshCw size={18} className="animate-spin" /> : tipoTab === 'lubrificacao' ? <Droplet size={18} /> : <ClipboardCheck size={18} />}
            {loading ? 'Criando...' : tipoTab === 'lubrificacao' ? 'Criar Lubrificação' : 'Criar Inspeção'}
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
  
  const menuGroups = [
    {
      label: 'GESTÃO',
      items: [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
        { icon: Box, label: 'Ativos', path: '/ativos' },
        { icon: Wrench, label: 'Ordens de Serviço', path: '/os' },
        { icon: ClipboardCheck, label: 'Inspeções', path: '/inspecoes' },
        { icon: AlertTriangle, label: 'Anomalias', path: '/anomalias' },
        { icon: Target, label: 'Ronda', path: '/ronda' },
      ]
    },
    {
      label: 'MATERIAIS',
      items: [
        { icon: Package, label: 'Estoque', path: '/estoque' },
        { icon: Cog, label: 'Sobressalentes', path: '/sobressalentes' },
      ]
    },
    {
      label: 'SUPORTE',
      items: [
        { icon: Zap, label: 'Assistente IA', path: '/assistente' },
      ]
    },
    ...(user?.role === 'admin' ? [{
      label: 'ADMIN',
      items: [
        { icon: Users, label: 'Usuários', path: '/admin/usuarios' },
      ]
    }] : [])
  ];
  
  return (
    <aside className={`hidden md:flex flex-col bg-slate-900/95 backdrop-blur-sm border-r border-slate-800 h-screen sticky top-0 transition-all duration-300 ${collapsed ? 'w-16' : 'w-64'}`}>
      <div className={`p-4 border-b border-slate-800 flex items-center ${collapsed ? 'justify-center' : 'justify-between'}`}>
        {!collapsed && (
          <div>
            <h1 className="text-xl font-bold text-emerald-400 tracking-wider">MANUTRIX</h1>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider">Enterprise CMMS</p>
          </div>
        )}
        <button onClick={() => setCollapsed(!collapsed)} className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors">
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
                  className={`w-full flex items-center gap-3 px-4 py-2.5 transition-all ${
                    isActive 
                      ? 'bg-emerald-500/10 text-emerald-400 border-l-2 border-emerald-500' 
                      : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 border-l-2 border-transparent'
                  } ${collapsed ? 'justify-center' : ''}`}
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
            <div className="w-9 h-9 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
              <User size={18} className="text-emerald-400" />
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
  
  const items = [
    { icon: Home, label: 'Início', path: '/' },
    { icon: ClipboardCheck, label: 'Inspeções', path: '/inspecoes' },
    { icon: QrCode, label: 'Scan', path: '/scanner', special: true },
    { icon: Box, label: 'Ativos', path: '/ativos' },
    { icon: Wrench, label: 'OS', path: '/os' },
  ];
  
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur-sm border-t border-slate-800 z-40 pb-safe md:hidden">
      <div className="flex items-center justify-around h-16">
        {items.map((item, idx) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
          
          if (item.special) {
            return (
              <button key={idx} onClick={() => navigate(item.path)} className="scan-button pulse-glow">
                <Icon size={26} />
              </button>
            );
          }
          
          return (
            <button
              key={idx}
              onClick={() => navigate(item.path)}
              className={`nav-item ${isActive ? 'active' : ''}`}
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
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      login(response.data);
      toast.success('Login realizado!');
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro no login');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSeed = async () => {
    try {
      await axios.post(`${API}/seed`);
      toast.success('Dados de demonstração criados!');
    } catch (e) {
      toast.info('Dados já existem');
    }
  };
  
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 mb-4">
            <Cog size={32} className="text-emerald-400" />
          </div>
          <h1 className="text-3xl font-bold text-emerald-400 tracking-wider">MANUTRIX</h1>
          <p className="text-slate-500 mt-1 text-sm">Enterprise CMMS Platform</p>
        </div>
        
        <form onSubmit={handleSubmit} className="glass-card p-6 space-y-4">
          <FormInput label="Email">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-industrial w-full px-4"
              placeholder="seu@email.com"
              required
            />
          </FormInput>
          <FormInput label="Senha">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-industrial w-full px-4"
              placeholder="••••••••"
              required
            />
          </FormInput>
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
        
        <div className="mt-4 text-center">
          <button onClick={handleSeed} className="text-slate-500 hover:text-slate-300 text-sm underline">
            Criar dados de demonstração
          </button>
          <p className="text-slate-600 text-xs mt-2">admin@manutrix.com / admin123</p>
        </div>
      </div>
    </div>
  );
};

// Dashboard
const DashboardPage = () => {
  const [kpis, setKpis] = useState(null);
  const [stats, setStats] = useState(null);
  const [trend, setTrend] = useState([]);
  const [loading, setLoading] = useState(true);
  const [drillModal, setDrillModal] = useState({ open: false, type: '', title: '', data: [] });
  const [drillLoading, setDrillLoading] = useState(false);
  const { user } = useAuth();
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [kpisRes, statsRes, trendRes] = await Promise.all([
          api.get('/kpis'),
          api.get('/dashboard/stats'),
          api.get('/dashboard/trend')
        ]);
        setKpis(kpisRes.data);
        setStats(statsRes.data);
        setTrend(trendRes.data);
      } catch (error) {
        toast.error('Erro ao carregar dashboard');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

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
      a.download = `${entity}_manutrix.${format === 'excel' ? 'xlsx' : 'csv'}`;
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
    preditiva: acc.preditiva + (m.preditivas || 0),
    emergencia: acc.emergencia + (m.emergencias || 0),
  }), { corretiva: 0, preventiva: 0, preditiva: 0, emergencia: 0 });
  
  // Compute preventiva/corretiva % from trend for a more realistic view
  const totalTrendOS = osTrendTotals.preventiva + osTrendTotals.corretiva + osTrendTotals.preditiva + osTrendTotals.emergencia;
  const prevPercent = totalTrendOS > 0 ? Math.round(osTrendTotals.preventiva / totalTrendOS * 100) : kpis.preventivas_percent;
  const corrPercent = totalTrendOS > 0 ? Math.round(osTrendTotals.corretiva / totalTrendOS * 100) : kpis.corretivas_percent;
  
  const osTypes = [
    { name: 'Corretiva', value: osTrendTotals.corretiva, fill: '#ef4444', key: 'corretiva' },
    { name: 'Preventiva', value: osTrendTotals.preventiva, fill: '#10b981', key: 'preventiva' },
    { name: 'Preditiva', value: osTrendTotals.preditiva, fill: '#3b82f6', key: 'preditiva' },
    { name: 'Emergência', value: osTrendTotals.emergencia, fill: '#f59e0b', key: 'emergencia' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100" data-testid="dashboard-title">Dashboard Operacional</h1>
          <p className="text-sm text-slate-500">Monitoramento em tempo real da confiabilidade e desempenho operacional dos ativos</p>
        </div>
        <div className="flex gap-2">
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
            <p className="text-xs text-slate-600 mt-1">{kpis.ativos_operacionais} de {kpis.ativos_total} ativos</p>
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
                <p className="text-3xl font-black text-emerald-400 tabular-nums">{prevPercent}<span className="text-sm">%</span></p>
                <p className="text-[10px] text-emerald-600">preventiva</p>
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
          <h3 className="text-sm font-bold text-slate-300 mb-4">Tendência MTBF / MTTR</h3>
          <div className="h-64" data-testid="chart-trend">
            <TrendChart data={trend} />
          </div>
        </div>

        {/* Gráfico 2 - Distribuição OS */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h3 className="text-sm font-bold text-slate-300 mb-4">Distribuição de OS por Tipo</h3>
          <div className="h-64" data-testid="chart-os-dist">
            <OSDistChart data={osTypes} onBarClick={(key) => drillDown(key, `OS ${key.charAt(0).toUpperCase() + key.slice(1)}`)} />
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
                    {item.ativo && <span className="font-mono text-xs text-emerald-400">{item.ativo.tag}</span>}
                    {item.tag && <span className="font-mono text-xs text-emerald-400">{item.tag}</span>}
                    {item.sku && <span className="font-mono text-xs text-purple-400">{item.sku}</span>}
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
  const { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } = require('recharts');
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="mes" tick={{ fill: '#94a3b8', fontSize: 12 }} stroke="#475569" />
        <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} stroke="#475569" />
        <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#e2e8f0' }} />
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
  const [areas, setAreas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterCriticidade, setFilterCriticidade] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  
  useEffect(() => {
    const status = searchParams.get('status');
    if (status) setFilterStatus(status);
  }, [searchParams]);
  
  const fetchData = async () => {
    try {
      const [ativosRes, areasRes] = await Promise.all([
        api.get('/ativos'),
        api.get('/areas')
      ]);
      setAtivos(ativosRes.data);
      setAreas(areasRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => { fetchData(); }, []);
  
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
    if (filterStatus && a.status !== filterStatus) return false;
    if (filterCriticidade && a.criticidade !== filterCriticidade) return false;
    if (search) {
      const s = search.toLowerCase();
      return a.tag?.toLowerCase().includes(s) || a.nome?.toLowerCase().includes(s);
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
        {user?.role === 'admin' && (
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
            placeholder="Buscar por TAG ou nome..."
            className="input-industrial w-full pl-10 pr-4"
          />
        </div>
        <Select
          value={filterStatus}
          onChange={setFilterStatus}
          options={[
            { value: 'operacional', label: 'Operacional' },
            { value: 'parado', label: 'Parado' },
            { value: 'manutencao', label: 'Manutenção' },
          ]}
          placeholder="Status"
          className="w-40"
        />
        <Select
          value={filterCriticidade}
          onChange={setFilterCriticidade}
          options={[
            { value: 'critica', label: 'Crítica' },
            { value: 'alta', label: 'Alta' },
            { value: 'media', label: 'Média' },
            { value: 'baixa', label: 'Baixa' },
          ]}
          placeholder="Criticidade"
          className="w-40"
        />
      </div>
      
      {loading ? <Loading rows={5} /> : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((ativo) => (
            <div key={ativo.id} className="glass-card p-4 hover:border-slate-600 transition-all group">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate(`/ativos/${ativo.id}`)}>
                  <div className={`p-2 rounded-lg ${
                    ativo.status === 'operacional' ? 'bg-emerald-500/10' :
                    ativo.status === 'parado' ? 'bg-red-500/10' : 'bg-amber-500/10'
                  }`}>
                    <Box size={22} className={
                      ativo.status === 'operacional' ? 'text-emerald-400' :
                      ativo.status === 'parado' ? 'text-red-400' : 'text-amber-400'
                    } />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-emerald-400 text-sm">{ativo.tag}</span>
                      {ativo.area && <span className="text-xs text-slate-500 px-2 py-0.5 bg-slate-800 rounded">{ativo.area.nome}</span>}
                    </div>
                    <p className="text-slate-100">{ativo.nome}</p>
                    {ativo.fabricante && <p className="text-xs text-slate-500">{ativo.fabricante} {ativo.modelo}</p>}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {user?.role === 'admin' && (
                    <div className="hidden group-hover:flex items-center gap-1">
                      <button onClick={() => { setEditItem(ativo); setShowModal(true); }} className="p-2 hover:bg-slate-700 rounded-lg">
                        <Edit size={16} className="text-slate-400" />
                      </button>
                      <button onClick={() => setDeleteItem(ativo)} className="p-2 hover:bg-red-500/10 rounded-lg">
                        <Trash2 size={16} className="text-red-400" />
                      </button>
                    </div>
                  )}
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
        <EmptyState icon={Box} title="Nenhum ativo encontrado" description="Não há ativos com os filtros selecionados." action={() => setShowModal(true)} actionLabel="Criar Ativo" />
      )}
      
      <ModalNovoAtivo
        isOpen={showModal}
        onClose={() => { setShowModal(false); setEditItem(null); }}
        onSuccess={fetchData}
        areas={areas}
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
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const fetchAtivo = async () => {
    try {
      const [ativoRes, manuaisRes] = await Promise.all([
        api.get(`/ativos/${id}`),
        api.get(`/ativos/${id}/manuais`)
      ]);
      setAtivo(ativoRes.data);
      setManuais(manuaisRes.data);
    } catch (error) {
      toast.error('Ativo não encontrado');
      navigate('/ativos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAtivo(); }, [id]);
  
  const handleUploadManual = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      toast.error('Apenas arquivos PDF são permitidos');
      return;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      await api.post(`/ativos/${id}/manual`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      toast.success('Manual carregado com sucesso!');
      const res = await api.get(`/ativos/${id}/manuais`);
      setManuais(res.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao carregar manual');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteManual = async (manualId) => {
    try {
      await api.delete(`/manuais/${manualId}`);
      toast.success('Manual removido');
      setManuais(prev => prev.filter(m => m.id !== manualId));
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao remover');
    }
  };

  if (loading) return <Loading rows={4} />;
  if (!ativo) return null;
  
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/ativos')} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg">
          <ArrowLeft size={20} className="text-slate-400" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-emerald-400">{ativo.tag}</span>
            <StatusBadge status={ativo.status} size="sm" />
            <PriorityBadge priority={ativo.criticidade} />
          </div>
          <h1 className="text-xl font-bold text-slate-100">{ativo.nome}</h1>
        </div>
      </div>
      
      {/* QR Code */}
      <div className="glass-card p-4 flex items-center gap-4">
        <div className="bg-white p-3 rounded-lg">
          <QRCodeSVG 
            value={`${window.location.origin}/ativos/${ativo.id}`} 
            size={80} 
            level="H"
            includeMargin={false}
          />
        </div>
        <div>
          <p className="text-sm text-slate-400">QR Code</p>
          <p className="font-mono text-xs text-slate-500">{ativo.tag}</p>
          <p className="text-xs text-slate-600 mt-1">Escaneie para acessar este ativo</p>
        </div>
      </div>
      
      {/* Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass-card p-4 space-y-3">
          <h3 className="text-sm font-semibold text-emerald-400">Informações Técnicas</h3>
          {ativo.tipo_equipamento && <div className="flex justify-between text-sm"><span className="text-slate-500">Tipo</span><span className="text-slate-200">{ativo.tipo_equipamento}</span></div>}
          {ativo.fabricante && <div className="flex justify-between text-sm"><span className="text-slate-500">Fabricante</span><span className="text-slate-200">{ativo.fabricante}</span></div>}
          {ativo.modelo && <div className="flex justify-between text-sm"><span className="text-slate-500">Modelo</span><span className="text-slate-200">{ativo.modelo}</span></div>}
          {ativo.numero_serie && <div className="flex justify-between text-sm"><span className="text-slate-500">Nº Série</span><span className="text-slate-200 font-mono">{ativo.numero_serie}</span></div>}
        </div>
        
        <div className="glass-card p-4 space-y-3">
          <h3 className="text-sm font-semibold text-blue-400">Estatísticas</h3>
          <div className="flex justify-between text-sm"><span className="text-slate-500">Total OS</span><span className="text-slate-200">{ativo.estatisticas?.total_os || 0}</span></div>
          <div className="flex justify-between text-sm"><span className="text-slate-500">Corretivas</span><span className="text-red-400">{ativo.estatisticas?.os_corretivas || 0}</span></div>
          <div className="flex justify-between text-sm"><span className="text-slate-500">Preventivas</span><span className="text-emerald-400">{ativo.estatisticas?.os_preventivas || 0}</span></div>
        </div>
      </div>
      
      {/* Recent OS */}
      {ativo.ordens_servico?.length > 0 && (
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-slate-400 mb-3">Últimas OS</h3>
          <div className="space-y-2">
            {ativo.ordens_servico.slice(0, 5).map(os => (
              <div key={os.id} className="flex items-center justify-between p-2 bg-slate-800/50 rounded-lg cursor-pointer hover:bg-slate-800" onClick={() => navigate(`/os/${os.id}`)}>
                <div>
                  <span className="font-mono text-emerald-400 text-sm">#{os.numero}</span>
                  <p className="text-sm text-slate-300">{os.titulo}</p>
                </div>
                <StatusBadge status={os.status} size="sm" />
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Manuais PDF */}
      <div className="glass-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-blue-400 flex items-center gap-2"><FileText size={16} /> Manuais Técnicos</h3>
          {user?.role === 'admin' && (
            <label className="btn-primary text-sm flex items-center gap-2 cursor-pointer" data-testid="upload-manual-btn">
              <Upload size={16} /> {uploading ? 'Enviando...' : 'Enviar PDF'}
              <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleUploadManual} className="hidden" disabled={uploading} />
            </label>
          )}
        </div>
        {manuais.length > 0 ? (
          <div className="space-y-2">
            {manuais.map((m) => (
              <div key={m.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg group">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-500/10 rounded-lg"><FileText size={20} className="text-red-400" /></div>
                  <div>
                    <p className="text-sm text-slate-200">{m.filename}</p>
                    <p className="text-xs text-slate-500">{(m.size_bytes / 1024).toFixed(0)} KB • {new Date(m.created_at).toLocaleDateString('pt-BR')}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => {
                    const url = `${BACKEND_URL}${m.url}`;
                    window.open(url, '_blank');
                  }} className="p-2 hover:bg-blue-500/10 rounded-lg transition-colors" title="Abrir PDF">
                    <Eye size={16} className="text-blue-400" />
                  </button>
                  <button onClick={async () => {
                    try {
                      const res = await fetch(`${BACKEND_URL}${m.url}`);
                      const blob = await res.blob();
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url; a.download = m.filename; a.click();
                      window.URL.revokeObjectURL(url);
                    } catch { toast.error('Erro ao baixar'); }
                  }} className="p-2 hover:bg-emerald-500/10 rounded-lg transition-colors" title="Baixar PDF">
                    <Download size={16} className="text-emerald-400" />
                  </button>
                  {user?.role === 'admin' && (
                    <button onClick={() => handleDeleteManual(m.id)} className="p-2 hover:bg-red-500/10 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity" title="Remover">
                      <Trash2 size={16} className="text-red-400" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-slate-500">
            <FileText size={32} className="mx-auto mb-2 opacity-30" />
            <p className="text-sm">Nenhum manual carregado</p>
            {user?.role === 'admin' && <p className="text-xs mt-1">Clique em "Enviar PDF" para adicionar</p>}
          </div>
        )}
      </div>

      {/* Actions - Ativo Detail */}
      <div className="grid grid-cols-2 gap-3">
        <button onClick={() => navigate(`/inspecoes?new=true&ativo=${ativo.id}`)} className="btn-primary py-4 flex items-center justify-center gap-2">
          <ClipboardCheck size={20} /> Nova Inspeção
        </button>
        <button onClick={() => navigate(`/os?new=true&ativo=${ativo.id}`)} className="btn-secondary py-4 flex items-center justify-center gap-2">
          <Wrench size={20} /> Nova OS
        </button>
      </div>
    </div>
  );
};

// OS Page
const OSPage = () => {
  const [osList, setOsList] = useState([]);
  const [ativos, setAtivos] = useState([]);
  const [tecnicos, setTecnicos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  useEffect(() => {
    if (searchParams.get('new') === 'true') setShowModal(true);
  }, [searchParams]);
  
  const fetchData = async () => {
    try {
      const [osRes, ativosRes, tecnicosRes] = await Promise.all([
        api.get('/ordens-servico'),
        api.get('/ativos'),
        api.get('/users/tecnicos')
      ]);
      setOsList(osRes.data);
      setAtivos(ativosRes.data);
      setTecnicos(tecnicosRes.data);
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
  
  const filtered = filter ? osList.filter(os => os.status === filter) : osList;
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-slate-100">Ordens de Serviço</h1>
          <ExportButtons entity="ordens-servico" />
        </div>
        <button onClick={() => { setEditItem(null); setShowModal(true); }} className="btn-primary flex items-center gap-2" data-testid="add-os-btn">
          <Plus size={20} /> Nova OS
        </button>
      </div>
      
      {/* Filters */}
      <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-2">
        {[
          { value: '', label: 'Todas' },
          { value: 'aberta', label: 'Abertas' },
          { value: 'planejada', label: 'Planejadas' },
          { value: 'em_execucao', label: 'Em Execução' },
          { value: 'pausada', label: 'Pausadas' },
          { value: 'concluida', label: 'Concluídas' },
        ].map(f => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-4 py-2 rounded-lg whitespace-nowrap transition-all ${
              filter === f.value ? 'bg-emerald-500 text-slate-950 font-semibold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>
      
      {loading ? <Loading rows={5} /> : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((os) => (
            <div key={os.id} className="glass-card p-4 hover:border-slate-600 transition-all group">
              <div className="flex items-center justify-between">
                <div className="flex-1 cursor-pointer" onClick={() => navigate(`/os/${os.id}`)}>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-emerald-400">#{os.numero}</span>
                    {os.ativo && <span className="text-xs text-slate-500">{os.ativo.tag}</span>}
                    {os.atrasada && <span className="text-xs bg-red-500 text-white px-2 py-0.5 rounded">ATRASADA</span>}
                  </div>
                  <p className="text-slate-100">{os.titulo}</p>
                  {os.responsavel && <p className="text-xs text-slate-500"><User size={12} className="inline mr-1" />{os.responsavel.nome}</p>}
                </div>
                <div className="flex items-center gap-2">
                  <div className="hidden group-hover:flex items-center gap-1">
                    <button onClick={() => { setEditItem(os); setShowModal(true); }} className="p-2 hover:bg-slate-700 rounded-lg">
                      <Edit size={16} className="text-slate-400" />
                    </button>
                    <button onClick={() => setDeleteItem(os)} className="p-2 hover:bg-red-500/10 rounded-lg">
                      <Trash2 size={16} className="text-red-400" />
                    </button>
                  </div>
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
      
      <ModalNovaOS
        isOpen={showModal}
        onClose={() => { setShowModal(false); setEditItem(null); }}
        onSuccess={fetchData}
        ativos={ativos}
        tecnicos={tecnicos}
        editData={editItem}
      />
      
      <ConfirmDialog
        isOpen={!!deleteItem}
        onClose={() => setDeleteItem(null)}
        onConfirm={handleDelete}
        title="Excluir OS"
        message={`Tem certeza que deseja excluir a OS #${deleteItem?.numero}?`}
        confirmText="Excluir"
        danger
      />
    </div>
  );
};

// OS Detail
const OSDetailPage = () => {
  const { id } = useParams();
  const [os, setOs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const navigate = useNavigate();
  
  const fetchOS = async () => {
    try {
      const response = await api.get(`/ordens-servico/${id}`);
      setOs(response.data);
    } catch (error) {
      toast.error('OS não encontrada');
      navigate('/os');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => { fetchOS(); }, [id]);
  
  const handleAction = async (action) => {
    setUpdating(true);
    try {
      await api.post(`/ordens-servico/${id}/${action}`);
      toast.success(`OS ${action === 'iniciar' ? 'iniciada' : action === 'pausar' ? 'pausada' : 'concluída'}!`);
      fetchOS();
    } catch (error) {
      toast.error('Erro na ação');
    } finally {
      setUpdating(false);
    }
  };
  
  if (loading) return <Loading rows={4} />;
  if (!os) return null;
  
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/os')} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg">
          <ArrowLeft size={20} className="text-slate-400" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-emerald-400">#{os.numero}</span>
            <StatusBadge status={os.status} size="sm" />
            <PriorityBadge priority={os.prioridade} />
          </div>
          <h1 className="text-xl font-bold text-slate-100">{os.titulo}</h1>
        </div>
      </div>
      
      {/* Ativo */}
      {os.ativo && (
        <div className="glass-card p-4 cursor-pointer hover:border-slate-600" onClick={() => navigate(`/ativos/${os.ativo.id}`)}>
          <p className="text-xs text-slate-500">Ativo</p>
          <div className="flex items-center justify-between">
            <div>
              <span className="font-mono text-emerald-400">{os.ativo.tag}</span>
              <p className="text-slate-200">{os.ativo.nome}</p>
            </div>
            <ChevronRight className="text-slate-600" />
          </div>
        </div>
      )}
      
      {/* Info */}
      <div className="glass-card p-4 space-y-3">
        <div className="flex justify-between text-sm"><span className="text-slate-500">Tipo</span><span className="text-slate-200 capitalize">{os.tipo}</span></div>
        {os.responsavel && <div className="flex justify-between text-sm"><span className="text-slate-500">Responsável</span><span className="text-slate-200">{os.responsavel.nome}</span></div>}
        <div className="flex justify-between text-sm"><span className="text-slate-500">Abertura</span><span className="text-slate-200">{new Date(os.data_abertura).toLocaleString('pt-BR')}</span></div>
        {os.data_inicio && <div className="flex justify-between text-sm"><span className="text-slate-500">Início</span><span className="text-slate-200">{new Date(os.data_inicio).toLocaleString('pt-BR')}</span></div>}
        {os.data_conclusao && <div className="flex justify-between text-sm"><span className="text-slate-500">Conclusão</span><span className="text-slate-200">{new Date(os.data_conclusao).toLocaleString('pt-BR')}</span></div>}
        {os.tempo_execucao_minutos && <div className="flex justify-between text-sm border-t border-slate-800 pt-2"><span className="text-slate-500">Tempo Execução</span><span className="text-emerald-400 font-semibold">{Math.floor(os.tempo_execucao_minutos / 60)}h {os.tempo_execucao_minutos % 60}min</span></div>}
      </div>
      
      {os.descricao && (
        <div className="glass-card p-4">
          <p className="text-xs text-slate-500 mb-1">Descrição</p>
          <p className="text-slate-200 whitespace-pre-wrap">{os.descricao}</p>
        </div>
      )}
      
      {/* Actions */}
      {!['concluida', 'cancelada'].includes(os.status) && (
        <div className="space-y-2">
          {os.status === 'aberta' && (
            <button onClick={() => handleAction('iniciar')} disabled={updating} className="btn-primary w-full flex items-center justify-center gap-2">
              <Play size={20} /> {updating ? 'Iniciando...' : 'Iniciar OS'}
            </button>
          )}
          {os.status === 'em_execucao' && (
            <>
              <button onClick={() => handleAction('concluir')} disabled={updating} className="btn-primary w-full flex items-center justify-center gap-2">
                <CheckCircle size={20} /> {updating ? 'Finalizando...' : 'Concluir OS'}
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
  const [searchParams] = useSearchParams();
  
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
    i.nome.toLowerCase().includes(search.toLowerCase()) || i.sku.toLowerCase().includes(search.toLowerCase())
  ) : items;
  
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
            placeholder="Buscar por nome ou SKU..."
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
            <div key={item.id} className={`glass-card p-4 hover:border-slate-600 transition-all group ${item.is_critico ? 'border-red-500/50' : ''}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${item.is_critico ? 'bg-red-500/10' : 'bg-emerald-500/10'}`}>
                    <Package size={20} className={item.is_critico ? 'text-red-400' : 'text-emerald-400'} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-emerald-400 text-sm">{item.sku}</span>
                      <span className="text-xs text-slate-500 px-2 py-0.5 bg-slate-800 rounded capitalize">{item.categoria}</span>
                    </div>
                    <p className="text-slate-100">{item.nome}</p>
                    {item.prateleira && <p className="text-xs text-slate-500"><MapPin size={12} className="inline mr-1" />{item.almoxarifado} - {item.prateleira}</p>}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="hidden group-hover:flex items-center gap-1">
                    <button onClick={() => { setEditItem(item); setShowModal(true); }} className="p-2 hover:bg-slate-700 rounded-lg">
                      <Edit size={16} className="text-slate-400" />
                    </button>
                    <button onClick={() => setDeleteItem(item)} className="p-2 hover:bg-red-500/10 rounded-lg">
                      <Trash2 size={16} className="text-red-400" />
                    </button>
                  </div>
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
        message={`Tem certeza que deseja excluir "${deleteItem?.sku} - ${deleteItem?.nome}"?`}
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
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [deleteItem, setDeleteItem] = useState(null);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  useEffect(() => {
    if (searchParams.get('new') === 'true') setShowModal(true);
  }, [searchParams]);
  
  const fetchData = async () => {
    try {
      const [inspRes, ativosRes, rotasRes, tecnicosRes] = await Promise.all([
        api.get('/inspecoes'),
        api.get('/ativos'),
        api.get('/rotas-inspecao'),
        api.get('/users/tecnicos')
      ]);
      setInspecoes(inspRes.data);
      setAtivos(ativosRes.data);
      setRotas(rotasRes.data);
      setTecnicos(tecnicosRes.data);
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
      
      {loading ? <Loading rows={5} /> : inspecoes.length > 0 ? (
        <div className="space-y-2">
          {inspecoes.map((insp) => (
            <div key={insp.id} className="glass-card p-4 hover:border-slate-600 transition-all group">
              <div className="flex items-center justify-between">
                <div className="flex-1 cursor-pointer" onClick={() => navigate(`/inspecoes/${insp.id}`)}>
                  <div className="flex items-center gap-2 mb-1">
                    {insp.ativo && <span className="font-mono text-emerald-400 text-sm">{insp.ativo.tag}</span>}
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
                  <button onClick={() => setDeleteItem(insp)} className="p-2 hover:bg-red-500/10 rounded-lg opacity-0 group-hover:opacity-100">
                    <Trash2 size={16} className="text-red-400" />
                  </button>
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
        <EmptyState icon={ClipboardCheck} title="Nenhuma inspeção" description="Crie uma nova inspeção." action={() => setShowModal(true)} actionLabel="Nova Inspeção" />
      )}
      
      <ModalNovaInspecao
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={fetchData}
        ativos={ativos}
        rotas={rotas}
        tecnicos={tecnicos}
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
    const missing = checklist.filter(item => item.obrigatorio && item.resultado === undefined);
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
      toast.error('Erro ao concluir');
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) return <Loading rows={4} />;
  if (!inspecao) return null;
  
  const isFinished = ['concluida', 'com_pendencias'].includes(inspecao.status);
  
  return (
    <div className="space-y-4 pb-24">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/inspecoes')} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg">
          <ArrowLeft size={20} className="text-slate-400" />
        </button>
        <div className="flex-1">
          {inspecao.ativo && <span className="font-mono text-emerald-400">{inspecao.ativo.tag}</span>}
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
        </div>
      </div>
      
      {/* Lubrificação Info */}
      {inspecao.tipo === 'lubrificacao' && (inspecao.tipo_lubrificante || inspecao.ponto_lubrificacao) && (
        <div className="glass-card p-4 space-y-2 border-amber-500/30">
          <h3 className="text-sm font-semibold text-amber-400 flex items-center gap-2"><Droplet size={16} /> Dados da Lubrificação</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {inspecao.tipo_lubrificante && (
              <div><span className="text-slate-500">Lubrificante:</span> <span className="text-slate-200 capitalize">{inspecao.tipo_lubrificante.replace(/_/g, ' ')}</span></div>
            )}
            {inspecao.quantidade_lubrificante && (
              <div><span className="text-slate-500">Quantidade:</span> <span className="text-slate-200">{inspecao.quantidade_lubrificante}</span></div>
            )}
            {inspecao.ponto_lubrificacao && (
              <div><span className="text-slate-500">Ponto:</span> <span className="text-slate-200">{inspecao.ponto_lubrificacao}</span></div>
            )}
            {inspecao.metodo_aplicacao && (
              <div><span className="text-slate-500">Método:</span> <span className="text-slate-200 capitalize">{inspecao.metodo_aplicacao}</span></div>
            )}
          </div>
          {inspecao.observacoes_lubrificacao && (
            <p className="text-xs text-slate-400 mt-2">{inspecao.observacoes_lubrificacao}</p>
          )}
        </div>
      )}
      
      {inspecao.status === 'pendente' && (
        <button onClick={handleIniciar} className="btn-primary w-full flex items-center justify-center gap-2">
          <Play size={20} /> Iniciar Inspeção
        </button>
      )}
      
      {/* Checklist */}
      {inspecao.status !== 'pendente' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm text-slate-400">Checklist</h3>
            <span className="text-xs text-slate-500">
              {checklist.filter(i => i.resultado !== undefined).length}/{checklist.length} respondidos
            </span>
          </div>
          
          {checklist.map((item, idx) => {
            const itemTipo = item.tipo || 'boolean';
            return (
            <div key={item.id} className={`glass-card p-4 ${item.resultado !== undefined ? 'border-emerald-500/30' : ''}`}>
              <div className="flex items-start gap-3">
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                  item.resultado !== undefined ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 text-slate-400'
                }`}>{idx + 1}</span>
                <div className="flex-1">
                  <p className="text-slate-200">{item.descricao}</p>
                  {item.obrigatorio && <span className="text-xs text-red-400">* Obrigatório</span>}
                  
                  {!isFinished && itemTipo === 'boolean' && (
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={() => {
                          handleItemChange(item.id, 'resultado', true);
                          handleItemChange(item.id, 'conforme', true);
                        }}
                        className={`flex-1 py-3 rounded-lg border transition-all ${
                          item.resultado === true ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400' : 'border-slate-700 text-slate-400'
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
                          item.resultado === false ? 'bg-red-500/20 border-red-500 text-red-400' : 'border-slate-700 text-slate-400'
                        }`}
                      >
                        <XCircle size={20} className="mx-auto mb-1" />
                        Não Conforme
                      </button>
                    </div>
                  )}
                  
                  {!isFinished && itemTipo === 'numero' && (
                    <div className="mt-3 flex gap-2">
                      <input
                        type="number"
                        step="0.1"
                        value={item.resultado || ''}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value);
                          handleItemChange(item.id, 'resultado', val);
                          if (item.tolerancia_min !== undefined && item.tolerancia_max !== undefined) {
                            handleItemChange(item.id, 'conforme', val >= item.tolerancia_min && val <= item.tolerancia_max);
                          }
                        }}
                        placeholder={item.valor_esperado ? `Esperado: ${item.valor_esperado}` : 'Valor'}
                        className="input-industrial flex-1 px-4"
                      />
                      {item.unidade && <span className="input-industrial px-4 flex items-center text-slate-400">{item.unidade}</span>}
                    </div>
                  )}
                  
                  {!isFinished && itemTipo === 'texto' && (
                    <textarea
                      value={item.resultado || ''}
                      onChange={(e) => handleItemChange(item.id, 'resultado', e.target.value)}
                      className="input-industrial w-full px-4 py-3 mt-3"
                      rows={2}
                    />
                  )}
                  
                  {isFinished && (
                    <div className="mt-2">
                      {itemTipo === 'boolean' && (
                        <StatusBadge status={item.conforme ? 'conforme' : 'nao_conforme'} size="sm" />
                      )}
                      {itemTipo === 'numero' && item.resultado !== undefined && (
                        <span className={`text-sm ${item.conforme ? 'text-emerald-400' : 'text-red-400'}`}>
                          {item.resultado} {item.unidade}
                        </span>
                      )}
                      {itemTipo === 'texto' && item.resultado && (
                        <p className="text-sm text-slate-300">{item.resultado}</p>
                      )}
                    </div>
                  )}
                  
                  {!isFinished && item.resultado === false && itemTipo === 'boolean' && (
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
              <CheckCircle size={24} className="text-emerald-400" />
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
      
      {inspecao.os_gerada && (
        <div className="glass-card p-4 border-amber-500/50 cursor-pointer" onClick={() => navigate(`/os/${inspecao.os_gerada.id}`)}>
          <p className="text-xs text-slate-500">OS Gerada</p>
          <div className="flex items-center justify-between">
            <span className="font-mono text-amber-400">#{inspecao.os_gerada.numero}</span>
            <ChevronRight className="text-slate-600" />
          </div>
        </div>
      )}
      
      {/* Action */}
      {inspecao.status === 'em_andamento' && (
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
  
  if (loading) return <Loading rows={4} />;
  
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-100">Modo Ronda</h1>
      <p className="text-slate-500">Selecione uma área para iniciar a ronda de inspeção</p>
      
      <div className="space-y-3">
        {areas.map(({ area, total_ativos }) => (
          <div
            key={area.id}
            className="glass-card p-4 cursor-pointer hover:border-emerald-500/50 transition-all"
            onClick={() => navigate(`/ronda/${area.id}`)}
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

// Scanner Page
const ScannerPage = () => {
  const [manualCode, setManualCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const navigate = useNavigate();
  
  const resolveScannedValue = async (value) => {
    // If scanned value is a URL containing /ativos/, extract the ID
    const ativoMatch = value.match(/\/ativos\/([a-f0-9-]+)/i);
    if (ativoMatch) {
      navigate(`/ativos/${ativoMatch[1]}`);
      return;
    }
    // Otherwise try QR code field, then TAG
    try {
      const response = await api.get(`/ativos/qr/${value}`);
      navigate(`/ativos/${response.data.id}`);
      return;
    } catch {}
    try {
      const response = await api.get(`/ativos/tag/${value.toUpperCase()}`);
      navigate(`/ativos/${response.data.id}`);
      return;
    } catch {}
    toast.error('Ativo não encontrado');
  };

  const handleSearch = async () => {
    if (!manualCode.trim()) return;
    setLoading(true);
    try {
      await resolveScannedValue(manualCode.trim());
    } finally {
      setLoading(false);
    }
  };

  const startCamera = async () => {
    setCameraError('');
    setScanning(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      // Use BarcodeDetector if available
      if ('BarcodeDetector' in window) {
        const detector = new window.BarcodeDetector({ formats: ['qr_code'] });
        const scanLoop = async () => {
          if (!streamRef.current || !videoRef.current) return;
          try {
            const barcodes = await detector.detect(videoRef.current);
            if (barcodes.length > 0) {
              const value = barcodes[0].rawValue;
              stopCamera();
              toast.success('QR Code detectado!');
              await resolveScannedValue(value);
              return;
            }
          } catch {}
          if (streamRef.current) requestAnimationFrame(scanLoop);
        };
        // Wait for video to be ready
        videoRef.current.onloadedmetadata = () => {
          scanLoop();
        };
      } else {
        setCameraError('BarcodeDetector não suportado neste navegador. Use a busca manual por TAG.');
      }
    } catch (err) {
      setCameraError('Não foi possível acessar a câmera. Verifique as permissões.');
      setScanning(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    setScanning(false);
  };

  useEffect(() => {
    return () => stopCamera();
  }, []);
  
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-100">Identificar Ativo</h1>
      
      {scanning ? (
        <div className="glass-card p-4 space-y-4">
          <div className="relative rounded-lg overflow-hidden bg-black aspect-video">
            <video ref={videoRef} className="w-full h-full object-cover" playsInline muted />
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="w-48 h-48 border-2 border-emerald-400 rounded-lg animate-pulse opacity-60" />
            </div>
          </div>
          {cameraError && <p className="text-sm text-amber-400 text-center">{cameraError}</p>}
          <button onClick={stopCamera} className="btn-secondary w-full flex items-center justify-center gap-2">
            <X size={20} /> Fechar Câmera
          </button>
        </div>
      ) : (
        <div className="glass-card p-8 flex flex-col items-center justify-center gap-4">
          <div className="w-24 h-24 rounded-full bg-emerald-500/10 flex items-center justify-center">
            <Camera size={48} className="text-emerald-400" />
          </div>
          <div className="text-center">
            <p className="text-lg text-slate-200">Escanear QR Code</p>
            <p className="text-sm text-slate-500">Use a câmera para ler o código do ativo</p>
          </div>
          <button onClick={startCamera} className="btn-primary" data-testid="open-camera-btn">Abrir Câmera</button>
        </div>
      )}
      
      <div className="flex items-center gap-4">
        <div className="flex-1 h-px bg-slate-800"></div>
        <span className="text-slate-500 text-sm">ou</span>
        <div className="flex-1 h-px bg-slate-800"></div>
      </div>
      
      <div className="glass-card p-4 space-y-4">
        <p className="text-sm text-slate-400">Buscar por TAG do ativo</p>
        <div className="flex gap-2">
          <input
            type="text"
            value={manualCode}
            onChange={(e) => setManualCode(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Ex: BOM-001"
            className="input-industrial flex-1 px-4 font-mono"
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


// ============== SOBRESSALENTES PAGE ==============

const SobressalentesPage = () => {
  const [spares, setSpares] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ descricao: '', modelo: '', fabricante: '', status: 'estoque', localizacao: '', custo: '' });
  const [saving, setSaving] = useState(false);
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
      await api.post('/sobressalentes', { ...form, custo: form.custo ? parseFloat(form.custo) : null });
      toast.success('Sobressalente criado!');
      setShowModal(false);
      setForm({ descricao: '', modelo: '', fabricante: '', status: 'estoque', localizacao: '', custo: '' });
      fetchData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro'); }
    finally { setSaving(false); }
  };

  const handleExport = (fmt) => { window.open(`${API}/export/sobressalentes?format=${fmt}&token=${localStorage.getItem('manutrix_token')}`, '_blank'); };

  const filtered = search ? spares.filter(s => s.descricao?.toLowerCase().includes(search.toLowerCase()) || s.tag?.toLowerCase().includes(search.toLowerCase())) : spares;

  const statusConfig = {
    estoque: { class: 'bg-emerald-500/10 text-emerald-400', label: 'Em Estoque' },
    em_uso: { class: 'bg-blue-500/10 text-blue-400', label: 'Em Uso' },
    em_reforma: { class: 'bg-amber-500/10 text-amber-400', label: 'Em Reforma' },
    descartado: { class: 'bg-red-500/10 text-red-400', label: 'Descartado' },
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Sobressalentes</h1>
        <div className="flex gap-2">
          {['admin','pcm'].includes(user?.role) && (
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
          {filtered.map((sp) => (
            <div key={sp.id} className="glass-card p-4 hover:border-slate-600 transition-all">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-emerald-400 text-sm">{sp.tag}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${statusConfig[sp.status]?.class || ''}`}>{statusConfig[sp.status]?.label || sp.status}</span>
                  </div>
                  <p className="text-slate-100">{sp.descricao}</p>
                  <p className="text-xs text-slate-500">{[sp.fabricante, sp.modelo, sp.localizacao].filter(Boolean).join(' • ')}</p>
                  {sp.ativo_vinculado && <p className="text-xs text-blue-400 mt-1">Ativo: {sp.ativo_vinculado.tag} - {sp.ativo_vinculado.nome}</p>}
                </div>
                {sp.custo && <p className="text-lg font-bold text-slate-200">R$ {sp.custo.toFixed(2)}</p>}
              </div>
            </div>
          ))}
        </div>
      ) : <EmptyState icon={Cog} title="Nenhum sobressalente" description="Cadastre sobressalentes." />}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Novo Sobressalente" size="md">
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormInput label="Descrição" required>
            <input value={form.descricao} onChange={(e) => setForm({...form, descricao: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: Rolamento 6205-2RS" required />
          </FormInput>
          <div className="grid grid-cols-2 gap-4">
            <FormInput label="Fabricante"><input value={form.fabricante} onChange={(e) => setForm({...form, fabricante: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
            <FormInput label="Modelo"><input value={form.modelo} onChange={(e) => setForm({...form, modelo: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
            <FormInput label="Localização"><input value={form.localizacao} onChange={(e) => setForm({...form, localizacao: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: Almox A-01" /></FormInput>
            <FormInput label="Custo (R$)"><input type="number" step="0.01" value={form.custo} onChange={(e) => setForm({...form, custo: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
          </div>
          <FormInput label="Status">
            <Select value={form.status} onChange={(v) => setForm({...form, status: v})} options={[{value:'estoque',label:'Em Estoque'},{value:'em_uso',label:'Em Uso'},{value:'em_reforma',label:'Em Reforma'}]} />
          </FormInput>
          <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Salvando...' : 'Salvar'}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

// ============== ANOMALIAS PAGE ==============

const AnomaliasPage = () => {
  const [anomalias, setAnomalias] = useState([]);
  const [ativos, setAtivos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ ativo_id: '', descricao: '', severidade: 'media', gerar_os: true });
  const [saving, setSaving] = useState(false);

  const fetchData = async () => {
    try {
      const [anomRes, ativosRes] = await Promise.all([api.get('/anomalias'), api.get('/ativos')]);
      setAnomalias(anomRes.data);
      setAtivos(ativosRes.data);
    } catch (e) { toast.error('Erro ao carregar'); }
    finally { setLoading(false); }
  };
  useEffect(() => { fetchData(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.ativo_id || !form.descricao) { toast.error('Preencha ativo e descrição'); return; }
    setSaving(true);
    try {
      const res = await api.post('/anomalias', form);
      toast.success(`Anomalia criada! Prioridade: ${res.data.prioridade_os?.toUpperCase()}${res.data.os_gerada_id ? ' - OS gerada automaticamente' : ''}`);
      setShowModal(false);
      fetchData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro'); }
    finally { setSaving(false); }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Anomalias</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2" data-testid="add-anomalia-btn"><Plus size={20} /> Reportar Anomalia</button>
      </div>
      {loading ? <Loading rows={5} /> : anomalias.length > 0 ? (
        <div className="space-y-2">
          {anomalias.map((a) => (
            <div key={a.id} className="glass-card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    {a.ativo && <span className="font-mono text-emerald-400 text-sm">{a.ativo.tag}</span>}
                    <PriorityBadge priority={a.severidade} />
                    <span className="text-xs px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded">Score: {a.score_prioridade}</span>
                  </div>
                  <p className="text-slate-100">{a.descricao}</p>
                  <p className="text-xs text-slate-500">{new Date(a.created_at).toLocaleDateString('pt-BR')}</p>
                </div>
                <div className="flex items-center gap-2">
                  <PriorityBadge priority={a.prioridade_calculada} />
                  {a.os_gerada_id && <span className="text-xs px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded">OS Gerada</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : <EmptyState icon={AlertTriangle} title="Nenhuma anomalia" description="Reporte anomalias detectadas nos equipamentos." action={() => setShowModal(true)} actionLabel="Reportar" />}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Reportar Anomalia" size="md">
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormInput label="Equipamento" required>
            <Select value={form.ativo_id} onChange={(v) => setForm({...form, ativo_id: v})} options={ativos.map(a => ({value: a.id, label: `${a.tag} - ${a.nome}`}))} placeholder="Selecione..." />
          </FormInput>
          <FormInput label="Descrição da Anomalia" required>
            <textarea value={form.descricao} onChange={(e) => setForm({...form, descricao: e.target.value})} className="input-industrial w-full px-4 py-3 min-h-[100px]" placeholder="Descreva o problema encontrado..." required />
          </FormInput>
          <FormInput label="Severidade">
            <Select value={form.severidade} onChange={(v) => setForm({...form, severidade: v})} options={[{value:'baixa',label:'Baixa'},{value:'media',label:'Média'},{value:'alta',label:'Alta'},{value:'critica',label:'Crítica'}]} />
          </FormInput>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" checked={form.gerar_os} onChange={(e) => setForm({...form, gerar_os: e.target.checked})} className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-emerald-500" />
            <span className="text-slate-300">Gerar OS automaticamente</span>
          </label>
          <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Criando...' : 'Reportar'}</button>
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
      } catch {}
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
            <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mb-4"><Zap size={40} className="text-emerald-400" /></div>
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

// ============== ADMIN USUARIOS PAGE ==============

const AdminUsuariosPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ nome: '', email: '', password: '', role: 'tecnico', telefone: '' });
  const [saving, setSaving] = useState(false);
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
      setForm({ nome: '', email: '', password: '', role: 'tecnico', telefone: '' });
      fetchUsers();
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro'); }
    finally { setSaving(false); }
  };

  const handleDelete = async (uid) => {
    if (uid === user?.id) { toast.error('Não pode excluir a si mesmo'); return; }
    try { await api.delete(`/admin/users/${uid}`); toast.success('Removido'); fetchUsers(); } catch { toast.error('Erro'); }
  };

  const roleLabels = { admin: 'Administrador', gerente: 'Gerente', pcm: 'PCM', supervisor: 'Supervisor', tecnico: 'Técnico', inspetor: 'Inspetor', viewer: 'Visualizador' };
  const roleColors = { admin: 'text-red-400 bg-red-500/10', gerente: 'text-purple-400 bg-purple-500/10', pcm: 'text-blue-400 bg-blue-500/10', supervisor: 'text-amber-400 bg-amber-500/10', tecnico: 'text-emerald-400 bg-emerald-500/10', inspetor: 'text-cyan-400 bg-cyan-500/10', viewer: 'text-slate-400 bg-slate-500/10' };

  if (user?.role !== 'admin') return <EmptyState icon={Shield} title="Acesso Restrito" description="Apenas administradores podem gerenciar usuários." />;

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
                <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center"><User size={20} className="text-emerald-400" /></div>
                <div>
                  <p className="text-slate-100 font-medium">{u.nome}</p>
                  <p className="text-xs text-slate-500">{u.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-xs px-3 py-1 rounded-full font-medium ${roleColors[u.role] || ''}`}>{roleLabels[u.role] || u.role}</span>
                {u.id !== user?.id && (
                  <button onClick={() => handleDelete(u.id)} className="p-2 hover:bg-red-500/10 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"><Trash2 size={16} className="text-red-400" /></button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Novo Usuário" size="md">
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormInput label="Nome Completo" required><input value={form.nome} onChange={(e) => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-4" required /></FormInput>
          <div className="grid grid-cols-2 gap-4">
            <FormInput label="Email" required><input type="email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} className="input-industrial w-full px-4" required /></FormInput>
            <FormInput label="Senha" required><input type="password" value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} className="input-industrial w-full px-4" required /></FormInput>
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
            <p><span className="text-emerald-400">Técnico</span>: Preenche inspeções, abre anomalias</p>
          </div>
          <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Criando...' : 'Criar Usuário'}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

// ============== EXPORT BUTTONS COMPONENT ==============

const ExportButtons = ({ entity }) => {
  const { user } = useAuth();
  if (!['admin','pcm','gerente'].includes(user?.role)) return null;
  
  const handleExport = async (format) => {
    try {
      const res = await api.get(`/export/${entity}?format=${format}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `${entity}_manutrix.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      link.click();
      window.URL.revokeObjectURL(url);
      toast.success(`Exportado em ${format.toUpperCase()}`);
    } catch (e) { toast.error('Erro ao exportar'); }
  };

  return (
    <div className="flex gap-1">
      <button onClick={() => handleExport('excel')} className="p-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg transition-colors" title="Excel"><FileText size={16} /></button>
      <button onClick={() => handleExport('pdf')} className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors" title="PDF"><FileText size={16} /></button>
    </div>
  );
};

// ============== LAYOUT ==============

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen bg-slate-950 flex items-center justify-center"><Cog size={48} className="text-emerald-400 animate-spin" /></div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

const AppLayout = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  return (
    <div className="min-h-screen bg-slate-950 flex">
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
    const storedUser = localStorage.getItem('manutrix_user');
    if (storedUser) setUser(JSON.parse(storedUser));
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
  
  return <AuthContext.Provider value={{ user, login, logout, loading }}>{children}</AuthContext.Provider>;
};

// App
function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<ProtectedRoute><AppLayout><DashboardPage /></AppLayout></ProtectedRoute>} />
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
          <Route path="/anomalias" element={<ProtectedRoute><AppLayout><AnomaliasPage /></AppLayout></ProtectedRoute>} />
          <Route path="/assistente" element={<ProtectedRoute><AppLayout><AssistentePage /></AppLayout></ProtectedRoute>} />
          <Route path="/admin/usuarios" element={<ProtectedRoute><AppLayout><AdminUsuariosPage /></AppLayout></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster position="top-center" richColors />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
