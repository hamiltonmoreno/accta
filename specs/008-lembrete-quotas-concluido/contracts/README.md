# Contracts — Lembrete informativo de quotas

A feature **não cria** endpoints novos de "lembrete" — o lembrete é um **efeito** do
fluxo existente. Os contratos tocados:

## `POST /api/finances/generate-quotas` (existente — comportamento alterado)

Inalterado no contrato (request/response: `month`, `year` → `{created, skipped, total_value}`).
**Muda o efeito secundário**: em vez de **uma** notificação genérica a todos os ativos
(link `/financeiro`), cria **uma notificação por sócio** que recebeu quota nova —
título/corpo informativos com o **valor do período** e o **total acumulado**, link
**`/carteira`** — saltando sócios com `quota_reminder_opt_out`, contas técnicas e inativos.
Continua a exigir `manage_finances` e a auditar.

## Preferência de lembrete (self-service)

Atualização de `quota_reminder_opt_out` do **próprio** sócio, no padrão das preferências
existentes (`PATCH` de preferências de comunicação; `Depends(get_current_user)`, sem
privilégio, escreve só o próprio user). Reutiliza/estende o endpoint de preferências de
email já existente, ou um análogo dedicado.

- **200**: preferência atualizada (reflete no `/auth/me`).
- **401**: não autenticado.

## Email (US3) — gated, não construído no MVP

Nenhum contrato de envio de email é ativado no MVP. Qualquer envio real a utilizadores
é **condição STOP** e fica atrás de confirmação explícita do dono + flag off por defeito.
