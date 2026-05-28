import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { assembleiasAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import {
  ASSEMBLEIA_TIPO_LABELS,
  ASSEMBLEIA_STATUS_LABELS,
  MAIORIA_LABELS,
} from '../../lib/governanceLabels';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import {
  Landmark, Calendar, MapPin, Users, Gavel, CheckCircle2, XCircle,
  PlusCircle, UserPlus, Lock, ChevronRight, ShieldCheck, X, FileText,
} from 'lucide-react';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../../components/ui/dialog';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { MemberPicker } from '../../components/MemberPicker';

const TIPO_OPTIONS = ['ordinaria', 'extraordinaria', 'eleitoral'];
const MAIORIA_OPTIONS = ['absoluta', 'qualificada_2_3', 'qualificada_3_4_presentes', 'qualificada_3_4_universo'];

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

// Estilo do badge de estado da assembleia — cor + ícone + texto (nunca só cor).
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

const TipoBadge = ({ tipo }) => (
  <span className="inline-flex items-center px-2.5 py-1 rounded-full border border-[#E5E7EB] bg-white text-xs font-medium text-grafite">
    {ASSEMBLEIA_TIPO_LABELS[tipo] || tipo}
  </span>
);

const fieldCls ='w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none';
const labelCls = 'block text-xs font-medium text-[#6B7280] mb-1.5';
const secondaryBtn = 'inline-flex items-center gap-1.5 bg-white border border-[#D1D5DB] text-[#3A3A3A] hover:bg-[#F5F5F5] rounded-md px-4 py-2 text-sm font-medium transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50';
const primaryBtn = 'inline-flex items-center gap-1.5 bg-carmesim text-white hover:bg-carmesim-dark rounded-md px-4 py-2 text-sm font-semibold transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50';

// Linha de contagem de votos no detalhe de uma deliberação.
const VoteStat = ({ label, value, color }) => (
  <div className="text-center">
    <p className={`text-lg font-bold ${color}`}>{value ?? 0}</p>
    <p className="text-xs text-[#6B7280]">{label}</p>
  </div>
);

export const AdminAssembleiasPage = () => {
  const qc = useQueryClient();
  const { isAdmin, isMesaAG } = useAuth();
  const canManage = isAdmin || isMesaAG;

  const [selectedId, setSelectedId] = useState(null);
  const [convocarOpen, setConvocarOpen] = useState(false);
  const [presencaOpen, setPresencaOpen] = useState(false);
  const [deliberacaoOpen, setDeliberacaoOpen] = useState(false);
  const [encerrarOpen, setEncerrarOpen] = useState(false);

  // ----- Listagem -----
  const { data: listResp, isLoading } = useQuery({
    queryKey: queryKeys.assembleias.list(),
    queryFn: async () => (await assembleiasAPI.list()).data,
  });
  const assembleias = listResp?.assembleias || [];

  // ----- Detalhe (assembleia seleccionada) -----
  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: queryKeys.assembleias.byId(selectedId),
    queryFn: async () => (await assembleiasAPI.get(selectedId)).data,
    enabled: !!selectedId,
  });

  const { data: quorum } = useQuery({
    queryKey: queryKeys.assembleias.quorum(selectedId),
    queryFn: async () => (await assembleiasAPI.quorum(selectedId)).data,
    enabled: !!selectedId,
  });

  const { data: delibResp, isLoading: delibLoading } = useQuery({
    queryKey: queryKeys.assembleias.deliberacoes(selectedId),
    queryFn: async () => (await assembleiasAPI.deliberacoes(selectedId)).data,
    enabled: !!selectedId,
  });
  const deliberacoes = delibResp?.deliberacoes || [];

  const invalidateDetail = () => {
    qc.invalidateQueries({ queryKey: queryKeys.assembleias.byId(selectedId) });
    qc.invalidateQueries({ queryKey: queryKeys.assembleias.quorum(selectedId) });
    qc.invalidateQueries({ queryKey: queryKeys.assembleias.deliberacoes(selectedId) });
  };

  // ----- Forms locais -----
  const emptyConvocar = { tipo: 'ordinaria', titulo: '', data: '', local: '', requerente_tipo: '' };
  const [convocarForm, setConvocarForm] = useState(emptyConvocar);

  const [presenca, setPresenca] = useState({ presente: null, representados: [], repCurrent: null });

  const emptyDelib = { ponto: '', descricao: '', tipo_maioria: 'absoluta', votos_favor: 0, votos_contra: 0, abstencoes: 0, source_article: '' };
  const [delibForm, setDelibForm] = useState(emptyDelib);
  const [actaId, setActaId] = useState('');

  // ----- Mutações -----
  const convocarMutation = useMutation({
    mutationFn: (data) => assembleiasAPI.create(data),
    onSuccess: (res) => {
      toast.success('Assembleia convocada.');
      setConvocarOpen(false);
      setConvocarForm(emptyConvocar);
      qc.invalidateQueries({ queryKey: queryKeys.assembleias.list() });
      const newId = res.data?.id || res.data?.assembleia?.id;
      if (newId) setSelectedId(newId);
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao convocar a assembleia'),
  });

  const presencaMutation = useMutation({
    mutationFn: (data) => assembleiasAPI.addPresenca(selectedId, data),
    onSuccess: () => {
      toast.success('Presença registada.');
      setPresencaOpen(false);
      setPresenca({ presente: null, representados: [], repCurrent: null });
      invalidateDetail();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao registar a presença'),
  });

  const deliberacaoMutation = useMutation({
    mutationFn: (data) => assembleiasAPI.addDeliberacao(selectedId, data),
    onSuccess: (res) => {
      const aprovado = res.data?.aprovado ?? res.data?.deliberacao?.aprovado;
      toast.success(aprovado ? 'Deliberação registada — APROVADA.' : 'Deliberação registada — REJEITADA.');
      setDeliberacaoOpen(false);
      setDelibForm(emptyDelib);
      invalidateDetail();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao registar a deliberação'),
  });

  const encerrarMutation = useMutation({
    mutationFn: () => assembleiasAPI.encerrar(selectedId, acaParams()),
    onSuccess: () => {
      toast.success('Assembleia encerrada.');
      setEncerrarOpen(false);
      setActaId('');
      qc.invalidateQueries({ queryKey: queryKeys.assembleias.list() });
      invalidateDetail();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao encerrar a assembleia'),
  });

  const acaParams = () => (actaId.trim() ? { acta_document_id: actaId.trim() } : undefined);

  const submitConvocar = () => {
    const payload = {
      tipo: convocarForm.tipo,
      titulo: convocarForm.titulo.trim(),
      data: convocarForm.data ? new Date(convocarForm.data).toISOString() : null,
      local: convocarForm.local.trim() || null,
    };
    if (convocarForm.tipo === 'extraordinaria' && convocarForm.requerente_tipo) {
      payload.requerente_tipo = convocarForm.requerente_tipo;
    }
    convocarMutation.mutate(payload);
  };

  const submitPresenca = () => {
    presencaMutation.mutate({
      user_id: presenca.presente.id,
      representados: presenca.representados.map((r) => r.id),
    });
  };

  const submitDeliberacao = () => {
    deliberacaoMutation.mutate({
      ponto: delibForm.ponto.trim(),
      descricao: delibForm.descricao.trim() || null,
      tipo_maioria: delibForm.tipo_maioria,
      votos_favor: Number(delibForm.votos_favor) || 0,
      votos_contra: Number(delibForm.votos_contra) || 0,
      abstencoes: Number(delibForm.abstencoes) || 0,
      source_article: delibForm.source_article.trim() || null,
    });
  };

  const addRepresentado = () => {
    if (!presenca.repCurrent) return;
    if (presenca.representados.length >= 3) {
      toast.error('Máximo de 3 representados por presente.');
      return;
    }
    if (presenca.representados.some((r) => r.id === presenca.repCurrent.id)) return;
    setPresenca((p) => ({ ...p, representados: [...p.representados, p.repCurrent], repCurrent: null }));
  };

  const convocarValid = convocarForm.titulo.trim().length >= 3 && !!convocarForm.data;
  const isEncerrada = detail?.status === 'encerrada' || detail?.status === 'anulada';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-carmesim/10 flex items-center justify-center">
            <Landmark className="w-5 h-5 text-carmesim" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-grafite">Assembleia Geral</h1>
            <p className="text-sm text-[#6B7280]">Convocatórias, quórum e deliberações dos órgãos sociais.</p>
          </div>
        </div>
        {canManage && (
          <button onClick={() => setConvocarOpen(true)} className={primaryBtn} data-testid="convocar-btn">
            <PlusCircle className="w-4 h-4" aria-hidden="true" />Convocar assembleia
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,360px)_1fr] gap-6">
        {/* Lista de assembleias */}
        <div className="space-y-3">
          {isLoading ? (
            [...Array(4)].map((_, i) => <Skeleton key={i} className="h-24 w-full rounded-lg" />)
          ) : assembleias.length === 0 ? (
            <EmptyState
              icon={Landmark}
              title="Sem assembleias"
              description={canManage ? 'Convoque a primeira assembleia geral.' : 'Ainda não foram convocadas assembleias.'}
              testId="no-assembleias"
            />
          ) : (
            assembleias.map((a) => {
              const active = a.id === selectedId;
              return (
                <div key={a.id} className="relative">
                  <button
                    onClick={() => setSelectedId(a.id)}
                    className={`w-full text-left bg-white rounded-lg border shadow-sm p-4 transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 ${active ? 'border-carmesim ring-1 ring-carmesim/30' : 'border-[#E5E7EB] hover:bg-[#F5F5F5]'}`}
                    data-testid={`assembleia-row-${a.id}`}
                    aria-current={active ? 'true' : undefined}
                  >
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <TipoBadge tipo={a.tipo} />
                      <StatusBadge status={a.status} />
                    </div>
                    <p className="font-semibold text-grafite leading-snug">{a.titulo}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[#6B7280]">
                      <span className="inline-flex items-center gap-1"><Calendar className="w-3.5 h-3.5" aria-hidden="true" />{formatDateTime(a.data)}</span>
                      {a.local && <span className="inline-flex items-center gap-1"><MapPin className="w-3.5 h-3.5" aria-hidden="true" />{a.local}</span>}
                    </div>
                  </button>
                  {/* Entrada para a sala "ao vivo" (camada participativa) — sai do
                      botão pai p/ permitir click próprio sem `button-in-button`. */}
                  {(a.status === 'convocada' || a.status === 'em_curso') && (
                    <Link
                      to={`/assembleias/${a.id}`}
                      className="absolute right-3 bottom-3 text-xs text-carmesim hover:underline inline-flex items-center gap-1"
                      data-testid={`assembleia-sala-${a.id}`}
                    >
                      Sala ao vivo
                      <ChevronRight className="w-3 h-3" aria-hidden="true" />
                    </Link>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Detalhe */}
        <div>
          {!selectedId ? (
            <EmptyState
              icon={ChevronRight}
              title="Selecione uma assembleia"
              description="Escolha uma assembleia na lista para ver o quórum e as deliberações."
              testId="no-selection"
            />
          ) : detailLoading || !detail ? (
            <div className="space-y-4">
              <Skeleton className="h-28 w-full rounded-lg" />
              <Skeleton className="h-40 w-full rounded-lg" />
            </div>
          ) : (
            <div
              key={selectedId}
              className="space-y-5 animate-fade-up"
            >
              {/* Cabeçalho do detalhe */}
              <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <TipoBadge tipo={detail.tipo} />
                  <StatusBadge status={detail.status} />
                </div>
                <h2 className="text-lg font-bold text-grafite">{detail.titulo}</h2>
                <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-[#6B7280]">
                  <span className="inline-flex items-center gap-1.5"><Calendar className="w-4 h-4" aria-hidden="true" />{formatDateTime(detail.data)}</span>
                  {detail.local && <span className="inline-flex items-center gap-1.5"><MapPin className="w-4 h-4" aria-hidden="true" />{detail.local}</span>}
                </div>

                {Array.isArray(detail.ordem_trabalhos) && detail.ordem_trabalhos.length > 0 && (
                  <div className="mt-4">
                    <p className="text-xs font-semibold uppercase tracking-wider text-[#6B7280] mb-1.5">Ordem de trabalhos</p>
                    <ol className="list-decimal list-inside space-y-0.5 text-sm text-grafite">
                      {detail.ordem_trabalhos.map((p, i) => (
                        <li key={i}>{typeof p === 'string' ? p : (p?.titulo || p?.ponto || '—')}</li>
                      ))}
                    </ol>
                  </div>
                )}

                {detail.acta_document_id && (
                  <div className="mt-4">
                    <p className="text-xs font-semibold uppercase tracking-wider text-[#6B7280] mb-1.5">Acta</p>
                    <Link
                      to="/documentos"
                      className="inline-flex items-center gap-1.5 text-sm text-carmesim font-medium hover:underline focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 rounded"
                      data-testid="acta-link"
                    >
                      <FileText className="w-4 h-4" aria-hidden="true" /> Acta registada — ver na biblioteca de documentos
                    </Link>
                  </div>
                )}

                {/* Ações de gestão */}
                {canManage && (
                  <div className="mt-5 flex flex-wrap gap-2">
                    <button onClick={() => setPresencaOpen(true)} disabled={isEncerrada} className={secondaryBtn} data-testid="presenca-btn">
                      <UserPlus className="w-4 h-4" aria-hidden="true" />Registar presença
                    </button>
                    <button onClick={() => setDeliberacaoOpen(true)} disabled={isEncerrada} className={secondaryBtn} data-testid="deliberacao-btn">
                      <Gavel className="w-4 h-4" aria-hidden="true" />Registar deliberação
                    </button>
                    <button onClick={() => setEncerrarOpen(true)} disabled={isEncerrada} className={secondaryBtn} data-testid="encerrar-btn">
                      <Lock className="w-4 h-4" aria-hidden="true" />Encerrar
                    </button>
                  </div>
                )}
              </div>

              {/* Painel de quórum */}
              <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6" data-testid="quorum-panel">
                <h3 className="text-sm font-semibold text-grafite flex items-center gap-2 mb-4">
                  <Users className="w-4 h-4 text-[#6B7280]" aria-hidden="true" />Quórum
                </h3>
                {!quorum ? (
                  <Skeleton className="h-20 w-full rounded-md" />
                ) : (
                  <>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                      <VoteStat label="Eleitores" value={quorum.eligible_voters_count} color="text-grafite" />
                      <VoteStat label="Presentes" value={quorum.present_count} color="text-grafite" />
                      <VoteStat label="Poder de voto presente" value={quorum.present_voting_power} color="text-grafite" />
                      <VoteStat label="Chamada" value={quorum.chamada_actual} color="text-grafite" />
                    </div>
                    <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                      <div className="px-3 py-2 rounded-md bg-[#F5F5F5] border border-[#E5E7EB] flex items-center justify-between">
                        <span className="text-[#6B7280]">Quórum 1ª chamada</span>
                        <span className="font-semibold text-grafite">{quorum.quorum_required_primeira ?? '—'}</span>
                      </div>
                      <div className="px-3 py-2 rounded-md bg-[#F5F5F5] border border-[#E5E7EB] flex items-center justify-between">
                        <span className="text-[#6B7280]">Quórum 2ª chamada</span>
                        <span className="font-semibold text-grafite">{quorum.quorum_required_segunda ?? '—'}</span>
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {quorum.quorum_met ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[#BBF7D0] bg-[#F0FDF4] text-[#15803D] text-xs font-medium">
                          <CheckCircle2 className="w-4 h-4" aria-hidden="true" />Quórum atingido
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[#FECACA] bg-[#FEF2F2] text-[#B91C1C] text-xs font-medium">
                          <XCircle className="w-4 h-4" aria-hidden="true" />Sem quórum
                        </span>
                      )}
                      {quorum.pode_deliberar ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[#BBF7D0] bg-[#F0FDF4] text-[#15803D] text-xs font-medium">
                          <Gavel className="w-4 h-4" aria-hidden="true" />Pode deliberar
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[#FDE68A] bg-[#FFFBEB] text-[#B45309] text-xs font-medium">
                          <XCircle className="w-4 h-4" aria-hidden="true" />Não pode deliberar
                        </span>
                      )}
                    </div>
                  </>
                )}
              </div>

              {/* Deliberações */}
              <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6">
                <h3 className="text-sm font-semibold text-grafite flex items-center gap-2 mb-4">
                  <Gavel className="w-4 h-4 text-[#6B7280]" aria-hidden="true" />Deliberações
                </h3>
                {delibLoading ? (
                  <Skeleton className="h-24 w-full rounded-md" />
                ) : deliberacoes.length === 0 ? (
                  <p className="text-sm text-[#6B7280]">Ainda não há deliberações registadas.</p>
                ) : (
                  <ul className="space-y-3" data-testid="deliberacoes-list">
                    {deliberacoes.map((d) => (
                      <li key={d.id} className="rounded-md border border-[#E5E7EB] p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="font-semibold text-grafite">{d.ponto}</p>
                            {d.descricao && <p className="text-sm text-[#6B7280] mt-0.5">{d.descricao}</p>}
                          </div>
                          {d.aprovado ? (
                            <span className="shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-[#BBF7D0] bg-[#F0FDF4] text-[#15803D] text-xs font-medium">
                              <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />Aprovada
                            </span>
                          ) : (
                            <span className="shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-[#FECACA] bg-[#FEF2F2] text-[#B91C1C] text-xs font-medium">
                              <XCircle className="w-3.5 h-3.5" aria-hidden="true" />Rejeitada
                            </span>
                          )}
                        </div>
                        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[#6B7280]">
                          <span>{MAIORIA_LABELS[d.tipo_maioria] || d.tipo_maioria}</span>
                          {d.base_calculo != null && <span>· Base: {d.base_calculo}</span>}
                          {d.threshold != null && <span>· Limiar: {d.threshold}</span>}
                          {d.source_article && <span>· {d.source_article}</span>}
                        </div>
                        <div className="mt-3 grid grid-cols-3 gap-2 max-w-xs">
                          <VoteStat label="A favor" value={d.votos_favor} color="text-[#15803D]" />
                          <VoteStat label="Contra" value={d.votos_contra} color="text-[#B91C1C]" />
                          <VoteStat label="Abstenções" value={d.abstencoes} color="text-[#6B7280]" />
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modal: Convocar */}
      <Dialog open={convocarOpen} onOpenChange={(o) => { if (!o) { setConvocarOpen(false); setConvocarForm(emptyConvocar); } }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Convocar assembleia</DialogTitle>
            <DialogDescription>Defina o tipo, título, data e local da assembleia geral.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label htmlFor="convocar-tipo" className={labelCls}>Tipo</label>
              <select
                id="convocar-tipo"
                value={convocarForm.tipo}
                onChange={(e) => setConvocarForm({ ...convocarForm, tipo: e.target.value })}
                className={`${fieldCls} bg-white`}
                data-testid="convocar-tipo"
              >
                {TIPO_OPTIONS.map((t) => <option key={t} value={t}>{ASSEMBLEIA_TIPO_LABELS[t]}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="convocar-titulo" className={labelCls}>Título</label>
              <input
                id="convocar-titulo"
                type="text"
                value={convocarForm.titulo}
                onChange={(e) => setConvocarForm({ ...convocarForm, titulo: e.target.value })}
                placeholder="Ex.: Assembleia Geral Ordinária 2026"
                className={fieldCls}
                data-testid="convocar-titulo"
              />
              {convocarForm.titulo.trim().length > 0 && convocarForm.titulo.trim().length < 3 && (
                <p className="mt-1 text-xs text-[#B91C1C]">O título deve ter pelo menos 3 caracteres.</p>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label htmlFor="convocar-data" className={labelCls}>Data e hora</label>
                <input
                  id="convocar-data"
                  type="datetime-local"
                  value={convocarForm.data}
                  onChange={(e) => setConvocarForm({ ...convocarForm, data: e.target.value })}
                  className={fieldCls}
                  data-testid="convocar-data"
                />
              </div>
              <div>
                <label htmlFor="convocar-local" className={labelCls}>Local</label>
                <input
                  id="convocar-local"
                  type="text"
                  value={convocarForm.local}
                  onChange={(e) => setConvocarForm({ ...convocarForm, local: e.target.value })}
                  placeholder="Sede / Online"
                  className={fieldCls}
                  data-testid="convocar-local"
                />
              </div>
            </div>
            {convocarForm.tipo === 'extraordinaria' && (
              <div>
                <label htmlFor="convocar-requerente" className={labelCls}>Requerente (opcional)</label>
                <select
                  id="convocar-requerente"
                  value={convocarForm.requerente_tipo}
                  onChange={(e) => setConvocarForm({ ...convocarForm, requerente_tipo: e.target.value })}
                  className={`${fieldCls} bg-white`}
                  data-testid="convocar-requerente"
                >
                  <option value="">—</option>
                  <option value="direcao">Direcção</option>
                  <option value="conselho_fiscal">Conselho Fiscal</option>
                  <option value="socios">Sócios (1/5)</option>
                </select>
              </div>
            )}
            <div className="flex justify-end gap-2 pt-1">
              <button onClick={() => { setConvocarOpen(false); setConvocarForm(emptyConvocar); }} className={secondaryBtn}>Cancelar</button>
              <button
                onClick={submitConvocar}
                disabled={!convocarValid || convocarMutation.isPending}
                className={primaryBtn}
                data-testid="convocar-confirm"
              >
                {convocarMutation.isPending ? 'A convocar...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal: Registar presença */}
      <Dialog open={presencaOpen} onOpenChange={(o) => { if (!o) { setPresencaOpen(false); setPresenca({ presente: null, representados: [], repCurrent: null }); } }}>
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
              <button onClick={() => { setPresencaOpen(false); setPresenca({ presente: null, representados: [], repCurrent: null }); }} className={secondaryBtn}>Cancelar</button>
              <button
                onClick={submitPresenca}
                disabled={!presenca.presente || presencaMutation.isPending}
                className={primaryBtn}
                data-testid="presenca-confirm"
              >
                {presencaMutation.isPending ? 'A registar...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal: Registar deliberação */}
      <Dialog open={deliberacaoOpen} onOpenChange={(o) => { if (!o) { setDeliberacaoOpen(false); setDelibForm(emptyDelib); } }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Registar deliberação</DialogTitle>
            <DialogDescription>Indique o ponto, o tipo de maioria e a contagem de votos.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className={labelCls}>Ponto</label>
              <input
                type="text"
                value={delibForm.ponto}
                onChange={(e) => setDelibForm({ ...delibForm, ponto: e.target.value })}
                placeholder="Ex.: Aprovação das contas"
                className={fieldCls}
                data-testid="deliberacao-ponto"
              />
            </div>
            <div>
              <label className={labelCls}>Descrição (opcional)</label>
              <textarea
                value={delibForm.descricao}
                onChange={(e) => setDelibForm({ ...delibForm, descricao: e.target.value })}
                rows={2}
                maxLength={1000}
                className={`${fieldCls} resize-none`}
              />
            </div>
            <div>
              <label className={labelCls}>Tipo de maioria</label>
              <select
                value={delibForm.tipo_maioria}
                onChange={(e) => setDelibForm({ ...delibForm, tipo_maioria: e.target.value })}
                className={`${fieldCls} bg-white`}
                data-testid="deliberacao-maioria"
              >
                {MAIORIA_OPTIONS.map((m) => <option key={m} value={m}>{MAIORIA_LABELS[m]}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className={labelCls}>A favor</label>
                <input type="number" min={0} value={delibForm.votos_favor}
                  onChange={(e) => setDelibForm({ ...delibForm, votos_favor: e.target.value })}
                  className={fieldCls} data-testid="deliberacao-favor" />
              </div>
              <div>
                <label className={labelCls}>Contra</label>
                <input type="number" min={0} value={delibForm.votos_contra}
                  onChange={(e) => setDelibForm({ ...delibForm, votos_contra: e.target.value })}
                  className={fieldCls} data-testid="deliberacao-contra" />
              </div>
              <div>
                <label className={labelCls}>Abstenções</label>
                <input type="number" min={0} value={delibForm.abstencoes}
                  onChange={(e) => setDelibForm({ ...delibForm, abstencoes: e.target.value })}
                  className={fieldCls} data-testid="deliberacao-abstencoes" />
              </div>
            </div>
            <div>
              <label className={labelCls}>Artigo de base (opcional)</label>
              <input
                type="text"
                value={delibForm.source_article}
                onChange={(e) => setDelibForm({ ...delibForm, source_article: e.target.value })}
                placeholder="Ex.: Art. 23.º CV-CAR 2.3/2026"
                className={fieldCls}
                data-testid="deliberacao-artigo"
              />
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <button onClick={() => { setDeliberacaoOpen(false); setDelibForm(emptyDelib); }} className={secondaryBtn}>Cancelar</button>
              <button
                onClick={submitDeliberacao}
                disabled={delibForm.ponto.trim().length < 1 || deliberacaoMutation.isPending}
                className={primaryBtn}
                data-testid="deliberacao-confirm"
              >
                {deliberacaoMutation.isPending ? 'A registar...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal: Encerrar */}
      <Dialog open={encerrarOpen} onOpenChange={(o) => { if (!o) { setEncerrarOpen(false); setActaId(''); } }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Encerrar assembleia</DialogTitle>
            <DialogDescription>
              Confirma o encerramento de “{detail?.titulo}”? Esta ação fixa as deliberações registadas.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className={labelCls}>ID do documento da acta (opcional)</label>
              <input
                type="text"
                value={actaId}
                onChange={(e) => setActaId(e.target.value)}
                placeholder="ID do documento carregado"
                className={fieldCls}
                data-testid="encerrar-acta"
              />
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <button onClick={() => { setEncerrarOpen(false); setActaId(''); }} className={secondaryBtn}>Cancelar</button>
              <button
                onClick={() => encerrarMutation.mutate()}
                disabled={encerrarMutation.isPending}
                className={primaryBtn}
                data-testid="encerrar-confirm"
              >
                {encerrarMutation.isPending ? 'A encerrar...' : 'Confirmar encerramento'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminAssembleiasPage;
