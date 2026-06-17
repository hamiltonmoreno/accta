import React, { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Mail, Mic, UserPlus } from 'lucide-react';
import { toast } from 'sonner';
import { assembleiasAPI } from '../../../utils/api';
import { primaryBtn } from '../../../lib/buttonStyles';
import { Input } from '../../../components/ui/input';
import { secondaryBtn, fieldCls, labelCls } from './tokens';

export const ConvidadosPanel = ({ assembleia, snapshot }) => {
  const qc = useQueryClient();
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [canSpeak, setCanSpeak] = useState(false);

  const { data: convidados = [], refetch } = useQuery({
    queryKey: ['assembleia', assembleia.id, 'convidados'],
    queryFn: async () => (await assembleiasAPI.convidados(assembleia.id)).data.convidados || [],
    staleTime: 10000,
  });
  const ver = snapshot?.version;
  useEffect(() => { if (ver != null) refetch(); }, [ver, refetch]);

  const okAndRefresh = (msg) => () => {
    toast.success(msg);
    qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id, 'convidados'] });
  };
  const onErr = (fallback) => (e) => toast.error(e.response?.data?.detail || fallback);

  const addMut = useMutation({
    mutationFn: (data) => assembleiasAPI.addConvidado(assembleia.id, data),
    onSuccess: () => {
      okAndRefresh('Convidado adicionado')();
      setNome(''); setEmail(''); setCanSpeak(false);
    },
    onError: onErr('Erro'),
  });
  const checkinMut = useMutation({
    mutationFn: (cid) => assembleiasAPI.checkinConvidado(assembleia.id, cid),
    onSuccess: okAndRefresh('Convidado presente'),
    onError: onErr('Erro'),
  });
  const palavraMut = useMutation({
    mutationFn: (cid) => assembleiasAPI.pedirPalavraConvidado(assembleia.id, { convidado_id: cid, tipo: 'intervencao' }),
    onSuccess: () => {
      toast.success('Convidado inscrito na fila de palavra');
      qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id, 'palavra'] });
    },
    onError: onErr('Erro'),
  });

  return (
    <div className="space-y-4">
      {convidados.length === 0 ? (
        <p className="text-sm text-[#6B7280] italic">Sem convidados.</p>
      ) : (
        <ul className="divide-y divide-[#E5E7EB] border border-[#E5E7EB] rounded-md">
          {convidados.map((c) => (
            <li key={c.id} className="px-3 py-2 text-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <span className="font-medium">{c.nome}</span>
                  {c.email && (
                    <span className="ml-2 text-xs text-[#6B7280] inline-flex items-center gap-1">
                      <Mail className="w-3 h-3" />{c.email}
                    </span>
                  )}
                  {c.can_speak && (
                    <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-[#EFF6FF] text-[#1D4ED8] border border-[#BFDBFE]">
                      pode intervir
                    </span>
                  )}
                  {c.checked_in && (
                    <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-[#F0FDF4] text-[#15803D] border border-[#BBF7D0]">
                      presente
                    </span>
                  )}
                  {c.motivo && <p className="text-xs text-[#6B7280] mt-0.5">{c.motivo}</p>}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {!c.checked_in && (
                    <button type="button" className={secondaryBtn} onClick={() => checkinMut.mutate(c.id)}>
                      Marcar presente
                    </button>
                  )}
                  {c.can_speak && c.checked_in && (
                    <button type="button" className={secondaryBtn} onClick={() => palavraMut.mutate(c.id)}>
                      <Mic className="w-3.5 h-3.5" />
                      Pôr na fila
                    </button>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      <form
        className="space-y-2 pt-3 border-t border-[#E5E7EB]"
        onSubmit={(e) => {
          e.preventDefault();
          addMut.mutate({ nome, email: email || null, can_speak: canSpeak });
        }}
      >
        <p className="text-xs font-medium text-[#6B7280]">Convidar (Mesa)</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div>
            <label className={labelCls} htmlFor="conv-nome">Nome</label>
            <Input id="conv-nome" className={fieldCls} required minLength={2} value={nome} onChange={(e) => setNome(e.target.value)} />
          </div>
          <div>
            <label className={labelCls} htmlFor="conv-email">Email (opcional)</label>
            <Input id="conv-email" type="email" className={fieldCls} value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
        </div>
        <label className="inline-flex items-center gap-2 text-sm">
          <input type="checkbox" checked={canSpeak} onChange={(e) => setCanSpeak(e.target.checked)} />
          Pode intervir
        </label>
        <p className="text-xs text-[#6B7280]">
          Email não é enviado automaticamente — partilhe o `meeting_link` manualmente.
        </p>
        <button type="submit" className={primaryBtn} disabled={addMut.isPending}>
          <UserPlus className="w-3.5 h-3.5" />
          Adicionar
        </button>
      </form>
    </div>
  );
};
