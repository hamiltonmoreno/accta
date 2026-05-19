// Base de conhecimento — Estrutura ATS de Cabo Verde.
// Fonte autoritativa: memory/deep-research-report.md. PT-PT.

// As quatro camadas funcionais da navegação aérea em Cabo Verde.
export const camadas = [
  {
    sigla: 'AAC',
    nome: 'Agência de Aviação Civil',
    papel: 'Regulador aeronáutico',
    descricao:
      'Autoridade pública responsável pela regulação técnica e económica do ' +
      'setor. Emite os regulamentos CV-CAR e licencia os controladores. ' +
      'Equivalente funcional de uma ANAC/INAC nacional.',
    baseLegal: 'Estatutos aprovados pelo Decreto-Lei n.º 47/2019',
  },
  {
    sigla: 'ASA',
    nome: 'ASA — Navegação Aérea de Cabo Verde, S.A.',
    papel: 'Prestador dos serviços de tráfego aéreo (ATS)',
    descricao:
      'Presta operacionalmente os serviços ATS, incluindo o Centro de ' +
      'Controlo (ACC), as torres de controlo e os serviços de informação de ' +
      'voo. Sede na ilha do Sal.',
    baseLegal: 'Certificação ATS ao abrigo do CV-CAR 17',
  },
  {
    sigla: 'Cabo Verde Airports',
    nome: 'Cabo Verde Airports, S.A.',
    papel: 'Gestão aeroportuária concessionada',
    descricao:
      'Concessionária da gestão dos aeroportos e aeródromos do país desde a ' +
      'entrada em vigor do contrato, em julho de 2023. Não confundir ' +
      'infraestrutura aeroportuária com a prestação ATS.',
    baseLegal: 'Lei n.º 64/IX/2019 e Decreto-Lei n.º 14/2022',
  },
  {
    sigla: 'IPIAAM',
    nome: 'IPIAAM',
    papel: 'Investigação técnica de acidentes e incidentes graves',
    descricao:
      'Conduz a investigação técnica em caso de acidente ou incidente grave, ' +
      'com finalidade preventiva. Não se confunde com a regulação nem com o ' +
      'reporte interno de ocorrências do prestador ATS.',
    baseLegal: 'Decreto-Lei n.º 6/2023',
  },
];

// A FIR Oceânica do Sal.
export const fir = {
  nome: 'FIR Oceânica do Sal',
  baseLegal: 'Decreto-Lei n.º 9/80, de 11 de fevereiro',
  descricao:
    'Uma das maiores regiões de informação de voo do Atlântico. Criada pelo ' +
    'Decreto-Lei n.º 9/80, que integrou os serviços, instalações, ' +
    'equipamentos e pessoal afetos ao seu funcionamento no Aeroporto ' +
    'Internacional Amílcar Cabral. A prestação ATS é operada pela ASA.',
  comunicacoes: 'VHF, HF e CPDLC',
  vigilancia: 'Cobertura radar (Santo Antão, Sal e Santiago) e ADS-C',
  // Regra editorial: dado não publicado, formulação neutra (spec §2).
  utaUir: 'Não especificado nesta versão — confirmar na AIP/e-AIP vigente.',
};

// Órgãos ATS operados pela ASA.
export const unidades = {
  acc: ['ACC — Centro de Controlo de Tráfego Aéreo, no Sal'],
  twr: ['Sal', 'Praia', 'Boa Vista', 'São Vicente'],
  fis: ['São Filipe', 'Maio', 'São Nicolau'],
};

// Infraestrutura aeroportuária (gestão concessionada à Cabo Verde Airports).
export const infraestrutura = {
  resumo: '4 aeroportos internacionais e 3 aeródromos domésticos (7 no total)',
  internacionais: [
    'Aeroporto Internacional Amílcar Cabral (Sal)',
    'Aeroporto Internacional da Praia — Nelson Mandela (Santiago)',
    'Aeroporto Internacional Aristides Pereira (Boa Vista)',
    'Aeroporto Internacional Cesária Évora (São Vicente)',
  ],
  domesticos: [
    'Aeródromo de Preguiça (São Nicolau)',
    'Aeródromo do Maio',
    'Aeródromo de São Filipe (Fogo)',
  ],
};
