# Redesenho do shell privado — cabeçalho + sidebar

**Data:** 2026-06-07
**Âmbito:** layout autenticado (`PrivateLayout`) do Portal ACCTA — frontend apenas.
**Estado:** design aprovado pelo dono; pronto para plano de implementação.

---

## 1. Problema

O layout privado atual (`frontend/src/layouts/PrivateLayout.js`) tem três fricções:

1. **Colisão estrutural** — o sidebar é `fixed h-screen top-0 z-30`, sobe até ao
   topo absoluto, e o cabeçalho é apenas empurrado para a direita com
   `padding-left = sidebarWidth`. Não existe um cabeçalho a toda a largura; o
   sidebar "entra por baixo" da banda do cabeçalho.
2. **Logo no sítio errado** — a logo (`BrandLogo`) vive no topo do sidebar, não
   num cabeçalho fixo.
3. **Densidade do sidebar** — itens de uso muito frequente (Mural) estão a meio
   da lista; itens pessoais/utilitários (Ranking, Meu Perfil, Notificações,
   nome + Sair) ocupam espaço de navegação.

## 2. Objetivos

- Cabeçalho **fixo a toda a largura** com a **logo fixa**.
- Sidebar a **começar abaixo** do cabeçalho (sem colisão).
- Mover para o cabeçalho: **Notificações**, **Ranking**, **Meu Perfil**,
  **Carteira Digital**, **nome do utilizador** e **Sair**.
- Reordenar o sidebar por **frequência de interação** (Mural no topo).
- Tudo **fluido, responsivo e legível**, dentro do design system ACCTA.

### Não-objetivos (fora de âmbito)

- Reordenação do menu **por role** (decisão: ordem única para todos + RBAC).
- Novas páginas, novas rotas ou mudanças de permissões/RBAC.
- Qualquer alteração de backend.

## 3. Decisões (validadas com o dono)

| # | Decisão |
|---|---------|
| 1 | Cabeçalho full-width **por cima de tudo**; sidebar começa abaixo; logo no cabeçalho. |
| 2 | Cluster direito = **avatar com dropdown**. Notificações e Ranking como ícones diretos; Meu Perfil, Carteira e Sair (+ nome/email) dentro do dropdown. |
| 3 | Ícone de **Ranking só para sócios** (membros). Escondido para `account_type === 'technical'` e contas sem pontuação (admin técnico). |
| 4 | **Personalização = ordem única + RBAC.** Sem reordenação por role; `filterItem` continua a esconder o que cada role não pode ver. |
| 5 | **Mural no topo** da navegação (logo a seguir ao Dashboard). |
| 6 | Ordem do sidebar conforme §5. |
| 7 | **Carteira Digital migra para o dropdown** do avatar (área pessoal; só sócios). |
| 8 | **Mobile:** cabeçalho = hambúrguer + logo + título + sino + avatar. O **Ranking dobra para dentro do dropdown** (não fica como ícone solto). |
| 9 | Botão de **colapsar/expandir o sidebar → topo do sidebar** (onde estava a logo). |

## 4. Estrutura do shell

Substituir o hack de `padding-left` por um shell com cabeçalho fixo e
deslocamentos por margem.

```
┌───────────────────────────────────────────────────────────┐  ← header
│ [logo] Título                  🔔  🏆  │  ( avatar ▾ )      │   fixed top-0 inset-x-0
├──────────────┬────────────────────────────────────────────┤   h = var(--header-h) (64px)
│  SIDEBAR     │                                             │   z-40
│  (top:       │            MAIN                             │
│   header-h)  │  margin-top: var(--header-h)                │
│  z-30        │  margin-left: sidebarWidth (desktop)        │
│              │                                             │
└──────────────┴────────────────────────────────────────────┘
```

- **Header:** `fixed top-0 inset-x-0 z-40`, altura `var(--header-h)` (definir token,
  ex.: 64px), fundo `--surface-header`, borda inferior, `backdrop-blur`.
- **Sidebar (desktop):** `fixed left-0 top-[var(--header-h)] bottom-0 z-30`,
  largura `SIDEBAR_W` (270) / `SIDEBAR_COLLAPSED_W` (72). Mantém persistência em
  `localStorage` (`accta:sidebar-expanded`) e as transições atuais.
- **Main:** `margin-top: var(--header-h)`; `margin-left` = largura do sidebar no
  desktop (via media query `min-width:768px`, como hoje em `isDesktop`).
- **Mobile:** sidebar continua a ser um **drawer** (`-translate-x-full` →
  `translate-x-0`), a deslizar **a partir de `top: var(--header-h)`** (o
  cabeçalho fixo, com logo e hambúrguer, permanece visível por cima). O overlay
  cobre a área abaixo do cabeçalho. Manter o focus-trap + fecho com Escape +
  devolução de foco existentes.

## 5. Cabeçalho

### 5.1 Desktop
- **Esquerda:** `BrandLogo` (fixa) + título da página (`getPageTitle`).
- **Direita (cluster):**
  - 🔔 **Notificações** — `NotificationBell` (componente atual, inalterado).
  - 🏆 **Ranking** — `Link` para `/ranking`, **só visível a sócios** (ver §7).
  - separador vertical.
  - **Avatar ▾** — abre o `UserMenu` (dropdown).

### 5.2 Dropdown do avatar (`UserMenu`)
Usar `shadcn/ui` `DropdownMenu` (a11y/teclado já tratados pelo primitivo).
Conteúdo, por ordem:
1. Cabeçalho não-clicável: **nome** + **email** (+ badge de estado se
   `status !== 'ativo'`, reaproveitando `statusConfig`).
2. **Meu Perfil** → `/perfil`.
3. **Carteira Digital** → `/carteira` (**só sócios**).
4. separador.
5. **Sair** — ação destrutiva (texto Carmesim `#C7202F`), chama `logout()` +
   `navigate('/login')`.

### 5.3 Mobile
- Hambúrguer (abre drawer) + logo + título à esquerda; **sino + avatar** à
  direita. O **Ranking** entra no dropdown do avatar (item extra, só sócios),
  em vez de ícone no cabeçalho.

## 6. Sidebar — ordem proposta

Mesma estrutura agrupada de hoje; `filterItem` (RBAC) **inalterado**. Itens
movidos para o cabeçalho/dropdown são **removidos** das secções.

| Secção | Itens (ordem) |
|--------|---------------|
| Painel | Dashboard |
| Comunidade | **Mural**, Galeria, Benefícios, Notícias / Blog, Aparência |
| Atividade & Gestão | Votações, Eventos, Projetos, Documentos, Financeiro, Co-aprovações |
| Participação | Patrocínios, Petições, Propostas, Esclarecimentos, Reclamações |
| Órgãos Sociais | Assembleias, Eleições, Regulamentos, Honorários, Disciplina |
| Profissional | Formações, Publicações, Defesa Profissional, Relações Externas |
| Sistema (admin) | Pedidos de Inscrição, Utilizadores, Cargos & Mandatos, Comunicados, Audit Logs |

- **Removidos do sidebar:** Ranking, Meu Perfil, Notificações, Carteira Digital,
  bloco de perfil (nome/email) + botão Sair, logo.
- **Botão de colapsar** ‹‹/›› passa para o **topo do sidebar**.
- O badge de "Pedidos de Inscrição" (`registrationBadgeCount`) mantém-se no item.
- A secção "Gestão" passa a chamar-se **"Atividade & Gestão"** (apenas o rótulo).

## 7. Visibilidade do Ranking (regra)

O ícone/entrada de Ranking só aparece para **sócios reais**:

- Esconder quando `user.account_type === 'technical'`.
- (Contas `member`, ou sem `account_type`, são tratadas como sócio — coerente
  com a regra de identidade: "missing ⇒ member".)
- Reutilizar/centralizar num helper simples (ex.: `isMember(user)`), evitando
  espalhar a condição.

## 8. Responsividade & acessibilidade

- Breakpoint desktop: `min-width: 768px` (igual ao atual `isDesktop`).
- Drawer mobile: manter **overlay**, **focus-trap**, fecho com **Escape** e
  devolução de foco ao botão que o abriu (código já existente — preservar).
- `DropdownMenu` do shadcn garante navegação por teclado, `aria-*` e fecho ao
  clicar fora / Escape.
- Contraste ≥ 4.5:1; foco visível `ring-2 ring-[#C7202F]/40 ring-offset-2`.
- Sem dark mode. Sem inline styles — Tailwind + tokens de superfície
  (`--surface-*`) existentes.

## 9. Design system (ACCTA)

- Neutro a liderar (branco/`#F5F5F5`, Grafite `#3A3A3A`).
- **Carmesim `#C7202F`** = identidade (logo, nav ativa, focus, links) +
  **destrutivo** (texto "Sair"). **Nunca** Carmesim como primário positivo,
  **nunca** vermelho sobre fundo escuro/colorido.
- `Floresta #166534` não se aplica aqui (não há botão primário positivo no
  shell).
- Fonte Open Sans; ícones `lucide-react`.

## 10. Decomposição de componentes

Reduzir o tamanho do `PrivateLayout` extraindo responsabilidades:

| Unidade | Responsabilidade | Depende de |
|---------|------------------|------------|
| `PrivateLayout.js` | Compõe o shell (header + sidebar + main), estado de colapso/drawer, media query. | Header, Sidebar, useAuth |
| `Header.jsx` (novo) | Cabeçalho fixo: logo, título, cluster (Notificações, Ranking, UserMenu). | NotificationBell, UserMenu, BrandLogo, useAuth |
| `UserMenu.jsx` (novo) | Dropdown do avatar: nome/email, Meu Perfil, Carteira, Ranking (mobile), Sair. | shadcn DropdownMenu, UserAvatar, useAuth |
| `Sidebar.jsx` (novo, opcional) | Navegação agrupada + colapso + drawer; consome `menuSections` + `filterItem`. | useAuth, react-router |
| `menuSections` | Constante de dados (reordenada). Pode ir para módulo próprio. | — |

> A extração de `Sidebar.jsx` é recomendada mas não obrigatória; o plano pode
> manter o sidebar inline se a extração aumentar o risco. Header + UserMenu são
> as extrações de maior valor.

## 11. Critérios de aceitação

1. Cabeçalho fixo a toda a largura, com a logo à esquerda; visível em todas as
   páginas privadas; o sidebar nunca o sobrepõe nem "entra por baixo".
2. O sidebar começa abaixo do cabeçalho e o conteúdo (`main`) nunca fica oculto
   sob o cabeçalho nem sob o sidebar (desktop e mobile).
3. Notificações e Ranking (só sócios) aparecem como ícones no cabeçalho desktop;
   o dropdown do avatar contém nome/email, Meu Perfil, Carteira (sócios) e Sair.
4. Não há nome de utilizador, botão Sair, Ranking, Meu Perfil, Notificações nem
   Carteira no sidebar; nem logo no sidebar.
5. Mural é o primeiro item navegável a seguir ao Dashboard.
6. RBAC inalterado: cada role vê exatamente as mesmas entradas que via antes
   (apenas reposicionadas).
7. Botão de colapsar funciona a partir do topo do sidebar e persiste em
   `localStorage`.
8. Mobile: cabeçalho compacto (hambúrguer + logo + título + sino + avatar);
   Ranking dentro do dropdown; drawer mantém focus-trap + Escape.
9. Lint do frontend passa; sem regressões de a11y (foco/teclado no dropdown e
   no drawer).

## 12. Riscos

- **`--header-h` e offsets:** errar a altura do cabeçalho deixa uma faixa de
  conteúdo escondida. Usar um único token e derivar margens dele.
- **z-index:** garantir header (`z-40`) > drawer/overlay coerentes; rever a
  pilha atual (`z-30/40/50`).
- **Tamanho do `PrivateLayout`:** extrair Header/UserMenu para não inflar o
  ficheiro.
```
