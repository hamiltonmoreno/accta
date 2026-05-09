/**
 * Test helper para componentes que usam useQuery / useMutation.
 *
 * Cria um QueryClient isolado por teste com retry desligado e gcTime=0
 * para evitar leaks entre testes. Usar em vez do queryClient de prod.
 *
 * Exemplo:
 *   import { renderWithQuery } from '../../lib/testQueryClient';
 *   renderWithQuery(<MyPage />);
 */

import React from 'react';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

export const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: { retry: false },
    },
    // Suprime console.error do TanStack durante testes (stale promise rejection
    // dos retries que silenciamos).
    logger: { log: () => {}, warn: () => {}, error: () => {} },
  });

export const renderWithQuery = (ui, { queryClient, ...options } = {}) => {
  const client = queryClient || createTestQueryClient();
  return {
    ...render(
      <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
      options,
    ),
    queryClient: client,
  };
};
