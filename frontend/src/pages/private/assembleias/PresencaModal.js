import React from 'react';
import { PlusCircle, X } from 'lucide-react';
import { toast } from 'sonner';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../../../components/ui/dialog';
import { MemberPicker } from '../../../components/MemberPicker';
import { primaryBtn } from '../../../lib/buttonStyles';
import { labelCls, secondaryBtn } from './tokens';

export const PresencaModal = ({
  open, onClose, presenca, setPresenca, onSubmit, pending,
}) => {
  const addRepresentado = () => {
    if (!presenca.repCurrent) return;
    if (presenca.representados.length >= 3) {
      toast.error('Máximo de 3 representados por presente.');
      return;
    }
    if (presenca.representados.some((r) => r.id === presenca.repCurrent.id)) return;
    setPresenca((p) => ({ ...p, representados: [...p.representados, p.repCurrent], repCurrent: null }));
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Registar presença</DialogTitle>
          <DialogDescription>Selecione o sócio presente e, se aplicável, quem representa (máx. 3). A Mesa da AG não pode representar.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className={labelCls}>Sócio presente</label>
            <MemberPicker
              value={presenca.presente}
              onSelect={(u) => setPresenca((p) => ({ ...p, presente: u }))}
              testId="presenca-presente-search"
            />
          </div>
          <div>
            <label className={labelCls}>Representados (opcional, máx. 3)</label>
            {presenca.representados.length > 0 && (
              <ul className="mb-2 space-y-1.5">
                {presenca.representados.map((r) => (
                  <li key={r.id} className="flex items-center justify-between px-3 py-2 rounded-md bg-[#F5F5F5] border border-[#E5E7EB] text-sm text-grafite">
                    <span>{r.name} <span className="font-mono text-xs text-[#6B7280]">{r.member_id || ''}</span></span>
                    <button
                      onClick={() => setPresenca((p) => ({ ...p, representados: p.representados.filter((x) => x.id !== r.id) }))}
                      className="text-[#6B7280] hover:text-carmesim cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 rounded"
                      aria-label={`Remover ${r.name}`}
                    >
                      <X className="w-4 h-4" aria-hidden="true" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {presenca.representados.length < 3 && (
              <div className="space-y-2">
                <MemberPicker
                  value={presenca.repCurrent}
                  onSelect={(u) => setPresenca((p) => ({ ...p, repCurrent: u }))}
                  testId="presenca-representado-search"
                  placeholder="Procurar sócio a representar..."
                />
                {presenca.repCurrent && (
                  <button onClick={addRepresentado} className={secondaryBtn} data-testid="presenca-add-representado">
                    <PlusCircle className="w-4 h-4" aria-hidden="true" />Adicionar representado
                  </button>
                )}
              </div>
            )}
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button onClick={onClose} className={secondaryBtn}>Cancelar</button>
            <button
              onClick={onSubmit}
              disabled={!presenca.presente || pending}
              className={primaryBtn}
              data-testid="presenca-confirm"
            >
              {pending ? 'A registar...' : 'Confirmar'}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
