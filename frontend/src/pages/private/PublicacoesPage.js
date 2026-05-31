import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { publicacoesAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';
import {
  BookOpen, Plus, Search, FileText, Newspaper, Pencil, Trash2,
  Calendar, Download, Globe, Lock,
} from 'lucide-react';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';

// Cat 5 F2 — espelha PUBLICACAO_TIPOS do backend (models.py).
const TIPO_LABELS = {
  revista: 'Revista',
  boletim: 'Boletim',
  artigo: 'Artigo',
  relatorio_tecnico: 'Relatório Técnico',
};
const TIPO_ICONS = {
  revista: BookOpen,
  boletim: Newspaper,
  artigo: FileText,
  relatorio_tecnico: FileText,
};

const PublicacaoCard = ({ publicacao, canManage, onEdit, onDelete }) => {
  const Icon = TIPO_ICONS[publicacao.tipo] || BookOpen;
  const VisIcon = publicacao.visibility === 'publico' ? Globe : Lock;
  const downloadUrl = publicacao.document_id
    ? `/api/documents/${publicacao.document_id}/download`
    : null;
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl p-5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all duration-200 animate-fade-up flex gap-4"
      data-testid={`publicacao-card-${publicacao.id}`}>
      {publicacao.capa_url ? (
        <img
          src={publicacao.capa_url}
          alt={`Capa de ${publicacao.titulo}`}
          loading="lazy"
          className="w-20 h-28 object-cover rounded-lg border border-gray-200 flex-shrink-0"
        />
      ) : (
        <div className="w-20 h-28 bg-gray-50 rounded-lg border border-gray-200 flex items-center justify-center flex-shrink-0">
          <Icon className="w-8 h-8 text-gray-300" aria-hidden="true" />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-1">
          <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-gray-500">
            <Icon className="w-3 h-3" aria-hidden="true" />
            {TIPO_LABELS[publicacao.tipo]}
          </span>
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
              publicacao.visibility === 'publico'
                ? 'bg-gray-100 text-grafite'
                : 'bg-gray-50 text-gray-600 border border-gray-200'
            }`}
          >
            <VisIcon className="w-3 h-3" />
            {publicacao.visibility === 'publico' ? 'Público' : 'Sócios'}
          </span>
        </div>
        <h3 className="font-semibold text-grafite text-base mb-1 line-clamp-2">{publicacao.titulo}</h3>
        {publicacao.autor && (
          <p className="text-xs text-gray-500 mb-1">por {publicacao.autor}</p>
        )}
        {publicacao.descricao && (
          <p className="text-sm text-gray-600 mb-2 line-clamp-2">{publicacao.descricao}</p>
        )}
        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 mb-2">
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {publicacao.data_publicacao}
          </span>
          {publicacao.a_venda && publicacao.preco != null && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-gray-100 text-grafite border border-gray-200">
              À venda · {Number(publicacao.preco).toLocaleString('pt-PT')} CVE
            </span>
          )}
          {downloadUrl && (
            <a
              href={downloadUrl}
              className="inline-flex items-center gap-1 text-grafite hover:text-carmesim transition-colors font-semibold"
              data-testid={`publicacao-download-${publicacao.id}`}
            >
              <Download className="w-3 h-3" />
              Descarregar
            </a>
          )}
        </div>
        {canManage && (
          <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
            <button
              onClick={onEdit}
              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-lg border border-gray-200 text-grafite hover:bg-gray-50 transition-colors"
              data-testid={`publicacao-edit-${publicacao.id}`}
            >
              <Pencil className="w-3 h-3" /> Editar
            </button>
            <button
              onClick={onDelete}
              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-lg border border-gray-200 text-carmesim hover:bg-[#FDF2F3] transition-colors"
              data-testid={`publicacao-delete-${publicacao.id}`}
            >
              <Trash2 className="w-3 h-3" /> Remover
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const PublicacaoModal = ({ publicacao, onClose }) => {
  const qc = useQueryClient();
  const isEdit = Boolean(publicacao);
  const [form, setForm] = useState({
    titulo: publicacao?.titulo || '',
    descricao: publicacao?.descricao || '',
    tipo: publicacao?.tipo || 'revista',
    autor: publicacao?.autor || '',
    document_id: publicacao?.document_id || '',
    capa_url: publicacao?.capa_url || '',
    data_publicacao: publicacao?.data_publicacao || '',
    visibility: publicacao?.visibility || 'socios',
    a_venda: publicacao?.a_venda || false,
    preco: publicacao?.preco ?? '',
  });

  const mutation = useMutation({
    mutationFn: (payload) => {
      if (isEdit) return publicacoesAPI.update(publicacao.id, payload);
      return publicacoesAPI.create(payload);
    },
    onSuccess: () => {
      toast.success(isEdit ? 'Publicação atualizada' : 'Publicação criada');
      qc.invalidateQueries({ queryKey: ['publicacoes'] });
      onClose();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao guardar'),
  });

  const saving = mutation.isPending;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.titulo.trim()) { toast.error('Título é obrigatório'); return; }
    if (!form.document_id.trim()) { toast.error('Document ID é obrigatório'); return; }
    if (!form.data_publicacao) { toast.error('Data de publicação é obrigatória'); return; }
    // F5: à venda exige preço positivo.
    const precoNum = form.preco === '' ? null : Number(form.preco);
    if (form.a_venda && (!precoNum || precoNum <= 0)) {
      toast.error('Publicação à venda exige um preço positivo (CVE)');
      return;
    }
    const payload = { ...form, preco: precoNum };
    Object.keys(payload).forEach((k) => {
      if (payload[k] === '' && !['titulo', 'document_id', 'data_publicacao'].includes(k)) {
        delete payload[k];
      }
    });
    if (payload.preco === null) delete payload.preco;
    // Em edição não se envia o tipo (imutável).
    if (isEdit) delete payload.tipo;
    mutation.mutate(payload);
  };

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-lg rounded-xl p-0 gap-0 max-h-[90vh] overflow-y-auto" data-testid="publicacao-modal">
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
                data-testid="publicacao-tipo-select"
              >
                <option value="revista">Revista</option>
                <option value="boletim">Boletim</option>
                <option value="artigo">Artigo</option>
                <option value="relatorio_tecnico">Relatório Técnico</option>
              </select>
            </div>
          )}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Título *</label>
            <input
              type="text"
              value={form.titulo}
              onChange={(e) => setForm({ ...form, titulo: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="publicacao-titulo-input"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Autor</label>
            <input
              type="text"
              value={form.autor}
              onChange={(e) => setForm({ ...form, autor: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
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
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Document ID *</label>
            <input
              type="text"
              value={form.document_id}
              onChange={(e) => setForm({ ...form, document_id: e.target.value })}
              placeholder="ID do PDF no módulo de Documentos"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm font-mono focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="publicacao-document-input"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">URL da capa</label>
            <input
              type="url"
              value={form.capa_url}
              onChange={(e) => setForm({ ...form, capa_url: e.target.value })}
              placeholder="https://..."
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Data de publicação *</label>
              <input
                type="date"
                value={form.data_publicacao}
                onChange={(e) => setForm({ ...form, data_publicacao: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                data-testid="publicacao-data-input"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Visibilidade</label>
              <select
                value={form.visibility}
                onChange={(e) => setForm({ ...form, visibility: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                data-testid="publicacao-visibility-select"
              >
                <option value="socios">Sócios</option>
                <option value="publico">Público</option>
              </select>
            </div>
          </div>
          <div className="rounded-lg border border-gray-200 p-3 space-y-3">
            <label className="inline-flex items-center gap-2 text-sm text-grafite cursor-pointer">
              <input
                type="checkbox"
                checked={form.a_venda}
                onChange={(e) => setForm({ ...form, a_venda: e.target.checked })}
                className="accent-carmesim"
                data-testid="publicacao-avenda-check"
              />
              À venda
            </label>
            {form.a_venda && (
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Preço (CVE) *</label>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={form.preco}
                  onChange={(e) => setForm({ ...form, preco: e.target.value })}
                  placeholder="ex.: 1500"
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                  data-testid="publicacao-preco-input"
                />
                <p className="text-[11px] text-gray-500 mt-1.5">
                  Sócios descarregam grátis. Mantenha o documento com visibilidade
                  <strong> Sócios</strong> para que o público não o descarregue sem comprar.
                  A receita externa regista-se no Financeiro (categoria “Venda de Publicações”).
                </p>
              </div>
            )}
          </div>
          <button type="submit" disabled={saving} className="w-full btn-primary py-3 text-sm font-semibold">
            {saving ? 'A guardar...' : isEdit ? 'Guardar Alterações' : 'Publicar'}
          </button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export const PublicacoesPage = () => {
  const { isAdmin, isDirecao } = useAuth();
  const canManage = isAdmin || isDirecao;
  const [filterTipo, setFilterTipo] = useState('');
  const [searchText, setSearchText] = useState('');
  const [editing, setEditing] = useState(null);
  const qc = useQueryClient();

  const { data, isLoading: loading } = useQuery({
    queryKey: ['publicacoes', { tipo: filterTipo || undefined }],
    queryFn: async () => {
      const params = filterTipo ? { tipo: filterTipo } : {};
      const res = await publicacoesAPI.getAll(params);
      return res.data;
    },
  });
  const items = data?.items || [];

  const deleteMutation = useMutation({
    mutationFn: (id) => publicacoesAPI.delete(id),
    onSuccess: () => {
      toast.success('Publicação removida');
      qc.invalidateQueries({ queryKey: ['publicacoes'] });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao remover'),
  });

  const filtered = searchText
    ? items.filter((p) => {
        const q = searchText.toLowerCase();
        return (
          p.titulo.toLowerCase().includes(q) ||
          (p.descricao || '').toLowerCase().includes(q) ||
          (p.autor || '').toLowerCase().includes(q)
        );
      })
    : items;

  const tabs = [
    { val: '', label: 'Todas' },
    { val: 'revista', label: 'Revistas' },
    { val: 'boletim', label: 'Boletins' },
    { val: 'artigo', label: 'Artigos' },
    { val: 'relatorio_tecnico', label: 'Relatórios Técnicos' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="page-title" data-testid="publicacoes-title">Publicações</h1>
          <p className="page-subtitle">Revistas, boletins, artigos e relatórios técnicos da ACCTA (Art. 5.c)</p>
        </div>
        {canManage && (
          <button
            onClick={() => setEditing('new')}
            className="btn-primary flex items-center gap-2 text-sm w-fit"
            data-testid="publicacao-new-btn"
          >
            <Plus className="w-4 h-4" /> Nova Publicação
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
              data-testid={`publicacoes-tab-${t.val || 'all'}`}
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
            data-testid="publicacoes-search"
          />
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-2xl" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="Sem publicações"
          description={canManage ? 'Publique a primeira para começar' : 'Aguarde — a Direcção ainda não publicou nada'}
          testId="publicacoes-empty"
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((p) => (
            <PublicacaoCard
              key={p.id}
              publicacao={p}
              canManage={canManage}
              onEdit={() => setEditing(p)}
              onDelete={() => {
                if (window.confirm(`Remover '${p.titulo}'?`)) {
                  deleteMutation.mutate(p.id);
                }
              }}
            />
          ))}
        </div>
      )}

      {editing && (
        <PublicacaoModal
          publicacao={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  );
};

export default PublicacoesPage;
