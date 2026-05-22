import React, { useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { financesAPI } from '../../../utils/api';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../../components/ui/dialog';
import { INCOME_CATEGORIES, EXPENSE_CATEGORIES } from './constants';

export const TransactionModal = ({ tx, onClose, onSaved }) => {
  const isEdit = !!tx;
  const [form, setForm] = useState({
    type: tx?.type || 'receita',
    category: tx?.category || 'quotas',
    description: tx?.description || '',
    amount: tx?.amount || '',
    date: tx?.date ? tx.date.split('T')[0] : new Date().toISOString().split('T')[0],
    reference: tx?.reference || '',
  });

  const categories = form.type === 'receita' ? INCOME_CATEGORIES : EXPENSE_CATEGORIES;

  useEffect(() => {
    if (!isEdit) {
      setForm((prev) => ({ ...prev, category: form.type === 'receita' ? 'quotas' : 'operacional' }));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.type]);

  const saveMutation = useMutation({
    mutationFn: (payload) =>
      isEdit
        ? financesAPI.updateTransaction(tx.id, payload)
        : financesAPI.createTransaction(payload),
    onSuccess: () => {
      toast.success(isEdit ? 'Transacao atualizada' : 'Transacao criada');
      // onSaved: parent invalida ['transactions']. onClose: o modal fecha-se a
      // si proprio, sem depender do parent para o fechar.
      onSaved();
      onClose();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao salvar'),
  });

  const saving = saveMutation.isPending;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.description || !form.amount || !form.date) {
      toast.error('Preencha todos os campos obrigatorios');
      return;
    }
    saveMutation.mutate({
      ...form,
      amount: parseFloat(form.amount),
      date: new Date(form.date).toISOString(),
    });
  };

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-md rounded-xl p-0 gap-0 max-h-[90vh] overflow-y-auto" data-testid="transaction-modal">
        <DialogHeader className="p-5 border-b border-gray-200 text-left space-y-0">
          <DialogTitle className="font-bold text-lg text-grafite">{isEdit ? 'Editar Transacao' : 'Nova Transacao'}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Tipo</label>
            <div className="flex gap-2">
              {[{ val: 'receita', label: 'Receita', color: 'bg-[#16A34A]' }, { val: 'despesa', label: 'Despesa', color: 'bg-[#C7202F]' }].map((opt) => (
                <button
                  key={opt.val}
                  type="button"
                  onClick={() => setForm({ ...form, type: opt.val })}
                  data-testid={`type-${opt.val}`}
                  className={`flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                    form.type === opt.val ? `${opt.color} text-white` : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Categoria</label>
            <select
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="category-select"
            >
              {categories.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Descricao *</label>
            <input
              type="text"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Ex: Quota mensal Janeiro 2026"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="description-input"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Valor (CVE) *</label>
              <input
                type="number"
                inputMode="decimal"
                min="0"
                step="0.01"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                placeholder="2000"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm font-mono focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                data-testid="amount-input"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Data *</label>
              <input
                type="date"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                data-testid="date-input"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Referencia</label>
            <input
              type="text"
              value={form.reference}
              onChange={(e) => setForm({ ...form, reference: e.target.value })}
              placeholder="Ex: FOLHA-202601"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="reference-input"
            />
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full btn-primary py-3 text-sm font-semibold"
            data-testid="save-transaction-btn"
          >
            {saving ? 'A guardar...' : isEdit ? 'Atualizar' : 'Criar Transacao'}
          </button>
        </form>
      </DialogContent>
    </Dialog>
  );
};
