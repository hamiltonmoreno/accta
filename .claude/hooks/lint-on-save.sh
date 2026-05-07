#!/bin/bash
# PostToolUse hook: auto-format Python files after Edit/Write
# Claude Code passes the tool input as JSON via stdin — no $1 argument.
# We detect recently modified Python files via git and format them.

CHANGED=$(git diff --name-only 2>/dev/null | grep '\.py$')

if [ -n "$CHANGED" ]; then
  for FILE in $CHANGED; do
    if [ -f "$FILE" ]; then
      echo "  Formatting: $FILE"
      ruff format "$FILE" 2>/dev/null
      ruff check "$FILE" --fix --quiet 2>/dev/null
    fi
  done
fi

exit 0
