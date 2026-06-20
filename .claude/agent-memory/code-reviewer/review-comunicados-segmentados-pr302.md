---
name: review-comunicados-segmentados-pr302
description: Security/correctness findings from PR #302 (feature/comunicados-segmentados, Comunicados Segmentados v2)
metadata:
  type: project
---

## PR #302 — Comunicados Segmentados v2 (2026-06-20)

Branch: `feature/comunicados-segmentados` vs `origin/develop`.
Files reviewed: `backend/comunicados_service.py`, `backend/routes/comunicados.py`,
`backend/models.py`, `backend/permissions.py`, `backend/governance.py`,
`frontend/src/pages/private/AdminComunicadosPage.js`,
`frontend/src/pages/private/comunicados/AudienceBuilder.js`,
`frontend/src/pages/private/comunicados/ComposerCard.js`,
`frontend/src/pages/private/comunicados/PreviewCard.js`,
`frontend/src/pages/private/comunicados/HistoryTable.js`,
`frontend/src/pages/private/comunicados/ConfirmDialog.js`,
`frontend/src/utils/api.js`, `frontend/src/lib/queryClient.js`.

---

## CRITICAL

### C1 — IDOR on PATCH /comunicados/{id}: no ownership check
`backend/routes/comunicados.py` line 175–191.
`update_comunicado` calls `_guard` (passes for any `_can_send` user) then
`_enforce_intra_orgao_scope` (checks audience scope, not ownership). No
`created_by == current_user.id` check exists, unlike `cancelar_comunicado`
which correctly checks it (line 243). Any user with `comunicar_intra_orgao`
can overwrite another user's draft subject/body before send.
Fix: add `if doc.get("created_by") != current_user.id and current_user.role != "admin": 403`.

### C2 — IDOR on POST /comunicados/{id}/enviar: no ownership check
`backend/routes/comunicados.py` line 194–229.
`enviar_comunicado` calls `_guard` and `_enforce_intra_orgao_scope` but never
checks `created_by`. Any `_can_send` user can trigger send of another user's
draft (correct actor recorded in audit, but wrong actor triggers actual fan-out).
Fix: same pattern as DELETE — only `created_by` or `admin` may trigger send.

---

## WARNINGS

### W1 — Missing _enforce_intra_orgao_scope on preview-audience endpoint
`backend/routes/comunicados.py` line 89–96.
`preview_audience` calls `_guard` (allows restricted `comunicar_intra_orgao`
users) but NOT `_enforce_intra_orgao_scope`. A restricted CF-member can POST
`{"audience_filter": {"categorias": ["ordinario"]}}` and receive counts + name
samples of all active members — bypassing the scope restriction enforced at
create/patch/enviar. This is information disclosure.
Fix: add `_enforce_intra_orgao_scope(current_user, payload.audience_filter.model_dump())` before the service call.

### W2 — preview_audience ignores `channels` parameter (correctness)
`backend/comunicados_service.py` line 260–274.
`channels` is accepted as a parameter but never used. `_resolve_audience_core`
returns the raw intersection without applying email opt-out or no-email-address
filters. For an `["email"]` channel with `tipo="informativo"`, the preview count
can be materially higher than actual recipients (members who opted out or have no
email are counted but won't receive). Admin sees inflated number.
Fix: call `resolve_audience` per channel (union for in_app, intersect optouts for email), or add a channels-aware post-filter to the preview.

### W3 — ComunicadoUpdate has no field validators for subject/body
`backend/models.py` line 1114–1124.
`ComunicadoUpdate` (PATCH payload) has `subject: Optional[str]` and
`body: Optional[str]` with no `@field_validator`. Via PATCH a draft's subject
can be set to `""` or body to `"a"` (1 char), bypassing the length guards in
`ComunicadoCreate`. The enviar endpoint does not re-validate before send.
Fix: add same validators as ComunicadoCreate (`_v_subject`, `_v_body`).

### W4 — /enviar dispatches synchronously (potential HTTP timeout for large audiences)
`backend/routes/comunicados.py` line 220.
`result = await comunicados_service.dispatch_comunicado(comunicado_id)` blocks
the HTTP response until the full fan-out completes. The legacy v1 path correctly
uses `background_tasks.add_task(...)`. For a full-sender targeting `all_active`
with email+in_app (potentially hundreds of recipients), this could exceed the
Nginx/client timeout and leave the HTTP connection hanging while the dispatch
continues running in the async event loop (or crash it).
Fix: mirror the v1 pattern — transition rascunho→a_enviar, add_task the
dispatch, return immediately with `{"status": "a_enviar", "id": ...}`.

### W5 — Date fields (joined_after/joined_before) accept arbitrary strings
`backend/models.py` line 983–984.
`AudienceFilter.joined_after/joined_before` are `Optional[str]` with only a
cross-field `joined_after > joined_before` check but no ISO 8601 format
validation. A malformed value like `"abc"` passes Pydantic and causes
incorrect (but non-crashing) membership matching in `_matches_period`.
Fix: add a regex validator `^\d{4}-\d{2}-\d{2}$` or use `date.fromisoformat`.

---

## SUGGESTIONS

### S1 — GET /comunicados/segments uses _guard (not _guard_full) for restricted users
`backend/routes/comunicados.py` line 84–86.
`get_segment_counts()` returns full membership breakdown by role, category, and
orgao — internal governance information. A restricted `comunicar_intra_orgao`
user can call this endpoint (frontend disables it for them, but backend does not
enforce). Low risk since the privilege is admin-assigned, but inconsistent with
the full-sender-only intent of the segment data. Fix: use `_guard_full`.

### S2 — HistoryTable supplementary annotations use color-only signaling
`frontend/src/pages/private/comunicados/HistoryTable.js` lines 96, 98.
`text-[#B91C1C]` for "falha(s)" count and `text-[#B45309]` for "simulação"
have no accompanying icon. ACCTA convention requires icon + text for status
signals. The main status column uses `StatusBadge` with icon correctly; the
supplementary detail inside the description cell does not. Add a small
`<XCircle>` / `<FlaskConical>` icon inline.

### S3 — HistoryTable shows created_by as raw UUID
`frontend/src/pages/private/comunicados/HistoryTable.js` line 117.
`{c.created_by}` renders the UUID string, not the user's name. Pre-existing,
but worsened by the new rascunho/edit flow where multiple users may create
drafts. Consider resolving to name at API level or enriching the list response.

### S4 — AudienceFilter.statuses validation allows "inativo" and "rejeitado"
`backend/models.py` line 1010, validated against `USER_STATUSES`.
`AudienceFilter._v_filter` accepts any `USER_STATUSES` value including `rejeitado`
and `inativo`. The `includes_unapproved` warning only covers
`{pendente_aprovacao, pendente_convite, rejeitado}`. Sending a comunicado to
`inativo` members is not warned about at all and may be surprising. Consider
adding a separate `includes_inactive` warning.

---

## Confirmed good

- `_enforce_intra_orgao_scope` is correctly called at create (line 123), PATCH (line 187), and enviar (line 206).
- The legacy `segment` path is gated by `_guard_full` (line 144) — restricted users cannot use it.
- CAS `rascunho→a_enviar` in enviar (line 215) + `a_enviar→enviando` in dispatch prevents duplicate dispatch.
- `dry_run` is blocked at create (line 115) and patch (line 181) in prod; dispatch applies defense-in-depth (`effective_dry_run = bool(doc.get("dry_run")) and not IS_PROD`).
- Snapshot (`audience_resolved`, `recipients_count`, `failed_member_ids`) persisted correctly only for v2 path.
- DELETE (`cancelar_comunicado`) correctly checks `created_by == current_user.id OR role==admin`.
- Audit log present at: create-rascunho (criar_rascunho_comunicado), enviar (comunicado_enviado), delete (cancelar_comunicado).
- `AudienceFilter` model validates cargos/orgaos/categorias/statuses against canonical lists.
- `_resolve_audience_core`: OR-within-type, AND-between-types logic is correct (tested: 85 green).
- `_filter_base` Python-side re-check of status and account_type is a valid defence for test parity.
- Frontend `isFullSender`/`restricted` correctly uses `can('send_comunicados')` (includes admin) vs `hasPrivilege('comunicar_intra_orgao')`.
- Delete confirmation dialog uses carmesim-solid (irreversible confirm) — correct per design system.
- Save-draft button is neutral secondary; send button is Floresta primary — correct button taxonomy.

**How to apply:** C1+C2 are blockers; W1 is a security bypass for a new privilege class; all three must be fixed before merging to develop.
