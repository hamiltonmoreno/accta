import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { registrationAPI } from '../utils/api';
import { queryKeys } from '../lib/queryClient';
import { NotificationBell } from '../components/NotificationBell';
import { BrandLogo } from '../components/BrandLogo';
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
  ChevronsLeft,
  ChevronsRight,
  UserCircle,
  FolderKanban,
  Camera,
  UserPlus,
  Award,
  Landmark,
  ListChecks,
  Gavel,
  Palette,
  Newspaper,
  Handshake,
  FileSignature,
  HelpCircle,
  ShieldAlert,
  Lightbulb,
} from 'lucide-react';

const SIDEBAR_STORAGE_KEY = 'accta:sidebar-expanded';

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
      { label: 'Financeiro', path: '/financeiro', icon: DollarSign, roles: ['admin', 'financeiro'], privileges: ['view_finances_readonly', 'manage_finances'] },
      { label: 'Projetos', path: '/projetos', icon: FolderKanban, roles: ['all'] },
      { label: 'Votações', path: '/votacoes', icon: Vote, roles: ['all'] },
      { label: 'Eventos', path: '/eventos', icon: Calendar, roles: ['all'] },
      { label: 'Documentos', path: '/documentos', icon: FileText, roles: ['all'] },
    ],
  },
  {
    title: 'Órgãos Sociais',
    items: [
      { label: 'Assembleias', path: '/admin/assembleias', icon: Landmark, roles: ['all'] },
      { label: 'Eleições', path: '/admin/eleicoes', icon: ListChecks, roles: ['all'] },
      { label: 'Disciplina', path: '/admin/disciplinar', icon: Gavel, roles: ['admin'], match: 'direcao' },
    ],
  },
  {
    title: 'Participação',
    items: [
      { label: 'Patrocínios', path: '/participacao/patrocinios', icon: Handshake, roles: ['all'] },
      { label: 'Petições', path: '/participacao/peticoes', icon: FileSignature, roles: ['all'] },
      { label: 'Propostas', path: '/participacao/propostas', icon: Lightbulb, roles: ['all'] },
      { label: 'Esclarecimentos', path: '/participacao/esclarecimentos', icon: HelpCircle, roles: ['all'] },
      { label: 'Reclamações', path: '/participacao/reclamacoes', icon: ShieldAlert, roles: ['all'] },
    ],
  },
  {
    title: 'Comunidade',
    items: [
      { label: 'Mural', path: '/mural', icon: MessageSquare, roles: ['all'] },
      { label: 'Galeria', path: '/galeria-admin', icon: Camera, roles: ['all'] },
      { label: 'Notícias', path: '/admin/noticias', icon: Newspaper, roles: ['admin', 'moderador'] },
      { label: 'Aparência', path: '/admin/aparencia', icon: Palette, roles: ['admin', 'moderador'] },
      { label: 'Benefícios', path: '/beneficios', icon: Gift, roles: ['all'] },
    ],
  },
  {
    title: 'Sistema',
    items: [
      { label: 'Notificações', path: '/notificacoes', icon: Bell, roles: ['all'] },
      { label: 'Pedidos de Inscrição', path: '/admin/pedidos-inscricao', icon: UserPlus, roles: ['admin'], badge: 'registration' },
      { label: 'Utilizadores', path: '/admin/usuarios', icon: Users, roles: ['admin'], privileges: ['manage_users'] },
      { label: 'Cargos & Mandatos', path: '/admin/cargos', icon: Award, roles: ['admin'], privileges: ['manage_users'] },
      { label: 'Audit Logs', path: '/admin/logs', icon: ClipboardList, roles: ['admin'], privileges: ['view_audit_logs'] },
    ],
  },
];

export const PrivateLayout = ({ children }) => {
  const { user, logout, isAdmin, isFinanceiro, isModerador, isDirecao } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const pathname = location.pathname;

  // Badge de pedidos de inscrição pendentes (só admin). staleTime moderado —
  // o número muda devagar; é apenas um indicador no menu.
  const { data: pendingRegistrations = [] } = useQuery({
    queryKey: queryKeys.registration.requests('pendente_aprovacao'),
    queryFn: async () => (await registrationAPI.listPending({ status: 'pendente_aprovacao' })).data,
    enabled: !!isAdmin,
    staleTime: 60 * 1000,
  });
  const registrationBadgeCount = Array.isArray(pendingRegistrations) ? pendingRegistrations.length : 0;

  const [expanded, setExpanded] = useState(() => {
    if (typeof window === 'undefined') return true;
    const stored = window.localStorage.getItem(SIDEBAR_STORAGE_KEY);
    return stored === null ? true : stored === 'true';
  });
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);

  const SIDEBAR_W = 270;
  const SIDEBAR_COLLAPSED_W = 72;
  const collapsed = !expanded;

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(expanded));
    }
  }, [expanded]);

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
    if (pathname === '/galeria-admin') return 'Galeria';
    if (pathname === '/beneficios') return 'Benefícios';
    if (pathname === '/notificacoes') return 'Notificações';
    if (pathname === '/admin/pedidos-inscricao') return 'Pedidos de Inscrição';
    if (pathname === '/admin/cargos') return 'Cargos & Mandatos';
    if (pathname === '/admin/assembleias') return 'Assembleias';
    if (pathname.startsWith('/admin/assembleias/')) return 'Assembleia';
    if (pathname === '/admin/eleicoes') return 'Eleições';
    if (pathname.startsWith('/admin/eleicoes/')) return 'Eleição';
    if (pathname === '/admin/disciplinar') return 'Disciplina';
    if (pathname === '/admin/aparencia') return 'Aparência do Site';
    if (pathname === '/admin/noticias') return 'Notícias / Blog';
    if (pathname === '/participacao/patrocinios') return 'Patrocínios';
    if (pathname === '/participacao/peticoes') return 'Petições';
    if (pathname === '/participacao/propostas') return 'Propostas para a ordem de trabalhos';
    if (pathname === '/participacao/esclarecimentos') return 'Pedidos de esclarecimento';
    if (pathname === '/participacao/reclamacoes') return 'Reclamações e recursos';
    if (pathname === '/admin/usuarios') return 'Utilizadores';
    if (pathname === '/admin/logs') return 'Audit Logs';
    return 'Portal';
  })();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  /* ========== TOGGLE LOGIC ========== */
  const toggleSidebar = useCallback(() => {
    setExpanded((prev) => !prev);
  }, []);

  /* Filter menu items by role (ou por privilégio granular — RBAC aditivo) */
  const filterItem = (item) => {
    // Gating por cargo/órgão (extensão ao RBAC por role/privilégio).
    if (item.match === 'direcao' && (isAdmin || isDirecao)) return true;
    if (item.roles.includes('all')) return true;
    if (item.roles.includes('admin') && isAdmin) return true;
    if (item.roles.includes('financeiro') && (isFinanceiro || isAdmin)) return true;
    if (item.roles.includes('moderador') && (isModerador || isAdmin)) return true;
    if (item.roles.includes('socio') && user?.role === 'socio') return true;
    // Privilégios concedem acesso EXTRA à entrada (ex.: Conselho Fiscal vê Financeiro).
    if (item.privileges?.some((p) => (user?.privileges || []).includes(p))) return true;
    return false;
  };

  const sidebarWidth = collapsed ? SIDEBAR_COLLAPSED_W : SIDEBAR_W;

  /* ========== SIDEBAR CONTENT (shared desktop/mobile) ========== */
  const sidebarInner = ({ isMobile = false }) => (
    <div className="flex flex-col h-full">
      {/* ---- Logo row ---- */}
      <div className="flex items-center gap-2 px-3 py-4 min-h-[64px]" style={{ borderBottom: '1px solid var(--surface-border)' }}>
        {/* Recolhida: mark compacto "AC". Expandida: marca gerida (BrandLogo /
            SVG fallback) — spec-gestao-logo-marca §4.2. */}
        {collapsed && !isMobile ? (
          <span className="flex items-center justify-center min-w-[48px]">
            <div className="w-9 h-9 bg-carmesim rounded-lg flex items-center justify-center">
              <span className="text-white font-extrabold text-sm tracking-tight">AC</span>
            </div>
          </span>
        ) : (
          <BrandLogo className="h-9" />
        )}

        {/* Toggle expand/collapse — only on desktop */}
        {!isMobile && (
          <button
            onClick={toggleSidebar}
            className="ml-auto h-11 w-11 flex items-center justify-center rounded-md text-gray-500 hover:text-carmesim hover:bg-carmesim/10 transition-colors"
            title={expanded ? 'Colapsar menu' : 'Expandir menu'}
            aria-label={expanded ? 'Colapsar menu' : 'Expandir menu'}
            aria-expanded={expanded}
            data-testid="sidebar-toggle-btn"
          >
            {expanded ? <ChevronsLeft className="w-5 h-5" aria-hidden="true" /> : <ChevronsRight className="w-5 h-5" aria-hidden="true" />}
          </button>
        )}
        {isMobile && (
          <button
            onClick={() => setMobileOpen(false)}
            className="ml-auto p-1.5 rounded-md text-gray-400 hover:text-carmesim transition-colors"
            aria-label="Fechar menu"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        )}
      </div>

      {/* ---- Menu sections ---- */}
      <nav className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-2 py-3 sidebar-scroll">
        {menuSections.map((section) => {
          const visibleItems = section.items.filter(filterItem);
          if (visibleItems.length === 0) return null;
          return (
            <div key={section.title} className="mb-2">
              {/* Section title */}
              <div className="flex items-center h-9 px-1 mb-0.5">
                <span
                  className={`text-xs uppercase tracking-[0.12em] font-semibold whitespace-nowrap transition-opacity duration-300 ${
                    collapsed && !isMobile ? 'opacity-0 w-0' : 'opacity-100 ml-2'
                  } text-muted-auto`}
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
                            : 'hover:bg-[#F5F5F5] hover:text-grafite text-secondary-auto'
                        }`}
                        data-testid={`sidebar-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                        title={collapsed && !isMobile ? item.label : undefined}
                      >
                        <span className="flex items-center justify-center min-w-[48px] h-[44px]">
                          <Icon
                            className={`w-[20px] h-[20px] transition-colors ${
                              isActive ? 'text-white' : 'group-hover:text-grafite text-muted-auto'
                            }`}
                          />
                        </span>
                        <span
                          className={`text-sm whitespace-nowrap transition-opacity duration-300 ${
                            collapsed && !isMobile ? 'opacity-0 pointer-events-none w-0' : 'opacity-100'
                          }`}
                        >
                          {item.label}
                        </span>
                        {item.badge === 'registration' && registrationBadgeCount > 0 && (
                          collapsed && !isMobile ? (
                            <span className="absolute top-1.5 right-2 w-2 h-2 rounded-full bg-carmesim" aria-hidden="true" />
                          ) : (
                            <span
                              className={`ml-auto mr-2 min-w-[20px] h-5 px-1.5 rounded-full text-[11px] font-bold flex items-center justify-center ${
                                isActive ? 'bg-white text-carmesim' : 'bg-carmesim text-white'
                              }`}
                              aria-label={`${registrationBadgeCount} pedidos pendentes`}
                            >
                              {registrationBadgeCount}
                            </span>
                          )
                        )}
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
            <div className="text-sm font-semibold truncate text-grafite-auto">{user?.name}</div>
            <div className="text-xs truncate text-muted-auto">{user?.email}</div>
          </div>
        </div>

        {/* Status badge */}
        {user?.status !== 'ativo' && !collapsed && (
          <div className="mx-1 mb-2 px-2 py-1 bg-carmesim/10 border border-carmesim/30 rounded-md text-xs text-carmesim uppercase tracking-wider font-semibold text-center">
            {user?.status}
          </div>
        )}

        {/* Logout button */}
        <button
          onClick={handleLogout}
          className="w-full flex items-center rounded-lg transition-colors text-secondary-auto"
          data-testid="logout-button"
        >
          <span className="flex items-center justify-center min-w-[48px] h-[40px]">
            <LogOut className="w-[18px] h-[18px]" />
          </span>
          <span
            className={`text-sm whitespace-nowrap transition-opacity duration-300 ${
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
        data-testid="desktop-sidebar"
      >
        {sidebarInner({ isMobile: false })}
      </aside>

      {/* ======= Mobile Sidebar Overlay — CSS transitions, sem framer.
          ease-spring (cubic-bezier 0.32,0.72,0,1) replica feel "premium"
          dos animations Apple/iOS, mais polished que ease-out linear. */}
      <div
        className={`fixed inset-0 bg-black/40 z-40 md:hidden backdrop-blur-sm transition-opacity duration-300 ease-spring ${
          mobileOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={() => setMobileOpen(false)}
        aria-hidden={!mobileOpen}
      />
      <aside
        className={`fixed left-0 top-0 bottom-0 z-50 md:hidden flex flex-col shadow-xl transition-transform duration-[280ms] ease-spring will-change-transform ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ width: SIDEBAR_W, backgroundColor: 'var(--surface-sidebar)' }}
        aria-hidden={!mobileOpen}
      >
        {sidebarInner({ isMobile: true })}
      </aside>

      {/* ======= Main Content ======= */}
      <div className="flex-1 min-w-0">
        {/* Mobile Header */}
        <header className="md:hidden sticky top-0 z-30 backdrop-blur-md px-4 py-3" style={{ backgroundColor: 'var(--surface-header)', borderBottom: '1px solid var(--surface-border)' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setMobileOpen(true)}
                className="p-2 -ml-2 rounded-lg transition-colors touch-target text-grafite-auto"
                aria-label="Abrir menu"
                data-testid="mobile-sidebar-button"
              >
                <Menu className="w-5 h-5" aria-hidden="true" />
              </button>
              <span className="font-bold text-base text-grafite-auto">{currentPageTitle}</span>
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
            <h1 className="font-semibold text-base text-grafite-auto">{currentPageTitle}</h1>
            <div className="flex items-center gap-3">
              <NotificationBell />
              <div className="flex items-center gap-2 pl-3" style={{ borderLeft: '1px solid var(--surface-border)' }}>
                <div className="w-8 h-8 bg-carmesim rounded-full flex items-center justify-center text-white text-xs font-bold">
                  {user?.name?.charAt(0).toUpperCase()}
                </div>
                <span className="text-sm font-medium hidden lg:block text-grafite-auto">{user?.name}</span>
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
