---
paths:
  - "backend/routes/**/*.py"
  - "backend/server.py"
  - "backend/auth.py"
  - "backend/helpers.py"
---

# API Rules — ACCTA Portal Backend

## Route Structure
- Each domain has its own router file in `backend/routes/`
- Prefix all routes with `/api/{domain}`
- Use FastAPI dependency injection for auth: `current_user = Depends(get_current_user)`

## Authentication & Authorization
- Every protected endpoint MUST use `get_current_user` dependency
- Access checks go through the canonical helpers (spec 018 — NEVER compare
  `user.role` inline in routes; guarded by `test_no_inline_role_checks`):
  `if not has_role_or_privilege(current_user, ("admin",), "manage_x")` /
  `is_admin(current_user)` / `module_gate(current_user, "<module>")`
  (table: `governance.MODULE_ACCESS`). Roles are {admin, socio} only.
- Return 403 for unauthorized access
- Return 401 for missing/invalid token

## Database
- Use asyncpg (PostgreSQL/Supabase) via the Mongo-compatible DAO in `database.py` — all DB operations must be `await`
- Access collections via attribute on the DAO: `database.db.collection_name` (e.g. `db.users`, `db.transactions`)
- Use `str(uuid.uuid4())` for generating IDs (stored as `id`; there is no Mongo `_id`)
- Serialize dates as ISO 8601 strings (`datetime.now(timezone.utc).isoformat()`)
- Never build raw SQL in routes — the DAO parameterizes asyncpg queries; indexes are defined in `database.py` via `ensure_schema()` (do not call `create_index` from routes)

## Error Handling
- Use `HTTPException` with appropriate status codes
- 400: Bad request / validation error
- 401: Not authenticated
- 403: Not authorized (wrong role)
- 404: Resource not found
- 422: Validation error (automatic from Pydantic)

## Notifications & Audit
- Use `create_notification()` from helpers for user notifications
- Use `notify_admins()` for admin alerts
- Use `create_audit_log()` for ALL admin actions
- Notification types: finance, event, project, poll, wall, gallery, admin, system

## Rate Limiting
- Login: 10/minute
- Forgot password: 3/minute
- Setup account: 5/minute
- Default: 200/minute

## File Uploads
- Validate file extension and size per category
- Categories: documents (10MB), proofs (5MB), logos (2MB), avatars (2MB)
- Store in `/backend/uploads/{category}/`
