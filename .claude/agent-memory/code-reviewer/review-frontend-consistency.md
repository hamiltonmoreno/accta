---
name: review-frontend-consistency
description: Findings from code review of fix/frontend-consistency branch (Fases 7.1/7.2/4/5) — color semantics in financial area, ValidadorPage migration, redundant specs
metadata:
  type: project
---

## Key findings (May 2026)

**Why:** Reviewed `fix/frontend-consistency` vs `fix/frontend-neutral-led` covering DRETab, CashFlowTab, MemberFinanceView, SettingsTab, ValidadorPage, ProjectDetailPage, MuralPage.

- DRETab Fase 7.1 migration: `style={{ color: 'var(--text-*)' }}` correctly replaced by `text-*-auto` classes. Color semantics preserved: receitas = `#15803D`/`#16A34A` (green), despesas = `#B91C1C`/`#C7202F` (carmesim), resultado negativo = `#B45309` (warning amber). One residual `style={{ borderTop: '1px solid var(--surface-border)' }}` remains (surface token, out of Fase 7.1 scope per spec).
- CashFlowTab: NOT yet migrated from `style={}` (inline styles remain on StatBlock). Working tree shows already migrated — confirms branch is ahead of diff starting point. Full migration complete with SKILL §4 palette.
- ValidadorPage: Migrated to `statusConfig.js` (WALLET_VALIDATION_CONFIG with TONE.success/TONE.error). Semantic correction: "ativo"=success (#15803D green), invalid=error (#B91C1C) — previously both used Carmesim (V7). Logic unchanged; only presentation refactored. Focus ring corrected to `focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2`.
- `tasks/spec-auto-registo.md` and `tasks/spec-identidade-cargos.md` in branch commit 13ff240 are CONFIRMED REDUNDANT — both already in `origin/main` (git cat-file -e returns 0).
- SettingsTab: inline `style={{ color }}` fully replaced; `text-grafite-auto`, `text-muted-auto` used throughout.
- DRETab: one remaining `style={{ borderTop: '1px solid var(--surface-border)' }}` is a surface token (not a text token) — explicitly out of scope per frontend-consistency-7.3-spec.md "Fora de escopo".

**How to apply:** When reviewing future financial pages, verify receitas=green, despesas=error-red, resultado_liquido_negativo=warning-amber (never Carmesim for any of these). The `statusConfig.js` is the canonical source for all status/validation states.
