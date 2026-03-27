import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { invoicesAPI } from '../../utils/api';
import { DollarSign, CheckCircle, Clock, XCircle, Filter } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { useAuth } from '../../contexts/AuthContext';

const StatusBadge = ({ status }) => {
  const config = {
    pago: { icon: CheckCircle, color: 'bg-green-50 text-green-700 border-green-200', label: 'Pago' },
    pendente: { icon: Clock, color: 'bg-orange-50 text-orange-700 border-orange-200', label: 'Pendente' },
    cancelado: { icon: XCircle, color: 'bg-gray-50 text-gray-500 border-gray-200', label: 'Cancelado' },
  };
  const { icon: Icon, color, label } = config[status] || config.cancelado;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold uppercase tracking-wider border ${color}`}>
      <Icon className="w-3 h-3" />
      {label}
    </span>
  );
};

export const FinanceiroPage = () => {
  const { isAdmin, isFinanceiro } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    try {
      const response = await invoicesAPI.getAll();
      setInvoices(response.data);
    } catch (error) {
      console.error('Erro ao carregar invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredInvoices = filter === 'all' ? invoices : invoices.filter((inv) => inv.status === filter);
  const totalPendente = invoices.filter((inv) => inv.status === 'pendente').reduce((sum, inv) => sum + inv.amount, 0);
  const totalPago = invoices.filter((inv) => inv.status === 'pago').reduce((sum, inv) => sum + inv.amount, 0);

  const filters = [
    { key: 'all', label: 'Todos', activeClass: 'bg-grafite text-white' },
    { key: 'pendente', label: 'Pendentes', activeClass: 'bg-orange-500 text-white' },
    { key: 'pago', label: 'Pagos', activeClass: 'bg-green-600 text-white' },
    { key: 'cancelado', label: 'Cancelados', activeClass: 'bg-gray-400 text-white' },
  ];

  return (
    <div className="space-y-5 sm:space-y-6">
      {/* Header */}
      <div>
        <h1 className="page-title" data-testid="finance-title">Gestão Financeira</h1>
        <p className="page-subtitle">Acompanhe suas quotas e pagamentos</p>
      </div>

      {/* Info Banner */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-technical p-4 sm:p-5 border-l-4 border-l-carmesim bg-carmesim/5"
      >
        <div className="flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-carmesim flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-sm text-grafite mb-1">Pagamento Automatico</h3>
            <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">
              As quotas mensais sao descontadas automaticamente em folha de pagamento.
            </p>
          </div>
        </div>
      </motion.div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-3 sm:gap-4">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="card-technical p-3 sm:p-5">
          <div className="w-9 h-9 sm:w-10 sm:h-10 bg-grafite rounded-lg flex items-center justify-center mb-2 sm:mb-3">
            <DollarSign className="w-4 h-4 sm:w-5 sm:h-5 text-carmesim" />
          </div>
          <div className="font-mono text-lg sm:text-2xl font-bold text-grafite">{invoices.length}</div>
          <div className="text-[9px] sm:text-xs text-gray-500 uppercase tracking-wider">Registros</div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card-technical p-3 sm:p-5">
          <div className="w-9 h-9 sm:w-10 sm:h-10 bg-orange-500 rounded-lg flex items-center justify-center mb-2 sm:mb-3">
            <Clock className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
          </div>
          <div className="font-mono text-lg sm:text-2xl font-bold text-orange-600">{totalPendente.toFixed(0)}</div>
          <div className="text-[9px] sm:text-xs text-gray-500 uppercase tracking-wider">Pendente CVE</div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="card-technical p-3 sm:p-5">
          <div className="w-9 h-9 sm:w-10 sm:h-10 bg-green-600 rounded-lg flex items-center justify-center mb-2 sm:mb-3">
            <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
          </div>
          <div className="font-mono text-lg sm:text-2xl font-bold text-green-600">{totalPago.toFixed(0)}</div>
          <div className="text-[9px] sm:text-xs text-gray-500 uppercase tracking-wider">Pago CVE</div>
        </motion.div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
        {filters.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap touch-target ${
              filter === f.key ? f.activeClass : 'bg-white text-gray-500 hover:bg-gray-50 border border-gray-100'
            }`}
            data-testid={`filter-${f.key}`}
          >
            {f.key === 'all' && <Filter className="w-3.5 h-3.5" />}
            {f.label}
          </button>
        ))}
      </div>

      {/* Invoice List */}
      <div className="card-technical overflow-hidden">
        {loading ? (
          <div className="p-10 text-center">
            <div className="inline-block w-7 h-7 border-3 border-carmesim border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filteredInvoices.length === 0 ? (
          <div className="p-10 text-center" data-testid="no-invoices">
            <DollarSign className="w-10 h-10 text-gray-200 mx-auto mb-2" />
            <p className="text-sm text-gray-400">Nenhum registro encontrado</p>
          </div>
        ) : (
          <>
            {/* Desktop Table */}
            <div className="hidden sm:block overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50/80 text-gray-400 uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="px-5 py-3 font-semibold">Tipo</th>
                    <th className="px-5 py-3 font-semibold">Valor</th>
                    <th className="px-5 py-3 font-semibold">Vencimento</th>
                    <th className="px-5 py-3 font-semibold">Status</th>
                    <th className="px-5 py-3 font-semibold">Origem</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredInvoices.map((invoice) => (
                    <tr
                      key={invoice.id}
                      className="border-t border-gray-50 hover:bg-gray-50/50 transition-colors"
                      data-testid={`invoice-row-${invoice.id}`}
                    >
                      <td className="px-5 py-3.5 font-semibold text-grafite capitalize">{invoice.type}</td>
                      <td className="px-5 py-3.5 font-mono font-bold text-grafite">{invoice.amount} CVE</td>
                      <td className="px-5 py-3.5 font-mono text-gray-500 text-xs">
                        {format(new Date(invoice.due_date), 'dd/MM/yyyy', { locale: ptBR })}
                      </td>
                      <td className="px-5 py-3.5">
                        <StatusBadge status={invoice.status} />
                      </td>
                      <td className="px-5 py-3.5 text-xs text-gray-400 capitalize">{invoice.source?.replace('_', ' ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Card View */}
            <div className="sm:hidden divide-y divide-gray-50">
              {filteredInvoices.map((invoice) => (
                <div key={invoice.id} className="p-4" data-testid={`invoice-card-${invoice.id}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm text-grafite capitalize">{invoice.type}</span>
                    <span className="font-mono font-bold text-sm text-grafite">{invoice.amount} CVE</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <Clock className="w-3 h-3" />
                      <span>{format(new Date(invoice.due_date), 'dd/MM/yyyy', { locale: ptBR })}</span>
                      <span className="text-gray-300">|</span>
                      <span className="capitalize">{invoice.source?.replace('_', ' ')}</span>
                    </div>
                    <StatusBadge status={invoice.status} />
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
