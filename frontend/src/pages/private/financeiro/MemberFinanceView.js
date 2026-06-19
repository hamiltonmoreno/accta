import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { financesAPI } from '../../../utils/api';
import { queryKeys } from '../../../lib/queryClient';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { DollarSign, TrendingUp } from 'lucide-react';
import { CATEGORY_LABELS } from './constants';
import { EmptyState } from '../../../components/EmptyState';
import { Skeleton } from '../../../components/ui/skeleton';

const StatBlock = ({ label, value, icon: Icon, color }) => (
  <div className="card-technical p-4 sm:p-5 animate-fade-up">
    <div className={`w-9 h-9 sm:w-10 sm:h-10 ${color} rounded-lg flex items-center justify-center mb-2 sm:mb-3`}>
      <Icon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
    </div>
    <div className="font-mono text-lg sm:text-2xl font-bold text-grafite-auto">{value}</div>
    <div className="text-xs uppercase tracking-wider mt-0.5 text-muted-auto">{label}</div>
  </div>
);

export const MemberFinanceView = () => {
  // Quotas/jóias do próprio sócio, lidas de `transactions` (filtro por user_id no
  // backend). Não há estado pendente/pago — são lançamentos efetivos (folha).
  const { data, isLoading: loading } = useQuery({
    queryKey: queryKeys.myQuotas.list(),
    queryFn: async () => (await financesAPI.getMyQuotas()).data,
  });

  const items = data?.items || [];
  const totalPago = data?.total_pago || 0;

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
            <h3 className="font-semibold text-sm mb-1 text-grafite-auto">Pagamento Automatico</h3>
            <p className="text-xs sm:text-sm text-secondary-auto">As quotas mensais sao descontadas automaticamente em folha de pagamento.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:gap-4">
        <StatBlock label="Registos" value={items.length} icon={DollarSign} color="bg-grafite" />
        <StatBlock label="Total Pago" value={`${totalPago.toLocaleString('pt')} CVE`} icon={TrendingUp} color="bg-[#16A34A]" />
      </div>

      {loading ? (
        <div className="card-technical overflow-hidden divide-y divide-gray-50" data-testid="quotas-loading">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="p-4 flex items-center justify-between">
              <div className="space-y-2">
                <Skeleton className="h-3.5 w-24" />
                <Skeleton className="h-3 w-20" />
              </div>
              <Skeleton className="h-3.5 w-20" />
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <EmptyState icon={DollarSign} title="Nenhum registo encontrado" testId="no-quotas" />
      ) : (
        <div className="card-technical overflow-hidden">
          <div className="divide-y divide-gray-50">
            {items.map((tx) => (
              <div key={tx.id} className="p-4 flex items-center justify-between" data-testid={`quota-${tx.id}`}>
                <div>
                  <span className="font-semibold text-sm text-grafite-auto">
                    {CATEGORY_LABELS[tx.category] || tx.description || tx.category}
                  </span>
                  <div className="text-xs mt-0.5 text-muted-auto">
                    {tx.date ? format(new Date(tx.date), 'dd/MM/yyyy', { locale: ptBR }) : '-'}
                    {tx.reference ? ` · ${tx.reference}` : ''}
                  </div>
                </div>
                <div className="font-mono font-bold text-sm text-grafite-auto">
                  {(tx.amount || 0).toLocaleString('pt')} CVE
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
