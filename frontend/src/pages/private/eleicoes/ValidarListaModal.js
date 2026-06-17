import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../../components/ui/dialog';
import { Textarea } from '../../../components/ui/textarea';
import { primaryBtn } from '../../../lib/buttonStyles';
import { cargoLabelFrom } from '../../../lib/governanceLabels';
import { fieldClass, labelClass, secondaryBtn } from './tokens';

export const ValidarListaModal = ({ lista, structure, onClose, onSubmit, pending }) => {
  const [motivo, setMotivo] = useState('');

  useEffect(() => { setMotivo(''); }, [lista]);

  const candidatos = lista?.candidatos || [];

  return (
    <Dialog open={!!lista} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Validar lista {lista?.letra}</DialogTitle>
          <DialogDescription>Confira os cargos cobertos e aceite a lista, ou rejeite-a indicando o motivo.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          {candidatos.length > 0 && (
            <div>
              <p className={labelClass}>Cargos na lista ({candidatos.length})</p>
              <ul className="max-h-44 overflow-y-auto rounded-md border border-[#E5E7EB] divide-y divide-[#F5F5F5] text-sm" data-testid="validar-candidatos">
                {candidatos.map((c, i) => (
                  <li key={c.user_id || c.slot_key || i} className="px-3 py-1.5 flex items-center justify-between gap-2">
                    <span className="text-grafite truncate">{cargoLabelFrom(structure, c.cargo)}</span>
                    {c.suplente && <span className="text-xs text-[#6B7280] shrink-0">suplente</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div>
            <label className={labelClass} htmlFor="rejeicao-motivo">Motivo (em caso de rejeição)</label>
            <Textarea
              id="rejeicao-motivo"
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              rows={2}
              maxLength={500}
              placeholder="Ex.: candidato inelegível"
              className={`${fieldClass} resize-none`}
              data-testid="rejeicao-motivo"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => onSubmit({ aceite: false, motivo: motivo.trim() || undefined })}
              disabled={pending}
              className={`${secondaryBtn} text-[#B91C1C] border-[#FECACA] hover:bg-[#FEF2F2]`}
              data-testid="rejeitar-lista-confirm"
            >
              Rejeitar
            </button>
            <button
              type="button"
              onClick={() => onSubmit({ aceite: true })}
              disabled={pending}
              className={primaryBtn}
              data-testid="aceitar-lista-confirm"
            >
              {pending ? 'A validar...' : 'Aceitar lista'}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
