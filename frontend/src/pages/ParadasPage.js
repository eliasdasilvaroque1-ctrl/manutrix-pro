import { useState, useEffect } from "react";
import { useNavigate, Navigate, useLocation } from "react-router-dom";
import { Plus, Clock, Calendar, Wrench, AlertTriangle, Filter, CheckCircle, XCircle, Activity, Edit, Trash2, Play, Pause, Target, ArrowLeft, Box, Building, ChevronRight, ClipboardCheck, Cog, Copy, Download, Edit3, Factory, FileText, Layers, List, Lock, MapPin, RefreshCw, Save, Search, Shield, Sparkles, Upload, User, X } from "lucide-react";
import { toast } from "sonner";
import { api, useAuth } from "../lib/api";
import { normalizeError, ROLE_LABELS } from "../lib/constants";
import { StatusBadge, PriorityBadge, EmptyState, Loading, Modal, PageContainer, PageHeader, PageToolbar, SearchInput, FormInput, Select, ConfirmDialog } from "../components/shared";
import ExportButtons from "../components/widgets/ExportButtons";

const PARADA_TIPOS = [
  { value: 'preventiva', label: 'Preventiva' },
  { value: 'corretiva', label: 'Corretiva' },
  { value: 'grande_parada', label: 'Grande Parada' },
  { value: 'parada_geral', label: 'Parada Geral' },
];

const FIELD_TYPES = [
  { value: 'boolean', label: 'Conforme / Não Conforme' },
  { value: 'numerico', label: 'Número' },
  { value: 'temperatura', label: 'Temperatura' },
  { value: 'vibracao', label: 'Vibração' },
  { value: 'opcao', label: 'Opção (Bom/Regular/Ruim)' },
  { value: 'texto', label: 'Texto' },
  { value: 'observacao', label: 'Observação' },
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
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-2">OS Vinculadas</h3>
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
    <PageContainer>
      <PageHeader title="Paradas Programadas" subtitle={`${paradas.length} parada(s)`}>
        {['admin','master','pcm'].includes(user?.role) && (
          <button onClick={() => { setEditItem(null); setForm({ area_id: '', data_inicio: '', data_fim: '', duracao_horas: '', tipo: 'preventiva', responsavel_id: '', descricao: '', observacoes: '', os_vinculadas: [] }); setShowModal(true); }} className="btn-primary flex items-center gap-2" data-testid="new-parada-btn"><Plus size={20} /> Nova Parada</button>
        )}
      </PageHeader>

      {paradas.length > 0 ? (
        <div className="space-y-2">
          {paradas.map(p => (
            <div key={p.id} className="glass-card p-4 cursor-pointer hover:border-slate-600" onClick={() => openDetail(p)} data-testid={`parada-card-${p.id}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-warning font-semibold">{p.numero}</span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-surface text-secondary capitalize">{p.tipo?.replace('_',' ')}</span>
                    <StatusBadge status={p.status} size="sm" />
                  </div>
                  <p className="text-primary">{p.descricao || p.area?.nome}</p>
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
      ) : <EmptyState icon={Calendar} title="Nenhuma parada" description="Crie paradas programadas para planejar manutenção." action={() => setShowModal(true)} actionLabel="Nova Parada" />}

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
    </PageContainer>
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
        // Save as master template (Biblioteca) — map field names to TemplateItemCreate schema
        const tipoMap = { conforme_nao_conforme: 'boolean', foto: 'observacao' };
        const payload = {
          nome: config.nome, tipo_equipamento: '',
          descricao: `Importado via Assistente — ${preview.metadata.total_perguntas} perguntas`,
          itens: preview.perguntas.map((p, i) => ({
            descricao: p.texto,
            tipo: tipoMap[p.tipo_campo] || p.tipo_campo || 'boolean',
            obrigatorio: p.obrigatorio !== false,
            unidade: p.unidade || '',
            tolerancia_min: p.limite_min ? parseFloat(p.limite_min) : null,
            tolerancia_max: p.limite_max ? parseFloat(p.limite_max) : null,
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
          <h1 className="text-2xl font-bold text-primary">Planos de Inspeção</h1>
          <p className="text-sm text-slate-500">Gerenciar perguntas por tipo de equipamento e por ativo</p>
        </div>
        <div className="flex gap-2">
          <ExportButtons entity="preventivas" />
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
        <EmptyState icon={ClipboardCheck} title="Nenhum plano" description="Crie planos de inspeção para cada tipo de equipamento" actionLabel="Novo Plano" action={openNew} />
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
      setTimeout(() => { window.URL.revokeObjectURL(url); }, 10000);
      toast.success('Exportado!');
    } catch { toast.error('Erro ao exportar'); }
  };

  const modules = ['auth', 'ativos', 'ordens_servico', 'inspecoes', 'estoque', 'sobressalentes', 'security'];
  const actions = ['login', 'create', 'update', 'delete', 'status_change', 'access_denied', 'duplicate'];
  const actionColors = {
    login: 'text-blue-400 bg-blue-500/10', create: 'text-emerald-400 bg-brand-10',
    update: 'text-amber-400 bg-amber-500/10', delete: 'text-red-400 bg-red-500/10',
    status_change: 'text-purple-400 bg-purple-500/10', access_denied: 'text-red-400 bg-red-500/20',
    duplicate: 'text-blue-400 bg-blue-500/10',
  };

  return (
    <PageContainer data-testid="auditoria-page">
      <PageHeader title="Auditoria" subtitle={stats ? `${stats.total} registros` : ''}>
        <button onClick={() => handleExport('excel')} className="btn-secondary text-sm flex items-center gap-1" data-testid="audit-export-excel"><Download size={14} /> Excel</button>
        <button onClick={() => handleExport('pdf')} className="btn-secondary text-sm flex items-center gap-1"><FileText size={14} /> PDF</button>
      </PageHeader>

      {stats && (
        <div className="flex gap-2 flex-wrap">
          {Object.entries(stats.by_module || {}).map(([mod, count]) => (
            <span key={mod} className="bg-surface text-secondary text-xs px-2 py-1 rounded">{mod}: {count}</span>
          ))}
        </div>
      )}

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
              <span className="text-xs text-slate-400 flex-1 truncate">{typeof log.details === 'string' ? log.details : (log.details == null ? '-' : JSON.stringify(log.details))}</span>
            </div>
          ))}
        </div>
      ) : <EmptyState icon={Shield} title="Nenhum registro" description="Logs de auditoria aparecerão aqui." />}
    </PageContainer>
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

  const roleLabels = ROLE_LABELS;
  const roleColors = { master: 'text-pink-400 bg-pink-500/10', admin: 'text-red-400 bg-red-500/10', gerente: 'text-purple-400 bg-purple-500/10', pcm: 'text-blue-400 bg-blue-500/10', supervisor: 'text-amber-400 bg-amber-500/10', tecnico: 'text-emerald-400 bg-brand-10', operador: 'text-teal-400 bg-teal-500/10', inspetor: 'text-cyan-400 bg-cyan-500/10', viewer: 'text-slate-400 bg-slate-500/10' };
  const disciplinaLabels = { mecanica: 'Mecânica', eletrica: 'Elétrica', instrumentacao: 'Instrumentação', operacao: 'Operação', civil: 'Civil', producao: 'Produção', lubrificacao: 'Lubrificação' };

  if (!['admin','master'].includes(user?.role)) return <EmptyState icon={Shield} title="Acesso Restrito" description="Apenas administradores podem gerenciar usuários." />;

  return (
    <PageContainer>
      <PageHeader title="Gestão de Usuários">
        <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2" data-testid="add-user-btn"><Plus size={20} /> Novo Usuário</button>
      </PageHeader>
      {loading ? <Loading rows={5} /> : (
        <div className="space-y-2">
          {users.map((u) => (
            <div key={u.id} className="glass-card p-4 flex items-center justify-between group">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-brand-20 flex items-center justify-center"><User size={20} className="text-brand" /></div>
                <div>
                  <p className="text-primary font-medium">{u.nome}</p>
                  <div className="flex items-center gap-2 text-xs text-secondary">
                    <span>{u.email}</span>
                    {u.disciplina_principal && <span className="bg-surface px-1.5 py-0.5 rounded capitalize">{disciplinaLabels[u.disciplina_principal] || u.disciplina_principal}</span>}
                    {u.turno && <span className="bg-surface px-1.5 py-0.5 rounded">Turno {u.turno}</span>}
                  </div>
                  {u.force_password_change && <span className="text-[10px] text-warning">Troca de senha pendente</span>}
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
                {value:'supervisor',label:'Supervisor'},{value:'tec_mecanico',label:'Técnico Mecânico'},{value:'tec_eletrico',label:'Técnico Elétrico'},{value:'instrumentista',label:'Instrumentista'},{value:'lubrificador',label:'Lubrificador'},{value:'operador',label:'Operador'},{value:'inspetor',label:'Inspetor'},{value:'visualizador',label:'Visualizador'}
              ]} />
            </FormInput>
            <FormInput label="Telefone"><input value={form.telefone} onChange={(e) => setForm({...form, telefone: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
          </div>
          <div className="glass-card p-3 text-xs text-slate-500">
            <p className="font-semibold text-slate-400 mb-1">Permissões por perfil:</p>
            <p><span className="text-red-400">Admin</span>: Controle total</p>
            <p><span className="text-purple-400">Gerente</span>: Dashboard e relatórios (somente leitura)</p>
            <p><span className="text-blue-400">PCM</span>: Gerencia OS, estoque, relatórios, exporta dados</p>
            <p><span className="text-brand">Técnico</span>: Preenche inspeções, solicita serviços</p>
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
    </PageContainer>
  );
};

// ============== EXPORT BUTTONS COMPONENT ==============

// ExportButtons → extracted to /components/widgets/ExportButtons.js

// ============== LAYOUT ==============

const ProtectedRoute = ({ children, allow }) => {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="min-h-screen bg-slate-950 flex items-center justify-center"><Cog size={48} className="text-brand animate-spin" /></div>;
  if (!user) return <Navigate to="/login" state={{ from: location.pathname + location.search }} replace />;
  if (allow && !allow.includes(user.role)) {
    return (
      <div>
        <div className="flex items-center justify-center min-h-[60vh]" data-testid="access-restricted">
          <div className="glass-card p-8 text-center max-w-md">
            <Shield size={48} className="text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-slate-100 mb-2">Acesso Restrito</h2>
            <p className="text-slate-400 text-sm mb-4">Seu perfil ({ROLE_LABELS[user.role] || user.role}) não possui permissão para acessar esta página.</p>
            <button onClick={() => window.history.back()} className="btn-primary text-sm">Voltar</button>
          </div>
        </div>
      </div>
    );
  }
  return children;
};

const CatchAllRedirect = () => {
  const { user } = useAuth();
  const isViewer = user?.role === 'visualizador' || user?.role === 'viewer';
  return <Navigate to={isViewer ? '/consulta' : '/'} replace />;
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
    <PageContainer>
      <PageHeader title="Áreas" subtitle={`${sectors.length} áreas cadastradas`} testId="setores-title">
        {['admin','master'].includes(user?.role) && (
          <button onClick={() => openModal()} className="btn-primary flex items-center gap-2" data-testid="add-sector-btn">
            <Plus size={20} /> Nova Área
          </button>
        )}
      </PageHeader>

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
    </PageContainer>
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
        <h1 className="text-2xl font-bold text-primary">Unidades</h1>
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


export default ParadasPage;
export { PlanImportWizard, AdminTemplatesPage, AuditoriaPage, AdminUsuariosPage, ProtectedRoute, CatchAllRedirect, SetoresPage, UnidadesPage };
