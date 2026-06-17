import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { CheckCircle, DollarSign, MessageSquare, Target } from 'lucide-react';
import { projectsAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { queryKeys } from '../../lib/queryClient';
import { PROJECT_STATUS_CONFIG } from '../../lib/statusConfig';

import { TabBtn } from './projects/widgets';
import { DetailHeader } from './projects/DetailHeader';
import { InfoCards } from './projects/InfoCards';
import { TasksTab } from './projects/TasksTab';
import { CommentsTab } from './projects/CommentsTab';
import { BudgetTab } from './projects/BudgetTab';
import { TimelineTab } from './projects/TimelineTab';

const ProjectDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isAdmin } = useAuth();
  const qc = useQueryClient();
  const [tab, setTab] = useState('tasks');

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
  };

  const handleProgressChange = (val) => updateMutation.mutate({ progress: parseInt(val) });

  return (
    <div className="space-y-6">
      <DetailHeader
        project={project}
        isAdmin={isAdmin}
        onBack={() => navigate('/projetos')}
        onStatusChange={handleStatusChange}
        onApprove={() => approveMutation.mutate()}
      />

      <InfoCards
        project={project}
        canManage={canManage}
        onProgressChange={handleProgressChange}
      />

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
