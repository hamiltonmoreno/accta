import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
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
import { benefitsAPI } from '../../utils/api';
import { unsplashSrcSet } from '../../utils/unsplash';

export const BeneficiosPublicoPage = () => {
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
  // Prepend https:// quando falta scheme; filtra schemes invalidos (javascript:).
  const safeWebsite = (url) => {
    if (!url || typeof url !== 'string') return null;
    const trimmed = url.trim();
    if (/^https?:\/\//i.test(trimmed)) return trimmed;
    // Bloqueia schemes perigosos (javascript:, data:, file:, etc).
    if (/^[a-z][a-z0-9+\-.]*:/i.test(trimmed)) return null;
    return `https://${trimmed}`;
  };

  const partnerCategories = [
    { icon: Hotel, label: 'Hotelaria', color: 'bg-blue-50 text-blue-600' },
    { icon: Dumbbell, label: 'Ginásios', color: 'bg-green-50 text-green-600' },
    { icon: Stethoscope, label: 'Clínicas', color: 'bg-red-50 text-red-600' },
    { icon: Shield, label: 'Seguros', color: 'bg-purple-50 text-purple-600' },
    { icon: Car, label: 'Rent-a-Car', color: 'bg-amber-50 text-amber-600' },
    { icon: Heart, label: 'Bem-Estar', color: 'bg-pink-50 text-pink-600' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="relative py-20 sm:py-28 overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1600880292203-757bb62b4baf?q=80&w=1280&auto=format&fit=crop"
          srcSet={unsplashSrcSet('https://images.unsplash.com/photo-1600880292203-757bb62b4baf?q=80&auto=format&fit=crop')}
          sizes="100vw"
          alt=""
          aria-hidden="true"
          loading="lazy"
          decoding="async"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-grafite via-grafite/85 to-grafite/50" />
        <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-6">
          <div className="max-w-2xl animate-fade-up">
            <span className="inline-block px-3 py-1.5 bg-white/10 text-white rounded-full text-xs uppercase tracking-wider font-semibold mb-5">
              Parcerias
            </span>
            <h1 className="font-bold text-3xl sm:text-5xl lg:text-6xl text-white mb-4" data-testid="benefits-title">
              Clube de{' '}
              <span className="text-white">Benefícios</span>
            </h1>
            <p className="text-base sm:text-xl text-white/80 max-w-xl leading-relaxed">
              Vantagens exclusivas para os membros da ACCTA
            </p>
          </div>
        </div>
      </section>

      {/* Introduction for Partners */}
      <section className="py-12 sm:py-20 lg:py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="animate-fade-up">
              <h2 className="font-sans font-bold text-4xl text-grafite mb-6">
                Vantagens de ser{' '}
                <span className="text-carmesim">ACCTA</span>
              </h2>
              <p className="text-lg text-gray-600 leading-relaxed mb-6">
                A nossa associação reúne um grupo seleto de <strong className="text-grafite">profissionais altamente qualificados</strong>. 
                Através do Clube de Benefícios, estabelecemos parcerias com empresas de excelência que oferecem 
                condições exclusivas aos nossos membros.
              </p>
              <p className="text-lg text-gray-600 leading-relaxed mb-8">
                Hotéis, ginásios, clínicas, seguros, rent-a-car e muitos outros serviços com descontos especiais 
                para quem faz parte da família ACCTA.
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
              <div className="bg-gradient-to-br from-primary to-[#0A3A5A] rounded-2xl p-8 text-white">
                <Gift className="w-12 h-12 text-carmesim mb-6" />
                <h3 className="font-sans font-bold text-2xl mb-4">Benefícios Exclusivos</h3>
                <ul className="space-y-4">
                  {[
                    'Descontos em estabelecimentos parceiros',
                    'Validação digital via QR Code',
                    'Acesso imediato aos benefícios',
                    'Novos parceiros regularmente',
                    'Condições especiais para família'
                  ].map((item, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-carmesim flex-shrink-0 mt-0.5" />
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
              Simples e Rápido
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
              Como Funciona?
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Um processo totalmente digital e instantâneo
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {[
              {
                step: '01',
                title: 'Carteira Digital',
                desc: 'Os associados possuem uma Carteira Digital com validação via QR Code único.',
                icon: QrCode
              },
              {
                step: '02',
                title: 'Apresentação',
                desc: 'Ao chegar ao estabelecimento parceiro, o sócio apresenta o código da carteira.',
                icon: Building2
              },
              {
                step: '03',
                title: 'Validação Instantânea',
                desc: 'O código é validado em tempo real, garantindo acesso imediato ao desconto.',
                icon: CheckCircle
              }
            ].map((item, index) => (
              <div key={index}
                className="text-center animate-fade-up">
                <div className="relative mb-6">
                  <div className="w-20 h-20 bg-grafite rounded-2xl flex items-center justify-center mx-auto">
                    <item.icon className="w-10 h-10 text-carmesim" />
                  </div>
                  <span className="absolute -top-2 -right-2 w-8 h-8 bg-carmesim rounded-full flex items-center justify-center font-sans font-bold text-grafite text-sm">
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
                Rede de Parceiros
              </span>
              <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
                Nossos Parceiros
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Empresas que confiam na ACCTA e oferecem condições especiais aos nossos membros
              </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {partners.map((partner) => {
                const card = (
                  <div className="card-technical rounded-xl p-8 flex items-center justify-center h-32 animate-fade-up hover:shadow-md transition-shadow">
                    <img
                      src={partner.logo_url}
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
                    aria-label={`Visitar website de ${partner.name}`}
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
              <HandshakeIcon className="w-16 h-16 text-carmesim mb-6" />
              <h2 className="font-sans font-bold text-4xl text-white mb-6">
                Quer ser nosso parceiro?
              </h2>
              <p className="text-xl text-white/80 leading-relaxed">
                Se a sua empresa deseja oferecer serviços aos Controladores de Tráfego Aéreo de Cabo Verde, 
                entre em contacto connosco. Juntos podemos criar uma parceria de sucesso.
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20 animate-fade-up">
              <h3 className="font-sans font-semibold text-xl text-white mb-6">Vantagens para Parceiros</h3>
              <ul className="space-y-4 mb-8">
                {[
                  'Acesso a profissionais qualificados',
                  'Divulgação na nossa rede',
                  'Selo de parceiro ACCTA',
                  'Validação digital integrada'
                ].map((item, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-carmesim flex-shrink-0 mt-0.5" />
                    <span className="text-white/90">{item}</span>
                  </li>
                ))}
              </ul>
              <Link
                to="/contactos"
                className="inline-flex items-center gap-2 bg-confianca text-white px-6 py-3 rounded-lg font-bold hover:bg-confianca-dark transition-all w-full justify-center"
              >
                <Mail className="w-5 h-5" />
                Contactar-nos
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
            É um estabelecimento parceiro?
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            Utilize o nosso validador online para verificar a carteira dos associados
          </p>
          <Link
            to="/validador"
            className="inline-flex items-center gap-2 bg-grafite text-white px-8 py-4 rounded-lg font-bold hover:bg-grafite/90 transition-all"
          >
            Aceder ao Validador
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
};
