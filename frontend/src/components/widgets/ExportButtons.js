import { FileText } from "lucide-react";
import { toast } from "sonner";
import { api, useAuth } from "@/lib/api";

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
      <button onClick={() => handleExport('excel')} className="p-2 bg-brand-10 hover:bg-brand-20 text-brand rounded-lg transition-colors" title="Excel" data-testid={`${entity}-export-excel`}><FileText size={16} /></button>
      <button onClick={() => handleExport('pdf')} className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors" title="PDF" data-testid={`${entity}-export-pdf`}><FileText size={16} /></button>
    </div>
  );
};

export default ExportButtons;
