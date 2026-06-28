# Data Model — Lembrete informativo de quotas

Alteração de dados **mínima**: 1 campo aditivo em `users`. Sem migração destrutiva.

## `users` (existente) — + 1 campo

| Campo | Tipo | Default | Uso |
|-------|------|---------|-----|
| `quota_reminder_opt_out` | bool | `False` | Se `True`, o sócio não recebe lembretes de quota (in-app e, se ligado, email). Aditivo: docs sem o campo → tratado como `False` (recebe). **Não** é STOP #5 (não quebra docs existentes). |

Distinto de `email_opt_out_informativos` (esse é específico de **email de comunicados**).

## `transactions` (existente, leitura) — fonte dos valores

- Valor do período: `quota_amount` (das `finance_settings`, já lido no gerador).
- Total acumulado por sócio: aggregate `group by user_id`, `sum(amount)` sobre
  `type=receita` + `category ∈ {quotas,joias}` (= `total_pago` de `/me/quotas`).

## `notifications` (existente, escrita) — o lembrete

Criada via `create_notification(user_id, type="financeiro", title, message, link="/carteira")`,
uma por sócio que recebeu quota nova. Sem nova coleção.

## Modelos Pydantic

- `User`/`UserBase`: + `quota_reminder_opt_out: bool = False` (leitura/escrita).
- Novo modelo de update de preferência (ou estender o de prefs existente) com
  `quota_reminder_opt_out: bool` — self-service (próprio user).

## Idempotência (sem entidade nova)

Garantida pela geração: `insert_quotas_atomic` devolve os user_ids **novos**; só esses
são notificados. Re-gerar o mês → 0 novos → 0 lembretes. Sem marcador de período extra.

## State transitions

N/A.
