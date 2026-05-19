import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { documentsAPI } from '../../utils/api';
import {
  FileText,
  Download,
  Shield,
  BookOpen,
  BarChart3,
  Calendar,
  ExternalLink,
  CheckCircle,
  Scale
} from 'lucide-react';
import { unsplashSrcSet } from '../../utils/unsplash';
import { legislacao } from '../../content/cta';

export const TransparenciaPage = () => {
  const [documents, setDocuments] = useState([]);
  const [reports, setReports] = useState([]);

  useEffect(() => {
    loadPublicDocuments();
  }, []);

  const loadPublicDocuments = async () => {
    try {
      const res = await documentsAPI.getPublic();
      const all = res.data || [];
      setDocuments(all.filter(d => d.type !== 'balancete' && d.type !== 'plano'));
      setReports(all.filter(d => d.type === 'balancete' || d.type === 'plano'));
    } catch {
      setDocuments([]);
      setReports([]);
    }
  };

  const getDocIcon = (type) => {
    switch (type) {
      case 'estatuto': return BookOpen;
      case 'balancete': return BarChart3;
      case 'plano': return Calendar;
      default: return FileText;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="relative py-20 sm:py-28 overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1618506060789-b63788b0cecd?q=80&w=1280&auto=format&fit=crop"
          srcSet={unsplashSrcSet('https://images.unsplash.com/photo-1618506060789-b63788b0cecd?q=80&auto=format&fit=crop')}
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
              Governança
            </span>
            <h1 className="font-bold text-3xl sm:text-5xl lg:text-6xl text-white mb-4" data-testid="transparency-title">
              Transparência e{' '}
              <span className="text-white">Prestação de Contas</span>
            </h1>
            <p className="text-base sm:text-xl text-white/80 max-w-xl leading-relaxed">
              A credibilidade da ACCTA baseia-se na transparência com os seus associados e com a sociedade
            </p>
          </div>
        </div>
      </section>

      {/* Intro */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-200 animate-fade-up">
            <Shield className="w-12 h-12 text-carmesim mx-auto mb-4" />
            <p className="text-lg text-gray-600 leading-relaxed">
              Nesta secção, disponibilizamos os documentos que regem a nossa atuação e os relatórios que comprovam 
              a nossa gestão responsável. A transparência é um dos nossos valores fundamentais.
            </p>
          </div>
        </div>
      </section>

      {/* Institutional Documents */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <span className="inline-block px-4 py-2 bg-grafite/5 text-grafite rounded-full text-sm uppercase tracking-wider mb-4">
              Documentos Institucionais
            </span>
            <h2 className="font-sans font-bold text-3xl text-grafite">
              Regulamentos e Estatutos
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {documents.map((doc, index) => {
              const IconComponent = getDocIcon(doc.type);
              return (
                <div key={doc.id}
                  className="card-technical rounded-xl p-6 hover:shadow-lg transition-all group animate-fade-up">
                  <div className="w-14 h-14 bg-grafite rounded-xl flex items-center justify-center mb-5">
                    <IconComponent className="w-7 h-7 text-white" />
                  </div>
                  <h3 className="font-sans font-semibold text-xl text-grafite mb-3 group-hover:text-carmesim transition-colors">
                    {doc.title}
                  </h3>
                  <p className="text-gray-600 mb-6">{doc.description}</p>
                  <a
                    href={documentsAPI.publicDownloadUrl(doc.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-grafite font-semibold hover:text-carmesim transition-colors"
                  >
                    <Download className="w-5 h-5" />
                    Download PDF
                  </a>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Reports */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <span className="inline-block px-4 py-2 bg-carmesim/10 text-carmesim rounded-full text-sm uppercase tracking-wider mb-4">
              Relatórios de Gestão
            </span>
            <h2 className="font-sans font-bold text-3xl text-grafite">
              Contas e Planos de Atividades
            </h2>
          </div>

          {reports.length === 0 ? (
            <p className="text-center text-gray-400">Nenhum relatório publicado ainda.</p>
          ) : (
            <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {reports.map((report, index) => {
                const IconComponent = getDocIcon(report.type);
                return (
                  <div key={report.id}
                    className="card-technical rounded-xl overflow-hidden animate-fade-up">
                    <div className="h-24 bg-gradient-to-r from-primary to-[#0A3A5A] flex items-center px-6">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-carmesim rounded-lg flex items-center justify-center">
                          <IconComponent className="w-6 h-6 text-grafite" />
                        </div>
                        <div>
                          <span className="text-xs text-white uppercase tracking-wider">{report.year}</span>
                          <h3 className="font-sans font-semibold text-lg text-white">{report.title}</h3>
                        </div>
                      </div>
                    </div>
                    <div className="p-6">
                      <p className="text-gray-600 mb-6">{report.description}</p>
                      <a
                        href={documentsAPI.publicDownloadUrl(report.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 bg-grafite text-white px-5 py-2.5 rounded-lg font-semibold hover:bg-grafite/90 transition-all"
                      >
                        <Download className="w-4 h-4" />
                        Ver Documento
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* Governance Commitments (qualitativo, sem números não oficiais) */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="font-sans font-bold text-3xl text-grafite mb-4">
              Compromissos de Governança
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              O nosso compromisso com uma gestão responsável e prestação de contas aos associados
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: BarChart3, title: 'Prestação de contas', desc: 'Publicamos contas e planos de atividades para consulta.' },
              { icon: Calendar, title: 'Assembleias regulares', desc: 'Decisões estratégicas tomadas em assembleia, com os associados.' },
              { icon: BookOpen, title: 'Documentos públicos', desc: 'Estatutos e regulamentos acessíveis nesta página.' },
              { icon: CheckCircle, title: 'Gestão responsável', desc: 'A transparência é um dos nossos valores fundamentais.' },
            ].map((item, index) => (
              <div key={index}
                className="card-technical rounded-xl p-6 text-center animate-fade-up">
                <item.icon className="w-8 h-8 text-carmesim mx-auto mb-3" />
                <div className="font-sans font-semibold text-lg text-grafite mb-2">{item.title}</div>
                <div className="text-sm text-gray-600">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Legislação e Regulamentos (base de conhecimento) */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <span className="inline-block px-4 py-2 bg-grafite/5 text-grafite rounded-full text-sm uppercase tracking-wider mb-4">
              Base de Conhecimento
            </span>
            <h2 className="font-sans font-bold text-3xl text-grafite mb-4">
              Legislação e Regulamentos
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              O Código Aeronáutico é a base legal superior; os regulamentos CV-CAR detalham a
              implementação técnica aplicável aos controladores de tráfego aéreo
            </p>
          </div>

          <div className="space-y-4 max-w-5xl mx-auto">
            {legislacao.map((lei, index) => (
              <div key={index}
                className="card-technical rounded-xl p-6 animate-fade-up sm:flex sm:items-start sm:gap-5">
                <div className="w-12 h-12 bg-grafite rounded-lg flex items-center justify-center flex-shrink-0 mb-4 sm:mb-0">
                  <Scale className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-3 mb-2">
                    <h3 className="font-sans font-semibold text-grafite">{lei.documento}</h3>
                    <span className="px-2.5 py-0.5 bg-gray-100 text-grafite rounded-full text-xs font-medium">
                      {lei.natureza}
                    </span>
                  </div>
                  <p className="text-sm text-grafite mb-1">{lei.tema}</p>
                  <p className="text-sm text-gray-500">{lei.relevancia}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-grafite">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-sans font-bold text-3xl text-white mb-6">
            Tem dúvidas sobre os nossos documentos?
          </h2>
          <p className="text-lg text-white/80 mb-8">
            Entre em contacto connosco para mais informações sobre a governança da ACCTA
          </p>
          <Link
            to="/contactos"
            className="inline-flex items-center gap-2 bg-carmesim text-white px-8 py-4 rounded-lg font-bold hover:bg-carmesim/90 transition-all"
          >
            Fale Conosco
            <ExternalLink className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
};
