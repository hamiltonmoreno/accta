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
- Check roles explicitly: `if current_user["role"] not in ["admin", "financeiro"]`
- Return 403 for unauthorized role access
- Return 401 for missing/invalid token

## Database
- Use Motor async driver — all DB operations must be `await`
- Access collections via `database.db["collection_name"]`
- Use `str(ObjectId())` for generating IDs
- Serialize dates as ISO 8601 strings
- Always create indexes in `database.py` for queried fields

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
