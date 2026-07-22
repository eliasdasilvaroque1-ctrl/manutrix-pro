/**
 * PublicEquipmentPage — Dossiê Digital Público do Ativo
 * RC P1 v1.0 — Fase 3: Página Pública Evoluída
 *
 * Mobile-first. Renderiza apenas blocos com conteúdo público.
 * Dados filtrados no backend (projeção segura).
 */
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  Cog, AlertCircle, MapPin, Factory, Gauge, Zap, Shield, Lightbulb,
  AlertTriangle, CheckCircle, FileText, Download, Wrench, ClipboardCheck,
  Calendar, Clock, Activity, ChevronRight
} from "lucide-react";
import axios from "axios";
import { BACKEND_URL } from "../lib/api";
import { clearChunkReloadFlag } from "../components/PublicErrorBoundary";

// ============== STATUS CONFIG ==============
const STATUS_COLORS = {
  green: { bg: "bg-emerald-500/15", border: "border-emerald-500/30", text: "text-emerald-400", dot: "bg-emerald-400" },
  red: { bg: "bg-red-500/15", border: "border-red-500/30", text: "text-red-400", dot: "bg-red-400" },
  yellow: { bg: "bg-amber-500/15", border: "border-amber-500/30", text: "text-amber-400", dot: "bg-amber-400" },
  blue: { bg: "bg-blue-500/15", border: "border-blue-500/30", text: "text-blue-400", dot: "bg-blue-400" },
};

// ============== SAFE TEXT (prevent XSS) ==============
function safeText(text) {
  if (!text) return "";
  return String(text).replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ============== TECH FIELD LABELS ==============
const TECH_LABELS = {
  fabricante: "Fabricante", modelo: "Modelo", numero_serie: "N. Serie", ano: "Ano",
  potencia: "Potencia", tensao: "Tensao", corrente: "Corrente", frequencia: "Frequencia",
  rotacao: "Rotacao", peso: "Peso", capacidade: "Capacidade", dimensoes: "Dimensoes",
  tipo_equipamento: "Tipo",
};

// ============== FORMAT DATE ==============
function formatDate(dateStr) {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
  } catch { return ""; }
}

// ============== SECTION HEADING ==============
const SectionTitle = ({ children }) => (
  <h2 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2.5">{children}</h2>
);

// ============== INFO BLOCK ==============
const InfoBlock = ({ icon: Icon, title, text, colorClass }) => {
  if (!text) return null;
  return (
    <div className={`rounded-xl border px-4 py-3 ${colorClass}`} data-testid={`block-${title.toLowerCase().replace(/\s/g, "-")}`}>
      <div className="flex items-center gap-2 mb-1.5">
        <Icon size={15} />
        <span className="text-xs font-semibold">{title}</span>
      </div>
      <p className="text-sm leading-relaxed text-slate-300 whitespace-pre-line">{text}</p>
    </div>
  );
};

// ============== MAIN COMPONENT ==============
const PublicEquipmentPage = () => {
  const { slug, token } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [imgError, setImgError] = useState(false);

  useEffect(() => { clearChunkReloadFlag(); }, []);

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

  // --- Loading ---
  if (loading) return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 gap-3">
      <Cog size={36} className="text-emerald-400 animate-spin" />
      <p className="text-xs text-slate-600">Carregando equipamento...</p>
    </div>
  );

  // --- Error / Not Available ---
  if (error || !data || !data.available) return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-950">
      <div className="w-14 h-14 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center mb-4">
        <AlertCircle size={28} className="text-slate-500" />
      </div>
      <p className="text-slate-300 text-base font-medium text-center max-w-xs">
        {data?.message || "Este equipamento nao possui informacoes publicas disponiveis."}
      </p>
      <p className="text-slate-600 text-xs mt-3 text-center">Verifique o QR Code e tente novamente</p>
    </div>
  );

  const eq = data.equipment || {};
  const branding = eq.branding || {};
  const brandColor = branding.cor_primaria || "#10b981";
  const hasImage = eq.image_url && !imgError;
  const tech = eq.technical_data || {};
  const loc = eq.location || {};
  const history = eq.history_summary || {};
  const inspections = eq.inspections || [];
  const maintenance = eq.maintenance || [];
  const documents = eq.documents || [];
  const statusStyle = STATUS_COLORS[eq.status_color] || STATUS_COLORS.green;

  // Build location string
  const locParts = [loc.area, loc.unidade, loc.linha, loc.ponto_instalacao].filter(Boolean);

  // Build tech entries from the technical_data object
  const techEntries = Object.entries(tech)
    .filter(([, v]) => v && v !== "" && v !== "undefined")
    .map(([k, v]) => ({ label: TECH_LABELS[k] || k, value: v }));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200" data-testid="public-equipment-page">
      {/* ===== 1. BRANDING HEADER ===== */}
      <header className="bg-slate-900 border-b border-slate-800 px-4 py-3 flex items-center gap-3" style={{ borderBottomColor: `${brandColor}30` }}>
        {branding.logo_url ? (
          <img
            src={branding.logo_url.startsWith("http") ? branding.logo_url : `${BACKEND_URL}${branding.logo_url}`}
            alt={branding.nome_empresa || "Logo"}
            className="h-8 w-8 rounded-lg object-contain bg-white/5 p-0.5"
            onError={e => { e.target.style.display = "none"; }}
          />
        ) : (
          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold" style={{ backgroundColor: `${brandColor}20`, color: brandColor }}>
            {(branding.nome_empresa || "M").substring(0, 2).toUpperCase()}
          </div>
        )}
        <div className="min-w-0">
          {(branding.nome_empresa || eq.empresa) && (
            <p className="text-sm font-semibold text-slate-200 truncate">{branding.nome_empresa || eq.empresa}</p>
          )}
          {loc.unidade && <p className="text-[10px] text-slate-500 truncate">{loc.unidade}</p>}
        </div>
      </header>

      {/* Container com largura limitada em desktop */}
      <div className="max-w-2xl mx-auto">

        {/* ===== 2. FOTO ===== */}
        {hasImage ? (
          <div className="w-full aspect-video bg-slate-900 overflow-hidden">
            <img
              src={`${BACKEND_URL}${eq.image_url}`}
              alt={eq.nome || "Equipamento"}
              className="w-full h-full object-cover"
              loading="lazy"
              onError={() => setImgError(true)}
            />
          </div>
        ) : (
          <div className="w-full h-32 bg-gradient-to-br from-slate-800/80 to-slate-900 flex items-center justify-center">
            <Factory size={48} className="text-slate-700/60" />
          </div>
        )}

        {/* ===== 3. IDENTIFICACAO ===== */}
        <div className="px-4 pt-4 pb-3">
          {eq.tag && (
            <span className="inline-block text-[11px] font-bold px-2 py-0.5 rounded-md mb-2 tracking-wider" style={{ backgroundColor: `${brandColor}15`, color: brandColor }}>
              {eq.tag}
            </span>
          )}
          <h1 className="text-xl font-bold text-white leading-tight" data-testid="equipment-name">
            {eq.nome || "Equipamento"}
          </h1>
          {(eq.fabricante || eq.modelo) && (
            <p className="text-sm text-slate-400 mt-1">
              {[eq.fabricante, eq.modelo].filter(Boolean).join(" / ")}
            </p>
          )}
          {eq.ano && <p className="text-xs text-slate-500 mt-0.5">Ano: {eq.ano}</p>}
        </div>

        {/* ===== 4. STATUS ===== */}
        {eq.status_publico && (
          <div className="px-4 pb-3">
            <div className={`inline-flex items-center gap-2 ${statusStyle.bg} ${statusStyle.border} border rounded-lg px-3 py-1.5`} data-testid="public-status">
              <span className={`w-2 h-2 rounded-full ${statusStyle.dot}`} aria-hidden="true" />
              <span className={`text-xs font-medium ${statusStyle.text}`}>{eq.status_publico}</span>
            </div>
          </div>
        )}

        {/* ===== 5. LOCALIZACAO ===== */}
        {locParts.length > 0 && (
          <div className="px-4 pb-3">
            <div className="flex items-start gap-2 text-sm text-slate-400">
              <MapPin size={14} className="text-slate-500 mt-0.5 shrink-0" />
              <span>{locParts.join(" / ")}</span>
            </div>
          </div>
        )}

        {/* ===== 6. DESCRICAO ===== */}
        {eq.description && (
          <div className="px-4 pb-4">
            <SectionTitle>Descricao</SectionTitle>
            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">{eq.description}</p>
          </div>
        )}

        {/* ===== 7-10. BLOCOS INFORMATIVOS ===== */}
        {(eq.curiosity || eq.warning || eq.safety || eq.best_practices) && (
          <div className="px-4 pb-4 space-y-2.5">
            <InfoBlock
              icon={Lightbulb} title="Voce Sabia?" text={eq.curiosity}
              colorClass="bg-amber-500/5 border-amber-500/20 text-amber-400"
            />
            <InfoBlock
              icon={AlertTriangle} title="Atencao" text={eq.warning}
              colorClass="bg-orange-500/5 border-orange-500/20 text-orange-400"
            />
            <InfoBlock
              icon={Shield} title="Seguranca" text={eq.safety}
              colorClass="bg-red-500/5 border-red-500/20 text-red-400"
            />
            <InfoBlock
              icon={CheckCircle} title="Boas Praticas" text={eq.best_practices}
              colorClass="bg-emerald-500/5 border-emerald-500/20 text-emerald-400"
            />
          </div>
        )}

        {/* ===== 11. DADOS TECNICOS ===== */}
        {techEntries.length > 0 && (
          <div className="px-4 pb-4">
            <SectionTitle>Dados Tecnicos</SectionTitle>
            <div className="grid grid-cols-2 gap-2">
              {techEntries.map(({ label, value }) => (
                <div key={label} className="bg-slate-800/50 border border-slate-700/40 rounded-lg px-3 py-2">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">{label}</p>
                  <p className="text-sm font-medium text-slate-200">{value}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ===== 12. ULTIMAS INSPECOES ===== */}
        {inspections.length > 0 && (
          <div className="px-4 pb-4">
            <SectionTitle>Ultimas Inspecoes</SectionTitle>
            <div className="space-y-1.5">
              {inspections.map((insp, i) => (
                <div key={i} className="flex items-center gap-3 bg-slate-800/40 border border-slate-700/30 rounded-lg px-3 py-2.5">
                  <ClipboardCheck size={16} className="text-blue-400 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-slate-200 capitalize">{insp.tipo || "Inspecao"}</span>
                      {insp.resultado && (
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${insp.resultado === "conforme" || insp.resultado === "aprovado" ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>
                          {insp.resultado}
                        </span>
                      )}
                    </div>
                    {insp.data && <p className="text-[10px] text-slate-500 mt-0.5">{formatDate(insp.data)}</p>}
                  </div>
                  {insp.status && (
                    <span className="text-[10px] text-slate-500 capitalize shrink-0">{insp.status}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ===== 13. ULTIMAS MANUTENCOES ===== */}
        {maintenance.length > 0 && (
          <div className="px-4 pb-4">
            <SectionTitle>Ultimas Manutencoes</SectionTitle>
            <div className="space-y-1.5">
              {maintenance.map((os, i) => (
                <div key={i} className="flex items-center gap-3 bg-slate-800/40 border border-slate-700/30 rounded-lg px-3 py-2.5">
                  <Wrench size={16} className="text-emerald-400 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-slate-200 truncate">{os.titulo || os.tipo || "Manutencao"}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      {os.tipo && <span className="text-[10px] text-slate-500 capitalize">{os.tipo}</span>}
                      {os.data && <span className="text-[10px] text-slate-600">{formatDate(os.data)}</span>}
                    </div>
                  </div>
                  {os.status && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 capitalize shrink-0">{os.status}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ===== 14. HISTORICO RESUMIDO ===== */}
        {(history.total_manutencoes || history.total_inspecoes) && (
          <div className="px-4 pb-4">
            <SectionTitle>Historico</SectionTitle>
            <div className="grid grid-cols-2 gap-2">
              {history.total_manutencoes > 0 && (
                <div className="bg-slate-800/40 border border-slate-700/30 rounded-lg px-3 py-2 text-center">
                  <p className="text-lg font-bold text-slate-200">{history.total_manutencoes}</p>
                  <p className="text-[10px] text-slate-500">Manutencoes</p>
                  {history.ultima_manutencao && <p className="text-[9px] text-slate-600 mt-0.5">Ultima: {formatDate(history.ultima_manutencao)}</p>}
                </div>
              )}
              {history.total_inspecoes > 0 && (
                <div className="bg-slate-800/40 border border-slate-700/30 rounded-lg px-3 py-2 text-center">
                  <p className="text-lg font-bold text-slate-200">{history.total_inspecoes}</p>
                  <p className="text-[10px] text-slate-500">Inspecoes</p>
                  {history.ultima_inspecao && <p className="text-[9px] text-slate-600 mt-0.5">Ultima: {formatDate(history.ultima_inspecao)}</p>}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ===== 15. DOCUMENTOS ===== */}
        {documents.length > 0 && (
          <div className="px-4 pb-4">
            <SectionTitle>Documentos</SectionTitle>
            <div className="space-y-1.5">
              {documents.map(doc => (
                <a
                  key={doc.id}
                  href={`${BACKEND_URL}${doc.download_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 bg-slate-800/40 border border-slate-700/30 rounded-lg px-3 py-2.5 hover:border-slate-600 transition-colors active:scale-[0.99]"
                  data-testid={`public-doc-${doc.id}`}
                >
                  <FileText size={16} className="text-indigo-400 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-slate-200 truncate">{doc.title}</p>
                    <p className="text-[10px] text-slate-500">{doc.doc_type}{doc.size_bytes ? ` — ${(doc.size_bytes / 1024).toFixed(0)}KB` : ""}</p>
                  </div>
                  <Download size={14} className="text-slate-500 shrink-0" />
                </a>
              ))}
            </div>
          </div>
        )}

        {/* ===== 16. RODAPE ===== */}
        <footer className="border-t border-slate-800/60 px-4 py-5 text-center mt-2">
          <p className="text-[10px] text-slate-600">Equipamento monitorado pelo MAINTRIX Enterprise</p>
          <a href="https://maintrix.com.br" target="_blank" rel="noopener noreferrer"
             className="text-[10px] hover:underline mt-0.5 inline-block" style={{ color: brandColor }}>
            Conheca o MAINTRIX
          </a>
        </footer>
      </div>
    </div>
  );
};

export default PublicEquipmentPage;
