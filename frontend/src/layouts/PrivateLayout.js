import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { registrationAPI } from '../utils/api';
import { queryKeys } from '../lib/queryClient';
import { NotificationBell } from '../components/NotificationBell';
import { BrandLogo } from '../components/BrandLogo';
import { UserAvatar } from '../components/UserAvatar';
import { USER_STATUS_CONFIG, USER_STATUS_FALLBACK, getStatusConfig } from '../lib/statusConfig';
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
  Medal,
  FileCheck,
  ScrollText,
  Megaphone,
  Trophy,
  GraduationCap,
  BookOpen,
  Network,
} from 'lucide-react';

const SIDEBAR_STORAGE_KEY = 'accta:sidebar-expanded';

/* ========== GROUPED MENU SECTIONS ========== */
const menuSections = [
  {
    title: 'Painel',
    items: [
      { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, roles: ['all'] },
    ],
  },
  {
    title: 'Comunidade',
    items: [
      { label: 'Mural', path: '/mural', icon: MessageSquare, roles: ['all'] },
      { label: 'Galeria', path: '/galeria-admin', icon: Camera, roles: ['all'] },
      { label: 'Benefícios', path: '/beneficios', icon: Gift, roles: ['all'] },
      { label: 'Notícias', path: '/admin/noticias', icon: Newspaper, roles: ['admin', 'moderador'] },
      { label: 'Aparência', path: '/admin/aparencia', icon: Palette, roles: ['admin', 'moderador'] },
    ],
  },
  {
    title: 'Atividade & Gestão',
    items: [
      { label: 'Votações', path: '/votacoes', icon: Vote, roles: ['all'] },
      { label: 'Eventos', path: '/eventos', icon: Calendar, roles: ['all'] },
      { label: 'Projetos', path: '/projetos', icon: FolderKanban, roles: ['all'] },
      { label: 'Documentos', path: '/documentos', icon: FileText, roles: ['all'] },
      { label: 'Financeiro', path: '/financeiro', icon: DollarSign, roles: ['admin', 'financeiro'], privileges: ['view_finances_readonly', 'manage_finances'] },
      { label: 'Co-aprovações', path: '/financeiro/co-aprovacoes', icon: FileCheck, roles: ['admin', 'financeiro'], privileges: ['view_finances_readonly', 'manage_finances'], match: 'direcao' },
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
    title: 'Órgãos Sociais',
    items: [
      { label: 'Assembleias', path: '/admin/assembleias', icon: Landmark, roles: ['all'] },
      { label: 'Eleições', path: '/admin/eleicoes', icon: ListChecks, roles: ['all'] },
      { label: 'Regulamentos', path: '/regulamentos', icon: ScrollText, roles: ['all'] },
      { label: 'Honorários', path: '/governanca/honorarios', icon: Medal, roles: ['admin'], match: 'governanca' },
      { label: 'Disciplina', path: '/admin/disciplinar', icon: Gavel, roles: ['admin'], match: 'direcao' },
    ],
  },
  {
    // Cat 5 (spec-fins-profissionais §10) — Grupos/Comissões já vivem em
    // /projetos via Project.tipo (F1). F3 acrescenta Defesa profissional e
    // Relações/IFATCA.
    title: 'Profissional',
    items: [
      { label: 'Formações', path: '/formacoes', icon: GraduationCap, roles: ['all'] },
      { label: 'Publicações', path: '/publicacoes', icon: BookOpen, roles: ['all'] },
      { label: 'Defesa Profissional', path: '/defesa-profissional', icon: Megaphone, roles: ['all'] },
      { label: 'Relações Externas', path: '/relacoes-externas', icon: Network, roles: ['all'] },
    ],
  },
  {
    title: 'Sistema',
    items: [
      { label: 'Pedidos de Inscrição', path: '/admin/pedidos-inscricao', icon: UserPlus, roles: ['admin'], badge: 'registration' },
      { label: 'Utilizadores', path: '/admin/usuarios', icon: Users, roles: ['admin'], privileges: ['manage_users'] },
      { label: 'Cargos & Mandatos', path: '/admin/cargos', icon: Award, roles: ['admin'], privileges: ['manage_users'] },
      { label: 'Comunicados', path: '/admin/comunicados', icon: Megaphone, roles: ['admin'], privileges: ['send_comunicados'] },
      { label: 'Audit Logs', path: '/admin/logs', icon: ClipboardList, roles: ['admin'], privileges: ['view_audit_logs'] },
    ],
  },
];

// Título do cabeçalho por rota. Match exacto via lookup; rotas com :id usam o
// fallback por prefixo (PAGE_TITLE_PREFIXES); default 'Portal'.
const PAGE_TITLES = {
  '/dashboard': 'Dashboard',
  '/perfil': 'Meu Perfil',
  '/carteira': 'Carteira Digital',
  '/financeiro': 'Financeiro',
  '/financeiro/co-aprovacoes': 'Co-aprovações',
  '/regulamentos': 'Regulamentos',
  '/projetos': 'Projetos',
  '/votacoes': 'Votações',
  '/eventos': 'Eventos',
  '/documentos': 'Documentos',
  '/mural': 'Mural',
  '/galeria-admin': 'Galeria',
  '/beneficios': 'Benefícios',
  '/notificacoes': 'Notificações',
  '/admin/pedidos-inscricao': 'Pedidos de Inscrição',
  '/admin/cargos': 'Cargos & Mandatos',
  '/admin/assembleias': 'Assembleias',
  '/admin/eleicoes': 'Eleições',
  '/admin/disciplinar': 'Disciplina',
  '/admin/aparencia': 'Aparência do Site',
  '/admin/comunicados': 'Comunicados',
  '/admin/noticias': 'Notícias / Blog',
  '/participacao/patrocinios': 'Patrocínios',
  '/participacao/peticoes': 'Petições',
  '/participacao/propostas': 'Propostas para a ordem de trabalhos',
  '/participacao/esclarecimentos': 'Pedidos de esclarecimento',
  '/participacao/reclamacoes': 'Reclamações e recursos',
  '/governanca/honorarios': 'Membros Honorários',
  '/admin/usuarios': 'Utilizadores',
  '/admin/logs': 'Audit Logs',
  '/formacoes': 'Formações & Certificações',
  '/publicacoes': 'Publicações',
  '/defesa-profissional': 'Defesa Profissional',
  '/relacoes-externas': 'Relações Externas',
};

// Rotas dinâmicas (com :id) — verificadas por prefixo só depois do match exacto.
const PAGE_TITLE_PREFIXES = [
  ['/projetos/', 'Detalhe do Projeto'],
  ['/admin/assembleias/', 'Assembleia'],
  ['/admin/eleicoes/', 'Eleição'],
];

const getPageTitle = (pathname) => {
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname];
  const prefixMatch = PAGE_TITLE_PREFIXES.find(([prefix]) => pathname.startsWith(prefix));
  return prefixMatch ? prefixMatch[1] : 'Portal';
};

export const PrivateLayout = ({ children }) => {
  const { user, logout, isAdmin, isFinanceiro, isModerador, isDirecao, isMesaAG } = useAuth();
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

  const mobileNavRef = useRef(null);
  const menuBtnRef = useRef(null);

  // Drawer mobile: prende o foco, fecha com Escape e devolve o foco ao botão
  // que o abriu — sem isto o teclado escapava para o conteúdo por trás (a11y).
  useEffect(() => {
    if (!mobileOpen) return;
    const node = mobileNavRef.current;
    if (!node) return;
    const getItems = () =>
      node.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])');
    getItems()[0]?.focus();
    const onKeyDown = (e) => {
      if (e.key === 'Escape') { setMobileOpen(false); return; }
      if (e.key !== 'Tab') return;
      const items = getItems();
      if (!items.length) return;
      const firstEl = items[0];
      const lastEl = items[items.length - 1];
      if (e.shiftKey && document.activeElement === firstEl) { e.preventDefault(); lastEl.focus(); }
      else if (!e.shiftKey && document.activeElement === lastEl) { e.preventDefault(); firstEl.focus(); }
    };
    const trigger = menuBtnRef.current;
    node.addEventListener('keydown', onKeyDown);
    return () => {
      node.removeEventListener('keydown', onKeyDown);
      trigger?.focus();
    };
  }, [mobileOpen]);

  const currentPageTitle = getPageTitle(pathname);

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
    if (item.match === 'governanca' && (isAdmin || isDirecao || isMesaAG)) return true;
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
      <div className="flex items-center gap-2 px-3 py-4 min-h-[64px] border-b border-[var(--surface-border)]">
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
                            <span className="absolute top-1.5 right-2 w-2 h-2 rounded-full bg-carmesim" role="status" aria-label={`${registrationBadgeCount} pedidos pendentes`} />
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
      <div className="px-2 py-3 border-t border-[var(--surface-border)]">
        {/* User profile */}
        <div className="flex items-center gap-3 px-1 mb-2">
          <UserAvatar size="sm" name={user?.name} photoUrl={user?.photo_url} />
          <div
            className={`min-w-0 flex-1 transition-opacity duration-300 ${
              collapsed && !isMobile ? 'opacity-0 pointer-events-none w-0' : 'opacity-100'
            }`}
          >
            <div className="text-sm font-semibold truncate text-grafite-auto">{user?.name}</div>
            <div className="text-xs truncate text-muted-auto">{user?.email}</div>
          </div>
        </div>

        {/* Status badge — só para estados não-'ativo'; tom semântico por estado
            (pendente_* warning · inativo neutro · rejeitado erro) via statusConfig */}
        {user?.status && user.status !== 'ativo' && !collapsed && (() => {
          const sc = getStatusConfig(USER_STATUS_CONFIG, user.status, USER_STATUS_FALLBACK);
          const StatusIcon = sc.icon;
          return (
            <div className={`mx-1 mb-2 px-2 py-1 rounded-md text-xs uppercase tracking-wider font-semibold text-center flex items-center justify-center gap-1 ${sc.className}`}>
              {StatusIcon && <StatusIcon className="h-3 w-3" />}
              {sc.label}
            </div>
          );
        })()}

        {/* Logout button */}
        <button
          onClick={handleLogout}
          aria-label="Sair"
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
    <div className="min-h-screen flex bg-[var(--surface-bg)]">
      {/* ======= Desktop Sidebar ======= */}
      <aside
        className="hidden md:flex md:flex-col fixed h-screen z-30 transition-all duration-300 ease-in-out bg-[var(--surface-sidebar)] shadow-[0_0_6px_rgba(0,0,0,0.06)]"
        style={{ width: sidebarWidth }}
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
        ref={mobileNavRef}
        className={`fixed left-0 top-0 bottom-0 z-50 md:hidden flex flex-col shadow-xl transition-transform duration-[280ms] ease-spring will-change-transform bg-[var(--surface-sidebar)] ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ width: SIDEBAR_W }}
        aria-hidden={!mobileOpen}
        aria-label="Menu de navegação"
      >
        {sidebarInner({ isMobile: true })}
      </aside>

      {/* ======= Main Content ======= */}
      <div className="flex-1 min-w-0">
        {/* Mobile Header */}
        <header className="md:hidden sticky top-0 z-30 backdrop-blur-md px-4 py-3 bg-[var(--surface-header)] border-b border-[var(--surface-border)]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                ref={menuBtnRef}
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
              <UserAvatar size="xs" name={user?.name} photoUrl={user?.photo_url} />
            </div>
          </div>
        </header>

        {/* Desktop Top Bar */}
        <header
          className="hidden md:block sticky top-0 z-30 backdrop-blur-md py-3 pr-6 transition-all duration-300 bg-[var(--surface-header)] border-b border-[var(--surface-border)]"
          style={{ paddingLeft: isDesktop ? `calc(${sidebarWidth}px + 1.5rem)` : undefined }}
        >
          <div className="flex items-center justify-between">
            <h1 className="font-semibold text-base text-grafite-auto">{currentPageTitle}</h1>
            <div className="flex items-center gap-3">
              <NotificationBell />
              <div className="flex items-center gap-2 pl-3 border-l border-[var(--surface-border)]">
                <UserAvatar size="xs" name={user?.name} photoUrl={user?.photo_url} />
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
