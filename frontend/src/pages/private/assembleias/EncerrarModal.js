import React from 'react';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../../../components/ui/dialog';
import { Input } from '../../../components/ui/input';
import { primaryBtn } from '../../../lib/buttonStyles';
import { fieldCls, labelCls, secondaryBtn } from './tokens';

export const EncerrarModal = ({
  open, onClose, titulo, actaId, setActaId, onSubmit, pending,
}) => (
  <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle>Encerrar assembleia</DialogTitle>
        <DialogDescription>
          Confirma o encerramento de “{titulo}”? Esta ação fixa as deliberações registadas.
        </DialogDescription>
      </DialogHeader>
      <div className="space-y-4">
        <div>
          <label className={labelCls}>ID do documento da acta (opcional)</label>
          <Input
            type="text"
            value={actaId}
            onChange={(e) => setActaId(e.target.value)}
            placeholder="ID do documento carregado"
            className={fieldCls}
            data-testid="encerrar-acta"
          />
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className={secondaryBtn}>Cancelar</button>
          <button
            onClick={onSubmit}
            disabled={pending}
            className={primaryBtn}
            data-testid="encerrar-confirm"
          >
            {pending ? 'A encerrar...' : 'Confirmar encerramento'}
          </button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
);
