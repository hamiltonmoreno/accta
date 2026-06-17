import React from 'react';
import { AlertTriangle } from 'lucide-react';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../../../components/ui/dialog';
import { MemberPicker } from '../../../components/MemberPicker';
import { primaryBtn } from '../../../lib/buttonStyles';
import { Field } from './widgets';
import { cancelBtn, inputCls } from './tokens';

export const ComissaoModal = ({
  open, onClose, form, setForm, ids, valid, onSubmit, pending,
}) => (
  <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle>Comissão de inquérito</DialogTitle>
        <DialogDescription>Nomeie exatamente 3 membros distintos e defina o prazo do inquérito.</DialogDescription>
      </DialogHeader>
      <div className="space-y-4">
        {[0, 1, 2].map((idx) => (
          <Field key={idx} label={`Membro ${idx + 1}`}>
            <MemberPicker
              value={form.m[idx]}
              onSelect={(u) => {
                const next = [...form.m];
                next[idx] = u;
                setForm({ ...form, m: next });
              }}
              testId={`comissao-member-${idx}`}
              emptyLabel="Nenhum membro encontrado."
            />
          </Field>
        ))}
        <Field label="Prazo do inquérito (dias)">
          <input
            type="number"
            min="1"
            step="1"
            value={form.prazo_dias}
            onChange={(e) => setForm({ ...form, prazo_dias: e.target.value })}
            className={inputCls}
            data-testid="comissao-prazo"
          />
        </Field>
        {!valid && ids.length > 0 && (
          <p className="text-xs text-[#B45309] flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />
            São necessários 3 membros distintos.
          </p>
        )}
        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className={cancelBtn}>Cancelar</button>
          <button
            onClick={onSubmit}
            disabled={!valid || pending}
            className={primaryBtn}
            data-testid="comissao-confirm"
          >
            {pending ? 'A nomear...' : 'Nomear comissão'}
          </button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
);
