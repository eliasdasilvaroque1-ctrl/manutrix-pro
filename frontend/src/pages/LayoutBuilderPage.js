import { useState, useEffect, useCallback } from "react";
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, TouchSensor, useSensor, useSensors } from "@dnd-kit/core";
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy, useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Plus, Trash2, Eye, EyeOff, ChevronUp, ChevronDown, Save, FileText, Copy, Send, ArrowLeft, Settings, Printer, RotateCcw } from "lucide-react";
import { api, useAuth } from "@/lib/api";
import { toast } from "sonner";

const BLOCK_CATALOG = [
  { type: "header", label: "Cabeçalho", icon: "📄", singular: true, category: "estrutura" },
  { type: "footer", label: "Rodapé", icon: "📋", singular: true, category: "estrutura" },
  { type: "equipment", label: "Equipamento", icon: "⚙", category: "dados" },
  { type: "info", label: "Informações", icon: "ℹ", category: "dados" },
  { type: "description", label: "Descrição", icon: "📝", category: "dados" },
  { type: "team", label: "Equipe", icon: "👥", category: "dados" },
  { type: "dates", label: "Datas/Tempos", icon: "📅", category: "dados" },
  { type: "procedure", label: "Procedimento", icon: "📑", category: "biblioteca", hasRef: true, refType: "procedimentos_padrao" },
  { type: "safety", label: "Segurança/APR", icon: "🛡", category: "biblioteca", hasRef: true, refType: "seguranca_padrao" },
  { type: "checklist", label: "Checklist", icon: "✓", category: "biblioteca", hasRef: true, refType: "checklists_padrao" },
  { type: "signature", label: "Assinatura", icon: "✍", category: "biblioteca", hasRef: true, refType: "blocos_assinatura" },
  { type: "custom_fields", label: "Campos Personalizados", icon: "⊞", category: "biblioteca", hasRef: true, refType: "campos_personalizados" },
  { type: "qr_code", label: "QR Code", icon: "▣", category: "conteudo" },
  { type: "photos", label: "Fotografias", icon: "📷", category: "conteudo" },
  { type: "materials", label: "Materiais", icon: "📦", category: "conteudo" },
  { type: "indicators", label: "Indicadores", icon: "📊", category: "conteudo" },
  { type: "history", label: "Histórico", icon: "🕐", category: "conteudo" },
  { type: "observations", label: "Observações", icon: "💬", category: "conteudo" },
  { type: "free_text", label: "Texto Livre", icon: "T", category: "especial" },
  { type: "separator", label: "Separador", icon: "—", category: "especial" },
  { type: "page_break", label: "Quebra de Página", icon: "⏎", category: "especial" },
];

const CATEGORIES = [
  { id: "estrutura", label: "Estrutura" },
  { id: "dados", label: "Dados da OS" },
  { id: "biblioteca", label: "Biblioteca" },
  { id: "conteudo", label: "Conteúdo" },
  { id: "especial", label: "Especial" },
];

const uuid = () => crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;

// ===== SORTABLE BLOCK ITEM =====
const SortableBlock = ({ block, isSelected, onSelect, onToggleVisible, onRemove, onMoveUp, onMoveDown, isFirst, isLast }) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: block.id });
  const style = { transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.5 : 1 };
  const catalog = BLOCK_CATALOG.find(b => b.type === block.type);

  return (
    <div ref={setNodeRef} style={style} onClick={() => onSelect(block.id)}
      className={`flex items-center gap-2 p-2.5 rounded-lg border transition-all cursor-pointer group ${isSelected ? 'border-brand bg-brand/10' : 'border-slate-700 bg-slate-800/60 hover:border-slate-600'} ${!block.visible ? 'opacity-40' : ''}`}
      data-testid={`block-${block.id}`}>
      <button {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing text-slate-500 hover:text-white shrink-0" data-testid={`drag-${block.id}`}>
        <GripVertical size={16} />
      </button>
      <span className="text-sm shrink-0 w-5 text-center">{catalog?.icon || '?'}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-primary truncate">{catalog?.label || block.type}</p>
        {block.settings?.title && <p className="text-xs text-slate-500 truncate">{block.settings.title}</p>}
        {block.library_ref_id && <p className="text-xs text-brand truncate">Ref: {block.library_ref_id.slice(0, 8)}...</p>}
      </div>
      <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
        <button onClick={e => { e.stopPropagation(); onMoveUp(); }} disabled={isFirst} className="p-1 text-slate-500 hover:text-white disabled:opacity-20" title="Mover para cima"><ChevronUp size={14} /></button>
        <button onClick={e => { e.stopPropagation(); onMoveDown(); }} disabled={isLast} className="p-1 text-slate-500 hover:text-white disabled:opacity-20" title="Mover para baixo"><ChevronDown size={14} /></button>
        <button onClick={e => { e.stopPropagation(); onToggleVisible(); }} className="p-1 text-slate-500 hover:text-amber-400" title={block.visible ? 'Ocultar' : 'Mostrar'}>
          {block.visible ? <Eye size={14} /> : <EyeOff size={14} />}
        </button>
        <button onClick={e => { e.stopPropagation(); onRemove(); }} className="p-1 text-slate-500 hover:text-red-400" title="Remover"><Trash2 size={14} /></button>
      </div>
    </div>
  );
};

// ===== BLOCK PROPERTIES PANEL =====
const BlockProperties = ({ block, onChange, libraryItems }) => {
  if (!block) return <div className="text-sm text-slate-500 p-4 text-center">Selecione um bloco para editar suas propriedades</div>;
  const catalog = BLOCK_CATALOG.find(b => b.type === block.type);

  return (
    <div className="space-y-3 p-3" data-testid="block-properties">
      <h4 className="text-xs font-bold text-slate-400 uppercase">{catalog?.label}</h4>
      {block.type === 'free_text' && (
        <div>
          <label className="text-xs text-slate-500">Título</label>
          <input value={block.settings?.title || ''} onChange={e => onChange({ ...block, settings: { ...block.settings, title: e.target.value } })} className="input-industrial w-full px-2 text-sm mt-1" placeholder="Título do bloco" />
          <label className="text-xs text-slate-500 mt-2 block">Conteúdo</label>
          <textarea value={block.settings?.content || ''} onChange={e => onChange({ ...block, settings: { ...block.settings, content: e.target.value } })} className="input-industrial w-full px-2 text-sm mt-1 h-20" placeholder="Texto livre..." />
        </div>
      )}
      {catalog?.hasRef && (
        <div>
          <label className="text-xs text-slate-500">Referência da Biblioteca</label>
          <select value={block.library_ref_id || ''} onChange={e => onChange({ ...block, library_ref_id: e.target.value || null })} className="input-industrial w-full px-2 text-sm mt-1">
            <option value="">Padrão do sistema</option>
            {(libraryItems[block.type] || []).map(item => (
              <option key={item.id} value={item.id}>{item.nome} (v{item.versao || 1})</option>
            ))}
          </select>
        </div>
      )}
      {block.type === 'photos' && (
        <div>
          <label className="text-xs text-slate-500">Colunas</label>
          <select value={block.settings?.columns || 2} onChange={e => onChange({ ...block, settings: { ...block.settings, columns: parseInt(e.target.value) } })} className="input-industrial w-full px-2 text-sm mt-1">
            <option value={1}>1</option><option value={2}>2</option><option value={3}>3</option>
          </select>
        </div>
      )}
      <div>
        <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
          <input type="checkbox" checked={block.visible} onChange={e => onChange({ ...block, visible: e.target.checked })} className="w-3.5 h-3.5" />
          Visível no documento
        </label>
      </div>
    </div>
  );
};

// ===== MAIN LAYOUT BUILDER PAGE =====
const LayoutBuilderPage = () => {
  const { user } = useAuth();
  const [layouts, setLayouts] = useState([]);
  const [currentLayout, setCurrentLayout] = useState(null);
  const [blocks, setBlocks] = useState([]);
  const [selectedBlockId, setSelectedBlockId] = useState(null);
  const [meta, setMeta] = useState({ nome: '', tipo_documento: '', orientacao: 'retrato' });
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [libraryItems, setLibraryItems] = useState({});
  const [listView, setListView] = useState(true);
  const canEdit = ['master', 'admin', 'pcm'].includes(user?.role);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 150, tolerance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const fetchLayouts = useCallback(async () => {
    try {
      const r = await api.get('/doc-config/layouts');
      setLayouts(r.data);
    } catch { /* silent */ }
  }, []);

  const fetchLibrary = useCallback(async () => {
    try {
      const [procs, segs, cls, sigs, campos, cabs] = await Promise.all([
        api.get('/doc-config/procedimentos'), api.get('/doc-config/seguranca'),
        api.get('/doc-config/checklists'), api.get('/doc-config/assinaturas'),
        api.get('/doc-config/campos'), api.get('/doc-config/cabecalhos-rodapes'),
      ]);
      setLibraryItems({
        procedure: procs.data, safety: segs.data, checklist: cls.data,
        signature: sigs.data, custom_fields: campos.data,
        header: cabs.data.filter(c => c.tipo === 'cabecalho'),
        footer: cabs.data.filter(c => c.tipo === 'rodape'),
      });
    } catch { /* silent */ }
  }, []);

  useEffect(() => { fetchLayouts(); fetchLibrary(); }, [fetchLayouts, fetchLibrary]);

  const openLayout = (layout) => {
    setCurrentLayout(layout);
    setBlocks(layout.blocks || []);
    setMeta({ nome: layout.nome, tipo_documento: layout.tipo_documento || '', orientacao: layout.orientacao || 'retrato' });
    setSelectedBlockId(null);
    setDirty(false);
    setListView(false);
  };

  const newLayout = () => {
    setCurrentLayout(null);
    setBlocks([]);
    setMeta({ nome: 'Novo Layout', tipo_documento: '', orientacao: 'retrato' });
    setSelectedBlockId(null);
    setDirty(true);
    setListView(false);
  };

  const addBlock = (type) => {
    const catalog = BLOCK_CATALOG.find(b => b.type === type);
    if (catalog?.singular && blocks.some(b => b.type === type)) {
      toast.error(`Apenas 1 bloco '${catalog.label}' permitido`); return;
    }
    const newBlock = { id: uuid(), type, order: blocks.length, visible: true, settings: {}, library_ref_id: null };
    setBlocks(prev => [...prev, newBlock]);
    setSelectedBlockId(newBlock.id);
    setDirty(true);
  };

  const removeBlock = (id) => {
    if (!window.confirm('Remover este bloco?')) return;
    setBlocks(prev => prev.filter(b => b.id !== id).map((b, i) => ({ ...b, order: i })));
    if (selectedBlockId === id) setSelectedBlockId(null);
    setDirty(true);
  };

  const updateBlock = (updated) => {
    setBlocks(prev => prev.map(b => b.id === updated.id ? updated : b));
    setDirty(true);
  };

  const moveBlock = (id, dir) => {
    setBlocks(prev => {
      const idx = prev.findIndex(b => b.id === id);
      if (idx < 0) return prev;
      const newIdx = idx + dir;
      if (newIdx < 0 || newIdx >= prev.length) return prev;
      return arrayMove(prev, idx, newIdx).map((b, i) => ({ ...b, order: i }));
    });
    setDirty(true);
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    setBlocks(prev => {
      const oldIdx = prev.findIndex(b => b.id === active.id);
      const newIdx = prev.findIndex(b => b.id === over.id);
      return arrayMove(prev, oldIdx, newIdx).map((b, i) => ({ ...b, order: i }));
    });
    setDirty(true);
  };

  const handleSave = async (asDraft = true) => {
    if (!meta.nome.trim()) { toast.error('Nome do layout obrigatório'); return; }
    setSaving(true);
    try {
      const payload = {
        nome: meta.nome, tipo_documento: meta.tipo_documento || null, orientacao: meta.orientacao,
        schema_version: 1, blocks: blocks.map((b, i) => ({ ...b, order: i })),
        publication_status: asDraft ? 'rascunho' : undefined,
      };
      if (currentLayout?.id) {
        const r = await api.put(`/doc-config/layouts/${currentLayout.id}`, payload);
        toast.success(`Layout salvo (v${r.data.versao})`);
        setCurrentLayout(prev => ({ ...prev, versao: r.data.versao }));
      } else {
        const r = await api.post('/doc-config/layouts', payload);
        toast.success('Layout criado');
        setCurrentLayout({ id: r.data.id, versao: 1 });
      }
      setDirty(false);
      fetchLayouts();
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro ao salvar'); }
    setSaving(false);
  };

  const handlePublish = async () => {
    if (!currentLayout?.id) { toast.error('Salve antes de publicar'); return; }
    if (dirty) { await handleSave(); }
    try {
      await api.post(`/doc-config/layouts/${currentLayout.id}/publicar`);
      toast.success('Layout publicado');
      fetchLayouts();
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro ao publicar'); }
  };

  const handleDuplicate = async (id) => {
    try {
      const r = await api.post(`/doc-config/layouts/${id}/duplicar`);
      toast.success('Layout duplicado');
      fetchLayouts();
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Excluir este layout?')) return;
    try { await api.delete(`/doc-config/layouts/${id}`); toast.success('Excluído'); fetchLayouts(); setListView(true); } catch { toast.error('Erro'); }
  };

  const handlePreview = async () => {
    if (!currentLayout?.id) { toast.error('Salve antes de visualizar'); return; }
    if (dirty) await handleSave();
    setPreviewing(true);
    try {
      const r = await api.get(`/doc-config/layouts/${currentLayout.id}/preview-data`);
      toast.success('Dados carregados — PDF será gerado com estes blocos');
    } catch { toast.error('Erro no preview'); }
    setPreviewing(false);
  };

  const selectedBlock = blocks.find(b => b.id === selectedBlockId);

  // ===== LIST VIEW =====
  if (listView) {
    return (
      <div className="max-w-5xl mx-auto p-6" data-testid="layout-builder-list">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-primary">Construtor de Documentos</h1>
            <p className="text-sm text-slate-500 mt-1">Monte templates arrastando blocos da Biblioteca Corporativa</p>
          </div>
          {canEdit && <button onClick={newLayout} className="btn-primary flex items-center gap-2" data-testid="new-layout-btn"><Plus size={16} /> Novo Layout</button>}
        </div>
        {layouts.length === 0 ? (
          <div className="glass-card p-8 text-center">
            <FileText size={40} className="mx-auto text-slate-600 mb-3" />
            <p className="text-slate-400">Nenhum layout criado</p>
            {canEdit && <button onClick={newLayout} className="btn-primary mt-4">Criar primeiro layout</button>}
          </div>
        ) : (
          <div className="space-y-2">
            {layouts.map(l => (
              <div key={l.id} className="glass-card p-4 flex items-center justify-between hover:border-slate-600 transition-all cursor-pointer" onClick={() => openLayout(l)} data-testid={`layout-item-${l.id}`}>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-primary">{l.nome}</span>
                    <span className="text-xs text-brand bg-brand/10 px-2 py-0.5 rounded">v{l.versao || 1}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${l.publication_status === 'publicado' ? 'bg-emerald-500/20 text-emerald-400' : l.publication_status === 'inativo' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>
                      {(l.publication_status || 'rascunho').charAt(0).toUpperCase() + (l.publication_status || 'rascunho').slice(1)}
                    </span>
                    {l.tipo_documento && <span className="text-xs bg-slate-700 px-2 py-0.5 rounded">{l.tipo_documento}</span>}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{(l.blocks || []).length} blocos | {l.orientacao || 'retrato'}</p>
                </div>
                <div className="flex gap-2 items-center" onClick={e => e.stopPropagation()}>
                  {canEdit && <button onClick={() => handleDuplicate(l.id)} className="text-xs text-slate-400 hover:text-blue-400 flex items-center gap-1" data-testid={`dup-${l.id}`}><Copy size={14} /></button>}
                  {canEdit && <button onClick={() => handleDelete(l.id)} className="text-xs text-slate-400 hover:text-red-400" data-testid={`del-${l.id}`}><Trash2 size={14} /></button>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ===== BUILDER VIEW =====
  return (
    <div className="h-[calc(100vh-64px)] flex flex-col" data-testid="layout-builder">
      {/* Toolbar */}
      <div className="bg-slate-900 border-b border-slate-800 px-4 py-2 flex items-center gap-3 shrink-0">
        <button onClick={() => { if (dirty && !window.confirm('Alterações não salvas. Sair?')) return; setListView(true); }} className="text-slate-400 hover:text-white" data-testid="back-to-list"><ArrowLeft size={18} /></button>
        <input value={meta.nome} onChange={e => { setMeta({ ...meta, nome: e.target.value }); setDirty(true); }} className="bg-transparent border-b border-slate-700 text-primary font-medium text-sm px-1 py-0.5 w-48 focus:border-brand outline-none" data-testid="layout-name-input" />
        <select value={meta.tipo_documento} onChange={e => { setMeta({ ...meta, tipo_documento: e.target.value }); setDirty(true); }} className="bg-slate-800 text-xs text-slate-300 rounded px-2 py-1 border border-slate-700">
          <option value="">Tipo documento</option>
          <option value="os_corretiva">OS Corretiva</option><option value="os_preventiva">OS Preventiva</option>
          <option value="os_lubrificacao">OS Lubrificação</option><option value="inspecao_mecanica">Inspeção Mecânica</option>
          <option value="inspecao_eletrica">Inspeção Elétrica</option><option value="geral">Geral</option>
        </select>
        <select value={meta.orientacao} onChange={e => { setMeta({ ...meta, orientacao: e.target.value }); setDirty(true); }} className="bg-slate-800 text-xs text-slate-300 rounded px-2 py-1 border border-slate-700">
          <option value="retrato">Retrato</option><option value="paisagem">Paisagem</option>
        </select>
        <div className="flex-1" />
        {dirty && <span className="text-xs text-amber-400">Não salvo</span>}
        {canEdit && <button onClick={() => handleSave(true)} disabled={saving} className="text-xs bg-slate-700 text-white px-3 py-1.5 rounded hover:bg-slate-600 flex items-center gap-1" data-testid="save-draft"><Save size={14} /> {saving ? '...' : 'Salvar'}</button>}
        {canEdit && <button onClick={handlePreview} disabled={previewing} className="text-xs bg-slate-700 text-white px-3 py-1.5 rounded hover:bg-slate-600 flex items-center gap-1" data-testid="preview-btn"><Printer size={14} /> Preview</button>}
        {canEdit && currentLayout?.id && <button onClick={handlePublish} className="text-xs bg-emerald-600 text-white px-3 py-1.5 rounded hover:bg-emerald-500 flex items-center gap-1" data-testid="publish-btn"><Send size={14} /> Publicar</button>}
      </div>

      {/* Main 3-panel layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Block Palette */}
        <div className="w-56 bg-slate-900/80 border-r border-slate-800 overflow-y-auto p-3 shrink-0" data-testid="block-palette">
          <p className="text-xs font-bold text-slate-400 uppercase mb-3">Blocos Disponíveis</p>
          {CATEGORIES.map(cat => (
            <div key={cat.id} className="mb-3">
              <p className="text-xs text-slate-600 uppercase mb-1">{cat.label}</p>
              <div className="space-y-1">
                {BLOCK_CATALOG.filter(b => b.category === cat.id).map(b => (
                  <button key={b.type} onClick={() => addBlock(b.type)} disabled={!canEdit}
                    className="w-full text-left flex items-center gap-2 px-2 py-1.5 rounded text-xs text-slate-300 hover:bg-slate-800 hover:text-white transition-colors disabled:opacity-40"
                    data-testid={`add-block-${b.type}`}>
                    <span className="w-5 text-center">{b.icon}</span> {b.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Center: Document Canvas */}
        <div className="flex-1 overflow-y-auto p-4 bg-slate-950/50" data-testid="document-canvas">
          {blocks.length === 0 ? (
            <div className="border-2 border-dashed border-slate-700 rounded-xl p-12 text-center">
              <FileText size={40} className="mx-auto text-slate-600 mb-3" />
              <p className="text-slate-400 text-sm">Arraste blocos do painel esquerdo</p>
              <p className="text-slate-600 text-xs mt-1">ou clique para adicionar</p>
            </div>
          ) : (
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
              <SortableContext items={blocks.map(b => b.id)} strategy={verticalListSortingStrategy}>
                <div className="space-y-1.5 max-w-2xl mx-auto">
                  {blocks.map((block, i) => (
                    <SortableBlock key={block.id} block={block} isSelected={selectedBlockId === block.id}
                      onSelect={setSelectedBlockId} onToggleVisible={() => updateBlock({ ...block, visible: !block.visible })}
                      onRemove={() => removeBlock(block.id)} onMoveUp={() => moveBlock(block.id, -1)}
                      onMoveDown={() => moveBlock(block.id, 1)} isFirst={i === 0} isLast={i === blocks.length - 1} />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          )}
        </div>

        {/* Right: Properties */}
        <div className="w-64 bg-slate-900/80 border-l border-slate-800 overflow-y-auto shrink-0" data-testid="properties-panel">
          <div className="p-3 border-b border-slate-800">
            <p className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1"><Settings size={12} /> Propriedades</p>
          </div>
          <BlockProperties block={selectedBlock} onChange={updateBlock} libraryItems={libraryItems} />
        </div>
      </div>
    </div>
  );
};

export default LayoutBuilderPage;
