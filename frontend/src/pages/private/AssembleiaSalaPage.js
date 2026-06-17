import React, { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  ArrowLeft, Calendar, CheckCircle2, ChevronRight, ExternalLink, FileText, Gavel,
  KeyRound, Mail, Mic, MicOff, PlayCircle, ShieldCheck, StopCircle, Users, UserPlus,
  Vote, XCircle,
} from 'lucide-react';

import { assembleiasAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { useAssembleiaStream } from '../../hooks/useAssembleiaStream';
import {
  ASSEMBLEIA_STATUS_LABELS,
  SESSION_PHASE_LABELS,
  VOTING_MODE_LABELS,
  PALAVRA_TIPO_LABELS,
  MOCAO_TIPO_LABELS,
  MAIORIA_LABELS,
  EXPEDIENTE_TIPO_LABELS,
} from '../../lib/governanceLabels';
import { primaryBtn } from '../../lib/buttonStyles';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
// ---------- Tokens & helpers ----------------------------------------------- //

const secondaryBtn =
  'inline-flex items-center gap-1.5 bg-white border border-[#D1D5DB] text-[#3A3A3A] hover:bg-[#F5F5F5] rounded-md px-3 py-1.5 text-sm font-medium transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50';
const dangerBtn =
  'inline-flex items-center gap-1.5 bg-white border border-[#FECACA] text-[#B91C1C] hover:bg-[#FEF2F2] rounded-md px-3 py-1.5 text-sm font-medium transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50';
const fieldCls =
  'w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none';
const labelCls = 'block text-xs font-medium text-[#6B7280] mb-1.5';
const cardCls = 'rounded-lg border border-[#E5E7EB] bg-white p-5';
const sectionTitle = 'text-sm font-semibold text-[#3A3A3A] uppercase tracking-wide';

const PHASE_ORDER = ['fechada', 'checkin', 'antes_ot', 'ordem_trabalhos', 'encerramento'];

const STATUS_STYLES = {
  rascunho: { cls: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]', Icon: Calendar },
  convocada: { cls: 'bg-[#EFF6FF] text-[#1D4ED8] border-[#BFDBFE]', Icon: Calendar },
  em_curso: { cls: 'bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]', Icon: ShieldCheck },
  encerrada: { cls: 'bg-[#F0FDF4] text-[#15803D] border-[#BBF7D0]', Icon: CheckCircle2 },
  anulada: { cls: 'bg-[#FEF2F2] text-[#B91C1C] border-[#FECACA]', Icon: XCircle },
};

const StatusBadge = ({ status }) => {
  const s = STATUS_STYLES[status] || STATUS_STYLES.rascunho;
  const { Icon } = s;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${s.cls}`}>
      <Icon className="w-3.5 h-3.5" aria-hidden="true" />
      {ASSEMBLEIA_STATUS_LABELS[status] || status}
    </span>
  );
};

const PhaseBadge = ({ phase }) => (
  <span className="inline-flex items-center px-2.5 py-1 rounded-full border border-[#E5E7EB] bg-[#F5F5F5] text-xs font-medium text-[#3A3A3A]">
    {SESSION_PHASE_LABELS[phase] || phase}
  </span>
);

const formatDateTime = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('pt-PT', {
      day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return '—';
  }
};

// ---------- Quórum bar ----------------------------------------------------- //

export const QuorumBar = ({ snapshot, fallback }) => {
  // Preferir snapshot SSE (live); cair para `fallback` (GET /quorum) enquanto não chega.
  const q = snapshot?.quorum || fallback;
  if (!q) return <div className="h-6 bg-[#F5F5F5] rounded animate-pulse" />;
  const required = q.required ?? q.quorum_required ?? 0;
  const present = q.present_power ?? q.present_voting_power ?? 0;
  const met = q.met ?? present >= required;
  const ratio = required > 0 ? Math.min(1, present / required) : 0;
  const pct = Math.round(ratio * 100);
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between text-sm">
        <span className="font-semibold text-[#3A3A3A]">
          Quórum: <span className={met ? 'text-[#15803D]' : 'text-[#B45309]'}>{present} / {required}</span>
        </span>
        <span className="text-xs text-[#6B7280]">
          {snapshot ? `Chamada ${snapshot.chamada || 1}` : ''}{' '}
          {met ? '✓ atingido' : '· em curso'}
        </span>
      </div>
      <div className="h-2 w-full rounded-full bg-[#F5F5F5] overflow-hidden" aria-hidden="true">
        <div
          className={`h-full transition-all ${met ? 'bg-[#15803D]' : 'bg-[#B45309]'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};

// ---------- Countdown para palavra ----------------------------------------- //

export const Countdown = ({ endsAt }) => {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  if (!endsAt) return null;
  const remaining = Math.max(0, Math.floor((new Date(endsAt).getTime() - now) / 1000));
  const m = Math.floor(remaining / 60);
  const s = String(remaining % 60).padStart(2, '0');
  return (
    <span className={`font-mono text-xs ${remaining <= 10 ? 'text-[#B91C1C]' : 'text-[#3A3A3A]'}`}>
      {m}:{s}
    </span>
  );
};

// ---------- Painel da Mesa: fases & check-in ------------------------------- //

const FaseControls = ({ assembleia, snapshot, refetchSnap }) => {
  const qc = useQueryClient();
  const phase = snapshot?.phase || assembleia.session_phase || 'fechada';
  const idx = PHASE_ORDER.indexOf(phase);
  const next = idx >= 0 && idx < PHASE_ORDER.length - 1 ? PHASE_ORDER[idx + 1] : null;

  const setFaseMut = useMutation({
    mutationFn: (target) => assembleiasAPI.setFase(assembleia.id, { session_phase: target }),
    onSuccess: () => {
      toast.success('Fase actualizada');
      qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id] });
      refetchSnap?.();
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro a transitar fase'),
  });

  return (
    <div className="flex flex-wrap items-center gap-2">
      <PhaseBadge phase={phase} />
      {next && (
        <button
          type="button"
          className={secondaryBtn}
          disabled={setFaseMut.isPending}
          onClick={() => setFaseMut.mutate(next)}
        >
          Avançar para {SESSION_PHASE_LABELS[next]}
          <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
        </button>
      )}
    </div>
  );
};

const CheckinMesaPanel = ({ assembleia, refetchAssemb, refetchSnap }) => {
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

// ---------- Painel do membro: self check-in -------------------------------- //

export const CheckinParticipantePanel = ({ assembleia, presente, refetchAssemb }) => {
  const qc = useQueryClient();
  const [code, setCode] = useState('');

  const checkinMut = useMutation({
    mutationFn: (data) => assembleiasAPI.checkin(assembleia.id, data),
    onSuccess: () => {
      toast.success('Presença registada');
      qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id] });
      refetchAssemb?.();
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Não foi possível registar presença'),
  });

  if (presente) {
    return (
      <div className="rounded-md bg-[#F0FDF4] border border-[#BBF7D0] px-3 py-2 text-sm text-[#15803D] inline-flex items-center gap-2">
        <CheckCircle2 className="w-4 h-4" />
        Presente nesta sessão.
      </div>
    );
  }

  const meeting = assembleia.meeting_link;
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {meeting ? (
          <button
            type="button"
            className={primaryBtn}
            disabled={checkinMut.isPending}
            onClick={async () => {
              await checkinMut.mutateAsync({ method: 'join_click' });
              window.open(meeting, '_blank', 'noopener');
            }}
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Entrar na reunião
          </button>
        ) : (
          <button
            type="button"
            className={primaryBtn}
            disabled={checkinMut.isPending}
            onClick={() => checkinMut.mutate({ method: 'join_click' })}
          >
            Registar presença
          </button>
        )}
      </div>
      <div className="flex flex-wrap items-end gap-2">
        <div className="flex-1 min-w-[160px]">
          <label className={labelCls} htmlFor="checkin-code">Código de sessão (opcional)</label>
          <Input
            id="checkin-code"
            className={fieldCls}
            placeholder="ABC123"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            maxLength={8}
          />
        </div>
        <button
          type="button"
          className={secondaryBtn}
          disabled={!code || checkinMut.isPending}
          onClick={() => checkinMut.mutate({ method: 'self_code', code: code.trim() })}
        >
          Confirmar com código
        </button>
      </div>
    </div>
  );
};

// ---------- Fila de uso da palavra ----------------------------------------- //

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

// ---------- Votação ao vivo ------------------------------------------------ //

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

// ---------- Moções --------------------------------------------------------- //

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

// ---------- Expediente (F5) ------------------------------------------------ //

const ExpedientePanel = ({ assembleia, snapshot, isMesa }) => {
  const qc = useQueryClient();
  const [tipo, setTipo] = useState('correspondencia');
  const [texto, setTexto] = useState('');
  const [aclamacao, setAclamacao] = useState(true);

  const { data: entries = [], refetch } = useQuery({
    queryKey: ['assembleia', assembleia.id, 'expediente'],
    queryFn: async () => (await assembleiasAPI.expediente(assembleia.id)).data.expediente || [],
    staleTime: 10000,
  });
  const ver = snapshot?.version;
  useEffect(() => { if (ver != null) refetch(); }, [ver, refetch]);

  const addMut = useMutation({
    mutationFn: (data) => assembleiasAPI.addExpediente(assembleia.id, data),
    onSuccess: () => {
      toast.success('Expediente registado');
      qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id, 'expediente'] });
      setTexto('');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro'),
  });

  return (
    <div className="space-y-4">
      {entries.length === 0 ? (
        <p className="text-sm text-[#6B7280] italic">Sem expediente registado.</p>
      ) : (
        <ul className="divide-y divide-[#E5E7EB] border border-[#E5E7EB] rounded-md">
          {entries.map((e) => (
            <li key={e.id} className="px-3 py-2 text-sm">
              <span className="inline-block text-xs px-1.5 py-0.5 rounded bg-[#F5F5F5] text-[#6B7280] border border-[#E5E7EB] mr-2">
                {EXPEDIENTE_TIPO_LABELS[e.tipo] || e.tipo}
              </span>
              {e.aprovado_por_aclamacao && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#F0FDF4] text-[#15803D] border border-[#BBF7D0] mr-2">
                  por aclamação
                </span>
              )}
              <span className="text-[#3A3A3A]">{e.texto}</span>
            </li>
          ))}
        </ul>
      )}

      {isMesa && (
        <form
          className="space-y-2 pt-3 border-t border-[#E5E7EB]"
          onSubmit={(ev) => {
            ev.preventDefault();
            const payload = { tipo, texto };
            if (tipo !== 'correspondencia') payload.aprovado_por_aclamacao = aclamacao;
            addMut.mutate(payload);
          }}
        >
          <p className="text-xs font-medium text-[#6B7280]">Registar (Mesa)</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div className="sm:col-span-1">
              <label className={labelCls} htmlFor="exp-tipo">Tipo</label>
              <select id="exp-tipo" className={fieldCls} value={tipo} onChange={(ev) => setTipo(ev.target.value)}>
                {Object.entries(EXPEDIENTE_TIPO_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className={labelCls} htmlFor="exp-texto">Texto</label>
              <Input id="exp-texto" className={fieldCls} required minLength={1} value={texto} onChange={(ev) => setTexto(ev.target.value)} />
            </div>
          </div>
          {tipo !== 'correspondencia' && (
            <label className="inline-flex items-center gap-2 text-sm">
              <input type="checkbox" checked={aclamacao} onChange={(ev) => setAclamacao(ev.target.checked)} />
              Aprovado por aclamação
            </label>
          )}
          <button type="submit" className={primaryBtn} disabled={addMut.isPending}>
            Registar
          </button>
        </form>
      )}
    </div>
  );
};

// ---------- Documentos (F6) ----------------------------------------------- //

const DocumentosPanel = ({ assembleia, isMesa }) => {
  const qc = useQueryClient();
  const [docId, setDocId] = useState('');

  const { data: docs = [] } = useQuery({
    queryKey: ['assembleia', assembleia.id, 'documentos'],
    queryFn: async () => (await assembleiasAPI.documentos(assembleia.id)).data.documentos || [],
    staleTime: 30000,
  });

  const anexarMut = useMutation({
    mutationFn: (document_id) => assembleiasAPI.anexarDocumento(assembleia.id, { document_id }),
    onSuccess: (res) => {
      if (res.data.tardio) {
        toast.warning('Documento anexado (tardio — <3 dias antes da sessão)');
      } else {
        toast.success('Documento anexado');
      }
      qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id, 'documentos'] });
      setDocId('');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro'),
  });

  return (
    <div className="space-y-3">
      {docs.length === 0 ? (
        <p className="text-sm text-[#6B7280] italic">Sem documentos anexados.</p>
      ) : (
        <ul className="divide-y divide-[#E5E7EB] border border-[#E5E7EB] rounded-md">
          {docs.map((d) => (
            <li key={d.id} className="px-3 py-2 text-sm flex items-center justify-between">
              <span className="inline-flex items-center gap-2">
                <FileText className="w-3.5 h-3.5 text-[#6B7280]" />
                {d.title || d.id}
              </span>
              {d.file_url && (
                <a href={d.file_url} target="_blank" rel="noopener noreferrer" className="text-xs text-carmesim hover:underline inline-flex items-center gap-1">
                  Abrir <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </li>
          ))}
        </ul>
      )}

      {isMesa && (
        <div className="flex flex-wrap items-end gap-2 pt-2 border-t border-[#E5E7EB]">
          <div className="flex-1 min-w-[220px]">
            <label className={labelCls} htmlFor="doc-id">document_id existente</label>
            <Input
              id="doc-id"
              className={fieldCls}
              placeholder="UUID do documento já carregado"
              value={docId}
              onChange={(e) => setDocId(e.target.value)}
            />
          </div>
          <button
            type="button"
            className={secondaryBtn}
            disabled={!docId || anexarMut.isPending}
            onClick={() => anexarMut.mutate(docId.trim())}
          >
            Anexar
          </button>
          <p className="w-full text-xs text-[#6B7280]">
            Anexar com <strong>&lt;3 dias</strong> de antecedência fica marcado como tardio (Art. 20).
            Upload integrado de ficheiros — futuro.
          </p>
        </div>
      )}
    </div>
  );
};

// ---------- Convidados (F6) ----------------------------------------------- //

const ConvidadosPanel = ({ assembleia, snapshot }) => {
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

// ---------- Página principal ---------------------------------------------- //

export const AssembleiaSalaPage = () => {
  const { id } = useParams();
  const { user, isAdmin, isMesaAG } = useAuth();
  const isMesa = isAdmin || isMesaAG;
  const { snapshot, connected: streamConnected } = useAssembleiaStream(id);

  const { data: assembleia, isLoading, refetch } = useQuery({
    queryKey: ['assembleia', id, 'detail'],
    queryFn: async () => (await assembleiasAPI.get(id)).data,
    staleTime: 10000,
  });

  // Quorum fallback enquanto o SSE não chega.
  const { data: quorumData } = useQuery({
    queryKey: ['assembleia', id, 'quorum'],
    queryFn: async () => (await assembleiasAPI.quorum(id)).data,
    staleTime: 10000,
  });

  // Presenças → a Mesa lê a lista completa; os participantes recebem só o seu
  // próprio estado dentro do snapshot SSE (`me.present`), sem precisar de um
  // endpoint que devolve 403 ao não-Mesa.
  const { data: presencasResp } = useQuery({
    queryKey: ['assembleia', id, 'presencas'],
    queryFn: async () => (await assembleiasAPI.presencas(id)).data.presencas || [],
    enabled: isMesa,
    staleTime: 10000,
  });

  const presente = useMemo(() => {
    if (!user) return false;
    if (presencasResp) return presencasResp.some((p) => p.user_id === user.id);
    return Boolean(snapshot?.me?.present);
  }, [user, presencasResp, snapshot?.me?.present]);

  if (isLoading || !assembleia) {
    return <div className="p-8"><div className="h-24 bg-[#F5F5F5] rounded animate-pulse" /></div>;
  }

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Header */}
      <div>
        <Link to="/admin/assembleias" className="text-sm text-[#6B7280] hover:text-[#3A3A3A] inline-flex items-center gap-1 mb-2">
          <ArrowLeft className="w-3.5 h-3.5" />
          Voltar à lista
        </Link>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <h1 className="text-2xl font-bold text-[#3A3A3A]">{assembleia.titulo}</h1>
            <p className="text-sm text-[#6B7280]">
              {formatDateTime(assembleia.data)} · {assembleia.local}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={assembleia.status} />
            <PhaseBadge phase={snapshot?.phase || assembleia.session_phase || 'fechada'} />
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${
                streamConnected
                  ? 'bg-[#F0FDF4] border-[#BBF7D0] text-[#15803D]'
                  : 'bg-[#FFFBEB] border-[#FDE68A] text-[#92400E]'
              }`}
              title={streamConnected ? 'Actualização em tempo real' : 'Sem ligação ao stream — actualização a cada 30s'}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${streamConnected ? 'bg-[#16A34A]' : 'bg-[#D97706]'}`} />
              {streamConnected ? 'ao vivo' : '30s'}
            </span>
          </div>
        </div>
      </div>

      {/* Quórum */}
      <section className={cardCls}>
        <p className={`${sectionTitle} mb-3 flex items-center gap-1.5`}><Users className="w-4 h-4" />Quórum em tempo real</p>
        <QuorumBar snapshot={snapshot} fallback={quorumData} />
      </section>

      {/* Mesa: controlos de fase e check-in */}
      {isMesa && (
        <section className={cardCls}>
          <p className={`${sectionTitle} mb-3 flex items-center gap-1.5`}><ShieldCheck className="w-4 h-4" />Consola da Mesa</p>
          <div className="space-y-4">
            <FaseControls assembleia={assembleia} snapshot={snapshot} refetchSnap={refetch} />
            <div className="pt-3 border-t border-[#E5E7EB]">
              <CheckinMesaPanel assembleia={assembleia} refetchAssemb={refetch} />
            </div>
          </div>
        </section>
      )}

      {/* Participante: self check-in */}
      {!isMesa && (
        <section className={cardCls}>
          <p className={`${sectionTitle} mb-3 flex items-center gap-1.5`}><KeyRound className="w-4 h-4" />Check-in</p>
          <CheckinParticipantePanel assembleia={assembleia} presente={presente} refetchAssemb={refetch} />
        </section>
      )}

      {/* Palavra */}
      <section className={cardCls}>
        <p className={`${sectionTitle} mb-3 flex items-center gap-1.5`}><Mic className="w-4 h-4" />Uso da palavra</p>
        <PalavraPanel assembleia={assembleia} snapshot={snapshot} isMesa={isMesa} presente={presente} />
      </section>

      {/* Voto */}
      <section className={cardCls}>
        <p className={`${sectionTitle} mb-3 flex items-center gap-1.5`}><Vote className="w-4 h-4" />Votação</p>
        <VotacaoPanel assembleia={assembleia} snapshot={snapshot} isMesa={isMesa} currentUserId={user?.id} />
      </section>

      {/* Moções */}
      <section className={cardCls}>
        <p className={`${sectionTitle} mb-3 flex items-center gap-1.5`}><Gavel className="w-4 h-4" />Moções, requerimentos e recomendações</p>
        <MocoesPanel assembleia={assembleia} snapshot={snapshot} isMesa={isMesa} presente={presente} currentUserId={user?.id} />
      </section>

      {/* Expediente (F5) — antes da OT */}
      <section className={cardCls}>
        <p className={`${sectionTitle} mb-3 flex items-center gap-1.5`}><Mail className="w-4 h-4" />Expediente</p>
        <ExpedientePanel assembleia={assembleia} snapshot={snapshot} isMesa={isMesa} />
      </section>

      {/* Documentos (F6) — anexos ≥3 dias antes */}
      <section className={cardCls}>
        <p className={`${sectionTitle} mb-3 flex items-center gap-1.5`}><FileText className="w-4 h-4" />Documentos da sessão</p>
        <DocumentosPanel assembleia={assembleia} isMesa={isMesa} />
      </section>

      {/* Convidados (F6) — só visível à Mesa (RBAC no GET) */}
      {isMesa && (
        <section className={cardCls}>
          <p className={`${sectionTitle} mb-3 flex items-center gap-1.5`}><UserPlus className="w-4 h-4" />Convidados</p>
          <ConvidadosPanel assembleia={assembleia} snapshot={snapshot} />
        </section>
      )}
    </div>
  );
};

export default AssembleiaSalaPage;
