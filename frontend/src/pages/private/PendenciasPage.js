import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Vote, Calendar, FileCheck, FileText, ChevronRight, ClipboardCheck } from 'lucide-react';
import { pollsAPI, eventsAPI, atosAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { queryKeys } from '../../lib/queryClient';

// Painel «As minhas pendências» (spec 014): vista que agrega, num só sítio, tudo o
// que aguarda a ação do sócio — DERIVADO do estado dos reads existentes (frontend-only).
// Role-aware: sócio comum vê votações + eventos; Direção/admin vê também os Atos
// (só Direção/admin propõem/listam Atos — um sócio comum levaria 403 em GET /atos,
// por isso essas queries só correm com `enabled: isDir`).

const fmtDate = (value) => {
  try {
    return new Date(value).toLocaleDateString('pt-PT', { day: '2-digit', month: 'short' });
  } catch {
    return null;
  }
};

const PendenciaRow = ({ to, title, meta, cta }) => (
  <Link
    to={to}
    className="flex items-center justify-between gap-3 px-5 py-3 hover:bg-[#F5F5F5] transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
  >
    <div className="min-w-0">
      <p className="text-[#3A3A3A] font-medium truncate">{title}</p>
      {meta && <p className="text-sm text-[#6B7280] truncate">{meta}</p>}
    </div>
    <span className="flex items-center gap-1 shrink-0 text-[#C7202F] text-sm font-semibold">
      {cta}
      <ChevronRight className="w-4 h-4" aria-hidden="true" />
    </span>
  </Link>
);

const PendenciaSection = ({ icon: Icon, title, items }) => {
  if (!items.length) return null;
  return (
    <section className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm overflow-hidden">
      <header className="flex items-center gap-3 px-5 py-4 border-b border-[#E5E7EB]">
        <Icon className="w-5 h-5 text-[#6B7280]" aria-hidden="true" />
        <h2 className="font-semibold text-[#3A3A3A] flex-1">{title}</h2>
        <span className="text-xs font-semibold text-[#6B7280] bg-[#F5F5F5] px-2 py-0.5 rounded-full">
          {items.length}
        </span>
      </header>
      <div className="divide-y divide-[#E5E7EB]">
        {items.map((it) => (
          <PendenciaRow key={it.id} to={it.to} title={it.title} meta={it.meta} cta={it.cta} />
        ))}
      </div>
    </section>
  );
};

const SectionSkeleton = () => (
  <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-5 animate-pulse">
    <div className="h-5 w-48 bg-[#F5F5F5] rounded mb-4" />
    <div className="space-y-3">
      <div className="h-10 bg-[#F5F5F5] rounded" />
      <div className="h-10 bg-[#F5F5F5] rounded" />
    </div>
  </div>
);

export const PendenciasPage = () => {
  const { user, isAdmin, isDirecao } = useAuth();
  const isDir = Boolean(isAdmin || isDirecao);

  const { data: polls = [], isLoading: pollsLoading } = useQuery({
    queryKey: queryKeys.polls.list(),
    queryFn: async () => (await pollsAPI.getAll()).data,
  });
  const { data: events = [], isLoading: eventsLoading } = useQuery({
    queryKey: queryKeys.events.upcoming(),
    queryFn: async () => (await eventsAPI.getUpcoming()).data,
  });
  // Atos só para Direção/admin — evita o 403 de _require_view ao sócio comum.
  const { data: assinatura, isLoading: assLoading } = useQuery({
    queryKey: queryKeys.atos.list({ mine: true }),
    queryFn: async () => (await atosAPI.list({ pendentes_para_mim: true })).data,
    enabled: isDir,
  });
  const { data: propostos, isLoading: propLoading } = useQuery({
    queryKey: queryKeys.atos.list({ status: 'pendente' }),
    queryFn: async () => (await atosAPI.list({ status: 'pendente' })).data,
    enabled: isDir,
  });

  const votacoes = (polls || []).filter((p) => p.status === 'aberta' && !p.has_voted);
  const eventos = (events || []).filter((e) => !(e.attendees || []).includes(user?.id));
  const assinaturaItems = isDir ? assinatura?.items || [] : [];
  const propostosItems = isDir
    ? (propostos?.items || []).filter((a) => a.created_by === user?.id)
    : [];

  const sections = [
    isDir && {
      key: 'assinatura',
      icon: FileCheck,
      title: 'Atos à minha assinatura',
      items: assinaturaItems.map((a) => ({
        id: a.id,
        to: '/financeiro/co-aprovacoes',
        title: a.descricao || 'Ato de co-aprovação',
        meta: a.tipo || null,
        cta: 'Assinar',
      })),
    },
    isDir && {
      key: 'propostos',
      icon: FileText,
      title: 'Atos que propus (pendentes)',
      items: propostosItems.map((a) => ({
        id: a.id,
        to: '/financeiro/co-aprovacoes',
        title: a.descricao || 'Ato de co-aprovação',
        meta: 'a aguardar a Direção',
        cta: 'Ver',
      })),
    },
    {
      key: 'votacoes',
      icon: Vote,
      title: 'Votações por votar',
      items: votacoes.map((p) => ({
        id: p.id,
        to: '/votacoes',
        title: p.title || p.question || 'Votação',
        meta: null,
        cta: 'Votar',
      })),
    },
    {
      key: 'eventos',
      icon: Calendar,
      title: 'Eventos por confirmar',
      items: eventos.map((e) => ({
        id: e.id,
        to: '/eventos',
        title: e.title || 'Evento',
        meta: e.date ? fmtDate(e.date) : null,
        cta: 'Confirmar presença',
      })),
    },
  ].filter(Boolean);

  const isLoading = pollsLoading || eventsLoading || (isDir && (assLoading || propLoading));
  const total = sections.reduce((n, s) => n + s.items.length, 0);

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-[#3A3A3A]">As minhas pendências</h1>
        <p className="text-[#6B7280] mt-1">Tudo o que aguarda a sua ação, num só sítio.</p>
      </header>

      {isLoading ? (
        <div className="space-y-5">
          <SectionSkeleton />
          <SectionSkeleton />
        </div>
      ) : total === 0 ? (
        <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm py-16 px-6 text-center">
          <ClipboardCheck className="w-12 h-12 text-[#15803D] mx-auto mb-4" aria-hidden="true" />
          <p className="text-lg font-semibold text-[#3A3A3A]">Está tudo em dia</p>
          <p className="text-[#6B7280] mt-1">Não tem nada pendente neste momento.</p>
        </div>
      ) : (
        <motion.div
          className="space-y-5"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {sections.map((s) => (
            <PendenciaSection key={s.key} icon={s.icon} title={s.title} items={s.items} />
          ))}
        </motion.div>
      )}
    </div>
  );
};
