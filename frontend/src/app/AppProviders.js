import { useState, useEffect } from "react";
import { Shield, CheckCircle, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { AuthContext, useAuth, api } from "../lib/api";
import { BrandingProvider, useBranding } from "../lib/branding";
import { Loading, Modal } from "../components/shared";
import ErrorBoundary from "../components/ErrorBoundary";

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const storedUser = sessionStorage.getItem('maintrix_user');
    if (storedUser) setUser(JSON.parse(storedUser));
    setLoading(false);
  }, []);
  const login = (data) => {
    sessionStorage.setItem('maintrix_token', data.access_token);
    sessionStorage.setItem('maintrix_user', JSON.stringify(data.user));
    setUser(data.user);
  };
  const logout = () => {
    sessionStorage.removeItem('maintrix_token');
    sessionStorage.removeItem('maintrix_user');
    setUser(null);
  };
  return <AuthContext.Provider value={{ user, login, logout, loading }}>{children}</AuthContext.Provider>;
};

export const BrandingLoader = ({ children }) => {
  const { user } = useAuth();
  const { loadFromUser } = useBranding();
  useEffect(() => { if (user) loadFromUser(user); }, [user, loadFromUser]);
  return children;
};

export const ConsentGate = ({ children }) => {
  const { user } = useAuth();
  const [status, setStatus] = useState(null);
  const [accepting, setAccepting] = useState(false);
  const [termsChecked, setTermsChecked] = useState(false);
  const [privacyChecked, setPrivacyChecked] = useState(false);
  const [viewDoc, setViewDoc] = useState(null);
  const [docContent, setDocContent] = useState('');

  useEffect(() => {
    if (!user) { setStatus(true); return; }
    api.get('/compliance/status').then(r => setStatus(r.data.accepted)).catch(() => setStatus(true));
  }, [user]);

  const handleAccept = async () => {
    if (!termsChecked || !privacyChecked) { toast.error('Você precisa aceitar ambos os documentos'); return; }
    setAccepting(true);
    try { await api.post('/compliance/accept'); setStatus(true); toast.success('Termos aceitos com sucesso'); }
    catch { toast.error('Erro ao registrar aceite'); }
    finally { setAccepting(false); }
  };

  const loadDoc = async (type) => {
    try { const res = await api.get(`/compliance/${type === 'terms' ? 'terms' : 'privacy'}`); setDocContent(res.data.content || ''); setViewDoc(type); }
    catch { toast.error('Erro ao carregar documento'); }
  };

  if (status === null) return <Loading rows={3} />;
  if (status === true) return children;

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: 'var(--brand-bg, #0f172a)' }}>
      <div className="glass-card max-w-lg w-full p-8 space-y-6" data-testid="consent-gate">
        <div className="text-center">
          <Shield size={40} className="mx-auto text-brand mb-3" />
          <h2 className="text-xl font-bold text-primary">Termos e Privacidade</h2>
          <p className="text-sm text-secondary mt-2">Para continuar utilizando o MAINTRIX, leia e aceite os documentos abaixo.</p>
        </div>
        <div className="space-y-3">
          <label className="flex items-start gap-3 p-3 rounded-lg border border-surface hover:border-slate-600 cursor-pointer transition-colors" data-testid="terms-checkbox">
            <input type="checkbox" checked={termsChecked} onChange={e => setTermsChecked(e.target.checked)} className="mt-1 accent-emerald-500" />
            <div><p className="text-sm text-primary font-medium">Termos de Uso</p><button type="button" onClick={() => loadDoc('terms')} className="text-xs text-brand hover:underline">Ler Termos de Uso v1.0</button></div>
          </label>
          <label className="flex items-start gap-3 p-3 rounded-lg border border-surface hover:border-slate-600 cursor-pointer transition-colors" data-testid="privacy-checkbox">
            <input type="checkbox" checked={privacyChecked} onChange={e => setPrivacyChecked(e.target.checked)} className="mt-1 accent-emerald-500" />
            <div><p className="text-sm text-primary font-medium">Politica de Privacidade</p><button type="button" onClick={() => loadDoc('privacy')} className="text-xs text-brand hover:underline">Ler Politica de Privacidade v1.0</button></div>
          </label>
        </div>
        <button onClick={handleAccept} disabled={!termsChecked || !privacyChecked || accepting} className="btn-primary w-full flex items-center justify-center gap-2" data-testid="accept-compliance-btn">
          {accepting ? <RefreshCw size={16} className="animate-spin" /> : <CheckCircle size={16} />}
          {accepting ? 'Registrando...' : 'Aceitar e Continuar'}
        </button>
      </div>
      {viewDoc && (
        <Modal isOpen={true} onClose={() => setViewDoc(null)} title={viewDoc === 'terms' ? 'Termos de Uso' : 'Politica de Privacidade'} size="lg">
          <div className="prose prose-invert prose-sm max-h-[60vh] overflow-y-auto custom-scrollbar whitespace-pre-wrap text-sm text-slate-300 leading-relaxed">{docContent}</div>
        </Modal>
      )}
    </div>
  );
};

export const AppProviders = ({ children }) => (
  <ErrorBoundary>
    <BrandingProvider>
      <AuthProvider>
        {children}
      </AuthProvider>
    </BrandingProvider>
  </ErrorBoundary>
);
