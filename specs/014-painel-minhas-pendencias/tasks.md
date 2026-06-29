# Tasks: Painel «As minhas pendências»

**Feature**: `specs/014-painel-minhas-pendencias/` · **Branch**: `feature/painel-minhas-pendencias`
**Input**: [plan.md](plan.md) · [spec.md](spec.md) · [research.md](research.md) · [data-model.md](data-model.md) · [contracts/pendencias-ui.md](contracts/pendencias-ui.md) · [quickstart.md](quickstart.md)

> **Frontend-only, ZERO backend** (achado do plano: só admin/Direção propõem/veem Atos ⇒ as
> secções de Atos usam os endpoints já existentes; sócio comum vê votações+eventos). Página
> dedicada `/pendencias`, **role-aware**, tudo **derivado** dos reads existentes via TanStack
> Query. **Sem Via B** — entrega pela Vercel no push a `main`. Aplicar o skill `frontend-design`.

## Phase 1: Setup

- [ ] T001 Confirmar a branch `feature/painel-minhas-pendencias` ativa; **não tocar `backend/`**; zero deps novas. Confirmar que `frontend/src/utils/api.js` expõe `atosAPI` (com `list({status, pendentes_para_mim})`), `pollsAPI` e `eventsAPI`, e que `frontend/src/lib/queryClient.js` tem `queryKeys` para events/polls (criar chaves em falta seguindo o padrão existente, ex.: `queryKeys.atos`, `queryKeys.polls`).

## Phase 2: Foundational (bloqueia as user stories)

- [ ] T002 Esqueleto partilhado: criar `frontend/src/pages/private/PendenciasPage.js` (shell com título "As minhas pendências" + container); adicionar a **rota lazy** `/pendencias` em `frontend/src/App.js` (padrão `lazy(() => import('./pages/private/PendenciasPage').then(m => ({ default: m.PendenciasPage })))`, dentro de `ProtectedRoute`, qualquer sócio autenticado); adicionar o **item de menu** "As minhas pendências" na sidebar do sócio em `frontend/src/layouts/PrivateLayout.js` (ícone lucide adequado).

## Phase 3: User Story 1 — Ver votações e eventos por agir num só sítio (P1) 🎯 MVP

**Goal**: um sócio comum abre `/pendencias` e vê, agrupadas e com contagem, as votações que lhe falta votar e os eventos por confirmar, cada item com ligação para agir.

**Independent Test**: sócio com 1 votação aberta por votar + 1 evento futuro por confirmar → ambos aparecem com ligação; depois de votar/confirmar, somem.

- [ ] T003 [US1] Em `frontend/src/pages/private/PendenciasPage.js`: secção **"Votações por votar"** via `useQuery` sobre `pollsAPI` (read existente), derivando `polls.filter(p => p.status === 'aberta' && !p.has_voted)` e só para **membro votante** (reutilizar a verificação de elegibilidade já usada na página de votações). Cada item com ligação para votar. Skeleton no loading; erro **isolado** à secção (não derruba a página).
- [ ] T004 [US1] Em `PendenciasPage.js`: secção **"Eventos por confirmar"** via `useQuery` sobre `eventsAPI` (`upcoming`), derivando `events.filter(e => !e.attendees?.includes(user.id) && futuro)`. Cada item com ligação para confirmar presença. Skeleton + erro isolado.
- [ ] T005 [US1] Em `PendenciasPage.js`: cabeçalho de cada secção com **contagem**; uma secção **sem itens não se mostra** (exceto o estado vazio global da US2). Aplicar o skill `frontend-design` (cartões neutros white/`#F5F5F5`, ligações Carmesim-on-white, **sem** vários botões primários, sem dark mode), texto **PT**, sem inadimplência.

**Checkpoint US1**: sócio vê e age sobre votações+eventos pendentes — MVP utilizável.

## Phase 4: User Story 2 — Estado vazio claro quando nada está pendente (P2)

**Goal**: quando nenhuma secção tem itens, o painel diz claramente "nada pendente".

**Independent Test**: sócio sem pendências → vê mensagem explícita de "tudo em dia", não secções vazias.

- [ ] T006 [US2] Em `PendenciasPage.js`: **estado vazio global** — se nenhuma secção (depois de carregadas) tem itens, mostrar uma mensagem clara e tranquilizadora ("Está tudo em dia — nada pendente"), com ícone; não mostrar secções vazias soltas.

**Checkpoint US2**: ciclo aviso→ação fechado; sem ambiguidade quando vazio.

## Phase 5: User Story 3 — (Direção) Atos no mesmo painel (P3)

**Goal**: membros da Direção veem também "Atos à minha assinatura" e "Atos que propus".

**Independent Test**: utilizador da Direção com 1 Ato por assinar e 1 que propôs (pendente) → vê as 2 secções; sócio comum **não** vê secções de Atos.

- [ ] T007 [US3] Em `PendenciasPage.js`: **só se** o utilizador for Direção/admin (reutilizar a verificação de papel que a `CoAprovacoesPage` já usa — `AuthContext`/`user.role`/órgão), secção **"Atos à minha assinatura"** via `atosAPI.list({ pendentes_para_mim: true })`, ligação para assinar. **Não** chamar `GET /atos` para um sócio comum (evita o 403 de `_require_view`).
- [ ] T008 [US3] Em `PendenciasPage.js`: secção **"Atos que propus"** via `atosAPI.list({ status: 'pendente' })` derivando `items.filter(a => a.created_by === user.id)`, ligação para ver o Ato. Também **só** Direção/admin (são os únicos que propõem/listam Atos).

**Checkpoint US3**: painel completo e role-aware.

## Phase 6: Polish & Cross-Cutting

- [ ] T009 [P] `cd frontend && npx eslint src/pages/private/PendenciasPage.js src/App.js src/layouts/PrivateLayout.js --max-warnings=0` limpo.
- [ ] T010 **Verificação em navegador** (preview Vercel da PR ou dev local), Cenários do [quickstart.md](quickstart.md): A (sócio: votações+eventos, sem secções de Atos), B (Direção: +2 secções de Atos), C (eleições/deliberações-secretas **não** aparecem), D (falha de um read degrada só a secção). Princípio VII (dono). **Frontend-only ⇒ Vercel, sem Via B.**

---

## Dependencies & Execution Order

- **Setup (T001)** → **Foundational (T002)** → **US1 (T003–T005)** → **US2 (T006)** → **US3 (T007–T008)** → **Polish (T009–T010)**.
- T003–T008 editam o **mesmo ficheiro** (`PendenciasPage.js`) ⇒ sequenciais entre si; dependem do esqueleto T002.
- US1 é independentemente entregável (sócio comum já tem valor) sem US2/US3.

## Parallel Opportunities

- Pouca: um ficheiro de página central (edições sequenciais). **T009** (lint) paraleliza no fim. As 4 `useQuery` correm em paralelo **em runtime** (não são tarefas).

## Implementation Strategy

- **MVP = US1 (T001–T005)**: sócio vê e age sobre votações+eventos — valor central, entregável sozinho.
- **US2 (T006)**: estado vazio (qualidade/clareza).
- **US3 (T007–T008)**: conveniência para a Direção (reutiliza endpoints existentes).
- **Polish (T009–T010)**: lint + validação em navegador.

## Notas / Follow-ups (fora do âmbito frontend-only)

- **Re-apontar as ligações dos avisos das specs 010–013** (hoje `/financeiro/co-aprovacoes`) para `/pendencias`: tocaria `backend/routes/atos.py` (`_LINK`) ⇒ exigiria **Via B**. Fica como **follow-up backend separado**, não no MVP desta feature.

## Format Validation

Todas as tarefas seguem `- [ ] [TaskID] [P?] [Story?] descrição com caminho`. Setup/Foundational/Polish sem label; US1/US2/US3 com label; caminhos de ficheiro explícitos.
