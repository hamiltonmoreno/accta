---
name: review-finances-governance
description: Findings from finances/governance backend review (finances.py, invoices.py, report.py, prestacao_contas.py, regulamentos.py, assembleias.py, eleicoes.py, sancoes.py, governance.py, atos.py, participacao.py)
metadata:
  type: project
---

## Critical finding — CLOSED (2026-06-19 via PR #275 / c3710b1)

**atos.py `sign_ato` — TOCTOU race on co-approval signatures — FIXED.** Resolved via `sign_ato_atomic` DAO helper (FOR UPDATE / advisory lock pattern, mirroring cast_ballot). Tests updated in test_atos.py with `_wire_sign_atomic` monkeypatch. Status codes updated to 409 where appropriate. Prior C1 is no longer a blocker.

## Re-review 2026-06-19 (develop vs main, next release batch)

### CLOSED findings from prior warnings
- **participacao.py email sync on invite — FIXED** via BackgroundTasks in apurar_honorario. send_invite_email is now fire-and-forget (background_tasks.add_task). The 500 risk is gone.
- **participacao.py vote-window race — FIXED** votes now read BEFORE polls.update_one closes the poll.
- **finances.py silent truncation (5000 cap) — FIXED** across compute_financial_summary, compute_dre_report, generate_monthly_quotas (1000 cap), CSV export. All use to_list(None).
- **regulamentos.py draft visibility — FIXED** list_regulamentos now filters to only approved-version regs for non-managers; get_regulamento 404s when no approved version exists.

### New findings in this batch (2026-06-19)

**WARNING: profissional.py `get_publicacao` (line 253) — stale `noqa: ARG001` comment.** `current_user` IS now used in the function body (visibility check). The noqa suppressor masks a real ruff warning that should be removed so linting is accurate.

**SUGGESTION: regulamentos.py `list_regulamentos` — N+1 query pattern.** One `find_one` per regulamento to fetch its current_version. Pre-existing; not introduced in this diff but now harder to miss since the function gained a visibility-filter loop.

**SUGGESTION: `cta_qualified_since` future-date check uses `date.today()` (server local TZ, not UTC).** In a UTC-deployed server with UTC locale this is fine; if the server's localtime ever drifts to e.g. UTC-1, a date equal to UTC "today" could be incorrectly rejected for one hour. Low risk but `date.fromisoformat(datetime.now(timezone.utc).date().isoformat())` would be more explicit.

### Patterns confirmed good in this batch
- `sign_ato_atomic`: FOR UPDATE + lock_timeout + outcome dict pattern is clean.
- `replace_period_scores`: atomic delete+insert transaction eliminates leaderboard empty-window. Return value (len(docs)) is correct.
- `setup_account` CAS: filter includes token+status in the update_one predicate; modified_count==0 → 409. Correct.
- `list_my_quotas`: user_id scoped to current_user.id (no IDOR). password not in transactions table.
- `list_my_quotas` route ordering: `/me/quotas` is placed ABOVE `/{transaction_id}` patterns — no shadowing risk with FastAPI prefix router.
- `PollWithVote.has_voted`: scoped to current user only; does not reveal other voters or vote direction. Secret ballot maintained.
- `PageBannerUpdate._v_image_url`: blocks external URLs, mirrors UserProfileUpdate._v_photo_url pattern correctly.
- `ux_comunicados_source_ref` in REQUIRED_INDEX_NAMES: startup blocks if index missing, preventing duplicate official emails.
- `ux_users_member_id` as best-effort (NOT in REQUIRED): correct — prod may have pre-existing collisions; app-level check in admin.py is the primary guard.
- `stats.py total_revenue` removal: frontend already calls `getMyQuotas` via api.js; no stale invoices references remain in frontend.
- `invoices` table/collection removed from COLLECTIONS and index DDL cleanly; no remaining route/model references in non-test code.

## Patterns confirmed good

- cast_ballot / cast_assembleia_ballot / insert_quotas_atomic / register_presenca_locked — all use FOR UPDATE in DAO.
- apurar (eleicoes) and proclamar use pre-close CAS (update_one with status filter, check modified_count==0) correctly.
- compute_dre_report / compute_financial_summary shared single source — correctly avoids DRE divergence.
- Finance settings monetary changes require AG deliberation with 3/4 majority and snapshot history.
- Secret ballot: receipt (voter_hash) and ballot (voto) in separate collections, ballot never carries user_id. Confirmed in eleicoes.py.
- sancoes.py `aplicar_sancao`: effects-before-CAS pattern (idempotent effects first, CAS final mark) is correct.

**How to apply:** When reviewing future atos/co-approval changes, verify atomic write pattern. When reviewing email calls after CAS commits, verify retry path exists or use BackgroundTask.
