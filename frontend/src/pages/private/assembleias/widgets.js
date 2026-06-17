import React from 'react';
import { Calendar, CheckCircle2, ShieldCheck, XCircle } from 'lucide-react';
import {
  ASSEMBLEIA_TIPO_LABELS,
  ASSEMBLEIA_STATUS_LABELS,
} from '../../../lib/governanceLabels';

// Estilo do badge de estado da assembleia — cor + ícone + texto (nunca só cor).
const STATUS_STYLES = {
  rascunho: { cls: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]', Icon: Calendar },
  convocada: { cls: 'bg-[#EFF6FF] text-[#1D4ED8] border-[#BFDBFE]', Icon: Calendar },
  em_curso: { cls: 'bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]', Icon: ShieldCheck },
  encerrada: { cls: 'bg-[#F0FDF4] text-[#15803D] border-[#BBF7D0]', Icon: CheckCircle2 },
  anulada: { cls: 'bg-[#FEF2F2] text-[#B91C1C] border-[#FECACA]', Icon: XCircle },
};

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

export const TipoBadge = ({ tipo }) => (
  <span className="inline-flex items-center px-2.5 py-1 rounded-full border border-[#E5E7EB] bg-white text-xs font-medium text-grafite">
    {ASSEMBLEIA_TIPO_LABELS[tipo] || tipo}
  </span>
);

// Linha de contagem de votos no detalhe de uma deliberação.
export const VoteStat = ({ label, value, color }) => (
  <div className="text-center">
    <p className={`text-lg font-bold ${color}`}>{value ?? 0}</p>
    <p className="text-xs text-[#6B7280]">{label}</p>
  </div>
);
