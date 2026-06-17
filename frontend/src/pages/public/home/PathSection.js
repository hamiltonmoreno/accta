import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, GraduationCap } from 'lucide-react';
import { caminhoCTA } from '../../../content/cta';
import { CAMINHO_RESUMO } from './tokens';

export const PathSection = () => (
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
);
