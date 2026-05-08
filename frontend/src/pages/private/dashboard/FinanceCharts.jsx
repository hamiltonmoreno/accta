import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3, ArrowRight } from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

const CHART_COLORS = ['#C7202F', '#3A3A3A', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6'];

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

const FinanceCharts = ({ monthlyChartData, expensePieData, currentYear, onViewAll }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-5">
      <div className="lg:col-span-3">
        <ChartCard
          title="Evolucao Financeira"
          subtitle={`Receitas vs Despesas - ${currentYear}`}
          delay={0.25}
          action={
            <button
              onClick={onViewAll}
              className="text-xs text-carmesim font-semibold uppercase tracking-wider hover:text-carmesim-dark flex items-center gap-1"
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
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradDespesas" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#C7202F" stopOpacity={0.1} />
                    <stop offset="95%" stopColor="#C7202F" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="Receitas" stroke="#10b981" strokeWidth={2.5} fill="url(#gradReceitas)" />
                <Area type="monotone" dataKey="Despesas" stroke="#C7202F" strokeWidth={2.5} fill="url(#gradDespesas)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      </div>

      <div className="lg:col-span-2">
        <ChartCard
          title="Distribuicao de Despesas"
          subtitle="Por categoria"
          delay={0.3}
        >
          <div className="h-[280px]" data-testid="expense-chart" style={{ minWidth: 0 }}>
            {expensePieData.length === 0 ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <BarChart3 className="w-10 h-10 text-gray-200 mx-auto mb-2" />
                  <p className="text-sm text-gray-400">Sem despesas registradas</p>
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
