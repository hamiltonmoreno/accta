// REVISÃO HUMANA PENDENTE — espelho FR de src/content/cta (mesma forma; teste de paridade).
const ASSOCIACAO_NOME = 'Association cap-verdienne des contrôleurs de la circulation aérienne';
const ASSOCIACAO_SIGLA = 'ACCTA';

export default {
  ASSOCIACAO_NOME,
  ASSOCIACAO_SIGLA,
  ASSOCIACAO_NOME_COMPLETO: `${ASSOCIACAO_NOME} (${ASSOCIACAO_SIGLA})`,

  // profissao
  definicaoCTA: {
    resumo:
      'Le contrôleur de la circulation aérienne (CCA) est le professionnel ' +
      'titulaire d’une licence délivrée par l’AAC — Agence de l’aviation ' +
      'civile pour exercer, dans un organisme ATS donné, les privilèges des ' +
      'qualifications d’aérodrome, d’approche ou de région, selon la ' +
      'qualification, la mention d’organisme et les exigences médicales et ' +
      'linguistiques applicables.',
    baseLegal: 'CV-CAR 2.3 (2026) ; Annexe 1 de l’OACI (Licences du personnel)',
  },
  responsabilidades: [
    'Prévenir les collisions entre aéronefs',
    'Prévenir les collisions entre les aéronefs et les obstacles sur l’aire de manœuvre',
    'Accélérer et ordonner la circulation aérienne',
    'Fournir les avis et renseignements utiles à l’exécution sûre et efficace des vols',
    'Assurer le service d’alerte et appuyer les opérations de recherche et de sauvetage',
    'Assurer la coordination avec les autres organismes et centres de contrôle',
  ],
  tiposControlo: [
    {
      sigla: 'TWR',
      nome: 'Tour de contrôle (contrôle d’aérodrome)',
      descricao:
        'Les « yeux » de l’aéroport. Ils gèrent les aéronefs à l’atterrissage, ' +
        'au décollage et en mouvement sur les pistes et les aires de trafic.',
      detalheLabel: 'Organismes au Cap-Vert',
      detalhe: 'Sal, Praia, Boa Vista et São Vicente',
    },
    {
      sigla: 'APP',
      nome: 'Contrôle d’approche',
      descricao:
        'Ils prennent en charge les aéronefs dans une zone élargie autour de ' +
        'l’aéroport et organisent la séquence d’atterrissage. Il peut être ' +
        'assuré aux procédures ou avec surveillance.',
      detalheLabel: 'Modalités',
      detalhe: 'Approche aux procédures · Approche avec surveillance',
    },
    {
      sigla: 'ACC',
      nome: 'Contrôle régional',
      descricao:
        'Ils gèrent les aéronefs en croisière dans la FIR océanique de Sal, ' +
        'souvent en traversée de l’Atlantique entre continents. Il peut être ' +
        'assuré aux procédures ou avec surveillance.',
      detalheLabel: 'Centre de contrôle',
      detalhe: 'ACC à Sal — Europe ↔ Amérique du Sud, Afrique ↔ Amérique du Nord',
    },
  ],
  caminhoCTA: [
    {
      etapa: 'Prérequis',
      itens: [
        'Âge minimum de 21 ans',
        'Certificat médical de classe 3',
        'Anglais opérationnel, au minimum niveau 4 (OACI)',
      ],
    },
    {
      etapa: 'Formation initiale',
      itens: [
        'Inscription dans un ATO agréé par l’AAC',
        'Formation théorique agréée (connaissances obligatoires)',
        'Réussite à l’examen théorique',
      ],
    },
    {
      etapa: 'Formation opérationnelle',
      itens: [
        'Formation de qualification (ADI / APP / ACC)',
        'Au moins 3 mois de service avec trafic réel sous OJTI',
        'Évaluation pratique de compétence et délivrance de la licence',
      ],
    },
    {
      etapa: 'Intégration dans un organisme',
      itens: [
        'Cours de mention d’organisme (organisme spécifique)',
        'Autorisation opérationnelle pour la position de travail',
        'Formation de maintien des compétences selon le plan de compétences',
      ],
    },
    {
      etapa: 'Maintien',
      itens: [
        'Revalidation de la mention (jusqu’à 3 ans, selon le plan de l’organisme)',
        'Expérience récente — invalidation après plus de 90 jours sans exercice',
      ],
    },
  ],
  qualificacoes: {
    baseLegal: 'CV-CAR 2.3 (2026)',
    lista: [
      { sigla: 'ADI', nome: 'Contrôle d’aérodrome (aux instruments)' },
      { sigla: 'APP', nome: 'Contrôle d’approche sans surveillance (aux procédures)' },
      { sigla: 'APS', nome: 'Contrôle d’approche avec systèmes de surveillance' },
      { sigla: 'ACP', nome: 'Contrôle régional sans surveillance (aux procédures)' },
      { sigla: 'ACS', nome: 'Contrôle régional avec systèmes de surveillance' },
    ],
  },

  // estruturaAts
  camadas: [
    {
      sigla: 'AAC',
      nome: 'Agence de l’aviation civile (Agência de Aviação Civil)',
      papel: 'Régulateur aéronautique',
      descricao:
        'Autorité publique chargée de la régulation technique et économique du ' +
        'secteur. Elle édicte les règlements CV-CAR et délivre les licences ' +
        'des contrôleurs. Équivalent fonctionnel d’une autorité nationale de ' +
        'l’aviation civile.',
      baseLegal: 'Statuts approuvés par le Decreto-Lei n.º 47/2019',
    },
    {
      sigla: 'ASA',
      nome: 'ASA — Aeroportos e Segurança Aérea, S.A.',
      papel: 'Prestataire des services de la circulation aérienne (ATS)',
      descricao:
        'Assure opérationnellement les services ATS, y compris le centre de ' +
        'contrôle régional (ACC), les tours de contrôle et les services ' +
        'd’information de vol. Siège sur l’île de Sal.',
      baseLegal: 'Certification ATS au titre du CV-CAR 17',
    },
    {
      sigla: 'Cabo Verde Airports',
      nome: 'Cabo Verde Airports, S.A.',
      papel: 'Gestion aéroportuaire concédée',
      descricao:
        'Concessionnaire de la gestion des aéroports et aérodromes du pays ' +
        'depuis juillet 2023 — concession de 40 ans exploitée par VINCI ' +
        'Airports et ANA — Aeroportos de Portugal. L’infrastructure ' +
        'aéroportuaire ne doit pas être confondue avec la fourniture des ' +
        'services ATS.',
      baseLegal: 'Lei n.º 64/IX/2019 et Decreto-Lei n.º 14/2022',
    },
    {
      sigla: 'IPIAAM',
      nome: 'IPIAAM',
      papel: 'Enquête technique sur les accidents et incidents graves',
      descricao:
        'Mène l’enquête technique en cas d’accident ou d’incident grave, à des ' +
        'fins de prévention. Elle se distingue de la régulation comme du ' +
        'compte rendu interne des événements du prestataire ATS.',
      baseLegal: 'Decreto-Lei n.º 6/2023',
    },
  ],
  fir: {
    nome: 'FIR océanique de Sal',
    baseLegal: 'Decreto-Lei n.º 9/80, du 11 février',
    descricao:
      'L’une des plus grandes régions d’information de vol de l’Atlantique, ' +
      'd’environ 1,3 million de km². Créée par le Decreto-Lei n.º 9/80, qui ' +
      'a regroupé les services, installations, équipements et personnels ' +
      'affectés à son fonctionnement à l’aéroport international Amílcar ' +
      'Cabral. La fourniture des services ATS est assurée par l’ASA.',
    comunicacoes: 'VHF, HF et CPDLC',
    vigilancia: 'Couverture radar (Santo Antão, Sal et Santiago) et ADS-C',
    utaUir: 'Non précisé dans cette version — vérifier dans l’AIP/e-AIP en vigueur.',
  },
  unidades: {
    acc: ['ACC — Centre de contrôle de la circulation aérienne, à Sal'],
    twr: ['Sal', 'Praia', 'Boa Vista', 'São Vicente'],
    fis: ['São Filipe', 'Maio', 'São Nicolau'],
  },
  infraestrutura: {
    resumo: '4 aéroports internationaux et 3 aérodromes nationaux (7 au total)',
    internacionais: [
      'Aéroport international Amílcar Cabral (Sal)',
      'Aéroport international de Praia — Nelson Mandela (Santiago)',
      'Aéroport international Aristides Pereira (Boa Vista)',
      'Aéroport international Cesária Évora (São Vicente)',
    ],
    domesticos: [
      'Aérodrome de Preguiça (São Nicolau)',
      'Aérodrome de Maio',
      'Aérodrome de São Filipe (Fogo)',
    ],
  },

  // licenciamento
  notaRegulatoria:
    'En cas de divergence entre d’anciennes pages d’information et le ' +
    'règlement en vigueur, le CV-CAR 2.3 (2026), qui a révisé le régime ' +
    'antérieur, prévaut.',
  requisitos: [
    {
      titulo: 'Âge minimum',
      desc: 'Être âgé d’au moins 21 ans.',
      baseLegal: 'CV-CAR 2.3 (2026)',
    },
    {
      titulo: 'Formation agréée',
      desc:
        'Suivre une formation dans un ATO agréé par l’AAC et démontrer les ' +
        'connaissances obligatoires (droit aérien, équipements ATC, ' +
        'connaissances générales des aéronefs, performances humaines, ' +
        'météorologie, navigation et procédures opérationnelles).',
      baseLegal: 'CV-CAR 2.3 (2026)',
    },
    {
      titulo: 'Service sous OJTI',
      desc:
        'Effectuer au moins 3 mois de service satisfaisant comportant le ' +
        'contrôle effectif de la circulation aérienne sous la supervision d’un ' +
        'OJTI (instructeur de formation en situation de travail).',
      baseLegal: 'CV-CAR 2.3 (2026)',
    },
    {
      titulo: 'Compétence linguistique',
      desc:
        'Démontrer l’aptitude à parler et à comprendre la langue anglaise ' +
        'utilisée dans les communications radiotéléphoniques, au minimum au ' +
        'niveau opérationnel 4 (OACI).',
      baseLegal: 'CV-CAR 2.3 (2026)',
    },
    {
      titulo: 'Certificat médical de classe 3',
      desc:
        'Obtenir et conserver un certificat médical de classe 3, avec ' +
        'revalidation périodique et examens complémentaires échelonnés selon ' +
        'l’âge.',
      baseLegal: 'CV-CAR 2.4',
    },
  ],
  medico: {
    baseLegal: 'CV-CAR 2.4',
    resumo:
      'L’accès à la profession et son exercice exigent un certificat médical ' +
      'de classe 3. La périodicité des examens est échelonnée selon l’âge.',
    periodicidade: [
      { faixa: 'Jusqu’à 30 ans', intervalo: 'Jusqu’à 4 ans (électrocardiogramme à l’examen initial)' },
      { faixa: 'De 30 à 49 ans', intervalo: 'Jusqu’à 2 ans' },
      { faixa: 'À partir de 50 ans', intervalo: 'Annuelle' },
    ],
    nota:
      'Comprend également des examens ORL avec audiogramme et des examens ' +
      'ophtalmologiques, à des périodicités échelonnées selon l’âge et l’état ' +
      'visuel.',
  },
  recencia: {
    baseLegal: 'CV-CAR 2.3 (2026)',
    pontos: [
      'La révision de 2026 a supprimé la durée de validité de la licence elle-même.',
      'Ce qui compte pour l’exploitation quotidienne est la mention d’organisme de contrôle.',
      'La mention d’organisme est valable pour la durée fixée dans le plan de ' +
        'compétences de l’organisme, sans jamais dépasser 3 ans.',
      'La mention devient invalide si le contrôleur cesse d’exercer ses ' +
        'privilèges pendant plus de 90 jours.',
      'La revalidation exige un nombre minimal d’heures, une formation de ' +
        'maintien des compétences et une évaluation selon le plan de ' +
        'l’organisme approuvé par l’AAC.',
    ],
  },
  reentrada: {
    baseLegal: 'Diretiva n.º 01/PEL/2024',
    intro:
      'Après une longue interruption, le rétablissement des privilèges est ' +
      'progressif (règle de reprise opérationnelle, et non voie normale ' +
      'd’accès) :',
    escalonamento: [
      { periodo: 'Plus de 6 mois et jusqu’à 1 an', medida: 'Supervision et vérification des compétences' },
      { periodo: 'Plus de 1 an et jusqu’à 5 ans', medida: 'Cours de maintien, supervision prolongée et vérification' },
      { periodo: 'Plus de 5 ans', medida: 'Cours initial, examens, nouvelle qualification et supervision élargie' },
    ],
  },
  conversao: {
    baseLegal: 'Procédure de l’AAC (FS.PEL.09 / FS.PEL.01)',
    passos: [
      'Demande d’examen de droit aérien au moyen du formulaire FS.PEL.09, ' +
        'avec paiement des frais d’examen théorique selon le barème de l’AAC.',
      'Présentation d’une licence étrangère valide, d’un certificat médical ' +
        'de classe 3, d’une pièce d’identité et d’une photographie.',
      'Preuve de la compétence linguistique dans la langue utilisée en ' +
        'radiotéléphonie au Cap-Vert et en anglais.',
      'Après approbation, demande de conversion au moyen du formulaire ' +
        'FS.PEL.01, avec paiement des frais de conversion selon le barème de l’AAC.',
    ],
  },

  // formacao
  notaFonte:
    'Liste et dates de validité conformes à la liste officielle des ATO ' +
    'agréés par l’AAC à la date de cette publication. Toujours vérifier ' +
    'auprès de la source officielle en vigueur.',
  ato: [
    {
      nome: 'SENASA',
      pais: 'Espagne',
      certificado: 'CV-05/ATOE',
      escopo:
        'ATCO Basic, formation de qualification, ADI, APP aux procédures, APP ' +
        'avec surveillance, ACC aux procédures, ACC avec surveillance, ' +
        'instructeur pratique et évaluateurs.',
      validade: '31/07/2027',
    },
    {
      nome: 'NAV Portugal, E.P.E.',
      pais: 'Portugal',
      certificado: 'CV-12/ATOE',
      escopo:
        'Même périmètre CCA que la SENASA, avec en plus les formations ' +
        'refresher et conversion.',
      validade: '25/07/2027',
    },
  ],
  caminhos: [
    {
      titulo: 'Par un ATO agréé',
      desc:
        'Inscription dans un ATO agréé par l’AAC, formation théorique et ' +
        'opérationnelle, réussite à l’examen théorique et service avec trafic ' +
        'réel sous OJTI.',
    },
    {
      titulo: 'Modèle parrainé / sélectionné',
      desc:
        'Il existe des programmes parrainés (par exemple, le concours du FPEF ' +
        'en coopération avec la SENASA pour un cours ATC initial TWR — base ' +
        'et ADI/ADV) avec une sélection en plusieurs phases : test d’anglais, ' +
        'test psychotechnique et de personnalité, et entretien oral en anglais.',
    },
  ],
  academico: {
    titulo: 'Formation académique complémentaire',
    desc:
      'L’UTA, par l’intermédiaire de l’ISAT à Sal, propose une formation ' +
      'supérieure en gestion et planification de l’aviation civile. Il s’agit ' +
      'd’une base académique complémentaire/préparatoire pour le secteur — ' +
      'elle ne constitue pas, à elle seule, une voie d’accès à la licence de ' +
      'contrôleur de la circulation aérienne.',
  },

  // legislacao
  legislacao: [
    {
      documento:
        'Código Aeronáutico (Code aéronautique) — Decreto-Legislativo n.º ' +
        '1/2001, modifié par le Decreto-Legislativo n.º 4/2009',
      natureza: 'Loi de base',
      tema: 'Fondement juridique de la régulation aéronautique',
      relevancia: 'Donne un fondement juridique aux règlements techniques de l’AAC',
    },
    {
      documento: 'Decreto-Lei n.º 9/80, du 11 février',
      natureza: 'Décret-loi',
      tema: 'Création de la FIR océanique de Sal',
      relevancia: 'Fonde la FIR et la responsabilité ATS sur l’espace océanique de Sal',
    },
    {
      documento: 'Decreto-Lei n.º 47/2019',
      natureza: 'Décret-loi',
      tema: 'Statuts de l’AAC',
      relevancia: 'Définit l’autorité de régulation compétente',
    },
    {
      documento: 'Lei n.º 64/IX/2019',
      natureza: 'Loi',
      tema: 'Régime juridique de la concession aéroportuaire',
      relevancia: 'Distingue l’exploitant aéroportuaire du prestataire ATS',
    },
    {
      documento: 'Decreto-Lei n.º 14/2022',
      natureza: 'Décret-loi',
      tema: 'Attribution de la concession aéroportuaire',
      relevancia: 'A consacré Cabo Verde Airports comme concessionnaire',
    },
    {
      documento: 'CV-CAR 17',
      natureza: 'Règlement technique de l’AAC',
      tema: 'Services de la circulation aérienne',
      relevancia: 'Certification ATS, fatigue, passation de service, qualité, SMS et événements',
    },
    {
      documento: 'CV-CAR 2.3 (2026)',
      natureza: 'Règlement technique de l’AAC',
      tema: 'Licences de CCA',
      relevancia: 'Éligibilité, cours, examen, qualifications, mentions, instructeurs et évaluateurs',
    },
    {
      documento: 'CV-CAR 2.4',
      natureza: 'Règlement technique de l’AAC',
      tema: 'Médecine aéronautique pour les CCA',
      relevancia: 'Certificat médical de classe 3 et aptitude médicale',
    },
    {
      documento: 'Diretiva n.º 01/PEL/2024',
      natureza: 'Directive de l’AAC',
      tema: 'Rétablissement des privilèges',
      relevancia: 'Reprise opérationnelle après de longues périodes sans exercice',
    },
    {
      documento: 'CV-CAR 22',
      natureza: 'Règlement technique de l’AAC',
      tema: 'Notification des événements',
      relevancia: 'Base d’une culture juste et d’un compte rendu préventif, non punitif',
    },
  ],

  // faq
  faq: [
    {
      pergunta: 'Qui réglemente les contrôleurs de la circulation aérienne au Cap-Vert ?',
      resposta:
        'L’autorité de régulation est l’AAC — Agence de l’aviation civile, dont ' +
        'les statuts ont été approuvés par le Decreto-Lei n.º 47/2019.',
    },
    {
      pergunta: 'Qui fournit les services de la circulation aérienne dans le pays ?',
      resposta:
        'L’ASA — Aeroportos e Segurança Aérea, S.A. assure opérationnellement ' +
        'les services ATS, y compris le centre de contrôle régional (ACC), les ' +
        'tours de contrôle et les services d’information de vol.',
    },
    {
      pergunta: 'Quels organismes ATS existent au Cap-Vert ?',
      resposta:
        'Un centre de contrôle à Sal ; des tours de contrôle à Sal, Praia, Boa ' +
        'Vista et São Vicente ; et des services d’information de vol à São ' +
        'Filipe, Maio et São Nicolau.',
    },
    {
      pergunta: 'Quel est l’âge minimum pour la licence de CCA ?',
      resposta: 'Au moins 21 ans, conformément au CV-CAR 2.3 (2026).',
    },
    {
      pergunta: 'Faut-il parler anglais ?',
      resposta:
        'Oui. Une compétence en anglais pour la radiotéléphonie est exigée, au ' +
        'minimum au niveau opérationnel 4 (OACI), conformément au CV-CAR 2.3 (2026).',
    },
    {
      pergunta: 'Faut-il un certificat médical ?',
      resposta:
        'Oui. L’accès à la profession et son exercice exigent un certificat ' +
        'médical de classe 3, conformément au CV-CAR 2.4.',
    },
    {
      pergunta: 'La licence de CCA a-t-elle une durée de validité fixe ?',
      resposta:
        'Le CV-CAR 2.3 (2026) a supprimé la durée de validité de la licence ' +
        'elle-même. En pratique, ce sont la validité des qualifications et ' +
        'surtout celle de la mention d’organisme de contrôle qui comptent. Les ' +
        'anciennes pages d’information mentionnant une validité de 5 ans ne ' +
        'doivent pas être utilisées.',
    },
    {
      pergunta: 'Combien de temps puis-je rester sans exercer avant de perdre l’expérience récente ?',
      resposta:
        'La mention d’organisme devient invalide après plus de 90 jours sans ' +
        'exercice des privilèges.',
    },
    {
      pergunta: 'Existe-t-il des formations de CCA agréées par l’AAC hors du Cap-Vert ?',
      resposta:
        'Oui. La liste révisée comprend notamment la SENASA (Espagne) et NAV ' +
        'Portugal pour les cours de CCA. Toujours vérifier la liste officielle ' +
        'des ATO agréés par l’AAC à la date concernée.',
    },
    {
      pergunta: 'Existe-t-il une association des contrôleurs au Cap-Vert ?',
      resposta:
        'Oui. L’ACCTA — Association cap-verdienne des contrôleurs de la ' +
        'circulation aérienne (Associação Cabo-verdiana dos Controladores de ' +
        'Tráfego Aéreo) représente et valorise les contrôleurs de la ' +
        'circulation aérienne du pays et est l’entité titulaire de ce portail.',
    },
  ],

  // contactosUteis
  notaContactos:
    'Contacts d’organismes officiels tiers, selon des sources publiques à la ' +
    'date de cette publication. Toujours vérifier sur les pages officielles ' +
    'respectives.',
  contactosUteis: [
    {
      entidade: 'AAC — Agence de l’aviation civile',
      papel: 'Régulateur aéronautique',
      contacto: 'Tél. +238 260 34 30 · Achada Grande Frente, Praia, BP 371',
      site: 'https://www.aac.cv/',
    },
    {
      entidade: 'ASA — Aeroportos e Segurança Aérea, S.A.',
      papel: 'Prestataire ATS / navigation aérienne',
      contacto: 'Tél. (+238) 241 92 00 · geral@asa.cv · Espargos, île de Sal',
      site: 'https://www.asa.cv/',
    },
    {
      entidade: 'Cabo Verde Airports, S.A.',
      papel: 'Concessionnaire aéroportuaire',
      contacto: 'Voir la page officielle',
      site: 'https://www.caboverde-airports.cv/',
    },
    {
      entidade: 'UTA — ISAT',
      papel: 'Enseignement supérieur en aviation civile',
      contacto: 'Tél. (+238) 354 11 13 · Espargos, île de Sal',
      site: 'https://uta.cv/',
    },
    {
      entidade: 'SENASA',
      papel: 'ATO agréé par l’AAC pour les cours de CCA',
      contacto: 'Avenida de la Hispanidad, 12, Madrid (Espagne)',
      site: 'https://www.senasa.es/',
    },
    {
      entidade: 'NAV Portugal, E.P.E.',
      papel: 'ATO agréé par l’AAC pour les cours de CCA',
      contacto: 'Edifício 7, Rua C, aéroport Humberto Delgado, Lisbonne (Portugal)',
      site: 'https://www.nav.pt/',
    },
  ],

  // instituicoes — `aliases` têm de existir no texto FR para o TextoInstituicoes ligar
  instituicoes: [
    {
      nome: 'AAC — Agence de l’aviation civile',
      url: 'https://www.aac.cv/',
      papel: 'Régulateur aéronautique',
      aliases: ['Agence de l’aviation civile', 'AAC'],
    },
    {
      nome: 'ASA — Aeroportos e Segurança Aérea, S.A.',
      url: 'https://www.asa.cv/',
      papel: 'Prestataire des services de la circulation aérienne (ATS)',
      aliases: ['Aeroportos e Segurança Aérea', 'ASA'],
    },
    {
      nome: 'OACI — Organisation de l’aviation civile internationale',
      url: 'https://www.icao.int/',
      papel: 'Normes et pratiques recommandées internationales',
      aliases: ['OACI'],
    },
    {
      nome: 'IPIAAM',
      url: 'https://www.ipiaam.cv/',
      papel: 'Enquêtes sur les accidents aéronautiques et maritimes',
      aliases: ['IPIAAM'],
    },
    {
      nome: 'Cabo Verde Airports, S.A.',
      url: 'https://www.caboverde-airports.cv/',
      papel: 'Concessionnaire aéroportuaire (VINCI Airports + ANA)',
      aliases: ['Cabo Verde Airports'],
    },
    {
      nome: 'VINCI Airports',
      url: 'https://www.vinci-airports.com/',
      papel: 'Exploitant de la concession aéroportuaire',
      aliases: ['VINCI Airports'],
    },
    {
      nome: 'SENASA',
      url: 'https://www.senasa.es/',
      papel: 'ATO agréé par l’AAC (Espagne)',
      aliases: ['SENASA'],
    },
    {
      nome: 'NAV Portugal, E.P.E.',
      url: 'https://www.nav.pt/',
      papel: 'ATO agréé par l’AAC (Portugal)',
      aliases: ['NAV Portugal'],
    },
    {
      nome: 'UTA — ISAT',
      url: 'https://uta.cv/',
      papel: 'Enseignement supérieur en aviation civile',
      aliases: ['UTA', 'ISAT'],
    },
  ],
};
