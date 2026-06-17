import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Vote, ArrowRight } from 'lucide-react';
import { EmptyState } from '../../../components/EmptyState';

export const ActivePolls = ({ polls }) => {
  const navigate = useNavigate();
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6 animate-fade-up">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-grafite">Votacoes Abertas</h2>
        {polls.length > 0 && (
          <button onClick={() => navigate('/votacoes')} className="text-xs text-carmesim font-semibold hover:text-carmesim-dark">
            Ver todas
          </button>
        )}
      </div>
      {polls.length === 0 ? (
        <EmptyState
          icon={Vote}
          title="Nenhuma votacao aberta"
          testId="no-active-polls"
          className="border-0 shadow-none p-0 py-8"
        />
      ) : (
        <div className="space-y-2.5">
          {polls.slice(0, 3).map((poll) => (
            <button key={poll.id} onClick={() => navigate('/votacoes')} className="w-full flex items-center gap-3 p-3.5 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors text-left" data-testid={`poll-${poll.id}`}>
              <div className="w-9 h-9 bg-carmesim/10 rounded-xl flex items-center justify-center flex-shrink-0">
                <Vote className="w-4 h-4 text-carmesim" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-sm text-grafite truncate">{poll.title}</div>
                <div className="text-xs text-[#6B7280]">
                  Ate {new Date(poll.end_date).toLocaleDateString('pt')}
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
