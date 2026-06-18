import React, { useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { HelpCircle, Search, ArrowRight, LifeBuoy } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { ajudaSections } from '../../content/ajuda';
import { buildNavContext, isNavItemVisible } from '../../lib/nav/visibility';
import { Input } from '../../components/ui/input';
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from '../../components/ui/accordion';

const ALL_GATE = { roles: ['all'] };

// Texto pesquisável de um artigo (título + resumo + passos + dicas + FAQ +
// quando usar/não + campos). Mantém-se em sincronia com o que a página desenha.
const articleHaystack = (a) =>
  [
    a.titulo,
    a.resumo,
    ...(a.passos || []),
    ...(a.dicas || []),
    ...(a.quandoUsar || []),
    ...(a.quandoNaoUsar || []),
    ...(a.campos || []).flatMap((c) => [c.campo, c.ajuda, c.exemplo]),
    ...(a.faq || []).flatMap((f) => [f.q, f.a]),
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();

/**
 * Central de Ajuda (spec-central-ajuda) — manual de utilização do Portal ACCTA.
 * Apenas CONSOME `content/ajuda`; filtra secções/artigos pela visibilidade real
 * (role + privilégios, mesma regra da sidebar via lib/nav/visibility) e oferece
 * pesquisa client-side. Sem conteúdo hardcoded.
 */
export const AjudaPage = () => {
  const auth = useAuth();
  const location = useLocation();
  const [query, setQuery] = useState('');
  const q = query.trim().toLowerCase();

  const ctx = useMemo(
    () => buildNavContext(auth),
    // Recalcula quando muda o utilizador/role/privilégios.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [auth.user, auth.isAdmin, auth.isFinanceiro, auth.isModerador, auth.isDirecao, auth.isMesaAG],
  );

  // Secções visíveis ao utilizador, já filtradas pela pesquisa.
  const sections = useMemo(() => {
    return ajudaSections
      .map((s) => {
        const visiveis = s.artigos.filter((a) => isNavItemVisible(a.gate || ALL_GATE, ctx));
        const tituloMatch = !!q && s.titulo.toLowerCase().includes(q);
        const artigos = !q || tituloMatch ? visiveis : visiveis.filter((a) => articleHaystack(a).includes(q));
        return { ...s, artigos };
      })
      .filter((s) => s.artigos.length > 0);
  }, [ctx, q]);

  // Itens de accordion (valores únicos `secao:artigo`) abertos. Em pesquisa,
  // abre tudo o que casou; sem pesquisa, começa fechado e o utilizador controla.
  const [open, setOpen] = useState([]);
  useEffect(() => {
    if (q) {
      setOpen(sections.flatMap((s) => s.artigos.map((a) => `${s.id}:${a.id}`)));
    } else {
      setOpen([]);
    }
  }, [q, sections]);

  // Deep-link por secção (/ajuda#financas) — faz scroll suave ao montar.
  useEffect(() => {
    const id = location.hash?.replace('#', '');
    if (!id) return;
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [location.hash, sections.length]);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Herói sóbrio */}
      <div className="flex items-start gap-3 animate-fade-up">
        <div className="w-11 h-11 rounded-xl bg-carmesim/10 flex items-center justify-center shrink-0">
          <LifeBuoy className="w-6 h-6 text-carmesim" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-grafite">Central de Ajuda</h1>
          <p className="text-sm text-[#6B7280]">
            Manual de utilização do Portal ACCTA. As secções adaptam-se ao seu perfil de acesso.
          </p>
        </div>
      </div>

      {/* Pesquisa */}
      <div className="relative max-w-xl animate-fade-up">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" aria-hidden="true" />
        <Input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Procurar no manual…"
          className="pl-9"
          aria-label="Procurar no manual"
          data-testid="ajuda-search"
        />
      </div>

      <div className="grid lg:grid-cols-[220px_1fr] gap-6">
        {/* Índice (TOC) */}
        <nav className="lg:sticky lg:top-[calc(var(--header-h)+1rem)] lg:self-start" aria-label="Índice da ajuda">
          <ul className="flex flex-wrap lg:flex-col gap-2" data-testid="ajuda-toc">
            {sections.map((s) => {
              const Icon = s.icon;
              return (
                <li key={s.id}>
                  <a
                    href={`#${s.id}`}
                    className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm text-grafite border border-[#E5E7EB] lg:border-0 hover:bg-[#F5F5F5] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                    data-testid={`ajuda-toc-${s.id}`}
                  >
                    {Icon && <Icon className="w-4 h-4 text-[#6B7280]" aria-hidden="true" />}
                    {s.titulo}
                  </a>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Conteúdo */}
        <div className="min-w-0 space-y-8">
          {sections.length === 0 ? (
            <div className="text-center py-16 text-[#6B7280]" data-testid="ajuda-vazio">
              <Search className="w-10 h-10 mx-auto mb-3 text-[#D1D5DB]" aria-hidden="true" />
              Nenhum resultado para “{query}”.
            </div>
          ) : (
            sections.map((s) => {
              const Icon = s.icon;
              return (
                <section key={s.id} id={s.id} className="scroll-mt-[calc(var(--header-h)+1rem)] animate-fade-up" data-testid={`ajuda-secao-${s.id}`}>
                  <div className="flex items-center gap-2 mb-1">
                    {Icon && <Icon className="w-5 h-5 text-carmesim" aria-hidden="true" />}
                    <h2 className="text-lg font-bold text-grafite">{s.titulo}</h2>
                  </div>
                  {s.resumo && <p className="text-sm text-[#6B7280] mb-3">{s.resumo}</p>}

                  <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm px-4">
                    <Accordion type="multiple" value={open} onValueChange={setOpen}>
                      {s.artigos.map((a) => (
                        <AccordionItem key={a.id} value={`${s.id}:${a.id}`} data-testid={`ajuda-artigo-${a.id}`}>
                          <AccordionTrigger className="text-grafite font-semibold">{a.titulo}</AccordionTrigger>
                          <AccordionContent>
                            {a.resumo && <p className="text-sm text-[#4B5563] mb-3">{a.resumo}</p>}
                            {(a.quandoUsar?.length > 0 || a.quandoNaoUsar?.length > 0) && (
                              <div className="grid sm:grid-cols-2 gap-2.5 mb-3">
                                {a.quandoUsar?.length > 0 && (
                                  <div className="rounded-md bg-[#F0FDF4] border border-[#DCFCE7] p-3">
                                    <p className="text-xs font-semibold uppercase tracking-wider text-[#15803D] mb-1.5">Quando usar</p>
                                    <ul className="list-disc list-inside space-y-1 text-sm text-[#3F6212] marker:text-[#86EFAC]">
                                      {a.quandoUsar.map((d, i) => (
                                        <li key={i}>{d}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                                {a.quandoNaoUsar?.length > 0 && (
                                  <div className="rounded-md bg-[#FBEAEC] border border-[#F5D0D4] p-3">
                                    <p className="text-xs font-semibold uppercase tracking-wider text-[#A51B27] mb-1.5">Quando NÃO usar</p>
                                    <ul className="list-disc list-inside space-y-1 text-sm text-[#7F1D1D] marker:text-[#F5A3AB]">
                                      {a.quandoNaoUsar.map((d, i) => (
                                        <li key={i}>{d}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}
                            {a.passos?.length > 0 && (
                              <ol className="list-decimal list-inside space-y-1.5 text-sm text-grafite mb-3 marker:text-[#9CA3AF]">
                                {a.passos.map((p, i) => (
                                  <li key={i}>{p}</li>
                                ))}
                              </ol>
                            )}
                            {a.campos?.length > 0 && (
                              <div className="rounded-md border border-[#E5E7EB] overflow-hidden mb-3">
                                <p className="text-xs font-semibold uppercase tracking-wider text-[#6B7280] bg-[#F5F5F5] px-3 py-2">Como preencher cada campo</p>
                                <dl className="divide-y divide-[#F0F0F0]">
                                  {a.campos.map((c, i) => (
                                    <div key={i} className="px-3 py-2.5">
                                      <dt className="text-sm font-semibold text-grafite">{c.campo}</dt>
                                      {c.ajuda && <dd className="text-sm text-[#4B5563] mt-0.5">{c.ajuda}</dd>}
                                      {c.exemplo && (
                                        <dd className="text-sm text-[#4B5563] mt-1">
                                          <span className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF] mr-1.5">Exemplo</span>
                                          <span className="italic">{c.exemplo}</span>
                                        </dd>
                                      )}
                                    </div>
                                  ))}
                                </dl>
                              </div>
                            )}
                            {a.dicas?.length > 0 && (
                              <div className="rounded-md bg-[#F5F5F5] border border-[#E5E7EB] p-3 mb-3">
                                <p className="text-xs font-semibold uppercase tracking-wider text-[#6B7280] mb-1.5">Dicas</p>
                                <ul className="list-disc list-inside space-y-1 text-sm text-[#4B5563] marker:text-[#9CA3AF]">
                                  {a.dicas.map((d, i) => (
                                    <li key={i}>{d}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {a.faq?.length > 0 && (
                              <div className="space-y-2 mb-3">
                                {a.faq.map((f, i) => (
                                  <div key={i}>
                                    <p className="text-sm font-semibold text-grafite">{f.q}</p>
                                    <p className="text-sm text-[#4B5563]">{f.a}</p>
                                  </div>
                                ))}
                              </div>
                            )}
                            {a.rota && (
                              <Link
                                to={a.rota}
                                className="inline-flex items-center gap-1.5 text-sm font-semibold text-carmesim hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 rounded"
                                data-testid={`ajuda-ir-${a.id}`}
                              >
                                Abrir módulo
                                <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                              </Link>
                            )}
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  </div>
                </section>
              );
            })
          )}

          {/* Rodapé — encaminha para os canais de apoio */}
          <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 flex flex-col sm:flex-row sm:items-center gap-3 justify-between">
            <div className="flex items-center gap-2 text-sm text-[#4B5563]">
              <HelpCircle className="w-5 h-5 text-[#6B7280]" aria-hidden="true" />
              Não encontrou o que procura?
            </div>
            <Link
              to="/participacao/esclarecimentos"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-carmesim hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 rounded"
              data-testid="ajuda-esclarecimentos"
            >
              Pedir esclarecimento à Direção
              <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AjudaPage;
