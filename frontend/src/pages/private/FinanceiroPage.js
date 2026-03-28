import React, { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { financesAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  DollarSign, TrendingUp, TrendingDown, Plus, Pencil, Trash2,
  FileBarChart, Settings, ArrowUpCircle, ArrowDownCircle,
  RefreshCw, X, Filter, Wallet, Download,
  Search, ChevronLeft, ChevronRight, FileSpreadsheet, CheckCircle, Users,
} from 'lucide-react';

const CATEGORY_LABELS = {
  quotas: 'Quotas', patrocinios: 'Patrocinios', doacoes: 'Doacoes',
  eventos: 'Eventos', outros_receita: 'Outros',
  operacional: 'Operacional', juridico: 'Juridico',
  comunicacao: 'Comunicacao', viagens: 'Viagens', outros_despesa: 'Outros',
};

const MONTH_NAMES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

const TabBtn = ({ active, label, icon: Icon, onClick, testId }) => (
  <button
    onClick={onClick}
    data-testid={testId}
    className={`flex items-center gap-2 px-4 py-2.5 text-sm font-semibold rounded-lg transition-all whitespace-nowrap ${
      active ? 'bg-carmesim text-white shadow-sm' : 'text-gray-500 hover:bg-gray-100 hover:text-grafite'
    }`}
  >
    <Icon className="w-4 h-4" />
    {label}
  </button>
);

const StatBlock = ({ label, value, icon: Icon, color, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay }}
    className="card-technical p-4 sm:p-5"
  >
    <div className={`w-9 h-9 sm:w-10 sm:h-10 ${color} rounded-lg flex items-center justify-center mb-2 sm:mb-3`}>
      <Icon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
    </div>
    <div className="font-mono text-lg sm:text-2xl font-bold text-grafite">{value}</div>
    <div className="text-[9px] sm:text-xs text-gray-500 uppercase tracking-wider mt-0.5">{label}</div>
  </motion.div>
);

const PAGE_SIZE = 20;

// ======== CASH FLOW TAB ========
const CashFlowTab = ({ isAdmin }) => {
  const [transactions, setTransactions] = useState([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('');
  const [searchText, setSearchText] = useState('');
  const [searchDebounced, setSearchDebounced] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [page, setPage] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const [editingTx, setEditingTx] = useState(null);
  const [csvExporting, setCsvExporting] = useState(false);

  const currentYear = new Date().getFullYear();

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setSearchDebounced(searchText), 400);
    return () => clearTimeout(timer);
  }, [searchText]);

  // Reset page on filter change
  useEffect(() => { setPage(0); }, [filterType, searchDebounced, startDate, endDate]);

  const buildParams = useCallback(() => {
    const params = { skip: page * PAGE_SIZE, limit: PAGE_SIZE };
    if (filterType) params.type = filterType;
    if (searchDebounced) params.search = searchDebounced;
    if (startDate) params.start_date = `${startDate}T00:00:00`;
    if (endDate) params.end_date = `${endDate}T23:59:59`;
    return params;
  }, [filterType, searchDebounced, startDate, endDate, page]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params = buildParams();
      const [txRes, sumRes] = await Promise.all([
        financesAPI.getTransactions(params),
        financesAPI.getSummary({ year: currentYear }),
      ]);
      setTransactions(txRes.data.items);
      setTotal(txRes.data.total);
      setSummary(sumRes.data);
    } catch {
      toast.error('Erro ao carregar dados financeiros');
    } finally {
      setLoading(false);
    }
  }, [buildParams, currentYear]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja remover esta transacao?')) return;
    try {
      await financesAPI.deleteTransaction(id);
      toast.success('Transacao removida');
      loadData();
    } catch { toast.error('Erro ao remover'); }
  };

  const handleExportCSV = async () => {
    setCsvExporting(true);
    try {
      const params = {};
      if (filterType) params.type = filterType;
      if (searchDebounced) params.search = searchDebounced;
      if (startDate) params.start_date = `${startDate}T00:00:00`;
      if (endDate) params.end_date = `${endDate}T23:59:59`;
      const res = await financesAPI.exportTransactionsCsv(params);
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Fluxo_Caixa_ACCTA.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('CSV exportado');
    } catch { toast.error('Erro ao exportar CSV'); }
    finally { setCsvExporting(false); }
  };

  const openEdit = (tx) => { setEditingTx(tx); setShowModal(true); };
  const openNew = () => { setEditingTx(null); setShowModal(true); };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="space-y-5">
      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <StatBlock label="Receitas" value={`${summary.total_receitas.toLocaleString('pt')} CVE`} icon={TrendingUp} color="bg-green-600" delay={0.05} />
          <StatBlock label="Despesas" value={`${summary.total_despesas.toLocaleString('pt')} CVE`} icon={TrendingDown} color="bg-carmesim" delay={0.1} />
          <StatBlock label="Resultado" value={`${summary.resultado_liquido.toLocaleString('pt')} CVE`} icon={Wallet} color={summary.resultado_liquido >= 0 ? 'bg-grafite' : 'bg-orange-500'} delay={0.15} />
          <StatBlock label="Transacoes" value={summary.total_transacoes} icon={DollarSign} color="bg-grafite" delay={0.2} />
        </div>
      )}

      {/* Actions Bar */}
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        <button onClick={openNew} className="btn-primary flex items-center gap-2 text-sm" data-testid="add-transaction-btn">
          <Plus className="w-4 h-4" /> Nova Transacao
        </button>
        <button onClick={handleExportCSV} disabled={csvExporting} className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold bg-white border border-gray-200 text-grafite hover:bg-gray-50 transition-all" data-testid="export-csv-btn">
          <FileSpreadsheet className={`w-4 h-4 ${csvExporting ? 'animate-spin' : ''}`} />
          {csvExporting ? 'A exportar...' : 'Exportar CSV'}
        </button>
      </div>

      {/* Filters Bar */}
      <div className="card-technical p-3 sm:p-4">
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-[180px] max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Pesquisar descricao..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="search-input"
            />
          </div>

          {/* Date Range */}
          <div className="flex items-center gap-1.5">
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="px-2.5 py-2 border border-gray-200 rounded-lg text-xs focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="start-date-filter"
            />
            <span className="text-gray-400 text-xs">a</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="px-2.5 py-2 border border-gray-200 rounded-lg text-xs focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="end-date-filter"
            />
          </div>

          {/* Type filter */}
          <div className="flex items-center gap-1.5 ml-auto">
            <Filter className="w-4 h-4 text-gray-400 hidden sm:block" />
            {['', 'receita', 'despesa'].map((f) => (
              <button
                key={f}
                onClick={() => setFilterType(f)}
                data-testid={`filter-type-${f || 'all'}`}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                  filterType === f ? 'bg-grafite text-white' : 'bg-white text-gray-500 border border-gray-100 hover:bg-gray-50'
                }`}
              >
                {f === '' ? 'Todos' : f === 'receita' ? 'Receitas' : 'Despesas'}
              </button>
            ))}
          </div>
        </div>

        {/* Active filters summary */}
        {(searchDebounced || startDate || endDate) && (
          <div className="flex items-center gap-2 mt-2 pt-2 border-t border-gray-100">
            <span className="text-[10px] text-gray-400 uppercase tracking-wider">Filtros ativos:</span>
            {searchDebounced && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded-full text-[11px] text-gray-600">
                "{searchDebounced}"
                <button onClick={() => setSearchText('')} className="hover:text-carmesim"><X className="w-3 h-3" /></button>
              </span>
            )}
            {startDate && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded-full text-[11px] text-gray-600">
                De: {startDate}
                <button onClick={() => setStartDate('')} className="hover:text-carmesim"><X className="w-3 h-3" /></button>
              </span>
            )}
            {endDate && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded-full text-[11px] text-gray-600">
                Ate: {endDate}
                <button onClick={() => setEndDate('')} className="hover:text-carmesim"><X className="w-3 h-3" /></button>
              </span>
            )}
            <button
              onClick={() => { setSearchText(''); setStartDate(''); setEndDate(''); setFilterType(''); }}
              className="text-[11px] text-carmesim font-semibold hover:underline ml-auto"
            >
              Limpar todos
            </button>
          </div>
        )}
      </div>

      {/* Transactions Table */}
      <div className="card-technical overflow-hidden">
        {loading ? (
          <div className="p-10 text-center">
            <div className="inline-block w-7 h-7 border-3 border-carmesim border-t-transparent rounded-full animate-spin" />
          </div>
        ) : transactions.length === 0 ? (
          <div className="p-10 text-center" data-testid="no-transactions">
            <DollarSign className="w-10 h-10 text-gray-200 mx-auto mb-2" />
            <p className="text-sm text-gray-400">Nenhuma transacao encontrada</p>
          </div>
        ) : (
          <>
            {/* Desktop */}
            <div className="hidden sm:block overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50/80 text-gray-400 uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Tipo</th>
                    <th className="px-4 py-3 font-semibold">Categoria</th>
                    <th className="px-4 py-3 font-semibold">Descricao</th>
                    <th className="px-4 py-3 font-semibold text-right">Valor</th>
                    <th className="px-4 py-3 font-semibold">Data</th>
                    <th className="px-4 py-3 font-semibold text-center">Acoes</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx) => (
                    <tr key={tx.id} className="border-t border-gray-50 hover:bg-gray-50/50 transition-colors" data-testid={`tx-row-${tx.id}`}>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                          tx.type === 'receita' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                        }`}>
                          {tx.type === 'receita' ? <ArrowUpCircle className="w-3 h-3" /> : <ArrowDownCircle className="w-3 h-3" />}
                          {tx.type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600 capitalize text-xs">{CATEGORY_LABELS[tx.category] || tx.category}</td>
                      <td className="px-4 py-3 text-grafite font-medium text-xs max-w-[200px] truncate">{tx.description}</td>
                      <td className={`px-4 py-3 font-mono font-bold text-right ${tx.type === 'receita' ? 'text-green-600' : 'text-red-600'}`}>
                        {tx.type === 'receita' ? '+' : '-'}{tx.amount.toLocaleString('pt')} CVE
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-500 text-xs">
                        {tx.date ? format(new Date(tx.date), 'dd/MM/yyyy', { locale: ptBR }) : '-'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <button onClick={() => openEdit(tx)} className="p-1.5 rounded-md hover:bg-gray-100 text-gray-400 hover:text-carmesim" data-testid={`edit-tx-${tx.id}`}>
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                          <button onClick={() => handleDelete(tx.id)} className="p-1.5 rounded-md hover:bg-red-50 text-gray-400 hover:text-red-500" data-testid={`delete-tx-${tx.id}`}>
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile */}
            <div className="sm:hidden divide-y divide-gray-50">
              {transactions.map((tx) => (
                <div key={tx.id} className="p-4" data-testid={`tx-card-${tx.id}`}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className={`inline-flex items-center gap-1 text-xs font-bold uppercase ${tx.type === 'receita' ? 'text-green-600' : 'text-red-600'}`}>
                      {tx.type === 'receita' ? <ArrowUpCircle className="w-3 h-3" /> : <ArrowDownCircle className="w-3 h-3" />}
                      {CATEGORY_LABELS[tx.category] || tx.category}
                    </span>
                    <span className={`font-mono font-bold text-sm ${tx.type === 'receita' ? 'text-green-600' : 'text-red-600'}`}>
                      {tx.type === 'receita' ? '+' : '-'}{tx.amount.toLocaleString('pt')} CVE
                    </span>
                  </div>
                  <p className="text-xs text-grafite truncate">{tx.description}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-[11px] text-gray-400">
                      {tx.date ? format(new Date(tx.date), 'dd/MM/yyyy', { locale: ptBR }) : '-'}
                    </span>
                    <div className="flex items-center gap-1">
                      <button onClick={() => openEdit(tx)} className="p-1 text-gray-400 hover:text-carmesim"><Pencil className="w-3.5 h-3.5" /></button>
                      <button onClick={() => handleDelete(tx.id)} className="p-1 text-gray-400 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
                <span className="text-[11px] text-gray-400">
                  {page * PAGE_SIZE + 1}-{Math.min((page + 1) * PAGE_SIZE, total)} de {total}
                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setPage(Math.max(0, page - 1))}
                    disabled={page === 0}
                    className="p-1.5 rounded-md hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
                    data-testid="prev-page-btn"
                  >
                    <ChevronLeft className="w-4 h-4 text-gray-500" />
                  </button>
                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i;
                    } else if (page < 3) {
                      pageNum = i;
                    } else if (page > totalPages - 4) {
                      pageNum = totalPages - 5 + i;
                    } else {
                      pageNum = page - 2 + i;
                    }
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPage(pageNum)}
                        className={`w-8 h-8 rounded-md text-xs font-semibold transition-all ${
                          page === pageNum ? 'bg-carmesim text-white' : 'text-gray-500 hover:bg-gray-100'
                        }`}
                        data-testid={`page-${pageNum}`}
                      >
                        {pageNum + 1}
                      </button>
                    );
                  })}
                  <button
                    onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                    disabled={page >= totalPages - 1}
                    className="p-1.5 rounded-md hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
                    data-testid="next-page-btn"
                  >
                    <ChevronRight className="w-4 h-4 text-gray-500" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <TransactionModal
          tx={editingTx}
          onClose={() => { setShowModal(false); setEditingTx(null); }}
          onSaved={() => { setShowModal(false); setEditingTx(null); loadData(); }}
        />
      )}
    </div>
  );
};

// ======== TRANSACTION MODAL ========
const TransactionModal = ({ tx, onClose, onSaved }) => {
  const isEdit = !!tx;
  const [form, setForm] = useState({
    type: tx?.type || 'receita',
    category: tx?.category || 'quotas',
    description: tx?.description || '',
    amount: tx?.amount || '',
    date: tx?.date ? tx.date.split('T')[0] : new Date().toISOString().split('T')[0],
    reference: tx?.reference || '',
  });
  const [saving, setSaving] = useState(false);

  const incomeCategories = [
    { value: 'quotas', label: 'Quotas' },
    { value: 'patrocinios', label: 'Patrocinios' },
    { value: 'doacoes', label: 'Doacoes' },
    { value: 'eventos', label: 'Eventos' },
    { value: 'outros_receita', label: 'Outros' },
  ];
  const expenseCategories = [
    { value: 'operacional', label: 'Operacional' },
    { value: 'eventos', label: 'Eventos' },
    { value: 'juridico', label: 'Juridico' },
    { value: 'comunicacao', label: 'Comunicacao' },
    { value: 'viagens', label: 'Viagens' },
    { value: 'outros_despesa', label: 'Outros' },
  ];

  const categories = form.type === 'receita' ? incomeCategories : expenseCategories;

  useEffect(() => {
    if (!isEdit) {
      setForm((prev) => ({ ...prev, category: form.type === 'receita' ? 'quotas' : 'operacional' }));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.type]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.description || !form.amount || !form.date) {
      toast.error('Preencha todos os campos obrigatorios');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...form,
        amount: parseFloat(form.amount),
        date: new Date(form.date).toISOString(),
      };
      if (isEdit) {
        await financesAPI.updateTransaction(tx.id, payload);
        toast.success('Transacao atualizada');
      } else {
        await financesAPI.createTransaction(payload);
        toast.success('Transacao criada');
      }
      onSaved();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <h2 className="font-bold text-grafite text-lg">{isEdit ? 'Editar Transacao' : 'Nova Transacao'}</h2>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-gray-100 text-gray-400" data-testid="close-modal-btn"><X className="w-5 h-5" /></button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Tipo</label>
            <div className="flex gap-2">
              {[{ val: 'receita', label: 'Receita', color: 'bg-green-600' }, { val: 'despesa', label: 'Despesa', color: 'bg-red-600' }].map((opt) => (
                <button
                  key={opt.val}
                  type="button"
                  onClick={() => setForm({ ...form, type: opt.val })}
                  data-testid={`type-${opt.val}`}
                  className={`flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                    form.type === opt.val ? `${opt.color} text-white` : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Categoria</label>
            <select
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="category-select"
            >
              {categories.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Descricao *</label>
            <input
              type="text"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Ex: Quota mensal Janeiro 2026"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="description-input"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Valor (CVE) *</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                placeholder="2000"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
                data-testid="amount-input"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Data *</label>
              <input
                type="date"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
                data-testid="date-input"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Referencia</label>
            <input
              type="text"
              value={form.reference}
              onChange={(e) => setForm({ ...form, reference: e.target.value })}
              placeholder="Ex: FOLHA-202601"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="reference-input"
            />
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full btn-primary py-3 text-sm font-semibold"
            data-testid="save-transaction-btn"
          >
            {saving ? 'A guardar...' : isEdit ? 'Atualizar' : 'Criar Transacao'}
          </button>
        </form>
      </motion.div>
    </div>
  );
};

// ======== DRE TAB (with percentages) ========
const DRETab = () => {
  const [year, setYear] = useState(new Date().getFullYear());
  const [dre, setDRE] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const loadDRE = useCallback(async () => {
    setLoading(true);
    try {
      const res = await financesAPI.getDRE(year);
      setDRE(res.data);
    } catch { toast.error('Erro ao carregar DRE'); }
    finally { setLoading(false); }
  }, [year]);

  useEffect(() => { loadDRE(); }, [loadDRE]);

  const handleExportPDF = async () => {
    setExporting(true);
    try {
      const res = await financesAPI.exportDREPdf(year);
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `DRE_ACCTA_${year}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('PDF exportado com sucesso');
    } catch {
      toast.error('Erro ao exportar PDF');
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-10 text-center">
        <div className="inline-block w-7 h-7 border-3 border-carmesim border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!dre) return null;

  const maxMonthly = Math.max(
    ...Object.values(dre.monthly).map((m) => Math.max(m.receitas, m.despesas)),
    1
  );

  const calcPct = (val, total) => total > 0 ? ((val / total) * 100).toFixed(0) : '0';

  return (
    <div className="space-y-5">
      {/* Year Selector + Export */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-semibold text-gray-500">Ano:</label>
        <select
          value={year}
          onChange={(e) => setYear(parseInt(e.target.value))}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
          data-testid="dre-year-select"
        >
          {[2024, 2025, 2026, 2027].map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>

        <button
          onClick={handleExportPDF}
          disabled={exporting || loading}
          className="ml-auto btn-primary flex items-center gap-2 text-sm"
          data-testid="export-dre-pdf-btn"
        >
          <Download className={`w-4 h-4 ${exporting ? 'animate-bounce' : ''}`} />
          {exporting ? 'A exportar...' : 'Exportar PDF'}
        </button>
      </div>

      {/* Totals */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
        <div className="card-technical p-4 sm:p-5 border-l-4 border-l-green-500">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Total Receitas</div>
          <div className="font-mono text-xl sm:text-2xl font-bold text-green-600" data-testid="dre-total-receitas">
            {dre.total_receitas.toLocaleString('pt')} CVE
          </div>
        </div>
        <div className="card-technical p-4 sm:p-5 border-l-4 border-l-red-500">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Total Despesas</div>
          <div className="font-mono text-xl sm:text-2xl font-bold text-red-600" data-testid="dre-total-despesas">
            {dre.total_despesas.toLocaleString('pt')} CVE
          </div>
        </div>
        <div className={`card-technical p-4 sm:p-5 border-l-4 ${dre.resultado_liquido >= 0 ? 'border-l-grafite' : 'border-l-orange-500'}`}>
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Resultado Liquido</div>
          <div className={`font-mono text-xl sm:text-2xl font-bold ${dre.resultado_liquido >= 0 ? 'text-grafite' : 'text-orange-600'}`} data-testid="dre-resultado">
            {dre.resultado_liquido.toLocaleString('pt')} CVE
          </div>
        </div>
      </div>

      {/* Monthly Chart */}
      <div className="card-technical p-4 sm:p-5">
        <h3 className="font-semibold text-grafite text-sm mb-4">Evolucao Mensal</h3>
        <div className="space-y-2">
          {Object.entries(dre.monthly).map(([month, data]) => (
            <div key={month} className="flex items-center gap-2 sm:gap-3" data-testid={`dre-month-${month}`}>
              <span className="text-[11px] font-mono text-gray-500 w-7 text-right">{MONTH_NAMES[parseInt(month) - 1]}</span>
              <div className="flex-1 flex gap-1 h-5">
                <div
                  className="bg-green-500 rounded-sm h-full transition-all duration-500"
                  style={{ width: `${(data.receitas / maxMonthly) * 100}%`, minWidth: data.receitas > 0 ? '2px' : '0px' }}
                  title={`Receitas: ${data.receitas.toLocaleString('pt')} CVE`}
                />
                <div
                  className="bg-red-400 rounded-sm h-full transition-all duration-500"
                  style={{ width: `${(data.despesas / maxMonthly) * 100}%`, minWidth: data.despesas > 0 ? '2px' : '0px' }}
                  title={`Despesas: ${data.despesas.toLocaleString('pt')} CVE`}
                />
              </div>
              <span className="text-[10px] font-mono text-gray-400 w-20 text-right hidden sm:block">
                {(data.receitas - data.despesas).toLocaleString('pt')}
              </span>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-4 mt-4 pt-3 border-t border-gray-100">
          <span className="flex items-center gap-1.5 text-[11px] text-gray-500">
            <span className="w-3 h-3 bg-green-500 rounded-sm" /> Receitas
          </span>
          <span className="flex items-center gap-1.5 text-[11px] text-gray-500">
            <span className="w-3 h-3 bg-red-400 rounded-sm" /> Despesas
          </span>
        </div>
      </div>

      {/* Category Breakdown WITH PERCENTAGES */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Income */}
        <div className="card-technical p-4 sm:p-5">
          <h3 className="font-semibold text-grafite text-sm mb-3 flex items-center gap-2">
            <ArrowUpCircle className="w-4 h-4 text-green-500" /> Receitas por Categoria
          </h3>
          {Object.keys(dre.receitas_por_categoria).length === 0 ? (
            <p className="text-xs text-gray-400">Sem receitas neste periodo</p>
          ) : (
            <div className="space-y-2.5">
              {Object.entries(dre.receitas_por_categoria).sort((a, b) => b[1] - a[1]).map(([cat, val]) => {
                const pct = calcPct(val, dre.total_receitas);
                return (
                  <div key={cat}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-600 capitalize">{CATEGORY_LABELS[cat] || cat}</span>
                      <span className="font-mono text-xs font-bold text-green-600">{val.toLocaleString('pt')} CVE <span className="text-gray-400 font-normal">({pct}%)</span></span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div className="bg-green-500 h-1.5 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Expenses */}
        <div className="card-technical p-4 sm:p-5">
          <h3 className="font-semibold text-grafite text-sm mb-3 flex items-center gap-2">
            <ArrowDownCircle className="w-4 h-4 text-red-500" /> Despesas por Categoria
          </h3>
          {Object.keys(dre.despesas_por_categoria).length === 0 ? (
            <p className="text-xs text-gray-400">Sem despesas neste periodo</p>
          ) : (
            <div className="space-y-2.5">
              {Object.entries(dre.despesas_por_categoria).sort((a, b) => b[1] - a[1]).map(([cat, val]) => {
                const pct = calcPct(val, dre.total_despesas);
                return (
                  <div key={cat}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-600 capitalize">{CATEGORY_LABELS[cat] || cat}</span>
                      <span className="font-mono text-xs font-bold text-red-600">{val.toLocaleString('pt')} CVE <span className="text-gray-400 font-normal">({pct}%)</span></span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div className="bg-red-400 h-1.5 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ======== SETTINGS TAB (with quota generation detail) ========
const SettingsTab = () => {
  const [settings, setSettings] = useState(null);
  const [quotaAmount, setQuotaAmount] = useState('');
  const [quotaDesc, setQuotaDesc] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [genMonth, setGenMonth] = useState(new Date().getMonth() + 1);
  const [genYear, setGenYear] = useState(new Date().getFullYear());
  const [genResult, setGenResult] = useState(null);

  useEffect(() => { loadSettings(); }, []);

  const loadSettings = async () => {
    try {
      const res = await financesAPI.getSettings();
      setSettings(res.data);
      setQuotaAmount(res.data.quota_amount);
      setQuotaDesc(res.data.quota_description);
    } catch { toast.error('Erro ao carregar configuracoes'); }
    finally { setLoading(false); }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await financesAPI.updateSettings({
        quota_amount: parseFloat(quotaAmount),
        quota_description: quotaDesc,
      });
      toast.success('Configuracoes atualizadas');
      loadSettings();
    } catch (err) { toast.error(err.response?.data?.detail || 'Erro ao salvar'); }
    finally { setSaving(false); }
  };

  const handleGenerate = async () => {
    if (!window.confirm(`Gerar quotas de ${MONTH_NAMES[genMonth - 1]}/${genYear} para todos os socios ativos?`)) return;
    setGenerating(true);
    setGenResult(null);
    try {
      const res = await financesAPI.generateQuotas(genMonth, genYear);
      setGenResult(res.data);
      toast.success(res.data.message);
    } catch (err) { toast.error(err.response?.data?.detail || 'Erro ao gerar quotas'); }
    finally { setGenerating(false); }
  };

  if (loading) {
    return (
      <div className="p-10 text-center">
        <div className="inline-block w-7 h-7 border-3 border-carmesim border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Quota Configuration */}
      <div className="card-technical p-5 sm:p-6">
        <h3 className="font-semibold text-grafite mb-4 flex items-center gap-2">
          <Settings className="w-4 h-4 text-carmesim" /> Configuracao de Quotas
        </h3>
        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Valor da Quota Mensal (CVE)</label>
            <input
              type="number"
              min="0"
              value={quotaAmount}
              onChange={(e) => setQuotaAmount(e.target.value)}
              className="w-full max-w-xs px-3 py-2.5 border border-gray-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="quota-amount-input"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Descricao da Quota</label>
            <input
              type="text"
              value={quotaDesc}
              onChange={(e) => setQuotaDesc(e.target.value)}
              className="w-full max-w-sm px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="quota-desc-input"
            />
          </div>
          <button onClick={handleSave} disabled={saving} className="btn-primary text-sm px-6" data-testid="save-settings-btn">
            {saving ? 'A guardar...' : 'Guardar Configuracoes'}
          </button>
        </div>
      </div>

      {/* Generate Quotas */}
      <div className="card-technical p-5 sm:p-6">
        <h3 className="font-semibold text-grafite mb-2 flex items-center gap-2">
          <RefreshCw className="w-4 h-4 text-carmesim" /> Gerar Quotas Mensais
        </h3>
        <p className="text-xs text-gray-500 mb-4 leading-relaxed">
          Gera automaticamente as quotas mensais para todos os socios ativos. Socios que ja possuem quota para o mes selecionado serao ignorados.
        </p>
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Mes</label>
            <select
              value={genMonth}
              onChange={(e) => setGenMonth(parseInt(e.target.value))}
              className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="gen-month-select"
            >
              {MONTH_NAMES.map((name, i) => (
                <option key={i} value={i + 1}>{name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Ano</label>
            <select
              value={genYear}
              onChange={(e) => setGenYear(parseInt(e.target.value))}
              className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="gen-year-select"
            >
              {[2024, 2025, 2026, 2027].map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
          <button onClick={handleGenerate} disabled={generating} className="btn-primary text-sm px-5 flex items-center gap-2" data-testid="generate-quotas-btn">
            <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
            {generating ? 'A gerar...' : 'Gerar Quotas'}
          </button>
        </div>

        {/* Generation Result Detail */}
        {genResult && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg"
            data-testid="gen-result"
          >
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="font-semibold text-sm text-green-700">Quotas Geradas com Sucesso</span>
            </div>
            <div className="grid grid-cols-3 gap-3 mt-2">
              <div className="text-center">
                <div className="font-mono text-lg font-bold text-green-700" data-testid="gen-created">{genResult.created}</div>
                <div className="text-[10px] text-green-600 uppercase tracking-wider">Criadas</div>
              </div>
              <div className="text-center">
                <div className="font-mono text-lg font-bold text-gray-500" data-testid="gen-skipped">{genResult.skipped}</div>
                <div className="text-[10px] text-gray-500 uppercase tracking-wider">Ignoradas</div>
              </div>
              <div className="text-center">
                <div className="font-mono text-lg font-bold text-grafite" data-testid="gen-total-value">{genResult.total_value?.toLocaleString('pt')}</div>
                <div className="text-[10px] text-gray-500 uppercase tracking-wider">CVE Total</div>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Info Banner */}
      <div className="card-technical p-4 sm:p-5 border-l-4 border-l-carmesim bg-carmesim/5">
        <div className="flex items-start gap-3">
          <DollarSign className="w-5 h-5 text-carmesim flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm text-grafite mb-1">Desconto em Folha</h4>
            <p className="text-xs text-gray-600 leading-relaxed">
              As quotas dos socios ativos sao descontadas diretamente na folha de pagamento. Nao existe o conceito de "socio inadimplente" nesta associacao.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// ======== MAIN PAGE ========
export const FinanceiroPage = () => {
  const { isAdmin, isFinanceiro } = useAuth();
  const hasFinanceAccess = isAdmin || isFinanceiro;
  const [activeTab, setActiveTab] = useState('cashflow');

  if (!hasFinanceAccess) {
    return <MemberFinanceView />;
  }

  return (
    <div className="space-y-5 sm:space-y-6">
      <div>
        <h1 className="page-title" data-testid="finance-title">Gestao Financeira</h1>
        <p className="page-subtitle">Fluxo de caixa, relatorios DRE e configuracoes</p>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
        <TabBtn active={activeTab === 'cashflow'} label="Fluxo de Caixa" icon={DollarSign} onClick={() => setActiveTab('cashflow')} testId="tab-cashflow" />
        <TabBtn active={activeTab === 'dre'} label="Relatorio DRE" icon={FileBarChart} onClick={() => setActiveTab('dre')} testId="tab-dre" />
        {isAdmin && (
          <TabBtn active={activeTab === 'settings'} label="Configuracoes" icon={Settings} onClick={() => setActiveTab('settings')} testId="tab-settings" />
        )}
      </div>

      {activeTab === 'cashflow' && <CashFlowTab isAdmin={isAdmin} />}
      {activeTab === 'dre' && <DRETab />}
      {activeTab === 'settings' && isAdmin && <SettingsTab />}
    </div>
  );
};

// ======== MEMBER VIEW ========
const MemberFinanceView = () => {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await (await import('../../utils/api')).invoicesAPI.getAll();
        setInvoices(res.data);
      } catch { /* ignore */ }
      finally { setLoading(false); }
    };
    load();
  }, []);

  const totalPago = invoices.filter((i) => i.status === 'pago').reduce((s, i) => s + i.amount, 0);

  return (
    <div className="space-y-5 sm:space-y-6">
      <div>
        <h1 className="page-title" data-testid="finance-title">Minhas Quotas</h1>
        <p className="page-subtitle">Acompanhe os seus pagamentos</p>
      </div>

      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="card-technical p-4 sm:p-5 border-l-4 border-l-carmesim bg-carmesim/5">
        <div className="flex items-start gap-3">
          <DollarSign className="w-5 h-5 text-carmesim flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-sm text-grafite mb-1">Pagamento Automatico</h3>
            <p className="text-xs sm:text-sm text-gray-600">As quotas mensais sao descontadas automaticamente em folha de pagamento.</p>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-2 gap-3 sm:gap-4">
        <StatBlock label="Registros" value={invoices.length} icon={DollarSign} color="bg-grafite" />
        <StatBlock label="Total Pago" value={`${totalPago.toLocaleString('pt')} CVE`} icon={TrendingUp} color="bg-green-600" delay={0.1} />
      </div>

      <div className="card-technical overflow-hidden">
        {loading ? (
          <div className="p-10 text-center"><div className="inline-block w-7 h-7 border-3 border-carmesim border-t-transparent rounded-full animate-spin" /></div>
        ) : invoices.length === 0 ? (
          <div className="p-10 text-center" data-testid="no-invoices">
            <DollarSign className="w-10 h-10 text-gray-200 mx-auto mb-2" />
            <p className="text-sm text-gray-400">Nenhum registro encontrado</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {invoices.map((inv) => (
              <div key={inv.id} className="p-4 flex items-center justify-between" data-testid={`invoice-${inv.id}`}>
                <div>
                  <span className="font-semibold text-sm text-grafite capitalize">{inv.type}</span>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {inv.due_date ? format(new Date(inv.due_date), 'dd/MM/yyyy', { locale: ptBR }) : '-'}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-sm text-grafite">{inv.amount} CVE</div>
                  <span className={`text-[10px] font-semibold uppercase ${inv.status === 'pago' ? 'text-green-600' : 'text-orange-500'}`}>
                    {inv.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
