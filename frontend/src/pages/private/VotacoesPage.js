import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { pollsAPI } from '../../utils/api';
import { Vote, CheckCircle, Clock, BarChart3, AlertCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { PollCard } from '../../components/voting/PollCard';
import { VotingInterface } from '../../components/voting/VotingInterface';
import { VotingResults } from '../../components/voting/VotingResults';

export const VotacoesPage = () => {
  const { user, isAtivo } = useAuth();
  const [polls, setPolls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState({});
  const [loadingResults, setLoadingResults] = useState({});
  const [showResults, setShowResults] = useState({});

  useEffect(() => {
    loadPolls();
  }, []);

  const loadPolls = async () => {
    setLoading(true);
    try {
      const response = await pollsAPI.getAll();
      setPolls(response.data);
    } catch (error) {
      console.error('Erro ao carregar votações:', error);
      // Se não conseguir carregar, pelo menos para o loading
      setPolls([]);
    } finally {
      setLoading(false);
    }
  };

  const loadResults = async (pollId) => {
    setLoadingResults(prev => ({ ...prev, [pollId]: true }));
    try {
      const response = await pollsAPI.getResults(pollId);
      setResults(prev => ({ ...prev, [pollId]: response.data }));
      setShowResults(prev => ({ ...prev, [pollId]: true }));
    } catch (error) {
      console.error('Erro ao carregar resultados:', error);
    } finally {
      setLoadingResults(prev => ({ ...prev, [pollId]: false }));
    }
  };

  const toggleResults = (pollId) => {
    if (showResults[pollId]) {
      setShowResults(prev => ({ ...prev, [pollId]: false }));
    } else {
      if (!results[pollId]) {
        loadResults(pollId);
      } else {
        setShowResults(prev => ({ ...prev, [pollId]: true }));
      }
    }
  };

  const openPolls = polls.filter(p => p.status === 'aberta');
  const closedPolls = polls.filter(p => p.status === 'fechada');

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-outfit font-bold text-4xl text-primary mb-2" data-testid="polls-title">
          Votações
        </h1>
        <p className="text-slate-600">Participe das decisões da associação</p>
      </div>

      {/* Status Alert for Inactive Members */}
      {!isAtivo && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-technical rounded-xl p-6 border-2 border-alert"
          data-testid="voting-restricted"
        >
          <div className="flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-alert flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-outfit font-semibold text-lg text-alert mb-2">Votação Restrita</h3>
              <p className="text-slate-600">
                Apenas sócios com status <strong>ativo</strong> podem participar de votações. 
                Por favor, regularize sua situação junto à administração para poder exercer seus direitos de voto.
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Open Polls Section */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-outfit font-semibold text-2xl text-primary flex items-center gap-3">
            <Clock className="w-7 h-7 text-accent" />
            Votações Abertas
          </h2>
          {openPolls.length > 0 && (
            <span className="px-4 py-2 bg-accent/10 text-accent rounded-full text-sm font-mono font-semibold">
              {openPolls.length} ativa{openPolls.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {openPolls.length === 0 ? (
          <div className="card-technical rounded-xl p-12 text-center" data-testid="no-open-polls">
            <Vote className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500 font-medium mb-1">Nenhuma votação aberta no momento</p>
            <p className="text-sm text-slate-400">Você será notificado quando novas votações forem criadas</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {openPolls.map((poll, index) => (
              <motion.div
                key={poll.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <PollCard poll={poll} isActive={true}>
                  {isAtivo ? (
                    <VotingInterface poll={poll} onVoteSuccess={loadPolls} />
                  ) : (
                    <div className="border-t border-slate-200 pt-6 mt-6">
                      <div className="text-center py-4 text-slate-500 text-sm">
                        Regularize seu status para participar desta votação
                      </div>
                    </div>
                  )}
                </PollCard>
              </motion.div>
            ))}
          </div>
        )}
      </section>

      {/* Closed Polls Section */}
      {closedPolls.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-outfit font-semibold text-2xl text-primary flex items-center gap-3">
              <CheckCircle className="w-7 h-7 text-slate-400" />
              Votações Encerradas
            </h2>
            <span className="px-4 py-2 bg-slate-100 text-slate-500 rounded-full text-sm font-mono font-semibold">
              {closedPolls.length} encerrada{closedPolls.length !== 1 ? 's' : ''}
            </span>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {closedPolls.map((poll, index) => (
              <motion.div
                key={poll.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <PollCard poll={poll} isActive={false}>
                  <div className="border-t border-slate-200 pt-6 mt-6">
                    <button
                      onClick={() => toggleResults(poll.id)}
                      disabled={loadingResults[poll.id]}
                      className="flex items-center gap-2 text-sm text-primary hover:text-primary/80 font-mono uppercase tracking-wider transition-colors disabled:opacity-50"
                      data-testid={`view-results-${poll.id}`}
                    >
                      {loadingResults[poll.id] ? (
                        <>
                          <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
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
              </motion.div>
            ))}
          </div>
        </section>
      )}

      {/* Info Box */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="card-technical rounded-xl p-6 bg-accent/5 border-accent/20"
      >
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-accent rounded-lg flex items-center justify-center flex-shrink-0">
            <Vote className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h3 className="font-outfit font-semibold text-lg text-primary mb-2">Como Funciona</h3>
            <ul className="space-y-2 text-sm text-slate-600">
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-accent rounded-full mt-2" />
                <span>Cada sócio ativo pode votar uma única vez por votação</span>
              </li>
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-accent rounded-full mt-2" />
                <span>Seu voto é anônimo e confidencial</span>
              </li>
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-accent rounded-full mt-2" />
                <span>Os resultados são publicados após o encerramento da votação</span>
              </li>
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-accent rounded-full mt-2" />
                <span>Você será notificado quando novas votações forem abertas</span>
              </li>
            </ul>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
