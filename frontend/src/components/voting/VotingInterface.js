import React, { useState } from 'react';
import { Vote, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { pollsAPI } from '../utils/api';

export const VotingInterface = ({ poll, onVoteSuccess }) => {
  const [selectedOption, setSelectedOption] = useState(null);
  const [voting, setVoting] = useState(false);
  const [hasVoted, setHasVoted] = useState(false);

  const handleVote = async () => {
    if (selectedOption === null) {
      toast.error('Por favor, selecione uma opção');
      return;
    }

    setVoting(true);
    try {
      await pollsAPI.vote({
        poll_id: poll.id,
        vote_option: selectedOption,
      });
      
      setHasVoted(true);
      toast.success('Voto registrado com sucesso!', {
        description: 'Obrigado pela sua participação!',
      });
      
      if (onVoteSuccess) {
        setTimeout(() => onVoteSuccess(), 1500);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Erro ao registrar voto';
      toast.error(errorMsg);
      
      if (errorMsg.includes('já votou')) {
        setHasVoted(true);
      }
    } finally {
      setVoting(false);
    }
  };

  if (hasVoted) {
    return (
      <div className="border-t border-slate-200 pt-6 mt-6">
        <div className="flex items-center gap-3 p-4 bg-accent/5 rounded-lg border border-accent/20">
          <CheckCircle className="w-6 h-6 text-accent flex-shrink-0" />
          <div>
            <div className="font-manrope font-semibold text-primary">Voto Registrado</div>
            <div className="text-sm text-slate-600">Você já participou desta votação. Obrigado!</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="border-t border-slate-200 pt-6 mt-6">
      <div className="space-y-3 mb-6">
        {poll.options.map((option) => (
          <label
            key={option.id}
            className={`flex items-center gap-3 p-4 rounded-lg cursor-pointer transition-all ${
              selectedOption === option.id
                ? 'bg-accent/10 border-2 border-accent'
                : 'bg-slate-50 border-2 border-transparent hover:bg-slate-100'
            }`}
          >
            <input
              type="radio"
              name={`poll-${poll.id}`}
              value={option.id}
              checked={selectedOption === option.id}
              onChange={() => setSelectedOption(option.id)}
              className="w-5 h-5 text-accent focus:ring-accent"
              data-testid={`option-${option.id}`}
            />
            <span className="font-manrope font-medium text-primary flex-1">{option.label}</span>
            {selectedOption === option.id && (
              <CheckCircle className="w-5 h-5 text-accent" />
            )}
          </label>
        ))}
      </div>

      <button
        onClick={handleVote}
        disabled={selectedOption === null || voting}
        className="w-full bg-primary text-white hover:bg-primary/90 h-12 px-6 rounded-lg uppercase tracking-wider font-bold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        data-testid="vote-button"
      >
        {voting ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <span>Registrando...</span>
          </>
        ) : (
          <>
            <Vote className="w-5 h-5" />
            Confirmar Voto
          </>
        )}
      </button>
    </div>
  );
};
