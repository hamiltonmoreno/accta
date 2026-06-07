import React from 'react';
import { Link } from 'react-router-dom';
import { Menu, Trophy } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { NotificationBell } from '../../components/NotificationBell';
import { BrandLogo } from '../../components/BrandLogo';
import { UserMenu } from './UserMenu';
import { isMemberAccount } from '../../lib/account';

/**
 * Cabeçalho fixo full-width. Esquerda: hambúrguer (mobile) + logo + título.
 * Direita: Notificações, Ranking (só desktop + membros), UserMenu.
 * `mobileMenuButtonRef` é encaminhado para o hambúrguer (o PrivateLayout
 * devolve-lhe o foco ao fechar o drawer — a11y).
 */
export const Header = ({ title, onOpenMobileMenu, onLogout, mobileMenuButtonRef }) => {
  const { user } = useAuth();
  const isSocio = user?.role === 'socio';
  const isMember = isMemberAccount(user);
  return (
    <header
      className="fixed top-0 inset-x-0 z-40 h-[var(--header-h)] flex items-center gap-3 px-4 backdrop-blur-md bg-[var(--surface-header)] border-b border-[var(--surface-border)]"
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

      <h1 className="font-semibold text-base text-grafite-auto truncate">{title}</h1>

      <div className="ml-auto flex items-center gap-2 sm:gap-3">
        <NotificationBell />
        {isMember && (
          <Link
            to="/ranking"
            className="hidden md:flex items-center justify-center h-10 w-10 rounded-lg text-secondary-auto hover:text-carmesim hover:bg-carmesim/10 transition-colors"
            aria-label="Ranking"
            data-testid="header-ranking"
          >
            <Trophy className="w-5 h-5" aria-hidden="true" />
          </Link>
        )}
        <div className="flex items-center pl-2 sm:pl-3 border-l border-[var(--surface-border)]">
          <UserMenu user={user} isSocio={isSocio} isMember={isMember} onLogout={onLogout} />
        </div>
      </div>
    </header>
  );
};

export default Header;
