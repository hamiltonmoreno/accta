# Implementation Plan: Lembrete de Ato pendente ao próprio proponente

**Branch**: `feature/aviso-proponente-ato-pendente` | **Date**: 2026-06-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/012-aviso-proponente-ato-pendente/spec.md`

## Summary

Estender a avaliação diária da **spec 010** (`_notify_overdue_atos_locked` em
`routes/atos.py`) para, no **mesmo varrimento** e **partilhando a marca de
idempotência `Ato.overdue_notified_at`**, avisar também **o proponente** (`created_by`)
de que o seu Ato continua `pendente` há mais de X dias. **Uma única vez** por Ato
(Q1=A). Para não duplicar e para **não tocar no comportamento já existente do aviso à
Direção** (SC-004), o proponente só é avisado quando **não é já destinatário Direção**
e é uma conta elegível (ativa, não-técnica). Backend-only: **sem schema, sem migração,
sem novo agendador, sem novo limiar, zero deps**. Sem frontend.

## Technical Context

**Language/Version**: Python 3.11 (backend).

**Primary Dependencies**: helpers `notify_users` (já com `exclude_id`), `members_of_orgao`;
DAO Mongo-compatível; agendador diário + lock já existentes (spec 010). **Zero deps novas.**

**Storage**: PostgreSQL via DAO. **Sem campos novos** — partilha
`Ato.overdue_notified_at` (spec 010). Uma query adicional a `users` para apurar a
elegibilidade dos proponentes (ativos/não-técnicos), sem N+1.

**Testing**: pytest (unit, in-process com `mock_db`); validação funcional do dono.

**Target Platform**: Backend Linux/Docker (prod Via B).

**Project Type**: Web app (só backend muda nesta feature).

**Performance Goals**: N/A (varrimento diário, lista de overdue pequena; +1 query a `users`).

**Constraints**: aviso ao proponente **uma vez** por Ato, no mesmo evento da spec 010;
**dedup** com a Direção; spec 010 **inalterada**; reutiliza limiar X (`ato_overdue_dias`).

**Scale/Scope**: Atos de co-aprovação; volume baixo.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Simplicity First** ✅ — estende o varrimento existente; partilha a marca; sem
  schema/migração/config/estado novos. Delta mínimo num único ponto (`routes/atos.py`).
- **II. Root-Cause Discipline** ✅ — preenche o ponto cego na origem (o varrimento que
  já decide "Ato parado"), não um aviso paralelo.
- **III. RBAC + Audit** ✅ — é um varrimento de **sistema** (sem ação de utilizador):
  como na spec 010, o loop não audita; o endpoint manual `POST /atos/notify-overdue`
  (admin, já auditado/RBAC) passa a cobrir também este aviso. Sem SQL em rotas.
- **IV. Language Discipline** ✅ — mensagem ao utilizador em PT; identificadores EN +
  domínio PT (`proponente`/`created_by`/`overdue`). Sem renomeações.
- **V. Design System Authority** ✅ — **sem frontend** (reusa o sino/Web Push). N/A.
- **VI. GitFlow + Confirmation** ✅ — `feature/* → develop`; release `develop→main`
  exigirá **Via B** (toca `backend/`).
- **VII. Verification Before Done** ✅ — testes unit + validação funcional do dono.

**Sem violações — sem entradas em Complexity Tracking.**

## Project Structure

### Documentation (this feature)

```text
specs/012-aviso-proponente-ato-pendente/
├── plan.md              # Este ficheiro
├── research.md          # Phase 0 (dedup proponente×Direção; elegibilidade; mensagem)
├── data-model.md        # Phase 1 (sem campos novos; marca partilhada; counters)
├── quickstart.md        # Phase 1 (cenários de validação)
├── contracts/           # Phase 1 (extensão de comportamento do varrimento/endpoint)
└── checklists/requirements.md
```

### Source Code (repository root)

```text
backend/
├── routes/atos.py                       # _notify_overdue_atos_locked: + aviso ao
│                                         #   proponente (dedup vs Direção, elegibilidade),
│                                         #   +counter notified_proponentes; spec 010 intacta
└── tests/test_atos_overdue.py           # +casos: proponente avisado 1×; dedup quando é
                                          #   Direção; inativo/técnico excluído; resolvido não avisa
```

**Structure Decision**: Web app existente; muda **um único ficheiro de runtime**
(`routes/atos.py`) + testes. `models.py`, `database.py`, `server.py` e frontend **não
mudam**.

## Complexity Tracking

> Sem violações da Constituição — secção não aplicável.
