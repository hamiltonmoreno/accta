// Base de conhecimento CTA — ponto único de consumo pelas páginas públicas.
// Fonte autoritativa: memory/deep-research-report.md.
// Uma alteração no relatório → uma alteração neste módulo → propaga a todas
// as páginas. Auditável contra o relatório num só lugar (spec §3).

// Identidade institucional canónica (decisão do dono — extenso "Cabo-verdiana").
export const ASSOCIACAO_NOME =
  'Associação Cabo-verdiana dos Controladores de Tráfego Aéreo';
export const ASSOCIACAO_SIGLA = 'ACCTA';
export const ASSOCIACAO_NOME_COMPLETO = `${ASSOCIACAO_NOME} (${ASSOCIACAO_SIGLA})`;

export * from './profissao';
export * from './estruturaAts';
export * from './licenciamento';
export * from './formacao';
export * from './legislacao';
export * from './faq';
export * from './contactosUteis';
export * from './instituicoes';
