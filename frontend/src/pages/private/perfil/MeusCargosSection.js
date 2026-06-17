import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { History } from 'lucide-react';
import { cargosAPI } from '../../../utils/api';
import { queryKeys } from '../../../lib/queryClient';
import { cargoLabelFrom } from '../../../lib/governanceLabels';
import { formatDate } from './tokens';

// Timeline só-leitura do percurso do próprio sócio na associação. Mostra o
// label do cargo (a key canónica é interna), com marcação de suplente.
export const MeusCargosSection = ({ userId, structure }) => {
  const { data: history = [] } = useQuery({
    queryKey: queryKeys.cargos.history(userId),
    queryFn: async () => (await cargosAPI.history(userId)).data.cargo_history,
    enabled: !!userId,
  });
  if (history.length === 0) return null;
  return (
    <div className="card-technical p-5 animate-fade-up">
      <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">
        <History className="w-3 h-3 inline mr-1" aria-hidden="true" /> Os Meus Cargos e Mandatos
      </h3>
      <ul className="space-y-2" data-testid="meus-cargos-timeline">
        {history.map((m) => (
          <li key={m.id || `${m.cargo}-${m.inicio}`} className="flex items-center justify-between text-sm">
            <span className="text-grafite font-medium">
              {m.label || cargoLabelFrom(structure, m.cargo)}
              {m.suplente && <span className="ml-1.5 text-xs text-[#6B7280]">(suplente)</span>}
            </span>
            <span className="font-mono text-xs text-[#6B7280]">
              {formatDate(m.inicio) || '—'} → {m.fim ? formatDate(m.fim) : 'presente'}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};
