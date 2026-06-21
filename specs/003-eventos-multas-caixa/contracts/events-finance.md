# Contrato: Finanças de Evento

Prefixo: `/api/events`. Auth: `Bearer`. Guard: `has_role_or_privilege(admin, "manage_events")` (mesmo de gerir o evento). Audit em escritas.

## POST `/events/{event_id}/expenses`

Cria uma despesa do evento como `Transaction` no caixa.

**Body** (`EventExpenseCreate`): `{ description, amount>0, date?, category? }` (category ∈ EXPENSE_CATEGORIES; default `eventos`).

**Comportamento**:
1. 404 se evento não existe; 403 se sem `manage_events`.
2. Valida `category` (400 se inválida); default `eventos`.
3. **Gate Art. 54**: `limiar = coaprovacao_limiar()`; se `>0` e `amount>limiar` → 400 (PT, orientar para Ato com este evento).
4. Cria `Transaction(type="despesa", category, event_id, …)`; `create_audit_log`.

**200**: a `Transaction` criada. **Acceptance**: US1 #1; US3 #1.

## POST `/events/{event_id}/receitas`

Cria uma receita do evento (inscrições/patrocínios).

**Body** (`EventReceitaCreate`): `{ description, amount>0, date? }`.

**Comportamento**: 404/403 como acima; cria `Transaction(type="receita", category="extraordinarias", event_id, …)`; `create_audit_log`.

**200**: a `Transaction` criada. **Acceptance**: US1 #2.

## GET `/events/{event_id}/expenses` · GET `/events/{event_id}/receitas`

Listam `transactions.find({event_id, type})` (`despesa`/`receita`), `sort(date,-1)`, cap 500. Guard de leitura do evento.

## DELETE `/events/{event_id}/expenses/{tx_id}` · `/receitas/{tx_id}`

- 404 se transação não existe; 403 sem permissão.
- Se `ato_id` presente → **400** (reverter pelo Ato). (FR-009)
- Senão apaga a transação + `create_audit_log`. Resultado recomputado na leitura.

## GET `/events/{event_id}` — `resultado_financeiro` (alterado)

Passa a anexar `resultado_financeiro = { receitas, despesas, resultado }` (agregação sobre `transactions` com `event_id`). **Larga `response_model=Event`** e devolve dict enriquecido. **Acceptance**: US1 #3.

## DELETE `/events/{event_id}` — guarda (alterado)

Antes de apagar: conta `transactions` com `event_id`; se `>0` → **409** (PT: remover os movimentos primeiro). (FR-011)
