import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Calendar, CheckCircle, Clock, Plus, Trash2, Users } from 'lucide-react';
import { projectsAPI } from '../../../utils/api';
import { useAuth } from '../../../contexts/AuthContext';
import {
  TASK_PRIORITY_CONFIG, TASK_PRIORITY_FALLBACK, getStatusConfig,
} from '../../../lib/statusConfig';
import { EmptyState } from '../../../components/EmptyState';

const EMPTY_TASK = { title: '', description: '', assignee_id: '', priority: 'media', due_date: '' };

export const TasksTab = ({ project, tasks, members, canManage, onReload }) => {
  const { user } = useAuth();
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(EMPTY_TASK);

  const createMutation = useMutation({
    mutationFn: (data) => projectsAPI.createTask(project.id, data),
    onSuccess: () => {
      toast.success('Tarefa criada');
      setForm(EMPTY_TASK);
      setShowAdd(false);
      onReload();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ taskId, data }) => projectsAPI.updateTask(project.id, taskId, data),
    onSuccess: onReload,
    onError: () => toast.error('Erro ao atualizar'),
  });

  const deleteMutation = useMutation({
    mutationFn: (taskId) => projectsAPI.deleteTask(project.id, taskId),
    onSuccess: onReload,
    onError: () => toast.error('Erro'),
  });

  const saving = createMutation.isPending;

  const handleAdd = () => {
    if (!form.title.trim()) { toast.error('Titulo da tarefa obrigatorio'); return; }
    createMutation.mutate(form);
  };

  const toggleStatus = (task) => {
    const next = task.status === 'concluido' ? 'pendente' : task.status === 'pendente' ? 'em_curso' : 'concluido';
    updateMutation.mutate({ taskId: task.id, data: { status: next } });
  };

  const taskStatusIcon = (status) => {
    if (status === 'concluido') return <CheckCircle className="w-4 h-4 text-[#16A34A]" />;
    if (status === 'em_curso') return <Clock className="w-4 h-4 text-[#2563EB]" />;
    return <div className="w-4 h-4 rounded-full border-2 border-gray-300" />;
  };

  return (
    <div className="space-y-4">
      {canManage && (
        <div className="flex justify-end">
          <button onClick={() => setShowAdd(!showAdd)} className="btn-outline flex items-center gap-2 text-sm" data-testid="add-task-btn">
            <Plus className="w-4 h-4" /> Tarefa
          </button>
        </div>
      )}

      {showAdd && (
        <div className="bg-white border border-gray-200/80 rounded-xl p-4 space-y-3 animate-fade-up">
          <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
            placeholder="Titulo da tarefa" data-testid="task-title-input"
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none" />
          <textarea rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Descricao (opcional)"
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none resize-none" />
          <div className="flex flex-wrap gap-2">
            <select value={form.assignee_id} onChange={(e) => setForm({ ...form, assignee_id: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm flex-1 min-w-[140px] focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="task-assignee-select">
              <option value="">Sem responsavel</option>
              {members.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
            <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none">
              <option value="baixa">Baixa</option>
              <option value="media">Media</option>
              <option value="alta">Alta</option>
            </select>
            <input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none" />
            <button onClick={handleAdd} disabled={saving} className="btn-primary text-sm px-5" data-testid="save-task-btn">
              {saving ? '...' : 'Adicionar'}
            </button>
          </div>
        </div>
      )}

      {tasks.length === 0 ? (
        <EmptyState icon={CheckCircle} title="Nenhuma tarefa criada" className="p-6 sm:p-8" testId="no-tasks" />
      ) : (
        <div className="space-y-1.5">
          {tasks.map((task) => {
            const pri = getStatusConfig(TASK_PRIORITY_CONFIG, task.priority, TASK_PRIORITY_FALLBACK);
            const PriIcon = pri.icon;
            const canUpdateTask = canManage || task.assignee_id === user?.id;
            return (
              <div key={task.id}
                className={`bg-white border border-gray-200/80 rounded-xl p-3.5 flex items-start gap-3 transition-all ${task.status === 'concluido' ? 'opacity-60' : ''}`}
                data-testid={`task-${task.id}`}>
                <button
                  onClick={() => canUpdateTask && toggleStatus(task)}
                  disabled={!canUpdateTask}
                  className={`mt-0.5 flex-shrink-0 ${canUpdateTask ? '' : 'cursor-not-allowed opacity-50'}`}
                  aria-label="Alternar estado da tarefa"
                  data-testid={`toggle-task-${task.id}`}
                >
                  {taskStatusIcon(task.status)}
                </button>
                <div className="flex-1 min-w-0">
                  <div className={`font-medium text-sm ${task.status === 'concluido' ? 'line-through text-[#6B7280]' : 'text-grafite'}`}>
                    {task.title}
                  </div>
                  {task.description && <p className="text-xs text-gray-500 mt-0.5">{task.description}</p>}
                  <div className="flex items-center gap-3 mt-1.5 text-xs text-[#6B7280]">
                    {task.assignee_name && <span className="flex items-center gap-1"><Users className="w-3 h-3" />{task.assignee_name}</span>}
                    {task.due_date && <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{task.due_date}</span>}
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold ${pri.className}`}>
                      <PriIcon className="w-3 h-3" aria-hidden="true" />{pri.label}
                    </span>
                  </div>
                </div>
                {canManage && (
                  <button onClick={() => deleteMutation.mutate(task.id)} className="p-1 text-gray-400 hover:text-[#B91C1C] flex-shrink-0" aria-label="Apagar tarefa">
                    <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
