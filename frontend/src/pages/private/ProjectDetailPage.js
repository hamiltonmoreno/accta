import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { queryKeys } from '../../lib/queryClient';
import { toast } from 'sonner';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, CheckCircle, Clock, Plus, Trash2, Send,
  DollarSign, Target, MessageSquare, Calendar, Users,
  Pencil, Eye, EyeOff, X, AlertCircle,
} from 'lucide-react';
import {
  PROJECT_STATUS_CONFIG, PROJECT_STATUS_FALLBACK,
  TASK_PRIORITY_CONFIG, TASK_PRIORITY_FALLBACK,
  getStatusConfig,
} from '../../lib/statusConfig';
import { EmptyState } from '../../components/EmptyState';

const TabBtn = ({ active, label, icon: Icon, onClick, badge, testId }) => (
  <button onClick={onClick} data-testid={testId}
    className={`flex items-center gap-2 px-4 py-2.5 text-sm font-semibold rounded-lg transition-all whitespace-nowrap ${
      active ? 'bg-carmesim text-white shadow-sm' : 'text-gray-500 hover:bg-gray-100 hover:text-grafite'
    }`}>
    <Icon className="w-4 h-4" />
    {label}
    {badge > 0 && <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${active ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-500'}`}>{badge}</span>}
  </button>
);

// ===== TASKS TAB =====
const TasksTab = ({ project, tasks, members, canManage, onReload }) => {
  const { user } = useAuth();
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', assignee_id: '', priority: 'media', due_date: '' });

  const createMutation = useMutation({
    mutationFn: (data) => projectsAPI.createTask(project.id, data),
    onSuccess: () => {
      toast.success('Tarefa criada');
      setForm({ title: '', description: '', assignee_id: '', priority: 'media', due_date: '' });
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

  const handleDelete = (taskId) => deleteMutation.mutate(taskId);

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
                  <button onClick={() => handleDelete(task.id)} className="p-1 text-gray-400 hover:text-[#B91C1C] flex-shrink-0" aria-label="Apagar tarefa">
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

// ===== COMMENTS TAB =====
const CommentsTab = ({ project, comments, onReload }) => {
  const { user } = useAuth();
  const [text, setText] = useState('');

  const sendMutation = useMutation({
    mutationFn: (content) => projectsAPI.addComment(project.id, content),
    onSuccess: () => {
      setText('');
      onReload();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro'),
  });

  const deleteMutation = useMutation({
    mutationFn: (commentId) => projectsAPI.deleteComment(project.id, commentId),
    onSuccess: onReload,
    onError: () => toast.error('Erro'),
  });

  const sending = sendMutation.isPending;

  const handleSend = () => {
    if (!text.trim()) return;
    sendMutation.mutate(text);
  };

  const handleDelete = (commentId) => deleteMutation.mutate(commentId);

  return (
    <div className="space-y-4">
      {/* Input */}
      <div className="bg-white border border-gray-200/80 rounded-xl p-3.5 flex items-start gap-3">
        <div className="w-8 h-8 bg-carmesim rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
          {user?.name?.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1">
          <textarea rows={2} value={text} onChange={(e) => setText(e.target.value)}
            placeholder="Partilhe uma ideia ou comentario..."
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none resize-none"
            data-testid="comment-input" />
          <div className="flex justify-end mt-2">
            <button onClick={handleSend} disabled={sending || !text.trim()}
              className="btn-primary text-xs px-4 py-2 flex items-center gap-1.5 disabled:opacity-40" data-testid="send-comment-btn">
              <Send className="w-3.5 h-3.5" /> {sending ? '...' : 'Enviar'}
            </button>
          </div>
        </div>
      </div>

      {/* List */}
      {comments.length === 0 ? (
        <EmptyState icon={MessageSquare} title="Nenhum comentario ainda" className="p-6 sm:p-8" testId="no-comments" />
      ) : (
        <div className="space-y-2">
          {comments.map((c) => (
            <div key={c.id} className="bg-white border border-gray-200/80 rounded-xl p-4" data-testid={`comment-${c.id}`}>
              <div className="flex items-center gap-2 mb-1.5">
                <div className="w-7 h-7 bg-grafite rounded-full flex items-center justify-center text-white text-xs font-bold">
                  {c.user_name?.charAt(0)?.toUpperCase() || '?'}
                </div>
                <span className="font-semibold text-sm text-grafite">{c.user_name}</span>
                <span className="text-xs text-[#6B7280] ml-auto">
                  {c.created_at ? new Date(c.created_at).toLocaleDateString('pt') : ''}
                </span>
                {(c.user_id === user?.id || user?.role === 'admin') && (
                  <button onClick={() => handleDelete(c.id)} className="p-1 text-gray-400 hover:text-[#B91C1C]" aria-label="Apagar comentário">
                    <Trash2 className="w-3 h-3" aria-hidden="true" />
                  </button>
                )}
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">{c.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ===== BUDGET TAB =====
const BudgetTab = ({ project, expenses, canManage, onReload }) => {
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ description: '', amount: '', date: new Date().toISOString().split('T')[0] });

  const spent = expenses.reduce((s, e) => s + e.amount, 0);
  const budget = project.budget || 0;
  const pct = budget > 0 ? Math.round((spent / budget) * 100) : 0;
  const remaining = budget - spent;

  const addMutation = useMutation({
    mutationFn: (data) => projectsAPI.addExpense(project.id, data),
    onSuccess: () => {
      setForm({ description: '', amount: '', date: new Date().toISOString().split('T')[0] });
      setShowAdd(false);
      onReload();
      toast.success('Despesa registrada');
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
    addMutation.mutate({ ...form, amount: parseFloat(form.amount) });
  };

  const handleDelete = (expenseId) => deleteMutation.mutate(expenseId);

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
        <EmptyState icon={DollarSign} title="Nenhuma despesa registrada" className="p-6 sm:p-8" testId="no-expenses" />
      ) : (
        <div className="bg-white border border-gray-200/80 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50/80 text-[#6B7280] uppercase text-xs tracking-wider">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Descricao</th>
                <th className="px-4 py-3 text-right font-semibold">Valor</th>
                <th className="px-4 py-3 text-left font-semibold">Data</th>
                <th className="px-4 py-3 text-left font-semibold">Por</th>
                {canManage && <th className="px-4 py-3 w-10"></th>}
              </tr>
            </thead>
            <tbody>
              {expenses.map(e => (
                <tr key={e.id} className="border-t border-gray-50" data-testid={`expense-${e.id}`}>
                  <td className="px-4 py-3 text-grafite">{e.description}</td>
                  <td className="px-4 py-3 text-right font-mono font-bold text-[#3A3A3A]">{e.amount.toLocaleString('pt')} CVE</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{e.date}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{e.created_by_name}</td>
                  {canManage && (
                    <td className="px-4 py-3"><button onClick={() => handleDelete(e.id)} className="p-1 text-gray-400 hover:text-[#B91C1C]" aria-label="Apagar despesa"><Trash2 className="w-3.5 h-3.5" aria-hidden="true" /></button></td>
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

// ===== TIMELINE TAB =====
const TimelineTab = ({ project, milestones, canManage, onReload }) => {
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ title: '', date: '' });

  const addMutation = useMutation({
    mutationFn: (data) => projectsAPI.addMilestone(project.id, data),
    onSuccess: () => {
      setForm({ title: '', date: '' });
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

  const toggleComplete = (milestone) =>
    toggleMutation.mutate({ id: milestone.id, completed: !milestone.completed });

  const handleDelete = (milestoneId) => deleteMutation.mutate(milestoneId);

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
            {milestones.map((m, i) => (
              <div key={m.id} className="relative flex items-start gap-4" data-testid={`milestone-${m.id}`}>
                <button onClick={() => toggleComplete(m)}
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
                        <button onClick={() => handleDelete(m.id)} className="p-1 text-gray-400 hover:text-[#B91C1C]" aria-label="Apagar milestone">
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

// ===== MAIN DETAIL PAGE =====
const ProjectDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isAdmin } = useAuth();
  const qc = useQueryClient();
  const [tab, setTab] = useState('tasks');
  const [editingStatus, setEditingStatus] = useState(false);

  const projectQuery = useQuery({
    queryKey: queryKeys.projects.byId(id),
    queryFn: async () => (await projectsAPI.getOne(id)).data,
    retry: (count, err) => err?.response?.status !== 404 && count < 3,
  });

  // 404 → projeto inexistente: redireciona como efeito, não dentro do queryFn
  // (chamar navigate durante o fetch faz setState num componente a desmontar).
  useEffect(() => {
    if (projectQuery.error?.response?.status === 404) navigate('/projetos');
  }, [projectQuery.error, navigate]);

  const membersQuery = useQuery({
    queryKey: ['users', 'members'],
    queryFn: async () => (await projectsAPI.getMembers()).data,
  });

  const project = projectQuery.data;
  const members = membersQuery.data || [];
  const loading = projectQuery.isLoading || membersQuery.isLoading;

  // onReload callback para os tab children. Substitui loadProject imperativo.
  const onReload = () => qc.invalidateQueries({ queryKey: queryKeys.projects.byId(id) });

  // Status / approve / progress mutations (quase identicas — share helper).
  const updateMutation = useMutation({
    mutationFn: (data) => projectsAPI.update(id, data),
    onSuccess: () => onReload(),
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro'),
  });

  const approveMutation = useMutation({
    mutationFn: () => projectsAPI.approve(id),
    onSuccess: () => {
      onReload();
      // Invalida lista para o card no /projetos refletir status novo.
      qc.invalidateQueries({ queryKey: ['projects'] });
      toast.success('Projeto aprovado');
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro'),
  });

  if (loading) return <div className="flex justify-center py-20"><div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" /></div>;
  if (!project) return null;

  const canManage = isAdmin || project.created_by === user?.id || project.responsible_id === user?.id;
  const canEditProjectStatus = isAdmin;
  const st = getStatusConfig(PROJECT_STATUS_CONFIG, project.status, PROJECT_STATUS_FALLBACK);
  const StatusIcon = st.icon;

  const handleStatusChange = (newStatus) => {
    updateMutation.mutate(
      { status: newStatus },
      {
        onSuccess: () => {
          onReload();
          toast.success(`Status atualizado para ${PROJECT_STATUS_CONFIG[newStatus]?.label || newStatus}`);
        },
      },
    );
    setEditingStatus(false);
  };

  const handleApprove = () => approveMutation.mutate();

  const handleProgressChange = (val) => updateMutation.mutate({ progress: parseInt(val) });

  return (
    <div className="space-y-6">
      {/* Back + Title */}
      <div>
        <button onClick={() => navigate('/projetos')} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-carmesim mb-3 transition-colors" data-testid="back-to-projects">
          <ArrowLeft className="w-4 h-4" /> Voltar aos projetos
        </button>
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div>
            <h1 className="page-title" data-testid="project-title">{project.title}</h1>
            <div className="flex items-center gap-3 mt-1.5 flex-wrap">
              <div className="relative">
                <button onClick={() => canEditProjectStatus && setEditingStatus(!editingStatus)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${st.className} ${canEditProjectStatus ? 'cursor-pointer hover:opacity-80' : ''}`}
                  data-testid="project-status-badge">
                  <StatusIcon className="w-3 h-3" aria-hidden="true" />
                  {st.label}
                </button>
                {editingStatus && canEditProjectStatus && (
                  <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1 min-w-[140px]">
                    {Object.entries(PROJECT_STATUS_CONFIG).map(([key, val]) => {
                      const ValIcon = val.icon;
                      return (
                        <button key={key} onClick={() => handleStatusChange(key)}
                          className="w-full px-3 py-1.5 text-left text-sm hover:bg-gray-50 flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${val.dotClassName}`} />
                          <ValIcon className="w-3.5 h-3.5 text-[#6B7280]" aria-hidden="true" />
                          {val.label}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
              {project.visibility === 'privado' && (
                <span className="flex items-center gap-1 text-xs text-carmesim font-semibold"><EyeOff className="w-3.5 h-3.5" /> Privado</span>
              )}
              {project.category && <span className="text-xs text-[#6B7280] bg-gray-100 px-2 py-0.5 rounded-full">{project.category}</span>}
            </div>
          </div>

          {/* Admin approve button */}
          {isAdmin && project.status === 'proposta' && (
            <button onClick={handleApprove} className="btn-primary flex items-center gap-2 text-sm" data-testid="approve-project-btn">
              <CheckCircle className="w-4 h-4" /> Aprovar Projeto
            </button>
          )}
        </div>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white border border-gray-200/80 rounded-xl p-3.5">
          <div className="text-xs text-[#6B7280] uppercase tracking-wider mb-0.5">Progresso</div>
          <div className="flex items-center gap-2">
            {canManage ? (
              <input type="range" min="0" max="100" step="5" value={project.progress}
                onChange={(e) => handleProgressChange(e.target.value)}
                className="flex-1 accent-carmesim" data-testid="progress-slider" />
            ) : (
              <div className="flex-1 bg-gray-100 rounded-full h-2">
                <div className="bg-carmesim h-2 rounded-full" style={{ width: `${project.progress}%` }} />
              </div>
            )}
            <span className="font-mono text-sm font-bold text-grafite">{project.progress}%</span>
          </div>
        </div>
        <div className="bg-white border border-gray-200/80 rounded-xl p-3.5">
          <div className="text-xs text-[#6B7280] uppercase tracking-wider mb-0.5">Responsavel</div>
          <div className="text-sm font-medium text-grafite truncate">{project.responsible_name || project.created_by_name || '-'}</div>
        </div>
        <div className="bg-white border border-gray-200/80 rounded-xl p-3.5">
          <div className="text-xs text-[#6B7280] uppercase tracking-wider mb-0.5">Periodo</div>
          <div className="text-xs text-gray-600">{project.start_date || '?'} - {project.end_date || '?'}</div>
        </div>
        <div className="bg-white border border-gray-200/80 rounded-xl p-3.5">
          <div className="text-xs text-[#6B7280] uppercase tracking-wider mb-0.5">Orcamento</div>
          <div className="font-mono text-sm font-bold text-grafite">{(project.budget || 0).toLocaleString('pt')} CVE</div>
        </div>
      </div>

      {/* Description */}
      {project.description && (
        <div className="bg-white border border-gray-200/80 rounded-xl p-5">
          <h3 className="font-semibold text-sm text-grafite mb-2">Descricao</h3>
          <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">{project.description}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
        <TabBtn active={tab === 'tasks'} label="Tarefas" icon={CheckCircle} onClick={() => setTab('tasks')}
          badge={project.tasks?.length || 0} testId="tab-tasks" />
        <TabBtn active={tab === 'comments'} label="Comentarios" icon={MessageSquare} onClick={() => setTab('comments')}
          badge={project.comments?.length || 0} testId="tab-comments" />
        <TabBtn active={tab === 'budget'} label="Orcamento" icon={DollarSign} onClick={() => setTab('budget')}
          badge={project.expenses?.length || 0} testId="tab-budget" />
        <TabBtn active={tab === 'timeline'} label="Timeline" icon={Target} onClick={() => setTab('timeline')}
          badge={project.milestones?.length || 0} testId="tab-timeline" />
      </div>

      {/* Tab Content */}
      {tab === 'tasks' && <TasksTab project={project} tasks={project.tasks || []} members={members} canManage={canManage} onReload={onReload} />}
      {tab === 'comments' && <CommentsTab project={project} comments={project.comments || []} onReload={onReload} />}
      {tab === 'budget' && <BudgetTab project={project} expenses={project.expenses || []} canManage={canManage} onReload={onReload} />}
      {tab === 'timeline' && <TimelineTab project={project} milestones={project.milestones || []} canManage={canManage} onReload={onReload} />}
    </div>
  );
};

export default ProjectDetailPage;
