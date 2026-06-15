import { DollarSign } from 'lucide-react';

// E. Finanças — visível a admin/financeiro e a quem tenha privilégios
// financeiros (Conselho Fiscal em leitura). Cada artigo herda o gate da secção
// salvo indicação própria.
const FINANCE_GATE = { roles: ['admin', 'financeiro'], privileges: ['view_finances_readonly', 'manage_finances'] };

export const financas = {
  id: 'financas',
  titulo: 'Finanças',
  icon: DollarSign,
  resumo: 'Gestão financeira: transações, configurações e co-aprovações.',
  artigos: [
    {
      id: 'financeiro',
      titulo: 'Financeiro',
      resumo: 'Registar e consultar transações, receitas, despesas e configurações.',
      rota: '/financeiro',
      gate: FINANCE_GATE,
      passos: [
        'Abra "Financeiro" na barra lateral.',
        'Consulte as transações e os saldos por categoria.',
        'Registe receitas/despesas conforme as categorias definidas.',
        'Ajuste as configurações financeiras quando autorizado.',
      ],
      dicas: [
        'O Conselho Fiscal acede em modo de leitura (view_finances_readonly); a gestão exige manage_finances.',
        'As quotas são descontadas na folha — não existe incumprimento de quotas a tratar aqui.',
      ],
      faq: [
        { q: 'Vejo o Financeiro mas não consigo editar — porquê?', a: 'Tem acesso de leitura (ex.: Conselho Fiscal). A criação/edição de transações exige o privilégio de gestão financeira.' },
      ],
    },
    {
      id: 'co-aprovacoes',
      titulo: 'Co-aprovações',
      resumo: 'O fluxo de dupla aprovação para operações que o exigem.',
      rota: '/financeiro/co-aprovacoes',
      gate: FINANCE_GATE,
      passos: [
        'Abra "Co-aprovações" na barra lateral.',
        'Veja as operações pendentes da sua aprovação.',
        'Aprove ou rejeite; algumas operações só ficam efetivas com a segunda aprovação.',
      ],
      dicas: [
        'A dupla aprovação protege operações sensíveis — confirme os valores antes de aprovar.',
      ],
    },
  ],
};

export default financas;
