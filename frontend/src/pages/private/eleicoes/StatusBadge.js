import React from 'react';
import { ELEICAO_STATUS_LABELS } from '../../../lib/governanceLabels';
import { STATUS_STYLE } from './tokens';

export const StatusBadge = ({ status }) => {
  const s = STATUS_STYLE[status] || STATUS_STYLE.preparacao;
  const Icon = s.icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ring-1 ${s.bg} ${s.fg} ${s.ring}`}
      data-testid={`status-${status}`}
    >
      <Icon className="w-3.5 h-3.5" aria-hidden="true" />
      {ELEICAO_STATUS_LABELS[status] || status}
    </span>
  );
};
