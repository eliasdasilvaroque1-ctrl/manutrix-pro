import { useState, useEffect } from "react";
import { useAuth, api } from "../lib/api";
import { normalizeError } from "../lib/constants";
import { toast } from "sonner";
import { Plus, Edit, Trash2, Save, X, ChevronDown, ChevronUp, FileText, CheckCircle, Clock, Search, AlertCircle } from "lucide-react";
import { PageContainer, PageHeader, SearchInput, EmptyState, Loading, Modal, ConfirmDialog } from "../components/shared";

const STATUS_LABELS = { rascunho: 'Rascunho', aprovado: 'Aprovado', inativo: 'Inativo' };
const STATUS_COLORS = { rascunho: 'bg-amber-500/20 text-amber-400', aprovado: 'bg-emerald-500/20 text-emerald-400', inativo: 'bg-slate-500/20 text-slate-400' };

const ProcedimentosPage = () => {
  const { user } = useAuth();
  const [procs, setProcs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [expanded, setExpanded] = useState(null);

  const canWrite = ['admin', 'pcm', 'master'].includes(user?.role);

  const fetchProcs = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (statusFilter) params.set('status', statusFilter);
      const res = await api.get(`/procedimentos?${params}`);
      setProcs(res.data);
    } catch (e) { toast.error(normalizeError(e)); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchProcs(); }, [search, statusFilter]);

  const handleDelete = async () => {
    try {
      await api.delete(`/procedimentos/${deleting.id}`);
      toast.success('Procedimento excluído');
      setDeleting(null);
      fetchProcs();
    } catch (e) { toast.error(normalizeError(e)); }
  };

  if (loading) return <Loading rows={4} />;

  return (
    <PageContainer>
      <PageHeader title="Procedimentos Operacionais" subtitle={`${procs.length} procedimento(s)`}>
        {canWrite && <button onClick={() => { setEditing(null); setShowForm(true); }} className="btn-primary flex items-center gap-2" data-testid="proc-create-btn"><Plus size={16} /> Novo Procedimento</button>}
      </PageHeader>

      <div className="flex flex-wrap gap-3 mb-4" data-testid="proc-filters">
        <SearchInput value={search} onChange={setSearch} placeholder="Buscar por nome ou código..." />
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="input-field w-auto text-sm" data-testid="proc-status-filter">
          <option value="">Todos os status</option>
          <option value="rascunho">Rascunho</option>
          <option value="aprovado">Aprovado</option>
          <option value="inativo">Inativo</option>
        </select>
      </div>

      {procs.length === 0 ? (
        <EmptyState icon={FileText} title="Nenhum procedimento encontrado" subtitle={canWrite ? "Crie o primeiro procedimento operacional" : "Nenhum procedimento cadastrado"} />
      ) : (
        <div className="space-y-3" data-testid="proc-list">
          {procs.map(p => (
            <div key={p.id} className="glass-card overflow-hidden" data-testid={`proc-card-${p.id}`}>
              <div className="p-4 flex items-center gap-4 cursor-pointer" onClick={() => setExpanded(expanded === p.id ? null : p.id)}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono bg-slate-700/50 px-2 py-0.5 rounded">{p.codigo}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[p.status] || ''}`}>{STATUS_LABELS[p.status] || p.status}</span>
                    {p.tempo_estimado_minutos && <span className="text-xs text-slate-400 flex items-center gap-1"><Clock size={12} />{p.tempo_estimado_minutos} min</span>}
                  </div>
                  <h3 className="text-sm font-semibold text-slate-100 truncate">{p.nome}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">Rev. {p.revisao} | v{p.versao} | {(p.etapas || []).length} etapa(s)</p>
                </div>
                <div className="flex items-center gap-2">
                  {canWrite && (
                    <>
                      <button onClick={e => { e.stopPropagation(); setEditing(p); setShowForm(true); }} className="p-2 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg" data-testid={`proc-edit-${p.id}`}><Edit size={16} /></button>
                      <button onClick={e => { e.stopPropagation(); setDeleting(p); }} className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg" data-testid={`proc-delete-${p.id}`}><Trash2 size={16} /></button>
                    </>
                  )}
                  {expanded === p.id ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
                </div>
              </div>
              {expanded === p.id && (
                <div className="border-t border-slate-700/50 p-4 bg-slate-800/30">
                  {p.descricao && <p className="text-xs text-slate-300 mb-3">{p.descricao}</p>}
                  {(p.etapas || []).length > 0 ? (
                    <div className="space-y-2">
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Etapas</p>
                      {p.etapas.map((et, i) => (
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
          ))}
        </div>
      )}

      {showForm && <ProcedimentoForm proc={editing} onClose={() => { setShowForm(false); setEditing(null); }} onSaved={fetchProcs} />}
      {deleting && <ConfirmDialog title="Excluir Procedimento?" message={`Tem certeza que deseja excluir "${deleting.nome}"?`} onConfirm={handleDelete} onCancel={() => setDeleting(null)} />}
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
