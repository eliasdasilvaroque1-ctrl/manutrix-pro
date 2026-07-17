import { useState, useRef, useEffect, useCallback } from "react";

const TIPO_LABELS = {
  texto_curto:'Texto curto',texto_longo:'Texto longo',numero:'Número',decimal:'Decimal',
  data:'Data',hora:'Hora',data_hora:'Data/hora',selecao_unica:'Seleção única',
  multipla_selecao:'Múltipla seleção',checkbox:'Checkbox',sim_nao:'Sim/Não',
  foto:'Foto',assinatura:'Assinatura',qr_code:'QR Code',url:'URL',email:'E-mail',telefone:'Telefone'
};

/**
 * Dynamic field renderer — renders custom fields based on type configuration.
 * @param {Array} campos - Array of campo definitions from the API
 * @param {Object} valores - Current values {identificador_tecnico: valor}
 * @param {Function} onChange - Callback (identificador_tecnico, valor)
 * @param {boolean} readOnly - If true, fields are display-only
 * @param {string} userRole - Current user role for permission checks
 */
export const DynamicFieldRenderer = ({ campos = [], valores = {}, onChange, readOnly = false, userRole = '' }) => {
  if (!campos || campos.length === 0) return null;

  const filtered = campos.filter(c => {
    if (c.status === 'inativo') return false;
    if (c.permissao_visualizacao?.length && !c.permissao_visualizacao.includes(userRole)) return false;
    return true;
  });

  if (filtered.length === 0) return null;

  return (
    <div className="space-y-3" data-testid="dynamic-fields">
      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Campos Personalizados</h4>
      {filtered.map(campo => (
        <FieldInput
          key={campo.identificador_tecnico}
          campo={campo}
          value={valores[campo.identificador_tecnico] ?? campo.valor_padrao ?? ''}
          onChange={val => onChange?.(campo.identificador_tecnico, val)}
          readOnly={readOnly || (campo.permissao_edicao?.length > 0 && !campo.permissao_edicao.includes(userRole))}
        />
      ))}
    </div>
  );
};

const FieldInput = ({ campo, value, onChange, readOnly }) => {
  const { nome, tipo, obrigatorio, placeholder, texto_ajuda, unidade_medida, opcoes, validacao_min, validacao_max, limite_caracteres, casas_decimais, mascara } = campo;

  const cls = "input-industrial w-full px-3 text-sm";
  const wrapCls = `${readOnly ? 'opacity-60' : ''}`;

  const renderInput = () => {
    switch (tipo) {
      case 'texto_curto':
        return <input type="text" value={value || ''} onChange={e => onChange(e.target.value)} placeholder={placeholder} maxLength={limite_caracteres || 255} className={cls} disabled={readOnly} data-testid={`field-${campo.identificador_tecnico}`} />;
      case 'texto_longo':
        return <textarea value={value || ''} onChange={e => onChange(e.target.value)} placeholder={placeholder} maxLength={limite_caracteres || 2000} className={`${cls} h-16`} disabled={readOnly} data-testid={`field-${campo.identificador_tecnico}`} />;
      case 'numero':
        return (
          <div className="flex gap-2 items-center">
            <input type="number" value={value ?? ''} onChange={e => onChange(e.target.value ? parseInt(e.target.value) : null)} min={validacao_min} max={validacao_max} className={cls} disabled={readOnly} data-testid={`field-${campo.identificador_tecnico}`} />
            {unidade_medida && <span className="text-xs text-slate-500 shrink-0">{unidade_medida}</span>}
          </div>
        );
      case 'decimal':
        return (
          <div className="flex gap-2 items-center">
            <input type="number" step={casas_decimais ? Math.pow(10, -casas_decimais) : 0.01} value={value ?? ''} onChange={e => onChange(e.target.value ? parseFloat(e.target.value) : null)} min={validacao_min} max={validacao_max} className={cls} disabled={readOnly} data-testid={`field-${campo.identificador_tecnico}`} />
            {unidade_medida && <span className="text-xs text-slate-500 shrink-0">{unidade_medida}</span>}
          </div>
        );
      case 'data':
        return <input type="date" value={value || ''} onChange={e => onChange(e.target.value)} className={cls} disabled={readOnly} data-testid={`field-${campo.identificador_tecnico}`} />;
      case 'hora':
        return <input type="time" value={value || ''} onChange={e => onChange(e.target.value)} className={cls} disabled={readOnly} data-testid={`field-${campo.identificador_tecnico}`} />;
      case 'data_hora':
        return <input type="datetime-local" value={value || ''} onChange={e => onChange(e.target.value)} className={cls} disabled={readOnly} data-testid={`field-${campo.identificador_tecnico}`} />;
      case 'selecao_unica':
        return (
          <select value={value || ''} onChange={e => onChange(e.target.value)} className={cls} disabled={readOnly} data-testid={`field-${campo.identificador_tecnico}`}>
            <option value="">Selecionar...</option>
            {(opcoes || []).map(o => <option key={o.valor || o} value={o.valor || o}>{o.label || o.valor || o}</option>)}
          </select>
        );
      case 'multipla_selecao': {
        const selected = Array.isArray(value) ? value : [];
        return (
          <div className="flex flex-wrap gap-2" data-testid={`field-${campo.identificador_tecnico}`}>
            {(opcoes || []).map(o => {
              const v = o.valor || o;
              const checked = selected.includes(v);
              return (
                <label key={v} className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded cursor-pointer ${checked ? 'bg-brand/20 text-brand' : 'bg-slate-800 text-slate-400'}`}>
                  <input type="checkbox" checked={checked} onChange={() => {
                    if (readOnly) return;
                    onChange(checked ? selected.filter(s => s !== v) : [...selected, v]);
                  }} disabled={readOnly} className="w-3 h-3" />
                  {o.label || v}
                </label>
              );
            })}
          </div>
        );
      }
      case 'checkbox':
        return (
          <label className="flex items-center gap-2 cursor-pointer" data-testid={`field-${campo.identificador_tecnico}`}>
            <input type="checkbox" checked={!!value} onChange={e => onChange(e.target.checked)} disabled={readOnly} className="w-4 h-4" />
            <span className="text-sm text-slate-300">{placeholder || 'Sim'}</span>
          </label>
        );
      case 'sim_nao':
        return (
          <div className="flex gap-4" data-testid={`field-${campo.identificador_tecnico}`}>
            <label className="flex items-center gap-2 cursor-pointer"><input type="radio" name={campo.identificador_tecnico} checked={value === true || value === 'true'} onChange={() => onChange(true)} disabled={readOnly} /> <span className="text-sm text-slate-300">Sim</span></label>
            <label className="flex items-center gap-2 cursor-pointer"><input type="radio" name={campo.identificador_tecnico} checked={value === false || value === 'false'} onChange={() => onChange(false)} disabled={readOnly} /> <span className="text-sm text-slate-300">Não</span></label>
          </div>
        );
      case 'url':
        return <input type="url" value={value || ''} onChange={e => onChange(e.target.value)} placeholder={placeholder || 'https://'} className={cls} disabled={readOnly} data-testid={`field-${campo.identificador_tecnico}`} />;
      case 'email':
        return <input type="email" value={value || ''} onChange={e => onChange(e.target.value)} placeholder={placeholder || 'email@example.com'} className={cls} disabled={readOnly} data-testid={`field-${campo.identificador_tecnico}`} />;
      case 'telefone':
        return <input type="tel" value={value || ''} onChange={e => onChange(e.target.value)} placeholder={placeholder || '(00) 00000-0000'} className={cls} disabled={readOnly} data-testid={`field-${campo.identificador_tecnico}`} />;
      case 'foto':
        return <div className="text-xs text-slate-500" data-testid={`field-${campo.identificador_tecnico}`}>{value ? 'Foto anexada' : 'Usar seção de fotos do documento'}</div>;
      case 'assinatura':
        return <div className="text-xs text-slate-500" data-testid={`field-${campo.identificador_tecnico}`}>{value ? 'Assinatura capturada' : 'Usar seção de assinaturas'}</div>;
      case 'qr_code':
        return <input type="text" value={value || ''} onChange={e => onChange(e.target.value)} placeholder={placeholder || 'Código QR'} className={cls} disabled={readOnly} data-testid={`field-${campo.identificador_tecnico}`} />;
      default:
        return <input type="text" value={value || ''} onChange={e => onChange(e.target.value)} className={cls} disabled={readOnly} data-testid={`field-${campo.identificador_tecnico}`} />;
    }
  };

  return (
    <div className={wrapCls}>
      <label className="flex items-center gap-1 text-xs font-medium text-slate-400 mb-1">
        {nome}
        {obrigatorio && <span className="text-red-400">*</span>}
        {unidade_medida && tipo !== 'numero' && tipo !== 'decimal' && <span className="text-slate-600">({unidade_medida})</span>}
      </label>
      {renderInput()}
      {texto_ajuda && <p className="text-xs text-slate-600 mt-0.5">{texto_ajuda}</p>}
    </div>
  );
};

/**
 * Signature capture pad — canvas-based touch/draw component.
 * Captures signature as base64 PNG image.
 */
export const SignaturePad = ({ onCapture, width = 300, height = 100, label = "Assinatura" }) => {
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasContent, setHasContent] = useState(false);

  const getPos = useCallback((e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const touch = e.touches ? e.touches[0] : e;
    return {
      x: (touch.clientX - rect.left) * (canvas.width / rect.width),
      y: (touch.clientY - rect.top) * (canvas.height / rect.height),
    };
  }, []);

  const startDraw = useCallback((e) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const pos = getPos(e);
    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
    setIsDrawing(true);
    setHasContent(true);
  }, [getPos]);

  const draw = useCallback((e) => {
    if (!isDrawing) return;
    e.preventDefault();
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const pos = getPos(e);
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
  }, [isDrawing, getPos]);

  const endDraw = useCallback(() => {
    setIsDrawing(false);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }, []);

  const clear = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasContent(false);
  };

  const capture = () => {
    if (!hasContent) return;
    const canvas = canvasRef.current;
    const dataUrl = canvas.toDataURL('image/png');
    onCapture?.(dataUrl);
  };

  return (
    <div className="space-y-2" data-testid="signature-pad">
      <label className="text-xs font-medium text-slate-400">{label}</label>
      <div className="border border-slate-700 rounded-lg bg-white overflow-hidden" style={{ width, maxWidth: '100%' }}>
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          onMouseDown={startDraw}
          onMouseMove={draw}
          onMouseUp={endDraw}
          onMouseLeave={endDraw}
          onTouchStart={startDraw}
          onTouchMove={draw}
          onTouchEnd={endDraw}
          className="cursor-crosshair touch-none w-full"
          style={{ height }}
          data-testid="signature-canvas"
        />
      </div>
      <div className="flex gap-2">
        <button onClick={clear} className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-800" data-testid="signature-clear">Limpar</button>
        <button onClick={capture} disabled={!hasContent} className="text-xs text-brand hover:text-brand-light px-2 py-1 rounded bg-brand/10 disabled:opacity-30" data-testid="signature-capture">Confirmar Assinatura</button>
      </div>
    </div>
  );
};

export default DynamicFieldRenderer;
