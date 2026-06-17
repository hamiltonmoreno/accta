import React, { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Mic, MicOff, PlayCircle, StopCircle } from 'lucide-react';
import { toast } from 'sonner';
import { assembleiasAPI } from '../../../utils/api';
import { PALAVRA_TIPO_LABELS } from '../../../lib/governanceLabels';
import { primaryBtn } from '../../../lib/buttonStyles';
import { secondaryBtn, dangerBtn, fieldCls, labelCls } from './tokens';
import { Countdown } from './Countdown';

export const PalavraPanel = ({ assembleia, snapshot, isMesa, presente }) => {
  const qc = useQueryClient();
  const [tipo, setTipo] = useState('intervencao');

  const { data: fila = [], refetch } = useQuery({
    queryKey: ['assembleia', assembleia.id, 'palavra'],
    queryFn: async () => (await assembleiasAPI.palavra(assembleia.id)).data.palavra || [],
    staleTime: 5000,
  });

  // Re-fetch quando o SSE bumpa a sessão (versão muda → snapshot muda).
  const ver = snapshot?.version;
  useEffect(() => {
    if (ver != null) refetch();
  }, [ver, refetch]);

  const onOk = (msg) => () => {
    toast.success(msg);
    qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id, 'palavra'] });
  };
  const onErr = (fallback) => (e) => toast.error(e.response?.data?.detail || fallback);

  const pedirMut = useMutation({
    mutationFn: (t) => assembleiasAPI.pedirPalavra(assembleia.id, { tipo: t }),
    onSuccess: onOk('Pedido inscrito'),
    onError: onErr('Erro'),
  });
  const retirarMut = useMutation({
    mutationFn: (qid) => assembleiasAPI.retirarPalavra(assembleia.id, qid),
    onSuccess: onOk('Pedido retirado'),
    onError: onErr('Erro'),
  });
  const iniciarMut = useMutation({
    mutationFn: (qid) => assembleiasAPI.iniciarPalavra(assembleia.id, qid, {}),
    onSuccess: onOk('Palavra concedida'),
    onError: onErr('Erro'),
  });
  const terminarMut = useMutation({
    mutationFn: (qid) => assembleiasAPI.terminarPalavra(assembleia.id, qid),
    onSuccess: onOk('Intervenção encerrada'),
    onError: onErr('Erro'),
  });

  const aFalar = fila.find((p) => p.status === 'a_falar');
  const inscritos = fila
    .filter((p) => p.status === 'inscrito')
    .sort((a, b) => (a.ordem ?? 1e9) - (b.ordem ?? 1e9) || a.requested_at.localeCompare(b.requested_at));

  return (
    <div className="space-y-4">
      {aFalar ? (
        <div className="rounded-md bg-[#FFFBEB] border border-[#FDE68A] p-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Mic className="w-4 h-4 text-[#B45309]" />
            <span className="text-sm font-medium text-[#92400E]">
              A falar: {aFalar.user_id || aFalar.convidado_id} ({PALAVRA_TIPO_LABELS[aFalar.tipo]})
            </span>
            <Countdown endsAt={aFalar.ends_at} />
          </div>
          {isMesa && (
            <button type="button" className={secondaryBtn} onClick={() => terminarMut.mutate(aFalar.id)}>
              <StopCircle className="w-3.5 h-3.5" />
              Terminar
            </button>
          )}
        </div>
      ) : (
        <p className="text-sm text-[#6B7280]">Ninguém a falar.</p>
      )}

      <div>
        <p className="text-xs font-medium text-[#6B7280] mb-2">
          Fila ({inscritos.length} {inscritos.length === 1 ? 'inscrito' : 'inscritos'})
        </p>
        {inscritos.length === 0 ? (
          <p className="text-sm text-[#6B7280] italic">Fila vazia.</p>
        ) : (
          <ul className="divide-y divide-[#E5E7EB] border border-[#E5E7EB] rounded-md">
            {inscritos.map((p, i) => (
              <li key={p.id} className="flex items-center justify-between px-3 py-2 text-sm">
                <span>
                  <span className="font-mono text-[#6B7280] mr-2">{i + 1}.</span>
                  {p.user_id || `Convidado ${p.convidado_id}`}{' '}
                  <span className="text-xs text-[#6B7280]">({PALAVRA_TIPO_LABELS[p.tipo]})</span>
                </span>
                <div className="flex items-center gap-2">
                  {isMesa && (
                    <button type="button" className={secondaryBtn} onClick={() => iniciarMut.mutate(p.id)}>
                      <PlayCircle className="w-3.5 h-3.5" />
                      Conceder
                    </button>
                  )}
                  <button type="button" className={dangerBtn} onClick={() => retirarMut.mutate(p.id)}>
                    <MicOff className="w-3.5 h-3.5" />
                    Retirar
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {presente && !isMesa && (
        <div className="flex flex-wrap items-end gap-2 pt-2 border-t border-[#E5E7EB]">
          <div>
            <label className={labelCls} htmlFor="palavra-tipo">Tipo</label>
            <select id="palavra-tipo" className={fieldCls} value={tipo} onChange={(e) => setTipo(e.target.value)}>
              {Object.entries(PALAVRA_TIPO_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
          <button type="button" className={primaryBtn} disabled={pedirMut.isPending} onClick={() => pedirMut.mutate(tipo)}>
            <Mic className="w-3.5 h-3.5" />
            Pedir a palavra
          </button>
        </div>
      )}
    </div>
  );
};
