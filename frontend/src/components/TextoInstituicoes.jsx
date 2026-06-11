import React from 'react';
import { instituicoes } from '../content/cta/instituicoes';

// Linka a 1ª ocorrência de cada instituição num texto corrido (sub-projeto C).
// Estratégia: alias mais longo primeiro (evita que "AAC" ganhe a "Agência de
// Aviação Civil"), correspondência exata com word-boundary, case-sensitive
// (os nomes são siglas/próprios — evita apanhar "asa" em "casa"). Cada
// instituição é linkada UMA vez por bloco; ocorrências seguintes ficam texto.
// Estilo: link Carmesim sobre branco (frontend-design). NÃO usar sobre fundos
// escuros — viola a regra de contraste (Carmesim só sobre claro).

const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

// Aliases ordenados por comprimento desc para a alternância do regex.
const ALIASES = instituicoes
  .flatMap((inst) => inst.aliases.map((alias) => ({ alias, inst })))
  .sort((a, b) => b.alias.length - a.alias.length);

const PATTERN = new RegExp(
  `\\b(${ALIASES.map((a) => escapeRe(a.alias)).join('|')})\\b`,
  'g'
);

const LINK_CLS =
  'text-carmesim hover:text-carmesim-dark underline underline-offset-2 decoration-1 transition-colors';

export const TextoInstituicoes = ({ texto, className }) => {
  if (!texto) return null;

  const linked = new Set();
  const parts = [];
  let lastIndex = 0;
  let match;
  PATTERN.lastIndex = 0;

  while ((match = PATTERN.exec(texto)) !== null) {
    const matched = match[0];
    const entry = ALIASES.find((a) => a.alias === matched);
    if (!entry || linked.has(entry.inst.url)) continue; // já linkado → fica texto
    linked.add(entry.inst.url);
    if (match.index > lastIndex) parts.push(texto.slice(lastIndex, match.index));
    parts.push(
      <a
        key={`${entry.inst.url}-${match.index}`}
        href={entry.inst.url}
        target="_blank"
        rel="noopener noreferrer"
        className={LINK_CLS}
      >
        {matched}
      </a>
    );
    lastIndex = match.index + matched.length;
  }
  if (lastIndex < texto.length) parts.push(texto.slice(lastIndex));

  return <span className={className}>{parts}</span>;
};

export default TextoInstituicoes;
