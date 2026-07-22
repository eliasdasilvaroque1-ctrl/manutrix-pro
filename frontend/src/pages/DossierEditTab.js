/**
 * DossierEditTab — Tab de edição do Dossiê Digital do Ativo
 * RC P1 Dossiê Digital v1.0 — Fase 2 (Frontend)
 * 
 * RBAC: Master/Admin/PCM editam. Demais perfis: somente leitura.
 * Pré-visualização em tempo real respeitando visibilidade.
 */
import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import {
  Camera, FileText, Upload, Trash2, Save, Eye, EyeOff, AlertTriangle,
  Shield, Lightbulb, CheckCircle, Info, ChevronDown, ExternalLink,
  X, Image as ImageIcon, File, Globe, Lock, Users, RefreshCw,
  MapPin, Zap, Gauge, Weight, Maximize2, Box, Factory, BookOpen
} from "lucide-react";
import { api, useAuth, BACKEND_URL } from "../lib/api";
import { toast } from "sonner";

// ============== CONSTANTS ==============

const STATUS_OPTIONS = [
  { value: "operando", label: "Operando", color: "#22c55e" },
  { value: "parado", label: "Parado", color: "#ef4444" },
  { value: "em_manutencao", label: "Em Manutencao", color: "#eab308" },
  { value: "indisponivel", label: "Indisponivel", color: "#ef4444" },
  { value: "standby", label: "Standby", color: "#3b82f6" },
  { value: "nao_informado", label: "Nao Informado", color: "#64748b" },
];

const VISIBILITY_OPTIONS = [
  { value: "public", label: "Publico", icon: Globe, desc: "Qualquer pessoa com o QR pode ver" },
  { value: "authenticated", label: "Autenticado", icon: Users, desc: "Somente usuarios logados da empresa" },
  { value: "restricted", label: "Restrito", icon: Lock, desc: "Somente PCM, Admin e Master" },
  { value: "hidden", label: "Oculto", icon: EyeOff, desc: "Nao exibido em nenhuma visualizacao" },
];

const VISIBILITY_BLOCKS = [
  { key: "technical_data", label: "Dados Tecnicos" },
  { key: "history", label: "Historico Resumido" },
  { key: "inspections", label: "Ultimas Inspecoes" },
  { key: "maintenance", label: "Ultimas Manutencoes" },
  { key: "documents", label: "Documentos" },
  { key: "curiosity", label: "Voce Sabia?" },
  { key: "warning", label: "Atencao" },
  { key: "safety", label: "Seguranca" },
  { value: "best_practices", label: "Boas Praticas" },
];

const DOC_TYPES = [
  { value: "manual", label: "Manual" },
  { value: "catalogo", label: "Catalogo" },
  { value: "lista_pecas", label: "Lista de Pecas" },
  { value: "diagrama", label: "Diagrama" },
  { value: "procedimento", label: "Procedimento" },
  { value: "outro", label: "Outro" },
];

const TECH_FIELDS = [
  { key: "fabricante", label: "Fabricante", source: "ativo" },
  { key: "modelo", label: "Modelo", source: "ativo" },
  { key: "numero_serie", label: "Numero de Serie", source: "ativo" },
  { key: "ano", label: "Ano", source: "ativo" },
  { key: "potencia", label: "Potencia", source: "ativo", placeholder: "Ex: 75 kW" },
  { key: "tensao", label: "Tensao", source: "ativo", placeholder: "Ex: 440 V" },
  { key: "corrente", label: "Corrente", source: "dossier", placeholder: "Ex: 95 A" },
  { key: "frequencia", label: "Frequencia", source: "dossier", placeholder: "Ex: 60 Hz" },
  { key: "rotacao", label: "Rotacao", source: "ativo", placeholder: "Ex: 900 rpm" },
  { key: "peso", label: "Peso", source: "ativo", placeholder: "Ex: 18.500 kg" },
  { key: "capacidade", label: "Capacidade", source: "ativo", placeholder: "Ex: 450 t/h" },
  { key: "dimensoes", label: "Dimensoes", source: "ativo", placeholder: "Ex: 4200x1600mm" },
];

// ============== HELPERS ==============

function canEdit(role) {
  return ["master", "admin", "pcm"].includes(role);
}

function isBlockVisible(visibility, block, viewMode) {
  const level = visibility[block] || "hidden";
  if (level === "hidden") return false;
  if (viewMode === "public") return level === "public";
  if (viewMode === "authenticated") return level === "public" || level === "authenticated";
  if (viewMode === "restricted") return level !== "hidden";
  return false;
}

// ============== SECTION COMPONENT ==============

const Section = ({ icon: Icon, title, children, color = "text-slate-500" }) => (
  <div className="space-y-3">
    <div className="flex items-center gap-2">
      {Icon && <Icon size={16} className={color} />}
      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</h4>
    </div>
    {children}
  </div>
);

// ============== TEXTAREA WITH COUNTER ==============

const TextArea = ({ value, onChange, placeholder, maxLen = 5000, rows = 3, readOnly, label }) => (
  <div>
    {label && <label className="text-xs text-slate-500 block mb-1">{label}</label>}
    <textarea
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      maxLength={maxLen}
      rows={rows}
      readOnly={readOnly}
      className={`w-full rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-sm text-slate-200 placeholder-slate-600 resize-y focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 outline-none transition-all ${readOnly ? 'opacity-60 cursor-not-allowed' : ''}`}
    />
    {!readOnly && <p className="text-[10px] text-slate-600 text-right mt-0.5">{(value || "").length}/{maxLen}</p>}
  </div>
);

// ============== VISIBILITY SELECT ==============

const VisibilitySelect = ({ value, onChange, readOnly }) => (
  <select
    value={value}
    onChange={e => onChange(e.target.value)}
    disabled={readOnly}
    className={`text-xs rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-slate-300 focus:border-emerald-500/50 outline-none ${readOnly ? 'opacity-60 cursor-not-allowed' : ''}`}
    data-testid="visibility-select"
  >
    {VISIBILITY_OPTIONS.map(v => (
      <option key={v.value} value={v.value}>{v.label}</option>
    ))}
  </select>
);

// ============== PREVIEW PANEL ==============

const DossierPreview = ({ form, ativo, viewMode, branding }) => {
  const vis = form.visibility || {};
  const statusOpt = STATUS_OPTIONS.find(s => s.value === form.public_status) || STATUS_OPTIONS[5];
  const hasImage = form._previewImageUrl || form.image_url;

  const techEntries = TECH_FIELDS.map(f => {
    const val = f.source === "dossier" ? (form.technical_data || {})[f.key] : (ativo[f.key] || "");
    return val ? { label: f.label, value: val } : null;
  }).filter(Boolean);

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-950 overflow-hidden text-slate-200 text-sm" data-testid="dossier-preview">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-800 px-3 py-2 flex items-center gap-2">
        {branding?.logo_url && (
          <img src={branding.logo_url.startsWith("http") ? branding.logo_url : `${BACKEND_URL}${branding.logo_url}`} alt="" className="h-5 w-5 rounded object-contain bg-white/10" onError={e => e.target.style.display = 'none'} />
        )}
        <span className="text-xs font-medium text-slate-300 truncate">{branding?.nome_empresa || "Empresa"}</span>
      </div>

      {/* Image */}
      {hasImage ? (
        <div className="w-full aspect-[16/9] bg-slate-900 flex items-center justify-center overflow-hidden">
          <img src={form._previewImageUrl || `${BACKEND_URL}${form.image_url}`} alt="" className="w-full h-full object-cover" onError={e => { e.target.style.display = 'none'; }} />
        </div>
      ) : (
        <div className="w-full h-20 bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center">
          <Factory size={28} className="text-slate-700" />
        </div>
      )}

      {/* Tag + Name */}
      <div className="px-3 py-2">
        {ativo.tag && <span className="inline-block text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 tracking-wider mb-1">{ativo.tag}</span>}
        <p className="text-sm font-bold text-white leading-tight">{ativo.nome || "Equipamento"}</p>

        {statusOpt.value !== "nao_informado" && (
          <div className="mt-1.5 inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded border border-slate-700 bg-slate-800">
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: statusOpt.color }} />
            {statusOpt.label}
          </div>
        )}
      </div>

      {/* Location */}
      {(ativo.sector?.nome || form.location?.linha) && (
        <div className="px-3 pb-2">
          <div className="flex items-center gap-1 text-[10px] text-slate-500">
            <MapPin size={10} />
            {[ativo.sector?.nome, form.location?.linha, form.location?.ponto_instalacao].filter(Boolean).join(" / ")}
          </div>
        </div>
      )}

      {/* Description */}
      {form.description && (
        <div className="px-3 pb-2">
          <p className="text-[10px] text-slate-400 leading-relaxed line-clamp-3">{form.description}</p>
        </div>
      )}

      {/* Tech data */}
      {isBlockVisible(vis, "technical_data", viewMode) && techEntries.length > 0 && (
        <div className="px-3 pb-2">
          <p className="text-[9px] text-slate-600 uppercase tracking-wider mb-1">Dados Tecnicos</p>
          <div className="grid grid-cols-2 gap-1">
            {techEntries.slice(0, 6).map(e => (
              <div key={e.label} className="bg-slate-800/50 rounded px-1.5 py-1">
                <p className="text-[8px] text-slate-600">{e.label}</p>
                <p className="text-[10px] text-slate-300 truncate">{e.value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info blocks */}
      {[
        { key: "curiosity", label: "Voce Sabia?", icon: Lightbulb, color: "text-amber-400", bg: "bg-amber-500/5 border-amber-500/20" },
        { key: "warning", label: "Atencao", icon: AlertTriangle, color: "text-orange-400", bg: "bg-orange-500/5 border-orange-500/20" },
        { key: "safety", label: "Seguranca", icon: Shield, color: "text-red-400", bg: "bg-red-500/5 border-red-500/20" },
        { key: "best_practices", label: "Boas Praticas", icon: CheckCircle, color: "text-emerald-400", bg: "bg-emerald-500/5 border-emerald-500/20" },
      ].map(block => {
        if (!isBlockVisible(vis, block.key, viewMode) || !form[block.key]) return null;
        return (
          <div key={block.key} className={`mx-3 mb-2 rounded-lg border px-2 py-1.5 ${block.bg}`}>
            <div className="flex items-center gap-1 mb-0.5">
              <block.icon size={10} className={block.color} />
              <span className={`text-[9px] font-semibold ${block.color}`}>{block.label}</span>
            </div>
            <p className="text-[10px] text-slate-400 leading-relaxed line-clamp-2">{form[block.key]}</p>
          </div>
        );
      })}

      {/* Footer */}
      <div className="border-t border-slate-800 px-3 py-1.5 text-center">
        <p className="text-[8px] text-slate-600">MAINTRIX Enterprise</p>
      </div>
    </div>
  );
};

// ============== DOCUMENT ROW ==============

const DocRow = ({ doc, onToggle, onDelete, readOnly }) => (
  <div className="flex items-center gap-2 p-2 rounded-lg border border-slate-700/50 bg-slate-800/30" data-testid={`doc-${doc.id}`}>
    <File size={16} className={doc.is_published ? "text-emerald-400" : "text-slate-500"} />
    <div className="flex-1 min-w-0">
      <p className="text-xs text-slate-200 truncate">{doc.title}</p>
      <p className="text-[10px] text-slate-500">{doc.doc_type} — {(doc.size_bytes / 1024).toFixed(0)}KB</p>
    </div>
    {!readOnly && (
      <>
        <button
          onClick={() => onToggle(doc)}
          className={`text-[10px] px-2 py-0.5 rounded border transition-all ${doc.is_published ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10' : 'border-slate-600 text-slate-500'}`}
          data-testid={`doc-publish-${doc.id}`}
        >
          {doc.is_published ? "Publicado" : "Privado"}
        </button>
        <button onClick={() => onDelete(doc)} className="text-slate-600 hover:text-red-400 transition-colors" data-testid={`doc-delete-${doc.id}`}>
          <Trash2 size={14} />
        </button>
      </>
    )}
    {readOnly && doc.is_published && (
      <span className="text-[10px] px-2 py-0.5 rounded border border-emerald-500/30 text-emerald-400 bg-emerald-500/10">Publicado</span>
    )}
  </div>
);

// ============== MAIN COMPONENT ==============

const DossierEditTab = ({ ativo, ativoId, onRefresh }) => {
  const { user } = useAuth();
  const readOnly = !canEdit(user?.role);
  const fileInputRef = useRef(null);
  const docInputRef = useRef(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [viewMode, setViewMode] = useState("public");
  const [docUpload, setDocUpload] = useState({ title: "", doc_type: "manual" });
  const [uploading, setUploading] = useState(false);

  // Form state — all optional fields
  const [form, setForm] = useState({
    description: "",
    curiosity: "",
    warning: "",
    safety: "",
    best_practices: "",
    public_status: "nao_informado",
    image_url: "",
    _previewImageUrl: null,
    location: { linha: "", ponto_instalacao: "" },
    technical_data: { corrente: "", frequencia: "" },
    visibility: {
      technical_data: "public", history: "hidden", inspections: "hidden",
      maintenance: "hidden", documents: "hidden", curiosity: "public",
      warning: "public", safety: "public", best_practices: "public",
    },
  });

  // Branding (read-only, from org)
  const [branding, setBranding] = useState(null);

  // Load dossier data
  const fetchDossier = useCallback(async () => {
    try {
      const res = await api.get(`/ativos/${ativoId}/dossier`);
      const d = res.data.public_dossier || {};
      setForm(prev => ({
        ...prev,
        description: d.description || "",
        curiosity: d.curiosity || "",
        warning: d.warning || "",
        safety: d.safety || "",
        best_practices: d.best_practices || "",
        public_status: res.data.public_status || "nao_informado",
        image_url: d.image_url || "",
        _previewImageUrl: null,
        location: { linha: d.location?.linha || "", ponto_instalacao: d.location?.ponto_instalacao || "" },
        technical_data: { corrente: d.technical_data?.corrente || "", frequencia: d.technical_data?.frequencia || "" },
        visibility: d.visibility || prev.visibility,
      }));
      setDocuments(res.data.documents || []);
      setDirty(false);
    } catch {
      toast.error("Erro ao carregar dossie");
    } finally {
      setLoading(false);
    }
  }, [ativoId]);

  useEffect(() => { fetchDossier(); }, [fetchDossier]);

  // Load branding
  useEffect(() => {
    if (!ativo?.organization_id) return;
    api.get("/org/config").then(r => {
      setBranding(r.data?.identidade || null);
    }).catch(() => {});
  }, [ativo?.organization_id]);

  // Update form field
  const updateField = useCallback((field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
    setDirty(true);
  }, []);

  const updateNested = useCallback((parent, field, value) => {
    setForm(prev => ({ ...prev, [parent]: { ...prev[parent], [field]: value } }));
    setDirty(true);
  }, []);

  const updateVisibility = useCallback((block, level) => {
    setForm(prev => ({ ...prev, visibility: { ...prev.visibility, [block]: level } }));
    setDirty(true);
  }, []);

  // Save
  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/ativos/${ativoId}/dossier`, {
        description: form.description,
        curiosity: form.curiosity,
        warning: form.warning,
        safety: form.safety,
        best_practices: form.best_practices,
        public_status: form.public_status,
        location: form.location,
        technical_data: form.technical_data,
        visibility: form.visibility,
      });
      toast.success("Dossie salvo com sucesso!");
      setDirty(false);
      if (onRefresh) onRefresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Erro ao salvar dossie");
    } finally {
      setSaving(false);
    }
  };

  // Photo upload
  const handlePhotoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["jpg", "jpeg", "png", "webp"].includes(ext)) {
      toast.error("Formato nao permitido. Use JPG, PNG ou WebP.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error("Imagem excede 5MB");
      return;
    }
    // Preview imediato
    const previewUrl = URL.createObjectURL(file);
    setForm(prev => ({ ...prev, _previewImageUrl: previewUrl }));

    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await api.post(`/ativos/${ativoId}/dossier/photo`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      setForm(prev => ({ ...prev, image_url: res.data.image_url, _previewImageUrl: null }));
      toast.success("Foto atualizada!");
    } catch (err) {
      setForm(prev => ({ ...prev, _previewImageUrl: null }));
      toast.error(err.response?.data?.detail || "Erro ao enviar foto");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // Photo delete
  const handlePhotoDelete = async () => {
    if (!window.confirm("Remover a foto publica?")) return;
    try {
      await api.delete(`/ativos/${ativoId}/dossier/photo`);
      setForm(prev => ({ ...prev, image_url: "", _previewImageUrl: null }));
      toast.success("Foto removida");
    } catch {
      toast.error("Erro ao remover foto");
    }
  };

  // Document upload
  const handleDocUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!docUpload.title.trim()) {
      toast.error("Informe um titulo para o documento");
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("title", docUpload.title.trim());
      fd.append("doc_type", docUpload.doc_type);
      const res = await api.post(`/ativos/${ativoId}/dossier/documents`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      setDocuments(prev => [res.data, ...prev]);
      setDocUpload({ title: "", doc_type: "manual" });
      toast.success("Documento adicionado!");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Erro ao enviar documento");
    } finally {
      setUploading(false);
      if (docInputRef.current) docInputRef.current.value = "";
    }
  };

  // Document toggle publish
  const handleDocToggle = async (doc) => {
    try {
      const res = await api.put(`/ativos/${ativoId}/dossier/documents/${doc.id}/publish`, { is_published: !doc.is_published });
      setDocuments(prev => prev.map(d => d.id === doc.id ? { ...d, is_published: res.data.is_published } : d));
      toast.success(res.data.is_published ? "Documento publicado" : "Documento despublicado");
    } catch {
      toast.error("Erro ao alterar publicacao");
    }
  };

  // Document delete
  const handleDocDelete = async (doc) => {
    if (!window.confirm(`Remover "${doc.title}"?`)) return;
    try {
      await api.delete(`/ativos/${ativoId}/dossier/documents/${doc.id}`);
      setDocuments(prev => prev.filter(d => d.id !== doc.id));
      toast.success("Documento removido");
    } catch {
      toast.error("Erro ao remover documento");
    }
  };

  // Unsaved changes warning
  useEffect(() => {
    if (!dirty) return;
    const handler = (e) => { e.preventDefault(); e.returnValue = ""; };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);

  const publicUrl = ativo?.public_qr_url || "";

  if (loading) return <div className="flex justify-center py-12"><RefreshCw size={24} className="text-slate-600 animate-spin" /></div>;

  return (
    <div className="space-y-4" data-testid="dossier-edit-tab">
      {/* Top bar */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <BookOpen size={16} className="text-emerald-400" />
          <h3 className="text-sm font-semibold text-slate-200">Dossie Digital</h3>
          {readOnly && <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-500">Somente leitura</span>}
          {dirty && !readOnly && <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400">Nao salvo</span>}
        </div>
        <div className="flex items-center gap-2">
          {publicUrl ? (
            <a href={publicUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-all" data-testid="dossier-view-public">
              <Eye size={14} /> Visualizar Dossie
            </a>
          ) : (
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-600 bg-slate-800/50 border border-slate-800 cursor-not-allowed" title="QR Code publico nao gerado">
              <EyeOff size={14} /> Sem QR publico
            </span>
          )}
          {!readOnly && (
            <button onClick={handleSave} disabled={saving || !dirty} className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed" data-testid="dossier-save-btn">
              {saving ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
              {saving ? "Salvando..." : "Salvar"}
            </button>
          )}
        </div>
      </div>

      {/* Two-column layout: Form + Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* === LEFT: FORM (3/5) === */}
        <div className="lg:col-span-3 space-y-5">

          {/* PHOTO */}
          <div className="glass-card p-4">
            <Section icon={Camera} title="Foto Publica" color="text-blue-400">
              {(form.image_url || form._previewImageUrl) ? (
                <div className="relative group">
                  <img
                    src={form._previewImageUrl || `${BACKEND_URL}${form.image_url}`}
                    alt="Foto do equipamento"
                    className="w-full max-h-48 object-cover rounded-lg border border-slate-700"
                    onError={e => { e.target.src = ""; e.target.alt = "Imagem indisponivel"; }}
                  />
                  {!readOnly && (
                    <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button onClick={() => fileInputRef.current?.click()} className="p-1.5 rounded-lg bg-slate-900/80 text-slate-300 hover:text-white" data-testid="dossier-photo-change"><Camera size={14} /></button>
                      <button onClick={handlePhotoDelete} className="p-1.5 rounded-lg bg-slate-900/80 text-red-400 hover:text-red-300" data-testid="dossier-photo-delete"><Trash2 size={14} /></button>
                    </div>
                  )}
                </div>
              ) : (
                !readOnly && (
                  <button onClick={() => fileInputRef.current?.click()} className="w-full py-6 rounded-lg border-2 border-dashed border-slate-700 hover:border-emerald-500/40 text-slate-500 hover:text-slate-400 transition-all flex flex-col items-center gap-2" data-testid="dossier-photo-upload" disabled={uploading}>
                    {uploading ? <RefreshCw size={20} className="animate-spin" /> : <Upload size={20} />}
                    <span className="text-xs">{uploading ? "Enviando..." : "Selecionar Foto"}</span>
                    <span className="text-[10px] text-slate-600">JPG, PNG ou WebP (max 5MB)</span>
                  </button>
                )
              )}
              <input ref={fileInputRef} type="file" accept=".jpg,.jpeg,.png,.webp" className="hidden" onChange={handlePhotoUpload} />
            </Section>
          </div>

          {/* STATUS + LOCATION */}
          <div className="glass-card p-4 space-y-4">
            <Section icon={Zap} title="Status e Localizacao" color="text-emerald-400">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-500 block mb-1">Status Publico</label>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: (STATUS_OPTIONS.find(s => s.value === form.public_status) || {}).color || "#64748b" }} />
                    <select
                      value={form.public_status}
                      onChange={e => updateField("public_status", e.target.value)}
                      disabled={readOnly}
                      className={`flex-1 text-sm rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-slate-200 outline-none ${readOnly ? 'opacity-60 cursor-not-allowed' : ''}`}
                      data-testid="dossier-status"
                    >
                      {STATUS_OPTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">Linha</label>
                  <input value={form.location.linha} onChange={e => updateNested("location", "linha", e.target.value)} readOnly={readOnly} placeholder="Ex: Linha 1" className={`w-full text-sm rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-slate-200 placeholder-slate-600 outline-none ${readOnly ? 'opacity-60 cursor-not-allowed' : ''}`} data-testid="dossier-linha" />
                </div>
                <div className="sm:col-span-2">
                  <label className="text-xs text-slate-500 block mb-1">Ponto de Instalacao</label>
                  <input value={form.location.ponto_instalacao} onChange={e => updateNested("location", "ponto_instalacao", e.target.value)} readOnly={readOnly} placeholder="Ex: Entrada Britagem" className={`w-full text-sm rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-slate-200 placeholder-slate-600 outline-none ${readOnly ? 'opacity-60 cursor-not-allowed' : ''}`} data-testid="dossier-ponto" />
                </div>
              </div>
            </Section>
          </div>

          {/* TEXT BLOCKS */}
          <div className="glass-card p-4 space-y-4">
            <Section icon={FileText} title="Conteudo do Dossie" color="text-purple-400">
              <TextArea value={form.description} onChange={v => updateField("description", v)} placeholder="Descricao publica do equipamento..." rows={3} readOnly={readOnly} label="Descricao" />
              <TextArea value={form.curiosity} onChange={v => updateField("curiosity", v)} placeholder="Curiosidade sobre o equipamento... (ex: capacidade maxima, historico)" rows={2} readOnly={readOnly} label="Voce Sabia?" />
              <TextArea value={form.warning} onChange={v => updateField("warning", v)} placeholder="Alertas de operacao... (ex: limites, cuidados)" rows={2} readOnly={readOnly} label="Atencao" />
              <TextArea value={form.safety} onChange={v => updateField("safety", v)} placeholder="Instrucoes de seguranca... (ex: bloqueio, etiquetagem)" rows={2} readOnly={readOnly} label="Seguranca" />
              <TextArea value={form.best_practices} onChange={v => updateField("best_practices", v)} placeholder="Boas praticas de operacao e manutencao..." rows={2} readOnly={readOnly} label="Boas Praticas" />
            </Section>
          </div>

          {/* TECHNICAL DATA (extra) */}
          <div className="glass-card p-4">
            <Section icon={Gauge} title="Dados Tecnicos Adicionais" color="text-cyan-400">
              <p className="text-[10px] text-slate-600 -mt-1 mb-2">Campos como fabricante, modelo e tensao vem do cadastro do ativo. Abaixo, campos extras do dossie.</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-500 block mb-1">Corrente</label>
                  <input value={form.technical_data.corrente} onChange={e => updateNested("technical_data", "corrente", e.target.value)} readOnly={readOnly} placeholder="Ex: 95 A" className={`w-full text-sm rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-slate-200 placeholder-slate-600 outline-none ${readOnly ? 'opacity-60 cursor-not-allowed' : ''}`} data-testid="dossier-corrente" />
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">Frequencia</label>
                  <input value={form.technical_data.frequencia} onChange={e => updateNested("technical_data", "frequencia", e.target.value)} readOnly={readOnly} placeholder="Ex: 60 Hz" className={`w-full text-sm rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-slate-200 placeholder-slate-600 outline-none ${readOnly ? 'opacity-60 cursor-not-allowed' : ''}`} data-testid="dossier-frequencia" />
                </div>
              </div>
            </Section>
          </div>

          {/* VISIBILITY CONTROLS */}
          <div className="glass-card p-4">
            <Section icon={Eye} title="Nivel de Divulgacao" color="text-amber-400">
              <p className="text-[10px] text-slate-600 -mt-1 mb-2">Controle quais blocos aparecem em cada nivel de acesso.</p>
              <div className="space-y-2">
                {[
                  { key: "technical_data", label: "Dados Tecnicos" },
                  { key: "history", label: "Historico Resumido" },
                  { key: "inspections", label: "Ultimas Inspecoes" },
                  { key: "maintenance", label: "Ultimas Manutencoes" },
                  { key: "documents", label: "Documentos" },
                  { key: "curiosity", label: "Voce Sabia?" },
                  { key: "warning", label: "Atencao" },
                  { key: "safety", label: "Seguranca" },
                  { key: "best_practices", label: "Boas Praticas" },
                ].map(block => (
                  <div key={block.key} className="flex items-center justify-between py-1.5 border-b border-slate-800/50 last:border-0">
                    <span className="text-xs text-slate-300">{block.label}</span>
                    <VisibilitySelect value={form.visibility[block.key] || "hidden"} onChange={v => updateVisibility(block.key, v)} readOnly={readOnly} />
                  </div>
                ))}
              </div>
              {/* Legend */}
              <div className="mt-3 grid grid-cols-2 gap-1">
                {VISIBILITY_OPTIONS.map(v => (
                  <div key={v.value} className="flex items-center gap-1.5 text-[10px] text-slate-600">
                    <v.icon size={10} /> <span className="font-medium">{v.label}</span>: {v.desc}
                  </div>
                ))}
              </div>
            </Section>
          </div>

          {/* DOCUMENTS */}
          <div className="glass-card p-4">
            <Section icon={FileText} title="Documentos" color="text-indigo-400">
              {documents.length > 0 && (
                <div className="space-y-1.5 mb-3">
                  {documents.map(doc => (
                    <DocRow key={doc.id} doc={doc} onToggle={handleDocToggle} onDelete={handleDocDelete} readOnly={readOnly} />
                  ))}
                </div>
              )}
              {!readOnly && (
                <div className="space-y-2 p-3 rounded-lg border border-dashed border-slate-700 bg-slate-800/20">
                  <div className="grid grid-cols-2 gap-2">
                    <input value={docUpload.title} onChange={e => setDocUpload(p => ({ ...p, title: e.target.value }))} placeholder="Titulo do documento" className="text-sm rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-slate-200 placeholder-slate-600 outline-none" data-testid="doc-title-input" />
                    <select value={docUpload.doc_type} onChange={e => setDocUpload(p => ({ ...p, doc_type: e.target.value }))} className="text-sm rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-slate-200 outline-none" data-testid="doc-type-select">
                      {DOC_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                    </select>
                  </div>
                  <button onClick={() => { if (!docUpload.title.trim()) { toast.error("Informe um titulo"); return; } docInputRef.current?.click(); }} disabled={uploading} className="w-full py-2 rounded-lg border border-dashed border-slate-600 hover:border-emerald-500/40 text-slate-500 hover:text-slate-400 text-xs transition-all flex items-center justify-center gap-2" data-testid="doc-upload-btn">
                    {uploading ? <RefreshCw size={14} className="animate-spin" /> : <Upload size={14} />}
                    {uploading ? "Enviando..." : "Adicionar Documento"}
                  </button>
                  <input ref={docInputRef} type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" className="hidden" onChange={handleDocUpload} />
                  <p className="text-[10px] text-slate-600">Documentos sao adicionados como privados. Publique individualmente.</p>
                </div>
              )}
              {documents.length === 0 && readOnly && (
                <p className="text-xs text-slate-600 text-center py-4">Nenhum documento no dossie</p>
              )}
            </Section>
          </div>
        </div>

        {/* === RIGHT: PREVIEW (2/5) === */}
        <div className="lg:col-span-2 space-y-2">
          <div className="sticky top-4">
            {/* View mode selector */}
            <div className="flex items-center gap-1 mb-2 p-1 rounded-lg bg-slate-800/50 border border-slate-700/50">
              {[
                { value: "public", label: "Publico", icon: Globe },
                { value: "authenticated", label: "Autenticado", icon: Users },
                { value: "restricted", label: "Restrito", icon: Lock },
              ].map(m => (
                <button key={m.value} onClick={() => setViewMode(m.value)}
                  className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded-md text-[10px] font-medium transition-all ${viewMode === m.value ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'text-slate-500 hover:text-slate-400'}`}
                  data-testid={`preview-mode-${m.value}`}
                >
                  <m.icon size={10} /> {m.label}
                </button>
              ))}
            </div>
            <p className="text-[9px] text-slate-600 mb-2 text-center">
              {viewMode === "public" && "Como qualquer pessoa com o QR vera"}
              {viewMode === "authenticated" && "Como usuario logado da empresa vera"}
              {viewMode === "restricted" && "Como PCM/Admin vera"}
            </p>
            <DossierPreview form={form} ativo={ativo || {}} viewMode={viewMode} branding={branding} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DossierEditTab;
