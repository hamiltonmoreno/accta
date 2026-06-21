import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { DollarSign, Plus, Trash2 } from 'lucide-react';
import { projectsAPI } from '../../../utils/api';
import { EmptyState } from '../../../components/EmptyState';

const EMPTY_EXPENSE = () => ({ description: '', amount: '', date: new Date().toISOString().split('T')[0], category: 'operacional' });

// Categorias de despesa (espelham backend EXPENSE_CATEGORIES). A despesa de
// projeto é uma transação no caixa e exige categoria (spec-fluxo-financeiro-unificado).
const EXPENSE_CATS = [
  ['operacional', 'Operacional'],
  ['eventos', 'Eventos'],
  ['juridico', 'Jurídico'],
  ['comunicacao', 'Comunicação'],
  ['viagens', 'Viagens'],
  ['outros_despesa', 'Outras Despesas'],
];
const CAT_LABEL = Object.fromEntries(EXPENSE_CATS);

export const BudgetTab = ({ project, expenses, canManage, onReload }) => {
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(EMPTY_EXPENSE());

  const spent = expenses.reduce((s, e) => s + e.amount, 0);
  const budget = project.budget || 0;
  const pct = budget > 0 ? Math.round((spent / budget) * 100) : 0;
  const remaining = budget - spent;

  const addMutation = useMutation({
    mutationFn: (data) => projectsAPI.addExpense(project.id, data),
    onSuccess: () => {
      setForm(EMPTY_EXPENSE());
      setShowAdd(false);
      onReload();
      toast.success('Despesa registada');
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro'),
  });

  const deleteMutation = useMutation({
    mutationFn: (expenseId) => projectsAPI.deleteExpense(project.id, expenseId),
    onSuccess: onReload,
    onError: () => toast.error('Erro'),
  });

  const saving = addMutation.isPending;

  const handleAdd = () => {
    if (!form.description.trim() || !form.amount) { toast.error('Preencha os campos'); return; }
    addMutation.mutate({ ...form, amount: parseFloat(form.amount), category: form.category || 'operacional' });
  };

  return (
    <div className="space-y-5">
      {/* Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-white border border-gray-200/80 rounded-xl p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Orcamento</div>
          <div className="font-mono text-xl font-bold text-grafite" data-testid="budget-total">{budget.toLocaleString('pt')} CVE</div>
        </div>
        <div className="bg-white border border-gray-200/80 rounded-xl p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Gasto</div>
          <div className="font-mono text-xl font-bold text-[#3A3A3A]" data-testid="budget-spent">{spent.toLocaleString('pt')} CVE</div>
          {budget > 0 && <div className="text-xs text-[#6B7280] mt-0.5">{pct}% do orcamento</div>}
        </div>
        <div className="bg-white border border-gray-200/80 rounded-xl p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Disponivel</div>
          <div className={`font-mono text-xl font-bold ${remaining >= 0 ? 'text-[#15803D]' : 'text-[#B91C1C]'}`} data-testid="budget-remaining">
            {remaining.toLocaleString('pt')} CVE
          </div>
        </div>
      </div>

      {/* Progress bar */}
      {budget > 0 && (
        <div className="bg-white border border-gray-200/80 rounded-xl p-4">
          <div className="flex justify-between text-xs text-gray-500 mb-1.5">
            <span>Execucao Orcamental</span>
            <span className="font-mono font-bold">{pct}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2.5">
            <div className={`h-2.5 rounded-full transition-all ${pct > 90 ? 'bg-[#C7202F]' : pct > 70 ? 'bg-[#D97706]' : 'bg-[#16A34A]'}`}
              style={{ width: `${Math.min(pct, 100)}%` }} />
          </div>
        </div>
      )}

      {/* Expenses list */}
      {canManage && (
        <div className="flex justify-end">
          <button onClick={() => setShowAdd(!showAdd)} className="btn-outline flex items-center gap-2 text-sm" data-testid="add-expense-btn">
            <Plus className="w-4 h-4" /> Despesa
          </button>
        </div>
      )}

      {showAdd && (
        <div className="bg-white border border-gray-200/80 rounded-xl p-4 flex flex-wrap items-end gap-2 animate-fade-up">
          <div className="flex-1 min-w-[180px]">
            <label className="text-xs text-[#6B7280] uppercase tracking-wider block mb-1">Descricao</label>
            <input type="text" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="expense-desc-input" />
          </div>
          <div className="w-28">
            <label className="text-xs text-[#6B7280] uppercase tracking-wider block mb-1">Valor (CVE)</label>
            <input type="number" inputMode="decimal" min="0" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="expense-amount-input" />
          </div>
          <div className="w-40">
            <label className="text-xs text-[#6B7280] uppercase tracking-wider block mb-1">Categoria</label>
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="expense-category-input">
              {EXPENSE_CATS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
          <div className="w-36">
            <label className="text-xs text-[#6B7280] uppercase tracking-wider block mb-1">Data</label>
            <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none" />
          </div>
          <button onClick={handleAdd} disabled={saving} className="btn-primary text-sm px-5" data-testid="save-expense-btn">
            {saving ? '...' : 'Adicionar'}
          </button>
        </div>
      )}

      {expenses.length === 0 ? (
        <EmptyState icon={DollarSign} title="Nenhuma despesa registada" className="p-6 sm:p-8" testId="no-expenses" />
      ) : (
        <div className="bg-white border border-gray-200/80 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50/80 text-[#6B7280] uppercase text-xs tracking-wider">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Descricao</th>
                <th className="px-4 py-3 text-left font-semibold">Categoria</th>
                <th className="px-4 py-3 text-right font-semibold">Valor</th>
                <th className="px-4 py-3 text-left font-semibold">Data</th>
                {canManage && <th className="px-4 py-3 w-10"></th>}
              </tr>
            </thead>
            <tbody>
              {expenses.map(e => (
                <tr key={e.id} className="border-t border-gray-50" data-testid={`expense-${e.id}`}>
                  <td className="px-4 py-3 text-grafite">{e.description}{e.ato_id && <span className="ml-1.5 text-[10px] text-[#6B7280] uppercase">(co-aprovado)</span>}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{CAT_LABEL[e.category] || e.category || '—'}</td>
                  <td className="px-4 py-3 text-right font-mono font-bold text-[#3A3A3A]">{e.amount.toLocaleString('pt')} CVE</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{(e.date || '').slice(0, 10)}</td>
                  {canManage && (
                    <td className="px-4 py-3"><button onClick={() => deleteMutation.mutate(e.id)} className="p-1 text-gray-400 hover:text-[#B91C1C]" aria-label="Apagar despesa"><Trash2 className="w-3.5 h-3.5" aria-hidden="true" /></button></td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
