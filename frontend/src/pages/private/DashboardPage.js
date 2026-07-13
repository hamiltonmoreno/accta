import React, { Suspense, lazy, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import { pollsAPI, eventsAPI, activityAPI, reportAPI, rankingAPI, dashboardAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { Skeleton } from '../../components/ui/skeleton';

import { MONTH_LABELS, CATEGORY_LABELS } from './dashboard/tokens';
import { FinanceSummary } from './dashboard/FinanceSummary';
import { Contribuicoes } from './dashboard/Contribuicoes';
import { ActivePolls } from './dashboard/ActivePolls';
import { UpcomingEvents } from './dashboard/UpcomingEvents';
import { PersonalReport } from './dashboard/PersonalReport';
import { RankingTopN } from './dashboard/RankingTopN';
import { ActivityFeed } from './dashboard/ActivityFeed';
import { NotificationsList } from './dashboard/NotificationsList';
import { VidaAssociativa } from './dashboard/VidaAssociativa';
import { ProximasAssembleias } from './dashboard/ProximasAssembleias';
import { QuotasMes } from './dashboard/QuotasMes';

// Recharts (~334KB) só carregado para utilizadores com finance, via Suspense.
const FinanceCharts = lazy(() => import('./dashboard/FinanceCharts'));

export const DashboardPage = () => {
  const { user, isAdmin, isFinanceiro } = useAuth();
  const { notifications, unreadCount } = useNotifications();
  const navigate = useNavigate();

  const currentYear = new Date().getFullYear();
  // ponytail: hasFinance controla apenas AFORDÂNCIA DE CLIQUE (drill-down
  // para /financeiro) — não a visibilidade dos widgets. Spec 020 uniformizou
  // o conteúdo do Dashboard para todos os sócios.
  const hasFinance = isAdmin || isFinanceiro;

  // Dashboard universal (spec 020): 1 round-trip agregado para finance +
  // socios + atos + votacoes + assembleias.
  const overviewQuery = useQuery({
    queryKey: queryKeys.dashboard.overview(),
    queryFn: async () => (await dashboardAPI.overview()).data,
  });

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

  // Adaptador: extrai `financeSummary`/`dreData` do payload agregado para os
  // componentes FinanceSummary/FinanceCharts continuarem com a sua API estável.
  // (AdminStats foi retirado — os seus KPIs vivem agora em VidaAssociativa,
  // ProximasAssembleias e FinanceSummary.) Memoizado — o useMemo do
  // monthlyChartData depende de `dreData` e queremos estabilidade referencial.
  const overview = overviewQuery.data;
  const { financeSummary, dreData } = useMemo(() => {
    if (!overview) return { financeSummary: null, dreData: null };
    return {
      financeSummary: {
        total_receitas: overview.finance.receitas_ano,
        total_despesas: overview.finance.despesas_ano,
        resultado_liquido: overview.finance.resultado_ano,
      },
      dreData: {
        monthly: overview.finance.monthly.reduce((acc, p) => {
          acc[p.month] = { receitas: p.receitas, despesas: p.despesas };
          return acc;
        }, {}),
        despesas_por_categoria: overview.finance.despesas_por_categoria,
      },
    };
  }, [overview]);

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
  // dashboard (enquadramento positivo) — filtrados antes do slice. A `position`
  // é calculada sobre a lista COMPLETA (antes do filtro) para coincidir com a
  // posição contínua da página /ranking, que conta os inativos (spec 006 W1).
  const topEntries = (leaderboard?.entries || [])
    .map((e, i) => ({ ...e, position: i + 1 }))
    .filter((e) => e.status !== 'inativo')
    .slice(0, topN);
  const maxScore = topEntries.length ? Math.max(...topEntries.map((e) => e.score || 0), 1) : 1;

  // Loading apenas das queries criticas para o paint inicial.
  // personalReport carrega em background; ate chegar, render parcial e ok.
  const loading =
    pollsQuery.isLoading ||
    upcomingEventsQuery.isLoading ||
    recentActivityQuery.isLoading ||
    overviewQuery.isLoading;

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

      {/* Charts grid — recharts em chunk lazy. Universal em conteúdo (spec 020);
          drill-down "Ver detalhes" só é passado se o utilizador tiver privilégio. */}
      {dreData && (
        <Suspense fallback={
          <div className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6 h-[320px] flex items-center justify-center">
            <div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
          </div>
        }>
          <FinanceCharts
            monthlyChartData={monthlyChartData}
            expensePieData={expensePieData}
            currentYear={currentYear}
            onViewAll={hasFinance ? () => navigate('/financeiro') : undefined}
          />
        </Suspense>
      )}

      {/* Financial summary banner — universal em conteúdo, clique só a hasFinance */}
      {financeSummary && (
        <FinanceSummary financeSummary={financeSummary} currentYear={currentYear} clickable={hasFinance} />
      )}

      {/* Vida associativa + quotas do mês (spec 020 US3) — universal */}
      {overview && (
        <>
          <QuotasMes valor={overview.finance.quotas_mes} clickable={hasFinance} />
          <VidaAssociativa
            socios={overview.socios}
            atos={overview.atos}
            votacoes={overview.votacoes}
            canViewAtos={hasFinance}
          />
          <ProximasAssembleias proximas={overview.assembleias.proximas} />
        </>
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
