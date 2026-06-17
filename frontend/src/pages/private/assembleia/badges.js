import React from 'react';
import { ASSEMBLEIA_STATUS_LABELS, SESSION_PHASE_LABELS } from '../../../lib/governanceLabels';
import { STATUS_STYLES } from './tokens';

export const StatusBadge = ({ status }) => {
  const s = STATUS_STYLES[status] || STATUS_STYLES.rascunho;
  const { Icon } = s;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${s.cls}`}>
      <Icon className="w-3.5 h-3.5" aria-hidden="true" />
      {ASSEMBLEIA_STATUS_LABELS[status] || status}
    </span>
  );
};

export const PhaseBadge = ({ phase }) => (
  <span className="inline-flex items-center px-2.5 py-1 rounded-full border border-[#E5E7EB] bg-[#F5F5F5] text-xs font-medium text-[#3A3A3A]">
    {SESSION_PHASE_LABELS[phase] || phase}
  </span>
);
