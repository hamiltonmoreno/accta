import { LayoutDashboard } from 'lucide-react';

// B. O meu portal — funcionalidades do próprio sócio. Visível a todos
// (a Carteira é só para sócios, marcada com gate).
export const meuPortal = {
  id: 'meu-portal',
  titulo: 'O meu portal',
  icon: LayoutDashboard,
  resumo: 'O seu painel pessoal: dashboard, carteira, ranking e notificações.',
  artigos: [
    {
      id: 'dashboard',
      titulo: 'Dashboard',
      resumo: 'A primeira página depois de entrar — um resumo do que lhe interessa.',
      rota: '/dashboard',
      passos: [
        'Ao entrar, é levado ao Dashboard.',
        'Cada cartão resume um módulo (votações abertas, próximos eventos, avisos recentes…).',
        'Carregue num cartão para abrir o módulo correspondente.',
        'Volte ao Dashboard a qualquer momento pelo logótipo no cabeçalho.',
      ],
      dicas: [
        'Os cartões mostram só o que é relevante para si — começam vazios numa conta nova e enchem-se com a atividade.',
      ],
    },
    {
      id: 'carteira',
      titulo: 'Carteira Digital',
      resumo: 'O seu cartão de membro digital com o estado da associação.',
      rota: '/carteira',
      gate: { roles: ['socio'] },
      passos: [
        'Abra "Carteira Digital" no menu do avatar.',
        'Veja o seu cartão de membro, número de sócio e estado (ativo / inativo / pendente).',
        'Pode apresentar o código do cartão quando for pedido para validação.',
      ],
      dicas: [
        'As quotas são descontadas na folha de pagamento — não há cobrança manual nem situação de incumprimento.',
        'O número de sócio é permanente e não muda.',
      ],
      faq: [
        { q: 'O meu cartão pode ser validado por terceiros?', a: 'Sim. O código do cartão permite confirmar que é sócio através do validador público do portal.' },
      ],
    },
    {
      id: 'ranking',
      titulo: 'Ranking de sócios',
      resumo: 'A pontuação de participação dos membros.',
      rota: '/ranking',
      passos: [
        'Abra "Ranking" no menu do avatar.',
        'Veja a sua posição e a pontuação acumulada.',
        'A pontuação reflete a participação (presença em assembleias, votações, eventos, etc.).',
      ],
      dicas: [
        'A participação consistente faz subir a posição ao longo do tempo.',
        'A pontuação é recalculada periodicamente — pode não refletir de imediato a última ação.',
      ],
    },
    {
      id: 'notificacoes',
      titulo: 'Notificações',
      resumo: 'Onde chegam os avisos do portal e como geri-los.',
      rota: '/notificacoes',
      passos: [
        'Abra o sino no cabeçalho para ver os avisos recentes.',
        'Carregue numa notificação para ir diretamente ao que a originou.',
        'Use "marcar como lida" para limpar o contador.',
        'Veja o histórico completo na página de Notificações.',
      ],
      dicas: [
        'Os avisos chegam em tempo real; se a ligação cair, o portal volta a verificar a cada 30 segundos.',
      ],
      faq: [
        { q: 'Recebo notificações por email?', a: 'Alguns avisos importantes (ex.: comunicados da Direção) também são enviados por email; os restantes ficam no portal.' },
      ],
    },
  ],
};

export default meuPortal;
