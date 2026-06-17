import React from 'react';
import { Users, CheckCircle, Calendar, DollarSign } from 'lucide-react';
import { StatCard } from './widgets';

export const AdminStats = ({ stats, financeSummary }) => (
  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
    <StatCard
      title="Total Socios"
      value={stats.total_users}
      icon={Users}
      iconBg="bg-grafite/10 text-grafite"
    />
    <StatCard
      title="Socios Ativos"
      value={stats.active_users}
      icon={CheckCircle}
      iconBg="bg-[#F0FDF4] text-[#15803D]"
    />
    <StatCard
      title="Eventos Ativos"
      value={stats.active_events}
      icon={Calendar}
      iconBg="bg-carmesim/10 text-carmesim"
    />
    <StatCard
      title="Receita Anual"
      value={financeSummary ? `${(financeSummary.total_receitas / 1000).toFixed(0)}k` : `${stats.total_revenue.toFixed(0)}`}
      icon={DollarSign}
      iconBg="bg-[#EFF6FF] text-[#1D4ED8]"
      change={financeSummary && financeSummary.total_receitas > 0 ? Math.round((financeSummary.resultado_liquido / financeSummary.total_receitas) * 100) : undefined}
      changeLabel="margem"
    />
  </div>
);
