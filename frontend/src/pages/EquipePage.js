import { useState, useEffect } from "react";
import { Users, Wrench, Clock, Activity, TrendingUp, TrendingDown, BarChart3 } from "lucide-react";
import { api, useAuth } from "@/lib/api";
import { toast } from "sonner";
import { EmptyState, Loading, PageContainer, PageHeader } from "@/components/shared";

const EquipePage = () => {
  const [periodo, setPeriodo] = useState('semana');
  const [metricas, setMetricas] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  const fetchMetricas = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/metricas/equipe?periodo=${periodo}`);
      setMetricas(res.data);
    } catch { toast.error('Erro ao carregar métricas'); }
    finally { setLoading(false); }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchMetricas(); }, [periodo]);

  const formatHH = (min) => { const h = Math.floor(min/60); const m = Math.round(min%60); return `${h}h${m > 0 ? m + 'm' : ''}`; };
  const totalOS = metricas.reduce((s, m) => s + (m.os_total || 0), 0);
  const totalHH = metricas.reduce((s, m) => s + (m.hh_liquida_min || 0), 0);
  const totalInsp = metricas.reduce((s, m) => s + (m.inspecoes || 0), 0);

  return (
    <div className="space-y-4" data-testid="equipe-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-primary">Equipe</h1>
        <div className="flex gap-1">
          {[{v:'hoje',l:'Hoje'},{v:'semana',l:'Semana'},{v:'mes',l:'Mês'},{v:'ano',l:'Ano'}].map(p => (
            <button key={p.v} onClick={() => setPeriodo(p.v)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${periodo === p.v ? 'bg-brand-20 text-brand border border-brand-30' : 'border border-slate-700 text-slate-500 hover:text-slate-300'}`}
              data-testid={`equipe-periodo-${p.v}`}
            >{p.l}</button>
          ))}
        </div>
      </div>

      {/* KPI Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="glass-card p-4 text-center">
          <p className="text-3xl font-bold text-brand">{metricas.length}</p>
          <p className="text-xs text-slate-500">Técnicos Ativos</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-3xl font-bold text-blue-400">{totalOS}</p>
          <p className="text-xs text-slate-500">OS Executadas</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-3xl font-bold text-amber-400">{formatHH(totalHH)}</p>
          <p className="text-xs text-slate-500">HH Total</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-3xl font-bold text-cyan-400">{totalInsp}</p>
          <p className="text-xs text-slate-500">Inspeções</p>
        </div>
      </div>

      {/* Ranking */}
      {loading ? <Loading rows={5} /> : metricas.length > 0 ? (
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-3">Ranking — {periodo === 'hoje' ? 'Hoje' : periodo === 'semana' ? 'Semana' : periodo === 'mes' ? 'Mês' : 'Ano'}</h3>
          <div className="space-y-2">
            {metricas.slice(0, 10).map((m, idx) => {
              const maxOS = metricas[0]?.os_total || 1;
              const pct = Math.min(100, ((m.os_total || 0) / maxOS) * 100);
              const medalColors = ['text-amber-400', 'text-slate-300', 'text-amber-600'];
              const tipos = m.os_por_tipo || {};
              return (
                <div key={m.user_id} className="group" data-testid={`ranking-${idx}`}>
                  <div className="flex items-center gap-3 py-2">
                    <span className={`text-lg font-bold w-8 text-center ${medalColors[idx] || 'text-slate-600'}`}>
                      {idx < 3 ? ['1º','2º','3º'][idx] : `${idx+1}º`}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <div>
                          <span className="text-sm text-slate-200 font-medium">{m.user_nome || 'Sem nome'}</span>
                          <span className="text-[10px] text-slate-600 ml-2 capitalize">{m.user_role}</span>
                        </div>
                        <span className="text-sm font-bold text-brand">{m.os_total || 0} OS</span>
                      </div>
                      {/* Progress bar */}
                      <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-brand rounded-full transition-all" style={{width: `${pct}%`}} />
                      </div>
                      {/* Detail metrics */}
                      <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5 text-[10px] text-slate-500">
                        <span>HH: <b className="text-slate-400">{formatHH(m.hh_liquida_min || 0)}</b></span>
                        <span>Solo: <b className="text-slate-400">{m.os_solo || 0}</b></span>
                        <span>Compartilhada: <b className="text-slate-400">{m.os_compartilhada || 0}</b></span>
                        {m.inspecoes > 0 && <span>Inspeções: <b className="text-cyan-400">{m.inspecoes}</b></span>}
                        {m.tempo_medio_os_min > 0 && <span>Tempo médio: <b className="text-slate-400">{formatHH(m.tempo_medio_os_min)}</b></span>}
                        {tipos.corretiva > 0 && <span className="text-red-400/70">Corr: {tipos.corretiva}</span>}
                        {tipos.preventiva > 0 && <span className="text-blue-400/70">Prev: {tipos.preventiva}</span>}
                        {tipos.lubrificacao > 0 && <span className="text-yellow-400/70">Lub: {tipos.lubrificacao}</span>}
                        {tipos.melhoria > 0 && <span className="text-brand/70">Melh: {tipos.melhoria}</span>}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <EmptyState icon={Users} title="Sem dados para o período" description="Nenhuma métrica registrada. As métricas são geradas automaticamente conforme as OS são concluídas." />
      )}

      {/* Individual cards (for tecnico viewing their own) */}
      {user?.role === 'tecnico' && metricas.find(m => m.user_id === user?.id) && (() => {
        const my = metricas.find(m => m.user_id === user.id);
        const tipos = my.os_por_tipo || {};
        return (
          <div className="glass-card p-4 border-l-4 border-brand" data-testid="minha-performance">
            <h3 className="text-sm font-semibold text-brand mb-3">Minha Performance</h3>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div><p className="text-2xl font-bold text-slate-200">{my.os_total}</p><p className="text-[10px] text-slate-500">OS Total</p></div>
              <div><p className="text-2xl font-bold text-slate-200">{formatHH(my.hh_liquida_min || 0)}</p><p className="text-[10px] text-slate-500">HH Líquida</p></div>
              <div><p className="text-2xl font-bold text-slate-200">{my.inspecoes || 0}</p><p className="text-[10px] text-slate-500">Inspeções</p></div>
            </div>
            <div className="mt-3 grid grid-cols-4 gap-2 text-center text-[10px]">
              {Object.entries(tipos).map(([tipo, count]) => (
                <div key={tipo} className="bg-slate-800/50 rounded p-1.5">
                  <p className="text-sm font-bold text-slate-300">{count}</p>
                  <p className="text-slate-600 capitalize">{tipo.replace(/_/g,' ')}</p>
                </div>
              ))}
            </div>
          </div>
        );
      })()}
    </div>
  );
};


// ============== WHITE LABEL DESIGNER PAGE ==============


export default EquipePage;
