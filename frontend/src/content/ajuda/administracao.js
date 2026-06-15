import { Settings } from 'lucide-react';

// F. Administração — cada artigo tem o seu gate (admin + privilégio/órgão).
// A secção aparece se o utilizador puder ver pelo menos um dos seus artigos
// (ex.: um moderador vê só Aparência e Notícias).
export const administracao = {
  id: 'administracao',
  titulo: 'Administração',
  icon: Settings,
  resumo: 'Gestão do sistema: utilizadores, cargos, comunicados, auditoria e aparência.',
  artigos: [
    {
      id: 'pedidos-inscricao',
      titulo: 'Pedidos de Inscrição',
      resumo: 'Rever e decidir os pedidos de novos membros.',
      rota: '/admin/pedidos-inscricao',
      gate: { roles: ['admin'] },
      passos: [
        'Abra "Pedidos de Inscrição" na barra lateral.',
        'Analise cada pedido pendente de aprovação.',
        'Aprove ou rejeite. A aprovação cria/ativa o acesso do membro.',
      ],
      dicas: [
        'Aprovar um pedido pode desencadear o envio de email ao novo membro — confirme antes.',
      ],
    },
    {
      id: 'utilizadores',
      titulo: 'Utilizadores',
      resumo: 'Gerir as contas dos membros e os seus dados de acesso.',
      rota: '/admin/usuarios',
      gate: { roles: ['admin'], privileges: ['manage_users'] },
      passos: [
        'Abra "Utilizadores" na barra lateral.',
        'Procure o utilizador e abra o seu perfil administrativo.',
        'Edite os dados permitidos e o estado da conta.',
      ],
      dicas: [
        'O número de membro é imutável e não é editável pela administração.',
        'Toda a ação administrativa fica registada no Audit Log.',
      ],
    },
    {
      id: 'cargos',
      titulo: 'Cargos e Mandatos',
      resumo: 'Atribuir, exonerar ou transferir cargos dos órgãos sociais.',
      rota: '/admin/cargos',
      gate: { roles: ['admin'], privileges: ['manage_users'] },
      passos: [
        'Abra "Cargos & Mandatos" na barra lateral.',
        'Escolha promover, exonerar ou transferir um cargo.',
        'Confirme — a operação regista um mandato no histórico do membro.',
      ],
      dicas: [
        'Nunca edite um mandato à mão: use sempre promover/exonerar/transferir (ou a proclamação eleitoral).',
      ],
    },
    {
      id: 'comunicados',
      titulo: 'Comunicados',
      resumo: 'Enviar comunicados por email e na aplicação aos membros.',
      rota: '/admin/comunicados',
      gate: { roles: ['admin'], privileges: ['send_comunicados'] },
      passos: [
        'Abra "Comunicados" na barra lateral.',
        'Redija o comunicado e escolha os destinatários.',
        'Reveja com atenção e confirme o envio.',
      ],
      dicas: [
        'O envio chega a emails reais de membros — reveja o conteúdo e os destinatários antes de confirmar.',
      ],
    },
    {
      id: 'disciplina',
      titulo: 'Disciplina e sanções',
      resumo: 'Registar e acompanhar processos disciplinares e sanções.',
      rota: '/admin/disciplinar',
      gate: { roles: ['admin'], match: 'direcao' },
      passos: [
        'Abra "Disciplina" na barra lateral.',
        'Consulte ou registe um processo/sanção.',
        'Acompanhe o estado até à decisão.',
      ],
    },
    {
      id: 'honorarios',
      titulo: 'Membros Honorários',
      resumo: 'Gerir a atribuição da categoria de membro honorário.',
      rota: '/governanca/honorarios',
      gate: { roles: ['admin'], match: 'governanca' },
      passos: [
        'Abra "Honorários" na barra lateral.',
        'Atribua ou reveja o estatuto de membro honorário.',
      ],
    },
    {
      id: 'audit-logs',
      titulo: 'Audit Logs',
      resumo: 'Consultar o registo de auditoria de todas as ações administrativas.',
      rota: '/admin/logs',
      gate: { roles: ['admin'], privileges: ['view_audit_logs'] },
      passos: [
        'Abra "Audit Logs" na barra lateral.',
        'Filtre por ação, autor ou data.',
        'Use o registo para investigar quem fez o quê e quando.',
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
