import React from 'react';
import { Globe, Navigation, Plane, Radio, Waves } from 'lucide-react';
import { useI18n } from '../../../i18n';

export const FIRSection = () => {
  const { t, cta } = useI18n();
  const { fir } = cta;
  const stats = [
    { icon: Globe, label: t('home.fir.coverage'), value: t('home.fir.coverageValue') },
    { icon: Radio, label: t('home.fir.communications'), value: fir.comunicacoes },
    { icon: Navigation, label: t('home.fir.surveillance'), value: t('home.fir.surveillanceValue') },
    { icon: Plane, label: t('home.fir.routes'), value: t('home.fir.routesValue') },
  ];

  return (
    <section className="py-12 sm:py-16 bg-grafite relative overflow-hidden">
      <div className="absolute top-0 right-0 w-72 h-72 bg-carmesim/10 rounded-full blur-3xl -translate-y-1/3 translate-x-1/4" />
      <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-6">
        <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-center">
          <div className="animate-fade-up">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/10 border border-white/20 rounded-full mb-4 sm:mb-5">
              <Waves className="w-3.5 h-3.5 text-white" />
              <span className="text-xs text-white font-semibold uppercase tracking-wider">{t('home.fir.badge')}</span>
            </div>
            <h2 className="font-bold text-2xl sm:text-3xl lg:text-4xl text-white mb-3 sm:mb-4">
              {fir.nome}
            </h2>
            <p className="text-sm sm:text-base text-white/70 leading-relaxed max-w-xl">
              {t('home.fir.lead')}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:gap-4 animate-fade-up">
            {stats.map((s) => (
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
  );
};
