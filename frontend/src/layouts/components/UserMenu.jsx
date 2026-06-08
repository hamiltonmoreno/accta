// frontend/src/layouts/components/UserMenu.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { UserCircle, CreditCard, Trophy, MessageSquare, LogOut } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '../../components/ui/dropdown-menu';
import { UserAvatar } from '../../components/UserAvatar';
import { USER_STATUS_CONFIG, USER_STATUS_FALLBACK, getStatusConfig } from '../../lib/statusConfig';

/**
 * Dropdown do avatar no cabeçalho. No DESKTOP, Meu Perfil/Mural/Ranking são
 * ícones no cabeçalho, por isso aqui ficam `md:hidden` (só aparecem no dropdown
 * em mobile). A Carteira Digital fica sempre dentro do dropdown ("dentro do
 * perfil"). Visibilidade: isSocio (Carteira), isMember||isAdmin (Mural/Ranking).
 */
export const UserMenu = ({ user, isSocio, isMember, isAdmin, onLogout }) => {
  const showQuick = isMember || isAdmin;
  const sc =
    user?.status && user.status !== 'ativo'
      ? getStatusConfig(USER_STATUS_CONFIG, user.status, USER_STATUS_FALLBACK)
      : null;
  const StatusIcon = sc?.icon;
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="flex items-center rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-carmesim/40 focus-visible:ring-offset-2"
        aria-label="Menu do utilizador"
        data-testid="user-menu-trigger"
      >
        <UserAvatar size="xs" name={user?.name} photoUrl={user?.photo_url} />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="flex flex-col">
          <span className="text-sm font-semibold truncate text-grafite-auto">{user?.name}</span>
          <span className="text-xs font-normal truncate text-muted-auto">{user?.email}</span>
        </DropdownMenuLabel>
        {sc && (
          <div
            data-testid="menu-status"
            className={`mx-1 my-1 px-2 py-1 rounded-md text-xs uppercase tracking-wider font-semibold text-center flex items-center justify-center gap-1 ${sc.className}`}
          >
            {StatusIcon && <StatusIcon className="h-3 w-3" />}
            {sc.label}
          </div>
        )}
        <DropdownMenuSeparator />
        {/* Meu Perfil / Mural / Ranking: no desktop vivem no cabeçalho (md:hidden aqui). */}
        <DropdownMenuItem asChild className="md:hidden">
          <Link to="/perfil" data-testid="menu-perfil">
            <UserCircle className="w-4 h-4 mr-2" aria-hidden="true" />
            Meu Perfil
          </Link>
        </DropdownMenuItem>
        {showQuick && (
          <DropdownMenuItem asChild className="md:hidden">
            <Link to="/mural" data-testid="menu-mural">
              <MessageSquare className="w-4 h-4 mr-2" aria-hidden="true" />
              Mural
            </Link>
          </DropdownMenuItem>
        )}
        {showQuick && (
          <DropdownMenuItem asChild className="md:hidden">
            <Link to="/ranking" data-testid="menu-ranking">
              <Trophy className="w-4 h-4 mr-2" aria-hidden="true" />
              Ranking
            </Link>
          </DropdownMenuItem>
        )}
        {isSocio && (
          <DropdownMenuItem asChild>
            <Link to="/carteira" data-testid="menu-carteira">
              <CreditCard className="w-4 h-4 mr-2" aria-hidden="true" />
              Carteira Digital
            </Link>
          </DropdownMenuItem>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={onLogout}
          data-testid="menu-sair"
          className="text-carmesim focus:text-carmesim focus:bg-carmesim/10"
        >
          <LogOut className="w-4 h-4 mr-2" aria-hidden="true" />
          Sair
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default UserMenu;
