import React from 'react';
import {
  Activity, ArrowDownRight, ArrowUpRight, Bell, Calendar, CheckCircle, DollarSign, Vote,
} from 'lucide-react';
import { ACTIVITY_ICONS, ACTIVITY_COLORS } from './tokens';

// Cartão de KPI tipo "Reference style": título topo, valor grande, indicador de variação.
export const StatCard = ({ title, value, icon: Icon, iconBg, change, changeLabel }) => (
  <div className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6 hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] hover:-translate-y-0.5 transition-all duration-200 animate-fade-up">
    <div className="flex items-center justify-between mb-3">
      <span className="text-sm text-gray-500 font-medium">{title}</span>
      <div className={`w-10 h-10 ${iconBg} rounded-xl flex items-center justify-center`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
    <div className="font-bold text-3xl sm:text-4xl text-grafite mb-1 font-sans tracking-tight">{value}</div>
    {change !== undefined && (
      <div className={`flex items-center gap-1 text-sm ${change >= 0 ? 'text-[#15803D]' : 'text-[#B91C1C]'}`}>
        {change >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
        <span className="font-semibold">{change >= 0 ? '+' : ''}{change}%</span>
        {changeLabel && <span className="text-[#6B7280] font-normal ml-0.5">{changeLabel}</span>}
      </div>
    )}
  </div>
);

// Pequeno avatar de tipo de notificação (cor + ícone).
export const NotifIcon = ({ type }) => {
  const config = {
    poll_opened: { icon: Vote, color: 'text-carmesim', bg: 'bg-carmesim/10' },
    invoice_due: { icon: DollarSign, color: 'text-[#B45309]', bg: 'bg-[#FFFBEB]' },
    event_new: { icon: Calendar, color: 'text-[#1D4ED8]', bg: 'bg-[#EFF6FF]' },
    wall_post_approved: { icon: CheckCircle, color: 'text-[#15803D]', bg: 'bg-[#F0FDF4]' },
    wall_comment: { icon: Bell, color: 'text-[#3A3A3A]', bg: 'bg-[#F5F5F5]' },
  };
  const c = config[type] || { icon: Bell, color: 'text-[#3A3A3A]', bg: 'bg-[#F5F5F5]' };
  const IconComp = c.icon;
  return (
    <div className={`w-9 h-9 ${c.bg} rounded-xl flex items-center justify-center flex-shrink-0`}>
      <IconComp className={`w-4 h-4 ${c.color}`} />
    </div>
  );
};

// Pequeno avatar de tipo de atividade (cor + ícone).
export const ActivityIcon = ({ type }) => {
  const Icon = ACTIVITY_ICONS[type] || Activity;
  const colors = ACTIVITY_COLORS[type] || { bg: 'bg-[#F5F5F5]', text: 'text-[#3A3A3A]' };
  return (
    <div className={`w-9 h-9 ${colors.bg} rounded-xl flex items-center justify-center flex-shrink-0`}>
      <Icon className={`w-4 h-4 ${colors.text}`} />
    </div>
  );
};
