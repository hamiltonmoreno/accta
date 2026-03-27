import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Shield, 
  Eye, 
  Users, 
  Star,
  Target,
  Heart,
  Award,
  Globe,
  UserCircle,
  Building,
  Scale,
  ArrowRight
} from 'lucide-react';

export const SobrePage = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="relative py-20 sm:py-28 overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?q=80&w=2070&auto=format&fit=crop"
          alt="Equipa ACCTA"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-grafite via-grafite/85 to-grafite/50" />
        <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-2xl"
          >
            <span className="inline-block px-3 py-1.5 bg-carmesim/20 border border-carmesim/40 text-carmesim rounded-full text-xs uppercase tracking-wider font-semibold mb-5">
              A Associação
            </span>
            <h1 className="font-bold text-3xl sm:text-5xl lg:text-6xl text-white mb-4" data-testid="about-title">
              Quem Somos
            </h1>
            <p className="text-base sm:text-xl text-white/80 max-w-xl leading-relaxed">
              A entidade representativa máxima dos controladores de tráfego aéreo em Cabo Verde
            </p>
          </motion.div>
        </div>
      </section>

      {/* Introduction */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <h2 className="font-sans font-bold text-4xl text-grafite mb-8">
                Unidos pela{' '}
                <span className="text-carmesim">Segurança Aérea</span>
              </h2>
              <div className="space-y-6 text-lg text-gray-600 leading-relaxed">
                <p>
                  A <strong className="text-grafite">Associação dos Controladores de Tráfego Aéreo de Cabo Verde (ACCTA)</strong> é 
                  a entidade representativa máxima da classe no arquipélago. Fundada com o propósito de unir os profissionais que 
                  gerem um dos espaços aéreos mais estratégicos do mundo, a nossa associação atua na defesa dos direitos laborais, 
                  na promoção da excelência técnica e na cooperação com autoridades nacionais e internacionais.
                </p>
                <p>
                  <span className="text-carmesim font-semibold">Não somos apenas uma voz sindical;</span> somos parceiros estratégicos 
                  no desenvolvimento da aviação civil nacional.
                </p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="relative"
            >
              <div className="bg-gradient-to-br from-primary to-primary/80 rounded-2xl p-8 text-white">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 bg-carmesim rounded-xl flex items-center justify-center">
                    <Globe className="w-8 h-8 text-grafite" />
                  </div>
                  <div>
                    <div className="font-sans font-bold text-2xl">FIR Sal</div>
                    <div className="text-white/70">Flight Information Region</div>
                  </div>
                </div>
                <p className="text-white/80 leading-relaxed">
                  Os nossos profissionais gerem a FIR Sal, uma das maiores regiões de informação de voo sobre o Atlântico, 
                  coordenando voos entre a Europa, África e as Américas.
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Mission, Vision, Values */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-carmesim/10 text-carmesim rounded-full text-sm uppercase tracking-wider mb-6">
              Os Nossos Pilares
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite">
              Missão, Visão e Valores
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-16">
            {/* Mission */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="card-technical rounded-2xl p-8 border-l-4 border-accent"
            >
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 bg-carmesim rounded-xl flex items-center justify-center">
                  <Target className="w-7 h-7 text-grafite" />
                </div>
                <h3 className="font-sans font-bold text-2xl text-grafite">Nossa Missão</h3>
              </div>
              <p className="text-gray-600 text-lg leading-relaxed">
                Representar e valorizar os controladores de tráfego aéreo, promovendo a <strong>segurança operacional</strong>, 
                o <strong>desenvolvimento contínuo</strong> e o <strong>bem-estar</strong> dos nossos associados.
              </p>
            </motion.div>

            {/* Vision */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="card-technical rounded-2xl p-8 border-l-4 border-primary"
            >
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 bg-grafite rounded-xl flex items-center justify-center">
                  <Eye className="w-7 h-7 text-carmesim" />
                </div>
                <h3 className="font-sans font-bold text-2xl text-grafite">Nossa Visão</h3>
              </div>
              <p className="text-gray-600 text-lg leading-relaxed">
                Ser reconhecida nacional e internacionalmente como uma organização de referência na gestão associativa e na 
                contribuição técnica para a <strong>segurança da navegação aérea no Atlântico</strong>.
              </p>
            </motion.div>
          </div>

          {/* Values */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { 
                icon: Shield, 
                title: 'Segurança', 
                desc: 'O nosso compromisso inegociável.',
                color: 'bg-red-50 text-red-600'
              },
              { 
                icon: Award, 
                title: 'Excelência', 
                desc: 'Rigor técnico em cada comunicação.',
                color: 'bg-amber-50 text-amber-600'
              },
              { 
                icon: Users, 
                title: 'União', 
                desc: 'A força do coletivo acima do individual.',
                color: 'bg-blue-50 text-blue-600'
              },
              { 
                icon: Star, 
                title: 'Transparência', 
                desc: 'Gestão clara e responsável.',
                color: 'bg-green-50 text-green-600'
              },
            ].map((value, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="card-technical rounded-xl p-6 text-center hover:shadow-lg transition-shadow"
              >
                <div className={`w-16 h-16 ${value.color} rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <value.icon className="w-8 h-8" />
                </div>
                <h4 className="font-sans font-bold text-xl text-grafite mb-2">{value.title}</h4>
                <p className="text-gray-600">{value.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Leadership / Corpos Sociais */}
      <section className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-grafite/5 text-grafite rounded-full text-sm uppercase tracking-wider mb-6">
              Gestão Atual
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
              Corpos Sociais
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Conheça os órgãos que dirigem e fiscalizam a nossa associação
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Assembleia Geral */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="card-technical rounded-2xl p-8"
            >
              <div className="w-16 h-16 bg-grafite rounded-xl flex items-center justify-center mb-6">
                <Building className="w-8 h-8 text-carmesim" />
              </div>
              <h3 className="font-sans font-bold text-2xl text-grafite mb-4">Mesa da Assembleia Geral</h3>
              <p className="text-gray-600 mb-6">
                O órgão deliberativo máximo da associação, responsável pelas decisões estratégicas.
              </p>
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <UserCircle className="w-10 h-10 text-grafite" />
                  <div>
                    <div className="font-semibold text-grafite">Presidente</div>
                    <div className="text-sm text-gray-500">A nomear</div>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Direção */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="card-technical rounded-2xl p-8 border-2 border-accent"
            >
              <div className="w-16 h-16 bg-carmesim rounded-xl flex items-center justify-center mb-6">
                <Users className="w-8 h-8 text-grafite" />
              </div>
              <h3 className="font-sans font-bold text-2xl text-grafite mb-4">Direção</h3>
              <p className="text-gray-600 mb-6">
                Responsável pela gestão executiva e representação da classe perante entidades externas.
              </p>
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-3 bg-carmesim/5 rounded-lg">
                  <UserCircle className="w-10 h-10 text-carmesim" />
                  <div>
                    <div className="font-semibold text-grafite">Presidente</div>
                    <div className="text-sm text-gray-500">A nomear</div>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-carmesim/5 rounded-lg">
                  <UserCircle className="w-10 h-10 text-carmesim" />
                  <div>
                    <div className="font-semibold text-grafite">Vice-Presidente</div>
                    <div className="text-sm text-gray-500">A nomear</div>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Conselho Fiscal */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="card-technical rounded-2xl p-8"
            >
              <div className="w-16 h-16 bg-grafite rounded-xl flex items-center justify-center mb-6">
                <Scale className="w-8 h-8 text-carmesim" />
              </div>
              <h3 className="font-sans font-bold text-2xl text-grafite mb-4">Conselho Fiscal</h3>
              <p className="text-gray-600 mb-6">
                Garante a transparência e o rigor nas contas da associação.
              </p>
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <UserCircle className="w-10 h-10 text-grafite" />
                  <div>
                    <div className="font-semibold text-grafite">Presidente</div>
                    <div className="text-sm text-gray-500">A nomear</div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-grafite">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-sans font-bold text-4xl text-white mb-6">
            Quer saber mais sobre a nossa atuação?
          </h2>
          <p className="text-xl text-white/80 mb-10">
            Consulte os nossos documentos de governança e relatórios de gestão
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/transparencia"
              className="inline-flex items-center gap-2 bg-carmesim text-white px-8 py-4 rounded-lg font-bold text-lg hover:bg-carmesim/90 transition-all"
            >
              Ver Transparência
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/contactos"
              className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white border border-white/20 px-8 py-4 rounded-lg font-bold text-lg hover:bg-white/20 transition-all"
            >
              Fale Conosco
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
