---
description: "Task list — Aviso à Direção de Ato pendente há mais de X dias"
---

# Tasks: Aviso à Direção de Ato (Art. 54) pendente há mais de X dias

**Input**: Design documents from `specs/010-aviso-deliberacao-pendente/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: INCLUÍDOS — o quickstart (Cenário A) enumera os casos pytest e o Princípio VII exige testes
para mudanças de backend.

**Organization**: Tarefas agrupadas por user story. Feature **backend-only**, zero deps novas.
Branch: `feature/aviso-deliberacao-pendente`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode correr em paralelo (ficheiro diferente, sem dependência por concluir)
- Caminhos relativos à raiz do repo (git root = `accta-main/accta/`)

---

## Phase 1: Setup

**Purpose**: Projeto existente — nada a inicializar.

- [x] T001 Confirmar branch `feature/aviso-deliberacao-pendente` ativa e que NÃO há deps novas (não tocar `backend/requirements.txt`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Campos aditivos nos modelos existentes — pré-requisito de todas as stories. Aditivos e
retrocompatíveis (docs antigos sem o campo ⇒ default/None), portanto **sem migração** e sem STOP condition.

- [x] T002 [P] Adicionar campo aditivo `overdue_notified_at: Optional[str] = None` à `class Ato` em `backend/models.py` (marca de "já avisado", FR-005; comentário PT a explicar idempotência).
- [x] T003 [P] Adicionar campo aditivo `ato_overdue_dias: int = 7` à `class FinanceSettings` em `backend/models.py` (limiar X, default 7 — FR-004).

**Checkpoint**: modelos aceitam os novos campos; suite existente continua verde (`cd backend && pytest -q`).

---

## Phase 3: User Story 1 — Direção é avisada de pendências paradas (P1) 🎯 MVP

**Goal**: Atos `pendente` há > X dias geram **um** aviso in-app (+push) a cada membro da Direção, com
título/descrição/antiguidade e link `/financeiro/co-aprovacoes`; abrir leva à página para agir.

**Independent Test**: Cenário B do quickstart — com um Ato pendente mais velho que X, disparar
`notify_overdue_atos()` (via endpoint manual ou teste) e confirmar que a Direção recebe o aviso e que o
Ato fica com `overdue_notified_at`.

- [x] T004 [US1] Implementar `notify_overdue_atos()` em `backend/routes/atos.py`: ler `ato_overdue_dias` de `finance_settings` (default 7); `find` Atos `status=="pendente"` **sem** `overdue_notified_at`; parse defensivo de `created_at` (inválido/ausente ⇒ skip, FR edge); filtrar idade > X dias (comentar: `(now - created_at).days` trunca para dias inteiros, logo `> X` dispara a partir de X+1 dias completos — semântica desejada de "mais de X"); devolver/contabilizar `evaluated/overdue/notified_atos/recipients`. Sem SQL em rota; via DAO. Não levanta para fora (loop non-fatal).
- [x] T005 [US1] No `notify_overdue_atos()`, resolver destinatários com `members_of_orgao("direcao")` (exclui técnicos/inativos — FR-007) e, por cada Ato qualificado **com** destinatários, chamar `notify_users(direcao_ids, "financeiro", titulo_pt, mensagem_pt, "/financeiro/co-aprovacoes")` com título legível + descrição/tipo/valor + antiguidade em dias (FR-003/FR-008). Lista vazia ⇒ no-op sem erro e **sem** gravar a marca (FR-009; ver nota em contracts).
- [x] T006 [US1] Após avisar, gravar `overdue_notified_at = datetime.now(timezone.utc).isoformat()` no Ato via `db.atos.update_one(...)` (idempotência FR-005).
- [x] T007 [US1] Engatar o agendador: `overdue_atos_loop()` (sleep ~24h → `notify_overdue_atos()` em `try/except` com log; repete) em `backend/routes/atos.py`, e `asyncio.create_task(overdue_atos_loop())` no `@app.on_event("startup")` de `backend/server.py` (padrão non-fatal dos seeds existentes; log de arranque do loop).

**Checkpoint**: US1 entregue — MVP funcional. Atos atrasados avisam a Direção uma vez, automaticamente.

---

## Phase 4: User Story 2 — Administração define o limiar X (P2)

**Goal**: Admin altera X nas definições; avaliações seguintes usam o novo valor; default 7 quando nunca configurado.

**Independent Test**: `PATCH /api/finances/settings {"ato_overdue_dias": N}` (admin) e confirmar que
`GET /api/finances/settings` devolve N e que o varrimento passa a usar N (Cenário B passo 1).

- [x] T008 [US2] Adicionar `ato_overdue_dias: Optional[int] = None` à `class FinanceSettingsUpdate` em `backend/models.py` (PATCH parcial — só grava não-`None`).
- [x] T009 [US2] Em `backend/routes/finances.py` (handler `PATCH /settings`, admin-only existente): garantir que `ato_overdue_dias` é aceite/persistido e validar fronteira `>= 1` (HTTP 400 PT se inválido). Sem novo endpoint.

**Checkpoint**: X configurável; US1 continua a funcionar com default 7 se nunca tocado.

---

## Phase 5: User Story 3 — Sem spam: aviso controlado por item (P3)

**Goal**: Um Ato que se mantém atrasado ao longo de várias avaliações recebe **no máximo um** aviso.

**Independent Test**: correr `notify_overdue_atos()` 2× sobre o mesmo Ato atrasado e confirmar 0 avisos
novos na 2.ª (filtro por `overdue_notified_at`).

- [x] T010 [US3] Confirmar/garantir no filtro de T004 a exclusão de Atos já com `overdue_notified_at` (dedup na fonte) e, no endpoint opcional, que a 2.ª chamada devolve `notified_atos: 0`. (Sem CAS — single-runner; `ponytail:` subir só se passar a multi-runner.)

**Checkpoint**: idempotência garantida (SC-003).

---

## Phase 6: Verificação & Polish

- [x] T011 [P] Endpoint opcional `POST /api/atos/notify-overdue` (admin-only, 403 não-admin) em `backend/routes/atos.py` que corre `notify_overdue_atos()` e devolve os contadores — para disparo manual e verificação (Princípio VII). Idempotente.
- [x] T012 Escrever `backend/tests/test_atos_overdue.py` cobrindo os 7 casos do quickstart Cenário A: >X dispara (com IDs+link), <X não, idempotência (1x), resolvido (0), Direção vazia (sem erro), X menor passa a qualificar, `created_at` ausente/inválido ignorado. Usar `mock_db` (wire `db.atos`/`db.finance_settings` se preciso) + fixtures de role. `cd backend && pytest tests/test_atos_overdue.py -q`.
- [x] T013 [P] `cd backend && ruff check . && ruff format --check .` limpo; correr suite completa `pytest -q` sem regressões.
- [x] T014 Atualizar `tasks/todo.md` (secção de revisão) e, no fim, fechar a spec (renomear dir `-concluido`) só após verificação. Nota: toca `backend/` ⇒ release `develop→main` exigirá **Via B**; verificação prod = `POST /api/atos/notify-overdue` sem token → 401 + log do loop no arranque.

---

## Dependencies & Execution Order

- **Setup (T001)** → **Foundational (T002, T003)** → stories.
- **US1 (T004–T007)** depende de T002+T003. **É o MVP** — entregável sozinho (lê X com default 7).
- **US2 (T008–T009)** depende de T003 (campo base). Independente de US1.
- **US3 (T010)** depende de US1 (T004/T006).
- **Polish (T011–T014)** depois das stories alvo.

```
T001 → T002,T003 → ┌─ US1: T004→T005→T006→T007  (MVP)
                   ├─ US2: T008→T009
                   └─ US3: T010 (após US1)
                          → T011,T012,T013,T014
```

## Parallel Opportunities

- T002 e T003 em paralelo `[P]` (mesmo ficheiro `models.py`, mas blocos distintos — coordenar se editados juntos; senão sequencial).
- T011 e T013 `[P]` (ficheiros/escopos distintos).
- Stories US1 e US2 podem ser desenvolvidas em paralelo após Foundational (tocam funções distintas).

## Implementation Strategy

- **MVP = US1** (T001–T007): comportamento completo com limiar default 7. Entregável e testável sozinho.
- Incremento 2 = US2 (configurabilidade). Incremento 3 = US3 (verificação anti-spam) + Polish.
- Email permanece **fora do MVP** (decisão de negócio + STOP em emails a sócios reais).
