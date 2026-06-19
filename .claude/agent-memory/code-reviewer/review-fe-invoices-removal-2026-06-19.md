---
name: review-fe-invoices-removal-2026-06-19
description: Frontend review 2026-06-19 — invoices removal, MemberFinanceView rewrite, gallery mediaUrl, voting UX, RBAC route guards (develop vs main)
metadata:
  type: project
---

## Scope

Diff of `frontend/src` between `origin/main` and `origin/develop`, reviewed
2026-06-19 as follow-on to backend PR #276 (drop-invoices / unifica carteira).

## Result: NO CRITICAL. Two WARNINGs, four SUGGESTIONs.

## WARNINGs

W1 — VotingInterface.js:38-40 — "Voto registado" confirmation banner uses
`bg-carmesim/5 … border-carmesim/20 … text-carmesim` (Carmesim as positive
success indicator). Design convention: positive/success states use Floresta
`#166534`. Carmesim = destructive/identity. Contrast is also very low
(`text-carmesim` on `bg-carmesim/5` is near 1:1). VotacaoPanel correctly uses
Floresta — inconsistency between the two vote-success UIs.

W2 — VotingInterface.js — `useState(poll.has_voted ?? false)` initialises from
prop at mount. If the parent re-queries and passes a new `poll` object (e.g.,
after invalidation), the stale `voted=false` persists because `useState` only
reads the initial value once. A `useEffect` keyed on `poll.id` (like
VotacaoPanel does with `deliberacaoId`) is needed to re-sync. Currently the
backend does not return `has_voted` yet (comment says so), so the risk is
deferred — but the pattern is fragile once the field lands.

## SUGGESTIONs

S1 — MemberFinanceView.js — The `totalPago` display shows `.toLocaleString('pt')`
but the `Registos` stat block shows raw `items.length` (integer). Cosmetically
fine, but `StatBlock` also wraps `value` in a `font-mono` div — showing an
un-formatted integer is inconsistent with the amount column.

S2 — AdminStats.js:28 — The fallback when `financeSummary` is absent is now `'—'`.
Fine. But `stats.total_users` / `stats.active_users` / `stats.active_events`
(lines 9, 15, 21) are accessed without guards — if the `/stats` endpoint ever
returns a partial object these will render `undefined`. The parent `DashboardPage`
already guards (`stats && <AdminStats …>`), so this is a belt-and-suspenders note.

S3 — NotificacoesPage.js — `DollarSign` is still imported and still used for
the `financeiro` notification type (line 19). This is correct — it is not an
orphaned import. Just confirming it is intentional.

S4 — SettingsTab.js:72 — `qc.invalidateQueries({ queryKey: ['transactions'] })`
uses a bare prefix key. This will invalidate ALL react-query keys that start with
`['transactions']` (admin view, export counts, etc.). That is intentional and
correct here. Worth noting for future maintainers that adding a more specific sub-key
to transaction queries would allow surgical invalidation.

## Clean / confirmed OK

- All `invoicesAPI` / `queryKeys.invoices` / `INVOICE_STATUS_CONFIG` /
  `invoice_due` symbols completely removed from develop — no runtime orphans.
- `queryKeys.myQuotas.list()` = `['finances', 'me', 'quotas']` is consistent
  across MemberFinanceView (query) and SettingsTab (invalidation).
- `CATEGORY_LABELS` in constants.js covers all canonical + legacy keys.
- `mediaUrl()` correctly applied in GaleriaAdminPage + GaleriaPage (4 callsites).
- `GaleriaAdminPage` delete-button guard changed from `photo.uploaded_by === undefined`
  to `photo.uploaded_by === user?.id` — correct ownership check.
- `ProtectedRoute allowedRoles={['admin']}` added for `/admin/disciplinar` and
  `/governanca/honorarios` — fixes missing RBAC gate at the route level.
- `NotificationContext` fallback interval now cleared on early-return path —
  memory-leak fix is correct.
- `VotacaoPanel` `hasVoted` reset via `useEffect([deliberacaoId])` — correct
  hook pattern; 409 guard on `onError` is consistent with VotingInterface.
- `AdminStats` `total_receitas || 0` null-guard and `'—'` fallback replace the
  old `stats.total_revenue.toFixed(0)` that would crash if `financeSummary`
  was absent and `stats.total_revenue` was undefined.
