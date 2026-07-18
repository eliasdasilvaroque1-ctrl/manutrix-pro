import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Plus, AlertTriangle, ChevronDown, ChevronUp, Edit3, Trash2, MapPin, Package, DollarSign, Tag, Zap, RefreshCw, Save } from "lucide-react";
import { toast } from "sonner";
import { api, useAuth } from "../lib/api";
import { normalizeError } from "../lib/constants";
import { EmptyState, Loading, Modal, PageContainer, PageHeader, PageToolbar, SearchInput, FormInput, Select, ConfirmDialog } from "../components/shared";
import { MaterialThumbnail, MaterialImageModal, MaterialImageUploader } from "../components/widgets/MaterialComponents";
import ExportButtons from "../components/widgets/ExportButtons";

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

const ModalNovoEstoque = ({ isOpen, onClose, onSuccess, editData = null }) => {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    sku: '', nome: '', descricao: '', categoria: 'outro',
    quantidade: 0, estoque_minimo: 0, estoque_maximo: '',
    unidade: 'UN', custo_unitario: 0, fornecedor: '',
    almoxarifado: 'Principal', prateleira: '', posicao: '',
    alertar_minimo: true, item_critico: false
  });
  
  useEffect(() => {
    if (editData) {
      setForm({
        sku: editData.sku || '',
        nome: editData.nome || '',
        descricao: editData.descricao || '',
        categoria: editData.categoria || 'outros',
        quantidade: editData.quantidade || 0,
        estoque_minimo: editData.estoque_minimo || 0,
        estoque_maximo: editData.estoque_maximo || '',
        unidade: editData.unidade || 'UN',
        custo_unitario: editData.custo_unitario || 0,
        fornecedor: editData.fornecedor || '',
        almoxarifado: editData.almoxarifado || 'Principal',
        prateleira: editData.prateleira || '',
        posicao: editData.posicao || '',
        alertar_minimo: editData.alertar_minimo ?? true,
        item_critico: editData.item_critico ?? false
      });
    } else {
      setForm({
        sku: '', nome: '', descricao: '', categoria: 'outro',
        quantidade: 0, estoque_minimo: 0, estoque_maximo: '',
        unidade: 'UN', custo_unitario: 0, fornecedor: '',
        almoxarifado: 'Principal', prateleira: '', posicao: '',
        alertar_minimo: true, item_critico: false
      });
    }
  }, [editData, isOpen]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.nome) {
      toast.error('Nome é obrigatório');
      return;
    }
    
    setLoading(true);
    try {
      const payload = {
        ...form,
        quantidade: parseFloat(form.quantidade) || 0,
        estoque_minimo: parseFloat(form.estoque_minimo) || 0,
        estoque_maximo: form.estoque_maximo ? parseFloat(form.estoque_maximo) : null,
        custo_unitario: parseFloat(form.custo_unitario) || 0,
      };
      
      if (editData) {
        await api.put(`/estoque/${editData.id}`, payload);
        toast.success('Item atualizado com sucesso!');
      } else {
        await api.post('/estoque', payload);
        toast.success('Item criado com sucesso!');
      }
      onSuccess();
      onClose();
    } catch (error) {
      toast.error(normalizeError(error));
    } finally {
      setLoading(false);
    }
  };
  
  const categorias = [
    { value: 'rolamento', label: 'Rolamento' },
    { value: 'lubrificante', label: 'Lubrificante' },
    { value: 'correia', label: 'Correia' },
    { value: 'vedacao', label: 'Vedação' },
    { value: 'filtro', label: 'Filtro' },
    { value: 'eletrico', label: 'Elétrico' },
    { value: 'mecanico', label: 'Mecânico' },
    { value: 'hidraulico', label: 'Hidráulico' },
    { value: 'pneumatico', label: 'Pneumático' },
    { value: 'instrumentacao', label: 'Instrumentação' },
    { value: 'outro', label: 'Outro' },
  ];
  
  const unidades = [
    { value: 'UN', label: 'Unidade (UN)' },
    { value: 'L', label: 'Litro (L)' },
    { value: 'KG', label: 'Quilograma (KG)' },
    { value: 'M', label: 'Metro (M)' },
    { value: 'PC', label: 'Peça (PC)' },
    { value: 'CX', label: 'Caixa (CX)' },
  ];
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={editData ? "Editar Item" : "Novo Item de Estoque"} size="lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-brand flex items-center gap-2">
            <Tag size={16} /> Identificação
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Código">
              <input type="text" value={form.sku} onChange={(e) => setForm({...form, sku: e.target.value.toUpperCase()})} placeholder="Auto-gerado se vazio" className="input-industrial w-full px-4 font-mono" />
            </FormInput>
            <FormInput label="Nome do Item" required>
              <input type="text" value={form.nome} onChange={(e) => setForm({...form, nome: e.target.value})} placeholder="Ex: Rolamento 6205-2RS" className="input-industrial w-full px-4" required />
            </FormInput>
            <FormInput label="Categoria">
              <Select value={form.categoria} onChange={(val) => setForm({...form, categoria: val})} options={categorias} />
            </FormInput>
            <FormInput label="Fornecedor">
              <input type="text" value={form.fornecedor} onChange={(e) => setForm({...form, fornecedor: e.target.value})} className="input-industrial w-full px-4" />
            </FormInput>
          </div>
          <FormInput label="Descrição">
            <textarea value={form.descricao} onChange={(e) => setForm({...form, descricao: e.target.value})} className="input-industrial w-full px-4 py-3" rows={2} />
          </FormInput>
        </div>
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wider flex items-center gap-2">
            <Package size={16} /> Controle de Estoque
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <FormInput label="Quantidade Atual"><input type="number" value={form.quantidade} onChange={(e) => setForm({...form, quantidade: e.target.value})} className="input-industrial w-full px-4" min="0" /></FormInput>
            <FormInput label="Estoque Mínimo"><input type="number" value={form.estoque_minimo} onChange={(e) => setForm({...form, estoque_minimo: e.target.value})} className="input-industrial w-full px-4" min="0" /></FormInput>
            <FormInput label="Estoque Máximo"><input type="number" value={form.estoque_maximo} onChange={(e) => setForm({...form, estoque_maximo: e.target.value})} className="input-industrial w-full px-4" min="0" /></FormInput>
            <FormInput label="Unidade"><Select value={form.unidade} onChange={(val) => setForm({...form, unidade: val})} options={unidades} /></FormInput>
          </div>
        </div>
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-2">
            <DollarSign size={16} /> Financeiro
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Custo Unitário (R$)"><input type="number" step="0.01" value={form.custo_unitario} onChange={(e) => setForm({...form, custo_unitario: e.target.value})} className="input-industrial w-full px-4" min="0" /></FormInput>
            <div className="flex items-end">
              <div className="glass-card p-3 w-full">
                <p className="text-xs text-slate-500">Valor Total em Estoque</p>
                <p className="text-lg font-bold text-brand">R$ {((parseFloat(form.quantidade) || 0) * (parseFloat(form.custo_unitario) || 0)).toFixed(2)}</p>
              </div>
            </div>
          </div>
        </div>
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-2">
            <MapPin size={16} /> Localização
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <FormInput label="Almoxarifado"><input type="text" value={form.almoxarifado} onChange={(e) => setForm({...form, almoxarifado: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
            <FormInput label="Prateleira"><input type="text" value={form.prateleira} onChange={(e) => setForm({...form, prateleira: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: A-01" /></FormInput>
            <FormInput label="Posição"><input type="text" value={form.posicao} onChange={(e) => setForm({...form, posicao: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
          </div>
        </div>
        <div className="glass-card p-4 space-y-4">
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider flex items-center gap-2">
            <Zap size={16} /> Automação
          </h3>
          <div className="flex flex-wrap gap-6">
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" checked={form.alertar_minimo} onChange={(e) => setForm({...form, alertar_minimo: e.target.checked})} className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-brand focus:ring-brand" />
              <span className="text-slate-300">Alertar estoque mínimo</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" checked={form.item_critico} onChange={(e) => setForm({...form, item_critico: e.target.checked})} className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-red-500 focus:ring-red-500" />
              <span className="text-slate-300">Item crítico</span>
            </label>
          </div>
        </div>
        {editData && (
          <div className="glass-card p-4">
            <MaterialImageUploader tipo="estoque" itemId={editData.id} images={editData.images} onUpdate={(imgs) => { editData.images = imgs; }} />
          </div>
        )}
        <div className="flex gap-3 justify-end pt-4 border-t border-slate-800">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
            {loading ? <RefreshCw size={18} className="animate-spin" /> : <Save size={18} />}
            {loading ? 'Salvando...' : 'Salvar Item'}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default EstoquePage;
