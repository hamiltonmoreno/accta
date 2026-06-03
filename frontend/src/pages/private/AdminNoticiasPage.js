import React, { useEffect, useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { postsAPI, uploadAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { queryKeys } from '../../lib/queryClient';
import {
  Newspaper, Plus, Search, Pencil, Trash2, Upload, X, Loader2, Check,
  Eye, FileEdit,
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { Switch } from '../../components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../components/ui/dialog';
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter,
  AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel,
} from '../../components/ui/alert-dialog';

const TYPE_LABELS = { noticia: 'Notícia', institucional: 'Institucional', educativo: 'Educativo' };
const VIS_LABELS = { publico: 'Público', socios: 'Sócios', privado: 'Privado' };

const StatusBadge = ({ status }) =>
  status === 'publicado' ? (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#F0FDF4] text-[#15803D] text-xs font-medium">
      <Eye className="w-3 h-3" aria-hidden="true" /> Publicado
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#FFFBEB] text-[#B45309] text-xs font-medium">
      <FileEdit className="w-3 h-3" aria-hidden="true" /> Rascunho
    </span>
  );

export const AdminNoticiasPage = () => {
  const { isAdmin, isModerador } = useAuth();
  const canManage = isAdmin || isModerador;

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [editing, setEditing] = useState(null); // post a editar, {} = novo, null = fechado
  const [toDelete, setToDelete] = useState(null);

  const params = {
    limit: 100,
    ...(statusFilter !== 'all' && { status: statusFilter }),
    ...(typeFilter !== 'all' && { type: typeFilter }),
    ...(search.trim() && { q: search.trim() }),
  };

  const { data: posts = [], isLoading } = useQuery({
    queryKey: queryKeys.posts.list(params),
    queryFn: async () => (await postsAPI.getAll(params)).data,
    enabled: canManage,
  });

  const qc = useQueryClient();
  const deleteMutation = useMutation({
    mutationFn: (id) => postsAPI.remove(id),
    onSuccess: () => {
      toast.success('Post eliminado.');
      qc.invalidateQueries({ queryKey: queryKeys.posts.all() });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao eliminar o post'),
    onSettled: () => setToDelete(null),
  });

  if (!canManage) {
    return <EmptyState icon={Newspaper} title="Sem permissão para gerir notícias" testId="noticias-no-access" />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="page-title" data-testid="admin-noticias-title">Notícias / Blog</h1>
          <p className="page-subtitle">Crie, edite e publique notícias do portal.</p>
        </div>
        <button
          onClick={() => setEditing({})}
          className="flex items-center gap-2 bg-floresta text-white px-4 py-2 rounded-lg hover:bg-floresta-dark transition-colors text-sm font-semibold cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
          data-testid="new-post-btn"
        >
          <Plus className="w-4 h-4" aria-hidden="true" /> Novo post
        </button>
      </div>

      {/* Filtros */}
      <div className="flex flex-col md:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" aria-hidden="true" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Pesquisar por título…"
            className="w-full pl-10 pr-4 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
            data-testid="noticias-search"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-[#E5E7EB] rounded-md px-3 py-2 text-sm text-grafite focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40"
          data-testid="noticias-filter-status"
        >
          <option value="all">Todos os estados</option>
          <option value="publicado">Publicados</option>
          <option value="rascunho">Rascunhos</option>
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="border border-[#E5E7EB] rounded-md px-3 py-2 text-sm text-grafite focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40"
          data-testid="noticias-filter-type"
        >
          <option value="all">Todos os tipos</option>
          <option value="noticia">Notícia</option>
          <option value="institucional">Institucional</option>
          <option value="educativo">Educativo</option>
        </select>
      </div>

      {/* Lista */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-16 w-full rounded-lg" />)}
        </div>
      ) : posts.length === 0 ? (
        <EmptyState
          icon={Newspaper}
          title="Nenhum post encontrado"
          description='Clique em "Novo post" para criar a primeira notícia.'
          testId="no-posts-admin"
        />
      ) : (
        <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#F5F5F5] text-left text-xs uppercase tracking-wider text-[#6B7280]">
                  <th className="px-4 py-3 font-semibold">Título</th>
                  <th className="px-4 py-3 font-semibold hidden sm:table-cell">Tipo</th>
                  <th className="px-4 py-3 font-semibold hidden md:table-cell">Visibilidade</th>
                  <th className="px-4 py-3 font-semibold">Estado</th>
                  <th className="px-4 py-3 font-semibold hidden lg:table-cell">Data</th>
                  <th className="px-4 py-3 font-semibold text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E7EB]">
                {posts.map((post) => (
                  <tr key={post.id} className="hover:bg-[#F5F5F5]" data-testid={`post-row-${post.id}`}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-grafite line-clamp-1">{post.title}</div>
                      {post.author_name && <div className="text-xs text-[#6B7280]">{post.author_name}</div>}
                    </td>
                    <td className="px-4 py-3 hidden sm:table-cell text-[#6B7280]">{TYPE_LABELS[post.type] || post.type}</td>
                    <td className="px-4 py-3 hidden md:table-cell text-[#6B7280]">{VIS_LABELS[post.visibility] || post.visibility}</td>
                    <td className="px-4 py-3"><StatusBadge status={post.status} /></td>
                    <td className="px-4 py-3 hidden lg:table-cell text-[#6B7280]">
                      {post.created_at ? format(new Date(post.created_at), 'dd MMM yyyy', { locale: ptBR }) : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => setEditing(post)}
                          className="rounded-md text-grafite hover:bg-[#F5F5F5] transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 min-w-[44px] min-h-[44px] inline-flex items-center justify-center"
                          title="Editar"
                          data-testid={`edit-post-${post.id}`}
                        >
                          <Pencil className="w-4 h-4" aria-hidden="true" />
                          <span className="sr-only">Editar</span>
                        </button>
                        <button
                          onClick={() => setToDelete(post)}
                          className="rounded-md text-[#B91C1C] hover:bg-[#FEF2F2] transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 min-w-[44px] min-h-[44px] inline-flex items-center justify-center"
                          title="Eliminar"
                          data-testid={`delete-post-${post.id}`}
                        >
                          <Trash2 className="w-4 h-4" aria-hidden="true" />
                          <span className="sr-only">Eliminar</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {editing !== null && (
        <PostFormModal post={editing} onClose={() => setEditing(null)} />
      )}

      <AlertDialog open={!!toDelete} onOpenChange={(o) => { if (!o) setToDelete(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminar notícia?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação é irreversível. O post “{toDelete?.title}” será removido permanentemente.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteMutation.mutate(toDelete.id)}
              disabled={deleteMutation.isPending}
              className="bg-carmesim text-white hover:bg-carmesim-dark"
              data-testid="confirm-delete-post"
            >
              {deleteMutation.isPending ? 'A eliminar…' : 'Eliminar'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

const PostFormModal = ({ post, onClose }) => {
  const qc = useQueryClient();
  const fileRef = useRef(null);
  const isEdit = !!post?.id;

  const [title, setTitle] = useState(post?.title || '');
  const [type, setType] = useState(post?.type || 'noticia');
  const [visibility, setVisibility] = useState(post?.visibility || 'publico');
  const [status, setStatus] = useState(post?.status || 'publicado');
  const [excerpt, setExcerpt] = useState(post?.excerpt || '');
  const [content, setContent] = useState(post?.content || '');
  const [tags, setTags] = useState((post?.tags || []).join(', '));
  const [coverFile, setCoverFile] = useState(null);
  const [coverPreview, setCoverPreview] = useState(post?.cover_url || null);
  const [notifySocios, setNotifySocios] = useState(false);
  const [regenerateSlug, setRegenerateSlug] = useState(false);

  useEffect(() => () => { if (coverFile && coverPreview?.startsWith('blob:')) URL.revokeObjectURL(coverPreview); },
    [coverFile, coverPreview]);

  const mutation = useMutation({
    mutationFn: async () => {
      let cover_url;
      if (coverFile) {
        const res = await uploadAPI.uploadFile('covers', coverFile);
        cover_url = res.data.file_url;
      }
      const tagList = tags.split(',').map((t) => t.trim()).filter(Boolean);
      if (isEdit) {
        const payload = { title, type, visibility, status, excerpt, content, tags: tagList };
        if (cover_url) payload.cover_url = cover_url;
        if (regenerateSlug && post.status === 'rascunho') payload.regenerate_slug = true;
        await postsAPI.update(post.id, payload);
      } else {
        const payload = {
          title, type, visibility, status, excerpt, content, tags: tagList,
          notify_socios: notifySocios && visibility === 'socios' && status === 'publicado',
        };
        if (cover_url) payload.cover_url = cover_url;
        await postsAPI.create(payload);
      }
    },
    onSuccess: () => {
      toast.success(isEdit ? 'Post atualizado.' : 'Post criado.');
      qc.invalidateQueries({ queryKey: queryKeys.posts.all() });
      if (isEdit) qc.invalidateQueries({ queryKey: queryKeys.posts.detail(post.slug || post.id) });
      onClose();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao guardar o post'),
  });

  const handleFile = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const ext = '.' + f.name.split('.').pop().toLowerCase();
    if (!['.png', '.jpg', '.jpeg'].includes(ext)) {
      toast.error('Use PNG ou JPG para a capa.');
      return;
    }
    if (f.size > 2 * 1024 * 1024) {
      toast.error('Capa muito grande. Máximo 2MB.');
      return;
    }
    setCoverFile(f);
    setCoverPreview(URL.createObjectURL(f));
  };

  const submit = (e) => {
    e.preventDefault();
    if (title.trim().length < 3) { toast.error('O título precisa de pelo menos 3 caracteres.'); return; }
    if (!content.trim()) { toast.error('O conteúdo é obrigatório.'); return; }
    mutation.mutate();
  };

  const showNotify = !isEdit && visibility === 'socios' && status === 'publicado';
  const inputCls = 'w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2';
  const labelCls = 'block text-xs font-medium text-[#6B7280] mb-1';

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-2xl rounded-xl p-0 gap-0 max-h-[90vh] overflow-y-auto" data-testid="post-form-modal">
        <DialogHeader className="p-6 border-b border-[#E5E7EB] text-left space-y-1">
          <DialogTitle className="font-bold text-2xl text-grafite">{isEdit ? 'Editar post' : 'Novo post'}</DialogTitle>
          <DialogDescription className="text-sm text-[#6B7280]">
            {isEdit ? 'Atualize os detalhes da notícia.' : 'Preencha os campos para criar uma notícia.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="p-6 space-y-5">
          <div>
            <label className={labelCls}>Título *</label>
            <input type="text" value={title} maxLength={180} onChange={(e) => setTitle(e.target.value)}
              className={inputCls} placeholder="Ex: Nova rota Praia–Sal" required data-testid="post-title-input" />
          </div>

          <div className="grid sm:grid-cols-3 gap-4">
            <div>
              <label className={labelCls}>Tipo</label>
              <select value={type} onChange={(e) => setType(e.target.value)} className={inputCls} data-testid="post-type-select">
                <option value="noticia">Notícia</option>
                <option value="institucional">Institucional</option>
                <option value="educativo">Educativo</option>
              </select>
            </div>
            <div>
              <label className={labelCls}>Visibilidade</label>
              <select value={visibility} onChange={(e) => setVisibility(e.target.value)} className={inputCls} data-testid="post-visibility-select">
                <option value="publico">Público</option>
                <option value="socios">Sócios</option>
                <option value="privado">Privado</option>
              </select>
            </div>
            <div>
              <label className={labelCls}>Estado</label>
              <select value={status} onChange={(e) => setStatus(e.target.value)} className={inputCls} data-testid="post-status-select">
                <option value="publicado">Publicado</option>
                <option value="rascunho">Rascunho</option>
              </select>
            </div>
          </div>

          <div>
            <label className={labelCls}>Resumo (excerpt)</label>
            <textarea value={excerpt} maxLength={320} rows={2} onChange={(e) => setExcerpt(e.target.value)}
              className={inputCls} placeholder="Frase de chamada apresentada na lista (opcional)." data-testid="post-excerpt-input" />
          </div>

          <div>
            <label className={labelCls}>Conteúdo *</label>
            <textarea value={content} maxLength={20000} rows={8} onChange={(e) => setContent(e.target.value)}
              className={inputCls} placeholder="Texto da notícia. As quebras de linha são preservadas." required data-testid="post-content-input" />
          </div>

          <div>
            <label className={labelCls}>Tags (separadas por vírgula)</label>
            <input type="text" value={tags} onChange={(e) => setTags(e.target.value)}
              className={inputCls} placeholder="Ex: aviação, segurança, 2026" data-testid="post-tags-input" />
          </div>

          {/* Capa */}
          <div>
            <label className={labelCls}>Imagem de capa (PNG/JPG, máx. 2MB)</label>
            <input ref={fileRef} type="file" accept="image/png,image/jpeg" className="hidden" onChange={handleFile} data-testid="post-cover-input" />
            {coverPreview ? (
              <div className="relative w-full h-40 rounded-md overflow-hidden border border-[#E5E7EB]">
                <img src={coverPreview} alt="Pré-visualização da capa" className="w-full h-full object-cover" />
                <button type="button" onClick={() => { setCoverFile(null); setCoverPreview(isEdit ? null : null); }}
                  className="absolute top-2 right-2 p-1.5 rounded-md bg-white/90 hover:bg-white text-grafite cursor-pointer"
                  aria-label="Remover capa selecionada">
                  <X className="w-4 h-4" aria-hidden="true" />
                </button>
                <button type="button" onClick={() => fileRef.current?.click()}
                  className="absolute bottom-2 right-2 inline-flex items-center gap-1 px-2 py-1 rounded-md bg-white/90 hover:bg-white text-grafite text-xs font-medium cursor-pointer">
                  <Upload className="w-3 h-3" aria-hidden="true" /> Trocar
                </button>
              </div>
            ) : (
              <button type="button" onClick={() => fileRef.current?.click()}
                className="w-full inline-flex items-center justify-center gap-2 px-3 py-3 rounded-md border border-dashed border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40"
                data-testid="post-cover-select">
                <Upload className="w-4 h-4" aria-hidden="true" /> Selecionar capa
              </button>
            )}
          </div>

          {/* Regenerar slug — só em rascunhos editados */}
          {isEdit && post.status === 'rascunho' && (
            <label className="flex items-center gap-2 text-sm text-grafite cursor-pointer">
              <input type="checkbox" checked={regenerateSlug} onChange={(e) => setRegenerateSlug(e.target.checked)}
                className="rounded border-[#D1D5DB] text-carmesim focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="post-regenerate-slug" />
              Regenerar o URL (slug) a partir do título
            </label>
          )}

          {/* Notificar sócios (D5) */}
          {showNotify && (
            <div className="flex items-center justify-between rounded-md bg-[#F5F5F5] px-3 py-2.5">
              <span className="text-sm text-grafite">Notificar sócios (notificação no portal)</span>
              <Switch checked={notifySocios} onCheckedChange={setNotifySocios} data-testid="post-notify-socios" />
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} disabled={mutation.isPending}
              className="flex-1 px-4 py-2.5 bg-white border border-[#D1D5DB] text-grafite rounded-md hover:bg-[#F5F5F5] transition-colors font-semibold cursor-pointer disabled:opacity-50">
              Cancelar
            </button>
            <button type="submit" disabled={mutation.isPending}
              className="flex-1 inline-flex items-center justify-center gap-2 bg-floresta text-white px-4 py-2.5 rounded-md hover:bg-floresta-dark transition-colors font-semibold cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
              data-testid="submit-post-btn">
              {mutation.isPending ? <><Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> A guardar…</> : <><Check className="w-4 h-4" aria-hidden="true" /> {isEdit ? 'Guardar' : 'Criar'}</>}
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default AdminNoticiasPage;
