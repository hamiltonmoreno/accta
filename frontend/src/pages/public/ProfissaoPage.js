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
import { PageBanner } from '../../components/PageBanner';
import { ProfissaoDestaques } from '../../components/ProfissaoDestaques';
import { TextoInstituicoes } from '../../components/TextoInstituicoes';
import { FontesOficiais } from '../../components/FontesOficiais';
import { FirMap } from '../../components/FirMap';
import { useI18n, useCta } from '../../i18n';
import { usePageMeta } from '../../i18n/usePageMeta';

const TIPO_ICONS = { TWR: Building2, APP: Radar, ACC: Globe };
const REQ_ICONS = [Users, GraduationCap, Radio, Languages, Heart];

export const ProfissaoPage = () => {
  const { t, lp } = useI18n();
  const {
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
    notaFonte,
  } = useCta();
  usePageMeta('profissao');
  return (
    <div className="min-h-screen bg-gray-50">
      <PageBanner pageKey="profissao" title={t('profissao.banner.title')} subtitle={t('profissao.banner.subtitle')} />

      {/* Introduction */}
      <section className="py-12 sm:py-20 lg:py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="animate-fade-up">
              <h2 className="font-sans font-bold text-3xl md:text-4xl text-grafite mb-8">
                {t('profissao.intro.titleA')}{' '}
                <span className="text-carmesim">{t('profissao.intro.titleHighlight')}</span>
              </h2>
              <div className="space-y-6 text-lg text-gray-600 leading-relaxed">
                <p>{definicaoCTA.resumo}</p>
                <p>
                  {t('profissao.intro.p2a')} <span className="text-carmesim font-semibold">{t('profissao.intro.p2Highlight')}</span>{t('profissao.intro.p2b')}
                </p>
                <p className="text-sm text-gray-500">
                  {t('profissao.baseLegal')} {definicaoCTA.baseLegal}.
                </p>
              </div>
            </div>

            <div className="animate-fade-up">
              <div className="bg-white card-technical rounded-2xl p-8">
                <h3 className="font-sans font-bold text-2xl text-grafite mb-6">{t('profissao.intro.responsibilities')}</h3>
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
              {t('profissao.tipos.badge')}
            </span>
            <h2 className="font-sans font-bold text-3xl md:text-4xl text-grafite mb-4">
              {t('profissao.tipos.title')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('profissao.tipos.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {tiposControlo.map((tipo) => {
              const Icon = TIPO_ICONS[tipo.sigla] || Radio;
              return (
                <div key={tipo.sigla} className="card-technical card-hover rounded-2xl p-8 animate-fade-up">
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
              {t('profissao.tipos.qualificacoes')}
            </h3>
            <p className="text-sm text-gray-500 text-center mb-8">{t('profissao.baseLegal')} {qualificacoes.baseLegal}</p>
            <div className="grid sm:grid-cols-2 gap-4">
              {qualificacoes.lista.map((q) => (
                <div key={q.sigla} className="flex items-start gap-3 card-technical card-hover rounded-xl p-5 animate-fade-up">
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
              {t('profissao.ats.badge')}
            </span>
            <h2 className="font-sans font-bold text-3xl md:text-4xl text-grafite mb-4">
              {t('profissao.ats.title')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('profissao.ats.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {camadas.map((c) => (
              <div key={c.sigla} className="card-technical card-hover rounded-xl p-6 animate-fade-up">
                <div className="w-12 h-12 bg-grafite rounded-lg flex items-center justify-center mb-4">
                  <Building2 className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-sans font-bold text-lg text-grafite mb-1">{c.nome}</h3>
                <p className="text-xs text-carmesim uppercase tracking-wider font-semibold mb-3">{c.papel}</p>
                <p className="text-sm text-gray-600 leading-relaxed mb-3">
                  <TextoInstituicoes texto={c.descricao} />
                </p>
                <p className="text-xs text-gray-500">{c.baseLegal}</p>
              </div>
            ))}
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* FIR */}
            <div className="card-technical card-hover rounded-2xl p-8 animate-fade-up">
              <div className="flex items-center gap-3 mb-4">
                <Globe className="w-7 h-7 text-carmesim" />
                <h3 className="font-sans font-bold text-2xl text-grafite">{fir.nome}</h3>
              </div>
              <p className="text-gray-600 leading-relaxed mb-4">
                <TextoInstituicoes texto={fir.descricao} />
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><strong className="text-grafite">{t('profissao.baseLegal')}</strong> {fir.baseLegal}</li>
                <li><strong className="text-grafite">{t('profissao.ats.comunicacoes')}</strong> {fir.comunicacoes}</li>
                <li><strong className="text-grafite">{t('profissao.ats.vigilancia')}</strong> {fir.vigilancia}</li>
                <li><strong className="text-grafite">UTA/UIR:</strong> {fir.utaUir}</li>
              </ul>
            </div>

            {/* Órgãos ATS + infraestrutura */}
            <div className="space-y-6">
              <div className="card-technical card-hover rounded-2xl p-8 animate-fade-up">
                <div className="flex items-center gap-3 mb-4">
                  <MapPin className="w-7 h-7 text-carmesim" />
                  <h3 className="font-sans font-bold text-2xl text-grafite">{t('profissao.ats.orgaos')}</h3>
                </div>
                <dl className="space-y-3 text-sm">
                  <div>
                    <dt className="text-xs text-gray-500 uppercase tracking-wider">{t('profissao.ats.acc')}</dt>
                    <dd className="text-grafite font-medium">{unidades.acc.join(' · ')}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500 uppercase tracking-wider">{t('profissao.ats.twr')}</dt>
                    <dd className="text-grafite font-medium">{unidades.twr.join(' · ')}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500 uppercase tracking-wider">{t('profissao.ats.fis')}</dt>
                    <dd className="text-grafite font-medium">{unidades.fis.join(' · ')}</dd>
                  </div>
                </dl>
              </div>
              <div className="card-technical card-hover rounded-2xl p-8 animate-fade-up">
                <div className="flex items-center gap-3 mb-3">
                  <Plane className="w-7 h-7 text-carmesim" />
                  <h3 className="font-sans font-bold text-xl text-grafite">{t('profissao.ats.infraestrutura')}</h3>
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
              {t('profissao.carreira.badge')}
            </span>
            <h2 className="font-sans font-bold text-3xl md:text-4xl text-grafite mb-4">
              {t('profissao.carreira.title')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              <TextoInstituicoes texto={t('profissao.carreira.subtitle')} />
            </p>
          </div>

          {/* Timeline */}
          <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-6 mb-20">
            {caminhoCTA.map((fase, i) => (
              <div key={fase.etapa} className="card-technical card-hover rounded-xl p-6 animate-fade-up">
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
            <h3 className="font-sans font-semibold text-2xl text-grafite mb-8 text-center">{t('profissao.carreira.requisitos')}</h3>
            <div className="grid sm:grid-cols-2 gap-6">
              {requisitos.map((req, index) => {
                const Icon = REQ_ICONS[index] || CheckCircle;
                return (
                  <div key={index} className="card-technical card-hover rounded-xl p-6 flex gap-5 animate-fade-up">
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
              {t('profissao.licenciamento.badge')}
            </span>
            <h2 className="font-sans font-bold text-3xl md:text-4xl text-grafite mb-4">
              {t('profissao.licenciamento.title')}
            </h2>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-6 mb-12 max-w-4xl mx-auto flex items-start gap-4">
            <Shield className="w-6 h-6 text-carmesim flex-shrink-0 mt-1" />
            <p className="text-gray-600 text-sm">{notaRegulatoria}</p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Recência */}
            <div className="card-technical card-hover rounded-2xl p-8 animate-fade-up">
              <div className="flex items-center gap-3 mb-4">
                <Clock className="w-7 h-7 text-carmesim" />
                <h3 className="font-sans font-bold text-xl text-grafite">{t('profissao.licenciamento.recencia')}</h3>
              </div>
              <ul className="space-y-3">
                {recencia.pontos.map((p, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                    <CheckCircle className="w-4 h-4 text-carmesim flex-shrink-0 mt-0.5" />
                    <span>{p}</span>
                  </li>
                ))}
              </ul>
              <p className="text-xs text-gray-500 mt-4">{t('profissao.baseLegal')} {recencia.baseLegal}</p>
            </div>

            {/* Reentrada */}
            <div className="card-technical card-hover rounded-2xl p-8 animate-fade-up">
              <div className="flex items-center gap-3 mb-4">
                <Scale className="w-7 h-7 text-carmesim" />
                <h3 className="font-sans font-bold text-xl text-grafite">{t('profissao.licenciamento.reentrada')}</h3>
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
              <p className="text-xs text-gray-500 mt-4">{t('profissao.baseLegal')} {reentrada.baseLegal}</p>
            </div>

            {/* Conversão */}
            <div className="card-technical card-hover rounded-2xl p-8 animate-fade-up">
              <div className="flex items-center gap-3 mb-4">
                <FileText className="w-7 h-7 text-carmesim" />
                <h3 className="font-sans font-bold text-xl text-grafite">{t('profissao.licenciamento.conversao')}</h3>
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
              {t('profissao.formacao.badge')}
            </span>
            <h2 className="font-sans font-bold text-3xl md:text-4xl text-grafite mb-4">
              {t('profissao.formacao.title')}
            </h2>
            <p className="text-sm text-gray-500 max-w-2xl mx-auto">{notaFonte}</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-12">
            {ato.map((a) => (
              <div key={a.nome} className="card-technical card-hover rounded-2xl p-8 animate-fade-up">
                <div className="flex items-center gap-3 mb-4">
                  <GraduationCap className="w-7 h-7 text-carmesim" />
                  <div>
                    <h3 className="font-sans font-bold text-xl text-grafite">{a.nome}</h3>
                    <p className="text-sm text-gray-500">{a.pais} · {a.certificado}</p>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-3">{a.escopo}</p>
                <p className="text-xs text-gray-500">
                  {t('profissao.formacao.validade', { validade: a.validade })}
                </p>
              </div>
            ))}
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {caminhos.map((c) => (
              <div key={c.titulo} className="card-technical card-hover rounded-xl p-6 animate-fade-up">
                <h4 className="font-sans font-semibold text-lg text-grafite mb-2">{c.titulo}</h4>
                <p className="text-sm text-gray-600">{c.desc}</p>
              </div>
            ))}
            <div className="card-technical card-hover rounded-xl p-6 animate-fade-up">
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
            backgroundImage: 'radial-gradient(circle at 30% 50%, rgba(255,255,255,0.06) 0%, transparent 50%)',
          }} />
        </div>
        <div className="relative z-10 max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <FirMap />

            <div className="animate-fade-up">
              <span className="inline-block px-4 py-2 bg-white/10 text-white rounded-full text-sm uppercase tracking-wider mb-6">
                {t('profissao.espaco.badge')}
              </span>
              <h2 className="font-sans font-bold text-3xl md:text-4xl text-white mb-6">
                {t('profissao.espaco.title', { fir: fir.nome })}
              </h2>
              <p className="text-xl text-white/80 leading-relaxed mb-6">
                {fir.descricao}
              </p>
              <p className="text-lg text-white/85 leading-relaxed mb-8">
                {t('profissao.espaco.texto')}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center">
                  <div className="font-sans font-bold text-2xl text-white mb-1">DL 9/80</div>
                  <div className="text-xs text-white/60 uppercase tracking-wider">{t('profissao.espaco.decreto')}</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center">
                  <div className="font-sans font-bold text-3xl text-white mb-1">24/7</div>
                  <div className="text-xs text-white/60 uppercase tracking-wider">{t('profissao.espaco.operacao')}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Cat 5 F4 — destaques dinâmicos: defesa publicada, relações, formações públicas */}
      <ProfissaoDestaques />

      {/* Sub-projeto C — fontes oficiais com hiperligação */}
      <FontesOficiais />

      {/* CTA Section */}
      <section className="py-12 sm:py-20 lg:py-24 bg-white">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-sans font-bold text-3xl md:text-4xl text-grafite mb-6">
            {t('profissao.cta.title')}
          </h2>
          <p className="text-xl text-gray-600 mb-10">
            {t('profissao.cta.subtitle')}
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to={lp('/sobre')}
              className="inline-flex items-center gap-2 bg-floresta text-white px-8 py-4 rounded-lg font-bold text-lg hover:bg-floresta-dark transition-all"
            >
              {t('profissao.cta.sobre')}
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to={lp('/contactos')}
              className="inline-flex items-center gap-2 border-2 border-[#D1D5DB] text-grafite px-8 py-4 rounded-lg font-bold text-lg hover:bg-gray-50 transition-all"
            >
              {t('profissao.cta.contacto')}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
