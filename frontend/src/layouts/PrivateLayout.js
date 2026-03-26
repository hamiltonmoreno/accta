import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { NotificationBell } from '../components/NotificationBell';
import { ACCTALogoHorizontal } from '../components/ACCTALogo';
import {
  LayoutDashboard,
  CreditCard,
  Vote,
  FileText,
  MessageSquare,
  Gift,
  Users,
  LogOut,
  Menu,
  X,
  ClipboardList,
  Bell,
  Calendar,
  ChevronRight,
  DollarSign,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const PrivateLayout = ({ children }) => {
  const { user, logout, isAdmin, isFinanceiro, isModerador } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const pathname = location.pathname;

  const currentPageTitle = (() => {
    if (pathname === '/dashboard') return 'Dashboard';
    if (pathname === '/carteira') return 'Carteira Digital';
    if (pathname === '/financeiro') return 'Financeiro';
    if (pathname === '/votacoes') return 'Votacoes';
    if (pathname === '/eventos') return 'Eventos';
    if (pathname === '/documentos') return 'Documentos';
    if (pathname === '/mural') return 'Mural';
    if (pathname === '/beneficios') return 'Beneficios';
    if (pathname === '/notificacoes') return 'Notificacoes';
    if (pathname === '/admin/usuarios') return 'Usuarios';
    if (pathname === '/admin/logs') return 'Audit Logs';
    return 'Portal';
  })();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const menuItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, roles: ['all'] },
    { label: 'Carteira Digital', path: '/carteira', icon: CreditCard, roles: ['socio'] },
    { label: 'Financeiro', path: '/financeiro', icon: DollarSign, roles: ['all'] },
    { label: 'Votacoes', path: '/votacoes', icon: Vote, roles: ['all'] },
    { label: 'Eventos', path: '/eventos', icon: Calendar, roles: ['all'] },
    { label: 'Documentos', path: '/documentos', icon: FileText, roles: ['all'] },
    { label: 'Mural', path: '/mural', icon: MessageSquare, roles: ['all'] },
    { label: 'Beneficios', path: '/beneficios', icon: Gift, roles: ['all'] },
    { label: 'Notificacoes', path: '/notificacoes', icon: Bell, roles: ['all'] },
    { label: 'Gestao de Usuarios', path: '/admin/usuarios', icon: Users, roles: ['admin'] },
    { label: 'Audit Logs', path: '/admin/logs', icon: ClipboardList, roles: ['admin'] },
  ];

  const filteredMenuItems = menuItems.filter((item) => {
    if (item.roles.includes('all')) return true;
    if (item.roles.includes('admin') && isAdmin) return true;
    if (item.roles.includes('financeiro') && (isFinanceiro || isAdmin)) return true;
    if (item.roles.includes('moderador') && (isModerador || isAdmin)) return true;
    if (item.roles.includes('socio') && user?.role === 'socio') return true;
    return false;
  });

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div className="p-5 border-b border-white/10">
        <ACCTALogoHorizontal dark />
      </div>

      {/* User Info */}
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-carmesim rounded-full flex items-center justify-center font-bold text-white text-sm flex-shrink-0">
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-white text-sm truncate">{user?.name}</div>
            <div className="text-[10px] text-carmesim uppercase tracking-wider font-semibold">{user?.role}</div>
          </div>
          <NotificationBell />
        </div>
        {user?.status !== 'ativo' && (
          <div className="mt-2 px-2 py-1 bg-carmesim/20 border border-carmesim rounded text-[10px] text-carmesim-light uppercase tracking-wider font-semibold text-center">
            {user?.status}
          </div>
        )}
      </div>

      {/* Menu */}
      <nav className="flex-1 p-3 overflow-y-auto">
        <ul className="space-y-0.5">
          {filteredMenuItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path;
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group touch-target ${
                    isActive
                      ? 'bg-carmesim text-white font-semibold'
                      : 'text-white/70 hover:bg-white/10 hover:text-white'
                  }`}
                  data-testid={`sidebar-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  <Icon className={`w-[18px] h-[18px] flex-shrink-0 ${isActive ? 'text-white' : 'text-white/50 group-hover:text-white'}`} />
                  <span className="text-sm truncate">{item.label}</span>
                  {isActive && <ChevronRight className="w-4 h-4 ml-auto opacity-60" />}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Logout */}
      <div className="p-3 border-t border-white/10">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/60 hover:bg-carmesim/80 hover:text-white transition-colors touch-target"
          data-testid="logout-button"
        >
          <LogOut className="w-[18px] h-[18px]" />
          <span className="text-sm">Sair</span>
        </button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex md:flex-col md:w-[260px] bg-grafite fixed h-screen z-30">
        <SidebarContent />
      </aside>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-40 md:hidden"
              onClick={() => setSidebarOpen(false)}
            />
            <motion.aside
              initial={{ x: -260 }}
              animate={{ x: 0 }}
              exit={{ x: -260 }}
              transition={{ type: 'tween', duration: 0.25 }}
              className="fixed left-0 top-0 bottom-0 w-[260px] bg-grafite z-50 md:hidden flex flex-col"
            >
              {/* Close button */}
              <button
                onClick={() => setSidebarOpen(false)}
                className="absolute top-3 right-3 p-2 text-white/60 hover:text-white rounded-lg z-10"
              >
                <X className="w-5 h-5" />
              </button>
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 md:ml-[260px] min-w-0">
        {/* Mobile Header */}
        <header className="md:hidden sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 -ml-2 rounded-lg hover:bg-gray-100 transition-colors touch-target"
                data-testid="mobile-sidebar-button"
              >
                <Menu className="w-5 h-5 text-grafite" />
              </button>
              <div>
                <span className="font-bold text-sm text-grafite">{currentPageTitle}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <NotificationBell />
              <div className="w-8 h-8 bg-carmesim rounded-full flex items-center justify-center text-white text-xs font-bold">
                {user?.name?.charAt(0).toUpperCase()}
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 sm:p-6 md:p-8 animate-fadeIn">
          {children}
        </main>
      </div>
    </div>
  );
};
