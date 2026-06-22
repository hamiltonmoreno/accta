import React from 'react';
import { Link } from 'react-router-dom';
import { PageBanner } from '../../components/PageBanner';
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

// Capacidades centrais do sistema — mapeadas aos módulos reais do portal.
// Texto factual, sem números/estatísticas nem promessas comerciais
// (regra editorial da área pública).
const capacidades = [
  {
    icon: Users,
    title: 'Gestão de sócios',
    desc: 'Registo, perfis e estados de cada sócio, com cargos e órgãos sociais sempre atualizados.',
  },
  {
    icon: Wallet,
    title: 'Quotas e finanças',
    desc: 'Quotas, jóia e transações reunidas num fluxo financeiro central e organizado.',
  },
  {
    icon: BarChart3,
    title: 'Transparência',
    desc: 'Prestação de contas, balancetes e exercícios acessíveis aos sócios.',
  },
  {
    icon: CalendarDays,
    title: 'Eventos',
    desc: 'Divulgação e inscrições, com os custos e receitas de cada evento ligados ao caixa.',
  },
  {
    icon: Vote,
    title: 'Votações e assembleias',
    desc: 'Deliberações, eleições com voto secreto e participação dos sócios num só lugar.',
  },
  {
    icon: Megaphone,
    title: 'Comunicação',
    desc: 'Comunicados segmentados e notificações que chegam a quem precisa de os receber.',
  },
];

// Pilares de enquadramento mostrados ao lado da introdução.
const pilares = [
  {
    icon: LayoutGrid,
    title: 'Tudo num só lugar',
    desc: 'Sócios, finanças, eventos e governança deixam de viver em folhas e caixas de correio dispersas.',
  },
  {
    icon: ShieldCheck,
    title: 'Acessos por função',
    desc: 'Cada pessoa vê e faz apenas o que o seu papel permite, com registo das ações administrativas.',
  },
];

export const PlataformaPage = () => {
  // O site não usa react-helmet; definimos o título por página de forma simples.
  React.useEffect(() => {
    const anterior = document.title;
    document.title = 'A plataforma | ACCTA';
    return () => {
      document.title = anterior;
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <PageBanner
        pageKey="plataforma"
        badge="A plataforma"
        title="Um sistema feito para gerir associações"
        subtitle="A tecnologia que sustenta o portal da ACCTA, pensada para a gestão do dia a dia de uma associação."
        icon={LayoutGrid}
      />

      {/* Introdução — o que é a plataforma */}
      <section className="py-12 sm:py-20 lg:py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            <div className="animate-fade-up">
              <h2 className="font-sans font-bold text-2xl sm:text-4xl text-grafite mb-6">
                Uma plataforma de <span className="text-carmesim">gestão de associações</span>
              </h2>
              <div className="space-y-5 text-base sm:text-lg text-gray-600 leading-relaxed">
                <p>
                  O portal da ACCTA assenta num sistema digital que reúne, num só
                  lugar, aquilo que uma associação precisa de gerir: os seus sócios,
                  as suas contas, os seus eventos e os seus processos de decisão.
                </p>
                <p>
                  Em vez de informação dispersa por folhas de cálculo e mensagens
                  avulsas, cada área tem o seu espaço próprio — organizado, acessível
                  aos sócios e preparado para o trabalho corrente dos órgãos sociais.
                </p>
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
              O que faz
            </span>
            <h2 className="font-sans font-bold text-2xl sm:text-4xl text-grafite">
              Os módulos que sustentam a associação
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
            Construído para o trabalho real de uma associação
          </h2>
          <p className="text-base sm:text-lg text-gray-600 leading-relaxed">
            Esta plataforma nasceu das necessidades concretas da ACCTA e continua
            a evoluir com elas. Os sócios acedem à sua área através do{' '}
            <Link to="/login" className="text-carmesim font-semibold hover:text-carmesim-dark transition-colors">
              portal
            </Link>
            .
          </p>
        </div>
      </section>
    </div>
  );
};

export default PlataformaPage;
