# Phase 1 — Data Model: Lembrete de Ato pendente ao próprio proponente

**Sem alterações de schema, sem campos novos, sem migração.** A feature partilha o
estado da spec 010 e deriva a elegibilidade de campos já existentes em `users`.

## Ato (`backend/models.py`) — inalterado

- `created_by` (existente): o **proponente** = destinatário do novo aviso.
- `overdue_notified_at` (existente, spec 010): **marca partilhada** de "já avisado neste
  evento" — gravada uma vez por Ato; cobre o aviso à Direção **e** ao proponente.
- `status` / `created_at` (existentes): gatilho `pendente` + antiguidade.

## users (coleção) — leitura, sem alteração

Elegibilidade do proponente (FR-007), apurada por **uma** query ao conjunto distinto de
`created_by` dos Atos overdue:

| Campo | Uso |
|-------|-----|
| `id` | casar com `Ato.created_by` |
| `status` | elegível se **`ativo`** (exclui `inativo`/`pendente_*`/`rejeitado`) |
| `account_type` | elegível se **≠ `technical`** (ausente ⇒ tratado como membro) |

`eligible_proponentes = { u.id : status==ativo AND account_type!=technical }`.

## Contadores devolvidos por `notify_overdue_atos()` (extensão)

| Chave | Origem | Notas |
|-------|--------|-------|
| `evaluated` / `overdue` / `recipients` / `notified_atos` | spec 010 | inalterados |
| `notified_proponentes` | **NOVO** | nº de proponentes avisados neste evento (observabilidade) |

## Regra de decisão (por Ato overdue)

1. Avisar a Direção **como hoje** (`direcao_ids`, mensagem da spec 010). *(inalterado)*
2. `proponente = ato.created_by`. Avisar o proponente **sse**
   `proponente not in direcao_ids` **e** `proponente in eligible_proponentes`.
3. Gravar `overdue_notified_at` **como hoje** (uma vez, só se houve destinatários
   Direção — invariante da spec 010 preservado).

## Transições de estado — inalteradas

`pendente` (> X dias, sem marca) → [avaliação diária] → avisa Direção (+proponente
elegível não-Direção) → grava `overdue_notified_at`. Sair de `pendente` ⇒ deixa de
qualificar.
