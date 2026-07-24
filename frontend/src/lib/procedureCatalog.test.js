import {
  emptyProcedureTotals,
  normalizeProcedureResponse,
  searchTextFromChange,
} from './procedureCatalog';

describe('procedure catalog UI normalization', () => {
  it('extracts a string from the input event instead of storing the event object', () => {
    const event = { target: { value: 'alimentadores' } };
    expect(searchTextFromChange(event)).toBe('alimentadores');
    expect(searchTextFromChange({ filters: {} })).toBe('');
    expect(searchTextFromChange('elétrica')).toBe('elétrica');
  });

  it('uses API metadata and always returns an array', () => {
    const result = normalizeProcedureResponse({
      items: [{ id: 'doc-1' }, { id: 'doc-2' }],
      totals: { total: 3, published: 2, filtered: 2, legacy: 1 },
    });

    expect(result.items).toHaveLength(2);
    expect(result.totals).toMatchObject({
      total: 3,
      published: 2,
      filtered: 2,
      legacy: 1,
    });
  });

  it('keeps backwards compatibility with the legacy array response', () => {
    const result = normalizeProcedureResponse([{ id: 'legacy-1' }]);
    expect(result.items).toHaveLength(1);
    expect(result.totals).toEqual({
      ...emptyProcedureTotals,
      total: 1,
      published: 1,
      filtered: 1,
    });
  });
});
