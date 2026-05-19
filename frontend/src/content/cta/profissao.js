// Base de conhecimento — A profissão de Controlador de Tráfego Aéreo (CTA).
// Fonte autoritativa: memory/deep-research-report.md. Não publicar números
// sem fonte oficial; citar sempre a base legal (CV-CAR / decreto).
// PT-PT. Ver tasks/spec-base-conhecimento.md.

export const definicaoCTA = {
  // Formulação fiel ao CV-CAR 2.3 (2026) — inferência editorial do relatório.
  resumo:
    'O Controlador de Tráfego Aéreo (CTA) é o profissional licenciado pela ' +
    'AAC — Agência de Aviação Civil para exercer, num órgão ATS específico, ' +
    'os privilégios das qualificações de aeródromo, aproximação ou área, ' +
    'conforme a qualificação, o averbamento de órgão e os requisitos médicos ' +
    'e linguísticos aplicáveis.',
  baseLegal: 'CV-CAR 2.3 (2026); Anexo 1 da ICAO (Personnel Licensing)',
};

// Objetivos dos Serviços de Tráfego Aéreo — Anexo 11 da ICAO, reproduzido
// pelo CV-CAR 17 (ATC + FIS + serviço de alerta).
export const responsabilidades = [
  'Prevenir colisões entre aeronaves',
  'Prevenir colisões entre aeronaves e obstáculos na área de manobras',
  'Acelerar e manter um fluxo de tráfego aéreo ordenado',
  'Fornecer informação útil à condução segura e eficiente dos voos',
  'Prestar serviço de alerta e apoio às operações de busca e salvamento',
  'Coordenar com outros órgãos e centros de controlo',
];

// O serviço de controlo de tráfego aéreo desdobra-se, no CV-CAR 17, em
// controlo de aeródromo (TWR), de aproximação (APP) e de área (ACC).
export const tiposControlo = [
  {
    sigla: 'TWR',
    nome: 'Torre de Controlo (controlo de aeródromo)',
    descricao:
      'São os "olhos" do aeroporto. Gerem as aeronaves a aterrar, a descolar ' +
      'e a movimentar-se nas pistas e pátios.',
    detalheLabel: 'Órgãos em Cabo Verde',
    detalhe: 'Sal, Praia, Boa Vista e São Vicente',
  },
  {
    sigla: 'APP',
    nome: 'Controlo de Aproximação',
    descricao:
      'Cuidam das aeronaves numa área alargada em torno do aeroporto, ' +
      'organizando a sequência para a aterragem. Pode ser prestado por ' +
      'procedimentos ou por vigilância.',
    detalheLabel: 'Modalidades',
    detalhe: 'Aproximação procedural · Aproximação por vigilância',
  },
  {
    sigla: 'ACC',
    nome: 'Controlo de Área',
    descricao:
      'Gerem as aeronaves em voo de cruzeiro na FIR Oceânica do Sal, muitas ' +
      'vezes a atravessar o Atlântico entre continentes. Pode ser prestado ' +
      'por procedimentos ou por vigilância.',
    detalheLabel: 'Centro de Controlo',
    detalhe: 'ACC no Sal — Europa ↔ América do Sul, África ↔ América do Norte',
  },
];

// Linha do tempo "Como se tornar CTA" — fluxo do relatório.
export const caminhoCTA = [
  {
    etapa: 'Pré-requisitos',
    itens: [
      'Idade mínima de 21 anos',
      'Certificado Médico Classe 3',
      'Inglês operacional, no mínimo Nível 4 (ICAO)',
    ],
  },
  {
    etapa: 'Formação inicial',
    itens: [
      'Matrícula numa ATO aprovada pela AAC',
      'Formação teórica aprovada (conhecimentos obrigatórios)',
      'Aprovação no exame teórico',
    ],
  },
  {
    etapa: 'Formação operacional',
    itens: [
      'Formação de qualificação (ADI / APP / ACC)',
      'Pelo menos 3 meses de serviço com tráfego real sob OJTI',
      'Avaliação prática de competência e emissão da licença',
    ],
  },
  {
    etapa: 'Ingresso numa unidade',
    itens: [
      'Curso para averbamento de órgão (unidade específica)',
      'Autorização operacional para a posição de trabalho',
      'Formação de refrescamento conforme o plano de competências',
    ],
  },
  {
    etapa: 'Manutenção',
    itens: [
      'Revalidação do averbamento (até 3 anos, por plano da unidade)',
      'Recência operacional — invalidação após mais de 90 dias sem exercício',
    ],
  },
];

// As cinco qualificações de CTA previstas no CV-CAR 2.3 (2026).
export const qualificacoes = {
  baseLegal: 'CV-CAR 2.3 (2026)',
  lista: [
    { sigla: 'ADI', nome: 'Controlo de aeródromo' },
    { sigla: 'APP procedural', nome: 'Controlo de aproximação sem vigilância' },
    { sigla: 'APP vigilância', nome: 'Controlo de aproximação com sistemas de vigilância' },
    { sigla: 'ACC procedural', nome: 'Controlo de área sem vigilância' },
    { sigla: 'ACC vigilância', nome: 'Controlo de área com sistemas de vigilância' },
  ],
};
