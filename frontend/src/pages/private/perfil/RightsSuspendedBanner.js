import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { formatDate } from './tokens';

export const RightsSuspendedBanner = ({ suspendedUntil, reason }) => (
  <div
    className="flex items-start gap-3 rounded-lg border border-[#FDE68A] bg-[#FFFBEB] p-4"
    role="alert"
    data-testid="rights-suspended-banner"
  >
    <AlertTriangle className="w-5 h-5 text-[#B45309] flex-shrink-0 mt-0.5" aria-hidden="true" />
    <div className="text-sm">
      <p className="font-semibold text-[#B45309]">Direitos suspensos</p>
      <p className="text-[#6B7280]">
        Os seus direitos de voto e elegibilidade estão suspensos até{' '}
        {formatDate(suspendedUntil) || suspendedUntil}.
        {reason ? ` Motivo: ${reason}.` : ''}
      </p>
    </div>
  </div>
);
