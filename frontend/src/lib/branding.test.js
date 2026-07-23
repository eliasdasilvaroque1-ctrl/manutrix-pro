jest.mock('axios', () => ({ create: () => ({ interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } }, get: jest.fn(), post: jest.fn(), defaults: { headers: { common: {} } } }), get: jest.fn(), post: jest.fn() }));

import { normalizeOrganizations } from './branding';

describe('normalizeOrganizations', () => {
  const organizations = [{ id: 'org-1', nome: 'ASTEC' }];

  it('keeps an array payload unchanged', () => {
    expect(normalizeOrganizations(organizations)).toBe(organizations);
  });

  it('returns [] for an object payload that is not a supported envelope', () => {
    expect(normalizeOrganizations({ detail: 'erro' })).toEqual([]);
  });

  it('returns [] for null payload', () => {
    expect(normalizeOrganizations(null)).toEqual([]);
  });

  it('returns [] for undefined payload', () => {
    expect(normalizeOrganizations(undefined)).toEqual([]);
  });

  it('uses response.data when it is an array', () => {
    expect(normalizeOrganizations({ data: organizations })).toBe(organizations);
  });

  it('uses response.organizations when it is an array', () => {
    expect(normalizeOrganizations({ organizations })).toBe(organizations);
  });
});
