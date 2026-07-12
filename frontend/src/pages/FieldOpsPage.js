import { useState } from "react";
import { ClipboardCheck, Wrench, AlertTriangle, MapPin, Plus, Target } from "lucide-react";
import { useAuth } from "@/lib/api";
import { PageContainer, PageHeader } from "@/components/shared";

// ============== FIELD OPS — STUB PAGES ==============
// These are structural placeholders for the Field Operations module.
// Logic will be implemented in a future release.

const FieldCard = ({ icon: Icon, title, subtitle, count, color, testId }) => (
  <div className="glass-card p-4 flex items-center gap-4 cursor-pointer hover:border-slate-600 transition-colors" data-testid={testId}>
    <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${color}15` }}>
      <Icon size={24} style={{ color }} />
    </div>
    <div className="flex-1 min-w-0">
      <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
      <p className="text-xs text-slate-500">{subtitle}</p>
    </div>
    {count !== undefined && (
      <span className="text-lg font-bold" style={{ color }}>{count}</span>
    )}
  </div>
);

const MinhaAreaPage = () => {
  const { user } = useAuth();
  return (
    <PageContainer>
      <PageHeader title="Minha Area" subtitle={`${user?.nome || 'Tecnico'} — ${(user?.turno || 'ADM')}`} />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        <FieldCard icon={Wrench} title="Minhas OS" subtitle="Ordens atribuidas a voce" count={0} color="#10b981" testId="field-minhas-os" />
        <FieldCard icon={ClipboardCheck} title="Minhas Inspecoes" subtitle="Inspecoes pendentes" count={0} color="#6366f1" testId="field-minhas-inspecoes" />
        <FieldCard icon={AlertTriangle} title="Solicitacoes" subtitle="Suas solicitacoes abertas" count={0} color="#f59e0b" testId="field-solicitacoes" />
        <FieldCard icon={Target} title="Ronda" subtitle="Proxima ronda programada" count={0} color="#06b6d4" testId="field-ronda" />
      </div>
      <div className="mt-8">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Acoes Rapidas</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <button className="glass-card p-3 flex items-center gap-3 hover:border-emerald-500/30 transition-colors" data-testid="field-nova-os">
            <Plus size={16} className="text-emerald-400" />
            <span className="text-sm text-slate-300">Nova OS</span>
          </button>
          <button className="glass-card p-3 flex items-center gap-3 hover:border-indigo-500/30 transition-colors" data-testid="field-nova-inspecao">
            <Plus size={16} className="text-indigo-400" />
            <span className="text-sm text-slate-300">Nova Inspecao</span>
          </button>
          <button className="glass-card p-3 flex items-center gap-3 hover:border-amber-500/30 transition-colors" data-testid="field-nova-solicitacao">
            <Plus size={16} className="text-amber-400" />
            <span className="text-sm text-slate-300">Nova Solicitacao</span>
          </button>
        </div>
      </div>
      <div className="mt-6 p-4 rounded-lg border border-dashed border-slate-700 text-center">
        <MapPin size={24} className="text-slate-600 mx-auto mb-2" />
        <p className="text-sm text-slate-500">Modulo de Field Operations em preparacao</p>
        <p className="text-xs text-slate-600 mt-1">Os dados serao carregados na proxima release</p>
      </div>
    </PageContainer>
  );
};

export default MinhaAreaPage;
