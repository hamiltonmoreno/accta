import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Radio } from 'lucide-react';
import { tiposControlo } from '../../../content/cta';
import { CONTROL_ICONS } from './tokens';

export const HowATCWorks = () => (
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
);
