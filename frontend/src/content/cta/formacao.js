// Base de conhecimento — Formação de CTA.
// Fonte autoritativa: memory/deep-research-report.md. PT-PT.
// Regra editorial (spec §10): validades de certificados de ATO são pontuais —
// publicar sempre com formulação que envelhece bem ("conforme a lista da AAC
// à data desta publicação").

export const notaFonte =
  'Lista e validades conforme a lista oficial de ATO aprovadas pela AAC à ' +
  'data desta publicação. Confirmar sempre na fonte oficial vigente.';

// ATO (Approved Training Organisations) aprovadas pela AAC com cursos CTA
// identificados nas fontes consultadas.
export const ato = [
  {
    nome: 'SENASA',
    pais: 'Espanha',
    certificado: 'CV-05/ATOE',
    escopo:
      'ATCO Basic, rating training, ADI, APP procedural, APP por ' +
      'vigilância, ACC procedural, ACC por vigilância, instrutor prático e ' +
      'avaliadores.',
    validade: '31/07/2027',
  },
  {
    nome: 'NAV Portugal, E.P.E.',
    pais: 'Portugal',
    certificado: 'CV-12/ATOE',
    escopo:
      'Mesmo âmbito CTA da SENASA, acrescido de refresher e conversion ' +
      'training.',
    validade: '25/07/2027',
  },
];

// Caminhos de ingresso.
export const caminhos = [
  {
    titulo: 'Via ATO aprovada',
    desc:
      'Matrícula numa ATO aprovada pela AAC, formação teórica e operacional, ' +
      'aprovação no exame teórico e serviço com tráfego real sob OJTI.',
  },
  {
    titulo: 'Modelo patrocinado / selecionado',
    desc:
      'Existem programas patrocinados (por exemplo, concurso do FPEF em ' +
      'cooperação com a SENASA para curso inicial ATC de TWR — básico e ' +
      'ADI/ADV) com seleção em fases: teste de inglês, teste psicotécnico e ' +
      'de personalidade e entrevista oral em inglês.',
  },
];

// Formação académica complementar — não é via direta de licença CTA.
export const academico = {
  titulo: 'Formação académica complementar',
  desc:
    'A UTA, através do ISAT no Sal, oferece formação superior em Gestão e ' +
    'Planeamento da Aviação Civil. É uma base académica complementar/' +
    'preparatória para o setor — não constitui, por si só, uma via de ' +
    'licenciamento de controlador de tráfego aéreo.',
};
