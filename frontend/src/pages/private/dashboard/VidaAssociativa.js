import React from 'react';
import { useNavigate } from 'react-router-dom';
import { UserPlus, Users, FileCheck, Vote, ArrowRight } from 'lucide-react';

// KPIs de vida associativa (spec 020 — grupo A). Universal: mesmos números
// para todos os sócios. Drill-down gated por widget (Atos → só para quem
// pode ver Co-Aprovações; contagem sem detalhes é neutra).
const Tile = ({ icon: Icon, iconBg, iconColor, label, value, sublabel, onClick }) => {
  const isButton = !!onClick;
  const props = isButton
    ? {
        onClick,
        role: 'button',
        tabIndex: 0,
        onKeyDown: (e) => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); }
        },
        'aria-label': `Ver ${label}`,
      }
    : {};
  const cursor = isButton ? 'cursor-pointer' : '';
  return (
    <div
      className={`bg-white border border-gray-200/80 rounded-2xl p-4 sm:p-5 ${cursor} hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2`}
      {...props}
    >
      <div className="flex items-center justify-between mb-2">
        <div className={`w-9 h-9 ${iconBg} rounded-xl flex items-center justify-center`}>
          <Icon className={`w-4 h-4 ${iconColor}`} />
        </div>
        {isButton && <ArrowRight className="w-4 h-4 text-gray-400" />}
      </div>
      <div className="font-bold text-2xl sm:text-3xl text-grafite tracking-tight">{value}</div>
      <div className="text-xs sm:text-sm text-[#6B7280] font-medium mt-0.5">{label}</div>
      {sublabel && <div className="text-xs text-[#6B7280] mt-0.5">{sublabel}</div>}
    </div>
  );
};

export const VidaAssociativa = ({ socios, atos, votacoes, canViewAtos = false }) => {
  const navigate = useNavigate();
  const ultima = votacoes?.ultima_fechada;
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl p-4 sm:p-5 animate-fade-up">
      <h3 className="text-lg font-semibold text-grafite mb-4">Vida Associativa</h3>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Tile
          icon={Users}
          iconBg="bg-grafite/10"
          iconColor="text-grafite"
          label="Sócios activos"
          value={socios?.ativos ?? '—'}
        />
        <Tile
          icon={UserPlus}
          iconBg="bg-[#F0FDF4]"
          iconColor="text-[#15803D]"
          label="Novos"
          sublabel="últimos 90 dias"
          value={socios?.novos_90d ?? '—'}
        />
        <Tile
          icon={FileCheck}
          iconBg="bg-[#EFF6FF]"
          iconColor="text-[#1D4ED8]"
          label="Actos pendentes"
          value={atos?.pendentes ?? '—'}
          onClick={canViewAtos && atos?.pendentes ? () => navigate('/atos') : undefined}
        />
        <Tile
          icon={Vote}
          iconBg="bg-carmesim/10"
          iconColor="text-carmesim"
          label="Participação"
          sublabel={ultima ? `última: ${ultima.titulo}` : 'sem votações fechadas'}
          value={ultima ? `${ultima.participacao_pct}%` : '—'}
        />
      </div>
    </div>
  );
};

export default VidaAssociativa;
