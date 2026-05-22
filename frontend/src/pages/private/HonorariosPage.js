import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { honorariosAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { Medal, Plus, Vote, Gavel, Loader2, ArrowRight } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';
import { Link } from 'react-router-dom';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../components/ui/dialog';

const STATUS = {
  proposta: { label: 'Proposta', cls: 'bg-[#FFFBEB] text-[#B45309]' },
  em_votacao: { label: 'Em votação', cls: 'bg-[#EFF6FF] text-[#1D4ED8]' },
  eleito: { label: 'Eleito', cls: 'bg-[#F0FDF4] text-[#15803D]' },
  rejeitado: { label: 'Rejeitado', cls: 'bg-[#F5F5F5] text-[#6B7280]' },
};

export const HonorariosPage = () => {
  const qc = useQueryClient();
  const { isAdmin, isDirecao, isMesaAG } = useAuth();
  const canSee = isAdmin || isDirecao || isMesaAG;
  const canNominate = isAdmin || isDirecao;
  const canManageVote = isAdmin || isMesaAG; // abrir/apurar votação (Mesa da AG)

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ nominee_name: '', justificacao: '', nominee_email: '' });
  const [statusFilter, setStatusFilter] = useState('');

  const KEY = ['honorarios', statusFilter];
  const { data: itens = [], isLoading } = useQuery({
    queryKey: KEY,
    queryFn: async () => (await honorariosAPI.list(statusFilter || undefined)).data,
    enabled: canSee,
  });
  const invalidate = () => qc.invalidateQueries({ queryKey: ['honorarios'] });

  const createMut = useMutation({
    mutationFn: () =>
      honorariosAPI.create({
        nominee_name: form.nominee_name,
        justificacao: form.justificacao,
        nominee_email: form.nominee_email.trim() || null,
      }),
    onSuccess: () => {
      toast.success('Nomeação registada. A Mesa da AG pode abrir a votação.');
      invalidate();
      setShowCreate(false);
      setForm({ nominee_name: '', justificacao: '', nominee_email: '' });
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao nomear'),
  });
  const abrirMut = useMutation({
    mutationFn: (id) => honorariosAPI.abrirVotacao(id),
    onSuccess: () => { toast.success('Votação aberta. Os sócios votantes foram notificados.'); invalidate(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao abrir votação'),
  });
  const apurarMut = useMutation({
    mutationFn: (id) => honorariosAPI.apurar(id),
    onSuccess: (res) => {
      const eleito = res?.data?.status === 'eleito';
      toast.success(eleito ? 'Apurado: eleito por 2/3.' : 'Apurado: não atingiu os 2/3.');
      invalidate();
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao apurar'),
  });

  if (!canSee) {
    return (
      <EmptyState
        icon={Medal}
        title="Sem permissão"
        description="A gestão de membros honorários está reservada à Direcção e à Mesa da Assembleia Geral."
        testId="honorarios-no-access"
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="page-title" data-testid="honorarios-title">Membros honorários</h1>
          <p className="page-subtitle">A Direcção nomeia; a Assembleia Geral vota e elege com maioria de 2/3 (Art. 8.4). O membro honorário não tem direito a voto.</p>
        </div>
        {canNominate && (
          <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 bg-carmesim text-white px-4 py-2 rounded-lg hover:bg-carmesim-dark transition-colors text-sm font-semibold cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="new-honorario-btn">
            <Plus className="w-4 h-4" aria-hidden="true" /> Nomear honorário
          </button>
        )}
      </div>

      <div className="flex items-center gap-2">
        <label className="text-xs font-medium text-[#6B7280]">Filtrar por estado</label>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-3 py-1.5 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="honorario-filter">
          <option value="">Todos</option>
          {Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-28 w-full rounded-lg" />)}</div>
      ) : itens.length === 0 ? (
        <EmptyState icon={Medal} title="Sem nomeações" testId="no-honorarios" />
      ) : (
        <div className="space-y-3">
          {itens.map((h) => {
            const st = STATUS[h.status] || STATUS.proposta;
            const decidido = h.status === 'eleito' || h.status === 'rejeitado';
            return (
              <div key={h.id} className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-4 space-y-2" data-testid={`honorario-${h.id}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="font-semibold text-grafite">{h.nominee_name}</h3>
                    <p className="text-xs text-[#6B7280]">
                      {h.nominee_email ? `${h.nominee_email} · ` : ''}
                      {h.created_at ? format(new Date(h.created_at), 'dd MMM yyyy', { locale: ptBR }) : ''}
                    </p>
                  </div>
                  <span className={`shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${st.cls}`}>{st.label}</span>
                </div>
                <p className="text-sm text-grafite whitespace-pre-wrap">{h.justificacao}</p>

                {decidido && h.votos_total_base != null && (
                  <div className="rounded-md bg-[#F5F5F5] p-3">
                    <p className="text-xs font-medium text-[#6B7280] mb-1">Resultado da votação (2/3 dos votos válidos)</p>
                    <p className="text-sm text-grafite">{h.votos_favor} a favor em {h.votos_total_base} válidos {h.status === 'eleito' ? '— eleito.' : '— não atingiu os 2/3.'}</p>
                  </div>
                )}

                {(h.status === 'proposta' || h.status === 'em_votacao') && (
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    {canManageVote && h.status === 'proposta' && (
                      <button onClick={() => abrirMut.mutate(h.id)} disabled={abrirMut.isPending} className="inline-flex items-center gap-1.5 border border-[#D1D5DB] text-grafite px-3 py-2 rounded-md text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`abrir-${h.id}`}>
                        <Vote className="w-4 h-4" aria-hidden="true" /> Abrir votação
                      </button>
                    )}
                    {h.status === 'em_votacao' && (
                      <Link to="/votacoes" className="inline-flex items-center gap-1.5 border border-[#D1D5DB] text-grafite px-3 py-2 rounded-md text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`ver-votacao-${h.id}`}>
                        Ver votação <ArrowRight className="w-4 h-4" aria-hidden="true" />
                      </Link>
                    )}
                    {canManageVote && h.status === 'em_votacao' && (
                      <button onClick={() => apurarMut.mutate(h.id)} disabled={apurarMut.isPending} className="inline-flex items-center gap-1.5 border border-[#D1D5DB] text-grafite px-3 py-2 rounded-md text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`apurar-${h.id}`}>
                        <Gavel className="w-4 h-4" aria-hidden="true" /> Apurar e fechar votação
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <Dialog open={showCreate} onOpenChange={(o) => { if (!o) setShowCreate(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Nomear membro honorário</DialogTitle><DialogDescription>Proposta da Direcção (Art. 8.4). A Assembleia Geral elege com 2/3 dos votos válidos.</DialogDescription></DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Nome do nomeado *</label>
              <input type="text" value={form.nominee_name} maxLength={120} onChange={(e) => setForm({ ...form, nominee_name: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="hon-nome" />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Email (opcional)</label>
              <input type="email" value={form.nominee_email} onChange={(e) => setForm({ ...form, nominee_email: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="hon-email" />
              <p className="text-xs text-[#6B7280] mt-1">Se for um sócio existente, é elevado a honorário ao ser eleito. Se for uma pessoa externa, recebe um convite para criar conta.</p>
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Justificação (serviços relevantes) *</label>
              <textarea value={form.justificacao} maxLength={4000} rows={4} onChange={(e) => setForm({ ...form, justificacao: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="hon-justificacao" />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer">Cancelar</button>
              <button onClick={() => createMut.mutate()} disabled={createMut.isPending || form.nominee_name.trim().length < 2 || !form.justificacao.trim()} className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-carmesim text-white text-sm font-semibold hover:bg-carmesim-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="hon-submit">
                {createMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Plus className="w-4 h-4" aria-hidden="true" />} Nomear
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default HonorariosPage;
