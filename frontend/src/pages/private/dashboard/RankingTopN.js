import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Medal, Trophy } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { EmptyState } from '../../../components/EmptyState';
import { Skeleton } from '../../../components/ui/skeleton';
import { CARGO_LABELS_FALLBACK } from '../../../lib/governanceLabels';

export const RankingTopN = ({
  topEntries, maxScore, topN, leaderboard, leaderboardLoading, currentUserId,
}) => {
  const navigate = useNavigate();
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl overflow-hidden animate-fade-up" data-testid="ranking-widget">
      <div className="flex items-center justify-between px-5 sm:px-6 py-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <Trophy className="w-4 h-4 text-grafite" />
          <h2 className="text-lg font-semibold text-grafite">Ranking de Atuacao</h2>
        </div>
        <span className="text-xs text-[#6B7280] uppercase tracking-wider hidden sm:block">Top {topN}</span>
      </div>

      {leaderboardLoading ? (
        <div className="p-5 sm:p-6 space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-12 rounded-xl" />
          ))}
        </div>
      ) : topEntries.length === 0 ? (
        <EmptyState
          icon={Trophy}
          title="Ranking ainda nao calculado"
          description="A atuacao dos socios aparece aqui apos o primeiro calculo."
          testId="ranking-empty"
          className="border-0 shadow-none p-0 py-10"
        />
      ) : (
        <>
          <div className="divide-y divide-gray-50">
            {topEntries.map((entry) => {
              const isMe = entry.user_id === currentUserId;
              const cargoLabel = entry.cargo && entry.cargo !== 'socio' ? CARGO_LABELS_FALLBACK[entry.cargo] : null;
              const barPct = Math.max(4, Math.round(((entry.score || 0) / maxScore) * 100));
              return (
                <div
                  key={entry.user_id}
                  className={`flex items-center gap-3 px-5 sm:px-6 py-3 ${isMe ? 'bg-carmesim/5' : ''}`}
                  data-testid={`ranking-row-${entry.rank}`}
                >
                  <div className="w-8 flex items-center justify-center flex-shrink-0">
                    {entry.rank <= 3 ? (
                      <Medal
                        className={`w-5 h-5 ${entry.rank === 1 ? 'text-carmesim' : 'text-[#6B7280]'}`}
                        aria-hidden="true"
                      />
                    ) : (
                      <span className="text-sm font-semibold text-[#6B7280] font-mono">{entry.rank}</span>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-grafite truncate">
                        {entry.member_name}{isMe && ' (eu)'}
                      </span>
                    </div>
                    {cargoLabel && <div className="text-xs text-[#6B7280] truncate">{cargoLabel}</div>}
                    <div className="mt-1.5 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${entry.rank === 1 ? 'bg-carmesim' : 'bg-gray-300'}`}
                        style={{ width: `${barPct}%` }}
                      />
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="font-bold text-base text-grafite leading-none">{entry.score}</div>
                    <div className="text-[10px] text-[#6B7280] mt-0.5">pts</div>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex items-center justify-between gap-3 px-5 sm:px-6 py-3 border-t border-gray-100">
            <span className="text-xs text-[#6B7280]" data-testid="ranking-computed-at">
              {leaderboard?.computed_at
                ? `Atualizado ${format(new Date(leaderboard.computed_at), "dd 'de' MMMM, HH:mm", { locale: ptBR })}`
                : ''}
            </span>
            <button
              onClick={() => navigate('/ranking')}
              className="text-xs text-carmesim hover:text-carmesim-dark font-semibold flex items-center gap-1 flex-shrink-0 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-1"
              data-testid="ranking-ver-completo"
            >
              Ver ranking completo <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </>
      )}
    </div>
  );
};
