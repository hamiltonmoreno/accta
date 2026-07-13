import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Wallet, ArrowRight, TrendingDown, TrendingUp } from 'lucide-react';

// Banner do saldo anual. Spec 020: conteúdo é universal (todos os sócios
// vêem os totais agregados); afordância de clique só existe se `clickable`
// (drill-down para /financeiro exige privilégio).
export const FinanceSummary = ({ financeSummary, currentYear, clickable = true }) => {
  const navigate = useNavigate();
  const goTo = () => navigate('/financeiro');
  const clickProps = clickable
    ? {
        onClick: goTo,
        role: 'button',
        tabIndex: 0,
        onKeyDown: (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); goTo(); } },
        'aria-label': `Ver Financeiro ${currentYear}`,
      }
    : {};
  const cursor = clickable ? 'cursor-pointer' : '';
  return (
    <div className={`bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6 ${cursor} hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all animate-fade-up outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2`}
      {...clickProps}
      data-testid="finance-summary-widget">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-grafite flex items-center gap-2">
          <Wallet className="w-5 h-5 text-grafite" /> Saldo Financeiro {currentYear}
        </h3>
        {clickable && <ArrowRight className="w-4 h-4 text-gray-400" />}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6">
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-medium">Receitas</div>
          <div className="font-mono text-xl sm:text-2xl font-bold text-[#15803D]">{financeSummary.total_receitas.toLocaleString('pt')}</div>
          <div className="text-xs text-[#6B7280] mt-0.5">CVE</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-medium">Despesas</div>
          <div className="font-mono text-xl sm:text-2xl font-bold text-[#B91C1C]">{financeSummary.total_despesas.toLocaleString('pt')}</div>
          <div className="text-xs text-[#6B7280] mt-0.5">CVE</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-medium">Resultado</div>
          <div className={`font-mono text-xl sm:text-2xl font-bold flex items-center gap-1.5 ${financeSummary.resultado_liquido >= 0 ? 'text-grafite' : 'text-[#B91C1C]'}`}>
            {financeSummary.resultado_liquido >= 0
              ? <TrendingUp className="w-4 h-4 shrink-0" aria-hidden="true" />
              : <TrendingDown className="w-4 h-4 shrink-0" aria-hidden="true" />}
            {financeSummary.resultado_liquido.toLocaleString('pt')}
          </div>
          <div className="text-xs text-[#6B7280] mt-0.5">CVE</div>
        </div>
      </div>
    </div>
  );
};
