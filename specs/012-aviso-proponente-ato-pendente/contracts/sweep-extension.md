# Contract — Extensão do varrimento de Atos pendentes (aviso ao proponente)

**Sem rotas novas.** Estende o comportamento do varrimento da spec 010
(`notify_overdue_atos()`), usado por (a) o **loop diário** e (b) o endpoint admin
existente `POST /api/atos/notify-overdue`.

## Comportamento (por Ato `pendente` há > X dias, ainda sem `overdue_notified_at`)

1. **Direção** — avisada exatamente como na spec 010 (lista `members_of_orgao("direcao")`,
   mensagem «O ato "…" … está pendente há N dias e aguarda ação da Direção.»).
   **Inalterado** (SC-004).
2. **Proponente** (NOVO) — se `created_by ∉ direcao_ids` **e** o proponente é conta
   **ativa/não-técnica**, recebe um aviso próprio:
   - `type`: `financeiro`
   - título: «O seu ato continua pendente»
   - corpo (PT): «O ato que propôs ("<descrição>") continua pendente há N dias, a aguardar assinaturas da Direção.»
   - link: `/financeiro/co-aprovacoes`
3. **Marca** `overdue_notified_at` gravada **como hoje** (uma vez; só se houve
   destinatários Direção). Cobre ambos os avisos → **uma única vez** por Ato (Q1=A).

## Saída (contadores)

`notify_overdue_atos()` devolve, além dos da spec 010, **`notified_proponentes`** (nº de
proponentes avisados no evento).

## `POST /api/atos/notify-overdue` (admin, existente)

- Auth/RBAC/audit **inalterados** (admin-only, auditado — spec 011 review).
- Passa a refletir também os avisos ao proponente; resposta inclui `notified_proponentes`.
- Idempotente: 2.ª chamada seguida → `notified_atos: 0` e `notified_proponentes: 0`
  (marca partilhada já gravada).

## Não-objetivos

- Sem novo endpoint, sem novo agendador, sem novo limiar/config, sem campo novo, sem
  migração. Sem alteração ao aviso que a Direção já recebe. Email fora do âmbito.
