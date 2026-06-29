# Contracts — Aviso à Direção de Ato pendente

A feature é maioritariamente **interna** (loop in-process). Superfície externa = 1 campo de
definições (endpoint existente) + 1 endpoint admin opcional para verificação/disparo manual.

## 1. Configuração do limiar X — endpoint EXISTENTE

`PATCH /api/finances/settings` (admin-only — `routes/finances.py:488-587`) passa a aceitar o campo
aditivo:

```jsonc
// request body (parcial; só campos não-null são gravados)
{ "ato_overdue_dias": 10 }
```

```jsonc
// GET /api/finances/settings → inclui o campo (default 7 se nunca configurado)
{ "id": "finance_settings", "ato_overdue_dias": 7, /* ...restantes campos... */ }
```

- 403 se não-admin (já garantido pelo endpoint). Validação: `ato_overdue_dias >= 1`.
- **Sem novo endpoint** para US2.

## 2. Disparo manual / verificação — endpoint NOVO (opcional, admin-only)

`POST /api/atos/notify-overdue` — corre `notify_overdue_atos()` uma vez (mesmo código do loop diário).
Existe para **provar o comportamento sem esperar 24h** (Princípio VII) e para um disparo administrativo
pontual.

```jsonc
// 200 OK
{ "evaluated": 12, "overdue": 3, "notified_atos": 3, "recipients": 4 }
```

- **Auth**: `Depends(get_current_user)` + `current_user.role == "admin"` (403 caso contrário).
- **Idempotente**: chamar 2× seguidas ⇒ a 2.ª devolve `notified_atos: 0` (marca `overdue_notified_at`).
- Sem membros de Direção ⇒ 200 com `recipients: 0` e `notified_atos: 0` — **não** se gera aviso nem se
  grava a marca (ver nota).

> **Nota de semântica (sem destinatários) — AUTORITATIVO (= T005)**: se não há Direção, não se gera
> aviso **nem** se grava `overdue_notified_at` — assim, quando houver Direção, o Ato ainda atrasado
> será avisado. (FR-009: sem erro; o sistema continua.) A spec exige apenas "sem erro"; esta é a
> decisão fixada e implementada em T005.

## 3. Comportamento interno (não-HTTP) — `notify_overdue_atos()`

Contrato da função (reutilizada por loop + endpoint):

- **Lê** `ato_overdue_dias` de `finance_settings` (default 7).
- **Seleciona** Atos `status=="pendente"` sem `overdue_notified_at`.
- **Filtra** por idade > X (parse defensivo de `created_at`; inválido ⇒ skip).
- **Resolve** destinatários `members_of_orgao("direcao")`.
- Por cada Ato qualificado com destinatários: `notify_users(direcao_ids, "financeiro", titulo, msg,
  "/financeiro/co-aprovacoes")` (PT, inclui descrição/tipo/valor + antiguidade) e grava
  `overdue_notified_at`.
- **Devolve** contadores (para o endpoint/logs). Nunca levanta para fora (loop non-fatal).
