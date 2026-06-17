import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Calendar, ChevronRight } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { mediaUrl } from '../../../utils/api';
import { NEWS_IMAGES } from './tokens';

export const NewsSection = ({ news, loading }) => (
  <section className="py-16 sm:py-24 bg-white">
    <div className="max-w-7xl mx-auto px-5 sm:px-6">
      <div className="text-center mb-10 sm:mb-16">
        <span className="inline-block px-3 py-1.5 bg-grafite/5 text-grafite rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
          Últimas Notícias
        </span>
        <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-grafite mb-3 sm:mb-4">
          Fique por dentro da{' '}
          <span className="text-carmesim">Aviação em CV</span>
        </h2>
        <p className="text-sm sm:text-lg text-gray-600 max-w-2xl mx-auto">
          Acompanhe as novidades da associação e do setor aeronáutico em Cabo Verde
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
        </div>
      ) : news.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-sm">Nenhuma notícia disponível no momento</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
          {news.map((post, index) => (
            <article key={post.id} className="group animate-fade-up">
              <div className="card-technical overflow-hidden hover:shadow-lg transition-all">
                <div className="h-36 sm:h-48 relative overflow-hidden">
                  <img
                    src={mediaUrl(post.cover_url) || NEWS_IMAGES[index % NEWS_IMAGES.length]}
                    alt={post.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                </div>
                <div className="p-4 sm:p-6">
                  <div className="flex items-center gap-2 text-xs text-gray-500 mb-2 sm:mb-3">
                    <Calendar className="w-3.5 h-3.5" />
                    {format(new Date(post.created_at), "dd MMM yyyy", { locale: ptBR })}
                  </div>
                  <h3 className="font-semibold text-base sm:text-lg text-grafite mb-2 sm:mb-3 group-hover:text-carmesim transition-colors">
                    {post.title}
                  </h3>
                  <p className="text-gray-600 text-xs sm:text-sm leading-relaxed mb-3 sm:mb-4 line-clamp-3">{post.excerpt || post.content}</p>
                  <Link
                    to={`/noticias/${post.slug ?? post.id}`}
                    className="inline-flex items-center gap-2 text-xs sm:text-sm text-carmesim font-semibold hover:text-carmesim-dark transition-colors"
                  >
                    Ler mais
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      <div className="text-center mt-8 sm:mt-12">
        <Link
          to="/noticias"
          className="inline-flex items-center gap-2 bg-grafite text-white px-6 sm:px-8 py-3 sm:py-4 rounded-lg font-bold text-sm hover:bg-grafite-dark transition-all"
        >
          Ver Todas as Notícias
          <ArrowRight className="w-4 sm:w-5 h-4 sm:h-5" />
        </Link>
      </div>
    </div>
  </section>
);
