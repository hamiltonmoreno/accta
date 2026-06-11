// Base de conhecimento — Registo de instituições oficiais (sub-projeto C).
// Fonte autoritativa: memory/deep-research-report.md + verificação factual
// (docs/superpowers/specs/2026-06-11-verificacao-factual-B-report.md). PT-PT.
//
// Cada entrada: nome canónico, URL oficial e `aliases` (formas como a
// instituição é nomeada no texto da base de conhecimento). Usado por:
//  - <TextoInstituicoes> — linka a 1ª ocorrência de cada alias no texto corrido;
//  - <FontesOficiais> — bloco de fontes oficiais com link.
// `aliases` ordenados manualmente do mais longo/específico para o mais curto;
// o componente também ordena por comprimento por segurança.

export const instituicoes = [
  {
    nome: 'AAC — Agência de Aviação Civil',
    url: 'https://www.aac.cv/',
    papel: 'Regulador aeronáutico',
    aliases: ['Agência de Aviação Civil', 'AAC'],
  },
  {
    nome: 'ASA — Aeroportos e Segurança Aérea, S.A.',
    url: 'https://www.asa.cv/',
    papel: 'Prestador dos serviços de tráfego aéreo (ATS)',
    aliases: ['Aeroportos e Segurança Aérea', 'ASA'],
  },
  {
    nome: 'ICAO — Organização da Aviação Civil Internacional',
    url: 'https://www.icao.int/',
    papel: 'Normas e práticas recomendadas internacionais',
    aliases: ['ICAO'],
  },
  {
    nome: 'IPIAAM',
    url: 'https://www.ipiaam.cv/',
    papel: 'Investigação de acidentes aeronáuticos e marítimos',
    aliases: ['IPIAAM'],
  },
  {
    nome: 'Cabo Verde Airports, S.A.',
    url: 'https://www.caboverde-airports.cv/',
    papel: 'Concessionária aeroportuária (VINCI Airports + ANA)',
    aliases: ['Cabo Verde Airports'],
  },
  {
    nome: 'VINCI Airports',
    url: 'https://www.vinci-airports.com/',
    papel: 'Operador da concessão aeroportuária',
    aliases: ['VINCI Airports'],
  },
  {
    nome: 'SENASA',
    url: 'https://www.senasa.es/',
    papel: 'ATO aprovada pela AAC (Espanha)',
    aliases: ['SENASA'],
  },
  {
    nome: 'NAV Portugal, E.P.E.',
    url: 'https://www.nav.pt/',
    papel: 'ATO aprovada pela AAC (Portugal)',
    aliases: ['NAV Portugal'],
  },
  {
    nome: 'UTA — ISAT',
    url: 'https://uta.cv/',
    papel: 'Formação superior em aviação civil',
    aliases: ['UTA', 'ISAT'],
  },
];
