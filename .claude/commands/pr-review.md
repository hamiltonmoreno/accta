---
name: pr-review
argument-hint: [pr-number]
---

Review pull request #$ARGUMENTS:
1. `gh pr view $ARGUMENTS` — read PR description
2. `gh pr diff $ARGUMENTS` — read all changes
3. Check for:
   - Security issues (auth, injection, secrets)
   - ACCTA conventions (Portuguese text; neutral-led design, Carmesim as
     single restrained accent, no red-on-dark, ≤1 primary button/view; no
     dark mode — see `/frontend-design`)
   - Role-based access on new endpoints
   - Audit logging for admin actions
   - Proper error handling
   - Test coverage for new features
4. Check CI status: `gh pr checks $ARGUMENTS`
5. Leave review with findings categorized as CRITICAL / WARNING / SUGGESTION
6. Approve or request changes based on findings
