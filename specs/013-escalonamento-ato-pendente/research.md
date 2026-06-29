# Research: Escalonamento de lembretes de Ato pendente

Fase 0. Todas as clarificações de scope foram resolvidas no `spec.md` (decisões do dono).
Aqui resolvem-se as incógnitas **técnicas** que sustentam a abordagem de 1-linha.

## Decisão 1 — Mecanismo de recorrência: reutilizar `overdue_notified_at` como cursor

- **Decisão**: NÃO criar campo novo. A marca `overdue_notified_at` (ISO-8601 string já
  escrita pelas specs 010/012 a cada aviso) passa a significar **"instante do último
  lembrete"**. A elegibilidade do varrimento muda de `overdue_notified_at IS None`
  (single-shot) para `IS None OR overdue_notified_at <= (now − X dias)`.
- **Rationale**: o loop já **escreve `now` na marca a cada passo** (`update_one … $set
  overdue_notified_at = now.isoformat()`). Logo, sem nenhuma mudança na escrita, a marca já
  é um cursor de tempo; só faltava o filtro deixar voltar a apanhar Atos cujo cursor
  envelheceu ≥ X dias. Custo: **1 cláusula de filtro**. Zero campos/migração/coleção.
- **Alternativas rejeitadas**:
  - *Campo novo `last_reminded_at` + `reminder_count`*: redundante — `overdue_notified_at`
    já guarda o timestamp; um contador não é preciso porque a paragem é "sair de pendente"
    (sem teto, Q3) e a cadência é puramente temporal.
  - *Marcos fixos 7/14/30 (lista)*: rejeitado pela decisão do dono (cadência = a cada X).
  - *Novo agendador/cron*: rejeitado — reutiliza o loop diário in-process da spec 010.

## Decisão 2 — Cutoff por comparação de string ISO (`$lte`)

- **Decisão**: o cutoff é `(now − timedelta(days=X)).isoformat()` e compara-se com
  `{"overdue_notified_at": {"$lte": cutoff}}`.
- **Rationale (verificado no DAO)**: `_WhereBuilder._field_clause` mapeia `$lte` →
  `_cmp(field, "<=", val)`; para um `val` **string**, `_cmp` gera
  `(doc->>'overdue_notified_at') <= $n` — **comparação de TEXTO** (`database.py:308`). Para
  timestamps `datetime.now(timezone.utc).isoformat()` (todos UTC, mesmo formato/sufixo
  `+00:00`), a ordem lexicográfica **coincide** com a ordem cronológica. Logo a comparação é
  correta sem cast para timestamp. (Cuidado análogo ao da spec 010, mas aqui a operação é
  `$lte` sobre texto, não `$ne`/`IS DISTINCT FROM`.)
- **Alternativas rejeitadas**: cast a `::timestamptz` no DAO — desnecessário e fora do
  subconjunto suportado; introduziria SQL especial só para isto.

## Decisão 3 — `$or` ao nível de topo combinado com `status`

- **Decisão**: filtro `{"status": "pendente", "$or": [{"overdue_notified_at": None},
  {"overdue_notified_at": {"$lte": cutoff}}]}`.
- **Rationale**: o DAO suporta `$or` (lista de subfiltros) **AND**-combinado com as outras
  chaves de topo (documentado em `.claude/rules/database.md`; já usado noutras rotas). O
  ramo `{"overdue_notified_at": None}` usa `_eq(None)` → `(NOT (doc ? key) OR doc->>key IS
  NULL)`, que apanha tanto a chave ausente (Atos legados) como o valor `null` (Atos novos) —
  exatamente o comportamento provado na spec 010. O ramo `$lte` apanha as marcas reais já
  envelhecidas. `NULL <= cutoff` é NULL (falso) ⇒ não há sobreposição perigosa entre os dois
  ramos.

## Decisão 4 — Mensagem e destinatários: reutilizar tal-qual (sem ramo "primeiro vs recorrente")

- **Decisão**: o corpo e os destinatários dos avisos **não mudam**. A antiguidade (`idade`)
  é recalculada a cada passo e já aparece no corpo (specs 010/012), comunicando a urgência
  crescente (FR-005). Não se distingue "primeiro aviso" de "lembrete recorrente" no texto.
- **Rationale**: a decisão do dono é "só tom/urgência via antiguidade, mesmos
  destinatários". A `idade` no corpo já entrega isso; um ramo separado seria complexidade sem
  valor. A dedup proponente∈Direção (spec 012) e as exclusões `technical`/`inativo`
  permanecem intactas.

## Riscos / notas

- **Import**: confirmar que `routes/atos.py` importa `timedelta` (necessário para o cutoff);
  se não, adicionar ao import de `datetime`.
- **Idempotência intra-dia**: como cada lembrete escreve `overdue_notified_at = now`, um
  segundo disparo no mesmo dia não re-apanha o Ato (cursor `now` > cutoff). SC-002 garantido.
- **Migração retroativa**: nenhuma. Atos já marcados pelas specs 010/012 voltam a qualificar
  naturalmente quando o cursor passar X dias — sem reprocessamento em massa.
