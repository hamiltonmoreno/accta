/**
 * TanStack Query — QueryClient com defaults para o ACCTA Portal.
 *
 * Defaults escolhidos:
 * - staleTime: 30s — reuso entre paginas evita re-fetch desnecessario quando
 *   o utilizador navega rapido. Notificacoes/dados volateis usam staleTime
 *   especifico no hook quando precisam.
 * - gcTime: 5min — cache em memoria depois do unmount; volta a abrir a
 *   pagina nao re-fetch se < 5min.
 * - refetchOnWindowFocus: true — UX standard. Quando o utilizador volta
 *   ao tab, dados frescos. Honra `staleTime` (so refetch se stale).
 * - retry: 1 — uma tentativa de retry em transient errors. Nao retry em 4xx.
 * - retryDelay: exponential backoff (1s, 2s, max 30s).
 *
 * Errors 4xx (auth, 403, 404) nao fazem retry porque nao vao melhorar.
 * O 401 ja e tratado pelo interceptor de utils/api.js (force-logout event).
 */

import { QueryClient } from '@tanstack/react-query';

const isClientError = (error) => {
  const status = error?.response?.status;
  return status >= 400 && status < 500;
};

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000, // 30s
      gcTime: 5 * 60 * 1000, // 5min
      refetchOnWindowFocus: true,
      retry: (failureCount, error) => {
        if (isClientError(error)) return false;
        return failureCount < 1;
      },
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30000),
    },
    mutations: {
      retry: 0,
    },
  },
});

/**
 * Convencao de query keys: array com domain + filtros.
 * Centralizado para typo-safety e cache invalidation correcta.
 *
 * Exemplos:
 *   queryKeys.benefits.list() -> ['benefits']
 *   queryKeys.audit.logs() -> ['audit', 'logs']
 *   queryKeys.users.byId('u1') -> ['users', 'u1']
 */
export const queryKeys = {
  audit: {
    logs: () => ['audit', 'logs'],
  },
  benefits: {
    list: () => ['benefits'],
    byId: (id) => ['benefits', id],
  },
  events: {
    list: () => ['events'],
    upcoming: () => ['events', 'upcoming'],
    byId: (id) => ['events', id],
  },
  users: {
    list: (filters) => ['users', filters || {}],
    byId: (id) => ['users', id],
  },
  registration: {
    requests: (status) => ['registration', 'requests', status || 'pendente_aprovacao'],
  },
  transactions: {
    list: (filters) => ['transactions', filters || {}],
    summary: (year, month) => ['transactions', 'summary', year, month],
  },
  invoices: {
    list: () => ['invoices'],
  },
  wall: {
    list: (category) => ['wall', category || 'all'],
    pending: () => ['wall', 'pending'],
    comments: (postId) => ['wall', postId, 'comments'],
  },
  notifications: {
    list: () => ['notifications'],
    unread: () => ['notifications', 'unread'],
  },
  polls: {
    list: () => ['polls'],
    byId: (id) => ['polls', id],
  },
  documents: {
    list: () => ['documents'],
  },
  gallery: {
    albums: () => ['gallery', 'albums'],
    photos: (albumId) => ['gallery', 'photos', albumId],
    pending: () => ['gallery', 'pending'],
  },
  projects: {
    list: () => ['projects'],
    byId: (id) => ['projects', id],
  },
  activity: {
    recent: () => ['activity', 'recent'],
  },
  report: {
    personal: () => ['report', 'personal'],
  },
};
