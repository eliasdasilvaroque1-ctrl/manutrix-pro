import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { BookOpen, Plus, FileText, ArrowLeft, Upload, Trash2, Download, Edit, Eye, Search } from "lucide-react";
import { toast } from "sonner";
import { api, useAuth } from "@/lib/api";
import { normalizeError } from "@/lib/constants";
import { EmptyState, Loading, Modal, PageContainer, PageHeader, PageToolbar, SearchInput, FormInput } from "@/components/shared";

const BibliotecaPage = () => {
  const [tab, setTab] = useState('categorias');
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [categorias, setCategorias] = useState([]);
  const [fabricantes, setFabricantes] = useState([]);
  const { user } = useAuth();

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = search ? `?search=${search}` : '';
      const res = await api.get(`/biblioteca/${tab}${params}`);
      setItems(res.data.items || res.data);
      setTotal(res.data.total || (res.data.items || res.data).length);
      if (tab === 'modelos-mestre' || tab === 'fabricantes') {
        const catRes = await api.get('/biblioteca/categorias');
        setCategorias(catRes.data.items || []);
      }
      if (tab === 'modelos-mestre') {
        const fabRes = await api.get('/biblioteca/fabricantes');
        setFabricantes(fabRes.data.items || []);
      }
    } catch { toast.error('Erro ao carregar dados'); }
    finally { setLoading(false); }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchData(); }, [tab, search]);

  const getEmptyForm = () => {
    if (tab === 'categorias') return { nome: '', descricao: '' };
    if (tab === 'fabricantes') return { nome: '', descricao: '', categoria_id: '', pais: '', website: '' };
    return { nome: '', modelo: '', categoria_id: '', fabricante_id: '', descricao: '' };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editItem) {
        await api.put(`/biblioteca/${tab}/${editItem.id}`, form);
        toast.success('Atualizado!');
      } else {
        await api.post(`/biblioteca/${tab}`, form);
        toast.success('Criado!');
      }
      setShowModal(false); setEditItem(null); setForm(getEmptyForm());
      fetchData();
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/biblioteca/${tab}/${deleteItem.id}`);
      toast.success('Excluído!');
      setDeleteItem(null);
      fetchData();
    } catch (err) { toast.error(normalizeError(err)); }
  };

  const tabs = [
    { id: 'categorias', label: 'Categorias', icon: Layers },
    { id: 'fabricantes', label: 'Fabricantes', icon: Factory },
    { id: 'modelos-mestre', label: 'Modelos Mestres', icon: BookOpen },
  ];

  return (
    <div className="space-y-4" data-testid="biblioteca-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-primary">Biblioteca de Modelos</h1>
        <button onClick={() => { setEditItem(null); setForm(getEmptyForm()); setShowModal(true); }} className="btn-primary flex items-center gap-2" data-testid="biblioteca-add-btn">
          <Plus size={20} /> Novo
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-800 pb-1">
        {tabs.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} onClick={() => { setTab(t.id); setSearch(''); }}
              className={`px-4 py-2 rounded-t-lg text-xs font-medium flex items-center gap-2 transition-all ${tab === t.id ? 'bg-slate-800 text-brand border-b-2 border-brand' : 'text-slate-500 hover:text-slate-300'}`}
              data-testid={`bib-tab-${t.id}`}
            ><Icon size={14} />{t.label}</button>
          );
        })}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar..." className="input-industrial w-full pl-9 pr-4 text-sm" data-testid="bib-search" />
      </div>

      <p className="text-xs text-slate-600">{total} registro(s)</p>

      {/* List */}
      {loading ? <Loading rows={5} /> : items.length > 0 ? (
        <div className="space-y-2">
          {items.map(item => (
            <div key={item.id} className="glass-card p-4 hover:border-slate-600 transition-all group">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-brand-10"><BookOpen size={20} className="text-brand" /></div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-brand text-xs">{item.codigo}</span>
                      {item.status === 'inativo' && <span className="text-[9px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/30">Inativo</span>}
                    </div>
                    <p className="text-slate-100 font-medium">{item.nome}</p>
                    <div className="flex gap-2 text-xs text-slate-500 mt-0.5">
                      {item.categoria_nome && <span className="bg-slate-800 px-1.5 py-0.5 rounded">{item.categoria_nome}</span>}
                      {item.fabricante_nome && <span className="bg-slate-800 px-1.5 py-0.5 rounded">{item.fabricante_nome}</span>}
                      {item.modelo && <span>Modelo: {item.modelo}</span>}
                      {item.versao && <span>v{item.versao}</span>}
                      {item.planos?.length > 0 && <span className="text-blue-400">{item.planos.length} plano(s)</span>}
                    </div>
                  </div>
                </div>
                <div className="hidden group-hover:flex items-center gap-1">
                  <button onClick={() => { setEditItem(item); setForm(tab === 'categorias' ? { nome: item.nome, descricao: item.descricao || '' } : tab === 'fabricantes' ? { nome: item.nome, descricao: item.descricao || '', categoria_id: item.categoria_id || '', pais: item.pais || '', website: item.website || '' } : { nome: item.nome, modelo: item.modelo || '', categoria_id: item.categoria_id || '', fabricante_id: item.fabricante_id || '', descricao: item.descricao || '' }); setShowModal(true); }} className="p-2 hover:bg-slate-700 rounded-lg"><Edit size={16} className="text-slate-400" /></button>
                  <button onClick={() => setDeleteItem(item)} className="p-2 hover:bg-red-500/10 rounded-lg"><Trash2 size={16} className="text-red-400" /></button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon={BookOpen} title={`Nenhum registro em ${tab}`} description="Crie o primeiro item." action={() => { setForm(getEmptyForm()); setShowModal(true); }} actionLabel="Criar" />
      )}

      {/* Modal */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editItem ? `Editar ${tab === 'categorias' ? 'Categoria' : tab === 'fabricantes' ? 'Fabricante' : 'Modelo Mestre'}` : `Novo ${tab === 'categorias' ? 'Categoria' : tab === 'fabricantes' ? 'Fabricante' : 'Modelo Mestre'}`}>
        <form onSubmit={handleSubmit} className="space-y-3">
          <FormInput label="Nome" required><input value={form.nome || ''} onChange={e => setForm({...form, nome: e.target.value})} className="input-industrial w-full px-4" required data-testid="bib-nome" /></FormInput>
          {tab === 'fabricantes' && (
            <>
              <FormInput label="Categoria"><select value={form.categoria_id || ''} onChange={e => setForm({...form, categoria_id: e.target.value})} className="input-industrial w-full px-4"><option value="">Selecione...</option>{categorias.map(c => <option key={c.id} value={c.id}>{c.nome}</option>)}</select></FormInput>
              <FormInput label="País"><input value={form.pais || ''} onChange={e => setForm({...form, pais: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
            </>
          )}
          {tab === 'modelos-mestre' && (
            <>
              <FormInput label="Modelo"><input value={form.modelo || ''} onChange={e => setForm({...form, modelo: e.target.value})} className="input-industrial w-full px-4" placeholder="Ex: C125" data-testid="bib-modelo" /></FormInput>
              <FormInput label="Categoria"><select value={form.categoria_id || ''} onChange={e => setForm({...form, categoria_id: e.target.value})} className="input-industrial w-full px-4"><option value="">Selecione...</option>{categorias.map(c => <option key={c.id} value={c.id}>{c.nome}</option>)}</select></FormInput>
              <FormInput label="Fabricante"><select value={form.fabricante_id || ''} onChange={e => setForm({...form, fabricante_id: e.target.value})} className="input-industrial w-full px-4"><option value="">Selecione...</option>{fabricantes.map(f => <option key={f.id} value={f.id}>{f.nome}</option>)}</select></FormInput>
            </>
          )}
          <FormInput label="Descrição"><textarea value={form.descricao || ''} onChange={e => setForm({...form, descricao: e.target.value})} className="input-industrial w-full px-4 min-h-[60px]" /></FormInput>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary" data-testid="bib-save">{saving ? 'Salvando...' : 'Salvar'}</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog isOpen={!!deleteItem} onClose={() => setDeleteItem(null)} onConfirm={handleDelete} title="Excluir" message={`Excluir "${deleteItem?.nome}"? Esta ação não poderá ser desfeita.`} confirmText="Excluir" danger />
    </div>
  );
};


// ============== EQUIPE PAGE (Dashboard + Ranking + Produtividade) ==============


export default BibliotecaPage;
