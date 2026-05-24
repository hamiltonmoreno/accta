import React from 'react';
import { BarChart3, ArrowRight } from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

const CHART_COLORS = ['#C7202F', '#3A3A3A', '#D97706', '#2563EB', '#16A34A', '#6B7280'];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-lg px-4 py-3 text-xs">
      <p className="font-semibold text-grafite mb-1.5">{label}</p>
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center gap-2 mb-0.5">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-gray-500">{entry.name}:</span>
          <span className="font-bold text-grafite">{entry.value.toLocaleString('pt')} CVE</span>
        </div>
      ))}
    </div>
  );
};

const renderPieLabel = ({ percent }) => {
  if (percent < 0.05) return null;
  return `${(percent * 100).toFixed(0)}%`;
};

// delay agora dropped — o stagger entre os 2 charts era cosmetico (0.25s/0.3s)
// CSS keyframe (animate-fade-up) suficiente — framer removido em Sprint 9.
const ChartCard = ({ title, subtitle, children, action }) => (
  <div className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6 animate-fade-up">
    <div className="flex items-start justify-between mb-5">
      <div>
        <h3 className="text-lg font-semibold text-grafite">{title}</h3>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
    {children}
  </div>
);

const FinanceCharts = ({ monthlyChartData, expensePieData, currentYear, onViewAll }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-5">
      <div className="lg:col-span-3">
        <ChartCard
          title="Evolucao Financeira"
          subtitle={`Receitas vs Despesas - ${currentYear}`}
          action={
            <button
              onClick={onViewAll}
              className="text-xs text-carmesim font-semibold hover:text-carmesim-dark flex items-center gap-1"
              data-testid="chart-view-all"
            >
              Ver tudo <ArrowRight className="w-3.5 h-3.5" />
            </button>
          }
        >
          <div className="h-[280px] -ml-2" data-testid="monthly-chart" style={{ minWidth: 0 }}>
            <ResponsiveContainer width="100%" height="100%" minWidth={100}>
              <AreaChart data={monthlyChartData}>
                <defs>
                  <linearGradient id="gradReceitas" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#16A34A" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#16A34A" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradDespesas" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#C7202F" stopOpacity={0.1} />
                    <stop offset="95%" stopColor="#C7202F" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#6B7280' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#6B7280' }} axisLine={false} tickLine={false} tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="Receitas" stroke="#16A34A" strokeWidth={2.5} fill="url(#gradReceitas)" />
                <Area type="monotone" dataKey="Despesas" stroke="#C7202F" strokeWidth={2.5} fill="url(#gradDespesas)" />
              </AreaChart>
            </ResponsiveContainer>
            <table className="sr-only">
              <caption>Receitas e despesas por mes</caption>
              <thead>
                <tr><th scope="col">Mes</th><th scope="col">Receitas (CVE)</th><th scope="col">Despesas (CVE)</th></tr>
              </thead>
              <tbody>
                {monthlyChartData.map((d) => (
                  <tr key={d.name}>
                    <th scope="row">{d.name}</th>
                    <td>{d.Receitas}</td>
                    <td>{d.Despesas}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ChartCard>
      </div>

      <div className="lg:col-span-2">
        <ChartCard
          title="Distribuicao de Despesas"
          subtitle="Por categoria"
        >
          <div className="h-[280px]" data-testid="expense-chart" style={{ minWidth: 0 }}>
            {expensePieData.length === 0 ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <BarChart3 className="w-10 h-10 text-gray-200 mx-auto mb-2" />
                  <p className="text-sm text-[#6B7280]">Sem despesas registadas</p>
                </div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={expensePieData}
                    cx="50%"
                    cy="45%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={3}
                    dataKey="value"
                    label={renderPieLabel}
                    labelLine={false}
                  >
                    {expensePieData.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => [`${v.toLocaleString('pt')} CVE`, '']} />
                  <Legend
                    verticalAlign="bottom"
                    iconType="circle"
                    iconSize={8}
                    formatter={(value) => <span className="text-xs text-gray-600">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </ChartCard>
      </div>
    </div>
  );
};

export default FinanceCharts;
