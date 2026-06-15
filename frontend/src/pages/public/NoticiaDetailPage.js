import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Calendar, Tag, User, Newspaper } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { postsAPI, mediaUrl } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { EmptyState } from '../../components/EmptyState';

const TYPE_LABELS = { noticia: 'Notícia', institucional: 'Institucional', educativo: 'Educativo' };

export const NoticiaDetailPage = () => {
  const { slug } = useParams();

  const { data: post, isLoading, isError } = useQuery({
    queryKey: queryKeys.posts.detail(slug),
    queryFn: async () => (await postsAPI.getOne(slug)).data,
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="h-64 bg-[#F5F5F5] rounded-xl animate-pulse mb-8" />
        <div className="h-8 w-3/4 bg-[#F5F5F5] rounded animate-pulse mb-4" />
        <div className="space-y-2">
          {[...Array(6)].map((_, i) => <div key={i} className="h-4 bg-[#F5F5F5] rounded animate-pulse" />)}
        </div>
      </div>
    );
  }

  if (isError || !post) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <EmptyState
          icon={Newspaper}
          title="Notícia não encontrada"
          description="O artigo que procura não existe ou já não está disponível."
          testId="noticia-not-found"
          action={
            <Link to="/noticias"
              className="inline-flex items-center gap-2 bg-grafite text-white px-5 py-2.5 rounded-lg font-semibold text-sm hover:bg-grafite-dark transition-colors">
              <ArrowLeft className="w-4 h-4" aria-hidden="true" /> Voltar às notícias
            </Link>
          }
        />
      </div>
    );
  }

  const dateStr = post.published_at || post.created_at;

  return (
    <article className="py-12 sm:py-16">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <Link to="/noticias"
          className="inline-flex items-center gap-2 text-sm text-carmesim font-semibold hover:text-carmesim-dark transition-colors mb-8"
          data-testid="back-to-noticias">
          <ArrowLeft className="w-4 h-4" aria-hidden="true" /> Voltar às notícias
        </Link>

        {post.cover_url && (
          <img
            src={mediaUrl(post.cover_url)}
            alt={post.title}
            className="w-full max-h-[420px] object-cover rounded-xl border border-[#E5E7EB] mb-8"
            loading="eager"
          />
        )}

        <div className="flex flex-wrap items-center gap-3 mb-4">
          <span className="px-3 py-1 bg-[#FBEAEC] text-carmesim rounded-full text-xs font-semibold uppercase tracking-wider">
            {TYPE_LABELS[post.type] || post.type}
          </span>
          {dateStr && (
            <span className="inline-flex items-center gap-1 text-xs text-[#6B7280]">
              <Calendar className="w-3.5 h-3.5" aria-hidden="true" />
              {format(new Date(dateStr), 'dd MMM yyyy', { locale: ptBR })}
            </span>
          )}
          {post.author_name && (
            <span className="inline-flex items-center gap-1 text-xs text-[#6B7280]">
              <User className="w-3.5 h-3.5" aria-hidden="true" /> {post.author_name}
            </span>
          )}
        </div>

        <h1 className="font-bold text-3xl sm:text-4xl text-grafite leading-tight mb-6" data-testid="noticia-title">
          {post.title}
        </h1>

        {post.excerpt && (
          <p className="text-lg text-[#6B7280] leading-relaxed mb-6">{post.excerpt}</p>
        )}

        {/* Conteúdo em texto simples — quebras preservadas, sem HTML (anti-XSS). */}
        <div className="text-grafite leading-relaxed whitespace-pre-wrap text-base" data-testid="noticia-content">
          {post.content}
        </div>

        {post.tags && post.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-10 pt-6 border-t border-[#E5E7EB]">
            {post.tags.map((tag, i) => (
              <span key={i} className="inline-flex items-center gap-1 text-xs text-[#6B7280] bg-[#F5F5F5] px-2.5 py-1 rounded-full">
                <Tag className="w-3 h-3" aria-hidden="true" /> {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </article>
  );
};

export default NoticiaDetailPage;
