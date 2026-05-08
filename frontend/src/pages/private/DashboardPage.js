import React, { useEffect, useState, Suspense, lazy } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import { statsAPI, pollsAPI, eventsAPI, financesAPI, activityAPI, reportAPI } from '../../utils/api';
import {
  Users, DollarSign, Vote, CheckCircle, Bell,
  Calendar, MapPin, Clock, ArrowRight, TrendingUp, TrendingDown,
  Wallet, ArrowUpRight, ArrowDownRight, BarChart3, MessageSquare,
  FolderKanban, Trophy, Activity, Image, FileText, Heart, ThumbsUp,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

// Recharts (~334KB) só carregado para utilizadores com finance, via Suspense.
const FinanceCharts = lazy(() => import('./dashboard/FinanceCharts'));

// ===== STAT CARD (Reference style: title top, big value, change indicator) =====
const StatCard = ({ title, value, icon: Icon, iconBg, change, changeLabel, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 16 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay }}
    className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6 hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] hover:-translate-y-0.5 transition-all duration-200"
  >
    <div className="flex items-center justify-between mb-3">
      <span className="text-sm text-gray-500 font-medium">{title}</span>
      <div className={`w-10 h-10 ${iconBg} rounded-xl flex items-center justify-center`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
    <div className="font-bold text-3xl sm:text-4xl text-grafite mb-1 font-sans tracking-tight">{value}</div>
    {change !== undefined && (
      <div className={`flex items-center gap-1 text-sm ${change >= 0 ? 'text-green-600' : 'text-red-500'}`}>
        {change >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
        <span className="font-semibold">{change >= 0 ? '+' : ''}{change}%</span>
        {changeLabel && <span className="text-gray-400 font-normal ml-0.5">{changeLabel}</span>}
      </div>
    )}
  </motion.div>
);

// ===== CHART CARD WRAPPER =====
const ChartCard = ({ title, subtitle, children, delay = 0, action }) => (
  <motion.div
    initial={{ opacity: 0, y: 16 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay }}
    className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6"
  >
    <div className="flex items-start justify-between mb-5">
      <div>
        <h3 className="text-lg font-semibold text-grafite">{title}</h3>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
    {children}
  </motion.div>
);

// ===== NOTIFICATION ICON =====
const NotifIcon = ({ type }) => {
  const config = {
    poll_opened: { icon: Vote, color: 'text-carmesim', bg: 'bg-carmesim/10' },
    invoice_due: { icon: DollarSign, color: 'text-orange-500', bg: 'bg-orange-50' },
    event_new: { icon: Calendar, color: 'text-blue-500', bg: 'bg-blue-50' },
    wall_post_approved: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-50' },
    wall_comment: { icon: Bell, color: 'text-purple-500', bg: 'bg-purple-50' },
  };
  const c = config[type] || { icon: Bell, color: 'text-gray-400', bg: 'bg-gray-100' };
  const IconComp = c.icon;
  return (
    <div className={`w-9 h-9 ${c.bg} rounded-xl flex items-center justify-center flex-shrink-0`}>
      <IconComp className={`w-4 h-4 ${c.color}`} />
    </div>
  );
};

// ===== CHART COLORS =====
const MONTH_LABELS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

const CATEGORY_LABELS = {
  quotas: 'Quotas', patrocinios: 'Patrocinios', doacoes: 'Doacoes',
  eventos: 'Eventos', outros_receita: 'Outros',
  operacional: 'Operacional', juridico: 'Juridico',
  comunicacao: 'Comunicacao', viagens: 'Viagens', outros_despesa: 'Outros Desp.',
};

// ===== ACTIVITY ICON =====
const ACTIVITY_ICONS = {
  mural: MessageSquare,
  projeto: FolderKanban,
  evento: Calendar,
  financeiro: DollarSign,
  votacao: Vote,
  trophy: Trophy,
};

const ACTIVITY_COLORS = {
  mural: { bg: 'bg-indigo-100', text: 'text-indigo-600' },
  projeto: { bg: 'bg-amber-100', text: 'text-amber-600' },
  evento: { bg: 'bg-purple-100', text: 'text-purple-600' },
  financeiro: { bg: 'bg-green-100', text: 'text-green-600' },
  votacao: { bg: 'bg-teal-100', text: 'text-teal-600' },
};

const ActivityIcon = ({ type }) => {
  const Icon = ACTIVITY_ICONS[type] || Activity;
  const colors = ACTIVITY_COLORS[type] || { bg: 'bg-gray-100', text: 'text-gray-500' };
  return (
    <div className={`w-9 h-9 ${colors.bg} rounded-xl flex items-center justify-center flex-shrink-0`}>
      <Icon className={`w-4 h-4 ${colors.text}`} />
    </div>
  );
};

const timeAgo = (dateStr) => {
  if (!dateStr) return '';
  try {
    const now = new Date();
    const date = new Date(dateStr);
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return 'agora mesmo';
    if (diff < 3600) return `ha ${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `ha ${Math.floor(diff / 3600)}h`;
    if (diff < 604800) return `ha ${Math.floor(diff / 86400)}d`;
    return format(date, 'dd MMM', { locale: ptBR });
  } catch {
    return '';
  }
};

// ===== MAIN DASHBOARD =====
export const DashboardPage = () => {
  const { user, isAdmin, isFinanceiro } = useAuth();
  const { notifications, unreadCount } = useNotifications();
  const navigate = useNavigate();

  const [stats, setStats] = useState(null);
  const [financeSummary, setFinanceSummary] = useState(null);
  const [dreData, setDreData] = useState(null);
  const [activePolls, setActivePolls] = useState([]);
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [personalReport, setPersonalReport] = useState(null);
  const [loading, setLoading] = useState(true);

  const currentYear = new Date().getFullYear();
  const hasFinance = isAdmin || isFinanceiro;

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadData = async () => {
    try {
      const promises = [
        pollsAPI.getAll(),
        eventsAPI.getUpcoming().catch(() => ({ data: [] })),
        activityAPI.getRecent(15).catch(() => ({ data: [] })),
      ];

      if (hasFinance) {
        promises.push(
          statsAPI.get(),
          financesAPI.getSummary({ year: currentYear }).catch(() => ({ data: null })),
          financesAPI.getDRE(currentYear).catch(() => ({ data: null })),
        );
      }

      const results = await Promise.all(promises);

      setActivePolls(results[0].data.filter((p) => p.status === 'aberta'));
      setUpcomingEvents(results[1].data.slice(0, 3));
      setRecentActivity(results[2].data || []);

      if (hasFinance) {
        setStats(results[3].data);
        setFinanceSummary(results[4].data);
        setDreData(results[5].data);
      }

      // Load personal report separately (non-blocking)
      reportAPI.getPersonal().then(r => setPersonalReport(r.data)).catch(() => {});
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  // Prepare chart data
  const monthlyChartData = dreData ? Object.entries(dreData.monthly).map(([month, d]) => ({
    name: MONTH_LABELS[parseInt(month) - 1],
    Receitas: d.receitas,
    Despesas: d.despesas,
  })) : [];

  const expensePieData = dreData ? Object.entries(dreData.despesas_por_categoria)
    .filter(([, v]) => v > 0)
    .map(([cat, val]) => ({
      name: CATEGORY_LABELS[cat] || cat,
      value: val,
    })) : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-3 border-carmesim border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 sm:space-y-7">
      {/* Header */}
      <div>
        <h1 className="page-title" data-testid="dashboard-title">
          Bem-vindo, {user?.name?.split(' ')[0]}
        </h1>
        <p className="page-subtitle">Resumo da sua conta e atividades</p>
      </div>

      {/* ===== ADMIN/FINANCEIRO: Stat Cards (Reference style) ===== */}
      {hasFinance && stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
          <StatCard
            title="Total Socios"
            value={stats.total_users}
            icon={Users}
            iconBg="bg-grafite/10 text-grafite"
            delay={0.05}
          />
          <StatCard
            title="Socios Ativos"
            value={stats.active_users}
            icon={CheckCircle}
            iconBg="bg-green-100 text-green-600"
            delay={0.1}
          />
          <StatCard
            title="Eventos Ativos"
            value={stats.active_events}
            icon={Calendar}
            iconBg="bg-carmesim/10 text-carmesim"
            delay={0.15}
          />
          <StatCard
            title="Receita Anual"
            value={financeSummary ? `${(financeSummary.total_receitas / 1000).toFixed(0)}k` : `${stats.total_revenue.toFixed(0)}`}
            icon={DollarSign}
            iconBg="bg-blue-100 text-blue-600"
            change={financeSummary && financeSummary.total_receitas > 0 ? Math.round((financeSummary.resultado_liquido / financeSummary.total_receitas) * 100) : undefined}
            changeLabel="margem"
            delay={0.2}
          />
        </div>
      )}

      {/* ===== CHARTS GRID — recharts em chunk lazy só carrega para finance users ===== */}
      {hasFinance && dreData && (
        <Suspense fallback={
          <div className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6 h-[320px] flex items-center justify-center">
            <div className="w-7 h-7 border-3 border-carmesim border-t-transparent rounded-full animate-spin" />
          </div>
        }>
          <FinanceCharts
            monthlyChartData={monthlyChartData}
            expensePieData={expensePieData}
            currentYear={currentYear}
            onViewAll={() => navigate('/financeiro')}
          />
        </Suspense>
      )}

      {/* ===== Financial Summary Banner (for admin) ===== */}
      {hasFinance && financeSummary && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6 cursor-pointer hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all"
          onClick={() => navigate('/financeiro')}
          data-testid="finance-summary-widget"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-grafite flex items-center gap-2">
              <Wallet className="w-5 h-5 text-carmesim" /> Saldo Financeiro {currentYear}
            </h3>
            <ArrowRight className="w-4 h-4 text-gray-400" />
          </div>
          <div className="grid grid-cols-3 gap-4 sm:gap-6">
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-medium">Receitas</div>
              <div className="font-mono text-xl sm:text-2xl font-bold text-green-600">{financeSummary.total_receitas.toLocaleString('pt')}</div>
              <div className="text-xs text-gray-400 mt-0.5">CVE</div>
            </div>
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-medium">Despesas</div>
              <div className="font-mono text-xl sm:text-2xl font-bold text-red-500">{financeSummary.total_despesas.toLocaleString('pt')}</div>
              <div className="text-xs text-gray-400 mt-0.5">CVE</div>
            </div>
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-medium">Resultado</div>
              <div className={`font-mono text-xl sm:text-2xl font-bold ${financeSummary.resultado_liquido >= 0 ? 'text-grafite' : 'text-orange-600'}`}>
                {financeSummary.resultado_liquido.toLocaleString('pt')}
              </div>
              <div className="text-xs text-gray-400 mt-0.5">CVE</div>
            </div>
          </div>
        </motion.div>
      )}

      {/* ===== MAIN GRID: Invoices + Polls ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-5">
        {/* Contribuicoes - Desconto em Folha */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-grafite" data-testid="contributions-title">Contribuicoes</h2>
            <span className="text-xs text-gray-400 uppercase tracking-wider hidden sm:block">Desconto em Folha</span>
          </div>
          <div className="text-center py-8">
            <div className="w-14 h-14 bg-green-50 rounded-2xl flex items-center justify-center mx-auto mb-3">
              <CheckCircle className="w-7 h-7 text-green-500" />
            </div>
            <p className="text-sm text-grafite font-semibold" data-testid="contributions-status">Tudo em dia!</p>
            <p className="text-xs text-gray-400 mt-1">Quotas descontadas automaticamente na folha salarial</p>
          </div>
        </motion.div>

        {/* Active Polls */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-grafite">Votacoes Abertas</h2>
            {activePolls.length > 0 && (
              <button onClick={() => navigate('/votacoes')} className="text-xs text-carmesim font-semibold uppercase tracking-wider hover:text-carmesim-dark">
                Ver todas
              </button>
            )}
          </div>
          {activePolls.length === 0 ? (
            <div className="text-center py-8">
              <div className="w-14 h-14 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <Vote className="w-7 h-7 text-gray-300" />
              </div>
              <p className="text-sm text-gray-400" data-testid="no-active-polls">Nenhuma votacao aberta</p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {activePolls.slice(0, 3).map((poll) => (
                <button key={poll.id} onClick={() => navigate('/votacoes')} className="w-full flex items-center gap-3 p-3.5 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors text-left" data-testid={`poll-${poll.id}`}>
                  <div className="w-9 h-9 bg-carmesim/10 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Vote className="w-4 h-4 text-carmesim" />
                  </div>
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

      {/* ===== UPCOMING EVENTS (Reference table style) ===== */}
      {upcomingEvents.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white border border-gray-200/80 rounded-2xl overflow-hidden"
        >
          <div className="flex items-center justify-between px-5 sm:px-6 py-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-grafite">Proximos Eventos</h2>
            <button
              onClick={() => navigate('/eventos')}
              className="text-xs text-carmesim hover:text-carmesim-dark uppercase tracking-wider font-semibold flex items-center gap-1"
            >
              Ver todos <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Desktop: Table style */}
          <div className="hidden md:block">
            <table className="w-full">
              <thead className="bg-gray-50/80">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Evento</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Data</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Local</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Hora</th>
                </tr>
              </thead>
              <tbody>
                {upcomingEvents.map((event, i) => (
                  <tr
                    key={event.id}
                    className="border-t border-gray-50 hover:bg-gray-50/50 cursor-pointer transition-colors"
                    onClick={() => navigate('/eventos')}
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-grafite rounded-xl flex flex-col items-center justify-center flex-shrink-0">
                          <span className="font-bold text-xs text-white leading-none">
                            {format(new Date(event.date), 'dd')}
                          </span>
                          <span className="text-xs text-carmesim uppercase font-bold leading-none mt-0.5">
                            {format(new Date(event.date), 'MMM', { locale: ptBR })}
                          </span>
                        </div>
                        <span className="font-medium text-sm text-grafite">{event.title}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {format(new Date(event.date), "dd 'de' MMMM", { locale: ptBR })}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1.5 text-sm text-gray-500">
                        <MapPin className="w-3.5 h-3.5 text-gray-400" />
                        {event.location}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 font-mono">
                      {format(new Date(event.date), 'HH:mm')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile: Card style */}
          <div className="md:hidden divide-y divide-gray-50">
            {upcomingEvents.map((event) => (
              <button
                key={event.id}
                className="flex items-start gap-3 p-4 hover:bg-gray-50 transition-colors text-left w-full"
                onClick={() => navigate('/eventos')}
              >
                <div className="w-11 h-11 bg-grafite rounded-xl flex flex-col items-center justify-center flex-shrink-0">
                  <span className="font-bold text-sm text-white leading-none">
                    {format(new Date(event.date), 'dd')}
                  </span>
                  <span className="text-xs text-carmesim uppercase font-bold leading-none mt-0.5">
                    {format(new Date(event.date), 'MMM', { locale: ptBR })}
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-sm text-grafite truncate">{event.title}</h3>
                  <div className="flex items-center gap-1.5 text-xs text-gray-400 mt-1">
                    <Clock className="w-3 h-3 flex-shrink-0" />
                    <span>{format(new Date(event.date), 'HH:mm')}</span>
                    <span className="text-gray-300 mx-0.5">|</span>
                    <MapPin className="w-3 h-3 flex-shrink-0" />
                    <span className="truncate">{event.location}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* ===== PERSONAL ACTIVITY REPORT ===== */}
      {personalReport && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white border border-gray-200/80 rounded-2xl overflow-hidden"
          data-testid="personal-report"
        >
          <div className="flex items-center justify-between px-5 sm:px-6 py-4 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-carmesim" />
              <h2 className="text-lg font-semibold text-grafite">A Minha Participacao</h2>
            </div>
            <span className="text-xs text-gray-400 uppercase tracking-wider hidden sm:block">Relatorio pessoal</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-px bg-gray-100">
            {[
              {
                icon: Calendar,
                label: 'Eventos',
                value: personalReport.events_attended,
                total: personalReport.total_events,
                color: 'bg-carmesim/10 text-carmesim',
              },
              {
                icon: Vote,
                label: 'Votacoes',
                value: personalReport.polls_voted,
                total: personalReport.total_polls,
                color: 'bg-blue-50 text-blue-600',
              },
              {
                icon: MessageSquare,
                label: 'Publicacoes',
                value: personalReport.wall_posts,
                total: null,
                color: 'bg-green-50 text-green-600',
              },
              {
                icon: ThumbsUp,
                label: 'Likes Recebidos',
                value: personalReport.likes_received,
                total: null,
                color: 'bg-pink-50 text-pink-600',
              },
              {
                icon: FolderKanban,
                label: 'Projetos',
                value: personalReport.projects_member,
                total: null,
                color: 'bg-purple-50 text-purple-600',
              },
              {
                icon: Image,
                label: 'Fotos',
                value: personalReport.photos_approved,
                total: personalReport.photos_submitted,
                color: 'bg-amber-50 text-amber-600',
              },
              {
                icon: Heart,
                label: 'Beneficios',
                value: personalReport.benefits_used,
                total: null,
                color: 'bg-red-50 text-red-500',
              },
              {
                icon: FileText,
                label: 'Documentos',
                value: personalReport.documents_available,
                total: null,
                color: 'bg-gray-50 text-gray-600',
              },
            ].map((item, idx) => (
              <div key={item.label} className="bg-white p-4 sm:p-5 flex flex-col items-center text-center" data-testid={`report-stat-${idx}`}>
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center mb-2.5 ${item.color}`}>
                  <item.icon className="w-4 h-4" />
                </div>
                <div className="font-bold text-xl text-grafite">{item.value}</div>
                {item.total !== null && item.total > 0 && (
                  <div className="text-xs text-gray-400 font-mono mt-0.5">de {item.total}</div>
                )}
                <div className="text-xs text-gray-500 mt-1">{item.label}</div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ===== ACTIVITY FEED ===== */}
      {recentActivity.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="bg-white border border-gray-200/80 rounded-2xl overflow-hidden"
          data-testid="activity-feed"
        >
          <div className="flex items-center justify-between px-5 sm:px-6 py-4 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-carmesim" />
              <h2 className="text-lg font-semibold text-grafite">Atividade Recente</h2>
            </div>
            <span className="text-xs text-gray-400 uppercase tracking-wider hidden sm:block">Ultimas atualizacoes</span>
          </div>

          <div className="divide-y divide-gray-50 max-h-[420px] overflow-y-auto">
            {recentActivity.map((item, i) => (
              <button
                key={`${item.type}-${i}`}
                onClick={() => item.link && navigate(item.link)}
                className="w-full flex items-start gap-3 px-5 sm:px-6 py-3.5 hover:bg-gray-50/80 transition-colors text-left"
                data-testid={`activity-item-${i}`}
              >
                <ActivityIcon type={item.type} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-grafite truncate">{item.title}</span>
                    <span className="text-xs text-gray-400 font-mono whitespace-nowrap">{timeAgo(item.created_at)}</span>
                  </div>
                  <p className="text-xs text-gray-500 truncate mt-0.5">{item.description}</p>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-gray-300 flex-shrink-0 mt-1" />
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* ===== NOTIFICATIONS ===== */}
      {unreadCount > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6 border-l-4 border-l-carmesim"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-carmesim" />
              <h3 className="font-semibold text-sm text-grafite">
                {unreadCount} {unreadCount === 1 ? 'notificacao nova' : 'notificacoes novas'}
              </h3>
            </div>
            <button
              onClick={() => navigate('/notificacoes')}
              className="text-xs text-carmesim hover:text-carmesim-dark uppercase tracking-wider font-semibold"
            >
              Ver todas
            </button>
          </div>
          <div className="space-y-2">
            {notifications.filter(n => !n.read).slice(0, 3).map((notif) => (
              <button
                key={notif.id}
                onClick={() => navigate('/notificacoes')}
                className="w-full flex items-center gap-3 p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors text-left"
              >
                <NotifIcon type={notif.type} />
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-grafite text-xs truncate">{notif.title}</div>
                  <div className="text-xs text-gray-400 truncate">{notif.message}</div>
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
