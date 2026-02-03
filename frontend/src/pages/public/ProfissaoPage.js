import React from 'react';
import { motion } from 'framer-motion';
import { Radio, Clock, Headphones, BarChart3 } from 'lucide-react';

export const ProfissaoPage = () => {
  return (
    <div className="py-16">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <h1 className="font-outfit font-bold text-5xl md:text-6xl text-primary mb-6" data-testid="profession-title">
            Controlador de Tráfego Aéreo
          </h1>
          <p className="text-xl text-slate-600 leading-relaxed">
            Uma profissão de precisão, responsabilidade e dedicação total à segurança aérea
          </p>
        </motion.div>

        {/* Hero Image */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-16 rounded-2xl overflow-hidden shadow-xl"
        >
          <img
            src="https://images.unsplash.com/photo-1760447197763-7f8caf035177?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHw0fHxhaXIlMjB0cmFmZmljJTIwY29udHJvbCUyMHRvd2VyJTIwc3Vuc2V0JTIwYXZpYXRpb258ZW58MHx8fHwxNzcwMTQ3Mjk2fDA&ixlib=rb-4.1.0&q=85"
            alt="Aviation"
            className="w-full h-[400px] object-cover"
          />
        </motion.div>

        {/* Content */}
        <div className="space-y-12">
          <section>
            <h2 className="font-outfit font-semibold text-3xl text-primary mb-6">O que faz um Controlador?</h2>
            <p className="text-lg text-slate-600 leading-relaxed mb-4">
              Os controladores de tráfego aéreo são responsáveis por coordenar o movimento de aeronaves no espaço aéreo e nos aeroportos, garantindo a segurança de todos os voos. Eles trabalham em torres de controle, centros de controle de área e instalações de controle de aproximação.
            </p>
            <p className="text-lg text-slate-600 leading-relaxed">
              Esta é uma profissão que exige alta concentração, tomada de decisão rápida, excelente comunicação e capacidade de trabalhar sob pressão. Cada decisão pode impactar a segurança de centenas de pessoas.
            </p>
          </section>

          {/* Responsibilities */}
          <section>
            <h2 className="font-outfit font-semibold text-3xl text-primary mb-6">Responsabilidades Principais</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="card-technical rounded-xl p-6">
                <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center mb-4">
                  <Radio className="w-6 h-6 text-accent" />
                </div>
                <h3 className="font-outfit font-semibold text-xl text-primary mb-3">Comunicação</h3>
                <p className="text-slate-600">
                  Manter comunicação constante e clara com pilotos, fornecendo instruções precisas para navegação segura
                </p>
              </div>

              <div className="card-technical rounded-xl p-6">
                <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center mb-4">
                  <Clock className="w-6 h-6 text-accent" />
                </div>
                <h3 className="font-outfit font-semibold text-xl text-primary mb-3">Gestão de Tempo</h3>
                <p className="text-slate-600">
                  Coordenar horários de decolagem e aterrissagem, otimizando o fluxo de tráfego aéreo
                </p>
              </div>

              <div className="card-technical rounded-xl p-6">
                <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center mb-4">
                  <BarChart3 className="w-6 h-6 text-accent" />
                </div>
                <h3 className="font-outfit font-semibold text-xl text-primary mb-3">Monitoramento</h3>
                <p className="text-slate-600">
                  Acompanhar múltiplas aeronaves simultaneamente usando sistemas de radar e tecnologia avançada
                </p>
              </div>

              <div className="card-technical rounded-xl p-6">
                <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center mb-4">
                  <Headphones className="w-6 h-6 text-accent" />
                </div>
                <h3 className="font-outfit font-semibold text-xl text-primary mb-3">Emergências</h3>
                <p className="text-slate-600">
                  Responder rapidamente a situações de emergência, coordenando ações de segurança
                </p>
              </div>
            </div>
          </section>

          {/* Requirements */}
          <section>
            <h2 className="font-outfit font-semibold text-3xl text-primary mb-6">Requisitos da Profissão</h2>
            <div className="card-technical rounded-xl p-8">
              <ul className="space-y-4 text-slate-600">
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-accent rounded-full mt-2" />
                  <span className="flex-1">Formação especializada em controle de tráfego aéreo</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-accent rounded-full mt-2" />
                  <span className="flex-1">Certificação pela autoridade de aviação civil</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-accent rounded-full mt-2" />
                  <span className="flex-1">Excelência em comunicação em português e inglês</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-accent rounded-full mt-2" />
                  <span className="flex-1">Capacidade de trabalhar sob pressão e tomar decisões rápidas</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-accent rounded-full mt-2" />
                  <span className="flex-1">Excelente visão, audição e saúde física e mental</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-accent rounded-full mt-2" />
                  <span className="flex-1">Formação contínua e atualização de competências</span>
                </li>
              </ul>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};
