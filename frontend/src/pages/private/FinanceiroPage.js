import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { DollarSign, FileBarChart, Settings } from 'lucide-react';
import { CashFlowTab } from './financeiro/CashFlowTab';
import { DRETab } from './financeiro/DRETab';
import { SettingsTab } from './financeiro/SettingsTab';
import { MemberFinanceView } from './financeiro/MemberFinanceView';

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
  const { isAdmin, isFinanceiro } = useAuth();
  const hasFinanceAccess = isAdmin || isFinanceiro;
  const [activeTab, setActiveTab] = useState('cashflow');

  if (!hasFinanceAccess) {
    return <MemberFinanceView />;
  }

  return (
    <div className="space-y-6">
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
