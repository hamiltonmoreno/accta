import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { postsAPI } from '../../utils/api';
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
  Calendar
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const HomePage = () => {
  const [news, setNews] = useState([]);
  const [loadingNews, setLoadingNews] = useState(true);

  useEffect(() => {
    loadNews();
  }, []);

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
      <section className="relative min-h-[85vh] sm:min-h-[90vh] flex items-center overflow-hidden">
        {/* Background Image */}
        <div className="absolute inset-0">
          <img 
            src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=2074&auto=format&fit=crop"
            alt="Aviao voando no ceu"
            className="absolute inset-0 w-full h-full object-cover"
            loading="eager"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-grafite via-grafite/90 to-grafite/50 sm:from-grafite sm:via-grafite/85 sm:to-grafite/50" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-6 py-16 sm:py-20">
          <div className="max-w-2xl">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-carmesim/20 backdrop-blur-sm border border-carmesim/40 rounded-full mb-6 sm:mb-8">
                <Radio className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-carmesim" />
                <span className="text-white font-sans text-xs sm:text-sm uppercase tracking-wider font-semibold">ACCTA Cabo Verde</span>
              </div>

              <h1 className="font-bold text-3xl sm:text-5xl lg:text-6xl xl:text-7xl text-white leading-tight mb-4 sm:mb-6" data-testid="hero-title">
                Os Guardioes{' '}
                <span className="text-carmesim">Invisiveis</span>{' '}
                dos Ceus de Cabo Verde
              </h1>

              <p className="text-base sm:text-xl lg:text-2xl text-white/80 leading-relaxed mb-8 sm:mb-10 max-w-xl">
                24 horas por dia, garantimos a seguranca, a fluidez e a soberania do espaco aereo no meio do Atlantico.{' '}
                <span className="text-carmesim font-semibold">Nos somos a CTA.</span>
              </p>

              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                <Link
                  to="/profissao"
                  className="group inline-flex items-center justify-center gap-2 bg-carmesim text-white px-6 sm:px-8 py-3.5 sm:py-4 rounded-lg font-bold text-sm sm:text-base hover:bg-carmesim-dark transition-all shadow-lg shadow-carmesim/25"
                  data-testid="hero-cta-primary"
                >
                  Conheca a Profissao
                  <ArrowRight className="w-4 sm:w-5 h-4 sm:h-5 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center gap-2 bg-white/10 backdrop-blur-sm text-white border border-white/30 px-6 sm:px-8 py-3.5 sm:py-4 rounded-lg font-bold text-sm sm:text-base hover:bg-white/20 transition-all"
                  data-testid="hero-cta-secondary"
                >
                  Area do Associado
                </Link>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="absolute bottom-6 sm:bottom-8 left-1/2 -translate-x-1/2 hidden sm:block"
        >
          <div className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center">
            <div className="w-1.5 h-3 bg-carmesim rounded-full mt-2 animate-bounce" />
          </div>
        </motion.div>
      </section>

      {/* Stats Bar */}
      <section className="bg-grafite py-6 sm:py-8 border-y border-carmesim/20">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5 sm:gap-8">
            {[
              { icon: Users, value: '+ 60', label: 'Profissionais' },
              { icon: Clock, value: '24/7', label: 'Operacao Ininterrupta' },
              { icon: MapPin, value: '4', label: 'Aeroportos Internacionais' },
              { icon: Target, value: '1', label: 'Missao: Seguranca Total' },
            ].map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="text-center"
              >
                <stat.icon className="w-6 sm:w-8 h-6 sm:h-8 text-carmesim mx-auto mb-2 sm:mb-3" />
                <div className="font-bold text-2xl sm:text-3xl lg:text-4xl text-white mb-0.5">{stat.value}</div>
                <div className="text-[10px] sm:text-xs text-white/50 uppercase tracking-wider">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* What We Do Section */}
      <section className="py-16 sm:py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-10 sm:gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <span className="inline-block px-3 py-1.5 bg-carmesim/10 text-carmesim rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
                O que fazemos
              </span>
              <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-grafite mb-4 sm:mb-6">
                Muito alem da{' '}
                <span className="text-carmesim">Torre de Controlo</span>
              </h2>
              <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-4 sm:mb-6">
                Quando voce embarca num aviao, ve o piloto e a tripulacao. Mas existe uma{' '}
                <strong className="text-grafite">equipa de elite em terra</strong>, monitorizando cada metro do seu voo.
              </p>
              <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-6 sm:mb-8">
                O Controlador de Trafego Aereo (CTA) e o responsavel por evitar colisoes, organizar descolagens e aterragens 
                e guiar aeronaves em seguranca atraves das complexas rotas do Atlantico.
              </p>
              <Link
                to="/profissao"
                className="inline-flex items-center gap-2 text-carmesim font-semibold hover:text-carmesim-dark transition-colors group text-sm sm:text-base"
              >
                Saiba como funciona o controlo aereo
                <ChevronRight className="w-4 sm:w-5 h-4 sm:h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="grid grid-cols-2 gap-3 sm:gap-6"
            >
              {[
                { icon: Eye, title: 'Vigilancia 24h', desc: 'Monitorizacao constante do espaco aereo' },
                { icon: Radio, title: 'Comunicacao', desc: 'Instrucoes precisas para cada voo' },
                { icon: Shield, title: 'Seguranca', desc: 'Prevencao de incidentes e colisoes' },
                { icon: Plane, title: 'Coordenacao', desc: 'Gestao de rotas do Atlantico' },
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
            </motion.div>
          </div>
        </div>
      </section>

      {/* News Section */}
      <section className="py-16 sm:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="text-center mb-10 sm:mb-16">
            <span className="inline-block px-3 py-1.5 bg-grafite/5 text-grafite rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
              Ultimas Noticias
            </span>
            <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-grafite mb-3 sm:mb-4">
              Fique por dentro da{' '}
              <span className="text-carmesim">Aviacao em CV</span>
            </h2>
            <p className="text-sm sm:text-lg text-gray-600 max-w-2xl mx-auto">
              Acompanhe as novidades da associacao e do setor aeronautico em Cabo Verde
            </p>
          </div>

          {loadingNews ? (
            <div className="flex justify-center py-12">
              <div className="w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
            </div>
          ) : news.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 text-sm">Nenhuma noticia disponivel no momento</p>
            </div>
          ) : (
            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
              {news.map((post, index) => (
                <motion.article
                  key={post.id}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  className="group"
                >
                  <div className="card-technical overflow-hidden hover:shadow-lg transition-all">
                    <div className="h-36 sm:h-48 bg-gradient-to-br from-grafite to-grafite-light flex items-center justify-center">
                      <Plane className="w-12 sm:w-16 h-12 sm:h-16 text-carmesim/30" />
                    </div>
                    <div className="p-4 sm:p-6">
                      <div className="flex items-center gap-2 text-[11px] sm:text-xs text-gray-500 mb-2 sm:mb-3">
                        <Calendar className="w-3.5 h-3.5" />
                        {format(new Date(post.created_at), "dd MMM yyyy", { locale: ptBR })}
                      </div>
                      <h3 className="font-semibold text-base sm:text-xl text-grafite mb-2 sm:mb-3 line-clamp-2 group-hover:text-carmesim transition-colors">
                        {post.title}
                      </h3>
                      <p className="text-gray-600 text-xs sm:text-sm line-clamp-3 mb-3 sm:mb-4">{post.content}</p>
                      <Link
                        to="/noticias"
                        className="inline-flex items-center gap-2 text-xs sm:text-sm text-carmesim font-semibold hover:text-carmesim-dark transition-colors"
                      >
                        Ler mais
                        <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                </motion.article>
              ))}
            </div>
          )}

          <div className="text-center mt-8 sm:mt-12">
            <Link
              to="/noticias"
              className="inline-flex items-center gap-2 bg-grafite text-white px-6 sm:px-8 py-3 sm:py-4 rounded-lg font-bold text-sm hover:bg-grafite-dark transition-all"
            >
              Ver Todas as Noticias
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
            <span className="text-carmesim">seguranca dos ceus</span>
          </h2>
          <p className="text-base sm:text-xl text-white/70 mb-8 sm:mb-10">
            A ACCTA representa e valoriza os controladores de trafego aereo de Cabo Verde
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4">
            <Link
              to="/sobre"
              className="inline-flex items-center justify-center gap-2 bg-carmesim text-white px-6 sm:px-8 py-3 sm:py-4 rounded-lg font-bold text-sm sm:text-lg hover:bg-carmesim-dark transition-all"
            >
              Conheca a Associacao
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
