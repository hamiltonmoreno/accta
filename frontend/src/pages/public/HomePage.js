import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { postsAPI, eventsAPI } from '../../utils/api';
import { unsplashSrcSet } from '../../utils/unsplash';
import { 
  Plane, 
  Shield, 
  Users, 
  Clock, 
  MapPin, 
  Target, 
  ArrowRight, 
  Radio,
  Eye,
  ChevronRight,
  Calendar,
  Globe
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const NEWS_IMAGES = [
  'https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=800&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1540962351504-03099e0a754b?q=80&w=800&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1474302770737-173ee21bab63?q=80&w=800&auto=format&fit=crop',
];

export const HomePage = () => {
  const [news, setNews] = useState([]);
  const [loadingNews, setLoadingNews] = useState(true);
  const [featuredEvent, setFeaturedEvent] = useState(null);
  const [countdown, setCountdown] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });

  useEffect(() => {
    loadNews();
    loadFeaturedEvent();
  }, []);

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

  const loadFeaturedEvent = async () => {
    try {
      const res = await eventsAPI.getFeatured();
      if (res.data) setFeaturedEvent(res.data);
    } catch (err) { /* no featured event */ }
  };

  const loadNews = async () => {
    try {
      const response = await postsAPI.getAll('publico');
      setNews(response.data.slice(0, 3));
    } catch (error) {
      console.error('Erro ao carregar notícias:', error);
    } finally {
      setLoadingNews(false);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative min-h-[600px] sm:min-h-[85vh] lg:min-h-[90vh] flex items-center overflow-hidden">
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=1280&auto=format&fit=crop"
            srcSet={unsplashSrcSet('https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&auto=format&fit=crop')}
            sizes="100vw"
            alt=""
            aria-hidden="true"
            className="absolute inset-0 w-full h-full object-cover"
            loading="eager"
            decoding="async"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-grafite via-grafite/90 to-grafite/50 sm:from-grafite sm:via-grafite/85 sm:to-grafite/50" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-6 py-16 sm:py-20">
          <div className="max-w-2xl">
            <div className="animate-fade-up">
              <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-carmesim/20 backdrop-blur-sm border border-carmesim/40 rounded-full mb-6 sm:mb-8">
                <Radio className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-carmesim" />
                <span className="text-white font-sans text-xs sm:text-sm uppercase tracking-wider font-semibold">ACCTA Cabo Verde</span>
              </div>

              <h1 className="font-bold text-3xl sm:text-5xl lg:text-6xl xl:text-7xl text-white leading-tight mb-4 sm:mb-6" data-testid="hero-title">
                Os Guardiões{' '}
                <span className="text-carmesim">Invisíveis</span>{' '}
                dos Céus de Cabo Verde
              </h1>

              <p className="text-base sm:text-xl lg:text-2xl text-white leading-relaxed mb-8 sm:mb-10 max-w-xl" style={{ textShadow: '0 1px 3px rgba(0,0,0,0.4)' }}>
                24 horas por dia, garantimos a segurança, a fluidez e a soberania do espaço aéreo no meio do Atlântico.{' '}
                <span className="text-white font-bold">Nós somos a CTA.</span>
              </p>

              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                <Link
                  to="/profissao"
                  className="group inline-flex items-center justify-center gap-2 bg-carmesim text-white px-6 sm:px-8 py-3.5 sm:py-4 rounded-lg font-bold text-sm sm:text-base hover:bg-carmesim-dark transition-all shadow-lg shadow-carmesim/25"
                  data-testid="hero-cta-primary"
                >
                  Conheça a Profissão
                  <ArrowRight className="w-4 sm:w-5 h-4 sm:h-5 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center gap-2 bg-white/10 backdrop-blur-sm text-white border border-white/30 px-6 sm:px-8 py-3.5 sm:py-4 rounded-lg font-bold text-sm sm:text-base hover:bg-white/20 transition-all"
                  data-testid="hero-cta-secondary"
                >
                  Área do Associado
                </Link>
              </div>
            </div>
          </div>
        </div>

        <div className="absolute bottom-6 sm:bottom-8 left-1/2 -translate-x-1/2 hidden sm:block animate-fade-up">
          <div className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center">
            <div className="w-1.5 h-3 bg-carmesim rounded-full mt-2 animate-bounce" />
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="bg-grafite py-6 sm:py-8 border-y border-carmesim/20">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5 sm:gap-8">
            {[
              { icon: Globe, value: 'FIR', label: 'Oceânica do Sal' },
              { icon: Clock, value: '24/7', label: 'Operação Ininterrupta' },
              { icon: MapPin, value: '4', label: 'Aeroportos Internacionais' },
              { icon: Target, value: '1', label: 'Missão: Segurança Total' },
            ].map((stat, index) => (
              <div key={index}
                className="text-center animate-fade-up">
                <stat.icon className="w-6 sm:w-8 h-6 sm:h-8 text-carmesim mx-auto mb-2 sm:mb-3" />
                <div className="font-bold text-2xl sm:text-3xl lg:text-4xl text-white mb-0.5">{stat.value}</div>
                <div className="text-xs text-white/60 tracking-wider">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Event Countdown */}
      {featuredEvent && (
        <section className="py-12 sm:py-16 bg-white border-b border-gray-100" data-testid="featured-event-section">
          <div className="max-w-7xl mx-auto px-5 sm:px-6">
            <div className="relative overflow-hidden rounded-2xl bg-grafite p-6 sm:p-10 lg:p-12">
              {/* Background pattern */}
              <div className="absolute inset-0 opacity-[0.04]" style={{
                backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)',
                backgroundSize: '24px 24px'
              }} />
              <div className="absolute top-0 right-0 w-64 h-64 bg-carmesim/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3" />

              <div className="relative z-10 grid lg:grid-cols-2 gap-8 items-center">
                {/* Event Info */}
                <div>
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-carmesim/20 border border-carmesim/30 rounded-full mb-4 sm:mb-5">
                    <Calendar className="w-3.5 h-3.5 text-carmesim" />
                    <span className="text-xs text-carmesim font-semibold uppercase tracking-wider">Proximo Evento</span>
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
                  <div className="grid grid-cols-4 gap-3 sm:gap-4" data-testid="countdown-timer">
                    {[
                      { value: countdown.days, label: 'Dias' },
                      { value: countdown.hours, label: 'Horas' },
                      { value: countdown.minutes, label: 'Min' },
                      { value: countdown.seconds, label: 'Seg' },
                    ].map((unit, i) => (
                      <div key={unit.label}
                        className="flex flex-col items-center animate-fade-up">
                        <div className="w-16 h-16 sm:w-20 sm:h-20 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl flex items-center justify-center mb-2">
                          <span className="font-bold text-2xl sm:text-3xl text-white font-mono" data-testid={`countdown-${unit.label.toLowerCase()}`}>
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
      )}

      {/* What We Do Section */}
      <section className="py-16 sm:py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-10 sm:gap-16 items-center">
            <div className="animate-fade-up">
              <span className="inline-block px-3 py-1.5 bg-carmesim/10 text-carmesim rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
                O que fazemos
              </span>
              <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-grafite mb-4 sm:mb-6">
                Muito além da{' '}
                <span className="text-carmesim">Torre de Controlo</span>
              </h2>
              <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-4 sm:mb-6">
                Quando você embarca num avião, vê o piloto e a tripulação. Mas existe uma{' '}
                <strong className="text-grafite">equipa de elite em terra</strong>, monitorizando cada metro do seu voo.
              </p>
              <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-6 sm:mb-8">
                O Controlador de Tráfego Aéreo (CTA) é o responsável por evitar colisões, organizar descolagens e aterragens 
                e guiar aeronaves em segurança através das complexas rotas do Atlântico.
              </p>
              <Link
                to="/profissao"
                className="inline-flex items-center gap-2 text-confianca font-semibold hover:text-confianca-dark transition-colors group text-sm sm:text-base"
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
                    <item.icon className="w-4 h-4 sm:w-6 sm:h-6 text-carmesim" />
                  </div>
                  <h3 className="font-semibold text-sm sm:text-lg text-grafite mb-1 sm:mb-2">{item.title}</h3>
                  <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">{item.desc}</p>
                </div>
              ))}
            </div>
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
                        src={NEWS_IMAGES[index % NEWS_IMAGES.length]}
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
                      <p className="text-gray-600 text-xs sm:text-sm leading-relaxed mb-3 sm:mb-4 line-clamp-3">{post.content}</p>
                      <Link
                        to="/noticias"
                        className="inline-flex items-center gap-2 text-xs sm:text-sm text-confianca font-semibold hover:text-confianca-dark transition-colors"
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
            Junte-se aos profissionais que garantem a{' '}
            <span className="text-carmesim">segurança dos céus</span>
          </h2>
          <p className="text-base sm:text-xl text-white/80 mb-8 sm:mb-10">
            A ACCTA representa e valoriza os controladores de tráfego aéreo de Cabo Verde
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4">
            <Link
              to="/sobre"
              className="inline-flex items-center justify-center gap-2 bg-confianca text-white px-6 sm:px-8 py-3 sm:py-4 rounded-lg font-bold text-sm sm:text-lg hover:bg-confianca-dark transition-all"
            >
              Conheça a Associação
            </Link>
            <Link
              to="/contactos"
              className="inline-flex items-center justify-center gap-2 bg-white/10 backdrop-blur-sm text-white border border-white/20 px-6 sm:px-8 py-3 sm:py-4 rounded-lg font-bold text-sm sm:text-lg hover:bg-white/20 transition-all"
            >
              Entre em Contacto
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
