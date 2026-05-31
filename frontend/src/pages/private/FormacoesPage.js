import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formacoesAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';
import {
  GraduationCap, Plus, Search, Award, FileText, BookOpen, Pencil, Trash2,
  Calendar, ExternalLink, CheckCircle2, XCircle,
} from 'lucide-react';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';

// Cat 5 F2 — espelha FORMACAO_TIPOS do backend (models.py).
const TIPO_LABELS = {
  formacao: 'Formação',
  certificacao: 'Certificação',
  material: 'Material',
};
const TIPO_ICONS = {
  formacao: BookOpen,
  certificacao: Award,
  material: FileText,
};

const FormacaoCard = ({ formacao, canManage, onEdit, onDelete }) => {
  const Icon = TIPO_ICONS[formacao.tipo] || GraduationCap;
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl p-5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all duration-200 animate-fade-up"
      data-testid={`formacao-card-${formacao.id}`}>
      <div className="flex items-start justify-between mb-3 gap-3">
        <div className="flex-1 min-w-0">
          <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-gray-500 mb-1">
            <Icon className="w-3 h-3" aria-hidden="true" />
            {TIPO_LABELS[formacao.tipo]}
          </span>
          <h3 className="font-semibold text-grafite text-base truncate">{formacao.titulo}</h3>
          {formacao.entidade && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">{formacao.entidade}</p>
          )}
        </div>
        {!formacao.ativo && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-gray-100 text-gray-500">
            <XCircle className="w-3 h-3" /> Inativo
          </span>
        )}
      </div>
      {formacao.descricao && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-3">{formacao.descricao}</p>
      )}
      <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
        {formacao.categoria && (
          <span className="px-2 py-0.5 rounded bg-gray-50 border border-gray-200">{formacao.categoria}</span>
        )}
        {formacao.data && (
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {formacao.data}
          </span>
        )}
        {formacao.validade && (
          <span className="flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            Válido até {formacao.validade}
          </span>
        )}
        {formacao.url && (
          <a
            href={formacao.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-grafite hover:text-carmesim transition-colors"
            data-testid={`formacao-url-${formacao.id}`}
          >
            <ExternalLink className="w-3 h-3" />
            Aceder
          </a>
        )}
      </div>
      {canManage && (
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100">
          <button
            onClick={onEdit}
            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-lg border border-gray-200 text-grafite hover:bg-gray-50 transition-colors"
            data-testid={`formacao-edit-${formacao.id}`}
          >
            <Pencil className="w-3 h-3" /> Editar
          </button>
          <button
            onClick={onDelete}
            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-lg border border-gray-200 text-carmesim hover:bg-[#FDF2F3] transition-colors"
            data-testid={`formacao-delete-${formacao.id}`}
          >
            <Trash2 className="w-3 h-3" /> Remover
          </button>
        </div>
      )}
    </div>
  );
};

const FormacaoModal = ({ formacao, onClose }) => {
  const qc = useQueryClient();
  const isEdit = Boolean(formacao);
  const [form, setForm] = useState({
    titulo: formacao?.titulo || '',
    tipo: formacao?.tipo || 'formacao',
    descricao: formacao?.descricao || '',
    entidade: formacao?.entidade || '',
    categoria: formacao?.categoria || '',
    url: formacao?.url || '',
    document_id: formacao?.document_id || '',
    data: formacao?.data || '',
    validade: formacao?.validade || '',
    ativo: formacao?.ativo ?? true,
    visibility: formacao?.visibility || 'socios',
  });

  const mutation = useMutation({
    mutationFn: (payload) => {
      if (isEdit) return formacoesAPI.update(formacao.id, payload);
      return formacoesAPI.create(payload);
    },
    onSuccess: () => {
      toast.success(isEdit ? 'Formação atualizada' : 'Formação criada');
      qc.invalidateQueries({ queryKey: ['formacoes'] });
      onClose();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao guardar'),
  });

  const saving = mutation.isPending;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.titulo.trim()) {
      toast.error('Título é obrigatório');
      return;
    }
    const payload = { ...form };
    // Limpar campos vazios para que update não envie strings vazias.
    Object.keys(payload).forEach((k) => {
      if (payload[k] === '' && k !== 'descricao') delete payload[k];
    });
    // Em edição não se envia o tipo (imutável).
    if (isEdit) delete payload.tipo;
    mutation.mutate(payload);
  };

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-lg rounded-xl p-0 gap-0 max-h-[90vh] overflow-y-auto" data-testid="formacao-modal">
        <DialogHeader className="p-5 border-b border-gray-100 text-left space-y-0">
          <DialogTitle className="font-bold text-grafite text-lg">
            {isEdit ? 'Editar' : 'Nova'} {TIPO_LABELS[form.tipo]}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {!isEdit && (
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Tipo *</label>
              <select
                value={form.tipo}
                onChange={(e) => setForm({ ...form, tipo: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                data-testid="formacao-tipo-select"
              >
                <option value="formacao">Formação</option>
                <option value="certificacao">Certificação</option>
                <option value="material">Material</option>
              </select>
            </div>
          )}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Título *</label>
            <input
              type="text"
              value={form.titulo}
              onChange={(e) => setForm({ ...form, titulo: e.target.value })}
              placeholder="Ex: ICAO English Level 4"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="formacao-titulo-input"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Descrição</label>
            <textarea
              rows={3}
              value={form.descricao}
              onChange={(e) => setForm({ ...form, descricao: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none resize-none"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Entidade</label>
              <input
                type="text"
                value={form.entidade}
                onChange={(e) => setForm({ ...form, entidade: e.target.value })}
                placeholder="Provedor / Entidade"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Categoria</label>
              <input
                type="text"
                value={form.categoria}
                onChange={(e) => setForm({ ...form, categoria: e.target.value })}
                placeholder="Ex: ATC, Segurança"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">URL externo</label>
            <input
              type="url"
              value={form.url}
              onChange={(e) => setForm({ ...form, url: e.target.value })}
              placeholder="https://..."
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Document ID (anexo)</label>
            <input
              type="text"
              value={form.document_id}
              onChange={(e) => setForm({ ...form, document_id: e.target.value })}
              placeholder="ID do documento no módulo de Documentos"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm font-mono focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Data</label>
              <input
                type="date"
                value={form.data}
                onChange={(e) => setForm({ ...form, data: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Validade</label>
              <input
                type="date"
                value={form.validade}
                onChange={(e) => setForm({ ...form, validade: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Visibilidade</label>
            <select
              value={form.visibility}
              onChange={(e) => setForm({ ...form, visibility: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none bg-white"
              data-testid="formacao-visibility-select"
            >
              <option value="socios">Só sócios</option>
              <option value="publico">Público (página da profissão)</option>
            </select>
          </div>
          <label className="inline-flex items-center gap-2 text-sm text-grafite cursor-pointer">
            <input
              type="checkbox"
              checked={form.ativo}
              onChange={(e) => setForm({ ...form, ativo: e.target.checked })}
              className="accent-carmesim"
            />
            Ativo (visível no catálogo)
          </label>
          <button type="submit" disabled={saving} className="w-full btn-primary py-3 text-sm font-semibold">
            {saving ? 'A guardar...' : isEdit ? 'Guardar Alterações' : 'Criar'}
          </button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export const FormacoesPage = () => {
  const { isAdmin, isDirecao } = useAuth();
  const canManage = isAdmin || isDirecao;
  const [filterTipo, setFilterTipo] = useState('');
  const [searchText, setSearchText] = useState('');
  const [editing, setEditing] = useState(null); // { …formacao } | 'new' | null
  const qc = useQueryClient();

  const { data, isLoading: loading } = useQuery({
    queryKey: ['formacoes', { tipo: filterTipo || undefined, ativo: true }],
    queryFn: async () => {
      const params = { ativo: true };
      if (filterTipo) params.tipo = filterTipo;
      const res = await formacoesAPI.getAll(params);
      return res.data;
    },
  });
  const items = data?.items || [];

  const deleteMutation = useMutation({
    mutationFn: (id) => formacoesAPI.delete(id),
    onSuccess: () => {
      toast.success('Formação removida');
      qc.invalidateQueries({ queryKey: ['formacoes'] });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao remover'),
  });

  const filtered = searchText
    ? items.filter((f) => {
        const q = searchText.toLowerCase();
        return f.titulo.toLowerCase().includes(q) || (f.descricao || '').toLowerCase().includes(q);
      })
    : items;

  const tabs = [
    { val: '', label: 'Todos' },
    { val: 'formacao', label: 'Formações' },
    { val: 'certificacao', label: 'Certificações' },
    { val: 'material', label: 'Materiais' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="page-title" data-testid="formacoes-title">Formações & Certificações</h1>
          <p className="page-subtitle">Catálogo de desenvolvimento técnico-profissional (Art. 2.c)</p>
        </div>
        {canManage && (
          <button
            onClick={() => setEditing('new')}
            className="btn-primary flex items-center gap-2 text-sm w-fit"
            data-testid="formacao-new-btn"
          >
            <Plus className="w-4 h-4" /> Nova Entrada
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-1.5 border-b border-gray-200">
        {tabs.map((t) => {
          const active = filterTipo === t.val;
          return (
            <button
              key={t.val}
              onClick={() => setFilterTipo(t.val)}
              data-testid={`formacoes-tab-${t.val || 'all'}`}
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
            data-testid="formacoes-search"
          />
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-2xl" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={GraduationCap}
          title="Sem registos no catálogo"
          description={canManage ? 'Crie a primeira entrada para começar' : 'Aguarde — a Direcção ainda não publicou nada'}
          testId="formacoes-empty"
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((f) => (
            <FormacaoCard
              key={f.id}
              formacao={f}
              canManage={canManage}
              onEdit={() => setEditing(f)}
              onDelete={() => {
                if (window.confirm(`Remover '${f.titulo}'?`)) {
                  deleteMutation.mutate(f.id);
                }
              }}
            />
          ))}
        </div>
      )}

      {editing && (
        <FormacaoModal
          formacao={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  );
};

export default FormacoesPage;
