---
name: review-eventos-multas-caixa-v0526-main
description: Code review of spec-003 "eventos e multas ligados ao caixa" diff v0.5.26..origin/main (v0.5.27 in prod)
metadata:
  type: project
---

Reviewed 2026-06-22. Diff covers: database.py (indexes), helpers.py (coaprovacao_limiar refactor), models.py (event_id/sancao_id on Transaction/Ato), routes/events.py (finance endpoints), routes/sancoes.py (multa→caixa), routes/atos.py (event_id propagation), routes/finances.py (filter/delete guard), routes/projects.py (import fix), scripts/migrate_multas_to_transactions.py, frontend EventosPage.js + EventFinanceDialog, utils/api.js, lib/queryClient.js.

**Verdict: No CRITICAL found.**

Key findings:

WARNING W1 — sancoes.py: CAS compensation window (lines 316–349). The find_one→insert_one→CAS sequence has a theoretical race where two concurrent calls both read `existing_tx=None`, both insert, and the "loser" CAS triggers the compensation delete. This is handled correctly in the code (multa_tx_id tracks only this call's insert; delete_one by id is precise). The remaining tiny gap is: what if the loser's delete_one also fails (network error)? No rollback or alert — leaves a duplicate receita. Marked WARNING not CRITICAL because the DAO is single-writer async (asyncpg pool sequential per connection) and the UNIQUE index on sancao_id was discussed but not added; adding one would close this fully.

WARNING W2 — EventFinanceDialog invalidation gap: `invalidate()` calls `qc.invalidateQueries({ queryKey: queryKeys.events.byId(eid) })`. `byId(eid)=['events',eid]` is a prefix of `expenses=['events',eid,'expenses']` and `receitas=['events',eid,'receitas']` so TanStack Query prefix matching does invalidate all three. BUT `queryKeys.events.list()=['events']` (the event list in EventosPage) is NOT invalidated when finance dialog closes — the `resultado_financeiro` shown inline in cards (if any) would be stale. However, `resultado_financeiro` is not shown in the list cards (only in the finance dialog), so this is low-impact.

WARNING W3 — database.py: DROP INDEX runs on every startup restart inside ensure_schema(). `DROP INDEX IF EXISTS ix_tx_project` is a DDL operation that acquires a brief ACCESS EXCLUSIVE lock on the `transactions` table. On a live system under load this could cause momentary query queue. Should be removed once all environments are upgraded.

SUGGESTION S1 — sancoes.py: No UNIQUE index on `(sancao_id)` in transactions would be the hard idempotency guarantee vs. the current advisory check-then-insert. The ix_tx_sancao partial index exists for query performance but is NOT a unique constraint. A race between two concurrent aplicar_sancao calls can still produce a duplicate receita if the compensation delete fails.

SUGGESTION S2 — migrate_multas_to_transactions.py: The idempotency check queries `{"type":"receita","sancao_id":{"$exists":True}}` — gets ALL receita-sancao transactions and builds `done_ids` set. This is correct and leverages the DAO's $exists support. No bug; just note it loads all such rows into memory (acceptable given low volume of multas).

SUGGESTION S3 — EventFinanceDialog: The delete button for each row has no confirmation dialog. A misclick permanently removes a caixa entry. Low risk (protected by ato_id guard on the backend), but UX is abrupt.
