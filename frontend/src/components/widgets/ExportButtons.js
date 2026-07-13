import { useState } from "react";
import { FileText, Printer, Download, X, CheckSquare, Square } from "lucide-react";
import { toast } from "sonner";
import { api, BACKEND_URL, useAuth } from "@/lib/api";

const ExportButtons = ({ entity }) => {
  const { user } = useAuth();
  if (!['admin','master','pcm','gerente','supervisor'].includes(user?.role)) return null;
  
  const handleExport = async (format) => {
    try {
      const res = await api.get(`/export/${entity}?format=${format}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      const cd = res.headers?.['content-disposition'] || '';
      const match = cd.match(/filename=([^;]+)/);
      link.download = match ? match[1].replace(/^"|"$/g, '').trim() : `${entity}_export.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      link.click();
      window.URL.revokeObjectURL(url);
      toast.success(`Exportado em ${format.toUpperCase()}`);
    } catch (e) { toast.error('Erro ao exportar'); }
  };

  return (
    <div className="flex gap-1" data-testid={`export-btns-${entity}`}>
      <button onClick={() => handleExport('excel')} className="p-2 bg-brand-10 hover:bg-brand-20 text-brand rounded-lg transition-colors" title="Exportar Excel" data-testid={`${entity}-export-excel`}>
        <Download size={16} />
      </button>
      <button onClick={() => handleExport('pdf')} className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors" title="Exportar PDF" data-testid={`${entity}-export-pdf`}>
        <FileText size={16} />
      </button>
    </div>
  );
};

// Batch Print Bar - shows when items are selected
const BatchPrintBar = ({ selectedIds, entity, onClear, entityLabel = "itens" }) => {
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();

  if (!selectedIds?.length) return null;
  if (!['master', 'admin', 'pcm'].includes(user?.role)) return null;

  const handleBatchPrint = async () => {
    setLoading(true);
    try {
      const ids = selectedIds.join(',');
      const endpoint = entity === 'ordens-servico' 
        ? `/ordens-servico/batch-pdf?ids=${ids}`
        : `/inspecoes/batch-pdf?ids=${ids}`;
      
      const res = await api.get(endpoint, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      window.open(url, '_blank');
      toast.success(`${selectedIds.length} ${entityLabel} enviados para impressão`);
    } catch (e) {
      toast.error('Erro ao gerar PDF em lote');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-20 left-1/2 -translate-x-1/2 z-50 bg-slate-900 border border-brand-30 rounded-xl px-5 py-3 flex items-center gap-4 shadow-2xl shadow-brand/20" data-testid="batch-print-bar">
      <div className="flex items-center gap-2">
        <CheckSquare size={18} className="text-brand" />
        <span className="text-sm font-medium text-primary">{selectedIds.length} {entityLabel} selecionado(s)</span>
      </div>
      <button
        onClick={handleBatchPrint}
        disabled={loading}
        className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg text-sm font-medium hover:brightness-110 transition-all disabled:opacity-50"
        data-testid="batch-print-btn"
      >
        <Printer size={16} />
        {loading ? 'Gerando...' : 'Imprimir Lote'}
      </button>
      <button onClick={onClear} className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors" data-testid="batch-clear-btn">
        <X size={16} className="text-slate-400" />
      </button>
    </div>
  );
};

// Checkbox for batch selection
const BatchCheckbox = ({ id, selectedIds, setSelectedIds }) => {
  const isSelected = selectedIds.includes(id);
  const toggle = (e) => {
    e.stopPropagation();
    setSelectedIds(prev => isSelected ? prev.filter(x => x !== id) : [...prev, id]);
  };
  return (
    <button onClick={toggle} className="p-1 hover:bg-slate-700 rounded transition-colors shrink-0" data-testid={`batch-check-${id}`}>
      {isSelected ? <CheckSquare size={16} className="text-brand" /> : <Square size={16} className="text-slate-600" />}
    </button>
  );
};

export default ExportButtons;
export { BatchPrintBar, BatchCheckbox };
