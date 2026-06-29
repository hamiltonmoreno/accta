# Implementation Plan: Aviso à Direção de Ato pendente há mais de X dias

**Branch**: `feature/aviso-deliberacao-pendente` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/010-aviso-deliberacao-pendente/spec.md`

## Summary

Avisar (in-app, espelhado em push) os membros da **Direção** quando um **Ato (Art. 54)**
fica em `pendente` há **mais de X dias** (X configurável por admin, default 7), **uma única
vez** por Ato. Avaliação periódica por um **loop in-process diário** (`asyncio.create_task`
no startup do FastAPI), idempotente por uma marca `overdue_notified_at` no próprio Ato.
Reutiliza por inteiro o sistema de notificações, a elegibilidade `members_of_orgao("direcao")`
(que já exclui contas técnicas/inativos) e o store `finance_settings`. Email fora do MVP.

## Technical Context

**Language/Version**: Python 3.11 (backend) — feature é **backend-only**

**Primary Dependencies**: FastAPI, asyncpg (DAO Mongo-compatible em `database.py`). **Zero deps novas.**

**Storage**: PostgreSQL/Supabase — coleções existentes `atos`, `finance_settings`, `notifications`, `users`

**Testing**: pytest (unit/in-process, `tests/conftest.py` com `mock_db`)

**Target Platform**: Linux server (Docker, container único no VPS)

**Project Type**: Web service (backend FastAPI) — sem alterações de frontend

**Performance Goals**: SLA da spec = aviso em ≤24h após cruzar o limiar (SC-001). 1 varrimento/dia.

**Constraints**: idempotência "uma única vez" (FR-005/SC-003); sem destinatários ⇒ sem erro (FR-009);
data de referência = `created_at` do Ato; ignora Atos sem `created_at` fiável.

**Scale/Scope**: ≤ algumas centenas de sócios; nº de Atos `pendente` em aberto é pequeno (dezenas).
Varrimento = 1 `find` filtrado + N notificações; sem N+1 problemático.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Simplicity First** — ✅ Loop in-process (≈15 linhas) + 1 campo aditivo no Ato + 1 campo aditivo
  em `FinanceSettings`. Sem framework de scheduler, sem novo endpoint obrigatório (1 endpoint admin
  *opcional* só para verificação/disparo manual — ver Phase 1). Reutiliza helpers existentes.
- **II. Root-Cause Discipline** — ✅ Idempotência na fonte (marca no Ato), não filtragem a jusante.
- **III. RBAC + Audit** — ✅ O loop é interno (sem request). O endpoint opcional de disparo manual é
  **admin-only**. Acesso a dados via DAO; sem SQL em rotas. Elegibilidade via `permissions.py`/`members_of_orgao`.
- **IV. Language** — ✅ Texto ao utilizador em PT; identificadores EN (`notify_overdue_atos`,
  `overdue_notified_at`, `ato_overdue_dias`); domínio PT (`ato`, `direcao`). Match ao ficheiro.
- **V. Design System** — N/A (sem UI nova; a configuração de X reutiliza o ecrã de definições financeiras existente).
- **VI. GitFlow** — ✅ `feature/aviso-deliberacao-pendente → develop`. Toca `backend/` ⇒ release `develop→main`
  precisará de **Via B**. Sem STOP conditions disparadas (campos aditivos não quebram docs; sem email; sem migração destrutiva).
- **VII. Verification Before Done** — ✅ pytest cobre a lógica de limiar/idempotência/exclusão; o endpoint
  de disparo manual permite provar o comportamento sem esperar 24h.

**Resultado**: PASS, sem violações. Complexity Tracking vazio.

## Project Structure

### Documentation (this feature)

```text
specs/010-aviso-deliberacao-pendente/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── settings-and-trigger.md
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
backend/
├── server.py                 # + hook no startup: asyncio.create_task(overdue_atos_loop())
├── routes/
│   └── atos.py               # + notify_overdue_atos() (core) e overdue_atos_loop();
│                             #   + (opcional) POST /api/atos/notify-overdue (admin, verificação/disparo manual)
├── models.py                 # + Ato.overdue_notified_at (aditivo); + FinanceSettings.ato_overdue_dias
│                             #   (default 7) + FinanceSettingsUpdate.ato_overdue_dias
├── helpers.py                # reutilizado (create_notification/notify_users, members_of_orgao) — sem alteração
├── permissions.py            # reutilizado (is_direcao via members_of_orgao) — sem alteração
└── tests/
    └── test_atos_overdue.py  # novo: limiar (>X dispara, <X não), idempotência (1x), resolvido (0),
                              #   sem destinatários (sem erro), created_at ausente (ignorado), X configurável
```

**Structure Decision**: Web service backend-only. A lógica vive em `routes/atos.py` (onde já estão
os Atos), exposta como função `notify_overdue_atos()` reutilizada por (a) o loop diário e (b) o endpoint
admin opcional. O agendador é um `asyncio` task arrancado no `@app.on_event("startup")` de `server.py`
(mesmo padrão non-fatal dos seeds existentes). Container único ⇒ sem risco de duplo-disparo; e mesmo que
houvesse, a marca `overdue_notified_at` torna o varrimento idempotente.

## Complexity Tracking

> Sem violações constitucionais — secção não aplicável.
