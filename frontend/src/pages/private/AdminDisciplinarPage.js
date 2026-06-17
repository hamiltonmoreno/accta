import React, { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sancoesAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { queryKeys } from '../../lib/queryClient';
import { toast } from 'sonner';
import { Gavel, Scale, ShieldOff } from 'lucide-react';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { primaryBtn } from '../../lib/buttonStyles';

import {
  EMPTY_CREATE_FORM, EMPTY_COMISSAO_FORM, EMPTY_DECIDIR_FORM, EMPTY_RECURSO_FORM,
  isoOrNull,
} from './disciplinar/tokens';
import { FiltersBar } from './disciplinar/FiltersBar';
import { SancaoCard } from './disciplinar/SancaoCard';
import { NovoProcessoModal } from './disciplinar/NovoProcessoModal';
import { ComissaoModal } from './disciplinar/ComissaoModal';
import { DecidirModal } from './disciplinar/DecidirModal';
import { RecursoModal } from './disciplinar/RecursoModal';
import { AplicarModal } from './disciplinar/AplicarModal';

export const AdminDisciplinarPage = () => {
  const { isAdmin, isDirecao } = useAuth();
  const canAccess = isAdmin || isDirecao;
  const qc = useQueryClient();

  const [statusFilter, setStatusFilter] = useState('');
  const [tipoFilter, setTipoFilter] = useState('');

  // Estados de modais (cada um guarda a sanção-alvo, quando aplicável).
  const [creating, setCreating] = useState(false);
  const [createForm, setCreateForm] = useState(EMPTY_CREATE_FORM);
  const [comissaoFor, setComissaoFor] = useState(null);
  const [comissaoForm, setComissaoForm] = useState(EMPTY_COMISSAO_FORM);
  const [decidirFor, setDecidirFor] = useState(null);
  const [decidirForm, setDecidirForm] = useState(EMPTY_DECIDIR_FORM);
  const [recursoFor, setRecursoFor] = useState(null);
  const [recursoForm, setRecursoForm] = useState(EMPTY_RECURSO_FORM);
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
      setCreateForm(EMPTY_CREATE_FORM);
      invalidate();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao criar o processo disciplinar'),
  });

  const comissaoMutation = useMutation({
    mutationFn: ({ id, data }) => sancoesAPI.comissao(id, data),
    onSuccess: () => {
      toast.success('Comissão de inquérito nomeada.');
      setComissaoFor(null);
      setComissaoForm(EMPTY_COMISSAO_FORM);
      invalidate();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao nomear a comissão de inquérito'),
  });

  const decidirMutation = useMutation({
    mutationFn: ({ id, data }) => sancoesAPI.decidir(id, data),
    onSuccess: () => {
      toast.success('Decisão registada.');
      setDecidirFor(null);
      setDecidirForm(EMPTY_DECIDIR_FORM);
      invalidate();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao registar a decisão'),
  });

  const recursoMutation = useMutation({
    mutationFn: ({ id, data }) => sancoesAPI.recurso(id, data),
    onSuccess: () => {
      toast.success('Recurso submetido.');
      setRecursoFor(null);
      setRecursoForm(EMPTY_RECURSO_FORM);
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

  // Validações client-side (espelham o backend; o servidor é a autoridade).
  const createValid =
    !!createForm.visado &&
    createForm.motivo.trim().length >= 3 &&
    (createForm.tipo !== 'multa' || createForm.multa_valor !== '') &&
    (createForm.tipo !== 'perda_direitos' || !!createForm.perda_direitos_ate);

  const comissaoIds = comissaoForm.m.filter(Boolean).map((u) => u.id);
  const comissaoValid = comissaoIds.length === 3 && new Set(comissaoIds).size === 3;

  const decidirValid =
    decidirFor?.tipo !== 'expulsao' ||
    (!!decidirForm.assembleia_id.trim() && !!decidirForm.deliberacao_id.trim());

  const submitCreate = () => createMutation.mutate({
    user_id: createForm.visado.id,
    tipo: createForm.tipo,
    motivo: createForm.motivo.trim(),
    artigo_violado: createForm.artigo_violado.trim() || undefined,
    multa_valor: createForm.tipo === 'multa' ? Number(createForm.multa_valor) : undefined,
    perda_direitos_ate: createForm.tipo === 'perda_direitos' ? isoOrNull(createForm.perda_direitos_ate) : undefined,
  });

  const submitComissao = () => comissaoMutation.mutate({
    id: comissaoFor.id,
    data: {
      membros: comissaoIds,
      prazo_dias: comissaoForm.prazo_dias ? Number(comissaoForm.prazo_dias) : 30,
    },
  });

  const submitDecidir = () => decidirMutation.mutate({
    id: decidirFor.id,
    data: {
      aprovado: decidirForm.aprovado,
      fundamentacao: decidirForm.fundamentacao.trim() || undefined,
      assembleia_id: decidirFor.tipo === 'expulsao' ? decidirForm.assembleia_id.trim() : undefined,
      deliberacao_id: decidirFor.tipo === 'expulsao' ? decidirForm.deliberacao_id.trim() : undefined,
    },
  });

  const submitRecurso = () => recursoMutation.mutate({
    id: recursoFor.id,
    data: { fundamentacao: recursoForm.fundamentacao.trim() },
  });

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
          onClick={() => { setCreateForm(EMPTY_CREATE_FORM); setCreating(true); }}
          className={primaryBtn}
          data-testid="novo-processo-btn"
        >
          Novo processo
        </button>
      </div>

      <FiltersBar
        statusFilter={statusFilter} setStatusFilter={setStatusFilter}
        tipoFilter={tipoFilter} setTipoFilter={setTipoFilter}
      />

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
            <SancaoCard
              key={s.id}
              sancao={s}
              onComissao={(t) => { setComissaoForm(EMPTY_COMISSAO_FORM); setComissaoFor(t); }}
              onDecidir={(t) => { setDecidirForm(EMPTY_DECIDIR_FORM); setDecidirFor(t); }}
              onRecurso={(t) => { setRecursoForm(EMPTY_RECURSO_FORM); setRecursoFor(t); }}
              onAplicar={setAplicarFor}
            />
          ))}
        </div>
      )}

      <NovoProcessoModal
        open={creating}
        onClose={() => { setCreating(false); setCreateForm(EMPTY_CREATE_FORM); }}
        form={createForm}
        setForm={setCreateForm}
        valid={createValid}
        pending={createMutation.isPending}
        onSubmit={submitCreate}
      />

      <ComissaoModal
        open={!!comissaoFor}
        onClose={() => { setComissaoFor(null); setComissaoForm(EMPTY_COMISSAO_FORM); }}
        form={comissaoForm}
        setForm={setComissaoForm}
        ids={comissaoIds}
        valid={comissaoValid}
        pending={comissaoMutation.isPending}
        onSubmit={submitComissao}
      />

      <DecidirModal
        open={!!decidirFor}
        onClose={() => setDecidirFor(null)}
        target={decidirFor}
        form={decidirForm}
        setForm={setDecidirForm}
        valid={decidirValid}
        pending={decidirMutation.isPending}
        onSubmit={submitDecidir}
      />

      <RecursoModal
        open={!!recursoFor}
        onClose={() => { setRecursoFor(null); setRecursoForm(EMPTY_RECURSO_FORM); }}
        form={recursoForm}
        setForm={setRecursoForm}
        pending={recursoMutation.isPending}
        onSubmit={submitRecurso}
      />

      <AplicarModal
        open={!!aplicarFor}
        onClose={() => setAplicarFor(null)}
        target={aplicarFor}
        pending={aplicarMutation.isPending}
        onSubmit={() => aplicarMutation.mutate(aplicarFor.id)}
      />
    </div>
  );
};

export default AdminDisciplinarPage;
