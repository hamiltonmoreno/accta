---
name: review-be-helpers-comms
description: helpers.py/email_service.py/comunicados_service.py/ranking.py review — HTML injection in email templates, Resend Batch double-count on fallback, dispatch_comunicado status bug for in_app-only, ranking N+1 query per member
metadata:
  type: project
---

Review of the helpers/comms/ranking unit (be-helpers-comms).

Key findings:

1. **HTML injection in email templates (security/high)** — `invite_email_html`, `welcome_email_html`, `password_reset_email_html`, and `registration_rejected_email_html` in `email_service.py` interpolate `name`, `setup_url`, `reset_url`, `token`, and `reason` directly into HTML f-strings without `html.escape()`. The `comunicado_email_html` function correctly escapes, but the transactional templates do not. `InviteCreate.name` has no sanitization in models.py.

2. **Resend Batch fallback double-count (correctness/medium)** — `send_comunicado_batch` (line 254): when `resend.Batch.send` raises, it falls through to per-recipient individual sends but `sent` was NOT incremented for the batch attempt. The per-recipient loop then increments `sent` or `failed` correctly — so the count is accurate on fallback. The `continue` prevents double-counting. This path is actually correct; no bug here.

3. **dispatch_comunicado status logic wrong for in_app-only channels (correctness/medium)** — When `channels=["in_app"]` only, `email_failed=0` and `email_sent=0`, so the `elif email_failed` branch is skipped and status becomes `"enviado"` correctly. But if in_app channel has 0 eligible recipients AND no email channel, status still becomes "enviado" even though nothing was dispatched.

4. **dispatch_comunicado TOCTOU on status transition (concurrency/low)** — `find_one` check + `update_one` is not atomic. Two concurrent background tasks for the same comunicado_id could both pass the status=="a_enviar" check before either writes "enviando". Low risk since typically only one background task runs per comunicado.

5. **ranking.py N+1 per-member per-period DB queries (performance/medium)** — `rebuild_scores` calls `compute_member_score` → `gather_signal_counts` for each member individually. For N members × 9 signals = 9N+elections queries. Accepted as future optimization per spec comment.

6. **_count_elections_voted: 1 find_one per election per member (performance/medium)** — With E elections and M members in rebuild, this is E×M individual DB calls just for election turnout. Capped at 1000 elections per period (`.to_list(1000)`) which is reasonable.

**Why:** These patterns were found during systematic review of the helpers/email/comms/ranking unit.
**How to apply:** Flag unescaped f-string interpolation into HTML in any email template function. Check dispatch status logic for edge cases when channels list is subset.
