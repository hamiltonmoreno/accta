import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  CalendarRange, CheckCircle2, Layers, ListChecks, Trophy, Vote, XCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import { eleicoesAPI } from '../../../utils/api';
import { queryKeys } from '../../../lib/queryClient';
import { Skeleton } from '../../../components/ui/skeleton';
import { primaryBtn } from '../../../lib/buttonStyles';
import { MODO_LABELS, ESTADO_LISTA_STYLE, formatDate, secondaryBtn } from './tokens';
import { StatusBadge } from './StatusBadge';
import { SubmeterListaModal } from './SubmeterListaModal';
import { VotarModal } from './VotarModal';
import { ValidarListaModal } from './ValidarListaModal';
import { VotoCorrespondenciaModal } from './VotoCorrespondenciaModal';
import { ResultadoPanel } from './ResultadoPanel';

export const EleicaoDetail = ({ eleicaoId, structure, canManage, isVotingMember, qc }) => {
  const [submeterOpen, setSubmeterOpen] = useState(false);
  const [votarOpen, setVotarOpen] = useState(false);
  const [corrOpen, setCorrOpen] = useState(false);
  const [validarLista, setValidarLista] = useState(null);

  const { data: detail, isLoading } = useQuery({
    queryKey: queryKeys.eleicoes.byId(eleicaoId),
    queryFn: async () => (await eleicoesAPI.get(eleicaoId)).data,
    enabled: !!eleicaoId,
  });

  const { data: listasResp } = useQuery({
    queryKey: queryKeys.eleicoes.listas(eleicaoId),
    queryFn: async () => (await eleicoesAPI.listas(eleicaoId)).data,
    enabled: !!eleicaoId,
  });

  const listas = listasResp?.listas || [];
  const slots = detail?.slots || [];
  const status = detail?.status;
  const resultado = detail?.resultado || {};

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['eleicoes'] });
  };

  const submitListaMutation = useMutation({
    mutationFn: (data) => eleicoesAPI.submitLista(eleicaoId, data),
    onSuccess: () => { toast.success('Lista submetida.'); setSubmeterOpen(false); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao submeter a lista'),
  });

  const validarMutation = useMutation({
    mutationFn: ({ listaId, data }) => eleicoesAPI.validarLista(eleicaoId, listaId, data),
    onSuccess: () => { toast.success('Lista validada.'); setValidarLista(null); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao validar a lista'),
  });

  const abrirMutation = useMutation({
    mutationFn: () => eleicoesAPI.abrirVotacao(eleicaoId),
    onSuccess: () => { toast.success('Votação aberta.'); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao abrir a votação'),
  });

  const votarMutation = useMutation({
    mutationFn: (data) => eleicoesAPI.votar(eleicaoId, data),
    onSuccess: () => { toast.success('Voto registado.'); setVotarOpen(false); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao registar o voto'),
  });

  const corrMutation = useMutation({
    mutationFn: (data) => eleicoesAPI.votoCorrespondencia(eleicaoId, data),
    onSuccess: () => { toast.success('Voto por correspondência registado.'); setCorrOpen(false); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao registar o voto'),
  });

  const apurarMutation = useMutation({
    mutationFn: () => eleicoesAPI.apurar(eleicaoId),
    onSuccess: () => { toast.success('Eleição apurada.'); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao apurar a eleição'),
  });

  const proclamarMutation = useMutation({
    mutationFn: () => eleicoesAPI.proclamar(eleicaoId),
    onSuccess: (res) => { toast.success(res.data?.message || 'Eleição proclamada.'); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao proclamar a eleição'),
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-24 w-full rounded-lg" />
        <Skeleton className="h-40 w-full rounded-lg" />
      </div>
    );
  }
  if (!detail) return null;

  const showResultado = status === 'apurada' || status === 'proclamada';
  const canProclamar = status === 'apurada' && resultado.vencedora && !resultado.empate;
  const canVotar = isVotingMember && status === 'votacao';

  return (
    <div className="space-y-5">
      {/* Resumo */}
      <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-bold text-grafite">Eleição {detail.ano}</h2>
            <StatusBadge status={status} />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {canVotar && (
              <button type="button" onClick={() => setVotarOpen(true)} className={primaryBtn} data-testid="votar-btn">
                <Vote className="w-4 h-4 inline -mt-0.5 mr-1.5" aria-hidden="true" />Votar
              </button>
            )}
            {canManage && status === 'candidaturas' && (
              <>
                <button type="button" onClick={() => setSubmeterOpen(true)} className={secondaryBtn} data-testid="submeter-lista-btn">
                  Submeter lista
                </button>
                <button
                  type="button"
                  onClick={() => abrirMutation.mutate()}
                  disabled={abrirMutation.isPending}
                  className={primaryBtn}
                  data-testid="abrir-votacao-btn"
                >
                  {abrirMutation.isPending ? 'A abrir...' : 'Abrir votação'}
                </button>
              </>
            )}
            {canManage && status === 'votacao' && (detail.modo_votacao === 'correspondencia' || detail.modo_votacao === 'hibrido') && (
              <button type="button" onClick={() => setCorrOpen(true)} className={secondaryBtn} data-testid="voto-corr-btn">
                Voto por correspondência
              </button>
            )}
            {canManage && status === 'votacao' && (
              <button
                type="button"
                onClick={() => apurarMutation.mutate()}
                disabled={apurarMutation.isPending}
                className={secondaryBtn}
                data-testid="apurar-btn"
              >
                {apurarMutation.isPending ? 'A apurar...' : 'Apurar'}
              </button>
            )}
            {canManage && canProclamar && (
              <button
                type="button"
                onClick={() => proclamarMutation.mutate()}
                disabled={proclamarMutation.isPending}
                className={primaryBtn}
                data-testid="proclamar-btn"
              >
                {proclamarMutation.isPending ? 'A proclamar...' : 'Proclamar'}
              </button>
            )}
          </div>
        </div>

        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div>
            <dt className="text-xs text-[#6B7280] flex items-center gap-1"><Vote className="w-3.5 h-3.5" aria-hidden="true" />Modo</dt>
            <dd className="text-grafite font-medium">{MODO_LABELS[detail.modo_votacao] || detail.modo_votacao || '—'}</dd>
          </div>
          <div>
            <dt className="text-xs text-[#6B7280] flex items-center gap-1"><CalendarRange className="w-3.5 h-3.5" aria-hidden="true" />Mandato</dt>
            <dd className="text-grafite font-medium">{formatDate(detail.mandato_inicio)} – {formatDate(detail.mandato_fim)}</dd>
          </div>
          <div>
            <dt className="text-xs text-[#6B7280] flex items-center gap-1"><Layers className="w-3.5 h-3.5" aria-hidden="true" />Lugares</dt>
            <dd className="text-grafite font-medium">{slots.length}</dd>
          </div>
          <div>
            <dt className="text-xs text-[#6B7280] flex items-center gap-1"><ListChecks className="w-3.5 h-3.5" aria-hidden="true" />Listas</dt>
            <dd className="text-grafite font-medium">{listas.length}</dd>
          </div>
        </dl>
      </div>

      {/* Listas */}
      <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6">
        <h3 className="text-sm font-semibold text-grafite mb-3">Listas candidatas</h3>
        {listas.length === 0 ? (
          <p className="text-sm text-[#6B7280]">Ainda não há listas submetidas.</p>
        ) : (
          <div className="space-y-2">
            {listas.map((l) => {
              const es = ESTADO_LISTA_STYLE[l.estado] || ESTADO_LISTA_STYLE.submetida;
              return (
                <div key={l.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 rounded-md border border-[#E5E7EB]" data-testid={`lista-${l.id}`}>
                  <div className="min-w-0">
                    <span className="text-sm text-grafite">
                      <span className="font-semibold">Lista {l.letra}</span>
                      {l.nome && <span className="text-[#6B7280] ml-2">{l.nome}</span>}
                    </span>
                    <span className="block text-xs text-[#6B7280]">{(l.candidatos || []).length} candidatos</span>
                    {l.estado === 'rejeitada' && l.rejeicao_motivo && (
                      <span className="block text-xs text-[#B91C1C] mt-0.5">{l.rejeicao_motivo}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${es.bg} ${es.fg}`}>
                      {l.estado === 'aceite' && <CheckCircle2 className="w-3 h-3" aria-hidden="true" />}
                      {l.estado === 'rejeitada' && <XCircle className="w-3 h-3" aria-hidden="true" />}
                      {es.label}
                    </span>
                    {canManage && status === 'candidaturas' && l.estado === 'submetida' && (
                      <button
                        type="button"
                        onClick={() => setValidarLista(l)}
                        className={secondaryBtn + ' !px-3 !py-1 text-xs'}
                        data-testid={`validar-lista-${l.id}`}
                      >
                        Validar
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Resultado (agregado apenas) */}
      {showResultado && (
        <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6">
          <h3 className="text-sm font-semibold text-grafite mb-3 flex items-center gap-2">
            <Trophy className="w-4 h-4 text-[#15803D]" aria-hidden="true" />Resultado
          </h3>
          <ResultadoPanel resultado={resultado} listas={listas} />
        </div>
      )}

      {/* Modais */}
      <SubmeterListaModal
        open={submeterOpen}
        onClose={() => setSubmeterOpen(false)}
        onSubmit={(data) => submitListaMutation.mutate(data)}
        pending={submitListaMutation.isPending}
        slots={slots}
        structure={structure}
      />
      <VotarModal
        open={votarOpen}
        onClose={() => setVotarOpen(false)}
        onSubmit={(data) => votarMutation.mutate(data)}
        pending={votarMutation.isPending}
        listas={listas}
      />
      <VotoCorrespondenciaModal
        open={corrOpen}
        onClose={() => setCorrOpen(false)}
        onSubmit={(data) => corrMutation.mutate(data)}
        pending={corrMutation.isPending}
        listas={listas}
      />
      <ValidarListaModal
        lista={validarLista}
        structure={structure}
        onClose={() => setValidarLista(null)}
        onSubmit={(data) => validarMutation.mutate({ listaId: validarLista.id, data })}
        pending={validarMutation.isPending}
      />
    </div>
  );
};
