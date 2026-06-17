import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../../components/ui/dialog';
import { Input } from '../../../components/ui/input';
import { primaryBtn } from '../../../lib/buttonStyles';
import { MODO_LABELS, fieldClass, labelClass, secondaryBtn } from './tokens';

export const CriarEleicaoModal = ({ open, onClose, onSubmit, pending }) => {
  const [form, setForm] = useState({ ano: new Date().getFullYear(), mandato_inicio: '', mandato_fim: '', modo_votacao: 'presencial', direcao_titulares: 5 });

  useEffect(() => {
    if (open) setForm({ ano: new Date().getFullYear(), mandato_inicio: '', mandato_fim: '', modo_votacao: 'presencial', direcao_titulares: 5 });
  }, [open]);

  const valid = form.ano && form.mandato_inicio && form.mandato_fim;

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Criar eleição</DialogTitle>
          <DialogDescription>Defina o ano, o mandato e o modo de votação dos órgãos sociais.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className={labelClass} htmlFor="ele-ano">Ano</label>
              <Input
                id="ele-ano"
                type="number"
                value={form.ano}
                onChange={(e) => setForm({ ...form, ano: Number(e.target.value) })}
                className={fieldClass}
                data-testid="eleicao-ano"
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="ele-direcao">Titulares da Direcção</label>
              <select
                id="ele-direcao"
                value={form.direcao_titulares}
                onChange={(e) => setForm({ ...form, direcao_titulares: Number(e.target.value) })}
                className={`${fieldClass} bg-white`}
              >
                <option value={5}>5</option>
                <option value={7}>7</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className={labelClass} htmlFor="ele-inicio">Início do mandato</label>
              <Input
                id="ele-inicio"
                type="date"
                value={form.mandato_inicio}
                onChange={(e) => setForm({ ...form, mandato_inicio: e.target.value })}
                className={fieldClass}
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="ele-fim">Fim do mandato</label>
              <Input
                id="ele-fim"
                type="date"
                value={form.mandato_fim}
                onChange={(e) => setForm({ ...form, mandato_fim: e.target.value })}
                className={fieldClass}
              />
            </div>
          </div>
          <div>
            <label className={labelClass} htmlFor="ele-modo">Modo de votação</label>
            <select
              id="ele-modo"
              value={form.modo_votacao}
              onChange={(e) => setForm({ ...form, modo_votacao: e.target.value })}
              className={`${fieldClass} bg-white`}
            >
              {Object.entries(MODO_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className={secondaryBtn}>Cancelar</button>
            <button
              type="button"
              onClick={() => onSubmit({
                ano: Number(form.ano),
                mandato_inicio: form.mandato_inicio,
                mandato_fim: form.mandato_fim,
                modo_votacao: form.modo_votacao,
                direcao_titulares: Number(form.direcao_titulares),
              })}
              disabled={!valid || pending}
              className={primaryBtn}
              data-testid="criar-eleicao-confirm"
            >
              {pending ? 'A criar...' : 'Criar eleição'}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
