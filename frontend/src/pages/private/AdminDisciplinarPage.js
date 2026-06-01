import React, { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sancoesAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { queryKeys } from '../../lib/queryClient';
import { SANCAO_TIPO_LABELS, SANCAO_STATUS_LABELS } from '../../lib/governanceLabels';
import { toast } from 'sonner';
import {
  Gavel, Scale, ShieldOff, Users, FileText,
  AlertTriangle, Ban, CircleDollarSign, CheckCircle2, Clock, Archive,
  XCircle, Undo2, ShieldAlert,
} from 'lucide-react';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../../components/ui/dialog';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { MemberPicker } from '../../components/MemberPicker';
import { primaryBtn } from '../../lib/buttonStyles';

const TIPO_OPTIONS = ['advertencia', 'multa', 'perda_direitos', 'expulsao'];
const STATUS_OPTIONS = [
  'proposta', 'inquerito', 'decidida', 'recurso', 'aplicada', 'arquivada', 'anulada',
];

// Paleta semântica por tipo de sanção. perda_direitos/expulsão = graves.
const TIPO_META = {
  advertencia: { icon: AlertTriangle, cls: 'bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]' },
  multa: { icon: CircleDollarSign, cls: 'bg-[#EFF6FF] text-[#1D4ED8] border-[#BFDBFE]' },
  perda_direitos: { icon: ShieldAlert, cls: 'bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]' },
  expulsao: { icon: Ban, cls: 'bg-[#FEF2F2] text-[#B91C1C] border-[#FECACA]' },
};

// Paleta semântica por estado do processo. icon + label + cor (nunca só cor).
const STATUS_META = {
  proposta: { icon: FileText, cls: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]' },
  inquerito: { icon: Clock, cls: 'bg-[#EFF6FF] text-[#1D4ED8] border-[#BFDBFE]' },
  decidida: { icon: Scale, cls: 'bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]' },
  recurso: { icon: Undo2, cls: 'bg-[#EFF6FF] text-[#1D4ED8] border-[#BFDBFE]' },
  aplicada: { icon: CheckCircle2, cls: 'bg-[#FEF2F2] text-[#B91C1C] border-[#FECACA]' },
  arquivada: { icon: Archive, cls: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]' },
  anulada: { icon: XCircle, cls: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]' },
};

const formatDate = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return '—';
  }
};

const formatEscudo = (v) => {
  if (v === null || v === undefined || v === '') return '—';
  const n = Number(v);
  if (Number.isNaN(n)) return '—';
  return `${n.toLocaleString('pt-PT')} CVE`;
};

// Meio-dia UTC evita o desvio de dia em fusos negativos (campo só-data).
const isoOrNull = (dateStr) => (dateStr ? `${dateStr}T12:00:00.000Z` : null);

const TipoBadge = ({ tipo }) => {
  const meta = TIPO_META[tipo] || TIPO_META.advertencia;
  const Icon = meta.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium ${meta.cls}`}>
      <Icon className="w-3 h-3" aria-hidden="true" />
      {SANCAO_TIPO_LABELS[tipo] || tipo}
    </span>
  );
};

const StatusBadge = ({ status }) => {
  const meta = STATUS_META[status] || STATUS_META.proposta;
  const Icon = meta.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium ${meta.cls}`}>
      <Icon className="w-3 h-3" aria-hidden="true" />
      {SANCAO_STATUS_LABELS[status] || status}
    </span>
  );
};

const Field = ({ label, children, hint }) => (
  <div>
    <label className="block text-xs font-medium text-gray-600 mb-1.5">{label}</label>
    {children}
    {hint && <p className="mt-1 text-xs text-[#6B7280]">{hint}</p>}
  </div>
);

const inputCls = 'w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none';
const selectCls = `${inputCls} bg-white`;
const secondaryBtn = 'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white border border-[#D1D5DB] text-grafite text-xs font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50';
const cancelBtn = 'px-4 py-2 rounded-md bg-white border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2';

const emptyCreateForm = {
  visado: null,
  tipo: 'advertencia',
  motivo: '',
  artigo_violado: '',
  multa_valor: '',
  perda_direitos_ate: '',
};

export const AdminDisciplinarPage = () => {
  const { isAdmin, isDirecao } = useAuth();
  const canAccess = isAdmin || isDirecao;
  const qc = useQueryClient();

  const [statusFilter, setStatusFilter] = useState('');
  const [tipoFilter, setTipoFilter] = useState('');

  // Estados de modais (cada um guarda a sanção-alvo, quando aplicável).
  const [creating, setCreating] = useState(false);
  const [createForm, setCreateForm] = useState(emptyCreateForm);
  const [comissaoFor, setComissaoFor] = useState(null);
  const [comissaoForm, setComissaoForm] = useState({ m: [null, null, null], prazo_dias: 30 });
  const [decidirFor, setDecidirFor] = useState(null);
  const [decidirForm, setDecidirForm] = useState({ aprovado: true, fundamentacao: '', assembleia_id: '', deliberacao_id: '' });
  const [recursoFor, setRecursoFor] = useState(null);
  const [recursoForm, setRecursoForm] = useState({ fundamentacao: '' });
  const [aplicarFor, setAplicarFor] = useState(null);

  const filters = useMemo(() => {
    const f = {};
    if (statusFilter) f.status = statusFilter;
    if (tipoFilter) f.tipo = tipoFilter;
    return f;
  }, [statusFilter, tipoFilter]);

  const { data: resp, isLoading } = useQuery({
    queryKey: queryKeys.sancoes.list(filters),
    queryFn: async () => (await sancoesAPI.list(Object.keys(filters).length ? filters : undefined)).data,
    enabled: canAccess,
  });

  const sancoes = resp?.sancoes || [];

  const invalidate = () => qc.invalidateQueries({ queryKey: queryKeys.sancoes.list() });

  const createMutation = useMutation({
    mutationFn: (data) => sancoesAPI.create(data),
    onSuccess: () => {
      toast.success('Processo disciplinar criado.');
      setCreating(false);
      setCreateForm(emptyCreateForm);
      invalidate();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao criar o processo disciplinar'),
  });

  const comissaoMutation = useMutation({
    mutationFn: ({ id, data }) => sancoesAPI.comissao(id, data),
    onSuccess: () => {
      toast.success('Comissão de inquérito nomeada.');
      setComissaoFor(null);
      setComissaoForm({ m: [null, null, null], prazo_dias: 30 });
      invalidate();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao nomear a comissão de inquérito'),
  });

  const decidirMutation = useMutation({
    mutationFn: ({ id, data }) => sancoesAPI.decidir(id, data),
    onSuccess: () => {
      toast.success('Decisão registada.');
      setDecidirFor(null);
      setDecidirForm({ aprovado: true, fundamentacao: '', assembleia_id: '', deliberacao_id: '' });
      invalidate();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao registar a decisão'),
  });

  const recursoMutation = useMutation({
    mutationFn: ({ id, data }) => sancoesAPI.recurso(id, data),
    onSuccess: () => {
      toast.success('Recurso submetido.');
      setRecursoFor(null);
      setRecursoForm({ fundamentacao: '' });
      invalidate();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao submeter o recurso'),
  });

  const aplicarMutation = useMutation({
    mutationFn: (id) => sancoesAPI.aplicar(id),
    onSuccess: () => {
      toast.success('Sanção aplicada.');
      setAplicarFor(null);
      invalidate();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao aplicar a sanção'),
  });

  // UX guard: o backend é a barreira real de segurança; isto é só apresentação.
  if (!canAccess) {
    return (
      <div className="space-y-6">
        <EmptyState
          icon={ShieldOff}
          title="Acesso restrito"
          description="Sem permissão para aceder ao módulo disciplinar."
          testId="disciplinar-no-access"
        />
      </div>
    );
  }

  // Helpers de elegibilidade de ações por estado.
  const canComissao = (s) => ['proposta', 'inquerito'].includes(s.status);
  const canDecidir = (s) => ['proposta', 'inquerito', 'recurso'].includes(s.status);
  const canRecurso = (s) => s.status === 'decidida' && ['multa', 'perda_direitos'].includes(s.tipo);
  const canAplicar = (s) => s.status === 'decidida';

  const openDecidir = (s) => {
    setDecidirForm({ aprovado: true, fundamentacao: '', assembleia_id: '', deliberacao_id: '' });
    setDecidirFor(s);
  };

  // Validações client-side (espelham o backend; o servidor é a autoridade).
  const createValid =
    !!createForm.visado &&
    createForm.motivo.trim().length >= 3 &&
    (createForm.tipo !== 'multa' || createForm.multa_valor !== '') &&
    (createForm.tipo !== 'perda_direitos' || !!createForm.perda_direitos_ate);

  const comissaoIds = comissaoForm.m.filter(Boolean).map((u) => u.id);
  const comissaoValid =
    comissaoIds.length === 3 && new Set(comissaoIds).size === 3;

  const decidirValid =
    decidirFor?.tipo !== 'expulsao' ||
    (!!decidirForm.assembleia_id.trim() && !!decidirForm.deliberacao_id.trim());

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-carmesim/10 flex items-center justify-center">
            <Gavel className="w-5 h-5 text-carmesim" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-grafite">Regime Disciplinar</h1>
            <p className="text-sm text-[#6B7280]">Processos, comissões de inquérito, decisões e aplicação de sanções.</p>
          </div>
        </div>
        <button
          onClick={() => { setCreateForm(emptyCreateForm); setCreating(true); }}
          className={primaryBtn}
          data-testid="novo-processo-btn"
        >
          Novo processo
        </button>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap items-end gap-3 bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-4">
        <div className="min-w-[180px]">
          <label className="block text-xs font-medium text-gray-600 mb-1.5">Estado</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className={selectCls}
            data-testid="filter-status"
          >
            <option value="">Todos os estados</option>
            {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{SANCAO_STATUS_LABELS[s]}</option>)}
          </select>
        </div>
        <div className="min-w-[180px]">
          <label className="block text-xs font-medium text-gray-600 mb-1.5">Tipo</label>
          <select
            value={tipoFilter}
            onChange={(e) => setTipoFilter(e.target.value)}
            className={selectCls}
            data-testid="filter-tipo"
          >
            <option value="">Todos os tipos</option>
            {TIPO_OPTIONS.map((t) => <option key={t} value={t}>{SANCAO_TIPO_LABELS[t]}</option>)}
          </select>
        </div>
        {(statusFilter || tipoFilter) && (
          <button
            onClick={() => { setStatusFilter(''); setTipoFilter(''); }}
            className={secondaryBtn}
            data-testid="filter-clear"
          >
            Limpar filtros
          </button>
        )}
      </div>

      {/* Lista */}
      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-28 w-full rounded-lg" />)}</div>
      ) : sancoes.length === 0 ? (
        <EmptyState
          icon={Scale}
          title="Sem processos disciplinares"
          description="Nenhum processo corresponde aos filtros selecionados."
          testId="no-sancoes"
        />
      ) : (
        <div className="space-y-3">
          {sancoes.map((s) => (
            <div
              key={s.id}
              className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6"
              data-testid={`sancao-row-${s.id}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <TipoBadge tipo={s.tipo} />
                    <StatusBadge status={s.status} />
                    <span className="text-xs text-[#6B7280]">{formatDate(s.created_at)}</span>
                  </div>
                  <p className="mt-2 text-sm text-grafite">
                    <span className="text-[#6B7280]">Membro:</span> <span className="font-mono">{s.user_id}</span>
                  </p>
                  <p className="mt-1 text-sm text-grafite line-clamp-2" title={s.motivo}>
                    {s.motivo}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-[#6B7280]">
                    {s.artigo_violado && <span>Artigo: {s.artigo_violado}</span>}
                    {s.tipo === 'multa' && <span>Multa: {formatEscudo(s.multa_valor)}</span>}
                    {s.tipo === 'perda_direitos' && <span>Direitos suspensos até: {formatDate(s.perda_direitos_ate)}</span>}
                    {Array.isArray(s.comissao_inquerito) && s.comissao_inquerito.length > 0 && (
                      <span>Comissão: {s.comissao_inquerito.length} membro(s)</span>
                    )}
                    {s.inquerito_prazo && <span>Prazo inquérito: {formatDate(s.inquerito_prazo)}</span>}
                  </div>
                </div>
                <div className="flex flex-wrap items-center justify-end gap-2">
                  {canComissao(s) && (
                    <button
                      onClick={() => { setComissaoForm({ m: [null, null, null], prazo_dias: 30 }); setComissaoFor(s); }}
                      className={secondaryBtn}
                      data-testid={`comissao-${s.id}`}
                    >
                      <Users className="w-3.5 h-3.5" aria-hidden="true" />Comissão de inquérito
                    </button>
                  )}
                  {canDecidir(s) && (
                    <button
                      onClick={() => openDecidir(s)}
                      className={secondaryBtn}
                      data-testid={`decidir-${s.id}`}
                    >
                      <Scale className="w-3.5 h-3.5" aria-hidden="true" />Decidir
                    </button>
                  )}
                  {canRecurso(s) && (
                    <button
                      onClick={() => { setRecursoForm({ fundamentacao: '' }); setRecursoFor(s); }}
                      className={secondaryBtn}
                      data-testid={`recurso-${s.id}`}
                    >
                      <Undo2 className="w-3.5 h-3.5" aria-hidden="true" />Recurso
                    </button>
                  )}
                  {canAplicar(s) && (
                    <button
                      onClick={() => setAplicarFor(s)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white border border-[#FECACA] text-[#B91C1C] text-xs font-medium hover:bg-[#FEF2F2] transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                      data-testid={`aplicar-${s.id}`}
                    >
                      <ShieldOff className="w-3.5 h-3.5" aria-hidden="true" />Aplicar
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Novo processo */}
      <Dialog open={creating} onOpenChange={(o) => { if (!o) { setCreating(false); setCreateForm(emptyCreateForm); } }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Novo processo disciplinar</DialogTitle>
            <DialogDescription>Instaure um processo contra um membro (spec-governança §13).</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Field label="Membro visado">
              <MemberPicker
                value={createForm.visado}
                onSelect={(u) => setCreateForm({ ...createForm, visado: u })}
                testId="create-visado-search"
                emptyLabel="Nenhum membro encontrado."
              />
            </Field>
            <Field label="Tipo de sanção">
              <select
                value={createForm.tipo}
                onChange={(e) => setCreateForm({ ...createForm, tipo: e.target.value, multa_valor: '', perda_direitos_ate: '' })}
                className={selectCls}
                data-testid="create-tipo"
              >
                {TIPO_OPTIONS.map((t) => <option key={t} value={t}>{SANCAO_TIPO_LABELS[t]}</option>)}
              </select>
            </Field>
            <Field label="Motivo">
              <textarea
                value={createForm.motivo}
                onChange={(e) => setCreateForm({ ...createForm, motivo: e.target.value })}
                rows={3}
                maxLength={1000}
                placeholder="Descreva os factos (mínimo 3 caracteres)"
                className={`${inputCls} resize-none`}
                data-testid="create-motivo"
              />
            </Field>
            <Field label="Artigo violado (opcional)">
              <input
                type="text"
                value={createForm.artigo_violado}
                onChange={(e) => setCreateForm({ ...createForm, artigo_violado: e.target.value })}
                placeholder="Ex.: Art. 12.º n.º 2"
                className={inputCls}
                data-testid="create-artigo"
              />
            </Field>
            {createForm.tipo === 'multa' && (
              <Field label="Valor da multa (CVE)" hint="máximo 3x a quota mensal">
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={createForm.multa_valor}
                  onChange={(e) => setCreateForm({ ...createForm, multa_valor: e.target.value })}
                  className={inputCls}
                  data-testid="create-multa-valor"
                />
              </Field>
            )}
            {createForm.tipo === 'perda_direitos' && (
              <Field label="Perda de direitos até" hint="Data até à qual os direitos ficam suspensos.">
                <input
                  type="date"
                  value={createForm.perda_direitos_ate}
                  onChange={(e) => setCreateForm({ ...createForm, perda_direitos_ate: e.target.value })}
                  className={inputCls}
                  data-testid="create-perda-ate"
                />
              </Field>
            )}
            <div className="flex justify-end gap-2 pt-1">
              <button onClick={() => { setCreating(false); setCreateForm(emptyCreateForm); }} className={cancelBtn}>Cancelar</button>
              <button
                onClick={() => createMutation.mutate({
                  user_id: createForm.visado.id,
                  tipo: createForm.tipo,
                  motivo: createForm.motivo.trim(),
                  artigo_violado: createForm.artigo_violado.trim() || undefined,
                  multa_valor: createForm.tipo === 'multa' ? Number(createForm.multa_valor) : undefined,
                  perda_direitos_ate: createForm.tipo === 'perda_direitos' ? isoOrNull(createForm.perda_direitos_ate) : undefined,
                })}
                disabled={!createValid || createMutation.isPending}
                className={primaryBtn}
                data-testid="create-confirm"
              >
                {createMutation.isPending ? 'A criar...' : 'Criar processo'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal: Comissão de inquérito */}
      <Dialog open={!!comissaoFor} onOpenChange={(o) => { if (!o) { setComissaoFor(null); setComissaoForm({ m: [null, null, null], prazo_dias: 30 }); } }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Comissão de inquérito</DialogTitle>
            <DialogDescription>Nomeie exatamente 3 membros distintos e defina o prazo do inquérito.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {[0, 1, 2].map((idx) => (
              <Field key={idx} label={`Membro ${idx + 1}`}>
                <MemberPicker
                  value={comissaoForm.m[idx]}
                  onSelect={(u) => {
                    const next = [...comissaoForm.m];
                    next[idx] = u;
                    setComissaoForm({ ...comissaoForm, m: next });
                  }}
                  testId={`comissao-member-${idx}`}
                  emptyLabel="Nenhum membro encontrado."
                />
              </Field>
            ))}
            <Field label="Prazo do inquérito (dias)">
              <input
                type="number"
                min="1"
                step="1"
                value={comissaoForm.prazo_dias}
                onChange={(e) => setComissaoForm({ ...comissaoForm, prazo_dias: e.target.value })}
                className={inputCls}
                data-testid="comissao-prazo"
              />
            </Field>
            {!comissaoValid && comissaoIds.length > 0 && (
              <p className="text-xs text-[#B45309] flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />
                São necessários 3 membros distintos.
              </p>
            )}
            <div className="flex justify-end gap-2 pt-1">
              <button onClick={() => { setComissaoFor(null); setComissaoForm({ m: [null, null, null], prazo_dias: 30 }); }} className={cancelBtn}>Cancelar</button>
              <button
                onClick={() => comissaoMutation.mutate({
                  id: comissaoFor.id,
                  data: {
                    membros: comissaoIds,
                    prazo_dias: comissaoForm.prazo_dias ? Number(comissaoForm.prazo_dias) : 30,
                  },
                })}
                disabled={!comissaoValid || comissaoMutation.isPending}
                className={primaryBtn}
                data-testid="comissao-confirm"
              >
                {comissaoMutation.isPending ? 'A nomear...' : 'Nomear comissão'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal: Decidir */}
      <Dialog open={!!decidirFor} onOpenChange={(o) => { if (!o) setDecidirFor(null); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Decidir processo</DialogTitle>
            <DialogDescription>
              {decidirFor && <>Sanção: {SANCAO_TIPO_LABELS[decidirFor.tipo] || decidirFor.tipo}. Registe a deliberação.</>}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <label className="flex items-center gap-2 text-sm text-grafite cursor-pointer">
              <input
                type="checkbox"
                checked={decidirForm.aprovado}
                onChange={(e) => setDecidirForm({ ...decidirForm, aprovado: e.target.checked })}
                className="rounded border-gray-300 text-carmesim focus:ring-carmesim/40"
                data-testid="decidir-aprovado"
              />
              Sanção aprovada
            </label>
            <Field label="Fundamentação (opcional)">
              <textarea
                value={decidirForm.fundamentacao}
                onChange={(e) => setDecidirForm({ ...decidirForm, fundamentacao: e.target.value })}
                rows={3}
                maxLength={2000}
                className={`${inputCls} resize-none`}
                data-testid="decidir-fundamentacao"
              />
            </Field>
            {decidirFor?.tipo === 'expulsao' && (
              <div className="space-y-3 rounded-md border border-[#FECACA] bg-[#FEF2F2] p-3">
                <p className="text-xs text-[#B91C1C] flex items-center gap-1">
                  <ShieldAlert className="w-3.5 h-3.5" aria-hidden="true" />
                  Expulsão exige deliberação da AG.
                </p>
                <Field label="ID da Assembleia">
                  <input
                    type="text"
                    value={decidirForm.assembleia_id}
                    onChange={(e) => setDecidirForm({ ...decidirForm, assembleia_id: e.target.value })}
                    className={inputCls}
                    data-testid="decidir-assembleia-id"
                  />
                </Field>
                <Field label="ID da Deliberação">
                  <input
                    type="text"
                    value={decidirForm.deliberacao_id}
                    onChange={(e) => setDecidirForm({ ...decidirForm, deliberacao_id: e.target.value })}
                    className={inputCls}
                    data-testid="decidir-deliberacao-id"
                  />
                </Field>
              </div>
            )}
            <div className="flex justify-end gap-2 pt-1">
              <button onClick={() => setDecidirFor(null)} className={cancelBtn}>Cancelar</button>
              <button
                onClick={() => decidirMutation.mutate({
                  id: decidirFor.id,
                  data: {
                    aprovado: decidirForm.aprovado,
                    fundamentacao: decidirForm.fundamentacao.trim() || undefined,
                    assembleia_id: decidirFor.tipo === 'expulsao' ? decidirForm.assembleia_id.trim() : undefined,
                    deliberacao_id: decidirFor.tipo === 'expulsao' ? decidirForm.deliberacao_id.trim() : undefined,
                  },
                })}
                disabled={!decidirValid || decidirMutation.isPending}
                className={primaryBtn}
                data-testid="decidir-confirm"
              >
                {decidirMutation.isPending ? 'A registar...' : 'Registar decisão'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal: Recurso */}
      <Dialog open={!!recursoFor} onOpenChange={(o) => { if (!o) { setRecursoFor(null); setRecursoForm({ fundamentacao: '' }); } }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Submeter recurso</DialogTitle>
            <DialogDescription>Recurso de decisão (apenas multa ou perda de direitos).</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Field label="Fundamentação do recurso">
              <textarea
                value={recursoForm.fundamentacao}
                onChange={(e) => setRecursoForm({ fundamentacao: e.target.value })}
                rows={4}
                maxLength={2000}
                placeholder="Apresente os fundamentos do recurso."
                className={`${inputCls} resize-none`}
                data-testid="recurso-fundamentacao"
              />
            </Field>
            <div className="flex justify-end gap-2 pt-1">
              <button onClick={() => { setRecursoFor(null); setRecursoForm({ fundamentacao: '' }); }} className={cancelBtn}>Cancelar</button>
              <button
                onClick={() => recursoMutation.mutate({ id: recursoFor.id, data: { fundamentacao: recursoForm.fundamentacao.trim() } })}
                disabled={!recursoForm.fundamentacao.trim() || recursoMutation.isPending}
                className={primaryBtn}
                data-testid="recurso-confirm"
              >
                {recursoMutation.isPending ? 'A submeter...' : 'Submeter recurso'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal: Aplicar (confirmação destrutiva) */}
      <Dialog open={!!aplicarFor} onOpenChange={(o) => { if (!o) setAplicarFor(null); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Aplicar sanção</DialogTitle>
            <DialogDescription>Esta ação enacta a sanção e produz efeitos imediatos. Confirma?</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="rounded-md border border-[#FECACA] bg-[#FEF2F2] p-3 text-sm text-[#B91C1C]">
              <p className="flex items-start gap-2">
                <ShieldAlert className="w-4 h-4 mt-0.5 shrink-0" aria-hidden="true" />
                <span>
                  Perda de direitos suspende o voto do membro; a expulsão inativa a conta.
                  Estes efeitos só podem ser revertidos por anulação do processo.
                </span>
              </p>
            </div>
            {aplicarFor && (
              <div className="flex flex-wrap items-center gap-2 text-sm text-grafite">
                <TipoBadge tipo={aplicarFor.tipo} />
                <span className="text-[#6B7280]">Membro:</span> <span className="font-mono text-xs">{aplicarFor.user_id}</span>
              </div>
            )}
            <div className="flex justify-end gap-2 pt-1">
              <button onClick={() => setAplicarFor(null)} className={cancelBtn}>Cancelar</button>
              <button
                onClick={() => aplicarMutation.mutate(aplicarFor.id)}
                disabled={aplicarMutation.isPending}
                className={primaryBtn}
                data-testid="aplicar-confirm"
              >
                {aplicarMutation.isPending ? 'A aplicar...' : 'Confirmar e aplicar'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminDisciplinarPage;
