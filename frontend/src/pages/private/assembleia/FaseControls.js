import React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import { assembleiasAPI } from '../../../utils/api';
import { SESSION_PHASE_LABELS } from '../../../lib/governanceLabels';
import { PHASE_ORDER, secondaryBtn } from './tokens';
import { PhaseBadge } from './badges';

export const FaseControls = ({ assembleia, snapshot, refetchSnap }) => {
  const qc = useQueryClient();
  const phase = snapshot?.phase || assembleia.session_phase || 'fechada';
  const idx = PHASE_ORDER.indexOf(phase);
  const next = idx >= 0 && idx < PHASE_ORDER.length - 1 ? PHASE_ORDER[idx + 1] : null;

  const setFaseMut = useMutation({
    mutationFn: (target) => assembleiasAPI.setFase(assembleia.id, { session_phase: target }),
    onSuccess: () => {
      toast.success('Fase actualizada');
      qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id] });
      refetchSnap?.();
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro a transitar fase'),
  });

  return (
    <div className="flex flex-wrap items-center gap-2">
      <PhaseBadge phase={phase} />
      {next && (
        <button
          type="button"
          className={secondaryBtn}
          disabled={setFaseMut.isPending}
          onClick={() => setFaseMut.mutate(next)}
        >
          Avançar para {SESSION_PHASE_LABELS[next]}
          <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
        </button>
      )}
    </div>
  );
};
