import React from 'react';
import { SANCAO_TIPO_LABELS, SANCAO_STATUS_LABELS } from '../../../lib/governanceLabels';
import { TIPO_META, STATUS_META } from './tokens';

export const TipoBadge = ({ tipo }) => {
  const meta = TIPO_META[tipo] || TIPO_META.advertencia;
  const Icon = meta.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium ${meta.cls}`}>
      <Icon className="w-3 h-3" aria-hidden="true" />
      {SANCAO_TIPO_LABELS[tipo] || tipo}
    </span>
  );
};

export const StatusBadge = ({ status }) => {
  const meta = STATUS_META[status] || STATUS_META.proposta;
  const Icon = meta.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium ${meta.cls}`}>
      <Icon className="w-3 h-3" aria-hidden="true" />
      {SANCAO_STATUS_LABELS[status] || status}
    </span>
  );
};

export const Field = ({ label, children, hint }) => (
  <div>
    <label className="block text-xs font-medium text-gray-600 mb-1.5">{label}</label>
    {children}
    {hint && <p className="mt-1 text-xs text-[#6B7280]">{hint}</p>}
  </div>
);
