import { useState, useEffect, useRef, memo } from "react";
import { Cog, Filter, Activity, Zap, Droplet, Wrench, Shield, Package, ZoomIn, Maximize2, X, Upload, Camera, ImagePlus, Trash2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { api, BACKEND_URL } from "../../lib/api";
import { useBranding } from "../../lib/branding";
import { compressImage } from "../../lib/constants";

const MaterialThumbnail = memo(({ images, nome, categoria, size = 'md', onClick }) => {
  const { config } = useBranding();
  const primaryColor = config?.tema?.cor_primaria || '#10b981';
  const src = (images || [])[0];
  const sizes = { sm: 'w-8 h-8', md: 'w-10 h-10', lg: 'w-14 h-14', xl: 'w-20 h-20' };
  const iconSizes = { sm: 12, md: 14, lg: 18, xl: 24 };
  const textSizes = { sm: 'text-[8px]', md: 'text-[10px]', lg: 'text-xs', xl: 'text-sm' };

  const catIcons = {
    rolamento: Cog, filtro: Filter, correia: Activity, eletrico: Zap,
    hidraulico: Droplet, mecanico: Wrench, vedacao: Shield, lubrificante: Droplet,
    outro: Package,
  };
  const matchCat = Object.keys(catIcons).find(k => (categoria || '').toLowerCase().includes(k));
  const CatIcon = catIcons[matchCat] || Package;
  const initials = (nome || '?').split(' ').map(w => w[0]).filter(Boolean).slice(0, 2).join('').toUpperCase();

  if (src) {
    return (
      <div
        className={`${sizes[size]} rounded-lg overflow-hidden flex-shrink-0 cursor-pointer border border-slate-700 hover:border-slate-500 transition-all`}
        onClick={onClick}
        data-testid="material-thumbnail"
      >
        <img src={`${BACKEND_URL}${src}`} alt={nome} className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }} />
        <div className="w-full h-full items-center justify-center hidden" style={{ background: `${primaryColor}15` }}>
          <CatIcon size={iconSizes[size]} style={{ color: primaryColor }} />
        </div>
      </div>
    );
  }

  return (
    <div
      className={`${sizes[size]} rounded-lg flex-shrink-0 flex flex-col items-center justify-center border border-slate-700/50 ${onClick ? 'cursor-pointer hover:border-slate-500' : ''} transition-all`}
      style={{ background: `${primaryColor}10` }}
      onClick={onClick}
      data-testid="material-placeholder"
    >
      <CatIcon size={iconSizes[size]} style={{ color: primaryColor, opacity: 0.6 }} />
      <span className={`${textSizes[size]} font-semibold mt-0.5`} style={{ color: primaryColor, opacity: 0.7 }}>{initials}</span>
    </div>
  );
});

const MaterialImageModal = ({ src, nome, onClose }) => {
  const [zoom, setZoom] = useState(1);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const lastPos = useRef({ x: 0, y: 0 });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef(null);

  const handleWheel = (e) => {
    e.preventDefault();
    setZoom(z => Math.max(0.5, Math.min(5, z + (e.deltaY > 0 ? -0.2 : 0.2))));
  };

  const handlePointerDown = (e) => {
    if (zoom <= 1) return;
    setDragging(true);
    lastPos.current = { x: e.clientX - pos.x, y: e.clientY - pos.y };
  };
  const handlePointerMove = (e) => {
    if (!dragging) return;
    setPos({ x: e.clientX - lastPos.current.x, y: e.clientY - lastPos.current.y });
  };
  const handlePointerUp = () => setDragging(false);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen?.();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.();
      setIsFullscreen(false);
    }
  };

  useEffect(() => {
    const onFs = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', onFs);
    return () => document.removeEventListener('fullscreenchange', onFs);
  }, []);

  return (
    <div ref={containerRef} className="fixed inset-0 z-[200] bg-black/95 flex flex-col" data-testid="material-image-modal" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="flex items-center justify-between p-3 bg-black/60">
        <span className="text-sm text-slate-300 truncate">{nome}</span>
        <div className="flex items-center gap-2">
          <button onClick={() => setZoom(z => Math.min(5, z + 0.5))} className="p-1.5 rounded hover:bg-slate-800 text-slate-400" data-testid="zoom-in"><ZoomIn size={18} /></button>
          <span className="text-xs text-slate-500 w-12 text-center">{Math.round(zoom * 100)}%</span>
          <button onClick={() => { setZoom(z => Math.max(0.5, z - 0.5)); setPos({ x: 0, y: 0 }); }} className="p-1.5 rounded hover:bg-slate-800 text-slate-400" data-testid="zoom-out"><ZoomIn size={18} className="rotate-180" /></button>
          <button onClick={toggleFullscreen} className="p-1.5 rounded hover:bg-slate-800 text-slate-400" data-testid="fullscreen-toggle"><Maximize2 size={18} /></button>
          <button onClick={onClose} className="p-1.5 rounded hover:bg-red-500/20 text-slate-400" data-testid="close-image-modal"><X size={18} /></button>
        </div>
      </div>
      <div
        className="flex-1 overflow-hidden flex items-center justify-center"
        onWheel={handleWheel}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        style={{ cursor: zoom > 1 ? (dragging ? 'grabbing' : 'grab') : 'default', touchAction: 'none' }}
      >
        <img
          src={`${BACKEND_URL}${src}`}
          alt={nome}
          className="select-none"
          draggable={false}
          style={{ transform: `translate(${pos.x}px, ${pos.y}px) scale(${zoom})`, transition: dragging ? 'none' : 'transform 0.15s ease', maxWidth: '95vw', maxHeight: '90vh', objectFit: 'contain' }}
        />
      </div>
    </div>
  );
};

const MaterialImageUploader = ({ tipo, itemId, images, onUpdate }) => {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [viewImg, setViewImg] = useState(null);
  const [localImages, setLocalImages] = useState(images || []);
  const fileRef = useRef(null);
  const { config } = useBranding();
  const primaryColor = config?.tema?.cor_primaria || '#10b981';

  useEffect(() => { setLocalImages(images || []); }, [images]);

  const handleFiles = async (files) => {
    if (!files.length || !itemId) return;
    setUploading(true);
    try {
      for (const rawFile of files) {
        const file = await compressImage(rawFile);
        const formData = new FormData();
        formData.append('file', file);
        const res = await api.post(`/materiais/${tipo}/${itemId}/images`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
        setLocalImages(res.data.images);
        onUpdate?.(res.data.images);
      }
      toast.success('Imagem enviada!');
    } catch (e) { toast.error('Erro ao enviar imagem'); }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = ''; }
  };

  const handleRemove = async (url) => {
    try {
      await api.delete(`/materiais/${tipo}/${itemId}/images?image_url=${encodeURIComponent(url)}`);
      const updated = localImages.filter(u => u !== url);
      setLocalImages(updated);
      onUpdate?.(updated);
      toast.success('Imagem removida');
    } catch (e) { toast.error('Erro ao remover imagem'); }
  };

  const imgList = localImages;

  return (
    <div className="space-y-2">
      <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider flex items-center gap-1"><ImagePlus size={14} /> Identificação Visual</p>
      {imgList.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {imgList.map((url, idx) => (
            <div key={idx} className="relative group w-16 h-16 rounded-lg overflow-hidden border border-slate-700 cursor-pointer hover:border-slate-500" onClick={() => setViewImg(url)}>
              <img src={`${BACKEND_URL}${url}`} alt={`Material ${idx + 1}`} className="w-full h-full object-cover" />
              <button
                onClick={(e) => { e.stopPropagation(); handleRemove(url); }}
                className="absolute top-0.5 right-0.5 p-0.5 bg-red-500/80 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                data-testid={`remove-material-img-${idx}`}
              ><X size={10} className="text-white" /></button>
            </div>
          ))}
        </div>
      )}
      <div
        className={`border-2 border-dashed rounded-lg p-3 text-center transition-all cursor-pointer ${dragOver ? 'border-emerald-400 bg-emerald-500/5' : 'border-slate-700 hover:border-slate-500'}`}
        style={dragOver ? {} : { borderColor: `${primaryColor}40` }}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'))); }}
        onClick={() => fileRef.current?.click()}
        data-testid="material-image-dropzone"
      >
        {uploading ? (
          <span className="text-xs text-slate-400 flex items-center justify-center gap-2"><RefreshCw size={14} className="animate-spin" /> Enviando...</span>
        ) : (
          <span className="text-xs text-slate-500 flex items-center justify-center gap-2"><Camera size={14} /> Arraste, selecione ou tire uma foto</span>
        )}
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={(e) => handleFiles(Array.from(e.target.files))}
          className="hidden"
          disabled={uploading}
          data-testid="material-image-input"
        />
      </div>
      {viewImg && <MaterialImageModal src={viewImg} nome="Material" onClose={() => setViewImg(null)} />}
    </div>
  );
};


// NotificationBell — removido (BLOCO A: zero referências, endpoints /notificacoes existem mas componente não era montado)

// ============== MODALS ==============

// Modal Novo Ativo

export { MaterialThumbnail, MaterialImageModal, MaterialImageUploader };
