import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { wallAPI } from '../../utils/api';
import { MessageSquare, Send } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';

export const MuralPage = () => {
  const { user, isAtivo } = useAuth();
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newPost, setNewPost] = useState('');
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    loadPosts();
  }, []);

  const loadPosts = async () => {
    try {
      const response = await wallAPI.getPosts();
      setPosts(response.data);
    } catch (error) {
      console.error('Erro ao carregar posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newPost.trim()) return;

    setPosting(true);
    try {
      await wallAPI.create({ content: newPost });
      toast.success('Post enviado para aprovação!');
      setNewPost('');
      loadPosts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar post');
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-outfit font-bold text-4xl text-primary mb-2" data-testid="wall-title">
          Mural de Comunicação
        </h1>
        <p className="text-slate-600">Compartilhe mensagens com a comunidade ACCTA</p>
      </div>

      {/* Status Alert */}
      {!isAtivo && (
        <div className="card-technical rounded-xl p-6 border-2 border-alert" data-testid="wall-restricted">
          <div className="flex items-start gap-4">
            <MessageSquare className="w-6 h-6 text-alert flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-outfit font-semibold text-lg text-alert mb-2">Acesso Restrito</h3>
              <p className="text-slate-600">
                Apenas sócios com status ativo podem postar no mural. Por favor, regularize sua situação.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Create Post */}
      {isAtivo && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-technical rounded-xl p-6"
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block font-mono text-xs uppercase tracking-widest text-slate-500 mb-2">
                Nova Mensagem
              </label>
              <textarea
                value={newPost}
                onChange={(e) => setNewPost(e.target.value)}
                placeholder="Compartilhe suas ideias, sugestões ou mensagens com a comunidade..."
                rows={4}
                className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-none"
                data-testid="post-textarea"
              />
            </div>

            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-500">
                Sua mensagem será enviada para aprovação antes de ser publicada
              </p>
              <button
                type="submit"
                disabled={!newPost.trim() || posting}
                className="bg-primary text-white hover:bg-primary/90 h-10 px-6 rounded-lg uppercase tracking-wider font-bold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
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
          </form>
        </motion.div>
      )}

      {/* Posts Feed */}
      <div className="space-y-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : posts.length === 0 ? (
          <div className="card-technical rounded-xl p-12 text-center" data-testid="no-posts">
            <p className="text-slate-500">Nenhuma mensagem no mural ainda</p>
          </div>
        ) : (
          posts.map((post, index) => (
            <motion.div
              key={post.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="card-technical rounded-xl p-6"
              data-testid={`wall-post-${post.id}`}
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-accent rounded-full flex items-center justify-center font-outfit font-bold text-primary flex-shrink-0">
                  {post.user_name?.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="font-manrope font-semibold text-primary">{post.user_name}</div>
                      <div className="font-mono text-xs text-slate-500">
                        {format(new Date(post.created_at), "dd 'de' MMMM 'de' yyyy 'às' HH:mm", { locale: ptBR })}
                      </div>
                    </div>
                  </div>
                  <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">{post.content}</p>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
};
