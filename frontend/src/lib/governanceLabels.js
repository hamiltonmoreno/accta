// Rótulos PT (apresentação) para governança estatutária. A fonte de verdade dos
// cargos/órgãos/categorias é SEMPRE o backend (GET /api/governance/structure) —
// aqui ficam apenas FALLBACKS leves e helpers para mapear key -> label quando a
// estrutura ainda não carregou. Nunca usar como fonte canónica.

import { ROLE_LABELS, PRIVILEGE_LABELS, roleLabel, privilegeLabel } from './cargoLabels';

export { ROLE_LABELS, PRIVILEGE_LABELS, roleLabel, privilegeLabel };

// Fallback estático de labels de cargo por key canónica (espelha governance.py).
export const CARGO_LABELS_FALLBACK = {
  ag_presidente: 'Presidente da Mesa da AG',
  ag_vice_presidente: 'Vice-Presidente da Mesa da AG',
  ag_secretario: 'Secretário da Mesa da AG',
  dir_presidente: 'Presidente da Direcção',
  dir_vice_presidente: 'Vice-Presidente da Direcção',
  dir_secretario: 'Secretário da Direcção',
  dir_tesoureiro: 'Tesoureiro',
  dir_vogal: 'Vogal da Direcção',
  cf_presidente: 'Presidente do Conselho Fiscal',
  cf_relator: 'Relator do Conselho Fiscal',
  cf_vogal: 'Vogal do Conselho Fiscal',
  socio: 'Sócio',
};

export const ORGAO_LABELS = {
  assembleia_geral: 'Assembleia Geral',
  direcao: 'Direcção',
  conselho_fiscal: 'Conselho Fiscal',
};

export const MEMBER_CATEGORY_LABELS = {
  fundador: 'Fundador',
  ordinario: 'Ordinário',
  honorario: 'Honorário',
};

export const ASSEMBLEIA_TIPO_LABELS = {
  ordinaria: 'Ordinária',
  extraordinaria: 'Extraordinária',
  eleitoral: 'Eleitoral',
};

export const ASSEMBLEIA_STATUS_LABELS = {
  rascunho: 'Rascunho',
  convocada: 'Convocada',
  em_curso: 'Em curso',
  encerrada: 'Encerrada',
  anulada: 'Anulada',
};

export const ELEICAO_STATUS_LABELS = {
  preparacao: 'Preparação',
  candidaturas: 'Candidaturas',
  campanha: 'Campanha',
  votacao: 'Votação',
  apurada: 'Apurada',
  recurso: 'Recurso',
  proclamada: 'Proclamada',
  anulada: 'Anulada',
};

export const MAIORIA_LABELS = {
  absoluta: 'Maioria absoluta dos presentes',
  qualificada_3_4_presentes: 'Qualificada (3/4 dos presentes)',
  qualificada_3_4_universo: 'Qualificada (3/4 do universo)',
};

export const SANCAO_TIPO_LABELS = {
  advertencia: 'Advertência escrita',
  multa: 'Multa',
  perda_direitos: 'Perda de direitos',
  expulsao: 'Expulsão',
};

export const SANCAO_STATUS_LABELS = {
  proposta: 'Proposta',
  inquerito: 'Inquérito',
  decidida: 'Decidida',
  recurso: 'Recurso',
  aplicada: 'Aplicada',
  arquivada: 'Arquivada',
  anulada: 'Anulada',
};

// Resolve o label de um cargo: estrutura do backend primeiro, fallback estático
// depois, e por fim a própria key (nunca rebenta).
export const cargoLabelFrom = (structure, key) => {
  if (!key) return '—';
  const fromStructure = structure?.cargos?.find((c) => c.key === key)?.label;
  return fromStructure || CARGO_LABELS_FALLBACK[key] || key;
};

export const orgaoLabel = (id) => ORGAO_LABELS[id] || id || '—';
export const memberCategoryLabel = (k) => MEMBER_CATEGORY_LABELS[k] || k || '—';
