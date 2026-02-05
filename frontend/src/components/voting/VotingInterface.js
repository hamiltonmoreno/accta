import React, { useState } from 'react';
import { Vote, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { pollsAPI } from '../utils/api';

export const VotingInterface = ({ poll, onVoteSuccess }) => {
  const [selected, setSelected] = useState(null);
  const [voting, setVoting] = useState(false);
  const [voted, setVoted] = useState(false);

  const handleVote = async () => {
    if (!selected) {
      toast.error('Selecione uma opção');
      return;
    }

    setVoting(true);
    try {
      await pollsAPI.vote({ poll_id: poll.id, vote_option: selected });
      setVoted(true);
      toast.success('Voto registrado!');
      setTimeout(() => onVoteSuccess && onVoteSuccess(), 1500);
    } catch (error) {
      const msg = error.response?.data?.detail || 'Erro ao votar';
      toast.error(msg);
      if (msg.includes('já votou')) setVoted(true);
    } finally {
      setVoting(false);
    }
  };

  if (voted) {
    return (
      <div className="border-t border-slate-200 pt-6 mt-6">
        <div className="flex items-center gap-3 p-4 bg-accent/5 rounded-lg border border-accent/20">
          <CheckCircle className="w-6 h-6 text-accent" />
          <div>
            <div className="font-semibold text-primary">Voto Registrado</div>
            <div className="text-sm text-slate-600">Obrigado pela participação!</div>
          </div>
        </div>
      </div>
    );
  }

  const options = poll.options || [];

  return (
    <div className="border-t border-slate-200 pt-6 mt-6">
      <div className="space-y-3 mb-6">
        {options.map((opt) => {
          const isSelected = selected === opt.id;
          return (
            <label
              key={opt.id}
              className={`flex items-center gap-3 p-4 rounded-lg cursor-pointer transition ${
                isSelected
                  ? 'bg-accent/10 border-2 border-accent'
                  : 'bg-slate-50 border-2 border-transparent hover:bg-slate-100'
              }`}
            >
              <input
                type="radio"
                name={`poll-${poll.id}`}
                checked={isSelected}
                onChange={() => setSelected(opt.id)}
                className="w-5 h-5"
                data-testid={`option-${opt.id}`}
              />
              <span className="flex-1">{opt.label}</span>
              {isSelected && <CheckCircle className="w-5 h-5 text-accent" />}
            </label>
          );
        })}
      </div>

      <button
        onClick={handleVote}
        disabled={!selected || voting}
        className="w-full bg-primary text-white h-12 rounded-lg font-bold disabled:opacity-50 flex items-center justify-center gap-2"
        data-testid="vote-button"
      >
        {voting ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Registrando...
          </>
        ) : (
          <>
            <Vote className="w-5 h-5" />
            CONFIRMAR VOTO
          </>
        )}
      </button>
    </div>
  );
};
