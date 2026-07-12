import { useState, useEffect } from "react";
import { Plus, AlertTriangle, ChevronDown, ChevronUp, Edit3, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, useAuth } from "@/lib/api";
import { normalizeError } from "@/lib/constants";
import { EmptyState, Loading, Modal, PageContainer, PageHeader, PageToolbar, SearchInput, FormInput, Select, ConfirmDialog } from "@/components/shared";
import { MaterialThumbnail, MaterialImageModal, MaterialImageUploader } from "@/components/widgets/MaterialComponents";
import ExportButtons from "@/components/widgets/ExportButtons";

const EstoquePage = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCritico, setShowCritico] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const [expandedItem, setExpandedItem] = useState(null);
  const [expandedMovs, setExpandedMovs] = useState([]);
  const [loadingMovs, setLoadingMovs] = useState(false);
  const [viewImage, setViewImage] = useState(null);
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  
  useEffect(() => {
    if (searchParams.get('critico') === 'true') setShowCritico(true);
  }, [searchParams]);
  
  const fetchData = async () => {
    try {
      const response = await api.get(`/estoque${showCritico ? '?critico=true' : ''}`);
      setItems(response.data);
    } catch (error) {
      toast.error('Erro ao carregar estoque');
    } finally {
      setLoading(false);
    }
  };
  
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchData(); }, [showCritico]);
  
  const handleDelete = async () => {
    try {
      await api.delete(`/estoque/${deleteItem.id}`);
      toast.success('Item excluído!');
      setDeleteItem(null);
      fetchData();
    } catch (error) {
      toast.error('Erro ao excluir');
    }
  };
  
  const filtered = search ? items.filter(i => 
    i.nome.toLowerCase().includes(search.toLowerCase()) || (i.sku || '').toLowerCase().includes(search.toLowerCase())
  ) : items;

  // E1: Toggle expand to show movimentações
  const toggleExpand = async (itemId) => {
    if (expandedItem === itemId) {
      setExpandedItem(null);
      setExpandedMovs([]);
      return;
    }
    setExpandedItem(itemId);
    setLoadingMovs(true);
    try {
      const res = await api.get(`/estoque/${itemId}`);
      setExpandedMovs(res.data.movimentacoes || []);
    } catch { setExpandedMovs([]); }
    finally { setLoadingMovs(false); }
  };

  const movTipoConfig = {
    entrada: { label: 'Entrada', class: 'text-emerald-400' },
    saida: { label: 'Saída', class: 'text-red-400' },
    devolucao: { label: 'Devolução', class: 'text-blue-400' },
    ajuste: { label: 'Ajuste', class: 'text-amber-400' },
  };
  
  return (
    <PageContainer>
      <PageHeader title="Estoque">
        <ExportButtons entity="estoque" />
        <button onClick={() => { setEditItem(null); setShowModal(true); }} className="btn-primary flex items-center gap-2" data-testid="add-estoque-btn">
          <Plus size={20} /> Novo Item
        </button>
      </PageHeader>
      
      <PageToolbar>
        <SearchInput value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar por nome ou código..." />
        <button
          onClick={() => setShowCritico(!showCritico)}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 ${showCritico ? 'bg-red-500 text-white' : 'bg-surface text-secondary'}`}
        >
          <AlertTriangle size={18} /> Crítico
        </button>
      </PageToolbar>
      
      {loading ? <Loading rows={5} /> : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((item) => (
            <div key={item.id} className={`glass-card hover:border-slate-600 transition-all group ${item.is_critico ? 'border-red-500/50' : ''}`}>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <MaterialThumbnail
                      images={item.images}
                      nome={item.nome}
                      categoria={item.categoria}
                      size="md"
                      onClick={() => (item.images || [])[0] && setViewImage({ src: item.images[0], nome: item.nome })}
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-brand text-sm">{item.sku}</span>
                        <span className="text-xs text-slate-500 px-2 py-0.5 bg-slate-800 rounded capitalize">{item.categoria}</span>
                      </div>
                      <p className="text-slate-100">{item.nome}</p>
                      {item.prateleira && <p className="text-xs text-slate-500"><MapPin size={12} className="inline mr-1" />{item.almoxarifado} - {item.prateleira}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {/* E1: Expand button */}
                    <button onClick={() => toggleExpand(item.id)} className="p-2 hover:bg-slate-700 rounded-lg transition-colors" title="Ver movimentações" data-testid={`expand-estoque-${item.id}`}>
                      {expandedItem === item.id ? <ChevronUp size={16} className="text-brand" /> : <ChevronDown size={16} className="text-slate-400" />}
                    </button>
                    {['admin','master'].includes(user?.role) && (
                      <div className="hidden group-hover:flex items-center gap-1">
                        <button onClick={() => { setEditItem(item); setShowModal(true); }} className="p-2 hover:bg-slate-700 rounded-lg" title="Editar">
                          <Edit3 size={15} className="text-blue-400" />
                        </button>
                        <button onClick={() => setDeleteItem(item)} className="p-2 hover:bg-red-500/10 rounded-lg" title="Excluir">
                          <Trash2 size={15} className="text-red-400" />
                        </button>
                      </div>
                    )}
                    <div className="text-right">
                      <p className={`text-xl font-bold ${item.is_critico ? 'text-red-400' : 'text-slate-200'}`}>{item.quantidade}</p>
                      <p className="text-xs text-slate-500">{item.unidade}</p>
                    </div>
                  </div>
                </div>
                {item.is_critico && (
                  <div className="mt-2 flex items-center gap-2 text-red-400 text-xs">
                    <AlertTriangle size={14} />
                    Estoque crítico (mín: {item.estoque_minimo})
                  </div>
                )}
              </div>
              {/* E1: Expandable movimentações */}
              {expandedItem === item.id && (
                <div className="border-t border-slate-800 px-4 py-3" data-testid={`movs-${item.id}`}>
                  <p className="text-xs text-slate-500 uppercase font-semibold mb-2">Últimas Movimentações</p>
                  {loadingMovs ? (
                    <div className="py-2 text-xs text-slate-600 animate-pulse">Carregando...</div>
                  ) : expandedMovs.length > 0 ? (
                    <div className="space-y-1.5">
                      {expandedMovs.slice(0, 5).map((mov, idx) => {
                        const cfg = movTipoConfig[mov.tipo] || { label: mov.tipo, class: 'text-slate-400' };
                        return (
                          <div key={mov.id || idx} className="flex items-center justify-between text-xs py-1 border-b border-slate-800/50 last:border-0">
                            <div className="flex items-center gap-2">
                              <span className={`font-medium w-16 ${cfg.class}`}>{cfg.label}</span>
                              <span className="text-slate-300">{mov.quantidade > 0 ? '+' : ''}{mov.quantidade} {item.unidade}</span>
                              {mov.motivo && <span className="text-slate-600 truncate max-w-[200px]">— {mov.motivo}</span>}
                            </div>
                            <span className="text-slate-600 shrink-0">{mov.created_at ? new Date(mov.created_at).toLocaleDateString('pt-BR', {day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}) : ''}</span>
                          </div>
                        );
                      })}
                      {expandedMovs.length > 5 && <p className="text-xs text-slate-600 text-center pt-1">+{expandedMovs.length - 5} movimentações anteriores</p>}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-600 py-1">Nenhuma movimentação registrada</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon={Package} title="Nenhum item encontrado" description="Adicione itens ao estoque." action={() => setShowModal(true)} actionLabel="Novo Item" />
      )}
      
      <ModalNovoEstoque
        isOpen={showModal}
        onClose={() => { setShowModal(false); setEditItem(null); }}
        onSuccess={fetchData}
        editData={editItem}
      />
      
      <ConfirmDialog
        isOpen={!!deleteItem}
        onClose={() => setDeleteItem(null)}
        onConfirm={handleDelete}
        title="Excluir Item"
        message={`Tem certeza que deseja excluir "${deleteItem?.sku || deleteItem?.nome}"?`}
        confirmText="Excluir"
        danger
      />
      {viewImage && <MaterialImageModal src={viewImage.src} nome={viewImage.nome} onClose={() => setViewImage(null)} />}
    </PageContainer>
  );
};

// Inspeções Page

export default EstoquePage;
