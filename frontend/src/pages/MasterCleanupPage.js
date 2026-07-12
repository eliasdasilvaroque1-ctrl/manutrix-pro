import { useState, useEffect } from "react";
import { Trash2, RefreshCw, AlertTriangle, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import { api, useAuth } from "@/lib/api";
import { normalizeError } from "@/lib/constants";
import { Loading, PageContainer, PageHeader, ConfirmDialog } from "@/components/shared";

const MasterCleanupPage = () => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [adminActions, setAdminActions] = useState([]);
  const [confirmProd, setConfirmProd] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const { user } = useAuth();

  const fetchActions = async () => {
    try {
      const res = await api.get('/master/admin-actions');
      setAdminActions(res.data);
    } catch {}
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchActions(); }, []);

  const cleanableItems = [
    { key: 'ordens_servico', label: 'Ordens de Serviço', icon: Wrench },
    { key: 'inspecoes', label: 'Inspeções', icon: ClipboardCheck },
    { key: 'paradas_programadas', label: 'Paradas Programadas', icon: Calendar },
    { key: 'audit_logs', label: 'Auditoria', icon: Shield },
    { key: 'notificacoes', label: 'Notificações', icon: Bell },
    { key: 'movimentacoes_estoque', label: 'Movimentações de Estoque', icon: Package },
    { key: 'attachments', label: 'Fotos e Uploads', icon: Image },
    { key: 'chat_history', label: 'Histórico de Chat', icon: FileText },
    { key: 'os_materiais', label: 'Materiais Utilizados em OS', icon: Package },
  ];

  const [selected, setSelected] = useState([]);

  const toggleSelect = (key) => {
    setSelected(prev => prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]);
  };

  const handleCleanup = async () => {
    if (selected.length === 0) { toast.error('Selecione pelo menos um item'); return; }
    setLoading(true);
    try {
      const res = await api.post(`/master/cleanup?${selected.map(s => `targets=${s}`).join('&')}`);
      setResults(res.data.deleted);
      toast.success('Limpeza concluída!');
      fetchActions();
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setLoading(false); }
  };

  const handlePrepareProduction = async () => {
    if (confirmText !== 'PREPARAR PRODUCAO') { toast.error('Digite exatamente: PREPARAR PRODUCAO'); return; }
    setLoading(true);
    try {
      const res = await api.post('/master/prepare-production');
      setResults(res.data.deleted);
      toast.success('Ambiente preparado para produção!');
      setConfirmProd(false);
      setConfirmText('');
      fetchActions();
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setLoading(false); }
  };

  if (user?.role !== 'master') return <div className="text-center text-red-400 mt-10">Acesso restrito ao Administrador Master.</div>;

  return (
    <div className="space-y-6" data-testid="master-cleanup-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-primary">Limpeza do Ambiente</h1>
          <p className="text-xs text-slate-500 mt-1">Remova dados de teste para preparar o ambiente de produção</p>
        </div>
        <button onClick={() => setConfirmProd(true)} className="px-4 py-2 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 text-sm font-medium hover:bg-red-500/30 transition-all" data-testid="prepare-production-btn">
          Preparar Ambiente para Produção
        </button>
      </div>

      {/* Selective cleanup */}
      <div className="glass-card p-4">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">Selecionar dados para limpar:</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          {cleanableItems.map(item => {
            const Icon = item.icon;
            const isSelected = selected.includes(item.key);
            return (
              <button key={item.key} onClick={() => toggleSelect(item.key)}
                className={`flex items-center gap-2 p-3 rounded-lg border text-left text-sm transition-all ${isSelected ? 'bg-red-500/10 border-red-500/30 text-red-300' : 'border-slate-700 text-slate-400 hover:border-slate-600'}`}
                data-testid={`cleanup-${item.key}`}
              >
                {isSelected ? <CheckSquare size={16} className="text-red-400 shrink-0" /> : <Square size={16} className="text-slate-600 shrink-0" />}
                <Icon size={14} className="shrink-0" />
                {item.label}
              </button>
            );
          })}
        </div>
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs text-slate-600">{selected.length} item(ns) selecionado(s)</p>
          <button onClick={handleCleanup} disabled={loading || selected.length === 0}
            className="px-4 py-2 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-medium hover:bg-red-500/30 disabled:opacity-50 transition-all" data-testid="cleanup-execute-btn">
            {loading ? 'Limpando...' : 'Executar Limpeza'}
          </button>
        </div>
      </div>

      {/* Results */}
      {results && (
        <div className="glass-card p-4" data-testid="cleanup-results">
          <h3 className="text-sm font-semibold text-brand mb-2">Resultado da Limpeza:</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {Object.entries(results).map(([key, count]) => (
              <div key={key} className="bg-slate-800/50 rounded-lg p-2 text-center">
                <p className="text-lg font-bold text-slate-200">{count}</p>
                <p className="text-[10px] text-slate-500 capitalize">{key.replace(/_/g, ' ')}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Admin actions log */}
      {adminActions.length > 0 && (
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-2">Histórico de Ações Administrativas</h3>
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {adminActions.map(a => (
              <div key={a.id} className="flex items-center justify-between py-2 border-b border-slate-800/50 last:border-0 text-xs">
                <div>
                  <span className="text-slate-400 font-medium">{a.user_nome}</span>
                  <span className="text-slate-600 mx-1">—</span>
                  <span className={`font-medium ${a.action === 'prepare_production' ? 'text-red-400' : 'text-amber-400'}`}>{a.action === 'prepare_production' ? 'Preparação Produção' : 'Limpeza'}</span>
                </div>
                <span className="text-slate-600">{new Date(a.created_at).toLocaleString('pt-BR')}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Prepare production confirmation modal */}
      <Modal isOpen={confirmProd} onClose={() => { setConfirmProd(false); setConfirmText(''); }} title="Preparar Ambiente para Produção">
        <div className="space-y-4">
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p className="text-sm text-red-300 font-medium">Esta ação não poderá ser desfeita.</p>
            <p className="text-xs text-red-400/80 mt-1">Todos os dados operacionais (OS, inspeções, paradas, auditoria, fotos, notificações) serão permanentemente excluídos. Usuários, áreas, ativos, materiais e planos serão mantidos.</p>
          </div>
          <FormInput label="Para confirmar, digite: PREPARAR PRODUCAO">
            <input value={confirmText} onChange={e => setConfirmText(e.target.value)} className="input-industrial w-full px-4" placeholder="PREPARAR PRODUCAO" data-testid="confirm-production-input" />
          </FormInput>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setConfirmProd(false); setConfirmText(''); }} className="btn-secondary">Cancelar</button>
            <button onClick={handlePrepareProduction} disabled={loading || confirmText !== 'PREPARAR PRODUCAO'}
              className="px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-500 disabled:opacity-50 transition-all" data-testid="confirm-production-btn">
              {loading ? 'Processando...' : 'Confirmar'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};



// ============== ORG CONFIG PAGE ==============


export default MasterCleanupPage;
