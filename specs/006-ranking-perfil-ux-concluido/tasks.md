---
description: "Task list — Revisão do Ranking e do Perfil"
---

# Tasks: Revisão do Ranking e do Perfil

**Input**: Design documents from `/specs/006-ranking-perfil-ux/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ (N/A)

**Tests**: NÃO solicitados. É uma feature de UI — a verificação é em **navegador**
nas larguras-alvo (Princípio VII), guiada por `quickstart.md`. Sem suite automática
nova (nada de backend muda).

**Organização**: por user story. Esta feature é **frontend-only, zero deps novas,
zero backend**.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode correr em paralelo (ficheiro diferente, sem dependências)
- **[Story]**: US1…US5 (mapeia spec.md)

## ⚠️ Sobreposição de ficheiros (ler antes de paralelizar)

- `frontend/src/pages/private/RankingPage.js` — tocado por **US1, US2, US3** → tarefas
  nesse ficheiro são **sequenciais entre si** (não [P] umas com as outras).
- `frontend/src/pages/private/dashboard/RankingTopN.js` — tocado por **US2, US3**.
- `frontend/src/components/NotificationBell.js` — só **US4** → [P] com tudo o resto.
- `frontend/src/pages/private/perfil/DetailsGrid.js` e
  `frontend/src/pages/private/PerfilPage.js` (este **fora** de `perfil/`) — só **US5**
  → [P] com tudo o resto.

Ordem recomendada nos ficheiros partilhados: **US1 → US2 → US3** (layout, depois
distinção, depois avatares). US4 e US5 correm em paralelo a qualquer momento.

---

## Phase 1: Setup

**Purpose**: arrancar o ambiente e ancorar o estado atual.

- [X] T001 Arrancar o dev server (`cd frontend && yarn start`) e abrir, no DevTools
  responsivo a 360/390/414/768/1024/1440px, `/ranking`, `/dashboard`, `/perfil` e o
  painel de notificações — registar o estado atual (baseline) para comparar no fim
  (`specs/006-ranking-perfil-ux/quickstart.md`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: pré-requisitos transversais.

- Nenhuma tarefa foundational. A feature reutiliza componentes existentes
  (`UserAvatar`, shadcn/ui, `mediaUrl`) e não introduz infraestrutura partilhada,
  schema, auth ou modelos. As user stories podem começar diretamente.

**Checkpoint**: pode iniciar-se qualquer user story.

---

## Phase 3: User Story 1 — Ranking responsivo no telemóvel (Priority: P1) 🎯 MVP

**Goal**: `/ranking` sem layout partido/distorção em ecrãs estreitos, sem regressão
no desktop/tablet.

**Independent Test**: abrir `/ranking` a 360/390/414px (como sócio **e** como gestor)
e confirmar que pódio, "A minha posição", tabela e paginação ficam contidos, sem
sobreposição nem corte horizontal indevido; desktop inalterado. (SC-001, SC-006)

- [X] T002 [US1] Reproduzir a 360/390/414px e **identificar o(s) elemento(s) que
  transbordam** em `frontend/src/pages/private/RankingPage.js` (suspeitos em
  research.md D1: barra de ações do cabeçalho `flex … flex-wrap` ~linha 241; tabela
  `overflow-x-auto` ~400; pódio `sm:-mt-2` ~353). Anotar a causa raiz antes de editar.
- [X] T003 [US1] Corrigir a **barra de ações do cabeçalho** em `RankingPage.js` para
  empilhar/quebrar corretamente no telemóvel (PeriodToggle + Definições + Registar
  ajuste + Recalcular nos perfis de gestor) sem empurrar a largura da página.
- [X] T004 [US1] Garantir o comportamento responsivo do **pódio Top-3**, da caixa
  **"A minha posição"** e da **tabela/paginação** em `RankingPage.js` (truncagem
  intencional de nomes/cargos longos; scroll da tabela contido e legível; sem vazar
  `-mt`/padding). Correção na origem — **não** mascarar com `overflow-hidden` global.
- [X] T005 [US1] Verificar em navegador a 360/390/414/768/1024/1440px, sócio e gestor,
  conforme `quickstart.md` (US1). Confirmar zero regressão desktop/tablet. (SC-001, SC-006)

**Checkpoint**: US1 funcional e testável de forma independente (MVP).

---

## Phase 4: User Story 2 — Distinção 1.º/2.º/3.º (Priority: P2)

**Goal**: 1.º/2.º/3.º com destaque distinto entre si — **1.º Carmesim (coroa), 2.º
Grafite (medalha), 3.º muted (medalha)** — + ordinal; 4.º+ mostra número. Consistente
no `/ranking` e no widget do dashboard. (Decisão D2 — sem metálicos.)

**Independent Test**: com ≥3 membros, em `/ranking` e `/dashboard`, identificar 1/2/3
ao relance (Carmesim→Grafite→muted) com ícone+número; <3 membros adapta sem partir.
(SC-002, FR-003, FR-005)

- [X] T006 [P] [US2] Criar componente partilhado **`RankBadge`** em
  `frontend/src/components/RankBadge.js` (fonte única, evita drift entre as duas
  superfícies): 1.º Coroa `text-carmesim`, 2.º Medalha `text-grafite`, 3.º Medalha
  `text-[#6B7280]`, 4.º+ número ordinal mono; ícone + número sempre presentes
  (acessível, nunca só por cor). Reusar lucide `Crown`/`Medal`.
- [X] T007 [US2] Substituir o `RankBadge` local de `RankingPage.js` (~linhas 43-48) pelo
  componente partilhado e aplicar a ênfase distinta de 2.º/3.º também no **pódio**
  (`ranking-podium`), preservando o realce Carmesim do 1.º.
- [X] T008 [US2] Atualizar a lógica de medalha inline de
  `frontend/src/pages/private/dashboard/RankingTopN.js` (~linhas 51-60 e a barra
  `~70`) para usar `RankBadge` partilhado — corrigir o caso atual em que **2.º e 3.º
  ficam ambos muted** (passar 2.º a Grafite).
- [X] T009 [US2] Verificar em navegador (`/ranking` + `/dashboard`) com ≥3 e com <3
  membros, conforme `quickstart.md` (US2). Confirmar acessibilidade (número+ícone). (SC-002)

---

## Phase 5: User Story 3 — Fotos dos sócios no ranking (Priority: P2)

**Goal**: cada entrada (pódio + tabela + widget) mostra a foto do sócio via
`UserAvatar`, com iniciais como fallback; opt-out continua não reexposto.

**Independent Test**: sócio com foto → foto; sócio sem foto → iniciais; zero imagens
quebradas; sócio em opt-out não aparece nas listas públicas. (SC-003, FR-006/7/8)

> Depende de tocar nos mesmos ficheiros que US2 → fazer **depois** de US2 em
> `RankingPage.js` e `RankingTopN.js`. `photo_url` já vem no payload (data-model.md).

- [X] T010 [US3] Adicionar `UserAvatar` (import de `frontend/src/components/UserAvatar`)
  às linhas do **pódio** e da **tabela** em `RankingPage.js`, passando
  `name={e.member_name}` e `photoUrl={e.photo_url}` (size maior no pódio, `xs`/`sm` na
  tabela). Não alterar a lógica de opt-out (já filtrada no servidor).
- [X] T011 [US3] Adicionar `UserAvatar` às linhas do widget
  `frontend/src/pages/private/dashboard/RankingTopN.js`, junto ao nome.
- [X] T012 [US3] Verificar em navegador (foto, fallback de iniciais, 404 sem imagem
  quebrada, opt-out oculto) conforme `quickstart.md` (US3). (SC-003)

---

## Phase 6: User Story 4 — Painel de notificações sem corte (Priority: P2)

**Goal**: o painel de notificações respeita margem nos **dois** bordos no telemóvel,
sem cortar conteúdo; desktop mantém alinhamento ao sino.

**Independent Test**: a 360/390/414px, abrir o painel em qualquer página → margem nos
dois lados, sem corte; desktop sem regressão. (SC-004, SC-006)

> Ficheiro independente → pode correr em paralelo com US1/US2/US3/US5.

- [X] T013 [P] [US4] Corrigir o posicionamento do painel em
  `frontend/src/components/NotificationBell.js` (~linha 72, `absolute right-0 …
  w-[400px] max-w-[90vw]`) para garantir margem mínima de **16px em ambos** os bordos
  no telemóvel sem ultrapassar a viewport (research.md D4), mantendo o padrão de
  montagem/animação (delayed-unmount) e o backdrop intactos.
- [X] T014 [US4] Verificar em navegador a 360/390/414px (painel sem corte, margem ≥16px
  dos dois lados) e em desktop (alinhamento ao sino), conforme `quickstart.md` (US4). (SC-004, SC-006)

---

## Phase 7: User Story 5 — Perfil: editável vs. gerido (Priority: P3)

**Goal**: fronteira óbvia entre campos de autosserviço (editáveis) e campos de
identidade/associação (geridos por admin); estes marcados como não-editáveis com
indicação de como alterá-los. Email permanece admin-only (Q1). Sem novos campos.

**Independent Test**: como sócio, editar e gravar todos os campos de autosserviço;
Email/N.º Sócio/Cargo/Função/Estado/Categoria/Admissão claramente não-editáveis com
indicação. (SC-005, FR-012/13)

> Ficheiros independentes → paralelo com o resto.

- [X] T015 [P] [US5] Em `frontend/src/pages/private/perfil/DetailsGrid.js`, marcar
  visualmente os campos **geridos pela associação** (Email, N.º Sócio, Cargo, Função,
  Categoria, Admissão) como não-editáveis e tornar óbvia a fronteira vs. os dados de
  autosserviço (ex.: rótulo/affordance "gerido pela administração"), dentro do sistema
  de design ACCTA (neutral-led; sem inventar tokens).
- [X] T016 [US5] Se necessário para a clareza da fronteira, reforçar a indicação na
  `frontend/src/pages/private/PerfilPage.js` (ex.: microcópia junto ao botão
  Editar a explicar o que é editável). Manter mínimo — não duplicar o `DetailsGrid`.
- [X] T017 [US5] Verificar em navegador: editar → gravar todos os campos de
  autosserviço; campos geridos aparecem não-editáveis com indicação, conforme
  `quickstart.md` (US5). (SC-005)

---

## Phase 8: Polish & Cross-Cutting

- [X] T018 [P] Lint: `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60`
  (resolver qualquer aviso novo introduzido).
- [X] T019 Execução completa do `quickstart.md` (SC-001…SC-006) nas larguras-alvo,
  sócio e gestor; confirmar zero regressão desktop/tablet e conformidade com a design
  system (Carmesim acento único, sem metálicos, sem dark mode).
- [X] T020 Atualizar `tasks/lessons.md` e a memória relevante se surgir alguma correção
  do dono durante a verificação (Princípio VII).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: vazia → não bloqueia.
- **User Stories (Phase 3-7)**: começam após Setup.
- **Polish (Phase 8)**: depois das stories desejadas.

### User Story Dependencies

- **US1 (P1)**: independente. **MVP.**
- **US2 (P2)**: independente em comportamento, mas **edita os mesmos ficheiros que US1/US3**
  → no `RankingPage.js`/`RankingTopN.js` correr **após US1**.
- **US3 (P2)**: independente em comportamento; **após US2** nos ficheiros partilhados.
- **US4 (P2)**: totalmente independente (NotificationBell.js) → paralelo.
- **US5 (P3)**: totalmente independente (perfil/) → paralelo.

### Within Each User Story

- Models→services→endpoints: **N/A** (frontend-only).
- Reproduzir/identificar → corrigir na origem → verificar em navegador.

### Parallel Opportunities

- **US4 (T013-T014)** e **US5 (T015-T017)** podem correr em paralelo com toda a linha
  do Ranking (US1→US2→US3), por serem ficheiros distintos.
- **T006** (criar `RankBadge`) é [P]: ficheiro novo, sem dependências.
- Dentro do Ranking, US1→US2→US3 são **sequenciais** nos ficheiros partilhados.

---

## Parallel Example

```bash
# Trilhos independentes (ficheiros distintos) — podem avançar ao mesmo tempo:
Trilho A (Ranking, sequencial):  US1 (T002-T005) → US2 (T006-T009) → US3 (T010-T012)
Trilho B (Notificações):         US4 (T013-T014)
Trilho C (Perfil):               US5 (T015-T017)
# Convergem no Polish (T018-T020).
```

---

## Implementation Strategy

### MVP First (US1)

1. Phase 1 (Setup) → 2. Phase 2 (vazia) → 3. Phase 3 (US1) → **validar `/ranking`
   no telemóvel** → demo/PR se pronto.

### Incremental Delivery

US1 (MVP) → US2 → US3 (Ranking completo) → US4 (notificações) → US5 (perfil) → Polish.
Cada incremento é mergeável e verificável isoladamente em navegador.

---

## Notes

- Feature **frontend-only**: sem backend, sem API/contratos, sem migrações, **sem Via B**
  (o delta não toca `backend/`).
- Zero dependências novas (reusa `UserAvatar`, shadcn/ui, lucide, `mediaUrl`).
- Sem testes automáticos novos — verificação em navegador (Princípio VII) via `quickstart.md`.
- Design: Carmesim acento único, sem metálicos (D2), sem dark mode; PT em todo o texto.
- Commit por tarefa/grupo lógico (Conventional Commits com escopo, ex.: `fix(ranking): …`,
  `feat(perfil): …`). PR para `develop` (GitFlow).
