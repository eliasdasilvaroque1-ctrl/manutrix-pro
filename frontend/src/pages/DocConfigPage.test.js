import React from 'react';
import { renderToString } from 'react-dom/server';
import { AlertTriangle } from 'lucide-react';

jest.mock('../lib/api', () => ({
  api: { get: jest.fn(), put: jest.fn(), post: jest.fn(), delete: jest.fn() },
  useAuth: () => ({ user: { role: 'admin' } }),
  safeErrorMsg: (err, fallback = 'Erro ao processar operação') => {
    const detail = err?.response?.data?.detail;
    if (!detail) return fallback;
    if (typeof detail === 'string') return detail;
    if (typeof detail === 'object' && typeof detail.msg === 'string') return detail.msg;
    return fallback;
  },
}));

import { EmptyState } from '../components/shared';
import { normalizeDocConfigArray, normalizeDocConfigObject } from './DocConfigPage';
import { safeErrorMsg } from '../lib/api';

describe('RC-P0.1 DocConfig recovery guards', () => {
  test('renders EmptyState without explicit icon and does not create React error #130', () => {
    expect(() => renderToString(<EmptyState title="Nenhum formulário" />)).not.toThrow();
    expect(renderToString(<EmptyState icon={AlertTriangle} title="Completo" />)).toContain('Completo');
  });

  test('normalizes null and object endpoint payloads when arrays are expected', () => {
    expect(normalizeDocConfigArray(null, 'Checklists')).toEqual([]);
    expect(normalizeDocConfigArray({ detail: 'erro' }, 'Layouts')).toEqual([]);
    expect(normalizeDocConfigArray([{ id: 'ok' }, null, 'bad'], 'Campos')).toEqual([{ id: 'ok' }]);
  });

  test('normalizes invalid config payloads without inventing collection data', () => {
    const config = normalizeDocConfigObject(null, 'Configuração geral');
    expect(config).toHaveProperty('identidade_doc');
    expect(config).toHaveProperty('foto_config.classificacoes');
  });

  test('safeErrorMsg always returns a string for object details', () => {
    const msg = safeErrorMsg({ response: { data: { detail: { msg: 'Sem permissão' } } } });
    expect(msg).toBe('Sem permissão');
    expect(typeof msg).toBe('string');
  });
});
