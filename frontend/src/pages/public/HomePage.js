import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Plane, ArrowRight, Radio, Shield, Users } from 'lucide-react';

export const HomePage = () => {
  return (
    <div>
      {/* Hero Section */}
      <section className="relative min-h-[80vh] flex items-end">
        {/* Background Image */}
        <div className="absolute inset-0 z-0">
          <img
            src="https://images.unsplash.com/photo-1746129700182-bef672132578?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHwxfHxhaXIlMjB0cmFmZmljJTIwY29udHJvbCUyMHRvd2VyJTIwc3Vuc2V0JTIwYXZpYXRpb258ZW58MHx8fHwxNzcwMTQ3Mjk2fDA&ixlib=rb-4.1.0&q=85"
            alt="Air Traffic Control Tower"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-primary via-primary/60 to-transparent" />
        </div>

        {/* Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 w-full">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="max-w-3xl"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-accent/20 backdrop-blur-sm border border-accent/40 rounded-full mb-6">
              <Radio className="w-4 h-4 text-accent animate-pulse" />
              <span className="font-mono text-xs uppercase tracking-widest text-white">Guardiões Invisíveis</span>
            </div>
            
            <h1 className="font-outfit font-bold text-5xl md:text-6xl lg:text-7xl text-white mb-6 tracking-tight" data-testid="hero-title">
              Controladores de Tráfego Aéreo de Cabo Verde
            </h1>
            
            <p className="text-lg md:text-xl text-white/90 mb-8 leading-relaxed">
              Garantindo a segurança dos céus de Cabo Verde, 24 horas por dia, 7 dias por semana. Conheça a profissão que mantém o tráfego aéreo seguro e eficiente.
            </p>
            
            <div className="flex flex-wrap gap-4">
              <Link
                to="/profissao"
                className="inline-flex items-center gap-2 bg-accent text-primary hover:bg-accent/90 h-12 px-8 rounded-md font-bold shadow-lg shadow-accent/20 transition-all"
                data-testid="cta-about-profession"
              >
                Conheça a Profissão
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to="/validador"
                className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white border border-white/20 hover:bg-white/20 h-12 px-8 rounded-md font-bold transition-all"
                data-testid="cta-validator"
              >
                Validar Carteira
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="font-outfit font-semibold text-4xl md:text-5xl text-primary mb-4">Nossa Missão</h2>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Representar e valorizar os profissionais que garantem a segurança do espaço aéreo cabo-verdiano
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="card-technical rounded-xl p-8 hover:border-accent transition-colors"
          >
            <div className="w-14 h-14 bg-primary rounded-lg flex items-center justify-center mb-6">
              <Shield className="w-7 h-7 text-accent" />
            </div>
            <h3 className="font-outfit font-semibold text-2xl text-primary mb-4">Segurança</h3>
            <p className="text-slate-600 leading-relaxed">
              Promover os mais altos padrões de segurança operacional no controle de tráfego aéreo
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="card-technical rounded-xl p-8 hover:border-accent transition-colors"
          >
            <div className="w-14 h-14 bg-primary rounded-lg flex items-center justify-center mb-6">
              <Users className="w-7 h-7 text-accent" />
            </div>
            <h3 className="font-outfit font-semibold text-2xl text-primary mb-4">Representação</h3>
            <p className="text-slate-600 leading-relaxed">
              Defender os direitos e interesses dos controladores de tráfego aéreo
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
            className="card-technical rounded-xl p-8 hover:border-accent transition-colors"
          >
            <div className="w-14 h-14 bg-primary rounded-lg flex items-center justify-center mb-6">
              <Plane className="w-7 h-7 text-accent" />
            </div>
            <h3 className="font-outfit font-semibold text-2xl text-primary mb-4">Excelência</h3>
            <p className="text-slate-600 leading-relaxed">
              Fomentar o desenvolvimento profissional contínuo e a excelência técnica
            </p>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-primary">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="font-outfit font-semibold text-4xl md:text-5xl text-white mb-6">
            Faça Parte da ACCTA
          </h2>
          <p className="text-lg text-white/80 mb-8 max-w-2xl mx-auto">
            Junte-se à nossa comunidade de profissionais dedicados à excelência no controle de tráfego aéreo
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 bg-accent text-primary hover:bg-accent/90 h-12 px-8 rounded-md font-bold shadow-lg shadow-accent/20 transition-all"
            data-testid="cta-join"
          >
            Acessar Portal
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
};
