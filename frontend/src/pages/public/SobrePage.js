import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { PageBanner } from '../../components/PageBanner';
import { Skeleton } from '../../components/ui/skeleton';
import { ASSOCIACAO_NOME_COMPLETO, fir, camadas } from '../../content/cta';
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
  ArrowRight,
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
          alt={`Foto de ${titular.name} — ${cargoLabel}`}
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
          {vago ? <span className="text-gray-500">Vago</span> : titular.name}
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

const ORGAO_ICONS = {
  assembleia_geral: Building,
  direcao: Users,
  conselho_fiscal: Scale,
};

export const SobrePage = () => {
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
        badge="A Associação"
        title="Quem Somos"
        subtitle="A associação profissional dos controladores de tráfego aéreo de Cabo Verde"
      />

      {/* Introdução */}
      <section className="py-12 sm:py-20 lg:py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="animate-fade-up">
              <h2 className="font-sans font-bold text-4xl text-grafite mb-8">
                Unidos pela <span className="text-carmesim">Segurança Aérea</span>
              </h2>
              <div className="space-y-6 text-lg text-gray-600 leading-relaxed">
                <p>
                  A{' '}
                  <strong className="text-grafite">{ASSOCIACAO_NOME_COMPLETO}</strong>{' '}
                  é a associação de representação profissional dos controladores
                  de tráfego aéreo no arquipélago. Reúne os profissionais que
                  asseguram a gestão de um dos espaços aéreos mais estratégicos
                  do Atlântico, atuando na valorização da carreira, na promoção
                  da excelência técnica e na cooperação com as autoridades
                  nacionais e os parceiros do setor.
                </p>
                <p>
                  Mais do que uma estrutura associativa, somos um{' '}
                  <span className="text-grafite font-semibold">parceiro técnico</span>{' '}
                  no desenvolvimento da aviação civil nacional.
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
                  Os nossos profissionais atuam na {fir.nome}, uma das maiores
                  regiões de informação de voo do Atlântico, coordenando voos
                  entre a Europa, a África e as Américas. A prestação dos
                  serviços de tráfego aéreo é operada pela {asa ? asa.nome : 'ASA'}.
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
              Os Nossos Pilares
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite">
              Missão, Visão e Valores
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-16">
            <div className="card-technical rounded-2xl p-8 border-l-4 border-carmesim animate-fade-up">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 bg-carmesim rounded-xl flex items-center justify-center">
                  <Target className="w-7 h-7 text-white" aria-hidden="true" />
                </div>
                <h3 className="font-sans font-bold text-2xl text-grafite">
                  A Nossa Missão
                </h3>
              </div>
              <p className="text-gray-600 text-lg leading-relaxed">
                Representar e valorizar os controladores de tráfego aéreo,
                promovendo a <strong>segurança operacional</strong>, o{' '}
                <strong>desenvolvimento contínuo</strong> da profissão e o{' '}
                <strong>bem-estar</strong> dos associados.
              </p>
            </div>

            <div className="card-technical rounded-2xl p-8 border-l-4 border-grafite animate-fade-up">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 bg-grafite rounded-xl flex items-center justify-center">
                  <Eye className="w-7 h-7 text-white" aria-hidden="true" />
                </div>
                <h3 className="font-sans font-bold text-2xl text-grafite">
                  A Nossa Visão
                </h3>
              </div>
              <p className="text-gray-600 text-lg leading-relaxed">
                Ser uma associação de referência na representação da classe e na
                contribuição técnica para a{' '}
                <strong>segurança da navegação aérea no Atlântico</strong>.
              </p>
            </div>
          </div>

          {/* Valores — neutral-led, Carmesim só no valor-chave "Segurança" (U3) */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                icon: Shield,
                title: 'Segurança',
                desc: 'O nosso compromisso inegociável.',
                color: 'bg-carmesim/10 text-carmesim',
              },
              {
                icon: Award,
                title: 'Excelência',
                desc: 'Rigor técnico em cada comunicação.',
                color: 'bg-grafite/10 text-grafite',
              },
              {
                icon: Users,
                title: 'União',
                desc: 'A força do coletivo acima do individual.',
                color: 'bg-grafite/10 text-grafite',
              },
              {
                icon: Star,
                title: 'Transparência',
                desc: 'Gestão clara e responsável.',
                color: 'bg-grafite/10 text-grafite',
              },
            ].map((value, index) => (
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
              Gestão Atual
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
              Corpos Sociais
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Os órgãos sociais que dirigem e fiscalizam a associação
            </p>
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
              Informação dos corpos sociais indisponível de momento.
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
            Quer saber mais sobre a nossa atuação?
          </h2>
          <p className="text-xl text-white/80 mb-10">
            Consulte os documentos de governança e os relatórios de gestão
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/transparencia"
              className="inline-flex items-center gap-2 bg-floresta text-white px-8 py-4 rounded-lg font-bold text-lg hover:bg-floresta-dark transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60 ring-offset-2 ring-offset-grafite"
            >
              Ver Transparência
              <ArrowRight className="w-5 h-5" aria-hidden="true" />
            </Link>
            <Link
              to="/contactos"
              className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white border border-white/20 px-8 py-4 rounded-lg font-bold text-lg hover:bg-white/20 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60 ring-offset-2 ring-offset-grafite"
            >
              Fale Connosco
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
