import { useState, useEffect, useCallback, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Box, Wrench, ClipboardCheck, AlertTriangle, FileText, Clock, BarChart3,
  ChevronRight, Plus, Edit, Download, RefreshCw, Eye, Calendar, Target, Shield, Zap,
  Activity, TrendingUp, MapPin, Package
} from "lucide-react";
import { api, useAuth, BACKEND_URL } from "@/lib/api";
import { StatusBadge, PriorityBadge, EmptyState, Loading, PageContainer, Modal, FormInput, Select } from "@/components/shared";
import { toast } from "sonner";

// ============== HEADER ==============
const DossierHeader = ({ ativo, kpis }) => {
  const a = ativo || {};
  const sector = a.sector || {};
  const crit = a.criticidade || 'C';
  const critColor = { A: '#ef4444', B: '#f59e0b', C: '#22c55e' }[crit] || '#64748b';

  return (
    <div className="glass-card p-4 md:p-6" data-testid="dossier-header">
      <div className="flex flex-col md:flex-row gap-4">
        <div className="w-16 h-16 md:w-20 md:h-20 rounded-xl flex items-center justify-center font-mono font-bold text-lg shrink-0" style={{ backgroundColor: `${critColor}15`, color: critColor, border: `1px solid ${critColor}30` }}>
          {(a.tag || '??').substring(0, 5)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-lg md:text-xl font-bold text-slate-100">{a.tag}</h1>
            <span className="text-base text-slate-400">—</span>
            <span className="text-base text-slate-300">{a.nome}</span>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-slate-500">
            {sector.nome && <span className="flex items-center gap-1"><MapPin size={12} /> {sector.nome}</span>}
            {a.tipo_equipamento && <span className="flex items-center gap-1"><Box size={12} /> {a.tipo_equipamento}</span>}
            {a.fabricante && <span className="flex items-center gap-1"><Package size={12} /> {a.fabricante} {a.modelo}</span>}
            {a.numero_serie && <span className="flex items-center gap-1">S/N: {a.numero_serie}</span>}
          </div>
          <div className="flex flex-wrap gap-2 mt-3">
            <span className="text-xs px-2 py-0.5 rounded border capitalize" style={{ borderColor: `${critColor}40`, color: critColor, backgroundColor: `${critColor}10` }}>
              Criticidade {crit}
            </span>
            <StatusBadge status={a.status || a.status_operacional || 'operando'} size="sm" />
          </div>
        </div>
        {/* KPI Cards */}
        <div className="grid grid-cols-3 gap-2 shrink-0">
          <div className="text-center p-2 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <p className="text-sm font-bold text-emerald-400">{kpis?.disponibilidade || 0}%</p>
            <p className="text-[9px] text-slate-500 uppercase">Disp.</p>
          </div>
          <div className="text-center p-2 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <p className="text-sm font-bold text-blue-400">{kpis?.mtbf_horas || 0}h</p>
            <p className="text-[9px] text-slate-500 uppercase">MTBF</p>
          </div>
          <div className="text-center p-2 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <p className="text-sm font-bold text-amber-400">{kpis?.mttr_horas || 0}h</p>
            <p className="text-[9px] text-slate-500 uppercase">MTTR</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============== TAB: Visão Geral ==============
const TabVisaoGeral = ({ kpis, os, inspecoes, solicitacoes }) => {
  const osAbertas = (os || []).filter(o => !['concluida', 'encerrada', 'cancelada'].includes(o.status));
  const osAtrasadas = osAbertas.filter(o => o.data_planejada && new Date(o.data_planejada) < new Date());
  const insPendentes = (inspecoes || []).filter(i => ['pendente', 'em_andamento'].includes(i.status));
  const solPendentes = (solicitacoes || []).filter(s => ['aberta', 'em_analise'].includes(s.status));
  const lastInsp = (inspecoes || []).find(i => i.status === 'concluida');
  const nextPrev = (os || []).find(o => o.tipo === 'preventiva' && ['aberta', 'planejada', 'programada'].includes(o.status));

  const cards = [
    { label: 'OS Abertas', value: osAbertas.length, color: '#6366f1', icon: Wrench },
    { label: 'OS Atrasadas', value: osAtrasadas.length, color: osAtrasadas.length > 0 ? '#ef4444' : '#22c55e', icon: AlertTriangle },
    { label: 'Insp. Pendentes', value: insPendentes.length, color: '#f59e0b', icon: ClipboardCheck },
    { label: 'Solicitacoes', value: solPendentes.length, color: '#06b6d4', icon: Target },
    { label: 'Total OS', value: kpis?.total_os || 0, color: '#8b5cf6', icon: Activity },
    { label: 'Total Inspecoes', value: kpis?.total_inspecoes || 0, color: '#10b981', icon: Shield },
  ];

  return (
    <div className="space-y-4" data-testid="tab-visao-geral">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {cards.map(c => (
          <div key={c.label} className="glass-card p-3 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${c.color}15` }}>
              <c.icon size={18} style={{ color: c.color }} />
            </div>
            <div>
              <p className="text-lg font-bold" style={{ color: c.color }}>{c.value}</p>
              <p className="text-[10px] text-slate-500 uppercase">{c.label}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="glass-card p-3">
          <p className="text-xs text-slate-500 mb-1">Ultima Inspecao</p>
          {lastInsp ? (
            <div className="flex items-center gap-2">
              <StatusBadge status={lastInsp.resultado || lastInsp.status} size="sm" />
              <span className="text-xs text-slate-400">{lastInsp.plano_nome || lastInsp.tipo}</span>
              <span className="text-xs text-slate-600">{(lastInsp.data_conclusao || '').substring(0, 10)}</span>
            </div>
          ) : <p className="text-xs text-slate-600">Nenhuma</p>}
        </div>
        <div className="glass-card p-3">
          <p className="text-xs text-slate-500 mb-1">Proxima Preventiva</p>
          {nextPrev ? (
            <div className="flex items-center gap-2">
              <StatusBadge status={nextPrev.status} size="sm" />
              <span className="text-xs text-slate-400">{nextPrev.titulo}</span>
              <span className="text-xs text-slate-600">{(nextPrev.data_planejada || '').substring(0, 10)}</span>
            </div>
          ) : <p className="text-xs text-slate-600">Nenhuma programada</p>}
        </div>
      </div>
      {/* Costs */}
      <div className="glass-card p-3">
        <p className="text-xs text-slate-500 mb-2">Custos Acumulados</p>
        <div className="flex gap-6">
          <div><p className="text-sm font-bold text-slate-200">R$ {(kpis?.custo_materiais || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</p><p className="text-[10px] text-slate-500">Materiais</p></div>
          <div><p className="text-sm font-bold text-slate-200">R$ {(kpis?.custo_hh || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</p><p className="text-[10px] text-slate-500">Mao de Obra</p></div>
          <div><p className="text-sm font-bold text-brand">R$ {(kpis?.custo_total || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</p><p className="text-[10px] text-slate-500">Total</p></div>
        </div>
      </div>
    </div>
  );
};

// ============== TAB: OS ==============
const TabOS = ({ os, navigate, ativoId }) => {
  const [filtro, setFiltro] = useState('');
  const filtered = useMemo(() => {
    let items = os || [];
    if (filtro) items = items.filter(o => o.status === filtro);
    return items;
  }, [os, filtro]);

  return (
    <div className="space-y-3" data-testid="tab-os">
      <div className="flex items-center gap-2 flex-wrap">
        {['', 'aberta', 'em_execucao', 'concluida', 'programada'].map(f => (
          <button key={f} onClick={() => setFiltro(f)} className={`text-xs px-2 py-1 rounded transition-colors ${filtro === f ? 'bg-brand-10 text-brand border border-brand/30' : 'bg-slate-800 text-slate-400 border border-slate-700'}`}>
            {f || 'Todas'} {f ? `(${(os || []).filter(o => o.status === f).length})` : `(${(os || []).length})`}
          </button>
        ))}
      </div>
      {filtered.length === 0 ? (
        <EmptyState icon={Wrench} title="Nenhuma OS encontrada" description="Este equipamento nao possui ordens de servico" />
      ) : filtered.map(o => (
        <div key={o.id} onClick={() => navigate(`/os/${o.id}`)} className="glass-card p-3 flex items-center gap-3 cursor-pointer hover:border-slate-600 transition-colors" data-testid={`dossier-os-${o.id}`}>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs text-slate-500 font-mono">#{o.numero}</span>
              <span className="text-xs text-slate-600 capitalize">{o.tipo}</span>
            </div>
            <p className="text-sm text-slate-200 truncate">{o.titulo}</p>
            <div className="flex items-center gap-2 mt-1">
              <StatusBadge status={o.status} size="sm" />
              <PriorityBadge priority={o.prioridade} />
              {o.responsavel_nome && <span className="text-xs text-slate-500">{o.responsavel_nome}</span>}
            </div>
          </div>
          <span className="text-xs text-slate-600">{(o.created_at || '').substring(0, 10)}</span>
          <ChevronRight size={16} className="text-slate-600 shrink-0" />
        </div>
      ))}
    </div>
  );
};

// ============== TAB: Planos ==============
const TabPlanos = ({ planos }) => (
  <div className="space-y-3" data-testid="tab-planos">
    {(!planos || planos.length === 0) ? (
      <EmptyState icon={ClipboardCheck} title="Nenhum plano" description="Crie planos de inspecao para este equipamento" />
    ) : planos.map(p => (
      <div key={p.id} className="glass-card p-3" data-testid={`dossier-plano-${p.id}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-slate-200">{p.nome}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 capitalize">{p.tipo}</span>
              {p.disciplina && <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 capitalize">{p.disciplina}</span>}
              {p.frequencia && <span className="text-xs text-slate-500"><Calendar size={12} className="inline mr-1" />{p.frequencia}</span>}
              <span className="text-xs text-slate-500">{(p.perguntas || []).length} perguntas</span>
              <span className="text-xs text-slate-600">v{p.versao || 1}</span>
            </div>
          </div>
          <StatusBadge status={p.status} size="sm" />
        </div>
      </div>
    ))}
  </div>
);

// ============== TAB: Execuções Inspeção ==============
const TabInspecoes = ({ inspecoes, navigate }) => {
  const [filtro, setFiltro] = useState('');
  const filtered = useMemo(() => {
    let items = inspecoes || [];
    if (filtro) items = items.filter(i => i.status === filtro);
    return items;
  }, [inspecoes, filtro]);

  return (
    <div className="space-y-3" data-testid="tab-inspecoes">
      <div className="flex items-center gap-2 flex-wrap">
        {['', 'concluida', 'pendente', 'em_andamento', 'com_pendencias'].map(f => (
          <button key={f} onClick={() => setFiltro(f)} className={`text-xs px-2 py-1 rounded transition-colors ${filtro === f ? 'bg-brand-10 text-brand border border-brand/30' : 'bg-slate-800 text-slate-400 border border-slate-700'}`}>
            {f || 'Todas'} ({(inspecoes || []).filter(i => f ? i.status === f : true).length})
          </button>
        ))}
      </div>
      {filtered.length === 0 ? (
        <EmptyState icon={ClipboardCheck} title="Nenhuma inspecao" description="Nenhuma execucao de inspecao registrada" />
      ) : filtered.map(i => (
        <div key={i.id} onClick={() => navigate(`/inspecoes/${i.id}`)} className="glass-card p-3 cursor-pointer hover:border-slate-600 transition-colors" data-testid={`dossier-insp-${i.id}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-200">{i.plano_nome || i.tipo}</p>
              <div className="flex items-center gap-2 mt-1">
                <StatusBadge status={i.resultado || i.status} size="sm" />
                <span className="text-xs text-slate-500 capitalize">{i.tipo}</span>
                {i.responsavel_nome && <span className="text-xs text-slate-600">{i.responsavel_nome}</span>}
                {i.duracao_minutos && <span className="text-xs text-slate-600"><Clock size={12} className="inline mr-1" />{i.duracao_minutos}min</span>}
              </div>
            </div>
            <span className="text-xs text-slate-600">{(i.data_conclusao || i.created_at || '').substring(0, 10)}</span>
          </div>
          {(i.fotos || []).length > 0 && (
            <div className="flex gap-1 mt-2">
              {i.fotos.slice(0, 4).map((f, idx) => (
                <img key={idx} src={`${BACKEND_URL}${f.file_url || f}`} alt="" className="w-10 h-10 rounded object-cover bg-slate-800" />
              ))}
              {i.fotos.length > 4 && <span className="w-10 h-10 rounded bg-slate-800 flex items-center justify-center text-xs text-slate-500">+{i.fotos.length - 4}</span>}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

// ============== TAB: Solicitações ==============
const TabSolicitacoes = ({ solicitacoes }) => (
  <div className="space-y-3" data-testid="tab-solicitacoes">
    {(!solicitacoes || solicitacoes.length === 0) ? (
      <EmptyState icon={AlertTriangle} title="Nenhuma solicitacao" description="Nenhuma solicitacao registrada" />
    ) : solicitacoes.map(s => (
      <div key={s.id} className="glass-card p-3" data-testid={`dossier-sol-${s.id}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-200">{s.descricao || s.titulo || 'Solicitacao'}</p>
            <div className="flex items-center gap-2 mt-1">
              <StatusBadge status={s.status} size="sm" />
              <span className="text-xs text-slate-500 capitalize">{s.tipo}</span>
              {s.solicitante_nome && <span className="text-xs text-slate-600">{s.solicitante_nome}</span>}
            </div>
          </div>
          <span className="text-xs text-slate-600">{(s.created_at || '').substring(0, 10)}</span>
        </div>
      </div>
    ))}
  </div>
);

// ============== TAB: Documentos ==============
const TabDocumentos = ({ documentos, ativoId }) => {
  const manuais = documentos?.manuais || [];
  const attachments = documentos?.attachments || [];
  return (
    <div className="space-y-3" data-testid="tab-documentos">
      {manuais.length > 0 && (
        <>
          <h4 className="text-xs font-semibold text-secondary uppercase">Manuais ({manuais.length})</h4>
          {manuais.map(m => (
            <div key={m.id} className="glass-card p-3 flex items-center gap-3">
              <FileText size={20} className="text-red-400 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-200 truncate">{m.nome || m.filename || 'Manual'}</p>
                <p className="text-xs text-slate-500">{(m.created_at || '').substring(0, 10)}</p>
              </div>
              <a href={`${BACKEND_URL}${m.url || m.file_url}`} target="_blank" rel="noreferrer" className="p-1.5 rounded hover:bg-slate-800 transition-colors" onClick={e => e.stopPropagation()}>
                <Download size={16} className="text-slate-400" />
              </a>
            </div>
          ))}
        </>
      )}
      {attachments.length > 0 && (
        <>
          <h4 className="text-xs font-semibold text-secondary uppercase mt-4">Anexos ({attachments.length})</h4>
          {attachments.map(a => (
            <div key={a.id} className="glass-card p-3 flex items-center gap-3">
              <FileText size={20} className="text-blue-400 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-200 truncate">{a.nome || a.filename || 'Anexo'}</p>
              </div>
              {a.file_url && (
                <a href={`${BACKEND_URL}${a.file_url}`} target="_blank" rel="noreferrer" className="p-1.5 rounded hover:bg-slate-800 transition-colors">
                  <Eye size={16} className="text-slate-400" />
                </a>
              )}
            </div>
          ))}
        </>
      )}
      {manuais.length === 0 && attachments.length === 0 && (
        <EmptyState icon={FileText} title="Nenhum documento" description="Adicione manuais e documentos ao equipamento" />
      )}
    </div>
  );
};

// ============== TAB: Histórico ==============
const TabHistorico = ({ ativoId }) => {
  const [eventos, setEventos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtro, setFiltro] = useState('');

  useEffect(() => {
    const params = filtro ? { tipo: filtro } : {};
    api.get(`/ativos/${ativoId}/historico`, { params }).then(r => setEventos(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, [ativoId, filtro]);

  const tipoIcon = { os: Wrench, inspecao: ClipboardCheck, anomalia: AlertTriangle, material: Package, parada: Clock };
  const tipoColor = { os: '#6366f1', inspecao: '#10b981', anomalia: '#ef4444', material: '#06b6d4', parada: '#f59e0b' };

  if (loading) return <Loading rows={4} />;

  return (
    <div className="space-y-3" data-testid="tab-historico">
      <div className="flex items-center gap-2 flex-wrap">
        {['', 'os', 'inspecao', 'anomalia', 'material', 'parada'].map(f => (
          <button key={f} onClick={() => { setFiltro(f); setLoading(true); }} className={`text-xs px-2 py-1 rounded transition-colors ${filtro === f ? 'bg-brand-10 text-brand border border-brand/30' : 'bg-slate-800 text-slate-400 border border-slate-700'}`}>
            {f || 'Todos'}
          </button>
        ))}
      </div>
      {eventos.length === 0 ? (
        <EmptyState icon={Clock} title="Sem historico" description="Nenhum evento registrado" />
      ) : (
        <div className="relative pl-6 space-y-0">
          <div className="absolute left-2 top-2 bottom-2 w-px bg-slate-700" />
          {eventos.slice(0, 50).map((e, idx) => {
            const Icon = tipoIcon[e.tipo_evento] || Clock;
            const color = tipoColor[e.tipo_evento] || '#64748b';
            return (
              <div key={e.id || idx} className="relative pb-3">
                <div className="absolute -left-4 w-4 h-4 rounded-full flex items-center justify-center" style={{ backgroundColor: `${color}20`, border: `2px solid ${color}` }}>
                  <Icon size={8} style={{ color }} />
                </div>
                <div className="ml-2 glass-card p-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold" style={{ color }}>{e.titulo}</span>
                    {e.status && <StatusBadge status={e.status} size="sm" />}
                  </div>
                  {e.descricao && <p className="text-xs text-slate-500 mt-0.5">{e.descricao}</p>}
                  <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-600">
                    {e.usuario && <span>{e.usuario}</span>}
                    {e.data && <span>{e.data.substring(0, 16).replace('T', ' ')}</span>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// ============== TAB: Indicadores ==============
const TabIndicadores = ({ kpis, os }) => {
  const osAll = os || [];
  const byType = {};
  osAll.forEach(o => { byType[o.tipo] = (byType[o.tipo] || 0) + 1; });
  const byStat = {};
  osAll.forEach(o => { byStat[o.status] = (byStat[o.status] || 0) + 1; });
  const hhTotal = osAll.reduce((s, o) => s + (o.tempo_execucao_minutos || 0), 0);

  return (
    <div className="space-y-4" data-testid="tab-indicadores">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="glass-card p-3 text-center"><p className="text-lg font-bold text-emerald-400">{kpis?.disponibilidade || 0}%</p><p className="text-[10px] text-slate-500">Disponibilidade</p></div>
        <div className="glass-card p-3 text-center"><p className="text-lg font-bold text-blue-400">{kpis?.mtbf_horas || 0}h</p><p className="text-[10px] text-slate-500">MTBF</p></div>
        <div className="glass-card p-3 text-center"><p className="text-lg font-bold text-amber-400">{kpis?.mttr_horas || 0}h</p><p className="text-[10px] text-slate-500">MTTR</p></div>
        <div className="glass-card p-3 text-center"><p className="text-lg font-bold text-purple-400">{Math.round(hhTotal / 60)}h</p><p className="text-[10px] text-slate-500">HH Total</p></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="glass-card p-3">
          <h4 className="text-xs font-semibold text-secondary uppercase mb-2">OS por Tipo</h4>
          {Object.entries(byType).map(([t, c]) => (
            <div key={t} className="flex items-center justify-between py-1 border-b border-slate-800/50">
              <span className="text-xs text-slate-400 capitalize">{t}</span>
              <span className="text-xs font-bold text-slate-200">{c}</span>
            </div>
          ))}
          {Object.keys(byType).length === 0 && <p className="text-xs text-slate-600">Sem dados</p>}
        </div>
        <div className="glass-card p-3">
          <h4 className="text-xs font-semibold text-secondary uppercase mb-2">Custos</h4>
          <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
            <span className="text-xs text-slate-400">Materiais</span>
            <span className="text-xs font-bold text-slate-200">R$ {(kpis?.custo_materiais || 0).toFixed(2)}</span>
          </div>
          <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
            <span className="text-xs text-slate-400">Mao de Obra</span>
            <span className="text-xs font-bold text-slate-200">R$ {(kpis?.custo_hh || 0).toFixed(2)}</span>
          </div>
          <div className="flex items-center justify-between py-1">
            <span className="text-xs text-brand font-semibold">Total</span>
            <span className="text-xs font-bold text-brand">R$ {(kpis?.custo_total || 0).toFixed(2)}</span>
          </div>
        </div>
      </div>
      <div className="glass-card p-3">
        <h4 className="text-xs font-semibold text-secondary uppercase mb-2">Inspecoes</h4>
        <div className="flex gap-6">
          <div><p className="text-sm font-bold text-slate-200">{kpis?.total_inspecoes || 0}</p><p className="text-[10px] text-slate-500">Realizadas</p></div>
          <div><p className="text-sm font-bold text-amber-400">{kpis?.inspecoes_pendentes || 0}</p><p className="text-[10px] text-slate-500">Pendentes</p></div>
          <div><p className="text-sm font-bold text-red-400">{kpis?.total_falhas || 0}</p><p className="text-[10px] text-slate-500">Falhas</p></div>
        </div>
      </div>
    </div>
  );
};

// ============== MAIN DOSSIER PAGE ==============
const AssetDossierPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('visao');

  const fetchDossier = useCallback(async () => {
    try {
      const res = await api.get(`/ativos/${id}/dossie`);
      setData(res.data);
    } catch {
      toast.error('Erro ao carregar dossie');
      navigate('/ativos');
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => { fetchDossier(); }, [fetchDossier]);

  const tabs = [
    { id: 'visao', label: 'Visao Geral', icon: Eye },
    { id: 'os', label: 'OS', icon: Wrench, count: data?.kpis?.total_os },
    { id: 'planos', label: 'Planos', icon: ClipboardCheck, count: data?.planos?.length },
    { id: 'inspecoes', label: 'Inspecoes', icon: Shield, count: data?.kpis?.total_inspecoes },
    { id: 'solicitacoes', label: 'Solicitacoes', icon: AlertTriangle, count: data?.solicitacoes?.length },
    { id: 'documentos', label: 'Documentos', icon: FileText },
    { id: 'historico', label: 'Historico', icon: Clock },
    { id: 'indicadores', label: 'Indicadores', icon: BarChart3 },
  ];

  if (loading) return <PageContainer><Loading rows={8} /></PageContainer>;
  if (!data) return null;

  return (
    <PageContainer data-testid="asset-dossier">
      {/* Back button */}
      <button onClick={() => navigate('/ativos')} className="flex items-center gap-1 text-xs text-secondary hover:text-slate-300 transition-colors mb-3" data-testid="dossier-back">
        <ArrowLeft size={14} /> Voltar aos Ativos
      </button>

      {/* Header */}
      <DossierHeader ativo={data.ativo} kpis={data.kpis} />

      {/* Tab bar */}
      <div className="flex overflow-x-auto gap-1 mt-4 pb-1 custom-scrollbar" data-testid="dossier-tabs">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs whitespace-nowrap transition-all shrink-0 ${
              activeTab === t.id
                ? 'bg-brand-10 text-brand border border-brand/30 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
            }`}
            data-testid={`dossier-tab-${t.id}`}
          >
            <t.icon size={14} />
            {t.label}
            {t.count !== undefined && t.count > 0 && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${activeTab === t.id ? 'bg-brand/20 text-brand' : 'bg-slate-700 text-slate-500'}`}>
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="mt-4">
        {activeTab === 'visao' && <TabVisaoGeral kpis={data.kpis} os={data.os} inspecoes={data.inspecoes} solicitacoes={data.solicitacoes} />}
        {activeTab === 'os' && <TabOS os={data.os} navigate={navigate} ativoId={id} />}
        {activeTab === 'planos' && <TabPlanos planos={data.planos} />}
        {activeTab === 'inspecoes' && <TabInspecoes inspecoes={data.inspecoes} navigate={navigate} />}
        {activeTab === 'solicitacoes' && <TabSolicitacoes solicitacoes={data.solicitacoes} />}
        {activeTab === 'documentos' && <TabDocumentos documentos={data.documentos} ativoId={id} />}
        {activeTab === 'historico' && <TabHistorico ativoId={id} />}
        {activeTab === 'indicadores' && <TabIndicadores kpis={data.kpis} os={data.os} />}
      </div>
    </PageContainer>
  );
};

export default AssetDossierPage;
