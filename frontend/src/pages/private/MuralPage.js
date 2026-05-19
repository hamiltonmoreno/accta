import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { wallAPI } from '../../utils/api';
import {
  MessageSquare, Send, Heart, MessageCircle, Pin, Trash2,
  CheckCircle, XCircle, Filter, ChevronDown, ChevronUp, Clock, Search
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { useAuth } from '../../contexts/AuthContext';
import { queryKeys } from '../../lib/queryClient';
import { toast } from 'sonner';
import { EmptyState } from '../../components/EmptyState';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle,
} from '../../components/ui/alert-dialog';

const CATEGORIES = [
  { value: 'todos', label: 'Todos', color: 'bg-[#F5F5F5] text-[#3A3A3A]' },
  { value: 'geral', label: 'Geral', color: 'bg-[#F5F5F5] text-[#3A3A3A]' },
  { value: 'sugestao', label: 'Sugestao', color: 'bg-[#F5F5F5] text-[#3A3A3A]' },
  { value: 'discussao', label: 'Discussao', color: 'bg-[#F5F5F5] text-[#3A3A3A]' },
  { value: 'aviso', label: 'Aviso', color: 'bg-[#FFFBEB] text-[#B45309]' },
];

const getCategoryStyle = (cat) => {
  const found = CATEGORIES.find(c => c.value === cat);
  return found?.color || 'bg-[#F5F5F5] text-[#3A3A3A]';
};

const getCategoryLabel = (cat) => {
  const found = CATEGORIES.find(c => c.value === cat);
  return found?.label || cat;
};

const CommentSection = ({ postId, commentCount, user }) => {
  const qc = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [newComment, setNewComment] = useState('');

  const { data: comments = [], isLoading: loading } = useQuery({
    queryKey: queryKeys.wall.comments(postId),
    queryFn: async () => (await wallAPI.getComments(postId)).data,
    enabled: expanded, // lazy: so carrega quando expandido
  });

  const createMutation = useMutation({
    mutationFn: (content) => wallAPI.createComment(postId, { content }),
    onSuccess: () => {
      setNewComment('');
      qc.invalidateQueries({ queryKey: queryKeys.wall.comments(postId) });
      toast.success('Comentario publicado!');
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Erro ao comentar');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (commentId) => wallAPI.deleteComment(postId, commentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.wall.comments(postId) });
      toast.success('Comentario removido');
    },
    onError: () => toast.error('Erro ao remover comentario'),
  });

  const submitting = createMutation.isPending;

  const handleSubmitComment = (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    createMutation.mutate(newComment);
  };

  return (
    <div className="mt-4 pt-3" style={{ borderTop: '1px solid var(--surface-border)' }}>
      <button
        onClick={() => setExpanded((p) => !p)}
        className="flex items-center gap-2 text-sm transition-colors text-muted-auto"
        data-testid={`toggle-comments-${postId}`}
      >
        <MessageCircle className="w-4 h-4" />
        <span>{commentCount || 0} comentario{(commentCount || 0) !== 1 ? 's' : ''}</span>
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>

      {expanded && (
          <div className="overflow-hidden animate-fade-up">
            <div className="mt-3 space-y-3">
              {loading ? (
                <div className="flex justify-center py-3">
                  <div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
                </div>
              ) : comments.length === 0 ? (
                <p className="text-sm py-2 text-muted-auto">Nenhum comentario ainda. Seja o primeiro!</p>
              ) : (
                comments.map((comment) => (
                  <div key={comment.id} className="flex gap-3 group" data-testid={`comment-${comment.id}`}>
                    <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 text-grafite-auto"
                      style={{ backgroundColor: 'var(--surface-border)' }}>
                      {comment.user_name?.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 rounded-lg px-3 py-2" style={{ backgroundColor: 'var(--surface-card-hover)' }}>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-grafite-auto">{comment.user_name}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-auto">
                            {format(new Date(comment.created_at), "dd MMM HH:mm", { locale: ptBR })}
                          </span>
                          {(user?.role === 'admin' || user?.role === 'moderador' || user?.id === comment.user_id) && (
                            <button
                              onClick={() => deleteMutation.mutate(comment.id)}
                              className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-carmesim transition-all"
                              aria-label="Apagar comentário"
                              data-testid={`delete-comment-${comment.id}`}
                            >
                              <Trash2 className="w-3 h-3" aria-hidden="true" />
                            </button>
                          )}
                        </div>
                      </div>
                      <p className="text-sm mt-1 text-secondary-auto">{comment.content}</p>
                    </div>
                  </div>
                ))
              )}

              <form onSubmit={handleSubmitComment} className="flex gap-2 mt-2">
                <input
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Escreva um comentario..."
                  className="flex-1 text-sm px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-carmesim/50 focus:border-carmesim/50 transition-all"
                  data-testid={`comment-input-${postId}`}
                />
                <button
                  type="submit"
                  disabled={!newComment.trim() || submitting}
                  className="px-3 py-2 bg-grafite text-white rounded-lg text-sm hover:bg-grafite/90 disabled:opacity-50 transition-all"
                  aria-label="Enviar comentário"
                  data-testid={`comment-submit-${postId}`}
                >
                  <Send className="w-4 h-4" aria-hidden="true" />
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
  );
};

const PendingPostsPanel = () => {
  const qc = useQueryClient();
  const [expanded, setExpanded] = useState(false);

  const { data: posts = [], isLoading: loading } = useQuery({
    queryKey: queryKeys.wall.pending(),
    queryFn: async () => (await wallAPI.getPending()).data,
  });

  const approveMutation = useMutation({
    mutationFn: (postId) => wallAPI.approve(postId),
    onSuccess: () => {
      toast.success('Post aprovado!');
      qc.invalidateQueries({ queryKey: queryKeys.wall.pending() });
      // Invalidate todas as listas (qualquer categoria) para o post aprovado aparecer.
      qc.invalidateQueries({ queryKey: ['wall'], predicate: (q) => q.queryKey[1] !== 'pending' });
    },
    onError: () => toast.error('Erro ao aprovar post'),
  });

  const rejectMutation = useMutation({
    mutationFn: (postId) => wallAPI.delete(postId),
    onSuccess: () => {
      toast.success('Post rejeitado e removido');
      qc.invalidateQueries({ queryKey: queryKeys.wall.pending() });
    },
    onError: () => toast.error('Erro ao rejeitar post'),
  });

  if (posts.length === 0 && !loading) return null;

  return (
    <div className="card-technical rounded-xl overflow-hidden" data-testid="pending-posts-panel">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 bg-[#FFFBEB] hover:bg-[#FEF3C7] transition-colors"
      >
        <div className="flex items-center gap-3">
          <Clock className="w-5 h-5 text-[#B45309]" />
          <span className="font-semibold text-[#B45309]">
            {posts.length} post{posts.length !== 1 ? 's' : ''} pendente{posts.length !== 1 ? 's' : ''}
          </span>
        </div>
        {expanded ? <ChevronUp className="w-5 h-5 text-[#B45309]" /> : <ChevronDown className="w-5 h-5 text-[#B45309]" />}
      </button>

      {expanded && (
          <div className="overflow-hidden animate-fade-up">
            <div className="p-4 space-y-4">
              {loading ? (
                <div className="flex justify-center py-4"><div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" /></div>
              ) : (
                posts.map((post) => (
                  <div key={post.id} className="border border-[#FDE68A] rounded-lg p-4 bg-[#FFFBEB]/50" data-testid={`pending-post-${post.id}`}>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-[#FEF3C7] rounded-full flex items-center justify-center text-sm font-bold text-[#B45309]">
                          {post.user_name?.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <span className="font-semibold text-sm text-grafite-auto">{post.user_name}</span>
                          <span className="text-xs ml-2 text-muted-auto">
                            {format(new Date(post.created_at), "dd MMM HH:mm", { locale: ptBR })}
                          </span>
                        </div>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getCategoryStyle(post.category || 'geral')}`}>
                        {getCategoryLabel(post.category || 'geral')}
                      </span>
                    </div>
                    <p className="text-sm mb-3 whitespace-pre-wrap text-secondary-auto">{post.content}</p>
                    <div className="flex gap-2 justify-end">
                      <button onClick={() => rejectMutation.mutate(post.id)}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm text-carmesim border border-carmesim/30 rounded-lg hover:bg-carmesim/10 transition-colors"
                        data-testid={`reject-post-${post.id}`}>
                        <XCircle className="w-4 h-4" /> Rejeitar
                      </button>
                      <button onClick={() => approveMutation.mutate(post.id)}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
                        data-testid={`approve-post-${post.id}`}>
                        <CheckCircle className="w-4 h-4" /> Aprovar
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
  );
};

export const MuralPage = () => {
  const { user, isAtivo, isAdmin, isModerador } = useAuth();
  const qc = useQueryClient();
  const [newPost, setNewPost] = useState('');
  const [category, setCategory] = useState('geral');
  const [filterCategory, setFilterCategory] = useState('todos');
  const [searchText, setSearchText] = useState('');
  const canModerate = isAdmin || isModerador;
  const [confirmDeletePost, setConfirmDeletePost] = useState(null);

  const wallListKey = queryKeys.wall.list(filterCategory !== 'todos' ? filterCategory : undefined);

  const { data: posts = [], isLoading: loading } = useQuery({
    queryKey: wallListKey,
    queryFn: async () => {
      const res = await wallAPI.getPosts(filterCategory !== 'todos' ? filterCategory : undefined);
      return res.data;
    },
  });

  const filteredPosts = searchText
    ? posts.filter((p) =>
        p.content?.toLowerCase().includes(searchText.toLowerCase()) ||
        p.user_name?.toLowerCase().includes(searchText.toLowerCase())
      )
    : posts;

  const createMutation = useMutation({
    mutationFn: (data) => wallAPI.create(data),
    onSuccess: () => {
      const isAutoApproved = canModerate;
      toast.success(isAutoApproved ? 'Post publicado!' : 'Post enviado para aprovacao!');
      setNewPost('');
      setCategory('geral');
      // Auto-approved → invalida lista. Caso contrario, vai para pending.
      if (isAutoApproved) qc.invalidateQueries({ queryKey: ['wall'], predicate: (q) => q.queryKey[1] !== 'pending' });
      else qc.invalidateQueries({ queryKey: queryKeys.wall.pending() });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Erro ao criar post');
    },
  });

  // Optimistic update para like — feedback instantaneo, rollback em caso de erro.
  const likeMutation = useMutation({
    mutationFn: (postId) => wallAPI.like(postId),
    onMutate: async (postId) => {
      await qc.cancelQueries({ queryKey: wallListKey });
      const previous = qc.getQueryData(wallListKey);
      qc.setQueryData(wallListKey, (old = []) =>
        old.map((p) => {
          if (p.id !== postId) return p;
          const isLiked = (p.likes || []).includes(user.id);
          return {
            ...p,
            likes: isLiked
              ? (p.likes || []).filter((id) => id !== user.id)
              : [...(p.likes || []), user.id],
          };
        }),
      );
      return { previous };
    },
    onError: (_err, _postId, context) => {
      if (context?.previous) qc.setQueryData(wallListKey, context.previous);
      toast.error('Erro ao reagir ao post');
    },
  });

  const pinMutation = useMutation({
    mutationFn: (postId) => wallAPI.pin(postId),
    onSuccess: (res) => {
      toast.success(res.data.message);
      qc.invalidateQueries({ queryKey: ['wall'], predicate: (q) => q.queryKey[1] !== 'pending' });
    },
    onError: () => toast.error('Erro ao fixar post'),
  });

  const deleteMutation = useMutation({
    mutationFn: (postId) => wallAPI.delete(postId),
    onSuccess: () => {
      toast.success('Post removido');
      qc.invalidateQueries({ queryKey: ['wall'], predicate: (q) => q.queryKey[1] !== 'pending' });
    },
    onError: () => toast.error('Erro ao remover post'),
  });

  const posting = createMutation.isPending;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!newPost.trim()) return;
    createMutation.mutate({ content: newPost, category });
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="page-title" data-testid="wall-title">Mural de Comunicacao</h1>
        <p className="page-subtitle">Espaco de partilha e discussao entre associados ACCTA</p>
      </div>

      {/* Status Alert */}
      {!isAtivo && (
        <div className="card-technical rounded-xl p-6 border-2 border-carmesim" data-testid="wall-restricted">
          <div className="flex items-start gap-4">
            <MessageSquare className="w-6 h-6 text-carmesim flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-lg text-carmesim mb-2">Acesso Restrito</h3>
              <p className="text-secondary-auto">
                Apenas socios com status ativo podem participar no mural. Por favor, regularize a sua situacao.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Pending Posts Panel */}
      {canModerate && <PendingPostsPanel />}

      {/* Create Post */}
      {isAtivo && (
        <div className="card-technical rounded-xl p-5 sm:p-6 animate-fade-up">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block font-mono text-xs uppercase tracking-widest mb-2 text-muted-auto">
                Nova Mensagem
              </label>
              <textarea
                value={newPost}
                onChange={(e) => setNewPost(e.target.value)}
                placeholder="Compartilhe as suas ideias, sugestoes ou mensagens com a comunidade..."
                rows={4}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-carmesim/50 focus:border-carmesim/50 transition-all resize-none"
                data-testid="post-textarea"
              />
            </div>

            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <label className="text-xs uppercase tracking-wider font-mono text-muted-auto">Categoria:</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-carmesim/50"
                  data-testid="post-category-select"
                >
                  {CATEGORIES.filter(c => c.value !== 'todos').map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-3">
                {!canModerate && (
                  <p className="text-xs text-muted-auto">Aguarda aprovacao</p>
                )}
                <button
                  type="submit"
                  disabled={!newPost.trim() || posting}
                  className="btn-primary flex items-center gap-2"
                  data-testid="post-submit"
                >
                  {posting ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Publicar
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Search + Filter Bar */}
      <div className="space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-auto" />
          <input
            type="text"
            placeholder="Pesquisar no mural..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="w-full pl-9 pr-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim outline-none"
            data-testid="mural-search-input"
          />
        </div>
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          <Filter className="w-4 h-4 flex-shrink-0 text-muted-auto" />
          {CATEGORIES.map(c => (
            <button
              key={c.value}
              onClick={() => setFilterCategory(c.value)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap ${
                filterCategory === c.value
                  ? 'bg-grafite text-white'
                  : 'btn-outline !h-auto !px-3 !py-1.5 !rounded-full !text-xs'
              }`}
              data-testid={`filter-${c.value}`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* Posts Feed */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filteredPosts.length === 0 ? (
          <EmptyState
            icon={MessageSquare}
            title={searchText ? 'Nenhum resultado encontrado' : 'Nenhuma mensagem no mural ainda'}
            description={isAtivo && !searchText ? 'Seja o primeiro a publicar!' : undefined}
            testId="no-posts"
          />
        ) : (
          filteredPosts.map((post, index) => {
            const isLiked = (post.likes || []).includes(user?.id);
            const likeCount = (post.likes || []).length;

            return (
              <div key={post.id}
                className={`card-technical rounded-xl p-5 sm:p-6 ${post.pinned ? 'border-l-4 border-l-carmesim' : ''} animate-fade-up`}
                data-testid={`wall-post-${post.id}`}>
                {post.pinned && (
                  <div className="flex items-center gap-1 text-xs text-carmesim font-semibold mb-3">
                    <Pin className="w-3 h-3" /> Fixado
                  </div>
                )}

                <div className="flex items-start gap-3 sm:gap-4">
                  <div className="w-10 h-10 sm:w-12 sm:h-12 bg-carmesim rounded-full flex items-center justify-center font-bold text-white flex-shrink-0 text-sm sm:text-base">
                    {post.user_name?.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-grafite-auto">{post.user_name}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${getCategoryStyle(post.category || 'geral')}`}>
                            {getCategoryLabel(post.category || 'geral')}
                          </span>
                        </div>
                        <div className="font-mono text-xs mt-0.5 text-muted-auto">
                          {format(new Date(post.created_at), "dd 'de' MMMM 'de' yyyy 'as' HH:mm", { locale: ptBR })}
                        </div>
                      </div>

                      {(canModerate || user?.id === post.user_id) && (
                        <div className="flex items-center gap-1">
                          {canModerate && (
                            <button
                              onClick={() => pinMutation.mutate(post.id)}
                              className={`p-1.5 rounded-lg transition-colors ${post.pinned ? 'text-carmesim bg-carmesim/10' : 'text-gray-400 hover:text-carmesim hover:bg-carmesim/10'}`}
                              title={post.pinned ? 'Desfixar' : 'Fixar'}
                              aria-label={post.pinned ? 'Desfixar post' : 'Fixar post'}
                              data-testid={`pin-post-${post.id}`}
                            >
                              <Pin className="w-4 h-4" aria-hidden="true" />
                            </button>
                          )}
                          <button
                            onClick={() => setConfirmDeletePost(post.id)}
                            className="p-1.5 rounded-lg text-gray-400 hover:text-carmesim hover:bg-carmesim/10 transition-colors"
                            title="Remover"
                            aria-label="Apagar post"
                            data-testid={`delete-post-${post.id}`}
                          >
                            <Trash2 className="w-4 h-4" aria-hidden="true" />
                          </button>
                        </div>
                      )}
                    </div>

                    <p className="leading-relaxed whitespace-pre-wrap text-secondary-auto">{post.content}</p>

                    <div className="flex items-center gap-4 mt-4">
                      <button
                        onClick={() => likeMutation.mutate(post.id)}
                        className={`flex items-center gap-1.5 text-sm transition-colors ${
                          isLiked ? 'text-carmesim font-semibold' : 'hover:text-carmesim text-muted-auto'
                        }`}
                        data-testid={`like-post-${post.id}`}
                      >
                        <Heart className={`w-4 h-4 ${isLiked ? 'fill-carmesim' : ''}`} />
                        <span>{likeCount > 0 ? likeCount : ''}</span>
                        <span className="hidden sm:inline">{isLiked ? 'Gostei' : 'Gostar'}</span>
                      </button>
                    </div>

                    <CommentSection postId={post.id} commentCount={post.comment_count || 0} user={user} />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      <AlertDialog open={!!confirmDeletePost} onOpenChange={(open) => !open && setConfirmDeletePost(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover post</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja remover este post? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              onClick={() => { deleteMutation.mutate(confirmDeletePost); setConfirmDeletePost(null); }}
            >
              Remover
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
