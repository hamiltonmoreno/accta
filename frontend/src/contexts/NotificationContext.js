import React, { createContext, useContext, useEffect, useMemo, useRef } from 'react';
import { toast } from 'sonner';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsAPI } from '../utils/api';
import { useAuth } from './AuthContext';
import { queryKeys } from '../lib/queryClient';

const NotificationContext = createContext(null);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
};

// Helpers para mexer no cache da count sem refetch.
const COUNT_KEY = queryKeys.notifications.unread();
const LIST_KEY = queryKeys.notifications.list();

export const NotificationProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const qc = useQueryClient();
  const eventSourceRef = useRef(null);

  // List query — gated por auth. staleTime longo porque SSE empurra updates.
  const listQuery = useQuery({
    queryKey: LIST_KEY,
    queryFn: async () => {
      const res = await notificationsAPI.getAll();
      return {
        items: res.data.items || res.data,
        total: res.data.total ?? (res.data.items || res.data).length,
      };
    },
    enabled: isAuthenticated,
    staleTime: 60 * 1000,
  });

  // Unread count — gated. SSE atualiza isto via setQueryData; polling
  // de 30s e fallback gerido pelo SSE handler abaixo (nao refetchInterval
  // permanente porque queremos SSE quando disponivel).
  const unreadQuery = useQuery({
    queryKey: COUNT_KEY,
    queryFn: async () => (await notificationsAPI.getUnreadCount()).data.count,
    enabled: isAuthenticated,
    staleTime: 60 * 1000,
  });

  const notifications = listQuery.data?.items || [];
  const total = listQuery.data?.total || 0;
  const unreadCount = unreadQuery.data || 0;
  const loading = listQuery.isLoading;

  // Mutations — usam setQueryData para optimistic updates sem refetch.
  const markAsReadMutation = useMutation({
    mutationFn: (id) => notificationsAPI.markRead(id),
    onMutate: async (id) => {
      qc.setQueryData(LIST_KEY, (old) => old && {
        ...old,
        items: old.items.map((n) => (n.id === id ? { ...n, read: true } : n)),
      });
      qc.setQueryData(COUNT_KEY, (old) => Math.max(0, (old || 0) - 1));
    },
    onError: () => {
      toast.error('Não foi possível marcar como lida');
      qc.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const markAllAsReadMutation = useMutation({
    mutationFn: () => notificationsAPI.markAllRead(),
    onMutate: async () => {
      qc.setQueryData(LIST_KEY, (old) => old && {
        ...old,
        items: old.items.map((n) => ({ ...n, read: true })),
      });
      qc.setQueryData(COUNT_KEY, () => 0);
    },
    onError: () => {
      toast.error('Não foi possível marcar todas como lidas');
      qc.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => notificationsAPI.delete(id),
    onMutate: async (id) => {
      qc.setQueryData(LIST_KEY, (old) => {
        if (!old) return old;
        return {
          items: old.items.filter((n) => n.id !== id),
          total: Math.max(0, old.total - 1),
        };
      });
    },
    onError: () => {
      toast.error('Não foi possível remover a notificação');
      qc.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const clearReadMutation = useMutation({
    mutationFn: () => notificationsAPI.clearRead(),
    onMutate: async () => {
      qc.setQueryData(LIST_KEY, (old) => {
        if (!old) return old;
        const remaining = old.items.filter((n) => !n.read);
        return { items: remaining, total: remaining.length };
      });
    },
    onError: () => {
      toast.error('Não foi possível limpar as notificações lidas');
      qc.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  // SSE connection para count em tempo-real. Pausa enquanto tab escondida.
  // Quando SSE falha, fallback para polling de 30s.
  // Em vez de setUnreadCount, usamos qc.setQueryData(COUNT_KEY, ...) para
  // atualizar o cache directamente — todos os subscribers re-renderizam.
  useEffect(() => {
    if (!isAuthenticated) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    let fallbackInterval = null;

    const startStream = () => {
      if (eventSourceRef.current || fallbackInterval) return;
      const token = localStorage.getItem('accta_token');
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
      const sseUrl = `${BACKEND_URL}/api/notifications/stream?token=${token}`;
      try {
        const es = new EventSource(sseUrl);
        eventSourceRef.current = es;
        es.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            qc.setQueryData(COUNT_KEY, data.count);
          } catch { /* ignore parse errors */ }
        };
        es.onerror = () => {
          es.close();
          eventSourceRef.current = null;
          // Fallback polling — invalida a query, TanStack faz o fetch.
          fallbackInterval = setInterval(
            () => qc.invalidateQueries({ queryKey: COUNT_KEY }),
            30000,
          );
        };
      } catch {
        fallbackInterval = setInterval(
          () => qc.invalidateQueries({ queryKey: COUNT_KEY }),
          30000,
        );
      }
    };

    const stopStream = () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (fallbackInterval) {
        clearInterval(fallbackInterval);
        fallbackInterval = null;
      }
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopStream();
      } else {
        // Ao voltar, refresh imediato + reabre stream.
        qc.invalidateQueries({ queryKey: COUNT_KEY });
        startStream();
      }
    };

    if (!document.hidden) startStream();
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      stopStream();
    };
  }, [isAuthenticated, qc]);

  const markAsRead = (id) => markAsReadMutation.mutate(id);
  const markAllAsRead = () => markAllAsReadMutation.mutate();
  const deleteNotification = (id) => deleteMutation.mutate(id);
  const clearReadNotifications = () => clearReadMutation.mutate();
  const refresh = () => qc.invalidateQueries({ queryKey: ['notifications'] });
  const loadNotifications = refresh; // back-compat alias

  const value = useMemo(
    () => ({
      notifications,
      total,
      unreadCount,
      loading,
      markAsRead,
      markAllAsRead,
      deleteNotification,
      clearReadNotifications,
      refresh,
      loadNotifications,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [notifications, total, unreadCount, loading],
  );

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};
