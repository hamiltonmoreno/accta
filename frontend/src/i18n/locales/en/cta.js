// REVISÃO HUMANA PENDENTE — espelho EN de src/content/cta (mesma forma; teste de paridade).
const ASSOCIACAO_NOME = 'Cape Verdean Association of Air Traffic Controllers';
const ASSOCIACAO_SIGLA = 'ACCTA';

export default {
  ASSOCIACAO_NOME,
  ASSOCIACAO_SIGLA,
  ASSOCIACAO_NOME_COMPLETO: `${ASSOCIACAO_NOME} (${ASSOCIACAO_SIGLA})`,

  // profissao
  definicaoCTA: {
    resumo:
      'An Air Traffic Controller (ATCO) is a professional licensed by the ' +
      'AAC — Civil Aviation Agency to exercise, at a specific ATS unit, the ' +
      'privileges of the aerodrome, approach or area ratings, in accordance ' +
      'with the rating, the unit endorsement and the applicable medical and ' +
      'language requirements.',
    baseLegal: 'CV-CAR 2.3 (2026); ICAO Annex 1 (Personnel Licensing)',
  },
  responsabilidades: [
    'Prevent collisions between aircraft',
    'Prevent collisions between aircraft and obstructions on the manoeuvring area',
    'Expedite and maintain an orderly flow of air traffic',
    'Provide advice and information useful for the safe and efficient conduct of flights',
    'Provide the alerting service and support search and rescue operations',
    'Coordinate with other units and control centres',
  ],
  tiposControlo: [
    {
      sigla: 'TWR',
      nome: 'Control Tower (aerodrome control)',
      descricao:
        'The "eyes" of the airport. They manage aircraft landing, taking off ' +
        'and moving on runways and aprons.',
      detalheLabel: 'Units in Cape Verde',
      detalhe: 'Sal, Praia, Boa Vista and São Vicente',
    },
    {
      sigla: 'APP',
      nome: 'Approach Control',
      descricao:
        'They handle aircraft in a wider area around the airport, organising ' +
        'the landing sequence. It may be provided procedurally or with ' +
        'surveillance.',
      detalheLabel: 'Modes',
      detalhe: 'Procedural approach · Surveillance approach',
    },
    {
      sigla: 'ACC',
      nome: 'Area Control',
      descricao:
        'They manage aircraft in cruise flight within the Sal Oceanic FIR, ' +
        'often crossing the Atlantic between continents. It may be provided ' +
        'procedurally or with surveillance.',
      detalheLabel: 'Control Centre',
      detalhe: 'ACC in Sal — Europe ↔ South America, Africa ↔ North America',
    },
  ],
  caminhoCTA: [
    {
      etapa: 'Prerequisites',
      itens: [
        'Minimum age of 21',
        'Class 3 Medical Certificate',
        'Operational English, at least ICAO Level 4',
      ],
    },
    {
      etapa: 'Initial training',
      itens: [
        'Enrolment in an ATO approved by the AAC',
        'Approved theoretical training (mandatory knowledge)',
        'Pass the theoretical examination',
      ],
    },
    {
      etapa: 'Operational training',
      itens: [
        'Rating training (ADI / APP / ACC)',
        'At least 3 months of service with live traffic under an OJTI',
        'Practical competence assessment and issue of the licence',
      ],
    },
    {
      etapa: 'Joining a unit',
      itens: [
        'Unit endorsement course (specific unit)',
        'Operational authorisation for the working position',
        'Refresher training in line with the competence scheme',
      ],
    },
    {
      etapa: 'Maintenance',
      itens: [
        'Revalidation of the endorsement (up to 3 years, per the unit scheme)',
        'Operational recency — invalidated after more than 90 days without exercising privileges',
      ],
    },
  ],
  qualificacoes: {
    baseLegal: 'CV-CAR 2.3 (2026)',
    lista: [
      { sigla: 'ADI', nome: 'Aerodrome control (instrument)' },
      { sigla: 'APP', nome: 'Approach control without surveillance (procedural)' },
      { sigla: 'APS', nome: 'Approach control with surveillance systems' },
      { sigla: 'ACP', nome: 'Area control without surveillance (procedural)' },
      { sigla: 'ACS', nome: 'Area control with surveillance systems' },
    ],
  },

  // estruturaAts
  camadas: [
    {
      sigla: 'AAC',
      nome: 'Civil Aviation Agency (Agência de Aviação Civil)',
      papel: 'Aviation regulator',
      descricao:
        'Public authority responsible for the technical and economic ' +
        'regulation of the sector. It issues the CV-CAR regulations and ' +
        'licenses controllers. Functionally equivalent to a national civil ' +
        'aviation authority.',
      baseLegal: 'Statutes approved by Decreto-Lei n.º 47/2019',
    },
    {
      sigla: 'ASA',
      nome: 'ASA — Aeroportos e Segurança Aérea, S.A.',
      papel: 'Air traffic services (ATS) provider',
      descricao:
        'Provides ATS operationally, including the Area Control Centre (ACC), ' +
        'the control towers and the flight information services. ' +
        'Headquartered on the island of Sal.',
      baseLegal: 'ATS certification under CV-CAR 17',
    },
    {
      sigla: 'Cabo Verde Airports',
      nome: 'Cabo Verde Airports, S.A.',
      papel: 'Concessioned airport management',
      descricao:
        'Concessionaire for the management of the country’s airports and ' +
        'aerodromes since July 2023 — a 40-year concession operated by VINCI ' +
        'Airports and ANA — Aeroportos de Portugal. Airport infrastructure ' +
        'should not be confused with the provision of ATS.',
      baseLegal: 'Lei n.º 64/IX/2019 and Decreto-Lei n.º 14/2022',
    },
    {
      sigla: 'IPIAAM',
      nome: 'IPIAAM',
      papel: 'Technical investigation of accidents and serious incidents',
      descricao:
        'Conducts the technical investigation of accidents or serious ' +
        'incidents, for preventive purposes. It is distinct from regulation ' +
        'and from the ATS provider’s internal occurrence reporting.',
      baseLegal: 'Decreto-Lei n.º 6/2023',
    },
  ],
  fir: {
    nome: 'Sal Oceanic FIR',
    baseLegal: 'Decreto-Lei n.º 9/80, of 11 February',
    descricao:
      'One of the largest flight information regions in the Atlantic, ' +
      'covering about 1.3 million km². Established by Decreto-Lei n.º 9/80, ' +
      'which brought together the services, facilities, equipment and ' +
      'personnel assigned to its operation at Amílcar Cabral International ' +
      'Airport. ATS provision is operated by ASA.',
    comunicacoes: 'VHF, HF and CPDLC',
    vigilancia: 'Radar coverage (Santo Antão, Sal and Santiago) and ADS-C',
    utaUir: 'Not specified in this version — check the current AIP/e-AIP.',
  },
  unidades: {
    acc: ['ACC — Area Control Centre, in Sal'],
    twr: ['Sal', 'Praia', 'Boa Vista', 'São Vicente'],
    fis: ['São Filipe', 'Maio', 'São Nicolau'],
  },
  infraestrutura: {
    resumo: '4 international airports and 3 domestic aerodromes (7 in total)',
    internacionais: [
      'Amílcar Cabral International Airport (Sal)',
      'Praia International Airport — Nelson Mandela (Santiago)',
      'Aristides Pereira International Airport (Boa Vista)',
      'Cesária Évora International Airport (São Vicente)',
    ],
    domesticos: [
      'Preguiça Aerodrome (São Nicolau)',
      'Maio Aerodrome',
      'São Filipe Aerodrome (Fogo)',
    ],
  },

  // licenciamento
  notaRegulatoria:
    'Where older information pages differ from the regulation in force, ' +
    'CV-CAR 2.3 (2026), which revised the previous regime, prevails.',
  requisitos: [
    {
      titulo: 'Minimum age',
      desc: 'Be at least 21 years of age.',
      baseLegal: 'CV-CAR 2.3 (2026)',
    },
    {
      titulo: 'Approved training',
      desc:
        'Complete a training course at an ATO approved by the AAC and ' +
        'demonstrate the mandatory knowledge (air law, ATC equipment, ' +
        'general aircraft knowledge, human performance, meteorology, ' +
        'navigation and operational procedures).',
      baseLegal: 'CV-CAR 2.3 (2026)',
    },
    {
      titulo: 'Service under an OJTI',
      desc:
        'Complete at least 3 months of satisfactory service involving the ' +
        'actual control of air traffic under the supervision of an OJTI ' +
        '(on-the-job training instructor).',
      baseLegal: 'CV-CAR 2.3 (2026)',
    },
    {
      titulo: 'Language proficiency',
      desc:
        'Demonstrate the ability to speak and understand the English ' +
        'language used in radiotelephony communications, at least at ICAO ' +
        'Operational Level 4.',
      baseLegal: 'CV-CAR 2.3 (2026)',
    },
    {
      titulo: 'Class 3 Medical Certificate',
      desc:
        'Obtain and maintain a Class 3 Medical Certificate, with periodic ' +
        'revalidation and additional examinations scaled by age.',
      baseLegal: 'CV-CAR 2.4',
    },
  ],
  medico: {
    baseLegal: 'CV-CAR 2.4',
    resumo:
      'Entry into and practice as an ATCO require a Class 3 Medical ' +
      'Certificate. The frequency of examinations is scaled by age.',
    periodicidade: [
      { faixa: 'Up to age 30', intervalo: 'Up to 4 years (electrocardiogram at the initial examination)' },
      { faixa: 'From 30 to 49', intervalo: 'Up to 2 years' },
      { faixa: 'From age 50', intervalo: 'Annual' },
    ],
    nota:
      'It also includes ENT examinations with audiogram and eye ' +
      'examinations, at intervals scaled by age and visual condition.',
  },
  recencia: {
    baseLegal: 'CV-CAR 2.3 (2026)',
    pontos: [
      'The 2026 revision removed the validity period of the licence itself.',
      'What matters for day-to-day operation is the control unit endorsement.',
      'The unit endorsement is valid for the period set in the unit ' +
        'competence scheme, never more than 3 years.',
      'The endorsement becomes invalid if the controller has not exercised ' +
        'its privileges for more than 90 days.',
      'Revalidation requires minimum hours, refresher training and a ' +
        'competence assessment in line with the unit scheme approved by the AAC.',
    ],
  },
  reentrada: {
    baseLegal: 'Diretiva n.º 01/PEL/2024',
    intro:
      'After long absences, privileges are restored gradually (an ' +
      'operational re-entry rule, not the normal entry route):',
    escalonamento: [
      { periodo: 'More than 6 months up to 1 year', medida: 'Supervision and competence check' },
      { periodo: 'More than 1 up to 5 years', medida: 'Refresher course, longer supervision and check' },
      { periodo: 'More than 5 years', medida: 'Initial course, examinations, new rating and extended supervision' },
    ],
  },
  conversao: {
    baseLegal: 'AAC procedure (FS.PEL.09 / FS.PEL.01)',
    passos: [
      'Application for the air law test using form FS.PEL.09, with payment ' +
        'of the theoretical examination fee according to the AAC fee table.',
      'Submission of a valid foreign licence, Class 3 Medical Certificate, ' +
        'identity document and photograph.',
      'Proof of language proficiency in the language used in radiotelephony ' +
        'in Cape Verde and in English.',
      'Once approved, application for conversion using form FS.PEL.01, with ' +
        'payment of the conversion fee according to the AAC fee table.',
    ],
  },

  // formacao
  notaFonte:
    'List and validity dates as per the official list of ATOs approved by ' +
    'the AAC at the date of this publication. Always check the current ' +
    'official source.',
  ato: [
    {
      nome: 'SENASA',
      pais: 'Spain',
      certificado: 'CV-05/ATOE',
      escopo:
        'ATCO Basic, rating training, ADI, procedural APP, surveillance APP, ' +
        'procedural ACC, surveillance ACC, practical instructor and assessors.',
      validade: '31/07/2027',
    },
    {
      nome: 'NAV Portugal, E.P.E.',
      pais: 'Portugal',
      certificado: 'CV-12/ATOE',
      escopo: 'Same ATCO scope as SENASA, plus refresher and conversion training.',
      validade: '25/07/2027',
    },
  ],
  caminhos: [
    {
      titulo: 'Through an approved ATO',
      desc:
        'Enrolment in an ATO approved by the AAC, theoretical and operational ' +
        'training, passing the theoretical examination and service with live ' +
        'traffic under an OJTI.',
    },
    {
      titulo: 'Sponsored / selected model',
      desc:
        'There are sponsored programmes (for example, the FPEF competition in ' +
        'cooperation with SENASA for an initial ATC TWR course — basic and ' +
        'ADI/ADV) with phased selection: English test, psychometric and ' +
        'personality test, and an oral interview in English.',
    },
  ],
  academico: {
    titulo: 'Complementary academic education',
    desc:
      'UTA, through ISAT in Sal, offers higher education in Civil Aviation ' +
      'Management and Planning. It is a complementary/preparatory academic ' +
      'foundation for the sector — it is not, on its own, a route to an air ' +
      'traffic controller licence.',
  },

  // legislacao
  legislacao: [
    {
      documento:
        'Código Aeronáutico (Aeronautical Code) — Decreto-Legislativo n.º ' +
        '1/2001, as amended by Decreto-Legislativo n.º 4/2009',
      natureza: 'Framework law',
      tema: 'Legal basis for aviation regulation',
      relevancia: 'Provides the legal foundation for the AAC technical regulations',
    },
    {
      documento: 'Decreto-Lei n.º 9/80, of 11 February',
      natureza: 'Decree-law',
      tema: 'Establishment of the Sal Oceanic FIR',
      relevancia: 'Underpins the FIR and ATS responsibility over the Sal oceanic airspace',
    },
    {
      documento: 'Decreto-Lei n.º 47/2019',
      natureza: 'Decree-law',
      tema: 'AAC statutes',
      relevancia: 'Defines the competent regulatory authority',
    },
    {
      documento: 'Lei n.º 64/IX/2019',
      natureza: 'Law',
      tema: 'Legal regime of the airport concession',
      relevancia: 'Distinguishes the airport operator from the ATS provider',
    },
    {
      documento: 'Decreto-Lei n.º 14/2022',
      natureza: 'Decree-law',
      tema: 'Award of the airport concession',
      relevancia: 'Established Cabo Verde Airports as concessionaire',
    },
    {
      documento: 'CV-CAR 17',
      natureza: 'AAC technical regulation',
      tema: 'Air traffic services',
      relevancia: 'ATS certification, fatigue, handover, quality, SMS and occurrences',
    },
    {
      documento: 'CV-CAR 2.3 (2026)',
      natureza: 'AAC technical regulation',
      tema: 'ATCO licensing',
      relevancia: 'Eligibility, course, examination, ratings, endorsements, instructors and assessors',
    },
    {
      documento: 'CV-CAR 2.4',
      natureza: 'AAC technical regulation',
      tema: 'Aviation medicine for ATCOs',
      relevancia: 'Class 3 Medical Certificate and medical fitness',
    },
    {
      documento: 'Diretiva n.º 01/PEL/2024',
      natureza: 'AAC directive',
      tema: 'Restoration of privileges',
      relevancia: 'Operational re-entry after long periods without practice',
    },
    {
      documento: 'CV-CAR 22',
      natureza: 'AAC technical regulation',
      tema: 'Occurrence reporting',
      relevancia: 'Basis for a just culture and preventive, non-punitive reporting',
    },
  ],

  // faq
  faq: [
    {
      pergunta: 'Who regulates air traffic controllers in Cape Verde?',
      resposta:
        'The regulatory authority is the AAC — Civil Aviation Agency, whose ' +
        'statutes were approved by Decreto-Lei n.º 47/2019.',
    },
    {
      pergunta: 'Who provides air traffic services in the country?',
      resposta:
        'ASA — Aeroportos e Segurança Aérea, S.A. provides ATS operationally, ' +
        'including the Area Control Centre (ACC), the control towers and the ' +
        'flight information services.',
    },
    {
      pergunta: 'Which ATS units exist in Cape Verde?',
      resposta:
        'An Area Control Centre in Sal; control towers in Sal, Praia, Boa ' +
        'Vista and São Vicente; and flight information services in São ' +
        'Filipe, Maio and São Nicolau.',
    },
    {
      pergunta: 'What is the minimum age for an ATCO licence?',
      resposta: 'At least 21 years, under CV-CAR 2.3 (2026).',
    },
    {
      pergunta: 'Do I need to speak English?',
      resposta:
        'Yes. English proficiency for radiotelephony is required, at least at ' +
        'ICAO Operational Level 4, under CV-CAR 2.3 (2026).',
    },
    {
      pergunta: 'Is a medical certificate required?',
      resposta:
        'Yes. Entry into and practice as an ATCO require a Class 3 Medical ' +
        'Certificate, under CV-CAR 2.4.',
    },
    {
      pergunta: 'Does the ATCO licence have a fixed validity period?',
      resposta:
        'CV-CAR 2.3 (2026) removed the validity period of the licence itself. ' +
        'In practice, what applies is the validity of the ratings and, above ' +
        'all, of the control unit endorsement. Older information pages that ' +
        'mentioned a 5-year validity should not be used.',
    },
    {
      pergunta: 'How long can I go without operating before losing recency?',
      resposta:
        'The unit endorsement becomes invalid after more than 90 days without ' +
        'exercising the privileges.',
    },
    {
      pergunta: 'Is there AAC-approved ATCO training outside Cape Verde?',
      resposta:
        'Yes. The revised list includes, among others, SENASA (Spain) and NAV ' +
        'Portugal for ATCO courses. Always check the official list of ' +
        'AAC-approved ATOs at the time.',
    },
    {
      pergunta: 'Is there an association of controllers in Cape Verde?',
      resposta:
        'Yes. ACCTA — the Cape Verdean Association of Air Traffic Controllers ' +
        '(Associação Cabo-verdiana dos Controladores de Tráfego Aéreo) ' +
        'represents and promotes the country’s air traffic controllers and is ' +
        'the owner of this portal.',
    },
  ],

  // contactosUteis
  notaContactos:
    'Contacts of third-party official bodies, as per public sources at the ' +
    'date of this publication. Always check the respective official pages.',
  contactosUteis: [
    {
      entidade: 'AAC — Civil Aviation Agency',
      papel: 'Aviation regulator',
      contacto: 'Tel. +238 260 34 30 · Achada Grande Frente, Praia, PO Box 371',
      site: 'https://www.aac.cv/',
    },
    {
      entidade: 'ASA — Aeroportos e Segurança Aérea, S.A.',
      papel: 'ATS / air navigation provider',
      contacto: 'Tel. (+238) 241 92 00 · geral@asa.cv · Espargos, Sal Island',
      site: 'https://www.asa.cv/',
    },
    {
      entidade: 'Cabo Verde Airports, S.A.',
      papel: 'Airport concessionaire',
      contacto: 'See official page',
      site: 'https://www.caboverde-airports.cv/',
    },
    {
      entidade: 'UTA — ISAT',
      papel: 'Higher education in civil aviation',
      contacto: 'Tel. (+238) 354 11 13 · Espargos, Sal Island',
      site: 'https://uta.cv/',
    },
    {
      entidade: 'SENASA',
      papel: 'AAC-approved ATO for ATCO courses',
      contacto: 'Avenida de la Hispanidad, 12, Madrid (Spain)',
      site: 'https://www.senasa.es/',
    },
    {
      entidade: 'NAV Portugal, E.P.E.',
      papel: 'AAC-approved ATO for ATCO courses',
      contacto: 'Edifício 7, Rua C, Humberto Delgado Airport, Lisbon (Portugal)',
      site: 'https://www.nav.pt/',
    },
  ],

  // instituicoes — `aliases` têm de existir no texto EN para o TextoInstituicoes ligar
  instituicoes: [
    {
      nome: 'AAC — Civil Aviation Agency',
      url: 'https://www.aac.cv/',
      papel: 'Aviation regulator',
      aliases: ['Civil Aviation Agency', 'AAC'],
    },
    {
      nome: 'ASA — Aeroportos e Segurança Aérea, S.A.',
      url: 'https://www.asa.cv/',
      papel: 'Air traffic services (ATS) provider',
      aliases: ['Aeroportos e Segurança Aérea', 'ASA'],
    },
    {
      nome: 'ICAO — International Civil Aviation Organization',
      url: 'https://www.icao.int/',
      papel: 'International standards and recommended practices',
      aliases: ['ICAO'],
    },
    {
      nome: 'IPIAAM',
      url: 'https://www.ipiaam.cv/',
      papel: 'Aviation and maritime accident investigation',
      aliases: ['IPIAAM'],
    },
    {
      nome: 'Cabo Verde Airports, S.A.',
      url: 'https://www.caboverde-airports.cv/',
      papel: 'Airport concessionaire (VINCI Airports + ANA)',
      aliases: ['Cabo Verde Airports'],
    },
    {
      nome: 'VINCI Airports',
      url: 'https://www.vinci-airports.com/',
      papel: 'Operator of the airport concession',
      aliases: ['VINCI Airports'],
    },
    {
      nome: 'SENASA',
      url: 'https://www.senasa.es/',
      papel: 'AAC-approved ATO (Spain)',
      aliases: ['SENASA'],
    },
    {
      nome: 'NAV Portugal, E.P.E.',
      url: 'https://www.nav.pt/',
      papel: 'AAC-approved ATO (Portugal)',
      aliases: ['NAV Portugal'],
    },
    {
      nome: 'UTA — ISAT',
      url: 'https://uta.cv/',
      papel: 'Higher education in civil aviation',
      aliases: ['UTA', 'ISAT'],
    },
  ],
};
