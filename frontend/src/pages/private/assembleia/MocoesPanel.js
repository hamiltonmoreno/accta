import React, { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { assembleiasAPI } from '../../../utils/api';
import { MOCAO_TIPO_LABELS } from '../../../lib/governanceLabels';
import { primaryBtn } from '../../../lib/buttonStyles';
import { Input } from '../../../components/ui/input';
import { Textarea } from '../../../components/ui/textarea';
import { secondaryBtn, dangerBtn, fieldCls, labelCls } from './tokens';

export const MocoesPanel = ({ assembleia, snapshot, isMesa, presente, currentUserId }) => {
  const qc = useQueryClient();
  const [tipo, setTipo] = useState('mocao');
  const [titulo, setTitulo] = useState('');
  const [texto, setTexto] = useState('');

  const { data: mocoes = [], refetch } = useQuery({
    queryKey: ['assembleia', assembleia.id, 'mocoes'],
    queryFn: async () => (await assembleiasAPI.mocoes(assembleia.id)).data.mocoes || [],
    staleTime: 5000,
  });

  const ver = snapshot?.version;
  useEffect(() => {
    if (ver != null) refetch();
  }, [ver, refetch]);

  const onOk = (msg) => () => {
    toast.success(msg);
    qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id, 'mocoes'] });
  };
  const onErr = (fallback) => (e) => toast.error(e.response?.data?.detail || fallback);

  const submeterMut = useMutation({
    mutationFn: (data) => assembleiasAPI.submeterMocao(assembleia.id, data),
    onSuccess: onOk('Submetida'),
    onError: onErr('Erro a submeter'),
  });
  const colocarMut = useMutation({
    mutationFn: (mid) => assembleiasAPI.colocarMocaoAVoto(assembleia.id, mid, { voting_mode: 'braco_no_ar' }),
    onSuccess: onOk('Colocada a voto'),
    onError: onErr('Erro'),
  });
  const retirarMut = useMutation({
    mutationFn: (mid) => assembleiasAPI.retirarMocao(assembleia.id, mid),
    onSuccess: onOk('Retirada'),
    onError: onErr('Erro'),
  });

  return (
    <div className="space-y-4">
      {mocoes.length === 0 ? (
        <p className="text-sm text-[#6B7280] italic">Sem moções nesta sessão.</p>
      ) : (
        <ul className="divide-y divide-[#E5E7EB] border border-[#E5E7EB] rounded-md">
          {mocoes.map((m) => (
            <li key={m.id} className="px-3 py-2 text-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="font-medium">{m.titulo}</span>
                    <span className="text-xs text-[#6B7280]">({MOCAO_TIPO_LABELS[m.tipo]})</span>
                    {m.votacao_imediata && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#FFFBEB] text-[#B45309] border border-[#FDE68A]">
                        voto imediato
                      </span>
                    )}
                    <span className="text-xs text-[#6B7280]">— {m.status}</span>
                  </div>
                  <p className="text-xs text-[#6B7280] line-clamp-2">{m.texto}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {isMesa && (m.status === 'submetida' || m.status === 'em_discussao') && (
                    <button type="button" className={secondaryBtn} onClick={() => colocarMut.mutate(m.id)}>
                      Colocar a voto
                    </button>
                  )}
                  {(m.status === 'submetida' || m.status === 'em_discussao') &&
                    (isMesa || m.proposta_por === currentUserId) && (
                      <button type="button" className={dangerBtn} onClick={() => retirarMut.mutate(m.id)}>
                        Retirar
                      </button>
                    )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      {presente && (
        <form
          className="space-y-2 pt-3 border-t border-[#E5E7EB]"
          onSubmit={(e) => {
            e.preventDefault();
            submeterMut.mutate({ tipo, titulo, texto });
            setTitulo('');
            setTexto('');
          }}
        >
          <p className="text-xs font-medium text-[#6B7280]">Submeter</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div className="sm:col-span-1">
              <label className={labelCls} htmlFor="mocao-tipo">Tipo</label>
              <select id="mocao-tipo" className={fieldCls} value={tipo} onChange={(e) => setTipo(e.target.value)}>
                {Object.entries(MOCAO_TIPO_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className={labelCls} htmlFor="mocao-titulo">Título</label>
              <Input id="mocao-titulo" className={fieldCls} required minLength={3} value={titulo} onChange={(e) => setTitulo(e.target.value)} />
            </div>
          </div>
          <div>
            <label className={labelCls} htmlFor="mocao-texto">Texto</label>
            <Textarea id="mocao-texto" className={fieldCls} required rows={2} value={texto} onChange={(e) => setTexto(e.target.value)} />
          </div>
          <button type="submit" className={primaryBtn} disabled={submeterMut.isPending}>
            Submeter
          </button>
        </form>
      )}
    </div>
  );
};
