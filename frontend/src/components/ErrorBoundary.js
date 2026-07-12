import { Component } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error("[ErrorBoundary]", error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  handleHome = () => {
    window.location.href = "/";
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6" style={{ background: "var(--cor-fundo, #0f172a)" }} data-testid="error-boundary-page">
          <div className="max-w-md w-full text-center space-y-6">
            <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto" style={{ background: "rgba(239,68,68,0.15)" }}>
              <AlertTriangle size={32} style={{ color: "#ef4444" }} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-100 mb-2">Algo deu errado</h1>
              <p className="text-sm text-slate-400">
                Ocorreu um erro inesperado. Tente recarregar a página ou voltar ao início.
              </p>
            </div>
            {this.state.error && (
              <div className="text-left text-xs font-mono p-3 rounded-lg border max-h-32 overflow-y-auto" style={{ background: "rgba(15,23,42,0.8)", borderColor: "rgba(100,116,139,0.3)", color: "#94a3b8" }}>
                {this.state.error.toString()}
              </div>
            )}
            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleReload}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all"
                style={{ background: "var(--cor-primaria, #10b981)", color: "#0f172a" }}
                data-testid="error-boundary-reload"
              >
                <RefreshCw size={16} /> Recarregar
              </button>
              <button
                onClick={this.handleHome}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium border transition-all"
                style={{ borderColor: "rgba(100,116,139,0.4)", color: "#94a3b8" }}
                data-testid="error-boundary-home"
              >
                <Home size={16} /> Início
              </button>
            </div>
            <p className="text-xs text-slate-600">MAINTRIX v5.2.0-RC2</p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
