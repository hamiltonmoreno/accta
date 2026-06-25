import React, { useState, useEffect } from 'react';
import { Vote, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { pollsAPI } from '../../utils/api';

export const VotingInterface = ({ poll, onVoteSuccess }) => {
  const [selected, setSelected] = useState(null);
  const [voting, setVoting] = useState(false);
  // Inicializa a partir do campo has_voted devolvido pelo backend (se disponível).
  // O ?? false garante retrocompatibilidade enquanto o backend ainda não devolve o campo.
  const [voted, setVoted] = useState(poll.has_voted ?? false);
  // Re-sincroniza ao trocar de sondagem (o useState só corre no mount): sem
  // isto, o estado "votado" arrastava-se para a próxima poll. Depende só de
  // poll.id para não desfazer o setVoted(true) optimista após votar.
  useEffect(() => {
    setVoted(poll.has_voted ?? false);
  }, [poll.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleVote = async () => {
    if (!selected) {
      toast.error('Selecione uma opção');
      return;
    }

    setVoting(true);
    try {
      await pollsAPI.vote({ poll_id: poll.id, vote_option: selected });
      setVoted(true);
      toast.success('Voto registado!');
      setTimeout(() => onVoteSuccess && onVoteSuccess(), 1500);
    } catch (error) {
      const msg = error.response?.data?.detail || 'Erro ao votar';
      toast.error(msg);
      // Defesa adicional: 409 = já votou (duplicado); marca estado sem alarme extra.
      if (error.response?.status === 409 || msg.includes('já votou')) setVoted(true);
    } finally {
      setVoting(false);
    }
  };

  if (voted) {
    return (
      <div className="border-t border-gray-200 pt-6 mt-6">
        <div className="flex items-center gap-3 p-4 bg-[#F0FDF4] rounded-lg border border-[#BBF7D0]">
          <CheckCircle className="w-6 h-6 text-[#166534]" />
          <div>
            <div className="font-semibold text-grafite">Voto Registado</div>
            <div className="text-sm text-gray-600">Obrigado pela participação!</div>
          </div>
        </div>
      </div>
    );
  }

  const options = poll.options || [];
  const optionLabel = (opt) => opt.label || opt.text || `Opção ${opt.id}`;

  return (
    <div className="border-t border-gray-200 pt-6 mt-6">
      <div className="space-y-3 mb-6">
        {options.map((opt) => {
          const isSelected = selected === opt.id;
          return (
            <label
              key={opt.id}
              className={`flex items-center gap-3 p-4 rounded-lg cursor-pointer transition ${
                isSelected
                  ? 'bg-[#166534]/10 border-2 border-[#166534]'
                  : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
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
              <span className="flex-1">{optionLabel(opt)}</span>
              {isSelected && <CheckCircle className="w-5 h-5 text-[#166534]" />}
            </label>
          );
        })}
      </div>

      <button
        onClick={handleVote}
        disabled={!selected || voting}
        className="w-full bg-floresta text-white hover:bg-floresta-dark h-12 rounded-lg font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        data-testid="vote-button"
      >
        {voting ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            A registar...
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
