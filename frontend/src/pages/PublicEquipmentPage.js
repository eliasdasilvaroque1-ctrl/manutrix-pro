import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Cog, AlertCircle, MapPin, Factory, Gauge, Zap, Weight, Maximize2, Box } from "lucide-react";
import axios from "axios";
import { BACKEND_URL } from "../lib/api";
import { clearChunkReloadFlag } from "../components/PublicErrorBoundary";

const PublicEquipmentPage = () => {
  const { slug, token } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [imgError, setImgError] = useState(false);

  // HOTFIX P0: Limpa flag de reload ao montar com sucesso (evita loops)
  useEffect(() => {
    clearChunkReloadFlag();
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/public/equipment/${slug}/${token}`);
        setData(res.data);
      } catch {
        setError(true);
      } finally { setLoading(false); }
    })();
  }, [slug, token]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <Cog size={40} className="text-emerald-400 animate-spin" />
    </div>
  );

  if (error || !data || !data.available) return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-950">
      <AlertCircle size={48} className="text-slate-500 mb-4" />
      <p className="text-slate-300 text-lg font-medium text-center">
        {data?.message || "Este equipamento não possui informações públicas disponíveis."}
      </p>
      <p className="text-slate-600 text-sm mt-3">Verifique o QR Code e tente novamente</p>
    </div>
  );

  const eq = data.equipment || {};
  const hasImage = eq.image_url && !imgError;

  const specs = [
    { icon: Gauge, label: "Potência", value: eq.potencia },
    { icon: Zap, label: "Tensão", value: eq.tensao },
    { icon: Gauge, label: "Rotação", value: eq.rotacao },
    { icon: Weight, label: "Peso", value: eq.peso },
    { icon: Maximize2, label: "Capacidade", value: eq.capacidade },
    { icon: Box, label: "Dimensões", value: eq.dimensoes },
  ].filter(s => s.value);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200" data-testid="public-equipment-page">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-800 px-4 py-3 flex items-center gap-3">
        {eq.logo_url && (
          <img src={`${BACKEND_URL}${eq.logo_url}`} alt="" className="h-8 w-8 rounded object-contain bg-white/10" onError={e => e.target.style.display = 'none'} />
        )}
        <div className="min-w-0">
          {eq.empresa && <p className="text-sm font-semibold text-slate-200 truncate">{eq.empresa}</p>}
          {eq.unidade && <p className="text-xs text-slate-500 truncate">{eq.unidade}</p>}
        </div>
      </header>

      {/* Hero Image */}
      {hasImage ? (
        <div className="w-full aspect-video bg-slate-900 flex items-center justify-center overflow-hidden">
          <img
            src={`${BACKEND_URL}${eq.image_url}`}
            alt={eq.nome || "Equipamento"}
            className="w-full h-full object-cover"
            onError={() => setImgError(true)}
          />
        </div>
      ) : (
        <div className="w-full h-40 bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center">
          <Factory size={56} className="text-slate-700" />
        </div>
      )}

      {/* Main Info */}
      <div className="px-4 py-5">
        {eq.tag && (
          <span className="inline-block bg-emerald-500/15 text-emerald-400 text-xs font-bold px-2.5 py-1 rounded-md mb-2 tracking-wider">{eq.tag}</span>
        )}
        <h1 className="text-xl font-bold text-white leading-tight" data-testid="equipment-name">
          {eq.nome || "Equipamento"}
        </h1>

        {(eq.fabricante || eq.modelo) && (
          <p className="text-sm text-slate-400 mt-1.5">
            {[eq.fabricante, eq.modelo].filter(Boolean).join(" · ")}
          </p>
        )}
        {eq.ano && <p className="text-xs text-slate-500 mt-0.5">Ano: {eq.ano}</p>}

        {eq.area && (
          <div className="flex items-center gap-1.5 mt-3 text-sm text-slate-400">
            <MapPin size={14} className="text-slate-500" />
            <span>{[eq.area, eq.unidade].filter(Boolean).join(" · ")}</span>
          </div>
        )}

        {eq.status_publico && (
          <div className="mt-3 inline-flex items-center gap-1.5 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            {eq.status_publico}
          </div>
        )}
      </div>

      {/* Description */}
      {eq.descricao && (
        <div className="px-4 pb-4">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Descrição</h2>
          <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">{eq.descricao}</p>
        </div>
      )}

      {/* Specs */}
      {specs.length > 0 && (
        <div className="px-4 pb-5">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Dados Técnicos</h2>
          <div className="grid grid-cols-2 gap-2">
            {specs.map(({ icon: Icon, label, value }) => (
              <div key={label} className="bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2.5">
                <div className="flex items-center gap-1.5 mb-1">
                  <Icon size={12} className="text-emerald-400" />
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</span>
                </div>
                <p className="text-sm font-medium text-slate-200">{value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Type */}
      {eq.tipo_equipamento && (
        <div className="px-4 pb-5">
          <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg px-3 py-2.5">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider">Tipo</span>
            <p className="text-sm text-slate-200 capitalize">{eq.tipo_equipamento}</p>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800 px-4 py-6 text-center mt-4">
        <p className="text-xs text-slate-500">Equipamento monitorado pelo MAINTRIX Enterprise</p>
        <a href="https://maintrix.com.br" target="_blank" rel="noopener noreferrer"
           className="text-xs text-emerald-500 hover:text-emerald-400 mt-1 inline-block">
          Conheça o MAINTRIX
        </a>
      </footer>
    </div>
  );
};

export default PublicEquipmentPage;
