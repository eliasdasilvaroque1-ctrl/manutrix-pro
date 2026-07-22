import { useState, useEffect, useRef, memo, useCallback, useMemo, lazy, Suspense } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, useParams, useSearchParams } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import { QRCodeSVG } from "qrcode.react";
import { 
  Home, ClipboardCheck, Box, User, Settings, LogOut, 
  AlertTriangle, CheckCircle, XCircle, Clock, Wrench, Package,
  ChevronRight, ChevronLeft, ChevronDown, Search, Plus, QrCode, Camera, ArrowLeft,
  Activity, TrendingUp, TrendingDown, BarChart3, Bell, Menu, X, Play, Pause,
  MapPin, Calendar, FileText, Image, Upload, RefreshCw, WifiOff,
  Zap, Target, Layers, Filter, Eye, Edit, Trash2, Save,
  Building, Hash, Droplet, Cog,
  DollarSign, AlertCircle, Users, Tag,
  Shield, CheckSquare, Square, ChevronUp, LayoutDashboard, List, Download, Lock, Edit3, Copy, Factory, ExternalLink,
  Building2, Palette, BookOpen, CheckCircle2, Sparkles, Send,
  ZoomIn, Maximize2, ImagePlus, Printer
} from "lucide-react";
import { BACKEND_URL, API, AuthContext, useAuth, api } from "./lib/api";
import { useBranding } from "./lib/branding";
import { queueOperation, getPendingCount, syncPendingOperations, registerServiceWorker, cacheData, getCachedData, queuePhoto } from "./lib/offlineQueue";
import axios from "axios";
import { DynamicFieldRenderer, SignaturePad } from "./components/DynamicFieldRenderer";

import {
  StatusBadge, PriorityBadge, Modal, ConfirmDialog, Loading, EmptyState,
  DataTable, DataRow, PageContainer, PageHeader, PageToolbar, FormInput, Select,
  SearchInput
} from "./components/shared";
import {
  FIELD_LABEL_MAP, ROLE_LABELS, ROLES_EXCEPT_VIEWER, PRIO_COLORS, PRIO_LABELS,
  CENTRAL_TITLES, normalizeError, compressImage
} from "./lib/constants";
import { MaterialThumbnail, MaterialImageModal, MaterialImageUploader } from "./components/widgets/MaterialComponents";
import ExportButtons, { BatchPrintBar, BatchCheckbox } from "./components/widgets/ExportButtons";
import { ProtectedRoute, CatchAllRedirect } from "./pages/ParadasPage";
import { PhotoUploader } from "./pages/InspecoesPages";
import { QRLabelModal } from "./pages/WhiteLabelDesignerPage";
import { AppProviders, BrandingLoader, ConsentGate } from "./app/AppProviders";
import MainLayout from "./app/MainLayout";
import PublicErrorBoundary from "./components/PublicErrorBoundary";

// Lazy-loaded pages (heavy, less frequently accessed)
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const EstoquePage = lazy(() => import("./pages/EstoquePage"));
const SobressalentesPage = lazy(() => import("./pages/SobressalentesPage").then(m => ({ default: m.default })));
const SolicitacaoServicoPage = lazy(() => import("./pages/SobressalentesPage").then(m => ({ default: m.SolicitacaoServicoPage })));
const AssistentePage = lazy(() => import("./pages/SobressalentesPage").then(m => ({ default: m.AssistentePage })));
const ParadasPage = lazy(() => import("./pages/ParadasPage").then(m => ({ default: m.default })));
const AdminTemplatesPage = lazy(() => import("./pages/ParadasPage").then(m => ({ default: m.AdminTemplatesPage })));
const AuditoriaPage = lazy(() => import("./pages/ParadasPage").then(m => ({ default: m.AuditoriaPage })));
const AdminUsuariosPage = lazy(() => import("./pages/ParadasPage").then(m => ({ default: m.AdminUsuariosPage })));
const SetoresPage = lazy(() => import("./pages/ParadasPage").then(m => ({ default: m.SetoresPage })));
const UnidadesPage = lazy(() => import("./pages/ParadasPage").then(m => ({ default: m.UnidadesPage })));
const InspecoesPage = lazy(() => import("./pages/InspecoesPages").then(m => ({ default: m.InspecoesPage })));
const InspecaoDetailPage = lazy(() => import("./pages/InspecoesPages").then(m => ({ default: m.InspecaoDetailPage })));
const RondaPage = lazy(() => import("./pages/InspecoesPages").then(m => ({ default: m.RondaPage })));
const ScannerPage = lazy(() => import("./pages/InspecoesPages").then(m => ({ default: m.ScannerPage })));
const BibliotecaPage = lazy(() => import("./pages/BibliotecaPage"));
const EquipePage = lazy(() => import("./pages/EquipePage"));
const WhiteLabelDesignerPage = lazy(() => import("./pages/WhiteLabelDesignerPage"));
const DocConfigPage = lazy(() => import("./pages/DocConfigPage"));
const LayoutBuilderPage = lazy(() => import("./pages/LayoutBuilderPage"));
const BibliotecaCorporativaPage = lazy(() => import("./pages/BibliotecaCorporativaPage"));
const ConsultaEquipamentosPage = lazy(() => import("./pages/ConsultaPages").then(m => ({ default: m.ConsultaEquipamentosPage })));
const DossiePesquisaPage = lazy(() => import("./pages/ConsultaPages").then(m => ({ default: m.DossiePesquisaPage })));
const PortalPublicoPage = lazy(() => import("./pages/PortalPages").then(m => ({ default: m.PortalPublicoPage })));
const PortalTecnicoPage = lazy(() => import("./pages/PortalPages").then(m => ({ default: m.PortalTecnicoPage })));
const MasterCleanupPage = lazy(() => import("./pages/MasterCleanupPage"));
const ProcedimentosPage = lazy(() => import("./pages/ProcedimentosPage"));
const OrgConfigPage = lazy(() => import("./pages/OrgConfigPage"));
const FieldOpsPage = lazy(() => import("./pages/FieldOpsPage"));
const AssetDossierPage = lazy(() => import("./pages/AssetDossierPage"));
// HOTFIX P0: Import estático — evita ChunkLoadError em dispositivos móveis após deploy
import PublicEquipmentPage from "./pages/PublicEquipmentPage";

// Suspense fallback
const LazyFallback = () => <div className="flex items-center justify-center min-h-[50vh]"><Loading rows={3} /></div>;

// Register PWA Service Worker
registerServiceWorker();

// AssetIdentity + getAssetContext — removidos (BLOCO A: zero referências)



// normalizeError → extracted to /lib/constants.js

// ============== COMPONENTS ==============

// Modal Component
// Modal, FormInput, Select → extracted to /components/shared/

// StatusBadge, PriorityBadge → extracted to /components/shared/

// KPICard — removido (BLOCO A: zero referências, Dashboard usa inline KPIs)

// Loading, EmptyState → extracted to /components/shared/

// ConfirmDialog → extracted to /components/shared/

// ============== DESIGN SYSTEM — STRUCTURAL COMPONENTS ==============

// PageContainer, PageHeader, PageToolbar, SearchInput → extracted to /components/shared/

// SectionDivider — removido (BLOCO A: zero referências)




// ============== NETWORK STATUS + SYNC ==============
// NetworkStatus, Sidebar, BottomNav, AppLayout → extracted to /app/MainLayout.js
// Alias for backward compatibility within this file
const AppLayout = MainLayout;

// ============== CAMERA CAPTURE ==============
// CameraCapture → moved to /pages/InspecoesPages.js

// ============== MATERIAL IMAGE COMPONENTS ==============
// compressImage → extracted to /lib/constants.js

// MaterialThumbnail, MaterialImageModal, MaterialImageUploader → extracted to /components/widgets/MaterialComponents.js

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
                  <button type="button" onClick={() => { import('./lib/api').then(mod => mod.openAuthenticatedPdf(m.url, (msg) => toast.error(msg))); }} className="text-xs text-blue-400 hover:text-blue-300">Abrir</button>
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
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider flex items-center gap-2">
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
// ModalNovoEstoque → moved to /pages/EstoquePage.js

// Modal Nova OS
const ModalNovaOS = ({ isOpen, onClose, onSuccess, ativos = [], tecnicos = [], editData = null, preSelectedAtivoId = null }) => {
  const [loading, setLoading] = useState(false);
  const [camposConfig, setCamposConfig] = useState([]);
  const [camposValores, setCamposValores] = useState({});
  const [procedimentosSelect, setProcedimentosSelect] = useState([]);
  const { user } = useAuth();
  const [form, setForm] = useState({
    ativo_id: '', tipo: 'corretiva', disciplina: 'mecanica', prioridade: 'media',
    titulo: '', descricao: '', responsavel_id: '',
    data_planejada: '', custo_pecas: 0, custo_mao_obra: 0,
    causa_falha: '', equipamento_parado: false, horas_parada: null,
    procedimento_id: ''
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
        horas_parada: editData.horas_parada || null,
        procedimento_id: editData.procedimento_id || ''
      });
      setCamposValores(editData.campos_personalizados_valores || {});
    } else {
      setForm({
        ativo_id: preSelectedAtivoId || '', tipo: 'corretiva', disciplina: 'mecanica', prioridade: 'media',
        titulo: '', descricao: '', responsavel_id: '', equipe: [],
        data_planejada: '', custo_pecas: 0, custo_mao_obra: 0,
        causa_falha: '', equipamento_parado: false, horas_parada: null,
        procedimento_id: ''
      });
      setCamposValores({});
    }
  }, [editData, isOpen, preSelectedAtivoId]);
  
  // Load approved procedures for select
  useEffect(() => {
    if (!isOpen) return;
    api.get('/procedimentos-select').then(r => setProcedimentosSelect(r.data || [])).catch(() => {});
  }, [isOpen]);

  // Load custom fields for the OS type
  useEffect(() => {
    if (!isOpen || !form.tipo) return;
    api.get(`/doc-config/campos/por-modulo/os?tipo=${form.tipo}`).then(r => setCamposConfig(r.data)).catch(() => setCamposConfig([]));
  }, [isOpen, form.tipo]);
  
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
        campos_personalizados_valores: Object.keys(camposValores).length > 0 ? camposValores : undefined,
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
                  options={ativos.map(a => ({ value: a.id, label: `${a.sector?.nome || ''} › ${a.tag} — ${a.nome}` }))}
                  placeholder="Selecione o ativo..."
                  data-testid="os-modal-ativo-select"
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
                data-testid="os-modal-titulo"
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
                  { value: 'automacao', label: 'Automação' },
                  { value: 'lubrificacao', label: 'Lubrificação' },
                  { value: 'civil', label: 'Civil' },
                  { value: 'operacao', label: 'Operação' },
                  { value: 'producao', label: 'Produção' },
                  { value: 'multidisciplinar', label: 'Multidisciplinar' },
                  { value: 'outra', label: 'Outra' },
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
              className="input-industrial w-full px-4 py-3 min-h-[150px] resize-y"
              placeholder="Descreva o problema ou serviço..."
              maxLength={5000}
            />
          </FormInput>
          
          {/* Procedimento Operacional */}
          <FormInput label="Procedimento Operacional">
            <select value={form.procedimento_id || ''} onChange={e => setForm({...form, procedimento_id: e.target.value || null})} className="input-industrial w-full px-4" data-testid="os-procedimento-select">
              <option value="">Nenhum (opcional)</option>
              {procedimentosSelect.map(p => <option key={p.id} value={p.id}>{p.codigo} — {p.nome} (Rev. {p.revisao})</option>)}
            </select>
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
        
        {/* Campos Personalizados Dinâmicos */}
        {camposConfig.length > 0 && (
          <div className="glass-card p-4 space-y-4">
            <DynamicFieldRenderer
              campos={camposConfig}
              valores={camposValores}
              onChange={(ident, val) => setCamposValores(prev => ({...prev, [ident]: val}))}
              userRole={user?.role}
            />
          </div>
        )}
        
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

// ModalNovaInspecao → moved to /pages/InspecoesPages.js

// Sidebar, BottomNav → extracted to /app/MainLayout.js

// ============== PAGES ==============

// Login
const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState('login');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [tempToken, setTempToken] = useState('');
  const [empresaBusca, setEmpresaBusca] = useState('');
  const [showEmpresaDropdown, setShowEmpresaDropdown] = useState(false);
  const { login } = useAuth();
  const { branding, organizations, selectOrg, orgId, loadOrganizations } = useBranding();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // Determine org source for UX clarity
  const [orgSource, setOrgSource] = useState(null); // 'subdomain' | 'remembered' | 'single' | 'manual' | 'auto' | null
  const [showOrgSelector, setShowOrgSelector] = useState(false);
  const [isMasterUser, setIsMasterUser] = useState(false);
  const [autoOrgLoading, setAutoOrgLoading] = useState(false);

  useEffect(() => { loadOrganizations(); }, [loadOrganizations]);

  // Auto-select from subdomain, localStorage, or single org
  useEffect(() => {
    if (orgId) return;
    // Check subdomain first
    const hostname = window.location.hostname;
    const parts = hostname.split('.');
    const sub = parts.length >= 3 ? parts[0].toLowerCase() : null;
    const isCustomer = sub && sub !== 'www' && sub !== 'app' && !['localhost','127.0.0.1','preview','emergentagent','vercel','railway','netlify'].some(p => hostname.includes(p));
    if (isCustomer && organizations.length > 0) {
      const matchOrg = organizations.find(o => (o.subdominio || '').toLowerCase() === sub || (o.nome || '').toLowerCase().includes(sub));
      if (matchOrg) {
        selectOrg(matchOrg.id);
        setEmpresaBusca(matchOrg.nome);
        setOrgSource('subdomain');
        return;
      }
    }
    // Then localStorage
    const saved = localStorage.getItem('maintrix_last_org');
    if (saved) {
      const org = organizations.find(o => o.id === saved);
      if (org) {
        selectOrg(org.id);
        setEmpresaBusca(org.nome);
        setOrgSource('remembered');
        return;
      }
    }
    // Single org
    if (organizations.length === 1) {
      selectOrg(organizations[0].id);
      setEmpresaBusca(organizations[0].nome);
      setOrgSource('single');
    }
  }, [organizations, orgId, selectOrg]);

  const handleSelectEmpresa = (org) => {
    selectOrg(org.id);
    setEmpresaBusca(org.nome);
    setShowEmpresaDropdown(false);
    setShowOrgSelector(false);
    setOrgSource('manual');
    localStorage.setItem('maintrix_last_org', org.id);
  };

  const handleTrocarOrg = () => {
    setOrgSource(null);
    setShowOrgSelector(true);
    setEmpresaBusca('');
    setShowEmpresaDropdown(false);
    setIsMasterUser(false);
  };

  // Auto-detect org from email (for non-master users)
  const handleEmailBlur = async () => {
    if (!email || orgId) return;
    setAutoOrgLoading(true);
    try {
      const res = await axios.post(`${API}/auth/lookup-email`, { email: email.trim() });
      if (res.data.is_master) {
        setIsMasterUser(true);
        setShowOrgSelector(true);
      } else {
        selectOrg(res.data.organization_id);
        setEmpresaBusca(res.data.organization_name);
        setOrgSource('auto');
        setIsMasterUser(false);
      }
    } catch {
      // Email not found — show org selector as fallback
      if (!orgId) setShowOrgSelector(true);
    } finally { setAutoOrgLoading(false); }
  };

  const filteredOrgs = organizations.filter(o =>
    !empresaBusca || (o.nome || '').toLowerCase().includes(empresaBusca.toLowerCase())
  );

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!orgId) { toast.error('Selecione uma empresa'); return; }
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password, organization_id: orgId });
      if (response.data.user?.force_password_change) {
        setTempToken(response.data.access_token);
        setView('forceChange');
        toast.info('Você precisa trocar sua senha');
      } else {
        login(response.data);
        toast.success('Login realizado!');
        const userRole = response.data.user?.role;
        // Restaurar destino original (ex: /os/{id} escaneado via QR)
        const from = location.state?.from;
        const defaultRoute = (userRole === 'visualizador' || userRole === 'viewer') ? '/consulta' : '/';
        navigate(from || defaultRoute, { replace: true });
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
      const res = await axios.post(`${API}/auth/forgot-password`, { email, organization_id: orgId });
      setResetToken(res.data.token || '');
      setView('reset');
      toast.success(res.data.message || 'Token de redefinição gerado!');
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
          <p className="text-secondary mt-1 text-sm">{branding.texto_login || 'Sistema de Gestão de Manutenção'}</p>
        </div>

        {/* LOGIN */}
        {view === 'login' && (
          <form onSubmit={handleLogin} className="glass-card p-6 space-y-4" data-testid="login-form">
            {/* Organização — Smart Selector */}
            {orgId && !showOrgSelector ? (
              <div data-testid="org-confirmed">
                <p className="text-xs text-secondary uppercase tracking-wider mb-1.5">
                  {orgSource === 'subdomain' ? 'Ambiente' : 'Organização'}
                </p>
                <div className="flex items-center gap-3 p-3 rounded-lg border border-surface" style={{ backgroundColor: 'var(--brand-surface)' }}>
                  {(() => { const selOrg = organizations.find(o => o.id === orgId); return selOrg?.logo_url ? (
                    <img src={selOrg.logo_url} alt="" className="w-8 h-8 rounded-lg object-contain bg-slate-800 p-0.5" />
                  ) : (
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-xs" style={{ backgroundColor: branding.cor_primaria }}>
                      {(empresaBusca || '?').substring(0, 2).toUpperCase()}
                    </div>
                  ); })()}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-primary truncate" data-testid="org-confirmed-name">{empresaBusca}</p>
                    <p className="text-[10px] text-secondary">
                      {orgSource === 'subdomain' && 'Detectado pelo endereço'}
                      {orgSource === 'remembered' && 'Última organização utilizada'}
                      {orgSource === 'single' && 'Organização única'}
                      {orgSource === 'manual' && 'Selecionada manualmente'}
                      {orgSource === 'auto' && 'Detectado pelo email'}
                    </p>
                  </div>
                  {orgSource === 'subdomain' || orgSource === 'auto' ? (
                    <Lock size={16} className="text-secondary shrink-0" title={orgSource === 'auto' ? 'Organização vinculada ao email' : 'Ambiente detectado'} />
                  ) : (
                    <button type="button" onClick={handleTrocarOrg} className="text-xs px-2 py-1 rounded border border-surface hover:bg-surface-hover text-secondary transition-colors" data-testid="trocar-org-btn">
                      Trocar
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="relative" data-testid="org-selector">
                <FormInput label="Organização">
                  <div className="relative">
                    <Building2 size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
                    <input value={empresaBusca} onChange={e => { setEmpresaBusca(e.target.value); setShowEmpresaDropdown(true); }}
                      onFocus={() => setShowEmpresaDropdown(true)}
                      className="input-industrial w-full pl-10 pr-4" placeholder="Buscar organização..."
                      autoFocus={showOrgSelector}
                      data-testid="org-search-input" />
                  </div>
                </FormInput>
                {showEmpresaDropdown && filteredOrgs.length > 0 && (
                  <div className="absolute z-20 w-full mt-1 bg-surface border border-surface rounded-lg shadow-xl max-h-48 overflow-y-auto">
                    {filteredOrgs.map(org => (
                      <button key={org.id} type="button" onClick={() => handleSelectEmpresa(org)}
                        className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-surface-hover transition-colors text-left ${orgId === org.id ? 'bg-brand-10' : ''}`}
                        data-testid={`org-option-${org.id}`}>
                        {org.logo_url ? (
                          <img src={org.logo_url} alt="" className="w-8 h-8 rounded-lg object-contain bg-slate-800 p-0.5" />
                        ) : (
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-xs" style={{ backgroundColor: org.cor_primaria || '#10b981' }}>
                            {(org.nome || 'E').substring(0, 2).toUpperCase()}
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-primary font-medium truncate">{org.nome}</p>
                          {org.subdominio && <p className="text-[10px] text-secondary">{org.subdominio}.maintrix.com.br</p>}
                        </div>
                        {orgId === org.id && <CheckCircle size={16} className="text-brand shrink-0" />}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            <FormInput label="Email">
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} onBlur={handleEmailBlur} className="input-industrial w-full px-4" placeholder="seu@email.com" required data-testid="login-email" />
            </FormInput>
            <FormInput label="Senha">
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input-industrial w-full px-4" placeholder="Sua senha" required data-testid="login-password" />
            </FormInput>
            <button type="submit" disabled={loading || !orgId} className="w-full py-3 rounded-lg font-semibold text-white transition-all disabled:opacity-50" style={{ backgroundColor: branding.cor_primaria }} data-testid="login-submit">
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
            <div className="text-center">
              <button type="button" onClick={() => setView('forgot')} className="text-sm text-slate-400 hover:text-slate-200 transition-colors" data-testid="forgot-password-link">Esqueci minha senha</button>
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
            <FormInput label="Código de Recuperação"><input type="text" value={resetToken} onChange={(e) => setResetToken(e.target.value)} className="input-industrial w-full px-4 font-mono text-sm tracking-widest text-center" required data-testid="reset-token" placeholder="XXXXXX" /></FormInput>
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

const centralTitles = CENTRAL_TITLES;

const prioColors = PRIO_COLORS;
const prioLabels = PRIO_LABELS;

const AtividadeCard = memo(({ item, tipo, navigate }) => {
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
        {item.ativo?.sector?.nome && <p className="text-[10px] text-slate-500">{item.ativo.sector.nome}</p>}
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
});

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
      } catch { toast.error('Não foi possível carregar a central. Verifique sua conexão.'); }
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
    <PageContainer data-testid="central-trabalho">
      <PageHeader title={titulo} subtitle={`${data.user_nome}${data.turno ? ` • Turno ${data.turno}` : ''} • ${new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}`}>
        <div className="text-right">
          <p className="text-2xl font-bold text-primary">{data.total_atividades}</p>
          <p className="text-[10px] text-secondary uppercase">Atividades</p>
        </div>
        <button onClick={() => { setLoading(true); api.get('/central').then(r => setData(r.data)).finally(() => setLoading(false)); }} className="p-2 hover:bg-surface-hover rounded-lg transition-colors" data-testid="central-refresh">
          <RefreshCw size={18} className="text-secondary" />
        </button>
      </PageHeader>

      {data.resumo && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="glass-card p-3 text-center">
            <p className="text-xl font-bold text-primary">{data.resumo.total_os_abertas}</p>
            <p className="text-[10px] text-secondary uppercase">OS Abertas</p>
          </div>
          <div className="glass-card p-3 text-center">
            <p className="text-xl font-bold text-primary">{data.resumo.total_insp_pendentes}</p>
            <p className="text-[10px] text-secondary uppercase">Inspeções Pendentes</p>
          </div>
          <div className="glass-card p-3 text-center">
            <p className="text-xl font-bold text-primary">{data.resumo.total_ativos}</p>
            <p className="text-[10px] text-secondary uppercase">Ativos</p>
          </div>
          <div className="glass-card p-3 text-center">
            <p className="text-xl font-bold text-warning">{data.resumo.ativos_parados}</p>
            <p className="text-[10px] text-secondary uppercase">Parados</p>
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
            <div key={p.id} className="flex items-center gap-3 p-3 rounded-lg border border-surface bg-surface/50 cursor-pointer hover:border-slate-600" onClick={() => navigate('/admin/templates')} data-testid={`plano-pendente-${p.id}`}>
              <ClipboardCheck size={16} className="text-purple-400 shrink-0" />
              <div className="flex-1">
                <p className="text-sm text-primary">{p.nome}</p>
                <span className="text-[10px] text-secondary">{(p.perguntas || []).length} perguntas • {p.tipo}</span>
              </div>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-warning-10 text-warning border border-amber-500/30">{p.status}</span>
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
          <CheckCircle size={48} className="text-success mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-primary">Tudo em dia!</h3>
          <p className="text-sm text-secondary mt-1">Nenhuma atividade pendente no momento.</p>
        </div>
      )}
    </PageContainer>
  );
};


// DashboardPage + TrendChart + OSDistChart → extracted to /pages/DashboardPage.js

const AtivosPage = () => {
  const [ativos, setAtivos] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [plantas, setPlantas] = useState([]);
  const [osList, setOsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterSector, setFilterSector] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const [selectedForQR, setSelectedForQR] = useState([]);
  const [showBatchQR, setShowBatchQR] = useState(false);
  const [batchModelo, setBatchModelo] = useState('etiqueta');
  const [batchLayout, setBatchLayout] = useState('6_per_page');
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const fetchData = async () => {
    try {
      const params = {};
      if (filterSector) params.sector_id = filterSector;
      const [ativosRes, sectorsRes, osRes, plantasRes] = await Promise.all([
        api.get('/ativos', { params }),
        api.get('/sectors'),
        api.get('/ordens-servico'),
        api.get('/plantas')
      ]);
      setAtivos(ativosRes.data);
      setSectors(sectorsRes.data);
      setOsList(osRes.data);
      setPlantas(plantasRes.data);
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
    <PageContainer>
      <PageHeader title="Ativos">
        <ExportButtons entity="ativos" />
        {selectedForQR.length > 0 && (
          <button onClick={() => setShowBatchQR(true)} className="btn-secondary flex items-center gap-2 text-sm" data-testid="batch-qr-btn">
            <QrCode size={16} /> QR Lote ({selectedForQR.length})
          </button>
        )}
        {['admin','master'].includes(user?.role) && (
          <button onClick={() => { setEditItem(null); setShowModal(true); }} className="btn-primary flex items-center gap-2" data-testid="add-ativo-btn">
            <Plus size={20} /> Novo Ativo
          </button>
        )}
      </PageHeader>
      
      <PageToolbar>
        <SearchInput value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar por TAG, nome ou área..." />
        <Select
          value={filterSector}
          onChange={setFilterSector}
          options={sectors.map(s => ({ value: s.id, label: s.nome }))}
          placeholder="Área"
          className="w-40"
        />
      </PageToolbar>
      
      {loading ? <Loading rows={5} /> : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((ativo) => (
            <div key={ativo.id} className="glass-card p-4 hover:border-slate-600 transition-all group cursor-pointer" data-testid={`ativo-card-${ativo.tag}`} onClick={() => navigate(`/ativos/${ativo.id}`)}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <input type="checkbox" checked={selectedForQR.includes(ativo.id)} onClick={(e) => { e.stopPropagation(); setSelectedForQR(prev => prev.includes(ativo.id) ? prev.filter(x=>x!==ativo.id) : [...prev, ativo.id]); }}
                    className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-emerald-500 cursor-pointer shrink-0" data-testid={`qr-select-${ativo.tag}`} />
                  <div className="p-2 rounded-lg bg-brand-10">
                    <Box size={22} className="text-brand" />
                  </div>
                  <div>
                    <div className="flex items-center gap-1 text-[10px] text-secondary mb-0.5">
                      {plantas[0]?.nome && <span>{plantas[0].nome}</span>}
                      {plantas[0]?.nome && ativo.sector?.nome && <span className="text-secondary">›</span>}
                      {ativo.sector?.nome && <span>{ativo.sector.nome}</span>}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-brand text-sm">{ativo.tag}</span>
                      {(() => { const st = getAtivoStatus(ativo.id); return (
                        <span className={`${st.class} border text-[10px] px-1.5 py-0.5 rounded font-medium`} data-testid={`ativo-status-${ativo.tag}`}>{st.label}</span>
                      ); })()}
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

      {/* Batch QR Modal */}
      {showBatchQR && (
        <Modal isOpen={showBatchQR} onClose={() => setShowBatchQR(false)} title={`Imprimir QR Code em Lote (${selectedForQR.length} ativos)`} size="md">
          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-400 block mb-1">Modelo</label>
              <Select value={batchModelo} onChange={setBatchModelo} options={[
                { value: 'simples', label: 'QR Simples' },
                { value: 'etiqueta', label: 'Etiqueta do Equipamento' },
              ]} />
            </div>
            <div>
              <label className="text-sm text-slate-400 block mb-1">Layout</label>
              <Select value={batchLayout} onChange={setBatchLayout} options={[
                { value: '6_per_page', label: '6 etiquetas por folha' },
                { value: '8_per_page', label: '8 etiquetas por folha' },
                { value: '12_per_page', label: '12 etiquetas por folha' },
              ]} />
            </div>
            <div className="flex items-center justify-between pt-2">
              <button onClick={() => setSelectedForQR(filtered.map(a => a.id))} className="text-xs text-emerald-400 hover:text-emerald-300">
                Selecionar todos da página ({filtered.length})
              </button>
              <button onClick={() => setSelectedForQR([])} className="text-xs text-slate-500 hover:text-slate-400">Limpar seleção</button>
            </div>
            <button onClick={async () => {
              try {
                const res = await api.post('/ativos/qrcode/batch-pdf', { asset_ids: selectedForQR, modelo: batchModelo, layout: batchLayout }, { responseType: 'blob' });
                const url = URL.createObjectURL(res.data);
                window.open(url);
                toast.success(`PDF gerado com ${selectedForQR.length} etiquetas!`);
                setShowBatchQR(false);
              } catch(e) { toast.error('Erro ao gerar PDF em lote'); }
            }} className="btn-primary w-full" data-testid="batch-qr-generate">
              Gerar PDF ({selectedForQR.length} etiquetas)
            </button>
          </div>
        </Modal>
      )}
    </PageContainer>
  );
};

// Ativo Detail

// ============== DOSSIÊ PERMANENTE DO EQUIPAMENTO ==============
const DossieTab = ({ ativoId, plantas, user }) => {
  const [eventos, setEventos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtro, setFiltro] = useState('');
  const [dossie, setDossie] = useState(null);
  const [dossieType, setDossieType] = useState(null);
  const [dossieLoading, setDossieLoading] = useState(false);
  const canViewDossie = ['master','admin','pcm','supervisor','gerente'].includes(user?.role);
  const formatD = (d) => d ? new Date(d).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—';
  const formatMin = (m) => m ? `${Math.floor(m/60)}h${String(m%60).padStart(2,'0')}` : '—';

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get(`/ativos/${ativoId}/historico`);
        setEventos(res.data.sort((a,b) => (b.data||'').localeCompare(a.data||'')));
      } catch { /* empty */ }
      finally { setLoading(false); }
    })();
  }, [ativoId]);

  const openDossie = async (tipo, id) => {
    if (!canViewDossie) return;
    setDossieLoading(true);
    try {
      const res = await api.get(`/dossie/${tipo}/${id}`);
      setDossie(res.data);
      setDossieType(tipo);
    } catch { toast.error('Erro ao carregar dossiê'); }
    finally { setDossieLoading(false); }
  };

  const tipoConfig = {
    os: { icon: Wrench, color: 'text-blue-400 bg-blue-500/10 border-blue-500/30', label: 'OS' },
    inspecao: { icon: ClipboardCheck, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30', label: 'Inspeção' },
    material: { icon: Package, color: 'text-amber-400 bg-amber-500/10 border-amber-500/30', label: 'Material' },
    anomalia: { icon: AlertTriangle, color: 'text-red-400 bg-red-500/10 border-red-500/30', label: 'Solicitação' },
  };

  const filtered = filtro ? eventos.filter(e => e.tipo_evento === filtro) : eventos;

  // --- DOSSIÊ OS MODAL ---
  if (dossie && dossieType === 'os') {
    const d = dossie;
    return (
      <div className="space-y-4" data-testid="dossie-os-view">
        <div className="flex items-center justify-between">
          <button onClick={() => { setDossie(null); setDossieType(null); }} className="flex items-center gap-1 text-sm text-slate-400 hover:text-brand" data-testid="dossie-voltar"><ChevronLeft size={16} /> Voltar ao Histórico</button>
          <span className="text-xs bg-slate-700 text-slate-300 px-3 py-1 rounded-full">SOMENTE LEITURA</span>
        </div>
        <div className="glass-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-1 text-[10px] text-slate-500 mb-1">
                {d.ativo_unidade && <span className="flex items-center gap-0.5"><Building2 size={10} />{d.ativo_unidade}</span>}
                {d.ativo_sector && <span className="flex items-center gap-0.5"><MapPin size={10} />{d.ativo_sector}</span>}
              </div>
              <span className="font-mono text-brand text-sm font-bold">{d.ativo?.tag}</span>
              <span className="text-slate-300 ml-2">{d.ativo?.nome}</span>
            </div>
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium capitalize ${d.status === 'concluida' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-700 text-slate-300'}`}>{d.status}</span>
          </div>
          <h2 className="text-lg font-bold text-slate-100">OS #{d.numero} — {d.titulo}</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div><span className="text-slate-500 text-xs">Tipo</span><p className="text-slate-200 capitalize">{d.tipo}</p></div>
            <div><span className="text-slate-500 text-xs">Origem</span><p className="text-slate-200 capitalize">{d.origem}</p></div>
            <div><span className="text-slate-500 text-xs">Prioridade</span><p className="text-slate-200 capitalize">{d.prioridade}</p></div>
            <div><span className="text-slate-500 text-xs">Disciplina</span><p className="text-slate-200 capitalize">{d.disciplina || '—'}</p></div>
            <div><span className="text-slate-500 text-xs">Solicitante</span><p className="text-slate-200">{d.solicitante?.nome || '—'}</p></div>
            <div><span className="text-slate-500 text-xs">Responsável PCM</span><p className="text-slate-200">{d.responsavel?.nome || '—'}</p></div>
            <div><span className="text-slate-500 text-xs">Iniciado por</span><p className="text-slate-200">{d.iniciado_por_info?.nome || '—'}</p></div>
            <div><span className="text-slate-500 text-xs">Concluído por</span><p className="text-slate-200">{d.concluido_por_info?.nome || '—'}</p></div>
            <div><span className="text-slate-500 text-xs">Abertura</span><p className="text-slate-200">{formatD(d.data_abertura || d.created_at)}</p></div>
            <div><span className="text-slate-500 text-xs">Início</span><p className="text-slate-200">{formatD(d.data_inicio)}</p></div>
            <div><span className="text-slate-500 text-xs">Conclusão</span><p className="text-slate-200">{formatD(d.data_conclusao)}</p></div>
            <div><span className="text-slate-500 text-xs">Tempo</span><p className="text-slate-200">{formatMin(d.tempo_execucao_minutos)}</p></div>
          </div>
        </div>
        {d.descricao && <div className="glass-card p-4"><h3 className="text-sm font-semibold text-slate-300 mb-2">Descrição</h3><p className="text-sm text-slate-400">{d.descricao}</p></div>}
        {d.descricao_servico && <div className="glass-card p-4"><h3 className="text-sm font-semibold text-slate-300 mb-2">Solução Aplicada</h3><p className="text-sm text-slate-400">{d.descricao_servico}</p></div>}
        {d.causa_falha && <div className="glass-card p-4"><h3 className="text-sm font-semibold text-slate-300 mb-2">Causa da Falha</h3><p className="text-sm text-slate-400">{d.causa_falha}</p></div>}
        {d.observacoes && <div className="glass-card p-4"><h3 className="text-sm font-semibold text-slate-300 mb-2">Observações</h3><p className="text-sm text-slate-400">{d.observacoes}</p></div>}
        {d.executantes?.length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-2">Executantes e HH</h3>
            <div className="space-y-1">
              {d.executantes.map((ex, i) => (
                <div key={i} className="flex items-center justify-between text-sm border-b border-slate-800 pb-1">
                  <span className="text-slate-200">{ex.nome} <span className="text-xs text-slate-500">({ROLE_LABELS[ex.role] || ex.role})</span></span>
                  <span className="text-brand font-mono">{formatMin(ex.hh_minutos)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {d.materiais?.length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-2">Materiais Consumidos</h3>
            <div className="space-y-1">
              {d.materiais.map((m, i) => (
                <div key={i} className="flex items-center gap-2 text-sm border-b border-slate-800 pb-1">
                  <MaterialThumbnail images={m.image_url ? [m.image_url] : []} nome={m.item_nome || m.item_codigo} categoria="" size="sm" />
                  <span className="text-slate-200 flex-1">{m.item_nome || m.item_codigo} <span className="text-xs text-slate-500">{m.item_codigo}</span></span>
                  <span className="text-slate-300">{m.quantidade} {m.unidade || 'un'}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {d.aprovacao?.status && (
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-2">Aprovação</h3>
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div><span className="text-slate-500 text-xs">Status</span><p className="text-slate-200 capitalize">{d.aprovacao.status}</p></div>
              <div><span className="text-slate-500 text-xs">Aprovador</span><p className="text-slate-200">{d.aprovacao.aprovador_nome || '—'}</p></div>
              <div><span className="text-slate-500 text-xs">Data</span><p className="text-slate-200">{formatD(d.aprovacao.data)}</p></div>
            </div>
          </div>
        )}
        {d.fotos?.length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-2">Fotos e Anexos ({d.fotos.length})</h3>
            <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
              {d.fotos.map((f, i) => (
                <a key={i} href={f.url?.startsWith('http') ? f.url : `${BACKEND_URL}${f.url}`} target="_blank" rel="noreferrer" className="block rounded-lg overflow-hidden border border-slate-700 hover:border-brand/40 transition-all">
                  {f.mime_type?.startsWith('image') ? <img src={f.url?.startsWith('http') ? f.url : `${BACKEND_URL}${f.url}`} alt="" className="w-full h-20 object-cover" /> : <div className="h-20 flex items-center justify-center bg-slate-800"><FileText size={24} className="text-slate-500" /></div>}
                </a>
              ))}
            </div>
          </div>
        )}
        {d.auditoria?.length > 0 && (
          <details className="glass-card p-4">
            <summary className="text-sm font-semibold text-slate-300 cursor-pointer">Auditoria ({d.auditoria.length} registros)</summary>
            <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
              {d.auditoria.map((a, i) => (
                <div key={i} className="text-[11px] text-slate-500 border-b border-slate-800 pb-1">
                  <span className="text-slate-400">{formatD(a.created_at)}</span> — {a.action} — {a.details}
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    );
  }

  // --- DOSSIÊ INSPEÇÃO MODAL ---
  if (dossie && dossieType === 'inspecao') {
    const d = dossie;
    return (
      <div className="space-y-4" data-testid="dossie-inspecao-view">
        <div className="flex items-center justify-between">
          <button onClick={() => { setDossie(null); setDossieType(null); }} className="flex items-center gap-1 text-sm text-slate-400 hover:text-brand" data-testid="dossie-voltar"><ChevronLeft size={16} /> Voltar ao Histórico</button>
          <span className="text-xs bg-slate-700 text-slate-300 px-3 py-1 rounded-full">SOMENTE LEITURA</span>
        </div>
        <div className="glass-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-1 text-[10px] text-slate-500 mb-1">
                {d.ativo_unidade && <span className="flex items-center gap-0.5"><Building2 size={10} />{d.ativo_unidade}</span>}
                {d.ativo_sector && <span className="flex items-center gap-0.5"><MapPin size={10} />{d.ativo_sector}</span>}
              </div>
              <span className="font-mono text-brand text-sm font-bold">{d.ativo?.tag}</span>
              <span className="text-slate-300 ml-2">{d.ativo?.nome}</span>
            </div>
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium capitalize ${d.status === 'concluida' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-700 text-slate-300'}`}>{d.status}</span>
          </div>
          <h2 className="text-lg font-bold text-slate-100">Inspeção {d.tipo?.charAt(0).toUpperCase() + d.tipo?.slice(1)}</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div><span className="text-slate-500 text-xs">Tipo</span><p className="text-slate-200 capitalize">{d.tipo}</p></div>
            <div><span className="text-slate-500 text-xs">Disciplina</span><p className="text-slate-200 capitalize">{d.disciplina || '—'}</p></div>
            <div><span className="text-slate-500 text-xs">Resultado</span><p className={`capitalize ${d.resultado === 'conforme' ? 'text-emerald-400' : d.resultado === 'nao_conforme' ? 'text-red-400' : 'text-slate-200'}`}>{d.resultado || '—'}</p></div>
            <div><span className="text-slate-500 text-xs">Duração</span><p className="text-slate-200">{formatMin(d.duracao_minutos)}</p></div>
            <div><span className="text-slate-500 text-xs">Executado por</span><p className="text-slate-200">{d.executado_por_info?.nome || '—'}</p></div>
            <div><span className="text-slate-500 text-xs">Criado por</span><p className="text-slate-200">{d.criado_por_info?.nome || '—'}</p></div>
            <div><span className="text-slate-500 text-xs">Data Execução</span><p className="text-slate-200">{formatD(d.data_conclusao || d.data_inicio)}</p></div>
            <div><span className="text-slate-500 text-xs">Criação</span><p className="text-slate-200">{formatD(d.created_at)}</p></div>
          </div>
          {d.plano && (
            <div className="bg-slate-800/50 rounded p-3">
              <span className="text-xs text-slate-500">Plano utilizado:</span>
              <p className="text-sm text-slate-300 font-medium">{d.plano.nome} <span className="text-xs text-slate-500 capitalize">({d.plano.tipo} — {d.plano.frequencia})</span></p>
            </div>
          )}
        </div>
        {d.checklist?.length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Respostas do Checklist ({d.checklist.length})</h3>
            <div className="space-y-2">
              {d.checklist.map((c, i) => (
                <div key={i} className={`flex items-start justify-between text-sm border-b border-slate-800 pb-2 ${c.resposta === 'nao_conforme' || c.resposta === 'reprovado' ? 'bg-red-500/5 -mx-2 px-2 rounded' : ''}`}>
                  <div className="flex-1">
                    <p className="text-slate-300">{c.pergunta}</p>
                    {c.observacao && <p className="text-xs text-slate-500 mt-0.5">{c.observacao}</p>}
                  </div>
                  <span className={`ml-3 text-xs px-2 py-0.5 rounded-full font-medium whitespace-nowrap ${c.resposta === 'conforme' || c.resposta === 'sim' ? 'bg-emerald-500/10 text-emerald-400' : c.resposta === 'nao_conforme' || c.resposta === 'nao' || c.resposta === 'reprovado' ? 'bg-red-500/10 text-red-400' : 'bg-slate-700 text-slate-300'}`}>{c.resposta || '—'}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {d.nao_conformidades?.length > 0 && (
          <div className="glass-card p-4 border border-red-500/20">
            <h3 className="text-sm font-semibold text-red-400 mb-2">Não Conformidades ({d.nao_conformidades.length})</h3>
            <div className="space-y-1">
              {d.nao_conformidades.map((nc, i) => (
                <div key={i} className="text-sm text-red-300">{nc.pergunta}: <span className="text-red-400 font-medium">{nc.resposta}</span></div>
              ))}
            </div>
          </div>
        )}
        {d.observacoes && <div className="glass-card p-4"><h3 className="text-sm font-semibold text-slate-300 mb-2">Observações</h3><p className="text-sm text-slate-400">{d.observacoes}</p></div>}
        {d.fotos?.length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-2">Fotos ({d.fotos.length})</h3>
            <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
              {d.fotos.map((f, i) => (
                <a key={i} href={f.url?.startsWith('http') ? f.url : `${BACKEND_URL}${f.url}`} target="_blank" rel="noreferrer" className="block rounded-lg overflow-hidden border border-slate-700 hover:border-brand/40 transition-all">
                  {f.mime_type?.startsWith('image') ? <img src={f.url?.startsWith('http') ? f.url : `${BACKEND_URL}${f.url}`} alt="" className="w-full h-20 object-cover" /> : <div className="h-20 flex items-center justify-center bg-slate-800"><FileText size={24} className="text-slate-500" /></div>}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // --- TIMELINE LIST ---
  return (
    <div className="space-y-3" data-testid="dossie-tab">
      <div className="glass-card p-3 flex flex-wrap items-center gap-2">
        <select value={filtro} onChange={e => setFiltro(e.target.value)} className="input-industrial px-3 text-sm">
          <option value="">Todos ({eventos.length})</option>
          <option value="os">Ordens de Serviço</option>
          <option value="inspecao">Inspeções</option>
          <option value="material">Materiais</option>
        </select>
        <span className="text-xs text-slate-500 ml-auto">{filtered.length} registros</span>
      </div>
      {loading ? (
        <div className="flex justify-center py-8"><Cog size={32} className="text-brand animate-spin" /></div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-8 text-slate-500"><ClipboardCheck size={32} className="mx-auto mb-2 opacity-30" /><p>Nenhum registro encontrado</p></div>
      ) : (
        <div className="space-y-1.5">
          {filtered.map((ev, idx) => {
            const cfg = tipoConfig[ev.tipo_evento] || tipoConfig.os;
            const Icon = cfg.icon;
            const clickable = canViewDossie && (ev.tipo_evento === 'os' || ev.tipo_evento === 'inspecao');
            return (
              <div key={idx} onClick={() => clickable && openDossie(ev.tipo_evento, ev.id)} className={`glass-card p-3 flex items-center gap-3 ${clickable ? 'cursor-pointer hover:border-brand/30' : ''} transition-all`} data-testid={`dossie-item-${idx}`}>
                <div className={`p-2 rounded-lg border ${cfg.color}`}><Icon size={16} /></div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-200 truncate">{ev.titulo}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full capitalize ${ev.status === 'concluida' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-700 text-slate-400'}`}>{ev.status}</span>
                  </div>
                  {ev.descricao && <p className="text-xs text-slate-500 truncate">{ev.descricao}</p>}
                  {ev.usuario && <p className="text-[10px] text-slate-600">{ev.usuario}</p>}
                </div>
                <div className="text-right shrink-0">
                  <p className="text-xs text-slate-400">{formatD(ev.data)}</p>
                  {ev.tempo_minutos && <p className="text-[10px] text-slate-500">{formatMin(ev.tempo_minutos)}</p>}
                </div>
                {clickable && <ChevronRight size={14} className="text-slate-600" />}
              </div>
            );
          })}
        </div>
      )}
      {dossieLoading && <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"><Cog size={48} className="text-brand animate-spin" /></div>}
    </div>
  );
};


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
  const [plantas, setPlantas] = useState([]);
  const [timelineLimit, setTimelineLimit] = useState(20);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const fetchAtivo = async () => {
    try {
      const [ativoRes, manuaisRes, histRes, planosRes, saudeRes, plantasRes] = await Promise.all([
        api.get(`/ativos/${id}`),
        api.get(`/ativos/${id}/manuais`),
        api.get(`/ativos/${id}/historico`).catch(() => ({ data: [] })),
        api.get(`/planos-inspecao/por-ativo/${id}`).catch(() => ({ data: [] })),
        api.get(`/ativos/${id}/saude`).catch(() => ({ data: null })),
        api.get('/plantas').catch(() => ({ data: [] })),
      ]);
      setAtivo(ativoRes.data);
      setManuais(manuaisRes.data);
      setHistorico(histRes.data);
      setPlanosVinculados(planosRes.data);
      setSaude(saudeRes.data);
      setPlantas(plantasRes.data);
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
    anomalia: { color: 'border-red-500', bg: 'bg-red-500', icon: AlertTriangle, label: 'Solicitação' },
    material: { color: 'border-amber-500', bg: 'bg-amber-500', icon: Package, label: 'Material' },
    parada: { color: 'border-purple-500', bg: 'bg-purple-500', icon: Calendar, label: 'Parada' },
  };

  const tabs = [
    { key: 'prontuario', label: 'Prontuário' },
    { key: 'dossie', label: 'Histórico Completo' },
    { key: 'timeline', label: `Timeline (${historico.length})` },
    { key: 'planos', label: `Planos (${planosVinculados.length})` },
    { key: 'os', label: `OS (${ativo.ordens_servico?.length || 0})` },
    { key: 'docs', label: `Docs (${manuais.length})` },
    { key: 'materiais', label: `BOM (${ativo.materiais?.length || 0})` },
    { key: 'qrcode', label: 'QR Code' },
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
                  <div><span className="text-slate-500">Unidade</span><p className="text-slate-300">{plantas?.[0]?.nome || '—'}</p></div>
                  <div><span className="text-slate-500">Área</span><p className="text-slate-300">{ativo.sector?.nome || '—'}</p></div>
                  <div><span className="text-slate-500">Tipo</span><p className="text-slate-300">{ativo.tipo_equipamento || '—'}</p></div>
                  <div><span className="text-slate-500">Fabricante</span><p className="text-slate-300">{ativo.fabricante || '—'}</p></div>
                  <div><span className="text-slate-500">Modelo</span><p className="text-slate-300">{ativo.modelo || '—'}</p></div>
                  <div><span className="text-slate-500">Nº Série</span><p className="text-slate-300">{ativo.numero_serie || '—'}</p></div>
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
            <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-3 flex items-center gap-2"><Activity size={16} className="text-brand" /> Saúde do Equipamento</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <SaudeItem label="Última Inspeção" data={saude?.ultima_inspecao} icon={ClipboardCheck} color="bg-emerald-600" />
              <SaudeItem label="Próxima Inspeção" data={saude?.proxima_inspecao} icon={Calendar} color="bg-blue-600" />
              <SaudeItem label="Última Preventiva" data={saude?.ultima_preventiva} icon={Shield} color="bg-purple-600" />
              <SaudeItem label="Próxima Preventiva" data={saude?.proxima_preventiva} icon={Calendar} color="bg-purple-500" />
              <SaudeItem label="Última Lubrificação" data={saude?.ultima_lubrificacao} icon={Droplet} color="bg-amber-600" />
              <SaudeItem label="Última OS" data={saude?.ultima_os} icon={Wrench} color="bg-blue-600" />
              <div className="flex items-center gap-3 p-2.5 rounded-lg bg-slate-800/30">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-slate-600"><Clock size={14} className="text-white" /></div>
                <div><p className="text-[10px] text-slate-500 uppercase">MTTR</p><p className="text-xs text-slate-300">{ativo.kpis?.mttr_horas || 0}h</p></div>
              </div>
            </div>
          </div>

          {/* Planos Permanentes */}
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-3 flex items-center gap-2"><ClipboardCheck size={16} className="text-brand" /> Planos Permanentes ({planosVinculados.length})</h3>
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
              <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-3 flex items-center gap-2"><Wrench size={16} className="text-blue-400" /> OS em Aberto</h3>
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
              <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider flex items-center gap-2"><Clock size={16} className="text-slate-400" /> Últimos Eventos</h3>
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


      {/* ===== TAB: DOSSIÊ PERMANENTE ===== */}
      {activeTab === 'dossie' && (
        <DossieTab ativoId={ativo.id} plantas={plantas} user={user} />
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
              <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider">Documentos</h3>
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
              <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider">Lista de Materiais (BOM)</h3>
              <button onClick={() => { setBomEdit(null); setBomForm({ nome: '', codigo: '', quantidade: 1, unidade: 'UN', observacoes: '' }); setShowBomModal(true); }} className="btn-primary text-sm flex items-center gap-2"><Plus size={16} /> Adicionar</button>
            </div>
            {(ativo.materiais || []).length > 0 ? (
              <DataTable headers={[
                { label: '', className: 'w-8' },
                { label: 'Código' },
                { label: 'Descrição' },
                { label: 'Qtd', align: 'right' },
                { label: 'Un' },
                { label: 'Ações', align: 'right' },
              ]}>
                    {(ativo.materiais || []).filter(m => !bomSearch || (m.nome||'').toLowerCase().includes(bomSearch) || (m.codigo||'').toLowerCase().includes(bomSearch)).map(m => (
                      <DataRow key={m.id}>
                        <td className="py-1 px-1"><MaterialThumbnail images={m.images} nome={m.nome} categoria="" size="sm" /></td>
                        <td className="py-2 px-3 font-mono text-xs text-blue-400">{m.codigo || '—'}</td>
                        <td className="py-2 px-3 text-primary">{m.nome}</td>
                        <td className="py-2 px-3 text-right text-primary">{m.quantidade}</td>
                        <td className="py-2 px-3 text-secondary">{m.unidade}</td>
                        <td className="py-2 px-3 text-right">
                          <button onClick={() => { setBomEdit(m); setBomForm({ nome: m.nome, codigo: m.codigo||'', quantidade: m.quantidade, unidade: m.unidade, observacoes: m.observacoes||'' }); setShowBomModal(true); }} className="p-1 hover:bg-slate-700 rounded"><Edit size={12} className="text-secondary" /></button>
                        </td>
                      </DataRow>
                    ))}
              </DataTable>
            ) : (
              <p className="text-sm text-slate-600 text-center py-4">Nenhum material cadastrado.</p>
            )}
          </div>
        </div>
      )}

      {/* ===== TAB: QR CODE PÚBLICO ===== */}
      {activeTab === 'qrcode' && (
        <div className="space-y-4" data-testid="qrcode-tab">
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-4">QR Code do Equipamento</h3>
            <div className="flex flex-col lg:flex-row gap-6 items-start">
              {/* QR Preview — usa public_qr_url absoluta do backend */}
              <div className="bg-white p-4 rounded-xl flex flex-col items-center gap-2 shrink-0">
                {ativo.public_qr_url ? (
                  <QRCodeSVG value={ativo.public_qr_url} size={180} level="H" />
                ) : (
                  <div className="w-[180px] h-[180px] bg-slate-200 rounded flex items-center justify-center"><QrCode size={48} className="text-slate-400" /></div>
                )}
                <p className="text-xs text-slate-600 font-mono mt-1">{ativo.tag}</p>
              </div>
              {/* Info + Actions */}
              <div className="flex-1 space-y-4 min-w-0">
                <div>
                  <label className="text-xs text-slate-500 block mb-1">URL Pública</label>
                  <div className="flex items-center gap-2">
                    <code className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-emerald-400 flex-1 truncate" data-testid="qr-public-url">
                      {ativo.public_qr_url || 'QR Code não gerado'}
                    </code>
                    {ativo.public_qr_url && (
                      <button onClick={() => { navigator.clipboard.writeText(ativo.public_qr_url); toast.success('Link copiado!'); }}
                        className="btn-secondary text-xs px-3 py-2" data-testid="qr-copy-btn">Copiar</button>
                    )}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {ativo.public_qr_url && (
                    <>
                      <a href={ativo.public_qr_url} target="_blank" rel="noopener noreferrer" className="btn-primary text-xs px-3 py-2 inline-flex items-center gap-1.5" data-testid="qr-open-btn">
                        <ExternalLink size={14} /> Abrir página pública
                      </a>
                      <button onClick={async () => { try { const res = await api.get(`/ativos/${id}/qrcode/png`, { responseType: 'blob' }); const url = URL.createObjectURL(res.data); const a = document.createElement('a'); a.href = url; a.download = `QR_${ativo.tag}.png`; a.click(); URL.revokeObjectURL(url); toast.success('PNG baixado!'); } catch(e) { toast.error('Erro ao baixar PNG'); } }}
                        className="btn-secondary text-xs px-3 py-2" data-testid="qr-download-png">Baixar PNG</button>
                      <button onClick={async () => { try { const res = await api.get(`/ativos/${id}/qrcode/svg`, { responseType: 'blob' }); const url = URL.createObjectURL(res.data); const a = document.createElement('a'); a.href = url; a.download = `QR_${ativo.tag}.svg`; a.click(); URL.revokeObjectURL(url); toast.success('SVG baixado!'); } catch(e) { toast.error('Erro ao baixar SVG'); } }}
                        className="btn-secondary text-xs px-3 py-2" data-testid="qr-download-svg">Baixar SVG</button>
                    </>
                  )}
                </div>
                {/* Print models */}
                {ativo.public_qr_url && (
                  <div>
                    <label className="text-xs text-slate-500 block mb-2">Imprimir</label>
                    <div className="flex flex-wrap gap-2">
                      {[{m:'simples',l:'QR Simples'},{m:'etiqueta',l:'Etiqueta'},{m:'placa',l:'Placa A4'}].map(({m,l}) => (
                        <button key={m} onClick={async () => { try { const res = await api.get(`/ativos/${id}/qrcode/pdf?modelo=${m}`, { responseType: 'blob' }); const url = URL.createObjectURL(res.data); window.open(url); toast.success(`PDF ${l} gerado!`); } catch(e) { toast.error('Erro ao gerar PDF'); } }}
                          className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs px-3 py-2 rounded-lg transition-all" data-testid={`qr-print-${m}`}>
                          {l}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {/* Regenerate (Master/Admin only) */}
                {(user?.role === 'master' || user?.role === 'admin') && (
                  <div className="pt-2 border-t border-slate-800">
                    <button onClick={async () => { if (!window.confirm('Regenerar o QR Code irá invalidar o QR anterior. Continuar?')) return; try { await api.post(`/ativos/${id}/qrcode/regenerate`); toast.success('QR Code regenerado!'); fetchAtivo(); } catch(e) { toast.error('Erro ao regenerar'); } }}
                      className="text-xs text-amber-500 hover:text-amber-400 font-medium" data-testid="qr-regenerate-btn">
                      Regenerar QR Code
                    </button>
                    <p className="text-[10px] text-slate-600 mt-1">Isso invalidará imediatamente o QR Code anterior</p>
                  </div>
                )}
              </div>
            </div>
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

const KanbanBoard = ({ columns, items, onMove, onCardClick, onEdit, onDelete, plantas }) => {
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
            className={`flex-shrink-0 w-48 md:w-60 rounded-xl border ${col.color} ${col.bg} flex flex-col snap-start ${isDragOver ? 'ring-2 ring-emerald-400/50' : ''}`}
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
                  {/* Top: Unidade > Área stripe */}
                  <div className="px-3 py-1.5 bg-slate-800/60 border-b border-slate-700/30">
                    <p className="text-[10px] text-slate-400 font-medium">{plantas?.[0]?.nome ? `${plantas[0].nome} › ` : ''}{os.ativo?.sector?.nome || os.ativo?.area_nome || ''}</p>
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
  const [selectedOsIds, setSelectedOsIds] = useState([]);
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
      if (!navigator.onLine) {
        await queueOperation({ method: 'PATCH', url: `/ordens-servico/${osId}/status`, data: { new_status: newStatus }, priority: 2 });
        setOsList(prev => prev.map(os => os.id === osId ? { ...os, status: newStatus } : os));
        toast.info('Sem conexão — mudança de status salva para sincronizar');
      } else {
        await api.patch(`/ordens-servico/${osId}/status`, { new_status: newStatus });
        setOsList(prev => prev.map(os => os.id === osId ? { ...os, status: newStatus } : os));
        toast.success(`OS movida para ${kanbanColumns.find(c => c.id === newStatus)?.title || newStatus}`);
      }
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
    <PageContainer>
      <PageHeader title="Ordens de Serviço">
        <ExportButtons entity="ordens-servico" />
        <div className="flex bg-surface rounded-lg p-0.5">
          <button onClick={() => setViewMode('kanban')} className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${viewMode === 'kanban' ? 'bg-brand-20 text-brand' : 'text-secondary'}`} data-testid="view-kanban">
            <LayoutDashboard size={14} className="inline mr-1" />Kanban
          </button>
          <button onClick={() => setViewMode('list')} className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${viewMode === 'list' ? 'bg-brand-20 text-brand' : 'text-secondary'}`} data-testid="view-list">
            <List size={14} className="inline mr-1" />Lista
          </button>
        </div>
        {user?.role !== 'visualizador' && user?.role !== 'gerente' && (
        <button onClick={() => { setEditItem(null); setShowModal(true); }} className="btn-primary flex items-center gap-2" data-testid="add-os-btn">
          <Plus size={20} /> Nova OS
        </button>
        )}
      </PageHeader>
      
      <PageToolbar>
        <SearchInput value={searchOS} onChange={(e) => setSearchOS(e.target.value)} placeholder="Buscar por nº, título ou TAG do ativo..." />
        <button onClick={() => setShowFilters(!showFilters)}
          className={`px-3 py-2 rounded-lg text-xs font-medium border transition-all flex items-center gap-1.5 ${showFilters || activeFilterCount > 0 ? 'bg-brand-20 text-brand border-brand-30' : 'border-surface text-secondary hover:text-primary'}`}
          data-testid="os-toggle-filters"
        >
          <Filter size={14} />Filtros
          {activeFilterCount > 0 && <span className="bg-brand text-white text-[9px] w-4 h-4 rounded-full flex items-center justify-center">{activeFilterCount}</span>}
        </button>
        <div className="flex gap-1">
          {[
            { value: '', label: 'Todas' },
            { value: 'emergencia', label: 'Emerg.', cls: 'text-danger bg-danger-10 border-red-500/30' },
            { value: 'alta', label: 'Alta', cls: 'text-warning bg-warning-10 border-amber-500/30' },
            { value: 'media', label: 'Média', cls: 'text-success bg-brand-10 border-emerald-500/30' },
            { value: 'baixa', label: 'Baixa', cls: 'text-secondary bg-slate-500/10 border-slate-500/30' },
          ].map(p => (
            <button key={p.value} onClick={() => setFilterPriority(p.value)}
              className={`px-2 py-1.5 rounded-lg text-[10px] font-medium border transition-all ${filterPriority === p.value ? (p.cls || 'bg-brand-20 text-brand border-brand-30') : 'border-surface text-secondary hover:text-primary'}`}
              data-testid={`os-filter-priority-${p.value || 'all'}`}
            >{p.label}</button>
          ))}
        </div>

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
              className="text-xs text-secondary hover:text-brand flex items-center justify-center gap-1" data-testid="os-clear-all-filters">
              <X size={12} />Limpar filtros
            </button>
          </div>
        )}
      </PageToolbar>

      {loading ? <Loading rows={5} /> : viewMode === 'kanban' ? (
        <KanbanBoard
          columns={kanbanColumns}
          items={kanbanItems}
          onMove={handleKanbanMove}
          onCardClick={(os) => navigate(`/os/${os.id}`)}
          onEdit={['admin','master','pcm'].includes(user?.role) ? (os) => { setEditItem(os); setShowModal(true); } : null}
          onDelete={['admin','master'].includes(user?.role) ? (os) => setDeleteItem(os) : null}
          plantas={plantas}
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
                    {['master','admin','pcm'].includes(user?.role) && <BatchCheckbox id={os.id} selectedIds={selectedOsIds} setSelectedIds={setSelectedOsIds} />}
                    <div className="flex-1 cursor-pointer" onClick={() => navigate(`/os/${os.id}`)}>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-brand">#{os.numero}</span>
                        {os.ativo && <span className="text-xs text-slate-500">{plantas?.[0]?.nome ? `${plantas[0].nome} › ` : ''}{os.ativo.sector?.nome ? `${os.ativo.sector.nome} · ` : ''}{os.ativo.tag} — {os.ativo.nome}</span>}
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
      <BatchPrintBar selectedIds={selectedOsIds} entity="ordens-servico" onClear={() => setSelectedOsIds([])} entityLabel="OS" />
    </PageContainer>
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
  const [showFinalizarRapido, setShowFinalizarRapido] = useState(false);
  const [concluirForm, setConcluirForm] = useState({ servicos_realizados: '', causa_falha: '', solucao: '', tempo_execucao_minutos: '', observacoes: '', hora_inicio: '', hora_final: '' });
  const [hhManualForm, setHhManualForm] = useState({ executante_id: '', data_inicio: '', data_fim: '', horas: '', descricao: '' });
  const [showHhManual, setShowHhManual] = useState(false);
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
  const [plantas, setPlantas] = useState([]);
  const [docsVinculados, setDocsVinculados] = useState([]);
  const [confirmacoes, setConfirmacoes] = useState([]);
  const [procExecucao, setProcExecucao] = useState({ procedimento: null, execucao: null });
  const [procLoading, setProcLoading] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const fetchOS = async () => {
    try {
      const [osRes, histRes, matRes, hhRes, execRes, evtRes, tecRes, plantasRes] = await Promise.all([
        api.get(`/ordens-servico/${id}`),
        api.get(`/ordens-servico/${id}/historico`).catch(() => ({ data: [] })),
        api.get(`/ordens-servico/${id}/materiais`).catch(() => ({ data: [] })),
        api.get(`/hh/resumo/${id}`).catch(() => ({ data: { executantes: [], hh_total_liquida_min: 0 } })),
        api.get(`/os/${id}/executantes`).catch(() => ({ data: [] })),
        api.get(`/os/${id}/eventos`).catch(() => ({ data: [] })),
        api.get('/users/tecnicos').catch(() => ({ data: [] })),
        api.get('/plantas').catch(() => ({ data: [] })),
      ]);
      setOs(osRes.data);
      setHistorico(histRes.data);
      setMateriais(matRes.data);
      setHhResumo(hhRes.data);
      setExecutantes(execRes.data);
      setOsEventos(evtRes.data);
      setTecnicos(tecRes.data);
      setPlantas(plantasRes.data);
      
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

  // Fetch linked documents when OS loads
  useEffect(() => {
    if (!id) return;
    api.get(`/documentos-corporativos/vinculo-automatico/${id}`).then(r => setDocsVinculados(r.data.documentos || [])).catch(() => {});
    api.get(`/documentos-corporativos/confirmacoes/${id}`).then(r => setConfirmacoes(r.data || [])).catch(() => {});
    api.get(`/ordens-servico/${id}/procedimento-execucao`).then(r => setProcExecucao(r.data || { procedimento: null, execucao: null })).catch(() => {});
  }, [id]);
  
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

  const handleHhManual = async () => {
    try {
      if (!navigator.onLine) {
        await queueOperation({ method: 'POST', url: `/os/${id}/hh-manual`, data: hhManualForm, priority: 3 });
        toast.info('Sem conexão — HH salvo para sincronizar');
      } else {
        await api.post(`/os/${id}/hh-manual`, hhManualForm);
        toast.success('HH registrado!');
      }
      setShowHhManual(false);
      setHhManualForm({ executante_id: '', data_inicio: '', data_fim: '', horas: '', descricao: '' });
      if (navigator.onLine) fetchOS();
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const handleFinalizarRapido = async () => {
    if (!concluirForm.servicos_realizados?.trim()) { toast.error('Descreva o serviço executado'); return; }
    setUpdating(true);
    try {
      const concluirData = {
        servicos_realizados: concluirForm.servicos_realizados,
        tempo_execucao_minutos: parseInt(concluirForm.tempo_execucao_minutos) || 0,
        observacoes: [concluirForm.causa_falha && `Causa: ${concluirForm.causa_falha}`, concluirForm.solucao && `Solução: ${concluirForm.solucao}`, concluirForm.observacoes].filter(Boolean).join('\n'),
        skip_foto_check: true,
      };
      if (!navigator.onLine) {
        if (concluirForm.tempo_execucao_minutos) {
          const horas = parseFloat(concluirForm.tempo_execucao_minutos) / 60;
          await queueOperation({ method: 'POST', url: `/os/${id}/hh-manual`, data: { horas, descricao: 'HH da finalização rápida' }, priority: 2 });
        }
        await queueOperation({ method: 'POST', url: `/ordens-servico/${id}/concluir`, data: concluirData, priority: 2 });
        toast.info('Sem conexão — conclusão da OS salva para sincronizar');
        setOs(prev => prev ? { ...prev, status: 'concluida' } : prev);
      } else {
        if (concluirForm.tempo_execucao_minutos) {
          const horas = parseFloat(concluirForm.tempo_execucao_minutos) / 60;
          await api.post(`/os/${id}/hh-manual`, { horas, descricao: 'HH da finalização rápida' }).catch(() => {});
        }
        await api.post(`/ordens-servico/${id}/concluir`, concluirData);
        toast.success('OS finalizada com sucesso!');
      }
      setShowFinalizarRapido(false);
      if (navigator.onLine) fetchOS();
    } catch (e) { toast.error(normalizeError(e)); }
    finally { setUpdating(false); }
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
      if (!navigator.onLine) {
        await queueOperation({ method: 'POST', url: `/ordens-servico/${id}/${action}`, data: {}, priority: 2 });
        toast.info(`Sem conexão — ação "${action}" salva para sincronizar`);
        setOs(prev => prev ? { ...prev, status: action === 'iniciar' ? 'em_execucao' : 'pausada' } : prev);
      } else {
        await api.post(`/ordens-servico/${id}/${action}`);
        toast.success(`OS ${action === 'iniciar' ? 'iniciada' : 'pausada'}!`);
        fetchOS();
      }
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
      const concluirData = {
        servicos_realizados: concluirForm.servicos_realizados.trim(),
        tempo_execucao_minutos: tempo,
        observacoes: concluirForm.observacoes || null,
        data_inicio: concluirForm.hora_inicio ? new Date(concluirForm.hora_inicio).toISOString() : null,
        data_conclusao: concluirForm.hora_final ? new Date(concluirForm.hora_final).toISOString() : null,
      };
      if (!navigator.onLine) {
        await queueOperation({ method: 'POST', url: `/ordens-servico/${id}/concluir`, data: concluirData, priority: 2 });
        toast.info('Sem conexão — conclusão salva para sincronizar');
        setOs(prev => prev ? { ...prev, status: 'concluida' } : prev);
        setShowConcluir(false);
      } else {
        await api.post(`/ordens-servico/${id}/concluir`, concluirData);
        toast.success('OS concluída com sucesso!');
        setShowConcluir(false);
        fetchOS();
      }
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
              <div className="flex items-center gap-1 text-[10px] text-slate-500 mb-0.5">
                {plantas?.length > 0 && <span>{plantas[0].nome}</span>}
                {plantas?.length > 0 && os.ativo.sector && <span className="text-slate-600">›</span>}
                {os.ativo.sector && <span>{os.ativo.sector.nome || os.ativo.sector_nome}</span>}
              </div>
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
                <button onClick={async () => { try { await api.post(`/ordens-servico/${os.id}/aprovar`, { decisao: 'aprovada', observacao: '' }); toast.success('OS Aprovada!'); fetchOS(); } catch(e) { toast.error(normalizeError(e)); }}} className="flex-1 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg text-sm font-semibold hover:bg-emerald-500/30 transition-all" data-testid="os-btn-aprovar"><CheckCircle size={14} className="inline mr-1" /> Aprovar</button>
                <button onClick={async () => { const obs = prompt('Motivo da rejeição:'); if (obs !== null) { try { await api.post(`/ordens-servico/${os.id}/aprovar`, { decisao: 'rejeitada', observacao: obs }); toast.success('OS Rejeitada'); fetchOS(); } catch(e) { toast.error(normalizeError(e)); }}}} className="flex-1 py-2 bg-red-500/20 text-red-400 rounded-lg text-sm font-semibold hover:bg-red-500/30 transition-all" data-testid="os-btn-rejeitar"><XCircle size={14} className="inline mr-1" /> Rejeitar</button>
                <button onClick={async () => { const obs = prompt('Observação para revisão:'); if (obs !== null) { try { await api.post(`/ordens-servico/${os.id}/aprovar`, { decisao: 'revisao', observacao: obs }); toast.success('Enviada para revisão'); fetchOS(); } catch(e) { toast.error(normalizeError(e)); }}}} className="flex-1 py-2 bg-amber-500/20 text-amber-400 rounded-lg text-sm font-semibold hover:bg-amber-500/30 transition-all"><Edit3 size={14} className="inline mr-1" /> Revisão</button>
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

      {/* ============ HORAS TRABALHADAS ============ */}
      <div className="glass-card p-4" data-testid="hh-section">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider flex items-center gap-2">
            <Clock size={16} /> Horas Trabalhadas
          </h3>
          {!['concluida','encerrada','cancelada'].includes(os.status) && (
            <button onClick={() => setShowHhManual(!showHhManual)} className="text-xs text-brand hover:brightness-110 flex items-center gap-1" data-testid="hh-manual-toggle">
              <Plus size={14} /> Lançar HH
            </button>
          )}
        </div>

        {/* HH Manual Form (inline compact) */}
        {showHhManual && (
          <div className="bg-slate-900/60 rounded-lg p-3 mb-3 space-y-2 border border-slate-800" data-testid="hh-manual-form">
            <div className="grid grid-cols-2 gap-2">
              <div><label className="text-[10px] text-slate-500">Executante</label>
                <select value={hhManualForm.executante_id || user?.id} onChange={e => setHhManualForm({...hhManualForm, executante_id: e.target.value})} className="input-industrial w-full px-2 text-xs h-9">
                  <option value={user?.id}>{user?.nome} (eu)</option>
                  {tecnicos.filter(t => t.id !== user?.id).map(t => <option key={t.id} value={t.id}>{t.nome}</option>)}
                </select>
              </div>
              <div><label className="text-[10px] text-slate-500">Horas Trabalhadas</label>
                <input type="number" step="0.5" min="0.5" value={hhManualForm.horas} onChange={e => setHhManualForm({...hhManualForm, horas: e.target.value})}
                  className="input-industrial w-full px-2 text-xs h-9" placeholder="Ex: 2.5" data-testid="hh-manual-horas" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div><label className="text-[10px] text-slate-500">Início</label>
                <input type="datetime-local" value={hhManualForm.data_inicio} onChange={e => setHhManualForm({...hhManualForm, data_inicio: e.target.value})} className="input-industrial w-full px-2 text-xs h-9" /></div>
              <div><label className="text-[10px] text-slate-500">Fim</label>
                <input type="datetime-local" value={hhManualForm.data_fim} onChange={e => setHhManualForm({...hhManualForm, data_fim: e.target.value})} className="input-industrial w-full px-2 text-xs h-9" /></div>
            </div>
            <input value={hhManualForm.descricao} onChange={e => setHhManualForm({...hhManualForm, descricao: e.target.value})} className="input-industrial w-full px-2 text-xs h-9" placeholder="Descrição da atividade (opcional)" />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowHhManual(false)} className="text-xs text-slate-400 px-3 py-1.5">Cancelar</button>
              <button onClick={handleHhManual} className="text-xs bg-brand-20 text-brand px-3 py-1.5 rounded-lg font-medium" data-testid="hh-manual-save">Salvar</button>
            </div>
          </div>
        )}

        {/* Cronômetro (compacto, apenas se ativo e OS em execução) */}
        {!['concluida','encerrada','cancelada'].includes(os.status) && (
          <div className="flex items-center gap-3 mb-3 bg-slate-900/40 rounded-lg px-3 py-2">
            <p className={`text-lg font-mono font-bold ${timerRunning ? 'text-emerald-400' : 'text-slate-600'}`} data-testid="hh-timer-display">
              {formatTimer(timerSeconds)}
            </p>
            <p className="text-[10px] text-slate-600 flex-1">
              {!hhStatus && 'Pronto'}{(hhStatus === 'iniciar' || hhStatus === 'retornar') && 'Trabalhando...'}{hhStatus === 'pausar' && 'Pausado'}{hhStatus === 'finalizar' && '—'}
            </p>
            <div className="flex gap-1">
              {(!hhStatus || hhStatus === 'finalizar') && <button onClick={() => handleHH('iniciar')} className="p-1.5 rounded bg-brand-20 text-brand" data-testid="hh-iniciar" title="Iniciar"><Play size={14} /></button>}
              {(hhStatus === 'iniciar' || hhStatus === 'retornar') && <>
                <button onClick={() => handleHH('pausar')} className="p-1.5 rounded bg-amber-500/20 text-amber-400" data-testid="hh-pausar" title="Pausar"><Pause size={14} /></button>
                <button onClick={() => handleHH('finalizar')} className="p-1.5 rounded bg-blue-500/20 text-blue-400" data-testid="hh-finalizar" title="Finalizar"><CheckCircle size={14} /></button>
              </>}
              {hhStatus === 'pausar' && <>
                <button onClick={() => handleHH('retornar')} className="p-1.5 rounded bg-brand-20 text-brand" data-testid="hh-retornar" title="Retornar"><Play size={14} /></button>
                <button onClick={() => handleHH('finalizar')} className="p-1.5 rounded bg-blue-500/20 text-blue-400" title="Finalizar"><CheckCircle size={14} /></button>
              </>}
            </div>
          </div>
        )}

        {/* HH Summary — compact */}
        {hhResumo && hhResumo.executantes?.length > 0 && (
          <div className="space-y-1">
            {hhResumo.executantes.map(e => (
              <div key={e.user_id} className="flex items-center justify-between text-xs bg-slate-800/50 rounded px-3 py-1.5">
                <span className="text-slate-300">{e.user_nome}</span>
                <span className="text-brand font-semibold">{Math.floor(e.hh_liquida_min/60)}h{Math.round(e.hh_liquida_min%60)}m</span>
              </div>
            ))}
            <div className="text-right text-[10px] text-slate-500 pt-1">
              Total: <span className="text-brand font-bold">{Math.floor(hhResumo.hh_total_liquida_min/60)}h{Math.round(hhResumo.hh_total_liquida_min%60)}m</span>
            </div>
          </div>
        )}
      </div>

      {/* ============ EXECUTANTES DA OS ============ */}
      <div className="glass-card p-4" data-testid="os-executantes-section">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider flex items-center gap-2">
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

      {/* ============ PROCEDIMENTO OPERACIONAL ============ */}
      {procExecucao.procedimento && (() => {
        const proc = procExecucao.procedimento;
        const exec = procExecucao.execucao || {};
        const etapasExec = exec.etapas_executadas || {};
        const sortedEtapas = [...(proc.etapas || [])].sort((a, b) => a.ordem - b.ordem);
        const totalEtapas = sortedEtapas.length;
        const concluidas = sortedEtapas.filter(e => etapasExec[e.id]?.concluida).length;
        const pct = totalEtapas > 0 ? Math.round((concluidas / totalEtapas) * 100) : 0;
        const nextPendingId = sortedEtapas.find(e => !etapasExec[e.id]?.concluida)?.id;

        const handleEtapa = async (etapaId, concluida, obs) => {
          try {
            await api.post(`/ordens-servico/${id}/procedimento-execucao/etapa`, { etapa_id: etapaId, concluida, observacao: obs || '' });
            const r = await api.get(`/ordens-servico/${id}/procedimento-execucao`);
            setProcExecucao(r.data);
            toast.success(concluida ? 'Etapa concluída' : 'Etapa reaberta');
          } catch (e) { toast.error(normalizeError(e)); }
        };

        return (
          <div className="glass-card p-4" data-testid="procedimento-operacional-section">
            <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
              <ClipboardCheck size={16} /> Procedimento Operacional
            </h3>

            {/* Cabeçalho profissional */}
            <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 mb-4" data-testid="proc-header">
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mb-2">
                <span className="text-xs font-mono bg-slate-700/60 px-2 py-0.5 rounded" data-testid="proc-header-code">{proc.codigo}</span>
                <span className="text-sm text-slate-100 font-semibold">{proc.nome}</span>
              </div>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
                <span>Rev. {proc.revisao}</span>
                <span>Versão {proc.versao || 1}</span>
                {proc.tempo_estimado_minutos && <span className="flex items-center gap-1"><Clock size={11} />{proc.tempo_estimado_minutos} min</span>}
                <span className={`px-2 py-0.5 rounded-full ${proc.status === 'aprovado' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>{proc.status === 'aprovado' ? 'Aprovado' : proc.status}</span>
              </div>
              {proc.descricao && <p className="text-xs text-slate-400 mt-2">{proc.descricao}</p>}
            </div>

            {/* Barra de progresso */}
            <div className="mb-4" data-testid="proc-progress">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs text-slate-400">Etapas concluídas</span>
                <span className="text-xs font-semibold" style={{ color: pct === 100 ? '#34d399' : '#94a3b8' }}>{concluidas} / {totalEtapas}</span>
              </div>
              <div className="w-full h-2 bg-slate-700/50 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: pct === 100 ? '#34d399' : pct > 0 ? '#3b82f6' : 'transparent' }} />
              </div>
            </div>

            {/* Etapas */}
            <div className="space-y-2">
              {sortedEtapas.map(etapa => {
                const ex = etapasExec[etapa.id] || {};
                const done = ex.concluida;
                const isNext = etapa.id === nextPendingId;
                const borderClass = done ? 'border-emerald-500/30 bg-emerald-500/5' : isNext ? 'border-blue-500/40 bg-blue-500/5 ring-1 ring-blue-500/20' : 'border-slate-700/50 bg-slate-800/30';
                return (
                  <div key={etapa.id} className={`p-3 rounded-lg border ${borderClass}`} data-testid={`proc-etapa-exec-${etapa.id}`}>
                    <div className="flex items-start gap-3">
                      <button onClick={() => handleEtapa(etapa.id, !done, ex.observacao)} className={`mt-0.5 w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors ${done ? 'border-emerald-500 bg-emerald-500 text-white' : isNext ? 'border-blue-400 hover:border-blue-300' : 'border-slate-500 hover:border-emerald-400'}`} data-testid={`proc-etapa-check-${etapa.id}`}>
                        {done && <CheckCircle size={12} />}
                      </button>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-500">{etapa.ordem}.</span>
                          <span className={`text-sm ${done ? 'text-slate-400 line-through' : 'text-slate-200'}`}>{etapa.titulo}</span>
                          {etapa.obrigatoria && <span className="text-red-400 text-xs">*</span>}
                          {isNext && !done && <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-medium">Próxima</span>}
                        </div>
                        {etapa.descricao && <p className="text-xs text-slate-400 mt-1">{etapa.descricao}</p>}
                        {done && ex.executado_por_nome && <p className="text-xs text-emerald-400/70 mt-1">{ex.executado_por_nome} — {(ex.executado_em || '').slice(0,16).replace('T',' ')}</p>}
                        {!done && (
                          <input placeholder="Observação (opcional)" className="input-field text-xs mt-2 w-full" onBlur={e => { if (e.target.value.trim()) handleEtapa(etapa.id, false, e.target.value.trim()); }} data-testid={`proc-etapa-obs-${etapa.id}`} />
                        )}
                        {ex.observacao && <p className="text-xs text-slate-400 mt-1 italic">Obs: {ex.observacao}</p>}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}

      {/* ============ PROCEDIMENTOS APLICÁVEIS ============ */}
      {docsVinculados.length > 0 && (
        <div className="glass-card p-4" data-testid="docs-vinculados-section">
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
            <FileText size={16} /> Procedimentos Aplicáveis ({docsVinculados.length})
          </h3>
          <div className="space-y-2">
            {docsVinculados.map(doc => {
              const isConfirmed = confirmacoes.some(c => c.documento_id === doc.id);
              return (
                <div key={doc.id} className="flex items-center justify-between p-2 bg-slate-800/50 rounded-lg" data-testid={`doc-vinc-${doc.id}`}>
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {doc.safety_document && <Shield size={14} className="text-amber-400 shrink-0" />}
                    <span className="text-sm text-primary truncate">{doc.title}</span>
                    {doc.code && <span className="text-xs bg-slate-700 px-1.5 py-0.5 rounded shrink-0">{doc.code}</span>}
                    <span className="text-xs text-brand shrink-0">v{doc.version || 1}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {doc.requires_acknowledgement && (
                      isConfirmed
                        ? <span className="text-xs text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded">Ciente</span>
                        : <button onClick={async () => {
                            try {
                              await api.post(`/documentos-corporativos/confirmar-leitura/${id}`, { documento_id: doc.id, versao_lida: doc.version || 1 });
                              toast.success('Leitura confirmada');
                              const r = await api.get(`/documentos-corporativos/confirmacoes/${id}`);
                              setConfirmacoes(r.data);
                            } catch { toast.error('Erro'); }
                          }} className="text-xs text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded hover:bg-amber-400/20" data-testid={`confirm-${doc.id}`}>
                            Li e estou ciente
                          </button>
                    )}
                    <button onClick={() => navigate(`/biblioteca?view=${doc.id}`)} className="text-xs text-blue-400 hover:text-blue-300" data-testid={`view-doc-${doc.id}`}>Visualizar</button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ============ TIMELINE DE EVENTOS ============ */}
      {osEventos.length > 0 && (
        <div className="glass-card p-4" data-testid="os-eventos-timeline">
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
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
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider flex items-center gap-2">
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
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <MaterialThumbnail images={m.image_url ? [m.image_url] : []} nome={m.descricao} categoria="" size="sm" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-brand text-sm">{m.codigo}</span>
                      <span className="text-slate-300 text-sm">{m.descricao}</span>
                    </div>
                    <p className="text-xs text-slate-500">
                      {m.quantidade} {m.unidade} • {m.local_estoque} • {m.usuario_nome} • {new Date(m.created_at).toLocaleString('pt-BR')}
                    </p>
                  </div>
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
          {/* Preview do material selecionado */}
          {matForm.item_estoque_id && (() => {
            const sel = estoqueItems.find(i => i.id === matForm.item_estoque_id);
            return sel ? (
              <div className="flex items-center gap-3 p-2 bg-slate-800/50 rounded-lg border border-slate-700/50">
                <MaterialThumbnail images={sel.images} nome={sel.nome} categoria={sel.categoria} size="lg" />
                <div>
                  <p className="text-sm text-slate-200 font-medium">{sel.nome}</p>
                  <p className="text-xs text-slate-500">{sel.sku} • Disp: {sel.quantidade} {sel.unidade}</p>
                </div>
              </div>
            ) : null;
          })()}
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
        <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
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
          {(os.status === 'aberta' || os.status === 'programada' || os.status === 'disponivel') && (
            <button onClick={() => handleAction('iniciar')} disabled={updating} className="btn-primary w-full flex items-center justify-center gap-2" data-testid="os-iniciar-btn">
              <Play size={20} /> {updating ? 'Iniciando...' : 'Iniciar OS'}
            </button>
          )}
          {os.status === 'em_execucao' && (
            <>
              <button onClick={() => setShowFinalizarRapido(true)} disabled={updating} className="btn-primary w-full flex items-center justify-center gap-2" data-testid="os-finalizar-rapido">
                <Zap size={20} /> Finalizar Rapidamente
              </button>
              <div className="flex gap-2">
                <button onClick={() => handleAction('concluir')} disabled={updating} className="flex-1 btn-secondary flex items-center justify-center gap-2 text-sm" data-testid="os-concluir-btn">
                  <CheckCircle size={16} /> Concluir
                </button>
                <button onClick={() => handleAction('pausar')} disabled={updating} className="flex-1 btn-secondary flex items-center justify-center gap-2 text-sm">
                  <Pause size={16} /> Pausar
                </button>
              </div>
            </>
          )}
          {os.status === 'pausada' && (
            <>
              <button onClick={() => setShowFinalizarRapido(true)} disabled={updating} className="btn-primary w-full flex items-center justify-center gap-2" data-testid="os-finalizar-rapido-pausada">
                <Zap size={20} /> Finalizar Rapidamente
              </button>
              <button onClick={() => handleAction('iniciar')} disabled={updating} className="btn-secondary w-full flex items-center justify-center gap-2">
                <Play size={16} /> {updating ? 'Retomando...' : 'Retomar OS'}
              </button>
            </>
          )}
        </div>
      )}

      {/* Print OS Button — always visible */}
      <button
        onClick={() => { import('./lib/api').then(m => m.openAuthenticatedPdf(`/ordens-servico/${id}/pdf`, (msg) => toast.error(msg))); }}
        className="btn-secondary w-full flex items-center justify-center gap-2 mt-2"
        data-testid="os-print-btn"
      >
        <Printer size={18} /> Imprimir OS
      </button>

      {/* Modal Concluir OS */}
      <Modal isOpen={showConcluir} onClose={() => setShowConcluir(false)} title="Concluir Ordem de Serviço" size="md">
        <div className="space-y-4">
          {os.ativo && (
            <div className="bg-slate-800/50 rounded-lg p-3">
              {os.ativo.sector && <p className="text-xs text-slate-500 uppercase">{os.ativo.sector.nome || os.ativo.sector_nome}</p>}
              <span className="font-mono text-brand text-sm">{os.ativo.tag}</span>
              <span className="text-slate-300 text-sm ml-2">{os.ativo.nome}</span>
            </div>
          )}
          <FormInput label="Servico Executado" required>
            <textarea value={concluirForm.servicos_realizados} onChange={(e) => setConcluirForm({...concluirForm, servicos_realizados: e.target.value})}
              className="input-industrial w-full px-4 py-3 min-h-[120px]" placeholder="Descreva o servico realizado..." data-testid="os-servico-input" />
          </FormInput>
          <div className="grid grid-cols-2 gap-3">
            <FormInput label="Hora Inicial">
              <input type="datetime-local" value={concluirForm.hora_inicio} onChange={(e) => {
                const val = e.target.value;
                setConcluirForm(prev => {
                  const updated = {...prev, hora_inicio: val};
                  if (val && prev.hora_final) {
                    const diff = Math.round((new Date(prev.hora_final) - new Date(val)) / 60000);
                    if (diff > 0) updated.tempo_execucao_minutos = String(diff);
                  }
                  return updated;
                });
              }} className="input-industrial w-full px-4" data-testid="os-hora-inicio" />
            </FormInput>
            <FormInput label="Hora Final">
              <input type="datetime-local" value={concluirForm.hora_final} onChange={(e) => {
                const val = e.target.value;
                setConcluirForm(prev => {
                  const updated = {...prev, hora_final: val};
                  if (prev.hora_inicio && val) {
                    const diff = Math.round((new Date(val) - new Date(prev.hora_inicio)) / 60000);
                    if (diff > 0) updated.tempo_execucao_minutos = String(diff);
                  }
                  return updated;
                });
              }} className="input-industrial w-full px-4" data-testid="os-hora-final" />
            </FormInput>
          </div>
          <FormInput label="Tempo Gasto (minutos)">
            <input type="number" min="1" value={concluirForm.tempo_execucao_minutos} onChange={(e) => setConcluirForm({...concluirForm, tempo_execucao_minutos: e.target.value})}
              className="input-industrial w-full px-4" placeholder="Calculado automaticamente" data-testid="os-tempo-input" />
          </FormInput>
          <FormInput label="Observações">
            <textarea value={concluirForm.observacoes} onChange={(e) => setConcluirForm({...concluirForm, observacoes: e.target.value})}
              className="input-industrial w-full px-4 py-3 min-h-[60px]" placeholder="Observações adicionais..." />
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

      {/* Modal Finalizar Rapidamente */}
      <Modal isOpen={showFinalizarRapido} onClose={() => setShowFinalizarRapido(false)} title="Finalizar Rapidamente" size="md">
        <div className="space-y-3" data-testid="finalizar-rapido-modal">
          {os.ativo && (
            <div className="bg-slate-800/50 rounded-lg p-2 flex items-center gap-2">
              <span className="font-mono text-brand text-xs">{os.ativo.tag}</span>
              <span className="text-slate-400 text-xs">{os.ativo.nome}</span>
            </div>
          )}
          <FormInput label="✔ Serviço executado *">
            <textarea value={concluirForm.servicos_realizados} onChange={(e) => setConcluirForm({...concluirForm, servicos_realizados: e.target.value})}
              className="input-industrial w-full px-3 py-2 min-h-[80px] text-sm" placeholder="O que foi feito?" data-testid="rapido-servico" autoFocus />
          </FormInput>
          <div className="grid grid-cols-2 gap-2">
            <FormInput label="✔ Causa da falha">
              <input value={concluirForm.causa_falha || ''} onChange={(e) => setConcluirForm({...concluirForm, causa_falha: e.target.value})}
                className="input-industrial w-full px-3 text-sm h-10" placeholder="Desgaste, folga..." data-testid="rapido-causa" />
            </FormInput>
            <FormInput label="✔ Solução aplicada">
              <input value={concluirForm.solucao || ''} onChange={(e) => setConcluirForm({...concluirForm, solucao: e.target.value})}
                className="input-industrial w-full px-3 text-sm h-10" placeholder="Troca, ajuste..." data-testid="rapido-solucao" />
            </FormInput>
          </div>
          <FormInput label="✔ HH (minutos)">
            <input type="number" min="1" value={concluirForm.tempo_execucao_minutos} onChange={(e) => setConcluirForm({...concluirForm, tempo_execucao_minutos: e.target.value})}
              className="input-industrial w-full px-3 text-sm h-10" placeholder="60" data-testid="rapido-hh" />
          </FormInput>
          <FormInput label="Observações">
            <input value={concluirForm.observacoes} onChange={(e) => setConcluirForm({...concluirForm, observacoes: e.target.value})}
              className="input-industrial w-full px-3 text-sm h-10" placeholder="Notas adicionais..." data-testid="rapido-obs" />
          </FormInput>
          <SignaturePad
            label="Assinatura do Executor"
            width={280}
            height={80}
            onCapture={async (dataUrl) => {
              try {
                await api.post('/assinaturas/capturar', {
                  entity_type: 'os', entity_id: id, papel: 'executor',
                  nome: user?.nome || user?.email || '-', cargo: user?.role || '',
                  imagem_base64: dataUrl, status: 'assinado'
                });
                toast.success('Assinatura capturada');
              } catch { toast.error('Erro ao capturar assinatura'); }
            }}
          />
          <button onClick={handleFinalizarRapido} disabled={updating || !concluirForm.servicos_realizados?.trim()}
            className="w-full py-3 rounded-lg font-bold text-sm flex items-center justify-center gap-2 bg-brand text-slate-950 active:scale-[0.98] transition-all disabled:opacity-50"
            data-testid="rapido-confirmar">
            <Zap size={18} /> {updating ? 'Finalizando...' : 'Finalizar OS'}
          </button>
        </div>
      </Modal>
    </div>
  );
};

// Estoque Page
// EstoquePage → extracted to /pages/EstoquePage.js

// InspecoesPage, InspecaoDetailPage, RondaPage → extracted to /pages/InspecoesPages.js

// BibliotecaPage → extracted to /pages/BibliotecaPage.js

// Extracted pages: EquipePage, WhiteLabelDesignerPage, ConsultaEquipamentosPage,
// DossiePesquisaPage, PortalPublicoPage, PortalTecnicoPage, MasterCleanupPage, OrgConfigPage
// → /pages/*.js

// AppLayout, ConsentGate → extracted to /app/MainLayout.js and /app/AppProviders.js

// ============== SOBRE O MAINTRIX ==============
const SobrePage = () => {
  const [info, setInfo] = useState(null);
  useEffect(() => { api.get('/compliance/about').then(r => setInfo(r.data)).catch(() => {}); }, []);
  if (!info) return <Loading rows={2} />;
  return (
    <PageContainer>
      <PageHeader title="Sobre o MAINTRIX" subtitle="Informações do sistema" />
      <div className="max-w-lg mx-auto space-y-6">
        <div className="glass-card p-6 text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-brand-10 flex items-center justify-center mx-auto">
            <Cog size={32} className="text-brand" />
          </div>
          <h2 className="text-2xl font-bold text-brand">{info.product}</h2>
          <div className="space-y-1 text-sm">
            <p className="text-secondary">Versão <span className="text-primary font-mono">{info.version}</span></p>
            <p className="text-secondary">Build <span className="text-primary font-mono">{info.build}</span></p>
            <p className="text-secondary">Ambiente: <span className="text-primary capitalize">{info.environment}</span></p>
          </div>
        </div>
        <div className="glass-card p-6 space-y-3">
          <h3 className="text-sm font-semibold text-primary uppercase tracking-wider">Contato</h3>
          <p className="text-sm text-secondary">Suporte: <a href={`mailto:${info.support_email}`} className="text-brand hover:underline">{info.support_email}</a></p>
          <p className="text-sm text-secondary">Privacidade: <a href={`mailto:${info.privacy_email}`} className="text-brand hover:underline">{info.privacy_email}</a></p>
        </div>
        <div className="glass-card p-6 space-y-3">
          <h3 className="text-sm font-semibold text-primary uppercase tracking-wider">Documentos Legais</h3>
          <div className="flex flex-col gap-2">
            <a href="/termos" className="text-sm text-brand hover:underline flex items-center gap-2"><FileText size={14} /> Termos de Uso v{info.terms_version}</a>
            <a href="/privacidade" className="text-sm text-brand hover:underline flex items-center gap-2"><Shield size={14} /> Politica de Privacidade v{info.privacy_version}</a>
          </div>
        </div>
        <p className="text-center text-xs text-secondary">{info.copyright}</p>
      </div>
    </PageContainer>
  );
};

// ============== LEGAL DOCUMENT PAGES ==============
const LegalDocPage = ({ type }) => {
  const [doc, setDoc] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDoc = useCallback(() => {
    setLoading(true);
    setError(null);
    api.get(`/compliance/${type}`)
      .then(r => {
        if (!r.data || !r.data.content) {
          setError('Documento sem conteúdo disponível.');
        } else {
          setDoc(r.data);
        }
      })
      .catch(err => {
        const msg = err?.response?.status === 401 ? 'Sessão expirada. Faça login novamente.'
          : err?.response?.status === 404 ? 'Documento não encontrado.'
          : err?.response?.status >= 500 ? 'Erro no servidor. Tente novamente.'
          : err?.message === 'Network Error' ? 'Sem conexão com o servidor.'
          : 'Erro ao carregar documento.';
        setError(msg);
        console.error(`[LegalDocPage] Falha ao carregar /compliance/${type}:`, err?.response?.status || err?.message);
      })
      .finally(() => setLoading(false));
  }, [type]);

  useEffect(() => { fetchDoc(); }, [fetchDoc]);

  if (loading) return <Loading rows={4} />;

  if (error) return (
    <PageContainer>
      <div className="glass-card p-8 max-w-lg mx-auto mt-12 text-center" data-testid="legal-doc-error">
        <AlertCircle size={40} className="mx-auto mb-4 text-red-400" />
        <p className="text-sm text-slate-300 mb-4">{error}</p>
        <button onClick={fetchDoc} className="btn-primary text-sm" data-testid="legal-doc-retry">Tentar novamente</button>
      </div>
    </PageContainer>
  );

  return (
    <PageContainer>
      <PageHeader title={type === 'terms' ? 'Termos de Uso' : 'Política de Privacidade'} subtitle={`Versão ${doc.version}`} />
      <div className="glass-card p-6 max-w-3xl mx-auto">
        <div className="prose prose-invert prose-sm whitespace-pre-wrap text-sm text-slate-300 leading-relaxed" data-testid="legal-doc-content">
          {doc.content}
        </div>
      </div>
    </PageContainer>
  );
};

// Auth Provider
// AuthProvider, BrandingLoader → extracted to /app/AppProviders.js

// App
function App() {
  return (
    <AppProviders>
      <BrowserRouter>
        <BrandingLoader>
          <ConsentGate>
          <Suspense fallback={<LazyFallback />}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/termos" element={<ProtectedRoute><AppLayout><LegalDocPage type="terms" /></AppLayout></ProtectedRoute>} />
            <Route path="/privacidade" element={<ProtectedRoute><AppLayout><LegalDocPage type="privacy" /></AppLayout></ProtectedRoute>} />
            <Route path="/sobre" element={<ProtectedRoute><AppLayout><SobrePage /></AppLayout></ProtectedRoute>} />
            <Route path="/" element={<ProtectedRoute allow={ROLES_EXCEPT_VIEWER}><AppLayout><CentralTrabalhoPage /></AppLayout></ProtectedRoute>} />
            <Route path="/dashboard" element={<ProtectedRoute allow={ROLES_EXCEPT_VIEWER}><AppLayout><DashboardPage /></AppLayout></ProtectedRoute>} />
            <Route path="/ativos" element={<ProtectedRoute allow={ROLES_EXCEPT_VIEWER}><AppLayout><AtivosPage /></AppLayout></ProtectedRoute>} />
            <Route path="/ativos/:id" element={<ProtectedRoute><AppLayout><AssetDossierPage /></AppLayout></ProtectedRoute>} />
            <Route path="/os" element={<ProtectedRoute allow={ROLES_EXCEPT_VIEWER}><AppLayout><OSPage /></AppLayout></ProtectedRoute>} />
            <Route path="/os/:id" element={<ProtectedRoute><AppLayout><OSDetailPage /></AppLayout></ProtectedRoute>} />
            <Route path="/estoque" element={<ProtectedRoute allow={ROLES_EXCEPT_VIEWER}><AppLayout><EstoquePage /></AppLayout></ProtectedRoute>} />
            <Route path="/inspecoes" element={<ProtectedRoute allow={ROLES_EXCEPT_VIEWER}><AppLayout><InspecoesPage /></AppLayout></ProtectedRoute>} />
            <Route path="/inspecoes/:id" element={<ProtectedRoute><AppLayout><InspecaoDetailPage /></AppLayout></ProtectedRoute>} />
            <Route path="/ronda" element={<ProtectedRoute><AppLayout><RondaPage /></AppLayout></ProtectedRoute>} />
            <Route path="/scanner" element={<ProtectedRoute><AppLayout><ScannerPage /></AppLayout></ProtectedRoute>} />
            <Route path="/sobressalentes" element={<ProtectedRoute allow={ROLES_EXCEPT_VIEWER}><AppLayout><SobressalentesPage /></AppLayout></ProtectedRoute>} />
            <Route path="/paradas" element={<ProtectedRoute allow={ROLES_EXCEPT_VIEWER}><AppLayout><ParadasPage /></AppLayout></ProtectedRoute>} />
            <Route path="/solicitar" element={<ProtectedRoute allow={['master','admin','pcm','supervisor','tec_mecanico','tec_eletrico','instrumentista','lubrificador','tecnico','inspetor','operador']}><AppLayout><SolicitacaoServicoPage /></AppLayout></ProtectedRoute>} />
            <Route path="/minha-area" element={<ProtectedRoute><AppLayout><FieldOpsPage /></AppLayout></ProtectedRoute>} />
            <Route path="/assistente" element={<ProtectedRoute><AppLayout><AssistentePage /></AppLayout></ProtectedRoute>} />
            <Route path="/admin/usuarios" element={<ProtectedRoute allow={['master','admin']}><AppLayout><AdminUsuariosPage /></AppLayout></ProtectedRoute>} />
            <Route path="/admin/templates" element={<ProtectedRoute allow={['master','admin','pcm']}><AppLayout><AdminTemplatesPage /></AppLayout></ProtectedRoute>} />
            <Route path="/config/documentos" element={<ProtectedRoute allow={['master','admin','pcm']}><AppLayout><DocConfigPage /></AppLayout></ProtectedRoute>} />
            <Route path="/config/construtor" element={<ProtectedRoute allow={['master','admin']}><AppLayout><LayoutBuilderPage /></AppLayout></ProtectedRoute>} />
            <Route path="/biblioteca" element={<ProtectedRoute><AppLayout><BibliotecaCorporativaPage /></AppLayout></ProtectedRoute>} />
            <Route path="/procedimentos" element={<ProtectedRoute allow={['master','admin','pcm','supervisor']}><AppLayout><ProcedimentosPage /></AppLayout></ProtectedRoute>} />
            <Route path="/admin/auditoria" element={<ProtectedRoute allow={['master','admin','gerente','supervisor']}><AppLayout><AuditoriaPage /></AppLayout></ProtectedRoute>} />
            <Route path="/setores" element={<ProtectedRoute><AppLayout><SetoresPage /></AppLayout></ProtectedRoute>} />
            <Route path="/plantas" element={<ProtectedRoute><AppLayout><UnidadesPage /></AppLayout></ProtectedRoute>} />
            <Route path="/unidades" element={<ProtectedRoute allow={['master','admin']}><AppLayout><UnidadesPage /></AppLayout></ProtectedRoute>} />
            <Route path="/admin/config" element={<ProtectedRoute allow={['master','admin']}><AppLayout><OrgConfigPage /></AppLayout></ProtectedRoute>} />
            <Route path="/equipe" element={<ProtectedRoute allow={['master','admin','pcm','supervisor']}><AppLayout><EquipePage /></AppLayout></ProtectedRoute>} />
            <Route path="/biblioteca/equipamentos" element={<ProtectedRoute allow={['master','admin','pcm']}><AppLayout><BibliotecaPage /></AppLayout></ProtectedRoute>} />
            <Route path="/dossie" element={<ProtectedRoute allow={['master','admin','pcm','supervisor','gerente']}><AppLayout><DossiePesquisaPage /></AppLayout></ProtectedRoute>} />
            <Route path="/master/white-label" element={<ProtectedRoute allow={['master']}><AppLayout><WhiteLabelDesignerPage /></AppLayout></ProtectedRoute>} />
            <Route path="/master/cleanup" element={<ProtectedRoute allow={['master']}><AppLayout><MasterCleanupPage /></AppLayout></ProtectedRoute>} />
            <Route path="/consulta" element={<ProtectedRoute><AppLayout><ConsultaEquipamentosPage /></AppLayout></ProtectedRoute>} />
            <Route path="/portal/equipamento/:id" element={<PublicErrorBoundary><PortalPublicoPage /></PublicErrorBoundary>} />
            <Route path="/equipamento/:slug/:token" element={<PublicErrorBoundary><PublicEquipmentPage /></PublicErrorBoundary>} />
            <Route path="/portal/tecnico/:id" element={<ProtectedRoute><AppLayout><PortalTecnicoPage /></AppLayout></ProtectedRoute>} />
            <Route path="*" element={<CatchAllRedirect />} />
          </Routes>
          </Suspense>
          </ConsentGate>
        </BrandingLoader>
        <Toaster position="top-center" richColors />
      </BrowserRouter>
    </AppProviders>
  );
}

export default App;

