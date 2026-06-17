import React from 'react';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../../../components/ui/dialog';
import { Input } from '../../../components/ui/input';
import { Textarea } from '../../../components/ui/textarea';
import { primaryBtn } from '../../../lib/buttonStyles';
import { MAIORIA_LABELS } from '../../../lib/governanceLabels';
import { MAIORIA_OPTIONS, fieldCls, labelCls, secondaryBtn } from './tokens';

export const DeliberacaoModal = ({
  open, onClose, form, setForm, onSubmit, pending,
}) => (
  <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle>Registar deliberação</DialogTitle>
        <DialogDescription>Indique o ponto, o tipo de maioria e a contagem de votos.</DialogDescription>
      </DialogHeader>
      <div className="space-y-4">
        <div>
          <label className={labelCls}>Ponto</label>
          <Input
            type="text"
            value={form.ponto}
            onChange={(e) => setForm({ ...form, ponto: e.target.value })}
            placeholder="Ex.: Aprovação das contas"
            className={fieldCls}
            data-testid="deliberacao-ponto"
          />
        </div>
        <div>
          <label className={labelCls}>Descrição (opcional)</label>
          <Textarea
            value={form.descricao}
            onChange={(e) => setForm({ ...form, descricao: e.target.value })}
            rows={2}
            maxLength={1000}
            className={`${fieldCls} resize-none`}
          />
        </div>
        <div>
          <label className={labelCls}>Tipo de maioria</label>
          <select
            value={form.tipo_maioria}
            onChange={(e) => setForm({ ...form, tipo_maioria: e.target.value })}
            className={`${fieldCls} bg-white`}
            data-testid="deliberacao-maioria"
          >
            {MAIORIA_OPTIONS.map((m) => <option key={m} value={m}>{MAIORIA_LABELS[m]}</option>)}
          </select>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className={labelCls}>A favor</label>
            <Input type="number" min={0} value={form.votos_favor}
              onChange={(e) => setForm({ ...form, votos_favor: e.target.value })}
              className={fieldCls} data-testid="deliberacao-favor" />
          </div>
          <div>
            <label className={labelCls}>Contra</label>
            <Input type="number" min={0} value={form.votos_contra}
              onChange={(e) => setForm({ ...form, votos_contra: e.target.value })}
              className={fieldCls} data-testid="deliberacao-contra" />
          </div>
          <div>
            <label className={labelCls}>Abstenções</label>
            <Input type="number" min={0} value={form.abstencoes}
              onChange={(e) => setForm({ ...form, abstencoes: e.target.value })}
              className={fieldCls} data-testid="deliberacao-abstencoes" />
          </div>
        </div>
        <div>
          <label className={labelCls}>Artigo de base (opcional)</label>
          <Input
            type="text"
            value={form.source_article}
            onChange={(e) => setForm({ ...form, source_article: e.target.value })}
            placeholder="Ex.: Art. 23.º CV-CAR 2.3/2026"
            className={fieldCls}
            data-testid="deliberacao-artigo"
          />
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className={secondaryBtn}>Cancelar</button>
          <button
            onClick={onSubmit}
            disabled={form.ponto.trim().length < 1 || pending}
            className={primaryBtn}
            data-testid="deliberacao-confirm"
          >
            {pending ? 'A registar...' : 'Confirmar'}
          </button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
);
