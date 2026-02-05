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
      <section className="relative min-h-[90vh] flex items-center overflow-hidden">
        {/* Background with gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary to-[#0A3A5A]">
          {/* Animated radar effect */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px]">
              <div className="absolute inset-0 border border-accent/30 rounded-full animate-ping" style={{ animationDuration: '3s' }} />
              <div className="absolute inset-[100px] border border-accent/20 rounded-full animate-ping" style={{ animationDuration: '3s', animationDelay: '0.5s' }} />
              <div className="absolute inset-[200px] border border-accent/10 rounded-full animate-ping" style={{ animationDuration: '3s', animationDelay: '1s' }} />
            </div>
          </div>
          {/* Grid pattern */}
          <div className="absolute inset-0 opacity-5" style={{ 
            backgroundImage: 'linear-gradient(rgba(0,255,156,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,156,0.3) 1px, transparent 1px)',
            backgroundSize: '50px 50px'
          }} />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-accent/10 border border-accent/30 rounded-full mb-8">
                <Radio className="w-4 h-4 text-accent" />
                <span className="text-accent font-mono text-sm uppercase tracking-wider">ACCTA Cabo Verde</span>
              </div>

              <h1 className="font-outfit font-bold text-5xl lg:text-6xl xl:text-7xl text-white leading-tight mb-6" data-testid="hero-title">
                Os Guardiões{' '}
                <span className="text-accent">Invisíveis</span>{' '}
                dos Céus de Cabo Verde
              </h1>

              <p className="text-xl lg:text-2xl text-white/80 leading-relaxed mb-10 max-w-xl">
                24 horas por dia, garantimos a segurança, a fluidez e a soberania do espaço aéreo no meio do Atlântico.{' '}
                <span className="text-accent font-semibold">Nós somos a CTA.</span>
              </p>

              <div className="flex flex-wrap gap-4">
                <Link
                  to="/profissao"
                  className="group inline-flex items-center gap-3 bg-accent text-primary px-8 py-4 rounded-lg font-bold text-lg hover:bg-accent/90 transition-all"
                  data-testid="hero-cta-primary"
                >
                  Conheça a Profissão
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-3 bg-white/10 backdrop-blur-sm text-white border border-white/20 px-8 py-4 rounded-lg font-bold text-lg hover:bg-white/20 transition-all"
                  data-testid="hero-cta-secondary"
                >
                  Área do Associado
                </Link>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="hidden lg:block"
            >
              <div className="relative">
                {/* Control Tower Illustration */}
                <div className="w-80 h-80 mx-auto bg-gradient-to-b from-accent/20 to-transparent rounded-full flex items-center justify-center">
                  <div className="relative">
                    <Plane className="w-32 h-32 text-accent transform -rotate-45" />
                    <div className="absolute -top-4 -right-4 w-6 h-6 bg-accent rounded-full animate-pulse" />
                    <div className="absolute -bottom-2 -left-6 w-4 h-4 bg-white/50 rounded-full animate-pulse" style={{ animationDelay: '0.5s' }} />
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
        >
          <div className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center">
            <div className="w-1.5 h-3 bg-accent rounded-full mt-2 animate-bounce" />
          </div>
        </motion.div>
      </section>

      {/* Stats Bar */}
      <section className="bg-primary py-8 border-y border-accent/20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { icon: Users, value: '+ 60', label: 'Profissionais' },
              { icon: Clock, value: '24/7', label: 'Operação Ininterrupta' },
              { icon: MapPin, value: '4', label: 'Aeroportos Internacionais' },
              { icon: Target, value: '1', label: 'Missão: Segurança Total' },
            ].map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="text-center"
              >
                <stat.icon className="w-8 h-8 text-accent mx-auto mb-3" />
                <div className="font-outfit font-bold text-3xl lg:text-4xl text-white mb-1">{stat.value}</div>
                <div className="font-mono text-xs text-white/60 uppercase tracking-wider">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* What We Do Section */}
      <section className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <span className="inline-block px-4 py-2 bg-accent/10 text-accent rounded-full font-mono text-sm uppercase tracking-wider mb-6">
                O que fazemos
              </span>
              <h2 className="font-outfit font-bold text-4xl lg:text-5xl text-primary mb-6">
                Muito além da{' '}
                <span className="text-accent">Torre de Controlo</span>
              </h2>
              <p className="text-lg text-slate-600 leading-relaxed mb-6">
                Quando você embarca num avião, vê o piloto e a tripulação. Mas existe uma{' '}
                <strong className="text-primary">equipa de elite em terra</strong>, monitorizando cada metro do seu voo.
              </p>
              <p className="text-lg text-slate-600 leading-relaxed mb-8">
                O Controlador de Tráfego Aéreo (CTA) é o responsável por evitar colisões, organizar descolagens e aterragens 
                e guiar aeronaves em segurança através das complexas rotas do Atlântico.
              </p>
              <Link
                to="/profissao"
                className="inline-flex items-center gap-2 text-primary font-semibold hover:text-accent transition-colors group"
              >
                Saiba como funciona o controlo aéreo
                <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="grid grid-cols-2 gap-6"
            >
              {[
                { icon: Eye, title: 'Vigilância 24h', desc: 'Monitorização constante do espaço aéreo' },
                { icon: Radio, title: 'Comunicação', desc: 'Instruções precisas para cada voo' },
                { icon: Shield, title: 'Segurança', desc: 'Prevenção de incidentes e colisões' },
                { icon: Plane, title: 'Coordenação', desc: 'Gestão de rotas do Atlântico' },
              ].map((item, index) => (
                <div
                  key={index}
                  className="card-technical rounded-xl p-6 hover:shadow-lg transition-shadow"
                >
                  <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center mb-4">
                    <item.icon className="w-6 h-6 text-accent" />
                  </div>
                  <h3 className="font-outfit font-semibold text-lg text-primary mb-2">{item.title}</h3>
                  <p className="text-sm text-slate-600">{item.desc}</p>
                </div>
              ))}
            </motion.div>
          </div>
        </div>
      </section>

      {/* News Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-primary/5 text-primary rounded-full font-mono text-sm uppercase tracking-wider mb-6">
              Últimas Notícias
            </span>
            <h2 className="font-outfit font-bold text-4xl lg:text-5xl text-primary mb-4">
              Fique por dentro da{' '}
              <span className="text-accent">Aviação em CV</span>
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Acompanhe as novidades da associação e do setor aeronáutico em Cabo Verde
            </p>
          </div>

          {loadingNews ? (
            <div className="flex justify-center py-12">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          ) : news.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-slate-500">Nenhuma notícia disponível no momento</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-3 gap-8">
              {news.map((post, index) => (
                <motion.article
                  key={post.id}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  className="group"
                >
                  <div className="card-technical rounded-xl overflow-hidden hover:shadow-xl transition-all">
                    <div className="h-48 bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center">
                      <Plane className="w-16 h-16 text-accent/50" />
                    </div>
                    <div className="p-6">
                      <div className="flex items-center gap-2 text-xs font-mono text-slate-500 mb-3">
                        <Calendar className="w-4 h-4" />
                        {format(new Date(post.created_at), "dd MMM yyyy", { locale: ptBR })}
                      </div>
                      <h3 className="font-outfit font-semibold text-xl text-primary mb-3 line-clamp-2 group-hover:text-accent transition-colors">
                        {post.title}
                      </h3>
                      <p className="text-slate-600 text-sm line-clamp-3 mb-4">{post.content}</p>
                      <Link
                        to="/noticias"
                        className="inline-flex items-center gap-2 text-sm text-primary font-semibold hover:text-accent transition-colors"
                      >
                        Ler mais
                        <ChevronRight className="w-4 h-4" />
                      </Link>
                    </div>
                  </div>
                </motion.article>
              ))}
            </div>
          )}

          <div className="text-center mt-12">
            <Link
              to="/noticias"
              className="inline-flex items-center gap-2 bg-primary text-white px-8 py-4 rounded-lg font-bold hover:bg-primary/90 transition-all"
            >
              Ver Todas as Notícias
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-primary relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{ 
            backgroundImage: 'linear-gradient(rgba(0,255,156,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,156,0.3) 1px, transparent 1px)',
            backgroundSize: '30px 30px'
          }} />
        </div>
        <div className="relative z-10 max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-outfit font-bold text-4xl lg:text-5xl text-white mb-6">
            Junte-se aos profissionais que garantem a{' '}
            <span className="text-accent">segurança dos céus</span>
          </h2>
          <p className="text-xl text-white/80 mb-10">
            A ACCTA representa e valoriza os controladores de tráfego aéreo de Cabo Verde
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/sobre"
              className="inline-flex items-center gap-2 bg-accent text-primary px-8 py-4 rounded-lg font-bold text-lg hover:bg-accent/90 transition-all"
            >
              Conheça a Associação
            </Link>
            <Link
              to="/contactos"
              className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white border border-white/20 px-8 py-4 rounded-lg font-bold text-lg hover:bg-white/20 transition-all"
            >
              Entre em Contacto
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#061525] py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-accent rounded-lg flex items-center justify-center">
                  <Plane className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <div className="font-outfit font-bold text-xl text-white">ACCTA</div>
                  <div className="font-mono text-xs text-accent uppercase tracking-wider">Cabo Verde</div>
                </div>
              </div>
              <p className="text-white/60 leading-relaxed mb-4">
                Associação dos Controladores de Tráfego Aéreo de Cabo Verde
              </p>
              <p className="text-accent font-semibold italic">
                "Segurança no céu, união em terra."
              </p>
            </div>

            <div>
              <h4 className="font-outfit font-semibold text-white mb-4">Links Rápidos</h4>
              <ul className="space-y-3">
                {[
                  { to: '/sobre', label: 'Sobre' },
                  { to: '/profissao', label: 'A Profissão' },
                  { to: '/transparencia', label: 'Transparência' },
                  { to: '/beneficios-publico', label: 'Benefícios' },
                  { to: '/contactos', label: 'Contactos' },
                ].map((link) => (
                  <li key={link.to}>
                    <Link to={link.to} className="text-white/60 hover:text-accent transition-colors">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="font-outfit font-semibold text-white mb-4">Área Reservada</h4>
              <ul className="space-y-3">
                <li>
                  <Link to="/login" className="text-white/60 hover:text-accent transition-colors">
                    Login Associados
                  </Link>
                </li>
                <li>
                  <Link to="/validador" className="text-white/60 hover:text-accent transition-colors">
                    Validador QR
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/10 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-white/40 text-sm">
              © {new Date().getFullYear()} ACCTA - Todos os direitos reservados
            </p>
            <div className="flex gap-6">
              <Link to="/privacidade" className="text-white/40 text-sm hover:text-accent transition-colors">
                Política de Privacidade
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
