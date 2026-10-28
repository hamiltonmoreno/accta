import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { PageBanner } from '../../components/PageBanner';
import { Skeleton } from '../../components/ui/skeleton';
import { PortugueseContentNotice } from '../../components/PortugueseContentNotice';
import { useI18n, useCta } from '../../i18n';
import { usePageMeta } from '../../i18n/usePageMeta';
import { governanceAPI, mediaUrl } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import {
  Shield,
  Eye,
  Users,
  Star,
  Target,
  Award,
  Globe,
  UserCircle,
  Building,
  Scale,
} from 'lucide-react';

// Iniciais p/ placeholder de avatar (titular sem foto).
const initials = (name) =>
  (name || '')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase() || '—';

// Cartão de um titular (foto + nome) ou estado "Vago".
const TitularCard = ({ titular, cargoLabel, accent }) => {
  const { t } = useI18n();
  const vago = !titular;
  const ring = accent ? 'bg-carmesim/5' : 'bg-gray-50';
  return (
    <div className={`flex items-center gap-3 p-3 ${ring} rounded-lg`}>
      {vago ? (
        <span
          aria-hidden="true"
          className="flex w-10 h-10 shrink-0 items-center justify-center rounded-full bg-gray-200 text-gray-500"
        >
          <UserCircle className="w-7 h-7" />
        </span>
      ) : titular.photo_url ? (
        <img
          src={mediaUrl(titular.photo_url)}
          alt={t('sobre.corpos.photoAlt', { name: titular.name, cargo: cargoLabel })}
          loading="lazy"
          className="w-10 h-10 shrink-0 rounded-full object-cover"
        />
      ) : (
        <span
          aria-hidden="true"
          className={`flex w-10 h-10 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${
            accent ? 'bg-carmesim/10 text-carmesim' : 'bg-grafite/10 text-grafite'
          }`}
        >
          {initials(titular.name)}
        </span>
      )}
      <div className="min-w-0">
        <div className="font-semibold text-grafite truncate">{cargoLabel}</div>
        <div className="text-sm text-gray-600 truncate">
          {vago ? <span className="text-gray-500">{t('sobre.corpos.vacant')}</span> : titular.name}
        </div>
      </div>
    </div>
  );
};

// Bloco de um órgão social (lista os seus cargos; vários titulares por cargo).
const OrgaoCard = ({ orgao, icon: Icon, accent }) => (
  <div
    className={`card-technical rounded-2xl p-8 animate-fade-up ${
      accent ? 'border-2 border-carmesim' : ''
    }`}
  >
    <div
      className={`w-16 h-16 ${
        accent ? 'bg-carmesim' : 'bg-grafite'
      } rounded-xl flex items-center justify-center mb-6`}
    >
      <Icon className="w-8 h-8 text-white" aria-hidden="true" />
    </div>
    <h3 className="font-sans font-bold text-2xl text-grafite mb-6">{orgao.nome}</h3>
    <div className="space-y-3">
      {orgao.cargos.map((cargo) => {
        if (!cargo.titulares.length) {
          return (
            <TitularCard
              key={cargo.key}
              titular={null}
              cargoLabel={cargo.label}
              accent={accent}
            />
          );
        }
        return cargo.titulares.map((t, i) => (
          <TitularCard
            key={`${cargo.key}-${i}`}
            titular={t}
            cargoLabel={cargo.label}
            accent={accent}
          />
        ));
      })}
    </div>
  </div>
);

const VALUE_STYLES = [
  { icon: Shield, color: 'bg-carmesim/10 text-carmesim' },
  { icon: Award, color: 'bg-grafite/10 text-grafite' },
  { icon: Users, color: 'bg-grafite/10 text-grafite' },
  { icon: Star, color: 'bg-grafite/10 text-grafite' },
];

const ORGAO_ICONS = {
  assembleia_geral: Building,
  direcao: Users,
  conselho_fiscal: Scale,
};

export const SobrePage = () => {
  const { t, lp } = useI18n();
  const { ASSOCIACAO_NOME_COMPLETO, fir, camadas } = useCta();
  usePageMeta('sobre');
  const asa = camadas.find((c) => c.sigla === 'ASA');

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.governance.corposSociais(),
    queryFn: () => governanceAPI.getCorposSociais().then((r) => r.data),
    staleTime: 5 * 60 * 1000, // dado quase estático
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <PageBanner
        pageKey="sobre"
        badge={t('sobre.banner.badge')}
        title={t('sobre.banner.title')}
        subtitle={t('sobre.banner.subtitle')}
      />

      {/* Introdução */}
      <section className="py-12 sm:py-20 lg:py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="animate-fade-up">
              <h2 className="font-sans font-bold text-4xl text-grafite mb-8">
                {t('sobre.intro.titleA')} <span className="text-carmesim">{t('sobre.intro.titleHighlight')}</span>
              </h2>
              <div className="space-y-6 text-lg text-gray-600 leading-relaxed">
                <p>
                  {t('sobre.intro.p1a') && <>{t('sobre.intro.p1a')}{' '}</>}
                  <strong className="text-grafite">{ASSOCIACAO_NOME_COMPLETO}</strong>{' '}
                  {t('sobre.intro.p1b')}
                </p>
                <p>
                  {t('sobre.intro.p2a')}{' '}
                  <span className="text-grafite font-semibold">{t('sobre.intro.p2Highlight')}</span>{' '}
                  {t('sobre.intro.p2b')}
                </p>
              </div>
            </div>

            <div className="relative animate-fade-up">
              <div className="bg-gradient-to-br from-grafite to-grafite/80 rounded-2xl p-8 text-white">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 bg-carmesim rounded-xl flex items-center justify-center">
                    <Globe className="w-8 h-8 text-white" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="font-sans font-bold text-2xl">{fir.nome}</div>
                    <div className="text-white/70">{fir.baseLegal}</div>
                  </div>
                </div>
                <p className="text-white/80 leading-relaxed">
                  {t('sobre.intro.firText', { fir: fir.nome, asa: asa ? asa.nome : 'ASA' })}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Missão, Visão, Valores */}
      <section className="py-12 sm:py-20 lg:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-carmesim/10 text-carmesim rounded-full text-sm uppercase tracking-wider mb-6">
              {t('sobre.pillars.badge')}
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite">
              {t('sobre.pillars.title')}
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-16">
            <div className="card-technical rounded-2xl p-8 border-l-4 border-carmesim animate-fade-up">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 bg-carmesim rounded-xl flex items-center justify-center">
                  <Target className="w-7 h-7 text-white" aria-hidden="true" />
                </div>
                <h3 className="font-sans font-bold text-2xl text-grafite">
                  {t('sobre.pillars.missionTitle')}
                </h3>
              </div>
              <p className="text-gray-600 text-lg leading-relaxed">
                {t('sobre.pillars.missionA')} <strong>{t('sobre.pillars.missionS1')}</strong>{t('sobre.pillars.missionB')}{' '}
                <strong>{t('sobre.pillars.missionS2')}</strong> {t('sobre.pillars.missionC')}{' '}
                <strong>{t('sobre.pillars.missionS3')}</strong> {t('sobre.pillars.missionD')}
              </p>
            </div>

            <div className="card-technical rounded-2xl p-8 border-l-4 border-grafite animate-fade-up">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 bg-grafite rounded-xl flex items-center justify-center">
                  <Eye className="w-7 h-7 text-white" aria-hidden="true" />
                </div>
                <h3 className="font-sans font-bold text-2xl text-grafite">
                  {t('sobre.pillars.visionTitle')}
                </h3>
              </div>
              <p className="text-gray-600 text-lg leading-relaxed">
                {t('sobre.pillars.visionA')}{' '}
                <strong>{t('sobre.pillars.visionStrong')}</strong>{t('sobre.pillars.visionB')}
              </p>
            </div>
          </div>

          {/* Valores — neutral-led, Carmesim só no valor-chave "Segurança" (U3) */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {t('sobre.pillars.values').map((v, i) => ({ ...v, ...VALUE_STYLES[i] })).map((value, index) => (
              <div
                key={index}
                className="card-technical rounded-xl p-6 text-center hover:shadow-lg transition-shadow animate-fade-up"
              >
                <div
                  className={`w-16 h-16 ${value.color} rounded-full flex items-center justify-center mx-auto mb-4`}
                >
                  <value.icon className="w-8 h-8" aria-hidden="true" />
                </div>
                <h4 className="font-sans font-bold text-xl text-grafite mb-2">
                  {value.title}
                </h4>
                <p className="text-gray-600">{value.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Corpos Sociais — dinâmico */}
      <section className="py-12 sm:py-20 lg:py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-grafite/5 text-grafite rounded-full text-sm uppercase tracking-wider mb-6">
              {t('sobre.corpos.badge')}
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
              {t('sobre.corpos.title')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('sobre.corpos.subtitle')}
            </p>
          </div>

          <div className="flex justify-center mb-8">
            <PortugueseContentNotice />
          </div>

          {isLoading && (
            <div className="grid md:grid-cols-3 gap-8">
              {[0, 1, 2].map((i) => (
                <div key={i} className="card-technical rounded-2xl p-8">
                  <Skeleton className="w-16 h-16 rounded-xl mb-6" />
                  <Skeleton className="h-7 w-2/3 mb-6" />
                  <div className="space-y-3">
                    <Skeleton className="h-16 w-full rounded-lg" />
                    <Skeleton className="h-16 w-full rounded-lg" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {isError && (
            <p className="text-center text-gray-600">
              {t('sobre.corpos.error')}
            </p>
          )}

          {!isLoading && !isError && data && (
            <div className="grid md:grid-cols-3 gap-8">
              {data.orgaos.map((orgao) => (
                <OrgaoCard
                  key={orgao.id}
                  orgao={orgao}
                  icon={ORGAO_ICONS[orgao.id] || Building}
                  accent={orgao.id === 'direcao'}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* CTA */}
      <section className="py-12 sm:py-20 lg:py-24 bg-grafite">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-sans font-bold text-4xl text-white mb-6">
            {t('sobre.cta.title')}
          </h2>
          <p className="text-xl text-white/80 mb-10">
            {t('sobre.cta.subtitle')}
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to={lp('/contactos')}
              className="inline-flex items-center gap-2 bg-floresta text-white px-8 py-4 rounded-lg font-bold text-lg hover:bg-floresta-dark transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60 ring-offset-2 ring-offset-grafite"
            >
              {t('sobre.cta.button')}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
