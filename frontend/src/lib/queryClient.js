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
    logs: (params) => (params ? ['audit', 'logs', params] : ['audit', 'logs']),
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
  mfa: {
    // Key scoped por userId — sem isto o status (fresco 30s) vazaria entre
    // contas no mesmo browser após logout/login (logout só limpa o user, não
    // o cache). Mesmo padrão do NotificationContext.
    status: (userId) => ['mfa', 'status', userId || null],
  },
  registration: {
    requests: (status) => ['registration', 'requests', status || 'pendente_aprovacao'],
    joiaPreview: (userId, since) => ['registration', 'joia-preview', userId || null, since || null],
  },
  cargos: {
    meta: () => ['cargos', 'meta'],
    list: () => ['cargos', 'list'],
    candidates: (params) => ['cargos', 'candidates', params || {}],
    history: (userId) => ['cargos', 'history', userId],
  },
  governance: {
    structure: () => ['governance', 'structure'],
  },
  banners: {
    public: () => ['banners', 'public'],
    all: () => ['banners', 'all'],
  },
  comunicados: {
    list: (params) => ['comunicados', params || {}],
    segments: () => ['comunicados', 'segments'],
    recipientsCount: (key) => ['comunicados', 'recipients-count', key],
  },
  brand: {
    public: () => ['brand', 'public'],
    all: () => ['brand', 'all'],
  },
  assembleias: {
    list: (filters) => ['assembleias', filters || {}],
    byId: (id) => ['assembleias', id],
    quorum: (id) => ['assembleias', id, 'quorum'],
    deliberacoes: (id) => ['assembleias', id, 'deliberacoes'],
  },
  eleicoes: {
    list: (filters) => ['eleicoes', filters || {}],
    byId: (id) => ['eleicoes', id],
    listas: (id) => ['eleicoes', id, 'listas'],
  },
  sancoes: {
    list: (filters) => ['sancoes', filters || {}],
    byId: (id) => ['sancoes', id],
    ofUser: (userId) => ['sancoes', 'user', userId],
  },
  transactions: {
    list: (filters) => ['transactions', filters || {}],
    summary: (year, month) => ['transactions', 'summary', year, month],
  },
  atos: {
    list: (filters) => ['atos', filters || {}],
    byId: (id) => ['atos', id],
  },
  exercicios: {
    list: () => ['exercicios'],
    byAno: (ano) => ['exercicios', ano],
    execucao: (ano) => ['exercicios', ano, 'execucao'],
  },
  balancetes: {
    list: (filters) => ['balancetes', filters || {}],
    byId: (id) => ['balancetes', id],
  },
  regulamentos: {
    list: () => ['regulamentos'],
    byId: (id) => ['regulamentos', id],
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
  posts: {
    all: () => ['posts'], // prefixo p/ invalidação abrangente (prefix match)
    list: (params) => ['posts', params ?? {}], // { visibility, type, status, q, limit }
    detail: (idOrSlug) => ['posts', 'detail', idOrSlug],
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
