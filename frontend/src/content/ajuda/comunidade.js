import { Users } from 'lucide-react';

// D. Comunidade & conhecimento — visível a todos os membros. Eventos, projetos,
// documentos, mural, galeria, benefícios e a área profissional.
export const comunidade = {
  id: 'comunidade',
  titulo: 'Comunidade e conhecimento',
  icon: Users,
  resumo: 'Eventos, projetos, documentos, mural, galeria, benefícios e área profissional.',
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
      titulo: 'Projetos, grupos e comissões',
      resumo: 'Acompanhar projetos, tarefas e a colaboração entre membros.',
      rota: '/projetos',
      passos: [
        'Abra "Projetos" na barra lateral.',
        'Escolha um projeto para ver o detalhe, as tarefas e os comentários.',
        'Participe nas tarefas que lhe forem atribuídas.',
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
