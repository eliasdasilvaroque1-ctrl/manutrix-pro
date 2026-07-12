import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Box, Activity, FileText, Calendar, Wrench, Clock, AlertTriangle, CheckCircle, XCircle, MapPin, ArrowLeft, Eye, Search, Filter, Hash, Building2 } from "lucide-react";
import { toast } from "sonner";
import { api, BACKEND_URL } from "@/lib/api";
import { StatusBadge, PriorityBadge, Loading, PageContainer, PageHeader, SearchInput, EmptyState } from "@/components/shared";

const PortalPublicoPage = () => {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('info');

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API}/public/ativo/${id}`);
        setData(res.data);
      } catch (err) {
        setError(err.response?.status === 404 ? 'Equipamento não encontrado' : 'Erro ao carregar dados');
      } finally { setLoading(false); }
    })();
  }, [id]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#020617' }}>
      <Cog size={48} className="text-brand animate-spin" />
    </div>
  );

  if (error || !data) return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: '#020617' }}>
      <div className="text-center">
        <AlertCircle size={48} className="text-red-400 mx-auto mb-4" />
        <p className="text-lg text-slate-300 font-semibold">{error || 'Equipamento não encontrado'}</p>
        <p className="text-sm text-slate-500 mt-2">Verifique o QR Code e tente novamente</p>
      </div>
    </div>
  );

  const { ativo, area, unidade, branding: brand, kpis, ultimas_inspecoes, ultimas_os, ultimas_manutencoes, manuais } = data;
  const b = brand || {};
  const statusMap = { operacional: { label: 'Operacional', cls: 'bg-emerald-500/10 text-emerald-400' }, parado: { label: 'Parado', cls: 'bg-red-500/10 text-red-400' }, manutencao: { label: 'Em Manutenção', cls: 'bg-amber-500/10 text-amber-400' } };
  const st = statusMap[ativo.status] || statusMap.operacional;

  const tabs = [
    { id: 'info', label: 'Informações', icon: Box },
    { id: 'historico', label: 'Histórico', icon: Clock },
    { id: 'manuais', label: 'Manuais', icon: FileText },
  ];

  const formatDate = (d) => d ? new Date(d).toLocaleDateString('pt-BR') : '—';

  return (
    <div className="min-h-screen" style={{ backgroundColor: b.cor_fundo || '#020617' }} data-testid="portal-publico">
      {/* Header */}
      <div className="border-b border-slate-800" style={{ backgroundColor: b.cor_menu || '#0f172a' }}>
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          {b.logo_url ? (
            <img src={b.logo_url?.startsWith('http') ? b.logo_url : `${BACKEND_URL}${b.logo_url}`} alt="" className="h-8 object-contain" />
          ) : (
            <span className="font-bold text-sm" style={{ color: b.cor_primaria || '#10b981' }}>{b.nome_empresa || 'CMMS'}</span>
          )}
          <span className="text-[10px] text-slate-500 uppercase tracking-wider">Portal do Equipamento</span>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-5">
        {/* Hero */}
        <div className="glass-card p-5">
          <div className="flex items-start gap-4">
            {ativo.foto_url ? (
              <img src={ativo.foto_url.startsWith('http') ? ativo.foto_url : `${BACKEND_URL}${ativo.foto_url}`}
                alt="" className="w-20 h-20 rounded-xl object-cover border border-slate-700 shrink-0" />
            ) : (
              <div className="w-20 h-20 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: `${b.cor_primaria || '#10b981'}15`, border: `1px solid ${b.cor_primaria || '#10b981'}30` }}>
                <Cog size={32} style={{ color: b.cor_primaria || '#10b981' }} />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="font-mono text-lg font-bold" style={{ color: b.cor_primaria || '#10b981' }} data-testid="portal-tag">{ativo.tag}</p>
              <h1 className="text-xl font-bold text-slate-100" data-testid="portal-nome">{ativo.nome}</h1>
              <p className="text-sm text-slate-400 mt-1">{ativo.tipo_equipamento} {ativo.fabricante ? `• ${ativo.fabricante}` : ''}</p>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${st.cls}`}>{st.label}</span>
                {unidade && <span className="text-xs text-slate-500"><Building2 size={12} className="inline mr-1" />{unidade}</span>}
                {area && <span className="text-xs text-slate-500"><MapPin size={12} className="inline mr-1" />{area}</span>}
              </div>
            </div>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-3 gap-3">
          <div className="glass-card p-3 text-center">
            <p className="text-2xl font-bold" style={{ color: b.cor_primaria || '#10b981' }}>{kpis.disponibilidade || 100}%</p>
            <p className="text-[10px] text-slate-500 uppercase">Disponibilidade</p>
          </div>
          <div className="glass-card p-3 text-center">
            <p className="text-2xl font-bold text-primary">{kpis.total_os}</p>
            <p className="text-[10px] text-slate-500 uppercase">Total OS</p>
          </div>
          <div className="glass-card p-3 text-center">
            <p className="text-2xl font-bold text-primary">{kpis.total_inspecoes}</p>
            <p className="text-[10px] text-slate-500 uppercase">Inspeções</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-900/50 rounded-lg p-1">
          {tabs.map(t => {
            const Icon = t.icon;
            return (
              <button key={t.id} onClick={() => setActiveTab(t.id)}
                className={`flex-1 px-3 py-2 rounded-md text-xs font-medium flex items-center justify-center gap-1.5 transition-all ${
                  activeTab === t.id ? 'bg-brand-20 text-brand' : 'text-slate-400'
                }`} data-testid={`portal-tab-${t.id}`}>
                <Icon size={14} /> {t.label}
              </button>
            );
          })}
        </div>

        {/* Tab: Info */}
        {activeTab === 'info' && (
          <div className="glass-card divide-y divide-slate-800" data-testid="portal-info-tab">
            {[
              ['Fabricante', ativo.fabricante],
              ['Modelo', ativo.modelo],
              ['Nº Série', ativo.numero_serie],
              ['Criticidade', ativo.criticidade],
              ['Área', area],
              ['Tipo', ativo.tipo_equipamento],
            ].filter(([,v]) => v).map(([label, value]) => (
              <div key={label} className="flex items-center justify-between px-4 py-3">
                <span className="text-sm text-slate-500">{label}</span>
                <span className="text-sm text-slate-200 font-medium">{value}</span>
              </div>
            ))}
          </div>
        )}

        {/* Tab: Histórico */}
        {activeTab === 'historico' && (
          <div className="space-y-3" data-testid="portal-historico-tab">
            {ultimas_inspecoes?.length > 0 && (
              <div className="glass-card p-4">
                <h3 className="section-title mb-3"><ClipboardCheck size={14} /> Últimas Inspeções</h3>
                <div className="space-y-2">
                  {ultimas_inspecoes.map((insp, i) => (
                    <div key={i} className="flex items-center justify-between text-sm p-2 rounded-lg bg-slate-900/50">
                      <div>
                        <p className="text-slate-200">{insp.plano_nome || insp.tipo || 'Inspeção'}</p>
                        <p className="text-[10px] text-slate-500">{formatDate(insp.data_conclusao || insp.created_at)}</p>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${insp.resultado === 'conforme' ? 'bg-emerald-500/10 text-emerald-400' : insp.resultado === 'nao_conforme' ? 'bg-red-500/10 text-red-400' : 'bg-slate-700 text-slate-400'}`}>
                        {insp.resultado || insp.status || '—'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {ultimas_os?.length > 0 && (
              <div className="glass-card p-4">
                <h3 className="section-title mb-3"><Wrench size={14} /> Últimas Ordens de Serviço</h3>
                <div className="space-y-2">
                  {ultimas_os.map((os, i) => (
                    <div key={i} className="flex items-center justify-between text-sm p-2 rounded-lg bg-slate-900/50">
                      <div>
                        <p className="text-slate-200">{os.titulo || os.tipo}</p>
                        <p className="text-[10px] text-slate-500">{os.numero && `#${os.numero} • `}{formatDate(os.data_conclusao || os.created_at)}</p>
                      </div>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-400">{os.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {(!ultimas_inspecoes?.length && !ultimas_os?.length) && (
              <div className="glass-card p-8 text-center">
                <Clock size={32} className="text-slate-600 mx-auto mb-2" />
                <p className="text-slate-500 text-sm">Nenhum histórico disponível</p>
              </div>
            )}
          </div>
        )}

        {/* Tab: Manuais */}
        {activeTab === 'manuais' && (
          <div className="space-y-2" data-testid="portal-manuais-tab">
            {manuais?.length > 0 ? manuais.map(m => (
              <a key={m.id} href={m.url?.startsWith('http') ? m.url : `${BACKEND_URL}${m.url}`}
                target="_blank" rel="noopener noreferrer"
                className="glass-card p-4 flex items-center gap-3 hover:border-brand transition-all block">
                <FileText size={20} style={{ color: b.cor_primaria || '#10b981' }} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-200 truncate">{m.nome || 'Manual'}</p>
                  <p className="text-[10px] text-slate-500">{m.tipo_arquivo || 'PDF'}</p>
                </div>
                <Download size={16} className="text-slate-500" />
              </a>
            )) : (
              <div className="glass-card p-8 text-center">
                <FileText size={32} className="text-slate-600 mx-auto mb-2" />
                <p className="text-slate-500 text-sm">Nenhum manual disponível</p>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="text-center pt-4 pb-8">
          {b.mostrar_powered_by && <p className="text-[10px] text-slate-700">Powered by MAINTRIX</p>}
        </div>
      </div>
    </div>
  );
};


// ============== PORTAL DO TÉCNICO (FASE 5) ==============

const PortalTecnicoPage = () => {
  const { id } = useParams();
  const [ativo, setAtivo] = useState(null);
  const [plantas, setPlantas] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { user } = useAuth();
  const { branding } = useBranding() || {};
  const b = branding || {};

  useEffect(() => {
    (async () => {
      try {
        const [res, plantasRes] = await Promise.all([
          api.get(`/ativos/${id}`),
          api.get('/plantas').catch(() => ({ data: [] }))
        ]);
        setAtivo(res.data);
        setPlantas(plantasRes.data);
      } catch { toast.error('Ativo não encontrado'); navigate('/'); }
      finally { setLoading(false); }
    })();
  }, [id, navigate]);

  if (loading) return <Loading rows={4} />;
  if (!ativo) return null;

  const quickActions = [
    { icon: ClipboardCheck, label: 'Executar Inspeção', desc: 'Iniciar inspeção neste equipamento', action: () => navigate(`/inspecoes?ativo_id=${id}`) },
    { icon: Wrench, label: 'Solicitar Serviço', desc: 'Criar solicitação de manutenção', action: () => navigate(`/solicitar?ativo_id=${id}&ativo_tag=${ativo.tag}&ativo_nome=${ativo.nome}`) },
    { icon: AlertTriangle, label: 'Registrar Problema', desc: 'Reportar problema encontrado', action: () => navigate(`/solicitar?ativo_id=${id}&ativo_tag=${ativo.tag}`) },
    { icon: Camera, label: 'Adicionar Fotos', desc: 'Registrar foto do equipamento', action: () => navigate(`/ativos/${id}?tab=docs`) },
    { icon: Clock, label: 'Registrar HH', desc: 'Apontar hora trabalhada', action: () => navigate(`/os?ativo_id=${id}`) },
    { icon: Eye, label: 'Ver Prontuário', desc: 'Prontuário completo do ativo', action: () => navigate(`/ativos/${id}`) },
  ];

  return (
    <div className="space-y-5 animate-fadeInUp" data-testid="portal-tecnico">
      {/* Header */}
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <button onClick={() => navigate(-1)} className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg"><ArrowLeft size={18} className="text-slate-400" /></button>
          <h1 className="text-lg font-bold text-slate-100">Portal do Técnico</h1>
        </div>
        <div className="flex items-start gap-4">
          {ativo.foto_url ? (
            <img src={ativo.foto_url.startsWith('http') ? ativo.foto_url : `${BACKEND_URL}${ativo.foto_url}`}
              alt="" className="w-16 h-16 rounded-xl object-cover border border-slate-700 shrink-0" />
          ) : (
            <div className="w-16 h-16 rounded-xl bg-brand-20 flex items-center justify-center border border-slate-700 shrink-0">
              <Cog size={28} className="text-brand" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="font-mono text-brand text-lg font-bold">{ativo.tag}</p>
            <h2 className="text-lg text-slate-200 font-semibold">{ativo.nome}</h2>
            <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
              {plantas?.[0]?.nome && <span className="flex items-center gap-0.5"><Building2 size={11} />{plantas[0].nome}</span>}
              {ativo.sector?.nome && <span className="flex items-center gap-0.5"><MapPin size={11} />{ativo.sector.nome}</span>}
              {ativo.tipo_equipamento && <span>• {ativo.tipo_equipamento}</span>}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3" data-testid="portal-tecnico-actions">
        {quickActions.map((action, idx) => {
          const Icon = action.icon;
          return (
            <button key={idx} onClick={action.action}
              className="glass-card p-4 text-left hover:border-brand transition-all active:scale-[0.98] group"
              data-testid={`portal-action-${idx}`}>
              <div className="w-10 h-10 rounded-lg bg-brand-10 flex items-center justify-center mb-3 group-hover:bg-brand-20 transition-colors">
                <Icon size={20} className="text-brand" />
              </div>
              <p className="text-sm font-semibold text-slate-200">{action.label}</p>
              <p className="text-[10px] text-slate-500 mt-0.5">{action.desc}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
};


// ============== MASTER CLEANUP PAGE ==============


export { PortalPublicoPage, PortalTecnicoPage };
