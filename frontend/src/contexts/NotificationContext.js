import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
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

  const loadNotifications = useCallback(async (params = {}) => {
    setLoading(true);
    try {
      const response = await notificationsAPI.getAll(params);
      setNotifications(response.data.items || response.data);
      setTotal(response.data.total || (response.data.items || response.data).length);
    } catch (error) {
      console.error('Erro ao carregar notificacoes:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadUnreadCount = useCallback(async () => {
    try {
      const response = await notificationsAPI.getUnreadCount();
      setUnreadCount(response.data.count);
    } catch (error) {
      console.error('Erro ao carregar contagem:', error);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadNotifications();
      loadUnreadCount();

      const interval = setInterval(() => {
        loadUnreadCount();
      }, 30000);

      return () => clearInterval(interval);
    }
  }, [isAuthenticated, loadNotifications, loadUnreadCount]);

  const markAsRead = async (notificationId) => {
    try {
      await notificationsAPI.markRead(notificationId);
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Erro ao marcar como lida:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationsAPI.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Erro ao marcar todas como lidas:', error);
    }
  };

  const deleteNotification = async (notificationId) => {
    try {
      await notificationsAPI.delete(notificationId);
      setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
      setTotal((prev) => prev - 1);
    } catch (error) {
      console.error('Erro ao remover notificacao:', error);
    }
  };

  const clearReadNotifications = async () => {
    try {
      await notificationsAPI.clearRead();
      setNotifications((prev) => prev.filter((n) => !n.read));
      setTotal((prev) => prev - notifications.filter((n) => n.read).length);
    } catch (error) {
      console.error('Erro ao limpar notificacoes:', error);
    }
  };

  const refresh = () => {
    loadNotifications();
    loadUnreadCount();
  };

  return (
    <NotificationContext.Provider
      value={{
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
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};
