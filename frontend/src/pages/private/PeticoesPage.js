import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { peticoesAPI, assembleiasAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { FileSignature, Plus, Check, Loader2, Megaphone, Link2 } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../components/ui/dialog';

const PETICOES_KEY = ['peticoes'];
const STATUS_LABEL = {
  aberta: { label: 'Aberta', cls: 'bg-[#EFF6FF] text-[#1D4ED8]' },
  atingida: { label: 'Limiar atingido', cls: 'bg-[#F0FDF4] text-[#15803D]' },
  encaminhada: { label: 'Encaminhada à Mesa', cls: 'bg-[#FBEAEC] text-carmesim' },
  encerrada: { label: 'Encerrada', cls: 'bg-[#F5F5F5] text-[#6B7280]' },
  expirada: { label: 'Expirada', cls: 'bg-[#F5F5F5] text-[#6B7280]' },
};

export const PeticoesPage = () => {
  const qc = useQueryClient();
  const { isMesaAG, isAdmin } = useAuth();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ titulo: '', fundamentacao: '' });
  const [fwdAssembleia, setFwdAssembleia] = useState({}); // { [peticaoId]: assembleia_id }
  const canForward = isMesaAG || isAdmin;

  const { data: peticoes = [], isLoading } = useQuery({
    queryKey: PETICOES_KEY,
    queryFn: async () => (await peticoesAPI.list()).data,
  });
  // Assembleias para ligar a petição ao encaminhar e para resolver o título (§2.4).
  const { data: assembleias = [] } = useQuery({
    queryKey: ['assembleias', 'para-ligar'],
    queryFn: async () => (await assembleiasAPI.list()).data,
    enabled: canForward,
  });
  const assembleiaLabel = (id) => assembleias.find((a) => a.id === id)?.titulo || id;

  const invalidate = () => qc.invalidateQueries({ queryKey: PETICOES_KEY });

  const createMut = useMutation({
    mutationFn: () => peticoesAPI.create(form),
    onSuccess: () => { toast.success('Petição criada.'); invalidate(); setShowCreate(false); setForm({ titulo: '', fundamentacao: '' }); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao criar petição'),
  });

  const signMut = useMutation({
    mutationFn: ({ id, signed }) => (signed ? peticoesAPI.retirar(id) : peticoesAPI.assinar(id)),
    onSuccess: () => invalidate(),
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao assinar'),
  });

  const fwdMut = useMutation({
    mutationFn: ({ id, assembleiaId }) => peticoesAPI.encaminhar(id, assembleiaId || undefined),
    onSuccess: () => { toast.success('Petição encaminhada à Mesa da AG.'); invalidate(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao encaminhar'),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="page-title" data-testid="peticoes-title">Petições</h1>
          <p className="page-subtitle">Peça a convocação de uma Assembleia Geral extraordinária (Art. 9.f / 19.2.d). Ao atingir 1/4 dos sócios votantes, a Mesa é notificada.</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-carmesim text-white px-4 py-2 rounded-lg hover:bg-carmesim-dark transition-colors text-sm font-semibold cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
          data-testid="new-peticao-btn"
        >
          <Plus className="w-4 h-4" aria-hidden="true" /> Nova petição
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-28 w-full rounded-lg" />)}</div>
      ) : peticoes.length === 0 ? (
        <EmptyState icon={FileSignature} title="Sem petições" description="Crie a primeira petição para convocar uma AG extraordinária." testId="no-peticoes" />
      ) : (
        <div className="space-y-4">
          {peticoes.map((p) => {
            const st = STATUS_LABEL[p.status] || STATUS_LABEL.aberta;
            const target = p.target_count || null;
            const pct = target ? Math.min(100, Math.round((p.signature_count / target) * 100)) : null;
            const busy = signMut.isPending && signMut.variables?.id === p.id;
            return (
              <div key={p.id} className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-5 space-y-3" data-testid={`peticao-${p.id}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="font-semibold text-grafite">{p.titulo}</h3>
                    <p className="text-xs text-[#6B7280]">{p.created_at ? format(new Date(p.created_at), 'dd MMM yyyy', { locale: ptBR }) : ''}</p>
                  </div>
                  <span className={`shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${st.cls}`}>{st.label}</span>
                </div>
                <p className="text-sm text-grafite whitespace-pre-wrap">{p.fundamentacao}</p>

                {/* Barra de progresso (assinaturas / alvo). */}
                <div>
                  <div className="flex items-center justify-between text-xs text-[#6B7280] mb-1">
                    <span>{p.signature_count} assinatura{p.signature_count === 1 ? '' : 's'}{target ? ` de ${target}` : ''}</span>
                    {pct !== null && <span>{pct}%</span>}
                  </div>
                  <div className="h-2 bg-[#F5F5F5] rounded-full overflow-hidden">
                    <div className="h-full bg-carmesim rounded-full transition-[width] duration-300" style={{ width: `${pct ?? Math.min(100, p.signature_count * 10)}%` }} />
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {(p.status === 'aberta' || p.status === 'atingida') && (
                    <button
                      onClick={() => signMut.mutate({ id: p.id, signed: p.viewer_has_signed })}
                      disabled={busy || (p.viewer_has_signed && p.status !== 'aberta')}
                      className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-semibold cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50 ${p.viewer_has_signed ? 'bg-white border border-[#D1D5DB] text-grafite hover:bg-[#F5F5F5]' : 'bg-carmesim text-white hover:bg-carmesim-dark'}`}
                      data-testid={`assinar-${p.id}`}
                    >
                      {busy ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Check className="w-4 h-4" aria-hidden="true" />}
                      {p.viewer_has_signed ? 'Retirar assinatura' : 'Assinar'}
                    </button>
                  )}
                  {canForward && p.status === 'atingida' && (
                    <>
                      <select
                        value={fwdAssembleia[p.id] || ''}
                        onChange={(e) => setFwdAssembleia({ ...fwdAssembleia, [p.id]: e.target.value })}
                        className="px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40"
                        data-testid={`encaminhar-assembleia-${p.id}`}
                      >
                        <option value="">Ligar a uma AG (opcional)…</option>
                        {assembleias.map((a) => <option key={a.id} value={a.id}>{a.titulo}</option>)}
                      </select>
                      <button
                        onClick={() => fwdMut.mutate({ id: p.id, assembleiaId: fwdAssembleia[p.id] })}
                        disabled={fwdMut.isPending}
                        className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md bg-white border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer disabled:opacity-50"
                        data-testid={`encaminhar-${p.id}`}
                      >
                        <Megaphone className="w-4 h-4" aria-hidden="true" /> Encaminhar à Mesa
                      </button>
                    </>
                  )}
                </div>

                {p.status === 'encaminhada' && p.assembleia_id && (
                  <p className="text-xs text-[#6B7280] inline-flex items-center gap-1.5" data-testid={`peticao-ligada-${p.id}`}>
                    <Link2 className="w-3.5 h-3.5" aria-hidden="true" /> Ligada à AG: {assembleiaLabel(p.assembleia_id)}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}

      <Dialog open={showCreate} onOpenChange={(o) => { if (!o) setShowCreate(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Nova petição</DialogTitle>
            <DialogDescription>Pedido fundamentado de convocação de AG extraordinária (Art. 19.2.d).</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Título *</label>
              <input
                type="text" value={form.titulo} maxLength={180} onChange={(e) => setForm({ ...form, titulo: e.target.value })}
                className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40"
                placeholder="Ex: Convocação de AG extraordinária sobre…" data-testid="peticao-titulo"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Fundamentação *</label>
              <textarea
                value={form.fundamentacao} maxLength={5000} rows={5} onChange={(e) => setForm({ ...form, fundamentacao: e.target.value })}
                className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40"
                placeholder="Motivos do pedido." data-testid="peticao-fundamentacao"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer">Cancelar</button>
              <button
                onClick={() => createMut.mutate()}
                disabled={createMut.isPending || form.titulo.trim().length < 3 || !form.fundamentacao.trim()}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-carmesim text-white text-sm font-semibold hover:bg-carmesim-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                data-testid="peticao-submit"
              >
                {createMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Plus className="w-4 h-4" aria-hidden="true" />} Criar
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PeticoesPage;
