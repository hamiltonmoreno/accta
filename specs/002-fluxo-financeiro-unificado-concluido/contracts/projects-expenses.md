# Contrato: Despesas de Projeto (unificadas no caixa)

Prefixo: `/api/projects`. Auth: `Bearer`. Guard: `can_manage_project` (responsável/gestor do projeto) — ver Decisão 5 (research). **Adiciona audit log** (hoje ausente).

## POST `/projects/{project_id}/expenses`

Cria uma **despesa real** do projeto. Passa a persistir uma `Transaction` (não `project_expenses`).

**Request body** (`ProjectExpenseCreate`):
```json
{
  "description": "Aluguer de sala para workshop",
  "amount": 5000,
  "date": "2026-03-15",            // opcional; default hoje
  "category": "eventos"            // NOVO, opcional; default "operacional"; ∈ EXPENSE_CATEGORIES
}
```

**Comportamento**:
1. 404 se projeto não existe; 403 se sem `can_manage_project`.
2. Valida `category ∈ EXPENSE_CATEGORIES` (400 caso contrário); default `operacional`.
3. **Gate Art. 54**: lê `coaprovacao_limiar`; se `> 0` e `amount > limiar` → **400** com mensagem PT:
   `"Despesa de {amount} CVE excede o limiar de co-aprovacao ({limiar} CVE). Crie um Acto de pagamento (projeto associado) e execute-o apos aprovacao."`
4. Caso contrário cria `Transaction(type="despesa", category, description, amount, date, project_id=project_id, created_by)`.
5. `create_audit_log(...)` (NOVO).
6. Notifica stakeholders do projeto; alerta se `spent` derivado > `budget`.

**Response 200**: a `Transaction` criada (inclui `id`, `project_id`).

**Acceptance**: US1 cenário 1; US2 cenários 1 e 3.

## GET `/projects/{project_id}/expenses`

Lista as despesas do projeto = `transactions.find({project_id, type:"despesa"}).sort(date,-1)`.

**Response 200**:
```json
{ "items": [ { "id": "...", "amount": 5000, "category": "eventos", "date": "...", "ato_id": null, "project_id": "..." } ] }
```

## DELETE `/projects/{project_id}/expenses/{expense_id}`

- 404 se projeto/transação não existe; 403 se sem permissão.
- Se a transação tiver `ato_id` → **400**: `"Despesa originada por um Acto executado; reverta pelo Acto."` (FR-010).
- Caso contrário apaga a transação (`{id: expense_id, project_id, type:"despesa"}`) + `create_audit_log`. `spent` recomputado na próxima leitura.

**Response 200**: `{ "message": "Despesa removida" }`.

## Projeto: `spent` e Orçado vs. Realizado

- **Detalhe** `GET /projects/{id}`: `spent` = agregação `SUM(transactions where project_id, type="despesa")`. Resposta inclui `budget`, `spent` e (novo) bloco `orcamento_execucao: { budget, realizado, desvio }`.
- **Listagem** `GET /projects`: `spent` de todos os projetos via **uma** agregação `$group` por `project_id` (sem N+1).
