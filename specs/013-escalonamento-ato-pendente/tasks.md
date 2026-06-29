# Tasks: Escalonamento de lembretes de Ato (Art. 54) pendente

**Feature**: `specs/013-escalonamento-ato-pendente/` · **Branch**: `feature/escalonamento-ato-pendente`
**Input**: [plan.md](plan.md) · [spec.md](spec.md) · [research.md](research.md) · [data-model.md](data-model.md) · [contracts/sweep-recurrence.md](contracts/sweep-recurrence.md) · [quickstart.md](quickstart.md)

> Desenho de **1 linha**: em `_notify_overdue_atos_locked()` (`routes/atos.py`) a marca
> `overdue_notified_at` passa de *flag* single-shot a **cursor "último lembrete"** — a query
> muda de `{"overdue_notified_at": None}` para `{"$or": [{… None}, {… {"$lte": now − X dias}}]}`.
> Todo o resto do loop (gate de idade, avisos Direção+proponente, dedup spec 012, exclusões,
> escrita `= now`) **já funciona** sem mudança. **Sem schema/migração/campo/dep/frontend.**
> Toca `backend/` ⇒ release `develop→main` exigirá **Via B**.

## Phase 1: Setup

- [ ] T001 Confirmar a branch `feature/escalonamento-ato-pendente` ativa; confirmar que NÃO se adicionam dependências (não tocar `backend/requirements.txt`) nem há mudanças de schema/modelos (reutiliza `Ato.overdue_notified_at` e `FinanceSettings.ato_overdue_dias` das specs 010/012).

## Phase 2: Foundational (bloqueia as user stories)

- Nenhuma. O **disparo diário** (`asyncio.create_task` no startup), o **lock** `_overdue_lock`, o **limiar X** (`_overdue_limiar_dias`/`ato_overdue_dias`), a **marca** `overdue_notified_at`, os **avisos** Direção+proponente e as **exclusões** já existem das specs 010/012.

## Phase 3: User Story 1 — O Ato encalhado continua a ser lembrado (P1) 🎯 MVP

**Goal**: tornar o varrimento diário **recorrente** — um Ato pendente além de X recebe novo lembrete a cada X dias, não só uma vez.

**Independent Test**: Ato pendente com a marca envelhecida ≥ X dias → recebe novo lembrete e a marca avança; Ato pendente sem marca → 1.º lembrete (= specs 010/012); Ato que sai de `pendente` → zero lembretes.

- [ ] T002 [US1] Em `backend/routes/atos.py` (`_notify_overdue_atos_locked`): mover o cálculo de `now`/`dias` para **antes** da query inicial e calcular `cutoff = (now - timedelta(days=dias)).isoformat()`; **substituir** o filtro `{"status": "pendente", "overdue_notified_at": None}` por `{"status": "pendente", "$or": [{"overdue_notified_at": None}, {"overdue_notified_at": {"$lte": cutoff}}]}`. Importar `timedelta` (de `datetime`) se ainda não estiver importado. Atualizar o comentário do bloco para explicar o cursor "último lembrete" (preservando a nota do match-por-`None`/chave-null da spec 010). **Não tocar** no gate de idade, nos avisos Direção+proponente, na dedup, nas exclusões, nem na escrita `overdue_notified_at = now`.
- [ ] T003 [US1] Estender `backend/tests/test_atos_overdue.py` (sem quebrar specs 010/012): primeiro, **estender a fake `_atos_coll`** para honrar o ramo `$or`/`$lte` (marca `None`/ausente OU string ISO ≤ cutoff). Casos: (1) **recorrência** — Ato pendente com `overdue_notified_at` de há > X dias → 1 lembrete, marca avança para "agora", `notified_atos == 1`; (2) **1.º aviso intacto** — Ato pendente sem marca, idade > X → lembrete (Direção+proponente), `notified_atos == 1`; (3) **paragem por decisão** — Ato `aprovado` com marca antiga → **zero** lembretes. `cd backend && pytest tests/test_atos_overdue.py -q`.

**Checkpoint US1**: recorrência a cada X dias entregue, com o 1.º aviso e a paragem corretos — MVP.

## Phase 4: User Story 2 — A pressão aumenta com o tempo parado (P2)

**Goal**: o lembrete recorrente comunica a urgência crescente pela **antiguidade atualizada**, mantendo **os mesmos destinatários** (sem alargar a outros órgãos).

**Independent Test**: um lembrete recorrente de um Ato muito atrasado mostra a antiguidade (maior) no corpo, e os destinatários continuam a ser só Direção + proponente.

- [ ] T004 [US2] Em `backend/tests/test_atos_overdue.py`: caso que verifica que o corpo do lembrete recorrente reflete a **antiguidade atual** (ex.: Ato parado há 30 dias → "30 dias" no corpo) e que os destinatários se mantêm **Direção + proponente** (nenhum aviso a outros órgãos). Sem código novo — valida o comportamento do código de US1 sob recorrência (FR-005).

**Checkpoint US2**: a urgência cresce com a idade, sem escalonamento de destinatários.

## Phase 5: User Story 3 — O follow-up não vira spam (P3)

**Goal**: garantir o anti-spam — no máximo um lembrete por Ato por janela de X dias (nunca diário, sem teto artificial).

**Independent Test**: um Ato com marca recente (< X dias) não qualifica; dois varrimentos a < X dias de intervalo geram só um lembrete.

- [ ] T005 [US3] Em `backend/tests/test_atos_overdue.py`: casos (1) **anti-spam** — Ato pendente com `overdue_notified_at` de há < X dias → **não** qualifica (`notified_atos == 0`); (2) **cadência** — dois disparos sucessivos sem o cursor passar X dias → só **um** lembrete; só quando o cursor passa X dias é que o segundo dispara (SC-002/SC-005). Sem código novo — propriedade do filtro de US1.

**Checkpoint US3**: cadência de X dias comprovada; sem spam diário.

## Phase 6: Polish & Cross-Cutting

- [ ] T006 [P] `cd backend && ruff check routes/atos.py tests/test_atos_overdue.py && ruff format --check routes/atos.py tests/test_atos_overdue.py` limpo.
- [ ] T007 `cd backend && pytest tests/test_atos_overdue.py tests/test_atos.py -q` sem regressões (em especial os casos das specs 010 e 012 e o fluxo de Atos).
- [ ] T008 Atualizar `tasks/todo.md` (secção de revisão) e, só após verificação, deixar pronto para PR → `develop`. Nota: toca `backend/` ⇒ release `develop→main` exige **Via B**; prova decisiva prod = `POST /api/atos/notify-overdue` sem token → 401 (rota viva) + a resposta do disparo reflete os lembretes recorrentes. Fechar a spec (`-concluido`) só após RELEASED+deployed. Validação funcional ponta-a-ponta (2 janelas de X) = Princípio VII (dono).

---

## Dependencies & Execution Order

- **Setup (T001)** → **US1 (T002 → T003)** → **US2 (T004)** → **US3 (T005)** → **Polish (T006–T008)**.
- **T002** é o único task de código; **T003/T004/T005** dependem de T002 (testam o comportamento do filtro novo) e partilham o mesmo ficheiro de teso (edições sequenciais no `test_atos_overdue.py`).
- Sem Phase 2 (nada bloqueante).

## Parallel Opportunities

- Praticamente nenhuma: um único ficheiro de runtime e um único ficheiro de teste (edições sequenciais). **T006** (lint) é paralelizável no fim.

## Implementation Strategy

- **MVP = US1 (T001–T003)**: entrega a recorrência (o valor central). US2 e US3 são **test-only** (pinam propriedades já garantidas pela mudança de filtro de US1): a antiguidade crescente (US2) e o anti-spam/cadência (US3).
- **Polish (T006–T008)**: lint, suite verde sem regressão das specs 010/012, e preparação de PR/Via B.

## Format Validation

Todas as tarefas seguem `- [ ] [TaskID] [P?] [Story?] descrição com caminho`. Setup/Polish sem label de story; US1/US2/US3 com label; caminhos de ficheiro explícitos.
