import React, { useEffect, useState } from 'react';
import { Calendar, Tag } from 'lucide-react';
import { postsAPI } from '../../utils/api';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const NoticiasPage = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadPosts();
  }, []);

  const loadPosts = async () => {
    try {
      const response = await postsAPI.getAll('publico');
      setPosts(response.data);
    } catch (error) {
      console.error('Erro ao carregar notícias:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredPosts = filter === 'all' ? posts : posts.filter(p => p.type === filter);

  return (
    <div className="py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12 animate-fade-up">
          <h1 className="font-sans font-bold text-5xl md:text-6xl text-grafite mb-6" data-testid="news-title">
            Notícias e Atualizações
          </h1>
          <p className="text-xl text-gray-600">
            Acompanhe as últimas novidades da ACCTA e da aviação em Cabo Verde
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-12 justify-center">
          <button
            onClick={() => setFilter('all')}
            className={`px-6 py-2 rounded-full text-sm font-semibold transition-all ${
              filter === 'all'
                ? 'bg-grafite text-white'
                : 'bg-white text-gray-600 hover:bg-gray-100'
            }`}
            data-testid="filter-all"
          >
            Todas
          </button>
          <button
            onClick={() => setFilter('noticia')}
            className={`px-6 py-2 rounded-full text-sm font-semibold transition-all ${
              filter === 'noticia'
                ? 'bg-grafite text-white'
                : 'bg-white text-gray-600 hover:bg-gray-100'
            }`}
            data-testid="filter-news"
          >
            Notícias
          </button>
          <button
            onClick={() => setFilter('institucional')}
            className={`px-6 py-2 rounded-full text-sm font-semibold transition-all ${
              filter === 'institucional'
                ? 'bg-grafite text-white'
                : 'bg-white text-gray-600 hover:bg-gray-100'
            }`}
            data-testid="filter-institutional"
          >
            Institucional
          </button>
          <button
            onClick={() => setFilter('educativo')}
            className={`px-6 py-2 rounded-full text-sm font-semibold transition-all ${
              filter === 'educativo'
                ? 'bg-grafite text-white'
                : 'bg-white text-gray-600 hover:bg-gray-100'
            }`}
            data-testid="filter-educational"
          >
            Educativo
          </button>
        </div>

        {/* Posts Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filteredPosts.length === 0 ? (
          <div className="text-center py-12" data-testid="no-posts">
            <p className="text-gray-500">Nenhuma notícia disponível no momento</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {filteredPosts.map((post, index) => (
              <article key={post.id}
                className="card-technical rounded-xl overflow-hidden hover:shadow-xl transition-shadow animate-fade-up"
                data-testid={`post-${post.id}`}>
                <div className="p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="px-3 py-1 bg-carmesim/10 text-carmesim rounded-full text-xs uppercase tracking-wider">
                      {post.type}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-gray-500 font-mono">
                      <Calendar className="w-3 h-3" />
                      {format(new Date(post.created_at), 'dd MMM yyyy', { locale: ptBR })}
                    </span>
                  </div>
                  
                  <h3 className="font-sans font-semibold text-xl text-grafite mb-3 line-clamp-2">
                    {post.title}
                  </h3>
                  
                  <p className="text-gray-600 line-clamp-3 mb-4">
                    {post.content}
                  </p>
                  
                  {post.tags && post.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {post.tags.slice(0, 3).map((tag, i) => (
                        <span key={i} className="inline-flex items-center gap-1 text-xs text-gray-500">
                          <Tag className="w-3 h-3" />
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
