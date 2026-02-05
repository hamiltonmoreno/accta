import React from 'react';
import { motion } from 'framer-motion';
import { useNotifications } from '../../contexts/NotificationContext';
import { useNavigate } from 'react-router-dom';
import { Bell, CheckCheck, ArrowRight } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const NotificacoesPage = () => {
  const { notifications, unreadCount, markAsRead, markAllAsRead, loading } = useNotifications();
  const navigate = useNavigate();

  const getNotificationIcon = (type) => {
    const icons = {
      poll_opened: '📊',
      invoice_due: '💰',
      document_new: '📄',
      wall_post_approved: '✅',
    };
    return icons[type] || '🔔';
  };

  const getNotificationColor = (type) => {
    const colors = {
      poll_opened: 'bg-accent/10 border-accent/20',
      invoice_due: 'bg-alert/10 border-alert/20',
      document_new: 'bg-blue-50 border-blue-200',
      wall_post_approved: 'bg-green-50 border-green-200',
    };
    return colors[type] || 'bg-slate-50 border-slate-200';
  };

  const handleNotificationClick = (notification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
    if (notification.link) {
      navigate(notification.link);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-outfit font-bold text-4xl text-primary mb-2" data-testid="notifications-title">
            Central de Notificações
          </h1>
          <p className="text-slate-600">Acompanhe todas as atualizações importantes</p>
        </div>
        {unreadCount > 0 && (
          <button
            onClick={markAllAsRead}
            className="flex items-center gap-2 bg-accent text-primary hover:bg-accent/90 h-10 px-4 rounded-lg font-bold text-sm transition-all"
            data-testid="mark-all-read-button"
          >
            <CheckCheck className="w-4 h-4" />
            Marcar todas como lidas
          </button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-technical rounded-xl p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="font-mono text-3xl font-bold text-primary mb-1">{notifications.length}</div>
              <div className="text-sm text-slate-500 uppercase tracking-wider">Total de Notificações</div>
            </div>
            <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center">
              <Bell className="w-6 h-6 text-accent" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card-technical rounded-xl p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="font-mono text-3xl font-bold text-accent mb-1">{unreadCount}</div>
              <div className="text-sm text-slate-500 uppercase tracking-wider">Não Lidas</div>
            </div>
            <div className="w-12 h-12 bg-accent rounded-lg flex items-center justify-center">
              <CheckCheck className="w-6 h-6 text-primary" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Notifications List */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : notifications.length === 0 ? (
          <div className="card-technical rounded-xl p-12 text-center" data-testid="no-notifications-page">
            <Bell className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500 font-medium mb-1">Nenhuma notificação</p>
            <p className="text-sm text-slate-400">Você será notificado sobre eventos importantes</p>
          </div>
        ) : (
          notifications.map((notification, index) => (
            <motion.button
              key={notification.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => handleNotificationClick(notification)}
              className={`w-full card-technical rounded-xl p-6 hover:shadow-lg transition-all text-left border-2 ${
                !notification.read ? getNotificationColor(notification.type) : 'border-transparent'
              }`}
              data-testid={`notification-item-${notification.id}`}
            >
              <div className="flex items-start gap-4">
                <span className="text-3xl flex-shrink-0">{getNotificationIcon(notification.type)}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <h3 className="font-outfit font-semibold text-xl text-primary">{notification.title}</h3>
                    {!notification.read && (
                      <span className="px-3 py-1 bg-accent text-primary rounded-full text-xs font-mono font-semibold uppercase tracking-wider flex-shrink-0">
                        Nova
                      </span>
                    )}
                  </div>
                  <p className="text-slate-600 mb-3">{notification.message}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400 font-mono">
                      {format(new Date(notification.created_at), "dd 'de' MMMM 'às' HH:mm", { locale: ptBR })}
                    </span>
                    {notification.link && (
                      <span className="flex items-center gap-1 text-sm text-accent font-mono uppercase tracking-wider">
                        Ver detalhes
                        <ArrowRight className="w-4 h-4" />
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </motion.button>
          ))
        )}
      </div>
    </div>
  );
};
