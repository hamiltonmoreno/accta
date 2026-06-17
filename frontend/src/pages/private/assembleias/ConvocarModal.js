import React from 'react';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../../../components/ui/dialog';
import { Input } from '../../../components/ui/input';
import { primaryBtn } from '../../../lib/buttonStyles';
import { ASSEMBLEIA_TIPO_LABELS } from '../../../lib/governanceLabels';
import { TIPO_OPTIONS, fieldCls, labelCls, secondaryBtn } from './tokens';

export const ConvocarModal = ({
  open, onClose, form, setForm, onSubmit, pending,
}) => {
  const valid = form.titulo.trim().length >= 3 && !!form.data;
  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Convocar assembleia</DialogTitle>
          <DialogDescription>Defina o tipo, título, data e local da assembleia geral.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label htmlFor="convocar-tipo" className={labelCls}>Tipo</label>
            <select
              id="convocar-tipo"
              value={form.tipo}
              onChange={(e) => setForm({ ...form, tipo: e.target.value })}
              className={`${fieldCls} bg-white`}
              data-testid="convocar-tipo"
            >
              {TIPO_OPTIONS.map((t) => <option key={t} value={t}>{ASSEMBLEIA_TIPO_LABELS[t]}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="convocar-titulo" className={labelCls}>Título</label>
            <Input
              id="convocar-titulo"
              type="text"
              value={form.titulo}
              onChange={(e) => setForm({ ...form, titulo: e.target.value })}
              placeholder="Ex.: Assembleia Geral Ordinária 2026"
              className={fieldCls}
              data-testid="convocar-titulo"
            />
            {form.titulo.trim().length > 0 && form.titulo.trim().length < 3 && (
              <p className="mt-1 text-xs text-[#B91C1C]">O título deve ter pelo menos 3 caracteres.</p>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="convocar-data" className={labelCls}>Data e hora</label>
              <Input
                id="convocar-data"
                type="datetime-local"
                value={form.data}
                onChange={(e) => setForm({ ...form, data: e.target.value })}
                className={fieldCls}
                data-testid="convocar-data"
              />
            </div>
            <div>
              <label htmlFor="convocar-local" className={labelCls}>Local</label>
              <Input
                id="convocar-local"
                type="text"
                value={form.local}
                onChange={(e) => setForm({ ...form, local: e.target.value })}
                placeholder="Sede / Online"
                className={fieldCls}
                data-testid="convocar-local"
              />
            </div>
          </div>
          {form.tipo === 'extraordinaria' && (
            <div>
              <label htmlFor="convocar-requerente" className={labelCls}>Requerente (opcional)</label>
              <select
                id="convocar-requerente"
                value={form.requerente_tipo}
                onChange={(e) => setForm({ ...form, requerente_tipo: e.target.value })}
                className={`${fieldCls} bg-white`}
                data-testid="convocar-requerente"
              >
                <option value="">—</option>
                <option value="direcao">Direcção</option>
                <option value="conselho_fiscal">Conselho Fiscal</option>
                <option value="socios">Sócios (1/5)</option>
              </select>
            </div>
          )}
          <div className="flex justify-end gap-2 pt-1">
            <button onClick={onClose} className={secondaryBtn}>Cancelar</button>
            <button
              onClick={onSubmit}
              disabled={!valid || pending}
              className={primaryBtn}
              data-testid="convocar-confirm"
            >
              {pending ? 'A convocar...' : 'Confirmar'}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
