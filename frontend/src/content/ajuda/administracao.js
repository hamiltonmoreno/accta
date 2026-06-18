import { Settings } from 'lucide-react';

// F. Administração — cada artigo tem o seu gate (admin + privilégio/órgão).
// A secção aparece se o utilizador puder ver pelo menos um dos seus artigos
// (ex.: um moderador vê só Aparência). Campos/fluxos espelham os models reais
// (ComunicadoCreate, SancaoCreate/Comissao, /admin/cargos, honorários 2/3).
export const administracao = {
  id: 'administracao',
  titulo: 'Administração',
  icon: Settings,
  resumo: 'Gestão do sistema: inscrições, utilizadores, cargos, comunicados, disciplina, auditoria e aparência.',
  artigos: [
    {
      id: 'pedidos-inscricao',
      titulo: 'Pedidos de Inscrição',
      resumo: 'Rever e decidir os pedidos de novos membros.',
      rota: '/admin/pedidos-inscricao',
      gate: { roles: ['admin'] },
      quandoUsar: [
        'Há pedidos de inscrição em "pendente_aprovacao" à espera de decisão.',
      ],
      passos: [
        'Abra "Pedidos de Inscrição" na barra lateral.',
        'Analise cada pedido pendente (dados, categoria profissional).',
        'Aprove ou rejeite. A aprovação cria/ativa o acesso do membro.',
      ],
      dicas: [
        'Aprovar um pedido pode desencadear o envio de email ao novo membro — confirme antes de decidir.',
        'Um pedido rejeitado mantém o registo (para auditoria) com estado "rejeitado".',
      ],
    },
    {
      id: 'utilizadores',
      titulo: 'Utilizadores',
      resumo: 'Gerir as contas dos membros e os seus dados de acesso.',
      rota: '/admin/usuarios',
      gate: { roles: ['admin'], privileges: ['manage_users'] },
      quandoUsar: [
        'Precisa de atualizar dados de um membro, mudar o papel/privilégios ou o estado da conta.',
      ],
      quandoNaoUsar: [
        'Quer atribuir um cargo de um órgão social — isso faz-se em "Cargos & Mandatos", não aqui.',
      ],
      passos: [
        'Abra "Utilizadores" na barra lateral.',
        'Procure o utilizador e abra o seu perfil administrativo.',
        'Edite os dados permitidos, o papel (role), os privilégios e o estado da conta.',
      ],
      dicas: [
        'O número de membro é imutável e não é editável pela administração.',
        'Os privilégios são acréscimos ao papel (ex.: "view_finances_readonly" para o Conselho Fiscal) — somam-se ao acesso base.',
        'Toda a ação administrativa fica registada no Audit Log.',
      ],
    },
    {
      id: 'cargos',
      titulo: 'Cargos e Mandatos',
      resumo: 'Atribuir, exonerar ou transferir cargos dos órgãos sociais.',
      rota: '/admin/cargos',
      gate: { roles: ['admin'], privileges: ['manage_users'] },
      quandoUsar: [
        'Vai dar posse, exonerar ou transferir um titular de um cargo (Presidente, Tesoureiro, etc.).',
      ],
      quandoNaoUsar: [
        'Quer só mudar o papel de acesso (role) de alguém — isso é em "Utilizadores".',
      ],
      passos: [
        'Abra "Cargos & Mandatos" na barra lateral.',
        'Escolha a operação: promover (dar posse), exonerar ou transferir um cargo.',
        'Confirme — a operação regista um mandato no histórico do membro (cargo_history).',
      ],
      campos: [
        {
          campo: 'Operação',
          ajuda: 'Promover atribui o cargo a um membro; Exonerar retira-o; Transferir move o cargo de um titular para outro (numa operação atómica).',
          exemplo: 'Transferir — quando um Tesoureiro passa o cargo a outro membro.',
        },
        {
          campo: 'Cargo',
          ajuda: 'O cargo dos órgãos sociais (Assembleia Geral, Direção, Conselho Fiscal). A lista canónica vem da estrutura de governança, não é digitada à mão.',
          exemplo: 'Tesoureiro da Direção',
        },
      ],
      dicas: [
        'Nunca edite um mandato à mão: use sempre promover/exonerar/transferir (ou a proclamação eleitoral).',
        'Os cargos institucionais também são atribuídos automaticamente pela proclamação de uma eleição.',
      ],
    },
    {
      id: 'comunicados',
      titulo: 'Comunicados',
      resumo: 'Enviar comunicados por email e/ou na aplicação a segmentos de membros.',
      rota: '/admin/comunicados',
      gate: { roles: ['admin'], privileges: ['send_comunicados'] },
      quandoUsar: [
        'Quer informar membros de algo (oficial ou informativo), em app e/ou por email.',
      ],
      quandoNaoUsar: [
        'É um aviso automático do sistema (votação, evento) — esses já chegam pelas notificações.',
      ],
      passos: [
        'Abra "Comunicados" na barra lateral.',
        'Escreva o Assunto e o Corpo, escolha o tipo, os canais e o segmento de destinatários.',
        'Reveja com atenção (conteúdo e destinatários) e confirme o envio.',
      ],
      campos: [
        {
          campo: 'Assunto',
          ajuda: 'O título do comunicado (3 a 180 caracteres).',
          exemplo: '«Convocatória da Assembleia Geral Ordinária»',
        },
        {
          campo: 'Corpo',
          ajuda: 'O texto da mensagem que os membros vão receber.',
          exemplo: 'O texto da convocatória, com data, hora e ordem de trabalhos.',
        },
        {
          campo: 'Tipo',
          ajuda: 'Oficial (comunicação formal da associação) ou Informativo (aviso geral).',
          exemplo: 'Oficial',
        },
        {
          campo: 'Canais',
          ajuda: 'Onde entregar: na aplicação (in-app) e/ou por email. Escolha pelo menos um.',
          exemplo: 'In-app + Email',
        },
        {
          campo: 'Destinatários (segmento)',
          ajuda: 'Todos os ativos; por papel (role); por órgão; por categoria de membro; ou manual (escolher pessoas).',
          exemplo: 'Por órgão → Direção; ou Todos os ativos para uma convocatória geral.',
        },
      ],
      dicas: [
        'O canal "email" chega a emails reais de membros — reveja o conteúdo e os destinatários antes de confirmar.',
        'Use o segmento certo: uma convocatória de AG vai a todos os ativos; um aviso interno pode ir só a um órgão.',
      ],
    },
    {
      id: 'disciplina',
      titulo: 'Disciplina e sanções',
      resumo: 'Processos disciplinares, Comissão de Inquérito e sanções, com recurso à AG (Art. 54+).',
      rota: '/admin/disciplinar',
      gate: { roles: ['admin'], match: 'direcao' },
      quandoUsar: [
        'Há indícios de infração disciplinar de um membro a apurar formalmente.',
      ],
      quandoNaoUsar: [
        'É uma queixa genérica sua sobre um ato da associação — use uma Reclamação (Participação).',
        'Quer constituir uma estrutura de trabalho — isso é uma Comissão/Grupo no módulo de Projetos, não um processo disciplinar.',
      ],
      passos: [
        'Abra "Disciplina" na barra lateral.',
        'Registe a proposta de sanção: o membro visado, o tipo, o motivo e o artigo violado.',
        'Constitua a Comissão de Inquérito (3 membros) com um prazo (por defeito 30 dias) para apurar.',
        'Com as conclusões, decida a sanção. A expulsão tem de ser decidida pela Assembleia Geral.',
        'O visado pode recorrer no prazo de 15 dias.',
      ],
      campos: [
        {
          campo: 'Membro visado',
          ajuda: 'O sócio sobre quem corre o processo.',
          exemplo: 'O membro identificado nos factos.',
        },
        {
          campo: 'Tipo de sanção',
          ajuda: 'Advertência, Multa (até 3× a quota mensal), Perda de direitos (com data-limite) ou Expulsão (só por decisão da AG).',
          exemplo: 'Advertência',
        },
        {
          campo: 'Motivo / Artigo violado',
          ajuda: 'A fundamentação dos factos e, se aplicável, o artigo do estatuto/regulamento infringido.',
          exemplo: '«Incumprimento do dever previsto no Art. …»',
        },
        {
          campo: 'Comissão de Inquérito',
          ajuda: 'Exatamente 3 membros que apuram os factos, com um prazo (por defeito 30 dias).',
          exemplo: 'Três membros isentos, com prazo de 30 dias.',
        },
      ],
      dicas: [
        'A Comissão de Inquérito (disciplinar) é diferente de uma "Comissão" do módulo de Projetos — não as confunda.',
        'Multa: máximo de 3× a quota mensal. Perda de direitos: exige uma data-limite. Expulsão: decisão da AG.',
      ],
    },
    {
      id: 'honorarios',
      titulo: 'Membros Honorários',
      resumo: 'Nomear e eleger membros honorários (Direção nomeia, a AG elege por 2/3 — Art. 8.4).',
      rota: '/governanca/honorarios',
      gate: { roles: ['admin'], match: 'governanca' },
      quandoUsar: [
        'A Direção quer propor a atribuição da categoria de membro honorário a alguém.',
      ],
      passos: [
        'Abra "Honorários" na barra lateral.',
        'A Direção nomeia o candidato, com justificação.',
        'A Mesa da AG abre a votação; os membros votantes decidem.',
        'A Mesa apura: com 2/3 dos votos válidos, o candidato é eleito honorário.',
      ],
      dicas: [
        'A votação apura-se sobre os votos válidos (a favor + contra); as abstenções ficam de fora.',
        'Se o eleito ainda não tiver conta, a eleição pode despoletar um convite por email — confirme antes.',
      ],
    },
    {
      id: 'audit-logs',
      titulo: 'Audit Logs',
      resumo: 'Consultar o registo de auditoria de todas as ações administrativas.',
      rota: '/admin/logs',
      gate: { roles: ['admin'], privileges: ['view_audit_logs'] },
      quandoUsar: [
        'Precisa de investigar quem fez o quê e quando (ex.: quem alterou uma transação ou um cargo).',
      ],
      passos: [
        'Abra "Audit Logs" na barra lateral.',
        'Filtre por ação, autor ou data.',
        'Use o registo para investigar quem fez o quê e quando.',
      ],
      dicas: [
        'Toda a escrita administrativa do portal deixa rasto aqui — é a fonte para esclarecer dúvidas e responder ao Conselho Fiscal.',
      ],
    },
    {
      id: 'aparencia',
      titulo: 'Aparência: marca, banners e notícias',
      resumo: 'Personalizar o logótipo, os banners das páginas públicas e as notícias.',
      rota: '/admin/aparencia',
      gate: { roles: ['admin', 'moderador'] },
      passos: [
        'Abra "Aparência" na barra lateral.',
        'No separador Logótipo, substitua a marca (PNG transparente recomendado).',
        'No separador Banners, troque as imagens de cada página pública.',
        'Para o blog, use "Notícias" para publicar e editar artigos.',
      ],
      dicas: [
        'Sem upload, o portal usa o logótipo vetorial por defeito.',
      ],
    },
  ],
};

export default administracao;
