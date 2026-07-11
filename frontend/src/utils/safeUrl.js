// Sanitização de URLs vindos de dados editáveis antes de irem para um `href`
// (spec 019, M-HREF). Bloqueia esquemas perigosos (javascript:, data:, file:, vbscript:)
// que permitiriam XSS ao clicar. Fonte única — reutilizada por todas as páginas
// que renderizam websites/links de parceiros/relações vindos da BD.
//
// Regras:
//   - vazio/não-string           → null (o caller não renderiza o link)
//   - http(s)://…                 → mantém
//   - qualquer outro scheme (x:)  → null (bloqueia javascript:, data:, …)
//   - sem scheme (ex.: "acme.cv") → assume https:// (conveniência de introdução)
export function safeUrl(url) {
  if (!url || typeof url !== 'string') return null;
  const t = url.trim();
  if (/^https?:\/\//i.test(t)) return t;
  if (/^[a-z][a-z0-9+\-.]*:/i.test(t)) return null; // javascript:, data:, file:, …
  return `https://${t}`;
}

export default safeUrl;
