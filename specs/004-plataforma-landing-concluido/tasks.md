---
description: "Task list — Landing page da plataforma de gestão de associações"
---

# Tasks: Landing page da plataforma de gestão de associações

**Input**: Design documents from `/specs/004-plataforma-landing/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: NÃO foram pedidos testes automatizados (não há suite de testes de frontend para páginas públicas). A verificação é **lint + build + manual no browser** (Constituição VII, ver `quickstart.md`). Por isso não há tarefas de teste neste plano.

**Organization**: tarefas agrupadas por user story para entrega incremental e teste independente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode correr em paralelo (ficheiro diferente, sem dependências por concluir)
- **[Story]**: a que user story pertence (US1, US2, US3)
- Caminhos de ficheiro exatos nas descrições

## Path Conventions

- Web app — frontend em `frontend/src/`. Esta feature é **frontend-only** (sem `backend/`, sem DB).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: preparar o ambiente de frontend sem introduzir dependências novas.

- [x] T001 Confirmar ambiente do frontend e **ausência de novas dependências**: `cd frontend && yarn install` (se necessário) e `yarn start` arranca o site público. Não correr `yarn add` (penduram nesta máquina — ver memória `frontend-dep-install-hangs`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: criar o componente e a rota de que todas as user stories dependem.

**⚠️ CRITICAL**: nenhuma user story pode ser exercitada antes desta fase.

- [x] T002 Criar o esqueleto do componente em `frontend/src/pages/public/PlataformaPage.js` — **named export** `PlataformaPage`, com `PageBanner` (props `pageKey="plataforma"`, `badge`, `title`, `subtitle`, `icon` de `lucide-react`) e secções placeholder (introdução, capacidades, fecho) usando `.animate-fade-up` e tokens `grafite`/`carmesim`. Espelhar a estrutura de `frontend/src/pages/public/SobrePage.js`.
- [x] T003 Registar a rota **lazy** em `frontend/src/App.js` — adicionar `const PlataformaPage = lazy(() => import('./pages/public/PlataformaPage').then((m) => ({ default: m.PlataformaPage })));` junto aos restantes imports lazy (~L13–32) e `<Route path="/plataforma" element={<PublicLayout><PlataformaPage /></PublicLayout>} />` no bloco de rotas públicas de `AppRoutes()` (~L117–133). Depende de T002.

**Checkpoint**: `/plataforma` renderiza (ainda com conteúdo placeholder) dentro do `PublicLayout`.

---

## Phase 3: User Story 1 - Conhecer a plataforma a partir do rodapé (Priority: P1) 🎯 MVP

**Goal**: um visitante chega à landing por um link discreto no rodapé e vê uma página coerente (abertura + fecho) dentro do `PublicLayout`.

**Independent Test**: a partir de qualquer página pública, clicar no link discreto do rodapé navega em 1 clique para `/plataforma`, que renderiza com cabeçalho/rodapé e tom factual (cenários C1 + C2 do `quickstart.md`).

### Implementation for User Story 1

- [x] T004 [P] [US1] Adicionar o **link discreto** no rodapé em `frontend/src/layouts/PublicLayout.js` — na barra inferior (~L167–170, junto a "Política de Privacidade"), `<Link to="/plataforma">A plataforma</Link>` com estilo de baixa proeminência (`text-white/50 hover:text-white transition-colors text-xs sm:text-sm`). Ver `contracts/route.md`.
- [x] T005 [US1] Redigir e inserir a **secção de introdução** ("o que é a plataforma", PT-PT, factual) em `frontend/src/pages/public/PlataformaPage.js` — secção `py-12 sm:py-20 lg:py-24`, grelha `lg:grid-cols-2 gap-16 items-center`, `.animate-fade-up`.
- [x] T006 [US1] Redigir e inserir a **secção de fecho** institucional sóbria em `frontend/src/pages/public/PlataformaPage.js` — **sem** botão de ação primário comercial proeminente (FR-005). Depende de T005 (mesmo ficheiro).
- [x] T007 [US1] Verificar entrada ponta-a-ponta (C1 + C2): link do rodapé → `/plataforma` renderiza dentro do `PublicLayout`, sem recarregar (SPA).

**Checkpoint**: MVP funcional — entrada pelo rodapé + página com banner, introdução e fecho.

---

## Phase 4: User Story 2 - Compreender as capacidades/módulos (Priority: P2)

**Goal**: a página apresenta ≥ 5 capacidades/módulos reais do portal, descritos de forma factual.

**Independent Test**: percorrer a secção de capacidades e confirmar ≥ 5 módulos (título + descrição curta), sem números inventados nem preços (cenário C3).

### Implementation for User Story 2

- [x] T008 [US2] Definir a constante de **capacidades** (≥ 5 itens: gestão de sócios, quotas/finanças, transparência, eventos, votações/assembleias, comunicação) com `icon` (`lucide-react`), `title` e `desc` (PT-PT, factual) em `frontend/src/pages/public/PlataformaPage.js`. Ver `data-model.md`.
- [x] T009 [US2] Implementar a **secção de capacidades** em grelha de `card-technical card-hover p-4 sm:p-6` (ícone em caixa `bg-grafite`, título `text-grafite`, descrição `text-gray-600`) em `frontend/src/pages/public/PlataformaPage.js`. Depende de T008 (mesmo ficheiro).
- [x] T010 [US2] Verificar conteúdo (C3): ≥ 5 capacidades e ausência de números/estatísticas não oficiais, preços ou promessas (FR-009 / regra editorial).

**Checkpoint**: US1 + US2 funcionam de forma independente; a página está substancialmente completa.

---

## Phase 5: User Story 3 - Experiência responsiva e de marca (Priority: P3)

**Goal**: página totalmente responsiva e alinhada com o sistema de design ACCTA.

**Independent Test**: testar larguras 360/768/1024/1440px (sem overflow horizontal) e auditar tokens de marca (cenário C5).

### Implementation for User Story 3

- [x] T011 [US3] Passagem de **responsividade** em `frontend/src/pages/public/PlataformaPage.js` — secções empilham (`grid-cols-1` → `lg:grid-cols-2`), espaçamentos `py-12 sm:py-20`, sem overflow horizontal de 360px a 1440px (SC-003).
- [x] T012 [US3] **Auditoria de marca** em `frontend/src/pages/public/PlataformaPage.js` — tokens `carmesim`/`grafite`/`floresta` corretos, Open Sans herdado do layout, **sem dark mode**, `grep` por `style={{` = 0 (sem inline styles). Gate da skill `frontend-design` (Constituição V); ver `contracts/ui-page.md`.

**Checkpoint**: todas as user stories funcionam de forma independente e prontas para revisão.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: gates de qualidade e validação final.

- [x] T013 [P] (Opcional) Definir `document.title` por `useEffect` em `frontend/src/pages/public/PlataformaPage.js` (SEO best-effort; o site não usa `react-helmet`).
- [x] T014 Lint: `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60` sem novos avisos acima do limite (SC-005).
- [x] T015 Build: `cd frontend && yarn build` conclui com sucesso (SC-005).
- [x] T016 Validação completa do `quickstart.md` (C1–C5) no browser, mobile e desktop, + verificação manual (Constituição VII).
- [x] T017 Commit em Conventional Commits com scope (`feat(frontend): landing page da plataforma + link no rodapé`) e abrir PR para `develop` (GitFlow). Registar correções em `tasks/lessons.md` se aplicável. — Feito: commit `1713b0c` → PR #334 → develop (`f669a5d`); RELEASED v0.5.32 e em prod (`controlador.cv/plataforma` 200). Follow-up: "A Plataforma" na navegação pública (PR #337, RELEASED v0.5.33).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: depende do Setup; **bloqueia** todas as user stories. T003 depende de T002.
- **User Stories (Phase 3–5)**: dependem do Foundational. Em priorização P1 → P2 → P3.
- **Polish (Phase 6)**: depois das user stories desejadas.

### User Story Dependencies

- **US1 (P1)**: arranca após Foundational. Independentemente testável (entrada + shell de conteúdo).
- **US2 (P2)**: arranca após Foundational. Edita o mesmo ficheiro da página — fazer após US1 para evitar conflitos no `PlataformaPage.js`.
- **US3 (P3)**: passagem final de responsividade/marca sobre o conteúdo de US1+US2.

### Within Each User Story

- Tarefas no mesmo ficheiro (`PlataformaPage.js`) são **sequenciais** (sem `[P]`).
- T004 (footer, ficheiro diferente) é `[P]` relativamente a T005/T006.

### Parallel Opportunities

- T004 (`PublicLayout.js`) pode correr em paralelo com T005/T006 (`PlataformaPage.js`) — ficheiros diferentes.
- T013 (opcional) é independente das tarefas de gate T014/T015.
- A maioria das tarefas toca o mesmo ficheiro de página, pelo que o paralelismo é limitado (feature pequena, 3 ficheiros).

---

## Parallel Example: User Story 1

```bash
# Ficheiros diferentes — podem avançar em paralelo:
Task T004: "Adicionar link discreto no rodapé em frontend/src/layouts/PublicLayout.js"
Task T005: "Inserir secção de introdução em frontend/src/pages/public/PlataformaPage.js"
# (T006 depende de T005 — mesmo ficheiro — não paralelizar)
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1: Setup (T001)
2. Phase 2: Foundational (T002, T003) — **bloqueante**
3. Phase 3: User Story 1 (T004–T007)
4. **STOP e VALIDAR**: testar US1 (C1+C2) de forma independente
5. Demo se pronto

### Incremental Delivery

1. Setup + Foundational → fundação pronta
2. US1 → testar (C1+C2) → MVP
3. US2 → testar (C3) → página completa de conteúdo
4. US3 → testar (C5) → pronta para release
5. Polish (lint/build/quickstart) → PR para `develop`

---

## Notes

- Feature **frontend-only**: sem backend, sem DB, sem RBAC, sem novas dependências npm.
- `[P]` = ficheiros diferentes, sem dependências.
- Validar no browser antes de marcar "done" (Constituição VII).
- Commit por tarefa ou grupo lógico; PR para `develop` (nunca `main` direto).
- Evitar: números/estatísticas não oficiais, CTA comercial forte, inline styles, dark mode.
