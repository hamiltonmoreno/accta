import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Calendar, Tag, Newspaper } from 'lucide-react';
import { postsAPI, mediaUrl } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { EmptyState } from '../../components/EmptyState';
import { PageBanner } from '../../components/PageBanner';
import { useI18n } from '../../i18n';
import { useFormatDate } from '../../i18n/dates';
import { usePageMeta } from '../../i18n/usePageMeta';

const FILTERS = [
  { value: 'all', testId: 'filter-all' },
  { value: 'noticia', testId: 'filter-news' },
  { value: 'institucional', testId: 'filter-institutional' },
  { value: 'educativo', testId: 'filter-educational' },
];

export const NoticiasPage = () => {
  const [filter, setFilter] = useState('all');
  const { t, lp } = useI18n();
  const formatDate = useFormatDate();
  usePageMeta('noticias');
  const typeLabels = t('noticias.types');

  const { data: posts = [], isLoading } = useQuery({
    queryKey: queryKeys.posts.list({ visibility: 'publico', status: 'publicado' }),
    queryFn: async () => (await postsAPI.getAll({ visibility: 'publico', status: 'publicado' })).data,
  });

  const filteredPosts = filter === 'all' ? posts : posts.filter((p) => p.type === filter);

  return (
    <>
      <PageBanner
        pageKey="noticias"
        badge={t('noticias.banner.badge')}
        icon={Newspaper}
        title={t('noticias.banner.title')}
        subtitle={t('noticias.banner.subtitle')}
      />
      <div className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Filters */}
          <div className="flex flex-wrap gap-3 mb-12 justify-center">
            {FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setFilter(f.value)}
                className={`px-6 py-2 rounded-full text-sm font-semibold transition-all cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 ${
                  filter === f.value ? 'bg-grafite text-white' : 'bg-white text-gray-600 hover:bg-gray-100'
                }`}
                data-testid={f.testId}
              >
                {t(`noticias.filters.${f.value}`)}
              </button>
            ))}
          </div>

          {/* Posts Grid */}
          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
            </div>
          ) : filteredPosts.length === 0 ? (
            <EmptyState icon={Newspaper} title={t('noticias.empty')} testId="no-posts" />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {filteredPosts.map((post) => (
                <Link
                  key={post.id}
                  to={lp(`/noticias/${post.slug ?? post.id}`)}
                  className="card-technical rounded-xl overflow-hidden hover:shadow-xl transition-shadow animate-fade-up block focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                  data-testid={`post-${post.id}`}
                >
                  {post.cover_url && (
                    <div className="h-44 overflow-hidden">
                      <img src={mediaUrl(post.cover_url)} alt={post.title} className="w-full h-full object-cover" loading="lazy" />
                    </div>
                  )}
                  <div className="p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <span className="px-3 py-1 bg-[#FBEAEC] text-carmesim rounded-full text-xs uppercase tracking-wider font-semibold">
                        {typeLabels[post.type] || post.type}
                      </span>
                      <span className="flex items-center gap-1 text-xs text-gray-500 font-mono">
                        <Calendar className="w-3 h-3" aria-hidden="true" />
                        {formatDate(new Date(post.published_at || post.created_at), t('noticias.dateFormat'))}
                      </span>
                    </div>

                    <h3 className="font-sans font-semibold text-xl text-grafite mb-3 line-clamp-2">{post.title}</h3>

                    <p className="text-gray-600 line-clamp-3 mb-4">{post.excerpt || post.content}</p>

                    {post.tags && post.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {post.tags.slice(0, 3).map((tag, i) => (
                          <span key={i} className="inline-flex items-center gap-1 text-xs text-gray-500">
                            <Tag className="w-3 h-3" aria-hidden="true" />
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default NoticiasPage;
