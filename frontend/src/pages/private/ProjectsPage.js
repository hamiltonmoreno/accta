import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { queryKeys } from '../../lib/queryClient';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import {
  FolderKanban, Plus, Search, Filter, ArrowRight, Calendar,
  DollarSign, CheckCircle, Clock, Users, Eye, EyeOff,
  Target, AlertCircle, UsersRound, Briefcase,
} from 'lucide-react';

// Cat 5 F1 — espelha PROJECT_TIPOS do backend (models.py).
const TIPO_LABELS = {
  projeto: 'Projeto',
  grupo_trabalho: 'Grupo de Trabalho',
  comissao: 'Comissão',
};
const TIPO_ICONS = {
  projeto: FolderKanban,
  grupo_trabalho: UsersRound,
  comissao: Briefcase,
};
import {
  PROJECT_STATUS_CONFIG, PROJECT_STATUS_FALLBACK, getStatusConfig,
} from '../../lib/statusConfig';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';

const ProjectCard = ({ project, onClick }) => {
  const st = getStatusConfig(PROJECT_STATUS_CONFIG, project.status, PROJECT_STATUS_FALLBACK);
  const StatusIcon = st.icon;
  const progress = project.progress || 0;
  const budgetPct = project.budget > 0 ? Math.round((project.spent / project.budget) * 100) : 0;
  const tipo = project.tipo || 'projeto';
  const TipoIcon = TIPO_ICONS[tipo] || FolderKanban;
  const isOrganizational = tipo !== 'projeto';

  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl p-5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] hover:-translate-y-0.5 transition-all duration-200 cursor-pointer animate-fade-up outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick?.(); } }}
      aria-label={`Abrir ${TIPO_LABELS[tipo]} ${project.title}`}
      data-testid={`project-card-${project.id}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0 mr-3">
          {isOrganizational && (
            <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-gray-500 mb-1">
              <TipoIcon className="w-3 h-3" aria-hidden="true" />
              {TIPO_LABELS[tipo]}
            </span>
          )}
          <h3 className="font-semibold text-grafite text-base truncate">{project.title}</h3>
          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{project.description || 'Sem descricao'}</p>
        </div>
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider whitespace-nowrap ${st.className}`}>
          <StatusIcon className="w-3 h-3" aria-hidden="true" />
          {st.label}
        </span>
      </div>

      {isOrganizational && project.responsible_name && (
        <div className="flex items-center gap-1.5 text-xs text-gray-600 mb-2">
          <Users className="w-3 h-3" aria-hidden="true" />
          <span className="text-gray-500">Coordenador:</span>
          <span className="font-semibold text-grafite truncate">{project.responsible_name}</span>
        </div>
      )}

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
  const qc = useQueryClient();
  const { isAdmin, isDirecao } = useAuth();
  const canCreateOrganizational = isAdmin || isDirecao;
  const [form, setForm] = useState({
    title: '', description: '', visibility: 'publico',
    category: '', tipo: 'projeto', budget: '', start_date: '', end_date: '',
  });

  const createMutation = useMutation({
    mutationFn: (payload) => projectsAPI.create(payload),
    onSuccess: () => {
      const labels = { projeto: 'Projeto criado', grupo_trabalho: 'Grupo de trabalho criado', comissao: 'Comissão criada' };
      toast.success(labels[form.tipo] || 'Projeto criado');
      qc.invalidateQueries({ queryKey: queryKeys.projects.list() });
      onClose();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao criar'),
  });

  const saving = createMutation.isPending;
  const isOrganizational = form.tipo !== 'projeto';
  const submitLabel = saving
    ? 'A criar...'
    : isOrganizational
      ? `Criar ${TIPO_LABELS[form.tipo]}`
      : 'Propor Projeto';
  const titleLabel = isOrganizational ? `Novo ${TIPO_LABELS[form.tipo]}` : 'Novo Projeto';

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.title.trim()) { toast.error('Titulo e obrigatorio'); return; }
    const payload = { ...form, budget: form.budget ? parseFloat(form.budget) : 0 };
    createMutation.mutate(payload);
  };

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-lg rounded-xl p-0 gap-0 max-h-[90vh] overflow-y-auto" data-testid="create-project-modal">
        <DialogHeader className="p-5 border-b border-gray-100 text-left space-y-0">
          <DialogTitle className="font-bold text-grafite text-lg">{titleLabel}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {canCreateOrganizational && (
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Tipo *</label>
              <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                data-testid="project-tipo-select">
                <option value="projeto">Projeto</option>
                <option value="grupo_trabalho">Grupo de Trabalho (Art. 31.e)</option>
                <option value="comissao">Comissão (Art. 31.e)</option>
              </select>
              {isOrganizational && (
                <p className="mt-1 text-[11px] text-gray-500">
                  Criado pela Direcção — fica directamente <strong>Aprovado</strong> (salta o passo de proposta).
                </p>
              )}
            </div>
          )}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Titulo *</label>
            <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Ex: Festa do Dia do Controlador 2026"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="project-title-input" />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Descricao</label>
            <textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Descreva o objetivo e escopo do projeto..."
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none resize-none"
              data-testid="project-desc-input" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Visibilidade</label>
              <select value={form.visibility} onChange={(e) => setForm({ ...form, visibility: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                data-testid="project-visibility-select">
                <option value="publico">Publico</option>
                <option value="privado">Privado (Direcao)</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Categoria</label>
              <input type="text" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
                placeholder="Ex: Social, Formacao"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none" />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Orcamento (CVE)</label>
              <input type="number" inputMode="decimal" min="0" value={form.budget} onChange={(e) => setForm({ ...form, budget: e.target.value })}
                placeholder="0"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm font-mono focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                data-testid="project-budget-input" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Inicio</label>
              <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Fim</label>
              <input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none" />
            </div>
          </div>
          <button type="submit" disabled={saving} className="w-full btn-primary py-3 text-sm font-semibold" data-testid="create-project-btn">
            {submitLabel}
          </button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// ===== MAIN PAGE =====
const ProjectsPage = () => {
  const { isAdmin } = useAuth();
  const navigate = useNavigate();
  const [filterStatus, setFilterStatus] = useState('');
  const [filterTipo, setFilterTipo] = useState('');
  const [searchText, setSearchText] = useState('');
  const [showCreate, setShowCreate] = useState(false);

  // Cache server-side por filtros (search e client-side).
  const { data: items = [], isLoading: loading } = useQuery({
    queryKey: ['projects', { status: filterStatus || undefined, tipo: filterTipo || undefined }],
    queryFn: async () => {
      const params = {};
      if (filterStatus) params.status = filterStatus;
      if (filterTipo) params.tipo = filterTipo;
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
  const tipoTabs = [
    { val: '', label: 'Todos', icon: FolderKanban },
    { val: 'projeto', label: 'Projetos', icon: FolderKanban },
    { val: 'grupo_trabalho', label: 'Grupos de Trabalho', icon: UsersRound },
    { val: 'comissao', label: 'Comissões', icon: Briefcase },
  ];
  const newButtonLabel = filterTipo === 'grupo_trabalho'
    ? 'Novo Grupo'
    : filterTipo === 'comissao'
      ? 'Nova Comissão'
      : 'Novo Projeto';

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="page-title" data-testid="projects-title">Projetos</h1>
          <p className="page-subtitle">Gestão e acompanhamento de projetos da associação</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2 text-sm w-fit" data-testid="new-project-btn">
          <Plus className="w-4 h-4" /> {newButtonLabel}
        </button>
      </div>

      {/* Tipo tabs — Cat 5 F1 (spec-fins-profissionais §4.3) */}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-gray-200">
        {tipoTabs.map((t) => {
          const Icon = t.icon;
          const active = filterTipo === t.val;
          return (
            <button
              key={t.val}
              onClick={() => setFilterTipo(t.val)}
              data-testid={`tipo-tab-${t.val || 'all'}`}
              className={`inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold uppercase tracking-wider border-b-2 -mb-[1px] transition-colors ${
                active
                  ? 'text-grafite border-grafite'
                  : 'text-gray-500 border-transparent hover:text-grafite'
              }`}>
              <Icon className="w-3.5 h-3.5" aria-hidden="true" />
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Filters */}
      <div className="card-technical p-3 sm:p-4">
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="relative flex-1 min-w-[180px] max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input type="text" placeholder="Pesquisar projetos..." value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
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
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4" data-testid="projects-loading">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white border border-gray-200/80 rounded-2xl p-5">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0 mr-3 space-y-2">
                  <Skeleton className="h-4 w-2/3" />
                  <Skeleton className="h-3 w-full" />
                </div>
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
              <Skeleton className="h-1.5 w-full rounded-full mb-3" />
              <div className="flex items-center gap-4">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-3 w-20" />
              </div>
            </div>
          ))}
        </div>
      ) : projects.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title="Nenhum projeto encontrado"
          description="Crie um novo projeto para comecar"
          testId="no-projects"
        />
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
