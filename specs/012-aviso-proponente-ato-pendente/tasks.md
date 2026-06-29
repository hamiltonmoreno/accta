# Tasks: Lembrete de Ato pendente ao próprio proponente

**Feature**: `specs/012-aviso-proponente-ato-pendente/` · **Branch**: `feature/aviso-proponente-ato-pendente`
**Input**: [plan.md](plan.md) · [spec.md](spec.md) · [research.md](research.md) · [data-model.md](data-model.md) · [contracts/sweep-extension.md](contracts/sweep-extension.md) · [quickstart.md](quickstart.md)

> Desenho minimalíssimo: estender `_notify_overdue_atos_locked()` (spec 010) para também
> avisar o `created_by` — **só se não for já destinatário Direção** (dedup; spec 010
> intacta) e for conta ativa/não-técnica. **Partilha a marca `overdue_notified_at`**
> (uma única vez, Q1=A). **Sem schema/migração/agendador/limiar/campo novos, zero deps,
> sem frontend.** Toca `backend/` ⇒ release `develop→main` exigirá **Via B**.

## Phase 1: Setup

- [x] T001 Confirmar a branch `feature/aviso-proponente-ato-pendente` ativa e que NÃO se adicionam dependências (não tocar `backend/requirements.txt`); confirmar que não há mudanças de schema/modelos (reutiliza `Ato.overdue_notified_at` da spec 010).

## Phase 2: Foundational (bloqueia as user stories)

- Nenhuma. Sem prerequisito bloqueante: a marca de idempotência (`Ato.overdue_notified_at`), o limiar X (`ato_overdue_dias`), o agendador diário e o `_overdue_lock` **já existem** da spec 010.

## Phase 3: User Story 1 — Proponente é avisado de que o seu Ato está parado (P1) 🎯 MVP

**Goal**: no varrimento diário existente, avisar o proponente (`created_by`) de um Ato pendente > X dias, uma única vez, sem duplicar com a Direção e sem alterar o aviso à Direção.

**Independent Test**: criar um Ato, deixá-lo pendente > X dias → o proponente recebe um aviso (idade + link); um proponente-que-é-Direção recebe só um aviso.

- [x] T002 [US1] Em `backend/routes/atos.py` (`_notify_overdue_atos_locked`): após calcular `overdue` e `direcao_ids`, apurar `eligible_proponentes` com **uma** query a `db.users` para o conjunto distinto de `created_by` dos Atos overdue — elegível = `status == "ativo"` e `account_type != "technical"` (ausente ⇒ membro). Sem N+1. Inicializar `notified_proponentes: 0` no dict `counters`.
- [x] T003 [US1] Ainda no loop por Ato de `_notify_overdue_atos_locked`: manter o aviso à Direção **exatamente como está** (SC-004) e, a seguir, avisar o proponente **sse** `ato["created_by"] not in direcao_ids` **e** `ato["created_by"] in eligible_proponentes` — via `notify_users([created_by], "financeiro", "O seu ato continua pendente", mensagem_pt_com_idade_e_descricao, "/financeiro/co-aprovacoes")`; incrementar `counters["notified_proponentes"]`. Manter a regra «sem Direção ⇒ não marca» (a marca/aviso ao proponente não acontece quando não há destinatários Direção). Devolver `notified_proponentes` nos contadores.
- [x] T004 [US1] Estender `backend/tests/test_atos_overdue.py` (sem quebrar os casos da spec 010): (1) proponente sócio comum de Ato overdue → 1 aviso ao `created_by` (corpo com idade + link `/financeiro/co-aprovacoes`), `notified_proponentes == 1`; (2) **dedup** — proponente ∈ Direção → **sem** aviso de proponente (só o da Direção), `notified_proponentes == 0`; (3) proponente `inativo`/`technical` → não avisado, Direção avisada na mesma; (4) **idempotência** — 2.ª avaliação → `notified_atos == 0` e `notified_proponentes == 0`; (5) Ato fora de `pendente`/resolvido → nenhum aviso; (6) **spec 010 intacta** — a Direção continua a receber o mesmo aviso. Wirar `db.users` no `mock_db` se necessário (find que honre o filtro de elegibilidade). `cd backend && pytest tests/test_atos_overdue.py -q`.

**Checkpoint US1**: proponente avisado uma vez, com dedup e sem regressão da spec 010 — MVP entregue.

## Phase 4: Polish & Cross-Cutting

- [x] T005 [P] `cd backend && ruff check . && ruff format --check .` limpo nos ficheiros tocados.
- [x] T006 Correr a suite backend completa relevante `cd backend && pytest tests/test_atos_overdue.py tests/test_atos.py -q` sem regressões (em especial os casos da spec 010 e o fluxo de Atos).
- [ ] T007 Atualizar `tasks/todo.md` (secção de revisão) e, no fim e só após verificação, fechar a spec (renomear dir `-concluido`). Nota: toca `backend/` ⇒ release `develop→main` exige **Via B**; verificação prod = `POST /api/atos/notify-overdue` sem token → 401 (rota viva) + resposta inclui `notified_proponentes`. Validação funcional ponta-a-ponta (Cenário B, navegador) = Princípio VII (dono).

---

## Dependencies & Execution Order

- **Setup (T001)** → **US1 (T002 → T003 → T004)** → **Polish (T005–T007)**.
- **T002 → T003**: mesma função `_notify_overdue_atos_locked` (edições sequenciais; T003 usa `eligible_proponentes` e o counter de T002).
- **T004** depende de T002+T003 (testa o comportamento completo).
- Sem Phase 2 (nada bloqueante).

## Parallel Opportunities

- Praticamente nenhuma dentro do código (um único ficheiro de runtime, edições sequenciais). **T005** (lint) é paralelizável no fim. **T004** (testes) pode ser esboçado em paralelo com T003 mas só passa após T002+T003.

## Implementation Strategy

- **MVP = US1 (T001–T004)**: é a única story; entrega todo o valor (proponente avisado, com dedup, spec 010 intacta). Demonstrável e testável sozinho.
- **Polish (T005–T007)**: lint, suite verde, fecho/Via B.

## Format Validation

Todas as tarefas seguem `- [ ] [TaskID] [P?] [Story?] descrição com caminho`. Setup/Polish sem label; US1 com label; caminhos de ficheiro explícitos.
