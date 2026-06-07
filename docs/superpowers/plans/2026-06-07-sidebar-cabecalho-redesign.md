# Redesenho do shell privado (cabeçalho + sidebar) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganizar o layout autenticado do Portal ACCTA — cabeçalho fixo full-width com a logo, sidebar a começar abaixo do cabeçalho, e itens pessoais/utilitários (Notificações, Ranking, Meu Perfil, Carteira, Sair) movidos para o cabeçalho/dropdown do avatar; sidebar reordenado por frequência (Mural no topo).

**Architecture:** Extrair dois componentes novos de `PrivateLayout.js` — `Header` (cabeçalho fixo) e `UserMenu` (dropdown do avatar, sobre o `DropdownMenu` do shadcn já existente) — e um helper `isMemberAccount`. `PrivateLayout` passa a compor `<Header/>` + sidebar posicionado por baixo (token CSS `--header-h`) + `main` deslocado por margens. RBAC (`filterItem`) e o focus-trap do drawer mantêm-se.

**Tech Stack:** React 19 (funcional + hooks), Tailwind, shadcn/ui (`dropdown-menu.jsx` + `@radix-ui/react-dropdown-menu`), lucide-react, react-router-dom v7, TanStack Query; testes craco/jest + React Testing Library (react-router-dom é mockado como `virtual`).

**Spec:** `docs/superpowers/specs/2026-06-07-sidebar-cabecalho-redesign-design.md`

**Branch:** `feature/sidebar-cabecalho-redesign` (já criado a partir de `develop`; contém o spec).

---

## Estrutura de ficheiros

| Ficheiro | Tipo | Responsabilidade |
|----------|------|------------------|
| `frontend/src/lib/account.js` | Criar | `isMemberAccount(user)` — sócio real (não `technical`). |
| `frontend/src/lib/__tests__/account.test.js` | Criar | Testes do helper. |
| `frontend/src/layouts/components/UserMenu.jsx` | Criar | Dropdown do avatar (nome/email, estado, Meu Perfil, Carteira, Ranking-mobile, Sair). |
| `frontend/src/layouts/components/__tests__/UserMenu.test.jsx` | Criar | Testes do dropdown. |
| `frontend/src/layouts/components/Header.jsx` | Criar | Cabeçalho fixo (hambúrguer, logo, título, NotificationBell, Ranking-desktop, UserMenu). |
| `frontend/src/layouts/components/__tests__/Header.test.jsx` | Criar | Testes do cabeçalho. |
| `frontend/src/index.css` | Modificar | Token `--header-h: 64px`. |
| `frontend/src/layouts/PrivateLayout.js` | Modificar | Reordenar `menuSections`, remover itens movidos, mover toggle p/ topo do sidebar, compor `<Header/>` + posicionamento. |
| `frontend/src/layouts/__tests__/PrivateLayout.test.jsx` | Criar | Sidebar reorganizado + cabeçalho presente + children. |

Convenção de comandos: correr a partir de `frontend/` → `cd frontend`. Um teste isolado: `yarn test src/<caminho>` (craco passa para jest).

---

### Task 1: Helper `isMemberAccount`

**Files:**
- Create: `frontend/src/lib/account.js`
- Test: `frontend/src/lib/__tests__/account.test.js`

- [ ] **Step 1: Escrever o teste que falha**

```javascript
// frontend/src/lib/__tests__/account.test.js
import { isMemberAccount } from '../account';

describe('isMemberAccount', () => {
  test('conta sem account_type é tratada como membro', () => {
    expect(isMemberAccount({ name: 'X' })).toBe(true);
  });
  test("account_type 'member' é membro", () => {
    expect(isMemberAccount({ account_type: 'member' })).toBe(true);
  });
  test("account_type 'technical' NÃO é membro", () => {
    expect(isMemberAccount({ account_type: 'technical' })).toBe(false);
  });
  test('user nulo não é membro', () => {
    expect(isMemberAccount(null)).toBe(true); // missing ⇒ member (default), null tratado como ausência
  });
});
```

- [ ] **Step 2: Correr e ver falhar**

Run: `cd frontend && yarn test src/lib/__tests__/account.test.js`
Expected: FAIL — "Cannot find module '../account'".

- [ ] **Step 3: Implementação mínima**

```javascript
// frontend/src/lib/account.js
/**
 * Sócio real vs. conta técnica de sistema (spec-identidade-cargos).
 * `account_type` ausente ⇒ tratado como 'member' (regra de identidade).
 * Só `technical` (ex.: admin@controlador.cv) não é membro — excluído de
 * pontuação/ranking.
 */
export const isMemberAccount = (user) => (user?.account_type || 'member') !== 'technical';
```

- [ ] **Step 4: Correr e ver passar**

Run: `cd frontend && yarn test src/lib/__tests__/account.test.js`
Expected: PASS (4 testes).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/account.js frontend/src/lib/__tests__/account.test.js
git commit -m "feat(layout): helper isMemberAccount (socio real vs conta tecnica)"
```

---

### Task 2: Componente `UserMenu` (dropdown do avatar)

**Files:**
- Create: `frontend/src/layouts/components/UserMenu.jsx`
- Test: `frontend/src/layouts/components/__tests__/UserMenu.test.jsx`

> O `DropdownMenu` do shadcn (Radix) renderiza o conteúdo num portal só quando aberto, o que é frágil em jsdom. Seguindo o padrão do projeto (mock de `ui/dialog`), o teste **mocka `ui/dropdown-menu`** para renderizar tudo inline.

- [ ] **Step 1: Escrever o teste que falha**

```jsx
// frontend/src/layouts/components/__tests__/UserMenu.test.jsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

jest.mock('react-router-dom', () => ({
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
}), { virtual: true });

// Passthrough do dropdown — torna o conteúdo sempre visível no teste.
jest.mock('../../../components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children }) => <div>{children}</div>,
  DropdownMenuContent: ({ children }) => <div>{children}</div>,
  DropdownMenuItem: ({ children, onClick, asChild, ...props }) => (
    <div onClick={onClick} {...props}>{children}</div>
  ),
  DropdownMenuLabel: ({ children }) => <div>{children}</div>,
  DropdownMenuSeparator: () => <hr />,
}));
jest.mock('../../../components/UserAvatar', () => ({
  UserAvatar: ({ name }) => <span data-testid="avatar">{name}</span>,
}));

const { UserMenu } = require('../UserMenu');

const baseUser = { name: 'Hamilton V.', email: 'h@accta.cv', status: 'ativo' };

test('mostra nome, email e Meu Perfil sempre', () => {
  render(<UserMenu user={baseUser} isSocio={false} isMember={true} onLogout={() => {}} />);
  expect(screen.getByText('Hamilton V.')).toBeInTheDocument();
  expect(screen.getByText('h@accta.cv')).toBeInTheDocument();
  expect(screen.getByTestId('menu-perfil')).toHaveAttribute('href', '/perfil');
});

test('Carteira só aparece para sócios', () => {
  const { rerender } = render(<UserMenu user={baseUser} isSocio={false} isMember={true} onLogout={() => {}} />);
  expect(screen.queryByTestId('menu-carteira')).toBeNull();
  rerender(<UserMenu user={baseUser} isSocio={true} isMember={true} onLogout={() => {}} />);
  expect(screen.getByTestId('menu-carteira')).toHaveAttribute('href', '/carteira');
});

test('Ranking (item mobile) só aparece para membros', () => {
  const { rerender } = render(<UserMenu user={baseUser} isSocio={true} isMember={false} onLogout={() => {}} />);
  expect(screen.queryByTestId('menu-ranking')).toBeNull();
  rerender(<UserMenu user={baseUser} isSocio={true} isMember={true} onLogout={() => {}} />);
  expect(screen.getByTestId('menu-ranking')).toHaveAttribute('href', '/ranking');
});

test('Sair chama onLogout', () => {
  const onLogout = jest.fn();
  render(<UserMenu user={baseUser} isSocio={true} isMember={true} onLogout={onLogout} />);
  fireEvent.click(screen.getByTestId('menu-sair'));
  expect(onLogout).toHaveBeenCalledTimes(1);
});

test('badge de estado aparece quando status != ativo', () => {
  render(<UserMenu user={{ ...baseUser, status: 'pendente_aprovacao' }} isSocio={true} isMember={true} onLogout={() => {}} />);
  expect(screen.getByTestId('menu-status')).toBeInTheDocument();
});
```

- [ ] **Step 2: Correr e ver falhar**

Run: `cd frontend && yarn test src/layouts/components/__tests__/UserMenu.test.jsx`
Expected: FAIL — "Cannot find module '../UserMenu'".

- [ ] **Step 3: Implementação**

```jsx
// frontend/src/layouts/components/UserMenu.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { UserCircle, CreditCard, Trophy, LogOut } from 'lucide-react';
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
 * Dropdown do avatar no cabeçalho. Itens pessoais (Meu Perfil, Carteira) +
 * Sair. `Ranking` aparece aqui SÓ em mobile (md:hidden) — no desktop é um
 * ícone no cabeçalho. Visibilidade por: isSocio (Carteira), isMember (Ranking).
 */
export const UserMenu = ({ user, isSocio, isMember, onLogout }) => {
  const sc =
    user?.status && user.status !== 'ativo'
      ? getStatusConfig(USER_STATUS_CONFIG, user.status, USER_STATUS_FALLBACK)
      : null;
  const StatusIcon = sc?.icon;
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="flex items-center rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
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
        <DropdownMenuItem asChild>
          <Link to="/perfil" data-testid="menu-perfil">
            <UserCircle className="w-4 h-4 mr-2" aria-hidden="true" />
            Meu Perfil
          </Link>
        </DropdownMenuItem>
        {isSocio && (
          <DropdownMenuItem asChild>
            <Link to="/carteira" data-testid="menu-carteira">
              <CreditCard className="w-4 h-4 mr-2" aria-hidden="true" />
              Carteira Digital
            </Link>
          </DropdownMenuItem>
        )}
        {isMember && (
          <DropdownMenuItem asChild className="md:hidden">
            <Link to="/ranking" data-testid="menu-ranking">
              <Trophy className="w-4 h-4 mr-2" aria-hidden="true" />
              Ranking
            </Link>
          </DropdownMenuItem>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={onLogout}
          data-testid="menu-sair"
          className="text-[#C7202F] focus:text-[#C7202F] focus:bg-[#FBEAEC]"
        >
          <LogOut className="w-4 h-4 mr-2" aria-hidden="true" />
          Sair
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default UserMenu;
```

- [ ] **Step 4: Correr e ver passar**

Run: `cd frontend && yarn test src/layouts/components/__tests__/UserMenu.test.jsx`
Expected: PASS (5 testes).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/layouts/components/UserMenu.jsx frontend/src/layouts/components/__tests__/UserMenu.test.jsx
git commit -m "feat(layout): UserMenu (dropdown do avatar com perfil/carteira/ranking/sair)"
```

---

### Task 3: Componente `Header` (cabeçalho fixo)

**Files:**
- Create: `frontend/src/layouts/components/Header.jsx`
- Test: `frontend/src/layouts/components/__tests__/Header.test.jsx`

- [ ] **Step 1: Escrever o teste que falha**

```jsx
// frontend/src/layouts/components/__tests__/Header.test.jsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

jest.mock('react-router-dom', () => ({
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
}), { virtual: true });
jest.mock('../../../contexts/AuthContext', () => ({ useAuth: jest.fn() }));
jest.mock('../../../components/NotificationBell', () => ({
  NotificationBell: () => <div data-testid="notif-bell" />,
}));
jest.mock('../../../components/BrandLogo', () => ({
  BrandLogo: () => <div data-testid="brand-logo" />,
}));
jest.mock('../UserMenu', () => ({
  UserMenu: ({ isMember }) => <div data-testid="user-menu" data-member={String(isMember)} />,
}));

const { useAuth } = require('../../../contexts/AuthContext');
const { Header } = require('../Header');

beforeEach(() => jest.clearAllMocks());

test('mostra logo, título, sino e o menu de utilizador', () => {
  useAuth.mockReturnValue({ user: { name: 'X', role: 'socio', account_type: 'member' } });
  render(<Header title="Dashboard" onOpenMobileMenu={() => {}} onLogout={() => {}} />);
  expect(screen.getByTestId('brand-logo')).toBeInTheDocument();
  expect(screen.getByText('Dashboard')).toBeInTheDocument();
  expect(screen.getByTestId('notif-bell')).toBeInTheDocument();
  expect(screen.getByTestId('user-menu')).toBeInTheDocument();
});

test('ícone de Ranking (desktop) aparece para sócio e some para conta técnica', () => {
  useAuth.mockReturnValue({ user: { name: 'X', role: 'socio', account_type: 'member' } });
  const { rerender } = render(<Header title="T" onOpenMobileMenu={() => {}} onLogout={() => {}} />);
  expect(screen.getByTestId('header-ranking')).toHaveAttribute('href', '/ranking');

  useAuth.mockReturnValue({ user: { name: 'Sys', role: 'admin', account_type: 'technical' } });
  rerender(<Header title="T" onOpenMobileMenu={() => {}} onLogout={() => {}} />);
  expect(screen.queryByTestId('header-ranking')).toBeNull();
});

test('hambúrguer chama onOpenMobileMenu', () => {
  useAuth.mockReturnValue({ user: { name: 'X', role: 'socio' } });
  const onOpen = jest.fn();
  render(<Header title="T" onOpenMobileMenu={onOpen} onLogout={() => {}} />);
  fireEvent.click(screen.getByTestId('mobile-sidebar-button'));
  expect(onOpen).toHaveBeenCalledTimes(1);
});
```

- [ ] **Step 2: Correr e ver falhar**

Run: `cd frontend && yarn test src/layouts/components/__tests__/Header.test.jsx`
Expected: FAIL — "Cannot find module '../Header'".

- [ ] **Step 3: Implementação**

```jsx
// frontend/src/layouts/components/Header.jsx
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
```

- [ ] **Step 4: Correr e ver passar**

Run: `cd frontend && yarn test src/layouts/components/__tests__/Header.test.jsx`
Expected: PASS (3 testes).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/layouts/components/Header.jsx frontend/src/layouts/components/__tests__/Header.test.jsx
git commit -m "feat(layout): Header fixo (logo, titulo, notificacoes, ranking desktop, UserMenu)"
```

---

### Task 4: Token CSS `--header-h`

**Files:**
- Modify: `frontend/src/index.css:48` (bloco `:root`/`@layer base`, após `--surface-header`)

- [ ] **Step 1: Adicionar o token**

Editar `frontend/src/index.css`, logo a seguir à linha `--surface-header: rgba(255,255,255,0.8);`:

```css
        --surface-header: rgba(255,255,255,0.8);
        --header-h: 64px;
```

- [ ] **Step 2: Verificar build de CSS (lint rápido)**

Run: `cd frontend && npx eslint src/layouts --ext .js,.jsx --max-warnings=60`
Expected: sem erros novos (o eslint não cobre CSS, mas confirma que nada partiu nos ficheiros JS/JSX já criados).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "feat(layout): token --header-h para a altura do cabecalho fixo"
```

---

### Task 5: Reordenar e limpar `menuSections` em `PrivateLayout`

**Files:**
- Modify: `frontend/src/layouts/PrivateLayout.js:55-130` (constante `menuSections`)

Remover do sidebar: **Ranking**, **Meu Perfil**, **Carteira Digital** (secção Painel) e **Notificações** (secção Sistema). Reordenar secções e renomear `Gestão` → `Atividade & Gestão`.

- [ ] **Step 1: Substituir a constante `menuSections` inteira**

Substituir o bloco `const menuSections = [ ... ];` (linhas ~56-130) por:

```javascript
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
```

- [ ] **Step 2: Verificar lint (apanha imports não usados na próxima task)**

Run: `cd frontend && npx eslint src/layouts/PrivateLayout.js --max-warnings=60`
Expected: pode reportar `'Trophy'/'UserCircle'/'CreditCard'/'Bell'` como não usados — **esperado**, resolvido na Task 6. Não deve haver erros de sintaxe.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/layouts/PrivateLayout.js
git commit -m "feat(layout): reordenar sidebar (Mural no topo) e remover itens movidos p/ cabecalho"
```

---

### Task 6: Reestruturar o shell do `PrivateLayout` (Header + posicionamento)

**Files:**
- Modify: `frontend/src/layouts/PrivateLayout.js` — imports (1-51), `sidebarInner` topo/rodapé, e o `return` final (453-536).

- [ ] **Step 1: Ajustar imports**

Substituir o bloco de imports de ícones e componentes (linhas ~7-51) para remover os agora não usados (`LogOut, Menu, Bell, UserCircle, Trophy, CreditCard`) e os componentes movidos para o `Header` (`NotificationBell, BrandLogo, UserAvatar`, `statusConfig`), acrescentando `Header`. Resultado:

```javascript
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { registrationAPI } from '../utils/api';
import { queryKeys } from '../lib/queryClient';
import { Header } from './components/Header';
import {
  LayoutDashboard,
  Vote,
  FileText,
  MessageSquare,
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
```

> Nota: `handleLogout`, `currentPageTitle`, `menuBtnRef`, `isDesktop`, `expanded`/`collapsed`, `sidebarWidth` e `filterItem` mantêm-se (já existem no corpo do componente). Remover a desestruturação de `logout` NÃO — `handleLogout` usa-o.

- [ ] **Step 2: Substituir o topo do `sidebarInner` (linha do logo) por uma linha só com o toggle**

Substituir o bloco `{/* ---- Logo row ---- */}` (div completo, ~289-324) por:

```jsx
      {/* ---- Top row: toggle (desktop) / fechar (mobile) — a logo agora vive no Header ---- */}
      <div className="flex items-center px-3 py-3 min-h-[56px] border-b border-[var(--surface-border)]">
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
```

- [ ] **Step 3: Remover o rodapé de perfil/logout do `sidebarInner`**

Apagar o bloco completo `{/* ---- Profile & Logout ---- */}` (div com `UserAvatar`, status badge e o botão `Sair`, ~403-449). O `sidebarInner` termina agora logo após o `</nav>`.

- [ ] **Step 4: Substituir o `return` final (shell)**

Substituir todo o `return ( ... );` final (~453-536) por:

```jsx
  return (
    <div className="min-h-screen bg-[var(--surface-bg)]">
      {/* ======= Cabeçalho fixo full-width ======= */}
      <Header
        title={currentPageTitle}
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
```

- [ ] **Step 5: Lint do ficheiro inteiro**

Run: `cd frontend && npx eslint src/layouts/PrivateLayout.js --max-warnings=60`
Expected: **sem erros nem warnings de imports não usados** (todos os ícones/componentes removidos já saíram dos imports).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/layouts/PrivateLayout.js
git commit -m "feat(layout): cabecalho full-width + sidebar abaixo dele (corrige colisao)"
```

---

### Task 7: Teste de integração do `PrivateLayout`

**Files:**
- Create: `frontend/src/layouts/__tests__/PrivateLayout.test.jsx`

> Mocka `./components/Header` (já testado isoladamente) e usa um role NÃO-admin para que a `useQuery` do badge fique desativada (`enabled: !!isAdmin`) e não chame a API.

- [ ] **Step 1: Escrever o teste**

```jsx
// frontend/src/layouts/__tests__/PrivateLayout.test.jsx
import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

jest.mock('react-router-dom', () => ({
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
  useNavigate: () => jest.fn(),
  useLocation: () => ({ pathname: '/dashboard' }),
}), { virtual: true });
jest.mock('../../contexts/AuthContext', () => ({ useAuth: jest.fn() }));
jest.mock('../components/Header', () => ({
  Header: () => <header data-testid="app-header" />,
}));
jest.mock('../../utils/api', () => ({
  registrationAPI: { listPending: jest.fn().mockResolvedValue({ data: [] }) },
}));

const { useAuth } = require('../../contexts/AuthContext');
const { PrivateLayout } = require('../PrivateLayout');

const renderLayout = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <PrivateLayout><div data-testid="conteudo">Olá</div></PrivateLayout>
    </QueryClientProvider>,
  );
};

beforeEach(() => {
  jest.clearAllMocks();
  useAuth.mockReturnValue({
    user: { name: 'Sócio', email: 's@accta.cv', role: 'socio', account_type: 'member' },
    logout: jest.fn(),
    isAdmin: false, isFinanceiro: false, isModerador: false, isDirecao: false, isMesaAG: false,
  });
});

test('renderiza o cabeçalho e o conteúdo', () => {
  renderLayout();
  expect(screen.getByTestId('app-header')).toBeInTheDocument();
  expect(screen.getByTestId('conteudo')).toHaveTextContent('Olá');
});

test('o sidebar tem Mural e NÃO tem os itens movidos para o cabeçalho', () => {
  renderLayout();
  const sidebar = screen.getByTestId('desktop-sidebar');
  expect(within(sidebar).getByText('Mural')).toBeInTheDocument();
  expect(within(sidebar).queryByText('Meu Perfil')).toBeNull();
  expect(within(sidebar).queryByText('Notificações')).toBeNull();
  expect(within(sidebar).queryByText('Ranking')).toBeNull();
  expect(within(sidebar).queryByText('Carteira Digital')).toBeNull();
  expect(within(sidebar).queryByText('Sair')).toBeNull();
});
```

- [ ] **Step 2: Correr e ver passar**

Run: `cd frontend && yarn test src/layouts/__tests__/PrivateLayout.test.jsx`
Expected: PASS (2 testes).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/layouts/__tests__/PrivateLayout.test.jsx
git commit -m "test(layout): PrivateLayout renderiza Header e sidebar reorganizado"
```

---

### Task 8: Verificação final (suite + lint + manual)

**Files:** nenhum (verificação).

- [ ] **Step 1: Suite de testes frontend completa**

Run: `cd frontend && yarn test`
Expected: PASS — todos os testes verdes (os novos + os existentes, sem regressões).

- [ ] **Step 2: Lint**

Run: `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60`
Expected: sem erros; warnings dentro do limite (60).

- [ ] **Step 3: Verificação manual (dev server)**

Run: `cd frontend && yarn start` (ou ver memória "Correr o ACCTA localmente" — proxy mesma-origem + login dev).
Confirmar visualmente, em desktop e mobile (DevTools responsive):
1. Cabeçalho fixo a toda a largura com a logo à esquerda; o sidebar **não** o sobrepõe e começa logo abaixo dele.
2. `main` não fica escondido sob o cabeçalho nem sob o sidebar.
3. Notificações + Ranking (ícone) no cabeçalho desktop; Ranking some numa conta técnica.
4. Avatar abre o dropdown com nome/email, Meu Perfil, Carteira (sócio), Sair.
5. Sidebar: Mural é o 1.º item navegável depois do Dashboard; sem Sair/Perfil/Ranking/Notificações/Carteira/logo.
6. Toggle de colapsar funciona a partir do topo do sidebar e persiste após refresh.
7. Mobile: cabeçalho compacto (hambúrguer + logo + título + sino + avatar); Ranking dentro do dropdown; drawer abre/fecha, fecha com Escape e devolve o foco ao hambúrguer.

- [ ] **Step 4: Abrir PR para `develop`**

```bash
git push -u origin feature/sidebar-cabecalho-redesign
gh pr create --base develop --head feature/sidebar-cabecalho-redesign \
  --title "feat(layout): redesenho do shell privado (cabecalho + sidebar)" \
  --body "Implementa o spec docs/superpowers/specs/2026-06-07-sidebar-cabecalho-redesign-design.md. Cabecalho fixo full-width com logo; sidebar abaixo dele; Notificacoes/Ranking no cabecalho e Perfil/Carteira/Sair no dropdown do avatar; sidebar reordenado (Mural no topo); RBAC inalterado. Sem backend."
```

> Nota: o CI do PR pode falhar pelo billing-lock dos Actions (conhecido, alheio ao código).

---

## Auto-revisão (writing-plans)

**1. Cobertura do spec:**
- §3 estrutura full-width + sidebar abaixo → Task 4 (token) + Task 6 (shell). ✓
- §5.1 cabeçalho desktop (logo, título, Notif, Ranking-membros, avatar) → Task 3. ✓
- §5.2 dropdown (nome/email, estado, Meu Perfil, Carteira-sócio, Sair) → Task 2. ✓
- §5.3 mobile (hambúrguer, logo, título, sino, avatar; Ranking dobra) → Task 3 (hambúrguer + `header-ranking` é `hidden md:flex`) + Task 2 (`menu-ranking` é `md:hidden`). ✓
- §6 sidebar reordenado, remoções, rename "Atividade & Gestão", toggle no topo → Task 5 + Task 6. ✓
- §7 Ranking só sócios (`isMemberAccount`) → Task 1, usado em Task 3. ✓
- §8 a11y: focus-trap/Escape do drawer preservados (lógica mantida; `menuBtnRef` encaminhado p/ hambúrguer) → Task 6. ✓
- §10 decomposição (Header + UserMenu + helper) → Tasks 1-3. ✓ (Sidebar.jsx era opcional — não extraído, por menor risco.)
- §11 critérios de aceitação → Task 8 verificação manual cobre 1-8; testes cobrem conteúdo/RBAC. ✓

**2. Placeholders:** nenhum — todo o código (novos ficheiros) e todas as edições estão escritos por extenso.

**3. Consistência de tipos/nomes:** `isMemberAccount` (Task 1) usado em Header (Task 3); props `UserMenu({ user, isSocio, isMember, onLogout })` idênticas entre Task 2 (def) e Task 3 (uso); `Header({ title, onOpenMobileMenu, onLogout, mobileMenuButtonRef })` idênticas entre Task 3 (def) e Task 6 (uso); `data-testid` (`app-header`, `desktop-sidebar`, `mobile-sidebar-button`, `sidebar-toggle-btn`, `menu-*`, `header-ranking`) consistentes entre componentes e testes. ✓
