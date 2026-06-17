import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../../components/ui/dialog';
import { Input } from '../../../components/ui/input';
import { MemberPicker as CandidatePicker } from '../../../components/MemberPicker';
import { primaryBtn } from '../../../lib/buttonStyles';
import { cargoLabelFrom, orgaoLabel } from '../../../lib/governanceLabels';
import { fieldClass, labelClass, secondaryBtn } from './tokens';

export const SubmeterListaModal = ({ open, onClose, onSubmit, pending, slots, structure }) => {
  const [letra, setLetra] = useState('');
  const [nome, setNome] = useState('');
  const [picks, setPicks] = useState({}); // slot_key -> user

  useEffect(() => {
    if (open) { setLetra(''); setNome(''); setPicks({}); }
  }, [open]);

  const allFilled = slots.length > 0 && slots.every((s) => picks[s.slot_key]);
  const valid = letra.trim() && allFilled;

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Submeter lista</DialogTitle>
          <DialogDescription>
            Indique a letra da lista e atribua um sócio a cada um dos {slots.length} lugares.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className={labelClass} htmlFor="lista-letra">Letra</label>
              <Input
                id="lista-letra"
                type="text"
                maxLength={2}
                value={letra}
                onChange={(e) => setLetra(e.target.value.toUpperCase())}
                placeholder="A"
                className={`${fieldClass} text-center font-semibold`}
                data-testid="lista-letra"
              />
            </div>
            <div className="col-span-2">
              <label className={labelClass} htmlFor="lista-nome">Nome (opcional)</label>
              <Input
                id="lista-nome"
                type="text"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                placeholder="Lista de candidatura"
                className={fieldClass}
              />
            </div>
          </div>

          <div>
            <p className={labelClass}>Candidatos por lugar</p>
            <div className="max-h-72 overflow-y-auto space-y-3 pr-1 rounded-md border border-[#E5E7EB] p-3 bg-[#F5F5F5]/40">
              {slots.map((s) => (
                <div key={s.slot_key} className="rounded-md border border-[#E5E7EB] bg-white p-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm font-medium text-grafite">
                      {cargoLabelFrom(structure, s.cargo)}
                      {s.suplente && <span className="text-xs text-[#6B7280] font-normal"> (suplente)</span>}
                    </span>
                    <span className="text-xs text-[#6B7280]">{orgaoLabel(s.orgao)}</span>
                  </div>
                  <CandidatePicker
                    value={picks[s.slot_key] || null}
                    onSelect={(u) => setPicks((prev) => ({ ...prev, [s.slot_key]: u }))}
                    testId={`slot-picker-${s.slot_key}`}
                    placeholder="Procurar sócio por nome, email ou nº..."
                    showCargo={false}
                    gateOnQuery
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className={secondaryBtn}>Cancelar</button>
            <button
              type="button"
              onClick={() => onSubmit({
                letra: letra.trim(),
                nome: nome.trim() || undefined,
                candidatos: slots.map((s) => ({ slot_key: s.slot_key, user_id: picks[s.slot_key].id })),
              })}
              disabled={!valid || pending}
              className={primaryBtn}
              data-testid="submeter-lista-confirm"
            >
              {pending ? 'A submeter...' : 'Submeter lista'}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
