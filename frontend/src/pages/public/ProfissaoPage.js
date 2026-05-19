import React from 'react';
import { Link } from 'react-router-dom';
import {
  Radio,
  Globe,
  Plane,
  Building2,
  Radar,
  GraduationCap,
  Languages,
  Heart,
  ArrowRight,
  CheckCircle,
  Users,
  Clock,
  MapPin,
  Shield,
  Scale,
  FileText
} from 'lucide-react';
import { unsplashSrcSet } from '../../utils/unsplash';
import {
  definicaoCTA,
  responsabilidades,
  tiposControlo,
  qualificacoes,
  caminhoCTA,
  camadas,
  fir,
  unidades,
  infraestrutura,
  requisitos,
  recencia,
  reentrada,
  conversao,
  notaRegulatoria,
  ato,
  caminhos,
  academico,
  notaFonte
} from '../../content/cta';

const TIPO_ICONS = { TWR: Building2, APP: Radar, ACC: Globe };
const REQ_ICONS = [Users, GraduationCap, Radio, Languages, Heart];

export const ProfissaoPage = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="relative py-20 sm:py-28 overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1540962351504-03099e0a754b?q=80&w=1280&auto=format&fit=crop"
          srcSet={unsplashSrcSet('https://images.unsplash.com/photo-1540962351504-03099e0a754b?q=80&auto=format&fit=crop')}
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
            <span className="inline-block px-3 py-1.5 bg-carmesim/20 border border-carmesim/40 text-white rounded-full text-xs uppercase tracking-wider font-semibold mb-5">
              Base de conhecimento
            </span>
            <h1 className="font-bold text-3xl sm:text-5xl lg:text-6xl text-white mb-4" data-testid="profession-title">
              O que é ser um{' '}
              <span className="text-white">Controlador de Tráfego Aéreo?</span>
            </h1>
            <p className="text-base sm:text-xl text-white/80 max-w-xl leading-relaxed">
              Uma profissão de raciocínio rápido, alta responsabilidade e precisão absoluta
            </p>
          </div>
        </div>
      </section>

      {/* Introduction */}
      <section className="py-12 sm:py-20 lg:py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="animate-fade-up">
              <h2 className="font-sans font-bold text-4xl text-grafite mb-8">
                O profissional que guia os{' '}
                <span className="text-carmesim">Céus</span>
              </h2>
              <div className="space-y-6 text-lg text-gray-600 leading-relaxed">
                <p>{definicaoCTA.resumo}</p>
                <p>
                  É uma profissão que exige <span className="text-carmesim font-semibold">concentração extrema</span>,
                  capacidade de decidir rapidamente sob pressão e comunicação clara e precisa em inglês técnico.
                </p>
                <p className="text-sm text-gray-500">
                  Base legal: {definicaoCTA.baseLegal}.
                </p>
              </div>
            </div>

            <div className="animate-fade-up">
              <div className="bg-white card-technical rounded-2xl p-8">
                <h3 className="font-sans font-bold text-2xl text-grafite mb-6">Principais Responsabilidades</h3>
                <ul className="space-y-4">
                  {responsabilidades.map((item, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-carmesim flex-shrink-0 mt-0.5" />
                      <span className="text-gray-600">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Types of Control */}
      <section className="py-12 sm:py-20 lg:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-carmesim/10 text-carmesim rounded-full text-sm uppercase tracking-wider mb-6">
              Tipos de Controlo
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
              Os Tipos de Controlo em Cabo Verde
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              O serviço de controlo de tráfego aéreo desdobra-se, no CV-CAR 17, em controlo de aeródromo,
              de aproximação e de área
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {tiposControlo.map((tipo) => {
              const Icon = TIPO_ICONS[tipo.sigla] || Radio;
              return (
                <div key={tipo.sigla} className="card-technical rounded-2xl p-8 animate-fade-up">
                  <div className="w-14 h-14 bg-grafite rounded-xl flex items-center justify-center mb-5">
                    <Icon className="w-7 h-7 text-white" />
                  </div>
                  <div className="flex items-center gap-3 mb-4">
                    <span className="px-3 py-1 bg-gray-100 text-grafite rounded-full text-sm font-bold">{tipo.sigla}</span>
                    <h3 className="font-sans font-bold text-xl text-grafite">{tipo.nome}</h3>
                  </div>
                  <p className="text-gray-600 leading-relaxed mb-4">{tipo.descricao}</p>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">{tipo.detalheLabel}</div>
                    <p className="text-sm text-grafite font-medium">{tipo.detalhe}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Qualificações */}
          <div className="mt-16 max-w-4xl mx-auto">
            <h3 className="font-sans font-bold text-2xl text-grafite mb-2 text-center">
              As cinco qualificações de CTA
            </h3>
            <p className="text-sm text-gray-500 text-center mb-8">Base legal: {qualificacoes.baseLegal}</p>
            <div className="grid sm:grid-cols-2 gap-4">
              {qualificacoes.lista.map((q) => (
                <div key={q.sigla} className="flex items-start gap-3 card-technical rounded-xl p-5 animate-fade-up">
                  <CheckCircle className="w-5 h-5 text-carmesim flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-grafite">{q.sigla}</div>
                    <div className="text-sm text-gray-600">{q.nome}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ATS Structure */}
      <section className="py-12 sm:py-20 lg:py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-grafite/5 text-grafite rounded-full text-sm uppercase tracking-wider mb-6">
              Estrutura ATS
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
              Quem faz o quê na navegação aérea
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              A navegação aérea de Cabo Verde organiza-se em quatro camadas funcionais
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {camadas.map((c) => (
              <div key={c.sigla} className="card-technical rounded-xl p-6 animate-fade-up">
                <div className="w-12 h-12 bg-grafite rounded-lg flex items-center justify-center mb-4">
                  <Building2 className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-sans font-bold text-lg text-grafite mb-1">{c.nome}</h3>
                <p className="text-xs text-carmesim uppercase tracking-wider font-semibold mb-3">{c.papel}</p>
                <p className="text-sm text-gray-600 leading-relaxed mb-3">{c.descricao}</p>
                <p className="text-xs text-gray-500">{c.baseLegal}</p>
              </div>
            ))}
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* FIR */}
            <div className="card-technical rounded-2xl p-8 animate-fade-up">
              <div className="flex items-center gap-3 mb-4">
                <Globe className="w-7 h-7 text-carmesim" />
                <h3 className="font-sans font-bold text-2xl text-grafite">{fir.nome}</h3>
              </div>
              <p className="text-gray-600 leading-relaxed mb-4">{fir.descricao}</p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><strong className="text-grafite">Base legal:</strong> {fir.baseLegal}</li>
                <li><strong className="text-grafite">Comunicações:</strong> {fir.comunicacoes}</li>
                <li><strong className="text-grafite">Vigilância:</strong> {fir.vigilancia}</li>
                <li><strong className="text-grafite">UTA/UIR:</strong> {fir.utaUir}</li>
              </ul>
            </div>

            {/* Órgãos ATS + infraestrutura */}
            <div className="space-y-6">
              <div className="card-technical rounded-2xl p-8 animate-fade-up">
                <div className="flex items-center gap-3 mb-4">
                  <MapPin className="w-7 h-7 text-carmesim" />
                  <h3 className="font-sans font-bold text-2xl text-grafite">Órgãos ATS (operados pela ASA)</h3>
                </div>
                <dl className="space-y-3 text-sm">
                  <div>
                    <dt className="text-xs text-gray-500 uppercase tracking-wider">Centro de Controlo</dt>
                    <dd className="text-grafite font-medium">{unidades.acc.join(' · ')}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500 uppercase tracking-wider">Torres de Controlo</dt>
                    <dd className="text-grafite font-medium">{unidades.twr.join(' · ')}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500 uppercase tracking-wider">Serviço de Informação de Voo</dt>
                    <dd className="text-grafite font-medium">{unidades.fis.join(' · ')}</dd>
                  </div>
                </dl>
              </div>
              <div className="card-technical rounded-2xl p-8 animate-fade-up">
                <div className="flex items-center gap-3 mb-3">
                  <Plane className="w-7 h-7 text-carmesim" />
                  <h3 className="font-sans font-bold text-xl text-grafite">Infraestrutura aeroportuária</h3>
                </div>
                <p className="text-sm text-gray-600">{infraestrutura.resumo}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How to Become — timeline + requisitos */}
      <section className="py-12 sm:py-20 lg:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-carmesim/10 text-carmesim rounded-full text-sm uppercase tracking-wider mb-6">
              Carreira
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
              Como se tornar um Controlador
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              É um percurso seletivo e exigente, que segue padrões internacionais (ICAO) e é
              regulado pela AAC — Agência de Aviação Civil (Decreto-Lei n.º 47/2019), com a
              disciplina técnica a vir dos regulamentos CV-CAR
            </p>
          </div>

          {/* Timeline */}
          <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-6 mb-20">
            {caminhoCTA.map((fase, i) => (
              <div key={fase.etapa} className="card-technical rounded-xl p-6 animate-fade-up">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-9 h-9 rounded-full bg-grafite text-white flex items-center justify-center font-bold text-sm">
                    {i + 1}
                  </div>
                  <h3 className="font-sans font-semibold text-grafite">{fase.etapa}</h3>
                </div>
                <ul className="space-y-2">
                  {fase.itens.map((it, k) => (
                    <li key={k} className="flex items-start gap-2 text-sm text-gray-600">
                      <CheckCircle className="w-4 h-4 text-carmesim flex-shrink-0 mt-0.5" />
                      <span>{it}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Requisitos */}
          <div className="max-w-4xl mx-auto">
            <h3 className="font-sans font-semibold text-2xl text-grafite mb-8 text-center">Requisitos essenciais</h3>
            <div className="grid sm:grid-cols-2 gap-6">
              {requisitos.map((req, index) => {
                const Icon = REQ_ICONS[index] || CheckCircle;
                return (
                  <div key={index} className="card-technical rounded-xl p-6 flex gap-5 animate-fade-up">
                    <div className="w-14 h-14 bg-gray-100 text-grafite rounded-xl flex items-center justify-center flex-shrink-0">
                      <Icon className="w-7 h-7" />
                    </div>
                    <div>
                      <h4 className="font-sans font-semibold text-lg text-grafite mb-2">{req.titulo}</h4>
                      <p className="text-gray-600 text-sm mb-2">{req.desc}</p>
                      <p className="text-xs text-carmesim font-semibold">{req.baseLegal}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Licensing, recency and validity */}
      <section className="py-12 sm:py-20 lg:py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-grafite/5 text-grafite rounded-full text-sm uppercase tracking-wider mb-6">
              Licenciamento
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
              Licenciamento, recência e validade
            </h2>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-6 mb-12 max-w-4xl mx-auto flex items-start gap-4">
            <Shield className="w-6 h-6 text-carmesim flex-shrink-0 mt-1" />
            <p className="text-gray-600 text-sm">{notaRegulatoria}</p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Recência */}
            <div className="card-technical rounded-2xl p-8 animate-fade-up">
              <div className="flex items-center gap-3 mb-4">
                <Clock className="w-7 h-7 text-carmesim" />
                <h3 className="font-sans font-bold text-xl text-grafite">Recência e validade</h3>
              </div>
              <ul className="space-y-3">
                {recencia.pontos.map((p, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                    <CheckCircle className="w-4 h-4 text-carmesim flex-shrink-0 mt-0.5" />
                    <span>{p}</span>
                  </li>
                ))}
              </ul>
              <p className="text-xs text-gray-500 mt-4">Base legal: {recencia.baseLegal}</p>
            </div>

            {/* Reentrada */}
            <div className="card-technical rounded-2xl p-8 animate-fade-up">
              <div className="flex items-center gap-3 mb-4">
                <Scale className="w-7 h-7 text-carmesim" />
                <h3 className="font-sans font-bold text-xl text-grafite">Reentrada operacional</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">{reentrada.intro}</p>
              <ul className="space-y-3">
                {reentrada.escalonamento.map((e, i) => (
                  <li key={i} className="text-sm">
                    <span className="font-semibold text-grafite">{e.periodo}:</span>{' '}
                    <span className="text-gray-600">{e.medida}</span>
                  </li>
                ))}
              </ul>
              <p className="text-xs text-gray-500 mt-4">Base legal: {reentrada.baseLegal}</p>
            </div>

            {/* Conversão */}
            <div className="card-technical rounded-2xl p-8 animate-fade-up">
              <div className="flex items-center gap-3 mb-4">
                <FileText className="w-7 h-7 text-carmesim" />
                <h3 className="font-sans font-bold text-xl text-grafite">Conversão de licença estrangeira</h3>
              </div>
              <ol className="space-y-3 list-decimal list-inside">
                {conversao.passos.map((p, i) => (
                  <li key={i} className="text-sm text-gray-600">{p}</li>
                ))}
              </ol>
              <p className="text-xs text-gray-500 mt-4">{conversao.baseLegal}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Training */}
      <section className="py-12 sm:py-20 lg:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-carmesim/10 text-carmesim rounded-full text-sm uppercase tracking-wider mb-6">
              Formação
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
              Onde formar-se
            </h2>
            <p className="text-sm text-gray-500 max-w-2xl mx-auto">{notaFonte}</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-12">
            {ato.map((a) => (
              <div key={a.nome} className="card-technical rounded-2xl p-8 animate-fade-up">
                <div className="flex items-center gap-3 mb-4">
                  <GraduationCap className="w-7 h-7 text-carmesim" />
                  <div>
                    <h3 className="font-sans font-bold text-xl text-grafite">{a.nome}</h3>
                    <p className="text-sm text-gray-500">{a.pais} · {a.certificado}</p>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-3">{a.escopo}</p>
                <p className="text-xs text-gray-500">
                  Validade do certificado (à data desta publicação): {a.validade}
                </p>
              </div>
            ))}
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {caminhos.map((c) => (
              <div key={c.titulo} className="card-technical rounded-xl p-6 animate-fade-up">
                <h4 className="font-sans font-semibold text-lg text-grafite mb-2">{c.titulo}</h4>
                <p className="text-sm text-gray-600">{c.desc}</p>
              </div>
            ))}
            <div className="card-technical rounded-xl p-6 animate-fade-up">
              <h4 className="font-sans font-semibold text-lg text-grafite mb-2">{academico.titulo}</h4>
              <p className="text-sm text-gray-600">{academico.desc}</p>
            </div>
          </div>
        </div>
      </section>

      {/* FIR Section — bloco de design adjacente (gradiente legado) registado
          na spec §8 para tratamento separado; conteúdo atualizado, estilo
          mantido intencionalmente intacto. */}
      <section className="py-12 sm:py-20 lg:py-24 bg-grafite relative overflow-hidden">
        <div className="absolute inset-0 opacity-20">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 30% 50%, rgba(0,255,156,0.3) 0%, transparent 50%)',
          }} />
        </div>
        <div className="relative z-10 max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="animate-fade-up">
              <div className="relative">
                <div className="w-80 h-80 mx-auto border-2 border-white/20 rounded-full flex items-center justify-center">
                  <div className="w-60 h-60 border border-white/15 rounded-full flex items-center justify-center">
                    <div className="w-40 h-40 bg-white/5 rounded-full flex items-center justify-center">
                      <Globe className="w-20 h-20 text-white" />
                    </div>
                  </div>
                </div>
                <div className="absolute top-10 right-10">
                  <Plane className="w-8 h-8 text-white animate-pulse" />
                </div>
                <div className="absolute bottom-20 left-5">
                  <Plane className="w-6 h-6 text-white/70 -rotate-45" />
                </div>
              </div>
            </div>

            <div className="animate-fade-up">
              <span className="inline-block px-4 py-2 bg-white/10 text-white rounded-full text-sm uppercase tracking-wider mb-6">
                Espaço Aéreo
              </span>
              <h2 className="font-sans font-bold text-4xl text-white mb-6">
                A {fir.nome}: um espaço estratégico
              </h2>
              <p className="text-xl text-white/80 leading-relaxed mb-6">
                {fir.descricao}
              </p>
              <p className="text-lg text-white/70 leading-relaxed mb-8">
                Os controladores cabo-verdianos asseguram diariamente a passagem segura de voos
                intercontinentais por este corredor vital entre a Europa, África e as Américas.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center">
                  <div className="font-sans font-bold text-2xl text-white mb-1">DL 9/80</div>
                  <div className="text-xs text-white/60 uppercase tracking-wider">Decreto que criou a FIR</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center">
                  <div className="font-sans font-bold text-3xl text-white mb-1">24/7</div>
                  <div className="text-xs text-white/60 uppercase tracking-wider">Operação contínua</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-12 sm:py-20 lg:py-24 bg-white">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-sans font-bold text-4xl text-grafite mb-6">
            Quer conhecer a nossa associação?
          </h2>
          <p className="text-xl text-gray-600 mb-10">
            A ACCTA representa e defende os interesses dos controladores de tráfego aéreo em Cabo Verde
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/sobre"
              className="inline-flex items-center gap-2 bg-carmesim text-white px-8 py-4 rounded-lg font-bold text-lg hover:bg-carmesim-dark transition-all"
            >
              Sobre a ACCTA
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/contactos"
              className="inline-flex items-center gap-2 border-2 border-[#D1D5DB] text-grafite px-8 py-4 rounded-lg font-bold text-lg hover:bg-gray-50 transition-all"
            >
              Entre em Contacto
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
