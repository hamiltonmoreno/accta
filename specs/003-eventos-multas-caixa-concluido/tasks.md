---
description: "Task list — Eventos e Multas Ligados ao Caixa"
---

# Tasks: Eventos e Multas Ligados ao Caixa (Ronda 2)

**Input**: Design documents from `specs/003-eventos-multas-caixa-concluido/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: INCLUÍDOS para o backend (Princípio VII + critério "pytest verde" no quickstart). Frontend verificado no browser. Unit/in-process com `mock_db`.

**Organization**: por user story (US1–US4) + Setup, Foundational, Migração (STOP), Polish.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: ficheiros distintos, sem dependência por completar
- **[Story]**: US1–US4; Setup/Foundational/Migração/Polish sem label

## Path Conventions

Web app: `backend/` + `frontend/src/`. Scripts em `scripts/`.

---

## Phase 1: Setup

- [X] T001 Confirmar baseline: `cd backend && pytest -q` (linha de base; integração `requests`/ConnectionRefused é ambiental, ignorar).
- [X] T002 [P] Rever `backend/tests/conftest.py`: `transactions`/`events`/`finance_settings` pré-ligados; `sancoes`/`atos` precisam de wiring in-test (`_wire`), como na ronda 1.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: nenhuma user story arranca antes desta fase.

- [X] T003 [P] Adicionar `event_id: Optional[str] = None` e `sancao_id: Optional[str] = None` ao modelo `Transaction` em `backend/models.py` (comentário PT; coexistem com project_id/ato_id).
- [X] T004 [P] Adicionar `event_id: Optional[str] = None` a `Ato` e `AtoCreate` em `backend/models.py`.
- [X] T005 [P] Adicionar modelos `EventExpenseCreate(description, amount>0, date?, category?)` e `EventReceitaCreate(description, amount>0, date?)` em `backend/models.py` (espelham `ProjectExpenseCreate`).
- [X] T006 Adicionar índices em `ensure_schema()` (`backend/database.py`): `ix_tx_event_type` (`(doc->>'event_id'),(doc->>'type')) WHERE doc ? 'event_id'` e `ix_tx_sancao` (`(doc->>'sancao_id')) WHERE doc ? 'sancao_id'`.

**Checkpoint**: modelos e schema prontos.

---

## Phase 3: User Story 1 - Resultado financeiro do evento (Priority: P1) 🎯 MVP

**Goal**: despesas + receitas de evento como transações com `event_id`; resultado derivado; filtro por evento.

**Independent Test**: criar evento + despesa + receita (abaixo do limiar) e confirmar movimentos no caixa filtráveis por evento, `resultado_financeiro` correto, e resumo do período a incluí-los.

### Tests for User Story 1 ⚠️

- [X] T007 [P] [US1] Teste: `POST /events/{id}/expenses` cria Transaction(despesa, event_id, category) e `POST /events/{id}/receitas` cria Transaction(receita, event_id, "extraordinarias"), em `backend/tests/test_eventos_multas_caixa.py`.
- [X] T008 [P] [US1] Teste: `GET /events/{id}/expenses` e `/receitas` filtram por event_id+type; `DELETE` remove a transação, em `backend/tests/test_eventos_multas_caixa.py`.
- [X] T009 [P] [US1] Teste: `resultado_financeiro` (receitas/despesas/resultado) agregado no `get_event`, em `backend/tests/test_eventos_multas_caixa.py`.
- [X] T010 [P] [US1] Teste: `GET /finances/transactions?event_id=` filtra **e** `compute_financial_summary` do período reflete as receitas/despesas de evento (FR-003/SC-003 — prova que entram no resumo/DRE), em `backend/tests/test_eventos_multas_caixa.py`.

### Implementation for User Story 1

- [X] T011 [US1] Em `backend/routes/events.py`: helpers de finanças — `_event_result(event_id)` (agregação receitas/despesas/resultado) e guard de gestão (`has_role_or_privilege(admin, "manage_events")`) reutilizável.
- [X] T012 [US1] `POST /events/{id}/expenses` em `backend/routes/events.py`: valida/normaliza `category` (default "eventos" ∈ EXPENSE_CATEGORIES), cria `Transaction(type="despesa", event_id)`, `create_audit_log`. (Gate Art. 54 entra na US3 — T021.)
- [X] T013 [US1] `POST /events/{id}/receitas`: cria `Transaction(type="receita", category="extraordinarias", event_id)`, `create_audit_log`.
- [X] T014 [US1] `GET /events/{id}/expenses` e `GET /events/{id}/receitas`: `transactions.find({event_id, type}).sort(date,-1).to_list(500)`.
- [X] T015 [US1] `DELETE /events/{id}/expenses/{tx}` e `/receitas/{tx}`: apaga a transação + audit (guarda de `ato_id` entra na US3 — T022).
- [X] T016 [US1] `GET /events/{id}` (`events.py:110`): largar `response_model=Event`, anexar `resultado_financeiro = _event_result(id)` ao dict devolvido.
- [X] T017 [US1] Adicionar param `event_id: Optional[str]` a `list_transactions` em `backend/routes/finances.py` (→ `query["event_id"]`).

**Checkpoint**: evento reflete-se no caixa/resumo/DRE; resultado visível.

---

## Phase 4: User Story 2 - Multa aplicada entra no caixa (Priority: P1)

**Goal**: ao aplicar uma multa, criar receita idempotente com `sancao_id`.

**Independent Test**: levar multa a "aplicada" e confirmar 1 receita com sancao_id; re-aplicar não duplica; sanção não-multa não cria movimento.

### Tests for User Story 2 ⚠️

- [X] T018 [P] [US2] Teste: `aplicar_sancao` com tipo="multa"/valor>0 cria 1 receita (sancao_id, "extraordinarias"); re-execução não duplica (idempotência por sancao_id), em `backend/tests/test_eventos_multas_caixa.py`.
- [X] T019 [P] [US2] Teste: tipo≠"multa" (advertencia) ou multa_valor=0 → nenhum movimento; `GET /finances/transactions?sancao_id=` filtra; **e** `compute_financial_summary` do período reflete a receita da multa (FR-003/SC-003), em `backend/tests/test_eventos_multas_caixa.py`.

### Implementation for User Story 2

- [X] T020 [US2] Em `aplicar_sancao` (`backend/routes/sancoes.py`), **antes do CAS** decidida→aplicada (junto dos efeitos idempotentes): se `tipo=="multa"` e `multa_valor>0` e não existir `transactions.find_one({sancao_id, type:"receita"})`, criar `Transaction(type="receita", category="extraordinarias", sancao_id, amount=multa_valor, description="Multa - <nome do sócio>")`. Nome do sócio: ler de `db.users.find_one({"id": s["user_id"]}, {"_id":0,"name":1})`; fallback `"Multa"` (sem nome) se ausente. Importar `Transaction`.
- [X] T020b [US2] Adicionar param `sancao_id: Optional[str]` a `list_transactions` em `backend/routes/finances.py` (→ `query["sancao_id"]`).

**Checkpoint**: multa aplicada → receita no caixa, exactly-once.

---

## Phase 5: User Story 3 - Gate Art. 54 + Ato↔evento (Priority: P2)

**Goal**: despesa de evento acima do limiar exige Ato; Ato propaga event_id; guarda de remoção e de eliminação.

**Independent Test**: com limiar positivo, despesa direta acima → 400; criar+executar Ato com event_id → despesa ligada a Ato e evento; DELETE dessa despesa → 400; apagar evento com movimentos → 409.

### Tests for User Story 3 ⚠️

- [X] T021t [P] [US3] Teste: despesa de evento `amount>limiar` → 400 (pede Ato); `delete` de despesa com `ato_id` → 400; `delete_event` com transações → 409, em `backend/tests/test_eventos_multas_caixa.py`.
- [X] T022t [P] [US3] Teste: `execute_ato` com `event_id` cria Transaction com `ato_id` e `event_id`, em `backend/tests/test_eventos_multas_caixa.py`.

### Implementation for User Story 3

- [X] T021 [US3] Gate Art. 54 em `POST /events/{id}/expenses` (`events.py`): `limiar = await coaprovacao_limiar()` (de `helpers`); se `>0` e `amount>limiar` → 400 (PT, orientar para Ato com event_id).
- [X] T022 [US3] Guarda no `DELETE /events/{id}/expenses/{tx}` (`events.py`): se a transação tiver `ato_id` → 400 (reverter pelo Ato).
- [X] T023 [US3] `delete_event` (`events.py:158`): contar `transactions` com `event_id`; se `>0` → 409 (PT). Espelha `delete_project`.
- [X] T024 [US3] `execute_ato` (`backend/routes/atos.py`): propagar `event_id=ato.get("event_id")` para a `Transaction` (a par de `project_id`). `create_ato` persiste `event_id` do `AtoCreate`.

**Checkpoint**: atalho ao Art. 54 fechado para eventos; despesas via Ato ligadas ao evento.

---

## Phase 6: User Story 4 - Resultado do evento na interface (Priority: P3)

**Goal**: secção financeira no detalhe do evento.

### Implementation for User Story 4

- [X] T025 [P] [US4] `frontend/src/utils/api.js`: endpoints de finanças de evento (expenses/receitas POST/GET/DELETE) + filtros `event_id`/`sancao_id` em transações.
- [X] T026 [US4] Detalhe de evento (`frontend/src/pages/private/` — página/aba de evento): secção financeira com registar despesa (categoria), registar receita, listas e `resultado_financeiro` (receitas/despesas/resultado). Mensagem amigável quando o gate Art. 54 recusa. Seguir `frontend-design` (botões neutros/Floresta; sem Carmesim como primário positivo).
- [X] T027 [P] [US4] (Opcional) detalhe da sanção: mostrar a receita de multa associada quando aplicada.

  **Feito (2026-06-26):** faixa em `SancaoCard.js` que mostra "Receita no caixa:
  {valor} · {aplicada_em}" para multas aplicadas (ícone `CircleDollarSign`,
  Floresta `#166534` sobre `#F0FDF4`, contraste ≥4.5:1, ícone+texto).
  `data-testid="multa-receita-{id}"`.

  **W1 (revisão do PR #350, Codex P2) resolvido:** a faixa **não** infere do
  estado da sanção — `list_sancoes` (`routes/sancoes.py`) anota
  `multa_receita: {exists, amount}` agregando de `transactions` numa só query
  (`$in`, sem N+1) e a faixa só aparece com `multa_receita.exists`, mostrando o
  valor REAL do caixa. Assim, se a receita for removida/corrigida nas finanças
  (delete/patch não guardam `sancao_id`, e não há transição `aplicada→anulada`),
  a UI acompanha em vez de afirmar uma receita inexistente. Anotação no backend
  (não fetch no cliente) evita o 403 da Direcção sem `view_finances`. Verificado:
  2 testes novos em `test_sancoes_routes.py` (15/15), eventos 21/21, ruff/eslint
  limpos, e browser ponta-a-ponta (faixa presente com receita; desaparece após
  apagar a transação).

**Checkpoint**: UX de finanças de evento utilizável.

---

## Phase 7: Migração (STOP — confirmação do dono)

**⚠️ STOP (Princípio VI #1)**: `--apply` só após OK do dono, revisto o dry-run.

- [X] T028 Criar `scripts/migrate_multas_to_transactions.py` (padrão de `migrate_project_expenses_to_transactions.py`): dry-run por defeito — sanções `tipo="multa"`, `status="aplicada"`, `multa_valor>0` **sem** receita com esse `sancao_id`; relatório de reconciliação; não escreve.
- [X] T029 Adicionar `--apply --confirm` (idempotente: re-verifica `sancao_id`) ao script. **Não correr `--apply`** nesta fase.
- [X] T030 Correr o **dry-run** e anexar o relatório ao PR (gate antes de qualquer `--apply`).

  **Relatório dry-run (2026-06-21, contra prod via VPS, read-only):**
  `multas aplicadas c/ valor=0 | a criar receita=0 | já no caixa=0` →
  **nada a migrar**. Não existem multas legadas (aplicadas antes da feature)
  por reconciliar; o `--apply` seria um no-op, logo **dispensado**. Fase de
  migração concluída sem escrita em prod.

---

## Phase 8: Polish

- [X] T031 [P] `ruff check`/`ruff format` no backend; `eslint` no frontend; corrigir.
- [X] T032 [P] Atualizar docs (nota: "despesa/receita de evento = transação"; "multa aplicada → receita"); confirmar que nenhuma leitura usa dados financeiros fora de `transactions`.
- [X] T033 Validar `quickstart.md` (Cenários 1–4 via HTTP; Cenário 5 no browser com screenshot) — Princípio VII.

  **Cenários 1–4: FEITOS e verdes** — automatizados como validação executável
  ponta-a-ponta em `backend/tests/test_eventos_multas_caixa_quickstart.py`
  (estado partilhado em memória; `4 passed`, suite eventos 24/24, ruff limpo).
  Mapeiam 1:1 ao quickstart: C1 resultado de evento, C2 gate Art. 54 + Ato↔evento
  + guarda de delete, C3 multa exactly-once + advertência sem movimento, C4 delete
  de evento 409.
  **Cenário 5 (UI): FEITO e VALIDADO** (2026-06-21, browser, app local) —
  `EventFinanceDialog` no evento "Teste": despesa `Sala` 8000 + receita
  `Inscrições` 12000 → cabeçalho RECEITAS 12 000 · DESPESAS 8000 · RESULTADO ↗ 4000;
  gate Art. 54 (limiar 50000) recusou despesa de 70000 com toast PT amigável.
  Design conforme (`frontend-design`: Registar em Floresta, sem vermelho-sobre-escuro,
  sem dark mode). Registo + screenshots em
  `specs/003-eventos-multas-caixa-concluido/T033-cenario5-browser.md`
  (`T033-cenario5-resultado.png`, `T033-cenario5-gate.png`).
- [X] T034 (Opcional) `/speckit-analyze` final / registar lição em `tasks/lessons.md` se houver correção do dono.

  **No-op (2026-06-26):** spec já concluída e em prod (v0.5.27); não houve
  correção do dono na retoma do T027, logo não há lição nova a registar. Sem
  itens por reconciliar.

---

## Dependencies & Execution Order

- **Setup (P1)** → **Foundational (P2)** bloqueia tudo (modelos + schema).
- **US1 (P3)**: depende de Foundational. MVP.
- **US2 (P4)**: depende de Foundational (Transaction.sancao_id). Independente de US1.
- **US3 (P5)**: depende de US1 (gate/guarda vivem nas funções de despesa de evento) + Foundational (Ato.event_id).
- **US4 (P6)**: depende de US1–US3 (consome endpoints).
- **Migração (P7)**: depende de US2 (sancao_id). `--apply` = STOP.
- **Polish (P8)**: no fim.

### Parallel Opportunities
- T003–T005 (modelos) em paralelo; T006 a seguir.
- Testes [P] de cada story em paralelo.
- US2 corre em paralelo com US1 (ficheiros distintos: sancoes.py vs events.py).

---

## Implementation Strategy

**MVP** = US1 (resultado financeiro do evento). Depois US2 (multa), US3 (gate), US4 (UI), Migração (com confirmação), Polish. Cada incremento entrega valor sem partir o anterior. Conventional Commits com escopo (`feat(eventos): …`, `feat(financas): …`).

## Notes
- Despesas/receitas de evento e multas passam a `transactions`; granularidade por `event_id`/`sancao_id`.
- `--apply` da migração é STOP — nunca sem OK do dono.
- FR-016 (estorno) fora de âmbito (sem fluxo aplicada→anulada).
