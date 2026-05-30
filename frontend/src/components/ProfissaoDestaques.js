import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Megaphone, Globe, FileText, GraduationCap, ExternalLink, Download } from 'lucide-react';
import { defesaAPI, relacoesAPI, formacoesAPI, documentsAPI } from '../utils/api';

// Cat 5 F4 — secções dinâmicas da ProfissaoPage pública. Cada bloco só renderiza
// quando há conteúdo já marcado como público (defesa publicada, relações/formações
// `publico`); caso contrário não aparece (evita secções vazias numa landing).

const DEFESA_TIPO_LABELS = {
  representacao: 'Representação',
  tomada_posicao: 'Tomada de Posição',
  comunicado: 'Comunicado',
};
const RELACAO_TIPO_LABELS = {
  federacao_internacional: 'Federação Internacional',
  associacao_congenere: 'Associação Congénere',
  parceiro: 'Parceiro',
};
const ESTADO_LABELS = {
  filiado: 'Filiado',
  em_negociacao: 'Em negociação',
  nao_filiado: 'Não filiado',
  suspenso: 'Suspenso',
};
const FORMACAO_TIPO_LABELS = {
  formacao: 'Formação',
  certificacao: 'Certificação',
  material: 'Material',
};

const fmtData = (iso) => {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d.toLocaleDateString('pt-PT');
};

const safeUrl = (url) => {
  if (!url || typeof url !== 'string') return null;
  const t = url.trim();
  if (/^https?:\/\//i.test(t)) return t;
  if (/^[a-z][a-z0-9+\-.]*:/i.test(t)) return null; // bloqueia javascript:, data:, …
  return `https://${t}`;
};

const STALE = 5 * 60 * 1000; // conteúdo quase estático

export const ProfissaoDestaques = () => {
  const { data: defesa = [] } = useQuery({
    queryKey: ['public', 'defesa-profissional'],
    queryFn: async () => (await defesaAPI.getPublic({ limit: 6 })).data.items,
    staleTime: STALE,
  });
  const { data: relacoes = [] } = useQuery({
    queryKey: ['public', 'relacoes-externas'],
    queryFn: async () => (await relacoesAPI.getPublic({ limit: 12 })).data.items,
    staleTime: STALE,
  });
  const { data: formacoes = [] } = useQuery({
    queryKey: ['public', 'formacoes'],
    queryFn: async () => (await formacoesAPI.getPublic({ limit: 6 })).data.items,
    staleTime: STALE,
  });

  return (
    <>
      {/* Tomadas de posição / Defesa profissional publicada */}
      {defesa.length > 0 && (
        <section className="py-12 sm:py-20 lg:py-24 bg-gray-50">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-12">
              <span className="inline-block px-4 py-2 bg-carmesim/10 text-carmesim rounded-full text-sm uppercase tracking-wider mb-6">
                Defesa Profissional
              </span>
              <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
                Posições públicas da ACCTA
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Representações e tomadas de posição em defesa dos interesses dos controladores
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {defesa.map((d) => {
                const data = fmtData(d.data);
                return (
                  <article key={d.id} className="card-technical rounded-2xl p-6 animate-fade-up flex flex-col">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-gray-500">
                        <Megaphone className="w-3 h-3" aria-hidden="true" />
                        {DEFESA_TIPO_LABELS[d.tipo] || d.tipo}
                      </span>
                      {data && <span className="text-xs text-gray-400">· {data}</span>}
                    </div>
                    <h3 className="font-sans font-semibold text-lg text-grafite mb-2">{d.titulo}</h3>
                    {d.descricao && <p className="text-sm text-gray-600 line-clamp-4 flex-1">{d.descricao}</p>}
                    {d.document_id && (
                      <a
                        href={documentsAPI.publicDownloadUrl(d.document_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-carmesim hover:underline"
                      >
                        <FileText className="w-4 h-4" />
                        Ler documento
                      </a>
                    )}
                  </article>
                );
              })}
            </div>
          </div>
        </section>
      )}

      {/* Relações / IFATCA */}
      {relacoes.length > 0 && (
        <section className="py-12 sm:py-20 lg:py-24 bg-white">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-12">
              <span className="inline-block px-4 py-2 bg-grafite/5 text-grafite rounded-full text-sm uppercase tracking-wider mb-6">
                Cooperação Internacional
              </span>
              <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
                Relações e filiações
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                A ACCTA coopera com a IFATCA e congéneres na defesa da profissão
              </p>
            </div>

            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {relacoes.map((r) => {
                const website = safeUrl(r.website);
                return (
                  <div key={r.id} className="card-technical rounded-2xl p-6 animate-fade-up">
                    <div className="flex items-start gap-4">
                      {r.logo_url ? (
                        <img
                          src={r.logo_url}
                          alt={r.nome}
                          loading="lazy"
                          className="w-12 h-12 object-contain flex-shrink-0"
                        />
                      ) : (
                        <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                          <Globe className="w-6 h-6 text-grafite" />
                        </div>
                      )}
                      <div className="min-w-0">
                        <h3 className="font-sans font-semibold text-grafite truncate">{r.nome}</h3>
                        <p className="text-xs text-gray-500">{RELACAO_TIPO_LABELS[r.tipo] || r.tipo}</p>
                      </div>
                    </div>
                    {r.descricao && <p className="text-sm text-gray-600 mt-3 line-clamp-3">{r.descricao}</p>}
                    <div className="flex items-center justify-between mt-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-gray-100 text-grafite border border-gray-200">
                        {ESTADO_LABELS[r.estado_filiacao] || r.estado_filiacao}
                      </span>
                      {website && (
                        <a
                          href={website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-sm font-semibold text-carmesim hover:underline"
                          aria-label={`Visitar website de ${r.nome}`}
                        >
                          Website
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      )}

      {/* Formações / Certificações públicas */}
      {formacoes.length > 0 && (
        <section className="py-12 sm:py-20 lg:py-24 bg-gray-50">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-12">
              <span className="inline-block px-4 py-2 bg-carmesim/10 text-carmesim rounded-full text-sm uppercase tracking-wider mb-6">
                Desenvolvimento Profissional
              </span>
              <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
                Formação e certificação
              </h2>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {formacoes.map((f) => {
                const url = safeUrl(f.url);
                return (
                  <div key={f.id} className="card-technical rounded-2xl p-6 animate-fade-up flex flex-col">
                    <div className="flex items-center gap-2 mb-3 text-[10px] font-bold uppercase tracking-wider text-gray-500">
                      <GraduationCap className="w-3.5 h-3.5" aria-hidden="true" />
                      {FORMACAO_TIPO_LABELS[f.tipo] || f.tipo}
                    </div>
                    <h3 className="font-sans font-semibold text-lg text-grafite mb-1">{f.titulo}</h3>
                    {f.entidade && <p className="text-xs text-gray-500 mb-2">{f.entidade}</p>}
                    {f.descricao && <p className="text-sm text-gray-600 line-clamp-3 flex-1">{f.descricao}</p>}
                    <div className="flex items-center gap-4 mt-4">
                      {url && (
                        <a
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-sm font-semibold text-carmesim hover:underline"
                        >
                          Saber mais
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                      {f.document_id && (
                        <a
                          href={documentsAPI.publicDownloadUrl(f.document_id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-sm font-semibold text-grafite hover:underline"
                        >
                          <Download className="w-3.5 h-3.5" />
                          Material
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      )}
    </>
  );
};
