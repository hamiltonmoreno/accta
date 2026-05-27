import React, { useState, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Trophy, Medal, Crown, Search, RefreshCw, Slash } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { rankingAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { useAuth } from '../../contexts/AuthContext';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { Input } from '../../components/ui/input';
import { CARGO_LABELS_FALLBACK } from '../../lib/governanceLabels';

const PAGE_SIZE = 20;
// Uma busca generosa cobre a dimensão real da associação (centenas); pesquisa e
// paginação são client-side sobre este conjunto (pesquisa instantânea sobre todos).
const FETCH_LIMIT = 200;

const cargoLabelOf = (c) => (c && c !== 'socio' ? CARGO_LABELS_FALLBACK[c] || null : null);

// Medalha/posição: #1 Carmesim (único acento), #2/#3 neutro, resto número.
const RankBadge = ({ rank, size = 'sm' }) => {
  const cls = size === 'lg' ? 'w-7 h-7' : 'w-5 h-5';
  if (rank === 1) return <Crown className={`${cls} text-carmesim`} aria-hidden="true" />;
  if (rank === 2 || rank === 3) return <Medal className={`${cls} text-[#6B7280]`} aria-hidden="true" />;
  return <span className="text-sm font-semibold text-[#4B5563] font-mono">{rank}</span>;
};

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
    className="inline-flex items-center gap-2 bg-carmesim text-white hover:bg-carmesim-dark rounded-md px-4 py-2 text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
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

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.ranking.leaderboard(period),
    queryFn: async () => (await rankingAPI.leaderboard({ period, limit: FETCH_LIMIT })).data,
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

  const enabled = data?.enabled !== false;
  const visibility = data?.visibility;
  const allEntries = useMemo(() => data?.entries || [], [data]);
  const me = data?.me;
  const top3 = allEntries.slice(0, 3);

  // Respeita visibility=direcao_only: sócio comum é redirecionado (à semelhança
  // do ProtectedRoute). O enforcement server-side completo chega na F5.
  useEffect(() => {
    if (visibility === 'direcao_only' && !canManage) navigate('/dashboard', { replace: true });
  }, [visibility, canManage, navigate]);

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
        <div className="flex items-center gap-3">
          <PeriodToggle period={period} currentYear={currentYear} onChange={setPeriod} />
          {enabled && allEntries.length > 0 && canManage && (
            <RecalcularButton onClick={recalcular} isPending={rebuildMutation.isPending} />
          )}
        </div>
      </div>

      {/* A minha posição (#FBEAEC = superfície selecionada → texto Grafite) */}
      {enabled && me && (
        <div className="bg-[#FBEAEC] border border-carmesim/20 rounded-2xl px-5 py-4 flex items-center justify-between" data-testid="ranking-my-position">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white rounded-xl flex items-center justify-center flex-shrink-0">
              <RankBadge rank={me.rank} />
            </div>
            <div>
              <div className="text-sm font-semibold text-grafite">A minha posição</div>
              <div className="text-xs text-grafite">
                {me.rank ? `#${me.rank} de ${data.total}` : 'Ainda sem posição neste período'}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="font-bold text-xl text-grafite leading-none">{me.score}</div>
            <div className="text-[11px] text-grafite mt-0.5">pts</div>
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
                const first = e.rank === 1;
                return (
                  <div
                    key={e.user_id}
                    className={`bg-white rounded-2xl border p-5 text-center ${
                      first ? 'border-carmesim/30 sm:-mt-2' : 'border-gray-200/80'
                    } ${isMe ? 'ring-2 ring-carmesim/40' : first ? 'ring-1 ring-carmesim/20' : ''}`}
                    data-testid={`ranking-podium-${e.rank}`}
                  >
                    <div className="flex items-center justify-center mb-2">
                      <RankBadge rank={e.rank} size="lg" />
                    </div>
                    <div className="font-semibold text-grafite truncate">
                      {e.member_name}{isMe && ' (você)'}
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
                        <th className="px-4 sm:px-6 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider w-16">#</th>
                        <th className="px-4 sm:px-6 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Membro</th>
                        <th className="px-4 sm:px-6 py-3 text-right text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Pontuação</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pageRows.map((e) => {
                        const isMe = e.user_id === user?.id;
                        const cargo = cargoLabelOf(e.cargo);
                        return (
                          <tr
                            key={e.user_id}
                            className={`border-t border-gray-50 ${isMe ? 'bg-[#FBEAEC]' : 'hover:bg-gray-50/60'} transition-colors`}
                            data-testid={`ranking-row-${e.rank}`}
                          >
                            <td className="px-4 sm:px-6 py-3.5">
                              <div className="flex items-center justify-center w-6"><RankBadge rank={e.rank} /></div>
                            </td>
                            <td className="px-4 sm:px-6 py-3.5">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="font-medium text-sm text-grafite">
                                  {e.member_name}{isMe && ' (você)'}
                                </span>
                                {e.status === 'inativo' && (
                                  <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-wider text-[#4B5563] bg-gray-100 rounded px-1.5 py-0.5">
                                    <Slash className="w-2.5 h-2.5" aria-hidden="true" /> Inativo
                                  </span>
                                )}
                              </div>
                              {cargo && <div className="text-xs text-[#6B7280] mt-0.5">{cargo}</div>}
                            </td>
                            <td className="px-4 sm:px-6 py-3.5 text-right">
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
    </div>
  );
};

export default RankingPage;
