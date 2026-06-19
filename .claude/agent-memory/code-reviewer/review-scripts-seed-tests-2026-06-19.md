---
name: review-scripts-seed-tests-2026-06-19
description: Findings from 2026-06-19 review of drop-invoices DDL scripts, seed_data.py, runbook, and finance/test changes (PR #276 follow-up)
metadata:
  type: project
---

## Summary

Review of DDL artefacts for drop-invoices (issue #281), seed_data.py migration invoices→transactions, and test suite additions.

## DDL Safety — CLEAN

- `scripts/sql/2026-06-19-drop-invoices.sql`: DO block checks `to_regclass` (idempotent) and `count(*)`, RAISE EXCEPTION aborts before DROP when n≠0. Correct.
- `scripts/drop_invoices_table.py`: dry-run by default, `--apply --confirm` double gate, `sys.exit(3)` on non-empty, post-DROP existence check. Correct.
- Runbook: precondition (PR #276 deployed before DROP, else ensure_schema recreates) documented. Caminho A (SQL Editor) and B (Python script) both documented correctly.

## Seed — CLEAN with one non-blocking note

- `seed_data.py`: quota_txs use `type="receita"`, `category="quotas"`, `user_id`, `date` (ISO string), `description`, `amount`, `reference`, `created_by`. All fields match Transaction model and `list_my_quotas` query.
- `created_by="seed"` is a non-UUID string. Transaction.created_by is `str` (not Optional). The DAO inserts raw dicts so Pydantic validation is not exercised here. No functional problem at runtime but inconsistent with user-id convention.
- collection-clear list: "invoices" replaced by "transactions". Correct.

## Tests — two WARNING-level gaps found

1. `test_filters_by_own_user_id` (test_finances_routes.py ~596): captures query and asserts user_id/type/category. The `find()` side_effect returns `_cursor([])` which has `.sort` returning itself. But the test does NOT assert `.to_list` was called with `None` — so the unbounded fetch behavior is not locked in by this test. Not a blocker, but the regression test for "no cap" exists only on DRE/generate_quotas, not on list_my_quotas.
2. `test_my_quotas_requires_auth` (test_accta_portal.py, integration): asserts 401 or 403 on unauthenticated access. /me/quotas uses `Depends(get_current_user)` which raises 401 by default — test is correct but allows 403, which is looser than the actual behavior.

## Patterns fixed in this batch (from prior C1/W)

- TOCTOU on sign_ato: fixed via `sign_ato_atomic` DAO helper + monkeypatch pattern in tests.
- send_invite_email now via BackgroundTasks (apurar_honorario) — email failure can no longer 500 after CAS commit.
- regulamentos draft visibility: new TestVisibilidadeNaoGestor confirms non-managers don't see rascunhos.
- DRE/generate_quotas to_list(None) regression tests: correct.

**How to apply:** No CRITICALs in this batch. Prior C1 (sign_ato TOCTOU) is now closed.
