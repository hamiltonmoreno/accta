import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Bell } from 'lucide-react';
import { NotifIcon } from './widgets';

export const NotificationsList = ({ unreadCount, notifications }) => {
  const navigate = useNavigate();
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6 border-l-4 border-l-carmesim animate-fade-up">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-carmesim" />
          <h3 className="font-semibold text-sm text-grafite">
            {unreadCount} {unreadCount === 1 ? 'notificacao nova' : 'notificacoes novas'}
          </h3>
        </div>
        <button
          onClick={() => navigate('/notificacoes')}
          className="text-xs text-carmesim hover:text-carmesim-dark font-semibold"
        >
          Ver todas
        </button>
      </div>
      <div className="space-y-2">
        {notifications.filter((n) => !n.read).slice(0, 3).map((notif) => (
          <button
            key={notif.id}
            onClick={() => navigate('/notificacoes')}
            className="w-full flex items-center gap-3 p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors text-left"
          >
            <NotifIcon type={notif.type} />
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-grafite text-xs truncate">{notif.title}</div>
              <div className="text-xs text-[#6B7280] truncate">{notif.message}</div>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
          </button>
        ))}
      </div>
    </div>
  );
};
