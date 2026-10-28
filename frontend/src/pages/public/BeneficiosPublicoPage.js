import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { safeUrl } from '../../utils/safeUrl';
import {
  Gift,
  QrCode,
  CheckCircle,
  Shield,
  Building2,
  Heart,
  Car,
  Dumbbell,
  Hotel,
  Stethoscope,
  HandshakeIcon,
  ArrowRight,
  Mail
} from 'lucide-react';
import { benefitsAPI, mediaUrl } from '../../utils/api';
import { PageBanner } from '../../components/PageBanner';
import { useI18n } from '../../i18n';
import { usePageMeta } from '../../i18n/usePageMeta';

export const BeneficiosPublicoPage = () => {
  const { t, lp } = useI18n();
  usePageMeta('beneficios');
  // Sprint 12 — fetch real partners. Antes: 8 cards genericos placeholder.
  // Endpoint /benefits/public retorna apenas active=true, sem auth.
  // staleTime 5min: este conteudo e quase estatico.
  const { data: benefits = [] } = useQuery({
    queryKey: ['benefits', 'public'],
    queryFn: async () => (await benefitsAPI.getPublic()).data,
    staleTime: 5 * 60 * 1000,
  });

  // Dedup partners por nome (varios benefits podem ser do mesmo parceiro);
  // mostra apenas os com logo. Cap a 12 para nao sobrecarregar visualmente.
  const partners = Array.from(
    new Map(
      benefits
        .filter((b) => b.logo_url)
        .map((b) => [b.name, b]),
    ).values(),
  ).slice(0, 12);

  // Codex P2 #27: backend model nao valida scheme, "www.x.cv" sem http://
  // seria interpretado como path relativo (navegar para /beneficios-publico/...).
  // safeWebsite: fonte única em utils/safeUrl (spec 019 M-HREF).
  const safeWebsite = safeUrl;

  const categoryLabels = t('beneficios.categories');
  const partnerCategories = [
    { icon: Hotel, label: categoryLabels[0], color: 'bg-[#EFF6FF] text-[#1D4ED8]' },
    { icon: Dumbbell, label: categoryLabels[1], color: 'bg-[#F0FDF4] text-[#15803D]' },
    { icon: Stethoscope, label: categoryLabels[2], color: 'bg-[#FEF2F2] text-[#B91C1C]' },
    { icon: Shield, label: categoryLabels[3], color: 'bg-[#F5F5F5] text-[#3A3A3A]' },
    { icon: Car, label: categoryLabels[4], color: 'bg-[#FFFBEB] text-[#B45309]' },
    { icon: Heart, label: categoryLabels[5], color: 'bg-[#F5F5F5] text-[#3A3A3A]' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <PageBanner pageKey="beneficios" badge={t('beneficios.banner.badge')} title={t('beneficios.banner.title')} subtitle={t('beneficios.banner.subtitle')} />

      {/* Introduction for Partners */}
      <section className="py-12 sm:py-20 lg:py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="animate-fade-up">
              <h2 className="font-sans font-bold text-4xl text-grafite mb-6">
                {t('beneficios.intro.titleBefore')}{' '}
                <span className="text-carmesim">ACCTA</span>
              </h2>
              <p className="text-lg text-gray-600 leading-relaxed mb-6">
                {t('beneficios.intro.p1Before')}<strong className="text-grafite">{t('beneficios.intro.p1Strong')}</strong>
                {t('beneficios.intro.p1After')}
              </p>
              <p className="text-lg text-gray-600 leading-relaxed mb-8">
                {t('beneficios.intro.p2')}
              </p>
              
              <div className="flex flex-wrap gap-3">
                {partnerCategories.map((cat, index) => (
                  <div
                    key={index}
                    className={`inline-flex items-center gap-2 px-4 py-2 ${cat.color} rounded-full`}
                  >
                    <cat.icon className="w-4 h-4" />
                    <span className="font-medium text-sm">{cat.label}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="animate-fade-up">
              <div className="bg-gradient-to-br from-grafite to-grafite/60 rounded-2xl p-8 text-white">
                <Gift className="w-12 h-12 text-white mb-6" />
                <h3 className="font-sans font-bold text-2xl mb-4">{t('beneficios.exclusive.title')}</h3>
                <ul className="space-y-4">
                  {t('beneficios.exclusive.items').map((item, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                      <span className="text-white/90">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-12 sm:py-20 lg:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-carmesim/10 text-carmesim rounded-full text-sm uppercase tracking-wider mb-6">
              {t('beneficios.how.badge')}
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
              {t('beneficios.how.title')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('beneficios.how.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {t('beneficios.how.steps').map((step, index) => ({
              ...step,
              step: String(index + 1).padStart(2, '0'),
              icon: [QrCode, Building2, CheckCircle][index],
            })).map((item, index) => (
              <div key={index}
                className="text-center animate-fade-up">
                <div className="relative mb-6">
                  <div className="w-20 h-20 bg-grafite rounded-2xl flex items-center justify-center mx-auto">
                    <item.icon className="w-10 h-10 text-white" />
                  </div>
                  <span className="absolute -top-2 -right-2 w-8 h-8 bg-carmesim rounded-full flex items-center justify-center font-sans font-bold text-white text-sm">
                    {item.step}
                  </span>
                </div>
                <h3 className="font-sans font-semibold text-xl text-grafite mb-3">{item.title}</h3>
                <p className="text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Partners — Sprint 12: agora puxa dados reais via benefitsAPI.getPublic.
          Quando nao ha parceiros (DB vazio ou nenhum com logo_url), seccao
          gracefully cai para empty state em vez de mostrar 8 cards genericos. */}
      {partners.length > 0 && (
        <section className="py-12 sm:py-20 lg:py-24 bg-gray-50">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
              <span className="inline-block px-4 py-2 bg-grafite/5 text-grafite rounded-full text-sm uppercase tracking-wider mb-6">
                {t('beneficios.partners.badge')}
              </span>
              <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
                {t('beneficios.partners.title')}
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                {t('beneficios.partners.subtitle')}
              </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {partners.map((partner) => {
                const card = (
                  <div className="card-technical rounded-xl p-8 flex items-center justify-center h-32 animate-fade-up hover:shadow-md transition-shadow">
                    <img
                      src={mediaUrl(partner.logo_url)}
                      alt={partner.name}
                      title={partner.name}
                      loading="lazy"
                      className="max-h-16 max-w-full object-contain grayscale hover:grayscale-0 transition-all"
                    />
                  </div>
                );
                const website = safeWebsite(partner.website);
                return website ? (
                  <a
                    key={partner.id}
                    href={website}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={t('beneficios.partners.visitWebsite', { name: partner.name })}
                  >
                    {card}
                  </a>
                ) : (
                  <div key={partner.id}>{card}</div>
                );
              })}
            </div>
          </div>
        </section>
      )}

      {/* Become a Partner CTA */}
      <section className="py-12 sm:py-20 lg:py-24 bg-grafite">
        <div className="max-w-4xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="animate-fade-up">
              <HandshakeIcon className="w-16 h-16 text-white mb-6" />
              <h2 className="font-sans font-bold text-4xl text-white mb-6">
                {t('beneficios.become.title')}
              </h2>
              <p className="text-xl text-white/80 leading-relaxed">
                {t('beneficios.become.body')}
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20 animate-fade-up">
              <h3 className="font-sans font-semibold text-xl text-white mb-6">{t('beneficios.become.advantagesTitle')}</h3>
              <ul className="space-y-4 mb-8">
                {t('beneficios.become.advantages').map((item, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-white flex-shrink-0 mt-0.5" />
                    <span className="text-white/90">{item}</span>
                  </li>
                ))}
              </ul>
              <Link
                to={lp('/contactos')}
                className="inline-flex items-center gap-2 bg-floresta text-white px-6 py-3 rounded-lg font-bold hover:bg-floresta-dark transition-all w-full justify-center"
              >
                <Mail className="w-5 h-5" />
                {t('beneficios.become.cta')}
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Validator CTA */}
      <section className="py-16 bg-white">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <QrCode className="w-12 h-12 text-grafite mx-auto mb-4" />
          <h2 className="font-sans font-bold text-3xl text-grafite mb-4">
            {t('beneficios.validator.title')}
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            {t('beneficios.validator.body')}
          </p>
          <Link
            to={lp('/validador')}
            className="inline-flex items-center gap-2 bg-grafite text-white px-8 py-4 rounded-lg font-bold hover:bg-grafite/90 transition-all"
          >
            {t('beneficios.validator.cta')}
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
};
