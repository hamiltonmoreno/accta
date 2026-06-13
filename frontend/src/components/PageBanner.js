import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { bannersAPI } from '../utils/api';
import { queryKeys } from '../lib/queryClient';
import { bannerDefault } from '../lib/bannerDefaults';
import { unsplashSrcSet } from '../utils/unsplash';

/**
 * Banner (hero) padrão das páginas públicas (spec-padronizacao-banners §4.1).
 * Tamanho ÚNICO (h-64 sm:h-72 lg:h-80) — a Home é a exceção e NÃO usa este
 * componente. A imagem vem de GET /api/banners/public por `pageKey`, com
 * fallback embebido se a query falhar (banner nunca fica vazio).
 *
 * Props: pageKey, badge?, title, subtitle?, icon? (LucideIcon).
 */
export const PageBanner = ({ pageKey, badge, title, subtitle, icon: Icon }) => {
  const { data } = useQuery({
    queryKey: queryKeys.banners.public(),
    queryFn: async () => (await bannersAPI.getPublic()).data,
    staleTime: 30 * 60 * 1000, // quase-estático
  });

  const cfg = data?.[pageKey];
  const imageUrl = cfg?.image_url || bannerDefault(pageKey);
  const alt = cfg?.alt || '';
  const isUnsplash = imageUrl.includes('images.unsplash.com');

  return (
    <section className="relative h-64 sm:h-72 lg:h-80 flex items-center overflow-hidden">
      {/* Above-the-fold / provável LCP → eager + fetchPriority alta (nunca lazy). */}
      <img
        src={imageUrl}
        srcSet={isUnsplash ? unsplashSrcSet(imageUrl) : undefined}
        sizes="100vw"
        alt={alt}
        aria-hidden={alt ? undefined : 'true'}
        fetchPriority="high"
        decoding="async"
        className="absolute inset-0 w-full h-full object-cover"
      />
      {/* Overlay grafite — garante contraste do texto branco (nunca vermelho aqui). */}
      <div className="absolute inset-0 bg-gradient-to-r from-grafite via-grafite/85 to-grafite/50" />
      <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-6 w-full">
        <div className="max-w-2xl animate-fade-up">
          {badge && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-carmesim/20 border border-carmesim/40 text-white rounded-full text-xs uppercase tracking-wider font-semibold mb-4">
              {Icon && <Icon className="w-3.5 h-3.5" aria-hidden="true" />}
              {badge}
            </span>
          )}
          <h1 className="font-bold text-3xl sm:text-4xl lg:text-5xl text-white">{title}</h1>
          {subtitle && (
            <p className="mt-3 text-base sm:text-lg text-white/80 leading-relaxed">{subtitle}</p>
          )}
        </div>
      </div>
    </section>
  );
};

export default PageBanner;
