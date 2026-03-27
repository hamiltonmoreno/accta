import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { documentsAPI } from '../../utils/api';
import { 
  FileText, 
  Download, 
  Shield, 
  BookOpen,
  Scale,
  BarChart3,
  Calendar,
  ExternalLink,
  CheckCircle,
  Building
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const TransparenciaPage = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPublicDocuments();
  }, []);

  const loadPublicDocuments = async () => {
    try {
      // Note: This would need a public endpoint for documents
      // For now, we'll show placeholder data
      setDocuments([
        {
          id: '1',
          title: 'Estatutos da Associação',
          type: 'estatuto',
          description: 'O conjunto de regras que define os nossos direitos e deveres.',
          file_url: '#',
          created_at: new Date().toISOString()
        },
        {
          id: '2',
          title: 'Código de Ética',
          type: 'estatuto',
          description: 'Os princípios de conduta esperados de cada associado.',
          file_url: '#',
          created_at: new Date().toISOString()
        },
        {
          id: '3',
          title: 'Regulamento Interno',
          type: 'estatuto',
          description: 'Diretrizes operacionais da associação.',
          file_url: '#',
          created_at: new Date().toISOString()
        }
      ]);
    } catch (error) {
      console.error('Erro ao carregar documentos:', error);
    } finally {
      setLoading(false);
    }
  };

  const reports = [
    {
      id: 'r1',
      title: 'Relatório de Contas 2024',
      description: 'Balancete anual aprovado em Assembleia Geral.',
      type: 'balancete',
      year: '2024',
      file_url: '#'
    },
    {
      id: 'r2',
      title: 'Plano de Atividades 2025',
      description: 'As metas e projetos para o próximo ciclo.',
      type: 'plano',
      year: '2025',
      file_url: '#'
    }
  ];

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
          src="https://images.unsplash.com/photo-1618506060789-b63788b0cecd?q=80&w=2070&auto=format&fit=crop"
          alt="Transparencia institucional"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-grafite via-grafite/85 to-grafite/50" />
        <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-2xl"
          >
            <span className="inline-block px-3 py-1.5 bg-carmesim/20 border border-carmesim/40 text-carmesim rounded-full text-xs uppercase tracking-wider font-semibold mb-5">
              Governanca
            </span>
            <h1 className="font-bold text-3xl sm:text-5xl lg:text-6xl text-white mb-4" data-testid="transparency-title">
              Transparencia e{' '}
              <span className="text-carmesim">Prestacao de Contas</span>
            </h1>
            <p className="text-base sm:text-xl text-white/80 max-w-xl leading-relaxed">
              A credibilidade da ACCTA baseia-se na transparencia com os seus associados e com a sociedade
            </p>
          </motion.div>
        </div>
      </section>

      {/* Intro */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="bg-white rounded-2xl p-8 shadow-sm border border-gray-200"
          >
            <Shield className="w-12 h-12 text-carmesim mx-auto mb-4" />
            <p className="text-lg text-gray-600 leading-relaxed">
              Nesta secção, disponibilizamos os documentos que regem a nossa atuação e os relatórios que comprovam 
              a nossa gestão responsável. A transparência é um dos nossos valores fundamentais.
            </p>
          </motion.div>
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
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  className="card-technical rounded-xl p-6 hover:shadow-lg transition-all group"
                >
                  <div className="w-14 h-14 bg-grafite rounded-xl flex items-center justify-center mb-5">
                    <IconComponent className="w-7 h-7 text-carmesim" />
                  </div>
                  <h3 className="font-sans font-semibold text-xl text-grafite mb-3 group-hover:text-carmesim transition-colors">
                    {doc.title}
                  </h3>
                  <p className="text-gray-600 mb-6">{doc.description}</p>
                  <a
                    href={doc.file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-grafite font-semibold hover:text-carmesim transition-colors"
                  >
                    <Download className="w-5 h-5" />
                    Download PDF
                  </a>
                </motion.div>
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

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {reports.map((report, index) => {
              const IconComponent = getDocIcon(report.type);
              return (
                <motion.div
                  key={report.id}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  className="card-technical rounded-xl overflow-hidden"
                >
                  <div className="h-24 bg-gradient-to-r from-primary to-[#0A3A5A] flex items-center px-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-carmesim rounded-lg flex items-center justify-center">
                        <IconComponent className="w-6 h-6 text-grafite" />
                      </div>
                      <div>
                        <span className="text-xs text-carmesim uppercase tracking-wider">{report.year}</span>
                        <h3 className="font-sans font-semibold text-lg text-white">{report.title}</h3>
                      </div>
                    </div>
                  </div>
                  <div className="p-6">
                    <p className="text-gray-600 mb-6">{report.description}</p>
                    <a
                      href={report.file_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 bg-grafite text-white px-5 py-2.5 rounded-lg font-semibold hover:bg-grafite/90 transition-all"
                    >
                      <Download className="w-4 h-4" />
                      Ver Documento
                    </a>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Governance Stats */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="font-sans font-bold text-3xl text-grafite mb-4">
              Indicadores de Governança
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Números que demonstram o nosso compromisso com a gestão responsável
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { value: '60+', label: 'Sócios Ativos', icon: Building },
              { value: '90%', label: 'Taxa de Adimplência', icon: CheckCircle },
              { value: '100%', label: 'Assembleias Realizadas', icon: Calendar },
              { value: '4', label: 'Relatórios Anuais', icon: FileText },
            ].map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="card-technical rounded-xl p-6 text-center"
              >
                <stat.icon className="w-8 h-8 text-carmesim mx-auto mb-3" />
                <div className="font-sans font-bold text-3xl text-grafite mb-1">{stat.value}</div>
                <div className="text-xs text-gray-500 uppercase tracking-wider">{stat.label}</div>
              </motion.div>
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
            className="inline-flex items-center gap-2 bg-carmesim text-grafite px-8 py-4 rounded-lg font-bold hover:bg-carmesim/90 transition-all"
          >
            Fale Conosco
            <ExternalLink className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
};
