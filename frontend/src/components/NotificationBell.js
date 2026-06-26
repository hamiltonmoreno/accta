import React, { useEffect, useState } from 'react';
import { useNotifications } from '../contexts/NotificationContext';
import { useNavigate } from 'react-router-dom';
import { Bell, BarChart3, CheckCheck, CheckCircle2, FileText, X } from 'lucide-react';
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

  const recentNotifications = notifications.slice(0, 10);

  const NOTIF_ICONS = {
    poll_opened: BarChart3,
    document_new: FileText,
    wall_post_approved: CheckCircle2,
  };
  const getNotificationIcon = (type) => NOTIF_ICONS[type] || Bell;

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
        className="relative flex items-center justify-center h-11 w-11 rounded-lg text-secondary-auto hover:text-carmesim hover:bg-carmesim/10 transition-colors"
        data-testid="notification-bell"
        aria-label={
          unreadCount > 0
            ? `Notificações (${unreadCount} não lidas)`
            : 'Notificações'
        }
        aria-haspopup="dialog"
        aria-expanded={isOpen}
      >
        <Bell className="w-5 h-5" aria-hidden="true" />
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

          {/* Panel — em telemóvel fixa-se com margem de 16px nos dois bordos
              (left-4/right-4) para nunca cortar; em sm+ volta ao painel ancorado
              ao sino (sem regressão no desktop). spec 006 US4. */}
          <div
            className={`fixed left-4 right-4 top-16 w-auto sm:absolute sm:left-auto sm:right-0 sm:top-full sm:mt-2 sm:w-[400px] sm:max-w-[90vw] bg-white rounded-xl shadow-2xl border border-gray-200 z-50 ${
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
                    className="p-2 -mr-1 rounded hover:bg-gray-100 transition-colors cursor-pointer"
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
                    {recentNotifications.map((notification) => {
                      const Icon = getNotificationIcon(notification.type);
                      return (
                      <button
                        key={notification.id}
                        onClick={() => handleNotificationClick(notification)}
                        className={`w-full px-6 py-4 hover:bg-gray-50 transition-colors text-left ${
                          !notification.read ? 'bg-carmesim/5' : ''
                        }`}
                        data-testid={`notification-${notification.id}`}
                      >
                        <div className="flex items-start gap-3">
                          <span className="flex-shrink-0 w-9 h-9 rounded-lg bg-[#F5F5F5] flex items-center justify-center">
                            <Icon className="w-5 h-5 text-grafite" aria-hidden="true" />
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2 mb-1">
                              <h4 className="font-sans font-semibold text-grafite">
                                {notification.title}
                              </h4>
                              {!notification.read && (
                                <>
                                  <div className="w-2 h-2 bg-carmesim rounded-full flex-shrink-0 mt-2" aria-hidden="true" />
                                  <span className="sr-only">Não lida</span>
                                </>
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
                      );
                    })}
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
