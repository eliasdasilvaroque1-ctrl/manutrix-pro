import { Component } from "react";
import { RefreshCw, AlertCircle, Cog } from "lucide-react";

// Flag específica por sessão para evitar loops de reload
const CHUNK_RELOAD_KEY = "public_equipment_chunk_reload_attempted";

/**
 * Verifica se o erro é um ChunkLoadError (falha ao carregar chunk JS/CSS após deploy)
 */
function isChunkLoadError(error) {
  if (!error) return false;
  const name = error.name || "";
  const message = error.message || "";
  return (
    name === "ChunkLoadError" ||
    message.includes("Loading chunk") ||
    message.includes("Loading CSS chunk") ||
    message.includes("Failed to fetch dynamically imported module") ||
    message.includes("Unexpected token '<'")
  );
}

/**
 * Limpa SOMENTE caches relacionados ao app MAINTRIX (não afeta caches globais do navegador)
 */
async function clearAppCaches() {
  if (!("caches" in window)) return;
  try {
    const keys = await caches.keys();
    const appCaches = keys.filter(
      (k) => k.startsWith("maintrix") || k.startsWith("workbox")
    );
    await Promise.all(appCaches.map((k) => caches.delete(k)));
    console.info("[PublicErrorBoundary] Caches do app limpos:", appCaches);
  } catch (e) {
    console.warn("[PublicErrorBoundary] Falha ao limpar caches:", e);
  }
}

class PublicErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, isChunkError: false };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      error,
      isChunkError: isChunkLoadError(error),
    };
  }

  componentDidCatch(error, errorInfo) {
    console.error("[PublicErrorBoundary] Erro capturado:", error);
    console.error("[PublicErrorBoundary] Info:", errorInfo);

    // Se for ChunkLoadError e ainda não tentamos reload nesta sessão
    if (isChunkLoadError(error)) {
      const alreadyAttempted = sessionStorage.getItem(CHUNK_RELOAD_KEY);
      if (!alreadyAttempted) {
        console.info("[PublicErrorBoundary] ChunkLoadError detectado — limpando caches e recarregando (1x)");
        sessionStorage.setItem(CHUNK_RELOAD_KEY, Date.now().toString());
        clearAppCaches().finally(() => {
          window.location.reload();
        });
        return;
      }
      console.warn("[PublicErrorBoundary] ChunkLoadError persistente — exibindo fallback (reload já tentado)");
    }
  }

  handleRetry = () => {
    // Limpa a flag e força reload limpo
    sessionStorage.removeItem(CHUNK_RELOAD_KEY);
    clearAppCaches().finally(() => {
      window.location.reload();
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="min-h-screen flex items-center justify-center p-6"
          style={{ backgroundColor: "#0f172a" }}
          data-testid="public-error-boundary"
        >
          <div className="max-w-sm w-full text-center space-y-6">
            {/* Identidade visual MAINTRIX */}
            <div className="flex flex-col items-center gap-2">
              <div
                className="w-14 h-14 rounded-xl flex items-center justify-center"
                style={{
                  backgroundColor: "rgba(16,185,129,0.1)",
                  border: "1px solid rgba(16,185,129,0.2)",
                }}
              >
                <Cog size={28} style={{ color: "#10b981" }} />
              </div>
              <h1
                className="text-lg font-bold tracking-widest"
                style={{ color: "#10b981" }}
              >
                MAINTRIX
              </h1>
            </div>

            {/* Mensagem de erro */}
            <div>
              <AlertCircle
                size={40}
                className="mx-auto mb-3"
                style={{ color: "#64748b" }}
              />
              <p className="text-sm" style={{ color: "#94a3b8" }}>
                {this.state.isChunkError
                  ? "Uma atualização foi detectada. Toque no botão abaixo para recarregar."
                  : "Ocorreu um erro ao carregar esta página. Tente novamente."}
              </p>
            </div>

            {/* Botão "Tentar novamente" */}
            <button
              onClick={this.handleRetry}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg text-sm font-semibold transition-all active:scale-95"
              style={{
                backgroundColor: "#10b981",
                color: "#0f172a",
              }}
              data-testid="public-error-retry-btn"
            >
              <RefreshCw size={16} />
              Tentar novamente
            </button>

            {/* Info técnica (colapsável para debug) */}
            {this.state.error && (
              <details className="text-left">
                <summary
                  className="text-xs cursor-pointer select-none"
                  style={{ color: "#475569" }}
                >
                  Detalhes técnicos
                </summary>
                <pre
                  className="mt-2 text-xs font-mono p-3 rounded-lg overflow-auto max-h-24"
                  style={{
                    backgroundColor: "rgba(15,23,42,0.8)",
                    border: "1px solid rgba(100,116,139,0.2)",
                    color: "#64748b",
                  }}
                >
                  {this.state.error.toString()}
                </pre>
              </details>
            )}

            <p className="text-xs" style={{ color: "#334155" }}>
              MAINTRIX Enterprise
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default PublicErrorBoundary;

/**
 * Limpa a flag de reload após carregamento bem-sucedido da página.
 * Deve ser chamada no useEffect do componente público ao montar com sucesso.
 */
export function clearChunkReloadFlag() {
  const attempted = sessionStorage.getItem(CHUNK_RELOAD_KEY);
  if (attempted) {
    console.info("[PublicErrorBoundary] Página carregou com sucesso — limpando flag de reload");
    sessionStorage.removeItem(CHUNK_RELOAD_KEY);
  }
}
