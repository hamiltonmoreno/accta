import { Compass } from 'lucide-react';

// A. Primeiros passos — visível a todos os utilizadores autenticados.
// Onboarding: entrar, completar perfil, foto, estados da conta, navegação e
// glossário dos termos do portal.
export const primeirosPassos = {
  id: 'primeiros-passos',
  titulo: 'Primeiros passos',
  icon: Compass,
  resumo: 'Como entrar no portal, preparar a sua conta e orientar-se no sistema.',
  artigos: [
    {
      id: 'entrar',
      titulo: 'Entrar e recuperar a palavra-passe',
      resumo: 'Aceder ao portal com email e palavra-passe; repor a palavra-passe se a esquecer.',
      passos: [
        'Abra a página de entrada e introduza o seu email e palavra-passe.',
        'Carregue em "Entrar". A sessão fica ativa durante 24 horas.',
        'Esqueceu-se da palavra-passe? Use "Recuperar palavra-passe" na página de entrada e siga a hiperligação enviada para o seu email.',
        'Recebeu um convite para ativar a conta? Abra a hiperligação do email de convite e defina a sua palavra-passe (mínimo 6 caracteres).',
      ],
      dicas: [
        'A sessão é guardada num cookie seguro — não precisa de copiar nenhum token.',
        'Se vir "sessão expirada", basta voltar a entrar.',
        'O acesso é apenas com email e palavra-passe — não há código de verificação (2FA) a introduzir.',
      ],
      faq: [
        { q: 'Posso ter mais do que uma conta?', a: 'Não. Cada pessoa tem uma única conta para toda a vida de associado.' },
        { q: 'A hiperligação de recuperação não funciona — porquê?', a: 'As hiperligações de recuperação expiram por segurança. Peça uma nova em "Recuperar palavra-passe" e use a mais recente.' },
      ],
    },
    {
      id: 'completar-perfil',
      titulo: 'Completar o Meu Perfil e carregar a foto',
      resumo: 'Manter os seus dados atualizados e a foto de perfil aprovada.',
      rota: '/perfil',
      passos: [
        'Abra o menu do seu avatar (canto superior direito) e escolha "Meu Perfil".',
        'Reveja e atualize os seus dados de contacto.',
        'Para a foto, carregue uma imagem (até 2 MB). A foto fica pendente de aprovação por um moderador antes de ficar visível.',
        'Guarde as alterações.',
      ],
      dicas: [
        'Use uma foto de rosto, nítida e recente.',
        'Enquanto a foto não for aprovada, é mostrada uma inicial ou a foto anterior.',
        'Formatos aceites: PNG, JPG ou WebP, até 2 MB.',
      ],
      faq: [
        { q: 'Carreguei a foto mas não mudou — está partida?', a: 'Não. As fotos carecem de aprovação de um moderador; até lá continua a ver a inicial ou a foto anterior.' },
      ],
    },
    {
      id: 'estados-conta',
      titulo: 'Estados da sua conta',
      resumo: 'O que significa cada estado que aparece junto ao seu perfil.',
      passos: [
        'Ativo — conta plena: tem acesso às funcionalidades de sócio e pode votar (se for membro votante).',
        'Inativo — conta sem acesso pleno; contacte a Direção para regularizar.',
        'Pendente de convite — recebeu convite mas ainda não ativou a conta; use a hiperligação do email.',
        'Pendente de aprovação — o seu pedido de inscrição aguarda decisão da administração.',
        'Rejeitado — o pedido de inscrição não foi aceite; pode pedir esclarecimentos à Direção.',
      ],
      dicas: [
        'O estado aparece como etiqueta no menu do avatar quando não está "ativo".',
        'As quotas são descontadas na folha de pagamento — não existe estado de incumprimento de quotas.',
      ],
    },
    {
      id: 'orientar-se',
      titulo: 'Orientar-se: cabeçalho, sidebar e notificações',
      resumo: 'Reconhecer os elementos de navegação e onde chegam os avisos.',
      rota: '/notificacoes',
      passos: [
        'No cabeçalho encontra: o logótipo (volta ao Dashboard), o sino de notificações e o seu avatar.',
        'O sino mostra avisos em tempo real (votações, eventos, finanças, moderação…). Abra-o para ver e marcar como lidas.',
        'A barra lateral (sidebar) agrupa os módulos a que tem acesso; pode colapsá-la no botão do topo.',
        'O menu do avatar dá acesso a Meu Perfil, Ranking, Carteira, Ajuda e Sair.',
      ],
      dicas: [
        'As notificações chegam em tempo real; se a ligação cair, o portal verifica novidades a cada 30 segundos.',
        'Em telemóvel, a sidebar abre no botão de menu (☰) e alguns atalhos passam para o menu do avatar.',
        'A sidebar só mostra os módulos a que tem acesso — não estranhe que outra pessoa veja itens diferentes.',
      ],
      faq: [
        { q: 'Porque não vejo um módulo que um colega vê?', a: 'A navegação adapta-se ao seu papel e privilégios. Itens de administração ou finanças só aparecem a quem tem esse acesso.' },
      ],
    },
    {
      id: 'glossario',
      titulo: 'Glossário rápido',
      resumo: 'Os termos do portal e da vida associativa, explicados em poucas palavras.',
      faq: [
        { q: 'Sócio', a: 'Membro da associação com conta no portal. Uma pessoa = uma conta para toda a vida de associado.' },
        { q: 'Jóia', a: 'Valor de entrada pago uma vez na admissão como sócio.' },
        { q: 'Quota', a: 'Contribuição periódica do sócio, descontada na folha de pagamento.' },
        { q: 'Órgãos sociais', a: 'As estruturas eleitas: Assembleia Geral, Direção e Conselho Fiscal.' },
        { q: 'Cargo / Mandato', a: 'A função institucional de um membro num órgão (ex.: Tesoureiro) e o período em que a exerce.' },
        { q: 'Deliberação', a: 'Decisão tomada e votada em assembleia.' },
        { q: 'Voto secreto', a: 'Modo de votação (eleições) em que o sentido do voto fica separado da identidade de quem votou; recebe um recibo que prova a participação.' },
        { q: 'Quórum', a: 'Número mínimo de presenças exigido para uma assembleia poder deliberar.' },
        { q: 'Sanção', a: 'Medida disciplinar aplicada na sequência de um processo.' },
      ],
      passos: [
        'Não encontrou um termo? Use "Pedir esclarecimento à Direção" no fim desta página.',
      ],
    },
  ],
};

export default primeirosPassos;
