# Quickstart / Validação: Eventos e Multas Ligados ao Caixa

Guia de validação end-to-end. Detalhes em `data-model.md` e `contracts/`.

## Pré-requisitos

- Backend local: `cd backend && uvicorn server:app --reload --port 8001` (Postgres acessível).
- Login admin (ou conta com `manage_events` + disciplina). `bcrypt==4.0.1`.
- Testes: `cd backend && pytest` (unit/in-process com `mock_db`; wire `events`/`sancoes`/`atos`/`transactions` conforme `conftest.py`).

## Cenário 1 — Resultado financeiro do evento (US1)

1. `coaprovacao_limiar=0` (ou despesas abaixo).
2. Criar evento; `POST /api/events/{id}/expenses` `{description:"Sala", amount:8000, category:"eventos"}`.
3. `POST /api/events/{id}/receitas` `{description:"Inscricoes", amount:12000}`.
4. **Esperado**:
   - `GET /api/finances/transactions?event_id={id}` devolve 2 movimentos (despesa 8000, receita 12000).
   - `GET /api/events/{id}` → `resultado_financeiro={receitas:12000, despesas:8000, resultado:4000}`.
   - `GET /api/finances/summary` do período: `total_despesas` +8000, `total_receitas` +12000.
   - Audit logs das criações.

## Cenário 2 — Gate Art. 54 em despesa de evento (US3)

1. `coaprovacao_limiar=50000`.
2. `POST /api/events/{id}/expenses` `amount=70000` → **400** (PT, pede Ato).
3. `POST /api/atos` `{tipo:"pagamento", valor:70000, event_id:"{id}", descricao:...}`; assinar (2 Direção + Presidente + Tesoureiro).
4. `POST /api/atos/{ato}/executar` → despesa com `ato_id` **e** `event_id`.
5. `DELETE /api/events/{id}/expenses/{essa_tx}` → **400** (tem `ato_id`).

## Cenário 3 — Multa entra no caixa ao aplicar (US2)

1. Criar sanção `tipo="multa"`, `multa_valor=6000`; levar a `decidida` (comissão/decidir aprovado).
2. `POST /api/sancoes/{id}/aplicar` → 200, status `aplicada`.
3. **Esperado**:
   - `GET /api/finances/transactions?sancao_id={id}` → 1 receita 6000, `extraordinarias`.
   - `/summary` do período: `total_receitas` +6000.
4. Re-aplicar (409 esperado) → **não** cria 2.ª receita (exactly-once).
5. Aplicar uma sanção `tipo="advertencia"` → **nenhum** movimento criado.

## Cenário 4 — Eliminação de evento bloqueada

1. Evento com ≥1 movimento no caixa.
2. `DELETE /api/events/{id}` → **409** (remover os movimentos primeiro).

## Cenário 5 — UI (US4)

1. Abrir detalhe de evento no browser.
2. **Esperado**: secção financeira (registar despesa c/ categoria, registar receita, listas, resultado); mensagem amigável quando o gate Art. 54 recusa. Botões neutros/Floresta (frontend-design).

## Migração (STOP — só após confirmação do dono)

1. **Dry-run**: `python scripts/migrate_multas_to_transactions.py`
   - Lista sanções `multa`/`aplicada`/`valor>0` sem receita com esse `sancao_id`; reconciliação; não escreve.
2. Rever com o dono.
3. **`--apply --confirm`** (após OK): cria as receitas em falta (idempotente).
4. **Esperado**: multas históricas refletidas; sem duplicados (SC-006). Prod provável no-op (0 sanções).

## Critério de pronto (Princípio VII)

- [ ] `pytest` verde para os novos testes (despesas/receitas de evento, gate, resultado, filtros, multa-ao-aplicar idempotente, delete 409).
- [ ] Cenários 1–4 via HTTP; Cenário 5 no browser (screenshot).
- [ ] Backfill validado em dry-run; `--apply` só após confirmação.
