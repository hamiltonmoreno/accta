import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Eye, Plane, Radio, Shield } from 'lucide-react';
import { useI18n } from '../../../i18n';

const ICONS = [Eye, Radio, Shield, Plane];

export const WhatWeDo = () => {
  const { t, lp } = useI18n();
  const items = t('home.whatWeDo.items').map((item, i) => ({ ...item, icon: ICONS[i] }));
  return (
  <section className="py-16 sm:py-24 bg-gray-50">
    <div className="max-w-7xl mx-auto px-5 sm:px-6">
      <div className="grid lg:grid-cols-2 gap-10 sm:gap-16 items-center">
        <div className="animate-fade-up">
          <span className="inline-block px-3 py-1.5 bg-carmesim/10 text-carmesim rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
            {t('home.whatWeDo.badge')}
          </span>
          <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-grafite mb-4 sm:mb-6">
            {t('home.whatWeDo.titleStart')}{' '}
            <span className="text-carmesim">{t('home.whatWeDo.titleHighlight')}</span>
          </h2>
          <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-4 sm:mb-6">
            {t('home.whatWeDo.p1Start')}{' '}
            <strong className="text-grafite">{t('home.whatWeDo.p1Strong')}</strong> {t('home.whatWeDo.p1End')}
          </p>
          <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-6 sm:mb-8">
            {t('home.whatWeDo.p2')}
          </p>
          <Link
            to={lp('/profissao')}
            className="inline-flex items-center gap-2 text-carmesim font-semibold hover:text-carmesim-dark transition-colors group text-sm sm:text-base"
          >
            {t('home.whatWeDo.link')}
            <ChevronRight className="w-4 sm:w-5 h-4 sm:h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:gap-6 animate-fade-up">
          {items.map((item, index) => (
            <div key={index} className="card-technical card-hover p-4 sm:p-6">
              <div className="w-9 h-9 sm:w-12 sm:h-12 bg-grafite rounded-lg flex items-center justify-center mb-3 sm:mb-4">
                <item.icon className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
              </div>
              <h3 className="font-semibold text-sm sm:text-lg text-grafite mb-1 sm:mb-2">{item.title}</h3>
              <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  </section>
  );
};
