import React from 'react';
import { ShieldAlert } from 'lucide-react';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../../../components/ui/dialog';
import { primaryBtn } from '../../../lib/buttonStyles';
import { TipoBadge } from './widgets';
import { cancelBtn } from './tokens';

export const AplicarModal = ({
  open, onClose, target, onSubmit, pending,
}) => (
  <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle>Aplicar sanção</DialogTitle>
        <DialogDescription>Esta ação enacta a sanção e produz efeitos imediatos. Confirma?</DialogDescription>
      </DialogHeader>
      <div className="space-y-4">
        <div className="rounded-md border border-[#FECACA] bg-[#FEF2F2] p-3 text-sm text-[#B91C1C]">
          <p className="flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 mt-0.5 shrink-0" aria-hidden="true" />
            <span>
              Perda de direitos suspende o voto do membro; a expulsão inativa a conta.
              Estes efeitos só podem ser revertidos por anulação do processo.
            </span>
          </p>
        </div>
        {target && (
          <div className="flex flex-wrap items-center gap-2 text-sm text-grafite">
            <TipoBadge tipo={target.tipo} />
            <span className="text-[#6B7280]">Membro:</span> <span className="font-mono text-xs">{target.user_id}</span>
          </div>
        )}
        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className={cancelBtn}>Cancelar</button>
          <button
            onClick={onSubmit}
            disabled={pending}
            className={primaryBtn}
            data-testid="aplicar-confirm"
          >
            {pending ? 'A aplicar...' : 'Confirmar e aplicar'}
          </button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
);
