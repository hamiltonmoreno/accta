import React from 'react';
import { Link } from 'react-router-dom';
import { PageBanner } from '../../components/PageBanner';
import { useI18n } from '../../i18n';
import { usePageMeta } from '../../i18n/usePageMeta';
import {
  Users,
  Wallet,
  BarChart3,
  CalendarDays,
  Vote,
  Megaphone,
  LayoutGrid,
  ShieldCheck,
} from 'lucide-react';

// Ícones por ordem dos itens em `plataforma.capacidades` / `plataforma.pilares`.
// Texto factual, sem números/estatísticas nem promessas comerciais
// (regra editorial da área pública).
const CAPACIDADE_ICONS = [Users, Wallet, BarChart3, CalendarDays, Vote, Megaphone];
const PILAR_ICONS = [LayoutGrid, ShieldCheck];

export const PlataformaPage = () => {
  const { t, lp } = useI18n();
  usePageMeta('plataforma');
  const capacidades = t('plataforma.capacidades').map((c, i) => ({ ...c, icon: CAPACIDADE_ICONS[i] }));
  const pilares = t('plataforma.pilares').map((p, i) => ({ ...p, icon: PILAR_ICONS[i] }));

  return (
    <div className="min-h-screen bg-gray-50">
      <PageBanner
        pageKey="plataforma"
        badge={t('plataforma.banner.badge')}
        title={t('plataforma.banner.title')}
        subtitle={t('plataforma.banner.subtitle')}
        icon={LayoutGrid}
      />

      {/* Introdução — o que é a plataforma */}
      <section className="py-12 sm:py-20 lg:py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            <div className="animate-fade-up">
              <h2 className="font-sans font-bold text-2xl sm:text-4xl text-grafite mb-6">
                {t('plataforma.intro.titleBefore')}<span className="text-carmesim">{t('plataforma.intro.titleHighlight')}</span>
              </h2>
              <div className="space-y-5 text-base sm:text-lg text-gray-600 leading-relaxed">
                <p>{t('plataforma.intro.p1')}</p>
                <p>{t('plataforma.intro.p2')}</p>
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-4 sm:gap-6 animate-fade-up">
              {pilares.map((p) => (
                <div key={p.title} className="card-technical card-hover p-5 sm:p-6">
                  <div className="w-11 h-11 sm:w-12 sm:h-12 bg-grafite rounded-lg flex items-center justify-center mb-4">
                    <p.icon className="w-5 h-5 sm:w-6 sm:h-6 text-white" aria-hidden="true" />
                  </div>
                  <h3 className="font-semibold text-base sm:text-lg text-grafite mb-1.5">{p.title}</h3>
                  <p className="text-sm text-gray-600 leading-relaxed">{p.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Capacidades / módulos */}
      <section className="py-12 sm:py-20 lg:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="max-w-2xl mb-10 sm:mb-14 animate-fade-up">
            <span className="inline-block px-3 py-1.5 bg-carmesim/10 text-carmesim rounded-full text-xs uppercase tracking-wider font-semibold mb-4">
              {t('plataforma.modules.badge')}
            </span>
            <h2 className="font-sans font-bold text-2xl sm:text-4xl text-grafite">
              {t('plataforma.modules.title')}
            </h2>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {capacidades.map((c) => (
              <div key={c.title} className="card-technical card-hover p-5 sm:p-6 animate-fade-up">
                <div className="w-11 h-11 sm:w-12 sm:h-12 bg-grafite rounded-lg flex items-center justify-center mb-4">
                  <c.icon className="w-5 h-5 sm:w-6 sm:h-6 text-white" aria-hidden="true" />
                </div>
                <h3 className="font-semibold text-base sm:text-lg text-grafite mb-1.5">{c.title}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{c.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Fecho institucional — sem CTA comercial forte */}
      <section className="py-12 sm:py-20 lg:py-24">
        <div className="max-w-3xl mx-auto px-6 text-center animate-fade-up">
          <h2 className="font-sans font-bold text-2xl sm:text-3xl text-grafite mb-4">
            {t('plataforma.closing.title')}
          </h2>
          <p className="text-base sm:text-lg text-gray-600 leading-relaxed">
            {t('plataforma.closing.textBefore')}
            <Link to={lp('/login')} className="text-carmesim font-semibold hover:text-carmesim-dark transition-colors">
              {t('plataforma.closing.link')}
            </Link>
            {t('plataforma.closing.textAfter')}
          </p>
        </div>
      </section>
    </div>
  );
};

export default PlataformaPage;
