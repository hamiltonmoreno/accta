# Data Model: Eventos e Multas Ligados ao Caixa

Alterações **aditivas e opcionais** sobre modelos Pydantic existentes (`extra="ignore"`) — não quebram docs em DB. Datas ISO-8601 string.

## Entidades alteradas

### `Transaction` (`models.py:1232`)

| Campo | Antes | Depois | Nota |
|-------|-------|--------|------|
| `event_id` | — | `Optional[str] = None` | **NOVO**. Liga a despesa/receita ao evento. |
| `sancao_id` | — | `Optional[str] = None` | **NOVO**. Liga a receita de multa à sanção. |

Coexistem com `project_id`, `ato_id`, `user_id`, `reference`. Invariantes:
- Despesa de evento: `type="despesa"`, `category ∈ EXPENSE_CATEGORIES`, `event_id != None`.
- Receita de evento: `type="receita"`, `category="extraordinarias"`, `event_id != None`.
- Receita de multa: `type="receita"`, `category="extraordinarias"`, `sancao_id != None`.

### `Ato` (`models.py:1349`) e `AtoCreate` (`models.py:1325`)

| Campo | Mudança |
|-------|---------|
| `event_id` | **NOVO** `Optional[str] = None` em ambos. Propagado para a `Transaction` em `execute_ato` (a par de `project_id`). |

### `Event` (`models.py:858`)

Sem mudança de campos persistidos. A resposta de `GET /events/{id}` ganha um bloco **derivado** (não persistido):
`resultado_financeiro = { receitas, despesas, resultado }` (resultado = receitas − despesas), agregado de `transactions` com `event_id`.

### Modelos de request novos

```
EventExpenseCreate: description (min 1), amount (>0), date? , category? (∈ EXPENSE_CATEGORIES; default "eventos" na rota)
EventReceitaCreate: description (min 1), amount (>0), date?
```

## Coleções

| Coleção | Mudança |
|---------|---------|
| `transactions` | Passa a conter despesas/receitas de evento (`event_id`) e receitas de multa (`sancao_id`). Novos índices `ix_tx_event_type`, `ix_tx_sancao` em `ensure_schema()`. |
| `events` | Sem mudança de schema. Detalhe expõe `resultado_financeiro` derivado. |
| `sancoes` | Sem mudança de schema. Ao aplicar multa, gera a receita ligada (`sancao_id`). |
| `atos` | Ganha `event_id` opcional nos docs novos. |

## Transições de estado

**Despesa de evento (criação)**:
```
[pedido] --(amount<=limiar OU limiar=0)--> Transaction(despesa, event_id)
        --(amount>limiar)--------------> 400: exige Ato (event_id pré-preenchido)
                                          --> Ato aprovado --> execute_ato --> Transaction(ato_id, event_id)
```

**Despesa de evento (remoção)**:
```
DELETE --(sem ato_id)--> apaga transação + audit; resultado recomputado
       --(com ato_id)--> 400: segue regras do Ato
```

**Multa (aplicação)** — `aplicar_sancao`, antes do CAS:
```
decidida --aplicar--> [efeitos idempotentes] + (tipo=multa & valor>0 & sem receita p/ sancao_id)
                       --> insert Transaction(receita, extraordinarias, sancao_id)
                     --CAS decidida->aplicada (exactly-once)--> "aplicada"
```

**Eliminação de evento**:
```
DELETE /events/{id} --(0 transações com event_id)--> apaga evento
                    --(>0)--> 409: remover os movimentos primeiro
```

## Regras de validação (de requisitos)

- FR-004: categoria de despesa de evento ∈ EXPENSE_CATEGORIES; default "eventos".
- FR-007: `amount > coaprovacao_limiar` ⇒ recusa criação direta (400, PT).
- FR-009: transação com `ato_id` não removível pela via de evento.
- FR-012/013/014: receita de multa só para `tipo=="multa"` com `multa_valor>0`, exactly-once por `sancao_id`.
- FR-017: receitas (evento/multa) em `extraordinarias`; sem categorias novas.
- FR-006: `resultado_financeiro` derivado das transações do evento.
