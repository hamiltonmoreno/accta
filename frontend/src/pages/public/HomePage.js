import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { postsAPI, eventsAPI, bannersAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { bannerDefault } from '../../lib/bannerDefaults';

import { HeroSection } from './home/HeroSection';
import { FeaturedEvent } from './home/FeaturedEvent';
import { WhatWeDo } from './home/WhatWeDo';
import { HowATCWorks } from './home/HowATCWorks';
import { AtsStructure } from './home/AtsStructure';
import { FIRSection } from './home/FIRSection';
import { PathSection } from './home/PathSection';
import { FAQSection } from './home/FAQSection';
import { NewsSection } from './home/NewsSection';
import { CTASection } from './home/CTASection';

export const HomePage = () => {
  // Imagem do hero editável via config (chave "home"), com fallback embebido
  // (spec-padronizacao-banners §4.2). A Home mantém o seu tamanho próprio.
  const { data: bannerCfg } = useQuery({
    queryKey: queryKeys.banners.public(),
    queryFn: async () => (await bannersAPI.getPublic()).data,
    staleTime: 30 * 60 * 1000,
  });
  const heroImg = bannerCfg?.home?.image_url || bannerDefault('home');

  // Últimas 3 notícias públicas — pedidas com limit=3 (não cortadas no browser).
  const { data: news = [], isLoading: loadingNews } = useQuery({
    queryKey: queryKeys.posts.list({ visibility: 'publico', status: 'publicado', limit: 3 }),
    queryFn: async () => (await postsAPI.getAll({ visibility: 'publico', status: 'publicado', limit: 3 })).data,
  });

  // Evento em destaque via useQuery (em vez de useState+useEffect+axios). Enquanto
  // carrega, reservamos espaço com um placeholder (FeaturedEvent loading) para
  // evitar o salto de layout (CLS) que ocorria quando o evento era inserido
  // após o primeiro paint. queryFn devolve null explícito quando não há evento
  // (RQ não aceita undefined).
  const { data: featuredEvent, isLoading: loadingEvent } = useQuery({
    queryKey: queryKeys.events.featured(),
    queryFn: async () => {
      try {
        return (await eventsAPI.getFeatured()).data || null;
      } catch {
        return null;
      }
    },
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="min-h-screen">
      <HeroSection heroImg={heroImg} alt={bannerCfg?.home?.alt} />
      <FeaturedEvent event={featuredEvent} loading={loadingEvent} />
      <WhatWeDo />
      <HowATCWorks />
      <AtsStructure />
      <FIRSection />
      <PathSection />
      <FAQSection />
      <NewsSection news={news} loading={loadingNews} />
      <CTASection />
    </div>
  );
};
