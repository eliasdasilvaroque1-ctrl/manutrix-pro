import { useState, useEffect, useCallback } from "react";
import { FileText, Settings, Shield, Wrench, Camera, PenTool, Plus, Save, Trash2, ChevronRight, Eye, GripVertical, History, RotateCcw } from "lucide-react";
import { api, useAuth } from "@/lib/api";
import { PageContainer, PageHeader, Loading, EmptyState, Modal, FormInput } from "@/components/shared";
import { toast } from "sonner";

// ===== MAIN PAGE =====
const DocConfigPage = () => {
  const { user } = useAuth();
  const [tab, setTab] = useState('identidade');
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [procedimentos, setProcedimentos] = useState([]);
  const [segurancas, setSegurancas] = useState([]);
  const [editProc, setEditProc] = useState(null);
  const [editSeg, setEditSeg] = useState(null);

  const canEdit = ['master', 'admin', 'pcm'].includes(user?.role);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [cfgRes, procRes, segRes] = await Promise.all([
        api.get('/doc-config'),
        api.get('/doc-config/procedimentos'),
        api.get('/doc-config/seguranca')
      ]);
      setConfig(cfgRes.data);
      setProcedimentos(procRes.data);
      setSegurancas(segRes.data);
    } catch { toast.error('Erro ao carregar configuracoes'); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const saveConfig = async (field, value) => {
    try {
      await api.put('/doc-config', { [field]: value });
      toast.success('Configuracao salva');
      fetchAll();
    } catch { toast.error('Erro ao salvar'); }
  };

  const tabs = [
    { id: 'identidade', label: 'Identidade Visual', icon: PenTool },
    { id: 'procedimentos', label: 'Procedimentos', icon: Wrench },
    { id: 'seguranca', label: 'Segurança', icon: Shield },
    { id: 'fotos', label: 'Fotografias', icon: Camera },
    { id: 'preview', label: 'Pré-visualização', icon: Eye },
  ];

  if (loading) return <Loading />;

  return (
    <PageContainer>
      <PageHeader title="Documentos e Formulários" subtitle="Configuração de impressão por empresa" testId="doc-config-title" />
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2" data-testid="doc-config-tabs">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} data-testid={`tab-${t.id}`}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${tab === t.id ? 'bg-brand text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}>
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {tab === 'identidade' && <IdentidadeTab config={config} onSave={saveConfig} canEdit={canEdit} />}
      {tab === 'procedimentos' && <ProcedimentosTab items={procedimentos} onRefresh={fetchAll} canEdit={canEdit} editItem={editProc} setEditItem={setEditProc} />}
      {tab === 'seguranca' && <SegurancaTab items={segurancas} onRefresh={fetchAll} canEdit={canEdit} editItem={editSeg} setEditItem={setEditSeg} />}
      {tab === 'fotos' && <FotosTab config={config} onSave={saveConfig} canEdit={canEdit} />}
      {tab === 'preview' && <PreviewTab />}
    </PageContainer>
  );
};

// ===== IDENTIDADE VISUAL TAB =====
const IdentidadeTab = ({ config, onSave, canEdit }) => {
  const ident = config?.identidade_doc || {};
  const [form, setForm] = useState({
    titulo_documento: ident.titulo_documento || 'ORDEM DE SERVICO',
    subtitulo: ident.subtitulo || '',
    codigo_interno: ident.codigo_interno || '',
    versao_formulario: ident.versao_formulario || '1.0',
    rodape_texto: ident.rodape_texto || '',
    mostrar_maintrix: ident.mostrar_maintrix !== false,
    qr_posicao: ident.qr_posicao || 'top-right',
    qr_tamanho: ident.qr_tamanho || 'medio',
  });

  const handleSave = () => onSave('identidade_doc', form);

  return (
    <div className="space-y-4" data-testid="identidade-tab">
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-primary mb-4">Identidade do Documento</h3>
        <p className="text-xs text-slate-500 mb-4">Logo e nome da empresa sao carregados das configuracoes da organizacao. Aqui voce configura os campos especificos do documento impresso.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormInput label="Titulo do Documento">
            <input value={form.titulo_documento} onChange={e => setForm({...form, titulo_documento: e.target.value})} className="input-industrial w-full px-3" disabled={!canEdit} data-testid="doc-titulo" />
          </FormInput>
          <FormInput label="Subtitulo">
            <input value={form.subtitulo} onChange={e => setForm({...form, subtitulo: e.target.value})} className="input-industrial w-full px-3" disabled={!canEdit} />
          </FormInput>
          <FormInput label="Codigo Interno">
            <input value={form.codigo_interno} onChange={e => setForm({...form, codigo_interno: e.target.value})} className="input-industrial w-full px-3" placeholder="Ex: FRM-MNT-001" disabled={!canEdit} />
          </FormInput>
          <FormInput label="Versao do Formulario">
            <input value={form.versao_formulario} onChange={e => setForm({...form, versao_formulario: e.target.value})} className="input-industrial w-full px-3" disabled={!canEdit} />
          </FormInput>
          <FormInput label="Texto do Rodape">
            <input value={form.rodape_texto} onChange={e => setForm({...form, rodape_texto: e.target.value})} className="input-industrial w-full px-3" disabled={!canEdit} />
          </FormInput>
          <FormInput label="Posicao QR Code">
            <select value={form.qr_posicao} onChange={e => setForm({...form, qr_posicao: e.target.value})} className="input-industrial w-full px-3" disabled={!canEdit}>
              <option value="top-right">Superior Direito</option>
              <option value="top-left">Superior Esquerdo</option>
              <option value="bottom-right">Inferior Direito</option>
            </select>
          </FormInput>
        </div>
        <label className="flex items-center gap-2 mt-4 text-sm text-slate-400">
          <input type="checkbox" checked={form.mostrar_maintrix} onChange={e => setForm({...form, mostrar_maintrix: e.target.checked})} disabled={!canEdit} />
          Exibir "Powered by MAINTRIX" no rodape
        </label>
        {canEdit && (
          <button onClick={handleSave} className="btn-primary mt-4 flex items-center gap-2" data-testid="save-identidade"><Save size={16} /> Salvar Identidade</button>
        )}
      </div>
    </div>
  );
};

// ===== PROCEDIMENTOS TAB =====
const ProcedimentosTab = ({ items, onRefresh, canEdit, editItem, setEditItem }) => {
  const [showForm, setShowForm] = useState(false);
  const [versionItem, setVersionItem] = useState(null);

  const handleDelete = async (id) => {
    if (!window.confirm('Excluir este procedimento?')) return;
    try { await api.delete(`/doc-config/procedimentos/${id}`); toast.success('Excluido'); onRefresh(); } catch { toast.error('Erro'); }
  };

  return (
    <div data-testid="procedimentos-tab">
      <div className="flex justify-between items-center mb-4">
        <p className="text-xs text-slate-500">Procedimentos padrão de execução. Cada alteração gera uma nova versão imutável.</p>
        {canEdit && <button onClick={() => { setEditItem(null); setShowForm(true); }} className="btn-primary flex items-center gap-2" data-testid="new-procedimento"><Plus size={16} /> Novo Procedimento</button>}
      </div>
      {items.length === 0 ? <EmptyState title="Nenhum procedimento cadastrado" /> : (
        <div className="space-y-2">
          {items.map(p => (
            <div key={p.id} className="glass-card p-4 flex items-center justify-between" data-testid={`proc-${p.id}`}>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-primary">{p.nome}</span>
                  {p.codigo && <span className="text-xs bg-slate-700 px-2 py-0.5 rounded">{p.codigo}</span>}
                  <span className="text-xs text-brand bg-brand/10 px-2 py-0.5 rounded">v{p.versao || 1}</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">{p.tipo_atividade || '-'} | {p.disciplina || '-'} | {(p.etapas || []).length} etapas</p>
              </div>
              <div className="flex gap-2 items-center">
                <button onClick={() => setVersionItem(p)} className="text-xs text-slate-400 hover:text-amber-400 flex items-center gap-1" data-testid={`proc-history-${p.id}`}><History size={14} /> Versoes</button>
                {canEdit && <button onClick={() => { setEditItem(p); setShowForm(true); }} className="text-xs text-blue-400 hover:text-blue-300">Editar</button>}
                {canEdit && <button onClick={() => handleDelete(p.id)} className="text-xs text-red-400 hover:text-red-300"><Trash2 size={14} /></button>}
              </div>
            </div>
          ))}
        </div>
      )}
      {showForm && <ProcedimentoForm item={editItem} onClose={() => setShowForm(false)} onSuccess={() => { setShowForm(false); onRefresh(); }} />}
      {versionItem && <VersionHistoryModal itemType="procedimentos" itemId={versionItem.id} itemName={versionItem.nome} onClose={() => setVersionItem(null)} onRestore={() => { setVersionItem(null); onRefresh(); }} />}
    </div>
  );
};

// ===== PROCEDIMENTO FORM MODAL =====
const ProcedimentoForm = ({ item, onClose, onSuccess }) => {
  const [form, setForm] = useState(item || { nome: '', codigo: '', tipo_atividade: '', disciplina: '', objetivo: '', pre_requisitos: '', etapas: [], ferramentas: [], materiais: [], observacoes: '' });
  const [saving, setSaving] = useState(false);

  const addEtapa = () => setForm({...form, etapas: [...form.etapas, { numero: form.etapas.length + 1, descricao: '', observacao: '' }]});
  const updateEtapa = (idx, field, val) => {
    const etapas = [...form.etapas];
    etapas[idx] = {...etapas[idx], [field]: val};
    setForm({...form, etapas});
  };
  const removeEtapa = (idx) => setForm({...form, etapas: form.etapas.filter((_, i) => i !== idx).map((e, i) => ({...e, numero: i + 1}))});

  const handleSave = async () => {
    if (!form.nome) { toast.error('Nome obrigatorio'); return; }
    setSaving(true);
    try {
      if (item?.id) {
        await api.put(`/doc-config/procedimentos/${item.id}`, form);
      } else {
        await api.post('/doc-config/procedimentos', form);
      }
      toast.success('Procedimento salvo');
      onSuccess();
    } catch { toast.error('Erro ao salvar'); }
    setSaving(false);
  };

  return (
    <Modal isOpen onClose={onClose} title={item ? 'Editar Procedimento' : 'Novo Procedimento'} size="xl">
      <div className="space-y-4 max-h-[70vh] overflow-y-auto">
        <div className="grid grid-cols-2 gap-3">
          <FormInput label="Nome"><input value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-3" data-testid="proc-nome" /></FormInput>
          <FormInput label="Codigo"><input value={form.codigo} onChange={e => setForm({...form, codigo: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
          <FormInput label="Tipo Atividade"><input value={form.tipo_atividade} onChange={e => setForm({...form, tipo_atividade: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
          <FormInput label="Disciplina"><input value={form.disciplina} onChange={e => setForm({...form, disciplina: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
        </div>
        <FormInput label="Objetivo"><textarea value={form.objetivo} onChange={e => setForm({...form, objetivo: e.target.value})} className="input-industrial w-full px-3 h-16" /></FormInput>
        <FormInput label="Pre-requisitos"><textarea value={form.pre_requisitos} onChange={e => setForm({...form, pre_requisitos: e.target.value})} className="input-industrial w-full px-3 h-12" /></FormInput>
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-xs font-medium text-slate-400">Etapas do Procedimento</label>
            <button onClick={addEtapa} className="text-xs text-brand hover:text-brand-light flex items-center gap-1"><Plus size={14} /> Adicionar Etapa</button>
          </div>
          {form.etapas.map((et, i) => (
            <div key={i} className="flex items-start gap-2 mb-2 bg-slate-800/50 rounded-lg p-2">
              <span className="text-brand font-bold text-sm mt-1 w-6 shrink-0">{et.numero}</span>
              <input value={et.descricao} onChange={e => updateEtapa(i, 'descricao', e.target.value)} placeholder="Descricao da etapa..." className="input-industrial flex-1 px-2 text-sm" />
              <button onClick={() => removeEtapa(i)} className="text-red-400 hover:text-red-300 mt-1"><Trash2 size={14} /></button>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <FormInput label="Ferramentas (separar por virgula)"><input value={(form.ferramentas || []).join(', ')} onChange={e => setForm({...form, ferramentas: e.target.value.split(',').map(s => s.trim()).filter(Boolean)})} className="input-industrial w-full px-3" /></FormInput>
          <FormInput label="Materiais (separar por virgula)"><input value={(form.materiais || []).join(', ')} onChange={e => setForm({...form, materiais: e.target.value.split(',').map(s => s.trim()).filter(Boolean)})} className="input-industrial w-full px-3" /></FormInput>
        </div>
        <FormInput label="Observacoes"><textarea value={form.observacoes} onChange={e => setForm({...form, observacoes: e.target.value})} className="input-industrial w-full px-3 h-12" /></FormInput>
        {item?.id && (
          <FormInput label="Motivo da alteracao (opcional)">
            <input value={form.motivo_alteracao || ''} onChange={e => setForm({...form, motivo_alteracao: e.target.value})} className="input-industrial w-full px-3" placeholder="Ex: Adicionada etapa de verificacao" data-testid="proc-motivo" />
          </FormInput>
        )}
      </div>
      <div className="flex gap-3 mt-4">
        <button onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="save-proc"><Save size={16} /> {saving ? 'Salvando...' : 'Salvar'}</button>
      </div>
    </Modal>
  );
};

// ===== SEGURANCA TAB =====
const SegurancaTab = ({ items, onRefresh, canEdit, editItem, setEditItem }) => {
  const [showForm, setShowForm] = useState(false);
  const [versionItem, setVersionItem] = useState(null);

  const handleDelete = async (id) => {
    if (!window.confirm('Excluir?')) return;
    try { await api.delete(`/doc-config/seguranca/${id}`); toast.success('Excluido'); onRefresh(); } catch { toast.error('Erro'); }
  };
  return (
    <div data-testid="seguranca-tab">
      <div className="flex justify-between items-center mb-4">
        <p className="text-xs text-slate-500">Modelos de segurança versionados. Cada alteração gera uma nova versão imutável.</p>
        {canEdit && <button onClick={() => { setEditItem(null); setShowForm(true); }} className="btn-primary flex items-center gap-2" data-testid="new-seguranca"><Plus size={16} /> Novo Modelo</button>}
      </div>
      {items.length === 0 ? <EmptyState title="Nenhum modelo de seguranca" /> : (
        <div className="space-y-2">
          {items.map(s => (
            <div key={s.id} className="glass-card p-4 flex items-center justify-between" data-testid={`seg-${s.id}`}>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-primary">{s.nome}</span>
                  <span className="text-xs text-brand bg-brand/10 px-2 py-0.5 rounded">v{s.versao || 1}</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">{(s.riscos || []).length} riscos | {(s.epis || []).length} EPIs | {s.loto?.necessario ? 'LOTO' : ''} {s.apr?.necessaria ? 'APR' : ''} {s.pt?.necessaria ? 'PT' : ''}</p>
              </div>
              <div className="flex gap-2 items-center">
                <button onClick={() => setVersionItem(s)} className="text-xs text-slate-400 hover:text-amber-400 flex items-center gap-1" data-testid={`seg-history-${s.id}`}><History size={14} /> Versoes</button>
                {canEdit && <button onClick={() => { setEditItem(s); setShowForm(true); }} className="text-xs text-blue-400 hover:text-blue-300">Editar</button>}
                {canEdit && <button onClick={() => handleDelete(s.id)} className="text-xs text-red-400 hover:text-red-300"><Trash2 size={14} /></button>}
              </div>
            </div>
          ))}
        </div>
      )}
      {showForm && <SegurancaForm item={editItem} onClose={() => setShowForm(false)} onSuccess={() => { setShowForm(false); onRefresh(); }} />}
      {versionItem && <VersionHistoryModal itemType="seguranca" itemId={versionItem.id} itemName={versionItem.nome} onClose={() => setVersionItem(null)} onRestore={() => { setVersionItem(null); onRefresh(); }} />}
    </div>
  );
};

// ===== SEGURANCA FORM =====
const SegurancaForm = ({ item, onClose, onSuccess }) => {
  const [form, setForm] = useState(item || { nome: '', codigo: '', tipo_atividade: '', disciplina: '', riscos: [], medidas_controle: [], epis: [], epcs: [], loto: { necessario: false }, apr: { necessaria: false }, pt: { necessaria: false }, bloqueios: [], observacoes: '' });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!form.nome) { toast.error('Nome obrigatorio'); return; }
    setSaving(true);
    try {
      if (item?.id) await api.put(`/doc-config/seguranca/${item.id}`, form);
      else await api.post('/doc-config/seguranca', form);
      toast.success('Salvo'); onSuccess();
    } catch { toast.error('Erro'); }
    setSaving(false);
  };

  return (
    <Modal isOpen onClose={onClose} title={item ? 'Editar Seguranca' : 'Novo Modelo de Seguranca'} size="xl">
      <div className="space-y-4 max-h-[70vh] overflow-y-auto">
        <div className="grid grid-cols-2 gap-3">
          <FormInput label="Nome"><input value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-3" data-testid="seg-nome" /></FormInput>
          <FormInput label="Codigo"><input value={form.codigo} onChange={e => setForm({...form, codigo: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
          <FormInput label="Tipo Atividade"><input value={form.tipo_atividade} onChange={e => setForm({...form, tipo_atividade: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
          <FormInput label="Disciplina"><input value={form.disciplina} onChange={e => setForm({...form, disciplina: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
        </div>
        <FormInput label="Riscos (um por linha)">
          <textarea value={(form.riscos || []).map(r => typeof r === 'string' ? r : r.descricao).join('\n')} onChange={e => setForm({...form, riscos: e.target.value.split('\n').filter(Boolean).map(d => ({descricao: d}))})} className="input-industrial w-full px-3 h-20" placeholder="Risco eletrico&#10;Queda de altura&#10;Prensamento" />
        </FormInput>
        <FormInput label="Medidas de Controle (uma por linha)">
          <textarea value={(form.medidas_controle || []).join('\n')} onChange={e => setForm({...form, medidas_controle: e.target.value.split('\n').filter(Boolean)})} className="input-industrial w-full px-3 h-16" />
        </FormInput>
        <div className="grid grid-cols-2 gap-3">
          <FormInput label="EPIs (separar por virgula)"><input value={(form.epis || []).join(', ')} onChange={e => setForm({...form, epis: e.target.value.split(',').map(s => s.trim()).filter(Boolean)})} className="input-industrial w-full px-3" placeholder="Capacete, Luva, Oculos" /></FormInput>
          <FormInput label="EPCs (separar por virgula)"><input value={(form.epcs || []).join(', ')} onChange={e => setForm({...form, epcs: e.target.value.split(',').map(s => s.trim()).filter(Boolean)})} className="input-industrial w-full px-3" /></FormInput>
        </div>
        <div className="flex gap-6">
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.loto?.necessario || false} onChange={e => setForm({...form, loto: {...(form.loto || {}), necessario: e.target.checked}})} /> LOTO / Bloqueio</label>
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.apr?.necessaria || false} onChange={e => setForm({...form, apr: {...(form.apr || {}), necessaria: e.target.checked}})} /> APR</label>
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.pt?.necessaria || false} onChange={e => setForm({...form, pt: {...(form.pt || {}), necessaria: e.target.checked}})} /> PT</label>
        </div>
        <FormInput label="Observacoes de Seguranca"><textarea value={form.observacoes} onChange={e => setForm({...form, observacoes: e.target.value})} className="input-industrial w-full px-3 h-12" /></FormInput>
        {item?.id && (
          <FormInput label="Motivo da alteracao (opcional)">
            <input value={form.motivo_alteracao || ''} onChange={e => setForm({...form, motivo_alteracao: e.target.value})} className="input-industrial w-full px-3" placeholder="Ex: Adicionado novo risco" data-testid="seg-motivo" />
          </FormInput>
        )}
      </div>
      <div className="flex gap-3 mt-4">
        <button onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="save-seg"><Save size={16} /> {saving ? 'Salvando...' : 'Salvar'}</button>
      </div>
    </Modal>
  );
};

// ===== VERSION HISTORY MODAL =====
const VersionHistoryModal = ({ itemType, itemId, itemName, onClose, onRestore }) => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [restoring, setRestoring] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const { user } = useAuth();
  const canRestore = ['master', 'admin', 'pcm'].includes(user?.role);

  useEffect(() => {
    const load = async () => {
      try {
        const r = await api.get(`/doc-config/${itemType}/${itemId}/versoes`);
        setVersions(r.data);
      } catch { toast.error('Erro ao carregar versoes'); }
      setLoading(false);
    };
    load();
  }, [itemType, itemId]);

  const handleRestore = async (versao) => {
    const motivo = window.prompt('Motivo da restauracao (opcional):') || '';
    setRestoring(versao);
    try {
      await api.post(`/doc-config/${itemType}/${itemId}/restaurar/${versao}?motivo=${encodeURIComponent(motivo)}`);
      toast.success(`Restaurado para v${versao}`);
      onRestore();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao restaurar');
    }
    setRestoring(null);
  };

  return (
    <Modal isOpen onClose={onClose} title={`Histórico de Versões — ${itemName}`} size="xl">
      <div className="max-h-[70vh] overflow-y-auto" data-testid="version-history-modal">
        {loading ? <Loading /> : versions.length === 0 ? (
          <p className="text-sm text-slate-500 py-4">Nenhuma versão encontrada.</p>
        ) : (
          <div className="space-y-2">
            {versions.map((v, i) => {
              const s = v.snapshot || {};
              const isFirst = i === 0;
              return (
                <div key={v.id} className={`rounded-lg border p-3 ${isFirst ? 'border-brand/30 bg-brand/5' : 'border-slate-700 bg-slate-800/50'}`} data-testid={`version-${v.versao}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${isFirst ? 'bg-brand text-white' : 'bg-slate-700 text-slate-300'}`}>v{v.versao}</span>
                      <span className="text-sm text-primary">{s.nome || '-'}</span>
                      {isFirst && <span className="text-xs text-emerald-400">(atual)</span>}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500">{(v.created_at || '').slice(0, 16).replace('T', ' ')}</span>
                      {canRestore && !isFirst && (
                        <button onClick={() => handleRestore(v.versao)} disabled={restoring === v.versao}
                          className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1 ml-2" data-testid={`restore-v${v.versao}`}>
                          <RotateCcw size={12} /> {restoring === v.versao ? 'Restaurando...' : 'Restaurar'}
                        </button>
                      )}
                      <button onClick={() => setExpanded(expanded === v.versao ? null : v.versao)} className="text-xs text-slate-400 hover:text-white ml-1">
                        {expanded === v.versao ? 'Ocultar' : 'Detalhes'}
                      </button>
                    </div>
                  </div>
                  {v.motivo && <p className="text-xs text-slate-400 mt-1 italic">{v.motivo}</p>}
                  {expanded === v.versao && (
                    <div className="mt-3 p-2 bg-slate-900/60 rounded text-xs text-slate-300 space-y-1">
                      {s.codigo && <p><strong>Codigo:</strong> {s.codigo}</p>}
                      {s.objetivo && <p><strong>Objetivo:</strong> {s.objetivo}</p>}
                      {s.disciplina && <p><strong>Disciplina:</strong> {s.disciplina}</p>}
                      {s.etapas?.length > 0 && <p><strong>Etapas:</strong> {s.etapas.map(e => e.descricao).join(' → ')}</p>}
                      {s.ferramentas?.length > 0 && <p><strong>Ferramentas:</strong> {s.ferramentas.join(', ')}</p>}
                      {s.materiais?.length > 0 && <p><strong>Materiais:</strong> {s.materiais.join(', ')}</p>}
                      {s.riscos?.length > 0 && <p><strong>Riscos:</strong> {s.riscos.map(r => typeof r === 'string' ? r : r.descricao).join(', ')}</p>}
                      {s.epis?.length > 0 && <p><strong>EPIs:</strong> {s.epis.join(', ')}</p>}
                      {s.observacoes && <p><strong>Obs:</strong> {s.observacoes}</p>}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Modal>
  );
};

// ===== FOTOS TAB =====
const FotosTab = ({ config, onSave, canEdit }) => {
  const foto = config?.foto_config || { classificacoes: ['antes', 'durante', 'depois', 'falha', 'componente', 'seguranca', 'outra'], legenda_obrigatoria: false, grid_colunas: 2, max_por_pagina: 4 };
  const [form, setForm] = useState(foto);

  return (
    <div className="glass-card p-5" data-testid="fotos-tab">
      <h3 className="text-sm font-semibold text-primary mb-4">Configuração de Fotografias no Documento</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormInput label="Colunas na grade de fotos">
          <select value={form.grid_colunas} onChange={e => setForm({...form, grid_colunas: parseInt(e.target.value)})} className="input-industrial w-full px-3" disabled={!canEdit}>
            <option value={2}>2 colunas</option>
            <option value={3}>3 colunas</option>
          </select>
        </FormInput>
        <FormInput label="Maximo de fotos por pagina">
          <select value={form.max_por_pagina} onChange={e => setForm({...form, max_por_pagina: parseInt(e.target.value)})} className="input-industrial w-full px-3" disabled={!canEdit}>
            <option value={2}>2</option>
            <option value={4}>4</option>
            <option value={6}>6</option>
          </select>
        </FormInput>
      </div>
      <label className="flex items-center gap-2 mt-4 text-sm text-slate-400">
        <input type="checkbox" checked={form.legenda_obrigatoria} onChange={e => setForm({...form, legenda_obrigatoria: e.target.checked})} disabled={!canEdit} />
        Legenda obrigatoria em todas as fotos
      </label>
      <p className="text-xs text-slate-500 mt-3">Classificacoes disponiveis: {(form.classificacoes || []).join(', ')}</p>
      {canEdit && <button onClick={() => onSave('foto_config', form)} className="btn-primary mt-4 flex items-center gap-2"><Save size={16} /> Salvar</button>}
    </div>
  );
};

// ===== PREVIEW TAB =====
const PreviewTab = () => {
  const { openAuthenticatedPdf } = require('@/lib/api');
  const [osId, setOsId] = useState('');
  const [osList, setOsList] = useState([]);

  useEffect(() => {
    api.get('/ordens-servico?status=programada').then(r => {
      const data = Array.isArray(r.data) ? r.data : [];
      setOsList(data.slice(0, 5));
      if (data.length > 0) setOsId(data[0].id);
    }).catch(() => {});
  }, []);

  const preview = (modo) => {
    if (!osId) { toast.error('Selecione uma OS'); return; }
    openAuthenticatedPdf(`/ordens-servico/${osId}/pdf?modo=${modo}`, (msg) => toast.error(msg));
  };

  return (
    <div className="glass-card p-5" data-testid="preview-tab">
      <h3 className="text-sm font-semibold text-primary mb-4">Pré-visualização do Documento</h3>
      <FormInput label="Selecionar OS para preview">
        <select value={osId} onChange={e => setOsId(e.target.value)} className="input-industrial w-full px-3">
          {osList.map(o => <option key={o.id} value={o.id}>{o.numero} - {o.titulo}</option>)}
        </select>
      </FormInput>
      <div className="flex gap-3 mt-4">
        <button onClick={() => preview('digital')} className="btn-primary flex items-center gap-2" data-testid="preview-digital"><Eye size={16} /> Documento Digital</button>
        <button onClick={() => preview('manual')} className="btn-secondary flex items-center gap-2" data-testid="preview-manual"><FileText size={16} /> Formulario Manual</button>
      </div>
    </div>
  );
};

export default DocConfigPage;
