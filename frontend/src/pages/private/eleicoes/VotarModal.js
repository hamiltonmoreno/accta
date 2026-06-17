import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../../components/ui/dialog';
import { primaryBtn } from '../../../lib/buttonStyles';
import { secondaryBtn } from './tokens';

export const VotarModal = ({ open, onClose, onSubmit, pending, listas }) => {
  const [voto, setVoto] = useState(null);

  useEffect(() => { if (open) setVoto(null); }, [open]);

  const aceites = listas.filter((l) => l.estado === 'aceite');

  // Radio buttons ficam como <input> raw — shadcn Input não suporta `type="radio"` (é estilizado para text).
  const Option = ({ id, children }) => (
    <label
      className={`flex items-center gap-3 px-3 py-2.5 rounded-md border cursor-pointer transition-colors ${voto === id ? 'border-carmesim bg-carmesim/5' : 'border-[#E5E7EB] hover:bg-[#F5F5F5]'}`}
    >
      <input
        type="radio"
        name="voto"
        checked={voto === id}
        onChange={() => setVoto(id)}
        className="text-carmesim focus:ring-carmesim/40"
      />
      <span className="text-sm text-grafite">{children}</span>
    </label>
  );

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Votar</DialogTitle>
          <DialogDescription>O voto é secreto. Selecione uma lista, voto em branco ou nulo.</DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          {aceites.map((l) => (
            <Option key={l.id} id={l.id}>
              <span className="font-semibold mr-1">Lista {l.letra}</span>{l.nome || ''}
            </Option>
          ))}
          <Option id="branco">Voto em branco</Option>
          <Option id="nulo">Voto nulo</Option>
        </div>
        <div className="flex justify-end gap-2 pt-3">
          <button type="button" onClick={onClose} className={secondaryBtn}>Cancelar</button>
          <button
            type="button"
            onClick={() => onSubmit({ voto })}
            disabled={!voto || pending}
            className={primaryBtn}
            data-testid="votar-confirm"
          >
            {pending ? 'A registar...' : 'Registar voto'}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
