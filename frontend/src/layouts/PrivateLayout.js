import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { NotificationBell } from '../components/NotificationBell';
import {
  Plane,
  LayoutDashboard,
  CreditCard,
  Vote,
  FileText,
  MessageSquare,
  Gift,
  Users,
  Settings,
  LogOut,
  Menu,
  X,
  ShieldCheck,
  ClipboardList,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const PrivateLayout = ({ children }) => {
  const { user, logout, isAdmin, isFinanceiro, isModerador } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const menuItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, roles: ['all'] },
    { label: 'Carteira Digital', path: '/carteira', icon: CreditCard, roles: ['socio'] },
    { label: 'Financeiro', path: '/financeiro', icon: CreditCard, roles: ['all'] },
    { label: 'Votações', path: '/votacoes', icon: Vote, roles: ['all'] },
    { label: 'Documentos', path: '/documentos', icon: FileText, roles: ['all'] },
    { label: 'Mural', path: '/mural', icon: MessageSquare, roles: ['all'] },
    { label: 'Benefícios', path: '/beneficios', icon: Gift, roles: ['all'] },
    { label: 'Gestão de Usuários', path: '/admin/usuarios', icon: Users, roles: ['admin'] },
    { label: 'Audit Logs', path: '/admin/logs', icon: ClipboardList, roles: ['admin'] },
  ];

  const filteredMenuItems = menuItems.filter((item) => {
    if (item.roles.includes('all')) return true;
    if (item.roles.includes('admin') && isAdmin) return true;
    if (item.roles.includes('financeiro') && (isFinanceiro || isAdmin)) return true;
    if (item.roles.includes('moderador') && (isModerador || isAdmin)) return true;
    return false;
  });

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-accent rounded-lg flex items-center justify-center">
            <Plane className="w-5 h-5 text-primary" />
          </div>
          <div>
            <div className="font-outfit font-bold text-lg text-white">ACCTA</div>
            <div className="font-mono text-xs text-accent uppercase tracking-wider">Portal</div>
          </div>
        </div>
      </div>

      {/* User Info */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-accent rounded-full flex items-center justify-center font-outfit font-bold text-primary">
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-manrope font-semibold text-white truncate">{user?.name}</div>
            <div className="font-mono text-xs text-accent uppercase tracking-wider">{user?.role}</div>
          </div>
        </div>
        {user?.status !== 'ativo' && (
          <div className="mt-3 px-3 py-1 bg-alert/20 border border-alert rounded text-xs text-white font-mono uppercase">
            {user?.status}
          </div>
        )}
      </div>

      {/* Menu */}
      <nav className="flex-1 p-4 overflow-y-auto">
        <ul className="space-y-2">
          {filteredMenuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all group ${
                    isActive
                      ? 'bg-accent text-primary font-semibold'
                      : 'text-white/80 hover:bg-white/10 hover:text-white'
                  }`}
                  data-testid={`sidebar-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  <Icon className={`w-5 h-5 ${isActive ? 'text-primary' : 'text-white/60 group-hover:text-white'}`} />
                  <span className="text-sm">{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-white/10">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-white/80 hover:bg-white/10 hover:text-white transition-all"
          data-testid="logout-button"
        >
          <LogOut className="w-5 h-5" />
          <span className="text-sm">Sair</span>
        </button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen flex">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex md:flex-col md:w-[280px] bg-primary fixed h-screen">
        <SidebarContent />
      </aside>

      {/* Mobile Sidebar */}
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
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              className="fixed left-0 top-0 bottom-0 w-[280px] bg-primary z-50 md:hidden flex flex-col"
            >
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 md:ml-[280px]">
        {/* Mobile Header */}
        <header className="md:hidden sticky top-0 z-30 bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
            data-testid="mobile-sidebar-button"
          >
            <Menu className="w-6 h-6" />
          </button>
          <div className="font-outfit font-bold text-lg text-primary">ACCTA</div>
          <div className="w-10" />
        </header>

        {/* Page Content */}
        <main className="p-6 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
};
