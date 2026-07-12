import { useState, useEffect } from "react";
import { Settings, Building, Palette, BookOpen, Hash, Cog, Save } from "lucide-react";
import { toast } from "sonner";
import { api, useAuth } from "@/lib/api";
import { normalizeError } from "@/lib/constants";
import { Loading, PageContainer, PageHeader, FormInput, Select } from "@/components/shared";

const OrgConfigPage = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('identidade');
  const [saving, setSaving] = useState(false);
  const [numPreview, setNumPreview] = useState('');
  const { user } = useAuth();

  const fetchConfig = async () => {
    try {
      const res = await api.get('/org/config');
      setConfig(res.data);
    } catch { toast.error('Erro ao carregar configurações'); }
    finally { setLoading(false); }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchConfig(); }, []);

  const updateSection = async (section, data) => {
    setSaving(true);
    try {
      await api.put(`/org/config/${section}`, data);
      toast.success('Configurações salvas!');
      fetchConfig();
    } catch (err) { toast.error(normalizeError(err)); }
    finally { setSaving(false); }
  };

  const fetchPreview = async (entidade, tipo) => {
    try {
      const res = await api.get(`/org/config/numeracao/preview?entidade=${entidade}&tipo=${tipo}`);
      setNumPreview(res.data.preview);
    } catch { setNumPreview(''); }
  };

  if (loading) return <Loading rows={5} />;
  if (!config) return <div className="text-red-400">Erro ao carregar configurações</div>;

  const tabs = [
    { id: 'identidade', label: 'Identidade', icon: Building2 },
    { id: 'tema', label: 'Tema', icon: Palette },
    { id: 'terminologia', label: 'Terminologia', icon: FileText },
    { id: 'numeracao', label: 'Numeração', icon: Hash },
    { id: 'preferencias', label: 'Preferências', icon: Settings },
  ];

  return (
    <div className="space-y-4" data-testid="org-config-page">
      <h1 className="text-2xl font-bold text-primary">Configurações da Organização</h1>
      
      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto hide-scrollbar border-b border-slate-800 pb-1">
        {tabs.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              className={`px-4 py-2 rounded-t-lg text-xs font-medium flex items-center gap-2 whitespace-nowrap transition-all ${activeTab === t.id ? 'bg-slate-800 text-brand border-b-2 border-brand' : 'text-slate-500 hover:text-slate-300'}`}
              data-testid={`config-tab-${t.id}`}
            ><Icon size={14} />{t.label}</button>
          );
        })}
      </div>

      {/* Identity Tab */}
      {activeTab === 'identidade' && (
        <IdentidadeTab config={config} onSave={(data) => updateSection('identidade', data)} saving={saving} />
      )}

      {/* Theme Tab */}
      {activeTab === 'tema' && (
        <TemaTab config={config} onSave={(data) => updateSection('tema', data)} saving={saving} />
      )}

      {/* Terminology Tab */}
      {activeTab === 'terminologia' && (
        <TerminologiaTab config={config} onSave={(data) => updateSection('terminologia', data)} saving={saving} />
      )}

      {/* Numbering Tab */}
      {activeTab === 'numeracao' && (
        <NumeracaoTab config={config} onSave={(data) => updateSection('numeracao', data)} saving={saving} onPreview={fetchPreview} preview={numPreview} />
      )}

      {/* Preferences Tab */}
      {activeTab === 'preferencias' && (
        <PreferenciasTab config={config} onSave={(data) => updateSection('preferencias', data)} saving={saving} />
      )}
    </div>
  );
};

// Sub-tabs as small components
const IdentidadeTab = ({ config, onSave, saving }) => {
  const [form, setForm] = useState(config?.identidade || {});
  return (
    <div className="glass-card p-4 space-y-4">
      <FormInput label="Nome do Sistema"><input value={form.nome_sistema || ''} onChange={e => setForm({...form, nome_sistema: e.target.value})} className="input-industrial w-full px-4" data-testid="config-nome-sistema" /></FormInput>
      <FormInput label="Subtítulo"><input value={form.subtitulo || ''} onChange={e => setForm({...form, subtitulo: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
      <FormInput label="Rodapé"><input value={form.rodape || ''} onChange={e => setForm({...form, rodape: e.target.value})} className="input-industrial w-full px-4" /></FormInput>
      <FormInput label="Texto Institucional"><textarea value={form.texto_institucional || ''} onChange={e => setForm({...form, texto_institucional: e.target.value})} className="input-industrial w-full px-4 min-h-[80px]" /></FormInput>
      <div className="flex justify-end"><button onClick={() => onSave(form)} disabled={saving} className="btn-primary" data-testid="config-save-identidade">{saving ? 'Salvando...' : 'Salvar'}</button></div>
    </div>
  );
};

const TemaTab = ({ config, onSave, saving }) => {
  const [form, setForm] = useState(config?.tema || {});
  const cores = [
    { key: 'cor_primaria', label: 'Cor Primária' },
    { key: 'cor_secundaria', label: 'Cor Secundária' },
    { key: 'cor_fundo', label: 'Cor de Fundo' },
    { key: 'cor_texto', label: 'Cor de Texto' },
    { key: 'cor_destaque', label: 'Cor de Destaque' },
    { key: 'cor_sucesso', label: 'Cor de Sucesso' },
    { key: 'cor_alerta', label: 'Cor de Alerta' },
    { key: 'cor_erro', label: 'Cor de Erro' },
  ];
  return (
    <div className="glass-card p-4 space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {cores.map(c => (
          <div key={c.key}>
            <label className="text-xs text-slate-400 mb-1 block">{c.label}</label>
            <div className="flex items-center gap-2">
              <input type="color" value={form[c.key] || '#000000'} onChange={e => setForm({...form, [c.key]: e.target.value})} className="w-10 h-8 rounded border border-slate-700 cursor-pointer" data-testid={`config-color-${c.key}`} />
              <input value={form[c.key] || ''} onChange={e => setForm({...form, [c.key]: e.target.value})} className="input-industrial flex-1 px-2 text-xs font-mono" />
            </div>
          </div>
        ))}
      </div>
      {/* Preview */}
      <div className="p-4 rounded-lg border border-slate-700" style={{backgroundColor: form.cor_fundo, color: form.cor_texto}}>
        <p className="text-sm font-bold" style={{color: form.cor_primaria}}>Preview do Tema</p>
        <p className="text-xs mt-1">Texto normal com <span style={{color: form.cor_destaque}}>destaque</span>, <span style={{color: form.cor_sucesso}}>sucesso</span>, <span style={{color: form.cor_alerta}}>alerta</span> e <span style={{color: form.cor_erro}}>erro</span></p>
        <button className="mt-2 px-3 py-1 rounded text-xs text-white" style={{backgroundColor: form.cor_primaria}}>Botão Primário</button>
        <button className="mt-2 ml-2 px-3 py-1 rounded text-xs text-white" style={{backgroundColor: form.cor_secundaria}}>Botão Secundário</button>
      </div>
      <div className="flex justify-end"><button onClick={() => onSave(form)} disabled={saving} className="btn-primary" data-testid="config-save-tema">{saving ? 'Salvando...' : 'Salvar'}</button></div>
    </div>
  );
};

const TerminologiaTab = ({ config, onSave, saving }) => {
  const [form, setForm] = useState(config?.terminologia || {});
  const [search, setSearch] = useState('');
  const entries = Object.entries(form).filter(([k]) => !search || k.includes(search.toLowerCase()));
  return (
    <div className="glass-card p-4 space-y-3">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar termo..." className="input-industrial w-full pl-9 pr-4 text-sm" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-[400px] overflow-y-auto">
        {entries.map(([key, value]) => (
          <div key={key} className="flex items-center gap-2">
            <span className="text-[10px] text-slate-600 font-mono w-32 shrink-0 truncate">{key}</span>
            <input value={value} onChange={e => setForm({...form, [key]: e.target.value})} className="input-industrial flex-1 px-3 text-sm" data-testid={`term-${key}`} />
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-600">{entries.length} termos</p>
      <div className="flex justify-end"><button onClick={() => onSave(form)} disabled={saving} className="btn-primary" data-testid="config-save-terminologia">{saving ? 'Salvando...' : 'Salvar'}</button></div>
    </div>
  );
};

const NumeracaoTab = ({ config, onSave, saving, onPreview, preview }) => {
  const [form, setForm] = useState(config?.numeracao || {});
  const [prefixo, setPrefixo] = useState(config?.preferencias?.prefixo_empresa || '');
  const entidades = ['ordens_servico', 'inspecoes', 'lubrificacoes', 'paradas_programadas'];
  
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { onPreview('ordens_servico', 'corretiva'); }, []);
  
  return (
    <div className="glass-card p-4 space-y-4">
      <FormInput label="Prefixo da Empresa">
        <input value={prefixo} onChange={e => setPrefixo(e.target.value)} className="input-industrial w-full px-4" placeholder="AST" data-testid="config-prefixo" />
        <p className="text-xs text-slate-600 mt-1">Será usado em todos os códigos operacionais</p>
      </FormInput>
      <div className="space-y-3">
        {entidades.map(ent => {
          const cfg = form[ent] || {};
          return (
            <div key={ent} className="p-3 bg-slate-800/50 rounded-lg">
              <p className="text-xs text-slate-400 font-medium capitalize mb-2">{ent.replace(/_/g, ' ')}</p>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-600">Padrão</label>
                  <input value={cfg.prefixo || ''} onChange={e => setForm({...form, [ent]: {...cfg, prefixo: e.target.value}})} className="input-industrial w-full px-2 text-xs font-mono" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-600">Dígitos</label>
                  <input type="number" min={3} max={10} value={cfg.digitos || 6} onChange={e => setForm({...form, [ent]: {...cfg, digitos: parseInt(e.target.value)}})} className="input-industrial w-full px-2 text-xs" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {preview && <div className="p-3 bg-brand-10 border border-brand-30 rounded-lg"><p className="text-xs text-slate-400">Preview:</p><p className="text-lg font-mono text-brand">{preview}</p></div>}
      <div className="flex justify-end gap-2">
        <button onClick={() => onPreview('ordens_servico', 'corretiva')} className="btn-secondary text-xs">Atualizar Preview</button>
        <button onClick={() => { onSave(form); if (prefixo) api.put('/org/config/preferencias', { prefixo_empresa: prefixo }); }} disabled={saving} className="btn-primary" data-testid="config-save-numeracao">{saving ? 'Salvando...' : 'Salvar'}</button>
      </div>
    </div>
  );
};

const PreferenciasTab = ({ config, onSave, saving }) => {
  const [form, setForm] = useState(config?.preferencias || {});
  return (
    <div className="glass-card p-4 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <FormInput label="Horário de Trabalho - Início"><input value={form.horario_trabalho?.inicio || '07:00'} onChange={e => setForm({...form, horario_trabalho: {...(form.horario_trabalho || {}), inicio: e.target.value}})} type="time" className="input-industrial w-full px-4" /></FormInput>
        <FormInput label="Horário de Trabalho - Fim"><input value={form.horario_trabalho?.fim || '17:00'} onChange={e => setForm({...form, horario_trabalho: {...(form.horario_trabalho || {}), fim: e.target.value}})} type="time" className="input-industrial w-full px-4" /></FormInput>
        <FormInput label="Fuso Horário">
          <select value={form.fuso_horario || 'America/Sao_Paulo'} onChange={e => setForm({...form, fuso_horario: e.target.value})} className="input-industrial w-full px-4">
            <option value="America/Sao_Paulo">São Paulo (BRT)</option>
            <option value="America/Manaus">Manaus (AMT)</option>
            <option value="America/Belem">Belém (BRT)</option>
            <option value="America/Cuiaba">Cuiabá (AMT)</option>
          </select>
        </FormInput>
        <FormInput label="Formato de Data">
          <select value={form.formato_data || 'DD/MM/YYYY'} onChange={e => setForm({...form, formato_data: e.target.value})} className="input-industrial w-full px-4">
            <option value="DD/MM/YYYY">DD/MM/YYYY</option>
            <option value="MM/DD/YYYY">MM/DD/YYYY</option>
            <option value="YYYY-MM-DD">YYYY-MM-DD</option>
          </select>
        </FormInput>
        <FormInput label="Unidade de Tempo">
          <select value={form.unidade_tempo || 'minutos'} onChange={e => setForm({...form, unidade_tempo: e.target.value})} className="input-industrial w-full px-4">
            <option value="minutos">Minutos</option>
            <option value="horas">Horas</option>
          </select>
        </FormInput>
        <FormInput label="Moeda">
          <select value={form.moeda || 'BRL'} onChange={e => setForm({...form, moeda: e.target.value})} className="input-industrial w-full px-4">
            <option value="BRL">R$ (Real)</option>
            <option value="USD">$ (Dólar)</option>
            <option value="EUR">€ (Euro)</option>
          </select>
        </FormInput>
      </div>
      {/* Turnos */}
      <div>
        <p className="text-sm text-slate-300 font-medium mb-2">Turnos</p>
        <div className="space-y-1">
          {(form.turnos || []).map((turno, idx) => (
            <div key={idx} className="flex items-center gap-2 text-xs">
              <input value={turno.nome} onChange={e => { const t = [...(form.turnos || [])]; t[idx] = {...t[idx], nome: e.target.value}; setForm({...form, turnos: t}); }} className="input-industrial flex-1 px-2" />
              <input type="time" value={turno.inicio} onChange={e => { const t = [...(form.turnos || [])]; t[idx] = {...t[idx], inicio: e.target.value}; setForm({...form, turnos: t}); }} className="input-industrial w-24 px-2" />
              <span className="text-slate-600">→</span>
              <input type="time" value={turno.fim} onChange={e => { const t = [...(form.turnos || [])]; t[idx] = {...t[idx], fim: e.target.value}; setForm({...form, turnos: t}); }} className="input-industrial w-24 px-2" />
              <button onClick={() => { const t = (form.turnos || []).filter((_,i) => i !== idx); setForm({...form, turnos: t}); }} className="text-red-400 hover:text-red-300"><X size={14} /></button>
            </div>
          ))}
          <button onClick={() => setForm({...form, turnos: [...(form.turnos || []), {nome: '', inicio: '06:00', fim: '14:00'}]})} className="text-xs text-brand hover:brightness-110 mt-1">+ Adicionar turno</button>
        </div>
      </div>
      <div className="flex justify-end"><button onClick={() => onSave(form)} disabled={saving} className="btn-primary" data-testid="config-save-preferencias">{saving ? 'Salvando...' : 'Salvar'}</button></div>
    </div>
  );
};



export default OrgConfigPage;
