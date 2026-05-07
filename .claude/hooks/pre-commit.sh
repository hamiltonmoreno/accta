#!/bin/bash
# PreToolUse hook: triggered on Bash tool calls.
# Only runs lint checks when the command is a git commit.
# Claude Code does not pass the command as $1 — we check stdin JSON.

# Read the tool input from stdin to check if it's a git commit call
INPUT=$(cat)
echo "$INPUT" | grep -q '"git commit' || exit 0

echo "Running pre-commit checks..."

# Backend lint (ruff) — only if backend files are staged
if git diff --cached --name-only 2>/dev/null | grep -q "^backend/"; then
  echo "  Checking backend (ruff)..."
  if command -v ruff &>/dev/null; then
    cd backend && ruff check . || { echo "Backend lint FAILED — commit blocked"; exit 2; }
    cd ..
  elif python3 -m ruff --version &>/dev/null 2>&1; then
    cd backend && python3 -m ruff check . || { echo "Backend lint FAILED — commit blocked"; exit 2; }
    cd ..
  else
    echo "  ruff not found, skipping backend lint"
  fi
  cd ..
fi

# Frontend lint (eslint) — only if frontend JS files are staged
if git diff --cached --name-only 2>/dev/null | grep -qE "^frontend/src/.*\.(js|jsx)$"; then
  echo "  Checking frontend (eslint)..."
  cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60 --quiet || { echo "Frontend lint FAILED — commit blocked"; exit 2; }
  cd ..
fi

echo "Pre-commit checks passed!"
exit 0
