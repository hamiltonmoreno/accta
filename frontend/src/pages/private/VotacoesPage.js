import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { pollsAPI } from '../../utils/api';
import { Vote, CheckCircle, Clock, BarChart3, AlertCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { queryKeys } from '../../lib/queryClient';
import { PollCard } from '../../components/voting/PollCard';
import { VotingInterface } from '../../components/voting/VotingInterface';
import { VotingResults } from '../../components/voting/VotingResults';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';

export const VotacoesPage = () => {
  const { isAtivo } = useAuth();
  const qc = useQueryClient();
  const [results, setResults] = useState({});
  const [loadingResults, setLoadingResults] = useState({});
  const [showResults, setShowResults] = useState({});

  const { data: polls = [], isLoading: loading } = useQuery({
    queryKey: queryKeys.polls.list(),
    queryFn: async () => {
      const res = await pollsAPI.getAll();
      return res.data;
    },
  });

  // Resultados sao lazy (so quando o user clica "Ver Resultados") e dinamicos
  // por pollId. Usamos qc.fetchQuery imperativo + cachear localmente em
  // showResults para evitar varios useQuery dinamicos com `enabled`.
  const loadResults = async (pollId) => {
    setLoadingResults((prev) => ({ ...prev, [pollId]: true }));
    try {
      const data = await qc.fetchQuery({
        queryKey: ['polls', pollId, 'results'],
        queryFn: async () => (await pollsAPI.getResults(pollId)).data,
      });
      setResults((prev) => ({ ...prev, [pollId]: data }));
      setShowResults((prev) => ({ ...prev, [pollId]: true }));
    } finally {
      setLoadingResults((prev) => ({ ...prev, [pollId]: false }));
    }
  };

  const toggleResults = (pollId) => {
    if (showResults[pollId]) {
      setShowResults((prev) => ({ ...prev, [pollId]: false }));
    } else if (!results[pollId]) {
      loadResults(pollId);
    } else {
      setShowResults((prev) => ({ ...prev, [pollId]: true }));
    }
  };

  const onVoteSuccess = () => qc.invalidateQueries({ queryKey: queryKeys.polls.list() });

  const openPolls = polls.filter((p) => p.status === 'aberta');
  const closedPolls = polls.filter((p) => ['encerrada', 'fechada'].includes(p.status));

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="grid grid-cols-1 gap-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="page-title" data-testid="polls-title">
          Votações
        </h1>
        <p className="page-subtitle">Participe das decisões da associação</p>
      </div>

      {/* Status Alert for Inactive Members */}
      {!isAtivo && (
        <div className="card-technical p-4 sm:p-6 border-l-4 border-l-[#D97706] bg-[#FFFBEB] animate-fade-up"
          data-testid="voting-restricted">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-[#D97706] flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-sm text-[#B45309] mb-1">Votação Restrita</h3>
              <p className="text-xs sm:text-sm text-gray-600">
                Apenas sócios com status <strong>ativo</strong> podem participar de votações.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Open Polls Section */}
      <section>
        <div className="flex items-center justify-between mb-4 sm:mb-6">
          <h2 className="font-semibold text-lg sm:text-2xl text-grafite flex items-center gap-2 sm:gap-3">
            <Clock className="w-5 sm:w-7 h-5 sm:h-7 text-carmesim" />
            Votações Abertas
          </h2>
          {openPolls.length > 0 && (
            <span className="px-2.5 sm:px-4 py-1 sm:py-2 bg-carmesim/10 text-carmesim rounded-full text-xs sm:text-sm font-mono font-semibold">
              {openPolls.length} ativa{openPolls.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {openPolls.length === 0 ? (
          <EmptyState
            icon={Vote}
            title="Nenhuma votação aberta no momento"
            description="Será notificado quando novas votações forem criadas"
            testId="no-open-polls"
          />
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {openPolls.map((poll, index) => (
              <div className="animate-fade-up"
                key={poll.id}>
                <PollCard poll={poll} isActive={true}>
                  {isAtivo ? (
                    <VotingInterface poll={poll} onVoteSuccess={onVoteSuccess} />
                  ) : (
                    <div className="border-t border-gray-200 pt-6 mt-6">
                      <div className="text-center py-4 text-gray-500 text-sm">
                        Regularize seu status para participar desta votação
                      </div>
                    </div>
                  )}
                </PollCard>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Closed Polls Section */}
      {closedPolls.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4 sm:mb-6">
            <h2 className="font-semibold text-lg sm:text-2xl text-grafite flex items-center gap-2 sm:gap-3">
              <CheckCircle className="w-5 sm:w-7 h-5 sm:h-7 text-gray-400" />
              Votações Encerradas
            </h2>
            <span className="px-2.5 sm:px-4 py-1 sm:py-2 bg-gray-100 text-gray-500 rounded-full text-xs sm:text-sm font-mono font-semibold">
              {closedPolls.length}
            </span>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {closedPolls.map((poll, index) => (
              <div className="animate-fade-up"
                key={poll.id}>
                <PollCard poll={poll} isActive={false}>
                  <div className="border-t border-gray-200 pt-6 mt-6">
                    <button
                      onClick={() => toggleResults(poll.id)}
                      disabled={loadingResults[poll.id]}
                      className="flex items-center gap-2 text-sm text-grafite hover:text-grafite/80 font-semibold transition-colors disabled:opacity-50"
                      data-testid={`view-results-${poll.id}`}
                    >
                      {loadingResults[poll.id] ? (
                        <>
                          <div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
                          <span>Carregando...</span>
                        </>
                      ) : (
                        <>
                          <BarChart3 className="w-4 h-4" />
                          <span>{showResults[poll.id] ? 'Ocultar' : 'Ver'} Resultados</span>
                        </>
                      )}
                    </button>

                    {showResults[poll.id] && results[poll.id] && (
                      <VotingResults poll={poll} results={results[poll.id]} />
                    )}
                  </div>
                </PollCard>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Info Box */}
      <div className="card-technical rounded-xl p-6 bg-carmesim/5 border-carmesim/20 animate-fade-up">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-grafite rounded-lg flex items-center justify-center flex-shrink-0">
            <Vote className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="font-sans font-semibold text-lg text-grafite mb-2">Como Funciona</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-carmesim rounded-full mt-2" />
                <span>Cada sócio ativo pode votar uma única vez por votação</span>
              </li>
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-carmesim rounded-full mt-2" />
                <span>Seu voto é anônimo e confidencial</span>
              </li>
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-carmesim rounded-full mt-2" />
                <span>Os resultados são publicados após o encerramento da votação</span>
              </li>
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-carmesim rounded-full mt-2" />
                <span>Será notificado quando novas votações forem abertas</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
