/**
 * Smoke tests para queryClient + queryKeys.
 */

import { queryClient, queryKeys } from '../queryClient';

describe('queryClient defaults', () => {
  test('staleTime default is 30s', () => {
    expect(queryClient.getDefaultOptions().queries.staleTime).toBe(30 * 1000);
  });

  test('gcTime default is 5min', () => {
    expect(queryClient.getDefaultOptions().queries.gcTime).toBe(5 * 60 * 1000);
  });

  test('refetchOnWindowFocus defaults to true', () => {
    expect(queryClient.getDefaultOptions().queries.refetchOnWindowFocus).toBe(true);
  });

  test('retry returns false for 4xx errors', () => {
    const retry = queryClient.getDefaultOptions().queries.retry;
    expect(retry(0, { response: { status: 401 } })).toBe(false);
    expect(retry(0, { response: { status: 403 } })).toBe(false);
    expect(retry(0, { response: { status: 404 } })).toBe(false);
    expect(retry(0, { response: { status: 422 } })).toBe(false);
  });

  test('retry allows 1 attempt for 5xx and network errors', () => {
    const retry = queryClient.getDefaultOptions().queries.retry;
    expect(retry(0, { response: { status: 500 } })).toBe(true);
    expect(retry(1, { response: { status: 500 } })).toBe(false);
    expect(retry(0, new Error('Network error'))).toBe(true);
  });

  test('retryDelay does exponential backoff capped at 30s', () => {
    const retryDelay = queryClient.getDefaultOptions().queries.retryDelay;
    expect(retryDelay(0)).toBe(1000);
    expect(retryDelay(1)).toBe(2000);
    expect(retryDelay(2)).toBe(4000);
    expect(retryDelay(10)).toBe(30000); // capped
  });
});

describe('queryKeys conventions', () => {
  test('audit.logs returns ["audit", "logs"]', () => {
    expect(queryKeys.audit.logs()).toEqual(['audit', 'logs']);
  });

  test('benefits.list and byId have stable shape', () => {
    expect(queryKeys.benefits.list()).toEqual(['benefits']);
    expect(queryKeys.benefits.byId('xyz')).toEqual(['benefits', 'xyz']);
  });

  test('users.list normalizes undefined filters to {}', () => {
    expect(queryKeys.users.list()).toEqual(['users', {}]);
    expect(queryKeys.users.list({ role: 'admin' })).toEqual(['users', { role: 'admin' }]);
  });

  test('transactions.summary includes year/month for cache key uniqueness', () => {
    expect(queryKeys.transactions.summary(2026, 5)).toEqual([
      'transactions',
      'summary',
      2026,
      5,
    ]);
  });
});
