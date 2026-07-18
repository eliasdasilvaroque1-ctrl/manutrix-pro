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
    const printWindow = window.open('', '_blank');

    if (!printWindow) {
      toast.error('O navegador bloqueou a janela de impressão. Autorize pop-ups para o MAINTRIX.');
      return;
    }

    printWindow.document.write(`<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Gerando impressão...</title></head><body style="font-family:Arial,sans-serif;background:#0f172a;color:white;display:flex;align-items:center;justify-content:center;height:100vh;margin:0"><p>Gerando PDF, aguarde...</p></body></html>`);
    printWindow.document.close();

    setLoading(true);

    try {
      const ids = selectedIds.join(',');
      const endpoint = entity === 'ordens-servico'
        ? `/ordens-servico/batch-pdf?ids=${encodeURIComponent(ids)}`
        : `/inspecoes/batch-pdf?ids=${encodeURIComponent(ids)}`;

      const res = await api.get(endpoint, { responseType: 'blob' });

      const contentType = res.headers?.['content-type'] || res.data?.type || '';
      if (!contentType.includes('application/pdf')) {
        throw new Error(`Resposta inválida: ${contentType || 'sem content-type'}`);
      }

      const pdfBlob = new Blob([res.data], { type: 'application/pdf' });
      if (pdfBlob.size === 0) {
        throw new Error('PDF vazio');
      }

      const pdfUrl = window.URL.createObjectURL(pdfBlob);
      printWindow.location.replace(pdfUrl);
      setTimeout(() => { window.URL.revokeObjectURL(pdfUrl); }, 60000);

      toast.success(`${selectedIds.length} ${entityLabel} preparados para impressão`);
    } catch (error) {
      console.error('Erro na impressão em lote:', error);
      if (!printWindow.closed) { printWindow.close(); }
      toast.error(error?.response?.status
        ? `Erro ${error.response.status} ao gerar o PDF`
        : 'Não foi possível gerar o PDF para impressão');
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
