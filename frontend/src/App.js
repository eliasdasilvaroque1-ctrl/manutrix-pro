import React, { useState, useEffect, useRef, useMemo, useCallback, memo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Plus, Search, Menu, LogOut, Settings, BarChart3, Lock, Bell, ChevronDown, Home, Book, Briefcase, Wrench, Truck, BarChart, Users, Eye, AlertCircle, ChevronRight, Filter, X, Clock, Calendar, CheckCircle, AlertTriangle, TrendingUp, TrendingDown, DollarSign, Activity, Zap, Package, Boxes, Shield, FileText, MoreVertical, Edit, Trash2, Eye as EyeIcon, ChevronUp, FileSpreadsheet, MapPin, Tool, Gauge, Cog, Terminal, Save, ChevronLeft, SkipBack, PlayCircle, PauseCircle, CheckCircle2, Hash, Layers, ArrowUp, ArrowDown, Grid, List, Download, Upload, Copy, RefreshCw, Loader, AlertCircle as AlertIconC, GripVertical, GripHorizontal, Maximize, Minimize, Minus, SquareCheck, Circle, Triangle, Square, Star, Flag, Message, MessageCircle, Mail, Phone, MapPin as LocationIcon, Calendar as CalendarIcon, Clock as ClockIcon, User, LogIn, Eye as ViewIcon, EyeOff, Folder, File, FilePlus, Video, Volume2, VolumeX, Mic, Maximize2, Minimize2, SkipForward, Info, Lightbulb, Zap as ZapIcon, TrendingUp as TrendingUpIcon, TrendingDown as TrendingDownIcon, MoreHorizontal, Move, Pause, Play, Repeat, RotateCw, Search as SearchIcon, Sliders, Target, Trash, Edit2, Eye as EyeOpen, EyeOff as EyeOffIcon, Copy as CopyIcon, Share2, Download as DownloadIcon, Upload as UploadIcon, Plus as PlusIcon, Minus as MinusIcon, X as XIcon, Check, CheckCircle as CheckCircleIcon, AlertCircle as AlertIcon, Info as InfoIcon, Lock as LockIcon, Unlock, Eye as EyeUIcon, MapPin as MapPinIcon, Phone as PhoneIcon, Mail as MailIcon, MessageCircle as MessageCircleIcon, User as UserIcon, Home as HomeIcon, Settings as SettingsIcon, LogOut as LogOutIcon, Menu as MenuIcon, Search as SearchIconF, Plus as PlusIconF, List as ListIcon, Grid as GridIcon, Download as DownloadIconF, Upload as UploadIconF, Filter as FilterIcon, MoreVertical as MoreVerticalIcon, Edit as EditIcon, Trash as TrashIcon, Archive, Package as PackageIcon, AlertTriangle as WarningIcon, ChevronDown as ChevronDownIcon, ChevronLeft as ChevronLeftIcon, ChevronRight as ChevronRightIcon } from 'lucide-react';
import { useAuth } from './lib/api';
import { useBranding } from './lib/branding';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showOrgSelector, setShowOrgSelector] = useState(false);
  const [empresaBusca, setEmpresaBusca] = useState('');
  const [showEmpresaDropdown, setShowEmpresaDropdown] = useState(false);
  const { login } = useAuth();
  const { branding, organizations, selectOrg, orgId, loadOrganizations } = useBranding();
  const safeOrganizations = useMemo(() => (Array.isArray(organizations) ? organizations : []), [organizations]);
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  useEffect(() => {
    if (user) navigate('/central');
  }, [user, navigate]);

  useEffect(() => {
    if (orgId) return;
    const hostname = window.location.hostname;
    const parts = hostname.split('.');
    const sub = parts.length >= 3 ? parts[0].toLowerCase() : null;
    const isCustomer = sub && sub !== 'www' && sub !== 'app' && !['localhost','127.0.0.1','preview','emergentagent','vercel','railway','netlify'].some(p => hostname.includes(p));
    if (isCustomer && safeOrganizations.length > 0) {
      const matchOrg = safeOrganizations.find(o => (o.subdominio || '').toLowerCase() === sub || (o.nome || '').toLowerCase().includes(sub));
      if (matchOrg) {
        selectOrg(matchOrg.id);
        setEmpresaBusca(matchOrg.nome);
        setOrgSource('subdomain');
        return;
      }
    }
    // Then localStorage
    const saved = localStorage.getItem('maintrix_last_org');
    if (saved) {
      const org = safeOrganizations.find(o => o.id === saved);
      if (org) {
        selectOrg(org.id);
        setEmpresaBusca(org.nome);
        setOrgSource('remembered');
        return;
      }
    }
    // Single org
    if (safeOrganizations.length === 1) {
      selectOrg(safeOrganizations[0].id);
      setEmpresaBusca(safeOrganizations[0].nome);
      setOrgSource('single');
    }
  }, [safeOrganizations, orgId, selectOrg]);

  const handleSelectEmpresa = (org) => {
    selectOrg(org.id);
    setEmpresaBusca(org.nome);
    setShowEmpresaDropdown(false);
    setShowOrgSelector(false);
    setOrgSource('manual');
    localStorage.setItem('maintrix_last_org', org.id);
  };

  const handleTrocarOrg = () => {
    setOrgSource(null);
    setShowOrgSelector(true);
    setEmpresaBusca('');
    setShowEmpresaDropdown(false);
    setIsMasterUser(false);
  };

  // Auto-detect org from email (for non-master users)
  const [autoOrgLoading, setAutoOrgLoading] = useState(false);
  const [orgSource, setOrgSource] = useState(null);
  const [isMasterUser, setIsMasterUser] = useState(false);
  const [tempToken, setTempToken] = useState(null);
  const [view, setView] = useState('login');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const handleEmailBlur = async () => {
    if (!email || orgId) return;
    setAutoOrgLoading(true);
    try {
      const res = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/auth/lookup-email`, { email: email.trim() });
      if (res.data.is_master) {
        setIsMasterUser(true);
        setShowOrgSelector(true);
      } else {
        selectOrg(res.data.organization_id);
        setEmpresaBusca(res.data.organization_name);
        setOrgSource('auto');
        setIsMasterUser(false);
      }
    } catch {
      // Email not found — show org selector as fallback
      if (!orgId) setShowOrgSelector(true);
    } finally { setAutoOrgLoading(false); }
  };

  const filteredOrgs = safeOrganizations.filter(o =>
    !empresaBusca || (o.nome || '').toLowerCase().includes(empresaBusca.toLowerCase())
  );

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!orgId) { toast.error('Selecione uma empresa'); return; }
    setLoading(true);
    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/auth/login`, { email, password, organization_id: orgId });
      if (response.data.user?.force_password_change) {
        setTempToken(response.data.access_token);
        setView('forceChange');
        toast.info('Você precisa trocar sua senha');
      } else {
        login(response.data);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error('Senhas não correspondem');
      return;
    }
    try {
      const res = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/auth/change-password`, {
        access_token: tempToken,
        new_password: newPassword,
      });
      login(res.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao trocar senha');
    }
  };

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: branding.cor_login }}>
      <div className="flex-1 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-md">
          {view === 'login' && (
            <div>
              <div className="text-center mb-8">
                <h1 className="text-3xl font-bold mb-2" style={{ color: branding.cor_primaria }}>
                  {branding.nome_empresa}
                </h1>
                <p className="text-sm" style={{ color: branding.cor_texto }}>
                  {branding.texto_login}
                </p>
              </div>

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium mb-1" style={{ color: branding.cor_texto }}>
                    E-mail
                  </label>
                  <input
                    type="email"
                    placeholder="seu@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onBlur={handleEmailBlur}
                    className="w-full px-3 py-2 rounded border text-sm"
                    style={{
                      backgroundColor: branding.cor_fundo,
                      borderColor: branding.cor_primaria,
                      color: branding.cor_texto,
                    }}
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium mb-1" style={{ color: branding.cor_texto }}>
                    Senha
                  </label>
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-2 rounded border text-sm"
                    style={{
                      backgroundColor: branding.cor_fundo,
                      borderColor: branding.cor_primaria,
                      color: branding.cor_texto,
                    }}
                  />
                </div>

                {/* Organização Selector */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="block text-xs font-medium" style={{ color: branding.cor_texto }}>
                      {orgSource === 'subdomain' ? 'Ambiente' : 'Organização'}
                    </label>
                    {orgId && orgSource !== 'single' && (
                      <button
                        type="button"
                        onClick={handleTrocarOrg}
                        className="text-xs underline"
                        style={{ color: branding.cor_primaria }}
                      >
                        Trocar
                      </button>
                    )}
                  </div>

                  {!showOrgSelector ? (
                    <div className="flex items-center gap-3 p-3 rounded-lg border" style={{ backgroundColor: 'var(--brand-surface)' }}>
                      {(() => { const selOrg = safeOrganizations.find(o => o.id === orgId); return selOrg?.logo_url ? (
                        <img src={selOrg.logo_url} alt="" className="w-8 h-8 rounded-lg object-contain bg-slate-800 p-0.5" />
                      ) : (
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-xs" style={{ backgroundColor: branding.cor_primaria }}>
                          {selOrg?.nome?.[0]?.toUpperCase() || '?'}
                        </div>
                      ); })()}
                      <span className="text-sm flex-1" style={{ color: branding.cor_texto }}>
                        {(() => { const selOrg = safeOrganizations.find(o => o.id === orgId); return selOrg?.nome || 'Selecione...'; })()}
                      </span>
                    </div>
                  ) : (
                    <div className="relative">
                      <input
                        type="text"
                        placeholder="Buscar empresa..."
                        value={empresaBusca}
                        onChange={(e) => { setEmpresaBusca(e.target.value); setShowEmpresaDropdown(true); }}
                        onFocus={() => setShowEmpresaDropdown(true)}
                        className="w-full px-3 py-2 rounded border text-sm"
                        style={{
                          backgroundColor: branding.cor_fundo,
                          borderColor: branding.cor_primaria,
                          color: branding.cor_texto,
                        }}
                      />
                      {showEmpresaDropdown && filteredOrgs.length > 0 && (
                        <div className="absolute z-10 top-full left-0 right-0 mt-1 rounded-lg border shadow-lg" style={{ backgroundColor: branding.cor_fundo }}>
                          {filteredOrgs.map((org) => (
                            <button
                              key={org.id}
                              type="button"
                              onClick={() => handleSelectEmpresa(org)}
                              className="w-full text-left px-3 py-2 text-sm hover:opacity-80 flex items-center gap-2"
                              style={{ color: branding.cor_texto }}
                            >
                              {org.logo_url && <img src={org.logo_url} alt="" className="w-6 h-6 rounded object-contain" />}
                              {org.nome}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={loading || !orgId}
                  className="w-full py-2 rounded font-medium text-sm transition"
                  style={{
                    backgroundColor: branding.cor_primaria,
                    color: branding.cor_fundo,
                  }}
                >
                  {loading ? 'Entrando...' : 'Entrar'}
                </button>
              </form>
            </div>
          )}

          {view === 'forceChange' && (
            <div>
              <h2 className="text-xl font-bold mb-6 text-center" style={{ color: branding.cor_primaria }}>
                Trocar Senha
              </h2>
              <form onSubmit={handleChangePassword} className="space-y-4">
                <input
                  type="password"
                  placeholder="Nova senha"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 rounded border text-sm"
                  style={{
                    backgroundColor: branding.cor_fundo,
                    borderColor: branding.cor_primaria,
                    color: branding.cor_texto,
                  }}
                />
                <input
                  type="password"
                  placeholder="Confirmar senha"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-3 py-2 rounded border text-sm"
                  style={{
                    backgroundColor: branding.cor_fundo,
                    borderColor: branding.cor_primaria,
                    color: branding.cor_texto,
                  }}
                />
                <button
                  type="submit"
                  className="w-full py-2 rounded font-medium text-sm"
                  style={{
                    backgroundColor: branding.cor_primaria,
                    color: branding.cor_fundo,
                  }}
                >
                  Confirmar
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
