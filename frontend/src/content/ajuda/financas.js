import { DollarSign } from 'lucide-react';

// E. Finanças — visível a admin/financeiro e a quem tenha privilégios
// financeiros (Conselho Fiscal em leitura). Campos/categorias espelham
// backend/models.py (INCOME_CATEGORIES/EXPENSE_CATEGORIES) e o gate de
// co-aprovação por Atos (Art. 54). Cada artigo herda o gate da secção.
const FINANCE_GATE = { roles: ['admin', 'financeiro'], privileges: ['view_finances_readonly', 'manage_finances'] };

export const financas = {
  id: 'financas',
  titulo: 'Finanças',
  icon: DollarSign,
  resumo: 'Gestão financeira: transações, categorias, co-aprovações e fiscalização.',
  artigos: [
    {
      id: 'financeiro',
      titulo: 'Financeiro: registar transações',
      resumo: 'Registar e consultar receitas e despesas por categoria, com comprovativo.',
      rota: '/financeiro',
      gate: FINANCE_GATE,
      quandoUsar: [
        'Vai registar uma receita (ex.: uma subvenção recebida) ou uma despesa da associação.',
        'Quer consultar saldos e o movimento por categoria.',
      ],
      quandoNaoUsar: [
        'Só tem acesso de leitura (ex.: Conselho Fiscal) — pode consultar, mas não registar.',
        'É uma despesa acima do limiar de co-aprovação — essa entra por um Ato executado, não diretamente aqui.',
      ],
      passos: [
        'Abra "Financeiro" na barra lateral.',
        'Consulte as transações e os saldos por categoria.',
        'Para registar, escolha o tipo (receita/despesa) e preencha os campos.',
        'Anexe o comprovativo nas despesas e guarde.',
      ],
      campos: [
        {
          campo: 'Tipo',
          ajuda: 'Receita (entrada) ou Despesa (saída). Determina as categorias disponíveis.',
          exemplo: 'Receita',
        },
        {
          campo: 'Categoria',
          ajuda: 'Receita: Quotas, Jóias, Subvenções, Donativos, Venda de Publicações, Juros, Receitas Extraordinárias. Despesa: Operacional, Eventos, Jurídico, Comunicação, Viagens, Outras Despesas.',
          exemplo: '«Subvenções» (receita) ou «Eventos» (despesa)',
        },
        {
          campo: 'Descrição',
          ajuda: 'O que é a transação, em texto claro.',
          exemplo: '«Subvenção anual para atividades de formação»',
        },
        {
          campo: 'Valor (CVE)',
          ajuda: 'Montante em escudos cabo-verdianos.',
          exemplo: '50000',
        },
        {
          campo: 'Data',
          ajuda: 'A data da transação (ISO/data do calendário).',
          exemplo: 'A data em que a verba entrou/saiu.',
        },
        {
          campo: 'Referência',
          ajuda: 'Opcional — número de documento, fatura ou recibo, para conciliação.',
          exemplo: '«FT 2026/014»',
        },
        {
          campo: 'Sócio (opcional)',
          ajuda: 'Liga a transação a um membro, quando faz sentido (ex.: uma jóia de admissão).',
          exemplo: 'O sócio cuja jóia está a registar.',
        },
      ],
      dicas: [
        'O Conselho Fiscal acede em modo de leitura (view_finances_readonly); registar/editar exige manage_finances.',
        'As quotas são descontadas na folha — não há cobrança manual nem situação de incumprimento a tratar aqui.',
        'Alterar o valor da quota ou da jóia não se faz aqui: exige uma deliberação da AG (a configuração reflete essa decisão).',
      ],
      faq: [
        {
          q: 'Vejo o Financeiro mas não consigo editar — porquê?',
          a: 'Tem acesso de leitura (ex.: Conselho Fiscal). A criação/edição de transações exige o privilégio de gestão financeira (manage_finances).',
        },
        {
          q: 'Porque é que uma despesa grande não me deixa registar diretamente?',
          a: 'Acima do limiar de co-aprovação, a despesa só pode entrar através de um Ato de pagamento aprovado e executado (Art. 54). Veja "Co-aprovações".',
        },
      ],
    },
    {
      id: 'co-aprovacoes',
      titulo: 'Co-aprovações (Atos)',
      resumo:
        'A dupla assinatura para atos que vinculam a ACCTA e para pagamentos acima do limiar (Art. 54).',
      rota: '/financeiro/co-aprovacoes',
      gate: FINANCE_GATE,
      quandoUsar: [
        'Vai assumir um compromisso que vincula a associação (ato vinculativo).',
        'Vai fazer um pagamento acima do limiar de co-aprovação definido.',
      ],
      quandoNaoUsar: [
        'É uma despesa pequena, abaixo do limiar — pode registá-la diretamente no Financeiro.',
      ],
      passos: [
        'Abra "Co-aprovações" na barra lateral.',
        'Crie o Ato (vinculativo ou pagamento), com descrição, valor e beneficiário.',
        'As pessoas exigidas assinam (aprovam/rejeitam) — o Ato fica "Aprovado" quando reúne as assinaturas necessárias.',
        'Num pagamento, executar o Ato cria automaticamente a despesa correspondente no Financeiro.',
      ],
      campos: [
        {
          campo: 'Tipo',
          ajuda: 'Vinculativo (compromisso que obriga a ACCTA) ou Pagamento (saída de dinheiro). Determina quem tem de assinar.',
          exemplo: 'Pagamento',
        },
        {
          campo: 'Descrição',
          ajuda: 'O que é o ato/pagamento e a sua finalidade.',
          exemplo: '«Pagamento ao fornecedor da formação de outubro»',
        },
        {
          campo: 'Valor',
          ajuda: 'O montante envolvido (CVE).',
          exemplo: '120000',
        },
        {
          campo: 'Beneficiário',
          ajuda: 'Quem recebe / a contraparte do ato.',
          exemplo: '«Centro de Formação XYZ»',
        },
      ],
      dicas: [
        'Atos vinculativos exigem duas assinaturas da Direção (uma delas o Presidente); pagamentos exigem também o Tesoureiro.',
        'Confirme sempre os valores antes de assinar — a dupla aprovação existe para proteger operações sensíveis.',
        'Só ao executar um Ato de pagamento é que a despesa entra no Financeiro (com o Ato associado).',
      ],
      faq: [
        {
          q: 'Quem precisa de assinar?',
          a: 'Depende do tipo: um ato vinculativo precisa de dois membros da Direção, sendo um o Presidente; um pagamento precisa, além disso, do Tesoureiro.',
        },
      ],
    },
  ],
};

export default financas;
