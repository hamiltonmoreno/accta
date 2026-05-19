import React, { useState } from 'react';
import { Vote } from 'lucide-react';
import { toast } from 'sonner';
import { pollsAPI } from '../utils/api';

export const PollVoteForm = ({ poll, isAtivo, onVoteSuccess }) => {
  const [selectedOption, setSelectedOption] = useState(null);
  const [voting, setVoting] = useState(false);

  const handleVote = async () => {
    if (selectedOption === null) return;

    setVoting(true);
    try {
      await pollsAPI.vote({
        poll_id: poll.id,
        vote_option: selectedOption,
      });
      toast.success('Voto registrado com sucesso!');
      setSelectedOption(null);
      if (onVoteSuccess) onVoteSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao votar');
    } finally {
      setVoting(false);
    }
  };

  if (!isAtivo) return null;

  return (
    <div className="border-t border-[#E5E7EB] pt-6 mt-6">
      <div className="space-y-3 mb-4">
        {poll.options.map((option) => (
          <label
            key={option.id}
            className="flex items-center gap-3 p-4 bg-[#F5F5F5] rounded-lg cursor-pointer hover:bg-[#E5E7EB] transition-colors"
          >
            <input
              type="radio"
              name={`poll-${poll.id}`}
              value={option.id}
              checked={selectedOption === option.id}
              onChange={() => setSelectedOption(option.id)}
              className="w-5 h-5 text-carmesim focus:ring-carmesim"
              data-testid={`option-${option.id}`}
            />
            <span className="font-manrope font-medium text-primary">{option.label}</span>
          </label>
        ))}
      </div>

      <button
        onClick={handleVote}
        disabled={selectedOption === null || voting}
        className="bg-primary text-white hover:bg-primary/90 h-12 px-6 rounded-lg uppercase tracking-wider font-bold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        data-testid="vote-button"
      >
        {voting ? (
          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
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
