#!/bin/bash
# SessionStart hook — Claude Code on the web.
#
# Installs backend (Python) + frontend (Node) dependencies so that the
# build, linters (ruff / eslint) and test suites (pytest / craco) work in
# remote web sessions. Mirrors the CI and Vercel build recipe:
#   backend  -> pip install -r requirements.txt
#   frontend -> yarn install --frozen-lockfile
# Idempotent and non-interactive — safe to re-run on every session.
set -euo pipefail

# Only run inside the remote (Claude Code on the web) environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

echo "[session-start] Backend: installing Python dependencies…"
# Note: the container's pip is Debian-managed and cannot self-upgrade
# (no RECORD file) — pip 24 installs every pinned wheel fine, so skip it.
python3 -m pip install --quiet --root-user-action=ignore -r "$ROOT/backend/requirements.txt"
# ruff + the pytest stack are not pinned in requirements.txt but are
# required to lint and run the test suite (pyproject: asyncio_mode=auto).
# cffi: python-jose[cryptography] leaves the container's Debian-managed
# `cryptography` in place (unpinned extra → "already satisfied"), so its
# cffi dep is never pulled and crypto imports crash without it.
python3 -m pip install --quiet --root-user-action=ignore ruff pytest pytest-asyncio pytest-cov cffi

echo "[session-start] Frontend: installing Node dependencies…"
( cd "$ROOT/frontend" && yarn install --frozen-lockfile --non-interactive )

echo "[session-start] Dependencies ready (backend + frontend)."
