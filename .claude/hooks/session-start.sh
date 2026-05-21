#!/bin/bash
# SessionStart hook — provisions backend (Python) + frontend (Node) deps so
# the build, linters (ruff / eslint) and test suites (pytest / craco) work
# from a clean checkout. Runs in BOTH Claude Code on the web and local
# sessions. Mirrors the CI and Vercel build recipe:
#   backend  -> pip install -r requirements.txt
#   frontend -> yarn install --frozen-lockfile
# On the web, deps go into the container's system Python; locally they go
# into backend/venv (created if missing) so the developer's global Python is
# never touched. Idempotent and non-interactive — safe to re-run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

# ruff + the pytest stack are not pinned in requirements.txt but are required
# to lint and run the test suite (pyproject: asyncio_mode=auto). cffi: the
# python-jose[cryptography] extra leaves the system `cryptography` in place
# (unpinned → "already satisfied"), so its cffi dep is never pulled and crypto
# imports crash without it.
EXTRA_PKGS=(ruff pytest pytest-asyncio pytest-cov cffi)

echo "[session-start] Backend: installing Python dependencies…"
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  # Web container: Debian-managed system pip can't self-upgrade (no RECORD
  # file) — pip 24 installs every pinned wheel fine, so don't try.
  python3 -m pip install --quiet --root-user-action=ignore -r "$ROOT/backend/requirements.txt"
  python3 -m pip install --quiet --root-user-action=ignore "${EXTRA_PKGS[@]}"
else
  # Local: install into the project venv, never the developer's global Python.
  VENV="$ROOT/backend/venv"
  if [ ! -x "$VENV/bin/python" ]; then
    echo "[session-start] Creating backend venv at backend/venv…"
    python3 -m venv "$VENV"
  fi
  "$VENV/bin/python" -m pip install --quiet --upgrade pip
  "$VENV/bin/python" -m pip install --quiet -r "$ROOT/backend/requirements.txt"
  "$VENV/bin/python" -m pip install --quiet "${EXTRA_PKGS[@]}"
fi

echo "[session-start] Frontend: installing Node dependencies…"
( cd "$ROOT/frontend" && yarn install --frozen-lockfile --non-interactive )

echo "[session-start] Dependencies ready (backend + frontend)."
