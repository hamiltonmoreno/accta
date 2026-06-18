import { Landmark } from 'lucide-react';

// C. Governança & voz — visível a todos os membros. Inclui o guia de decisão
// entre canais, votações, eleições (voto secreto), assembleias, regulamentos e
// as quatro ferramentas formais de participação (proposta, petição,
// esclarecimento, reclamação). Campos e fluxos espelham backend/routes/
// participacao.py + models.py — não inventar estados nem campos.
export const governanca = {
  id: 'governanca',
  titulo: 'Governança e voz',
  icon: Landmark,
  resumo: 'Votar, participar nas assembleias e usar — na ferramenta certa — a sua voz como sócio.',
  artigos: [
    {
      id: 'qual-canal',
      titulo: 'Qual canal de voz devo usar?',
      resumo:
        'O portal tem quatro ferramentas formais de voz, cada uma com um destino e um efeito diferentes. Escolher a certa faz a sua voz seguir o caminho mais rápido.',
      passos: [
        'Quero levar um assunto à Assembleia Geral (debate ou decisão) → Proposta.',
        'Quero obrigar a convocar uma AG extraordinária juntando apoios → Petição (precisa de 1/4 dos votantes).',
        'Tenho uma pergunta/dúvida para um órgão (Direção, Mesa da AG ou Conselho Fiscal) → Pedido de esclarecimento.',
        'Quero contestar um ato, omissão ou decisão que me afeta → Reclamação (com recurso à AG se não for resolvida).',
        'Quero organizar uma iniciativa com tarefas e colaboração → Projetos (em "Comunidade"). Grupos de trabalho e comissões são tipos de Projeto, criados pela Direção (Art. 31.e).',
        'Está em causa uma infração disciplinar → não é aqui: corre por processo disciplinar (Comissão de Inquérito), em "Administração".',
      ],
      dicas: [
        'Uma proposta entra na ordem de trabalhos; uma petição força a própria realização de uma AG. São coisas diferentes.',
        'Esclarecimento é para perguntar; reclamação é para contestar. Se só quer saber, não abra reclamação.',
        'Há dois sentidos de «comissão» no portal: a Comissão como tipo de Projeto (estrutura de trabalho, Art. 31.e) e a Comissão de Inquérito (módulo disciplinar). Não as confunda.',
      ],
      faq: [
        {
          q: 'Proposta ou petição?',
          a: 'Proposta: quer que um ponto seja discutido/votado na próxima AG; a Mesa e a Direção triam. Petição: quer forçar a convocação de uma AG extraordinária e para isso reúne assinaturas até 1/4 dos membros votantes.',
        },
        {
          q: 'Esclarecimento ou reclamação?',
          a: 'Esclarecimento é uma pergunta a um órgão (ex.: pedir contas ao Conselho Fiscal). Reclamação é contestar formalmente um ato ou decisão e exige resposta num prazo, com direito a recurso à AG.',
        },
        {
          q: 'E se o tema for só organizar trabalho entre colegas?',
          a: 'Use Projetos (secção "Comunidade"): tem tarefas, comentários e acompanhamento. Se for uma estrutura formal, a Direção pode criá-lo como Grupo de Trabalho ou Comissão (Art. 31.e). Não precisa de proposta nem de petição para isso.',
        },
      ],
    },
    {
      id: 'votacoes',
      titulo: 'Votações',
      resumo: 'Participar nas votações e sondagens abertas aos sócios.',
      rota: '/votacoes',
      quandoUsar: [
        'A Mesa/Direção abriu uma votação e quer registar a sua posição.',
        'Quer consultar resultados de votações já encerradas.',
      ],
      quandoNaoUsar: [
        'Quer propor um novo assunto para votação — isso é uma Proposta, não acontece aqui.',
        'É uma eleição de órgãos sociais — essa é secreta e está em "Eleições".',
      ],
      passos: [
        'Abra "Votações" na barra lateral.',
        'Escolha uma votação aberta para ver a pergunta e as opções.',
        'Selecione a sua opção e confirme. O seu voto é registado uma única vez.',
        'Após o fecho, pode consultar os resultados (se a visibilidade for de sócios).',
      ],
      dicas: [
        'Só membros votantes ativos podem votar (honorários, técnicos, inativos e suspensos não votam).',
        'Confirme a opção antes de submeter — o voto não é alterável depois de registado.',
      ],
      faq: [
        {
          q: 'Tentei votar e não consegui — porquê?',
          a: 'A votação pode ter fechado, ou a sua conta pode não ter direito de voto (só membros votantes ativos votam).',
        },
      ],
    },
    {
      id: 'eleicoes',
      titulo: 'Eleições (voto secreto)',
      resumo: 'Votar nas eleições dos órgãos sociais com garantia de segredo de voto.',
      rota: '/admin/eleicoes',
      quandoUsar: [
        'Está aberto um período eleitoral para a Assembleia Geral, a Direção ou o Conselho Fiscal.',
        'Quer guardar o comprovativo de que votou.',
      ],
      quandoNaoUsar: [
        'É uma votação corrente (deliberação/sondagem) — essa não é secreta e está em "Votações".',
      ],
      passos: [
        'Abra "Eleições" na barra lateral durante o período eleitoral.',
        'Consulte as listas/candidaturas apresentadas.',
        'Emita o seu voto: o sistema separa a identidade do conteúdo do voto (voto secreto).',
        'Guarde o recibo de voto — comprova que votou, sem revelar em quem.',
      ],
      dicas: [
        'O recibo confirma a participação; não expõe o sentido de voto.',
        'Só pode votar uma vez por eleição.',
      ],
      faq: [
        {
          q: 'O meu voto pode ser associado a mim?',
          a: 'Não. O voto é secreto: o recibo prova a participação, mas o conteúdo do voto é separado da identidade.',
        },
        {
          q: 'Perdi o recibo — e agora?',
          a: 'O recibo serve de comprovativo pessoal. Sem ele continua válido o registo da sua participação, mas guarde-o sempre que possível.',
        },
      ],
    },
    {
      id: 'assembleias',
      titulo: 'Assembleias',
      resumo: 'Acompanhar as assembleias, marcar presença e seguir as deliberações ao vivo.',
      rota: '/admin/assembleias',
      passos: [
        'Abra "Assembleias" na barra lateral.',
        'Escolha a assembleia convocada para ver a ordem de trabalhos (e as propostas incluídas).',
        'Na sala ao vivo, marque a sua presença quando esta for aberta.',
        'Vote as deliberações no momento em que cada uma é posta a votação.',
      ],
      dicas: [
        'A presença é registada para efeitos de quórum e de participação (conta para o seu ranking).',
        'Acompanhe a sala ao vivo para não perder o momento de cada votação — as deliberações abrem uma de cada vez.',
      ],
      faq: [
        {
          q: 'Marquei presença mas a votação não abriu — é normal?',
          a: 'Sim. As deliberações são postas a votação uma de cada vez, ao longo da sessão; aguarde o momento de cada ponto.',
        },
        {
          q: 'Onde vejo as propostas que vão ser discutidas?',
          a: 'Na ordem de trabalhos da assembleia. As propostas aceites e incluídas pela Mesa aparecem aí, pela ordem definida.',
        },
      ],
    },
    {
      id: 'propostas',
      titulo: 'Propostas para a ordem de trabalhos',
      resumo:
        'Submeter um ponto, medida ou tema para a Assembleia Geral. A Mesa da AG e a Direção triam; a Mesa pode incluí-lo na ordem de trabalhos (Art. 9.g/9.h).',
      rota: '/participacao/propostas',
      quandoUsar: [
        'Quer que um assunto concreto seja discutido ou votado na próxima Assembleia.',
        'Tem uma medida que precisa de decisão da AG (ex.: criar/alterar uma regra interna).',
      ],
      quandoNaoUsar: [
        'Só quer uma resposta de um órgão — use um Pedido de esclarecimento.',
        'Quer obrigar a convocar uma AG extraordinária — isso é uma Petição (junta apoios).',
        'É uma queixa sobre um ato que o afeta — use uma Reclamação.',
      ],
      passos: [
        'Em "Participação → Propostas", carregue em "Nova proposta".',
        'Escolha o Tipo, escreva o Título e a Descrição e submeta.',
        'A proposta fica "Submetida"; a Mesa da AG e a Direção fazem a triagem.',
        'Se for "Aceite", a Mesa pode incluí-la na ordem de trabalhos de uma assembleia (com o número do ponto).',
        'Acompanhe o estado na própria página — é notificado a cada mudança.',
      ],
      campos: [
        {
          campo: 'Tipo',
          ajuda: 'Ponto = assunto para discutir/deliberar; Medida = uma decisão concreta que quer ver aprovada; Tema = matéria mais ampla para a AG abordar.',
          exemplo: 'Medida — quando o objetivo é uma deliberação concreta da Assembleia.',
        },
        {
          campo: 'Título',
          ajuda: 'Uma frase clara e específica (3 a 180 caracteres). É o que aparece na lista e na ordem de trabalhos.',
          exemplo: '«Criar regulamento de compensação de turnos noturnos»',
        },
        {
          campo: 'Descrição',
          ajuda: 'Fundamente: o que propõe, porquê e o que pede à AG que decida. Seja concreto (até 5000 caracteres).',
          exemplo: '«Proponho que a AG aprove um regulamento que compense os turnos noturnos dos controladores, definindo critérios e o período de vigência. Justificação: …»',
        },
      ],
      dicas: [
        'Uma proposta bem escrita (pedido concreto + justificação) passa a triagem mais depressa.',
        'Enquanto está "Submetida" ou "Em triagem", só você e quem tria a veem; depois de "Aceite/Incluída" fica visível aos sócios.',
      ],
      faq: [
        {
          q: 'Quem decide se a minha proposta avança?',
          a: 'A triagem (aceitar/recusar) cabe à Mesa da AG e à Direção; a inclusão na ordem de trabalhos é da Mesa da AG. Pode ver o motivo da decisão na própria proposta.',
        },
        {
          q: 'A minha proposta foi recusada — posso saber porquê?',
          a: 'Sim. Quem tria pode deixar um motivo, que fica visível no cartão da proposta.',
        },
      ],
    },
    {
      id: 'peticoes',
      titulo: 'Petições',
      resumo:
        'Reunir o apoio de sócios para forçar a convocação de uma Assembleia Geral extraordinária (Art. 9.f, 19.2.d).',
      rota: '/participacao/peticoes',
      quandoUsar: [
        'Quer obrigar a realização de uma AG extraordinária sobre um tema urgente.',
        'Acredita que reúne apoio suficiente entre os membros votantes (o limiar é 1/4).',
      ],
      quandoNaoUsar: [
        'Só quer um ponto na próxima AG ordinária — isso é uma Proposta, mais simples.',
        'Quer apenas uma resposta de um órgão — use um Esclarecimento.',
      ],
      passos: [
        'Em "Participação → Petições", crie a petição com um título e a fundamentação.',
        'Partilhe-a: outros membros votantes podem assiná-la.',
        'Quando as assinaturas atingem 1/4 dos membros votantes, a petição fica "Atingida" e a Mesa da AG é notificada.',
        'A Mesa encaminha a petição (e pode ligá-la a uma assembleia).',
      ],
      campos: [
        {
          campo: 'Título',
          ajuda: 'O objeto da petição, claro e curto (3 a 180 caracteres).',
          exemplo: '«Convocação de AG extraordinária sobre as escalas de serviço»',
        },
        {
          campo: 'Fundamentação',
          ajuda: 'Porque é que a AG extraordinária se justifica e o que se pretende decidir nela (até 5000 caracteres).',
          exemplo: '«As escalas atuais geram fadiga acima do recomendado. Pedimos uma AG extraordinária para deliberar sobre…»',
        },
      ],
      dicas: [
        'Só sócios com direito a voto podem criar e assinar petições.',
        'Pode retirar a sua assinatura enquanto a petição estiver "Aberta".',
      ],
      faq: [
        {
          q: 'Quantas assinaturas são precisas?',
          a: 'Um quarto (1/4) dos membros votantes. O alvo é calculado sobre o número de votantes no momento em que o limiar é atingido.',
        },
      ],
    },
    {
      id: 'esclarecimentos',
      titulo: 'Pedidos de esclarecimento',
      resumo: 'Fazer uma pergunta formal a um órgão social e obter resposta registada (Art. 9.j).',
      rota: '/participacao/esclarecimentos',
      quandoUsar: [
        'Tem uma dúvida que um órgão (Direção, Mesa da AG ou Conselho Fiscal) deve responder.',
        'Quer pedir contas/informação — por exemplo, ao Conselho Fiscal sobre as finanças.',
      ],
      quandoNaoUsar: [
        'Quer contestar um ato ou decisão (não é só perguntar) — use uma Reclamação.',
        'Quer levar o assunto a deliberação da AG — use uma Proposta.',
      ],
      passos: [
        'Em "Participação → Esclarecimentos", escolha o órgão de destino.',
        'Escreva o Assunto e a Pergunta e submeta.',
        'O órgão é notificado e responde; recebe um aviso quando houver resposta.',
        'Acompanhe o estado (Submetido → Respondido) na mesma página.',
      ],
      campos: [
        {
          campo: 'Órgão de destino',
          ajuda: 'A quem dirige a pergunta: Direção, Mesa da Assembleia Geral ou Conselho Fiscal. Escolha o órgão competente para o tema.',
          exemplo: 'Conselho Fiscal — para questões de contas e fiscalização financeira.',
        },
        {
          campo: 'Assunto',
          ajuda: 'O tema da pergunta, em poucas palavras (3 a 180 caracteres).',
          exemplo: '«Aplicação das receitas de jóias em 2025»',
        },
        {
          campo: 'Pergunta',
          ajuda: 'A pergunta concreta a que o órgão deve responder (até 4000 caracteres).',
          exemplo: '«Podem detalhar como foram aplicadas as receitas de jóias no exercício de 2025?»',
        },
      ],
      dicas: [
        'Dirija ao órgão certo: uma pergunta de contas vai ao Conselho Fiscal, não à Direção.',
        'Vê os seus próprios pedidos; os membros do órgão veem os que lhes são dirigidos.',
      ],
    },
    {
      id: 'reclamacoes',
      titulo: 'Reclamações e recursos',
      resumo:
        'Contestar formalmente um ato, omissão ou decisão que o afeta, com prazo de resposta e recurso à AG (Art. 9.i).',
      rota: '/participacao/reclamacoes',
      quandoUsar: [
        'Foi prejudicado por um ato ou decisão e quer uma resposta formal da Direção.',
        'Não obteve resposta a um pedido e quer acionar o prazo (a Direção tem 15 dias).',
      ],
      quandoNaoUsar: [
        'Só quer informação — use um Esclarecimento.',
        'É uma matéria disciplinar contra outro membro — segue por processo disciplinar (Administração), não aqui.',
      ],
      passos: [
        'Em "Participação → Reclamações", descreva o Assunto e a Descrição e submeta.',
        'A Direção é notificada e tem 15 dias para responder.',
        'Se a resposta não o satisfizer (ou o prazo expirar), pode abrir Recurso para a AG.',
        'A Mesa da AG decide o recurso e o estado fica "Encerrada".',
      ],
      campos: [
        {
          campo: 'Assunto',
          ajuda: 'O que está a contestar, resumido (3 a 180 caracteres).',
          exemplo: '«Falta de resposta ao pedido de atualização de categoria»',
        },
        {
          campo: 'Descrição',
          ajuda: 'Os factos: o que aconteceu, quando, e o que pretende que seja corrigido (até 5000 caracteres).',
          exemplo: '«Submeti a atualização da minha categoria a 10/04 e até hoje não obtive resposta. Peço que seja apreciada e…»',
        },
      ],
      dicas: [
        'Só pode recorrer depois de a Direção responder ou depois de o prazo de 15 dias expirar.',
        'A reclamação é vista por si, pela Direção e pelo admin — não é pública.',
      ],
      faq: [
        {
          q: 'O que acontece se ninguém responder?',
          a: 'Passados os 15 dias sem resposta, pode abrir recurso para a Assembleia Geral, que decide através da Mesa.',
        },
      ],
    },
    {
      id: 'regulamentos',
      titulo: 'Regulamentos',
      resumo: 'Consultar os regulamentos em vigor e o seu histórico de versões.',
      rota: '/regulamentos',
      passos: [
        'Abra "Regulamentos" na barra lateral.',
        'Escolha um regulamento para ler.',
        'Consulte o histórico de versões quando disponível.',
      ],
      dicas: [
        'Confirme sempre que está a ler a versão em vigor antes de a citar (ex.: numa proposta ou reclamação).',
      ],
    },
  ],
};

export default governanca;
