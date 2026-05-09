import React, { useEffect, useState } from 'react';
import { invoicesAPI } from '../../../utils/api';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { DollarSign, TrendingUp } from 'lucide-react';

const StatBlock = ({ label, value, icon: Icon, color }) => (
  <div className="card-technical p-4 sm:p-5 animate-fade-up">
    <div className={`w-9 h-9 sm:w-10 sm:h-10 ${color} rounded-lg flex items-center justify-center mb-2 sm:mb-3`}>
      <Icon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
    </div>
    <div className="font-mono text-lg sm:text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{value}</div>
    <div className="text-xs uppercase tracking-wider mt-0.5" style={{ color: 'var(--text-muted)' }}>{label}</div>
  </div>
);

export const MemberFinanceView = () => {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await invoicesAPI.getAll();
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

      <div className="card-technical p-4 sm:p-5 border-l-4 border-l-carmesim bg-carmesim/5 animate-fade-in">
        <div className="flex items-start gap-3">
          <DollarSign className="w-5 h-5 text-carmesim flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-sm mb-1" style={{ color: 'var(--text-primary)' }}>Pagamento Automatico</h3>
            <p className="text-xs sm:text-sm" style={{ color: 'var(--text-secondary)' }}>As quotas mensais sao descontadas automaticamente em folha de pagamento.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:gap-4">
        <StatBlock label="Registros" value={invoices.length} icon={DollarSign} color="bg-grafite" />
        <StatBlock label="Total Pago" value={`${totalPago.toLocaleString('pt')} CVE`} icon={TrendingUp} color="bg-green-600" />
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
                  <span className="font-semibold text-sm capitalize" style={{ color: 'var(--text-primary)' }}>{inv.type}</span>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                    {inv.due_date ? format(new Date(inv.due_date), 'dd/MM/yyyy', { locale: ptBR }) : '-'}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-sm" style={{ color: 'var(--text-primary)' }}>{inv.amount} CVE</div>
                  <span className={`text-xs font-semibold uppercase ${inv.status === 'pago' ? 'text-green-600' : 'text-orange-500'}`}>
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
