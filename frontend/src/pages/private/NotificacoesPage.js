import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import { useNotifications } from '../../contexts/NotificationContext';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { notificationsAPI } from '../../utils/api';
import { toast } from 'sonner';
import {
  Bell, CheckCheck, ArrowRight, Trash2, Send, Filter,
  DollarSign, Calendar, FolderKanban, MessageSquare, Vote,
  FileText, Settings, Megaphone, X, ChevronDown, Info
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const NOTIFICATION_ICONS = {
  geral: Bell,
  financeiro: DollarSign,
  evento: Calendar,
  projeto: FolderKanban,
  mural: MessageSquare,
  wall_post_pending: MessageSquare,
  wall_post_approved: MessageSquare,
  wall_comment: MessageSquare,
  votacao: Vote,
  poll_opened: Vote,
  documento: FileText,
  document_new: FileText,
  sistema: Settings,
  invoice_due: DollarSign,
};

const NOTIFICATION_COLORS = {
  geral: 'bg-blue-500',
  financeiro: 'bg-green-600',
  evento: 'bg-purple-600',
  projeto: 'bg-amber-600',
  mural: 'bg-indigo-500',
  wall_post_pending: 'bg-orange-500',
  wall_post_approved: 'bg-green-500',
  wall_comment: 'bg-indigo-500',
  votacao: 'bg-teal-600',
  poll_opened: 'bg-teal-600',
  documento: 'bg-sky-600',
  document_new: 'bg-sky-600',
  sistema: 'bg-gray-600',
  invoice_due: 'bg-carmesim',
};

const FILTER_OPTIONS = [
  { value: '', label: 'Todas' },
  { value: 'geral', label: 'Geral' },
  { value: 'financeiro', label: 'Financeiro' },
  { value: 'evento', label: 'Evento' },
  { value: 'projeto', label: 'Projeto' },
  { value: 'mural', label: 'Mural' },
  { value: 'sistema', label: 'Sistema' },
];

const BroadcastPanel = ({ onSent }) => {
  const [expanded, setExpanded] = useState(false);
  const [form, setForm] = useState({ type: 'geral', title: '', message: '', link: '' });

  const broadcastMutation = useMutation({
    mutationFn: (payload) =>
      notificationsAPI.broadcast({
        user_id: 'broadcast',
        type: payload.type,
        title: payload.title,
        message: payload.message,
        link: payload.link || null,
      }),
    onSuccess: () => {
      toast.success('Notificacao enviada a todos os socios!');
      setForm({ type: 'geral', title: '', message: '', link: '' });
      setExpanded(false);
      // NotificationContext nao usa TanStack ainda — chamamos refresh()
      // do context para o admin tambem ver a sua propria broadcast.
      if (onSent) onSent();
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Erro ao enviar');
    },
  });

  const sending = broadcastMutation.isPending;

  const handleSend = (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.message.trim()) {
      toast.error('Preencha o titulo e a mensagem');
      return;
    }
    broadcastMutation.mutate(form);
  };

  return (
    <div className="card-technical overflow-hidden" data-testid="broadcast-panel">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:opacity-90 transition-colors"
        style={{ backgroundColor: 'var(--surface-card)' }}
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-carmesim rounded-lg flex items-center justify-center">
            <Megaphone className="w-4 h-4 text-white" />
          </div>
          <div className="text-left">
            <span className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>Enviar Notificacao</span>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Broadcast para todos os socios ativos</p>
          </div>
        </div>
        <ChevronDown className={`w-5 h-5 transition-transform ${expanded ? 'rotate-180' : ''}`} style={{ color: 'var(--text-muted)' }} />
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <form onSubmit={handleSend} className="p-4 space-y-3" style={{ borderTop: '1px solid var(--surface-border)' }}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider mb-1 block" style={{ color: 'var(--text-muted)' }}>Tipo</label>
                  <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
                    data-testid="broadcast-type-select">
                    <option value="geral">Geral</option>
                    <option value="financeiro">Financeiro</option>
                    <option value="evento">Evento</option>
                    <option value="projeto">Projeto</option>
                    <option value="sistema">Sistema</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider mb-1 block" style={{ color: 'var(--text-muted)' }}>Link (opcional)</label>
                  <input type="text" value={form.link} onChange={(e) => setForm({ ...form, link: e.target.value })}
                    placeholder="/financeiro, /eventos..."
                    className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
                    data-testid="broadcast-link-input" />
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider mb-1 block" style={{ color: 'var(--text-muted)' }}>Titulo *</label>
                <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="Ex: Assembleia Geral Extraordinaria"
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
                  data-testid="broadcast-title-input" />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider mb-1 block" style={{ color: 'var(--text-muted)' }}>Mensagem *</label>
                <textarea value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })}
                  placeholder="Detalhes da notificacao..."
                  rows={3}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none resize-none"
                  data-testid="broadcast-message-input" />
              </div>
              <div className="flex items-center justify-between">
                <p className="text-xs flex items-center gap-1" style={{ color: 'var(--text-muted)' }}>
                  <Info className="w-3 h-3" /> Sera enviada a todos os socios ativos
                </p>
                <button type="submit" disabled={sending} className="btn-primary flex items-center gap-2 text-sm" data-testid="broadcast-send-btn">
                  <Send className={`w-4 h-4 ${sending ? 'animate-pulse' : ''}`} />
                  {sending ? 'A enviar...' : 'Enviar'}
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export const NotificacoesPage = () => {
  const {
    notifications, total, unreadCount, loading,
    markAsRead, markAllAsRead, deleteNotification, clearReadNotifications, refresh,
  } = useNotifications();
  const { isAdmin } = useAuth();
  const navigate = useNavigate();
  const [filterType, setFilterType] = useState('');
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);

  const filteredNotifications = notifications.filter((n) => {
    if (filterType && n.type !== filterType) return false;
    if (showUnreadOnly && n.read) return false;
    return true;
  });

  const handleNotificationClick = (notification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
    if (notification.link) {
      navigate(notification.link);
    }
  };

  const handleDelete = async (e, notificationId) => {
    e.stopPropagation();
    await deleteNotification(notificationId);
    toast.success('Notificacao removida');
  };

  const getIcon = (type) => {
    const Icon = NOTIFICATION_ICONS[type] || Bell;
    return Icon;
  };

  const getColor = (type) => {
    return NOTIFICATION_COLORS[type] || 'bg-gray-500';
  };

  const readCount = notifications.filter(n => n.read).length;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="page-title" data-testid="notifications-title">Central de Notificacoes</h1>
          <p className="page-subtitle">Acompanhe todas as atualizacoes importantes</p>
        </div>
        <div className="flex items-center gap-2">
          {readCount > 0 && (
            <button onClick={clearReadNotifications}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-colors btn-outline"
              data-testid="clear-read-btn">
              <Trash2 className="w-3.5 h-3.5" /> Limpar lidas
            </button>
          )}
          {unreadCount > 0 && (
            <button onClick={markAllAsRead}
              className="btn-primary flex items-center gap-2 text-xs"
              data-testid="mark-all-read-button">
              <CheckCheck className="w-4 h-4" /> Marcar todas como lidas
            </button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="card-technical p-4">
          <div className="font-mono text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{total}</div>
          <div className="text-xs uppercase tracking-wider mt-1" style={{ color: 'var(--text-muted)' }}>Total</div>
        </div>
        <div className="card-technical p-4">
          <div className="font-mono text-2xl font-bold text-carmesim">{unreadCount}</div>
          <div className="text-xs uppercase tracking-wider mt-1" style={{ color: 'var(--text-muted)' }}>Nao lidas</div>
        </div>
        <div className="card-technical p-4">
          <div className="font-mono text-2xl font-bold text-green-600">{readCount}</div>
          <div className="text-xs uppercase tracking-wider mt-1" style={{ color: 'var(--text-muted)' }}>Lidas</div>
        </div>
        <div className="card-technical p-4">
          <div className="font-mono text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{filteredNotifications.length}</div>
          <div className="text-xs uppercase tracking-wider mt-1" style={{ color: 'var(--text-muted)' }}>Filtradas</div>
        </div>
      </div>

      {/* Admin Broadcast Panel */}
      {isAdmin && <BroadcastPanel onSent={refresh} />}

      {/* Filters */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <Filter className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
        {FILTER_OPTIONS.map((opt) => (
          <button key={opt.value} onClick={() => setFilterType(opt.value)}
            data-testid={`filter-notif-${opt.value || 'all'}`}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap ${
              filterType === opt.value ? 'bg-grafite text-white' : 'btn-outline !h-auto !px-3 !py-1.5 !rounded-full !text-xs'
            }`}>
            {opt.label}
          </button>
        ))}
        <button onClick={() => setShowUnreadOnly(!showUnreadOnly)}
          data-testid="toggle-unread-only"
          className={`ml-auto px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap ${
            showUnreadOnly ? 'bg-carmesim text-white' : 'btn-outline !h-auto !px-3 !py-1.5 !rounded-full !text-xs'
          }`}>
          Nao lidas
        </button>
      </div>

      {/* Notifications List */}
      <div className="space-y-2">
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filteredNotifications.length === 0 ? (
          <div className="card-technical rounded-xl p-12 text-center" data-testid="no-notifications-page">
            <Bell className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
            <p className="font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Nenhuma notificacao</p>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              {filterType || showUnreadOnly ? 'Tente alterar os filtros' : 'Sera notificado sobre eventos importantes'}
            </p>
          </div>
        ) : (
          filteredNotifications.map((notification, index) => {
            const Icon = getIcon(notification.type);
            const iconColor = getColor(notification.type);
            return (
              <motion.div
                key={notification.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                onClick={() => handleNotificationClick(notification)}
                className={`card-technical rounded-xl p-4 sm:p-5 cursor-pointer hover:shadow-md transition-all group ${
                  !notification.read ? 'border-l-4 border-l-carmesim' : ''
                }`}
                data-testid={`notification-item-${notification.id}`}
              >
                <div className="flex items-start gap-3 sm:gap-4">
                  <div className={`w-9 h-9 sm:w-10 sm:h-10 ${iconColor} rounded-lg flex items-center justify-center flex-shrink-0`}>
                    <Icon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <h3 className="font-semibold text-sm sm:text-base" style={{ color: 'var(--text-primary)' }}>{notification.title}</h3>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {!notification.read && (
                          <span className="w-2 h-2 bg-carmesim rounded-full" />
                        )}
                        <button
                          onClick={(e) => handleDelete(e, notification.id)}
                          className="p-1 rounded-md opacity-0 group-hover:opacity-100 text-gray-400 hover:text-carmesim hover:bg-carmesim/10 transition-all"
                          data-testid={`delete-notif-${notification.id}`}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <p className="text-sm mb-2" style={{ color: 'var(--text-secondary)' }}>{notification.message}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
                        {notification.created_at ? format(new Date(notification.created_at), "dd MMM yyyy 'as' HH:mm", { locale: ptBR }) : ''}
                      </span>
                      {notification.link && (
                        <span className="flex items-center gap-1 text-xs text-carmesim font-semibold">
                          Ver <ArrowRight className="w-3 h-3" />
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
};
