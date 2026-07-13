import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Coins, ArrowRight } from 'lucide-react';

// Tile compacta "Quotas do mês em curso" (spec 020 — B.11). Universal: valor
// agregado, sem PII. Drill-down para /financeiro/quotas só a quem tem
// privilégio (props.clickable).
export const QuotasMes = ({ valor, clickable = false }) => {
  const navigate = useNavigate();
  const goTo = () => navigate('/financeiro/quotas');
  const props = clickable
    ? {
        onClick: goTo,
        role: 'button',
        tabIndex: 0,
        onKeyDown: (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); goTo(); } },
        'aria-label': 'Ver quotas',
      }
    : {};
  const cursor = clickable ? 'cursor-pointer' : '';
  const nowLabel = new Date().toLocaleDateString('pt-PT', { month: 'long', year: 'numeric' });
  return (
    <div
      className={`bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6 ${cursor} hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all animate-fade-up outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2`}
      {...props}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="w-10 h-10 bg-[#FFFBEB] rounded-xl flex items-center justify-center">
          <Coins className="w-5 h-5 text-[#D97706]" />
        </div>
        {clickable && <ArrowRight className="w-4 h-4 text-gray-400" />}
      </div>
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-medium">Quotas do mês</div>
      <div className="font-mono text-2xl sm:text-3xl font-bold text-grafite">
        {(valor ?? 0).toLocaleString('pt')}
      </div>
      <div className="text-xs text-[#6B7280] mt-0.5">CVE · {nowLabel}</div>
    </div>
  );
};

export default QuotasMes;
