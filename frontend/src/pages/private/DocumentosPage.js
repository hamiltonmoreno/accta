import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { documentsAPI } from '../../utils/api';
import { FileText, Download, Search } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const DocumentosPage = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await documentsAPI.getAll();
      setDocuments(response.data);
    } catch (error) {
      console.error('Erro ao carregar documentos:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredDocuments = documents
    .filter((doc) => filter === 'all' || doc.type === filter)
    .filter((doc) => doc.title.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-outfit font-bold text-4xl text-primary mb-2" data-testid="documents-title">
          Secretaria & Documentos
        </h1>
        <p className="text-slate-600">Acesse atas, estatutos, balancetes e outros documentos oficiais</p>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar documentos..."
            className="w-full pl-12 pr-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
            data-testid="search-input"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all ${
              filter === 'all' ? 'bg-primary text-white' : 'bg-white text-slate-600 hover:bg-slate-50'
            }`}
            data-testid="filter-all"
          >
            Todos
          </button>
          <button
            onClick={() => setFilter('ata')}
            className={`px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all ${
              filter === 'ata' ? 'bg-primary text-white' : 'bg-white text-slate-600 hover:bg-slate-50'
            }`}
            data-testid="filter-ata"
          >
            Atas
          </button>
          <button
            onClick={() => setFilter('estatuto')}
            className={`px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all ${
              filter === 'estatuto' ? 'bg-primary text-white' : 'bg-white text-slate-600 hover:bg-slate-50'
            }`}
            data-testid="filter-estatuto"
          >
            Estatutos
          </button>
          <button
            onClick={() => setFilter('balancete')}
            className={`px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all ${
              filter === 'balancete' ? 'bg-primary text-white' : 'bg-white text-slate-600 hover:bg-slate-50'
            }`}
            data-testid="filter-balancete"
          >
            Balancetes
          </button>
        </div>
      </div>

      {/* Documents List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="card-technical rounded-xl p-12 text-center" data-testid="no-documents">
          <p className="text-slate-500">Nenhum documento encontrado</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDocuments.map((doc, index) => (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="card-technical rounded-xl p-6 hover:shadow-lg transition-shadow"
              data-testid={`document-${doc.id}`}
            >
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
                  <FileText className="w-6 h-6 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="inline-block px-3 py-1 bg-accent/10 text-accent rounded-full text-xs font-mono uppercase tracking-wider mb-2">
                    {doc.type}
                  </span>
                  <h3 className="font-outfit font-semibold text-lg text-primary line-clamp-2">{doc.title}</h3>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs font-mono text-slate-500 mb-4">
                <span>{format(new Date(doc.created_at), 'dd MMM yyyy', { locale: ptBR })}</span>
                <span className="uppercase">{doc.visibility}</span>
              </div>

              {doc.tags && doc.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {doc.tags.slice(0, 3).map((tag, i) => (
                    <span key={i} className="text-xs text-slate-500 bg-slate-50 px-2 py-1 rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              <a
                href={doc.file_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 bg-primary text-white hover:bg-primary/90 h-10 px-4 rounded-lg uppercase tracking-wider font-bold text-sm transition-all"
                data-testid={`download-${doc.id}`}
              >
                <Download className="w-4 h-4" />
                Download
              </a>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};
