/**
 * MAINTRIX — Shared UI Components
 * Extracted from App.js during RC1.5 modularization.
 * Pure presentational components with zero business logic.
 */
import { memo } from "react";
import {
  Clock, Search, Shield, Package, Calendar, CheckCircle, Play, Pause,
  Lock, XCircle, Activity, AlertTriangle, X
} from "lucide-react";

// ============== STATUS & PRIORITY BADGES ==============

export const StatusBadge = memo(({ status, size = 'md' }) => {
  const config = {
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
    aberta: { class: 'bg-blue-500/10 text-blue-400 border-blue-500/30', label: 'Aberta', icon: Clock },
    planejada: { class: 'bg-purple-500/10 text-purple-400 border-purple-500/30', label: 'Planejada', icon: Calendar },
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
});

export const PriorityBadge = memo(({ priority }) => {
  const config = {
    critica: { class: 'bg-red-500/20 border-red-500 text-red-400', label: 'Crítica' },
    emergencia: { class: 'bg-red-500/20 border-red-500 text-red-400', label: 'Emergência' },
    alta: { class: 'bg-amber-500/20 border-amber-500 text-amber-400', label: 'Alta' },
    media: { class: 'bg-emerald-500/20 border-emerald-500 text-emerald-400', label: 'Média' },
    baixa: { class: 'bg-slate-500/20 border-slate-500 text-slate-400', label: 'Baixa' },
  };
  const c = config[priority] || config.media;
  return <span className={`${c.class} border px-2 py-1 rounded text-xs font-medium`}>{c.label}</span>;
});

// ============== LAYOUT PRIMITIVES ==============

export const Modal = ({ isOpen, onClose, title, children, size = 'md' }) => {
  if (!isOpen) return null;
  const sizeClasses = { sm: 'max-w-md', md: 'max-w-2xl', lg: 'max-w-4xl', xl: 'max-w-6xl' };
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" data-testid="modal">
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose}></div>
      <div className="flex min-h-full items-center justify-center p-4">
        <div className={`relative w-full ${sizeClasses[size]} bg-surface border border-surface rounded-xl shadow-2xl animate-scaleIn`}>
          <div className="flex items-center justify-between p-4 border-b border-surface">
            <h2 className="text-xl font-bold text-primary">{title}</h2>
            <button onClick={onClose} className="p-2 hover:bg-surface-hover rounded-lg transition-colors">
              <X size={20} className="text-secondary" />
            </button>
          </div>
          <div className="p-4 max-h-[70vh] overflow-y-auto custom-scrollbar">{children}</div>
        </div>
      </div>
    </div>
  );
};

export const ConfirmDialog = ({ isOpen, onClose, onConfirm, title, message, confirmText = "Confirmar", danger = false }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose}></div>
      <div className="relative bg-surface border border-surface rounded-xl p-6 max-w-md w-full mx-4 animate-scaleIn">
        <h3 className="text-lg font-bold text-primary mb-2">{title}</h3>
        <p className="text-secondary mb-6">{message}</p>
        <div className="flex gap-3 justify-end">
          <button onClick={onClose} className="btn-secondary">Cancelar</button>
          <button onClick={onConfirm} className={danger ? "btn-destructive" : "btn-primary"}>{confirmText}</button>
        </div>
      </div>
    </div>
  );
};

// ============== FEEDBACK ==============

export const Loading = memo(({ rows = 3 }) => (
  <div className="space-y-3">
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="glass-card p-4 animate-pulse">
        <div className="h-4 bg-surface-hover rounded w-3/4 mb-2"></div>
        <div className="h-3 bg-surface-hover rounded w-1/2"></div>
      </div>
    ))}
  </div>
));

export const EmptyState = memo(({ icon: Icon, title, description, action, actionLabel }) => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <div className="w-16 h-16 rounded-full bg-surface flex items-center justify-center mb-4">
      <Icon size={32} className="text-secondary" />
    </div>
    <h3 className="text-lg text-primary font-semibold mb-2">{title}</h3>
    <p className="text-secondary max-w-sm mb-4">{description}</p>
    {action && <button onClick={action} className="btn-primary">{actionLabel}</button>}
  </div>
));

// ============== DATA DISPLAY ==============

export const DataTable = memo(({ headers, children, testId }) => (
  <div className="overflow-x-auto">
    <table className="w-full text-sm" data-testid={testId}>
      <thead>
        <tr className="border-b border-surface text-secondary text-xs uppercase">
          {headers.map((h, i) => (
            <th key={i} className={`py-2 px-3 ${h.align === 'right' ? 'text-right' : h.align === 'center' ? 'text-center' : 'text-left'} ${h.className || ''}`}>
              {h.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>{children}</tbody>
    </table>
  </div>
));

export const DataRow = memo(({ children, onClick, className = '' }) => (
  <tr className={`border-b border-surface/50 hover:bg-surface-hover/30 transition-colors ${onClick ? 'cursor-pointer' : ''} ${className}`} onClick={onClick}>
    {children}
  </tr>
));

// ============== PAGE STRUCTURE ==============

export const PageContainer = ({ children, className = '' }) => (
  <div className={`space-y-6 animate-fadeInUp ${className}`}>{children}</div>
);

export const PageHeader = ({ title, subtitle, children, testId }) => (
  <div className="flex items-center justify-between" data-testid={testId}>
    <div>
      <h1 className="text-2xl font-bold text-primary">{title}</h1>
      {subtitle && <p className="text-sm text-secondary">{subtitle}</p>}
    </div>
    {children && <div className="flex items-center gap-3">{children}</div>}
  </div>
);

export const PageToolbar = ({ children, className = '' }) => (
  <div className={`flex flex-wrap gap-3 items-center ${className}`}>{children}</div>
);

export const FormInput = ({ label, required, error, children }) => (
  <div className="space-y-1">
    <label className="block text-sm font-medium text-secondary">
      {label} {required && <span className="text-danger">*</span>}
    </label>
    {children}
    {error && <p className="text-xs text-danger">{error}</p>}
  </div>
);

export const Select = ({ value, onChange, options, placeholder, className = "" }) => (
  <select value={value} onChange={(e) => onChange(e.target.value)} className={`input-industrial w-full px-4 ${className}`}>
    <option value="">{placeholder || "Selecione..."}</option>
    {options.map((opt) => (
      <option key={opt.value} value={opt.value}>{opt.label}</option>
    ))}
  </select>
);

export const SearchInput = ({ value, onChange, placeholder = 'Buscar...' }) => (
  <div className="relative flex-1 min-w-[200px]">
    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" size={18} />
    <input type="text" value={value} onChange={onChange} placeholder={placeholder} className="input-industrial w-full pl-10 pr-4" />
  </div>
);
