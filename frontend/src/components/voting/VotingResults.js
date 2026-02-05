import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { TrendingUp } from 'lucide-react';

export const VotingResults = ({ poll, results }) => {
  if (!results || !results.results) return null;

  const totalVotes = results.total_votes;
  
  // Prepare data for chart
  const chartData = poll.options.map((option) => {
    const voteCount = results.results[option.id] || 0;
    const percentage = totalVotes > 0 ? (voteCount / totalVotes) * 100 : 0;
    
    return {
      name: option.label,
      votes: voteCount,
      percentage: percentage,
    };
  });

  // Sort by votes descending
  chartData.sort((a, b) => b.votes - a.votes);

  const COLORS = ['#00FF9C', '#0A1F44', '#6B7280', '#9CA3AF'];

  return (
    <div className="mt-6 pt-6 border-t border-slate-200">
      {/* Summary */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="font-outfit font-semibold text-xl text-primary mb-1">Resultados</div>
          <div className="text-sm text-slate-500">Total de {totalVotes} voto{totalVotes !== 1 ? 's' : ''}</div>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-accent/10 rounded-lg">
          <TrendingUp className="w-4 h-4 text-accent" />
          <span className="font-mono text-sm font-semibold text-accent">
            {totalVotes} participações
          </span>
        </div>
      </div>

      {/* Bar Chart */}
      <div className="mb-6" style={{ height: '300px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical">
            <XAxis type="number" />
            <YAxis dataKey="name" type="category" width={150} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-3 rounded-lg shadow-lg border border-slate-200">
                      <div className="font-manrope font-semibold text-primary mb-1">{data.name}</div>
                      <div className="text-sm text-slate-600">
                        {data.votes} votos ({data.percentage.toFixed(1)}%)
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="votes" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Detailed List */}
      <div className="space-y-3">
        {chartData.map((data, index) => (
          <div key={index} className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <span className="font-manrope font-medium text-primary">{data.name}</span>
                <span className="font-mono text-sm text-slate-500">
                  {data.votes} voto{data.votes !== 1 ? 's' : ''} ({data.percentage.toFixed(1)}%)
                </span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${data.percentage}%`,
                    backgroundColor: COLORS[index % COLORS.length],
                  }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Winner Highlight */}
      {chartData.length > 0 && chartData[0].votes > 0 && (
        <div className="mt-6 p-4 bg-accent/5 rounded-lg border border-accent/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-accent rounded-full flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-primary" />
            </div>
            <div>
              <div className="text-sm text-slate-500 uppercase tracking-wider mb-1">Opção Mais Votada</div>
              <div className="font-outfit font-semibold text-lg text-primary">
                {chartData[0].name} ({chartData[0].percentage.toFixed(1)}%)
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
