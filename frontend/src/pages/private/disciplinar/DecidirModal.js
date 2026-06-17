import React from 'react';
import { ShieldAlert } from 'lucide-react';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../../../components/ui/dialog';
import { primaryBtn } from '../../../lib/buttonStyles';
import { SANCAO_TIPO_LABELS } from '../../../lib/governanceLabels';
import { Field } from './widgets';
import { cancelBtn, inputCls } from './tokens';

export const DecidirModal = ({
  open, onClose, target, form, setForm, valid, onSubmit, pending,
}) => (
  <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle>Decidir processo</DialogTitle>
        <DialogDescription>
          {target && <>Sanção: {SANCAO_TIPO_LABELS[target.tipo] || target.tipo}. Registe a deliberação.</>}
        </DialogDescription>
      </DialogHeader>
      <div className="space-y-4">
        <label className="flex items-center gap-2 text-sm text-grafite cursor-pointer">
          <input
            type="checkbox"
            checked={form.aprovado}
            onChange={(e) => setForm({ ...form, aprovado: e.target.checked })}
            className="rounded border-gray-300 text-carmesim focus:ring-carmesim/40"
            data-testid="decidir-aprovado"
          />
          Sanção aprovada
        </label>
        <Field label="Fundamentação (opcional)">
          <textarea
            value={form.fundamentacao}
            onChange={(e) => setForm({ ...form, fundamentacao: e.target.value })}
            rows={3}
            maxLength={2000}
            className={`${inputCls} resize-none`}
            data-testid="decidir-fundamentacao"
          />
        </Field>
        {target?.tipo === 'expulsao' && (
          <div className="space-y-3 rounded-md border border-[#FECACA] bg-[#FEF2F2] p-3">
            <p className="text-xs text-[#B91C1C] flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5" aria-hidden="true" />
              Expulsão exige deliberação da AG.
            </p>
            <Field label="ID da Assembleia">
              <input
                type="text"
                value={form.assembleia_id}
                onChange={(e) => setForm({ ...form, assembleia_id: e.target.value })}
                className={inputCls}
                data-testid="decidir-assembleia-id"
              />
            </Field>
            <Field label="ID da Deliberação">
              <input
                type="text"
                value={form.deliberacao_id}
                onChange={(e) => setForm({ ...form, deliberacao_id: e.target.value })}
                className={inputCls}
                data-testid="decidir-deliberacao-id"
              />
            </Field>
          </div>
        )}
        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className={cancelBtn}>Cancelar</button>
          <button
            onClick={onSubmit}
            disabled={!valid || pending}
            className={primaryBtn}
            data-testid="decidir-confirm"
          >
            {pending ? 'A registar...' : 'Registar decisão'}
          </button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
);
