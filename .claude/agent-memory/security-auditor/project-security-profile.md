---
name: project-security-profile
description: ACCTA Portal security posture — known findings and mitigations as of 2026-05-18 full audit
metadata:
  type: project
---

Full security audit performed on 2026-05-18. Key findings:

**Why:** Baseline audit to identify vulnerabilities before production hardening.

**How to apply:** When reviewing PRs or discussing security improvements, reference these as the known baseline. Re-verify any finding before declaring it fixed.

## Confirmed Strong Points
- JWT stored in httpOnly cookie (Sprint 10), not localStorage — XSS-resistant
- CSRF middleware validates Origin/Referer for cookie-bearing unsafe methods
- bcrypt rounds=12, SECRET_KEY from env (fails fast if missing)
- JTI blocklist revocation on logout
- Account lockout: 5 failures / 15 min window
- DAO parameterizes all asyncpg queries — no raw SQL injection surface
- Path traversal guard on DELETE /upload/{category}/{filename}
- Magic-byte + Pillow.verify() file content validation
- CORS refuses wildcard in production (raises RuntimeError)
- X-Frame-Options: DENY, X-Content-Type-Options: nosniff, HSTS in prod

## Open Findings (as of 2026-05-18)
1. MEDIUM — SVG upload allowed for logos; no SVG sanitization → stored XSS vector
2. MEDIUM — `PATCH /users/{user_id}/status` accepts arbitrary status string (no allowlist) — admin-only but unvalidated
3. MEDIUM — `POST /contact` has no rate limit — email relay abuse
4. MEDIUM — invite_token returned in response body of POST /admin/invite (setup_url field contains the token in plaintext)
5. MEDIUM — X-Forwarded-For trusted unconditionally (IP spoofable for rate-limit and audit log bypass if not behind trusted proxy)
6. LOW — Password minimum length is 6 chars (weak floor)
7. LOW — No Content-Security-Policy header set
8. LOW — Token also returned in login/setup-account response body (legacy compat) — token in body not used by frontend but still transmitted
9. LOW — `GET /activity/recent` exposes wall post content and project comment content to all authenticated users without checking post visibility beyond `approved:true`
