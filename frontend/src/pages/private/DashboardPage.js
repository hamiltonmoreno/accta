import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import { statsAPI, invoicesAPI, pollsAPI, eventsAPI } from '../../utils/api';
import { Users, DollarSign, AlertCircle, Vote, CheckCircle, Bell, Calendar, MapPin, Clock, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const StatCard = ({ icon: Icon, value, label, color, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 16 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay }}
    className="card-technical card-hover p-4 sm:p-5"
  >
    <div className="flex items-center gap-3 sm:gap-4">
      <div className={`w-10 h-10 sm:w-11 sm:h-11 ${color} rounded-lg flex items-center justify-center flex-shrink-0`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div className="min-w-0">
        <div className="font-mono text-xl sm:text-2xl font-bold text-grafite truncate">{value}</div>
        <div className="text-[10px] sm:text-xs text-gray-500 uppercase tracking-wider">{label}</div>
      </div>
    </div>
  </motion.div>
);

const NotifIcon = ({ type }) => {
  const icons = {
    poll_opened: <Vote className="w-4 h-4 text-carmesim" />,
    invoice_due: <DollarSign className="w-4 h-4 text-orange-500" />,
    event_new: <Calendar className="w-4 h-4 text-blue-500" />,
    wall_post_approved: <CheckCircle className="w-4 h-4 text-green-500" />,
    wall_comment: <Bell className="w-4 h-4 text-purple-500" />,
  };
  return (
    <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
      {icons[type] || <Bell className="w-4 h-4 text-gray-400" />}
    </div>
  );
};

export const DashboardPage = () => {
  const { user, isAdmin, isFinanceiro } = useAuth();
  const { notifications, unreadCount } = useNotifications();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [myInvoices, setMyInvoices] = useState([]);
  const [activePolls, setActivePolls] = useState([]);
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadData = async () => {
    try {
      if (isAdmin || isFinanceiro) {
        const statsRes = await statsAPI.get();
        setStats(statsRes.data);
      }

      const invoicesRes = await invoicesAPI.getAll();
      setMyInvoices(invoicesRes.data.slice(0, 5));

      const pollsRes = await pollsAPI.getAll();
      const active = pollsRes.data.filter((p) => p.status === 'aberta');
      setActivePolls(active);

      try {
        const eventsRes = await eventsAPI.getUpcoming();
        setUpcomingEvents(eventsRes.data.slice(0, 3));
      } catch (e) {
        // Events not available
      }
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  const pendingInvoices = myInvoices.filter((inv) => inv.status === 'pendente');

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-3 border-carmesim border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-5 sm:space-y-6">
      {/* Header */}
      <div>
        <h1 className="page-title" data-testid="dashboard-title">
          Bem-vindo, {user?.name?.split(' ')[0]}
        </h1>
        <p className="page-subtitle">Resumo da sua conta e atividades</p>
      </div>

      {/* Status Alert */}
      {user?.status !== 'ativo' && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-technical p-4 sm:p-5 border-l-4 border-l-carmesim"
          data-testid="status-alert"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-carmesim flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-sm text-carmesim mb-1">Status: {user?.status}</h3>
              <p className="text-xs sm:text-sm text-gray-600">
                Algumas funcionalidades podem estar restritas. Regularize sua situacao.
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Admin Stats */}
      {(isAdmin || isFinanceiro) && stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <StatCard icon={Users} value={stats.total_users} label="Total Socios" color="bg-grafite" delay={0.05} />
          <StatCard icon={CheckCircle} value={stats.active_users} label="Socios Ativos" color="bg-green-600" delay={0.1} />
          <StatCard icon={AlertCircle} value={stats.pending_invoices} label="Quotas Pendentes" color="bg-carmesim" delay={0.15} />
          <StatCard icon={DollarSign} value={`${stats.total_revenue.toFixed(0)} CVE`} label="Receita Total" color="bg-grafite" delay={0.2} />
        </div>
      )}

      {/* Main Grid: Invoices + Polls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-5">
        {/* Pending Invoices */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-technical card-hover p-4 sm:p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-lg sm:text-xl text-grafite">Quotas Pendentes</h2>
            <span className="text-[10px] text-gray-400 uppercase tracking-wider hidden sm:block">Folha Salarial</span>
          </div>
          {pendingInvoices.length === 0 ? (
            <div className="text-center py-6 sm:py-8">
              <div className="w-12 h-12 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-2">
                <CheckCircle className="w-6 h-6 text-green-500" />
              </div>
              <p className="text-sm text-grafite font-medium" data-testid="no-pending-invoices">Tudo em dia!</p>
              <p className="text-xs text-gray-400 mt-1">Quotas descontadas automaticamente</p>
            </div>
          ) : (
            <div className="space-y-2">
              {pendingInvoices.map((invoice) => (
                <div key={invoice.id} className="flex items-center justify-between p-3 bg-carmesim/5 border border-carmesim/15 rounded-lg" data-testid={`invoice-${invoice.id}`}>
                  <div className="min-w-0">
                    <div className="font-semibold text-sm text-grafite capitalize">{invoice.type}</div>
                    <div className="text-xs text-gray-400">
                      Vence: {new Date(invoice.due_date).toLocaleDateString('pt')}
                    </div>
                  </div>
                  <div className="font-mono font-bold text-sm text-grafite flex-shrink-0 ml-3">{invoice.amount} CVE</div>
                </div>
              ))}
            </div>
          )}
        </motion.div>

        {/* Active Polls */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card-technical card-hover p-4 sm:p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-lg sm:text-xl text-grafite">Votacoes Abertas</h2>
            {activePolls.length > 0 && (
              <button onClick={() => navigate('/votacoes')} className="text-xs text-carmesim font-semibold uppercase tracking-wider hover:text-carmesim-dark">
                Ver todas
              </button>
            )}
          </div>
          {activePolls.length === 0 ? (
            <div className="text-center py-6 sm:py-8">
              <Vote className="w-10 h-10 text-gray-200 mx-auto mb-2" />
              <p className="text-sm text-gray-400" data-testid="no-active-polls">Nenhuma votacao aberta</p>
            </div>
          ) : (
            <div className="space-y-2">
              {activePolls.slice(0, 3).map((poll) => (
                <button key={poll.id} onClick={() => navigate('/votacoes')} className="w-full flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-left" data-testid={`poll-${poll.id}`}>
                  <Vote className="w-4 h-4 text-carmesim flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-sm text-grafite truncate">{poll.title}</div>
                    <div className="text-xs text-gray-400">
                      Ate {new Date(poll.end_date).toLocaleDateString('pt')}
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-300 flex-shrink-0" />
                </button>
              ))}
            </div>
          )}
        </motion.div>
      </div>

      {/* Upcoming Events */}
      {upcomingEvents.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="card-technical card-hover p-4 sm:p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-lg sm:text-xl text-grafite">Proximos Eventos</h2>
            <button
              onClick={() => navigate('/eventos')}
              className="text-xs text-carmesim hover:text-carmesim-dark uppercase tracking-wider font-semibold"
            >
              Ver todos
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {upcomingEvents.map((event) => (
              <button
                key={event.id}
                className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-left w-full"
                onClick={() => navigate('/eventos')}
              >
                <div className="w-11 h-11 bg-grafite rounded-lg flex flex-col items-center justify-center flex-shrink-0">
                  <span className="font-bold text-sm text-white leading-none">
                    {format(new Date(event.date), 'dd')}
                  </span>
                  <span className="text-[9px] text-carmesim uppercase font-bold leading-none mt-0.5">
                    {format(new Date(event.date), 'MMM', { locale: ptBR })}
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-sm text-grafite truncate">{event.title}</h3>
                  <div className="flex items-center gap-1.5 text-[11px] text-gray-400 mt-1">
                    <Clock className="w-3 h-3 flex-shrink-0" />
                    <span>{format(new Date(event.date), 'HH:mm')}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[11px] text-gray-400 mt-0.5">
                    <MapPin className="w-3 h-3 flex-shrink-0" />
                    <span className="truncate">{event.location}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Notifications */}
      {unreadCount > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-technical p-4 sm:p-5 border-l-4 border-l-carmesim"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-carmesim" />
              <h3 className="font-semibold text-sm text-grafite">
                {unreadCount} notificacao{unreadCount !== 1 ? 'es' : ''} nova{unreadCount !== 1 ? 's' : ''}
              </h3>
            </div>
            <button
              onClick={() => navigate('/notificacoes')}
              className="text-xs text-carmesim hover:text-carmesim-dark uppercase tracking-wider font-semibold"
            >
              Ver todas
            </button>
          </div>
          <div className="space-y-1.5">
            {notifications.filter(n => !n.read).slice(0, 3).map((notif) => (
              <button
                key={notif.id}
                onClick={() => navigate('/notificacoes')}
                className="w-full flex items-center gap-3 p-2.5 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-left"
              >
                <NotifIcon type={notif.type} />
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-grafite text-xs truncate">{notif.title}</div>
                  <div className="text-[11px] text-gray-400 truncate">{notif.message}</div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-gray-300 flex-shrink-0" />
              </button>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};
