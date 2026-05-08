import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { financesAPI } from '../../../utils/api';
import { useBodyScrollLock } from '../../../hooks/useBodyScrollLock';
import { toast } from 'sonner';
import { X } from 'lucide-react';
import { INCOME_CATEGORIES, EXPENSE_CATEGORIES } from './constants';

export const TransactionModal = ({ tx, onClose, onSaved }) => {
  useBodyScrollLock(true);
  const isEdit = !!tx;
  const [form, setForm] = useState({
    type: tx?.type || 'receita',
    category: tx?.category || 'quotas',
    description: tx?.description || '',
    amount: tx?.amount || '',
    date: tx?.date ? tx.date.split('T')[0] : new Date().toISOString().split('T')[0],
    reference: tx?.reference || '',
  });
  const [saving, setSaving] = useState(false);

  const categories = form.type === 'receita' ? INCOME_CATEGORIES : EXPENSE_CATEGORIES;

  useEffect(() => {
    if (!isEdit) {
      setForm((prev) => ({ ...prev, category: form.type === 'receita' ? 'quotas' : 'operacional' }));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.type]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.description || !form.amount || !form.date) {
      toast.error('Preencha todos os campos obrigatorios');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...form,
        amount: parseFloat(form.amount),
        date: new Date(form.date).toISOString(),
      };
      if (isEdit) {
        await financesAPI.updateTransaction(tx.id, payload);
        toast.success('Transacao atualizada');
      } else {
        await financesAPI.createTransaction(payload);
        toast.success('Transacao criada');
      }
      onSaved();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-black/40 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div className="flex min-h-full items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="rounded-xl shadow-2xl w-full max-w-md"
        style={{ backgroundColor: 'var(--surface-card)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-5" style={{ borderBottom: '1px solid var(--surface-border)' }}>
          <h2 className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>{isEdit ? 'Editar Transacao' : 'Nova Transacao'}</h2>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-gray-100 text-gray-400" aria-label="Fechar" data-testid="close-modal-btn"><X className="w-5 h-5" aria-hidden="true" /></button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Tipo</label>
            <div className="flex gap-2">
              {[{ val: 'receita', label: 'Receita', color: 'bg-green-600' }, { val: 'despesa', label: 'Despesa', color: 'bg-red-600' }].map((opt) => (
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
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
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
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
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
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
                data-testid="amount-input"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Data *</label>
              <input
                type="date"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
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
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
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
      </motion.div>
      </div>
    </div>
  );
};
