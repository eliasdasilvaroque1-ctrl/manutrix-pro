import { useState, useEffect, useCallback } from "react";
import { FileText, Settings, Shield, Wrench, Camera, PenTool, Plus, Save, Trash2, ChevronRight, Eye, GripVertical, History, RotateCcw, ClipboardList, BookOpen, Cog, FormInput as FormInputIcon, FileSignature, Layout, Type } from "lucide-react";
import { api, useAuth, safeErrorMsg } from "../lib/api";
import { PageContainer, PageHeader, Loading, EmptyState, Modal, FormInput } from "../components/shared";
import { toast } from "sonner";

// ===== MAIN PAGE =====
const DocConfigPage = () => {
  const { user } = useAuth();
  const [tab, setTab] = useState('identidade');
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [procedimentos, setProcedimentos] = useState([]);
  const [segurancas, setSegurancas] = useState([]);
  const [checklists, setChecklists] = useState([]);
  const [modelosInsp, setModelosInsp] = useState([]);
  const [modelosOS, setModelosOS] = useState([]);
  const [editProc, setEditProc] = useState(null);
  const [editSeg, setEditSeg] = useState(null);
  const [editCL, setEditCL] = useState(null);
  const [editMI, setEditMI] = useState(null);
  const [editMO, setEditMO] = useState(null);
  const [campos, setCampos] = useState([]);
  const [cabecalhos, setCabecalhos] = useState([]);
  const [assinaturas, setAssinaturas] = useState([]);
  const [layouts, setLayouts] = useState([]);

  const canEdit = ['master', 'admin', 'pcm'].includes(user?.role);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [cfgRes, procRes, segRes, clRes, miRes, moRes, cpRes, cbRes, asRes, lyRes] = await Promise.all([
        api.get('/doc-config'),
        api.get('/doc-config/procedimentos'),
        api.get('/doc-config/seguranca'),
        api.get('/doc-config/checklists'),
        api.get('/doc-config/modelos-inspecao'),
        api.get('/doc-config/modelos-os'),
        api.get('/doc-config/campos'),
        api.get('/doc-config/cabecalhos-rodapes'),
        api.get('/doc-config/assinaturas'),
        api.get('/doc-config/layouts'),
      ]);
      setConfig(cfgRes.data);
      setProcedimentos(procRes.data);
      setSegurancas(segRes.data);
      setChecklists(clRes.data);
      setModelosInsp(miRes.data);
      setModelosOS(moRes.data);
      setCampos(cpRes.data);
      setCabecalhos(cbRes.data);
      setAssinaturas(asRes.data);
      setLayouts(lyRes.data);
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
    { id: 'checklists', label: 'Checklists', icon: ClipboardList },
    { id: 'modelos-inspecao', label: 'Modelos Inspeção', icon: BookOpen },
    { id: 'modelos-os', label: 'Modelos OS', icon: Cog },
    { id: 'campos', label: 'Campos', icon: Type },
    { id: 'cabecalhos', label: 'Cabeçalhos/Rodapés', icon: FileText },
    { id: 'assinaturas', label: 'Assinaturas', icon: FileSignature },
    { id: 'layouts', label: 'Layouts', icon: Layout },
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
      {tab === 'checklists' && <ChecklistsTab items={checklists} onRefresh={fetchAll} canEdit={canEdit} editItem={editCL} setEditItem={setEditCL} />}
      {tab === 'modelos-inspecao' && <ModelosInspecaoTab items={modelosInsp} procedimentos={procedimentos} segurancas={segurancas} checklists={checklists} onRefresh={fetchAll} canEdit={canEdit} editItem={editMI} setEditItem={setEditMI} />}
      {tab === 'modelos-os' && <ModelosOSTab items={modelosOS} procedimentos={procedimentos} segurancas={segurancas} checklists={checklists} onRefresh={fetchAll} canEdit={canEdit} editItem={editMO} setEditItem={setEditMO} />}
      {tab === 'campos' && <CamposTab items={campos} onRefresh={fetchAll} canEdit={canEdit} />}
      {tab === 'cabecalhos' && <CabecalhosTab items={cabecalhos} onRefresh={fetchAll} canEdit={canEdit} />}
      {tab === 'assinaturas' && <AssinaturasTab items={assinaturas} onRefresh={fetchAll} canEdit={canEdit} />}
      {tab === 'layouts' && <LayoutsTab items={layouts} cabecalhos={cabecalhos} campos={campos} assinaturas={assinaturas} onRefresh={fetchAll} canEdit={canEdit} />}
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

// ===== CHECKLISTS TAB =====
const DISCIPLINAS = ['mecanica', 'eletrica', 'instrumentacao', 'civil', 'producao', 'lubrificacao'];
const TIPOS_ITEM = ['boolean', 'numero', 'texto', 'selecao'];

const ChecklistsTab = ({ items, onRefresh, canEdit, editItem, setEditItem }) => {
  const [showForm, setShowForm] = useState(false);
  const [versionItem, setVersionItem] = useState(null);
  const handleDelete = async (id) => {
    if (!window.confirm('Excluir este checklist?')) return;
    try { await api.delete(`/doc-config/checklists/${id}`); toast.success('Excluído'); onRefresh(); } catch { toast.error('Erro'); }
  };
  return (
    <div data-testid="checklists-tab">
      <div className="flex justify-between items-center mb-4">
        <p className="text-xs text-slate-500">Checklists reutilizáveis por disciplina. Versionados automaticamente.</p>
        {canEdit && <button onClick={() => { setEditItem(null); setShowForm(true); }} className="btn-primary flex items-center gap-2" data-testid="new-checklist"><Plus size={16} /> Novo Checklist</button>}
      </div>
      {items.length === 0 ? <EmptyState title="Nenhum checklist cadastrado" /> : (
        <div className="space-y-2">
          {items.map(c => (
            <div key={c.id} className="glass-card p-4 flex items-center justify-between" data-testid={`cl-${c.id}`}>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-primary">{c.nome}</span>
                  <span className="text-xs text-brand bg-brand/10 px-2 py-0.5 rounded">v{c.versao || 1}</span>
                  {c.status === 'inativo' && <span className="text-xs text-red-400 bg-red-400/10 px-2 py-0.5 rounded">Inativo</span>}
                </div>
                <p className="text-xs text-slate-500 mt-1">{c.disciplina || '-'} | {c.categoria || '-'} | {(c.itens || []).length} itens</p>
              </div>
              <div className="flex gap-2 items-center">
                <button onClick={() => setVersionItem(c)} className="text-xs text-slate-400 hover:text-amber-400 flex items-center gap-1"><History size={14} /> Versões</button>
                {canEdit && <button onClick={() => { setEditItem(c); setShowForm(true); }} className="text-xs text-blue-400 hover:text-blue-300">Editar</button>}
                {canEdit && <button onClick={() => handleDelete(c.id)} className="text-xs text-red-400 hover:text-red-300"><Trash2 size={14} /></button>}
              </div>
            </div>
          ))}
        </div>
      )}
      {showForm && <ChecklistForm item={editItem} onClose={() => setShowForm(false)} onSuccess={() => { setShowForm(false); onRefresh(); }} />}
      {versionItem && <VersionHistoryModal itemType="checklists" itemId={versionItem.id} itemName={versionItem.nome} onClose={() => setVersionItem(null)} onRestore={() => { setVersionItem(null); onRefresh(); }} />}
    </div>
  );
};

const ChecklistForm = ({ item, onClose, onSuccess }) => {
  const [form, setForm] = useState(item || { nome: '', descricao: '', disciplina: '', categoria: '', itens: [], status: 'ativo' });
  const [saving, setSaving] = useState(false);
  const addItem = () => setForm({...form, itens: [...form.itens, { descricao: '', tipo: 'boolean', obrigatorio: true, ordem: form.itens.length + 1 }]});
  const updateItem = (idx, field, val) => { const itens = [...form.itens]; itens[idx] = {...itens[idx], [field]: val}; setForm({...form, itens}); };
  const removeItem = (idx) => setForm({...form, itens: form.itens.filter((_, i) => i !== idx).map((e, i) => ({...e, ordem: i + 1}))});
  const handleSave = async () => {
    if (!form.nome) { toast.error('Nome obrigatório'); return; }
    setSaving(true);
    try {
      if (item?.id) await api.put(`/doc-config/checklists/${item.id}`, form);
      else await api.post('/doc-config/checklists', form);
      toast.success('Checklist salvo'); onSuccess();
    } catch { toast.error('Erro ao salvar'); }
    setSaving(false);
  };
  return (
    <Modal isOpen onClose={onClose} title={item ? 'Editar Checklist' : 'Novo Checklist'} size="xl">
      <div className="space-y-4 max-h-[70vh] overflow-y-auto">
        <div className="grid grid-cols-2 gap-3">
          <FormInput label="Nome"><input value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-3" data-testid="cl-nome" /></FormInput>
          <FormInput label="Disciplina">
            <select value={form.disciplina || ''} onChange={e => setForm({...form, disciplina: e.target.value})} className="input-industrial w-full px-3">
              <option value="">Selecionar</option>
              {DISCIPLINAS.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
            </select>
          </FormInput>
          <FormInput label="Categoria"><input value={form.categoria || ''} onChange={e => setForm({...form, categoria: e.target.value})} className="input-industrial w-full px-3" placeholder="Ex: preventiva, preditiva" /></FormInput>
          <FormInput label="Status">
            <select value={form.status} onChange={e => setForm({...form, status: e.target.value})} className="input-industrial w-full px-3">
              <option value="ativo">Ativo</option><option value="inativo">Inativo</option>
            </select>
          </FormInput>
        </div>
        <FormInput label="Descrição"><textarea value={form.descricao || ''} onChange={e => setForm({...form, descricao: e.target.value})} className="input-industrial w-full px-3 h-12" /></FormInput>
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-xs font-medium text-slate-400">Itens do Checklist</label>
            <button onClick={addItem} className="text-xs text-brand hover:text-brand-light flex items-center gap-1"><Plus size={14} /> Adicionar Item</button>
          </div>
          {form.itens.map((it, i) => (
            <div key={i} className="flex items-start gap-2 mb-2 bg-slate-800/50 rounded-lg p-2">
              <span className="text-brand font-bold text-sm mt-1 w-6 shrink-0">{it.ordem || i+1}</span>
              <input value={it.descricao} onChange={e => updateItem(i, 'descricao', e.target.value)} placeholder="Descrição do item" className="input-industrial flex-1 px-2 text-sm" />
              <select value={it.tipo || 'boolean'} onChange={e => updateItem(i, 'tipo', e.target.value)} className="input-industrial w-24 px-1 text-xs">
                {TIPOS_ITEM.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              {it.tipo === 'numero' && <>
                <input value={it.unidade || ''} onChange={e => updateItem(i, 'unidade', e.target.value)} placeholder="Un" className="input-industrial w-14 px-1 text-xs" />
                <input type="number" value={it.tolerancia_min ?? ''} onChange={e => updateItem(i, 'tolerancia_min', e.target.value ? parseFloat(e.target.value) : null)} placeholder="Mín" className="input-industrial w-16 px-1 text-xs" />
                <input type="number" value={it.tolerancia_max ?? ''} onChange={e => updateItem(i, 'tolerancia_max', e.target.value ? parseFloat(e.target.value) : null)} placeholder="Máx" className="input-industrial w-16 px-1 text-xs" />
              </>}
              <button onClick={() => removeItem(i)} className="text-red-400 hover:text-red-300 mt-1"><Trash2 size={14} /></button>
            </div>
          ))}
        </div>
        {item?.id && <FormInput label="Motivo da alteração (opcional)"><input value={form.motivo_alteracao || ''} onChange={e => setForm({...form, motivo_alteracao: e.target.value})} className="input-industrial w-full px-3" /></FormInput>}
      </div>
      <div className="flex gap-3 mt-4">
        <button onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="save-cl"><Save size={16} /> {saving ? 'Salvando...' : 'Salvar'}</button>
      </div>
    </Modal>
  );
};

// ===== MODELOS INSPEÇÃO TAB =====
const ModelosInspecaoTab = ({ items, procedimentos, segurancas, checklists, onRefresh, canEdit, editItem, setEditItem }) => {
  const [showForm, setShowForm] = useState(false);
  const [versionItem, setVersionItem] = useState(null);
  const handleDelete = async (id) => {
    if (!window.confirm('Excluir?')) return;
    try { await api.delete(`/doc-config/modelos-inspecao/${id}`); toast.success('Excluído'); onRefresh(); } catch { toast.error('Erro'); }
  };
  return (
    <div data-testid="modelos-inspecao-tab">
      <div className="flex justify-between items-center mb-4">
        <p className="text-xs text-slate-500">Modelos de inspeção por disciplina. Associam checklist, procedimento e segurança.</p>
        {canEdit && <button onClick={() => { setEditItem(null); setShowForm(true); }} className="btn-primary flex items-center gap-2" data-testid="new-modelo-insp"><Plus size={16} /> Novo Modelo</button>}
      </div>
      {items.length === 0 ? <EmptyState title="Nenhum modelo de inspeção" /> : (
        <div className="space-y-2">
          {items.map(m => (
            <div key={m.id} className="glass-card p-4 flex items-center justify-between" data-testid={`mi-${m.id}`}>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-primary">{m.nome}</span>
                  <span className="text-xs text-brand bg-brand/10 px-2 py-0.5 rounded">v{m.versao || 1}</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">{m.tipo || '-'} | {m.disciplina || '-'} | {m.checklist_snapshot ? 'CL' : ''} {m.procedimento_snapshot ? 'PROC' : ''} {m.seguranca_snapshot ? 'SEG' : ''}</p>
              </div>
              <div className="flex gap-2 items-center">
                <button onClick={() => setVersionItem(m)} className="text-xs text-slate-400 hover:text-amber-400 flex items-center gap-1"><History size={14} /> Versões</button>
                {canEdit && <button onClick={() => { setEditItem(m); setShowForm(true); }} className="text-xs text-blue-400 hover:text-blue-300">Editar</button>}
                {canEdit && <button onClick={() => handleDelete(m.id)} className="text-xs text-red-400 hover:text-red-300"><Trash2 size={14} /></button>}
              </div>
            </div>
          ))}
        </div>
      )}
      {showForm && <ModeloInspecaoForm item={editItem} procedimentos={procedimentos} segurancas={segurancas} checklists={checklists} onClose={() => setShowForm(false)} onSuccess={() => { setShowForm(false); onRefresh(); }} />}
      {versionItem && <VersionHistoryModal itemType="modelos-inspecao" itemId={versionItem.id} itemName={versionItem.nome} onClose={() => setVersionItem(null)} onRestore={() => { setVersionItem(null); onRefresh(); }} />}
    </div>
  );
};

const ModeloInspecaoForm = ({ item, procedimentos, segurancas, checklists, onClose, onSuccess }) => {
  const [form, setForm] = useState(item || { nome: '', tipo: '', disciplina: '', checklist_id: '', procedimento_id: '', seguranca_id: '', campos_obrigatorios: [], status: 'ativo' });
  const [saving, setSaving] = useState(false);
  const handleSave = async () => {
    if (!form.nome) { toast.error('Nome obrigatório'); return; }
    setSaving(true);
    try {
      const payload = {...form};
      if (item?.id) await api.put(`/doc-config/modelos-inspecao/${item.id}`, payload);
      else await api.post('/doc-config/modelos-inspecao', payload);
      toast.success('Modelo salvo'); onSuccess();
    } catch { toast.error('Erro ao salvar'); }
    setSaving(false);
  };
  return (
    <Modal isOpen onClose={onClose} title={item ? 'Editar Modelo de Inspeção' : 'Novo Modelo de Inspeção'} size="xl">
      <div className="space-y-4 max-h-[70vh] overflow-y-auto">
        <div className="grid grid-cols-2 gap-3">
          <FormInput label="Nome"><input value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-3" data-testid="mi-nome" /></FormInput>
          <FormInput label="Tipo">
            <select value={form.tipo || ''} onChange={e => setForm({...form, tipo: e.target.value})} className="input-industrial w-full px-3">
              <option value="">Selecionar</option>
              {DISCIPLINAS.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
            </select>
          </FormInput>
          <FormInput label="Disciplina">
            <select value={form.disciplina || ''} onChange={e => setForm({...form, disciplina: e.target.value})} className="input-industrial w-full px-3">
              <option value="">Selecionar</option>
              {DISCIPLINAS.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
            </select>
          </FormInput>
          <FormInput label="Status">
            <select value={form.status} onChange={e => setForm({...form, status: e.target.value})} className="input-industrial w-full px-3">
              <option value="ativo">Ativo</option><option value="inativo">Inativo</option>
            </select>
          </FormInput>
        </div>
        <FormInput label="Checklist associado">
          <select value={form.checklist_id || ''} onChange={e => setForm({...form, checklist_id: e.target.value, checklist_snapshot: null})} className="input-industrial w-full px-3">
            <option value="">Nenhum</option>
            {(checklists || []).map(c => <option key={c.id} value={c.id}>{c.nome} (v{c.versao})</option>)}
          </select>
        </FormInput>
        <FormInput label="Procedimento associado">
          <select value={form.procedimento_id || ''} onChange={e => setForm({...form, procedimento_id: e.target.value, procedimento_snapshot: null})} className="input-industrial w-full px-3">
            <option value="">Nenhum</option>
            {(procedimentos || []).map(p => <option key={p.id} value={p.id}>{p.nome} (v{p.versao})</option>)}
          </select>
        </FormInput>
        <FormInput label="Segurança associada">
          <select value={form.seguranca_id || ''} onChange={e => setForm({...form, seguranca_id: e.target.value, seguranca_snapshot: null})} className="input-industrial w-full px-3">
            <option value="">Nenhum</option>
            {(segurancas || []).map(s => <option key={s.id} value={s.id}>{s.nome} (v{s.versao})</option>)}
          </select>
        </FormInput>
        <FormInput label="Campos obrigatórios (separar por vírgula)">
          <input value={(form.campos_obrigatorios || []).join(', ')} onChange={e => setForm({...form, campos_obrigatorios: e.target.value.split(',').map(s => s.trim()).filter(Boolean)})} className="input-industrial w-full px-3" placeholder="Ex: resultado, observacoes, foto" />
        </FormInput>
        {item?.id && <FormInput label="Motivo da alteração"><input value={form.motivo_alteracao || ''} onChange={e => setForm({...form, motivo_alteracao: e.target.value})} className="input-industrial w-full px-3" /></FormInput>}
      </div>
      <div className="flex gap-3 mt-4">
        <button onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="save-mi"><Save size={16} /> {saving ? 'Salvando...' : 'Salvar'}</button>
      </div>
    </Modal>
  );
};

// ===== MODELOS OS TAB =====
const TIPOS_OS = ['preventiva', 'corretiva', 'lubrificacao', 'limpeza_organizacao', 'fabricacao_melhorias', 'preparacao_material', 'preditiva', 'melhoria'];

const ModelosOSTab = ({ items, procedimentos, segurancas, checklists, onRefresh, canEdit, editItem, setEditItem }) => {
  const [showForm, setShowForm] = useState(false);
  const [versionItem, setVersionItem] = useState(null);
  const handleDelete = async (id) => {
    if (!window.confirm('Excluir?')) return;
    try { await api.delete(`/doc-config/modelos-os/${id}`); toast.success('Excluído'); onRefresh(); } catch { toast.error('Erro'); }
  };
  return (
    <div data-testid="modelos-os-tab">
      <div className="flex justify-between items-center mb-4">
        <p className="text-xs text-slate-500">Modelos de OS por tipo de atividade. Associam procedimento, segurança e checklist padrão.</p>
        {canEdit && <button onClick={() => { setEditItem(null); setShowForm(true); }} className="btn-primary flex items-center gap-2" data-testid="new-modelo-os"><Plus size={16} /> Novo Modelo</button>}
      </div>
      {items.length === 0 ? <EmptyState title="Nenhum modelo de OS" /> : (
        <div className="space-y-2">
          {items.map(m => (
            <div key={m.id} className="glass-card p-4 flex items-center justify-between" data-testid={`mo-${m.id}`}>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-primary">{m.nome}</span>
                  <span className="text-xs text-brand bg-brand/10 px-2 py-0.5 rounded">v{m.versao || 1}</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">{m.tipo_os || '-'} | {m.disciplina || '-'} | Prio: {m.prioridade_padrao || 'media'}</p>
              </div>
              <div className="flex gap-2 items-center">
                <button onClick={() => setVersionItem(m)} className="text-xs text-slate-400 hover:text-amber-400 flex items-center gap-1"><History size={14} /> Versões</button>
                {canEdit && <button onClick={() => { setEditItem(m); setShowForm(true); }} className="text-xs text-blue-400 hover:text-blue-300">Editar</button>}
                {canEdit && <button onClick={() => handleDelete(m.id)} className="text-xs text-red-400 hover:text-red-300"><Trash2 size={14} /></button>}
              </div>
            </div>
          ))}
        </div>
      )}
      {showForm && <ModeloOSForm item={editItem} procedimentos={procedimentos} segurancas={segurancas} checklists={checklists} onClose={() => setShowForm(false)} onSuccess={() => { setShowForm(false); onRefresh(); }} />}
      {versionItem && <VersionHistoryModal itemType="modelos-os" itemId={versionItem.id} itemName={versionItem.nome} onClose={() => setVersionItem(null)} onRestore={() => { setVersionItem(null); onRefresh(); }} />}
    </div>
  );
};

const ModeloOSForm = ({ item, procedimentos, segurancas, checklists, onClose, onSuccess }) => {
  const [form, setForm] = useState(item || { nome: '', tipo_os: '', disciplina: '', prioridade_padrao: 'media', procedimento_id: '', seguranca_id: '', checklist_id: '', campos_obrigatorios: [], status: 'ativo' });
  const [saving, setSaving] = useState(false);
  const handleSave = async () => {
    if (!form.nome) { toast.error('Nome obrigatório'); return; }
    setSaving(true);
    try {
      if (item?.id) await api.put(`/doc-config/modelos-os/${item.id}`, form);
      else await api.post('/doc-config/modelos-os', form);
      toast.success('Modelo salvo'); onSuccess();
    } catch { toast.error('Erro ao salvar'); }
    setSaving(false);
  };
  return (
    <Modal isOpen onClose={onClose} title={item ? 'Editar Modelo de OS' : 'Novo Modelo de OS'} size="xl">
      <div className="space-y-4 max-h-[70vh] overflow-y-auto">
        <div className="grid grid-cols-2 gap-3">
          <FormInput label="Nome"><input value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-3" data-testid="mo-nome" /></FormInput>
          <FormInput label="Tipo de OS">
            <select value={form.tipo_os || ''} onChange={e => setForm({...form, tipo_os: e.target.value})} className="input-industrial w-full px-3">
              <option value="">Selecionar</option>
              {TIPOS_OS.map(t => <option key={t} value={t}>{t.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>)}
            </select>
          </FormInput>
          <FormInput label="Disciplina">
            <select value={form.disciplina || ''} onChange={e => setForm({...form, disciplina: e.target.value})} className="input-industrial w-full px-3">
              <option value="">Selecionar</option>
              {DISCIPLINAS.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
            </select>
          </FormInput>
          <FormInput label="Prioridade padrão">
            <select value={form.prioridade_padrao} onChange={e => setForm({...form, prioridade_padrao: e.target.value})} className="input-industrial w-full px-3">
              <option value="baixa">Baixa</option><option value="media">Média</option><option value="alta">Alta</option><option value="critica">Crítica</option>
            </select>
          </FormInput>
        </div>
        <FormInput label="Procedimento padrão">
          <select value={form.procedimento_id || ''} onChange={e => setForm({...form, procedimento_id: e.target.value, procedimento_snapshot: null})} className="input-industrial w-full px-3">
            <option value="">Nenhum</option>
            {(procedimentos || []).map(p => <option key={p.id} value={p.id}>{p.nome} (v{p.versao})</option>)}
          </select>
        </FormInput>
        <FormInput label="Segurança padrão">
          <select value={form.seguranca_id || ''} onChange={e => setForm({...form, seguranca_id: e.target.value, seguranca_snapshot: null})} className="input-industrial w-full px-3">
            <option value="">Nenhum</option>
            {(segurancas || []).map(s => <option key={s.id} value={s.id}>{s.nome} (v{s.versao})</option>)}
          </select>
        </FormInput>
        <FormInput label="Checklist padrão">
          <select value={form.checklist_id || ''} onChange={e => setForm({...form, checklist_id: e.target.value, checklist_snapshot: null})} className="input-industrial w-full px-3">
            <option value="">Nenhum</option>
            {(checklists || []).map(c => <option key={c.id} value={c.id}>{c.nome} (v{c.versao})</option>)}
          </select>
        </FormInput>
        <FormInput label="Campos obrigatórios (separar por vírgula)">
          <input value={(form.campos_obrigatorios || []).join(', ')} onChange={e => setForm({...form, campos_obrigatorios: e.target.value.split(',').map(s => s.trim()).filter(Boolean)})} className="input-industrial w-full px-3" placeholder="Ex: procedimento, seguranca, foto" />
        </FormInput>
        {item?.id && <FormInput label="Motivo da alteração"><input value={form.motivo_alteracao || ''} onChange={e => setForm({...form, motivo_alteracao: e.target.value})} className="input-industrial w-full px-3" /></FormInput>}
      </div>
      <div className="flex gap-3 mt-4">
        <button onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="save-mo"><Save size={16} /> {saving ? 'Salvando...' : 'Salvar'}</button>
      </div>
    </Modal>
  );
};

// ===== CAMPOS PERSONALIZADOS TAB =====
const TIPOS_CAMPO = ['texto_curto','texto_longo','numero','decimal','data','hora','data_hora','selecao_unica','multipla_selecao','checkbox','sim_nao','foto','assinatura','qr_code','url','email','telefone'];
const TIPO_LABELS = {texto_curto:'Texto curto',texto_longo:'Texto longo',numero:'Número',decimal:'Decimal',data:'Data',hora:'Hora',data_hora:'Data/hora',selecao_unica:'Seleção única',multipla_selecao:'Múltipla seleção',checkbox:'Checkbox',sim_nao:'Sim/Não',foto:'Foto',assinatura:'Assinatura',qr_code:'QR Code',url:'URL',email:'E-mail',telefone:'Telefone'};

const CamposTab = ({ items, onRefresh, canEdit }) => {
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [versionItem, setVersionItem] = useState(null);
  const handleDelete = async (id) => {
    if (!window.confirm('Excluir campo?')) return;
    try { await api.delete(`/doc-config/campos/${id}`); toast.success('Excluído'); onRefresh(); } catch { toast.error('Erro'); }
  };
  return (
    <div data-testid="campos-tab">
      <div className="flex justify-between items-center mb-4">
        <p className="text-xs text-slate-500">Campos personalizados por empresa. Aplicáveis a OS, Inspeções e Ativos.</p>
        {canEdit && <button onClick={() => { setEditItem(null); setShowForm(true); }} className="btn-primary flex items-center gap-2" data-testid="new-campo"><Plus size={16} /> Novo Campo</button>}
      </div>
      {items.length === 0 ? <EmptyState title="Nenhum campo personalizado" /> : (
        <div className="space-y-2">
          {items.map(c => (
            <div key={c.id} className="glass-card p-4 flex items-center justify-between" data-testid={`campo-${c.id}`}>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-primary">{c.nome}</span>
                  <span className="text-xs bg-slate-700 px-2 py-0.5 rounded">{c.identificador_tecnico}</span>
                  <span className="text-xs text-brand bg-brand/10 px-2 py-0.5 rounded">v{c.versao || 1}</span>
                  <span className="text-xs text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded">{TIPO_LABELS[c.tipo] || c.tipo}</span>
                  {c.obrigatorio && <span className="text-xs text-red-400">*</span>}
                </div>
                <p className="text-xs text-slate-500 mt-1">Módulos: {(c.aplicacao_modulos || []).join(', ') || 'todos'} | {c.unidade_medida || ''}</p>
              </div>
              <div className="flex gap-2 items-center">
                <button onClick={() => setVersionItem(c)} className="text-xs text-slate-400 hover:text-amber-400 flex items-center gap-1"><History size={14} /></button>
                {canEdit && <button onClick={() => { setEditItem(c); setShowForm(true); }} className="text-xs text-blue-400">Editar</button>}
                {canEdit && <button onClick={() => handleDelete(c.id)} className="text-xs text-red-400"><Trash2 size={14} /></button>}
              </div>
            </div>
          ))}
        </div>
      )}
      {showForm && <CampoForm item={editItem} onClose={() => setShowForm(false)} onSuccess={() => { setShowForm(false); onRefresh(); }} />}
      {versionItem && <VersionHistoryModal itemType="campos" itemId={versionItem.id} itemName={versionItem.nome} onClose={() => setVersionItem(null)} onRestore={() => { setVersionItem(null); onRefresh(); }} />}
    </div>
  );
};

const CampoForm = ({ item, onClose, onSuccess }) => {
  const [form, setForm] = useState(item || { nome:'',identificador_tecnico:'',tipo:'texto_curto',obrigatorio:false,valor_padrao:'',placeholder:'',texto_ajuda:'',ordem:0,status:'ativo',validacao_min:null,validacao_max:null,limite_caracteres:null,unidade_medida:'',casas_decimais:null,opcoes:[],aplicacao_modulos:[],aplicacao_tipos:[] });
  const [saving, setSaving] = useState(false);
  const needsOptions = ['selecao_unica','multipla_selecao'].includes(form.tipo);
  const needsNumeric = ['numero','decimal'].includes(form.tipo);
  const handleSave = async () => {
    if (!form.nome || !form.identificador_tecnico || !form.tipo) { toast.error('Nome, identificador e tipo são obrigatórios'); return; }
    setSaving(true);
    try {
      const payload = {...form, opcoes: (form.opcoes || []).map((o,i) => typeof o === 'string' ? {valor:o,label:o,ordem:i} : o)};
      if (item?.id) await api.put(`/doc-config/campos/${item.id}`, payload);
      else await api.post('/doc-config/campos', payload);
      toast.success('Campo salvo'); onSuccess();
    } catch (e) { toast.error(safeErrorMsg(e, 'Erro ao salvar')); }
    setSaving(false);
  };
  return (
    <Modal isOpen onClose={onClose} title={item ? 'Editar Campo' : 'Novo Campo Personalizado'} size="xl">
      <div className="space-y-4 max-h-[70vh] overflow-y-auto">
        <div className="grid grid-cols-2 gap-3">
          <FormInput label="Nome"><input value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-3" data-testid="campo-nome" /></FormInput>
          <FormInput label="Identificador técnico (imutável)"><input value={form.identificador_tecnico} onChange={e => setForm({...form, identificador_tecnico: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g,'')})} className="input-industrial w-full px-3" disabled={!!item?.id} placeholder="ex: temp_ambiente" data-testid="campo-ident" /></FormInput>
          <FormInput label="Tipo">
            <select value={form.tipo} onChange={e => setForm({...form, tipo: e.target.value})} className="input-industrial w-full px-3" data-testid="campo-tipo">
              {TIPOS_CAMPO.map(t => <option key={t} value={t}>{TIPO_LABELS[t]}</option>)}
            </select>
          </FormInput>
          <FormInput label="Ordem"><input type="number" value={form.ordem} onChange={e => setForm({...form, ordem: parseInt(e.target.value)||0})} className="input-industrial w-full px-3" /></FormInput>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <FormInput label="Placeholder"><input value={form.placeholder||''} onChange={e => setForm({...form, placeholder: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
          <FormInput label="Valor padrão"><input value={form.valor_padrao||''} onChange={e => setForm({...form, valor_padrao: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
        </div>
        <FormInput label="Texto de ajuda"><input value={form.texto_ajuda||''} onChange={e => setForm({...form, texto_ajuda: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
        {needsNumeric && <div className="grid grid-cols-3 gap-3">
          <FormInput label="Unidade"><input value={form.unidade_medida||''} onChange={e => setForm({...form, unidade_medida: e.target.value})} className="input-industrial w-full px-3" placeholder="°C, mm, kg" /></FormInput>
          <FormInput label="Mín"><input type="number" value={form.validacao_min??''} onChange={e => setForm({...form, validacao_min: e.target.value?parseFloat(e.target.value):null})} className="input-industrial w-full px-3" /></FormInput>
          <FormInput label="Máx"><input type="number" value={form.validacao_max??''} onChange={e => setForm({...form, validacao_max: e.target.value?parseFloat(e.target.value):null})} className="input-industrial w-full px-3" /></FormInput>
        </div>}
        {needsOptions && <FormInput label="Opções (uma por linha)">
          <textarea value={(form.opcoes||[]).map(o => typeof o === 'string' ? o : o.label || o.valor).join('\n')} onChange={e => setForm({...form, opcoes: e.target.value.split('\n').filter(Boolean).map((l,i) => ({valor:l.trim().toLowerCase().replace(/\s+/g,'_'),label:l.trim(),ordem:i}))})} className="input-industrial w-full px-3 h-20" placeholder="Opção 1&#10;Opção 2&#10;Opção 3" />
        </FormInput>}
        <div className="flex flex-wrap gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.obrigatorio} onChange={e => setForm({...form, obrigatorio: e.target.checked})} /> Obrigatório</label>
          {['os','inspecao','ativo'].map(m => (
            <label key={m} className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={(form.aplicacao_modulos||[]).includes(m)} onChange={e => { const mods = [...(form.aplicacao_modulos||[])]; e.target.checked ? mods.push(m) : mods.splice(mods.indexOf(m),1); setForm({...form, aplicacao_modulos: mods}); }} /> {m.toUpperCase()}</label>
          ))}
        </div>
        {item?.id && <FormInput label="Motivo da alteração"><input value={form.motivo_alteracao||''} onChange={e => setForm({...form, motivo_alteracao: e.target.value})} className="input-industrial w-full px-3" /></FormInput>}
      </div>
      <div className="flex gap-3 mt-4">
        <button onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="save-campo"><Save size={16} /> {saving ? 'Salvando...' : 'Salvar'}</button>
      </div>
    </Modal>
  );
};

// ===== CABEÇALHOS/RODAPÉS TAB =====
const CabecalhosTab = ({ items, onRefresh, canEdit }) => {
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [versionItem, setVersionItem] = useState(null);
  const handleDelete = async (id) => {
    if (!window.confirm('Excluir?')) return;
    try { await api.delete(`/doc-config/cabecalhos-rodapes/${id}`); toast.success('Excluído'); onRefresh(); } catch { toast.error('Erro'); }
  };
  return (
    <div data-testid="cabecalhos-tab">
      <div className="flex justify-between items-center mb-4">
        <p className="text-xs text-slate-500">Cabeçalhos e rodapés para documentos PDF. Configuráveis por empresa.</p>
        {canEdit && <button onClick={() => { setEditItem(null); setShowForm(true); }} className="btn-primary flex items-center gap-2" data-testid="new-cabecalho"><Plus size={16} /> Novo</button>}
      </div>
      {items.length === 0 ? <EmptyState title="Nenhum cabeçalho/rodapé" /> : (
        <div className="space-y-2">
          {items.map(c => (
            <div key={c.id} className="glass-card p-4 flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-primary">{c.nome}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${c.tipo === 'cabecalho' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'}`}>{c.tipo === 'cabecalho' ? 'Cabeçalho' : 'Rodapé'}</span>
                  <span className="text-xs text-brand bg-brand/10 px-2 py-0.5 rounded">v{c.versao || 1}</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">{c.razao_social || c.nome_fantasia || '-'} {c.cnpj ? `| ${c.cnpj}` : ''}</p>
              </div>
              <div className="flex gap-2 items-center">
                <button onClick={() => setVersionItem(c)} className="text-xs text-slate-400 hover:text-amber-400"><History size={14} /></button>
                {canEdit && <button onClick={() => { setEditItem(c); setShowForm(true); }} className="text-xs text-blue-400">Editar</button>}
                {canEdit && <button onClick={() => handleDelete(c.id)} className="text-xs text-red-400"><Trash2 size={14} /></button>}
              </div>
            </div>
          ))}
        </div>
      )}
      {showForm && <CabecalhoForm item={editItem} onClose={() => setShowForm(false)} onSuccess={() => { setShowForm(false); onRefresh(); }} />}
      {versionItem && <VersionHistoryModal itemType="cabecalhos-rodapes" itemId={versionItem.id} itemName={versionItem.nome} onClose={() => setVersionItem(null)} onRestore={() => { setVersionItem(null); onRefresh(); }} />}
    </div>
  );
};

const CabecalhoForm = ({ item, onClose, onSuccess }) => {
  const [form, setForm] = useState(item || { nome:'',tipo:'cabecalho',razao_social:'',nome_fantasia:'',cnpj:'',endereco:'',telefone:'',email:'',texto_personalizado:'',mostrar_paginacao:true,mostrar_data_emissao:true,mostrar_identificacao_doc:true,mostrar_versao:false });
  const [saving, setSaving] = useState(false);
  const handleSave = async () => {
    if (!form.nome) { toast.error('Nome obrigatório'); return; }
    setSaving(true);
    try {
      if (item?.id) await api.put(`/doc-config/cabecalhos-rodapes/${item.id}`, form);
      else await api.post('/doc-config/cabecalhos-rodapes', form);
      toast.success('Salvo'); onSuccess();
    } catch (e) { toast.error(safeErrorMsg(e)); }
    setSaving(false);
  };
  return (
    <Modal isOpen onClose={onClose} title={item ? 'Editar' : 'Novo Cabeçalho/Rodapé'} size="xl">
      <div className="space-y-4 max-h-[70vh] overflow-y-auto">
        <div className="grid grid-cols-2 gap-3">
          <FormInput label="Nome"><input value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-3" data-testid="cb-nome" /></FormInput>
          <FormInput label="Tipo">
            <select value={form.tipo} onChange={e => setForm({...form, tipo: e.target.value})} className="input-industrial w-full px-3">
              <option value="cabecalho">Cabeçalho</option><option value="rodape">Rodapé</option>
            </select>
          </FormInput>
          <FormInput label="Razão social"><input value={form.razao_social||''} onChange={e => setForm({...form, razao_social: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
          <FormInput label="Nome fantasia"><input value={form.nome_fantasia||''} onChange={e => setForm({...form, nome_fantasia: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
          <FormInput label="CNPJ"><input value={form.cnpj||''} onChange={e => setForm({...form, cnpj: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
          <FormInput label="Telefone"><input value={form.telefone||''} onChange={e => setForm({...form, telefone: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
          <FormInput label="E-mail"><input value={form.email||''} onChange={e => setForm({...form, email: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
          <FormInput label="Endereço"><input value={form.endereco||''} onChange={e => setForm({...form, endereco: e.target.value})} className="input-industrial w-full px-3" /></FormInput>
        </div>
        <FormInput label="Texto personalizado"><textarea value={form.texto_personalizado||''} onChange={e => setForm({...form, texto_personalizado: e.target.value})} className="input-industrial w-full px-3 h-12" /></FormInput>
        <div className="flex flex-wrap gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.mostrar_paginacao} onChange={e => setForm({...form, mostrar_paginacao: e.target.checked})} /> Paginação</label>
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.mostrar_data_emissao} onChange={e => setForm({...form, mostrar_data_emissao: e.target.checked})} /> Data/hora</label>
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.mostrar_identificacao_doc} onChange={e => setForm({...form, mostrar_identificacao_doc: e.target.checked})} /> ID documento</label>
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.mostrar_versao} onChange={e => setForm({...form, mostrar_versao: e.target.checked})} /> Versão</label>
        </div>
        {item?.id && <FormInput label="Motivo da alteração"><input value={form.motivo_alteracao||''} onChange={e => setForm({...form, motivo_alteracao: e.target.value})} className="input-industrial w-full px-3" /></FormInput>}
      </div>
      <div className="flex gap-3 mt-4">
        <button onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="save-cb"><Save size={16} /> {saving ? 'Salvando...' : 'Salvar'}</button>
      </div>
    </Modal>
  );
};

// ===== ASSINATURAS TAB =====
const AssinaturasTab = ({ items, onRefresh, canEdit }) => {
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [versionItem, setVersionItem] = useState(null);
  const handleDelete = async (id) => {
    if (!window.confirm('Excluir?')) return;
    try { await api.delete(`/doc-config/assinaturas/${id}`); toast.success('Excluído'); onRefresh(); } catch { toast.error('Erro'); }
  };
  return (
    <div data-testid="assinaturas-tab">
      <div className="flex justify-between items-center mb-4">
        <p className="text-xs text-slate-500">Blocos de assinatura para documentos. Nome, cargo, matrícula, captura digital.</p>
        {canEdit && <button onClick={() => { setEditItem(null); setShowForm(true); }} className="btn-primary flex items-center gap-2" data-testid="new-assinatura"><Plus size={16} /> Novo Bloco</button>}
      </div>
      {items.length === 0 ? <EmptyState title="Nenhum bloco de assinatura" /> : (
        <div className="space-y-2">
          {items.map(a => (
            <div key={a.id} className="glass-card p-4 flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-primary">{a.nome}</span>
                  <span className="text-xs bg-slate-700 px-2 py-0.5 rounded">{a.papel}</span>
                  <span className="text-xs text-brand bg-brand/10 px-2 py-0.5 rounded">v{a.versao || 1}</span>
                  {a.captura_digital && <span className="text-xs text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded">Digital</span>}
                </div>
                <p className="text-xs text-slate-500 mt-1">{(a.campos||[]).length} campos | {a.matricula_obrigatoria ? 'Matrícula obrig.' : ''}</p>
              </div>
              <div className="flex gap-2 items-center">
                <button onClick={() => setVersionItem(a)} className="text-xs text-slate-400 hover:text-amber-400"><History size={14} /></button>
                {canEdit && <button onClick={() => { setEditItem(a); setShowForm(true); }} className="text-xs text-blue-400">Editar</button>}
                {canEdit && <button onClick={() => handleDelete(a.id)} className="text-xs text-red-400"><Trash2 size={14} /></button>}
              </div>
            </div>
          ))}
        </div>
      )}
      {showForm && <AssinaturaForm item={editItem} onClose={() => setShowForm(false)} onSuccess={() => { setShowForm(false); onRefresh(); }} />}
      {versionItem && <VersionHistoryModal itemType="assinaturas" itemId={versionItem.id} itemName={versionItem.nome} onClose={() => setVersionItem(null)} onRestore={() => { setVersionItem(null); onRefresh(); }} />}
    </div>
  );
};

const AssinaturaForm = ({ item, onClose, onSuccess }) => {
  const CAMPOS_ASS = ['nome','cargo','matricula','data','papel','assinatura_imagem'];
  const [form, setForm] = useState(item || { nome:'',papel:'executor',campos:[{campo:'nome',obrigatorio:true,ordem:1},{campo:'cargo',obrigatorio:false,ordem:2},{campo:'data',obrigatorio:true,ordem:3}],matricula_obrigatoria:false,captura_digital:false,status:'ativo' });
  const [saving, setSaving] = useState(false);
  const toggleCampo = (campo) => {
    const exists = (form.campos||[]).find(c => c.campo === campo);
    if (exists) setForm({...form, campos: form.campos.filter(c => c.campo !== campo)});
    else setForm({...form, campos: [...form.campos, {campo, obrigatorio: false, ordem: form.campos.length+1}]});
  };
  const handleSave = async () => {
    if (!form.nome) { toast.error('Nome obrigatório'); return; }
    setSaving(true);
    try {
      if (item?.id) await api.put(`/doc-config/assinaturas/${item.id}`, form);
      else await api.post('/doc-config/assinaturas', form);
      toast.success('Salvo'); onSuccess();
    } catch (e) { toast.error(safeErrorMsg(e)); }
    setSaving(false);
  };
  return (
    <Modal isOpen onClose={onClose} title={item ? 'Editar Assinatura' : 'Novo Bloco de Assinatura'} size="lg">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <FormInput label="Nome"><input value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-3" data-testid="ass-nome" /></FormInput>
          <FormInput label="Papel">
            <select value={form.papel} onChange={e => setForm({...form, papel: e.target.value})} className="input-industrial w-full px-3">
              {['executor','supervisor','inspetor','aprovador','testemunha','responsavel'].map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase()+p.slice(1)}</option>)}
            </select>
          </FormInput>
        </div>
        <div>
          <label className="text-xs font-medium text-slate-400 mb-2 block">Campos do bloco</label>
          <div className="flex flex-wrap gap-2">
            {CAMPOS_ASS.map(c => (
              <label key={c} className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg cursor-pointer ${(form.campos||[]).find(x => x.campo===c) ? 'bg-brand/20 text-brand' : 'bg-slate-800 text-slate-400'}`}>
                <input type="checkbox" checked={!!(form.campos||[]).find(x => x.campo===c)} onChange={() => toggleCampo(c)} className="w-3 h-3" /> {c}
              </label>
            ))}
          </div>
        </div>
        <div className="flex gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.matricula_obrigatoria} onChange={e => setForm({...form, matricula_obrigatoria: e.target.checked})} /> Matrícula obrigatória</label>
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.captura_digital} onChange={e => setForm({...form, captura_digital: e.target.checked})} /> Captura digital (toque)</label>
        </div>
        {item?.id && <FormInput label="Motivo da alteração"><input value={form.motivo_alteracao||''} onChange={e => setForm({...form, motivo_alteracao: e.target.value})} className="input-industrial w-full px-3" /></FormInput>}
      </div>
      <div className="flex gap-3 mt-4">
        <button onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="save-ass"><Save size={16} /> {saving ? 'Salvando...' : 'Salvar'}</button>
      </div>
    </Modal>
  );
};

// ===== LAYOUTS TAB =====
const LayoutsTab = ({ items, cabecalhos, campos, assinaturas, onRefresh, canEdit }) => {
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [versionItem, setVersionItem] = useState(null);
  const handleDelete = async (id) => {
    if (!window.confirm('Excluir?')) return;
    try { await api.delete(`/doc-config/layouts/${id}`); toast.success('Excluído'); onRefresh(); } catch { toast.error('Erro'); }
  };
  return (
    <div data-testid="layouts-tab">
      <div className="flex justify-between items-center mb-4">
        <p className="text-xs text-slate-500">Perfis de layout que controlam blocos visíveis, ordem, cabeçalho/rodapé e campos nos documentos.</p>
        {canEdit && <button onClick={() => { setEditItem(null); setShowForm(true); }} className="btn-primary flex items-center gap-2" data-testid="new-layout"><Plus size={16} /> Novo Layout</button>}
      </div>
      {items.length === 0 ? <EmptyState title="Nenhum layout configurado" /> : (
        <div className="space-y-2">
          {items.map(l => (
            <div key={l.id} className="glass-card p-4 flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-primary">{l.nome}</span>
                  <span className="text-xs text-brand bg-brand/10 px-2 py-0.5 rounded">v{l.versao || 1}</span>
                  {l.tipo_documento && <span className="text-xs bg-slate-700 px-2 py-0.5 rounded">{l.tipo_documento}</span>}
                </div>
                <p className="text-xs text-slate-500 mt-1">{l.orientacao} | {(l.blocos_visiveis||[]).length} blocos | {(l.campos_personalizados_ids||[]).length} campos</p>
              </div>
              <div className="flex gap-2 items-center">
                <button onClick={() => setVersionItem(l)} className="text-xs text-slate-400 hover:text-amber-400"><History size={14} /></button>
                {canEdit && <button onClick={() => { setEditItem(l); setShowForm(true); }} className="text-xs text-blue-400">Editar</button>}
                {canEdit && <button onClick={() => handleDelete(l.id)} className="text-xs text-red-400"><Trash2 size={14} /></button>}
              </div>
            </div>
          ))}
        </div>
      )}
      {showForm && <LayoutForm item={editItem} cabecalhos={cabecalhos} campos={campos} assinaturas={assinaturas} onClose={() => setShowForm(false)} onSuccess={() => { setShowForm(false); onRefresh(); }} />}
      {versionItem && <VersionHistoryModal itemType="layouts" itemId={versionItem.id} itemName={versionItem.nome} onClose={() => setVersionItem(null)} onRestore={() => { setVersionItem(null); onRefresh(); }} />}
    </div>
  );
};

const BLOCOS = ['equipamento','informacoes','descricao','equipe','datas','procedimento','seguranca','materiais','observacoes','fotos','checklist','historico','assinaturas','campos_personalizados'];

const LayoutForm = ({ item, cabecalhos, campos, assinaturas, onClose, onSuccess }) => {
  const [form, setForm] = useState(item || { nome:'',tipo_documento:'',orientacao:'retrato',tamanho_pagina:'A4',cabecalho_id:'',rodape_id:'',blocos_visiveis:['equipamento','informacoes','descricao','procedimento','seguranca','fotos','assinaturas'],blocos_ocultos:[],campos_personalizados_ids:[],assinatura_ids:[],mostrar_fotos:true,mostrar_materiais:true,mostrar_historico:false,mostrar_checklist:true,mostrar_qr_code:true,colunas:1,status:'ativo' });
  const [saving, setSaving] = useState(false);
  const toggleBloco = (b) => {
    const vis = [...(form.blocos_visiveis||[])];
    if (vis.includes(b)) setForm({...form, blocos_visiveis: vis.filter(x => x !== b)});
    else setForm({...form, blocos_visiveis: [...vis, b]});
  };
  const handleSave = async () => {
    if (!form.nome) { toast.error('Nome obrigatório'); return; }
    setSaving(true);
    try {
      const payload = {...form, cabecalho_snapshot: null, rodape_snapshot: null};
      if (item?.id) await api.put(`/doc-config/layouts/${item.id}`, payload);
      else await api.post('/doc-config/layouts', payload);
      toast.success('Layout salvo'); onSuccess();
    } catch (e) { toast.error(safeErrorMsg(e)); }
    setSaving(false);
  };
  const cabs = (cabecalhos||[]).filter(c => c.tipo === 'cabecalho');
  const rods = (cabecalhos||[]).filter(c => c.tipo === 'rodape');
  return (
    <Modal isOpen onClose={onClose} title={item ? 'Editar Layout' : 'Novo Layout'} size="xl">
      <div className="space-y-4 max-h-[70vh] overflow-y-auto">
        <div className="grid grid-cols-2 gap-3">
          <FormInput label="Nome"><input value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-3" data-testid="layout-nome" /></FormInput>
          <FormInput label="Tipo de documento"><input value={form.tipo_documento||''} onChange={e => setForm({...form, tipo_documento: e.target.value})} className="input-industrial w-full px-3" placeholder="Ex: os_corretiva" /></FormInput>
          <FormInput label="Orientação">
            <select value={form.orientacao} onChange={e => setForm({...form, orientacao: e.target.value})} className="input-industrial w-full px-3">
              <option value="retrato">Retrato</option><option value="paisagem">Paisagem</option>
            </select>
          </FormInput>
          <FormInput label="Colunas">
            <select value={form.colunas} onChange={e => setForm({...form, colunas: parseInt(e.target.value)})} className="input-industrial w-full px-3">
              <option value={1}>1 coluna</option><option value={2}>2 colunas</option>
            </select>
          </FormInput>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <FormInput label="Cabeçalho">
            <select value={form.cabecalho_id||''} onChange={e => setForm({...form, cabecalho_id: e.target.value, cabecalho_snapshot: null})} className="input-industrial w-full px-3">
              <option value="">Padrão</option>
              {cabs.map(c => <option key={c.id} value={c.id}>{c.nome}</option>)}
            </select>
          </FormInput>
          <FormInput label="Rodapé">
            <select value={form.rodape_id||''} onChange={e => setForm({...form, rodape_id: e.target.value, rodape_snapshot: null})} className="input-industrial w-full px-3">
              <option value="">Padrão</option>
              {rods.map(r => <option key={r.id} value={r.id}>{r.nome}</option>)}
            </select>
          </FormInput>
        </div>
        <div>
          <label className="text-xs font-medium text-slate-400 mb-2 block">Blocos visíveis</label>
          <div className="flex flex-wrap gap-2">
            {BLOCOS.map(b => (
              <label key={b} className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg cursor-pointer ${(form.blocos_visiveis||[]).includes(b) ? 'bg-brand/20 text-brand' : 'bg-slate-800 text-slate-400'}`}>
                <input type="checkbox" checked={(form.blocos_visiveis||[]).includes(b)} onChange={() => toggleBloco(b)} className="w-3 h-3" /> {b}
              </label>
            ))}
          </div>
        </div>
        <div className="flex flex-wrap gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.mostrar_fotos} onChange={e => setForm({...form, mostrar_fotos: e.target.checked})} /> Fotos</label>
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.mostrar_materiais} onChange={e => setForm({...form, mostrar_materiais: e.target.checked})} /> Materiais</label>
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.mostrar_checklist} onChange={e => setForm({...form, mostrar_checklist: e.target.checked})} /> Checklist</label>
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.mostrar_qr_code} onChange={e => setForm({...form, mostrar_qr_code: e.target.checked})} /> QR Code</label>
          <label className="flex items-center gap-2 text-sm text-slate-400"><input type="checkbox" checked={form.mostrar_historico} onChange={e => setForm({...form, mostrar_historico: e.target.checked})} /> Histórico</label>
        </div>
        {item?.id && <FormInput label="Motivo da alteração"><input value={form.motivo_alteracao||''} onChange={e => setForm({...form, motivo_alteracao: e.target.value})} className="input-industrial w-full px-3" /></FormInput>}
      </div>
      <div className="flex gap-3 mt-4">
        <button onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="save-layout"><Save size={16} /> {saving ? 'Salvando...' : 'Salvar'}</button>
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
      toast.error(safeErrorMsg(e, 'Erro ao restaurar'));
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
    import('../lib/api').then(m => m.openAuthenticatedPdf(`/ordens-servico/${osId}/pdf?modo=${modo}`, (msg) => toast.error(msg)));
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
