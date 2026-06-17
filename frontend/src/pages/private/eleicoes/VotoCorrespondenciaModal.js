import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../../components/ui/dialog';
import { Textarea } from '../../../components/ui/textarea';
import { MemberPicker as CandidatePicker } from '../../../components/MemberPicker';
import { primaryBtn } from '../../../lib/buttonStyles';
import { fieldClass, labelClass, secondaryBtn } from './tokens';

// Registo administrativo de um boletim recebido por correspondência. SEGREDO: o
// sentido do voto nunca é confirmado associado ao eleitor após submissão.
export const VotoCorrespondenciaModal = ({ open, onClose, onSubmit, pending, listas }) => {
  const [voter, setVoter] = useState(null);
  const [voto, setVoto] = useState(null);
  const [justificacao, setJustificacao] = useState('');

  useEffect(() => { if (open) { setVoter(null); setVoto(null); setJustificacao(''); } }, [open]);

  const aceites = listas.filter((l) => l.estado === 'aceite');
  const Option = ({ id, children }) => (
    <label className={`flex items-center gap-3 px-3 py-2.5 rounded-md border cursor-pointer transition-colors ${voto === id ? 'border-carmesim bg-carmesim/5' : 'border-[#E5E7EB] hover:bg-[#F5F5F5]'}`}>
      <input type="radio" name="voto-corr" checked={voto === id} onChange={() => setVoto(id)} className="text-carmesim focus:ring-carmesim/40" />
      <span className="text-sm text-grafite">{children}</span>
    </label>
  );

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Voto por correspondência</DialogTitle>
          <DialogDescription>Registo administrativo de um boletim recebido por correspondência. O sentido do voto não fica associado ao eleitor.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Eleitor</label>
            <CandidatePicker value={voter} onSelect={setVoter} testId="corr-voter" />
          </div>
          <div className="space-y-2">
            {aceites.map((l) => (
              <Option key={l.id} id={l.id}><span className="font-semibold mr-1">Lista {l.letra}</span>{l.nome || ''}</Option>
            ))}
            <Option id="branco">Voto em branco</Option>
            <Option id="nulo">Voto nulo</Option>
          </div>
          <div>
            <label className={labelClass} htmlFor="corr-just">Justificação</label>
            <Textarea
              id="corr-just"
              value={justificacao}
              onChange={(e) => setJustificacao(e.target.value)}
              rows={2}
              maxLength={500}
              placeholder="Ex.: boletim recebido por correio em DD/MM/AAAA"
              className={`${fieldClass} resize-none`}
              data-testid="corr-justificacao"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className={secondaryBtn}>Cancelar</button>
            <button
              type="button"
              onClick={() => onSubmit({ user_id: voter.id, voto, justificacao: justificacao.trim() })}
              disabled={!voter || !voto || justificacao.trim().length < 3 || pending}
              className={primaryBtn}
              data-testid="corr-confirm"
            >
              {pending ? 'A registar...' : 'Registar voto'}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
