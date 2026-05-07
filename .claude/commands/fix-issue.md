---
name: fix-issue
argument-hint: [issue-number]
---

Fix GitHub issue #$ARGUMENTS:
1. `gh issue view $ARGUMENTS` — read the issue details
2. Find relevant source files (frontend/src/ or backend/)
3. Implement the minimal fix following ACCTA conventions
4. Write a regression test if applicable
5. Run linting: `cd backend && ruff check .` or `cd frontend && npx eslint src/ --ext .js,.jsx`
6. Commit: "fix: description (closes #$ARGUMENTS)"
