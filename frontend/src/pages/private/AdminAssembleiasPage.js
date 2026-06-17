import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { assembleiasAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { Landmark, ChevronRight, PlusCircle } from 'lucide-react';
import { EmptyState } from '../../components/EmptyState';
import { primaryBtn } from '../../lib/buttonStyles';
import { Skeleton } from '../../components/ui/skeleton';

import {
  EMPTY_CONVOCAR, EMPTY_PRESENCA, EMPTY_DELIB,
} from './assembleias/tokens';
import { AssembleiaListItem } from './assembleias/AssembleiaListItem';
import { DetailHeader } from './assembleias/DetailHeader';
import { QuorumPanel } from './assembleias/QuorumPanel';
import { DeliberacoesList } from './assembleias/DeliberacoesList';
import { ConvocarModal } from './assembleias/ConvocarModal';
import { PresencaModal } from './assembleias/PresencaModal';
import { DeliberacaoModal } from './assembleias/DeliberacaoModal';
import { EncerrarModal } from './assembleias/EncerrarModal';

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
  const [convocarForm, setConvocarForm] = useState(EMPTY_CONVOCAR);
  const [presenca, setPresenca] = useState(EMPTY_PRESENCA);
  const [delibForm, setDelibForm] = useState(EMPTY_DELIB);
  const [actaId, setActaId] = useState('');

  // ----- Mutações -----
  const convocarMutation = useMutation({
    mutationFn: (data) => assembleiasAPI.create(data),
    onSuccess: (res) => {
      toast.success('Assembleia convocada.');
      setConvocarOpen(false);
      setConvocarForm(EMPTY_CONVOCAR);
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
      setPresenca(EMPTY_PRESENCA);
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
      setDelibForm(EMPTY_DELIB);
      invalidateDetail();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao registar a deliberação'),
  });

  const encerrarMutation = useMutation({
    mutationFn: () => assembleiasAPI.encerrar(selectedId, actaId.trim() ? { acta_document_id: actaId.trim() } : undefined),
    onSuccess: () => {
      toast.success('Assembleia encerrada.');
      setEncerrarOpen(false);
      setActaId('');
      qc.invalidateQueries({ queryKey: queryKeys.assembleias.list() });
      invalidateDetail();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao encerrar a assembleia'),
  });

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
            assembleias.map((a) => (
              <AssembleiaListItem
                key={a.id}
                assembleia={a}
                active={a.id === selectedId}
                onSelect={setSelectedId}
              />
            ))
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
            <div key={selectedId} className="space-y-5 animate-fade-up">
              <DetailHeader
                detail={detail}
                canManage={canManage}
                isEncerrada={isEncerrada}
                onPresenca={() => setPresencaOpen(true)}
                onDeliberacao={() => setDeliberacaoOpen(true)}
                onEncerrar={() => setEncerrarOpen(true)}
              />
              <QuorumPanel quorum={quorum} />
              <DeliberacoesList deliberacoes={deliberacoes} loading={delibLoading} />
            </div>
          )}
        </div>
      </div>

      <ConvocarModal
        open={convocarOpen}
        onClose={() => { setConvocarOpen(false); setConvocarForm(EMPTY_CONVOCAR); }}
        form={convocarForm}
        setForm={setConvocarForm}
        onSubmit={submitConvocar}
        pending={convocarMutation.isPending}
      />

      <PresencaModal
        open={presencaOpen}
        onClose={() => { setPresencaOpen(false); setPresenca(EMPTY_PRESENCA); }}
        presenca={presenca}
        setPresenca={setPresenca}
        onSubmit={submitPresenca}
        pending={presencaMutation.isPending}
      />

      <DeliberacaoModal
        open={deliberacaoOpen}
        onClose={() => { setDeliberacaoOpen(false); setDelibForm(EMPTY_DELIB); }}
        form={delibForm}
        setForm={setDelibForm}
        onSubmit={submitDeliberacao}
        pending={deliberacaoMutation.isPending}
      />

      <EncerrarModal
        open={encerrarOpen}
        onClose={() => { setEncerrarOpen(false); setActaId(''); }}
        titulo={detail?.titulo}
        actaId={actaId}
        setActaId={setActaId}
        onSubmit={() => encerrarMutation.mutate()}
        pending={encerrarMutation.isPending}
      />
    </div>
  );
};

export default AdminAssembleiasPage;
