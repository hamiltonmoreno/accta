import React from 'react';
import { Link } from 'react-router-dom';
import { Menu, MessageSquare, Trophy, UserCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { NotificationBell } from '../../components/NotificationBell';
import { BrandLogo } from '../../components/BrandLogo';
import { UserMenu } from './UserMenu';
import { isMemberAccount } from '../../lib/account';

// Botão de ícone padrão do cabeçalho (desktop). Mesma forma/tamanho/cor para
// todos os atalhos — neutro, hover Carmesim (frontend-design).
const ICON_BTN =
  'hidden md:flex items-center justify-center h-10 w-10 rounded-lg text-secondary-auto hover:text-carmesim hover:bg-carmesim/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-carmesim/40 focus-visible:ring-offset-2';

/**
 * Cabeçalho fixo full-width. Esquerda: hambúrguer (mobile) + logo (SEM título —
 * o corpo da página já o mostra). Direita: atalhos de ícone (Mural, Ranking,
 * Notificações, Meu Perfil) + dropdown do avatar. Mural/Ranking só p/
 * membros+admins; em mobile os atalhos dobram para dentro do dropdown.
 * `mobileMenuButtonRef` é encaminhado p/ o hambúrguer (a11y: foco devolvido ao
 * fechar o drawer).
 */
export const Header = ({ onOpenMobileMenu, onLogout, mobileMenuButtonRef }) => {
  const { user, isAdmin } = useAuth();
  const isSocio = user?.role === 'socio';
  const isMember = isMemberAccount(user);
  const showQuick = isMember || isAdmin; // Mural + Ranking
  return (
    <header
      className="fixed top-0 inset-x-0 z-40 h-[var(--header-h)] flex items-center gap-2 px-4 backdrop-blur-md bg-[var(--surface-header)] border-b border-[var(--surface-border)]"
      data-testid="app-header"
    >
      <button
        ref={mobileMenuButtonRef}
        onClick={onOpenMobileMenu}
        className="md:hidden p-2 -ml-1 rounded-lg transition-colors touch-target text-grafite-auto"
        aria-label="Abrir menu"
        data-testid="mobile-sidebar-button"
      >
        <Menu className="w-5 h-5" aria-hidden="true" />
      </button>

      <Link to="/dashboard" aria-label="Início" className="flex items-center shrink-0">
        <BrandLogo className="h-9" />
      </Link>

      <div className="ml-auto flex items-center gap-1 sm:gap-2">
        {showQuick && (
          <Link to="/mural" className={ICON_BTN} aria-label="Mural" data-testid="header-mural">
            <MessageSquare className="w-5 h-5" aria-hidden="true" />
          </Link>
        )}
        {showQuick && (
          <Link to="/ranking" className={ICON_BTN} aria-label="Ranking" data-testid="header-ranking">
            <Trophy className="w-5 h-5" aria-hidden="true" />
          </Link>
        )}
        <NotificationBell />
        <Link to="/perfil" className={ICON_BTN} aria-label="Meu Perfil" data-testid="header-perfil">
          <UserCircle className="w-5 h-5" aria-hidden="true" />
        </Link>
        <div className="flex items-center pl-2 sm:pl-3 ml-1 border-l border-[var(--surface-border)]">
          <UserMenu user={user} isSocio={isSocio} isMember={isMember} isAdmin={isAdmin} onLogout={onLogout} />
        </div>
      </div>
    </header>
  );
};

export default Header;
