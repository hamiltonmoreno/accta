import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { BookOpen, Download, FileText, Calendar, User } from 'lucide-react';
import { publicacoesAPI, documentsAPI, mediaUrl } from '../../utils/api';
import { Skeleton } from '../../components/ui/skeleton';

// Cat 5 F4 — catálogo público de publicações formais (revista/boletim/artigo/
// relatório técnico) com visibility="publico". Download via /documents/public,
// que exige que o próprio documento também seja público.

const TIPO_LABELS = {
  revista: 'Revista',
  boletim: 'Boletim',
  artigo: 'Artigo',
  relatorio_tecnico: 'Relatório Técnico',
};
const FILTROS = [
  { key: '', label: 'Todas' },
  { key: 'revista', label: 'Revistas' },
  { key: 'boletim', label: 'Boletins' },
  { key: 'artigo', label: 'Artigos' },
  { key: 'relatorio_tecnico', label: 'Relatórios' },
];

const fmtData = (iso) => {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d.toLocaleDateString('pt-PT');
};

export const PublicacoesPublicoPage = () => {
  const [tipo, setTipo] = useState('');

  const { data: publicacoes = [], isLoading } = useQuery({
    queryKey: ['public', 'publicacoes', tipo || 'all'],
    queryFn: async () => (await publicacoesAPI.getPublic({ tipo: tipo || undefined, limit: 100 })).data.items,
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Cabeçalho */}
      <section className="bg-grafite py-16 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl animate-fade-up">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-carmesim/20 border border-carmesim/40 text-white rounded-full text-xs uppercase tracking-wider font-semibold mb-4">
              <BookOpen className="w-3.5 h-3.5" aria-hidden="true" />
              Publicações
            </span>
            <h1 className="font-bold text-3xl sm:text-4xl lg:text-5xl text-white">
              Publicações da ACCTA
            </h1>
            <p className="mt-3 text-base sm:text-lg text-white/80 leading-relaxed">
              Revistas, boletins, artigos e relatórios técnicos de acesso público
            </p>
          </div>
        </div>
      </section>

      <section className="py-12 sm:py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Filtros por tipo */}
          <div className="flex flex-wrap gap-2 mb-10">
            {FILTROS.map((f) => (
              <button
                key={f.key || 'todas'}
                type="button"
                onClick={() => setTipo(f.key)}
                className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                  tipo === f.key
                    ? 'bg-carmesim text-white border-carmesim'
                    : 'bg-white text-grafite border-[#D1D5DB] hover:bg-gray-50'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-64 rounded-2xl" />
              ))}
            </div>
          ) : publicacoes.length === 0 ? (
            <div className="text-center py-20">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" aria-hidden="true" />
              <p className="text-gray-500">Ainda não há publicações públicas disponíveis.</p>
            </div>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {publicacoes.map((p) => {
                const data = fmtData(p.data_publicacao);
                return (
                  <article
                    key={p.id}
                    className="bg-white border border-gray-200/80 rounded-2xl overflow-hidden flex flex-col animate-fade-up hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-shadow"
                  >
                    {p.capa_url ? (
                      <img
                        src={mediaUrl(p.capa_url)}
                        alt={p.titulo}
                        loading="lazy"
                        className="w-full h-44 object-cover bg-gray-100"
                      />
                    ) : (
                      <div className="w-full h-44 bg-gray-100 flex items-center justify-center">
                        <BookOpen className="w-12 h-12 text-gray-300" aria-hidden="true" />
                      </div>
                    )}
                    <div className="p-5 flex flex-col flex-1">
                      <span className="inline-flex items-center self-start px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-gray-100 text-grafite border border-gray-200 mb-2">
                        {TIPO_LABELS[p.tipo] || p.tipo}
                      </span>
                      <h2 className="font-sans font-semibold text-lg text-grafite mb-1">{p.titulo}</h2>
                      <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 mb-3">
                        {p.autor && (
                          <span className="inline-flex items-center gap-1">
                            <User className="w-3.5 h-3.5" aria-hidden="true" />
                            {p.autor}
                          </span>
                        )}
                        {data && (
                          <span className="inline-flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5" aria-hidden="true" />
                            {data}
                          </span>
                        )}
                      </div>
                      {p.descricao && <p className="text-sm text-gray-600 line-clamp-3 flex-1">{p.descricao}</p>}
                      {p.a_venda ? (
                        // F5: conteúdo à venda — mostra o preço e remete para aquisição
                        // (sócios descarregam grátis no portal; o documento fica privado).
                        <div className="mt-4">
                          <div className="flex items-baseline gap-1 mb-2">
                            <span className="text-lg font-bold text-grafite">
                              {Number(p.preco).toLocaleString('pt-PT')}
                            </span>
                            <span className="text-xs text-gray-500">CVE</span>
                          </div>
                          <Link
                            to="/contactos"
                            className="inline-flex items-center justify-center gap-2 w-full bg-floresta text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-floresta-dark transition-colors"
                          >
                            Adquirir — contactar ACCTA
                          </Link>
                        </div>
                      ) : (
                        p.document_id && (
                          <a
                            href={documentsAPI.publicDownloadUrl(p.document_id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-4 inline-flex items-center justify-center gap-2 w-full border border-[#D1D5DB] text-grafite rounded-lg py-2.5 text-sm font-semibold hover:bg-gray-50 transition-colors"
                          >
                            <Download className="w-4 h-4" />
                            Descarregar
                          </a>
                        )
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default PublicacoesPublicoPage;
