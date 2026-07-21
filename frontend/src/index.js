import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

// HOTFIX P0: Listener global para ChunkLoadError não capturado pelo ErrorBoundary
// Limpa caches do app e faz reload único por sessão
window.addEventListener("error", (event) => {
  const error = event.error;
  if (
    error &&
    (error.name === "ChunkLoadError" ||
      (error.message &&
        (error.message.includes("Loading chunk") ||
          error.message.includes("Loading CSS chunk") ||
          error.message.includes("Failed to fetch dynamically imported module"))))
  ) {
    const key = "global_chunk_reload_attempted";
    if (!sessionStorage.getItem(key)) {
      sessionStorage.setItem(key, Date.now().toString());
      if ("caches" in window) {
        caches.keys().then((keys) => {
          const appCaches = keys.filter((k) => k.startsWith("maintrix"));
          return Promise.all(appCaches.map((k) => caches.delete(k)));
        }).finally(() => window.location.reload());
      } else {
        window.location.reload();
      }
    }
  }
});

// Limpa a flag global após carregamento bem-sucedido
window.addEventListener("load", () => {
  sessionStorage.removeItem("global_chunk_reload_attempted");
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
