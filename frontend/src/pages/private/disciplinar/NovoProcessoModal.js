import React from 'react';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../../../components/ui/dialog';
import { MemberPicker } from '../../../components/MemberPicker';
import { primaryBtn } from '../../../lib/buttonStyles';
import { SANCAO_TIPO_LABELS } from '../../../lib/governanceLabels';
import { Field } from './widgets';
import {
  TIPO_OPTIONS, cancelBtn, inputCls, selectCls,
} from './tokens';

export const NovoProcessoModal = ({
  open, onClose, form, setForm, onSubmit, valid, pending,
}) => (
  <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle>Novo processo disciplinar</DialogTitle>
        <DialogDescription>Instaure um processo contra um membro (spec-governança §13).</DialogDescription>
      </DialogHeader>
      <div className="space-y-4">
        <Field label="Membro visado">
          <MemberPicker
            value={form.visado}
            onSelect={(u) => setForm({ ...form, visado: u })}
            testId="create-visado-search"
            emptyLabel="Nenhum membro encontrado."
          />
        </Field>
        <Field label="Tipo de sanção">
          <select
            value={form.tipo}
            onChange={(e) => setForm({ ...form, tipo: e.target.value, multa_valor: '', perda_direitos_ate: '' })}
            className={selectCls}
            data-testid="create-tipo"
          >
            {TIPO_OPTIONS.map((t) => <option key={t} value={t}>{SANCAO_TIPO_LABELS[t]}</option>)}
          </select>
        </Field>
        <Field label="Motivo">
          <textarea
            value={form.motivo}
            onChange={(e) => setForm({ ...form, motivo: e.target.value })}
            rows={3}
            maxLength={1000}
            placeholder="Descreva os factos (mínimo 3 caracteres)"
            className={`${inputCls} resize-none`}
            data-testid="create-motivo"
          />
        </Field>
        <Field label="Artigo violado (opcional)">
          <input
            type="text"
            value={form.artigo_violado}
            onChange={(e) => setForm({ ...form, artigo_violado: e.target.value })}
            placeholder="Ex.: Art. 12.º n.º 2"
            className={inputCls}
            data-testid="create-artigo"
          />
        </Field>
        {form.tipo === 'multa' && (
          <Field label="Valor da multa (CVE)" hint="máximo 3x a quota mensal">
            <input
              type="number"
              min="0"
              step="1"
              value={form.multa_valor}
              onChange={(e) => setForm({ ...form, multa_valor: e.target.value })}
              className={inputCls}
              data-testid="create-multa-valor"
            />
          </Field>
        )}
        {form.tipo === 'perda_direitos' && (
          <Field label="Perda de direitos até" hint="Data até à qual os direitos ficam suspensos.">
            <input
              type="date"
              value={form.perda_direitos_ate}
              onChange={(e) => setForm({ ...form, perda_direitos_ate: e.target.value })}
              className={inputCls}
              data-testid="create-perda-ate"
            />
          </Field>
        )}
        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className={cancelBtn}>Cancelar</button>
          <button
            onClick={onSubmit}
            disabled={!valid || pending}
            className={primaryBtn}
            data-testid="create-confirm"
          >
            {pending ? 'A criar...' : 'Criar processo'}
          </button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
);
