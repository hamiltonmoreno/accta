# Tasks: Pendências v2 — contador no menu + avisos apontam ao painel

**Feature**: `015-pendencias-contador-avisos` | **Branch**: `feature/pendencias-contador-avisos`
**Input**: spec.md, plan.md, research.md, data-model.md, contracts/pendencias-contract.md, quickstart.md

> Estado: **IMPLEMENTADA** — todas as tarefas concluídas e verificadas (pytest Atos 67 verdes,
> `craco build` OK, eslint limpo). Marcadas `[X]`. Validação ponta-a-ponta no navegador (US1/US2)
> = Princípio VII, critério do dono (quickstart.md).

## Phase 1: Setup

- [X] T001 Confirmar artefactos da feature (spec/plan/research/data-model/contracts/quickstart) e branch `feature/pendencias-contador-avisos`. Zero dependências novas (plan.md §Technical Context).

## Phase 2: Foundational (bloqueia US1)

- [X] T002 [US1] Criar o hook partilhado `frontend/src/hooks/usePendencias.js` — fonte única da derivação role-aware (4 `useQuery` com os `queryKeys` existentes `polls.list`/`events.upcoming`/`atos.list({mine})`/`atos.list({status:'pendente'})`, Atos com `enabled: isDir`; filtros cliente idênticos; devolve `{votacoes, eventos, assinaturaItems, propostosItems, total, isLoading, anyError, isDir}`). Garante SC-002 (contador ≡ painel) e C3 (zero 403, zero voto secreto, `anyError` preservado).

## Phase 3: User Story 1 — Contador no menu (P1/MVP)

**Goal**: o sócio vê quantas pendências tem sem abrir a página. **Independent test**: quickstart cenários 1–5.

- [X] T003 [US1] Refatorar `frontend/src/pages/private/PendenciasPage.js` para consumir `usePendencias()` (remover a derivação inline `useQuery`/filtros/`total`; manter `sections` + JSX + banner `anyError`).
- [X] T004 [US1] Em `frontend/src/layouts/PrivateLayout.js`: adicionar `badge: 'pendencias'` ao item `/pendencias`; chamar `usePendencias()` para `pendenciasCount`; novo ramo de render espelhando o badge `'registration'` (bolha carmesim; ponto no colapsado), escondido a 0 (FR-004), cap `"9+"` (FR-003), `aria-label` PT.

## Phase 4: User Story 2 — Avisos de Ato pendente → painel (P2)

**Goal**: o aviso de um Ato pendente leva a `/pendencias`; o de um Ato decidido não. **Independent test**: quickstart cenários 6–7 + pytest.

- [X] T005 [US2] Em `backend/routes/atos.py`: adicionar `_LINK_PENDENTE = "/pendencias"`; aplicar **só** aos 3 sites pendentes (`create_ato`; varrimento Direção; varrimento proponente). Manter `_LINK` nos 2 decididos (`sign_ato`, `execute_ato`). C2 (não é swap cego).
- [X] T006 [P] [US2] Testes do contrato de link em `backend/tests/test_atos.py` (criação → `_LINK_PENDENTE`), `test_atos_overdue.py` (Direção + proponente atrasados → `_LINK_PENDENTE`) e `test_atos_rejeicao_motivo.py` (rejeição decidida mantém `_LINK`).

## Phase 5: Polish & Cross-Cutting

- [X] T007 Correção incidental: `PendenciasPage.js` importava `framer-motion` (removido do projeto em `b84c832`, build de v0.5.45 falhava) — substituído o `<motion.div>` por `<div className="animate-fadeIn">` (keyframe existente em `src/index.css`). Repara o `/pendencias` da spec 014.
- [X] T008 Verificação: `pytest tests/test_atos.py tests/test_atos_overdue.py tests/test_atos_rejeicao_motivo.py` (67 verdes); `craco build` OK; `eslint` limpo nos ficheiros tocados.
- [ ] T009 Validação ponta-a-ponta no navegador (Princípio VII — dono): quickstart cenários 1–8 (contador ≡ painel, "9+", desaparece a 0, avisos pendentes→/pendencias, decididos→co-aprovações, sem 403, sem atraso na sidebar).

## Dependencies

- T002 (hook) bloqueia T003 e T004 (US1).
- US2 (T005/T006) é **independente** de US1 (backend puro).
- T007 é independente (mesmo ficheiro de T003).

## Parallel opportunities

- T006 [P] corre em paralelo com a edição frontend (ficheiros distintos).
- US1 (frontend) e US2 (backend) podiam ir em PRs separados; aqui vão no mesmo branch.

## MVP scope

US1 (contador) entrega valor sozinha. US2 fecha o ciclo aviso→ação.
