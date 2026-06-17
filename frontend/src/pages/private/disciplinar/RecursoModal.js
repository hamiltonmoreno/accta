import React from 'react';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../../../components/ui/dialog';
import { primaryBtn } from '../../../lib/buttonStyles';
import { Field } from './widgets';
import { cancelBtn, inputCls } from './tokens';

export const RecursoModal = ({
  open, onClose, form, setForm, onSubmit, pending,
}) => (
  <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle>Submeter recurso</DialogTitle>
        <DialogDescription>Recurso de decisão (apenas multa ou perda de direitos).</DialogDescription>
      </DialogHeader>
      <div className="space-y-4">
        <Field label="Fundamentação do recurso">
          <textarea
            value={form.fundamentacao}
            onChange={(e) => setForm({ fundamentacao: e.target.value })}
            rows={4}
            maxLength={2000}
            placeholder="Apresente os fundamentos do recurso."
            className={`${inputCls} resize-none`}
            data-testid="recurso-fundamentacao"
          />
        </Field>
        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className={cancelBtn}>Cancelar</button>
          <button
            onClick={onSubmit}
            disabled={!form.fundamentacao.trim() || pending}
            className={primaryBtn}
            data-testid="recurso-confirm"
          >
            {pending ? 'A submeter...' : 'Submeter recurso'}
          </button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
);
