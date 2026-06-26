import React from 'react';
import { Crown, Medal, Award } from 'lucide-react';

/**
 * Distinção de posição do ranking — FONTE ÚNICA (spec 006, Decisão D2).
 * 1.º/2.º/3.º distinguem-se por FORMA (ícone diferente) E por tom, dentro da
 * paleta ACCTA (sem metálicos): 1.º Coroa Carmesim, 2.º Medalha Grafite, 3.º
 * Award muted. 4.º+ mostra a **posição contínua a negrito**. A distinção nunca é
 * só por cor (FR-005) — o ícone difere de forma e há um rótulo sr-only.
 *
 * `rank` é a posição CONTÍNUA na lista (1,2,3,4,5…), não o rank do servidor (que
 * tem empates: 4,4,4). O cálculo da posição vive em quem renderiza a lista.
 *
 * Props: `rank` (int — posição contínua), `size` ('sm'|'lg').
 */
const TOP3 = {
  1: { Icon: Crown, cls: 'text-carmesim' },
  2: { Icon: Medal, cls: 'text-grafite' },
  3: { Icon: Award, cls: 'text-[#6B7280]' },
};

export const RankBadge = ({ rank, size = 'sm' }) => {
  const cls = size === 'lg' ? 'w-7 h-7' : 'w-5 h-5';
  const top = TOP3[rank];
  if (top) {
    const { Icon, cls: color } = top;
    return (
      <>
        <Icon className={`${cls} ${color}`} aria-hidden="true" />
        <span className="sr-only">{rank}.º lugar</span>
      </>
    );
  }
  return <span className="text-sm font-bold text-grafite font-mono">{rank}</span>;
};

export default RankBadge;
