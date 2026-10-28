import React from 'react';
import { Building2 } from 'lucide-react';
import { useI18n } from '../../../i18n';
import { ATS_ICONS } from './tokens';

export const AtsStructure = () => {
  const { t, cta } = useI18n();
  const { camadas } = cta;
  return (
  <section className="py-16 sm:py-24 bg-gray-50">
    <div className="max-w-7xl mx-auto px-5 sm:px-6">
      <div className="text-center max-w-2xl mx-auto mb-10 sm:mb-16 animate-fade-up">
        <span className="inline-block px-3 py-1.5 bg-grafite/5 text-grafite rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
          {t('home.ats.badge')}
        </span>
        <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-grafite mb-3 sm:mb-4">
          {t('home.ats.titleStart')}{' '}
          <span className="text-carmesim">{t('home.ats.titleHighlight')}</span>
        </h2>
        <p className="text-sm sm:text-lg text-gray-600">
          {t('home.ats.lead')}
        </p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {camadas.map((c) => {
          const Icon = ATS_ICONS[c.sigla] || Building2;
          return (
            <div key={c.sigla} className="card-technical card-hover p-5 sm:p-6 animate-fade-up">
              <div className="w-11 h-11 sm:w-12 sm:h-12 bg-grafite rounded-lg flex items-center justify-center mb-4">
                <Icon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <div className="font-bold text-lg text-grafite mb-1 leading-tight">{c.sigla}</div>
              <div className="text-sm text-gray-600 leading-snug">{c.papel}</div>
            </div>
          );
        })}
      </div>
    </div>
  </section>
  );
};
