import React, { useEffect, useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { postsAPI, eventsAPI, bannersAPI, mediaUrl } from '../../utils/api';
import { unsplashSrcSet } from '../../utils/unsplash';
import { queryKeys } from '../../lib/queryClient';
import { bannerDefault } from '../../lib/bannerDefaults';
import {
  Plane,
  Shield,
  Users,
  Clock,
  MapPin,
  ArrowRight,
  Radio,
  Eye,
  ChevronRight,
  Calendar,
  Globe,
  TowerControl,
  PlaneLanding,
  Navigation,
  Landmark,
  Building2,
  Search,
  Waves,
  GraduationCap,
  HelpCircle,
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '../../components/ui/accordion';
import { tiposControlo, camadas, fir, caminhoCTA, faq } from '../../content/cta';

const NEWS_IMAGES = [
  'https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=800&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1540962351504-03099e0a754b?q=80&w=800&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1474302770737-173ee21bab63?q=80&w=800&auto=format&fit=crop',
];

// Mapas visuais para as secções educativas (conteúdo em content/cta/).
const CONTROL_ICONS = { TWR: TowerControl, APP: PlaneLanding, ACC: Navigation };

const ATS_ICONS = {
  AAC: Landmark,
  ASA: Radio,
  'Cabo Verde Airports': Building2,
  IPIAAM: Search,
};

// Resumo de uma linha por etapa — o detalhe completo vive em /profissao.
const CAMINHO_RESUMO = {
  'Pré-requisitos': '21 anos, certificado médico Classe 3 e inglês ICAO nível 4.',
  'Formação inicial': 'Curso teórico numa ATO aprovada pela AAC, com exame.',
  'Formação operacional': 'Qualificação (ADI/APP/ACC) com tráfego real sob OJTI.',
  'Ingresso numa unidade': 'Averbamento de órgão e autorização para a posição.',
  'Manutenção': 'Revalidação periódica e recência operacional contínua.',
};

export const HomePage = () => {
  // Imagem do hero editável via config (chave "home"), com fallback embebido
  // (spec-padronizacao-banners §4.2). A Home mantém o seu tamanho próprio.
  const { data: bannerCfg } = useQuery({
    queryKey: queryKeys.banners.public(),
    queryFn: async () => (await bannersAPI.getPublic()).data,
    staleTime: 30 * 60 * 1000,
  });
  const heroImg = bannerCfg?.home?.image_url || bannerDefault('home');
  const heroIsUnsplash = heroImg.includes('images.unsplash.com');

  const [countdown, setCountdown] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });

  // Últimas 3 notícias públicas — pedidas com limit=3 (não cortadas no browser).
  const { data: news = [], isLoading: loadingNews } = useQuery({
    queryKey: queryKeys.posts.list({ visibility: 'publico', status: 'publicado', limit: 3 }),
    queryFn: async () => (await postsAPI.getAll({ visibility: 'publico', status: 'publicado', limit: 3 })).data,
  });

  // Evento em destaque via useQuery (em vez de useState+useEffect+axios). Enquanto
  // carrega, reservamos espaço com um placeholder (ver render) para evitar o salto
  // de layout (CLS) que ocorria quando o evento era inserido após o primeiro paint.
  // queryFn devolve null explícito quando não há evento (RQ não aceita undefined).
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

  const calcCountdown = useCallback((dateStr) => {
    const target = new Date(dateStr).getTime();
    const now = Date.now();
    const diff = Math.max(0, target - now);
    return {
      days: Math.floor(diff / 86400000),
      hours: Math.floor((diff % 86400000) / 3600000),
      minutes: Math.floor((diff % 3600000) / 60000),
      seconds: Math.floor((diff % 60000) / 1000),
    };
  }, []);

  useEffect(() => {
    if (!featuredEvent) return;
    setCountdown(calcCountdown(featuredEvent.date));
    const interval = setInterval(() => {
      setCountdown(calcCountdown(featuredEvent.date));
    }, 1000);
    return () => clearInterval(interval);
  }, [featuredEvent, calcCountdown]);

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative min-h-[600px] sm:min-h-[85vh] lg:min-h-[90vh] flex items-center overflow-hidden">
        <div className="absolute inset-0">
          <img
            src={mediaUrl(heroImg)}
            srcSet={heroIsUnsplash ? unsplashSrcSet(heroImg) : undefined}
            sizes="100vw"
            alt={bannerCfg?.home?.alt || ''}
            aria-hidden={bannerCfg?.home?.alt ? undefined : 'true'}
            className="absolute inset-0 w-full h-full object-cover"
            loading="eager"
            fetchPriority="high"
            decoding="async"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-grafite via-grafite/90 to-grafite/50 sm:from-grafite sm:via-grafite/85 sm:to-grafite/50" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-6 py-16 sm:py-20">
          <div className="max-w-2xl">
            <div className="animate-fade-up">
              <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-carmesim/20 backdrop-blur-sm border border-carmesim/40 rounded-full mb-6 sm:mb-8">
                <span className="w-2 h-2 rounded-full bg-carmesim shrink-0" aria-hidden="true" />
                <span className="text-white font-sans text-xs sm:text-sm uppercase tracking-wider font-semibold">ACCTA · Cabo Verde</span>
              </div>

              <h1 className="font-bold text-3xl sm:text-5xl lg:text-6xl xl:text-7xl text-white leading-tight mb-4 sm:mb-6" data-testid="hero-title">
                O controlo de tráfego aéreo em Cabo Verde.
              </h1>

              <p className="text-base sm:text-xl lg:text-2xl text-white leading-relaxed mb-8 sm:mb-10 max-w-xl [text-shadow:0_1px_3px_rgba(0,0,0,0.4)]">
                Somos os controladores de tráfego aéreo que organizam, comunicam e protegem cada voo na FIR Oceânica do Sal — uma das maiores regiões de informação de voo do Atlântico.
              </p>

              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                <Link
                  to="/profissao"
                  className="group inline-flex items-center justify-center gap-2 bg-floresta text-white px-6 sm:px-8 py-3.5 sm:py-4 rounded-lg font-bold text-sm sm:text-base hover:bg-floresta-dark transition-all shadow-lg shadow-floresta/25"
                  data-testid="hero-cta-primary"
                >
                  Conhecer a profissão
                  <ArrowRight className="w-4 sm:w-5 h-4 sm:h-5 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center gap-2 bg-white/10 backdrop-blur-sm text-white border border-white/30 px-6 sm:px-8 py-3.5 sm:py-4 rounded-lg font-bold text-sm sm:text-base hover:bg-white/20 transition-all"
                  data-testid="hero-cta-secondary"
                >
                  Área do associado
                </Link>
              </div>
            </div>
          </div>
        </div>

      </section>

      {/* Featured Event Countdown — placeholder reserva espaço enquanto carrega
          (evita CLS); colapsa para nada quando não há evento. */}
      {loadingEvent ? (
        <section className="py-8 sm:py-10 bg-white border-b border-gray-100" aria-hidden="true" data-testid="featured-event-skeleton">
          <div className="max-w-7xl mx-auto px-5 sm:px-6">
            <div className="rounded-2xl bg-grafite/5 animate-pulse min-h-[260px] sm:min-h-[220px] lg:min-h-[200px]" />
          </div>
        </section>
      ) : featuredEvent ? (
        <section className="py-8 sm:py-10 bg-white border-b border-gray-100" data-testid="featured-event-section">
          <div className="max-w-7xl mx-auto px-5 sm:px-6">
            <div className="relative overflow-hidden rounded-2xl bg-grafite p-5 sm:p-7 lg:p-8">
              <div className="relative z-10 grid lg:grid-cols-2 gap-8 items-center">
                {/* Event Info */}
                <div>
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-carmesim/20 border border-carmesim/30 rounded-full mb-4 sm:mb-5">
                    <Calendar className="w-3.5 h-3.5 text-white" />
                    <span className="text-xs text-white font-semibold uppercase tracking-wider">Próximo evento</span>
                  </div>
                  <h2 className="font-bold text-2xl sm:text-3xl lg:text-4xl text-white mb-3" data-testid="featured-event-title">
                    {featuredEvent.title}
                  </h2>
                  <p className="text-sm sm:text-base text-white/70 leading-relaxed mb-5 max-w-md">
                    {featuredEvent.description?.slice(0, 150)}{featuredEvent.description?.length > 150 ? '...' : ''}
                  </p>
                  <div className="flex flex-wrap gap-4 text-sm text-white/80">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-4 h-4 text-white/60" />
                      <span>{format(new Date(featuredEvent.date), "dd 'de' MMMM yyyy", { locale: ptBR })}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-4 h-4 text-white/60" />
                      <span>{format(new Date(featuredEvent.date), 'HH:mm')}</span>
                    </div>
                    {featuredEvent.location && (
                      <div className="flex items-center gap-1.5">
                        <MapPin className="w-4 h-4 text-white/60" />
                        <span>{featuredEvent.location}</span>
                      </div>
                    )}
                  </div>
                  {featuredEvent.attendee_count > 0 && (
                    <div className="mt-4 flex items-center gap-2 text-xs text-white/50">
                      <Users className="w-3.5 h-3.5" />
                      <span>{featuredEvent.attendee_count} inscrito{featuredEvent.attendee_count !== 1 ? 's' : ''}</span>
                    </div>
                  )}
                </div>

                {/* Countdown */}
                <div className="flex justify-center lg:justify-end">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4" data-testid="countdown-timer">
                    {[
                      { value: countdown.days, label: 'Dias' },
                      { value: countdown.hours, label: 'Horas' },
                      { value: countdown.minutes, label: 'Min' },
                      { value: countdown.seconds, label: 'Seg' },
                    ].map((unit, i) => (
                      <div key={unit.label}
                        className="flex flex-col items-center animate-fade-up">
                        <div className="w-12 h-12 sm:w-14 sm:h-14 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl flex items-center justify-center mb-2">
                          <span className="font-bold text-xl sm:text-2xl text-white font-mono" data-testid={`countdown-${unit.label.toLowerCase()}`}>
                            {String(unit.value).padStart(2, '0')}
                          </span>
                        </div>
                        <span className="text-xs text-white/50 uppercase tracking-widest font-semibold">{unit.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {/* What We Do Section */}
      <section className="py-16 sm:py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-10 sm:gap-16 items-center">
            <div className="animate-fade-up">
              <span className="inline-block px-3 py-1.5 bg-carmesim/10 text-carmesim rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
                O que é o CTA
              </span>
              <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-grafite mb-4 sm:mb-6">
                Muito além da{' '}
                <span className="text-carmesim">Torre de Controlo</span>
              </h2>
              <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-4 sm:mb-6">
                Quando embarca num avião, vê o piloto e a tripulação. Em terra, há também uma{' '}
                <strong className="text-grafite">equipa que acompanha cada fase do voo</strong> — da partida à chegada.
              </p>
              <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-6 sm:mb-8">
                O Controlador de Tráfego Aéreo (CTA) organiza descolagens e aterragens, mantém a separação entre aeronaves e guia os voos pelas rotas do Atlântico médio.
              </p>
              <Link
                to="/profissao"
                className="inline-flex items-center gap-2 text-carmesim font-semibold hover:text-carmesim-dark transition-colors group text-sm sm:text-base"
              >
                Saiba como funciona o controlo aéreo
                <ChevronRight className="w-4 sm:w-5 h-4 sm:h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:gap-6 animate-fade-up">
              {[
                { icon: Eye, title: 'Vigilância 24h', desc: 'Monitorização constante do espaço aéreo' },
                { icon: Radio, title: 'Comunicação', desc: 'Instruções precisas para cada voo' },
                { icon: Shield, title: 'Segurança', desc: 'Prevenção de incidentes e colisões' },
                { icon: Plane, title: 'Coordenação', desc: 'Gestão de rotas do Atlântico' },
              ].map((item, index) => (
                <div
                  key={index}
                  className="card-technical card-hover p-4 sm:p-6"
                >
                  <div className="w-9 h-9 sm:w-12 sm:h-12 bg-grafite rounded-lg flex items-center justify-center mb-3 sm:mb-4">
                    <item.icon className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
                  </div>
                  <h3 className="font-semibold text-sm sm:text-lg text-grafite mb-1 sm:mb-2">{item.title}</h3>
                  <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* How ATC works — TWR / APP / ACC */}
      <section className="py-16 sm:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="text-center max-w-2xl mx-auto mb-10 sm:mb-16 animate-fade-up">
            <span className="inline-block px-3 py-1.5 bg-carmesim/10 text-carmesim rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
              Como funciona
            </span>
            <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-grafite mb-3 sm:mb-4">
              Três formas de{' '}
              <span className="text-carmesim">controlar o tráfego</span>
            </h2>
            <p className="text-sm sm:text-lg text-gray-600">
              Do solo ao cruzeiro sobre o Atlântico, cada voo passa por diferentes serviços de controlo.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-5 sm:gap-8">
            {tiposControlo.map((t) => {
              const Icon = CONTROL_ICONS[t.sigla] || Radio;
              return (
                <div key={t.sigla} className="card-technical card-hover p-6 sm:p-8 animate-fade-up">
                  <div className="flex items-center gap-3 mb-4 sm:mb-5">
                    <div className="w-12 h-12 sm:w-14 sm:h-14 bg-grafite rounded-xl flex items-center justify-center shrink-0">
                      <Icon className="w-6 h-6 sm:w-7 sm:h-7 text-white" />
                    </div>
                    <span className="font-mono text-2xl sm:text-3xl font-bold text-gray-200">{t.sigla}</span>
                  </div>
                  <h3 className="font-semibold text-lg sm:text-xl text-grafite mb-2 sm:mb-3">{t.nome}</h3>
                  <p className="text-sm text-gray-600 leading-relaxed mb-4">{t.descricao}</p>
                  <div className="pt-4 border-t border-gray-100">
                    <div className="text-xs uppercase tracking-wider text-gray-400 font-semibold mb-1">{t.detalheLabel}</div>
                    <div className="text-sm text-grafite">{t.detalhe}</div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="text-center mt-8 sm:mt-12 animate-fade-up">
            <Link
              to="/profissao"
              className="inline-flex items-center gap-2 text-carmesim font-semibold hover:text-carmesim-dark transition-colors group text-sm sm:text-base"
            >
              Explorar a profissão em detalhe
              <ChevronRight className="w-4 sm:w-5 h-4 sm:h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      {/* ATS structure — the 4 entities */}
      <section className="py-16 sm:py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="text-center max-w-2xl mx-auto mb-10 sm:mb-16 animate-fade-up">
            <span className="inline-block px-3 py-1.5 bg-grafite/5 text-grafite rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
              Estrutura do setor
            </span>
            <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-grafite mb-3 sm:mb-4">
              Quem é quem na{' '}
              <span className="text-carmesim">aviação cabo-verdiana</span>
            </h2>
            <p className="text-sm sm:text-lg text-gray-600">
              Quatro entidades sustentam a navegação aérea do arquipélago — cada uma com um papel distinto.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
            {camadas.map((c) => {
              const Icon = ATS_ICONS[c.sigla] || Building2;
              return (
                <div key={c.sigla} className="card-technical card-hover p-5 sm:p-6 animate-fade-up">
                  <div className="w-11 h-11 sm:w-12 sm:h-12 bg-grafite rounded-lg flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                  </div>
                  <div className="font-bold text-lg text-grafite mb-1 leading-tight">{c.sigla}</div>
                  <div className="text-sm text-gray-600 leading-snug">{c.papel}</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* FIR Oceânica do Sal — dark highlight band */}
      <section className="py-12 sm:py-16 bg-grafite relative overflow-hidden">
        <div className="absolute top-0 right-0 w-72 h-72 bg-carmesim/10 rounded-full blur-3xl -translate-y-1/3 translate-x-1/4" />
        <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            <div className="animate-fade-up">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/10 border border-white/20 rounded-full mb-4 sm:mb-5">
                <Waves className="w-3.5 h-3.5 text-white" />
                <span className="text-xs text-white font-semibold uppercase tracking-wider">Espaço aéreo</span>
              </div>
              <h2 className="font-bold text-2xl sm:text-3xl lg:text-4xl text-white mb-3 sm:mb-4">
                {fir.nome}
              </h2>
              <p className="text-sm sm:text-base text-white/70 leading-relaxed max-w-xl">
                Uma das maiores regiões de informação de voo do Atlântico, operada pela ASA a partir da ilha do Sal.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:gap-4 animate-fade-up">
              {[
                { icon: Globe, label: 'Cobertura', value: 'Atlântico Médio' },
                { icon: Radio, label: 'Comunicações', value: fir.comunicacoes },
                { icon: Navigation, label: 'Vigilância', value: 'Radar + ADS-C' },
                { icon: Plane, label: 'Rotas', value: 'Europa ↔ Américas' },
              ].map((s) => (
                <div key={s.label} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 sm:p-5">
                  <s.icon className="w-5 h-5 text-white/80 mb-2" />
                  <div className="text-xs text-white/50 uppercase tracking-wider mb-0.5">{s.label}</div>
                  <div className="text-sm sm:text-base text-white font-semibold">{s.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Path to become a CTA — 5-step timeline */}
      <section className="py-16 sm:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="text-center max-w-2xl mx-auto mb-10 sm:mb-16 animate-fade-up">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-carmesim/10 text-carmesim rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
              <GraduationCap className="w-3.5 h-3.5" />
              Carreira
            </span>
            <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-grafite mb-3 sm:mb-4">
              O caminho para ser{' '}
              <span className="text-carmesim">Controlador</span>
            </h2>
            <p className="text-sm sm:text-lg text-gray-600">
              Da candidatura à operação real — as cinco etapas do percurso, conforme o CV-CAR.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-5 sm:gap-6">
            {caminhoCTA.map((step, i) => (
              <div key={step.etapa} className="animate-fade-up">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-full bg-grafite text-white font-mono font-bold flex items-center justify-center text-sm shrink-0">
                    {String(i + 1).padStart(2, '0')}
                  </div>
                  {i < caminhoCTA.length - 1 && <div className="hidden lg:block flex-1 h-px bg-gray-200" />}
                </div>
                <h3 className="font-semibold text-base text-grafite mb-1.5">{step.etapa}</h3>
                <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">{CAMINHO_RESUMO[step.etapa]}</p>
              </div>
            ))}
          </div>

          <div className="text-center mt-10 sm:mt-14 animate-fade-up">
            <Link
              to="/profissao"
              className="inline-flex items-center gap-2 text-carmesim font-semibold hover:text-carmesim-dark transition-colors group text-sm sm:text-base"
            >
              Ver requisitos e licenciamento
              <ChevronRight className="w-4 sm:w-5 h-4 sm:h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ — interactive accordion */}
      <section className="py-16 sm:py-24 bg-gray-50">
        <div className="max-w-3xl mx-auto px-5 sm:px-6">
          <div className="text-center mb-10 sm:mb-12 animate-fade-up">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-grafite/5 text-grafite rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
              <HelpCircle className="w-3.5 h-3.5" />
              Perguntas frequentes
            </span>
            <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-grafite mb-3 sm:mb-4">
              Ainda com{' '}
              <span className="text-carmesim">dúvidas?</span>
            </h2>
            <p className="text-sm sm:text-lg text-gray-600">
              As perguntas mais comuns sobre a profissão e o setor em Cabo Verde.
            </p>
          </div>

          <div className="bg-white rounded-2xl border border-gray-200 px-5 sm:px-8 animate-fade-up">
            <Accordion type="single" collapsible className="w-full">
              {faq.slice(0, 6).map((item, i) => (
                <AccordionItem key={i} value={`faq-${i}`} className="border-gray-100 last:border-0">
                  <AccordionTrigger className="text-grafite font-semibold text-sm sm:text-base hover:no-underline py-5 gap-4">
                    {item.pergunta}
                  </AccordionTrigger>
                  <AccordionContent className="text-gray-600 text-sm leading-relaxed">
                    {item.resposta}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>

          <div className="text-center mt-8 animate-fade-up">
            <Link
              to="/profissao"
              className="inline-flex items-center gap-2 text-carmesim font-semibold hover:text-carmesim-dark transition-colors group text-sm sm:text-base"
            >
              Ver tudo sobre a profissão
              <ChevronRight className="w-4 sm:w-5 h-4 sm:h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      {/* News Section */}
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

          {loadingNews ? (
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
                <article key={post.id}
                  className="group animate-fade-up">
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

      {/* CTA Section */}
      <section className="py-16 sm:py-24 bg-grafite relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{ 
            backgroundImage: 'linear-gradient(rgba(199,32,47,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(199,32,47,0.3) 1px, transparent 1px)',
            backgroundSize: '30px 30px'
          }} />
        </div>
        <div className="relative z-10 max-w-4xl mx-auto px-5 sm:px-6 text-center">
          <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-white mb-4 sm:mb-6">
            A ACCTA representa os controladores de tráfego aéreo de Cabo Verde.
          </h2>
          <p className="text-base sm:text-xl text-white/80 mb-8 sm:mb-10">
            Conheça quem somos, o que defendemos e como participamos no setor da navegação aérea.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4">
            <Link
              to="/sobre"
              className="inline-flex items-center justify-center gap-2 bg-floresta text-white px-6 sm:px-8 py-3 sm:py-4 rounded-lg font-bold text-sm sm:text-lg hover:bg-floresta-dark transition-all"
            >
              Conhecer a associação
            </Link>
            <Link
              to="/contactos"
              className="inline-flex items-center justify-center gap-2 bg-white/10 backdrop-blur-sm text-white border border-white/20 px-6 sm:px-8 py-3 sm:py-4 rounded-lg font-bold text-sm sm:text-lg hover:bg-white/20 transition-all"
            >
              Entrar em contacto
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
