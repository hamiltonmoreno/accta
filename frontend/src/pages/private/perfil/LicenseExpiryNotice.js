import React from 'react';
import { AlertTriangle, CheckCircle2, Clock } from 'lucide-react';
import { formatDate, toLocalDate } from './tokens';

// Aviso de validade da licença — ajuda o sócio a renovar a tempo (sem multa).
// Verde (>60 dias) → âmbar (≤60) → carmesim (expirada/urgente).
export const LicenseExpiryNotice = ({ expiry }) => {
  const exp = toLocalDate(expiry);
  if (!exp) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.round((exp - today) / 86400000);

  let cfg;
  if (days < 0) {
    cfg = {
      cls: 'border-carmesim/30 bg-carmesim/5 text-carmesim',
      Icon: AlertTriangle,
      msg: `Licença expirada há ${Math.abs(days)} dia(s). Renove com urgência para evitar multa.`,
    };
  } else if (days === 0) {
    cfg = {
      cls: 'border-carmesim/30 bg-carmesim/5 text-carmesim',
      Icon: AlertTriangle,
      msg: 'A sua licença expira hoje. Renove para evitar multa.',
    };
  } else if (days <= 60) {
    cfg = {
      cls: 'border-[#FDE68A] bg-[#FFFBEB] text-[#B45309]',
      Icon: Clock,
      msg: `A sua licença expira em ${days} dia(s) (${formatDate(expiry)}). Renove a tempo para evitar multa.`,
    };
  } else {
    cfg = {
      cls: 'border-[#BBF7D0] bg-[#F0FDF4] text-[#15803D]',
      Icon: CheckCircle2,
      msg: `Licença válida até ${formatDate(expiry)}.`,
    };
  }
  const { Icon } = cfg;
  return (
    <div className={`flex items-start gap-2 rounded-lg border p-3 mt-3 ${cfg.cls}`} role="status" data-testid="license-expiry-notice">
      <Icon className="w-4 h-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <p className="text-xs font-medium">{cfg.msg}</p>
    </div>
  );
};
