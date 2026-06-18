// Central de Ajuda (spec-central-ajuda §6) — manual do utilizador do Portal
// ACCTA como conteúdo estático versionado. A AjudaPage apenas CONSOME este
// módulo; zero conteúdo hardcoded na página. Uma mudança de produto → uma
// mudança aqui → propaga.
//
// Cada secção: { id, titulo, icon, resumo, artigos[] }.
// Cada artigo: { id, titulo, resumo, passos[], dicas?[], faq?[{q,a}], rota?,
//   gate?, quandoUsar?[], quandoNaoUsar?[], campos?[{campo, ajuda, exemplo}] }.
//   - `gate` segue o shape dos itens da sidebar (lib/nav/visibility); sem `gate`
//     => visível a todos os autenticados.
//   - `quandoUsar`/`quandoNaoUsar`: orientação de decisão (quando esta ferramenta
//     é a certa e quando deve usar outra).
//   - `campos`: guia campo-a-campo do formulário real (o "como preencher"); cada
//     entrada descreve um campo (`campo`), o que lá pôr (`ajuda`) e um `exemplo`.
//   Campos novos são opcionais — artigos sem eles renderizam como antes.
//   `passos` é obrigatório (≥1) — ver __tests__/integrity.test.js.
import { primeirosPassos } from './primeirosPassos';
import { meuPortal } from './meuPortal';
import { governanca } from './governanca';
import { comunidade } from './comunidade';
import { financas } from './financas';
import { administracao } from './administracao';

// Ordem de apresentação no índice e na página.
export const ajudaSections = [
  primeirosPassos,
  meuPortal,
  governanca,
  comunidade,
  financas,
  administracao,
];

export default ajudaSections;
