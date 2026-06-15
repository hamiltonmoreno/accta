import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { registrationAPI } from '../utils/api';
import { queryKeys } from '../lib/queryClient';
import { buildNavContext, isNavItemVisible } from '../lib/nav/visibility';
import { Header } from './components/Header';
import {
  LayoutDashboard,
  Vote,
  FileText,
  Gift,
  Users,
  X,
  ClipboardList,
  Calendar,
  DollarSign,
  ChevronsLeft,
  ChevronsRight,
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
  Medal,
  FileCheck,
  ScrollText,
  Megaphone,
  GraduationCap,
  BookOpen,
  Network,
  Lightbulb,
  ShieldAlert,
} from 'lucide-react';

const SIDEBAR_STORAGE_KEY = 'accta:sidebar-expanded';

/* ========== GROUPED MENU SECTIONS ========== */
// Mural e Ranking vivem no cabeçalho (atalhos de uso frequente). Aparência saiu
// de Comunidade para Administração, sob o sub-rótulo "Configurações do sistema"
// (secção única; Configurações deixou de ser uma secção própria).
const menuSections = [
  {
    title: 'Painel',
    items: [
      { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, roles: ['all'] },
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
      { label: 'Galeria', path: '/galeria-admin', icon: Camera, roles: ['all'] },
      { label: 'Benefícios', path: '/beneficios', icon: Gift, roles: ['all'] },
      { label: 'Notícias', path: '/admin/noticias', icon: Newspaper, roles: ['admin', 'moderador'] },
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
    title: 'Administração',
    items: [
      { label: 'Pedidos de Inscrição', path: '/admin/pedidos-inscricao', icon: UserPlus, roles: ['admin'], badge: 'registration' },
      { label: 'Utilizadores', path: '/admin/usuarios', icon: Users, roles: ['admin'], privileges: ['manage_users'] },
      { label: 'Cargos & Mandatos', path: '/admin/cargos', icon: Award, roles: ['admin'], privileges: ['manage_users'] },
      { label: 'Comunicados', path: '/admin/comunicados', icon: Megaphone, roles: ['admin'], privileges: ['send_comunicados'] },
      { label: 'Audit Logs', path: '/admin/logs', icon: ClipboardList, roles: ['admin'], privileges: ['view_audit_logs'] },
      // Sub-rótulo dentro de Administração (fundido da antiga secção
      // "Configurações do sistema"). Sem RBAC próprio — segue os itens abaixo.
      { subheader: 'Configurações do sistema' },
      { label: 'Aparência', path: '/admin/aparencia', icon: Palette, roles: ['admin', 'moderador'] },
    ],
  },
];

// Título do cabeçalho por rota. Match exacto via lookup; rotas com :id usam o
// fallback por prefixo (PAGE_TITLE_PREFIXES); default 'Portal'.
const PAGE_TITLES = {
  '/dashboard': 'Dashboard',
  '/perfil': 'Meu Perfil',
  '/ajuda': 'Central de Ajuda',
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

  // O título deixou de aparecer no cabeçalho (o corpo da página já o mostra) —
  // passamos a usá-lo no título da aba do browser.
  useEffect(() => {
    document.title = `ACCTA — ${currentPageTitle}`;
  }, [currentPageTitle]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  /* ========== TOGGLE LOGIC ========== */
  const toggleSidebar = useCallback(() => {
    setExpanded((prev) => !prev);
  }, []);

  /* Filter menu items by role (ou por privilégio granular — RBAC aditivo).
     A regra vive em lib/nav/visibility (partilhada com a Central de Ajuda). */
  const navCtx = buildNavContext({ isAdmin, isFinanceiro, isModerador, isDirecao, isMesaAG, user });
  const filterItem = (item) => isNavItemVisible(item, navCtx);

  const sidebarWidth = collapsed ? SIDEBAR_COLLAPSED_W : SIDEBAR_W;

  /* ========== SIDEBAR CONTENT (shared desktop/mobile) ========== */
  const sidebarInner = ({ isMobile = false }) => (
    <div className="flex flex-col h-full">
      {/* ---- Top: toggle compacto (desktop) / fechar (mobile). Slim, sem o
           "buraco" da antiga linha do logo — o menu estende-se para cima. ---- */}
      <div className="flex items-center px-2 py-2">
        {!isMobile && (
          <button
            onClick={toggleSidebar}
            className="ml-auto h-8 w-8 flex items-center justify-center rounded-md text-gray-500 hover:text-carmesim hover:bg-carmesim/10 transition-colors"
            title={expanded ? 'Colapsar menu' : 'Expandir menu'}
            aria-label={expanded ? 'Colapsar menu' : 'Expandir menu'}
            aria-expanded={expanded}
            data-testid="sidebar-toggle-btn"
          >
            {expanded ? <ChevronsLeft className="w-5 h-5" aria-hidden="true" /> : <ChevronsRight className="w-5 h-5" aria-hidden="true" />}
          </button>
        )}
        {isMobile && (
          <>
            <span className="font-semibold text-sm text-grafite-auto">Menu</span>
            <button
              onClick={() => setMobileOpen(false)}
              className="ml-auto p-1.5 rounded-md text-gray-400 hover:text-carmesim transition-colors"
              aria-label="Fechar menu"
            >
              <X className="w-5 h-5" aria-hidden="true" />
            </button>
          </>
        )}
      </div>

      {/* ---- Menu sections ---- */}
      <nav className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-2 py-3 sidebar-scroll">
        {menuSections.map((section) => {
          const filtered = section.items.filter(filterItem);
          // Esconde sub-rótulos órfãos (sem nenhum item real a seguir).
          const visibleItems = filtered.filter(
            (it, i) => !it.subheader || filtered.slice(i + 1).some((n) => !n.subheader)
          );
          // Secção só aparece se tiver pelo menos um item real (não só rótulos).
          if (!visibleItems.some((it) => !it.subheader)) return null;
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
                  // Sub-rótulo: divisor visual dentro da secção (não é um link).
                  if (item.subheader) {
                    return (
                      <li key={`sub-${item.subheader}`} className="pt-2">
                        {collapsed && !isMobile ? (
                          <span className="mx-auto block h-px w-5 rounded-full bg-gray-200" />
                        ) : (
                          <span className="block ml-2 px-1 pt-2 border-t border-gray-100 text-[11px] uppercase tracking-[0.1em] font-semibold whitespace-nowrap text-muted-auto">
                            {item.subheader}
                          </span>
                        )}
                      </li>
                    );
                  }
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
    </div>
  );

  return (
    <div className="min-h-screen bg-[var(--surface-bg)]">
      {/* ======= Cabeçalho fixo full-width ======= */}
      <Header
        onOpenMobileMenu={() => setMobileOpen(true)}
        onLogout={handleLogout}
        mobileMenuButtonRef={menuBtnRef}
      />

      {/* ======= Desktop Sidebar — começa ABAIXO do cabeçalho ======= */}
      <aside
        className="hidden md:flex md:flex-col fixed left-0 top-[var(--header-h)] bottom-0 z-30 transition-all duration-300 ease-in-out bg-[var(--surface-sidebar)] shadow-[0_0_6px_rgba(0,0,0,0.06)]"
        style={{ width: sidebarWidth }}
        data-testid="desktop-sidebar"
      >
        {sidebarInner({ isMobile: false })}
      </aside>

      {/* ======= Mobile drawer + overlay (abaixo do cabeçalho) ======= */}
      <div
        className={`fixed inset-x-0 bottom-0 top-[var(--header-h)] bg-black/40 z-40 md:hidden backdrop-blur-sm transition-opacity duration-300 ease-spring ${
          mobileOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={() => setMobileOpen(false)}
        aria-hidden={!mobileOpen}
      />
      <aside
        ref={mobileNavRef}
        className={`fixed left-0 top-[var(--header-h)] bottom-0 z-50 md:hidden flex flex-col shadow-xl transition-transform duration-[280ms] ease-spring will-change-transform bg-[var(--surface-sidebar)] ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ width: SIDEBAR_W }}
        aria-hidden={!mobileOpen}
        aria-label="Menu de navegação"
      >
        {sidebarInner({ isMobile: true })}
      </aside>

      {/* ======= Conteúdo ======= */}
      <main
        className="p-4 sm:p-6 animate-fadeIn transition-all duration-300"
        style={{
          marginTop: 'var(--header-h)',
          marginLeft: isDesktop ? sidebarWidth : undefined,
        }}
      >
        {children}
      </main>
    </div>
  );
};
