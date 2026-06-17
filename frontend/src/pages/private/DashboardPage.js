import React, { Suspense, lazy, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import { statsAPI, pollsAPI, eventsAPI, financesAPI, activityAPI, reportAPI, rankingAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { Skeleton } from '../../components/ui/skeleton';

import { MONTH_LABELS, CATEGORY_LABELS } from './dashboard/tokens';
import { AdminStats } from './dashboard/AdminStats';
import { FinanceSummary } from './dashboard/FinanceSummary';
import { Contribuicoes } from './dashboard/Contribuicoes';
import { ActivePolls } from './dashboard/ActivePolls';
import { UpcomingEvents } from './dashboard/UpcomingEvents';
import { PersonalReport } from './dashboard/PersonalReport';
import { RankingTopN } from './dashboard/RankingTopN';
import { ActivityFeed } from './dashboard/ActivityFeed';
import { NotificationsList } from './dashboard/NotificationsList';

// Recharts (~334KB) só carregado para utilizadores com finance, via Suspense.
const FinanceCharts = lazy(() => import('./dashboard/FinanceCharts'));

export const DashboardPage = () => {
  const { user, isAdmin, isFinanceiro } = useAuth();
  const { notifications, unreadCount } = useNotifications();
  const navigate = useNavigate();

  const currentYear = new Date().getFullYear();
  const hasFinance = isAdmin || isFinanceiro;

  // Queries always-on para todos os utilizadores.
  // Cada uma corre em paralelo (sem await sequencial); cache cross-page;
  // refetch independente em window focus.
  const pollsQuery = useQuery({
    queryKey: queryKeys.polls.list(),
    queryFn: async () => (await pollsAPI.getAll()).data,
  });

  const upcomingEventsQuery = useQuery({
    queryKey: queryKeys.events.upcoming(),
    queryFn: async () => (await eventsAPI.getUpcoming()).data,
  });

  const recentActivityQuery = useQuery({
    queryKey: queryKeys.activity.recent(),
    queryFn: async () => (await activityAPI.getRecent(15)).data,
  });

  const personalReportQuery = useQuery({
    queryKey: queryKeys.report.personal(),
    queryFn: async () => (await reportAPI.getPersonal()).data,
  });

  // Ranking de atuação do próprio (ao vivo): score + posição + pontos por tile.
  const myRankingQuery = useQuery({
    queryKey: queryKeys.ranking.me(String(currentYear)),
    queryFn: async () => (await rankingAPI.me(String(currentYear))).data,
  });

  // Leaderboard Top-N (lê o snapshot). `enabled` só depois de sabermos que o
  // ranking está ligado — evita um request quando a feature está desativada.
  const leaderboardEnabled = !!myRankingQuery.data?.enabled;
  const leaderboardQuery = useQuery({
    queryKey: queryKeys.ranking.leaderboard(String(currentYear)),
    // limit 50 (máximo) cobre `top_n_dashboard` configurável (até 50) e dá folga
    // para filtrar inativos client-side sem ficar abaixo do Top-N.
    queryFn: async () => (await rankingAPI.leaderboard({ period: String(currentYear), limit: 50 })).data,
    enabled: leaderboardEnabled,
    retry: false, // 403 (visibility=direcao_only) → esconde o widget sem 3 retries
  });

  // Queries gated por hasFinance — `enabled` evita request desnecessario
  // para socios. Quando false, isLoading=false e data=undefined.
  const statsQuery = useQuery({
    queryKey: ['stats'],
    queryFn: async () => (await statsAPI.get()).data,
    enabled: hasFinance,
  });

  const financeSummaryQuery = useQuery({
    queryKey: queryKeys.transactions.summary(currentYear, undefined),
    queryFn: async () => (await financesAPI.getSummary({ year: currentYear })).data,
    enabled: hasFinance,
  });

  const dreQuery = useQuery({
    queryKey: ['finance', 'dre', currentYear],
    queryFn: async () => (await financesAPI.getDRE(currentYear)).data,
    enabled: hasFinance,
  });

  const activePolls = (pollsQuery.data || []).filter((p) => p.status === 'aberta');
  const upcomingEvents = (upcomingEventsQuery.data || []).slice(0, 3);
  const recentActivity = recentActivityQuery.data || [];
  const personalReport = personalReportQuery.data;
  const myRanking = myRankingQuery.data;
  const rankingOn = !!myRanking?.enabled;
  const rankBreakdown = myRanking?.breakdown || {};
  const leaderboard = leaderboardQuery.data;
  const topN = leaderboard?.top_n_dashboard || 5;
  // D3: membros `inativo` entram no ranking geral mas ficam FORA do Top-N do
  // dashboard (enquadramento positivo) — filtrados antes do slice.
  const topEntries = (leaderboard?.entries || []).filter((e) => e.status !== 'inativo').slice(0, topN);
  const maxScore = topEntries.length ? Math.max(...topEntries.map((e) => e.score || 0), 1) : 1;
  const stats = statsQuery.data;
  const financeSummary = financeSummaryQuery.data;
  const dreData = dreQuery.data;

  // Loading apenas das queries criticas para o paint inicial.
  // personalReport carrega em background; ate chegar, render parcial e ok.
  const loading =
    pollsQuery.isLoading ||
    upcomingEventsQuery.isLoading ||
    recentActivityQuery.isLoading ||
    (hasFinance && (statsQuery.isLoading || financeSummaryQuery.isLoading || dreQuery.isLoading));

  // Prepare chart data — memoizado por dreData (evita recriar arrays a cada render).
  const monthlyChartData = useMemo(() => (
    dreData ? Object.entries(dreData.monthly).map(([month, d]) => ({
      name: MONTH_LABELS[parseInt(month) - 1],
      Receitas: d.receitas,
      Despesas: d.despesas,
    })) : []
  ), [dreData]);

  const expensePieData = useMemo(() => (
    dreData ? Object.entries(dreData.despesas_por_categoria)
      .filter(([, v]) => v > 0)
      .map(([cat, val]) => ({
        name: CATEGORY_LABELS[cat] || cat,
        value: val,
      })) : []
  ), [dreData]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-9 w-64 mb-2" />
          <Skeleton className="h-4 w-72" />
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-2xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-5">
          <Skeleton className="h-52 rounded-2xl" />
          <Skeleton className="h-52 rounded-2xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="page-title" data-testid="dashboard-title">
          Bem-vindo, {user?.name?.split(' ')[0]}
        </h1>
        <p className="page-subtitle">Resumo da sua conta e atividades</p>
      </div>

      {/* Admin/Financeiro: stat cards */}
      {hasFinance && stats && (
        <AdminStats stats={stats} financeSummary={financeSummary} />
      )}

      {/* Charts grid — recharts em chunk lazy só carrega para finance users */}
      {hasFinance && dreData && (
        <Suspense fallback={
          <div className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6 h-[320px] flex items-center justify-center">
            <div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
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

      {/* Financial summary banner */}
      {hasFinance && financeSummary && (
        <FinanceSummary financeSummary={financeSummary} currentYear={currentYear} />
      )}

      {/* Main grid: Contribuicoes + Active Polls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-5">
        <Contribuicoes />
        <ActivePolls polls={activePolls} />
      </div>

      {upcomingEvents.length > 0 && <UpcomingEvents events={upcomingEvents} />}

      {personalReport && (
        <PersonalReport
          personalReport={personalReport}
          myRanking={myRanking}
          rankingOn={rankingOn}
          rankBreakdown={rankBreakdown}
        />
      )}

      {/* isError esconde o widget quando o leaderboard e restrito (direcao_only → 403). */}
      {rankingOn && !leaderboardQuery.isError && (
        <RankingTopN
          topEntries={topEntries}
          maxScore={maxScore}
          topN={topN}
          leaderboard={leaderboard}
          leaderboardLoading={leaderboardQuery.isLoading}
          currentUserId={user?.id}
        />
      )}

      {recentActivity.length > 0 && <ActivityFeed items={recentActivity} />}

      {unreadCount > 0 && (
        <NotificationsList unreadCount={unreadCount} notifications={notifications} />
      )}
    </div>
  );
};

export default DashboardPage;
