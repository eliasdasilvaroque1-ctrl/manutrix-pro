import { useState, useEffect, memo } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, Download, FileText, Filter, Layers, Wrench, X } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/lib/api";
import { api } from "@/lib/api";
import { StatusBadge, PriorityBadge, Loading, Modal } from "@/components/shared";

const DashboardPage = () => {
  const [kpis, setKpis] = useState(null);
  const [stats, setStats] = useState(null);
  const [trend, setTrend] = useState([]);
  const [loading, setLoading] = useState(true);
  const [drillModal, setDrillModal] = useState({ open: false, type: '', title: '', data: [] });
  const [drillLoading, setDrillLoading] = useState(false);
  const [sectors, setSectors] = useState([]);
  const [filterSector, setFilterSector] = useState('');
  const [osPorSetor, setOsPorSetor] = useState([]);
  const [osPorDisciplina, setOsPorDisciplina] = useState([]);
  const [ativosMaisFalhas, setAtivosMaisFalhas] = useState([]);
  const { user } = useAuth();
  const navigate = useNavigate();
  
  useEffect(() => {
    api.get('/sectors').then(r => setSectors(r.data)).catch(() => {});
  }, []);
  
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const params = {};
        if (filterSector) params.sector_id = filterSector;
        const [kpisRes, statsRes, trendRes, setorRes, discRes, falhasRes, osStatsRes] = await Promise.all([
          api.get('/kpis', { params }),
          api.get('/dashboard/stats', { params }),
          api.get('/dashboard/trend', { params }),
          api.get('/dashboard/os-por-setor'),
          api.get('/dashboard/os-por-disciplina'),
          api.get('/dashboard/ativos-mais-falhas'),
          api.get('/ordens-servico/estatisticas').catch(() => ({ data: {} })),
        ]);
        setKpis({...kpisRes.data, osStats: osStatsRes.data});
        setStats(statsRes.data);
        setTrend(trendRes.data);
        setOsPorSetor(setorRes.data);
        setOsPorDisciplina(discRes.data);
        setAtivosMaisFalhas(falhasRes.data);
      } catch (error) {
        toast.error('Não foi possível carregar o dashboard. Verifique sua conexão.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [filterSector]);

  const drillDown = async (type, title) => {
    setDrillLoading(true);
    setDrillModal({ open: true, type, title, data: [] });
    try {
      let data = [];
      if (type === 'backlog' || type === 'os_abertas') {
        const res = await api.get('/ordens-servico');
        data = res.data.filter(o => ['aberta','planejada','em_execucao','pausada'].includes(o.status));
      } else if (type === 'os_criticas') {
        const res = await api.get('/ordens-servico');
        data = res.data.filter(o => o.prioridade === 'critica' && !['concluida','cancelada'].includes(o.status));
      } else if (type === 'corretiva' || type === 'preventiva' || type === 'preditiva' || type === 'emergencia') {
        const res = await api.get('/ordens-servico');
        data = res.data.filter(o => o.tipo === type);
      } else if (type === 'mttr') {
        const res = await api.get('/ordens-servico');
        data = res.data.filter(o => o.status === 'concluida' && o.tempo_execucao_minutos);
      } else if (type === 'estoque_critico') {
        const res = await api.get('/estoque');
        data = res.data.filter(i => i.quantidade <= i.estoque_minimo);
      } else if (type === 'insp_pendentes') {
        const res = await api.get('/inspecoes');
        data = res.data.filter(i => i.status === 'pendente');
      } else if (type === 'nao_conformes') {
        const res = await api.get('/inspecoes');
        data = res.data.filter(i => i.resultado === 'nao_conforme');
      }
      setDrillModal(prev => ({ ...prev, data }));
    } catch { toast.error('Erro ao carregar detalhes'); }
    finally { setDrillLoading(false); }
  };

  const handleExport = async (entity, format) => {
    try {
      const res = await api.get(`/export/${entity}?format=${format}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      // Extract filename from Content-Disposition header
      const cd = res.headers?.['content-disposition'] || '';
      const match = cd.match(/filename=([^;]+)/);
      a.download = match ? match[1].replace(/^"|"$/g, '').trim() : `${entity}_export.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success(`${entity} exportado com sucesso`);
    } catch { toast.error('Erro ao exportar'); }
  };

  const getColor = (value, thresholds) => {
    if (value >= thresholds[0]) return 'text-emerald-400';
    if (value >= thresholds[1]) return 'text-amber-400';
    return 'text-red-400';
  };
  const getBg = (value, thresholds) => {
    if (value >= thresholds[0]) return 'border-emerald-500/30 bg-emerald-500/5';
    if (value >= thresholds[1]) return 'border-amber-500/30 bg-amber-500/5';
    return 'border-red-500/30 bg-red-500/5';
  };
  const getInverseColor = (value, thresholds) => {
    if (value <= thresholds[0]) return 'text-emerald-400';
    if (value <= thresholds[1]) return 'text-amber-400';
    return 'text-red-400';
  };
  const getInverseBg = (value, thresholds) => {
    if (value <= thresholds[0]) return 'border-emerald-500/30 bg-emerald-500/5';
    if (value <= thresholds[1]) return 'border-amber-500/30 bg-amber-500/5';
    return 'border-red-500/30 bg-red-500/5';
  };
  
  if (loading) return <Loading rows={8} />;
  if (!kpis || !stats) return null;
  
  const backlog = kpis.backlog_total || 0;
  const osAbertas = (stats?.ordens_servico?.abertas || 0) + (stats?.ordens_servico?.em_execucao || 0) + (stats?.ordens_servico?.pausadas || 0);
  const osCriticas = stats?.ordens_servico?.por_prioridade?.critica || 0;
  const estoqueCritico = stats?.estoque?.criticos || 0;
  const inspPendentes = stats?.inspecoes?.pendentes || 0;
  const naoConformes = stats?.inspecoes?.nao_conformes_mes || 0;
  const osStats = kpis.osStats || {};
  const aguardandoAprov = osStats.aguardando_aprovacao || 0;
  const aguardandoMaterial = osStats.aguardando_material || 0;
  const solicitadas = osStats.por_status?.solicitada || 0;
  const porOrigem = osStats.por_origem || {};
  
  // OS distribution from trend data (aggregated 6 months)
  const osTrendTotals = trend.reduce((acc, m) => ({
    corretiva: acc.corretiva + (m.corretivas || 0),
    preventiva: acc.preventiva + (m.preventivas || 0),
  }), { corretiva: 0, preventiva: 0 });
  
  const prevPercent = 0;
  const corrPercent = 0;
  
  const osTypes = [
    { name: 'Lubrificação', fill: '#06b6d4', key: 'lubrificacao' },
    { name: 'Limpeza', fill: '#8b5cf6', key: 'limpeza_organizacao' },
    { name: 'Preventiva', fill: '#10b981', key: 'preventiva' },
    { name: 'Corretiva', fill: '#ef4444', key: 'corretiva' },
    { name: 'Prep. Material', fill: '#f59e0b', key: 'preparacao_material' },
    { name: 'Fabricação', fill: '#3b82f6', key: 'fabricacao_melhorias' },
  ].map(t => ({ ...t, value: stats?.ordens_servico?.por_tipo?.[t.key] || osTrendTotals[t.key] || 0 }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-primary" data-testid="dashboard-title">Dashboard Operacional</h1>
          <p className="text-sm text-slate-500">Monitoramento em tempo real da confiabilidade e desempenho operacional dos ativos</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-1.5" data-testid="dashboard-filters">
            <Filter size={14} className="text-slate-500" />
            <select
              value={filterSector}
              onChange={(e) => setFilterSector(e.target.value)}
              className="bg-transparent text-sm text-slate-300 border-none outline-none cursor-pointer"
              data-testid="filter-sector"
            >
              <option value="">Todas as Áreas</option>
              {sectors.map(s => <option key={s.id} value={s.id}>{s.nome}</option>)}
            </select>
            {filterSector && (
              <button onClick={() => setFilterSector('')} className="text-xs text-red-400 hover:text-red-300 ml-1" data-testid="clear-filters">
                <X size={14} />
              </button>
            )}
          </div>
          <div className="relative group">
            <button className="btn-secondary flex items-center gap-2 text-sm" data-testid="export-data-btn">
              <Download size={16} /> Exportar Dados
            </button>
            <div className="absolute right-0 top-full mt-1 w-56 bg-slate-800 border border-slate-700 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 py-2">
              {[{label:'OS - Excel', e:'ordens-servico', f:'excel'}, {label:'OS - CSV', e:'ordens-servico', f:'excel'}, {label:'Ativos - Excel', e:'ativos', f:'excel'}, {label:'Inspeções - Excel', e:'inspecoes', f:'excel'}, {label:'Estoque - Excel', e:'estoque', f:'excel'}].map(item => (
                <button key={item.label} onClick={() => handleExport(item.e, item.f)} className="w-full px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 text-left flex items-center gap-2">
                  <FileText size={14} /> {item.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* BLOCO 1 - VISÃO EXECUTIVA */}
      <div>
        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Visão Executiva</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getBg(kpis.disponibilidade_percent, [90, 75])}`} onClick={() => navigate('/ativos')} data-testid="kpi-disponibilidade">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Disponibilidade</p>
            <p className={`text-4xl font-black tabular-nums ${getColor(kpis.disponibilidade_percent, [90, 75])}`}>{kpis.disponibilidade_percent}<span className="text-lg">%</span></p>
            <p className="text-xs text-slate-600 mt-1">{kpis.ativos_total} ativos cadastrados</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(backlog, [5, 15])}`} onClick={() => drillDown('backlog', 'Backlog de OS')} data-testid="kpi-backlog">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Backlog</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(backlog, [5, 15])}`}>{backlog}</p>
            <p className="text-xs text-slate-600 mt-1">ordens em aberto</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(osAbertas, [5, 15])}`} onClick={() => drillDown('os_abertas', 'OS Abertas')} data-testid="kpi-os-abertas">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">OS Abertas</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(osAbertas, [5, 15])}`}>{osAbertas}</p>
            <p className="text-xs text-slate-600 mt-1">aguardando execução</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(osCriticas, [0, 3])}`} onClick={() => drillDown('os_criticas', 'Ordens Críticas')} data-testid="kpi-os-criticas">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Ordens Críticas</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(osCriticas, [0, 3])}`}>{osCriticas}</p>
            <p className="text-xs text-slate-600 mt-1">prioridade máxima</p>
          </div>
        </div>
        {/* Row 2 — Governança */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
          <div className={`rounded-xl border p-5 ${getInverseBg(solicitadas, [0, 3])}`} data-testid="kpi-solicitadas">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Solicitações</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(solicitadas, [0, 3])}`}>{solicitadas}</p>
            <p className="text-xs text-slate-600 mt-1">aguardando análise</p>
          </div>
          <div className={`rounded-xl border p-5 ${getInverseBg(aguardandoAprov, [0, 2])}`} data-testid="kpi-aguardando-aprovacao">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Aguard. Aprovação</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(aguardandoAprov, [0, 2])}`}>{aguardandoAprov}</p>
            <p className="text-xs text-slate-600 mt-1">pendente gerente</p>
          </div>
          <div className={`rounded-xl border p-5 ${getInverseBg(aguardandoMaterial, [0, 3])}`} data-testid="kpi-aguardando-material">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Aguard. Material</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(aguardandoMaterial, [0, 3])}`}>{aguardandoMaterial}</p>
            <p className="text-xs text-slate-600 mt-1">sem material</p>
          </div>
          {Object.keys(porOrigem).length > 0 && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5" data-testid="kpi-por-origem">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">OS por Origem</p>
              <div className="space-y-1">
                {Object.entries(porOrigem).sort((a,b) => b[1]-a[1]).slice(0, 4).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between text-xs">
                    <span className="text-slate-400 capitalize">{k}</span>
                    <span className="text-slate-200 font-bold">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* BLOCO 2 - PERFORMANCE */}
      <div>
        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Performance</h2>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getBg(kpis.mtbf_horas, [500, 200])}`} onClick={() => drillDown('mttr', 'Histórico MTBF/MTTR')} data-testid="kpi-mtbf">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">MTBF</p>
            <p className={`text-4xl font-black tabular-nums ${getColor(kpis.mtbf_horas, [500, 200])}`}>{kpis.mtbf_horas}<span className="text-lg">h</span></p>
            <p className="text-xs text-slate-600 mt-1">tempo médio entre falhas</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(kpis.mttr_horas, [2, 8])}`} onClick={() => drillDown('mttr', 'Histórico MTTR')} data-testid="kpi-mttr">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">MTTR</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(kpis.mttr_horas, [2, 8])}`}>{kpis.mttr_horas}<span className="text-lg">h</span></p>
            <p className="text-xs text-slate-600 mt-1">tempo médio de reparo</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getBg(prevPercent, [60, 40])}`} onClick={() => drillDown('preventiva', 'OS Preventivas')} data-testid="kpi-prev-corr">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Preventiva vs Corretiva</p>
            <div className="flex items-end gap-3 mt-1">
              <div>
                <p className="text-3xl font-black text-brand tabular-nums">{prevPercent}<span className="text-sm">%</span></p>
                <p className="text-[10px] text-brand">preventiva</p>
              </div>
              <div>
                <p className="text-3xl font-black text-red-400 tabular-nums">{corrPercent}<span className="text-sm">%</span></p>
                <p className="text-[10px] text-red-600">corretiva</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* BLOCO 3 - RISCO OPERACIONAL */}
      <div>
        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Risco Operacional</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(estoqueCritico, [0, 3])}`} onClick={() => drillDown('estoque_critico', 'Estoque Crítico')} data-testid="kpi-estoque-critico">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Estoque Crítico</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(estoqueCritico, [0, 3])}`}>{estoqueCritico}</p>
            <p className="text-xs text-slate-600 mt-1">itens abaixo do mínimo</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(inspPendentes, [2, 8])}`} onClick={() => drillDown('insp_pendentes', 'Inspeções Pendentes')} data-testid="kpi-insp-pendentes">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Inspeções Pendentes</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(inspPendentes, [2, 8])}`}>{inspPendentes}</p>
            <p className="text-xs text-slate-600 mt-1">aguardando execução</p>
          </div>
          <div className={`rounded-xl border p-5 cursor-pointer hover:scale-[1.02] transition-transform ${getInverseBg(naoConformes, [0, 3])}`} onClick={() => drillDown('nao_conformes', 'Não Conformidades')} data-testid="kpi-nao-conformes">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Não Conformidades</p>
            <p className={`text-4xl font-black tabular-nums ${getInverseColor(naoConformes, [0, 3])}`}>{naoConformes}</p>
            <p className="text-xs text-slate-600 mt-1">inspeções com falha</p>
          </div>
        </div>
      </div>

      {/* GRÁFICOS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico 1 - Tendência MTBF/MTTR */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-300">Tendência MTBF / MTTR</h3>
            {trend.some(m => m.is_estimated) && (
              <span className="text-[10px] px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded" data-testid="estimated-label">Dados estimados nos meses sem histórico</span>
            )}
          </div>
          <div className="h-64" data-testid="chart-trend">
            <TrendChart data={trend} />
          </div>
        </div>

        {/* Gráfico 2 - Distribuição OS */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-300">Distribuição de OS por Tipo</h3>
            {trend.some(m => m.is_estimated) && (
              <span className="text-[10px] px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded">Inclui estimativas</span>
            )}
          </div>
          <div className="h-64" data-testid="chart-os-dist">
            <OSDistChart data={osTypes} onBarClick={(key) => drillDown(key, `OS ${key.charAt(0).toUpperCase() + key.slice(1)}`)} />
          </div>
        </div>
      </div>
      
      {/* Row 3 — New Dashboard Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* OS por Área */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5" data-testid="chart-os-setor">
          <h3 className="text-sm font-bold text-slate-300 mb-4 flex items-center gap-2"><Layers size={16} className="text-brand" /> OS por Área</h3>
          <div className="space-y-2">
            {osPorSetor.length === 0 ? <p className="text-xs text-slate-600 text-center py-4">Sem dados</p> :
            osPorSetor.map((s, i) => (
              <div key={i} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: s.cor }} />
                <span className="text-xs text-slate-400 flex-1 truncate">{s.sector}</span>
                <span className="text-sm font-mono font-bold text-slate-200">{s.os_abertas}</span>
              </div>
            ))}
          </div>
        </div>
        
        {/* OS por Disciplina */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5" data-testid="chart-os-disciplina">
          <h3 className="text-sm font-bold text-slate-300 mb-4 flex items-center gap-2"><Wrench size={16} className="text-blue-400" /> OS por Disciplina</h3>
          <div className="space-y-2">
            {osPorDisciplina.map((d, i) => (
              <div key={i} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: d.cor }} />
                <span className="text-xs text-slate-400 flex-1">{d.disciplina}</span>
                <span className="text-sm font-mono font-bold text-slate-200">{d.count}</span>
              </div>
            ))}
          </div>
        </div>
        
        {/* Ativos com Mais Falhas */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5" data-testid="chart-ativos-falhas">
          <h3 className="text-sm font-bold text-slate-300 mb-4 flex items-center gap-2"><AlertTriangle size={16} className="text-red-400" /> Ativos com Mais Falhas</h3>
          <div className="space-y-2">
            {ativosMaisFalhas.length === 0 ? <p className="text-xs text-slate-600 text-center py-4">Nenhuma falha registrada</p> :
            ativosMaisFalhas.slice(0, 5).map((a, i) => (
              <div key={i} className="flex items-center gap-2 p-2 bg-slate-800/30 rounded-lg">
                <span className="text-xs font-mono text-brand w-16">{a.tag}</span>
                <span className="text-xs text-slate-400 flex-1 truncate">{a.nome}</span>
                <span className="text-xs text-slate-600">{a.sector}</span>
                <span className="text-sm font-mono font-bold text-red-400">{a.falhas}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Drill-Down Modal */}
      <Modal isOpen={drillModal.open} onClose={() => setDrillModal({open:false,type:'',title:'',data:[]})} title={drillModal.title} size="lg">
        {drillLoading ? <Loading rows={5} /> : (
          <div className="space-y-2 max-h-[60vh] overflow-y-auto custom-scrollbar">
            {drillModal.data.length === 0 ? (
              <p className="text-center text-slate-500 py-8">Nenhum registro encontrado</p>
            ) : drillModal.data.map((item, idx) => (
              <div key={item.id || idx} className="p-3 bg-slate-800/50 rounded-lg flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    {item.numero && <span className="font-mono text-xs text-blue-400">{item.numero}</span>}
                    {item.ativo && <span className="font-mono text-xs text-brand">{item.ativo.tag}</span>}
                    {item.tag && <span className="font-mono text-xs text-brand">{item.tag}</span>}
                    {item.sku && <span className="font-mono text-xs text-purple-400">{item.sku}</span>}
                    <span className="text-slate-100">{item.nome}</span>
                    {item.prioridade && <PriorityBadge priority={item.prioridade} />}
                    {item.severidade && <PriorityBadge priority={item.severidade} />}
                  </div>
                  <p className="text-sm text-slate-200">{item.titulo || item.nome || item.descricao || item.ativo?.nome || '—'}</p>
                  <p className="text-xs text-slate-500">
                    {item.tipo && <span className="capitalize mr-2">{item.tipo}</span>}
                    {item.status && <span className="capitalize mr-2">{item.status}</span>}
                    {item.tempo_execucao_minutos && <span>{item.tempo_execucao_minutos} min</span>}
                    {item.quantidade !== undefined && <span>Qtd: {item.quantidade} (min: {item.estoque_minimo})</span>}
                    {item.frequencia && <span className="capitalize">{item.frequencia}</span>}
                  </p>
                </div>
                <StatusBadge status={item.status || 'pendente'} size="sm" />
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
};

// Chart Components
const TrendChart = memo(({ data }) => {
  const { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } = require('recharts');
  const enriched = data.map(d => ({ ...d, mes_label: d.is_estimated ? `${d.mes}*` : d.mes }));
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={enriched} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="mes_label" tick={{ fill: '#94a3b8', fontSize: 12 }} stroke="#475569" />
        <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} stroke="#475569" />
        <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#e2e8f0' }} formatter={(value, name, props) => [value, `${name}${props.payload.is_estimated ? ' (estimado)' : ''}`]} />
        <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
        <Line type="monotone" dataKey="mtbf" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} name="MTBF (h)" />
        <Line type="monotone" dataKey="mttr" stroke="#ef4444" strokeWidth={2} dot={{ r: 4 }} name="MTTR (h)" />
      </LineChart>
    </ResponsiveContainer>
  );
});

const OSDistChart = memo(({ data, onBarClick }) => {
  const { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } = require('recharts');
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} stroke="#475569" />
        <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} stroke="#475569" allowDecimals={false} />
        <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#e2e8f0' }} />
        <Bar dataKey="value" radius={[6, 6, 0, 0]} cursor="pointer" onClick={(d) => onBarClick(d.key)}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
});

// Ativos Page

export default DashboardPage;
