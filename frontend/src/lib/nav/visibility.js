// Visibilidade de itens de navegação — RBAC aditivo (role OR privilégio) +
// gating por órgão social (`match`). Fonte ÚNICA partilhada entre a sidebar
// (PrivateLayout) e o manual (Central de Ajuda), para que as duas nunca
// divirjam. Espelha a regra de `filterItem` que vivia no PrivateLayout.
//
// Descritor de item (mesmo shape da sidebar e dos `gate` dos artigos de ajuda):
//   { roles: ['all'|'admin'|'financeiro'|'moderador'|'socio'],
//     privileges?: string[],            // privilégios que concedem acesso EXTRA
//     match?: 'direcao' | 'governanca', // gating por cargo/órgão
//     subheader?: string }              // divisor visual — passa sempre

/**
 * Constrói o contexto de visibilidade a partir do objeto devolvido por `useAuth`.
 * Aceita as flags já derivadas (isAdmin, isDirecao, …) + `user`.
 */
export const buildNavContext = (auth = {}) => ({
  isAdmin: !!auth.isAdmin,
  isFinanceiro: !!auth.isFinanceiro,
  isModerador: !!auth.isModerador,
  isDirecao: !!auth.isDirecao,
  isMesaAG: !!auth.isMesaAG,
  role: auth.user?.role,
  privileges: auth.user?.privileges || [],
});

/**
 * Decide se um item/descritor é visível para o contexto dado.
 * Regra idêntica à antiga `filterItem` da sidebar (RBAC aditivo).
 */
export const isNavItemVisible = (item, ctx) => {
  if (!item) return false;
  // Sub-rótulos são divisores visuais sem RBAC próprio.
  if (item.subheader) return true;
  // Gating por cargo/órgão (extensão ao RBAC por role/privilégio).
  if (item.match === 'direcao' && (ctx.isAdmin || ctx.isDirecao)) return true;
  if (item.match === 'governanca' && (ctx.isAdmin || ctx.isDirecao || ctx.isMesaAG)) return true;
  const roles = item.roles || [];
  if (roles.includes('all')) return true;
  if (roles.includes('admin') && ctx.isAdmin) return true;
  // spec 018: 'financeiro'/'moderador' já não são níveis — os descritores que
  // ainda os usem (ex.: gates de artigos de Ajuda) resolvem pelas flags de
  // compat do AuthContext, que derivam de PRIVILÉGIOS (manage_finances /
  // moderate_content), não do role.
  if (roles.includes('financeiro') && (ctx.isFinanceiro || ctx.isAdmin)) return true;
  if (roles.includes('moderador') && (ctx.isModerador || ctx.isAdmin)) return true;
  if (roles.includes('socio') && ctx.role === 'socio') return true;
  // Privilégios concedem acesso EXTRA à entrada (ex.: Conselho Fiscal vê Financeiro).
  if (item.privileges?.some((p) => (ctx.privileges || []).includes(p))) return true;
  return false;
};
