---
name: project-security-profile
description: ACCTA Portal security posture — known findings and mitigations, updated 2026-06-16 focused route-layer audit
metadata:
  type: project
---

Full security audit performed on 2026-05-18. Focused route-layer re-audit on 2026-06-16 (32 route modules, database.py DAO analysis, auth stack).

**Why:** Baseline audit and route-layer deep-dive to identify exploitable vulnerabilities before production hardening.

**How to apply:** When reviewing PRs or discussing security improvements, reference these as the known baseline. Re-verify any finding before declaring it fixed.

## Confirmed Strong Points
- JWT stored in httpOnly cookie (Sprint 10), not localStorage — XSS-resistant
- CSRF middleware validates Origin/Referer for cookie-bearing unsafe methods
- bcrypt rounds=12, SECRET_KEY from env (fails fast if missing)
- JTI blocklist revocation on logout
- Account lockout: 5 failures / 15 min window
- DAO parameterizes all asyncpg queries — no raw SQL injection surface
- Filter key literals go through _lit() single-quote-escape; collection names validated by _quote_ident()
- Path traversal guard on DELETE /upload/{category}/{filename} and GET /documents/{id}/download
- Magic-byte + Pillow.verify() file content validation; UUID-renamed filenames on disk
- CORS refuses wildcard in production (raises RuntimeError)
- X-Frame-Options: DENY, X-Content-Type-Options: nosniff, HSTS in prod
- Secret ballot: HMAC receipt + anonymous ballot in separate tables, cast under FOR UPDATE lock (TOCTOU-closed)
- Duplicate-vote prevented by UNIQUE index + in-tx check for polls AND elections AND assembleia
- Audit log immutability trigger + HMAC tamper-evidence (F4)
- RLS ON + 0 policies = deny-all on Supabase Data API surface
- Password reset: CAS used:False→True, 1-hour expiry, invalidates prior sessions via password_changed_at
- UserAdminUpdate explicitly excludes member_id and cargo (comment documents intent)

## Open Findings — 2026-06-16 Route Audit (HIGH CONFIDENCE)

### HIGH
1. **IDOR — `GET /invoices` member-visible filter bypassed by financeiro/CF users viewing all invoices**: Correct by design per role model, but a `socio` with the `view_finances_readonly` privilege (Conselho Fiscal) sees ALL invoices including other members' financial data (amounts, user_id). If CF members exist, this is cross-member PII exposure. File: `backend/routes/invoices.py:19-26`.
2. **admin/invite allows caller-supplied member_id (no uniqueness check)**: `POST /admin/invite` accepts `data.member_id` from the request body (InviteCreate.member_id is Optional[str]). If provided, it is written directly to the user document without checking for collision against existing member_ids. An admin can create two users with the same member_id. File: `backend/routes/admin.py:70`.
3. **hmac.new() is incorrect Python API — should be hmac.new()**: `hmac.new(...)` was removed in Python 3; the correct call is `hmac.new(key, msg, digestmod)`. However Python's hmac module does expose `hmac.new` as an alias — verify this doesn't silently fall through to a no-op. Files: `backend/routes/eleicoes.py:69`, `backend/routes/assembleias.py:941`.

### MEDIUM (carried from 2026-05-18)
4. SVG upload allowed for logos category; no SVG sanitization → stored XSS (FIXED per upload.py — SVG blocked in ALLOWED_EXTENSIONS)
5. `POST /contact` has no rate limit — email relay abuse
6. X-Forwarded-For trusted unconditionally — IP spoofable for rate-limit and audit log bypass if behind untrusted proxy
7. No Content-Security-Policy header set

### LOW (carried from 2026-05-18)
8. Password minimum length is 6 chars (owner decision — do not change per memory)
9. Token also returned in login/setup-account response body (legacy compat)

## DAO / Helpers / Email / Upload Focused Audit — 2026-06-16 (this session)

### DAO (database.py) — SQL Injection Surface
- All filter values go through asyncpg bound params ($1,$2…); no user value is concatenated.
- Filter key literals (field names) go through `_lit()` (single-quote doubling). Routes build filter dicts with hardcoded Python string keys — user input never flows into dict keys.
- `_quote_ident()` validates collection names against `_COLLECTION_SET` or strict `[a-z_][a-z0-9_]*` regex.
- `$regex` value is passed as a bound param (`self._ph(val)`); field name goes through `_lit()`. All callers use `re.escape()` or `_safe_search_regex()` before setting the regex value.
- `_order_by()` field names come from hardcoded sort specs in route code, never from query params.
- `_purge_ttl` interpolates field name directly from `_TTL_PURGE` constant dict (hardcoded strings, not user input).
- `_cast_secret_ballot_locked`: `parent_id_field_in_receipt`/`dup_field` always hardcoded at call sites; validated by `_safe_jsonb_key()`.
- VERDICT: No SQL injection in the DAO.

### File Upload (routes/upload.py, helpers.py, file_validation.py)
- Category validated against explicit allowlist before any filesystem use.
- Files renamed to `uuid4()` on disk; original filename only used for extension extraction.
- Magic-byte validation (`_check_prefix`) + Pillow `verify()` cross-checked against detected format.
- SVG blocked in all categories (stored XSS via SVG would be the risk).
- `DELETE /upload/{category}/{filename}`: resolves path and checks `is_relative_to(upload_root/category)` — path traversal prevented.
- `helpers.delete_upload_file()`: validates URL starts with `/uploads/` and resolved path is inside `UPLOAD_DIR`.
- `documents.py get_document_file_path()`: extracts only `Path(parsed_path).name` (basename only), resolves, checks `is_relative_to(documents_dir)`.
- VERDICT: No path traversal. No upload exploit at >80% confidence.

### Email Service (email_service.py)
- User-supplied `name` is HTML-escaped with `html.escape(name, quote=True)` in all email templates.
- `reset_url`/`setup_url` constructed from FRONTEND_URL env var or CORS-allowlisted Origin only (`resolve_link_base`).
- Password reset token is `str(uuid.uuid4())` — UUID chars only, no HTML special chars, not escaped but safe.
- Invite tokens use `secrets.token_urlsafe(32)` — cryptographically secure.
- Password reset tokens use `str(uuid.uuid4())` — 122 bits entropy, adequate.
- Email recipient (`to`) comes from the stored `email` field, not from request headers.
- VERDICT: No email header/template injection at >80% confidence.

### Auth (auth.py, auth_routes.py)
- bcrypt rounds=12, SECRET_KEY required from env.
- Password reset: single-use CAS (used:False→True), 1-hour expiry, sessions invalidated via `password_changed_at`.
- Invite token: `secrets.token_urlsafe(32)` with configurable TTL expiry.
- VERDICT: Auth layer is sound.

## Auth/AuthZ Core Focused Audit — 2026-06-18 (this session scope)

### Files reviewed: auth.py, permissions.py, server.py, routes/auth_routes.py, routes/upload.py, file_validation.py, config.py, helpers.py (partial), routes/contact.py, routes/admin.py (partial), models.py (partial), database.py (partial)

**CLOSED false positives from 2026-06-16:**
- Finding #3 (hmac.new() wrong API): `hmac.new` is a valid alias for `hmac.HMAC` in Python 3.11; verified working. NOT a bug.
- Finding #5 (contact no rate limit): FIXED — `POST /contact` now has `5/minute` + `20/day` dual limiter.
- Finding #6 (XFF spoofable for rate-limit bypass): slowapi's `get_remote_address` uses `request.client.host` (TCP peer), NOT X-Forwarded-For. Rate-limit bypass via XFF is NOT possible. Finding was wrong for rate-limiting; XFF only affects audit_log IP field (LOW).

**NEW FINDING — MEDIUM: TOCTOU in setup_account (no CAS for invite token)**
- `POST /setup-account` reads the user with `find_one({"invite_token":token, "status":"pendente_convite"})` then updates with `update_one({"id": user_doc["id"]}, ...)` (no token+status filter on write).
- Two concurrent requests with the same token both pass the `find_one` check, both get a JWT, and both activate the account (second update_one is a no-op silently). Unlike `reset_password` which uses `{"token":..., "used":False}` + `modified_count` CAS, setup_account has no atomic claim. Low practical risk (attacker needs the invite token), but the pattern should match reset_password's CAS.
- File: `backend/routes/auth_routes.py:254-264`

**NEW FINDING — LOW: setup_account does not set password_changed_at**
- When a user completes setup-account (first activation), `password_changed_at` is not written. This is harmless NOW because no prior session exists for the account (status was `pendente_convite`). However, if an admin re-invites a previously active account (resetting to `pendente_convite`), old sessions from the prior activation period would NOT be invalidated after the new setup-account completes, because `token_predates_password_change` checks `password_changed_at` only.
- File: `backend/routes/auth_routes.py:254-264`

**NEW FINDING — LOW: member_id has no database UNIQUE index**
- `member_id` is documented as "immutable" and generated by `member_id_seq`. However there is no `CREATE UNIQUE INDEX ... ux_users_member_id ...` in `ensure_schema()`. An admin can supply `data.member_id` in `POST /admin/invite` (line 70), bypassing the sequence; if supplied, no collision check runs, so two users can get the same `member_id`. The DAO also has no uniqueness enforcement.
- File: `backend/routes/admin.py:70`, `backend/database.py` (missing index)

**CONFIRMED STILL OPEN from 2026-06-16:**
- HIGH: Invoices IDOR — CF member with `view_finances_readonly` sees all member invoices (by design but cross-member PII).
- MEDIUM: CSRF bypass when CORS_ORIGINS is empty (dev/staging) — `self.allowed_origins` is falsy, check is skipped.

## Auth/AuthZ Focused Audit — 2026-06-16 (this session scope)

### File scope: auth.py, server.py, permissions.py, governance.py, routes/auth_routes.py, routes/admin.py, routes/users.py, models.py

**Strong points confirmed:**
- `get_current_user` enforces blocklist + password_changed_at on every request — no bypass observed
- `UserAdminUpdate` excludes `member_id`, `cargo`, `password`, `privileges` cannot be set by self-service (`UserProfileUpdate` does not inherit role/privileges)
- Role escalation via `POST /admin/invite` correctly blocks `admin` role (line 67: `if data.role not in ("socio","financeiro","moderador")`)
- `PATCH /users/{user_id}` (admin_update_user): validates `role`, `status`, `privileges` against allowlists; `member_id` not in `UserAdminUpdate` → cannot be set via this endpoint
- Password change (reset-password) correctly sets `password_changed_at` to invalidate prior sessions
- CSRF middleware protects cookie-auth state-changing requests with Origin/Referer allowlist check

**New HIGH-confidence finding — CSRF bypass in non-prod / dev deployment:**
- `CSRFOriginCheckMiddleware.dispatch()` (server.py:94): `if ... and self.allowed_origins:` — when `CORS_ORIGINS` is empty (dev or misconfigured staging), `self.allowed_origins` is an empty set (falsy), so the entire CSRF check is skipped. Any request with a cookie in that env can be CSRF'd.
- Severity: MEDIUM (only exploitable when `CORS_ORIGINS` is not set — which is dev/staging; production raises RuntimeError if `IS_PROD` and `cors_origins` is empty)

**IDOR — admin update user via PATCH /users/{user_id}:**
- Only admin or `manage_users` privilege holders can call it. A `socio` with `manage_users` privilege can update another user's `role`, `status`, and `privileges` — this is by design. Not a bug.

**No evidence of:**
- JWT algorithm confusion (algorithms=[ALGORITHM] locked in all decode calls)
- Missing expiry check (python-jose enforces exp by default)
- Auth bypass in `get_current_user` (all code paths raise HTTPException)
- Mass-assignment via profile self-update (UserProfileUpdate contains only safe personal fields)

## Closed / Not Confirmed in 2026-06-16 Audit
- SVG upload: FIXED — SVG blocked in ALLOWED_EXTENSIONS for logos, brand, covers, avatars
- `PATCH /users/{user_id}/status` status allowlist: FIXED — USER_STATUSES allowlist present at users.py:252
- invite_token in response: FIXED — admin.py:130-135 explicitly omits the token from response

## Full Broad Audit — 2026-06-26 (develop branch, commit 701c27e)

### Scope: all 32 route modules, auth.py, helpers.py, database.py, server.py, file_validation.py, upload.py

### MEDIUM Findings (new)

M1. **IDOR / Visibility leak — `GET /activity/recent` (activity.py:73-90)**
  Events fetched with NO visibility filter: `db.events.find({}, ...).limit(3)` — includes `direcao` events.
  Project comments also fetched with NO project visibility check — a `socio` gets comments from `direcao`/private projects.
  Confirmed at activity.py lines 40-70 and 73-90.

M2. **setup-account CAS race (TOCTOU)** — carried from 2026-06-18 audit. CONFIRMED OPEN in current code (auth_routes.py:258-270 now has CAS filter on update_one, but double-check: the update uses `{"id": user_doc["id"], "invite_token": data.token, "status": "pendente_convite"}` + checks `modified_count == 0` — this IS the CAS fix). CLOSED — CAS is present. False positive carried from earlier.

### LOW Findings (new)

L1. **member_id UNIQUE index is best-effort** — ux_users_member_id is created with `CREATE UNIQUE INDEX IF NOT EXISTS` but only in `REQUIRED_INDEX_NAMES` for warning, not hard failure. Per database.py:800-805 comment, this is intentional ("best-effort"). Collision check exists at admin.py:72-75 for manual member_id. Acceptable.

L2. **audit_log app-layer delete protection absent** — relies on Postgres role revoking DELETE/UPDATE. Documented as F5 operational gate. Acceptable.

L3. **SSE slot cap multiplies per worker** — documented in notifications.py comment. Acceptable for current scale.

L4. **Token also returned in login/setup-account body** — documented legacy compat. Acceptable.

### Confirmed CLOSED from prior audits
- M2 TOCTOU in setup_account: FIXED (CAS filter on update_one + modified_count check)
- setup_account password_changed_at: NOW SET (auth_routes.py:261 `"password_changed_at": now`)
- member_id uniqueness: collision check at admin.py:72-75, DB UNIQUE index (best-effort)
- CSRF bypass in dev: by design, logged as warning; prod raises RuntimeError with empty CORS_ORIGINS
- HIGH invoices IDOR: invoices module has been removed (replaced by me/quotas self-service + transactions module)

### Status of all routes RBAC (2026-06-26 verified)
All 32 route modules: every state-changing endpoint has explicit role/privilege check. All reads of other users' data gated. Password excluded everywhere via projection. MFA_SECRET_FIELDS excluded in all user list/read endpoints.
