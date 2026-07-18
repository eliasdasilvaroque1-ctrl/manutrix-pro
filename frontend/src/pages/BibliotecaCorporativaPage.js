import { useState, useEffect, useCallback } from "react";
import { Plus, Save, Trash2, Search, Filter, History, Eye, Shield, FileText, ChevronLeft, ChevronRight, RotateCcw, Archive, Send, Edit } from "lucide-react";
import { api, useAuth } from "@/lib/api";
import { PageContainer, PageHeader, Loading, EmptyState, Modal, FormInput } from "@/components/shared";
import { toast } from "sonner";

const DOC_TYPES = [
  { value: "procedimento_operacional", label: "Procedimento Operacional" },
  { value: "procedimento_manutencao", label: "Procedimento Manutenção" },
  { value: "instrucao_trabalho", label: "Instrução de Trabalho" },
  { value: "seguranca", label: "Segurança" },
  { value: "apr", label: "APR" },
  { value: "norma_interna", label: "Norma Interna" },
  { value: "manual", label: "Manual" },
  { value: "checklist", label: "Checklist" },
  { value: "formulario", label: "Formulário" },
  { value: "documento_tecnico", label: "Documento Técnico" },
  { value: "outro", label: "Outro" },
];

const STATUS_MAP = {
  rascunho: { label: "Rascunho", color: "bg-amber-500/20 text-amber-400" },
  em_revisao: { label: "Em Revisão", color: "bg-blue-500/20 text-blue-400" },
  aprovado: { label: "Aprovado", color: "bg-cyan-500/20 text-cyan-400" },
  publicado: { label: "Publicado", color: "bg-emerald-500/20 text-emerald-400" },
  obsoleto: { label: "Obsoleto", color: "bg-red-500/20 text-red-400" },
  arquivado: { label: "Arquivado", color: "bg-slate-500/20 text-slate-400" },
};

const DISCIPLINES = ['mecanica', 'eletrica', 'instrumentacao', 'civil', 'producao', 'lubrificacao', 'seguranca', 'geral'];

// ===== MAIN COMPONENT =====
const BibliotecaCorporativaPage = () => {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({ document_type: '', discipline: '', status: '', safety_document: '' });
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [viewItem, setViewItem] = useState(null);
  const [versionItem, setVersionItem] = useState(null);
  const canEdit = ['master', 'admin', 'pcm'].includes(user?.role);

  const fetchDocs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, per_page: 20 });
      if (search) params.set('search', search);
      if (filters.document_type) params.set('document_type', filters.document_type);
      if (filters.discipline) params.set('discipline', filters.discipline);
      if (filters.status) params.set('status', filters.status);
      if (filters.safety_document) params.set('safety_document', filters.safety_document);
      const r = await api.get(`/documentos-corporativos?${params}`);
      setItems(r.data.items);
      setTotal(r.data.total);
      setTotalPages(r.data.total_pages);
    } catch { toast.error('Erro ao carregar documentos'); }
    setLoading(false);
  }, [page, search, filters]);

  useEffect(() => { fetchDocs(); }, [fetchDocs]);

  const handleDelete = async (id, title) => {
    if (!window.confirm(`Excluir "${title}"?\nEsta ação pode ser revertida.`)) return;
    try { await api.delete(`/documentos-corporativos/${id}`); toast.success('Documento excluído'); fetchDocs(); } catch (e) { toast.error(e.response?.data?.detail || 'Erro'); }
  };

  const handleStatusChange = async (id, newStatus, motivo = '') => {
    try {
      await api.patch(`/documentos-corporativos/${id}/status`, { status: newStatus, motivo });
      toast.success(`Status alterado para ${STATUS_MAP[newStatus]?.label || newStatus}`);
      fetchDocs();
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro'); }
  };

  return (
    <PageContainer>
      <PageHeader title="Biblioteca Corporativa" subtitle={`${total} documentos`} testId="biblioteca-title" />

      {/* Search & Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} placeholder="Pesquisar por título, código ou tag..."
            className="input-industrial w-full pl-9 pr-3" data-testid="search-docs" />
        </div>
        <select value={filters.document_type} onChange={e => { setFilters(f => ({ ...f, document_type: e.target.value })); setPage(1); }} className="input-industrial px-3 w-48" data-testid="filter-type">
          <option value="">Todos os tipos</option>
          {DOC_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
        <select value={filters.discipline} onChange={e => { setFilters(f => ({ ...f, discipline: e.target.value })); setPage(1); }} className="input-industrial px-3 w-40">
          <option value="">Disciplina</option>
          {DISCIPLINES.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
        </select>
        <select value={filters.status} onChange={e => { setFilters(f => ({ ...f, status: e.target.value })); setPage(1); }} className="input-industrial px-3 w-36">
          <option value="">Status</option>
          {Object.entries(STATUS_MAP).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
        <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
          <input type="checkbox" checked={filters.safety_document === 'true'} onChange={e => { setFilters(f => ({ ...f, safety_document: e.target.checked ? 'true' : '' })); setPage(1); }} />
          <Shield size={14} /> Segurança
        </label>
        {canEdit && <button onClick={() => { setEditItem(null); setShowForm(true); }} className="btn-primary flex items-center gap-2" data-testid="new-doc-btn"><Plus size={16} /> Novo Documento</button>}
      </div>

      {/* List */}
      {loading ? <Loading /> : items.length === 0 ? <EmptyState title="Nenhum documento encontrado" /> : (
        <div className="space-y-2">
          {items.map(doc => {
            const st = STATUS_MAP[doc.status] || STATUS_MAP.rascunho;
            const typeLabel = DOC_TYPES.find(t => t.value === doc.document_type)?.label || doc.document_type;
            return (
              <div key={doc.id} className="glass-card p-4 flex items-start justify-between gap-3 hover:border-slate-600 transition-all" data-testid={`doc-${doc.id}`}>
                <div className="flex-1 min-w-0 cursor-pointer" onClick={() => setViewItem(doc)}>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-primary truncate">{doc.title}</span>
                    {doc.code && <span className="text-xs bg-slate-700 px-2 py-0.5 rounded shrink-0">{doc.code}</span>}
                    <span className={`text-xs px-2 py-0.5 rounded shrink-0 ${st.color}`}>{st.label}</span>
                    <span className="text-xs text-brand bg-brand/10 px-2 py-0.5 rounded shrink-0">v{doc.version || 1}</span>
                    {doc.safety_document && <Shield size={14} className="text-amber-400 shrink-0" />}
                  </div>
                  <p className="text-xs text-slate-500 mt-1 truncate">{typeLabel} | {doc.discipline || '-'} | {doc.category || '-'} | {(doc.tags || []).join(', ')}</p>
                </div>
                <div className="flex gap-1.5 items-center shrink-0">
                  <button onClick={() => setVersionItem(doc)} className="p-1 text-slate-500 hover:text-amber-400" title="Versões"><History size={14} /></button>
                  {canEdit && doc.status === 'rascunho' && <button onClick={() => handleStatusChange(doc.id, 'publicado', 'Publicação direta')} className="p-1 text-slate-500 hover:text-emerald-400" title="Publicar"><Send size={14} /></button>}
                  {canEdit && doc.status === 'publicado' && <button onClick={() => handleStatusChange(doc.id, 'arquivado', 'Arquivamento')} className="p-1 text-slate-500 hover:text-blue-400" title="Arquivar"><Archive size={14} /></button>}
                  {canEdit && <button onClick={() => { setEditItem(doc); setShowForm(true); }} className="p-1 text-slate-500 hover:text-blue-400" title="Editar"><Edit size={14} /></button>}
                  {canEdit && <button onClick={() => handleDelete(doc.id, doc.title)} className="p-1 text-slate-500 hover:text-red-400" title="Excluir"><Trash2 size={14} /></button>}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-4 mt-4">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} className="p-2 text-slate-400 hover:text-white disabled:opacity-30"><ChevronLeft size={18} /></button>
          <span className="text-sm text-slate-400">Página {page} de {totalPages}</span>
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="p-2 text-slate-400 hover:text-white disabled:opacity-30"><ChevronRight size={18} /></button>
        </div>
      )}

      {/* Modals */}
      {showForm && <DocForm item={editItem} onClose={() => setShowForm(false)} onSuccess={() => { setShowForm(false); fetchDocs(); }} />}
      {viewItem && <DocViewer doc={viewItem} onClose={() => setViewItem(null)} onEdit={canEdit ? () => { setEditItem(viewItem); setViewItem(null); setShowForm(true); } : null} />}
      {versionItem && <VersionModal docId={versionItem.id} docTitle={versionItem.title} onClose={() => setVersionItem(null)} onRestore={fetchDocs} canRestore={canEdit} />}
    </PageContainer>
  );
};

// ===== DOCUMENT FORM =====
const DocForm = ({ item, onClose, onSuccess }) => {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(item ? {
    title: item.title, code: item.code || '', description: item.description || '',
    document_type: item.document_type, category: item.category || '', department: item.department || '',
    discipline: item.discipline || '', applicable_asset_types: item.applicable_asset_types || [],
    applicable_work_order_types: item.applicable_work_order_types || [], applicable_areas: item.applicable_areas || [],
    tags: item.tags || [], status: item.status || 'rascunho', content: item.content || '',
    file_url: item.file_url || '', file_name: item.file_name || '', safety_document: item.safety_document || false,
    requires_acknowledgement: item.requires_acknowledgement || false,
    effective_date: item.effective_date || '', expiration_date: item.expiration_date || '',
    revision: item.revision || '', motivo_alteracao: '',
  } : {
    title: '', code: '', description: '', document_type: 'procedimento_operacional', category: '',
    department: '', discipline: '', applicable_asset_types: [], applicable_work_order_types: [],
    applicable_areas: [], tags: [], status: 'rascunho', content: '', file_url: '', file_name: '',
    safety_document: false, requires_acknowledgement: false, effective_date: '', expiration_date: '',
    revision: '', motivo_alteracao: '',
  });
  const [saving, setSaving] = useState(false);

  const sections = ['Identificação', 'Classificação', 'Aplicabilidade', 'Conteúdo', 'Segurança', 'Vigência', 'Versionamento'];

  const handleSave = async () => {
    if (!form.title.trim()) { toast.error('Título obrigatório'); return; }
    setSaving(true);
    try {
      if (item?.id) await api.put(`/documentos-corporativos/${item.id}`, form);
      else await api.post('/documentos-corporativos', form);
      toast.success(item ? 'Documento atualizado' : 'Documento criado');
      onSuccess();
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro ao salvar'); }
    setSaving(false);
  };

  const setF = (k, v) => setForm(prev => ({ ...prev, [k]: v }));

  return (
    <Modal isOpen onClose={onClose} title={item ? `Editar: ${item.title}` : 'Novo Documento Corporativo'} size="xl">
      <div className="max-h-[70vh] overflow-y-auto">
        {/* Step navigation */}
        <div className="flex gap-1 mb-4 overflow-x-auto pb-1">
          {sections.map((s, i) => (
            <button key={i} onClick={() => setStep(i)} className={`text-xs px-3 py-1.5 rounded whitespace-nowrap ${step === i ? 'bg-brand text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}>{s}</button>
          ))}
        </div>

        {/* Step 0: Identificação */}
        {step === 0 && <div className="space-y-3">
          <FormInput label="Título *"><input value={form.title} onChange={e => setF('title', e.target.value)} className="input-industrial w-full px-3" data-testid="doc-title" /></FormInput>
          <div className="grid grid-cols-2 gap-3">
            <FormInput label="Código"><input value={form.code} onChange={e => setF('code', e.target.value)} className="input-industrial w-full px-3" placeholder="Ex: POP-001" data-testid="doc-code" /></FormInput>
            <FormInput label="Revisão"><input value={form.revision} onChange={e => setF('revision', e.target.value)} className="input-industrial w-full px-3" placeholder="Ex: Rev. 02" /></FormInput>
          </div>
          <FormInput label="Descrição"><textarea value={form.description} onChange={e => setF('description', e.target.value)} className="input-industrial w-full px-3 h-16" /></FormInput>
        </div>}

        {/* Step 1: Classificação */}
        {step === 1 && <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <FormInput label="Tipo de documento *">
              <select value={form.document_type} onChange={e => setF('document_type', e.target.value)} className="input-industrial w-full px-3" data-testid="doc-type-select">
                {DOC_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </FormInput>
            <FormInput label="Disciplina">
              <select value={form.discipline} onChange={e => setF('discipline', e.target.value)} className="input-industrial w-full px-3">
                <option value="">Selecionar</option>
                {DISCIPLINES.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
              </select>
            </FormInput>
            <FormInput label="Categoria"><input value={form.category} onChange={e => setF('category', e.target.value)} className="input-industrial w-full px-3" placeholder="Ex: Manutenção Mecânica" /></FormInput>
            <FormInput label="Departamento"><input value={form.department} onChange={e => setF('department', e.target.value)} className="input-industrial w-full px-3" /></FormInput>
          </div>
          <FormInput label="Tags (separar por vírgula)">
            <input value={(form.tags || []).join(', ')} onChange={e => setF('tags', e.target.value.split(',').map(s => s.trim()).filter(Boolean))} className="input-industrial w-full px-3" placeholder="bomba, rolamento, mecânica" />
          </FormInput>
        </div>}

        {/* Step 2: Aplicabilidade */}
        {step === 2 && <div className="space-y-3">
          <FormInput label="Tipos de ativo aplicáveis (separar por vírgula)">
            <input value={(form.applicable_asset_types || []).join(', ')} onChange={e => setF('applicable_asset_types', e.target.value.split(',').map(s => s.trim()).filter(Boolean))} className="input-industrial w-full px-3" placeholder="Bomba, Motor, Compressor" />
          </FormInput>
          <FormInput label="Tipos de OS aplicáveis (separar por vírgula)">
            <input value={(form.applicable_work_order_types || []).join(', ')} onChange={e => setF('applicable_work_order_types', e.target.value.split(',').map(s => s.trim()).filter(Boolean))} className="input-industrial w-full px-3" placeholder="corretiva, preventiva" />
          </FormInput>
          <FormInput label="Áreas aplicáveis (separar por vírgula)">
            <input value={(form.applicable_areas || []).join(', ')} onChange={e => setF('applicable_areas', e.target.value.split(',').map(s => s.trim()).filter(Boolean))} className="input-industrial w-full px-3" placeholder="Utilidades, Produção" />
          </FormInput>
        </div>}

        {/* Step 3: Conteúdo */}
        {step === 3 && <div className="space-y-3">
          <FormInput label="Conteúdo do documento">
            <textarea value={form.content} onChange={e => setF('content', e.target.value)} className="input-industrial w-full px-3 h-40 font-mono text-xs" placeholder="Conteúdo do procedimento, instrução ou norma..." />
          </FormInput>
          <p className="text-xs text-slate-600">Upload de arquivos será implementado na próxima etapa.</p>
        </div>}

        {/* Step 4: Segurança */}
        {step === 4 && <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
            <input type="checkbox" checked={form.safety_document} onChange={e => setF('safety_document', e.target.checked)} className="w-4 h-4" />
            <Shield size={16} className="text-amber-400" /> Documento de segurança
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
            <input type="checkbox" checked={form.requires_acknowledgement} onChange={e => setF('requires_acknowledgement', e.target.checked)} className="w-4 h-4" />
            Requer aceite/reconhecimento
          </label>
        </div>}

        {/* Step 5: Vigência */}
        {step === 5 && <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <FormInput label="Data de vigência"><input type="date" value={form.effective_date} onChange={e => setF('effective_date', e.target.value)} className="input-industrial w-full px-3" /></FormInput>
            <FormInput label="Data de vencimento"><input type="date" value={form.expiration_date} onChange={e => setF('expiration_date', e.target.value)} className="input-industrial w-full px-3" /></FormInput>
          </div>
          <FormInput label="Status">
            <select value={form.status} onChange={e => setF('status', e.target.value)} className="input-industrial w-full px-3">
              {Object.entries(STATUS_MAP).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
          </FormInput>
        </div>}

        {/* Step 6: Versionamento */}
        {step === 6 && <div className="space-y-3">
          {item?.id && <FormInput label="Motivo da alteração">
            <input value={form.motivo_alteracao} onChange={e => setF('motivo_alteracao', e.target.value)} className="input-industrial w-full px-3" placeholder="Descreva o motivo desta revisão" data-testid="doc-motivo" />
          </FormInput>}
          <p className="text-xs text-slate-500">Versão atual: v{item?.version || 1}. Edições em documentos publicados criam nova versão automaticamente.</p>
        </div>}
      </div>

      <div className="flex gap-3 mt-4 pt-3 border-t border-slate-800">
        {step > 0 && <button onClick={() => setStep(s => s - 1)} className="btn-secondary">Anterior</button>}
        <div className="flex-1" />
        {step < sections.length - 1 && <button onClick={() => setStep(s => s + 1)} className="btn-secondary">Próximo</button>}
        <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2" data-testid="save-doc-btn">
          <Save size={16} /> {saving ? 'Salvando...' : 'Salvar'}
        </button>
      </div>
    </Modal>
  );
};

// ===== DOCUMENT VIEWER =====
const DocViewer = ({ doc, onClose, onEdit }) => {
  const st = STATUS_MAP[doc.status] || STATUS_MAP.rascunho;
  const typeLabel = DOC_TYPES.find(t => t.value === doc.document_type)?.label || doc.document_type;
  return (
    <Modal isOpen onClose={onClose} title={doc.title} size="xl">
      <div className="max-h-[70vh] overflow-y-auto space-y-4">
        <div className="flex flex-wrap gap-2">
          {doc.code && <span className="text-xs bg-slate-700 px-2 py-1 rounded">{doc.code}</span>}
          <span className={`text-xs px-2 py-1 rounded ${st.color}`}>{st.label}</span>
          <span className="text-xs text-brand bg-brand/10 px-2 py-1 rounded">v{doc.version}</span>
          {doc.safety_document && <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-1 rounded flex items-center gap-1"><Shield size={12} /> Segurança</span>}
        </div>
        {doc.description && <div><label className="text-xs text-slate-500">Descrição</label><p className="text-sm text-slate-300">{doc.description}</p></div>}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div><span className="text-slate-500">Tipo:</span> <span className="text-slate-300">{typeLabel}</span></div>
          <div><span className="text-slate-500">Disciplina:</span> <span className="text-slate-300">{doc.discipline || '-'}</span></div>
          <div><span className="text-slate-500">Categoria:</span> <span className="text-slate-300">{doc.category || '-'}</span></div>
          <div><span className="text-slate-500">Departamento:</span> <span className="text-slate-300">{doc.department || '-'}</span></div>
          {doc.effective_date && <div><span className="text-slate-500">Vigência:</span> <span className="text-slate-300">{doc.effective_date}</span></div>}
          {doc.expiration_date && <div><span className="text-slate-500">Vencimento:</span> <span className="text-slate-300">{doc.expiration_date}</span></div>}
        </div>
        {(doc.tags || []).length > 0 && <div className="flex flex-wrap gap-1">{doc.tags.map(t => <span key={t} className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded">{t}</span>)}</div>}
        {doc.content && <div className="bg-slate-900/60 rounded-lg p-4"><pre className="text-sm text-slate-300 whitespace-pre-wrap font-mono">{doc.content}</pre></div>}
      </div>
      <div className="flex gap-3 mt-4">
        <button onClick={onClose} className="btn-secondary flex-1">Fechar</button>
        {onEdit && <button onClick={onEdit} className="btn-primary flex items-center gap-2"><Edit size={16} /> Editar</button>}
      </div>
    </Modal>
  );
};

// ===== VERSION HISTORY MODAL =====
const VersionModal = ({ docId, docTitle, onClose, onRestore, canRestore }) => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    api.get(`/documentos-corporativos/${docId}/versoes`).then(r => setVersions(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, [docId]);

  const handleRestore = async (versao) => {
    const motivo = window.prompt('Motivo da restauração:') || '';
    try {
      await api.post(`/documentos-corporativos/${docId}/restaurar-versao/${versao}?motivo=${encodeURIComponent(motivo)}`);
      toast.success(`Restaurado para v${versao}`);
      onRestore();
      onClose();
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro'); }
  };

  return (
    <Modal isOpen onClose={onClose} title={`Versões — ${docTitle}`} size="lg">
      <div className="max-h-[60vh] overflow-y-auto">
        {loading ? <Loading /> : versions.length === 0 ? <p className="text-sm text-slate-500 py-4">Nenhuma versão</p> : (
          <div className="space-y-2">
            {versions.map((v, i) => {
              const s = v.snapshot || {};
              return (
                <div key={v.id} className={`rounded-lg border p-3 ${i === 0 ? 'border-brand/30 bg-brand/5' : 'border-slate-700 bg-slate-800/50'}`}>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${i === 0 ? 'bg-brand text-white' : 'bg-slate-700'}`}>v{v.versao}</span>
                      <span className="text-sm text-primary">{s.title || '-'}</span>
                      {i === 0 && <span className="text-xs text-emerald-400">(atual)</span>}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500">{(v.created_at || '').slice(0, 16).replace('T', ' ')}</span>
                      {canRestore && i > 0 && <button onClick={() => handleRestore(v.versao)} className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1"><RotateCcw size={12} /> Restaurar</button>}
                      <button onClick={() => setExpanded(expanded === v.versao ? null : v.versao)} className="text-xs text-slate-400">{expanded === v.versao ? 'Ocultar' : 'Detalhes'}</button>
                    </div>
                  </div>
                  {v.motivo && <p className="text-xs text-slate-400 mt-1 italic">{v.motivo}</p>}
                  {expanded === v.versao && <div className="mt-2 p-2 bg-slate-900/60 rounded text-xs text-slate-300 space-y-1">
                    {s.code && <p><strong>Código:</strong> {s.code}</p>}
                    {s.status && <p><strong>Status:</strong> {s.status}</p>}
                    {s.description && <p><strong>Descrição:</strong> {s.description?.slice(0, 200)}</p>}
                  </div>}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Modal>
  );
};

export default BibliotecaCorporativaPage;
