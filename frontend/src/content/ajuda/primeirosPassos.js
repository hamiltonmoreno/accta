import { Compass } from 'lucide-react';

// A. Primeiros passos — visível a todos os utilizadores autenticados.
// Onboarding: entrar, completar perfil, foto, notificações, navegação.
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
      ],
      faq: [
        { q: 'Posso ter mais do que uma conta?', a: 'Não. Cada pessoa tem uma única conta para toda a vida de associado.' },
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
      ],
    },
  ],
};

export default primeirosPassos;
