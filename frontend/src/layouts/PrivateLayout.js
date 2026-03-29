import React, { useState, useEffect, useCallback } from 'react';
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
  DollarSign,
  Lock,
  Unlock,
  Search,
  UserCircle,
  FolderKanban,
  Camera,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

/* ========== GROUPED MENU SECTIONS ========== */
const menuSections = [
  {
    title: 'Painel',
    items: [
      { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, roles: ['all'] },
      { label: 'Meu Perfil', path: '/perfil', icon: UserCircle, roles: ['all'] },
      { label: 'Carteira Digital', path: '/carteira', icon: CreditCard, roles: ['socio'] },
    ],
  },
  {
    title: 'Gestão',
    items: [
      { label: 'Financeiro', path: '/financeiro', icon: DollarSign, roles: ['admin', 'financeiro'] },
      { label: 'Projetos', path: '/projetos', icon: FolderKanban, roles: ['all'] },
      { label: 'Votações', path: '/votacoes', icon: Vote, roles: ['all'] },
      { label: 'Eventos', path: '/eventos', icon: Calendar, roles: ['all'] },
      { label: 'Documentos', path: '/documentos', icon: FileText, roles: ['all'] },
    ],
  },
  {
    title: 'Comunidade',
    items: [
      { label: 'Mural', path: '/mural', icon: MessageSquare, roles: ['all'] },
      { label: 'Galeria', path: '/galeria-admin', icon: Camera, roles: ['all'] },
      { label: 'Benefícios', path: '/beneficios', icon: Gift, roles: ['all'] },
    ],
  },
  {
    title: 'Sistema',
    items: [
      { label: 'Notificações', path: '/notificacoes', icon: Bell, roles: ['all'] },
      { label: 'Utilizadores', path: '/admin/usuarios', icon: Users, roles: ['admin'] },
      { label: 'Audit Logs', path: '/admin/logs', icon: ClipboardList, roles: ['admin'] },
    ],
  },
];

export const PrivateLayout = ({ children }) => {
  const { user, logout, isAdmin, isFinanceiro, isModerador } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const pathname = location.pathname;

  const [collapsed, setCollapsed] = useState(false);
  const [locked, setLocked] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);

  const SIDEBAR_W = 270;
  const SIDEBAR_COLLAPSED_W = 72;

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 768px)');
    const handler = (e) => setIsDesktop(e.matches);
    setIsDesktop(mq.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const currentPageTitle = (() => {
    if (pathname === '/dashboard') return 'Dashboard';
    if (pathname === '/perfil') return 'Meu Perfil';
    if (pathname === '/carteira') return 'Carteira Digital';
    if (pathname === '/financeiro') return 'Financeiro';
    if (pathname === '/projetos') return 'Projetos';
    if (pathname.startsWith('/projetos/')) return 'Detalhe do Projeto';
    if (pathname === '/votacoes') return 'Votações';
    if (pathname === '/eventos') return 'Eventos';
    if (pathname === '/documentos') return 'Documentos';
    if (pathname === '/mural') return 'Mural';
    if (pathname === '/beneficios') return 'Benefícios';
    if (pathname === '/notificacoes') return 'Notificações';
    if (pathname === '/admin/usuarios') return 'Utilizadores';
    if (pathname === '/admin/logs') return 'Audit Logs';
    return 'Portal';
  })();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  /* ========== LOCK / HOVER LOGIC ========== */
  const toggleLock = useCallback(() => {
    setLocked((prev) => {
      if (prev) {
        // Unlocking → enable hover collapse
        setCollapsed(true);
        return false;
      } else {
        // Locking → keep open
        setCollapsed(false);
        return true;
      }
    });
  }, []);

  const handleMouseEnter = useCallback(() => {
    if (!locked) setCollapsed(false);
  }, [locked]);

  const handleMouseLeave = useCallback(() => {
    if (!locked) setCollapsed(true);
  }, [locked]);

  /* Filter menu items by role */
  const filterItem = (item) => {
    if (item.roles.includes('all')) return true;
    if (item.roles.includes('admin') && isAdmin) return true;
    if (item.roles.includes('financeiro') && (isFinanceiro || isAdmin)) return true;
    if (item.roles.includes('moderador') && (isModerador || isAdmin)) return true;
    if (item.roles.includes('socio') && user?.role === 'socio') return true;
    return false;
  };

  const sidebarWidth = collapsed ? SIDEBAR_COLLAPSED_W : SIDEBAR_W;

  /* ========== SIDEBAR CONTENT (shared desktop/mobile) ========== */
  const SidebarInner = ({ isMobile = false }) => (
    <div className="flex flex-col h-full">
      {/* ---- Logo row ---- */}
      <div className="flex items-center gap-2 px-3 py-4 min-h-[64px]" style={{ borderBottom: '1px solid var(--surface-border)' }}>
        <span className="flex items-center justify-center min-w-[48px]">
          <div className="w-9 h-9 bg-carmesim rounded-lg flex items-center justify-center">
            <span className="text-white font-extrabold text-sm tracking-tight">AC</span>
          </div>
        </span>
        <span
          className={`font-bold text-[15px] whitespace-nowrap transition-opacity duration-300 ${
            collapsed && !isMobile ? 'opacity-0 pointer-events-none w-0' : 'opacity-100'
          }`}
          style={{ color: 'var(--text-primary)' }}
        >
          ACCTA
        </span>

        {/* Lock/Close buttons — only on desktop */}
        {!isMobile && (
          <button
            onClick={toggleLock}
            className="ml-auto p-1.5 rounded-md text-gray-400 hover:text-carmesim hover:bg-carmesim/10 transition-colors"
            title={locked ? 'Desbloquear (hover)' : 'Bloquear sidebar'}
            data-testid="sidebar-lock-btn"
          >
            {locked ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
          </button>
        )}
        {isMobile && (
          <button
            onClick={() => setMobileOpen(false)}
            className="ml-auto p-1.5 rounded-md text-gray-400 hover:text-carmesim transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* ---- Menu sections ---- */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden px-2 py-3 sidebar-scroll">
        {menuSections.map((section) => {
          const visibleItems = section.items.filter(filterItem);
          if (visibleItems.length === 0) return null;
          return (
            <div key={section.title} className="mb-2">
              {/* Section title */}
              <div className="flex items-center h-9 px-1 mb-0.5">
                <span
                  className={`text-[10px] uppercase tracking-[0.12em] font-semibold whitespace-nowrap transition-opacity duration-300 ${
                    collapsed && !isMobile ? 'opacity-0 w-0' : 'opacity-100 ml-2'
                  }`}
                  style={{ color: 'var(--text-muted)' }}
                >
                  {section.title}
                </span>
                {collapsed && !isMobile && (
                  <span className="mx-auto h-[3px] w-5 rounded-full bg-gray-200" />
                )}
              </div>

              {/* Items */}
              <ul className="space-y-0.5">
                {visibleItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.path;
                  return (
                    <li key={item.path}>
                      <Link
                        to={item.path}
                        onClick={() => isMobile && setMobileOpen(false)}
                        className={`flex items-center rounded-lg transition-all duration-200 group relative ${
                          isActive
                            ? 'bg-carmesim text-white shadow-sm'
                            : 'hover:bg-carmesim hover:text-white'
                        }`}
                        style={!isActive ? { color: 'var(--text-secondary)' } : undefined}
                        data-testid={`sidebar-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                        title={collapsed && !isMobile ? item.label : undefined}
                      >
                        <span className="flex items-center justify-center min-w-[48px] h-[44px]">
                          <Icon
                            className={`w-[20px] h-[20px] transition-colors ${
                              isActive ? 'text-white' : 'group-hover:text-white'
                            }`}
                            style={!isActive ? { color: 'var(--text-muted)' } : undefined}
                          />
                        </span>
                        <span
                          className={`text-[13px] whitespace-nowrap transition-opacity duration-300 ${
                            collapsed && !isMobile ? 'opacity-0 pointer-events-none w-0' : 'opacity-100'
                          }`}
                        >
                          {item.label}
                        </span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </nav>

      {/* ---- Profile & Logout ---- */}
      <div className="px-2 py-3" style={{ borderTop: '1px solid var(--surface-border)' }}>
        {/* User profile */}
        <div className="flex items-center gap-3 px-1 mb-2">
          <div className="w-9 h-9 bg-carmesim rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <div
            className={`min-w-0 flex-1 transition-opacity duration-300 ${
              collapsed && !isMobile ? 'opacity-0 pointer-events-none w-0' : 'opacity-100'
            }`}
          >
            <div className="text-[13px] font-semibold truncate" style={{ color: 'var(--text-primary)' }}>{user?.name}</div>
            <div className="text-[11px] truncate" style={{ color: 'var(--text-muted)' }}>{user?.email}</div>
          </div>
        </div>

        {/* Status badge */}
        {user?.status !== 'ativo' && !collapsed && (
          <div className="mx-1 mb-2 px-2 py-1 bg-carmesim/10 border border-carmesim/30 rounded-md text-[10px] text-carmesim uppercase tracking-wider font-semibold text-center">
            {user?.status}
          </div>
        )}

        {/* Logout button */}
        <button
          onClick={handleLogout}
          className="w-full flex items-center rounded-lg transition-colors"
          style={{ color: 'var(--text-secondary)' }}
          data-testid="logout-button"
        >
          <span className="flex items-center justify-center min-w-[48px] h-[40px]">
            <LogOut className="w-[18px] h-[18px]" />
          </span>
          <span
            className={`text-[13px] whitespace-nowrap transition-opacity duration-300 ${
              collapsed && !isMobile ? 'opacity-0 pointer-events-none w-0' : 'opacity-100'
            }`}
          >
            Sair
          </span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: 'var(--surface-bg)' }}>
      {/* ======= Desktop Sidebar ======= */}
      <aside
        className="hidden md:flex md:flex-col fixed h-screen z-30 transition-all duration-300 ease-in-out"
        style={{ width: sidebarWidth, backgroundColor: 'var(--surface-sidebar)', boxShadow: '0 0 6px rgba(0,0,0,0.06)' }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        data-testid="desktop-sidebar"
      >
        <SidebarInner />
      </aside>

      {/* ======= Mobile Sidebar Overlay ======= */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 z-40 md:hidden backdrop-blur-sm"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: -SIDEBAR_W }}
              animate={{ x: 0 }}
              exit={{ x: -SIDEBAR_W }}
              transition={{ type: 'tween', duration: 0.28 }}
              className="fixed left-0 top-0 bottom-0 z-50 md:hidden flex flex-col shadow-xl"
              style={{ width: SIDEBAR_W, backgroundColor: 'var(--surface-sidebar)' }}
            >
              <SidebarInner isMobile />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ======= Main Content ======= */}
      <div className="flex-1 min-w-0">
        {/* Mobile Header */}
        <header className="md:hidden sticky top-0 z-30 backdrop-blur-md px-4 py-3" style={{ backgroundColor: 'var(--surface-header)', borderBottom: '1px solid var(--surface-border)' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setMobileOpen(true)}
                className="p-2 -ml-2 rounded-lg transition-colors touch-target"
                style={{ color: 'var(--text-primary)' }}
                data-testid="mobile-sidebar-button"
              >
                <Menu className="w-5 h-5" />
              </button>
              <span className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>{currentPageTitle}</span>
            </div>
            <div className="flex items-center gap-2">
              <NotificationBell />
              <div className="w-8 h-8 bg-carmesim rounded-full flex items-center justify-center text-white text-xs font-bold">
                {user?.name?.charAt(0).toUpperCase()}
              </div>
            </div>
          </div>
        </header>

        {/* Desktop Top Bar */}
        <header
          className="hidden md:block sticky top-0 z-20 backdrop-blur-md py-3 transition-all duration-300"
          style={{ paddingLeft: isDesktop ? `calc(${sidebarWidth}px + 1.5rem)` : undefined, paddingRight: '1.5rem', backgroundColor: 'var(--surface-header)', borderBottom: '1px solid var(--surface-border)' }}
        >
          <div className="flex items-center justify-between">
            <h1 className="font-semibold text-base" style={{ color: 'var(--text-primary)' }}>{currentPageTitle}</h1>
            <div className="flex items-center gap-3">
              <NotificationBell />
              <div className="flex items-center gap-2 pl-3" style={{ borderLeft: '1px solid var(--surface-border)' }}>
                <div className="w-8 h-8 bg-carmesim rounded-full flex items-center justify-center text-white text-xs font-bold">
                  {user?.name?.charAt(0).toUpperCase()}
                </div>
                <span className="text-sm font-medium hidden lg:block" style={{ color: 'var(--text-primary)' }}>{user?.name}</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main
          className="p-4 sm:p-6 animate-fadeIn transition-all duration-300"
          style={{ paddingLeft: isDesktop ? `calc(${sidebarWidth}px + 1.5rem)` : undefined }}
        >
          {children}
        </main>
      </div>
    </div>
  );
};
