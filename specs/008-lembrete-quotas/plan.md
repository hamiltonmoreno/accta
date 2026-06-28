# Implementation Plan: Lembrete informativo de quotas

**Branch**: `feature/lembrete-quotas` | **Date**: 2026-06-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/008-lembrete-quotas/spec.md`

## Summary

Tornar **personalizado e por sócio** o aviso que já é disparado quando as quotas do
mês são geradas. Hoje `POST /finances/generate-quotas` envia **uma** notificação
genérica a todos os ativos (`notify_all_active_users`) com link para `/financeiro`
(que está **gated a admin/financeiro** — bug latente para o sócio). A feature
substitui esse aviso genérico por um **lembrete informativo por sócio** (valor da
quota do período + total acumulado), entregue **in-app**, com link para `/carteira`
(acessível ao sócio), respeitando um **opt-out** dedicado. O disparo é **orientado a
evento** (na geração de quotas — Decisão Q1), sem agendador. Email fica **desativado e
gated** (STOP). Sem inadimplência — tom informativo.

## Technical Context

**Language/Version**: Python 3.11 (backend), JavaScript/React 19 (frontend)

**Primary Dependencies**: FastAPI + DAO Mongo-compatible; `helpers.create_notification`;
React/shadcn (toggle). **Zero deps novas.**

**Storage**: PostgreSQL via DAO. **Leitura** de `transactions` (totais por sócio) +
**escrita** de `notifications` (já existe) + **1 campo aditivo** no doc `users`
(`quota_reminder_opt_out`, default `False`). Sem migração destrutiva.

**Testing**: pytest unit (geração → notifica os novos; opt-out excluído; idempotência;
contas técnicas/inativos excluídos) + verificação em navegador (notificação aparece;
toggle de preferência funciona).

**Target Platform**: Web (portal privado).

**Project Type**: Web app (frontend + backend).

**Performance Goals**: geração de quotas com ~centenas de sócios → 1 aggregate de totais
+ N `create_notification` (já é o padrão do gerador); aceitável.

**Constraints**: **sem inadimplência** (linguagem informativa); **email = STOP** (off por
defeito); opt-out respeitado; idempotente por período.

**Scale/Scope**: ~5 ficheiros (`routes/finances.py`, `database.py`, `models.py`;
frontend `perfil/EmailPrefs.js` (ou prefs) + `utils/api.js`).

## Constitution Check

| Princípio | Estado | Nota |
|-----------|--------|------|
| I. Simplicity First | ✅ | Liga-se ao gerador de quotas existente; reutiliza `create_notification`; 1 campo de preferência + 1 toggle. Substitui (não duplica) o aviso genérico. |
| II. Root-Cause Discipline | ✅ | Corrige de raiz o link `/financeiro` (gated) → `/carteira` para o sócio. |
| III. RBAC + Audit | ✅ | `generate-quotas` já exige `manage_finances` + audita (o lembrete é efeito dessa ação auditada — sem novo audit). Atualização de preferência = self-service (próprio user), padrão das prefs de email. Sem raw SQL (DAO). |
| IV. Language Discipline | ✅ | Notificações/preferência em PT; identificadores EN (`quota_reminder_opt_out`). |
| V. Design System Authority | ✅ | Toggle reaproveita o padrão shadcn `Switch` do `EmailPrefs`. Sem novas cores. |
| VI. GitFlow + Confirmation (STOP) | ⚠️ ver nota | **Email a utilizadores reais = STOP #6.** O MVP (US1+US2) é **só in-app** → não dispara o STOP. US3 (email) fica **OFF por defeito** e atrás de confirmação explícita do dono — **não se envia email real sem o gate**. Toca `backend/` → release = **Via B**. |
| VII. Verification Before Done | ✅ | pytest + verificação em navegador. |

**Resultado do gate**: PASS. O único ponto sensível (email STOP) é **evitado** mantendo
US3 desligado/gated; o MVP não envia email. Sem Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/008-lembrete-quotas/
├── plan.md · research.md · data-model.md · quickstart.md · contracts/ · tasks.md(/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── routes/finances.py     # generate-quotas: substituir notify genérico por lembrete por-sócio
│                          #   (valor + total acumulado, link /carteira, respeita opt-out)
├── database.py            # insert_quotas_atomic: devolver os user_ids criados (p/ notificar só os novos)
└── models.py              # users: + quota_reminder_opt_out (aditivo, default False) + modelo de update

frontend/src/
├── pages/private/perfil/EmailPrefs.js  # + toggle "Lembretes de quota" (opt-out)
└── utils/api.js                        # + método de preferência (ou estender o de email prefs)
```

**Structure Decision**: Web app; toca **backend** (gerador + DAO + modelo) e **frontend**
(toggle de preferência). Release → **Via B** (backend tocado). Email (US3) não é
construído como envio real no MVP (gate STOP).

## Complexity Tracking

> Sem violações — secção não aplicável. (O STOP de email é evitado por desenho, não justificado como deviation.)
