import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { defesaAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';
import {
  Megaphone, Plus, Search, FileText, Send, CheckCircle2, XCircle,
  Archive, Pencil, Trash2, Calendar, Globe, Lock, AlertCircle,
} from 'lucide-react';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';

// Cat 5 F3 — espelha DEFESA_TIPOS/STATUSES do backend (models.py).
const TIPO_LABELS = {
  representacao: 'Representação',
  tomada_posicao: 'Tomada de Posição',
  comunicado: 'Comunicado',
};

const STATUS_LABELS = {
  rascunho: 'Rascunho',
  submetido: 'Submetido',
  publicado: 'Publicado',
  arquivado: 'Arquivado',
};

const STATUS_STYLES = {
  rascunho: 'bg-gray-100 text-gray-700 border-gray-200',
  submetido: 'bg-gray-100 text-grafite border-gray-300',
  publicado: 'bg-gray-50 text-grafite border-gray-300 font-bold',
  arquivado: 'bg-gray-50 text-gray-500 border-gray-200',
};

const DefesaCard = ({ defesa, canManage, currentUserId, onEdit, onDelete, onSubmeter, onAprovar, onRejeitar, onArquivar }) => {
  const isAuthor = defesa.created_by === currentUserId;
  const VisIcon = defesa.visibility === 'publico' ? Globe : Lock;

  // Ações contextuais por status × papel × autor.
  const canEdit = canManage && (defesa.status === 'rascunho' || defesa.status === 'submetido');
  const canDelete = canManage && defesa.status !== 'publicado' && defesa.status !== 'arquivado';
  const canSubmeter = defesa.status === 'rascunho' && (isAuthor || canManage);
  const canAprovar = canManage && defesa.status === 'submetido' && !isAuthor;
  const canRejeitar = canManage && defesa.status === 'submetido' && !isAuthor;
  const canArquivar = canManage && (defesa.status === 'publicado' || defesa.status === 'rascunho' || defesa.status === 'submetido');

  return (
    <div
      className="bg-white border border-gray-200/80 rounded-2xl p-5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all duration-200 animate-fade-up"
      data-testid={`defesa-card-${defesa.id}`}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-gray-500">
            <FileText className="w-3 h-3" aria-hidden="true" />
            {TIPO_LABELS[defesa.tipo]}
          </span>
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider border ${STATUS_STYLES[defesa.status]}`}>
            {STATUS_LABELS[defesa.status]}
          </span>
        </div>
        <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-wider text-gray-500">
          <VisIcon className="w-3 h-3" />
          {defesa.visibility === 'publico' ? 'Público' : 'Sócios'}
        </span>
      </div>
      <h3 className="font-semibold text-grafite text-base mb-1 line-clamp-2">{defesa.titulo}</h3>
      {defesa.entidade_destino && (
        <p className="text-xs text-gray-500 mb-1">
          A: <span className="text-grafite">{defesa.entidade_destino}</span>
        </p>
      )}
      {defesa.descricao && (
        <p className="text-sm text-gray-600 mb-2 line-clamp-3">{defesa.descricao}</p>
      )}
      <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 mb-3">
        <span className="flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          {defesa.data}
        </span>
        {defesa.document_id && (
          <a
            href={`/api/documents/${defesa.document_id}/download`}
            className="inline-flex items-center gap-1 text-grafite hover:text-carmesim transition-colors font-semibold"
            target="_blank"
            rel="noreferrer"
          >
            <FileText className="w-3 h-3" /> Documento
          </a>
        )}
      </div>
      {defesa.status === 'rascunho' && defesa.motivo_rejeicao && (
        <div className="mb-3 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs">
          <p className="flex items-start gap-1.5 text-grafite">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
            <span>
              <strong>Rejeitado</strong> — {defesa.motivo_rejeicao}
            </span>
          </p>
        </div>
      )}

      <div className="flex flex-wrap gap-1.5">
        {canSubmeter && (
          <button
            onClick={() => onSubmeter(defesa)}
            className="inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border border-gray-300 text-grafite hover:bg-gray-50 transition-colors font-semibold"
            data-testid={`defesa-submeter-${defesa.id}`}
          >
            <Send className="w-3 h-3" /> Submeter
          </button>
        )}
        {canAprovar && (
          <button
            onClick={() => onAprovar(defesa)}
            className="inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border border-gray-300 text-grafite hover:bg-gray-50 transition-colors font-semibold"
            data-testid={`defesa-aprovar-${defesa.id}`}
          >
            <CheckCircle2 className="w-3 h-3" /> Aprovar
          </button>
        )}
        {canRejeitar && (
          <button
            onClick={() => onRejeitar(defesa)}
            className="inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border border-carmesim text-carmesim hover:bg-carmesim/5 transition-colors font-semibold"
            data-testid={`defesa-rejeitar-${defesa.id}`}
          >
            <XCircle className="w-3 h-3" /> Rejeitar
          </button>
        )}
        {canArquivar && (
          <button
            onClick={() => onArquivar(defesa)}
            className="inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors font-semibold"
            data-testid={`defesa-arquivar-${defesa.id}`}
          >
            <Archive className="w-3 h-3" /> Arquivar
          </button>
        )}
        {canEdit && (
          <button
            onClick={() => onEdit(defesa)}
            className="inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
            data-testid={`defesa-editar-${defesa.id}`}
          >
            <Pencil className="w-3 h-3" /> Editar
          </button>
        )}
        {canDelete && (
          <button
            onClick={() => onDelete(defesa)}
            className="inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border border-carmesim text-carmesim hover:bg-carmesim/5 transition-colors"
            data-testid={`defesa-eliminar-${defesa.id}`}
          >
            <Trash2 className="w-3 h-3" /> Eliminar
          </button>
        )}
      </div>
    </div>
  );
};

const DefesaModal = ({ defesa, onClose }) => {
  const qc = useQueryClient();
  const isEdit = !!defesa;
  const [form, setForm] = useState(
    defesa || {
      titulo: '',
      tipo: 'tomada_posicao',
      descricao: '',
      entidade_destino: '',
      data: new Date().toISOString().slice(0, 10),
      document_id: '',
      visibility: 'socios',
    }
  );
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.titulo.trim()) {
      toast.error('Título obrigatório');
      return;
    }
    setSaving(true);
    try {
      const payload = { ...form };
      if (!payload.document_id) delete payload.document_id;
      if (!payload.entidade_destino) delete payload.entidade_destino;
      if (isEdit) {
        await defesaAPI.update(defesa.id, payload);
        toast.success('Registo atualizado');
      } else {
        await defesaAPI.create(payload);
        toast.success('Registo criado em rascunho');
      }
      qc.invalidateQueries({ queryKey: ['defesa-profissional'] });
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao guardar');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Editar registo' : 'Novo registo de defesa profissional'}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Título *</label>
            <input
              type="text"
              value={form.titulo}
              onChange={(e) => setForm({ ...form, titulo: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="defesa-titulo-input"
            />
          </div>
          {!isEdit && (
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Tipo *</label>
              <select
                value={form.tipo}
                onChange={(e) => setForm({ ...form, tipo: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                data-testid="defesa-tipo-select"
              >
                <option value="representacao">Representação</option>
                <option value="tomada_posicao">Tomada de Posição</option>
                <option value="comunicado">Comunicado</option>
              </select>
            </div>
          )}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Descrição</label>
            <textarea
              rows={4}
              value={form.descricao}
              onChange={(e) => setForm({ ...form, descricao: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none resize-none"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Entidade destino</label>
            <input
              type="text"
              value={form.entidade_destino || ''}
              onChange={(e) => setForm({ ...form, entidade_destino: e.target.value })}
              placeholder="Ex.: AAC, ASA, Tutela"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Data *</label>
              <input
                type="date"
                value={form.data}
                onChange={(e) => setForm({ ...form, data: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Visibilidade</label>
              <select
                value={form.visibility}
                onChange={(e) => setForm({ ...form, visibility: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              >
                <option value="socios">Sócios</option>
                <option value="publico">Público</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Document ID (opcional)</label>
            <input
              type="text"
              value={form.document_id || ''}
              onChange={(e) => setForm({ ...form, document_id: e.target.value })}
              placeholder="ID do PDF anexo no módulo de Documentos"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm font-mono focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
            />
          </div>
          <p className="text-[11px] text-gray-500">
            Tomadas de posição passam por <strong>aprovação da Direcção</strong> antes de ficarem públicas.
            Quem submete não pode aprovar.
          </p>
          <button type="submit" disabled={saving} className="w-full btn-primary py-3 text-sm font-semibold">
            {saving ? 'A guardar...' : isEdit ? 'Guardar Alterações' : 'Criar rascunho'}
          </button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

const RejeicaoModal = ({ defesa, onClose }) => {
  const qc = useQueryClient();
  const [motivo, setMotivo] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!motivo.trim()) {
      toast.error('Motivo obrigatório');
      return;
    }
    setSaving(true);
    try {
      await defesaAPI.rejeitar(defesa.id, motivo);
      toast.success('Submissão rejeitada e devolvida a rascunho');
      qc.invalidateQueries({ queryKey: ['defesa-profissional'] });
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao rejeitar');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Rejeitar submissão</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-3">
          <p className="text-sm text-gray-600">
            <strong>{defesa.titulo}</strong> — indique o motivo da rejeição.
            O autor é notificado.
          </p>
          <textarea
            rows={4}
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            placeholder="Motivo da rejeição (obrigatório)"
            className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none resize-none"
            data-testid="defesa-motivo-input"
          />
          <button type="submit" disabled={saving} className="w-full btn-primary py-3 text-sm font-semibold">
            {saving ? 'A enviar...' : 'Rejeitar'}
          </button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export const DefesaProfissionalPage = () => {
  const { user, isAdmin, isDirecao } = useAuth();
  const canManage = isAdmin || isDirecao;
  const [filterStatus, setFilterStatus] = useState('');
  const [searchText, setSearchText] = useState('');
  const [editing, setEditing] = useState(null);
  const [rejeicaoModal, setRejeicaoModal] = useState(null);
  const qc = useQueryClient();

  const { data, isLoading: loading } = useQuery({
    queryKey: ['defesa-profissional', { status: filterStatus || undefined }],
    queryFn: async () => {
      const params = filterStatus ? { status: filterStatus } : {};
      const res = await defesaAPI.getAll(params);
      return res.data;
    },
  });
  const items = data?.items || [];

  const submeterMutation = useMutation({
    mutationFn: (id) => defesaAPI.submeter(id),
    onSuccess: () => {
      toast.success('Submetido para aprovação');
      qc.invalidateQueries({ queryKey: ['defesa-profissional'] });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao submeter'),
  });
  const aprovarMutation = useMutation({
    mutationFn: (id) => defesaAPI.aprovar(id),
    onSuccess: () => {
      toast.success('Aprovado e publicado');
      qc.invalidateQueries({ queryKey: ['defesa-profissional'] });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao aprovar'),
  });
  const arquivarMutation = useMutation({
    mutationFn: (id) => defesaAPI.arquivar(id),
    onSuccess: () => {
      toast.success('Arquivado');
      qc.invalidateQueries({ queryKey: ['defesa-profissional'] });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao arquivar'),
  });
  const deleteMutation = useMutation({
    mutationFn: (id) => defesaAPI.delete(id),
    onSuccess: () => {
      toast.success('Eliminado');
      qc.invalidateQueries({ queryKey: ['defesa-profissional'] });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao eliminar'),
  });

  const filtered = searchText
    ? items.filter((d) => {
        const q = searchText.toLowerCase();
        return (
          d.titulo.toLowerCase().includes(q) ||
          (d.descricao || '').toLowerCase().includes(q) ||
          (d.entidade_destino || '').toLowerCase().includes(q)
        );
      })
    : items;

  const tabs = [
    { val: '', label: 'Todos' },
    { val: 'rascunho', label: 'Rascunhos' },
    { val: 'submetido', label: 'Submetidos' },
    { val: 'publicado', label: 'Publicados' },
    { val: 'arquivado', label: 'Arquivados' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="page-title" data-testid="defesa-title">Defesa Profissional</h1>
          <p className="page-subtitle">
            Representações, tomadas de posição e comunicados em defesa dos
            interesses profissionais dos controladores (Art. 2.a). Tomadas de
            posição passam por aprovação da Direcção.
          </p>
        </div>
        {canManage && (
          <button
            onClick={() => setEditing('new')}
            className="btn-primary flex items-center gap-2 text-sm w-fit"
            data-testid="defesa-new-btn"
          >
            <Plus className="w-4 h-4" /> Novo Registo
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-1.5 border-b border-gray-200">
        {tabs.map((t) => {
          const active = filterStatus === t.val;
          return (
            <button
              key={t.val}
              onClick={() => setFilterStatus(t.val)}
              data-testid={`defesa-tab-${t.val || 'all'}`}
              className={`inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold uppercase tracking-wider border-b-2 -mb-[1px] transition-colors ${
                active ? 'text-grafite border-grafite' : 'text-gray-500 border-transparent hover:text-grafite'
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      <div className="card-technical p-3 sm:p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Pesquisar..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
            data-testid="defesa-search"
          />
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-2xl" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Megaphone}
          title="Sem registos"
          description={canManage ? 'Crie o primeiro registo para começar' : 'Aguarde — a Direcção ainda não publicou nada'}
          testId="defesa-empty"
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((d) => (
            <DefesaCard
              key={d.id}
              defesa={d}
              canManage={canManage}
              currentUserId={user?.id}
              onEdit={(x) => setEditing(x)}
              onDelete={(x) => {
                if (window.confirm(`Eliminar '${x.titulo}'?`)) deleteMutation.mutate(x.id);
              }}
              onSubmeter={(x) => submeterMutation.mutate(x.id)}
              onAprovar={(x) => {
                if (window.confirm(`Aprovar e publicar '${x.titulo}'?`)) aprovarMutation.mutate(x.id);
              }}
              onRejeitar={(x) => setRejeicaoModal(x)}
              onArquivar={(x) => arquivarMutation.mutate(x.id)}
            />
          ))}
        </div>
      )}

      {editing && (
        <DefesaModal defesa={editing === 'new' ? null : editing} onClose={() => setEditing(null)} />
      )}
      {rejeicaoModal && (
        <RejeicaoModal defesa={rejeicaoModal} onClose={() => setRejeicaoModal(null)} />
      )}
    </div>
  );
};

export default DefesaProfissionalPage;
