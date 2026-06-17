import React from 'react';
import { CheckCircle2, Gavel, XCircle } from 'lucide-react';
import { VoteStat } from './widgets';
import { Skeleton } from '../../../components/ui/skeleton';
import { MAIORIA_LABELS } from '../../../lib/governanceLabels';

export const DeliberacoesList = ({ deliberacoes, loading }) => (
  <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6">
    <h3 className="text-sm font-semibold text-grafite flex items-center gap-2 mb-4">
      <Gavel className="w-4 h-4 text-[#6B7280]" aria-hidden="true" />Deliberações
    </h3>
    {loading ? (
      <Skeleton className="h-24 w-full rounded-md" />
    ) : deliberacoes.length === 0 ? (
      <p className="text-sm text-[#6B7280]">Ainda não há deliberações registadas.</p>
    ) : (
      <ul className="space-y-3" data-testid="deliberacoes-list">
        {deliberacoes.map((d) => (
          <li key={d.id} className="rounded-md border border-[#E5E7EB] p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-semibold text-grafite">{d.ponto}</p>
                {d.descricao && <p className="text-sm text-[#6B7280] mt-0.5">{d.descricao}</p>}
              </div>
              {d.aprovado ? (
                <span className="shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-[#BBF7D0] bg-[#F0FDF4] text-[#15803D] text-xs font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />Aprovada
                </span>
              ) : (
                <span className="shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-[#FECACA] bg-[#FEF2F2] text-[#B91C1C] text-xs font-medium">
                  <XCircle className="w-3.5 h-3.5" aria-hidden="true" />Rejeitada
                </span>
              )}
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[#6B7280]">
              <span>{MAIORIA_LABELS[d.tipo_maioria] || d.tipo_maioria}</span>
              {d.base_calculo != null && <span>· Base: {d.base_calculo}</span>}
              {d.threshold != null && <span>· Limiar: {d.threshold}</span>}
              {d.source_article && <span>· {d.source_article}</span>}
            </div>
            <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-2 max-w-xs">
              <VoteStat label="A favor" value={d.votos_favor} color="text-[#15803D]" />
              <VoteStat label="Contra" value={d.votos_contra} color="text-[#B91C1C]" />
              <VoteStat label="Abstenções" value={d.abstencoes} color="text-[#6B7280]" />
            </div>
          </li>
        ))}
      </ul>
    )}
  </div>
);
