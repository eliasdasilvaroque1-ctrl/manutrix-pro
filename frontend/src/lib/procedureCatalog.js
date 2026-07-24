export const emptyProcedureTotals = {
  total: 0,
  published: 0,
  draft: 0,
  archived: 0,
  filtered: 0,
  corporate: 0,
  legacy: 0,
  by_status: {},
};

export const normalizeProcedureResponse = (data) => {
  if (Array.isArray(data)) {
    return {
      items: data,
      totals: {
        ...emptyProcedureTotals,
        total: data.length,
        published: data.length,
        filtered: data.length,
      },
    };
  }

  const items = Array.isArray(data?.items) ? data.items : [];
  return {
    items,
    totals: {
      ...emptyProcedureTotals,
      ...(data?.totals && typeof data.totals === 'object' ? data.totals : {}),
      filtered: data?.totals?.filtered ?? items.length,
    },
  };
};

export const searchTextFromChange = (eventOrValue) => {
  if (typeof eventOrValue === 'string') return eventOrValue;
  const value = eventOrValue?.target?.value;
  return typeof value === 'string' ? value : '';
};
