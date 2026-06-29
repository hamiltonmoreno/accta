# Phase 1 — Data Model: Aviso de rejeição de Ato com o motivo

Nenhuma tabela/coleção/índice novo. Só campos **aditivos** num modelo de request e no
sub-documento de assinatura já existente. Sem migração (jsonb).

## AtoSign (request model — `backend/models.py`)

| Campo | Tipo | Notas |
|-------|------|-------|
| `decisao` | `str` | Existente. `"aprovado"` \| `"rejeitado"`. |
| `motivo` | `Optional[str] = None` | **NOVO, aditivo.** Justificação da rejeição. Obrigatório quando `decisao == "rejeitado"` (validado na rota); ignorado se `aprovado`. Máx. 500 carateres; `strip()` aplicado. |

**Validação (regra de negócio, na rota `sign_ato`):**

- `decisao == "rejeitado"` e `motivo` ausente/só-espaços → **400** «É obrigatório
  indicar o motivo da rejeição.»
- `len(motivo.strip()) > 500` → **400** «O motivo não pode exceder 500 carateres.»
- `decisao == "aprovado"` → `motivo` ignorado (não gravado).

## Assinatura (sub-documento em `Ato.assinaturas[]` — jsonb, sem modelo Pydantic próprio)

Construída na rota e persistida por `database.sign_ato_atomic` (inalterado).

| Chave | Origem | Notas |
|-------|--------|-------|
| `user_id` | existente | quem assinou |
| `cargo` | existente | cargo do assinante |
| `decisao` | existente | `aprovado` \| `rejeitado` |
| `signed_at` | existente | ISO-8601 UTC |
| `motivo` | **NOVO** | só presente quando `decisao == "rejeitado"`; o `motivo.strip()` |

## Ato (`backend/models.py`)

**Sem alteração.** O motivo NÃO é denormalizado no Ato — lê-se da assinatura cuja
`decisao == "rejeitado"` (há no máximo uma, pelo modelo de veto único). A vista de
detalhe mostra esse motivo + o `user_id`/`cargo` dessa assinatura (quem rejeitou).

## Fluxo de estado (inalterado, contexto)

`pendente` → (qualquer assinatura `rejeitado`) → **`rejeitado`** [veto único,
`atos_rules.evaluate_status`]. A novidade é só o `motivo` que acompanha a assinatura de
rejeição e que alimenta o aviso ao proponente.
