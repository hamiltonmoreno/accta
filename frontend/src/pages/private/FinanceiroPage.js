import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { invoicesAPI } from '../../utils/api';
import { DollarSign, CheckCircle, Clock, XCircle, Filter } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { useAuth } from '../../contexts/AuthContext';

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

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pago':
        return <CheckCircle className="w-5 h-5 text-carmesim" />;
      case 'pendente':
        return <Clock className="w-5 h-5 text-alert" />;
      case 'cancelado':
        return <XCircle className="w-5 h-5 text-gray-400" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pago':
        return 'bg-carmesim/10 text-carmesim';
      case 'pendente':
        return 'bg-alert/10 text-alert';
      case 'cancelado':
        return 'bg-gray-100 text-gray-500';
      default:
        return 'bg-gray-100 text-gray-500';
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-sans font-bold text-4xl text-grafite mb-2" data-testid="finance-title">
          Gestão Financeira
        </h1>
        <p className="text-gray-600">Acompanhe suas quotas e pagamentos</p>
      </div>

      {/* Info Banner */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-technical rounded-xl p-6 bg-carmesim/5 border-accent/20"
      >
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-carmesim rounded-lg flex items-center justify-center flex-shrink-0">
            <CheckCircle className="w-6 h-6 text-grafite" />
          </div>
          <div>
            <h3 className="font-sans font-semibold text-lg text-grafite mb-2">Pagamento Automático por Folha Salarial</h3>
            <p className="text-gray-600 leading-relaxed">
              As quotas mensais são descontadas automaticamente em folha de pagamento quando você se torna associado. 
              Esta página mostra o histórico dos descontos realizados e sua situação financeira perante a associação.
            </p>
          </div>
        </div>
      </motion.div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card-technical rounded-xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-grafite rounded-lg flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-carmesim" />
            </div>
          </div>
          <div className="font-mono text-3xl font-bold text-grafite mb-1">{invoices.length}</div>
          <div className="text-sm text-gray-500 uppercase tracking-wider">Total de Registros</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card-technical rounded-xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-alert rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-white" />
            </div>
          </div>
          <div className="font-mono text-3xl font-bold text-alert mb-1">{totalPendente.toFixed(0)} CVE</div>
          <div className="text-sm text-gray-500 uppercase tracking-wider">Pendente</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card-technical rounded-xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-carmesim rounded-lg flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-grafite" />
            </div>
          </div>
          <div className="font-mono text-3xl font-bold text-carmesim mb-1">{totalPago.toFixed(0)} CVE</div>
          <div className="text-sm text-gray-500 uppercase tracking-wider">Pago</div>
        </motion.div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => setFilter('all')}
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all ${
            filter === 'all' ? 'bg-grafite text-white' : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
          data-testid="filter-all"
        >
          <Filter className="w-4 h-4" />
          Todos
        </button>
        <button
          onClick={() => setFilter('pendente')}
          className={`px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all ${
            filter === 'pendente' ? 'bg-alert text-white' : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
          data-testid="filter-pending"
        >
          Pendentes
        </button>
        <button
          onClick={() => setFilter('pago')}
          className={`px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all ${
            filter === 'pago' ? 'bg-carmesim text-grafite' : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
          data-testid="filter-paid"
        >
          Pagos
        </button>
        <button
          onClick={() => setFilter('cancelado')}
          className={`px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all ${
            filter === 'cancelado' ? 'bg-gray-400 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
          data-testid="filter-cancelled"
        >
          Cancelados
        </button>
      </div>

      {/* Invoices Table */}
      <div className="card-technical rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filteredInvoices.length === 0 ? (
          <div className="p-12 text-center" data-testid="no-invoices">
            <p className="text-gray-500">Nenhum registro encontrado</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50 text-gray-500 uppercase font-mono text-xs">
                <tr>
                  <th className="px-6 py-4">Tipo</th>
                  <th className="px-6 py-4">Valor</th>
                  <th className="px-6 py-4">Vencimento</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Origem</th>
                </tr>
              </thead>
              <tbody>
                {filteredInvoices.map((invoice, index) => (
                  <tr
                    key={invoice.id}
                    className="border-t border-gray-100 hover:bg-gray-50 transition-colors"
                    data-testid={`invoice-row-${invoice.id}`}
                  >
                    <td className="px-6 py-4 font-sans font-semibold text-grafite">{invoice.type}</td>
                    <td className="px-6 py-4 font-mono font-bold text-grafite">{invoice.amount} CVE</td>
                    <td className="px-6 py-4 font-mono text-gray-600">
                      {format(new Date(invoice.due_date), 'dd/MM/yyyy', { locale: ptBR })}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono uppercase tracking-wide ${getStatusColor(
                          invoice.status
                        )}`}
                      >
                        {getStatusIcon(invoice.status)}
                        {invoice.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-gray-500">{invoice.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
