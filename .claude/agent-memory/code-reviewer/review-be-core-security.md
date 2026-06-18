---
name: review-be-core-security
description: Review of backend core security (server.py/auth.py 2026-06-04; database.py/models.py/helpers.py/governance.py/email_service.py/comunicados_service.py/finance_joia.py/atos_rules.py/ranking.py/config.py 2026-06-18)
metadata:
  type: project
---

## Review 2026-06-04 (server.py, auth.py, file_validation.py — branch chore/coderabbit-baseline)

Key findings (MFA removed since; items moot):
- mfa/disable missing mandatory guard (MFA removed PR #removal).
- bootstrap_admin cargo label not canonical key.
- mfa/verify no rate-limit (MFA removed).

---

## Review 2026-06-18 (backend NÚCLEO: database.py, models.py, helpers.py, governance.py, email_service.py, comunicados_service.py, finance_joia.py, atos_rules.py, ranking.py, config.py)

### Critical
None new in these files. Previously found atos.py sign_ato TOCTOU (review-finances-governance.md) still open.

### Warnings

**W1 — `record_failed_login` stores `attempted_at` as Python `datetime` object (not ISO string).** `db.login_attempts.insert_one({"attempted_at": now})` — `now` is `datetime`. asyncpg's jsonb codec serializes it via `_json_default` → ISO string. `_DATETIME_FIELDS` rehydrates it back to `datetime` on `find_one`. The $gte filter in `count_documents` also receives `datetime` → `_to_scalar_text` → ISO string comparison. Round-trip consistent today, but fragile: any code bypassing the codec would break the lock check silently. (helpers.py:112)

**W2 — `dispatch_oficial_auto` TOCTOU closed only by DB UNIQUE index `ux_comunicados_source_ref`.** This index is marked non-fatal in `ensure_schema`. If it fails to create (pre-existing duplicates), concurrent governance triggers can send duplicate official emails to all active members. The index is load-bearing — its creation failure should be escalated the same way `ux_votes_user_poll` is (raise RuntimeError). (database.py:967, comunicados_service.py:190)

**W3 — `ranking.py rebuild_scores` has a window where `member_scores` for the period is empty** (between `delete_many` and `insert_many`). Concurrent GET /ranking requests during admin-triggered rebuild see an empty leaderboard. Low severity (admin action, bounded gap), but worth documenting. (ranking.py:278-280)

**W4 — `welcome_email_html` CTA button links to `"#"` instead of the portal URL.** Broken UX — welcome button does nothing. Fix: substitute `FRONTEND_URL` or the `/login` path. (email_service.py:118)

**W5 — `ComunicadoCreate._v_cta_url` blocks relative URLs, but `dispatch_oficial_auto` bypasses this validator** (constructs doc dict directly). Governance-triggered comunicados can carry relative `cta_url` (e.g. `/assembleias/{id}`). `comunicado_email_html` handles gracefully (no button if `FRONTEND_URL` absent), so no security issue — but silent missing button in production emails if FRONTEND_URL not set. (models.py:1029-1037, comunicados_service.py:184)

### Confirmed good patterns (do not regress)
- `_WhereBuilder._eq` scalar+array membership via `?` operator — fixed (no dead @> branch).
- `insert_quotas_atomic` advisory lock + re-read inside transaction.
- `cast_ballot` / `cast_assembleia_ballot` / `cast_assembleia_nominal_vote` / `register_presenca_locked` — all FOR UPDATE + status recheck.
- `transfer_cargo` atomic FOR UPDATE on both users.
- `_ssl_arg()` passes explicit sslmode verbatim (no silent downgrade).
- `audit_entry_hash` uses `hmac.compare_digest` (constant-time).
- `resolve_link_base` fails closed on untrusted origin.
- `_mask_email` prevents PII in logs.

**How to apply:** When reviewing new check-then-insert/update DB writes, verify FOR UPDATE or UNIQUE index backstop. Comunicado UNIQUE index is load-bearing — never make it silently non-fatal without app-level locking fallback.
