import { useState, useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { QrCode, Camera, Search, Box, ArrowLeft, Eye, FileText, Activity, Calendar, Wrench, Clock, AlertTriangle, CheckCircle, MapPin, Hash, Building2, ChevronLeft, ChevronRight, ClipboardCheck, Cog } from "lucide-react";
import { toast } from "sonner";
import { api, useAuth, BACKEND_URL } from "@/lib/api";
import { normalizeError, ROLE_LABELS } from "@/lib/constants";
import { StatusBadge, PriorityBadge, Loading, PageContainer, PageHeader, SearchInput, EmptyState } from "@/components/shared";

const ConsultaEquipamentosPage = () => {
  const [busca, setBusca] = useState('');
  const [ativos, setAtivos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [portalData, setPortalData] = useState(null);
  const [loadingPortal, setLoadingPortal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/ativos');
        setAtivos(res.data);
      } catch { /* empty */ }
      finally { setLoading(false); }
    })();
  }, []);

  const handleSelectAtivo = async (ativo) => {
    setSelected(ativo);
    setLoadingPortal(true);
    try {
      const res = await axios.get(`${API}/public/ativo/${ativo.id}`);
      setPortalData(res.data);
    } catch { toast.error('Erro ao carregar dados do equipamento'); }
    finally { setLoadingPortal(false); }
  };

  const filtered = ativos.filter(a => {
    const q = busca.toLowerCase();
    return !q || a.tag?.toLowerCase().includes(q) || a.nome?.toLowerCase().includes(q) || a.tipo_equipamento?.toLowerCase().includes(q);
  });

  const statusMap = { operacional: { label: 'Operacional', cls: 'bg-emerald-500/10 text-emerald-400' }, parado: { label: 'Parado', cls: 'bg-red-500/10 text-red-400' }, manutencao: { label: 'Manutenção', cls: 'bg-amber-500/10 text-amber-400' } };
  const formatDate = (d) => d ? new Date(d).toLocaleDateString('pt-BR') : '—';

  if (selected && portalData) {
    const { ativo: av, kpis, ultimas_inspecoes, ultimas_os, manuais } = portalData;
    const st = statusMap[av?.status] || statusMap.operacional;
    return (
      <div className="space-y-4" data-testid="consulta-detalhe">
        <button onClick={() => { setSelected(null); setPortalData(null); }} className="flex items-center gap-1 text-sm text-slate-400 hover:text-brand transition-colors" data-testid="consulta-voltar">
          <ChevronLeft size={16} /> Voltar à pesquisa
        </button>
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <span className="text-brand font-mono font-bold text-lg">{av?.tag}</span>
              <h2 className="text-xl font-bold text-slate-100 mt-1">{av?.nome}</h2>
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${st.cls}`}>{st.label}</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><span className="text-slate-500">Tipo</span><p className="text-slate-200 font-medium">{av?.tipo_equipamento || '—'}</p></div>
            <div><span className="text-slate-500">Fabricante</span><p className="text-slate-200 font-medium">{av?.fabricante || '—'}</p></div>
            <div><span className="text-slate-500">Modelo</span><p className="text-slate-200 font-medium">{av?.modelo || '—'}</p></div>
            <div><span className="text-slate-500">Criticidade</span><p className="text-slate-200 font-medium capitalize">{av?.criticidade || '—'}</p></div>
          </div>
        </div>
        {kpis && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {kpis.total_os != null && <div className="glass-card p-4 text-center"><p className="text-2xl font-bold text-brand">{kpis.total_os}</p><p className="text-xs text-slate-500">OS Total</p></div>}
            {kpis.total_inspecoes != null && <div className="glass-card p-4 text-center"><p className="text-2xl font-bold text-emerald-400">{kpis.total_inspecoes}</p><p className="text-xs text-slate-500">Inspeções</p></div>}
            {kpis.disponibilidade != null && <div className="glass-card p-4 text-center"><p className="text-2xl font-bold text-blue-400">{kpis.disponibilidade}%</p><p className="text-xs text-slate-500">Disponibilidade</p></div>}
            {kpis.mtbf != null && <div className="glass-card p-4 text-center"><p className="text-2xl font-bold text-amber-400">{kpis.mtbf}h</p><p className="text-xs text-slate-500">MTBF</p></div>}
          </div>
        )}
        {ultimas_os?.length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Últimas Ordens de Serviço</h3>
            <div className="space-y-2">
              {ultimas_os.slice(0, 5).map((os, i) => (
                <div key={i} className="flex items-center justify-between text-sm border-b border-slate-800 pb-2">
                  <div><span className="font-mono text-brand">#{os.numero}</span> <span className="text-slate-300 ml-2">{os.titulo}</span></div>
                  <div className="flex items-center gap-2"><span className="text-xs text-slate-500">{formatDate(os.created_at)}</span><span className="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-300 capitalize">{os.status}</span></div>
                </div>
              ))}
            </div>
          </div>
        )}
        {ultimas_inspecoes?.length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Últimas Inspeções</h3>
            <div className="space-y-2">
              {ultimas_inspecoes.slice(0, 5).map((ins, i) => (
                <div key={i} className="flex items-center justify-between text-sm border-b border-slate-800 pb-2">
                  <span className="text-slate-300">{ins.tipo || 'Inspeção'}</span>
                  <div className="flex items-center gap-2"><span className="text-xs text-slate-500">{formatDate(ins.data_execucao || ins.created_at)}</span><span className="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-300 capitalize">{ins.status}</span></div>
                </div>
              ))}
            </div>
          </div>
        )}
        {manuais?.length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Manuais e Documentos</h3>
            <div className="space-y-2">
              {manuais.map((m, i) => (
                <a key={i} href={m.url?.startsWith('http') ? m.url : `${BACKEND_URL}${m.url}`} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300">
                  <FileText size={14} /> {m.nome || m.filename}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="consulta-equipamentos">
      <div className="flex items-center gap-3 mb-2">
        <Search size={24} className="text-brand" />
        <h1 className="text-2xl font-bold text-primary">Portal de Consulta</h1>
      </div>
      <p className="text-sm text-slate-400">Pesquise equipamentos por TAG, nome ou tipo. Selecione para ver o prontuário completo.</p>
      <div className="relative">
        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
        <input value={busca} onChange={e => setBusca(e.target.value)} placeholder="Buscar por TAG, nome ou tipo de equipamento..." className="input-industrial w-full pl-10" data-testid="consulta-busca" />
      </div>
      {loading ? (
        <div className="flex justify-center py-12"><Cog size={32} className="text-brand animate-spin" /></div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          <Search size={48} className="mx-auto mb-3 opacity-30" />
          <p>{busca ? `Nenhum equipamento encontrado para "${busca}"` : 'Nenhum equipamento cadastrado'}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map(a => {
            const s = statusMap[a.status] || statusMap.operacional;
            return (
              <button key={a.id} onClick={() => handleSelectAtivo(a)} className="glass-card p-4 text-left hover:border-brand/40 transition-all group" data-testid={`consulta-ativo-${a.id}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-brand font-bold text-sm">{a.tag}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${s.cls}`}>{s.label}</span>
                </div>
                <p className="text-slate-200 text-sm font-medium truncate">{a.nome}</p>
                <p className="text-xs text-slate-500 mt-1">{a.tipo_equipamento} {a.fabricante ? `| ${a.fabricante}` : ''}</p>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};



// ============== PORTAL PÚBLICO DO EQUIPAMENTO (FASE 4) ==============


// ============== DOSSIÊ PESQUISA GLOBAL ==============
const DossiePesquisaPage = () => {
  const [busca, setBusca] = useState('');
  const [tipo, setTipo] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dossie, setDossie] = useState(null);
  const [dossieType, setDossieType] = useState(null);
  const [dossieLoading, setDossieLoading] = useState(false);
  const [plantas, setPlantas] = useState([]);
  const { user } = useAuth();
  const formatD = (d) => d ? new Date(d).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '—';
  const formatMin = (m) => m ? `${Math.floor(m/60)}h${String(m%60).padStart(2,'0')}` : '';

  useEffect(() => { api.get('/plantas').then(r => setPlantas(r.data)).catch(() => {}); }, []);

  const pesquisar = async () => {
    if (!busca.trim() && !tipo) return;
    setLoading(true);
    try {
      const params = {};
      if (busca.trim()) params.q = busca.trim();
      if (tipo) params.tipo = tipo;
      const res = await api.get('/dossie/pesquisa', { params });
      setResults(res.data);
    } catch { toast.error('Erro na pesquisa'); }
    finally { setLoading(false); }
  };

  const openDossie = async (tipoReg, id) => {
    setDossieLoading(true);
    try {
      const res = await api.get(`/dossie/${tipoReg}/${id}`);
      setDossie(res.data);
      setDossieType(tipoReg);
    } catch { toast.error('Erro ao carregar dossiê'); }
    finally { setDossieLoading(false); }
  };

  if (dossie) {
    return (
      <div data-testid="dossie-pesquisa-detail">
        <button onClick={() => { setDossie(null); setDossieType(null); }} className="flex items-center gap-1 text-sm text-slate-400 hover:text-brand mb-3"><ChevronLeft size={16} /> Voltar à pesquisa</button>
        <DossieTab ativoId={dossie.ativo_id || dossie.ativo?.id} plantas={plantas} user={user} />
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="dossie-pesquisa">
      <div className="flex items-center gap-3">
        <FileText size={24} className="text-brand" />
        <h1 className="text-2xl font-bold text-primary">Dossiê / Pesquisa</h1>
      </div>
      <p className="text-sm text-slate-400">Pesquise ordens de serviço e inspeções por número, TAG, equipamento, área ou tipo.</p>
      <div className="glass-card p-4 flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[200px]">
          <label className="text-xs text-slate-500 mb-1 block">Pesquisar</label>
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input value={busca} onChange={e => setBusca(e.target.value)} onKeyDown={e => e.key === 'Enter' && pesquisar()} placeholder="Nº OS, TAG, equipamento..." className="input-industrial w-full pl-9" data-testid="dossie-pesquisa-input" />
          </div>
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Tipo</label>
          <select value={tipo} onChange={e => setTipo(e.target.value)} className="input-industrial px-3" data-testid="dossie-pesquisa-tipo">
            <option value="">Todos</option>
            <option value="corretiva">OS Corretiva</option>
            <option value="preventiva">OS Preventiva</option>
            <option value="melhoria">OS Melhoria</option>
            <option value="inspecao">Inspeção</option>
          </select>
        </div>
        <button onClick={pesquisar} className="btn-primary flex items-center gap-2" data-testid="dossie-pesquisa-btn">
          <Search size={16} /> Pesquisar
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-8"><Cog size={32} className="text-brand animate-spin" /></div>
      ) : results.length > 0 ? (
        <div className="space-y-1.5">
          <p className="text-xs text-slate-500">{results.length} resultado(s)</p>
          {results.map((r, i) => (
            <div key={i} onClick={() => openDossie(r.tipo_registro, r.id)} className="glass-card p-3 flex items-center gap-3 cursor-pointer hover:border-brand/30 transition-all" data-testid={`dossie-result-${i}`}>
              <div className={`p-2 rounded-lg border ${r.tipo_registro === 'os' ? 'text-blue-400 bg-blue-500/10 border-blue-500/30' : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'}`}>
                {r.tipo_registro === 'os' ? <Wrench size={16} /> : <ClipboardCheck size={16} />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  {r.numero && <span className="font-mono text-brand text-sm">#{r.numero}</span>}
                  <span className="text-sm text-slate-200 truncate">{r.titulo || r.tipo}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full capitalize ${r.status === 'concluida' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-700 text-slate-400'}`}>{r.status}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  {r.area && <span>{r.area}</span>}
                  {r.tag && <span className="font-mono text-brand">{r.tag}</span>}
                  {r.equipamento && <span>{r.equipamento}</span>}
                </div>
              </div>
              <div className="text-right shrink-0">
                <p className="text-xs text-slate-400">{formatD(r.data)}</p>
                {r.tempo_minutos && <p className="text-[10px] text-slate-500">{formatMin(r.tempo_minutos)}</p>}
              </div>
              <ChevronRight size={14} className="text-slate-600" />
            </div>
          ))}
        </div>
      ) : busca || tipo ? (
        <div className="text-center py-8 text-slate-500"><Search size={32} className="mx-auto mb-2 opacity-30" /><p>Nenhum resultado para a pesquisa</p></div>
      ) : null}
      {dossieLoading && <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"><Cog size={48} className="text-brand animate-spin" /></div>}
    </div>
  );
};



export { ConsultaEquipamentosPage, DossiePesquisaPage };
