import React, { useEffect, useState } from 'react';
import { useNotifications } from '../contexts/NotificationContext';
import { useNavigate } from 'react-router-dom';
import { Bell, Check, CheckCheck, X } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const NotificationBell = () => {
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications();
  const [isOpen, setIsOpen] = useState(false);
  // `render` mantem o painel montado durante a fade-out animation.
  // Ao isOpen=true: render=true imediato (montagem). Ao isOpen=false:
  // render fica true ate onAnimationEnd da fade-out disparar.
  const [render, setRender] = useState(false);
  useEffect(() => { if (isOpen) setRender(true); }, [isOpen]);
  const navigate = useNavigate();

  const unreadNotifications = notifications.filter((n) => !n.read);
  const recentNotifications = notifications.slice(0, 10);

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'poll_opened':
        return '📊';
      case 'invoice_due':
        return '💰';
      case 'document_new':
        return '📄';
      case 'wall_post_approved':
        return '✅';
      default:
        return '🔔';
    }
  };

  const handleNotificationClick = (notification) => {
    markAsRead(notification.id);
    setIsOpen(false);
    if (notification.link) {
      navigate(notification.link);
    }
  };

  return (
    <div className="relative">
      {/* Bell Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-white/10 transition-colors"
        data-testid="notification-bell"
        aria-label={
          unreadCount > 0
            ? `Notificações (${unreadCount} não lidas)`
            : 'Notificações'
        }
        aria-haspopup="dialog"
        aria-expanded={isOpen}
      >
        <Bell className="w-6 h-6 text-white/80" aria-hidden="true" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-carmesim text-white text-xs font-bold rounded-full flex items-center justify-center animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown — delayed-unmount pattern para exit animation.
          render fica true ate animacao de fade-out terminar (onAnimationEnd). */}
      {render && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Panel */}
          <div
            className={`absolute right-0 top-full mt-2 w-[400px] max-w-[90vw] bg-white rounded-xl shadow-2xl border border-gray-200 z-50 ${
              isOpen ? 'animate-fade-up' : 'animate-fade-out'
            }`}
            onAnimationEnd={() => { if (!isOpen) setRender(false); }}
            data-testid="notification-panel"
          >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
                <div>
                  <h3 className="font-sans font-semibold text-lg text-grafite">Notificações</h3>
                  {unreadCount > 0 && (
                    <p className="text-xs text-gray-500 font-mono">{unreadCount} não lida{unreadCount !== 1 ? 's' : ''}</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllAsRead}
                      className="text-xs text-carmesim hover:text-carmesim/80 font-semibold flex items-center gap-1"
                      data-testid="mark-all-read"
                    >
                      <CheckCheck className="w-4 h-4" />
                      Marcar todas
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setIsOpen(false)}
                    className="p-1 rounded hover:bg-gray-100 transition-colors"
                    aria-label="Fechar painel de notificações"
                  >
                    <X className="w-5 h-5 text-gray-400" aria-hidden="true" />
                  </button>
                </div>
              </div>

              {/* Notifications List */}
              <div className="max-h-[500px] overflow-y-auto">
                {recentNotifications.length === 0 ? (
                  <div className="px-6 py-12 text-center" data-testid="no-notifications">
                    <Bell className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">Nenhuma notificação</p>
                  </div>
                ) : (
                  <div className="divide-y divide-[#E5E7EB]">
                    {recentNotifications.map((notification) => (
                      <button
                        key={notification.id}
                        onClick={() => handleNotificationClick(notification)}
                        className={`w-full px-6 py-4 hover:bg-gray-50 transition-colors text-left ${
                          !notification.read ? 'bg-carmesim/5' : ''
                        }`}
                        data-testid={`notification-${notification.id}`}
                      >
                        <div className="flex items-start gap-3">
                          <span className="text-2xl flex-shrink-0">
                            {getNotificationIcon(notification.type)}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2 mb-1">
                              <h4 className="font-sans font-semibold text-grafite">
                                {notification.title}
                              </h4>
                              {!notification.read && (
                                <div className="w-2 h-2 bg-carmesim rounded-full flex-shrink-0 mt-2" />
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{notification.message}</p>
                            <p className="text-xs text-[#6B7280] font-mono">
                              {formatDistanceToNow(new Date(notification.created_at), {
                                addSuffix: true,
                                locale: ptBR,
                              })}
                            </p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer */}
              {notifications.length > 10 && (
                <div className="px-6 py-4 border-t border-gray-200 text-center">
                  <button
                    onClick={() => {
                      setIsOpen(false);
                      navigate('/notificacoes');
                    }}
                    className="text-sm text-grafite hover:text-grafite/80 font-semibold"
                  >
                    Ver todas as notificações
                  </button>
                </div>
              )}
          </div>
        </>
      )}
    </div>
  );
};
