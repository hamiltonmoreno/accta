import React, { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { wallAPI } from '../../utils/api';
import {
  MessageSquare, Send, Heart, MessageCircle, Pin, Trash2,
  CheckCircle, XCircle, Filter, ChevronDown, ChevronUp, Clock
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';

const CATEGORIES = [
  { value: 'todos', label: 'Todos', color: 'bg-gray-100 text-gray-700' },
  { value: 'geral', label: 'Geral', color: 'bg-blue-100 text-blue-700' },
  { value: 'sugestao', label: 'Sugestao', color: 'bg-green-100 text-green-700' },
  { value: 'discussao', label: 'Discussao', color: 'bg-purple-100 text-purple-700' },
  { value: 'aviso', label: 'Aviso', color: 'bg-orange-100 text-orange-700' },
];

const getCategoryStyle = (cat) => {
  const found = CATEGORIES.find(c => c.value === cat);
  return found?.color || 'bg-gray-100 text-gray-700';
};

const getCategoryLabel = (cat) => {
  const found = CATEGORIES.find(c => c.value === cat);
  return found?.label || cat;
};

const CommentSection = ({ postId, commentCount, user }) => {
  const [comments, setComments] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const loadComments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await wallAPI.getComments(postId);
      setComments(res.data);
    } catch (err) {
      console.error('Erro ao carregar comentarios:', err);
    } finally {
      setLoading(false);
    }
  }, [postId]);

  const toggleExpand = () => {
    if (!expanded) loadComments();
    setExpanded(prev => !prev);
  };

  const handleSubmitComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    setSubmitting(true);
    try {
      await wallAPI.createComment(postId, { content: newComment });
      setNewComment('');
      loadComments();
      toast.success('Comentario publicado!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao comentar');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteComment = async (commentId) => {
    try {
      await wallAPI.deleteComment(postId, commentId);
      loadComments();
      toast.success('Comentario removido');
    } catch (err) {
      toast.error('Erro ao remover comentario');
    }
  };

  return (
    <div className="mt-4 border-t border-gray-100 pt-3">
      <button
        onClick={toggleExpand}
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-grafite transition-colors"
        data-testid={`toggle-comments-${postId}`}
      >
        <MessageCircle className="w-4 h-4" />
        <span>{commentCount || 0} comentario{(commentCount || 0) !== 1 ? 's' : ''}</span>
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-3 space-y-3">
              {loading ? (
                <div className="flex justify-center py-3">
                  <div className="w-5 h-5 border-2 border-carmesim border-t-transparent rounded-full animate-spin" />
                </div>
              ) : comments.length === 0 ? (
                <p className="text-sm text-gray-400 py-2">Nenhum comentario ainda. Seja o primeiro!</p>
              ) : (
                comments.map((comment) => (
                  <div key={comment.id} className="flex gap-3 group" data-testid={`comment-${comment.id}`}>
                    <div className="w-8 h-8 bg-grafite/10 rounded-full flex items-center justify-center text-xs font-bold text-grafite flex-shrink-0">
                      {comment.user_name?.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 bg-gray-50 rounded-lg px-3 py-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-grafite">{comment.user_name}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400">
                            {format(new Date(comment.created_at), "dd MMM HH:mm", { locale: ptBR })}
                          </span>
                          {(user?.role === 'admin' || user?.role === 'moderador' || user?.id === comment.user_id) && (
                            <button
                              onClick={() => handleDeleteComment(comment.id)}
                              className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-carmesim transition-all"
                              data-testid={`delete-comment-${comment.id}`}
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{comment.content}</p>
                    </div>
                  </div>
                ))
              )}

              {/* Comment input */}
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
                  data-testid={`comment-submit-${postId}`}
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const PendingPostsPanel = ({ onApproved }) => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  const loadPending = useCallback(async () => {
    try {
      const res = await wallAPI.getPending();
      setPosts(res.data);
    } catch (err) {
      console.error('Erro ao carregar posts pendentes:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadPending(); }, [loadPending]);

  const handleApprove = async (postId) => {
    try {
      await wallAPI.approve(postId);
      toast.success('Post aprovado!');
      loadPending();
      onApproved();
    } catch (err) {
      toast.error('Erro ao aprovar post');
    }
  };

  const handleReject = async (postId) => {
    try {
      await wallAPI.delete(postId);
      toast.success('Post rejeitado e removido');
      loadPending();
    } catch (err) {
      toast.error('Erro ao rejeitar post');
    }
  };

  if (posts.length === 0 && !loading) return null;

  return (
    <div className="card-technical rounded-xl overflow-hidden" data-testid="pending-posts-panel">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 bg-orange-50 hover:bg-orange-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Clock className="w-5 h-5 text-orange-600" />
          <span className="font-semibold text-orange-800">
            {posts.length} post{posts.length !== 1 ? 's' : ''} pendente{posts.length !== 1 ? 's' : ''}
          </span>
        </div>
        {expanded ? <ChevronUp className="w-5 h-5 text-orange-600" /> : <ChevronDown className="w-5 h-5 text-orange-600" />}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 space-y-4">
              {loading ? (
                <div className="flex justify-center py-4">
                  <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : (
                posts.map((post) => (
                  <div key={post.id} className="border border-orange-200 rounded-lg p-4 bg-orange-50/50" data-testid={`pending-post-${post.id}`}>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-orange-200 rounded-full flex items-center justify-center text-sm font-bold text-orange-800">
                          {post.user_name?.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <span className="font-semibold text-sm text-grafite">{post.user_name}</span>
                          <span className="text-xs text-gray-400 ml-2">
                            {format(new Date(post.created_at), "dd MMM HH:mm", { locale: ptBR })}
                          </span>
                        </div>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getCategoryStyle(post.category || 'geral')}`}>
                        {getCategoryLabel(post.category || 'geral')}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mb-3 whitespace-pre-wrap">{post.content}</p>
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={() => handleReject(post.id)}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm text-carmesim border border-carmesim/30 rounded-lg hover:bg-carmesim/10 transition-colors"
                        data-testid={`reject-post-${post.id}`}
                      >
                        <XCircle className="w-4 h-4" /> Rejeitar
                      </button>
                      <button
                        onClick={() => handleApprove(post.id)}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
                        data-testid={`approve-post-${post.id}`}
                      >
                        <CheckCircle className="w-4 h-4" /> Aprovar
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export const MuralPage = () => {
  const { user, isAtivo, isAdmin, isModerador } = useAuth();
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newPost, setNewPost] = useState('');
  const [category, setCategory] = useState('geral');
  const [filterCategory, setFilterCategory] = useState('todos');
  const [posting, setPosting] = useState(false);
  const canModerate = isAdmin || isModerador;

  const loadPosts = useCallback(async () => {
    try {
      const response = await wallAPI.getPosts(filterCategory !== 'todos' ? filterCategory : undefined);
      setPosts(response.data);
    } catch (error) {
      console.error('Erro ao carregar posts:', error);
    } finally {
      setLoading(false);
    }
  }, [filterCategory]);

  useEffect(() => {
    loadPosts();
  }, [loadPosts]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newPost.trim()) return;

    setPosting(true);
    try {
      await wallAPI.create({ content: newPost, category });
      const isAutoApproved = canModerate;
      toast.success(isAutoApproved ? 'Post publicado!' : 'Post enviado para aprovacao!');
      setNewPost('');
      setCategory('geral');
      loadPosts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar post');
    } finally {
      setPosting(false);
    }
  };

  const handleLike = async (postId) => {
    try {
      const res = await wallAPI.like(postId);
      setPosts(prev => prev.map(p =>
        p.id === postId ? {
          ...p,
          likes: res.data.liked
            ? [...(p.likes || []), user.id]
            : (p.likes || []).filter(id => id !== user.id)
        } : p
      ));
    } catch (err) {
      toast.error('Erro ao reagir ao post');
    }
  };

  const handlePin = async (postId) => {
    try {
      const res = await wallAPI.pin(postId);
      toast.success(res.data.message);
      loadPosts();
    } catch (err) {
      toast.error('Erro ao fixar post');
    }
  };

  const handleDelete = async (postId) => {
    if (!window.confirm('Tem certeza que deseja remover este post?')) return;
    try {
      await wallAPI.delete(postId);
      toast.success('Post removido');
      loadPosts();
    } catch (err) {
      toast.error('Erro ao remover post');
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-sans font-bold text-4xl text-grafite mb-2" data-testid="wall-title">
          Mural de Comunicacao
        </h1>
        <p className="text-gray-600">Espaco de partilha e discussao entre associados ACCTA</p>
      </div>

      {/* Status Alert */}
      {!isAtivo && (
        <div className="card-technical rounded-xl p-6 border-2 border-carmesim" data-testid="wall-restricted">
          <div className="flex items-start gap-4">
            <MessageSquare className="w-6 h-6 text-carmesim flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-sans font-semibold text-lg text-carmesim mb-2">Acesso Restrito</h3>
              <p className="text-gray-600">
                Apenas socios com status ativo podem participar no mural. Por favor, regularize sua situacao.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Pending Posts Panel (Admin/Moderator only) */}
      {canModerate && <PendingPostsPanel onApproved={loadPosts} />}

      {/* Create Post */}
      {isAtivo && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-technical rounded-xl p-6"
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block font-mono text-xs uppercase tracking-widest text-gray-500 mb-2">
                Nova Mensagem
              </label>
              <textarea
                value={newPost}
                onChange={(e) => setNewPost(e.target.value)}
                placeholder="Compartilhe suas ideias, sugestoes ou mensagens com a comunidade..."
                rows={4}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-carmesim/50 focus:border-carmesim/50 transition-all resize-none"
                data-testid="post-textarea"
              />
            </div>

            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-500 uppercase tracking-wider font-mono">Categoria:</label>
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
                  <p className="text-xs text-gray-400">Aguarda aprovacao</p>
                )}
                <button
                  type="submit"
                  disabled={!newPost.trim() || posting}
                  className="bg-grafite text-white hover:bg-grafite/90 h-10 px-6 rounded-lg uppercase tracking-wider font-bold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
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
        </motion.div>
      )}

      {/* Filter Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        <Filter className="w-4 h-4 text-gray-400 flex-shrink-0" />
        {CATEGORIES.map(c => (
          <button
            key={c.value}
            onClick={() => setFilterCategory(c.value)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap ${
              filterCategory === c.value
                ? 'bg-grafite text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            data-testid={`filter-${c.value}`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* Posts Feed */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
          </div>
        ) : posts.length === 0 ? (
          <div className="card-technical rounded-xl p-12 text-center" data-testid="no-posts">
            <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">Nenhuma mensagem no mural ainda</p>
            {isAtivo && <p className="text-sm text-gray-400 mt-1">Seja o primeiro a publicar!</p>}
          </div>
        ) : (
          posts.map((post, index) => {
            const isLiked = (post.likes || []).includes(user?.id);
            const likeCount = (post.likes || []).length;

            return (
              <motion.div
                key={post.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`card-technical rounded-xl p-6 ${post.pinned ? 'border-l-4 border-l-carmesim' : ''}`}
                data-testid={`wall-post-${post.id}`}
              >
                {/* Pinned badge */}
                {post.pinned && (
                  <div className="flex items-center gap-1 text-xs text-carmesim font-semibold mb-3">
                    <Pin className="w-3 h-3" /> Fixado
                  </div>
                )}

                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-grafite rounded-full flex items-center justify-center font-sans font-bold text-white flex-shrink-0">
                    {post.user_name?.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-sans font-semibold text-grafite">{post.user_name}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${getCategoryStyle(post.category || 'geral')}`}>
                            {getCategoryLabel(post.category || 'geral')}
                          </span>
                        </div>
                        <div className="font-mono text-xs text-gray-500 mt-0.5">
                          {format(new Date(post.created_at), "dd 'de' MMMM 'de' yyyy 'as' HH:mm", { locale: ptBR })}
                        </div>
                      </div>

                      {/* Admin actions */}
                      {(canModerate || user?.id === post.user_id) && (
                        <div className="flex items-center gap-1">
                          {canModerate && (
                            <button
                              onClick={() => handlePin(post.id)}
                              className={`p-1.5 rounded-lg transition-colors ${post.pinned ? 'text-carmesim bg-carmesim/10' : 'text-gray-400 hover:text-grafite hover:bg-gray-100'}`}
                              title={post.pinned ? 'Desfixar' : 'Fixar'}
                              data-testid={`pin-post-${post.id}`}
                            >
                              <Pin className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(post.id)}
                            className="p-1.5 rounded-lg text-gray-400 hover:text-carmesim hover:bg-carmesim/10 transition-colors"
                            title="Remover"
                            data-testid={`delete-post-${post.id}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>

                    <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{post.content}</p>

                    {/* Actions: Like + Comments */}
                    <div className="flex items-center gap-4 mt-4">
                      <button
                        onClick={() => handleLike(post.id)}
                        className={`flex items-center gap-1.5 text-sm transition-colors ${
                          isLiked ? 'text-carmesim font-semibold' : 'text-gray-500 hover:text-carmesim'
                        }`}
                        data-testid={`like-post-${post.id}`}
                      >
                        <Heart className={`w-4 h-4 ${isLiked ? 'fill-carmesim' : ''}`} />
                        <span>{likeCount > 0 ? likeCount : ''}</span>
                        <span className="hidden sm:inline">{isLiked ? 'Gostei' : 'Gostar'}</span>
                      </button>
                    </div>

                    {/* Comments Section */}
                    <CommentSection
                      postId={post.id}
                      commentCount={post.comment_count || 0}
                      user={user}
                    />
                  </div>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
};
