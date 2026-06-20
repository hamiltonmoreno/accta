import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Megaphone, Pencil, Trash2, XCircle } from 'lucide-react';
import {
  Table, TableHeader, TableBody, TableHead, TableRow, TableCell,
} from '../../../components/ui/table';
import { Skeleton } from '../../../components/ui/skeleton';
import { EmptyState } from '../../../components/EmptyState';
import { comunicadosAPI } from '../../../utils/api';
import { queryKeys } from '../../../lib/queryClient';
import { StatusBadge, segmentDescription, audienceDescription } from './widgets';
import {
  CHANNEL_LABELS, PAGE_SIZE, TIPO_LABELS, formatDate,
} from './tokens';

export function HistoryTable({ onEditDraft, onDeleteDraft }) {
  const [page, setPage] = useState(0);
  const skip = page * PAGE_SIZE;

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.comunicados.list({ skip, limit: PAGE_SIZE }),
    queryFn: async () => (await comunicadosAPI.list({ skip, limit: PAGE_SIZE })).data,
    staleTime: 15 * 1000,
  });

  const items = data?.items || [];
  const total = data?.total ?? 0;
  const hasNext = skip + items.length < total;

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-12 w-full rounded-md" />)}
      </div>
    );
  }

  if (isError) {
    return (
      <EmptyState
        icon={XCircle}
        title="Não foi possível carregar o histórico"
        description="Tente novamente dentro de momentos."
        testId="comunicados-history-error"
      />
    );
  }

  if (items.length === 0 && page === 0) {
    return (
      <EmptyState
        icon={Megaphone}
        title="Ainda não há comunicados"
        description="Os comunicados que enviar aparecerão aqui."
        testId="comunicados-history-empty"
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Assunto</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Canais</TableHead>
            <TableHead>Segmento</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead className="text-right">E-mail (env./falh.)</TableHead>
            <TableHead className="text-right">Na app</TableHead>
            <TableHead>Data</TableHead>
            <TableHead>Autor</TableHead>
            <TableHead className="text-right">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((c) => (
            <TableRow key={c.id} className="hover:bg-[#F5F5F5]" data-testid={`comunicado-row-${c.id}`}>
              <TableCell className="font-medium text-grafite max-w-[16rem] truncate" title={c.subject}>
                {c.subject}
              </TableCell>
              <TableCell className="text-[#6B7280]">{TIPO_LABELS[c.tipo] || c.tipo}</TableCell>
              <TableCell className="text-[#6B7280]">
                {(c.channels || []).map((ch) => CHANNEL_LABELS[ch] || ch).join(' · ')}
              </TableCell>
              <TableCell className="text-[#6B7280] max-w-[14rem]">
                {c.audience_filter ? (
                  <div className="space-y-0.5">
                    <div className="truncate" title={audienceDescription(c.audience_filter)}>
                      {audienceDescription(c.audience_filter)}
                    </div>
                    <div className="text-xs text-[#6B7280] tabular-nums">
                      {(c.audience_resolved?.length ?? c.recipients_count ?? 0)} destinatário(s)
                      {(c.failed_member_ids?.length ?? 0) > 0 && (
                        <span className="text-[#B91C1C]"> · {c.failed_member_ids.length} falha(s)</span>
                      )}
                      {c.dry_run && <span className="text-[#B45309]"> · simulação</span>}
                    </div>
                  </div>
                ) : (
                  <span className="block truncate" title={segmentDescription(c.segment)}>
                    {segmentDescription(c.segment)}
                  </span>
                )}
              </TableCell>
              <TableCell><StatusBadge status={c.status} /></TableCell>
              <TableCell className="text-right text-[#6B7280] tabular-nums">
                {c.email_sent ?? 0}
                {(c.email_failed ?? 0) > 0 && (
                  <span className="text-[#B91C1C]"> / {c.email_failed}</span>
                )}
              </TableCell>
              <TableCell className="text-right text-[#6B7280] tabular-nums">{c.inapp_created ?? 0}</TableCell>
              <TableCell className="text-[#6B7280] whitespace-nowrap">{formatDate(c.created_at)}</TableCell>
              <TableCell className="text-[#6B7280] max-w-[10rem] truncate" title={c.created_by}>
                {c.created_by}
              </TableCell>
              <TableCell className="text-right whitespace-nowrap">
                {c.status === 'rascunho' ? (
                  <div className="inline-flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => onEditDraft?.(c)}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-white border border-[#D1D5DB] text-grafite text-xs font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                      data-testid={`comunicado-edit-${c.id}`}
                    >
                      <Pencil className="w-3.5 h-3.5" aria-hidden="true" />
                      Editar
                    </button>
                    <button
                      type="button"
                      onClick={() => onDeleteDraft?.(c)}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-white border border-[#C7202F] text-[#C7202F] text-xs font-medium hover:bg-[#FBEAEC] transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                      data-testid={`comunicado-delete-${c.id}`}
                    >
                      <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                      Eliminar
                    </button>
                  </div>
                ) : (
                  <span className="text-[#6B7280]">—</span>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {(page > 0 || hasNext) && (
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-[#E5E7EB]">
          <span className="text-xs text-[#6B7280]">
            {total > 0 ? `${skip + 1}–${skip + items.length} de ${total}` : '—'}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-white border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
              data-testid="comunicados-prev-page"
            >
              <ChevronLeft className="w-4 h-4" aria-hidden="true" />
              Anterior
            </button>
            <button
              type="button"
              onClick={() => setPage((p) => p + 1)}
              disabled={!hasNext}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-white border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
              data-testid="comunicados-next-page"
            >
              Próxima
              <ChevronRight className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
