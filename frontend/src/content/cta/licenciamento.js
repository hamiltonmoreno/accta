// Base de conhecimento — Licenciamento de CTA em Cabo Verde.
// Fonte autoritativa: memory/deep-research-report.md. PT-PT.
// Regra editorial: em divergência regulatória prevalece o CV-CAR 2.3 (2026);
// nunca reproduzir a informação antiga da AAC (licença válida 5 anos / perda
// após 6 meses).

export const notaRegulatoria =
  'Em caso de divergência entre páginas informativas antigas e o regulamento ' +
  'em vigor, prevalece o CV-CAR 2.3 (2026), que reviu o regime anterior.';

// Requisitos de emissão da licença CTA.
export const requisitos = [
  {
    titulo: 'Idade mínima',
    desc: 'Ter pelo menos 21 anos de idade.',
    baseLegal: 'CV-CAR 2.3 (2026)',
  },
  {
    titulo: 'Formação aprovada',
    desc:
      'Concluir um curso de formação numa ATO aprovada pela AAC e demonstrar ' +
      'os conhecimentos obrigatórios (legislação aeronáutica, equipamento ' +
      'ATC, conhecimentos gerais de aeronaves, desempenho humano, ' +
      'meteorologia, navegação e procedimentos operacionais).',
    baseLegal: 'CV-CAR 2.3 (2026)',
  },
  {
    titulo: 'Serviço sob OJTI',
    desc:
      'Realizar pelo menos 3 meses de serviço satisfatório envolvendo ' +
      'controlo real de tráfego aéreo sob supervisão de um OJTI (instrutor ' +
      'de formação em contexto de trabalho).',
    baseLegal: 'CV-CAR 2.3 (2026)',
  },
  {
    titulo: 'Proficiência linguística',
    desc:
      'Demonstrar capacidade de falar e compreender a língua inglesa usada ' +
      'nas comunicações de radiotelefonia, no mínimo ao Nível Operacional 4 ' +
      '(ICAO).',
    baseLegal: 'CV-CAR 2.3 (2026)',
  },
  {
    titulo: 'Certificado Médico Classe 3',
    desc:
      'Obter e manter um Certificado Médico Classe 3, com revalidação ' +
      'periódica e exames complementares escalonados por idade.',
    baseLegal: 'CV-CAR 2.4',
  },
];

// Aptidão médica — Certificado Médico Classe 3.
export const medico = {
  baseLegal: 'CV-CAR 2.4',
  resumo:
    'O ingresso e o exercício como CTA exigem Certificado Médico Classe 3. ' +
    'A periodicidade dos exames é escalonada por idade.',
  periodicidade: [
    { faixa: 'Até aos 30 anos', intervalo: 'Até 4 anos (eletrocardiograma no exame inicial)' },
    { faixa: 'Dos 30 aos 49 anos', intervalo: 'Até 2 anos' },
    { faixa: 'A partir dos 50 anos', intervalo: 'Anual' },
  ],
  nota:
    'Inclui ainda exames ORL com audiograma e oftalmológicos, em ' +
    'periodicidades escalonadas por idade e condição visual.',
};

// Recência e validade — o ponto central do regime de 2026.
export const recencia = {
  baseLegal: 'CV-CAR 2.3 (2026)',
  pontos: [
    'A revisão de 2026 eliminou a validade da licença em si.',
    'O que conta para a operação diária é o averbamento de órgão de controlo.',
    'O averbamento de órgão é válido pelo prazo definido no plano de ' +
      'competências da unidade, nunca superior a 3 anos.',
    'O averbamento torna-se inválido se o controlador deixar de exercer os ' +
      'seus privilégios por período superior a 90 dias.',
    'A revalidação exige horas mínimas, formação de refrescamento e ' +
      'avaliação de competência conforme o plano da unidade aprovado pela AAC.',
  ],
};

// Reentrada operacional após afastamento longo (não é via de ingresso).
export const reentrada = {
  baseLegal: 'Diretiva n.º 01/PEL/2024',
  intro:
    'Para afastamentos prolongados, o restabelecimento de privilégios é ' +
    'gradual (regra de reentrada operacional, não o caminho normal de ' +
    'ingresso):',
  escalonamento: [
    { periodo: 'Mais de 6 meses até 1 ano', medida: 'Supervisão e verificação de competência' },
    { periodo: 'Mais de 1 até 5 anos', medida: 'Curso de refrescamento, supervisão mais prolongada e verificação' },
    { periodo: 'Mais de 5 anos', medida: 'Curso inicial, exames, nova qualificação e supervisão ampliada' },
  ],
};

// Conversão de licença estrangeira — fluxo da AAC.
export const conversao = {
  baseLegal: 'Procedimento da AAC (FS.PEL.09 / FS.PEL.01)',
  passos: [
    'Pedido de teste em legislação aeronáutica através do formulário ' +
      'FS.PEL.09, com pagamento da taxa de exame teórico conforme a tabela da AAC.',
    'Apresentação de licença estrangeira válida, Certificado Médico Classe 3, ' +
      'documento de identificação e fotografia.',
    'Comprovação de proficiência linguística na língua usada na ' +
      'radiotelefonia em Cabo Verde e em inglês.',
    'Após aprovação, pedido de conversão através do formulário FS.PEL.01, ' +
      'com pagamento da taxa de conversão conforme a tabela da AAC.',
  ],
};
