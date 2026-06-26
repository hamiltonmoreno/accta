import React, { useState, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Trophy, Search, RefreshCw, Slash, Settings2, Plus } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { rankingAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { useAuth } from '../../contexts/AuthContext';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Label } from '../../components/ui/label';
import { Switch } from '../../components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../../components/ui/dialog';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../../components/ui/select';
import { CARGO_LABELS_FALLBACK } from '../../lib/governanceLabels';
import { RankBadge } from '../../components/RankBadge';
import { UserAvatar } from '../../components/UserAvatar';

const PAGE_SIZE = 20;
// Uma busca generosa cobre a dimensão real da associação (centenas); pesquisa e
// paginação são client-side sobre este conjunto (pesquisa instantânea sobre todos).
const FETCH_LIMIT = 200;

// Rótulos PT dos sinais de pontuação (chaves de `weights`, §3.1).
const WEIGHT_LABELS = {
  assembleia_presenca: 'Presença em AGA',
  eleicao_turnout: 'Voto em eleição',
  projeto_participacao: 'Participação em projeto',
  tarefa_concluida: 'Tarefa concluída',
  votacao_voto: 'Voto em votação',
  evento_presenca: 'Presença em evento',
  mural_post: 'Publicação (mural)',
  galeria_foto: 'Foto aprovada (galeria)',
  mural_comentario: 'Comentário (mural)',
  mural_like_recebido: 'Like recebido',
};

const cargoLabelOf = (c) => (c && c !== 'socio' ? CARGO_LABELS_FALLBACK[c] || null : null);

// Distinção de posição (1.º/2.º/3.º) vive em components/RankBadge.js — fonte única
// partilhada com o widget do dashboard (spec 006, Decisão D2).

// Componentes ao nível do módulo (não dentro do render do RankingPage) — definir
// no corpo da função recria o tipo a cada render e desmonta/remonta (perda de foco).
const PeriodToggle = ({ period, currentYear, onChange }) => (
  <div className="inline-flex items-center bg-gray-100 rounded-lg p-0.5" role="tablist" aria-label="Período">
    {[{ key: currentYear, label: 'Este ano' }, { key: 'all', label: 'Sempre' }].map((opt) => {
      const active = period === opt.key;
      return (
        <button
          key={opt.key}
          type="button"
          role="tab"
          aria-selected={active}
          onClick={() => onChange(opt.key)}
          className={`px-3.5 py-1.5 text-sm font-medium rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-1 ${
            active ? 'bg-white text-grafite shadow-sm' : 'text-[#4B5563] hover:text-grafite'
          }`}
          data-testid={`ranking-period-${opt.key}`}
        >
          {opt.label}
        </button>
      );
    })}
  </div>
);

const RecalcularButton = ({ onClick, isPending }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={isPending}
    className="inline-flex items-center gap-2 bg-floresta text-white hover:bg-floresta-dark rounded-md px-4 py-2 text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
    data-testid="ranking-recalcular"
  >
    <RefreshCw className={`w-4 h-4 ${isPending ? 'animate-spin' : ''}`} />
    {isPending ? 'A recalcular…' : 'Recalcular'}
  </button>
);

export const RankingPage = () => {
  const { user, isAdmin, isDirecao, hasPrivilege } = useAuth();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const currentYear = String(new Date().getFullYear());

  const [period, setPeriod] = useState(currentYear);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);

  const canManage = isAdmin || isDirecao || hasPrivilege('manage_ranking');

  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.ranking.leaderboard(period),
    queryFn: async () => (await rankingAPI.leaderboard({ period, limit: FETCH_LIMIT })).data,
    retry: false, // 403 (direcao_only) não deve fazer retry
  });

  const rebuildMutation = useMutation({
    mutationFn: () => rankingAPI.rebuild(period),
    onSuccess: (res) => {
      toast.success(`Ranking recalculado — ${res.data.members} membros.`);
      qc.invalidateQueries({ queryKey: queryKeys.ranking.leaderboard(period) });
      qc.invalidateQueries({ queryKey: queryKeys.ranking.me(period) });
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Falha ao recalcular o ranking.'),
  });

  // ---- F4: configuração + ajustes manuais (só gestores) ----
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [form, setForm] = useState(null);
  const [adjustOpen, setAdjustOpen] = useState(false);
  const [adjust, setAdjust] = useState({ user_id: '', delta: '', reason: '' });

  const settingsQuery = useQuery({
    queryKey: queryKeys.ranking.settings(),
    queryFn: async () => (await rankingAPI.getSettings()).data,
    enabled: false, // só carrega quando um gestor está na página (ativada abaixo)
  });

  const settingsMutation = useMutation({
    mutationFn: (payload) => rankingAPI.updateSettings(payload),
    onSuccess: () => {
      toast.success('Definições do ranking atualizadas.');
      qc.invalidateQueries({ queryKey: queryKeys.ranking.settings() });
      qc.invalidateQueries({ queryKey: queryKeys.ranking.leaderboard(period) });
      qc.invalidateQueries({ queryKey: queryKeys.ranking.me(period) });
      setSettingsOpen(false);
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Falha ao guardar as definições.'),
  });

  const adjustMutation = useMutation({
    mutationFn: (payload) => rankingAPI.addAdjustment(payload),
    onSuccess: () => {
      toast.success('Ajuste registado. Recalcule para refletir na tabela.');
      qc.invalidateQueries({ queryKey: queryKeys.ranking.me(period) });
      setAdjustOpen(false);
      setAdjust({ user_id: '', delta: '', reason: '' });
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Falha ao registar o ajuste.'),
  });

  // Opt-out do próprio (§2.5): sair das listas públicas mantendo o /me.
  const optOutMutation = useMutation({
    mutationFn: (optOut) => rankingAPI.setOptOut(optOut),
    onSuccess: (res) => {
      toast.success(res.data.opt_out ? 'Saíste das listas públicas do ranking.' : 'Voltaste a aparecer no ranking.');
      qc.invalidateQueries({ queryKey: queryKeys.ranking.leaderboard(period) });
      qc.invalidateQueries({ queryKey: queryKeys.ranking.me(period) });
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Falha ao atualizar a preferência.'),
  });

  const openSettings = async () => {
    const { data: s } = await settingsQuery.refetch();
    setForm({
      enabled: s?.enabled ?? true,
      visibility: s?.visibility ?? 'all_members',
      top_n_dashboard: s?.top_n_dashboard ?? 5,
      max_like_points_per_period: s?.max_like_points_per_period ?? 50,
      weights: { ...(s?.weights || {}) },
    });
    setSettingsOpen(true);
  };

  const submitSettings = () => {
    if (!form) return;
    const weights = {};
    for (const k of Object.keys(WEIGHT_LABELS)) {
      const n = parseFloat(form.weights?.[k]);
      weights[k] = Number.isFinite(n) && n >= 0 ? n : 0;
    }
    settingsMutation.mutate({
      enabled: form.enabled,
      visibility: form.visibility,
      top_n_dashboard: parseInt(form.top_n_dashboard, 10) || 5,
      max_like_points_per_period: parseInt(form.max_like_points_per_period, 10) || 0,
      weights,
    });
  };

  const adjustDelta = parseFloat(adjust.delta);
  const adjustValid = !!adjust.user_id && !!adjust.reason.trim() && Number.isFinite(adjustDelta) && adjustDelta !== 0;
  const submitAdjust = () => {
    if (!adjustValid) return;
    adjustMutation.mutate({ user_id: adjust.user_id, period_key: period, delta: adjustDelta, reason: adjust.reason.trim() });
  };

  const enabled = data?.enabled !== false;
  const visibility = data?.visibility;
  const allEntries = useMemo(() => data?.entries || [], [data]);
  // Posição CONTÍNUA na lista ordenada (1,2,3,4,5…) — distinta do `rank` do
  // servidor, que usa empates (4,4,4). A lista já vem ordenada por rank asc.
  const positionOf = useMemo(
    () => new Map(allEntries.map((e, i) => [e.user_id, i + 1])),
    [allEntries],
  );
  const me = data?.me;
  const myPosition = (me && positionOf.get(me.user_id)) ?? me?.rank;
  const top3 = allEntries.slice(0, 3);

  // Respeita visibility=direcao_only: o servidor devolve 403 a não-gestores
  // (F5) → redirecionamos para o dashboard. O ramo `visibility` mantém o
  // redireccionamento defensivo caso o payload chegue (gestores).
  useEffect(() => {
    if (error?.response?.status === 403 || (visibility === 'direcao_only' && !canManage)) {
      navigate('/dashboard', { replace: true });
    }
  }, [error, visibility, canManage, navigate]);

  // Reset de paginação quando muda o período ou a pesquisa.
  useEffect(() => { setPage(0); }, [period, search]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return allEntries;
    return allEntries.filter((e) => (e.member_name || '').toLowerCase().includes(q));
  }, [allEntries, search]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageClamped = Math.min(page, totalPages - 1);
  const pageRows = filtered.slice(pageClamped * PAGE_SIZE, pageClamped * PAGE_SIZE + PAGE_SIZE);

  const periodLabel = period === 'all' ? 'Sempre' : period;
  const recalcular = () => rebuildMutation.mutate();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title flex items-center gap-2" data-testid="ranking-page-title">
            <Trophy className="w-6 h-6 text-carmesim" />
            Ranking de Atuação
          </h1>
          <p className="page-subtitle">
            Reconhecimento da participação dos sócios na vida associativa — {periodLabel}.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <PeriodToggle period={period} currentYear={currentYear} onChange={setPeriod} />
          {canManage && (
            <>
              <button
                type="button"
                onClick={openSettings}
                className="inline-flex items-center gap-2 rounded-md border border-[#D1D5DB] bg-white px-3.5 py-2 text-sm font-medium text-grafite hover:bg-[#F5F5F5] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-1"
                data-testid="ranking-settings-open"
              >
                <Settings2 className="w-4 h-4" /> Definições
              </button>
              {allEntries.length > 0 && (
                <button
                  type="button"
                  onClick={() => setAdjustOpen(true)}
                  className="inline-flex items-center gap-2 rounded-md border border-[#D1D5DB] bg-white px-3.5 py-2 text-sm font-medium text-grafite hover:bg-[#F5F5F5] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-1"
                  data-testid="ranking-adjust-open"
                >
                  <Plus className="w-4 h-4" /> Registar ajuste
                </button>
              )}
              {enabled && allEntries.length > 0 && (
                <RecalcularButton onClick={recalcular} isPending={rebuildMutation.isPending} />
              )}
            </>
          )}
        </div>
      </div>

      {/* A minha posição (#FBEAEC = superfície selecionada → texto Grafite) */}
      {enabled && me && (
        <div className="bg-[#FBEAEC] border border-carmesim/20 rounded-2xl px-5 py-4" data-testid="ranking-my-position">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-white rounded-xl flex items-center justify-center flex-shrink-0">
                <RankBadge rank={myPosition} />
              </div>
              <div>
                <div className="text-sm font-semibold text-grafite">A minha posição</div>
                <div className="text-xs text-grafite">
                  {me.ranking_opt_out
                    ? 'Estás oculto das listas públicas'
                    : myPosition ? `#${myPosition} de ${data.total_ranked ?? data.total}` : 'Ainda sem posição neste período'}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="font-bold text-xl text-grafite leading-none">{me.score}</div>
              <div className="text-[11px] text-grafite mt-0.5">pts</div>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-carmesim/15 flex items-center justify-between">
            <Label htmlFor="rk-optout" className="text-xs text-grafite">Aparecer no ranking público</Label>
            <Switch
              id="rk-optout"
              checked={!me.ranking_opt_out}
              onCheckedChange={(appear) => optOutMutation.mutate(!appear)}
              disabled={optOutMutation.isPending}
              data-testid="ranking-optout"
            />
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-32 rounded-2xl" />
            ))}
          </div>
          <Skeleton className="h-96 rounded-2xl" />
        </div>
      ) : !enabled ? (
        <div className="bg-white border border-gray-200/80 rounded-2xl">
          <EmptyState
            icon={Slash}
            title="Ranking desativado"
            description="A funcionalidade de ranking está desativada de momento."
            testId="ranking-disabled"
            className="border-0 shadow-none py-16"
          />
        </div>
      ) : allEntries.length === 0 ? (
        <div className="bg-white border border-gray-200/80 rounded-2xl">
          <EmptyState
            icon={Trophy}
            title="Ranking ainda não calculado"
            description={
              canManage
                ? 'Calcule o ranking para este período para o ver aqui.'
                : 'A atuação dos sócios aparece aqui após o primeiro cálculo.'
            }
            testId="ranking-empty"
            className="border-0 shadow-none py-16"
            action={canManage ? <RecalcularButton onClick={recalcular} isPending={rebuildMutation.isPending} /> : null}
          />
        </div>
      ) : (
        <>
          {/* Pódio Top-3 */}
          {top3.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4" data-testid="ranking-podium">
              {top3.map((e) => {
                const isMe = e.user_id === user?.id;
                const cargo = cargoLabelOf(e.cargo);
                const pos = positionOf.get(e.user_id);
                const first = pos === 1;
                return (
                  <div
                    key={e.user_id}
                    className={`bg-white rounded-2xl border p-5 text-center ${
                      first ? 'border-carmesim/30 sm:-mt-2' : 'border-gray-200/80'
                    } ${isMe ? 'ring-2 ring-carmesim/40' : first ? 'ring-1 ring-carmesim/20' : ''}`}
                    data-testid={`ranking-podium-${pos}`}
                  >
                    <div className="flex flex-col items-center gap-2 mb-2">
                      <UserAvatar name={e.member_name} photoUrl={e.photo_url} size="lg" />
                      <div className="flex items-center justify-center">
                        <RankBadge rank={pos} size="lg" />
                      </div>
                    </div>
                    <div className="font-semibold text-grafite truncate">
                      {e.member_name}{isMe && ' (eu)'}
                    </div>
                    {cargo && <div className="text-xs text-[#6B7280] truncate mt-0.5">{cargo}</div>}
                    <div className="mt-3 font-bold text-2xl text-grafite">
                      {e.score}
                      <span className="text-xs font-normal text-[#6B7280] ml-1">pts</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Pesquisa */}
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
            <Input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Pesquisar por nome…"
              className="pl-9"
              aria-label="Pesquisar membro por nome"
              data-testid="ranking-search"
            />
          </div>

          {/* Tabela */}
          <div className="bg-white border border-gray-200/80 rounded-2xl overflow-hidden">
            {filtered.length === 0 ? (
              <EmptyState
                icon={Search}
                title="Sem resultados"
                description={`Nenhum membro corresponde a “${search}”.`}
                testId="ranking-no-results"
                className="border-0 shadow-none py-12"
              />
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50/80">
                      <tr>
                        <th className="px-3 sm:px-6 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider w-10 sm:w-16">#</th>
                        <th className="px-3 sm:px-6 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Membro</th>
                        <th className="px-3 sm:px-6 py-3 text-right text-xs font-semibold text-[#6B7280] uppercase tracking-wider">
                          <span className="hidden sm:inline">Pontuação</span>
                          <span className="sm:hidden">Pts</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {pageRows.map((e) => {
                        const isMe = e.user_id === user?.id;
                        const cargo = cargoLabelOf(e.cargo);
                        const pos = positionOf.get(e.user_id);
                        return (
                          <tr
                            key={e.user_id}
                            className={`border-t border-gray-50 ${isMe ? 'bg-[#FBEAEC]' : 'hover:bg-gray-50/60'} transition-colors`}
                            data-testid={`ranking-row-${pos}`}
                          >
                            <td className="px-3 sm:px-6 py-3.5">
                              <div className="flex items-center justify-center w-6"><RankBadge rank={pos} /></div>
                            </td>
                            <td className="px-3 sm:px-6 py-3.5">
                              <div className="flex items-center gap-2.5 min-w-0">
                                <UserAvatar name={e.member_name} photoUrl={e.photo_url} size="xs" />
                                <div className="min-w-0 max-w-[42vw] sm:max-w-none">
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium text-sm text-grafite truncate">
                                      {e.member_name}{isMe && ' (eu)'}
                                    </span>
                                    {e.status === 'inativo' && (
                                      <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-wider text-[#4B5563] bg-gray-100 rounded px-1.5 py-0.5 flex-shrink-0">
                                        <Slash className="w-2.5 h-2.5" aria-hidden="true" /> Inativo
                                      </span>
                                    )}
                                  </div>
                                  {cargo && <div className="text-xs text-[#6B7280] mt-0.5 truncate">{cargo}</div>}
                                </div>
                              </div>
                            </td>
                            <td className="px-3 sm:px-6 py-3.5 text-right">
                              <span className="font-bold text-sm text-grafite">{e.score}</span>
                              <span className="text-[11px] text-[#6B7280] ml-1">pts</span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Paginação */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between px-4 sm:px-6 py-3 border-t border-gray-100">
                    <span className="text-xs text-[#6B7280]">
                      Página {pageClamped + 1} de {totalPages} · {filtered.length} membros
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setPage((p) => Math.max(0, p - 1))}
                        disabled={pageClamped === 0}
                        className="px-3 py-1.5 text-sm rounded-md border border-[#D1D5DB] text-grafite hover:bg-[#F5F5F5] disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-1"
                        data-testid="ranking-prev-page"
                      >
                        Anterior
                      </button>
                      <button
                        type="button"
                        onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                        disabled={pageClamped >= totalPages - 1}
                        className="px-3 py-1.5 text-sm rounded-md border border-[#D1D5DB] text-grafite hover:bg-[#F5F5F5] disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-1"
                        data-testid="ranking-next-page"
                      >
                        Próxima
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {data?.computed_at && (
            <p className="text-xs text-[#6B7280]" data-testid="ranking-page-computed-at">
              Atualizado {format(new Date(data.computed_at), "dd 'de' MMMM 'de' yyyy, HH:mm", { locale: ptBR })}
            </p>
          )}
        </>
      )}

      {/* ===== Dialogs de gestão (admin/Direcção/manage_ranking) ===== */}
      {canManage && (
        <>
          {/* Definições */}
          <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
            <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Definições do ranking</DialogTitle>
                <DialogDescription>Pesos por sinal, visibilidade e ativação da funcionalidade.</DialogDescription>
              </DialogHeader>
              {form && (
                <div className="space-y-5">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="rk-enabled" className="text-sm text-grafite">Ranking ativo</Label>
                    <Switch
                      id="rk-enabled"
                      checked={form.enabled}
                      onCheckedChange={(v) => setForm((f) => ({ ...f, enabled: v }))}
                      data-testid="settings-enabled"
                    />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <Label htmlFor="rk-vis" className="text-sm text-grafite">Visibilidade</Label>
                      <Select value={form.visibility} onValueChange={(v) => setForm((f) => ({ ...f, visibility: v }))}>
                        <SelectTrigger id="rk-vis" data-testid="settings-visibility"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all_members">Todos os membros</SelectItem>
                          <SelectItem value="direcao_only">Apenas Direcção</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="rk-topn" className="text-sm text-grafite">Top-N no dashboard</Label>
                      <Input id="rk-topn" type="number" min="1" max="50" value={form.top_n_dashboard}
                        onChange={(e) => setForm((f) => ({ ...f, top_n_dashboard: e.target.value }))} />
                    </div>
                    <div className="space-y-1.5 sm:col-span-2">
                      <Label htmlFor="rk-cap" className="text-sm text-grafite">Máx. pontos de likes por período</Label>
                      <Input id="rk-cap" type="number" min="0" value={form.max_like_points_per_period}
                        onChange={(e) => setForm((f) => ({ ...f, max_like_points_per_period: e.target.value }))} />
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-grafite mb-2">Pesos por sinal</div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {Object.keys(WEIGHT_LABELS).map((k) => (
                        <div key={k} className="flex items-center justify-between gap-3">
                          <Label htmlFor={`w-${k}`} className="text-sm text-[#6B7280]">{WEIGHT_LABELS[k]}</Label>
                          <Input id={`w-${k}`} type="number" min="0" step="0.5" value={form.weights?.[k] ?? ''}
                            onChange={(e) => setForm((f) => ({ ...f, weights: { ...f.weights, [k]: e.target.value } }))}
                            className="w-24 flex-shrink-0" data-testid={`weight-${k}`} />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
              <DialogFooter>
                <button type="button" onClick={() => setSettingsOpen(false)}
                  className="rounded-md border border-[#D1D5DB] bg-white px-4 py-2 text-sm font-medium text-grafite hover:bg-[#F5F5F5] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-1">
                  Cancelar
                </button>
                <button type="button" onClick={submitSettings} disabled={settingsMutation.isPending}
                  className="bg-floresta text-white hover:bg-floresta-dark rounded-md px-4 py-2 text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                  data-testid="settings-save">
                  {settingsMutation.isPending ? 'A guardar…' : 'Guardar'}
                </button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* Registar ajuste */}
          <Dialog open={adjustOpen} onOpenChange={(o) => { setAdjustOpen(o); if (!o) setAdjust({ user_id: '', delta: '', reason: '' }); }}>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Registar ajuste manual</DialogTitle>
                <DialogDescription>Pontos atribuídos pela Direcção ({periodLabel}). O membro é notificado.</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="adj-member" className="text-sm text-grafite">Membro</Label>
                  {allEntries.length > 0 ? (
                    <Select value={adjust.user_id} onValueChange={(v) => setAdjust((a) => ({ ...a, user_id: v }))}>
                      <SelectTrigger id="adj-member" data-testid="adjust-member"><SelectValue placeholder="Selecionar membro…" /></SelectTrigger>
                      <SelectContent>
                        {allEntries.map((e) => (
                          <SelectItem key={e.user_id} value={e.user_id}>{e.member_name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    <p className="text-sm text-[#6B7280]">Recalcule o ranking primeiro para listar os membros.</p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="adj-delta" className="text-sm text-grafite">Pontos (delta)</Label>
                  <Input id="adj-delta" type="number" step="0.5" value={adjust.delta}
                    onChange={(e) => setAdjust((a) => ({ ...a, delta: e.target.value }))}
                    placeholder="ex.: 10 ou -5" data-testid="adjust-delta" />
                  <p className="text-xs text-[#6B7280]">Use valores negativos para penalizar.</p>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="adj-reason" className="text-sm text-grafite">Motivo</Label>
                  <Textarea id="adj-reason" value={adjust.reason}
                    onChange={(e) => setAdjust((a) => ({ ...a, reason: e.target.value }))}
                    placeholder="ex.: Organizou a festa anual" maxLength={500} rows={3} data-testid="adjust-reason" />
                </div>
              </div>
              <DialogFooter>
                <button type="button" onClick={() => setAdjustOpen(false)}
                  className="rounded-md border border-[#D1D5DB] bg-white px-4 py-2 text-sm font-medium text-grafite hover:bg-[#F5F5F5] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-1">
                  Cancelar
                </button>
                <button type="button" onClick={submitAdjust} disabled={!adjustValid || adjustMutation.isPending}
                  className="bg-floresta text-white hover:bg-floresta-dark rounded-md px-4 py-2 text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                  data-testid="adjust-save">
                  {adjustMutation.isPending ? 'A registar…' : 'Registar'}
                </button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </>
      )}
    </div>
  );
};

export default RankingPage;
