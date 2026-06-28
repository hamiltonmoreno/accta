---
description: "Task list — Lembrete informativo de quotas"
---

# Tasks: Lembrete informativo de quotas

**Input**: Design documents from `/specs/008-lembrete-quotas/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: SIM — o `quickstart.md` pede `tests/test_lembrete_quotas.py`. Incluídos. A
notificação real + o toggle são verificados em navegador (Princípio VII).

**Organização**: por user story. Backend (gerador + DAO + modelo) + frontend (toggle).
Zero deps novas; 1 campo aditivo; sem migração destrutiva; toca `backend/` → release **Via B**.
**Sem inadimplência** (linguagem de cobrança proibida). **Email = STOP/off no MVP.**

## ⚠️ Sobreposição de ficheiros

- `backend/routes/finances.py` — só **US1** (gerador).
- `backend/database.py` — só **US1** (`insert_quotas_atomic`).
- `backend/models.py` — **Foundational** (campo partilhado por US1+US2).
- `backend/tests/test_lembrete_quotas.py` — **US1 + US2** escrevem nele → sequencial.
- Endpoint de preferência (`routes/comunicados.py` ou `users.py`) + `perfil/EmailPrefs.js`
  + `utils/api.js` — só **US2**, ficheiros distintos de US1 → [P] com US1.

---

## Phase 1: Setup

- [x] T001 Confirmar os pontos de reutilização (sem código): `POST /finances/generate-quotas`
  + `notify_all_active_users` a substituir (`routes/finances.py:~657`); `insert_quotas_atomic`
  (`database.py:~1474`); `create_notification` (`helpers.py:272`); o padrão de preferências
  `email_opt_out_informativos` + `EmailPreferencesUpdate` + `comunicadosAPI.updateEmailPreferences`
  e o toggle `perfil/EmailPrefs.js`.

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T002 Em `backend/models.py`, adicionar `quota_reminder_opt_out: bool = False` ao
  `User`/`UserBase` (aditivo; missing → False → recebe). **Bloqueia US1 (lê) e US2 (escreve).**

**Checkpoint**: campo disponível; US1 e US2 podem avançar.

---

## Phase 3: User Story 1 — Lembrete in-app na geração (Priority: P1) 🎯 MVP

**Goal**: ao gerar as quotas do mês, cada sócio que recebeu quota nova recebe um lembrete
informativo in-app (valor + total acumulado, link `/carteira`), respeitando o opt-out.

**Independent Test**: gerar quotas de um mês → cada sócio novo (sem opt-out, ativo, membro)
recebe **uma** notificação com valor+total e link `/carteira`; tom informativo. (SC-001/003)

- [x] T003 [US1] Em `backend/database.py`, alterar `insert_quotas_atomic(year, month, candidate_docs)`
  para **devolver a lista de `user_id` efetivamente inseridos** (em vez do `int`); manter a
  atomicidade/advisory lock. Atualizar o docstring.
- [x] T004 [US1] Em `backend/routes/finances.py` (`generate_monthly_quotas`): usar os
  `user_ids` devolvidos por `insert_quotas_atomic` (`created_count = len(...)`); obter o
  **total acumulado por sócio** com **1 aggregate** sobre `transactions` (group by `user_id`,
  sum `amount`, `type=receita` + `category ∈ {quotas,joias}`); **substituir** o
  `notify_all_active_users` por um `create_notification` **por sócio novo** — `type="financeiro"`,
  título/corpo **informativos** (valor do período + total; **sem** dívida/atraso), link
  **`/carteira`** — saltando `quota_reminder_opt_out=True`, contas `technical` e `inativo`.
- [x] T005 [US1] Criar `backend/tests/test_lembrete_quotas.py` (unit, `mock_db` + token de
  financeiro): geração → `create_notification` chamado **1×/sócio novo** com link `/carteira`
  e corpo com valor+total; **idempotência** (insert devolve [] no 2.º run → 0 notificações);
  sócio **sem quota nova** não recebe. Desligar limiter se aplicável.
- [ ] T006 [US1] Verificar em navegador (Princípio VII): como financeiro gerar um mês novo;
  como sócio abrir o sino → ver o lembrete (valor+total, tom informativo) a abrir `/carteira`.

**Checkpoint**: US1 funcional (MVP).

---

## Phase 4: User Story 2 — Opt-out (Priority: P1)

**Goal**: o sócio ativa/desativa os lembretes; quem opta por sair deixa de os receber.

**Independent Test**: pôr `quota_reminder_opt_out=True` num sócio → no próximo gerar, não
recebe; `False` → recebe. Toggle no Perfil reflete e persiste. (SC-006, FR-004/005)

> Ficheiros distintos de US1 (endpoint de prefs + frontend) → [P] com US1; o teste de
> exclusão (T009) depende do código de notify de US1 (T004).

- [x] T007 [P] [US2] Estender o endpoint de preferências (onde vive `email_opt_out_informativos`
  — `routes/comunicados.py` ou `routes/users.py`) para aceitar e gravar `quota_reminder_opt_out`
  do **próprio** sócio (`Depends(get_current_user)`, sem privilégio); refletir no `/auth/me`.
  Atualizar o modelo `EmailPreferencesUpdate` (ou análogo) com o campo.
- [x] T008 [P] [US2] Em `frontend/src/pages/private/perfil/EmailPrefs.js`, adicionar um 2.º
  toggle **"Lembretes de quota"** ligado a `!user.quota_reminder_opt_out`, que chama o método
  de preferências (`utils/api.js` — estender/adicionar) e faz `refreshUser`; copy informativo (PT).
- [x] T009 [US2] No `backend/tests/test_lembrete_quotas.py`, adicionar: sócio com
  `quota_reminder_opt_out=True` **não** é notificado; contas `technical` e `inativo` excluídos;
  e o endpoint de preferência grava o campo no próprio user. (FR-004/005)
- [ ] T010 [US2] Verificar em navegador: desativar o toggle → gerar outro mês → o sócio não
  recebe; reativar → volta a receber.

---

## Phase 5: User Story 3 — Email gated/off (Priority: P3)

**Goal**: nenhum email é enviado no MVP; o canal email fica atrás de um gate explícito do dono.

**Independent Test**: gerar quotas → **zero** envios de email; só in-app. (SC-005, FR-007)

> Não se constrói envio real de email (condição STOP #6). Apenas garantir/atestar o off.

- [x] T011 [US3] Garantir que o fluxo de `generate-quotas` **não** invoca envio de email
  (só `create_notification` in-app) e adicionar ao `test_lembrete_quotas.py` uma asserção de
  que **nenhuma função de email** (`email_service.*`) é chamada no fluxo. Documentar no código
  (comentário) que ligar email é decisão do dono (STOP) + respeitará `quota_reminder_opt_out`.

---

## Phase 6: Polish & Cross-Cutting

- [x] T012 [P] Lint: `cd backend && ruff check routes/finances.py database.py models.py` e
  `cd frontend && npx eslint src/pages/private/perfil/EmailPrefs.js src/utils/api.js --ext .js,.jsx --max-warnings=60`.
- [x] T013 Atualizar o teste existente do gerador (que afirmava `notify_all_active_users`) para
  o novo comportamento; correr `cd backend && pytest tests/test_lembrete_quotas.py` + a suite de
  finanças/geração de quotas (verde) e a checklist do `quickstart.md` (SC-001…SC-006).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2: T002 campo)** → US1/US2.
- **US1 (Phase 3)**: T003 (DAO) → T004 (gerador) → T005 (teste) → T006 (browser). MVP.
- **US2 (Phase 4)**: T007/T008 [P] com US1 (ficheiros distintos); T009 depende de T004; T010 depois.
- **US3 (Phase 5)**: depois de US1 (mesmo fluxo).
- **Polish (Phase 6)**: no fim (T013 inclui atualizar o teste existente do gerador).

### User Story Dependencies

- **US1 (P1)**: depende de T002 (campo). MVP.
- **US2 (P1)**: depende de T002; o teste de exclusão depende do notify de US1.
- **US3 (P3)**: garantia/teste sobre o fluxo de US1.

### Parallel Opportunities

- **T007** (endpoint prefs) e **T008** (toggle frontend) são [P] face ao backend de US1
  (`finances.py`/`database.py`) — ficheiros distintos.
- **T012** (lint) [P].
- Dentro de `finances.py`/`database.py` e do ficheiro de testes: sequencial.

---

## Parallel Example

```bash
# Após T002 (campo):
Trilho A (US1 backend):   T003 → T004 → T005 → T006
Trilho B (US2 prefs):     T007 (endpoint) + T008 (toggle)   # [P] com A
# Convergem: T009 (teste opt-out, usa T004) → T010 → US3 (T011) → Polish
```

---

## Implementation Strategy

### MVP First (US1)

Setup → T002 → US1 (T003-T006) → **validar a notificação no navegador** → demo/PR.

### Incremental Delivery

US1 (lembrete in-app) → US2 (opt-out) → US3 (garantir email off) → Polish.

---

## Notes

- Reutiliza: gerador de quotas, `create_notification`, padrão de preferências de email,
  toggle shadcn. **1 campo aditivo, zero deps, sem migração destrutiva.**
- **Sem inadimplência**: o corpo da notificação é informativo (transparência) — proibida
  linguagem de dívida/atraso (FR-002).
- **Email STOP**: não se constrói envio real no MVP; ligar é decisão explícita do dono.
- Toca `backend/` → release `develop→main` precisa de **Via B** (ver [[prod-backend-deployed-state]]).
- Commits: Conventional Commits com escopo (`feat(finances): …`, `feat(perfil): …`). PR → `develop`.
