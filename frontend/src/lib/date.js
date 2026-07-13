/**
 * Formatação de datas pt-PT — fonte única (antes duplicada em ~8 ficheiros).
 * `toLocaleString` com opções só de data == `toLocaleDateString` (o Intl só
 * renderiza os campos pedidos). Data ausente/inválida → `fallback` (por
 * omissão '—'; passar `null` onde o chamador esconde o campo).
 * Nota: para strings SÓ-data (ex.: aniversários) sujeitas a desvio de fuso,
 * usar o `toLocalDate` de perfil/tokens.js — não estes helpers.
 */
const PT = 'pt-PT';
const DATE_OPTS = { day: '2-digit', month: '2-digit', year: 'numeric' };
const DATETIME_OPTS = { ...DATE_OPTS, hour: '2-digit', minute: '2-digit' };

const format = (iso, opts, fallback) => {
  if (!iso) return fallback;
  try {
    return new Date(iso).toLocaleString(PT, opts);
  } catch {
    return fallback;
  }
};

export const formatDate = (iso, fallback = '—') => format(iso, DATE_OPTS, fallback);
export const formatDateTime = (iso, fallback = '—') => format(iso, DATETIME_OPTS, fallback);
