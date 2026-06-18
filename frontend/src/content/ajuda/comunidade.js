import { Users } from 'lucide-react';

// D. Comunidade & conhecimento — visível a todos os membros. Eventos, projetos
// (incl. grupos de trabalho e comissões — Art. 31.e), documentos, mural,
// galeria, benefícios e a área profissional. O artigo "Projetos…" espelha
// PROJECT_TIPOS (projeto/grupo_trabalho/comissao) e a regra de criação real
// (backend/routes/projects.py): só a Direção/admin cria grupos e comissões.
export const comunidade = {
  id: 'comunidade',
  titulo: 'Comunidade e conhecimento',
  icon: Users,
  resumo: 'Eventos, projetos, grupos de trabalho, comissões, documentos, mural, galeria, benefícios e área profissional.',
  artigos: [
    {
      id: 'eventos',
      titulo: 'Eventos',
      resumo: 'Ver e inscrever-se nos eventos da associação.',
      rota: '/eventos',
      passos: [
        'Abra "Eventos" na barra lateral.',
        'Escolha um evento para ver detalhes (data, local, descrição).',
        'Inscreva-se quando as inscrições estiverem abertas.',
      ],
    },
    {
      id: 'projetos',
      titulo: 'Projetos, grupos de trabalho e comissões',
      resumo:
        'Três tipos de estrutura colaborativa no mesmo módulo, com as mesmas ferramentas (tarefas, marcos, despesas, comentários). O que muda é a natureza e quem os cria.',
      rota: '/projetos',
      quandoUsar: [
        'Quer organizar uma iniciativa, estudo ou atividade com tarefas e colaboração entre membros.',
        'Quer acompanhar o trabalho de um grupo de trabalho ou de uma comissão e as suas tarefas.',
      ],
      quandoNaoUsar: [
        'Quer levar um assunto a decisão da Assembleia — isso é uma Proposta (secção "Governança e voz").',
        'É um processo disciplinar contra um membro — corre na Comissão de Inquérito (disciplinar), não aqui.',
      ],
      passos: [
        'Abra "Projetos" na barra lateral. Use as abas Projetos · Grupos de Trabalho · Comissões para filtrar.',
        'Escolha um item para ver o detalhe: tarefas, marcos, despesas e comentários.',
        'Participe nas tarefas que lhe forem atribuídas e comente o andamento.',
        'Para propor um Projeto comum, use "Novo Projeto" (entra como proposta e aguarda aprovação).',
      ],
      campos: [
        {
          campo: 'Tipo',
          ajuda: 'Projeto = iniciativa concreta proposta por qualquer sócio. Grupo de Trabalho e Comissão (Art. 31.e) só são criados pela Direção/admin e nascem já aprovados. O seletor de tipo só aparece a quem pode criar grupos/comissões.',
          exemplo: 'Grupo de Trabalho — para um estudo pontual; Comissão — para uma área de trabalho continuada.',
        },
        {
          campo: 'Título',
          ajuda: 'Nome claro da estrutura ou iniciativa.',
          exemplo: '«Festa do Dia do Controlador 2026» (projeto) ou «Grupo de Trabalho — Fadiga e Escalas» (grupo).',
        },
        {
          campo: 'Descrição',
          ajuda: 'O objetivo e o âmbito: o que se pretende fazer e até onde vai.',
          exemplo: '«Estudar o impacto das escalas atuais na fadiga e propor recomendações à Direção.»',
        },
        {
          campo: 'Visibilidade',
          ajuda: 'Público (visível aos sócios depois de aprovado) ou Privado (restrito à Direção e à equipa).',
          exemplo: 'Privado (Direção) — enquanto a comissão prepara um parecer interno.',
        },
        {
          campo: 'Categoria',
          ajuda: 'Uma etiqueta livre para agrupar (ex.: Social, Formação, Técnico).',
          exemplo: '«Formação»',
        },
        {
          campo: 'Orçamento (CVE)',
          ajuda: 'Valor estimado, se aplicável. Pode ficar a 0.',
          exemplo: '0 (sem orçamento próprio)',
        },
        {
          campo: 'Início / Fim',
          ajuda: 'Datas de vigência. O Fim é especialmente útil em grupos de trabalho eventuais, que se encerram quando concluem.',
          exemplo: 'Início hoje; Fim no encerramento previsto do estudo.',
        },
      ],
      dicas: [
        'Grupos de trabalho e comissões partilham as mesmas ferramentas que um projeto — a diferença está na natureza e em quem os cria.',
        'O coordenador de um grupo/comissão é uma função operacional, não um cargo estatutário — não entra no histórico de mandatos.',
      ],
      faq: [
        {
          q: 'Quando uso um grupo de trabalho em vez de uma comissão?',
          a: 'Em regra: grupo de trabalho para algo pontual e temporário (um estudo, um evento, um objetivo com prazo, que se encerra ao concluir); comissão para uma área de trabalho mais formal e continuada. Mecanicamente são iguais; a escolha do tipo é da Direção, conforme a natureza da estrutura (Art. 31.e).',
        },
        {
          q: 'Posso criar um grupo de trabalho ou uma comissão?',
          a: 'Não. Só a Direção ou o admin os criam (Art. 31.e) e ficam logo aprovados. Um sócio ativo pode, isso sim, propor um Projeto comum, que entra como proposta e aguarda aprovação.',
        },
        {
          q: 'Esta «Comissão» é a mesma do disciplinar?',
          a: 'Não. Aqui «Comissão» é uma estrutura de trabalho (Art. 31.e). A Comissão de Inquérito é outra coisa — pertence ao módulo disciplinar, em "Administração".',
        },
      ],
    },
    {
      id: 'documentos',
      titulo: 'Documentos',
      resumo: 'Consultar e descarregar os documentos disponíveis para sócios.',
      rota: '/documentos',
      passos: [
        'Abra "Documentos" na barra lateral.',
        'Procure o documento pretendido.',
        'Descarregue o ficheiro (PDF e outros).',
      ],
    },
    {
      id: 'mural',
      titulo: 'Mural',
      resumo: 'O espaço de partilha e conversa entre os sócios.',
      rota: '/mural',
      passos: [
        'Abra "Mural" (ícone no cabeçalho em computador; no menu do avatar em telemóvel).',
        'Leia as publicações e reaja/comente.',
        'Publique respeitando as regras de convivência.',
      ],
      dicas: [
        'As publicações passam por moderação antes de ficarem visíveis a todos.',
      ],
    },
    {
      id: 'galeria',
      titulo: 'Galeria',
      resumo: 'Ver e contribuir com fotos dos eventos e da vida associativa.',
      rota: '/galeria-admin',
      passos: [
        'Abra "Galeria" na barra lateral.',
        'Navegue pelos álbuns.',
        'Ao submeter fotos, lembre-se de que carecem de aprovação antes de ficarem visíveis.',
      ],
      faq: [
        {
          q: 'Submeti uma foto e não aparece — porquê?',
          a: 'Todas as fotos passam por aprovação de um moderador antes de ficarem visíveis na galeria.',
        },
      ],
    },
    {
      id: 'beneficios',
      titulo: 'Benefícios',
      resumo: 'Consultar as vantagens e parcerias para sócios.',
      rota: '/beneficios',
      passos: [
        'Abra "Benefícios" na barra lateral.',
        'Veja os parceiros e as condições especiais.',
      ],
    },
    {
      id: 'profissional',
      titulo: 'Área profissional: formações, publicações, defesa e relações',
      resumo: 'Os recursos ligados à profissão de controlador de tráfego aéreo.',
      rota: '/formacoes',
      passos: [
        'Formações — consultar formações e certificações.',
        'Publicações — aceder a revistas, boletins, artigos e relatórios técnicos.',
        'Defesa Profissional — acompanhar tomadas de posição e representações.',
        'Relações Externas — ver as filiações e parcerias (ex.: IFATCA).',
      ],
    },
  ],
};

export default comunidade;
