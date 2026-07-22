/**
 * MAINTRIX — Shared constants and utility functions
 * Extracted from App.js during modularization.
 */

// ============== CONSTANTS ==============

export const FIELD_LABEL_MAP = {
  nome: 'Nome', ativo_id: 'Ativo', tipo: 'Tipo', disciplina: 'Disciplina',
  titulo: 'Título', descricao: 'Descrição', prioridade: 'Prioridade', email: 'Email',
  password: 'Senha', frequencia: 'Frequência', responsavel_id: 'Responsável',
  tipo_equipamento: 'Tipo Equipamento', categoria: 'Categoria', sector_id: 'Área',
  perguntas: 'Perguntas', checklist: 'Checklist',
};

export const ROLE_LABELS = {
  master: 'Master', admin: 'Administrador', gerente: 'Gerente', pcm: 'PCM',
  supervisor: 'Supervisor', tec_mecanico: 'Técnico Mecânico', tec_eletrico: 'Técnico Elétrico',
  instrumentista: 'Instrumentista', lubrificador: 'Lubrificador', tecnico: 'Técnico (legado)',
  operador: 'Operador', inspetor: 'Inspetor', visualizador: 'Visualizador', viewer: 'Visualizador',
};

export const ROLES_EXCEPT_VIEWER = [
  'master','admin','gerente','pcm','supervisor','tec_mecanico','tec_eletrico',
  'instrumentista','lubrificador','tecnico','inspetor','operador',
];

export const PRIO_COLORS = { emergencia: 'bg-red-500', alta: 'bg-orange-500', media: 'bg-amber-500', baixa: 'bg-blue-500' };
export const PRIO_LABELS = { emergencia: 'Emergência', alta: 'Alta', media: 'Média', baixa: 'Baixa' };

export const CENTRAL_TITLES = {
  master: 'Central Executiva', admin: 'Central Administrativa', pcm: 'Central PCM',
  supervisor: 'Central Supervisor', tecnico: 'Central do Técnico', operador: 'Central Operacional',
  inspetor: 'Central do Inspetor', gerente: 'Painel Gerencial',
};

// ============== ERROR NORMALIZER ==============

export const normalizeError = (error) => {
  const detail = error?.response?.data?.detail;
  if (!detail) {
    if (error?.message?.includes('Network Error')) return 'Sem conexão com o servidor. Verifique sua rede.';
    if (error?.message?.includes('timeout')) return 'O servidor demorou para responder. Tente novamente.';
    return 'Não foi possível concluir a operação. Tente novamente.';
  }
  return formatApiDetail(detail);
};

/** Formata detail de API (string, array Pydantic, objeto) → string segura para toast/JSX */
export const formatApiDetail = (detail) => {
  if (!detail) return 'Não foi possível concluir a operação.';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map(d => {
      if (typeof d === 'object' && d !== null) {
        const loc = (d.loc || []).filter(l => !['body', 'query', 'path', 'header'].includes(l));
        const fieldName = loc[loc.length - 1];
        const label = FIELD_LABEL_MAP[fieldName] || fieldName;
        const msg = typeof d.msg === 'string' ? d.msg : String(d.msg || '');
        if (fieldName && msg.toLowerCase().includes('required')) {
          return `Campo '${label}' é obrigatório`;
        }
        if (fieldName) return `${label}: ${msg}`;
        return msg || 'Erro de validação';
      }
      return String(d);
    }).join('; ') || 'Erro de validação';
  }
  if (typeof detail === 'object' && detail !== null) {
    return typeof detail.msg === 'string' ? detail.msg : (typeof detail.message === 'string' ? detail.message : JSON.stringify(detail));
  }
  return String(detail);
};

// ============== IMAGE COMPRESSION ==============

export const compressImage = (file, maxWidth = 1200, quality = 0.8) => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let w = img.width, h = img.height;
        if (w > maxWidth) { h = (maxWidth / w) * h; w = maxWidth; }
        canvas.width = w; canvas.height = h;
        canvas.getContext('2d').drawImage(img, 0, 0, w, h);
        canvas.toBlob((blob) => resolve(new File([blob], file.name, { type: 'image/jpeg' })), 'image/jpeg', quality);
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
};
