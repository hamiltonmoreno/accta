import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import { statsAPI, invoicesAPI, pollsAPI } from '../../utils/api';
import { Users, DollarSign, AlertCircle, Vote, CheckCircle, Bell } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useNavigate } from 'react-router-dom';

export const DashboardPage = () => {
  const { user, isAdmin, isFinanceiro } = useAuth();
  const { notifications, unreadCount } = useNotifications();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [myInvoices, setMyInvoices] = useState([]);
  const [activePolls, setActivePolls] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
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
        <h1 className="font-outfit font-bold text-4xl text-primary mb-2" data-testid="dashboard-title">
          Bem-vindo, {user?.name}
        </h1>
        <p className="text-slate-600">Aqui está um resumo da sua conta e atividades</p>
      </div>

      {/* Status Alert */}
      {user?.status !== 'ativo' && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-technical rounded-xl p-6 border-2 border-alert"
          data-testid="status-alert"
        >
          <div className="flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-alert flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-outfit font-semibold text-lg text-alert mb-2">Atenção: Status {user?.status}</h3>
              <p className="text-slate-600">
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
              <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center">
                <Users className="w-6 h-6 text-accent" />
              </div>
            </div>
            <div className="font-mono text-3xl font-bold text-primary mb-1">{stats.total_users}</div>
            <div className="text-sm text-slate-500 uppercase tracking-wider">Total Sócios</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="card-technical rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-accent rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-primary" />
              </div>
            </div>
            <div className="font-mono text-3xl font-bold text-accent mb-1">{stats.active_users}</div>
            <div className="text-sm text-slate-500 uppercase tracking-wider">Sócios Ativos</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card-technical rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-alert rounded-lg flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="font-mono text-3xl font-bold text-alert mb-1">{stats.pending_invoices}</div>
            <div className="text-sm text-slate-500 uppercase tracking-wider">Quotas Pendentes</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="card-technical rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-accent" />
              </div>
            </div>
            <div className="font-mono text-3xl font-bold text-primary mb-1">{stats.total_revenue.toFixed(0)} CVE</div>
            <div className="text-sm text-slate-500 uppercase tracking-wider">Receita Total</div>
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
            <h2 className="font-outfit font-semibold text-2xl text-primary">Quotas Pendentes</h2>
            <div className="text-xs font-mono text-slate-500 uppercase">Folha Salarial</div>
          </div>
          {pendingInvoices.length === 0 ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center mx-auto mb-3">
                <CheckCircle className="w-8 h-8 text-accent" />
              </div>
              <p className="text-slate-600 font-medium mb-1" data-testid="no-pending-invoices">Tudo em dia!</p>
              <p className="text-sm text-slate-500">Suas quotas estão sendo descontadas automaticamente</p>
            </div>
          ) : (
            <div className="space-y-3">
              {pendingInvoices.map((invoice) => (
                <div key={invoice.id} className="flex items-center justify-between p-4 bg-alert/5 border border-alert/20 rounded-lg" data-testid={`invoice-${invoice.id}`}>
                  <div>
                    <div className="font-manrope font-semibold text-primary">{invoice.type}</div>
                    <div className="font-mono text-sm text-slate-500">
                      Vencimento: {new Date(invoice.due_date).toLocaleDateString('pt')}
                    </div>
                    {invoice.source === 'folha_salarial' && (
                      <div className="text-xs text-alert mt-1">Aguardando desconto em folha</div>
                    )}
                  </div>
                  <div className="font-mono font-bold text-lg text-primary">{invoice.amount} CVE</div>
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
          <h2 className="font-outfit font-semibold text-2xl text-primary mb-4">Votações Abertas</h2>
          {activePolls.length === 0 ? (
            <p className="text-slate-500 text-center py-8" data-testid="no-active-polls">Nenhuma votação aberta</p>
          ) : (
            <div className="space-y-3">
              {activePolls.slice(0, 3).map((poll) => (
                <div key={poll.id} className="flex items-start gap-3 p-4 bg-slate-50 rounded-lg" data-testid={`poll-${poll.id}`}>
                  <Vote className="w-5 h-5 text-accent flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <div className="font-manrope font-semibold text-primary mb-1">{poll.title}</div>
                    <div className="font-mono text-xs text-slate-500">
                      Até {new Date(poll.end_date).toLocaleDateString('pt')}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};
