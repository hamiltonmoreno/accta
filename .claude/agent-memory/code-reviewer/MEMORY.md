# Memory Index

- [Project review context](project-review-context.md) — ACCTA Portal code review scope, branch conventions, and key design invariants observed in practice
- [Frontend Consistency Branch Review](review-frontend-consistency.md) — findings from fix/frontend-consistency review (Fases 7.1/7.2/4/5); DRETab color semantics, ValidadorPage statusConfig migration, redundant task specs
- [shadcn migration PRs #251-253](review-shadcn-migration-251-253.md) — radio/checkbox wrapped in Input works via forwardRef but is semantically odd; fieldCls double-styling is intentional; CI fail = billing lock
- [Finances & Governance backend review](review-finances-governance.md) — C1: atos.py sign_ato TOCTOU race (lost-update on co-approval signatures); W: honorario email sync, sancoes expulsion no tipo_maioria check, regulamentos drafts exposed
- [Backend NÚCLEO review 2026-06-18](review-be-core-security.md) — W: comunicado UNIQUE index non-fatal (duplicate official emails), welcome email CTA href="#", ranking rebuild empty-window, attempted_at datetime fragility
