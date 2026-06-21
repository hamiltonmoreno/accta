# Data Model: Fluxo Financeiro Unificado

Todas as alterações são **aditivas e opcionais** sobre modelos Pydantic existentes (`model_config = ConfigDict(extra="ignore")`), pelo que não quebram documentos em DB (não dispara STOP #5). Datas são strings ISO-8601.

## Entidades alteradas

### `Transaction` (`models.py:1232`)

| Campo | Antes | Depois | Nota |
|-------|-------|--------|------|
| `project_id` | — | `Optional[str] = None` | **NOVO**. Liga a despesa ao projeto que a originou. Coexiste com `ato_id`, `user_id`, `reference`. |

Restantes campos inalterados (`type`, `category`, `description`, `amount`, `date`, `reference`, `user_id`, `created_by`, `created_at`, `ato_id`, `proof_url`, `conferido`).

Invariantes:
- Uma despesa de projeto: `type="despesa"`, `category ∈ EXPENSE_CATEGORIES`, `project_id != None`.
- Se `ato_id != None`, a transação resultou de um Ato executado — não removível pela via de despesa de projeto.

### `Project` (`models.py:1386`)

| Campo | Mudança |
|-------|---------|
| `budget` | **Inalterado** — previsão/dotação. Não gera movimento de caixa. |
| `spent` | **Semântica muda**: deixa de ser contador autoritativo escrito a cada despesa; passa a ser **derivado** de `SUM(transactions where project_id, type="despesa")`. Mantido no modelo, preenchido na leitura. |

Vista derivada **Orçado vs. Realizado** (não persistida): `{ budget, realizado: spent_agregado, desvio: budget - realizado }`.

### `ProjectExpenseCreate` (`models.py:1503`)

| Campo | Antes | Depois |
|-------|-------|--------|
| `description` | `str (min_length=1)` | inalterado |
| `amount` | `float (gt=0)` | inalterado |
| `date` | `Optional[str]` | inalterado |
| `category` | — | **NOVO** `Optional[str] = None` → validado contra `EXPENSE_CATEGORIES`; default `operacional` na rota |

> `ProjectExpense` (modelo de resposta/persistência, `models.py:1475`) torna-se **legado**: já não é escrito após a migração. Não removido nesta ronda (leitura histórica).

### `Ato` (`models.py:1349`) e `AtoCreate` (`models.py:1325`)

| Campo | Mudança |
|-------|---------|
| `project_id` | **NOVO** `Optional[str] = None` em ambos. Propagado para a `Transaction` em `execute_ato`. |

### `RelatorioContasSubmit` (`models.py:2336`)

| Campo | Antes | Depois |
|-------|-------|--------|
| `document_id` | `str` (obrigatório) | `Optional[str] = None` (anexo opcional) |

## Coleções (DAO Mongo-compatível sobre Postgres)

| Coleção | Mudança |
|---------|---------|
| `transactions` | Passa a conter despesas de projeto (`project_id`). Novo índice de expressão `(doc->>'project_id')` em `ensure_schema()`. |
| `projects` | `spent` deixa de ser autoritativo (derivado). Sem mudança de schema. |
| `project_expenses` | **Legado** — deixa de ser escrita. Mantida para leitura histórica; opcionalmente ganha marca `migrated_to_transaction_id` durante a migração. |
| `atos` | Ganha `project_id` opcional nos docs novos. |
| `exercicios` | `relatorio_contas.document_id` pode ser `None` (submissão sem upload). `dre_snapshot` continua congelado. |

## Transições de estado

**Despesa de projeto (criação)**:
```
[pedido de despesa] --(amount <= limiar OU limiar=0)--> Transaction(type=despesa, project_id) criada
                    --(amount  > limiar)-------------> 400: exige Ato de pagamento (project_id pré-preenchido)
                                                        --> Ato aprovado --> execute_ato --> Transaction(ato_id, project_id)
```

**Despesa de projeto (remoção)**:
```
DELETE expense --(transação sem ato_id)--> apaga transação + audit; spent recomputado
               --(transação com ato_id)--> 400: segue regras do Ato (não removível por aqui)
```

**Submissão de Relatório e Contas** (inalterada exceto upload):
```
exercicio "aberto" --submeter_relatorio(document_id?)--> congela dre_snapshot --> "relatorio_submetido"
                                                          (document_id opcional: se presente, publica anexo)
```

## Regras de validação (de requisitos)

- FR-005: categoria de despesa de projeto ∈ `EXPENSE_CATEGORIES`; default `operacional`.
- FR-006: `amount > coaprovacao_limiar` ⇒ recusa criação direta (400, PT).
- FR-002/FR-003: `spent` derivado; `budget` nunca vira transação.
- FR-010: transação com `ato_id` não removível via despesa de projeto.
- FR-016/FR-017: `document_id` opcional na submissão; `dre_snapshot` sempre congelado.
- FR-019: números de relatórios derivam só de `transactions`.
