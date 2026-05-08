import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { toast } from 'sonner';
import { notificationsAPI } from '../utils/api';
import { useAuth } from './AuthContext';

const NotificationContext = createContext(null);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const eventSourceRef = useRef(null);

  const loadNotifications = useCallback(async (params = {}) => {
    setLoading(true);
    try {
      const response = await notificationsAPI.getAll(params);
      setNotifications(response.data.items || response.data);
      setTotal(response.data.total || (response.data.items || response.data).length);
    } catch (error) {
      // silent — user may have logged out
    } finally {
      setLoading(false);
    }
  }, []);

  const loadUnreadCount = useCallback(async () => {
    try {
      const response = await notificationsAPI.getUnreadCount();
      setUnreadCount(response.data.count);
    } catch (error) {
      // silent
    }
  }, []);

  // SSE connection for real-time notification count.
  // Pausa SSE/polling enquanto a aba está escondida (poupa bateria + tráfego).
  useEffect(() => {
    if (!isAuthenticated) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    loadNotifications();
    loadUnreadCount();

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
            setUnreadCount(data.count);
          } catch { /* ignore parse errors */ }
        };
        es.onerror = () => {
          es.close();
          eventSourceRef.current = null;
          fallbackInterval = setInterval(loadUnreadCount, 30000);
        };
      } catch {
        fallbackInterval = setInterval(loadUnreadCount, 30000);
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
        loadUnreadCount();
        startStream();
      }
    };

    if (!document.hidden) startStream();
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      stopStream();
    };
  }, [isAuthenticated, loadNotifications, loadUnreadCount]);

  const markAsRead = useCallback(async (notificationId) => {
    try {
      await notificationsAPI.markRead(notificationId);
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (error) {
      toast.error('Não foi possível marcar como lida');
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await notificationsAPI.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      toast.error('Não foi possível marcar todas como lidas');
    }
  }, []);

  const deleteNotification = useCallback(async (notificationId) => {
    try {
      await notificationsAPI.delete(notificationId);
      setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
      setTotal((prev) => prev - 1);
    } catch (error) {
      toast.error('Não foi possível remover a notificação');
    }
  }, []);

  const clearReadNotifications = useCallback(async () => {
    try {
      await notificationsAPI.clearRead();
      setNotifications((prev) => prev.filter((n) => !n.read));
      setTotal((prev) => prev - notifications.filter((n) => n.read).length);
    } catch (error) {
      toast.error('Não foi possível limpar as notificações lidas');
    }
  }, [notifications]);

  const refresh = useCallback(() => {
    loadNotifications();
    loadUnreadCount();
  }, [loadNotifications, loadUnreadCount]);

  const value = useMemo(() => ({
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
  }), [notifications, total, unreadCount, loading, markAsRead, markAllAsRead, deleteNotification, clearReadNotifications, refresh, loadNotifications]);

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};
