import React, { useState } from 'react';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { auditAPI } from '../../utils/api';
import { ClipboardList, Activity, ChevronLeft, ChevronRight } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { queryKeys } from '../../lib/queryClient';
import { EmptyState } from '../../components/EmptyState';

const PAGE_SIZE = 50;

export const AdminLogsPage = () => {
  const [page, setPage] = useState(0);
  const skip = page * PAGE_SIZE;

  const { data: logs = [], isLoading: loading, isFetching } = useQuery({
    queryKey: queryKeys.audit.logs({ skip, limit: PAGE_SIZE }),
    queryFn: async () => {
      const res = await auditAPI.getLogs({ skip, limit: PAGE_SIZE });
      return res.data;
    },
    // Audit logs sao apenas leitura. 60s staleTime razoavel — o staff nao
    // espera ver entries inseridos por outros admins ao segundo.
    staleTime: 60 * 1000,
    // Mantém a página anterior visível enquanto a próxima carrega (sem flash).
    placeholderData: keepPreviousData,
  });

  // O backend devolve no máximo PAGE_SIZE entries — uma página cheia indica que
  // pode haver mais. Não há endpoint de contagem global, por isso paginamos por
  // tamanho de página.
  const hasNext = logs.length === PAGE_SIZE;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="page-title" data-testid="admin-logs-title">
          Audit Logs
        </h1>
        <p className="page-subtitle">Registro de todas as ações administrativas no sistema</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card-technical rounded-xl p-6 animate-fade-up">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-grafite rounded-lg flex items-center justify-center">
              <ClipboardList className="w-6 h-6 text-white" />
            </div>
          </div>
          <div className="font-mono text-3xl font-bold text-grafite mb-1">{logs.length}</div>
          <div className="text-sm text-gray-500 uppercase tracking-wider">Registros nesta página</div>
        </div>

        <div className="card-technical rounded-xl p-6 animate-fade-up">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-carmesim rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
          </div>
          <div className="font-mono text-3xl font-bold text-carmesim mb-1">
            {logs.filter((log) => {
              const logDate = new Date(log.created_at);
              const today = new Date();
              return logDate.toDateString() === today.toDateString();
            }).length}
          </div>
          <div className="text-sm text-gray-500 uppercase tracking-wider">Hoje</div>
        </div>
      </div>

      {/* Logs Timeline */}
      {loading ? (
        <div className="card-technical rounded-xl p-6 text-center py-12">
          <div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
        </div>
      ) : logs.length === 0 && page === 0 ? (
        <EmptyState icon={ClipboardList} title="Nenhum registro de auditoria" testId="no-logs" />
      ) : (
        <div className="card-technical rounded-xl p-6">
          <div className="space-y-4 max-h-[600px] overflow-y-auto">
            {logs.map((log) => (
              <div
                key={log.id}
                className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg animate-fade-in"
                data-testid={`log-${log.id}`}
              >
                <div className="w-2 h-2 bg-carmesim rounded-full mt-2 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-sans text-grafite mb-1">{log.action}</p>
                  <div className="flex items-center gap-4 text-xs font-mono text-gray-500">
                    <span>User ID: {log.user_id}</span>
                    {log.target_id && <span>Target: {log.target_id}</span>}
                    <span>
                      {format(new Date(log.created_at), "dd/MM/yyyy 'às' HH:mm:ss", { locale: ptBR })}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Paginação por página (skip/limit) */}
          {(page > 0 || hasNext) && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--surface-border)]">
              <span className="text-xs text-gray-500">
                Registros {skip + 1}–{skip + logs.length}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0 || isFetching}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-white border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                  data-testid="logs-prev-page"
                >
                  <ChevronLeft className="w-4 h-4" aria-hidden="true" />
                  Anterior
                </button>
                <button
                  type="button"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!hasNext || isFetching}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-white border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                  data-testid="logs-next-page"
                >
                  Próxima
                  <ChevronRight className="w-4 h-4" aria-hidden="true" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
