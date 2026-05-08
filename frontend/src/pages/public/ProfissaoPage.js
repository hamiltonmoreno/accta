import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Radio, 
  Eye, 
  Globe, 
  Plane, 
  Building2, 
  Radar,
  GraduationCap,
  Brain,
  Languages,
  Heart,
  ArrowRight,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

export const ProfissaoPage = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="relative py-20 sm:py-28 overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1540962351504-03099e0a754b?q=80&w=2070&auto=format&fit=crop"
          alt=""
          aria-hidden="true"
          loading="lazy"
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
              Educativo
            </span>
            <h1 className="font-bold text-3xl sm:text-5xl lg:text-6xl text-white mb-4" data-testid="profession-title">
              O que é ser um{' '}
              <span className="text-carmesim">Controlador de Tráfego Aéreo?</span>
            </h1>
            <p className="text-base sm:text-xl text-white/80 max-w-xl leading-relaxed">
              Uma profissão de raciocínio rápido, alta responsabilidade e precisão absoluta
            </p>
          </motion.div>
        </div>
      </section>

      {/* Introduction */}
      <section className="py-12 sm:py-20 lg:py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <h2 className="font-sans font-bold text-4xl text-grafite mb-8">
                A Autoridade nos{' '}
                <span className="text-carmesim">Céus</span>
              </h2>
              <div className="space-y-6 text-lg text-gray-600 leading-relaxed">
                <p>
                  O <strong className="text-grafite">Controlador de Tráfego Aéreo (CTA)</strong> é a autoridade que emite 
                  instruções aos pilotos para garantir que as aeronaves mantenham distâncias seguras entre si, 
                  tanto no ar quanto no solo.
                </p>
                <p>
                  É uma profissão que exige <span className="text-carmesim font-semibold">concentração extrema</span>, 
                  capacidade de tomar decisões rápidas sob pressão e uma comunicação clara e precisa em inglês técnico.
                </p>
                <p>
                  Os controladores trabalham em turnos de 24 horas, garantindo que cada voo chegue ao seu destino em segurança, 
                  seja um voo doméstico ou uma aeronave cruzando o Atlântico.
                </p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className="bg-gradient-to-br from-primary to-primary/80 rounded-2xl p-8 text-white">
                <h3 className="font-sans font-bold text-2xl mb-6">Principais Responsabilidades</h3>
                <ul className="space-y-4">
                  {[
                    'Evitar colisões entre aeronaves',
                    'Organizar descolagens e aterragens',
                    'Guiar aeronaves em rotas seguras',
                    'Gerir emergências aéreas',
                    'Coordenar com outros centros de controlo',
                    'Informar condições meteorológicas críticas'
                  ].map((item, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-carmesim flex-shrink-0 mt-0.5" />
                      <span className="text-white/90">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Types of Control */}
      <section className="py-12 sm:py-20 lg:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-carmesim/10 text-carmesim rounded-full text-sm uppercase tracking-wider mb-6">
              Tipos de Controlo
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
              Os Tipos de Controlo em Cabo Verde
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Conheça as diferentes funções desempenhadas pelos controladores de tráfego aéreo
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* TWR */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="card-technical rounded-2xl overflow-hidden"
            >
              <div className="h-48 bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center relative">
                <Building2 className="w-20 h-20 text-white/30 absolute" />
                <Eye className="w-16 h-16 text-white relative z-10" />
              </div>
              <div className="p-8">
                <div className="flex items-center gap-3 mb-4">
                  <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-bold">TWR</span>
                  <h3 className="font-sans font-bold text-xl text-grafite">Torre de Controlo</h3>
                </div>
                <p className="text-gray-600 leading-relaxed mb-4">
                  São os <strong>"olhos" do aeroporto</strong>. Gerem as aeronaves que estão a aterrar, a descolar e 
                  a movimentar-se nas pistas e pátios.
                </p>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Localizações</div>
                  <p className="text-sm text-grafite font-medium">Sal, Praia, São Vicente, Boa Vista</p>
                </div>
              </div>
            </motion.div>

            {/* APP */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="card-technical rounded-2xl overflow-hidden"
            >
              <div className="h-48 bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center relative">
                <Radar className="w-20 h-20 text-white/30 absolute animate-spin" style={{ animationDuration: '10s' }} />
                <Radio className="w-16 h-16 text-white relative z-10" />
              </div>
              <div className="p-8">
                <div className="flex items-center gap-3 mb-4">
                  <span className="px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-sm font-bold">APP</span>
                  <h3 className="font-sans font-bold text-xl text-grafite">Controlo de Aproximação</h3>
                </div>
                <p className="text-gray-600 leading-relaxed mb-4">
                  Cuidam das aeronaves numa área maior ao redor do aeroporto (geralmente até <strong>40-50 milhas</strong>), 
                  organizando a fila para aterragem.
                </p>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Tecnologia</div>
                  <p className="text-sm text-grafite font-medium">Radares de aproximação</p>
                </div>
              </div>
            </motion.div>

            {/* ACC */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="card-technical rounded-2xl overflow-hidden"
            >
              <div className="h-48 bg-gradient-to-br from-primary to-[#0A3A5A] flex items-center justify-center relative">
                <Globe className="w-20 h-20 text-white/30 absolute" />
                <Plane className="w-16 h-16 text-carmesim relative z-10 -rotate-45" />
              </div>
              <div className="p-8">
                <div className="flex items-center gap-3 mb-4">
                  <span className="px-3 py-1 bg-carmesim/20 text-grafite rounded-full text-sm font-bold">ACC</span>
                  <h3 className="font-sans font-bold text-xl text-grafite">Centro Oceânico</h3>
                </div>
                <p className="text-gray-600 leading-relaxed mb-4">
                  Gerem as aeronaves em voo de cruzeiro, muitas vezes atravessando o <strong>espaço aéreo FIR Sal</strong> 
                  entre continentes.
                </p>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Rotas</div>
                  <p className="text-sm text-grafite font-medium">Europa ↔ América do Sul, África ↔ América do Norte</p>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* How to Become */}
      <section className="py-12 sm:py-20 lg:py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-start">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <span className="inline-block px-4 py-2 bg-grafite/5 text-grafite rounded-full text-sm uppercase tracking-wider mb-6">
                Carreira
              </span>
              <h2 className="font-sans font-bold text-4xl text-grafite mb-6">
                Como se tornar um{' '}
                <span className="text-carmesim">Controlador?</span>
              </h2>
              <p className="text-lg text-gray-600 leading-relaxed mb-8">
                A carreira exige formação especializada e um perfil muito específico. Em Cabo Verde, 
                a formação segue padrões internacionais <strong>(ICAO)</strong> e é validada pela 
                Autoridade de Aviação Civil (AAC).
              </p>
              
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 mb-8">
                <div className="flex items-start gap-4">
                  <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-sans font-semibold text-amber-800 mb-2">Seleção Rigorosa</h4>
                    <p className="text-amber-700 text-sm">
                      Apenas uma pequena percentagem dos candidatos consegue concluir todo o processo de formação 
                      e obter a licença de CTA.
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="space-y-6"
            >
              <h3 className="font-sans font-semibold text-2xl text-grafite mb-6">Requisitos Essenciais</h3>
              
              {[
                { 
                  icon: GraduationCap, 
                  title: 'Formação Especializada', 
                  desc: 'Curso teórico e prático em instituição certificada, com simuladores e estágios em ambiente operacional real.',
                  color: 'bg-blue-50 text-blue-600'
                },
                { 
                  icon: Languages, 
                  title: 'Domínio do Inglês', 
                  desc: 'Proficiência mínima nível 4 ICAO. A comunicação aeronáutica internacional é exclusivamente em inglês.',
                  color: 'bg-green-50 text-green-600'
                },
                { 
                  icon: Brain, 
                  title: 'Aptidão Cognitiva', 
                  desc: 'Testes psicotécnicos rigorosos que avaliam raciocínio espacial, memória, atenção dividida e gestão de stress.',
                  color: 'bg-purple-50 text-purple-600'
                },
                { 
                  icon: Heart, 
                  title: 'Saúde e Estabilidade', 
                  desc: 'Exames médicos classe 3 (ICAO) periódicos e avaliação psicológica para garantir aptidão para a função.',
                  color: 'bg-red-50 text-red-600'
                },
              ].map((req, index) => (
                <div
                  key={index}
                  className="card-technical rounded-xl p-6 flex gap-5"
                >
                  <div className={`w-14 h-14 ${req.color} rounded-xl flex items-center justify-center flex-shrink-0`}>
                    <req.icon className="w-7 h-7" />
                  </div>
                  <div>
                    <h4 className="font-sans font-semibold text-lg text-grafite mb-2">{req.title}</h4>
                    <p className="text-gray-600">{req.desc}</p>
                  </div>
                </div>
              ))}
            </motion.div>
          </div>
        </div>
      </section>

      {/* FIR Sal Section */}
      <section className="py-12 sm:py-20 lg:py-24 bg-grafite relative overflow-hidden">
        <div className="absolute inset-0 opacity-20">
          <div className="absolute inset-0" style={{ 
            backgroundImage: 'radial-gradient(circle at 30% 50%, rgba(0,255,156,0.3) 0%, transparent 50%)',
          }} />
        </div>
        <div className="relative z-10 max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
            >
              <div className="relative">
                <div className="w-80 h-80 mx-auto border-2 border-carmesim/30 rounded-full flex items-center justify-center">
                  <div className="w-60 h-60 border border-carmesim/20 rounded-full flex items-center justify-center">
                    <div className="w-40 h-40 bg-carmesim/10 rounded-full flex items-center justify-center">
                      <Globe className="w-20 h-20 text-carmesim" />
                    </div>
                  </div>
                </div>
                <div className="absolute top-10 right-10">
                  <Plane className="w-8 h-8 text-white animate-pulse" />
                </div>
                <div className="absolute bottom-20 left-5">
                  <Plane className="w-6 h-6 text-carmesim -rotate-45" />
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <span className="inline-block px-4 py-2 bg-carmesim/10 text-carmesim rounded-full text-sm uppercase tracking-wider mb-6">
                Espaço Aéreo
              </span>
              <h2 className="font-sans font-bold text-4xl text-white mb-6">
                A FIR Sal: Um Espaço Estratégico
              </h2>
              <p className="text-xl text-white/80 leading-relaxed mb-6">
                A <strong className="text-carmesim">Flight Information Region (FIR) de Sal</strong> é uma das maiores 
                regiões de informação de voo do Atlântico, cobrindo milhões de quilómetros quadrados de oceano.
              </p>
              <p className="text-lg text-white/70 leading-relaxed mb-8">
                Os controladores cabo-verdianos gerem diariamente centenas de voos intercontinentais que atravessam 
                este corredor vital entre a Europa, África e as Américas.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center">
                  <div className="font-sans font-bold text-3xl text-amber mb-1">500+</div>
                  <div className="text-xs text-white/60 uppercase tracking-wider">Voos/dia em média</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center">
                  <div className="font-sans font-bold text-3xl text-amber mb-1">24/7</div>
                  <div className="text-xs text-white/60 uppercase tracking-wider">Operação contínua</div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-12 sm:py-20 lg:py-24 bg-white">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-sans font-bold text-4xl text-grafite mb-6">
            Quer conhecer a nossa associação?
          </h2>
          <p className="text-xl text-gray-600 mb-10">
            A ACCTA representa e defende os interesses dos controladores de tráfego aéreo em Cabo Verde
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/sobre"
              className="inline-flex items-center gap-2 bg-grafite text-white px-8 py-4 rounded-lg font-bold text-lg hover:bg-grafite/90 transition-all"
            >
              Sobre a ACCTA
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/contactos"
              className="inline-flex items-center gap-2 border-2 border-primary text-grafite px-8 py-4 rounded-lg font-bold text-lg hover:bg-grafite hover:text-white transition-all"
            >
              Entre em Contacto
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
