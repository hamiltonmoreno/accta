import { useQuery } from '@tanstack/react-query';
import { pollsAPI, eventsAPI, atosAPI } from '../utils/api';
import { useAuth } from '../contexts/AuthContext';
import { queryKeys } from '../lib/queryClient';

// Fonte ÚNICA da derivação de «As minhas pendências» (spec 014 + 015): a página
// `/pendencias` e o contador da barra lateral consomem este mesmo hook ⇒ o badge
// coincide exatamente com o painel (SC-002, sem deriva). Role-aware: as queries de
// Atos só correm para Direção/admin (`enabled: isDir`) — um sócio comum levaria 403
// em GET /atos (FR-009). Eleições/deliberações secretas ficam fora (nunca lidas).
// Frescura no carregamento/navegação via a cache do TanStack Query (staleTime 30s);
// sem stream/polling dedicado.
export const usePendencias = () => {
  const { user, isAdmin, isDirecao } = useAuth();
  const isDir = Boolean(isAdmin || isDirecao);

  const { data: polls = [], isLoading: pollsLoading, isError: pollsError } = useQuery({
    queryKey: queryKeys.polls.list(),
    queryFn: async () => (await pollsAPI.getAll()).data,
  });
  const { data: events = [], isLoading: eventsLoading, isError: eventsError } = useQuery({
    queryKey: queryKeys.events.upcoming(),
    queryFn: async () => (await eventsAPI.getUpcoming()).data,
  });
  // Atos só para Direção/admin — evita o 403 de _require_view ao sócio comum.
  const { data: assinatura, isLoading: assLoading, isError: assError } = useQuery({
    queryKey: queryKeys.atos.list({ mine: true }),
    queryFn: async () => (await atosAPI.list({ pendentes_para_mim: true })).data,
    enabled: isDir,
  });
  const { data: propostos, isLoading: propLoading, isError: propError } = useQuery({
    queryKey: queryKeys.atos.list({ status: 'pendente' }),
    queryFn: async () => (await atosAPI.list({ status: 'pendente' })).data,
    enabled: isDir,
  });

  const votacoes = (polls || []).filter((p) => p.status === 'aberta' && !p.has_voted);
  const eventos = (events || []).filter((e) => !(e.attendees || []).includes(user?.id));
  const assinaturaItems = isDir ? assinatura?.items || [] : [];
  const propostosItems = isDir
    ? (propostos?.items || []).filter((a) => a.created_by === user?.id)
    : [];

  const isLoading = pollsLoading || eventsLoading || (isDir && (assLoading || propLoading));
  // Um read falhado não deve passar por "nada pendente" (evita um falso "tudo em dia").
  const anyError = pollsError || eventsError || (isDir && (assError || propError));
  const total =
    votacoes.length + eventos.length + (isDir ? assinaturaItems.length + propostosItems.length : 0);

  return { votacoes, eventos, assinaturaItems, propostosItems, total, isLoading, anyError, isDir };
};
