import React, { useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft, FileText, Gavel, KeyRound, Mail, Mic, ShieldCheck, UserPlus, Users, Vote,
} from 'lucide-react';

import { assembleiasAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { useAssembleiaStream } from '../../hooks/useAssembleiaStream';

import { cardCls, sectionTitle, formatDateTime } from './assembleia/tokens';
import { StatusBadge, PhaseBadge } from './assembleia/badges';
import { QuorumBar } from './assembleia/QuorumBar';
import { Countdown } from './assembleia/Countdown';
import { FaseControls } from './assembleia/FaseControls';
import { CheckinMesaPanel } from './assembleia/CheckinMesaPanel';
import { CheckinParticipantePanel } from './assembleia/CheckinParticipantePanel';
import { PalavraPanel } from './assembleia/PalavraPanel';
import { VotacaoPanel } from './assembleia/VotacaoPanel';
import { MocoesPanel } from './assembleia/MocoesPanel';
import { ExpedientePanel } from './assembleia/ExpedientePanel';
import { DocumentosPanel } from './assembleia/DocumentosPanel';
import { ConvidadosPanel } from './assembleia/ConvidadosPanel';

// Re-exporta os componentes testados para manter o contrato de
// `require('../AssembleiaSalaPage')` da suite de testes em AssembleiaSalaPage.test.js.
export {
  QuorumBar,
  Countdown,
  CheckinParticipantePanel,
  PalavraPanel,
  VotacaoPanel,
  MocoesPanel,
};

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
