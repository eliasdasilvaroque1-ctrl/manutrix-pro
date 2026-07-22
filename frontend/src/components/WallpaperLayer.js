/**
 * WallpaperLayer — Componente compartilhado para wallpaper de fundo.
 * Usado no Login, MainLayout e Preview do WhiteLabel.
 * FONTE ÚNICA de renderização — preview e sistema real idênticos.
 */
import { useState } from "react";
import { BACKEND_URL } from "../lib/api";

const BLUR_MAP = {
  sem: "0px",
  suave: "4px",
  medio: "12px",
  forte: "24px",
};

const INTENSITY_MAP = {
  0: 0,
  5: 0.05,
  10: 0.10,
  15: 0.15,
};

/**
 * Renderiza wallpaper de fundo com overlay, intensidade e blur.
 *
 * @param {string} url - URL da imagem (relativa ou absoluta)
 * @param {number} intensidade - 0, 5, 10, 15
 * @param {string} blur - "sem", "suave", "medio", "forte"
 * @param {string} corFundo - Cor de fallback
 */
const WallpaperLayer = ({ url, intensidade = 10, blur = "sem", corFundo }) => {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  if (!url || error) return null;

  const fullUrl = url.startsWith("http") ? url : `${BACKEND_URL}${url}`;
  const opacity = INTENSITY_MAP[intensidade] ?? 0.10;
  const blurValue = BLUR_MAP[blur] || "0px";

  if (opacity === 0) return null;

  return (
    <>
      {/* Preload image */}
      <img
        src={fullUrl}
        alt=""
        onLoad={() => setLoaded(true)}
        onError={() => setError(true)}
        style={{ display: "none" }}
      />
      {loaded && (
        <div
          className="fixed inset-0 pointer-events-none"
          style={{ zIndex: 0 }}
          data-testid="wallpaper-layer"
        >
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: `url(${fullUrl})`,
              backgroundSize: "cover",
              backgroundPosition: "center",
              backgroundRepeat: "no-repeat",
              opacity,
              filter: blurValue !== "0px" ? `blur(${blurValue})` : undefined,
              transform: blurValue !== "0px" ? "scale(1.05)" : undefined,
            }}
          />
        </div>
      )}
    </>
  );
};

/**
 * Determina se o wallpaper deve ser exibido na rota atual.
 *
 * @param {string} aplicacao - "somente_login", "dashboard", "sistema_inteiro"
 * @param {string} pathname - window.location.pathname
 * @param {boolean} isAuthenticated - se o usuário está logado
 */
export function shouldShowWallpaper(aplicacao, pathname, isAuthenticated) {
  if (!aplicacao) return false;
  if (aplicacao === "somente_login") return !isAuthenticated || pathname === "/login";
  if (aplicacao === "dashboard") return pathname === "/login" || pathname === "/" || pathname === "/dashboard";
  if (aplicacao === "sistema_inteiro") return true;
  return false;
}

export default WallpaperLayer;
