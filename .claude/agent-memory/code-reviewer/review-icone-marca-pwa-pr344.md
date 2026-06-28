---
name: review-icone-marca-pwa-pr344
description: findings from feature/icone-marca-pwa PR #344 (spec 005 — ícone quadrado da marca / PWA); open redirect risk acknowledged but mitigated by write-admin-only; apple-touch-icon still static; FRONTEND_URL empty → relative Location
metadata:
  type: project
---

Review of PR #344 `feature/icone-marca-pwa` vs `develop` (spec 005). No CRITICAL; 4 WARNINGs.

**Why:** PR adds `icon_url` field to `brand_settings`, a public `/api/brand/icon` 302-redirect endpoint, `BrandIcon.js` component, and static PWA/og references hardcoded to `https://api.controlador.cv`.

**Key findings:**

- W1: `GET /api/brand/icon` is a restricted open redirect — any URL scheme (including `javascript:`) is served in Location header if icon_url is set. RBAC (admin+moderador only write) is the sole mitigation; Starlette encodes CRLF but passes `javascript:` through. An URL-scheme allowlist on `BrandSettingsUpdate` would close this.
- W2: `FRONTEND_URL` unset → `Location: /logo512.png` (relative). In a browser hitting `api.controlador.cv/api/brand/icon`, this resolves to `api.controlador.cv/logo512.png` (file doesn't exist there → 404). Prod has FRONTEND_URL set; dev/CI may not. Low severity but observable in test environments.
- W3: `apple-touch-icon` in `index.html` line 12 still points to `%PUBLIC_URL%/logo192.png` (static). iOS will always use the old template logo regardless of what is uploaded. Inconsistent with the stated goal of "todas as superfícies quadradas".
- W4: `manifest.json` shortcuts entries use `"sizes": "any"` without `"type"` field. `favicon.ico` entry loses the 192/512 static fallbacks — some older Android WebAPK paths may fall back to the favicon.ico (16px) as the largest icon. Low risk but inconsistent.

**How to apply:** Flag W1 (scheme allowlist) and W3 (apple-touch-icon) as WARNINGs when reviewing brand subsystem PRs. FRONTEND_URL empty path is a recurring pattern in this codebase (seen also in email_service.py and helpers.py).
