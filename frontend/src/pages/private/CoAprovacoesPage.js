import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { atosAPI, financesAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { queryKeys } from '../../lib/queryClient';
import { FileSignature, Plus, Check, X, Play, Ban, Loader2, ShieldAlert } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../components/ui/dialog';

const TIPO_LABEL = { vinculativo: 'Acto vinculativo', pagamento: 'Pagamento' };
const STATUS = {
  pendente: { label: 'Pendente', cls: 'bg-[#FFFBEB] text-[#B45309]' },
  aprovado: { label: 'Aprovado', cls: 'bg-[#F0FDF4] text-[#15803D]' },
  rejeitado: { label: 'Rejeitado', cls: 'bg-[#FEF2F2] text-[#B91C1C]' },
  executado: { label: 'Executado', cls: 'bg-[#EFF6FF] text-[#1D4ED8]' },
  cancelado: { label: 'Cancelado', cls: 'bg-[#F5F5F5] text-[#6B7280]' },
};

const fmtCve = (v) => (v == null ? '—' : `${Number(v).toLocaleString('pt-PT')} CVE`);
const fmtDate = (d) => (d ? format(new Date(d), 'dd MMM yyyy', { locale: ptBR }) : '');

// Estado das assinaturas para o cartão (espelha atos_rules no backend).
const signatureState = (ato) => {
  const req = ato.requisitos || {};
  const aprov = (ato.assinaturas || []).filter((a) => a.decisao === 'aprovado');
  return {
    req,
    nDirecao: aprov.filter((a) => (a.cargo || '').startsWith('dir_')).length,
    hasPresidente: aprov.some((a) => a.cargo === 'dir_presidente'),
    hasTesoureiro: aprov.some((a) => a.cargo === 'dir_tesoureiro'),
  };
};

export const CoAprovacoesPage = () => {
  const qc = useQueryClient();
  const { user, isAdmin, isDirecao, isTesoureiro, canViewFinances } = useAuth();
  const canAccess = canViewFinances || isAdmin || isDirecao;
  const canCreate = isAdmin || isDirecao;
  const canSign = isDirecao;
  const canExecute = isAdmin || isTesoureiro;

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ tipo: 'pagamento', descricao: '', valor: '', beneficiario: '' });
  const [statusFilter, setStatusFilter] = useState('');
  const [execCat, setExecCat] = useState({}); // { [atoId]: category }

  const invalidate = () => qc.invalidateQueries({ queryKey: ['atos'] });
  const signedByMe = (ato) => (ato.assinaturas || []).some((a) => a.user_id === user?.id);

  // Actos à minha assinatura (só Direcção). Backend já filtra status/assinou.
  const { data: mine } = useQuery({
    queryKey: queryKeys.atos.list({ mine: true }),
    queryFn: async () => (await atosAPI.list({ pendentes_para_mim: true })).data,
    enabled: !!canSign,
  });
  const meusPendentes = mine?.items || [];

  const { data: all, isLoading } = useQuery({
    queryKey: queryKeys.atos.list({ status: statusFilter || 'todos' }),
    queryFn: async () => (await atosAPI.list(statusFilter ? { status: statusFilter } : {})).data,
    enabled: !!canAccess,
  });
  const atos = all?.items || [];

  // Categorias de despesa para o select de execução (sem hard-code — meta endpoint).
  const { data: categorias } = useQuery({
    queryKey: ['finances', 'categories'],
    queryFn: async () => (await financesAPI.getCategories()).data,
    enabled: !!canExecute,
    staleTime: 5 * 60 * 1000,
  });
  const expenseCats = categorias?.expense || [];
  const catLabel = (c) => categorias?.labels?.[c] || c;

  const createMut = useMutation({
    mutationFn: () =>
      atosAPI.create({
        tipo: form.tipo,
        descricao: form.descricao.trim(),
        valor: form.valor === '' ? null : Number(form.valor),
        beneficiario: form.beneficiario.trim() || null,
      }),
    onSuccess: () => {
      toast.success('Acto criado e a aguardar assinaturas.');
      invalidate();
      setShowCreate(false);
      setForm({ tipo: 'pagamento', descricao: '', valor: '', beneficiario: '' });
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao criar acto'),
  });
  const assinarMut = useMutation({
    mutationFn: ({ id, decisao }) => atosAPI.assinar(id, decisao),
    onSuccess: (_d, v) => { toast.success(v.decisao === 'aprovado' ? 'Assinatura registada.' : 'Acto rejeitado.'); invalidate(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao assinar'),
  });
  const executarMut = useMutation({
    mutationFn: ({ id, category }) => atosAPI.executar(id, { category }),
    onSuccess: () => { toast.success('Pagamento executado — despesa registada.'); invalidate(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao executar'),
  });
  const cancelarMut = useMutation({
    mutationFn: (id) => atosAPI.cancelar(id),
    onSuccess: () => { toast.success('Acto cancelado.'); invalidate(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao cancelar'),
  });

  if (!canAccess) {
    return (
      <div className="space-y-6">
        <h1 className="page-title">Co-aprovações</h1>
        <EmptyState icon={ShieldAlert} title="Acesso restrito" description="Esta área é da Direcção e da Tesouraria." testId="coaprov-restrito" />
      </div>
    );
  }

  const renderAto = (ato, { compact = false } = {}) => {
    const st = STATUS[ato.status] || STATUS.pendente;
    const sig = signatureState(ato);
    const podeAssinar = canSign && ato.status === 'pendente' && !signedByMe(ato);
    const podeExecutar = canExecute && ato.status === 'aprovado' && ato.tipo === 'pagamento' && !ato.transaction_id;
    const podeCancelar = ato.status === 'pendente' && (isAdmin || ato.created_by === user?.id);
    return (
      <div key={ato.id} className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-4 space-y-3" data-testid={`ato-${ato.id}`}>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="font-semibold text-grafite">{ato.descricao}</h3>
            <p className="text-xs text-[#6B7280]">
              {TIPO_LABEL[ato.tipo] || ato.tipo}
              {ato.valor != null && ` · ${fmtCve(ato.valor)}`}
              {ato.beneficiario && ` · ${ato.beneficiario}`}
              {ato.created_at && ` · ${fmtDate(ato.created_at)}`}
            </p>
          </div>
          <span className={`shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${st.cls}`}>{st.label}</span>
        </div>

        {/* Cartão de assinaturas */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-[#F5F5F5] text-grafite font-medium">
            Direcção {sig.nDirecao}/{sig.req.min_direcao ?? 2}
          </span>
          {sig.req.exige_presidente && (
            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md font-medium ${sig.hasPresidente ? 'bg-[#F0FDF4] text-[#15803D]' : 'bg-[#F5F5F5] text-[#6B7280]'}`}>
              Presidente {sig.hasPresidente ? '✓' : 'em falta'}
            </span>
          )}
          {sig.req.exige_tesoureiro && (
            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md font-medium ${sig.hasTesoureiro ? 'bg-[#F0FDF4] text-[#15803D]' : 'bg-[#F5F5F5] text-[#6B7280]'}`}>
              Tesoureiro {sig.hasTesoureiro ? '✓' : 'em falta'}
            </span>
          )}
        </div>

        {/* Acções */}
        {!compact && (podeAssinar || podeExecutar || podeCancelar) && (
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {podeAssinar && (
              <>
                <button onClick={() => assinarMut.mutate({ id: ato.id, decisao: 'aprovado' })} disabled={assinarMut.isPending} className="inline-flex items-center gap-1.5 border border-[#D1D5DB] text-grafite px-3 py-2 rounded-md text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`assinar-aprovar-${ato.id}`}>
                  <Check className="w-4 h-4 text-[#15803D]" aria-hidden="true" /> Aprovar
                </button>
                <button onClick={() => assinarMut.mutate({ id: ato.id, decisao: 'rejeitado' })} disabled={assinarMut.isPending} className="inline-flex items-center gap-1.5 border border-[#D1D5DB] text-grafite px-3 py-2 rounded-md text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`assinar-rejeitar-${ato.id}`}>
                  <X className="w-4 h-4 text-[#6B7280]" aria-hidden="true" /> Rejeitar
                </button>
              </>
            )}
            {podeExecutar && (
              <>
                <select value={execCat[ato.id] || 'operacional'} onChange={(e) => setExecCat({ ...execCat, [ato.id]: e.target.value })} className="px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`exec-cat-${ato.id}`}>
                  {expenseCats.map((c) => <option key={c} value={c}>{catLabel(c)}</option>)}
                </select>
                <button onClick={() => executarMut.mutate({ id: ato.id, category: execCat[ato.id] || 'operacional' })} disabled={executarMut.isPending} className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-carmesim text-white text-sm font-semibold hover:bg-carmesim-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid={`executar-${ato.id}`}>
                  {executarMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Play className="w-4 h-4" aria-hidden="true" />} Executar pagamento
                </button>
              </>
            )}
            {podeCancelar && (
              <button onClick={() => cancelarMut.mutate(ato.id)} disabled={cancelarMut.isPending} className="inline-flex items-center gap-1.5 border border-[#D1D5DB] text-grafite px-3 py-2 rounded-md text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`cancelar-${ato.id}`}>
                <Ban className="w-4 h-4 text-[#6B7280]" aria-hidden="true" /> Cancelar
              </button>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="page-title" data-testid="coaprovacoes-title">Co-aprovações</h1>
          <p className="page-subtitle">Actos que vinculam a ACCTA exigem 2 membros da Direcção (incluindo o Presidente); os pagamentos exigem também o Tesoureiro (Art. 54).</p>
        </div>
        {canCreate && (
          <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 bg-carmesim text-white px-4 py-2 rounded-lg hover:bg-carmesim-dark transition-colors text-sm font-semibold cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="novo-ato-btn">
            <Plus className="w-4 h-4" aria-hidden="true" /> Novo acto
          </button>
        )}
      </div>

      {/* À minha assinatura */}
      {canSign && meusPendentes.length > 0 && (
        <section className="space-y-3" data-testid="atos-minha-assinatura">
          <h2 className="text-sm font-semibold uppercase tracking-[0.12em] text-[#6B7280]">À minha assinatura</h2>
          <div className="space-y-3">{meusPendentes.map((a) => renderAto(a))}</div>
        </section>
      )}

      {/* Todos os actos */}
      <section className="space-y-3">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold uppercase tracking-[0.12em] text-[#6B7280]">Todos os actos</h2>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-3 py-1.5 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="ato-filter">
            <option value="">Todos os estados</option>
            {Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
        </div>
        {isLoading ? (
          <div className="space-y-2">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-28 w-full rounded-lg" />)}</div>
        ) : atos.length === 0 ? (
          <EmptyState icon={FileSignature} title="Sem actos" description="Ainda não há actos de co-aprovação registados." testId="no-atos" />
        ) : (
          <div className="space-y-3">{atos.map((a) => renderAto(a))}</div>
        )}
      </section>

      {/* Criar acto */}
      <Dialog open={showCreate} onOpenChange={(o) => { if (!o) setShowCreate(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Novo acto de co-aprovação</DialogTitle>
            <DialogDescription>Vinculativo (contrato/decisão) ou pagamento. Os requisitos de assinatura são fixados pelo tipo.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Tipo</label>
              <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="ato-tipo">
                <option value="pagamento">Pagamento (exige Tesoureiro)</option>
                <option value="vinculativo">Acto vinculativo (contrato/decisão)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Descrição *</label>
              <textarea value={form.descricao} maxLength={2000} rows={3} onChange={(e) => setForm({ ...form, descricao: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="ato-descricao" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-[#6B7280] mb-1">Valor (CVE){form.tipo === 'pagamento' ? ' *' : ''}</label>
                <input type="number" min="0" step="1" value={form.valor} onChange={(e) => setForm({ ...form, valor: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="ato-valor" />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#6B7280] mb-1">Beneficiário</label>
                <input type="text" value={form.beneficiario} maxLength={180} onChange={(e) => setForm({ ...form, beneficiario: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="ato-beneficiario" />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer">Cancelar</button>
              <button
                onClick={() => createMut.mutate()}
                disabled={createMut.isPending || form.descricao.trim().length < 3 || (form.tipo === 'pagamento' && (form.valor === '' || Number(form.valor) <= 0))}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-carmesim text-white text-sm font-semibold hover:bg-carmesim-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                data-testid="ato-submit"
              >
                {createMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Plus className="w-4 h-4" aria-hidden="true" />} Criar acto
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CoAprovacoesPage;
