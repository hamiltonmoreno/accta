# Data Model — Aviso à Direção de Ato pendente

Apenas **campos aditivos** em modelos existentes. Sem coleções novas, sem migração de dados
(documentos antigos sem os campos ⇒ tratados como "não avisado" / default). Sem novos índices
(o varrimento filtra `status=="pendente"`, conjunto pequeno).

## Ato (existente — `models.py` `class Ato`, coleção `atos`)

| Campo | Tipo | Default | Notas |
|------|------|---------|-------|
| `overdue_notified_at` | `Optional[str]` (ISO-8601) | `None` | **NOVO, aditivo.** Marca de "já avisado" (FR-005). Ausente/`None` ⇒ ainda não avisado. Gravado no momento em que o Ato cruza o limiar e gera o aviso. |

- **Idade do Ato** = `now - created_at` (campo existente; data de referência por Assumption da spec).
- **Estado relevante**: só `status == "pendente"`. Sair de pendente (`aprovado/rejeitado/executado/cancelado`)
  ⇒ deixa de ser considerado (FR-006). A marca nunca é limpa (não há re-aviso por desenho).

## FinanceSettings (existente — `models.py` `class FinanceSettings`, singleton `finance_settings`)

| Campo | Tipo | Default | Notas |
|------|------|---------|-------|
| `ato_overdue_dias` | `int` | `7` | **NOVO, aditivo.** Limiar X em dias (FR-004). Lido pelo varrimento; default 7 quando o doc não o tem (leitura already-default-on-missing). |

- `FinanceSettingsUpdate` ganha `ato_overdue_dias: Optional[int] = None` (PATCH parcial existente só grava
  campos não-`None`). Validação mínima de fronteira: `>= 1` (admin é input boundary).

## Entidades reutilizadas (sem alteração)

- **Notification** (`notifications`): criada via `notify_users(...)` — título/mensagem PT + `link =
  "/financeiro/co-aprovacoes"`. Tipo `"financeiro"` (consistente com os avisos de Ato existentes).
- **User** (`users`): destinatários via `members_of_orgao("direcao")` — exclusão de técnicos/inativos
  herdada (FR-007).

## Regras de validação / transições

- Dispara aviso ⇔ `status=="pendente"` **E** `overdue_notified_at` ausente **E**
  `(now - created_at).days > ato_overdue_dias` **E** `created_at` parseável.
- Pós-aviso: `overdue_notified_at = now.isoformat()` (idempotência).
- `created_at` ausente/inválido ⇒ Ato ignorado (sem disparo por data não fiável).
