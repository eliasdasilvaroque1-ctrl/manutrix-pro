import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth, api } from "../lib/api";
import { normalizeError } from "../lib/constants";
import { downloadCorporateDocumentFile } from "../lib/corporateDocuments";
import { emptyProcedureTotals, normalizeProcedureResponse, searchTextFromChange } from "../lib/procedureCatalog";
import { toast } from "sonner";
import { Plus, Edit, Trash2, Save, X, ChevronDown, ChevronUp, FileText, Clock, Archive, Shield, Download, Library } from "lucide-react";
import { PageContainer, PageHeader, SearchInput, EmptyState, Loading, Modal, ConfirmDialog } from "../components/shared";

const STATUS_LABELS = {
  rascunho: 'Rascunho',
  em_revisao: 'Em revisão',
  aprovado: 'Aprovado',
  publicado: 'Publicado',
  inativo: 'Inativo',
  arquivado: 'Arquivado',
  obsoleto: 'Obsoleto',
};
const STATUS_COLORS = {
  rascunho: 'bg-amber-500/20 text-amber-400',
  em_revisao: 'bg-blue-500/20 text-blue-400',
  aprovado: 'bg-emerald-500/20 text-emerald-400',
  publicado: 'bg-emerald-500/20 text-emerald-400',
  inativo: 'bg-slate-500/20 text-slate-400',
  arquivado: 'bg-slate-500/20 text-slate-400',
  obsoleto: 'bg-red-500/20 text-red-400',
};
const TYPE_LABELS = {
  procedimento_operacional: 'Procedimento operacional',
  procedimento_manutencao: 'Procedimento de manutenção',
  procedimento_legado: 'Procedimento legado',
};

const formatDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('pt-BR');
};

const ProcedimentosPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [procs, setProcs] = useState([]);
  const [totals, setTotals] = useState(emptyProcedureTotals);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [archiving, setArchiving] = useState(null);
  const [expanded, setExpanded] = useState(null);

  const canWrite = ['admin', 'pcm', 'master'].includes(user?.role);

  const fetchProcs = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      params.set('include_meta', 'true');
      if (search) params.set('search', search);
      if (statusFilter) params.set('status', statusFilter);
      const res = await api.get(`/procedimentos?${params}`);
      const catalog = normalizeProcedureResponse(res.data);
      setProcs(catalog.items);
      setTotals(catalog.totals);
    } catch (e) { toast.error(normalizeError(e)); }
    finally { setLoading(false); }
  }, [search, statusFilter]);

  useEffect(() => { fetchProcs(); }, [fetchProcs]);

  const handleDelete = async () => {
    try {
      const endpoint = deleting.source === 'biblioteca_corporativa'
        ? `/documentos-corporativos/${deleting.id}`
        : `/procedimentos/${deleting.id}`;
      await api.delete(endpoint);
      toast.success('Procedimento excluído');
      setDeleting(null);
      fetchProcs();
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const handleArchive = async () => {
    try {
      if (archiving.source === 'biblioteca_corporativa') {
        await api.patch(`/documentos-corporativos/${archiving.id}/status`, {
          status: 'arquivado',
          motivo: 'Arquivamento pela visão de Procedimentos',
        });
      } else {
        await api.patch(`/procedimentos/${archiving.id}/status`, { status: 'inativo' });
      }
      toast.success('Procedimento arquivado');
      setArchiving(null);
      fetchProcs();
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const handleDownload = async (proc) => {
    try {
      await downloadCorporateDocumentFile(proc.file_url, proc.file_name);
    } catch (e) {
      toast.error(e?.message || normalizeError(e));
    }
  };

  if (loading) return <Loading rows={4} />;

  return (
    <PageContainer>
      <PageHeader
        title="Procedimentos Operacionais"
        subtitle={`${totals.filtered} exibido(s) • ${totals.published} publicado(s)/ativo(s) • ${totals.archived} arquivado(s)/inativo(s)`}
      >
        {canWrite && <button onClick={() => navigate('/biblioteca?new=procedure')} className="btn-primary flex items-center gap-2" data-testid="proc-create-btn"><Plus size={16} /> Novo Procedimento</button>}
      </PageHeader>

      <div className="flex flex-wrap gap-3 mb-4" data-testid="proc-filters">
        <SearchInput value={search} onChange={event => setSearch(searchTextFromChange(event))} placeholder="Buscar título, código, tipo, disciplina, área ou tag..." />
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="input-field w-auto text-sm" data-testid="proc-status-filter">
          <option value="">Publicados/ativos</option>
          <option value="todos">Todos os status</option>
          <option value="rascunho">Rascunho</option>
          <option value="em_revisao">Em revisão</option>
          <option value="publicado">Publicado/ativo</option>
          <option value="aprovado">Aprovado</option>
          <option value="arquivado">Arquivado</option>
          <option value="obsoleto">Obsoleto</option>
          <option value="inativo">Inativo</option>
        </select>
      </div>

      {procs.length === 0 ? (
        <EmptyState icon={FileText} title="Nenhum procedimento encontrado" subtitle={canWrite ? "Crie o primeiro procedimento operacional" : "Nenhum procedimento cadastrado"} />
      ) : (
        <div className="space-y-3" data-testid="proc-list">
          {procs.map(p => {
            const isCorporate = p.source === 'biblioteca_corporativa';
            const isDraft = p.status === 'rascunho';
            const isCurrent = ['publicado', 'aprovado'].includes(p.status);
            const typeLabel = TYPE_LABELS[p.document_type] || p.document_type || 'Procedimento';
            return (
              <div key={p.id} className="glass-card overflow-hidden" data-testid={`proc-card-${p.id}`}>
                <div className="p-4 flex items-center gap-4 cursor-pointer" onClick={() => setExpanded(expanded === p.id ? null : p.id)}>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      {p.codigo && <span className="text-xs font-mono bg-slate-700/50 px-2 py-0.5 rounded">{p.codigo}</span>}
                      <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[p.status] || ''}`}>{STATUS_LABELS[p.status] || p.status}</span>
                      <span className="text-xs text-blue-300 bg-blue-500/10 px-2 py-0.5 rounded">{typeLabel}</span>
                      {isCorporate && <span className="text-xs text-violet-300 bg-violet-500/10 px-2 py-0.5 rounded flex items-center gap-1"><Library size={11} /> Biblioteca</span>}
                      {p.safety_document && <span className="text-xs text-amber-400 flex items-center gap-1"><Shield size={12} /> Segurança</span>}
                      {p.tempo_estimado_minutos && <span className="text-xs text-slate-400 flex items-center gap-1"><Clock size={12} />{p.tempo_estimado_minutos} min</span>}
                    </div>
                    <h3 className="text-sm font-semibold text-slate-100 truncate">{p.nome}</h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {p.discipline || 'Disciplina não informada'} • Rev. {p.revisao} • v{p.versao}
                      {!isCorporate && ` • ${(p.etapas || []).length} etapa(s)`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {canWrite && (
                      <>
                        <button
                          onClick={event => {
                            event.stopPropagation();
                            if (isCorporate) navigate(`/biblioteca?edit=${p.id}`);
                            else { setEditing(p); setShowForm(true); }
                          }}
                          className="p-2 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg"
                          title={isCorporate ? 'Editar na Biblioteca' : 'Editar'}
                          data-testid={`proc-edit-${p.id}`}
                        >
                          <Edit size={16} />
                        </button>
                        {isCurrent && (
                          <button
                            onClick={event => { event.stopPropagation(); setArchiving(p); }}
                            className="p-2 text-slate-400 hover:text-amber-400 hover:bg-amber-500/10 rounded-lg"
                            title="Arquivar"
                            data-testid={`proc-archive-${p.id}`}
                          >
                            <Archive size={16} />
                          </button>
                        )}
                        {isDraft && (
                          <button
                            onClick={event => { event.stopPropagation(); setDeleting(p); }}
                            className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg"
                            title="Excluir rascunho"
                            data-testid={`proc-delete-${p.id}`}
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </>
                    )}
                    {expanded === p.id ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
                  </div>
                </div>
                {expanded === p.id && (
                  <div className="border-t border-slate-700/50 p-4 bg-slate-800/30">
                    {p.descricao && <p className="text-sm text-slate-300 mb-3">{p.descricao}</p>}
                    {isCorporate ? (
                      <div className="space-y-3">
                        {p.content && <div className="text-sm text-slate-300 whitespace-pre-wrap rounded-lg bg-slate-900/30 p-3">{p.content}</div>}
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 text-xs text-slate-400">
                          <span>Publicado: {formatDate(p.published_at)}</span>
                          <span>Última revisão: {formatDate(p.updated_at)}</span>
                          <span>Responsável: {p.responsavel || '-'}</span>
                          <span>Áreas/tags: {[...(p.areas || []), ...(p.tags || [])].join(', ') || '-'}</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {p.file_url && (
                            <button onClick={() => handleDownload(p)} className="btn-secondary text-xs flex items-center gap-2" data-testid={`proc-download-${p.id}`}>
                              <Download size={14} /> {p.file_name || 'Baixar arquivo'}
                            </button>
                          )}
                          <button onClick={() => navigate(`/biblioteca?view=${p.id}`)} className="btn-secondary text-xs flex items-center gap-2">
                            <Library size={14} /> Abrir na Biblioteca
                          </button>
                        </div>
                      </div>
                    ) : (p.etapas || []).length > 0 ? (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Etapas</p>
                        {p.etapas.map(et => (
                          <div key={et.id} className="flex items-start gap-3 p-2 rounded-lg bg-slate-700/20">
                            <span className="text-xs font-bold text-slate-500 mt-0.5 w-6">{et.ordem}.</span>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm text-slate-200">{et.titulo} {et.obrigatoria && <span className="text-red-400 text-xs">*</span>}</p>
                              {et.descricao && <p className="text-xs text-slate-400 mt-0.5">{et.descricao}</p>}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : <p className="text-xs text-slate-500 italic">Nenhuma etapa cadastrada</p>}
                    {p.observacoes && <p className="text-xs text-slate-400 mt-3 italic">Obs: {p.observacoes}</p>}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {showForm && <ProcedimentoForm proc={editing} onClose={() => { setShowForm(false); setEditing(null); }} onSaved={fetchProcs} />}
      {deleting && <ConfirmDialog title="Excluir rascunho?" message={`Excluir "${deleting.nome}"? A operação só será aceita se não houver utilização.`} onConfirm={handleDelete} onCancel={() => setDeleting(null)} />}
      {archiving && <ConfirmDialog title="Arquivar procedimento?" message={`Arquivar "${archiving.nome}" preservando versões, vínculos e auditoria?`} onConfirm={handleArchive} onCancel={() => setArchiving(null)} />}
    </PageContainer>
  );
};

const ProcedimentoForm = ({ proc, onClose, onSaved }) => {
  const [form, setForm] = useState({
    codigo: proc?.codigo || '',
    nome: proc?.nome || '',
    descricao: proc?.descricao || '',
    revisao: proc?.revisao || '01',
    versao: proc?.versao || 1,
    status: proc?.status || 'rascunho',
    tempo_estimado_minutos: proc?.tempo_estimado_minutos || '',
    observacoes: proc?.observacoes || '',
  });
  const [etapas, setEtapas] = useState(proc?.etapas || []);
  const [saving, setSaving] = useState(false);

  const addEtapa = () => {
    setEtapas([...etapas, { id: crypto.randomUUID(), ordem: etapas.length + 1, titulo: '', descricao: '', obrigatoria: true }]);
  };

  const updateEtapa = (idx, field, value) => {
    const updated = [...etapas];
    updated[idx] = { ...updated[idx], [field]: value };
    setEtapas(updated);
  };

  const removeEtapa = (idx) => {
    const updated = etapas.filter((_, i) => i !== idx).map((e, i) => ({ ...e, ordem: i + 1 }));
    setEtapas(updated);
  };

  const moveEtapa = (idx, dir) => {
    const newIdx = idx + dir;
    if (newIdx < 0 || newIdx >= etapas.length) return;
    const updated = [...etapas];
    [updated[idx], updated[newIdx]] = [updated[newIdx], updated[idx]];
    setEtapas(updated.map((e, i) => ({ ...e, ordem: i + 1 })));
  };

  const handleSave = async () => {
    if (!form.nome.trim()) { toast.error('Nome é obrigatório'); return; }
    const invalidSteps = etapas.filter(e => !e.titulo.trim());
    if (invalidSteps.length > 0) { toast.error('Todas as etapas precisam ter título'); return; }

    setSaving(true);
    try {
      const payload = { ...form, tempo_estimado_minutos: form.tempo_estimado_minutos ? Number(form.tempo_estimado_minutos) : null, etapas };
      if (proc?.id) {
        await api.put(`/procedimentos/${proc.id}`, payload);
        toast.success('Procedimento atualizado');
      } else {
        await api.post('/procedimentos', payload);
        toast.success('Procedimento criado');
      }
      onSaved();
      onClose();
    } catch (e) { toast.error(normalizeError(e)); }
    finally { setSaving(false); }
  };

  return (
    <Modal isOpen={true} onClose={onClose} title={proc ? 'Editar Procedimento' : 'Novo Procedimento'} size="lg">
      <div className="space-y-4 max-h-[70vh] overflow-y-auto custom-scrollbar pr-2" data-testid="proc-form">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Código</label>
            <input value={form.codigo} onChange={e => setForm({...form, codigo: e.target.value})} className="input-field text-sm w-full" placeholder="Auto" data-testid="proc-codigo" />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Status</label>
            <select value={form.status} onChange={e => setForm({...form, status: e.target.value})} className="input-field text-sm w-full" data-testid="proc-status">
              <option value="rascunho">Rascunho</option>
              <option value="aprovado">Aprovado</option>
              <option value="inativo">Inativo</option>
            </select>
          </div>
        </div>
        <div>
          <label className="text-xs text-slate-400 mb-1 block">Nome *</label>
          <input value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} className="input-field text-sm w-full" placeholder="Nome do procedimento" data-testid="proc-nome" />
        </div>
        <div>
          <label className="text-xs text-slate-400 mb-1 block">Descrição</label>
          <textarea value={form.descricao} onChange={e => setForm({...form, descricao: e.target.value})} className="input-field text-sm w-full" rows={2} placeholder="Descrição do procedimento" data-testid="proc-descricao" />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Revisão</label>
            <input value={form.revisao} onChange={e => setForm({...form, revisao: e.target.value})} className="input-field text-sm w-full" data-testid="proc-revisao" />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Versão</label>
            <input type="number" value={form.versao} onChange={e => setForm({...form, versao: Number(e.target.value)})} className="input-field text-sm w-full" data-testid="proc-versao" />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Tempo est. (min)</label>
            <input type="number" value={form.tempo_estimado_minutos} onChange={e => setForm({...form, tempo_estimado_minutos: e.target.value})} className="input-field text-sm w-full" placeholder="Ex: 60" data-testid="proc-tempo" />
          </div>
        </div>
        <div>
          <label className="text-xs text-slate-400 mb-1 block">Observações</label>
          <textarea value={form.observacoes} onChange={e => setForm({...form, observacoes: e.target.value})} className="input-field text-sm w-full" rows={2} data-testid="proc-obs" />
        </div>

        <div className="border-t border-slate-700 pt-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-semibold text-slate-200">Etapas ({etapas.length})</p>
            <button onClick={addEtapa} className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1" data-testid="proc-add-etapa"><Plus size={14} /> Adicionar Etapa</button>
          </div>
          {etapas.length === 0 && <p className="text-xs text-slate-500 italic text-center py-4">Nenhuma etapa. Clique em "Adicionar Etapa".</p>}
          <div className="space-y-3">
            {etapas.map((et, idx) => (
              <div key={et.id} className="p-3 rounded-lg border border-slate-700/50 bg-slate-800/30 space-y-2" data-testid={`proc-etapa-${idx}`}>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-500 w-6">{et.ordem}.</span>
                  <input value={et.titulo} onChange={e => updateEtapa(idx, 'titulo', e.target.value)} className="input-field text-sm flex-1" placeholder="Título da etapa *" data-testid={`proc-etapa-titulo-${idx}`} />
                  <label className="flex items-center gap-1 text-xs text-slate-400 whitespace-nowrap">
                    <input type="checkbox" checked={et.obrigatoria} onChange={e => updateEtapa(idx, 'obrigatoria', e.target.checked)} className="accent-emerald-500" />Obrig.
                  </label>
                  <button onClick={() => moveEtapa(idx, -1)} disabled={idx === 0} className="p-1 text-slate-400 hover:text-slate-200 disabled:opacity-30"><ChevronUp size={14} /></button>
                  <button onClick={() => moveEtapa(idx, 1)} disabled={idx === etapas.length - 1} className="p-1 text-slate-400 hover:text-slate-200 disabled:opacity-30"><ChevronDown size={14} /></button>
                  <button onClick={() => removeEtapa(idx)} className="p-1 text-red-400 hover:text-red-300"><X size={14} /></button>
                </div>
                <textarea value={et.descricao} onChange={e => updateEtapa(idx, 'descricao', e.target.value)} className="input-field text-xs w-full" rows={1} placeholder="Descrição detalhada (opcional)" />
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="flex justify-end gap-3 mt-4 pt-4 border-t border-slate-700">
        <button onClick={onClose} className="btn-secondary text-sm">Cancelar</button>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2 text-sm" data-testid="proc-save-btn">
          <Save size={14} /> {saving ? 'Salvando...' : 'Salvar'}
        </button>
      </div>
    </Modal>
  );
};

export default ProcedimentosPage;
