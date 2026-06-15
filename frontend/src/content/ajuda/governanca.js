import { Landmark } from 'lucide-react';

// C. Governança & voz — visível a todos os membros. Inclui votações, eleições
// (voto secreto), assembleias, regulamentos e os canais de participação.
export const governanca = {
  id: 'governanca',
  titulo: 'Governança e voz',
  icon: Landmark,
  resumo: 'Votar, participar nas assembleias e usar os canais de voz dos sócios.',
  artigos: [
    {
      id: 'votacoes',
      titulo: 'Votações',
      resumo: 'Participar nas votações e sondagens abertas aos sócios.',
      rota: '/votacoes',
      passos: [
        'Abra "Votações" na barra lateral.',
        'Escolha uma votação aberta para ver a pergunta e as opções.',
        'Selecione a sua opção e confirme. O seu voto é registado uma única vez.',
        'Após o fecho, pode consultar os resultados.',
      ],
      dicas: [
        'Só membros votantes ativos podem votar.',
      ],
    },
    {
      id: 'eleicoes',
      titulo: 'Eleições (voto secreto)',
      resumo: 'Votar nas eleições dos órgãos sociais com garantia de segredo de voto.',
      rota: '/admin/eleicoes',
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
        { q: 'O meu voto pode ser associado a mim?', a: 'Não. O voto é secreto: o recibo prova a participação, mas o conteúdo do voto é separado da identidade.' },
      ],
    },
    {
      id: 'assembleias',
      titulo: 'Assembleias',
      resumo: 'Acompanhar as assembleias, marcar presença e seguir as deliberações ao vivo.',
      rota: '/admin/assembleias',
      passos: [
        'Abra "Assembleias" na barra lateral.',
        'Escolha a assembleia convocada para ver a ordem de trabalhos.',
        'Na sala ao vivo, marque a sua presença quando aberta.',
        'Vote as deliberações no momento em que são postas a votação.',
      ],
      dicas: [
        'A presença é registada para efeitos de quórum e de participação.',
      ],
    },
    {
      id: 'regulamentos',
      titulo: 'Regulamentos',
      resumo: 'Consultar os regulamentos em vigor e as suas versões.',
      rota: '/regulamentos',
      passos: [
        'Abra "Regulamentos" na barra lateral.',
        'Escolha um regulamento para ler.',
        'Consulte o histórico de versões quando disponível.',
      ],
    },
    {
      id: 'participacao',
      titulo: 'Participação: patrocínios, petições, propostas, esclarecimentos e reclamações',
      resumo: 'Os canais formais para a sua voz junto da Direção e da Assembleia.',
      rota: '/participacao/propostas',
      passos: [
        'Na barra lateral, secção "Participação", escolha o canal adequado.',
        'Propostas — submeter pontos para a ordem de trabalhos da Assembleia.',
        'Petições — subscrever ou criar petições de sócios.',
        'Esclarecimentos — pedir esclarecimentos à Direção.',
        'Reclamações — apresentar reclamações ou recursos.',
        'Patrocínios — registar/consultar apoios e patrocínios.',
        'Depois de submeter, acompanhe o estado na própria página do canal.',
      ],
      dicas: [
        'Seja específico: um pedido claro é respondido mais depressa.',
      ],
    },
  ],
};

export default governanca;
