import { useState, useEffect, useRef, memo, useCallback } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  ClipboardCheck, Plus, Calendar, Clock, Activity, AlertTriangle, CheckCircle, XCircle,
  Search, Eye, Camera, ArrowLeft, MapPin, Play, Edit, Filter, ChevronDown, ChevronRight, Save,
  Box, Cog, Droplet, QrCode, RefreshCw, Shield, Sparkles, Target, Trash2, Upload, Wrench, X, Zap,
  AlertCircle, CheckCircle2
} from "lucide-react";
import { toast } from "sonner";
import { api, useAuth, BACKEND_URL } from "@/lib/api";
import { normalizeError } from "@/lib/constants";
import { queueOperation, queuePhoto } from "@/lib/offlineQueue";
import { StatusBadge, PriorityBadge, EmptyState, Loading, Modal, PageContainer, PageHeader, PageToolbar, SearchInput, FormInput, Select, ConfirmDialog } from "@/components/shared";
import ExportButtons from "@/components/widgets/ExportButtons";

const InspecoesPage = () => {
  const [inspecoes, setInspecoes] = useState([]);
  const [ativos, setAtivos] = useState([]);
  const [rotas, setRotas] = useState([]);
  const [tecnicos, setTecnicos] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [plantas, setPlantas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [deleteItem, setDeleteItem] = useState(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterArea, setFilterArea] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  
  useEffect(() => {
    if (searchParams.get('new') === 'true') setShowModal(true);
  }, [searchParams]);
  
  const fetchData = async () => {
    try {
      const [inspRes, ativosRes, rotasRes, tecnicosRes, sectorsRes, plantasRes] = await Promise.all([
        api.get('/inspecoes'),
        api.get('/ativos'),
        api.get('/rotas-inspecao'),
        api.get('/users/tecnicos'),
        api.get('/sectors'),
        api.get('/plantas').catch(() => ({ data: [] }))
      ]);
      setInspecoes(inspRes.data);
      setAtivos(ativosRes.data);
      setRotas(rotasRes.data);
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
      await api.delete(`/inspecoes/${deleteItem.id}`);
      toast.success('Inspeção excluída!');
      setDeleteItem(null);
      fetchData();
    } catch (error) {
      toast.error('Erro ao excluir');
    }
  };

  // I1 + I2: Filter logic
  const filteredInspecoes = inspecoes.filter(insp => {
    if (filterStatus && insp.status !== filterStatus) return false;
    if (filterArea && insp.ativo?.sector_id !== filterArea) return false;
    return true;
  });
  
  return (
    <PageContainer>
      <PageHeader title="Inspeções">
        <ExportButtons entity="inspecoes" />
        {user?.role !== 'visualizador' && user?.role !== 'gerente' && (
        <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2" data-testid="add-inspecao-btn">
          <Plus size={20} /> Nova Inspeção
        </button>
        )}
      </PageHeader>

      <PageToolbar>
        <div className="flex gap-1 overflow-x-auto hide-scrollbar">
          {[
            { value: '', label: 'Todas' },
            { value: 'pendente', label: 'Pendentes' },
            { value: 'em_andamento', label: 'Em Andamento' },
            { value: 'concluida', label: 'Concluídas' },
            { value: 'com_pendencias', label: 'Com Pendências' },
          ].map(f => (
            <button key={f.value} onClick={() => setFilterStatus(f.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${filterStatus === f.value ? 'bg-brand-20 text-brand border border-brand-30' : 'border border-surface text-secondary hover:text-primary'}`}
              data-testid={`insp-filter-status-${f.value || 'all'}`}
            >
              {f.label}
              {f.value && <span className="ml-1 text-secondary">({inspecoes.filter(i => i.status === f.value).length})</span>}
            </button>
          ))}
        </div>
        <select value={filterArea} onChange={(e) => setFilterArea(e.target.value)} className="input-industrial px-3 text-sm" data-testid="insp-filter-area">
          <option value="">Todas as Áreas</option>
          {sectors.map(s => <option key={s.id} value={s.id}>{s.nome}</option>)}
        </select>
        {(filterStatus || filterArea) && (
          <button onClick={() => { setFilterStatus(''); setFilterArea(''); }} className="text-xs text-secondary hover:text-brand" data-testid="insp-clear-filters">Limpar</button>
        )}
      </PageToolbar>

      <p className="text-xs text-secondary">{filteredInspecoes.length} inspeção(ões)</p>
      
      {loading ? <Loading rows={5} /> : filteredInspecoes.length > 0 ? (
        <div className="space-y-2">
          {filteredInspecoes.map((insp) => (
            <div key={insp.id} className="glass-card p-4 hover:border-slate-600 transition-all group">
              <div className="flex items-center justify-between">
                <div className="flex-1 cursor-pointer" onClick={() => navigate(`/inspecoes/${insp.id}`)}>
                  <div className="flex items-center gap-2 mb-1">
                    {insp.ativo && (
                      <div>
                        <div className="flex items-center gap-1 text-[10px] text-slate-500">
                          {plantas?.[0]?.nome && <span>{plantas[0].nome}</span>}
                          {plantas?.[0]?.nome && insp.ativo.sector?.nome && <span className="text-slate-600">›</span>}
                          {insp.ativo.sector?.nome && <span>{insp.ativo.sector.nome}</span>}
                        </div>
                        <span className="font-mono text-brand text-sm">{insp.ativo.tag}</span>
                        <span className="text-slate-400 text-xs ml-1">{insp.ativo.nome}</span>
                      </div>
                    )}
                    {insp.tipo === 'lubrificacao' ? (
                      <span className="text-xs px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded">Lubrificação</span>
                    ) : insp.frequencia ? (
                      <span className="text-xs px-2 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/30 rounded capitalize">{insp.frequencia}</span>
                    ) : null}
                  </div>
                  <p className="text-slate-100">
                    {insp.tipo === 'lubrificacao' 
                      ? `Lubrificação - ${insp.ativo?.nome || ''}` 
                      : insp.rota?.nome || `Inspeção ${insp.frequencia ? insp.frequencia.charAt(0).toUpperCase() + insp.frequencia.slice(1) : ''} - ${insp.ativo?.nome || ''}`
                    }
                  </p>
                  <p className="text-xs text-slate-500">
                    {new Date(insp.data_programada || insp.created_at).toLocaleDateString('pt-BR')} • {insp.responsavel?.nome}
                    {insp.tipo_lubrificante && ` • ${insp.tipo_lubrificante.replace(/_/g, ' ')}`}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {['admin','master','supervisor'].includes(user?.role) && (
                    <button onClick={() => setDeleteItem(insp)} className="p-2 hover:bg-red-500/10 rounded-lg opacity-0 group-hover:opacity-100" data-testid={`delete-inspecao-${insp.id}`}>
                      <Trash2 size={16} className="text-red-400" />
                    </button>
                  )}
                  <StatusBadge status={insp.status} size="sm" />
                  {insp.resultado && insp.resultado !== 'pendente' && (
                    <StatusBadge status={insp.resultado} size="sm" />
                  )}
                  <ChevronRight className="text-slate-600" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon={ClipboardCheck} title="Nenhuma inspeção encontrada" description={filterStatus || filterArea ? "Ajuste os filtros para ver resultados." : "Crie uma nova inspeção."} action={() => { if (!filterStatus && !filterArea) setShowModal(true); else { setFilterStatus(''); setFilterArea(''); } }} actionLabel={filterStatus || filterArea ? "Limpar Filtros" : "Nova Inspeção"} />
      )}
      
      <ModalNovaInspecao
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={fetchData}
        ativos={ativos}
        rotas={rotas}
        tecnicos={tecnicos}
        preSelectedAtivoId={searchParams.get('ativo') || null}
      />
      
      <ConfirmDialog
        isOpen={!!deleteItem}
        onClose={() => setDeleteItem(null)}
        onConfirm={handleDelete}
        title="Excluir Inspeção"
        message="Tem certeza que deseja excluir esta inspeção?"
        confirmText="Excluir"
        danger
      />
    </PageContainer>
  );
};

// Inspeção Detail / Execução
const InspecaoDetailPage = () => {
  const { id } = useParams();
  const [inspecao, setInspecao] = useState(null);
  const [checklist, setChecklist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [plantas, setPlantas] = useState([]);
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const fetchInspecao = async () => {
    try {
      const [response, plantasRes] = await Promise.all([
        api.get(`/inspecoes/${id}`),
        api.get('/plantas').catch(() => ({ data: [] }))
      ]);
      setInspecao(response.data);
      setChecklist(response.data.checklist || []);
      setPlantas(plantasRes.data);
    } catch (error) {
      toast.error('Inspeção não encontrada');
      navigate('/inspecoes');
    } finally {
      setLoading(false);
    }
  };
  
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchInspecao(); }, [id]);
  
  const handleItemChange = (itemId, field, value) => {
    setChecklist(prev => prev.map(item => 
      item.id === itemId ? { ...item, [field]: value } : item
    ));
  };
  
  const handleIniciar = async () => {
    try {
      if (!navigator.onLine) {
        await queueOperation({ method: 'POST', url: `/inspecoes/${id}/iniciar`, data: {}, priority: 2 });
        toast.info('Sem conexão — início da inspeção salvo para sincronizar');
        setInspecao(prev => prev ? { ...prev, status: 'em_andamento' } : prev);
      } else {
        await api.post(`/inspecoes/${id}/iniciar`);
        toast.success('Inspeção iniciada!');
        fetchInspecao();
      }
    } catch (error) {
      toast.error('Erro ao iniciar');
    }
  };
  
  const handleConcluir = async () => {
    const isItemFilled = (item) => {
      const t = item.tipo || 'boolean';
      if (t === 'boolean') return item.conforme !== null && item.conforme !== undefined;
      if (t === 'numero' || t === 'numerico') return item.resultado !== null && item.resultado !== undefined && item.resultado !== '';
      if (t === 'texto' || t === 'observacao') return item.resultado !== null && item.resultado !== undefined && item.resultado !== '';
      if (t === 'opcao' || t === 'temperatura' || t === 'vibracao') return item.resultado !== null && item.resultado !== undefined && item.resultado !== '';
      return item.resultado !== undefined;
    };
    const missing = checklist.filter(item => item.obrigatorio && !isItemFilled(item));
    if (missing.length > 0) {
      toast.error(`Preencha todos os itens obrigatórios (${missing.length} faltando)`);
      return;
    }
    
    setSubmitting(true);
    try {
      const concluirPayload = { checklist, observacoes: '' };
      if (!navigator.onLine) {
        await queueOperation({ method: 'POST', url: `/inspecoes/${id}/concluir`, data: concluirPayload, priority: 2 });
        toast.info('Sem conexão — conclusão da inspeção salva para sincronizar');
        navigate('/inspecoes');
      } else {
        const result = await api.post(`/inspecoes/${id}/concluir`, concluirPayload);
        if (result.data.os_gerada_id) {
          toast.warning(`Inspeção não conforme - OS gerada automaticamente`);
        } else {
          toast.success(`Inspeção concluída em ${result.data.duracao_minutos || 0} minutos!`);
        }
        navigate('/inspecoes');
      }
    } catch (error) {
      toast.error(normalizeError(error) || 'Erro ao concluir');
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) return <Loading rows={4} />;
  if (!inspecao) return null;
  
  const isFinished = ['concluida', 'com_pendencias'].includes(inspecao.status);
  const naoConformes = checklist.filter(i => i.conforme === false);
  const conformes = checklist.filter(i => i.conforme === true);
  
  return (
    <div className="space-y-4 pb-24" data-testid="inspecao-detail-page">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/inspecoes')} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg">
          <ArrowLeft size={20} className="text-slate-400" />
        </button>
        <div className="flex-1">
          {inspecao.ativo && (
            <div className="mb-1">
              <div className="flex items-center gap-1 text-[10px] text-slate-500">
                {plantas?.[0]?.nome && <span>{plantas[0].nome}</span>}
                {plantas?.[0]?.nome && inspecao.ativo.sector?.nome && <span className="text-slate-600">›</span>}
                {inspecao.ativo.sector?.nome && <span>{inspecao.ativo.sector.nome}</span>}
              </div>
              <span className="font-mono text-brand">{inspecao.ativo.tag}</span>
              <span className="text-slate-300 ml-2">{inspecao.ativo.nome}</span>
            </div>
          )}
          <h1 className="text-lg font-bold text-slate-100">
            {inspecao.tipo === 'lubrificacao' 
              ? `Lubrificação - ${inspecao.ativo?.nome || ''}`
              : inspecao.rota?.nome || `Inspeção ${inspecao.frequencia ? inspecao.frequencia.charAt(0).toUpperCase() + inspecao.frequencia.slice(1) : ''} - ${inspecao.ativo?.nome || ''}`
            }
          </h1>
        </div>
        <div className="flex items-center gap-2">
          {inspecao.tipo === 'lubrificacao' && (
            <span className="text-xs px-2 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded">Lubrificação</span>
          )}
          <StatusBadge status={inspecao.status} />
          {inspecao.resultado && inspecao.resultado !== 'pendente' && <StatusBadge status={inspecao.resultado} />}
        </div>
      </div>

      {/* Dados Gerais */}
      <div className="glass-card p-4" data-testid="inspecao-dados-gerais">
        <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider mb-2">Dados Gerais</p>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div><span className="text-slate-500">Tipo:</span> <span className="text-slate-200 capitalize">{inspecao.tipo}</span></div>
          {inspecao.frequencia && <div><span className="text-slate-500">Frequência:</span> <span className="text-slate-200 capitalize">{inspecao.frequencia}</span></div>}
          {inspecao.ativo?.tipo_equipamento && <div><span className="text-slate-500">Tipo Equip.:</span> <span className="text-slate-200">{inspecao.ativo.tipo_equipamento}</span></div>}
          {inspecao.ativo?.fabricante && <div><span className="text-slate-500">Fabricante:</span> <span className="text-slate-200">{inspecao.ativo.fabricante}</span></div>}
          {inspecao.ativo?.modelo && <div><span className="text-slate-500">Modelo:</span> <span className="text-slate-200">{inspecao.ativo.modelo}</span></div>}
          {inspecao.ativo?.numero_serie && <div><span className="text-slate-500">Série:</span> <span className="text-slate-200 font-mono">{inspecao.ativo.numero_serie}</span></div>}
          {inspecao.duracao_minutos && <div><span className="text-slate-500">Duração:</span> <span className="text-brand font-semibold">{inspecao.duracao_minutos} min</span></div>}
        </div>
      </div>
      
      {/* Lubrificação Info */}
      {inspecao.tipo === 'lubrificacao' && (inspecao.tipo_lubrificante || inspecao.ponto_lubrificacao) && (
        <div className="glass-card p-4 space-y-2 border-amber-500/30">
          <h3 className="text-sm font-semibold text-amber-400 flex items-center gap-2"><Droplet size={16} /> Dados da Lubrificação</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {inspecao.tipo_lubrificante && <div><span className="text-slate-500">Lubrificante:</span> <span className="text-slate-200 capitalize">{inspecao.tipo_lubrificante.replace(/_/g, ' ')}</span></div>}
            {inspecao.quantidade_lubrificante && <div><span className="text-slate-500">Quantidade:</span> <span className="text-slate-200">{inspecao.quantidade_lubrificante}</span></div>}
            {inspecao.ponto_lubrificacao && <div><span className="text-slate-500">Ponto:</span> <span className="text-slate-200">{inspecao.ponto_lubrificacao}</span></div>}
            {inspecao.metodo_aplicacao && <div><span className="text-slate-500">Método:</span> <span className="text-slate-200 capitalize">{inspecao.metodo_aplicacao}</span></div>}
          </div>
          {inspecao.observacoes_lubrificacao && <p className="text-xs text-slate-400 mt-2">{inspecao.observacoes_lubrificacao}</p>}
        </div>
      )}
      
      {/* Rastreabilidade e Executantes */}
      <div className="glass-card p-4 space-y-3" data-testid="inspecao-rastreabilidade">
        {inspecao.responsavel && (
          <div className="flex justify-between text-sm"><span className="text-slate-500">Responsável</span><span className="text-slate-200">{inspecao.responsavel.nome}</span></div>
        )}
        {(inspecao.executantes?.length > 0) && (
          <div className="text-sm">
            <span className="text-slate-500 block mb-1">Executantes</span>
            <div className="flex flex-wrap gap-1">
              {inspecao.executantes.map(uid => (
                <span key={uid} className="text-xs bg-slate-800 text-slate-300 px-2 py-1 rounded">{inspecao.executantes_nomes?.[uid] || uid}</span>
              ))}
            </div>
          </div>
        )}
        <div className="border-t border-slate-800 pt-2 space-y-2">
          <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider">Rastreabilidade</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
            <div><span className="text-slate-500">Criado por:</span> <span className="text-slate-300">{inspecao.criado_por_nome || '—'}</span></div>
            <div><span className="text-slate-500">Data criação:</span> <span className="text-slate-300">{inspecao.created_at ? new Date(inspecao.created_at).toLocaleString('pt-BR') : '—'}</span></div>
            <div><span className="text-slate-500">Iniciado por:</span> <span className="text-slate-300">{inspecao.iniciado_por_nome || '—'}</span></div>
            <div><span className="text-slate-500">Data início:</span> <span className="text-slate-300">{inspecao.data_inicio ? new Date(inspecao.data_inicio).toLocaleString('pt-BR') : '—'}</span></div>
            <div><span className="text-slate-500">Concluído por:</span> <span className="text-slate-300">{inspecao.concluido_por_nome || '—'}</span></div>
            <div><span className="text-slate-500">Data conclusão:</span> <span className="text-slate-300">{inspecao.data_conclusao ? new Date(inspecao.data_conclusao).toLocaleString('pt-BR') : '—'}</span></div>
            {inspecao.alterado_por_nome && (
              <>
                <div><span className="text-slate-500">Última alteração por:</span> <span className="text-amber-400">{inspecao.alterado_por_nome}</span></div>
                <div><span className="text-slate-500">Data alteração:</span> <span className="text-amber-400">{inspecao.updated_at ? new Date(inspecao.updated_at).toLocaleString('pt-BR') : '—'}</span></div>
              </>
            )}
          </div>
        </div>
      </div>
      
      {/* Observações */}
      {inspecao.observacoes && (
        <div className="glass-card p-4" data-testid="inspecao-observacoes">
          <p className="text-xs text-slate-500 mb-1">Observações</p>
          <p className="text-slate-200 whitespace-pre-wrap">{inspecao.observacoes}</p>
        </div>
      )}

      {inspecao.status === 'pendente' && !['pcm','gerente'].includes(user?.role) && (
        <button onClick={handleIniciar} className="btn-primary w-full flex items-center justify-center gap-2" data-testid="inspecao-iniciar-btn">
          <Play size={20} /> Iniciar Inspeção
        </button>
      )}
      
      {/* Checklist */}
      {inspecao.status !== 'pendente' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm text-slate-400">Checklist</h3>
            <div className="flex items-center gap-3 text-xs text-slate-500">
              {isFinished && <span className="text-brand">{conformes.length} conforme(s)</span>}
              {isFinished && naoConformes.length > 0 && <span className="text-red-400">{naoConformes.length} não conforme(s)</span>}
              <span>{checklist.filter(i => {
                const t = i.tipo || 'boolean';
                return t === 'boolean' ? (i.conforme !== null && i.conforme !== undefined) : (i.resultado !== null && i.resultado !== undefined && i.resultado !== '');
              }).length}/{checklist.length} respondidos</span>
            </div>
          </div>
          
          {checklist.map((item, idx) => {
            const itemTipo = item.tipo || 'boolean';
            const isNumeric = itemTipo === 'numero' || itemTipo === 'numerico' || itemTipo === 'temperatura' || itemTipo === 'vibracao';
            const isOption = itemTipo === 'opcao';
            const isText = itemTipo === 'texto' || itemTipo === 'observacao';
            const isBool = itemTipo === 'boolean';
            const isFilled = isBool ? (item.conforme !== null && item.conforme !== undefined) : (item.resultado !== null && item.resultado !== undefined && item.resultado !== '');
            return (
            <div key={item.id} className={`glass-card p-4 ${isFilled ? 'border-emerald-500/30' : ''}`}>
              <div className="flex items-start gap-3">
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                  isFilled ? 'bg-brand text-slate-950' : 'bg-slate-800 text-slate-400'
                }`}>{idx + 1}</span>
                <div className="flex-1">
                  <p className="text-sm text-slate-200">{item.descricao} {item.obrigatorio && <span className="text-red-400">*</span>}</p>
                  {item.unidade && <span className="text-xs text-slate-500">{item.unidade}</span>}
                  
                  {!isFinished && isBool && (
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={() => {
                          handleItemChange(item.id, 'resultado', true);
                          handleItemChange(item.id, 'conforme', true);
                        }}
                        className={`flex-1 py-3 rounded-lg border transition-all ${
                          item.conforme === true ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400' : 'border-slate-700 text-slate-400'
                        }`}
                      >
                        <CheckCircle size={20} className="mx-auto mb-1" />
                        Conforme
                      </button>
                      <button
                        onClick={() => {
                          handleItemChange(item.id, 'resultado', false);
                          handleItemChange(item.id, 'conforme', false);
                        }}
                        className={`flex-1 py-3 rounded-lg border transition-all ${
                          item.conforme === false ? 'bg-red-500/20 border-red-500 text-red-400' : 'border-slate-700 text-slate-400'
                        }`}
                      >
                        <XCircle size={20} className="mx-auto mb-1" />
                        Não Conforme
                      </button>
                    </div>
                  )}
                  
                  {!isFinished && isNumeric && (
                    <div className="mt-3 flex gap-2">
                      <input
                        type="number"
                        step="0.1"
                        value={item.resultado ?? ''}
                        onChange={(e) => {
                          const val = e.target.value === '' ? '' : parseFloat(e.target.value);
                          handleItemChange(item.id, 'resultado', val);
                          if (item.tolerancia_min !== undefined && item.tolerancia_max !== undefined && val !== '') {
                            handleItemChange(item.id, 'conforme', val >= item.tolerancia_min && val <= item.tolerancia_max);
                          }
                        }}
                        placeholder={item.tolerancia_min !== undefined ? `${item.tolerancia_min} - ${item.tolerancia_max}` : 'Valor'}
                        className="input-industrial flex-1 px-4"
                      />
                      {item.unidade && <span className="input-industrial px-4 flex items-center text-slate-400">{item.unidade}</span>}
                    </div>
                  )}
                  
                  {!isFinished && isOption && (
                    <div className="flex gap-2 mt-3 flex-wrap">
                      {['Bom', 'Regular', 'Ruim', 'Crítico'].map(opt => (
                        <button key={opt} onClick={() => {
                          handleItemChange(item.id, 'resultado', opt);
                          handleItemChange(item.id, 'conforme', opt === 'Bom' || opt === 'Regular');
                        }} className={`px-4 py-2 rounded-lg border text-sm transition-all ${
                          item.resultado === opt
                            ? (opt === 'Bom' || opt === 'Regular' ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400' : 'bg-red-500/20 border-red-500 text-red-400')
                            : 'border-slate-700 text-slate-400 hover:border-slate-500'
                        }`}>{opt}</button>
                      ))}
                    </div>
                  )}
                  
                  {!isFinished && isText && (
                    <textarea
                      value={item.resultado || ''}
                      onChange={(e) => handleItemChange(item.id, 'resultado', e.target.value)}
                      className="input-industrial w-full px-4 py-3 mt-3"
                      placeholder="Digite aqui..."
                      rows={2}
                    />
                  )}
                  
                  {isFinished && (
                    <div className="mt-2">
                      {isBool && <StatusBadge status={item.conforme ? 'conforme' : 'nao_conforme'} size="sm" />}
                      {isNumeric && item.resultado !== undefined && (
                        <span className={`text-sm ${item.conforme ? 'text-emerald-400' : 'text-red-400'}`}>
                          {item.resultado} {item.unidade}
                          {item.tolerancia_min !== undefined && <span className="text-xs text-slate-500 ml-2">(Faixa: {item.tolerancia_min} - {item.tolerancia_max})</span>}
                        </span>
                      )}
                      {isOption && item.resultado && (
                        <span className={`text-sm px-2 py-1 rounded ${item.conforme ? 'text-emerald-400 bg-brand-10' : 'text-red-400 bg-red-500/10'}`}>{item.resultado}</span>
                      )}
                      {isText && item.resultado && (
                        <p className="text-sm text-slate-300 bg-slate-800/50 rounded p-2 mt-1">{item.resultado}</p>
                      )}
                      {item.observacao && (
                        <p className="text-xs text-red-400/80 mt-1 bg-red-500/5 rounded p-2 border border-red-500/20">{item.observacao}</p>
                      )}
                    </div>
                  )}
                  
                  {!isFinished && item.conforme === false && isBool && (
                    <textarea
                      value={item.observacao || ''}
                      onChange={(e) => handleItemChange(item.id, 'observacao', e.target.value)}
                      placeholder="Descreva a não conformidade..."
                      className="input-industrial w-full px-4 py-3 mt-3 border-red-500/50"
                      rows={2}
                    />
                  )}
                </div>
              </div>
            </div>
            );
          })}
        </div>
      )}
      
      {/* Resultado */}
      {isFinished && inspecao.resultado && (
        <div className={`glass-card p-4 ${inspecao.resultado === 'conforme' ? 'border-emerald-500' : 'border-red-500'}`}>
          <div className="flex items-center gap-3">
            {inspecao.resultado === 'conforme' ? (
              <CheckCircle size={24} className="text-brand" />
            ) : (
              <XCircle size={24} className="text-red-400" />
            )}
            <div>
              <p className={`font-semibold ${inspecao.resultado === 'conforme' ? 'text-emerald-400' : 'text-red-400'}`}>
                {inspecao.resultado === 'conforme' ? 'Inspeção Conforme' : 'Inspeção Não Conforme'}
              </p>
              {inspecao.duracao_minutos && (
                <p className="text-xs text-slate-500">Duração: {inspecao.duracao_minutos} minutos</p>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* OS Geradas */}
      {(inspecao.os_vinculadas?.length > 0 || inspecao.os_gerada) && (
        <div className="glass-card p-4" data-testid="inspecao-os-geradas">
          <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wider mb-2 flex items-center gap-2">
            <Wrench size={16} /> OS Geradas ({inspecao.os_vinculadas?.length || (inspecao.os_gerada ? 1 : 0)})
          </h3>
          <div className="space-y-2">
            {(inspecao.os_vinculadas || (inspecao.os_gerada ? [inspecao.os_gerada] : [])).map(os => (
              <div key={os.id} className="flex items-center justify-between bg-slate-800/50 rounded-lg p-3 cursor-pointer hover:bg-slate-800" onClick={() => navigate(`/os/${os.id}`)}>
                <div>
                  <span className="font-mono text-amber-400">#{os.numero}</span>
                  <span className="text-slate-300 text-sm ml-2">{os.titulo}</span>
                </div>
                <div className="flex items-center gap-2">
                  {os.responsavel_nome && <span className="text-xs text-slate-500">{os.responsavel_nome}</span>}
                  <StatusBadge status={os.status} size="sm" />
                  <ChevronRight size={16} className="text-slate-600" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Registro Fotográfico */}
      {inspecao.id && (
        <div className="glass-card p-4">
          <PhotoUploader
            entityType="inspection"
            entityId={inspecao.id}
            label="Registro Fotográfico"
            required={checklist.some(i => i.conforme === false)}
          />
        </div>
      )}
      
      {/* Histórico Completo */}
      {inspecao.historico?.length > 0 && (
        <div className="glass-card p-4" data-testid="inspecao-historico">
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
            <Activity size={16} /> Histórico ({inspecao.historico.length})
          </h3>
          <div className="space-y-2">
            {inspecao.historico.map((h, idx) => (
              <div key={idx} className="flex items-start gap-3 text-sm border-l-2 border-slate-700 pl-3 py-1.5">
                <div className="flex-1">
                  <p className="text-slate-300">{h.details}</p>
                  <p className="text-xs text-slate-500">{h.user_name} · {new Date(h.created_at).toLocaleString('pt-BR')}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action */}
      {inspecao.status === 'em_andamento' && !['pcm','gerente'].includes(user?.role) && (
        <div className="fixed bottom-16 left-0 right-0 p-4 bg-slate-950/95 backdrop-blur-sm border-t border-slate-800 md:bottom-0">
          <button
            onClick={handleConcluir}
            disabled={submitting}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {submitting ? <RefreshCw size={20} className="animate-spin" /> : <CheckCircle size={20} />}
            {submitting ? 'Finalizando...' : 'Concluir Inspeção'}
          </button>
        </div>
      )}
    </div>
  );
};

// Ronda Page — Full inspection workflow: Área → Equipamento → Inspeção
const RondaPage = () => {
  const [areas, setAreas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedArea, setSelectedArea] = useState(null);
  const [areaDetail, setAreaDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [selectedAtivo, setSelectedAtivo] = useState(null);
  const [tipoInspecao, setTipoInspecao] = useState(null);
  const [templates, setTemplates] = useState({});
  const [checklist, setChecklist] = useState([]);
  const [executing, setExecuting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [photos, setPhotos] = useState([]);
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Step 1: Load areas
  useEffect(() => {
    const fetchAreas = async () => {
      try {
        const response = await api.get('/rondas');
        setAreas(response.data);
      } catch (error) {
        toast.error('Erro ao carregar áreas');
      } finally {
        setLoading(false);
      }
    };
    fetchAreas();
  }, []);
  
  // Step 2: Select area → load equipments
  const selectArea = async (areaId) => {
    setLoadingDetail(true);
    setSelectedArea(areaId);
    setSelectedAtivo(null);
    setTipoInspecao(null);
    setExecuting(false);
    try {
      const response = await api.get(`/ronda/${areaId}`);
      setAreaDetail(response.data);
    } catch (error) {
      toast.error(normalizeError(error));
    } finally {
      setLoadingDetail(false);
    }
  };
  
  // Step 3: Select equipment → load approved plans
  const selectAtivo = async (ativo) => {
    setSelectedAtivo(ativo);
    setTipoInspecao(null);
    setExecuting(false);
    setChecklist([]);
    setPhotos([]);
    // Load approved plans for this asset
    try {
      const res = await api.get(`/planos-inspecao/por-ativo/${ativo.id}`);
      setTemplates(res.data || []);
    } catch {
      setTemplates([]);
    }
  };
  
  // Step 4: Select plan → load checklist from plan
  const selectTipo = (plano) => {
    setTipoInspecao(plano);
    const perguntas = (plano.perguntas || []).map(p => ({
      id: p.id || String(Math.random()),
      descricao: p.texto || p.descricao || '',
      tipo: p.tipo_campo || p.tipo || 'boolean',
      obrigatorio: p.obrigatoria ?? p.obrigatorio ?? true,
      unidade: p.unidade || '',
      tolerancia_min: p.valor_min ?? p.tolerancia_min ?? null,
      tolerancia_max: p.valor_max ?? p.tolerancia_max ?? null,
      valor: null, conforme: null, observacao: ''
    }));
    setChecklist(perguntas);
    setExecuting(true);
  };
  
  // Update checklist item
  const updateChecklistItem = (itemId, field, value) => {
    setChecklist(prev => prev.map(item => 
      item.id === itemId ? {...item, [field]: value} : item
    ));
  };
  
  // Step 5: Submit inspection (linked to plan)
  const submitInspecao = async () => {
    const obrigatorios = checklist.filter(i => i.obrigatorio);
    const incompletos = obrigatorios.filter(i => i.tipo === 'boolean' && i.conforme === null);
    if (incompletos.length > 0) {
      toast.error(`${incompletos.length} item(ns) obrigatório(s) não preenchido(s)`);
      return;
    }
    
    setSubmitting(true);
    try {
      const payload = {
        ativo_id: selectedAtivo.id,
        plano_id: tipoInspecao.id,
        tipo: tipoInspecao.tipo || tipoInspecao.categoria || 'inspecao',
        disciplina: tipoInspecao.disciplina || null,
        responsavel_id: user?.id,
        checklist: checklist,
        observacoes: null,
      };
      
      if (!navigator.onLine) {
        await queueOperation({ method: 'POST', url: '/inspecoes', data: payload, priority: 1 });
        // Queue photos offline with a temporary entity ID
        const tempId = `offline_insp_${Date.now()}`;
        for (const photo of photos) {
          const arrayBuffer = await photo.arrayBuffer();
          await queuePhoto({ entityType: 'inspection', entityId: tempId, categoria: 'foto', blob: arrayBuffer, filename: photo.name });
        }
        toast.info(`Sem conexão — inspeção${photos.length ? ` + ${photos.length} foto(s)` : ''} salva para sincronizar`);
      } else {
        const res = await api.post('/inspecoes', payload);
        for (const photo of photos) {
          const formData = new FormData();
          formData.append('file', photo);
          formData.append('entity_type', 'inspection');
          formData.append('entity_id', res.data.id);
          await api.post('/attachments', formData, { headers: { 'Content-Type': 'multipart/form-data' } }).catch(() => {});
        }
        toast.success('Inspeção concluída!');
      }
      
      // Reset to equipment list
      setExecuting(false);
      setTipoInspecao(null);
      setSelectedAtivo(null);
      setChecklist([]);
      setPhotos([]);
      // Refresh area detail
      if (selectedArea) selectArea(selectedArea);
    } catch (error) {
      toast.error(normalizeError(error));
    } finally {
      setSubmitting(false);
    }
  };
  
  const handleCameraCapture = (file) => {
    setPhotos(prev => [...prev, file]);
    setShowCamera(false);
    toast.success('Foto capturada!');
  };
  
  // Back navigation
  const goBack = () => {
    if (executing) { setExecuting(false); setTipoInspecao(null); }
    else if (selectedAtivo) { setSelectedAtivo(null); }
    else if (selectedArea) { setSelectedArea(null); setAreaDetail(null); }
  };
  
  if (loading) return <Loading rows={4} />;
  
  // Camera overlay
  if (showCamera) return <CameraCapture onCapture={handleCameraCapture} onClose={() => setShowCamera(false)} />;
  
  return (
    <div className="space-y-4" data-testid="ronda-page">
      {/* Header with breadcrumb */}
      <div className="flex items-center gap-3">
        {(selectedArea || selectedAtivo || executing) && (
          <button onClick={goBack} className="p-2 rounded-lg hover:bg-slate-800 transition-all" data-testid="ronda-back-btn">
            <ArrowLeft size={20} className="text-slate-400" />
          </button>
        )}
        <div>
          <h1 className="text-2xl font-bold text-primary flex items-center gap-2">
            <Target size={24} className="text-brand" /> Modo Ronda
          </h1>
          <p className="text-sm text-slate-500">
            {!selectedArea && 'Selecione uma área para iniciar'}
            {selectedArea && !selectedAtivo && `${areaDetail?.area_nome || ''} — Selecione o equipamento`}
            {selectedAtivo && !executing && `${selectedAtivo.tag} — Planos disponíveis`}
            {executing && `${selectedAtivo.tag} — ${tipoInspecao?.nome || 'Execução'}`}
          </p>
        </div>
      </div>
      
      {/* STEP 1: Area list */}
      {!selectedArea && (
        <div className="space-y-3" data-testid="ronda-areas">
          {areas.length === 0 ? (
            <EmptyState icon={Target} title="Nenhuma área cadastrada" description="Cadastre áreas para iniciar rondas" />
          ) : areas.map(({ area, total_ativos, inspecoes_pendentes }) => (
            <div
              key={area.id}
              className="glass-card p-4 cursor-pointer hover:border-brand transition-all active:scale-[0.99]"
              onClick={() => selectArea(area.id)}
              data-testid={`ronda-area-${area.codigo || area.id}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: (area.cor || '#10b981') + '20' }}>
                    <MapPin size={20} style={{ color: area.cor || '#10b981' }} />
                  </div>
                  <div>
                    <p className="text-slate-100 font-semibold">{area.nome}</p>
                    <p className="text-sm text-slate-500">{total_ativos} equipamentos</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {inspecoes_pendentes > 0 && (
                    <span className="bg-amber-500/20 text-amber-400 text-xs font-medium px-2 py-1 rounded-full">{inspecoes_pendentes} pendente{inspecoes_pendentes > 1 ? 's' : ''}</span>
                  )}
                  <ChevronRight className="text-slate-600" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* STEP 2: Equipment list */}
      {selectedArea && !selectedAtivo && (
        <div className="space-y-3" data-testid="ronda-equipamentos">
          {loadingDetail ? <Loading rows={3} /> : (
            areaDetail?.ativos?.length === 0 ? (
              <EmptyState icon={Box} title="Nenhum equipamento nesta área" description="Cadastre ativos para esta área" />
            ) : areaDetail?.ativos?.map(({ ativo, ultima_inspecao, tem_pendente, ordem }) => (
              <div
                key={ativo.id}
                className="glass-card p-4 cursor-pointer hover:border-brand transition-all active:scale-[0.99]"
                onClick={() => selectAtivo(ativo)}
                data-testid={`ronda-ativo-${ativo.tag}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-600 font-mono w-6">{ordem}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-brand text-sm">{ativo.tag}</span>
                        {tem_pendente && <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />}
                      </div>
                      <p className="text-slate-200 text-sm">{ativo.nome}</p>
                      <p className="text-xs text-slate-500">{selectedArea?.nome} · {ativo.tipo_equipamento}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    {ultima_inspecao ? (
                      <div className="text-xs text-slate-500">
                        <p>Última: {ultima_inspecao.tipo}</p>
                        <p>{new Date(ultima_inspecao.created_at).toLocaleDateString('pt-BR')}</p>
                      </div>
                    ) : (
                      <span className="text-xs text-amber-400">Nunca inspecionado</span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
      
      {/* STEP 3: Plan selection (from approved plans) */}
      {selectedAtivo && !executing && (
        <div className="space-y-4" data-testid="ronda-tipo-inspecao">
          <div className="glass-card p-4">
            <div className="flex items-center gap-3 mb-2">
              <span className="font-mono text-brand">{selectedAtivo.tag}</span>
              <span className="text-slate-200">{selectedAtivo.nome}</span>
            </div>
            <p className="text-xs text-slate-500">{selectedAtivo.tipo_equipamento} {selectedAtivo.fabricante ? `• ${selectedAtivo.fabricante}` : ''}</p>
          </div>
          
          <p className="text-sm text-slate-400 font-medium">Planos disponíveis para execução:</p>
          
          {Array.isArray(templates) && templates.length > 0 ? (
            <div className="grid grid-cols-1 gap-3">
              {templates.map(plano => {
                const tipoIcons = { mecanica: Cog, eletrica: Zap, lubrificacao: Droplet, preventiva: Shield, inspecao: ClipboardCheck, limpeza: Sparkles };
                const tipoColors = { mecanica: '#10b981', eletrica: '#3b82f6', lubrificacao: '#f59e0b', preventiva: '#8b5cf6', inspecao: '#10b981', limpeza: '#06b6d4' };
                const Icon = tipoIcons[plano.tipo] || tipoIcons[plano.disciplina] || ClipboardCheck;
                const color = tipoColors[plano.tipo] || tipoColors[plano.disciplina] || '#64748b';
                return (
                  <button
                    key={plano.id}
                    onClick={() => selectTipo(plano)}
                    className="glass-card p-5 text-left hover:border-brand transition-all active:scale-[0.99] flex items-center gap-4"
                    data-testid={`ronda-plano-${plano.id}`}
                  >
                    <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ backgroundColor: color + '20' }}>
                      <Icon size={24} style={{ color }} />
                    </div>
                    <div className="flex-1">
                      <p className="text-slate-100 font-semibold">{plano.nome}</p>
                      <p className="text-xs text-slate-500">{(plano.perguntas || []).length} perguntas • v{plano.versao || 1}</p>
                    </div>
                    <ChevronRight className="text-slate-600" />
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="glass-card p-8 text-center">
              <ClipboardCheck size={40} className="text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400 font-medium">Nenhum plano aprovado</p>
              <p className="text-xs text-slate-600 mt-1">O PCM precisa criar e aprovar planos para este ativo.</p>
            </div>
          )}
        </div>
      )}
      
      {/* STEP 4: Execute checklist */}
      {executing && (
        <div className="space-y-4" data-testid="ronda-checklist">
          <div className="glass-card p-3 flex items-center justify-between">
            <div>
              <span className="font-mono text-brand text-sm">{selectedAtivo.tag}</span>
              <span className="text-slate-400 text-sm ml-2">{selectedAtivo.nome}</span>
            </div>
            <span className="text-xs bg-slate-800 px-2 py-1 rounded">{tipoInspecao?.nome || ''}</span>
          </div>
          
          {/* Checklist items */}
          <div className="space-y-2">
            {checklist.map((item, idx) => (
              <div key={item.id} className="glass-card p-4 space-y-2" data-testid={`checklist-item-${idx}`}>
                <div className="flex items-start gap-2">
                  <span className="text-xs text-slate-600 font-mono w-6 pt-0.5">{idx + 1}</span>
                  <div className="flex-1">
                    <p className="text-sm text-slate-200">{item.descricao} {item.obrigatorio && <span className="text-red-400">*</span>}</p>
                    
                    {/* Boolean type: OK / NOK */}
                    {item.tipo === 'boolean' && (
                      <div className="flex gap-2 mt-2">
                        <button onClick={() => updateChecklistItem(item.id, 'conforme', true)} className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${item.conforme === true ? 'bg-brand-20 text-brand border border-emerald-500/50' : 'bg-slate-800/50 text-slate-500 border border-slate-700'}`}>
                          <CheckCircle size={16} className="inline mr-1" /> OK
                        </button>
                        <button onClick={() => updateChecklistItem(item.id, 'conforme', false)} className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${item.conforme === false ? 'bg-red-500/20 text-red-400 border border-red-500/50' : 'bg-slate-800/50 text-slate-500 border border-slate-700'}`}>
                          <XCircle size={16} className="inline mr-1" /> NOK
                        </button>
                      </div>
                    )}
                    
                    {/* Numeric type */}
                    {item.tipo === 'numerico' && (
                      <div className="flex items-center gap-2 mt-2">
                        <input type="number" step="0.1" value={item.valor || ''} onChange={(e) => updateChecklistItem(item.id, 'valor', e.target.value)} className="input-industrial flex-1 px-3 py-2 text-sm" placeholder={`${item.tolerancia_min || ''}${item.tolerancia_min ? ' - ' : ''}${item.tolerancia_max || ''} ${item.unidade || ''}`} />
                        {item.unidade && <span className="text-xs text-slate-500">{item.unidade}</span>}
                      </div>
                    )}
                    
                    {/* Option type */}
                    {item.tipo === 'opcao' && (
                      <div className="flex gap-1 mt-2 flex-wrap">
                        {['Bom', 'Regular', 'Ruim'].map(opt => (
                          <button key={opt} onClick={() => updateChecklistItem(item.id, 'valor', opt)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${item.valor === opt ? (opt === 'Bom' ? 'bg-brand-20 text-brand border border-emerald-500/50' : opt === 'Regular' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50' : 'bg-red-500/20 text-red-400 border border-red-500/50') : 'bg-slate-800/50 text-slate-500 border border-slate-700'}`}>
                            {opt}
                          </button>
                        ))}
                      </div>
                    )}
                    
                    {/* Text type */}
                    {item.tipo === 'texto' && (
                      <textarea value={item.valor || ''} onChange={(e) => updateChecklistItem(item.id, 'valor', e.target.value)} className="input-industrial w-full px-3 py-2 mt-2 text-sm min-h-[60px]" placeholder="Observações..." />
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* Photo capture */}
          <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-400"><Camera size={14} className="inline mr-1" /> Fotos ({photos.length})</p>
              <button onClick={() => setShowCamera(true)} className="btn-secondary text-sm flex items-center gap-1" data-testid="ronda-camera-btn">
                <Camera size={16} /> Tirar Foto
              </button>
            </div>
            {photos.length > 0 && (
              <div className="flex gap-2 flex-wrap">
                {photos.map((p, i) => (
                  <div key={i} className="w-16 h-16 rounded-lg overflow-hidden bg-slate-800">
                    <img src={URL.createObjectURL(p)} alt="" className="w-full h-full object-cover" />
                  </div>
                ))}
              </div>
            )}
          </div>
          
          {/* Submit */}
          <button onClick={submitInspecao} disabled={submitting} className="btn-primary w-full py-4 text-lg font-semibold flex items-center justify-center gap-2" data-testid="ronda-submit-btn">
            {submitting ? <><RefreshCw size={20} className="animate-spin" /> Salvando...</> : <><CheckCircle size={20} /> Concluir Inspeção</>}
          </button>
        </div>
      )}
    </div>
  );
};

// Scanner Page — Mobile-first QR scanner with jsQR fallback
const ScannerPage = () => {
  const [manualCode, setManualCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const scanningRef = useRef(false);
  const navigate = useNavigate();
  
  const resolveScannedValue = async (value) => {
    // Portal URL pattern: /portal/equipamento/{id} or /portal/tecnico/{id}
    const portalMatch = value.match(/\/portal\/equipamento\/([a-f0-9-]+)/i);
    if (portalMatch) { navigate(`/portal/tecnico/${portalMatch[1]}`); return; }
    const ativoMatch = value.match(/\/ativos\/([a-f0-9-]+)/i);
    if (ativoMatch) { navigate(`/portal/tecnico/${ativoMatch[1]}`); return; }
    try {
      const r = await api.get(`/ativos/qr/${encodeURIComponent(value)}`);
      navigate(`/portal/tecnico/${r.data.id}`); return;
    } catch {}
    try {
      const r = await api.get(`/ativos/tag/${value.toUpperCase()}`);
      navigate(`/ativos/${r.data.id}`); return;
    } catch {}
    toast.error('Ativo não encontrado para este código');
  };

  const handleSearch = async () => {
    if (!manualCode.trim()) return;
    setLoading(true);
    try { await resolveScannedValue(manualCode.trim()); }
    finally { setLoading(false); }
  };

  const startCamera = async () => {
    setCameraError('');
    setScanning(true);
    scanningRef.current = true;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      
      // Try native BarcodeDetector first
      if ('BarcodeDetector' in window) {
        const detector = new window.BarcodeDetector({ formats: ['qr_code'] });
        const scanNative = async () => {
          if (!scanningRef.current || !videoRef.current) return;
          try {
            const barcodes = await detector.detect(videoRef.current);
            if (barcodes.length > 0) {
              stopCamera();
              toast.success('QR Code detectado!');
              await resolveScannedValue(barcodes[0].rawValue);
              return;
            }
          } catch {}
          if (scanningRef.current) requestAnimationFrame(scanNative);
        };
        videoRef.current.onloadedmetadata = () => scanNative();
      } else {
        // Fallback: jsQR library
        const jsQR = (await import('jsqr')).default;
        const canvas = canvasRef.current;
        const ctx = canvas?.getContext('2d');
        const scanJsQR = () => {
          if (!scanningRef.current || !videoRef.current || !ctx) return;
          const video = videoRef.current;
          if (video.readyState === video.HAVE_ENOUGH_DATA) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const code = jsQR(imageData.data, imageData.width, imageData.height, { inversionAttempts: 'dontInvert' });
            if (code) {
              stopCamera();
              toast.success('QR Code detectado!');
              resolveScannedValue(code.data);
              return;
            }
          }
          if (scanningRef.current) requestAnimationFrame(scanJsQR);
        };
        setTimeout(scanJsQR, 500);
      }
    } catch (err) {
      setCameraError('Não foi possível acessar a câmera. Verifique as permissões.');
      setScanning(false);
    }
  };

  const stopCamera = () => {
    scanningRef.current = false;
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    setScanning(false);
  };

  useEffect(() => { return () => { scanningRef.current = false; stopCamera(); }; }, []);

  // Auto-start camera on mount for quick field use
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { startCamera(); }, []);
  
  return (
    <div className="space-y-4" data-testid="scanner-page">
      <h1 className="text-2xl font-bold text-primary flex items-center gap-3">
        <QrCode size={28} className="text-brand" /> Identificar Ativo
      </h1>
      
      {scanning ? (
        <div className="glass-card p-3 space-y-3">
          <div className="relative rounded-xl overflow-hidden bg-black aspect-[4/3]">
            <video ref={videoRef} className="w-full h-full object-cover" playsInline muted />
            <canvas ref={canvasRef} className="hidden" />
            {/* Scan overlay */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="w-52 h-52 relative">
                <div className="absolute top-0 left-0 w-8 h-8 border-t-3 border-l-3 border-brand rounded-tl-lg" />
                <div className="absolute top-0 right-0 w-8 h-8 border-t-3 border-r-3 border-brand rounded-tr-lg" />
                <div className="absolute bottom-0 left-0 w-8 h-8 border-b-3 border-l-3 border-brand rounded-bl-lg" />
                <div className="absolute bottom-0 right-0 w-8 h-8 border-b-3 border-r-3 border-brand rounded-br-lg" />
                <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-brand animate-pulse" />
              </div>
            </div>
            <div className="absolute bottom-3 left-3 right-3 text-center">
              <p className="text-xs text-white/80 bg-black/50 rounded-full px-3 py-1 inline-block">Aponte para o QR Code do equipamento</p>
            </div>
          </div>
          {cameraError && <p className="text-sm text-amber-400 text-center">{cameraError}</p>}
          <button onClick={stopCamera} className="btn-secondary w-full flex items-center justify-center gap-2" data-testid="stop-camera-btn">
            <X size={20} /> Fechar Câmera
          </button>
        </div>
      ) : (
        <div className="glass-card p-8 flex flex-col items-center justify-center gap-4">
          <div className="w-20 h-20 rounded-full bg-brand-10 flex items-center justify-center">
            <Camera size={40} className="text-brand" />
          </div>
          <p className="text-sm text-slate-500">Câmera fechada</p>
          <button onClick={startCamera} className="btn-primary flex items-center gap-2" data-testid="open-camera-btn">
            <Camera size={20} /> Abrir Câmera
          </button>
        </div>
      )}
      
      <div className="flex items-center gap-4">
        <div className="flex-1 h-px bg-slate-800" />
        <span className="text-slate-500 text-sm">ou buscar por TAG</span>
        <div className="flex-1 h-px bg-slate-800" />
      </div>
      
      <div className="glass-card p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={manualCode}
            onChange={(e) => setManualCode(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Ex: BOM-001"
            className="input-industrial flex-1 px-4 font-mono text-lg"
            data-testid="manual-search-input"
          />
          <button onClick={handleSearch} disabled={loading} className="btn-primary px-6" data-testid="manual-search-btn">
            {loading ? <RefreshCw size={20} className="animate-spin" /> : <Search size={20} />}
          </button>
        </div>
      </div>
    </div>
  );
};


// ============== PHOTO UPLOADER COMPONENT ==============

const PhotoUploader = ({ entityType, entityId, categoria = 'foto', label = 'Fotos', required = false, onPhotoCountChange }) => {
  const [photos, setPhotos] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [fullscreenImg, setFullscreenImg] = useState(null);
  const fileInputRef = useRef(null);

  const fetchPhotos = async () => {
    if (!entityId) return;
    try {
      const res = await api.get(`/attachments/${entityType}/${entityId}`);
      const filtered = categoria ? res.data.filter(a => a.categoria === categoria) : res.data;
      setPhotos(filtered);
      onPhotoCountChange?.(filtered.length);
    } catch (err) { console.error(err); }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchPhotos(); }, [entityId, entityType]);

  const handleUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    setUploading(true);
    try {
      if (!navigator.onLine) {
        // Store photos in IndexedDB for later sync
        for (const file of files) {
          const arrayBuffer = await file.arrayBuffer();
          await queuePhoto({
            entityType,
            entityId,
            categoria,
            blob: arrayBuffer,
            filename: file.name || `photo_${Date.now()}.jpg`,
          });
        }
        toast.info(`${files.length} foto(s) salva(s) offline — serão enviadas ao reconectar`);
      } else {
        for (const file of files) {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('entity_type', entityType);
          formData.append('entity_id', entityId);
          formData.append('categoria', categoria);
          await api.post('/attachments', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
        }
        toast.success(`${files.length} foto(s) enviada(s)`);
        fetchPhotos();
      }
    } catch (e) {
      toast.error('Erro ao enviar foto');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/attachments/${id}`);
      fetchPhotos();
    } catch { toast.error('Erro ao remover'); }
  };

  return (
    <>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-slate-400 flex items-center gap-2">
            <Camera size={16} /> {label} {required && <span className="text-red-400">*</span>}
            {photos.length > 0 && <span className="text-xs text-slate-600">({photos.length})</span>}
          </h4>
        </div>

        {/* Photo Grid */}
        {photos.length > 0 && (
          <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
            {photos.map((p) => (
              <div key={p.id} className="relative group aspect-square rounded-lg overflow-hidden bg-slate-800 border border-slate-700">
                <img
                  src={`${BACKEND_URL}${p.file_url}`}
                  alt={p.filename}
                  className="w-full h-full object-cover cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => setFullscreenImg(`${BACKEND_URL}${p.file_url}`)}
                />
                <button
                  onClick={() => handleDelete(p.id)}
                  className="absolute top-1 right-1 p-1 bg-red-500/80 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X size={12} className="text-white" />
                </button>
                <p className="absolute bottom-0 left-0 right-0 bg-black/60 text-[10px] text-slate-300 px-1 py-0.5 truncate">
                  {new Date(p.created_at).toLocaleDateString('pt-BR')}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Upload Button */}
        <label className={`flex items-center justify-center gap-2 p-3 border-2 border-dashed rounded-lg cursor-pointer transition-all ${
          required && photos.length === 0 ? 'border-red-500/50 hover:border-red-400 bg-red-500/5' : 'border-slate-700 hover:border-brand hover:bg-brand-10'
        }`}>
          {uploading ? (
            <><RefreshCw size={18} className="animate-spin text-slate-400" /> <span className="text-sm text-slate-400">Enviando...</span></>
          ) : (
            <><Camera size={18} className="text-slate-500" /> <span className="text-sm text-slate-400">Tirar foto ou selecionar arquivo</span></>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            multiple
            onChange={handleUpload}
            className="hidden"
            disabled={uploading}
          />
        </label>
        {required && photos.length === 0 && (
          <p className="text-xs text-red-400">Foto obrigatória</p>
        )}
      </div>

      {/* Fullscreen Viewer */}
      {fullscreenImg && (
        <div className="fixed inset-0 z-[200] bg-black/95 flex items-center justify-center p-4" onClick={() => setFullscreenImg(null)}>
          <button className="absolute top-4 right-4 p-2 bg-slate-800 rounded-full" onClick={() => setFullscreenImg(null)}>
            <X size={24} className="text-white" />
          </button>
          <img src={fullscreenImg} alt="Fullscreen" className="max-w-full max-h-full object-contain rounded-lg" />
        </div>
      )}
    </>
  );
};


// ============== CAMERA CAPTURE ==============

const CameraCapture = ({ onCapture, onClose }) => {
  const videoRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const startCamera = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
        });
        setStream(mediaStream);
        if (videoRef.current) videoRef.current.srcObject = mediaStream;
      } catch (err) {
        setError('Não foi possível acessar a câmera. Verifique as permissões.');
      }
    };
    startCamera();
    return () => { if (stream) stream.getTracks().forEach(t => t.stop()); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const takePhoto = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    canvas.getContext('2d').drawImage(videoRef.current, 0, 0);
    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `foto_${Date.now()}.jpg`, { type: 'image/jpeg' });
        onCapture(file);
      }
    }, 'image/jpeg', 0.85);
    if (stream) stream.getTracks().forEach(t => t.stop());
  };

  if (error) {
    return (
      <div className="fixed inset-0 z-[70] bg-black flex items-center justify-center">
        <div className="text-center p-6">
          <AlertCircle size={48} className="text-red-400 mx-auto mb-4" />
          <p className="text-white mb-4">{error}</p>
          <button onClick={onClose} className="btn-secondary">Fechar</button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-[70] bg-black flex flex-col" data-testid="camera-capture">
      <video ref={videoRef} autoPlay playsInline className="flex-1 object-cover" />
      <div className="absolute bottom-0 left-0 right-0 p-6 flex items-center justify-center gap-6 bg-gradient-to-t from-black/80">
        <button onClick={onClose} className="p-3 rounded-full bg-white/20 text-white" data-testid="camera-close">
          <X size={24} />
        </button>
        <button onClick={takePhoto} className="w-16 h-16 rounded-full bg-white border-4 border-white/30 hover:bg-gray-200 transition-all" data-testid="camera-shutter" />
        <div className="w-12" />
      </div>
    </div>
  );
};


// ============== MODAL NOVA INSPEÇÃO ==============

const ModalNovaInspecao = ({ isOpen, onClose, onSuccess, ativos = [], rotas = [], tecnicos = [], preSelectedAtivoId = null }) => {
  const [loading, setLoading] = useState(false);
  const [planosDisponiveis, setPlanosDisponiveis] = useState([]);
  const [selectedPlano, setSelectedPlano] = useState(null);
  const [checklist, setChecklist] = useState([]);
  const [form, setForm] = useState({
    ativo_id: '', responsavel_id: '', executantes: [], data_planejada: '', observacoes: ''
  });
  const { user } = useAuth();
  
  useEffect(() => {
    if (isOpen) {
      setPlanosDisponiveis([]);
      setSelectedPlano(null);
      setChecklist([]);
      setForm({ ativo_id: preSelectedAtivoId || '', responsavel_id: user?.id || '', executantes: [], data_planejada: '', observacoes: '' });
    }
  }, [isOpen, user, preSelectedAtivoId]);

  const loadPlanos = async (ativoId) => {
    if (!ativoId) { setPlanosDisponiveis([]); return; }
    try {
      const res = await api.get(`/planos-inspecao/por-ativo/${ativoId}`);
      setPlanosDisponiveis(res.data);
    } catch {
      setPlanosDisponiveis([]);
    }
  };

  useEffect(() => {
    const ativoId = preSelectedAtivoId || form.ativo_id;
    if (ativoId && isOpen) loadPlanos(ativoId);
  }, [form.ativo_id, preSelectedAtivoId, isOpen]);

  const handleAtivoChange = (ativoId) => {
    setForm(prev => ({...prev, ativo_id: ativoId}));
    setSelectedPlano(null);
    setChecklist([]);
  };

  const handleSelectPlano = (plano) => {
    setSelectedPlano(plano);
    const perguntas = (plano.perguntas || []).map(p => ({
      id: p.id || String(Date.now()),
      descricao: p.texto || p.descricao || '',
      tipo: p.tipo_campo || p.tipo || 'boolean',
      obrigatorio: p.obrigatoria ?? p.obrigatorio ?? true,
      unidade: p.unidade || '',
      conforme: null, valor: null, observacao: ''
    }));
    setChecklist(perguntas);
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.ativo_id) { toast.error('Selecione o ativo'); return; }
    if (!selectedPlano) { toast.error('Selecione um plano de inspeção'); return; }
    
    setLoading(true);
    try {
      const payload = {
        ativo_id: form.ativo_id,
        plano_id: selectedPlano.id,
        tipo: selectedPlano.tipo || selectedPlano.categoria || 'inspecao',
        disciplina: selectedPlano.disciplina || null,
        responsavel_id: form.responsavel_id || null,
        executantes: form.executantes || [],
        checklist: checklist,
        data_planejada: form.data_planejada || null,
        observacoes: form.observacoes || null,
      };

      if (!navigator.onLine) {
        await queueOperation({ method: 'POST', url: '/inspecoes', data: payload });
        toast.info('Sem conexão — inspeção salva localmente');
      } else {
        await api.post('/inspecoes', payload);
        toast.success('Execução criada com sucesso!');
      }
      onSuccess();
      onClose();
    } catch (error) {
      toast.error(normalizeError(error));
    } finally {
      setLoading(false);
    }
  };

  const selectedAtivo = ativos.find(a => a.id === form.ativo_id);
  const tipoLabels = { inspecao: 'Inspeção', preventiva: 'Preventiva', lubrificacao: 'Lubrificação', limpeza: 'Limpeza', melhoria: 'Melhoria', mecanica: 'Mecânica', eletrica: 'Elétrica' };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Nova Execução de Inspeção" size="lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="glass-card p-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Ativo / Equipamento" required>
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
                <Select value={form.ativo_id} onChange={(val) => handleAtivoChange(val)}
                  options={ativos.map(a => ({ value: a.id, label: `${a.sector?.nome || ''} • ${a.tag} - ${a.nome}` }))} placeholder="Selecione o equipamento..." />
              )}
            </FormInput>
            <FormInput label="Responsável">
              <Select value={form.responsavel_id} onChange={(val) => setForm({...form, responsavel_id: val})}
                options={tecnicos.map(t => ({ value: t.id, label: t.nome }))} placeholder="Selecione..." />
            </FormInput>
            <FormInput label="Data Planejada">
              <input type="date" value={form.data_planejada} onChange={(e) => setForm({...form, data_planejada: e.target.value})} className="input-industrial w-full px-4" />
            </FormInput>
          </div>
          <FormInput label="Executantes">
            <div className="space-y-1">
              <div className="flex flex-wrap gap-1 min-h-[32px]">
                {(form.executantes || []).map(uid => {
                  const t = tecnicos.find(x => x.id === uid);
                  return t ? (
                    <span key={uid} className="bg-blue-500/20 text-blue-300 text-xs px-2 py-1 rounded flex items-center gap-1">
                      {t.nome} <button type="button" onClick={() => setForm({...form, executantes: form.executantes.filter(id => id !== uid)})} className="hover:text-red-400"><X size={12} /></button>
                    </span>
                  ) : null;
                })}
              </div>
              <select onChange={e => {
                if (e.target.value && !(form.executantes || []).includes(e.target.value)) {
                  setForm({...form, executantes: [...(form.executantes || []), e.target.value]});
                }
                e.target.value = '';
              }} className="input-industrial w-full px-3 text-sm" data-testid="inspecao-executantes-select">
                <option value="">Adicionar executante...</option>
                {tecnicos.filter(t => !(form.executantes || []).includes(t.id)).map(t => <option key={t.id} value={t.id}>{t.nome}</option>)}
              </select>
            </div>
          </FormInput>
        </div>

        {form.ativo_id && (
          <div className="glass-card p-4 space-y-3">
            <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider">
              Planos Aprovados ({planosDisponiveis.length})
            </h3>
            {planosDisponiveis.length === 0 ? (
              <div className="text-center py-6">
                <ClipboardCheck size={32} className="text-slate-600 mx-auto mb-2" />
                <p className="text-sm text-slate-500">Nenhum plano aprovado para este ativo.</p>
                <p className="text-xs text-slate-600 mt-1">O PCM precisa criar e aprovar planos antes de executar inspeções.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {planosDisponiveis.map(plano => (
                  <button key={plano.id} type="button"
                    onClick={() => handleSelectPlano(plano)}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      selectedPlano?.id === plano.id
                        ? 'border-emerald-500/50 bg-brand-10'
                        : 'border-slate-700 hover:border-slate-500 bg-slate-800/30'
                    }`}
                    data-testid={`plano-option-${plano.id}`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className={`font-medium text-sm ${selectedPlano?.id === plano.id ? 'text-emerald-400' : 'text-slate-200'}`}>{plano.nome}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 capitalize">{tipoLabels[plano.tipo] || plano.tipo}</span>
                          {plano.disciplina && <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 capitalize">{plano.disciplina}</span>}
                          <span className="text-xs text-slate-500">{(plano.perguntas || []).length} perguntas</span>
                          <span className="text-xs text-slate-600">v{plano.versao || 1}</span>
                          {plano._generico && <span className="text-xs px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400">Genérico</span>}
                        </div>
                      </div>
                      {selectedPlano?.id === plano.id && <CheckCircle2 size={20} className="text-brand" />}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {selectedPlano && checklist.length > 0 && (
          <div className="glass-card p-4 space-y-3">
            <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider">
              Checklist — {selectedPlano.nome} ({checklist.length} itens)
            </h3>
            <div className="max-h-48 overflow-y-auto space-y-1 custom-scrollbar">
              {checklist.map((item, idx) => (
                <div key={item.id || idx} className="flex items-center gap-2 text-xs text-slate-400 py-1 border-b border-slate-800/50">
                  <span className="text-slate-600 w-5">{idx + 1}.</span>
                  <span className="flex-1">{item.descricao}</span>
                  <span className="text-slate-600 capitalize">{item.tipo}</span>
                  {item.obrigatorio && <span className="text-red-400">*</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        <FormInput label="Observações">
          <textarea value={form.observacoes} onChange={(e) => setForm({...form, observacoes: e.target.value})} className="input-industrial w-full px-4 py-3 min-h-[60px]" placeholder="Observações adicionais..." />
        </FormInput>

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="submit" disabled={loading || !selectedPlano} className="btn-primary" data-testid="submit-inspecao">
            {loading ? 'Salvando...' : `Executar ${selectedPlano ? selectedPlano.nome : 'Inspeção'}`}
          </button>
        </div>
      </form>
    </Modal>
  );
};


export { InspecoesPage, InspecaoDetailPage, RondaPage, ScannerPage, PhotoUploader };
