import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { ClipboardCheck, Wrench, AlertTriangle, Plus, Target, Box, ChevronRight, RefreshCw, Clock, Play, Zap, Calendar } from "lucide-react";
import { api, useAuth, BACKEND_URL } from "../lib/api";
import { StatusBadge, PriorityBadge, EmptyState, Loading, PageContainer, PageHeader, Modal, FormInput, Select } from "../components/shared";
import { toast } from "sonner";

const FieldOpsPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedAtivo, setSelectedAtivo] = useState(null);
  const [showNovaOS, setShowNovaOS] = useState(false);
  const [novaOSForm, setNovaOSForm] = useState({ tipo: 'corretiva', titulo: '', descricao: '', prioridade: 'media' });
  const [saving, setSaving] = useState(false);
  const { user } = useAuth();
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      const res = await api.get('/minha-area');
      setData(res.data);
    } catch { toast.error('Erro ao carregar dados'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleNovaOSDireta = async (e) => {
    e.preventDefault();
    if (!selectedAtivo || !novaOSForm.titulo) { toast.error('Selecione equipamento e titulo'); return; }
    setSaving(true);
    try {
      await api.post('/ordens-servico', {
        ativo_id: selectedAtivo.id,
        tipo: novaOSForm.tipo,
        titulo: novaOSForm.titulo,
        descricao: novaOSForm.descricao,
        prioridade: novaOSForm.prioridade,
        execucao_direta: true,
        responsavel_id: user?.id,
      });
      toast.success('OS criada e iniciada!');
      setShowNovaOS(false);
      setNovaOSForm({ tipo: 'corretiva', titulo: '', descricao: '', prioridade: 'media' });
      fetchData();
    } catch (err) { toast.error(err?.response?.data?.detail && typeof err.response.data.detail === 'string' ? err.response.data.detail : 'Erro ao criar OS'); }
    finally { setSaving(false); }
  };

  if (loading) return <Loading rows={6} />;
  if (!data) return null;

  const tiposOS = [
    { value: 'corretiva', label: 'Corretiva' },
    { value: 'melhoria', label: 'Melhoria' },
    { value: 'limpeza', label: 'Limpeza' },
    { value: 'fabricacao', label: 'Fabricacao' },
  ];

  return (
    <PageContainer data-testid="minha-area">
      <PageHeader title="Minha Area" subtitle={`${data.user_nome} • Turno ${data.turno || 'ADM'} • ${(data.disciplinas || []).join(', ') || 'Geral'}`}>
        <button onClick={() => { setLoading(true); fetchData(); }} className="p-2 hover:bg-surface-hover rounded-lg transition-colors" data-testid="field-refresh">
          <RefreshCw size={18} className="text-secondary" />
        </button>
      </PageHeader>

      {/* Counters */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="glass-card p-3 text-center">
          <p className="text-xl font-bold text-emerald-400">{data.contadores?.minhas_os || 0}</p>
          <p className="text-[10px] text-secondary uppercase">Minhas OS</p>
        </div>
        <div className="glass-card p-3 text-center">
          <p className="text-xl font-bold text-indigo-400">{data.contadores?.inspecoes_pendentes || 0}</p>
          <p className="text-[10px] text-secondary uppercase">Inspecoes Pendentes</p>
        </div>
        <div className="glass-card p-3 text-center">
          <p className="text-xl font-bold text-cyan-400">{data.contadores?.equipamentos || 0}</p>
          <p className="text-[10px] text-secondary uppercase">Equipamentos</p>
        </div>
        <div className="glass-card p-3 text-center">
          <p className="text-xl font-bold text-amber-400">{data.contadores?.planos_ativos || 0}</p>
          <p className="text-[10px] text-secondary uppercase">Planos Ativos</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex flex-wrap gap-2 mt-4">
        <button onClick={() => setShowNovaOS(true)} className="btn-primary flex items-center gap-2 text-sm" data-testid="field-nova-os">
          <Plus size={16} /> Nova OS
        </button>
        <button onClick={() => navigate('/solicitar')} className="btn-secondary flex items-center gap-2 text-sm" data-testid="field-nova-solicitacao">
          <AlertTriangle size={16} /> Solicitar Servico
        </button>
        <button onClick={() => navigate('/ronda')} className="btn-secondary flex items-center gap-2 text-sm" data-testid="field-ronda">
          <Target size={16} /> Ronda
        </button>
      </div>

      {/* My OS */}
      {(data.minhas_os || []).length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
            <Wrench size={16} /> Minhas OS ({data.minhas_os.length})
          </h3>
          <div className="space-y-2">
            {data.minhas_os.map(os => (
              <div key={os.id} onClick={() => navigate(`/os/${os.id}`)} className="glass-card p-3 flex items-center gap-3 cursor-pointer hover:border-slate-600 transition-colors" data-testid={`field-os-${os.id}`}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {os.ativo && <span className="font-mono text-xs text-brand">{os.ativo.tag}</span>}
                    <span className="text-xs text-slate-500">#{os.numero}</span>
                  </div>
                  <p className="text-sm text-slate-200 truncate">{os.titulo}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <StatusBadge status={os.status} size="sm" />
                    <PriorityBadge priority={os.prioridade} />
                    <span className="text-xs text-slate-500 capitalize">{os.tipo}</span>
                  </div>
                </div>
                <ChevronRight size={18} className="text-slate-600" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pending Inspections */}
      {(data.inspecoes_pendentes || []).length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
            <ClipboardCheck size={16} /> Inspecoes Pendentes ({data.inspecoes_pendentes.length})
          </h3>
          <div className="space-y-2">
            {data.inspecoes_pendentes.map(insp => (
              <div key={insp.id} onClick={() => navigate(`/inspecoes/${insp.id}`)} className="glass-card p-3 flex items-center gap-3 cursor-pointer hover:border-slate-600 transition-colors" data-testid={`field-insp-${insp.id}`}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {insp.ativo && <span className="font-mono text-xs text-brand">{insp.ativo.tag}</span>}
                    <span className="text-xs text-slate-500 capitalize">{insp.tipo}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <StatusBadge status={insp.status} size="sm" />
                    {insp.data_programada && <span className="text-xs text-slate-500"><Calendar size={12} className="inline mr-1" />{insp.data_programada.substring(0, 10)}</span>}
                  </div>
                </div>
                <ChevronRight size={18} className="text-slate-600" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Equipment List with Plans */}
      <div className="mt-6">
        <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
          <Box size={16} /> Meus Equipamentos ({data.equipamentos?.length || 0})
        </h3>
        {(data.equipamentos || []).length === 0 ? (
          <EmptyState icon={Box} title="Nenhum equipamento na sua area" description="Solicite ao administrador que vincule sua area" />
        ) : (
          <div className="space-y-2">
            {data.equipamentos.map(ativo => {
              const planos = (data.planos_por_ativo || {})[ativo.id] || [];
              return (
                <div key={ativo.id} className="glass-card p-3" data-testid={`field-ativo-${ativo.id}`}>
                  <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate(`/ativos/${ativo.id}`)}>
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-slate-800 text-brand font-mono text-xs font-bold">
                      {(ativo.tag || '??').substring(0, 4)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-slate-200">{ativo.tag} — {ativo.nome}</p>
                      <p className="text-xs text-slate-500">{ativo.sector_nome || ''} • {ativo.tipo_equipamento || ''}</p>
                    </div>
                    {ativo.criticidade === 'A' && <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">Critico</span>}
                    <ChevronRight size={18} className="text-slate-600" />
                  </div>
                  {planos.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-800/50 flex flex-wrap gap-1">
                      {planos.map(p => (
                        <span key={p.id} className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                          {p.nome} {p._generico && '(G)'}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Modal: Nova OS Direta */}
      <Modal isOpen={showNovaOS} onClose={() => setShowNovaOS(false)} title="Nova OS — Execucao Direta" size="md">
        <form onSubmit={handleNovaOSDireta} className="space-y-4">
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-xs text-amber-400">
            <Zap size={14} className="inline mr-1" /> OS sera criada e iniciada automaticamente
          </div>
          <FormInput label="Equipamento" required>
            <Select value={selectedAtivo?.id || ''} onChange={(val) => {
              const a = (data.equipamentos || []).find(e => e.id === val);
              setSelectedAtivo(a || null);
            }} options={(data.equipamentos || []).map(a => ({ value: a.id, label: `${a.tag} — ${a.nome}` }))} placeholder="Selecione..." />
          </FormInput>
          <FormInput label="Tipo">
            <Select value={novaOSForm.tipo} onChange={(val) => setNovaOSForm({...novaOSForm, tipo: val})} options={tiposOS} />
          </FormInput>
          <FormInput label="Titulo" required>
            <input type="text" value={novaOSForm.titulo} onChange={(e) => setNovaOSForm({...novaOSForm, titulo: e.target.value})} className="input-industrial w-full px-4" placeholder="Descreva o servico" required data-testid="nova-os-titulo" />
          </FormInput>
          <FormInput label="Descricao">
            <textarea value={novaOSForm.descricao} onChange={(e) => setNovaOSForm({...novaOSForm, descricao: e.target.value})} className="input-industrial w-full px-4 py-3 min-h-[80px]" placeholder="Detalhes..." />
          </FormInput>
          <FormInput label="Prioridade">
            <Select value={novaOSForm.prioridade} onChange={(val) => setNovaOSForm({...novaOSForm, prioridade: val})} options={[
              { value: 'baixa', label: 'Baixa' }, { value: 'media', label: 'Media' },
              { value: 'alta', label: 'Alta' }, { value: 'critica', label: 'Critica' },
            ]} />
          </FormInput>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => setShowNovaOS(false)} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary" data-testid="nova-os-submit">
              {saving ? 'Criando...' : 'Criar e Iniciar OS'}
            </button>
          </div>
        </form>
      </Modal>
    </PageContainer>
  );
};

export default FieldOpsPage;
