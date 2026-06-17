import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Gavel, Vote } from 'lucide-react';
import { toast } from 'sonner';
import { assembleiasAPI } from '../../../utils/api';
import { VOTING_MODE_LABELS, MAIORIA_LABELS } from '../../../lib/governanceLabels';
import { primaryBtn } from '../../../lib/buttonStyles';
import { Input } from '../../../components/ui/input';
import { Textarea } from '../../../components/ui/textarea';
import { secondaryBtn, fieldCls, labelCls } from './tokens';

const ContagemBracoForm = ({ assembleia, deliberacaoId }) => {
  const qc = useQueryClient();
  const [favor, setFavor] = useState(0);
  const [contra, setContra] = useState(0);
  const [abst, setAbst] = useState(0);
  const mut = useMutation({
    mutationFn: () => assembleiasAPI.registarContagem(assembleia.id, deliberacaoId, {
      votos_favor: Number(favor), votos_contra: Number(contra), abstencoes: Number(abst),
    }),
    onSuccess: () => {
      toast.success('Contagem registada');
      qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id] });
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro'),
  });
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 items-end">
      <div>
        <label className={labelCls} htmlFor="favor">A favor</label>
        <Input id="favor" type="number" min={0} className={fieldCls} value={favor} onChange={(e) => setFavor(e.target.value)} />
      </div>
      <div>
        <label className={labelCls} htmlFor="contra">Contra</label>
        <Input id="contra" type="number" min={0} className={fieldCls} value={contra} onChange={(e) => setContra(e.target.value)} />
      </div>
      <div>
        <label className={labelCls} htmlFor="abst">Abstenções</label>
        <Input id="abst" type="number" min={0} className={fieldCls} value={abst} onChange={(e) => setAbst(e.target.value)} />
      </div>
      <div className="col-span-3">
        <button type="button" className={secondaryBtn} disabled={mut.isPending} onClick={() => mut.mutate()}>
          Registar contagem
        </button>
      </div>
    </div>
  );
};

export const VotacaoPanel = ({ assembleia, snapshot, isMesa, currentUserId }) => {
  const qc = useQueryClient();
  const openVote = snapshot?.open_vote;

  // Form para a Mesa abrir uma nova deliberação.
  const [ponto, setPonto] = useState('');
  const [descricao, setDescricao] = useState('');
  const [mode, setMode] = useState('braco_no_ar');
  const [maioria, setMaioria] = useState('absoluta');

  const { data: delib } = useQuery({
    queryKey: ['assembleia', assembleia.id, 'deliberacao', openVote?.deliberacao_id],
    queryFn: async () => (await assembleiasAPI.getDeliberacao(assembleia.id, openVote.deliberacao_id)).data,
    enabled: !!openVote?.deliberacao_id,
    staleTime: 2000,
  });

  const abrirMut = useMutation({
    mutationFn: (data) => assembleiasAPI.abrirDeliberacao(assembleia.id, data),
    onSuccess: () => {
      toast.success('Deliberação aberta');
      qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id] });
      setPonto('');
      setDescricao('');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro'),
  });

  const votarMut = useMutation({
    mutationFn: (escolha) => assembleiasAPI.votarDeliberacao(assembleia.id, openVote.deliberacao_id, { escolha }),
    onSuccess: () => toast.success('Voto registado'),
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro'),
  });

  const apurarMut = useMutation({
    mutationFn: () => assembleiasAPI.apurarDeliberacao(assembleia.id, openVote.deliberacao_id),
    onSuccess: () => {
      toast.success('Deliberação apurada');
      qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id] });
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro'),
  });

  if (!openVote) {
    if (!isMesa) return <p className="text-sm text-[#6B7280]">Sem deliberação aberta.</p>;
    return (
      <form
        className="space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          abrirMut.mutate({ ponto, descricao, tipo_maioria: maioria, voting_mode: mode });
        }}
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className={labelCls} htmlFor="ponto">Ponto</label>
            <Input id="ponto" className={fieldCls} required minLength={1} value={ponto} onChange={(e) => setPonto(e.target.value)} />
          </div>
          <div>
            <label className={labelCls} htmlFor="mode">Modo</label>
            <select id="mode" className={fieldCls} value={mode} onChange={(e) => setMode(e.target.value)}>
              {Object.entries(VOTING_MODE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className={labelCls} htmlFor="descricao">Descrição</label>
          <Textarea id="descricao" className={fieldCls} required rows={2} value={descricao} onChange={(e) => setDescricao(e.target.value)} />
        </div>
        <div>
          <label className={labelCls} htmlFor="maioria">Maioria</label>
          <select id="maioria" className={fieldCls} value={maioria} onChange={(e) => setMaioria(e.target.value)}>
            {Object.entries(MAIORIA_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>
        <button type="submit" className={primaryBtn} disabled={abrirMut.isPending}>
          <Vote className="w-3.5 h-3.5" />
          Abrir deliberação
        </button>
      </form>
    );
  }

  const isExcluded = delib?.conflitos_excluidos?.includes(currentUserId);

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-[#F5F5F5] border border-[#E5E7EB] p-3">
        <p className="text-xs uppercase tracking-wide text-[#6B7280]">Votação aberta</p>
        <p className="text-base font-semibold text-[#3A3A3A]">{delib?.ponto || openVote.ponto}</p>
        <p className="text-sm text-[#6B7280]">{VOTING_MODE_LABELS[openVote.voting_mode]}</p>
        {delib?.descricao && <p className="text-sm mt-1">{delib.descricao}</p>}
        {typeof delib?.votes_cast === 'number' && (
          <p className="text-xs text-[#6B7280] mt-1">{delib.votes_cast} {delib.votes_cast === 1 ? 'voto' : 'votos'} contado(s)</p>
        )}
      </div>

      {isExcluded && (
        <div className="rounded-md bg-[#FEF2F2] border border-[#FECACA] px-3 py-2 text-sm text-[#B91C1C]">
          Está excluído desta votação por conflito de interesses.
        </div>
      )}

      {openVote.voting_mode !== 'braco_no_ar' && !isExcluded && (
        <div className="flex flex-wrap gap-2">
          {['favor', 'contra', 'abstencao'].map((esc) => (
            <button
              key={esc}
              type="button"
              className={esc === 'favor' ? primaryBtn : secondaryBtn}
              disabled={votarMut.isPending}
              onClick={() => votarMut.mutate(esc)}
            >
              {esc === 'favor' ? 'A favor' : esc === 'contra' ? 'Contra' : 'Abstenção'}
            </button>
          ))}
        </div>
      )}

      {openVote.voting_mode === 'braco_no_ar' && isMesa && (
        <ContagemBracoForm assembleia={assembleia} deliberacaoId={openVote.deliberacao_id} />
      )}

      {isMesa && (
        <div className="pt-2 border-t border-[#E5E7EB]">
          <button type="button" className={primaryBtn} disabled={apurarMut.isPending} onClick={() => apurarMut.mutate()}>
            <Gavel className="w-3.5 h-3.5" />
            Apurar deliberação
          </button>
        </div>
      )}
    </div>
  );
};
