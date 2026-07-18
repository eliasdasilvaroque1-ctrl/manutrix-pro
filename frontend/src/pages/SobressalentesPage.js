import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Edit, Trash2, Package, Tag, AlertTriangle, Download, Upload, ArrowLeft, Box, ChevronRight, Cog, Edit3, FileText, RefreshCw, Send, Wrench, Zap } from "lucide-react";
import { toast } from "sonner";
import { api, useAuth } from "@/lib/api";
import { normalizeError } from "@/lib/constants";
import { EmptyState, Loading, Modal, PageContainer, PageHeader, PageToolbar, SearchInput, FormInput, Select, ConfirmDialog } from "@/components/shared";
import ExportButtons from "@/components/widgets/ExportButtons";
import { MaterialThumbnail, MaterialImageModal, MaterialImageUploader } from "@/components/widgets/MaterialComponents";

const CONDICAO_CONFIG = {
  novo: { label: 'Novo', class: 'text-emerald-400 bg-brand-10' },
  reformado: { label: 'Reformado', class: 'text-blue-400 bg-blue-500/10' },
  em_reforma: { label: 'Em Reforma', class: 'text-amber-400 bg-amber-500/10' },
  reservado: { label: 'Reservado', class: 'text-purple-400 bg-purple-500/10' },
  instalado: { label: 'Instalado', class: 'text-cyan-400 bg-cyan-500/10' },
  descartado: { label: 'Descartado', class: 'text-red-400 bg-red-500/10' },
};
const ORIGEM_OPTIONS = [
  { value: 'compra_nova', label: 'Compra Nova' },
  { value: 'reforma_interna', label: 'Reforma Interna' },
  { value: 'reforma_externa', label: 'Reforma Externa' },
  { value: 'transferencia', label: 'Transferência' },
];

const SobressalentesPage = () => {
  const [spares, setSpares] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const [form, setForm] = useState({ descricao: '', modelo: '', fabricante: '', status: 'estoque', localizacao: '', custo: '', origem: '', condicoes: { novo: 0, reformado: 0, em_reforma: 0, reservado: 0, instalado: 0, descartado: 0 } });
  const [saving, setSaving] = useState(false);
  const [showReformaModal, setShowReformaModal] = useState(null);
  const [reformaForm, setReformaForm] = useState({ empresa_reparadora: '', data_envio: '', data_retorno: '', observacao: '', valor: '' });
  const [reformas, setReformas] = useState([]);
  const [viewImage, setViewImage] = useState(null);
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
      const payload = { ...form, custo: form.custo ? parseFloat(form.custo) : null };
      if (editItem) {
        await api.put(`/sobressalentes/${editItem.id}`, payload);
        toast.success('Sobressalente atualizado!');
      } else {
        await api.post('/sobressalentes', payload);
        toast.success('Sobressalente criado!');
      }
      setShowModal(false);
      setEditItem(null);
      setForm({ descricao: '', modelo: '', fabricante: '', status: 'estoque', localizacao: '', custo: '', origem: '', condicoes: { novo: 0, reformado: 0, em_reforma: 0, reservado: 0, instalado: 0, descartado: 0 } });
      fetchData();
    } catch (e) { toast.error(normalizeError(e)); }
    finally { setSaving(false); }
  };

  const handleExport = async (fmt) => {
    try {
      const res = await api.get(`/export/sobressalentes?format=${fmt}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `sobressalentes_export.${fmt === 'excel' ? 'xlsx' : 'pdf'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => { window.URL.revokeObjectURL(url); }, 10000);
      toast.success('Exportado com sucesso!');
    } catch { toast.error('Erro ao exportar'); }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/sobressalentes/${deleteItem.id}`);
      toast.success('Sobressalente excluído!');
      setDeleteItem(null);
      fetchData();
    } catch (error) { toast.error(normalizeError(error)); }
  };

  const handleEdit = (sp) => {
    setEditItem(sp);
    setForm({
      descricao: sp.descricao || '', modelo: sp.modelo || '', fabricante: sp.fabricante || '',
      status: sp.status || 'estoque', localizacao: sp.localizacao || '', custo: sp.custo ? String(sp.custo) : '',
      origem: sp.origem || '',
      condicoes: sp.condicoes || { novo: 0, reformado: 0, em_reforma: 0, reservado: 0, instalado: 0, descartado: 0 }
    });
    setShowModal(true);
  };

  const handleOpenReformas = async (sp) => {
    setShowReformaModal(sp);
    setReformaForm({ empresa_reparadora: '', data_envio: '', data_retorno: '', observacao: '', valor: '' });
    try {
      const res = await api.get(`/sobressalentes/${sp.id}/reformas`);
      setReformas(res.data);
    } catch { setReformas([]); }
  };

  const handleAddReforma = async () => {
    if (!reformaForm.empresa_reparadora) { toast.error('Empresa reparadora é obrigatória'); return; }
    try {
      await api.post(`/sobressalentes/${showReformaModal.id}/reformas`, {
        ...reformaForm, valor: reformaForm.valor ? parseFloat(reformaForm.valor) : null
      });
      toast.success('Reforma registrada!');
      setReformaForm({ empresa_reparadora: '', data_envio: '', data_retorno: '', observacao: '', valor: '' });
      const res = await api.get(`/sobressalentes/${showReformaModal.id}/reformas`);
      setReformas(res.data);
    } catch (e) { toast.error(normalizeError(e)); }
  };

  const updateCondicao = (key, val) => {
    const v = Math.max(0, parseInt(val) || 0);
    setForm(prev => ({ ...prev, condicoes: { ...prev.condicoes, [key]: v } }));
  };

  const totalCondicoes = Object.values(form.condicoes || {}).reduce((s, v) => s + (v || 0), 0);

  const filtered = search ? spares.filter(s => s.descricao?.toLowerCase().includes(search.toLowerCase()) || s.tag?.toLowerCase().includes(search.toLowerCase())) : spares;

  const statusConfig = {
    estoque: { class: 'bg-brand-10 text-emerald-400', label: 'Em Estoque' },
    em_uso: { class: 'bg-blue-500/10 text-blue-400', label: 'Em Uso' },
    em_reforma: { class: 'bg-amber-500/10 text-amber-400', label: 'Em Reforma' },
    descartado: { class: 'bg-red-500/10 text-red-400', label: 'Descartado' },
  };

  return (
    <PageContainer>
      <PageHeader title="Sobressalentes">
        <button onClick={() => handleExport('excel')} className="btn-secondary flex items-center gap-2 text-sm" data-testid="spare-export-excel"><Download size={16} /> Excel</button>
        <button onClick={() => handleExport('pdf')} className="btn-secondary flex items-center gap-2 text-sm" data-testid="spare-export-pdf"><FileText size={16} /> PDF</button>
        {['admin','master','pcm'].includes(user?.role) && (
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2" data-testid="add-spare-btn"><Plus size={20} /> Novo</button>
        )}
      </PageHeader>
      <PageToolbar>
        <SearchInput value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar sobressalente..." />
      </PageToolbar>
      {loading ? <Loading rows={5} /> : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((sp) => {
            const conds = sp.condicoes || {};
            const qtTotal = sp.quantidade_total || Object.values(conds).reduce((s, v) => s + (v || 0), 0);
            const activeConditions = Object.entries(conds).filter(([, v]) => v > 0);
            const origemLabel = ORIGEM_OPTIONS.find(o => o.value === sp.origem)?.label;
            return (
            <div key={sp.id} className="glass-card p-4 hover:border-slate-600 transition-all" data-testid={`spare-card-${sp.id}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex gap-3 flex-1 min-w-0">
                  <MaterialThumbnail
                    images={sp.images}
                    nome={sp.descricao}
                    categoria={sp.tipo_equipamento}
                    size="lg"
                    onClick={() => (sp.images || [])[0] && setViewImage({ src: sp.images[0], nome: sp.descricao })}
                  />
                  <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="font-mono text-brand text-sm">{sp.tag || sp.codigo}</span>
                    {origemLabel && <span className="text-xs px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">{origemLabel}</span>}
                    {qtTotal > 0 && <span className="text-xs font-semibold text-slate-200 bg-slate-700 px-1.5 py-0.5 rounded">Qtd: {qtTotal}</span>}
                  </div>
                  <p className="text-slate-100 font-medium">{sp.descricao}</p>
                  <p className="text-xs text-slate-500">{[sp.fabricante, sp.modelo, sp.localizacao].filter(Boolean).join(' · ')}</p>
                  {sp.ativo_vinculado && <p className="text-xs text-blue-400 mt-0.5">Ativo: {sp.ativo_vinculado.tag} - {sp.ativo_vinculado.nome}</p>}
                  {/* Condições breakdown */}
                  {activeConditions.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {activeConditions.map(([k, v]) => (
                        <span key={k} className={`text-xs px-1.5 py-0.5 rounded ${CONDICAO_CONFIG[k]?.class || 'text-slate-400 bg-slate-800'}`}>
                          {CONDICAO_CONFIG[k]?.label || k}: {v}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  {sp.custo > 0 && <p className="text-lg font-bold text-slate-200">R$ {sp.custo.toFixed(2)}</p>}
                  {['admin','master','pcm'].includes(user?.role) && (
                    <div className="flex items-center gap-1">
                      <button onClick={() => handleOpenReformas(sp)} className="p-2 hover:bg-amber-500/10 rounded-lg" title="Reformas" data-testid={`reforma-spare-${sp.id}`}><Wrench size={15} className="text-amber-400" /></button>
                      <button onClick={() => handleEdit(sp)} className="p-2 hover:bg-slate-700 rounded-lg" title="Editar" data-testid={`edit-spare-${sp.id}`}><Edit3 size={15} className="text-blue-400" /></button>
                      <button onClick={() => setDeleteItem(sp)} className="p-2 hover:bg-red-500/10 rounded-lg" title="Excluir" data-testid={`delete-spare-${sp.id}`}><Trash2 size={15} className="text-red-400" /></button>
                    </div>
                  )}
                </div>
              </div>
            </div>
            );
          })}
        </div>
      ) : <EmptyState icon={Cog} title="Nenhum sobressalente" description="Cadastre sobressalentes." />}

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditItem(null); }} title={editItem ? "Editar Sobressalente" : "Novo Sobressalente"} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormInput label="Descrição" required>
            <input value={form.descricao} onChange={(e) => setForm({...form, descricao: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: Redutor Falk 500" required />
          </FormInput>
          <div className="grid grid-cols-2 gap-4">
            <FormInput label="Fabricante"><input value={form.fabricante} onChange={(e) => setForm({...form, fabricante: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
            <FormInput label="Modelo"><input value={form.modelo} onChange={(e) => setForm({...form, modelo: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
            <FormInput label="Localização"><input value={form.localizacao} onChange={(e) => setForm({...form, localizacao: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: Almox A-01" /></FormInput>
            <FormInput label="Custo (R$)"><input type="number" step="0.01" value={form.custo} onChange={(e) => setForm({...form, custo: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
          </div>
          <FormInput label="Origem">
            <select value={form.origem} onChange={(e) => setForm({...form, origem: e.target.value})} className="input-industrial w-full px-4">
              <option value="">Selecione...</option>
              {ORIGEM_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </FormInput>
          {/* Condições por quantidade */}
          <div className="border-t border-slate-800 pt-3">
            <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider mb-2">Quantidade por Condição <span className="text-slate-300 normal-case">(Total: {totalCondicoes})</span></p>
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(CONDICAO_CONFIG).map(([key, cfg]) => (
                <div key={key} className="flex items-center gap-2">
                  <span className={`text-xs w-20 truncate ${cfg.class.split(' ')[0]}`}>{cfg.label}</span>
                  <input type="number" min="0" value={form.condicoes?.[key] || 0} onChange={(e) => updateCondicao(key, e.target.value)}
                    className="input-industrial w-16 px-2 text-center text-sm" data-testid={`condicao-${key}`} />
                </div>
              ))}
            </div>
          </div>
          {/* Identificação Visual */}
          {editItem && (
            <div className="border-t border-slate-800 pt-3">
              <MaterialImageUploader
                tipo="sobressalente"
                itemId={editItem.id}
                images={editItem.images}
                onUpdate={(imgs) => { editItem.images = imgs; }}
              />
            </div>
          )}
          <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Salvando...' : 'Salvar'}</button>
          </div>
        </form>
      </Modal>

      {/* Modal Histórico de Reformas */}
      <Modal isOpen={!!showReformaModal} onClose={() => setShowReformaModal(null)} title={`Reformas — ${showReformaModal?.tag || ''}`} size="lg">
        <div className="space-y-4">
          {['admin','master','pcm'].includes(user?.role) && (
            <div className="glass-card p-3 space-y-3">
              <p className="text-xs text-slate-500 uppercase font-semibold">Registrar Reforma</p>
              <div className="grid grid-cols-2 gap-3">
                <FormInput label="Empresa Reparadora" required>
                  <input value={reformaForm.empresa_reparadora} onChange={e => setReformaForm({...reformaForm, empresa_reparadora: e.target.value})} className="input-industrial w-full px-3 text-sm" data-testid="reforma-empresa" />
                </FormInput>
                <FormInput label="Valor (R$)">
                  <input type="number" step="0.01" value={reformaForm.valor} onChange={e => setReformaForm({...reformaForm, valor: e.target.value})} className="input-industrial w-full px-3 text-sm" />
                </FormInput>
                <FormInput label="Data Envio">
                  <input type="date" value={reformaForm.data_envio} onChange={e => setReformaForm({...reformaForm, data_envio: e.target.value})} className="input-industrial w-full px-3 text-sm" />
                </FormInput>
                <FormInput label="Data Retorno">
                  <input type="date" value={reformaForm.data_retorno} onChange={e => setReformaForm({...reformaForm, data_retorno: e.target.value})} className="input-industrial w-full px-3 text-sm" />
                </FormInput>
              </div>
              <FormInput label="Observação">
                <textarea value={reformaForm.observacao} onChange={e => setReformaForm({...reformaForm, observacao: e.target.value})} className="input-industrial w-full px-3 text-sm" rows={2} />
              </FormInput>
              <button onClick={handleAddReforma} className="btn-primary text-sm" data-testid="reforma-submit">Registrar</button>
            </div>
          )}
          {reformas.length > 0 ? (
            <div className="space-y-2">
              {reformas.map(r => (
                <div key={r.id} className="glass-card p-3 text-sm" data-testid={`reforma-item-${r.id}`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-slate-200 font-medium">{r.empresa_reparadora}</p>
                      <div className="flex gap-3 text-xs text-slate-500 mt-0.5">
                        {r.data_envio && <span>Envio: {new Date(r.data_envio + 'T00:00:00').toLocaleDateString('pt-BR')}</span>}
                        {r.data_retorno && <span>Retorno: {new Date(r.data_retorno + 'T00:00:00').toLocaleDateString('pt-BR')}</span>}
                        {r.valor && <span className="text-brand">R$ {r.valor.toFixed(2)}</span>}
                      </div>
                      {r.observacao && <p className="text-xs text-slate-400 mt-1">{r.observacao}</p>}
                      <p className="text-xs text-slate-600 mt-0.5">{r.usuario_nome} · {new Date(r.created_at).toLocaleString('pt-BR')}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : <p className="text-xs text-slate-600 text-center py-4">Nenhuma reforma registrada</p>}
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteItem}
        onClose={() => setDeleteItem(null)}
        onConfirm={handleDelete}
        title="Excluir Sobressalente"
        message={`Tem certeza que deseja excluir "${deleteItem?.tag} - ${deleteItem?.descricao}"?`}
        confirmText="Excluir"
        danger
      />
      {viewImage && <MaterialImageModal src={viewImage.src} nome={viewImage.nome} onClose={() => setViewImage(null)} />}
    </PageContainer>
  );
};


// ============== SOLICITAÇÃO DE SERVIÇO PAGE (OPERADOR) ==============

const SolicitacaoServicoPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [ativos, setAtivos] = useState([]);
  const [busca, setBusca] = useState('');
  const [selectedAtivo, setSelectedAtivo] = useState(null);
  const [form, setForm] = useState({ titulo: '', justificativa: '', prioridade: 'media', equipamento_parado: false });
  const [saving, setSaving] = useState(false);
  const [step, setStep] = useState(1); // 1=select ativo, 2=describe problem

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/ativos');
        setAtivos(res.data);
      } catch {}
    })();
  }, []);

  const filteredAtivos = busca.trim()
    ? ativos.filter(a => `${a.tag} ${a.nome}`.toLowerCase().includes(busca.toLowerCase()))
    : ativos.slice(0, 20);

  const handleSubmit = async () => {
    if (!selectedAtivo || !form.titulo.trim()) { toast.error('Preencha o equipamento e o problema'); return; }
    setSaving(true);
    try {
      const payload = {
        ativo_id: selectedAtivo.id,
        titulo: form.titulo.trim(),
        justificativa: form.justificativa.trim(),
        descricao: form.justificativa.trim(),
        prioridade: form.prioridade,
        tipo: 'corretiva',
        origem: 'operador',
        equipamento_parado: form.equipamento_parado,
      };
      const res = await api.post('/ordens-servico', payload);
      toast.success(`Solicitação #${res.data.numero} criada com sucesso!`);
      navigate('/');
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setSaving(false); }
  };

  return (
    <div className="space-y-4 animate-fadeInUp max-w-2xl mx-auto" data-testid="solicitar-servico-page">
      <div className="flex items-center gap-3">
        <button onClick={() => step === 1 ? navigate(-1) : setStep(1)} className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg">
          <ArrowLeft size={18} className="text-slate-400" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-slate-100">Nova Solicitação de Serviço</h1>
          <p className="text-xs text-slate-500">Descreva o problema encontrado</p>
        </div>
      </div>

      {/* Step indicator */}
      <div className="flex gap-2">
        <div className={`flex-1 h-1 rounded-full ${step >= 1 ? 'bg-brand' : 'bg-slate-800'}`} />
        <div className={`flex-1 h-1 rounded-full ${step >= 2 ? 'bg-brand' : 'bg-slate-800'}`} />
      </div>

      {step === 1 && (
        <div className="space-y-3" data-testid="solicitar-step1">
          <p className="text-sm text-slate-300 font-medium">Qual equipamento precisa de serviço?</p>
          <input value={busca} onChange={e => setBusca(e.target.value)} className="input-industrial w-full px-4"
            placeholder="Buscar por TAG ou nome..." data-testid="solicitar-busca-ativo" autoFocus />
          <div className="space-y-2 max-h-[50vh] overflow-y-auto">
            {filteredAtivos.map(a => (
              <button key={a.id} onClick={() => { setSelectedAtivo(a); setStep(2); }}
                className={`w-full glass-card p-4 text-left flex items-center gap-3 hover:border-brand transition-all ${selectedAtivo?.id === a.id ? 'border-brand bg-brand-10' : ''}`}
                data-testid={`solicitar-ativo-${a.id}`}>
                <div className="w-10 h-10 rounded-lg bg-brand-10 flex items-center justify-center shrink-0">
                  <Box size={18} className="text-brand" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1 text-[10px] text-slate-500 mb-0.5">
                    {a.sector?.nome && <span>{a.sector.nome}</span>}
                  </div>
                  <p className="text-sm font-mono text-brand font-bold">{a.tag}</p>
                  <p className="text-sm text-slate-200 truncate">{a.nome}</p>
                  <p className="text-[10px] text-slate-500">{a.tipo_equipamento || ''} {a.fabricante ? `• ${a.fabricante}` : ''}</p>
                </div>
                <ChevronRight size={16} className="text-slate-600 ml-auto shrink-0" />
              </button>
            ))}
          </div>
        </div>
      )}

      {step === 2 && selectedAtivo && (
        <div className="space-y-4" data-testid="solicitar-step2">
          {/* Selected ativo summary */}
          <div className="glass-card p-3 flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-brand-10 flex items-center justify-center shrink-0">
              <Box size={16} className="text-brand" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-mono text-brand font-bold">{selectedAtivo.tag}</p>
              <p className="text-xs text-slate-400">{selectedAtivo.nome}</p>
            </div>
            <button onClick={() => setStep(1)} className="text-xs text-brand ml-auto">Trocar</button>
          </div>

          <FormInput label="Qual o problema? *">
            <input value={form.titulo} onChange={e => setForm({...form, titulo: e.target.value})}
              className="input-industrial w-full px-4" placeholder="Ex: Vazamento na bomba, Iluminação queimada..."
              data-testid="solicitar-titulo" autoFocus />
          </FormInput>

          <FormInput label="Justificativa / Detalhes">
            <textarea value={form.justificativa} onChange={e => setForm({...form, justificativa: e.target.value})}
              className="input-industrial w-full px-4 py-3 min-h-[100px] resize-y"
              placeholder="Descreva o que você observou. Quando começou? Há risco de segurança? O equipamento parou?"
              data-testid="solicitar-justificativa" />
          </FormInput>

          <div className="grid grid-cols-2 gap-3">
            <FormInput label="Urgência">
              <select value={form.prioridade} onChange={e => setForm({...form, prioridade: e.target.value})}
                className="input-industrial w-full px-4" data-testid="solicitar-prioridade">
                <option value="baixa">Baixa — pode esperar</option>
                <option value="media">Média — próximos dias</option>
                <option value="alta">Alta — precisa logo</option>
                <option value="critica">Urgente — agora!</option>
              </select>
            </FormInput>
            <FormInput label="Equipamento Parado?">
              <div className="flex items-center gap-3 h-12">
                <button onClick={() => setForm({...form, equipamento_parado: true})}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-all ${form.equipamento_parado ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-slate-800 text-slate-400 border-slate-700'}`}
                  data-testid="solicitar-parado-sim">Sim</button>
                <button onClick={() => setForm({...form, equipamento_parado: false})}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-all ${!form.equipamento_parado ? 'bg-brand-20 text-brand border-brand-30' : 'bg-slate-800 text-slate-400 border-slate-700'}`}
                  data-testid="solicitar-parado-nao">Não</button>
              </div>
            </FormInput>
          </div>

          <button onClick={handleSubmit} disabled={saving || !form.titulo.trim()}
            className="w-full btn-primary py-4 text-lg font-bold flex items-center justify-center gap-2"
            data-testid="solicitar-enviar">
            <Send size={20} /> {saving ? 'Enviando...' : 'Enviar Solicitação'}
          </button>
        </div>
      )}
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
      } catch (err) { console.error(err); }
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
          <h1 className="text-2xl font-bold text-primary">Assistente Técnico IA</h1>
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
            <div className="w-20 h-20 rounded-full bg-brand-10 flex items-center justify-center mb-4"><Zap size={40} className="text-brand" /></div>
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


// ============== ADMIN TEMPLATES INSPEÇÃO ==============

const FIELD_TYPES = [
  { value: 'boolean', label: 'Conforme / Não Conforme' },
  { value: 'numerico', label: 'Número' },
  { value: 'temperatura', label: 'Temperatura' },
  { value: 'vibracao', label: 'Vibração' },
  { value: 'opcao', label: 'Opção (Bom/Regular/Ruim)' },
  { value: 'texto', label: 'Texto' },
  { value: 'observacao', label: 'Observação' },
];


// ============== PARADAS PROGRAMADAS ==============
const PARADA_TIPOS = [
  { value: 'preventiva', label: 'Preventiva' },
  { value: 'corretiva', label: 'Corretiva' },
  { value: 'grande_parada', label: 'Grande Parada' },
  { value: 'parada_geral', label: 'Parada Geral' },
];


export default SobressalentesPage;
export { SolicitacaoServicoPage, AssistentePage };
