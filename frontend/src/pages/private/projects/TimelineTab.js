import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { CheckCircle, Plus, Target, Trash2 } from 'lucide-react';
import { projectsAPI } from '../../../utils/api';
import { EmptyState } from '../../../components/EmptyState';

const EMPTY_MILESTONE = { title: '', date: '' };

export const TimelineTab = ({ project, milestones, canManage, onReload }) => {
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(EMPTY_MILESTONE);

  const addMutation = useMutation({
    mutationFn: (data) => projectsAPI.addMilestone(project.id, data),
    onSuccess: () => {
      setForm(EMPTY_MILESTONE);
      setShowAdd(false);
      onReload();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro'),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, completed }) => projectsAPI.updateMilestone(project.id, id, { completed }),
    onSuccess: onReload,
    onError: () => toast.error('Erro'),
  });

  const deleteMutation = useMutation({
    mutationFn: (milestoneId) => projectsAPI.deleteMilestone(project.id, milestoneId),
    onSuccess: onReload,
    onError: () => toast.error('Erro'),
  });

  const saving = addMutation.isPending;

  const handleAdd = () => {
    if (!form.title.trim() || !form.date) { toast.error('Preencha titulo e data'); return; }
    addMutation.mutate(form);
  };

  return (
    <div className="space-y-4">
      {canManage && (
        <div className="flex justify-end">
          <button onClick={() => setShowAdd(!showAdd)} className="btn-outline flex items-center gap-2 text-sm" data-testid="add-milestone-btn">
            <Plus className="w-4 h-4" /> Milestone
          </button>
        </div>
      )}

      {showAdd && (
        <div className="bg-white border border-gray-200/80 rounded-xl p-4 flex flex-wrap items-end gap-2 animate-fade-up">
          <div className="flex-1 min-w-[180px]">
            <label className="text-xs text-[#6B7280] uppercase tracking-wider block mb-1">Titulo</label>
            <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Ex: Reservar local do evento"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="milestone-title-input" />
          </div>
          <div className="w-40">
            <label className="text-xs text-[#6B7280] uppercase tracking-wider block mb-1">Data</label>
            <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="milestone-date-input" />
          </div>
          <button onClick={handleAdd} disabled={saving} className="btn-primary text-sm px-5" data-testid="save-milestone-btn">
            {saving ? '...' : 'Adicionar'}
          </button>
        </div>
      )}

      {milestones.length === 0 ? (
        <EmptyState icon={Target} title="Nenhum milestone definido" className="p-6 sm:p-8" testId="no-milestones" />
      ) : (
        <div className="relative pl-6">
          {/* Timeline line */}
          <div className="absolute left-2.5 top-2 bottom-2 w-0.5 bg-gray-200" />
          <div className="space-y-4">
            {milestones.map((m) => (
              <div key={m.id} className="relative flex items-start gap-4" data-testid={`milestone-${m.id}`}>
                <button onClick={() => toggleMutation.mutate({ id: m.id, completed: !m.completed })}
                  className={`absolute -left-3.5 w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 z-10 transition-colors ${
                    m.completed ? 'bg-[#16A34A] border-[#16A34A] text-white' : 'bg-white border-gray-300'
                  }`} aria-label={m.completed ? 'Marcar milestone como pendente' : 'Marcar milestone como concluído'} data-testid={`toggle-milestone-${m.id}`}>
                  {m.completed && <CheckCircle className="w-3 h-3" aria-hidden="true" />}
                </button>
                <div className="bg-white border border-gray-200/80 rounded-xl p-4 flex-1 ml-2">
                  <div className="flex items-center justify-between">
                    <span className={`font-semibold text-sm ${m.completed ? 'text-[#6B7280] line-through' : 'text-grafite'}`}>{m.title}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[#6B7280] font-mono">{m.date}</span>
                      {canManage && (
                        <button onClick={() => deleteMutation.mutate(m.id)} className="p-1 text-gray-400 hover:text-[#B91C1C]" aria-label="Apagar milestone">
                          <Trash2 className="w-3 h-3" aria-hidden="true" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
