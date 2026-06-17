import React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { KeyRound } from 'lucide-react';
import { toast } from 'sonner';
import { assembleiasAPI } from '../../../utils/api';
import { secondaryBtn, formatDateTime } from './tokens';

export const CheckinMesaPanel = ({ assembleia, refetchAssemb, refetchSnap }) => {
  const qc = useQueryClient();
  const code = assembleia.check_in_code;
  const expires = assembleia.check_in_code_expires_at;

  // Factory partilhada para callbacks idênticos. Os useMutation ficam inline
  // (regra dos hooks) e só os onSuccess/onError partilham forma.
  const onOk = (msg) => () => {
    toast.success(msg);
    qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id] });
    refetchAssemb?.();
    refetchSnap?.();
  };
  const onErr = (fallback) => (e) => toast.error(e.response?.data?.detail || fallback);

  const abrirMut = useMutation({
    mutationFn: () => assembleiasAPI.abrirCheckin(assembleia.id),
    onSuccess: onOk('Check-in aberto'),
    onError: onErr('Erro a abrir check-in'),
  });
  const fecharMut = useMutation({
    mutationFn: () => assembleiasAPI.fecharCheckin(assembleia.id),
    onSuccess: onOk('Check-in fechado'),
    onError: onErr('Erro a fechar check-in'),
  });
  const segundaMut = useMutation({
    mutationFn: () => assembleiasAPI.segundaConvocatoria(assembleia.id),
    onSuccess: onOk('2.ª convocatória declarada'),
    onError: onErr('Erro a declarar 2.ª convocatória'),
  });

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" className={secondaryBtn} onClick={() => abrirMut.mutate()} disabled={abrirMut.isPending}>
          <KeyRound className="w-3.5 h-3.5" />
          Abrir check-in
        </button>
        <button type="button" className={secondaryBtn} onClick={() => fecharMut.mutate()} disabled={fecharMut.isPending}>
          Fechar check-in
        </button>
        <button type="button" className={secondaryBtn} onClick={() => segundaMut.mutate()} disabled={segundaMut.isPending}>
          Declarar 2.ª convocatória
        </button>
      </div>
      {code && (
        <div className="rounded-md bg-[#FFFBEB] border border-[#FDE68A] px-3 py-2 text-sm text-[#92400E]">
          <span className="font-medium">Código de sessão:</span>{' '}
          <span className="font-mono text-base tracking-widest">{code}</span>
          {expires && <span className="ml-2 text-xs text-[#92400E]/70">válido até {formatDateTime(expires)}</span>}
        </div>
      )}
    </div>
  );
};
