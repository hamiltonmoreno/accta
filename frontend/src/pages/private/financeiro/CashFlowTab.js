import React, { useEffect, useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { financesAPI } from '../../../utils/api';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  DollarSign, TrendingUp, TrendingDown, Plus, Pencil, Trash2,
  ArrowUpCircle, ArrowDownCircle, X, Filter, Wallet,
  Search, ChevronLeft, ChevronRight, FileSpreadsheet,
} from 'lucide-react';
import { TransactionModal } from './TransactionModal';
import { CATEGORY_LABELS, PAGE_SIZE } from './constants';
import { EmptyState } from '../../../components/EmptyState';
import { Skeleton } from '../../../components/ui/skeleton';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '../../../components/ui/alert-dialog';

// `delay` removido — stagger entre 4 cards era cosmetico (0-0.2s).
const StatBlock = ({ label, value, icon: Icon, color }) => (
  <div className="card-technical p-4 sm:p-5 animate-fade-up">
    <div className={`w-9 h-9 sm:w-10 sm:h-10 ${color} rounded-lg flex items-center justify-center mb-2 sm:mb-3`}>
      <Icon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
    </div>
    <div className="font-mono text-lg sm:text-2xl font-bold text-grafite-auto">{value}</div>
    <div className="text-xs uppercase tracking-wider mt-0.5 text-muted-auto">{label}</div>
  </div>
);

export const CashFlowTab = ({ canManage = true }) => {
  const qc = useQueryClient();
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [filterType, setFilterType] = useState('');
  const [searchText, setSearchText] = useState('');
  const [searchDebounced, setSearchDebounced] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [page, setPage] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const [editingTx, setEditingTx] = useState(null);

  const currentYear = new Date().getFullYear();

  useEffect(() => {
    const timer = setTimeout(() => setSearchDebounced(searchText), 400);
    return () => clearTimeout(timer);
  }, [searchText]);

  useEffect(() => { setPage(0); }, [filterType, searchDebounced, startDate, endDate]);

  const buildParams = useCallback(() => {
    const params = { skip: page * PAGE_SIZE, limit: PAGE_SIZE };
    if (filterType) params.type = filterType;
    if (searchDebounced) params.search = searchDebounced;
    if (startDate) params.start_date = `${startDate}T00:00:00`;
    if (endDate) params.end_date = `${endDate}T23:59:59`;
    return params;
  }, [filterType, searchDebounced, startDate, endDate, page]);

  // Listagem paginada — queryKey contem todos os filtros para cache
  // separado por combinacao. keepPreviousData evita flicker no paginate.
  const transactionsQuery = useQuery({
    queryKey: ['transactions', { filterType, searchDebounced, startDate, endDate, page }],
    queryFn: async () => {
      const res = await financesAPI.getTransactions(buildParams());
      return res.data;
    },
    placeholderData: (prev) => prev, // keepPreviousData equivalent (v5)
  });

  // Summary anual e independente dos filtros — query separada com cache proprio.
  const summaryQuery = useQuery({
    queryKey: ['transactions', 'summary', currentYear],
    queryFn: async () => (await financesAPI.getSummary({ year: currentYear })).data,
  });

  const transactions = transactionsQuery.data?.items || [];
  const total = transactionsQuery.data?.total || 0;
  const summary = summaryQuery.data;
  const loading = transactionsQuery.isLoading || summaryQuery.isLoading;

  const invalidateAll = () => qc.invalidateQueries({ queryKey: ['transactions'] });

  const deleteMutation = useMutation({
    mutationFn: (id) => financesAPI.deleteTransaction(id),
    onSuccess: () => {
      toast.success('Transacao removida');
      invalidateAll();
    },
    onError: () => toast.error('Erro ao remover'),
  });

  const exportMutation = useMutation({
    mutationFn: () => {
      const params = {};
      if (filterType) params.type = filterType;
      if (searchDebounced) params.search = searchDebounced;
      if (startDate) params.start_date = `${startDate}T00:00:00`;
      if (endDate) params.end_date = `${endDate}T23:59:59`;
      return financesAPI.exportTransactionsCsv(params);
    },
    onSuccess: (res) => {
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Fluxo_Caixa_ACCTA.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('CSV exportado');
    },
    onError: () => toast.error('Erro ao exportar CSV'),
  });

  const csvExporting = exportMutation.isPending;

  const handleDelete = (id) => setConfirmDeleteId(id);

  const confirmDelete = () => {
    if (confirmDeleteId) deleteMutation.mutate(confirmDeleteId);
    setConfirmDeleteId(null);
  };

  const handleExportCSV = () => exportMutation.mutate();

  const openEdit = (tx) => { setEditingTx(tx); setShowModal(true); };
  const openNew = () => { setEditingTx(null); setShowModal(true); };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="space-y-5">
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <StatBlock label="Receitas" value={`${summary.total_receitas.toLocaleString('pt')} CVE`} icon={TrendingUp} color="bg-[#16A34A]" />
          <StatBlock label="Despesas" value={`${summary.total_despesas.toLocaleString('pt')} CVE`} icon={TrendingDown} color="bg-carmesim" />
          <StatBlock label="Resultado" value={`${summary.resultado_liquido.toLocaleString('pt')} CVE`} icon={Wallet} color={summary.resultado_liquido >= 0 ? 'bg-grafite' : 'bg-[#D97706]'} />
          <StatBlock label="Transacoes" value={summary.total_transacoes} icon={DollarSign} color="bg-grafite" />
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        {canManage && (
          <button onClick={openNew} className="btn-primary flex items-center gap-2 text-sm" data-testid="add-transaction-btn">
            <Plus className="w-4 h-4" /> Nova Transacao
          </button>
        )}
        <button onClick={handleExportCSV} disabled={csvExporting} className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all btn-outline" data-testid="export-csv-btn">
          <FileSpreadsheet className={`w-4 h-4 ${csvExporting ? 'animate-spin' : ''}`} />
          {csvExporting ? 'A exportar...' : 'Exportar CSV'}
        </button>
      </div>

      {/* Filters Bar */}
      <div className="card-technical p-3 sm:p-4">
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="relative flex-1 min-w-[180px] max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Pesquisar descricao..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="w-full pl-9 pr-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="search-input"
            />
          </div>
          <div className="flex items-center gap-1.5">
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}
              className="px-2.5 py-2.5 border border-gray-200 rounded-lg text-xs focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none" data-testid="start-date-filter" />
            <span className="text-[#6B7280] text-xs">a</span>
            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)}
              className="px-2.5 py-2.5 border border-gray-200 rounded-lg text-xs focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none" data-testid="end-date-filter" />
          </div>
          <div className="flex items-center gap-1.5 ml-auto">
            <Filter className="w-4 h-4 text-gray-400 hidden sm:block" />
            {['', 'receita', 'despesa'].map((f) => (
              <button key={f} onClick={() => setFilterType(f)} data-testid={`filter-type-${f || 'all'}`}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                  filterType === f ? 'bg-grafite text-white' : 'btn-outline !h-auto !px-3 !py-1.5'
                }`}
              >
                {f === '' ? 'Todos' : f === 'receita' ? 'Receitas' : 'Despesas'}
              </button>
            ))}
          </div>
        </div>

        {(searchDebounced || startDate || endDate) && (
          <div className="flex items-center gap-2 mt-2 pt-2 border-t border-[var(--surface-border)]">
            <span className="text-xs text-[#6B7280] uppercase tracking-wider">Filtros ativos:</span>
            {searchDebounced && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded-full text-xs text-gray-600">
                "{searchDebounced}" <button onClick={() => setSearchText('')} className="hover:text-carmesim" aria-label="Limpar pesquisa"><X className="w-3 h-3" aria-hidden="true" /></button>
              </span>
            )}
            {startDate && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded-full text-xs text-gray-600">
                De: {startDate} <button onClick={() => setStartDate('')} className="hover:text-carmesim" aria-label="Limpar data inicial"><X className="w-3 h-3" aria-hidden="true" /></button>
              </span>
            )}
            {endDate && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded-full text-xs text-gray-600">
                Ate: {endDate} <button onClick={() => setEndDate('')} className="hover:text-carmesim" aria-label="Limpar data final"><X className="w-3 h-3" aria-hidden="true" /></button>
              </span>
            )}
            <button onClick={() => { setSearchText(''); setStartDate(''); setEndDate(''); setFilterType(''); }}
              className="text-xs text-carmesim font-semibold hover:underline ml-auto">Limpar todos</button>
          </div>
        )}
      </div>

      {/* Transactions Table */}
      {loading ? (
        <div className="card-technical overflow-hidden divide-y divide-gray-50" data-testid="transactions-loading">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-3.5">
              <Skeleton className="h-5 w-20 rounded-full" />
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-3 flex-1 min-w-0" />
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-3 w-20" />
            </div>
          ))}
        </div>
      ) : transactions.length === 0 ? (
        <EmptyState icon={DollarSign} title="Nenhuma transacao encontrada" testId="no-transactions" />
      ) : (
        <div className="card-technical overflow-hidden">
          <>
            {/* Desktop */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50/80 text-[#6B7280] uppercase text-xs tracking-wider">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Tipo</th>
                    <th className="px-4 py-3 font-semibold">Categoria</th>
                    <th className="px-4 py-3 font-semibold">Descricao</th>
                    <th className="px-4 py-3 font-semibold text-right">Valor</th>
                    <th className="px-4 py-3 font-semibold">Data</th>
                    {canManage && <th className="px-4 py-3 font-semibold text-center">Acoes</th>}
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx) => (
                    <tr key={tx.id} className="border-t border-gray-50 hover:bg-gray-50/50 transition-colors" data-testid={`tx-row-${tx.id}`}>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                          tx.type === 'receita' ? 'bg-[#F0FDF4] text-[#15803D]' : 'bg-[#FEF2F2] text-[#B91C1C]'
                        }`}>
                          {tx.type === 'receita' ? <ArrowUpCircle className="w-3 h-3" /> : <ArrowDownCircle className="w-3 h-3" />}
                          {tx.type}
                        </span>
                      </td>
                      <td className="px-4 py-3 capitalize text-xs text-secondary-auto">{CATEGORY_LABELS[tx.category] || tx.category}</td>
                      <td className="px-4 py-3 font-medium text-xs max-w-[200px] truncate text-grafite-auto" title={tx.description}>{tx.description}</td>
                      <td className={`px-4 py-3 font-mono font-bold text-right ${tx.type === 'receita' ? 'text-[#15803D]' : 'text-[#B91C1C]'}`}>
                        {tx.type === 'receita' ? '+' : '-'}{tx.amount.toLocaleString('pt')} CVE
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-muted-auto">
                        {tx.date ? format(new Date(tx.date), 'dd/MM/yyyy', { locale: ptBR }) : '-'}
                      </td>
                      {canManage && (
                        <td className="px-4 py-3 text-center">
                          <div className="flex items-center justify-center gap-1">
                            <button onClick={() => openEdit(tx)} className="p-1.5 rounded-md hover:bg-gray-100 text-gray-400 hover:text-carmesim" aria-label="Editar transação" data-testid={`edit-tx-${tx.id}`}>
                              <Pencil className="w-3.5 h-3.5" aria-hidden="true" />
                            </button>
                            <button onClick={() => handleDelete(tx.id)} className="p-1.5 rounded-md hover:bg-[#FEF2F2] text-gray-400 hover:text-[#B91C1C]" aria-label="Apagar transação" data-testid={`delete-tx-${tx.id}`}>
                              <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile */}
            <div className="md:hidden divide-y divide-gray-50">
              {transactions.map((tx) => (
                <div key={tx.id} className="p-4" data-testid={`tx-card-${tx.id}`}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className={`inline-flex items-center gap-1 text-xs font-bold uppercase ${tx.type === 'receita' ? 'text-[#15803D]' : 'text-[#B91C1C]'}`}>
                      {tx.type === 'receita' ? <ArrowUpCircle className="w-3 h-3" /> : <ArrowDownCircle className="w-3 h-3" />}
                      {CATEGORY_LABELS[tx.category] || tx.category}
                    </span>
                    <span className={`font-mono font-bold text-sm tabular-nums ${tx.type === 'receita' ? 'text-[#15803D]' : 'text-[#B91C1C]'}`}>
                      {tx.type === 'receita' ? '+' : '-'}{tx.amount.toLocaleString('pt')} CVE
                    </span>
                  </div>
                  <p className="text-xs truncate text-grafite-auto">{tx.description}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-[#6B7280]">{tx.date ? format(new Date(tx.date), 'dd/MM/yyyy', { locale: ptBR }) : '-'}</span>
                    {canManage && (
                      <div className="flex items-center gap-1">
                        <button onClick={() => openEdit(tx)} className="p-2 -m-2 text-gray-400 hover:text-carmesim" aria-label="Editar transação"><Pencil className="w-4 h-4" aria-hidden="true" /></button>
                        <button onClick={() => handleDelete(tx.id)} className="p-2 -m-2 text-gray-400 hover:text-[#B91C1C]" aria-label="Apagar transação"><Trash2 className="w-4 h-4" aria-hidden="true" /></button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--surface-border)]">
                <span className="text-xs text-[#6B7280]">{page * PAGE_SIZE + 1}-{Math.min((page + 1) * PAGE_SIZE, total)} de {total}</span>
                <div className="flex items-center gap-1">
                  <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
                    className="p-1.5 rounded-md hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed" aria-label="Página anterior" data-testid="prev-page-btn">
                    <ChevronLeft className="w-4 h-4 text-gray-500" aria-hidden="true" />
                  </button>
                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) pageNum = i;
                    else if (page < 3) pageNum = i;
                    else if (page > totalPages - 4) pageNum = totalPages - 5 + i;
                    else pageNum = page - 2 + i;
                    return (
                      <button key={pageNum} onClick={() => setPage(pageNum)} data-testid={`page-${pageNum}`}
                        className={`w-8 h-8 rounded-md text-xs font-semibold transition-all ${
                          page === pageNum ? 'bg-carmesim text-white' : 'text-gray-500 hover:bg-gray-100'
                        }`}>{pageNum + 1}</button>
                    );
                  })}
                  <button onClick={() => setPage(Math.min(totalPages - 1, page + 1))} disabled={page >= totalPages - 1}
                    className="p-1.5 rounded-md hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed" aria-label="Próxima página" data-testid="next-page-btn">
                    <ChevronRight className="w-4 h-4 text-gray-500" aria-hidden="true" />
                  </button>
                </div>
              </div>
            )}
          </>
        </div>
      )}

      {showModal && (
        <TransactionModal
          tx={editingTx}
          onClose={() => { setShowModal(false); setEditingTx(null); }}
          onSaved={invalidateAll}
        />
      )}

      <AlertDialog open={confirmDeleteId !== null} onOpenChange={(open) => !open && setConfirmDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover transação?</AlertDialogTitle>
            <AlertDialogDescription>Esta ação não pode ser desfeita.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction className="bg-[#C7202F] hover:bg-[#A51B27]" onClick={confirmDelete}>
              Remover
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
