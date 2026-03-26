import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import { statsAPI, invoicesAPI, pollsAPI, eventsAPI } from '../../utils/api';
import { Users, DollarSign, AlertCircle, Vote, CheckCircle, Bell, Calendar, MapPin, Clock } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

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

      // Load upcoming events
      try {
        const eventsRes = await eventsAPI.getUpcoming();
        setUpcomingEvents(eventsRes.data.slice(0, 3));
      } catch (e) {
        console.log('Eventos não disponíveis');
      }
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  const pendingInvoices = myInvoices.filter((inv) => inv.status === 'pendente');

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-bold text-4xl text-grafite mb-2" data-testid="dashboard-title">
          Bem-vindo, {user?.name}
        </h1>
        <p className="text-gray-600">Aqui está um resumo da sua conta e atividades</p>
      </div>

      {/* Status Alert */}
      {user?.status !== 'ativo' && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-technical rounded-xl p-6 border-2 border-carmesim"
          data-testid="status-alert"
        >
          <div className="flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-carmesim flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-lg text-carmesim mb-2">Atenção: Status {user?.status}</h3>
              <p className="text-gray-600">
                Sua conta está com status <strong>{user?.status}</strong>. Algumas funcionalidades podem estar restritas. 
                Por favor, regularize sua situação ou entre em contato com a administração.
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Admin Stats */}
      {(isAdmin || isFinanceiro) && stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="card-technical rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-grafite rounded-lg flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="text-3xl font-bold text-grafite mb-1">{stats.total_users}</div>
            <div className="text-sm text-gray-500 uppercase tracking-wider">Total Sócios</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="card-technical rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="text-3xl font-bold text-green-600 mb-1">{stats.active_users}</div>
            <div className="text-sm text-gray-500 uppercase tracking-wider">Sócios Ativos</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card-technical rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-carmesim rounded-lg flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="text-3xl font-bold text-carmesim mb-1">{stats.pending_invoices}</div>
            <div className="text-sm text-gray-500 uppercase tracking-wider">Quotas Pendentes</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="card-technical rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-grafite rounded-lg flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-carmesim" />
              </div>
            </div>
            <div className="text-3xl font-bold text-grafite mb-1">{stats.total_revenue.toFixed(0)} CVE</div>
            <div className="text-sm text-gray-500 uppercase tracking-wider">Receita Total</div>
          </motion.div>
        </div>
      )}

      {/* Pending Invoices & Active Polls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Invoices */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-technical rounded-xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-2xl text-grafite">Quotas Pendentes</h2>
            <div className="text-xs text-gray-500 uppercase">Folha Salarial</div>
          </div>
          {pendingInvoices.length === 0 ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <p className="text-gray-600 font-medium mb-1" data-testid="no-pending-invoices">Tudo em dia!</p>
              <p className="text-sm text-gray-500">Suas quotas estão sendo descontadas automaticamente</p>
            </div>
          ) : (
            <div className="space-y-3">
              {pendingInvoices.map((invoice) => (
                <div key={invoice.id} className="flex items-center justify-between p-4 bg-carmesim/5 border border-carmesim/20 rounded-lg" data-testid={`invoice-${invoice.id}`}>
                  <div>
                    <div className="font-semibold text-grafite">{invoice.type}</div>
                    <div className="text-sm text-gray-500">
                      Vencimento: {new Date(invoice.due_date).toLocaleDateString('pt')}
                    </div>
                    {invoice.source === 'folha_salarial' && (
                      <div className="text-xs text-carmesim mt-1">Aguardando desconto em folha</div>
                    )}
                  </div>
                  <div className="font-bold text-lg text-grafite">{invoice.amount} CVE</div>
                </div>
              ))}
            </div>
          )}
        </motion.div>

        {/* Active Polls */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card-technical rounded-xl p-6"
        >
          <h2 className="font-semibold text-2xl text-grafite mb-4">Votações Abertas</h2>
          {activePolls.length === 0 ? (
            <p className="text-gray-500 text-center py-8" data-testid="no-active-polls">Nenhuma votação aberta</p>
          ) : (
            <div className="space-y-3">
              {activePolls.slice(0, 3).map((poll) => (
                <div key={poll.id} className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg" data-testid={`poll-${poll.id}`}>
                  <Vote className="w-5 h-5 text-carmesim flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <div className="font-semibold text-grafite mb-1">{poll.title}</div>
                    <div className="text-xs text-gray-500">
                      Até {new Date(poll.end_date).toLocaleDateString('pt')}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>

      {/* Upcoming Events Widget */}
      {upcomingEvents.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="card-technical rounded-xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-2xl text-grafite">Próximos Eventos</h2>
            <button
              onClick={() => navigate('/eventos')}
              className="text-sm text-carmesim hover:text-carmesim-dark uppercase tracking-wider font-semibold"
            >
              Ver todos
            </button>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            {upcomingEvents.map((event) => (
              <div
                key={event.id}
                className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                onClick={() => navigate('/eventos')}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-grafite rounded-lg flex items-center justify-center">
                    <Calendar className="w-5 h-5 text-carmesim" />
                  </div>
                  <div>
                    <div className="font-bold text-lg text-grafite">
                      {format(new Date(event.date), 'dd')}
                    </div>
                    <div className="text-xs text-carmesim uppercase font-semibold">
                      {format(new Date(event.date), 'MMM', { locale: ptBR })}
                    </div>
                  </div>
                </div>
                <h3 className="font-semibold text-grafite mb-2 line-clamp-2">
                  {event.title}
                </h3>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Clock className="w-3 h-3" />
                  <span>{format(new Date(event.date), 'HH:mm')}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
                  <MapPin className="w-3 h-3" />
                  <span className="truncate">{event.location}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Recent Notifications Widget */}
      {unreadCount > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-technical rounded-xl p-6 border-2 border-carmesim/20 bg-carmesim/5"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-carmesim rounded-lg flex items-center justify-center">
                <Bell className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-lg text-grafite">Você tem {unreadCount} notificação{unreadCount !== 1 ? 'ões' : ''} nova{unreadCount !== 1 ? 's' : ''}</h3>
                <p className="text-sm text-gray-600">Atualizações importantes aguardando</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/notificacoes')}
              className="text-sm text-carmesim hover:text-carmesim-dark uppercase tracking-wider font-semibold"
            >
              Ver todas
            </button>
          </div>
          <div className="space-y-2">
            {notifications.filter(n => !n.read).slice(0, 3).map((notif) => (
              <button
                key={notif.id}
                onClick={() => navigate('/notificacoes')}
                className="w-full flex items-center gap-3 p-3 bg-white rounded-lg hover:bg-gray-50 transition-colors text-left"
              >
                <span className="text-xl">{notif.type === 'poll_opened' ? '📊' : notif.type === 'invoice_due' ? '💰' : '📄'}</span>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-grafite text-sm truncate">{notif.title}</div>
                  <div className="text-xs text-gray-500 truncate">{notif.message}</div>
                </div>
              </button>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};
