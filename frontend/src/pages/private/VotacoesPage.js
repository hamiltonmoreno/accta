import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { pollsAPI } from '../../utils/api';
import { Vote, CheckCircle, Clock, BarChart3 } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { useAuth } from '../../contexts/AuthContext';
import { PollVoteForm } from '../../components/PollVoteForm';
import { PollResults } from '../../components/PollResults';

export const VotacoesPage = () => {
  const { isAtivo } = useAuth();
  const [polls, setPolls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState({});
  const [loadingResults, setLoadingResults] = useState({});

  useEffect(() => {
    loadPolls();
  }, []);

  const loadPolls = async () => {
    try {
      const response = await pollsAPI.getAll();
      setPolls(response.data);
    } catch (error) {
      console.error('Erro:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadResults = async (pollId) => {
    setLoadingResults(prev => ({ ...prev, [pollId]: true }));
    try {
      const response = await pollsAPI.getResults(pollId);
      setResults(prev => ({ ...prev, [pollId]: response.data }));
    } catch (error) {
      console.error('Erro:', error);
    } finally {
      setLoadingResults(prev => ({ ...prev, [pollId]: false }));
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
      <div>
        <h1 className="font-outfit font-bold text-4xl text-primary mb-2" data-testid="polls-title">
          Votações
        </h1>
        <p className="text-slate-600">Participe das decisões da associação</p>
      </div>

      {!isAtivo && (
        <div className="card-technical rounded-xl p-6 border-2 border-alert" data-testid="voting-restricted">
          <div className="flex items-start gap-4">
            <Vote className="w-6 h-6 text-alert flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-outfit font-semibold text-lg text-alert mb-2">Votação Restrita</h3>
              <p className="text-slate-600">
                Apenas sócios com status ativo podem participar de votações.
              </p>
            </div>
          </div>
        </div>
      )}

      <section>
        <h2 className="font-outfit font-semibold text-2xl text-primary mb-6 flex items-center gap-3">
          <Clock className="w-7 h-7 text-accent" />
          Votações Abertas
        </h2>

        {openPolls.length === 0 ? (
          <div className="card-technical rounded-xl p-12 text-center" data-testid="no-open-polls">
            <p className="text-slate-500">Nenhuma votação aberta no momento</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {openPolls.map((poll, idx) => (
              <motion.div
                key={poll.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="card-technical rounded-xl p-6"
                data-testid={`poll-${poll.id}`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-outfit font-semibold text-2xl text-primary mb-2">{poll.title}</h3>
                    <p className="text-slate-600 mb-4">{poll.description}</p>
                    <div className="flex items-center gap-4 text-sm text-slate-500 font-mono">
                      <span>Início: {format(new Date(poll.start_date), 'dd/MM/yyyy', { locale: ptBR })}</span>
                      <span>Término: {format(new Date(poll.end_date), 'dd/MM/yyyy', { locale: ptBR })}</span>
                    </div>
                  </div>
                  <span className="px-4 py-2 bg-accent/10 text-accent rounded-full text-xs font-mono uppercase tracking-wider">
                    Aberta
                  </span>
                </div>

                <PollVoteForm poll={poll} isAtivo={isAtivo} onVoteSuccess={loadPolls} />
              </motion.div>
            ))}
          </div>
        )}
      </section>

      {closedPolls.length > 0 && (
        <section>
          <h2 className="font-outfit font-semibold text-2xl text-primary mb-6 flex items-center gap-3">
            <CheckCircle className="w-7 h-7 text-slate-400" />
            Votações Encerradas
          </h2>

          <div className="grid grid-cols-1 gap-6">
            {closedPolls.map((poll, idx) => (
              <motion.div
                key={poll.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="card-technical rounded-xl p-6 opacity-75"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-outfit font-semibold text-xl text-primary mb-2">{poll.title}</h3>
                    <p className="text-slate-600 text-sm">{poll.description}</p>
                  </div>
                  <span className="px-4 py-2 bg-slate-100 text-slate-500 rounded-full text-xs font-mono uppercase tracking-wider">
                    Encerrada
                  </span>
                </div>

                <button
                  onClick={() => loadResults(poll.id)}
                  disabled={loadingResults[poll.id]}
                  className="flex items-center gap-2 text-sm text-primary hover:text-primary/80 font-mono uppercase tracking-wider disabled:opacity-50"
                  data-testid={`view-results-${poll.id}`}
                >
                  {loadingResults[poll.id] ? (
                    <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <BarChart3 className="w-4 h-4" />
                  )}
                  {results[poll.id] ? 'Ocultar Resultados' : 'Ver Resultados'}
                </button>

                <PollResults poll={poll} results={results[poll.id]} />
              </motion.div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
