---
name: review-be-dao
description: findings from be-dao unit review of backend/database.py (branch chore/coderabbit-baseline, 2026-06-04)
metadata:
  type: project
---

Review of backend/database.py (1297 lines, Mongo-compatible asyncpg DAO).

Key findings recorded for future context:

1. `_purge_ttl` (line 565) interpolates the TTL field name directly into SQL without `_safe_jsonb_key` — inconsistent with the defensive pattern used in `_cast_secret_ballot_locked`. Fixed by wrapping: `doc->>'{_safe_jsonb_key(field)}'`.

2. `REQUIRED_INDEX_NAMES` (lines 989-992) only guards `ux_votes_user_poll` + `ux_eleicao_receipt`. Missing: `ux_assembpres_assemb_user`, `ux_assembvoto_delib_user`, `ux_assembvotoreceipt_delib_hash` — all three are concurrency backstops noted in code comments.

3. `_PGCRON_DDL` (lines 1006-1010) uses bare `cron.schedule()` which is NOT idempotent — duplicate jobs accumulate on every restart when pg_cron is available. Should use `cron.unschedule()` + `cron.schedule()` or check existence first.

4. `_aggregate` pipeline (lines 668-671) fetches ALL `$match` results into Python before grouping/limiting — performance risk on large collections (transactions, audit_logs).

**Why:** These are correctness/data-integrity gaps, not security vulnerabilities. The DAO is otherwise well-structured.
**How to apply:** Flag these when reviewing future DAO changes or when cron/schema issues are reported.
