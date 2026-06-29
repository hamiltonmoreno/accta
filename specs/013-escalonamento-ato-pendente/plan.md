# Implementation Plan: Escalonamento de lembretes de Ato (Art. 54) pendente

**Branch**: `feature/escalonamento-ato-pendente` | **Date**: 2026-06-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/013-escalonamento-ato-pendente/spec.md`

## Summary

Tornar **recorrente** o aviso de Ato (Art. 54) pendente além do limiar X: hoje as specs
010 (Direção) e 012 (proponente) avisam **uma única vez** e param. A decisão do dono
(minimalista) é lembrar **a cada X dias** (reutilizando `ato_overdue_dias`), aos **mesmos
destinatários** (Direção + proponente, com a dedup da spec 012), com a **antiguidade
crescente** a comunicar a urgência, **até o Ato sair de `pendente`** (sem teto).

**Abordagem técnica (1 alteração de filtro):** a marca existente `overdue_notified_at`
deixa de ser um *flag* single-shot e passa a ser o **cursor "último lembrete"**. O
varrimento diário (`_notify_overdue_atos_locked` em `routes/atos.py`, spec 010) muda **só a
query inicial**: de `{"overdue_notified_at": None}` para
`{"$or": [{"overdue_notified_at": None}, {"overdue_notified_at": {"$lte": now - X dias}}]}`.
O resto do loop — o *gate* de idade (`> X`), o aviso à Direção, o aviso ao proponente
deduplicado (spec 012), as exclusões `technical`/`inativo`, o push, e a escrita
`overdue_notified_at = now` a cada passo — **já funciona para a recorrência sem mudança**
(a escrita de `now` avança o cursor; o próximo lembrete só volta a qualificar passado X).

## Technical Context

**Language/Version**: Python 3.11 (backend)

**Primary Dependencies**: FastAPI + DAO Mongo-compatível sobre asyncpg (`database.py`). **Zero deps novas.**

**Storage**: PostgreSQL (jsonb) via DAO. **Sem schema/migração/campo novo** — reutiliza
`atos.overdue_notified_at` (ISO-8601 string) das specs 010/012, mudando só a *semântica*
(flag → cursor de último lembrete).

**Testing**: pytest — `backend/tests/test_atos_overdue.py` (in-process, sem DB/servidor).

**Target Platform**: servidor Linux (prod via **Via B**; `docs/runbook-deploy-backend-via-b.md`).

**Project Type**: web-service — alteração **backend-only**, **sem frontend**.

**Performance Goals**: 1 query/dia com uma cláusula `$or` extra; conjunto de Atos pequeno;
**sem N+1** (a query de elegibilidade do proponente da spec 012 mantém-se 1×).

**Constraints**: varrimento diário **idempotente** e não-fatal (herdado da spec 010 — lock
`_overdue_lock`, `asyncio.create_task` no startup); comparação do cutoff por **string ISO
lexicográfica** (válida porque todas as marcas usam `datetime.now(timezone.utc).isoformat()`).

**Scale/Scope**: ≤ algumas centenas de sócios; poucos Atos pendentes em simultâneo.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|-----------|-----------|
| **I. Simplicity First** | ✅ Uma cláusula de filtro alterada; reutiliza marca, loop, agendador e helpers existentes. Sem abstrações, flags ou campos novos. |
| **II. Root-Cause** | ✅ A causa de "avisa uma vez e cala" é o filtro `== None` excluir Atos já marcados; corrige-se na raiz (o filtro), não com um segundo mecanismo. |
| **III. RBAC + Audit** | ✅ Sem nova superfície protegida. O disparo é o loop interno; o endpoint admin `POST /api/atos/notify-overdue` (spec 010) já tem RBAC + audit e é reutilizado tal-qual. |
| **IV. Language** | ✅ Texto ao utilizador em PT; identificadores EN; comentários PT. |
| **V. Design System** | ✅ N/A — sem frontend. |
| **VI. GitFlow + Confirmação** | ✅ Branch `feature/*` off `develop`; release `develop→main` = **Via B** + confirmação do dono (STOP). |
| **VII. Verification** | ✅ Testes in-process + (pós-deploy) prova decisiva server-side: `POST /api/atos/notify-overdue` sem token → 401 e a resposta do disparo reflete os lembretes. |

**Resultado**: PASS — sem violações; **Complexity Tracking** não aplicável.

## Project Structure

### Documentation (this feature)

```text
specs/013-escalonamento-ato-pendente/
├── plan.md              # Este ficheiro
├── research.md          # Fase 0 — verificação dos operadores do DAO + decisão de desenho
├── data-model.md        # Fase 1 — semântica nova de overdue_notified_at (sem campo novo)
├── quickstart.md        # Fase 1 — cenários de validação (recorrência, no-spam, paragem)
├── contracts/
│   └── sweep-recurrence.md   # contrato da mudança do varrimento (filtro)
└── tasks.md             # Fase 2 (/speckit-tasks — NÃO criado aqui)
```

### Source Code (repository root)

```text
backend/
├── routes/
│   └── atos.py                 # _notify_overdue_atos_locked: muda só a query inicial
│                               #   (+ importar timedelta se necessário; + atualizar comentário)
└── tests/
    └── test_atos_overdue.py    # +casos de recorrência / no-spam / paragem (estende spec 010/012)
```

**Structure Decision**: web-service existente; a feature toca **um único ficheiro de
runtime** (`backend/routes/atos.py`) e o respetivo teste. Sem novos módulos, rotas, modelos
ou frontend.

## Complexity Tracking

> Sem violações constitucionais — secção não aplicável.
