/**
 * Sócio real vs. conta técnica de sistema (spec-identidade-cargos).
 * `account_type` ausente ⇒ tratado como 'member' (regra de identidade).
 * Só `technical` (ex.: admin@controlador.cv) não é membro — excluído de
 * pontuação/ranking.
 */
export const isMemberAccount = (user) => (user?.account_type || 'member') !== 'technical';
