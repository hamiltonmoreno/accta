import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { useBodyScrollLock } from '../../hooks/useBodyScrollLock';
import { queryKeys } from '../../lib/queryClient';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import {
  FolderKanban, Plus, Search, Filter, ArrowRight, Calendar,
  DollarSign, CheckCircle, Clock, Users, Eye, EyeOff, X,
  Target, AlertCircle,
} from 'lucide-react';

const STATUS_CONFIG = {
  proposta: { label: 'Proposta', color: 'bg-[#FFFBEB] text-[#B45309]', dot: 'bg-[#D97706]' },
  aprovado: { label: 'Aprovado', color: 'bg-[#EFF6FF] text-[#1D4ED8]', dot: 'bg-[#2563EB]' },
  em_curso: { label: 'Em Curso', color: 'bg-[#EFF6FF] text-[#1D4ED8]', dot: 'bg-[#2563EB]' },
  concluido: { label: 'Concluido', color: 'bg-[#F0FDF4] text-[#15803D]', dot: 'bg-[#16A34A]' },
  cancelado: { label: 'Cancelado', color: 'bg-[#FEF2F2] text-[#B91C1C]', dot: 'bg-[#C7202F]' },
};

const ProjectCard = ({ project, onClick }) => {
  const st = STATUS_CONFIG[project.status] || STATUS_CONFIG.proposta;
  const progress = project.progress || 0;
  const budgetPct = project.budget > 0 ? Math.round((project.spent / project.budget) * 100) : 0;

  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl p-5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] hover:-translate-y-0.5 transition-all duration-200 cursor-pointer animate-fade-up"
      onClick={onClick}
      data-testid={`project-card-${project.id}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0 mr-3">
          <h3 className="font-semibold text-grafite text-base truncate">{project.title}</h3>
          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{project.description || 'Sem descricao'}</p>
        </div>
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider whitespace-nowrap ${st.color}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${st.dot}`} />
          {st.label}
        </span>
      </div>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-[#6B7280] uppercase tracking-wider font-semibold">Progresso</span>
          <span className="text-xs font-mono font-bold text-grafite">{progress}%</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-1.5">
          <div
            className="bg-carmesim h-1.5 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Meta row */}
      <div className="flex items-center gap-4 text-xs text-gray-500">
        {project.end_date && (
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {project.end_date}
          </span>
        )}
        {project.budget > 0 && (
          <span className="flex items-center gap-1">
            <DollarSign className="w-3 h-3" />
            {budgetPct}% do orcamento
          </span>
        )}
        <span className="flex items-center gap-1">
          <CheckCircle className="w-3 h-3" />
          {project.task_done || 0}/{project.task_count || 0} tarefas
        </span>
        {project.visibility === 'privado' && (
          <span className="flex items-center gap-1 text-carmesim">
            <EyeOff className="w-3 h-3" /> Privado
          </span>
        )}
      </div>
    </div>
  );
};

// ===== CREATE PROJECT MODAL =====
const CreateProjectModal = ({ onClose }) => {
  useBodyScrollLock(true);
  const qc = useQueryClient();
  const [form, setForm] = useState({
    title: '', description: '', visibility: 'publico',
    category: '', budget: '', start_date: '', end_date: '',
  });

  const createMutation = useMutation({
    mutationFn: (payload) => projectsAPI.create(payload),
    onSuccess: () => {
      toast.success('Projeto criado');
      qc.invalidateQueries({ queryKey: queryKeys.projects.list() });
      onClose();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao criar'),
  });

  const saving = createMutation.isPending;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.title.trim()) { toast.error('Titulo e obrigatorio'); return; }
    const payload = { ...form, budget: form.budget ? parseFloat(form.budget) : 0 };
    createMutation.mutate(payload);
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-black/40 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div className="flex min-h-full items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg animate-fade-up"
        onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <h2 className="font-bold text-grafite text-lg">Novo Projeto</h2>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-gray-100 text-gray-400" aria-label="Fechar" data-testid="close-modal-btn"><X className="w-5 h-5" aria-hidden="true" /></button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Titulo *</label>
            <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Ex: Festa do Dia do Controlador 2026"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim outline-none"
              data-testid="project-title-input" />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Descricao</label>
            <textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Descreva o objetivo e escopo do projeto..."
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim outline-none resize-none"
              data-testid="project-desc-input" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Visibilidade</label>
              <select value={form.visibility} onChange={(e) => setForm({ ...form, visibility: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim outline-none"
                data-testid="project-visibility-select">
                <option value="publico">Publico</option>
                <option value="privado">Privado (Direcao)</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Categoria</label>
              <input type="text" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
                placeholder="Ex: Social, Formacao"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim outline-none" />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Orcamento (CVE)</label>
              <input type="number" inputMode="decimal" min="0" value={form.budget} onChange={(e) => setForm({ ...form, budget: e.target.value })}
                placeholder="0"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim outline-none"
                data-testid="project-budget-input" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Inicio</label>
              <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim outline-none" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Fim</label>
              <input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim outline-none" />
            </div>
          </div>
          <button type="submit" disabled={saving} className="w-full btn-primary py-3 text-sm font-semibold" data-testid="create-project-btn">
            {saving ? 'A criar...' : 'Propor Projeto'}
          </button>
        </form>
      </div>
      </div>
    </div>
  );
};

// ===== MAIN PAGE =====
const ProjectsPage = () => {
  const { isAdmin } = useAuth();
  const navigate = useNavigate();
  const [filterStatus, setFilterStatus] = useState('');
  const [searchText, setSearchText] = useState('');
  const [showCreate, setShowCreate] = useState(false);

  // Cache server-side por filterStatus apenas (search e client-side).
  const { data: items = [], isLoading: loading } = useQuery({
    queryKey: ['projects', { status: filterStatus || undefined }],
    queryFn: async () => {
      const params = filterStatus ? { status: filterStatus } : {};
      const res = await projectsAPI.getAll(params);
      return res.data.items || [];
    },
  });

  const projects = searchText
    ? items.filter((p) => {
        const q = searchText.toLowerCase();
        return p.title.toLowerCase().includes(q) || (p.description || '').toLowerCase().includes(q);
      })
    : items;

  const statusFilters = [
    { val: '', label: 'Todos' },
    { val: 'proposta', label: 'Propostas' },
    { val: 'aprovado', label: 'Aprovados' },
    { val: 'em_curso', label: 'Em Curso' },
    { val: 'concluido', label: 'Concluidos' },
  ];

  return (
    <div className="space-y-5 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="page-title" data-testid="projects-title">Projetos</h1>
          <p className="page-subtitle">Gestao e acompanhamento de projetos da associacao</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2 text-sm w-fit" data-testid="new-project-btn">
          <Plus className="w-4 h-4" /> Novo Projeto
        </button>
      </div>

      {/* Filters */}
      <div className="card-technical p-3 sm:p-4">
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="relative flex-1 min-w-[180px] max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input type="text" placeholder="Pesquisar projetos..." value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim outline-none"
              data-testid="projects-search" />
          </div>
          <div className="flex items-center gap-1.5 ml-auto">
            <Filter className="w-4 h-4 text-gray-400 hidden sm:block" />
            {statusFilters.map((f) => (
              <button key={f.val} onClick={() => setFilterStatus(f.val)}
                data-testid={`filter-${f.val || 'all'}`}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                  filterStatus === f.val ? 'bg-grafite text-white' : 'bg-white text-gray-500 border border-gray-100 hover:bg-gray-50'
                }`}>
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="text-center py-16">
          <div className="inline-block w-8 h-8 border-3 border-carmesim border-t-transparent rounded-full animate-spin" />
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-16" data-testid="no-projects">
          <FolderKanban className="w-12 h-12 text-gray-200 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">Nenhum projeto encontrado</p>
          <p className="text-xs text-[#6B7280] mt-1">Crie um novo projeto para comecar</p>
        </div>
      ) : (
        <>
          {/* Pending approval banner for admin */}
          {isAdmin && projects.some(p => p.status === 'proposta') && (
            <div className="bg-white border border-[#FDE68A] rounded-xl p-4 flex items-center gap-3" data-testid="pending-approval-banner">
              <AlertCircle className="w-5 h-5 text-[#B45309] flex-shrink-0" />
              <span className="text-sm text-gray-700">
                <strong>{projects.filter(p => p.status === 'proposta').length}</strong> projeto(s) aguardam a sua aprovacao
              </span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} onClick={() => navigate(`/projetos/${project.id}`)} />
            ))}
          </div>
        </>
      )}

      {showCreate && <CreateProjectModal onClose={() => setShowCreate(false)} />}
    </div>
  );
};

export default ProjectsPage;
