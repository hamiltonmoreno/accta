---
name: review-shadcn-migration-251-253
description: Findings from PRs #251/252/253 (shadcn Input/Textarea migration + responsive grid cleanup); radio/checkbox wrapped in Input is an established pattern here but warrants note
metadata:
  type: project
---

PRs #251–#253 form the first stacked wave of a planned 13-PR frontend refactor.

**Pattern to watch across the series:**
- `<Input type="radio">` and `<Input type="checkbox">` — the shadcn Input primitive wraps `<input>` via forwardRef and spreads `...props`, so these work functionally. However the shadcn default classes (`h-11 md:h-10 w-full rounded-md border ...`) are visually wrong for checkboxes/radios (they apply block sizing). These callers pass their own `className` that override the defaults, so the visual is fine in practice — but it's semantically odd. In future PRs, if checkbox/radio inputs are encountered without an overriding className, flag it.
- `fieldCls` is still passed as `className` in many migrated inputs (overrides the shadcn defaults) — this is intentional during the transition period; the PR description acknowledges it.
- `<Input>` in #253/AdminUsuariosPage still has inline `className` strings with hardcoded colors (`border-gray-200`, `focus-visible:ring-[#C7202F]/40`) on some inputs, meaning those inputs get double-styling (their own className wins over the shadcn default due to cn() merge order). Not a bug, but creates inconsistency that a later PR in the series should clean up.
- CI failures across all 3 PRs = billing lock (not code), per [[ci-billing-lock-not-code]].

**Approved status:** All 3 PRs were APPROVED WITH NITS (no CRITICALs found).
