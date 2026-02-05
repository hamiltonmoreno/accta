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
    <div className="min-h-screen bg-slate-50">
      {/* Hero Section */}
      <section className="relative py-24 bg-primary overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{ 
            backgroundImage: 'linear-gradient(rgba(0,255,156,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,156,0.3) 1px, transparent 1px)',
            backgroundSize: '40px 40px'
          }} />
        </div>
        <div className="relative z-10 max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <span className="inline-block px-4 py-2 bg-accent/10 border border-accent/30 text-accent rounded-full font-mono text-sm uppercase tracking-wider mb-6">
              Governança
            </span>
            <h1 className="font-outfit font-bold text-5xl lg:text-6xl text-white mb-6" data-testid="transparency-title">
              Transparência e{' '}
              <span className="text-accent">Prestação de Contas</span>
            </h1>
            <p className="text-xl text-white/80 max-w-3xl mx-auto leading-relaxed">
              A credibilidade da ACCTA baseia-se na transparência com os seus associados e com a sociedade
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
            className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200"
          >
            <Shield className="w-12 h-12 text-accent mx-auto mb-4" />
            <p className="text-lg text-slate-600 leading-relaxed">
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
            <span className="inline-block px-4 py-2 bg-primary/5 text-primary rounded-full font-mono text-sm uppercase tracking-wider mb-4">
              Documentos Institucionais
            </span>
            <h2 className="font-outfit font-bold text-3xl text-primary">
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
                  <div className="w-14 h-14 bg-primary rounded-xl flex items-center justify-center mb-5">
                    <IconComponent className="w-7 h-7 text-accent" />
                  </div>
                  <h3 className="font-outfit font-semibold text-xl text-primary mb-3 group-hover:text-accent transition-colors">
                    {doc.title}
                  </h3>
                  <p className="text-slate-600 mb-6">{doc.description}</p>
                  <a
                    href={doc.file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-primary font-semibold hover:text-accent transition-colors"
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
      <section className="py-16 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <span className="inline-block px-4 py-2 bg-accent/10 text-accent rounded-full font-mono text-sm uppercase tracking-wider mb-4">
              Relatórios de Gestão
            </span>
            <h2 className="font-outfit font-bold text-3xl text-primary">
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
                      <div className="w-12 h-12 bg-accent rounded-lg flex items-center justify-center">
                        <IconComponent className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <span className="font-mono text-xs text-accent uppercase tracking-wider">{report.year}</span>
                        <h3 className="font-outfit font-semibold text-lg text-white">{report.title}</h3>
                      </div>
                    </div>
                  </div>
                  <div className="p-6">
                    <p className="text-slate-600 mb-6">{report.description}</p>
                    <a
                      href={report.file_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 bg-primary text-white px-5 py-2.5 rounded-lg font-semibold hover:bg-primary/90 transition-all"
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
            <h2 className="font-outfit font-bold text-3xl text-primary mb-4">
              Indicadores de Governança
            </h2>
            <p className="text-slate-600 max-w-2xl mx-auto">
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
                <stat.icon className="w-8 h-8 text-accent mx-auto mb-3" />
                <div className="font-outfit font-bold text-3xl text-primary mb-1">{stat.value}</div>
                <div className="font-mono text-xs text-slate-500 uppercase tracking-wider">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-primary">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-outfit font-bold text-3xl text-white mb-6">
            Tem dúvidas sobre os nossos documentos?
          </h2>
          <p className="text-lg text-white/80 mb-8">
            Entre em contacto connosco para mais informações sobre a governança da ACCTA
          </p>
          <Link
            to="/contactos"
            className="inline-flex items-center gap-2 bg-accent text-primary px-8 py-4 rounded-lg font-bold hover:bg-accent/90 transition-all"
          >
            Fale Conosco
            <ExternalLink className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
};
