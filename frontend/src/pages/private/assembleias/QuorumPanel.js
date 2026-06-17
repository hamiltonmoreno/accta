import React from 'react';
import { CheckCircle2, Gavel, Users, XCircle } from 'lucide-react';
import { VoteStat } from './widgets';
import { Skeleton } from '../../../components/ui/skeleton';

export const QuorumPanel = ({ quorum }) => (
  <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6" data-testid="quorum-panel">
    <h3 className="text-sm font-semibold text-grafite flex items-center gap-2 mb-4">
      <Users className="w-4 h-4 text-[#6B7280]" aria-hidden="true" />Quórum
    </h3>
    {!quorum ? (
      <Skeleton className="h-20 w-full rounded-md" />
    ) : (
      <>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <VoteStat label="Eleitores" value={quorum.eligible_voters_count} color="text-grafite" />
          <VoteStat label="Presentes" value={quorum.present_count} color="text-grafite" />
          <VoteStat label="Poder de voto presente" value={quorum.present_voting_power} color="text-grafite" />
          <VoteStat label="Chamada" value={quorum.chamada_actual} color="text-grafite" />
        </div>
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <div className="px-3 py-2 rounded-md bg-[#F5F5F5] border border-[#E5E7EB] flex items-center justify-between">
            <span className="text-[#6B7280]">Quórum 1ª chamada</span>
            <span className="font-semibold text-grafite">{quorum.quorum_required_primeira ?? '—'}</span>
          </div>
          <div className="px-3 py-2 rounded-md bg-[#F5F5F5] border border-[#E5E7EB] flex items-center justify-between">
            <span className="text-[#6B7280]">Quórum 2ª chamada</span>
            <span className="font-semibold text-grafite">{quorum.quorum_required_segunda ?? '—'}</span>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {quorum.quorum_met ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[#BBF7D0] bg-[#F0FDF4] text-[#15803D] text-xs font-medium">
              <CheckCircle2 className="w-4 h-4" aria-hidden="true" />Quórum atingido
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[#FECACA] bg-[#FEF2F2] text-[#B91C1C] text-xs font-medium">
              <XCircle className="w-4 h-4" aria-hidden="true" />Sem quórum
            </span>
          )}
          {quorum.pode_deliberar ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[#BBF7D0] bg-[#F0FDF4] text-[#15803D] text-xs font-medium">
              <Gavel className="w-4 h-4" aria-hidden="true" />Pode deliberar
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[#FDE68A] bg-[#FFFBEB] text-[#B45309] text-xs font-medium">
              <XCircle className="w-4 h-4" aria-hidden="true" />Não pode deliberar
            </span>
          )}
        </div>
      </>
    )}
  </div>
);
