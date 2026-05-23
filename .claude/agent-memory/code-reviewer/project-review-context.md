---
name: project-review-context
description: ACCTA Portal code review scope, shadcn Dialog migration patterns observed, and key design invariants confirmed in the fix/frontend-consistency branch
metadata:
  type: project
---

Reviewed branch `fix/frontend-consistency` against `fix/frontend-neutral-led` covering 8 files (App.js, index.css, ProjectsPage, EventosPage, DocumentosPage, GaleriaAdminPage, TransactionModal, AdminUsuariosPage).

**Why:** Fase 6.1–6.9 migrated hand-rolled modals to shadcn Dialog/AlertDialog; Fase 0 fixed a functional bug and added prefers-reduced-motion support.

**How to apply:** When reviewing future shadcn Dialog migrations, check: (1) `open onOpenChange` pattern wired correctly, (2) `useBodyScrollLock` present where shadcn Dialog is NOT used (shadcn handles scroll-lock internally), (3) form state reset on close, (4) ESC/overlay close via onOpenChange delegation.

Key findings from this review:
- `DocumentosPage:327` still has `hover:border-primary` (stale token, renders as no-op) — not yet fixed as of this review
- `EventosPage` CreateEventModal remains a hand-rolled modal (not migrated to shadcn Dialog) — intentional or deferred; uses useBodyScrollLock correctly
- `AdminUsuariosPage` Fase 7.3.2: deleteMutation `onSuccess` calls `setEditingUser(null)` after `setDeleteConfirm(null)` — order is safe; both states are cleared synchronously before re-render
- `TransactionModal` does NOT call `onClose()` on save success — it calls `onSaved()` only; the parent (CashFlowTab) is responsible for closing. This is intentional contract but must not change.
- `prefers-reduced-motion` block in index.css covers `animate-fadeIn/fade-up/fade-in/fade-out` but NOT `animate-spin` (loading spinners) — this is correct per WCAG (spinners are functional, not decorative).
