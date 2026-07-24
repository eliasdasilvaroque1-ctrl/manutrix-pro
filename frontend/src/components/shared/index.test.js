import React from 'react';
import { renderToString } from 'react-dom/server';
import { AlertTriangle } from 'lucide-react';

import { EmptyState } from './index';

describe('EmptyState', () => {
  it('renders safely when no icon is provided', () => {
    expect(() => renderToString(<EmptyState title="Nenhum registro" />)).not.toThrow();
    expect(renderToString(<EmptyState title="Nenhum registro" />)).toContain('Nenhum registro');
  });

  it('continues to accept a custom icon', () => {
    expect(() => renderToString(
      <EmptyState icon={AlertTriangle} title="Atenção" />
    )).not.toThrow();
  });
});
