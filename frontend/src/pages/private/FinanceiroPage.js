import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { DollarSign, FileBarChart, Settings, CalendarClock, ClipboardList } from 'lucide-react';
import { CashFlowTab } from './financeiro/CashFlowTab';
import { DRETab } from './financeiro/DRETab';
import { SettingsTab } from './financeiro/SettingsTab';
import { MemberFinanceView } from './financeiro/MemberFinanceView';
import { PrestacaoContasTab } from './financeiro/PrestacaoContasTab';
import { BalancetesTab } from './financeiro/BalancetesTab';

const TabBtn = ({ active, label, icon: Icon, onClick, testId }) => (
  <button
    onClick={onClick}
    data-testid={testId}
    className={`flex items-center gap-2 px-4 py-2.5 text-sm font-semibold rounded-lg transition-all whitespace-nowrap ${
      active ? 'bg-carmesim text-white shadow-sm' : 'text-muted-auto'
    }`}
  >
    <Icon className="w-4 h-4" />
    {label}
  </button>
);

export const FinanceiroPage = () => {
  const { isAdmin, canViewFinances, canManageFinances } = useAuth();
  const [activeTab, setActiveTab] = useState('cashflow');

  // Quem não pode ver finanças (sócio comum) cai na vista pessoal.
  if (!canViewFinances) {
    return <MemberFinanceView />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title" data-testid="finance-title">Gestão Financeira</h1>
        <p className="page-subtitle">
          Fluxo de caixa, relatórios DRE e configurações
          {!canManageFinances && (
            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-[#F5F5F5] text-[#6B7280]" data-testid="finance-readonly-badge">
              Modo leitura
            </span>
          )}
        </p>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
        <TabBtn active={activeTab === 'cashflow'} label="Fluxo de Caixa" icon={DollarSign} onClick={() => setActiveTab('cashflow')} testId="tab-cashflow" />
        <TabBtn active={activeTab === 'dre'} label="Relatorio DRE" icon={FileBarChart} onClick={() => setActiveTab('dre')} testId="tab-dre" />
        <TabBtn active={activeTab === 'prestacao'} label="Prestacao de Contas" icon={CalendarClock} onClick={() => setActiveTab('prestacao')} testId="tab-prestacao" />
        <TabBtn active={activeTab === 'balancetes'} label="Balancetes" icon={ClipboardList} onClick={() => setActiveTab('balancetes')} testId="tab-balancetes" />
        {isAdmin && (
          <TabBtn active={activeTab === 'settings'} label="Configuracoes" icon={Settings} onClick={() => setActiveTab('settings')} testId="tab-settings" />
        )}
      </div>

      {activeTab === 'cashflow' && <CashFlowTab canManage={canManageFinances} />}
      {activeTab === 'dre' && <DRETab />}
      {activeTab === 'prestacao' && <PrestacaoContasTab />}
      {activeTab === 'balancetes' && <BalancetesTab />}
      {activeTab === 'settings' && isAdmin && <SettingsTab />}
    </div>
  );
};
