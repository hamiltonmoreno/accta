---
paths:
  - "backend/models.py"
  - "backend/helpers.py"
  - "backend/email_service.py"
---

# Models & Helpers Rules — ACCTA Portal

## models.py — Pydantic Models

- Use Pydantic v2 syntax (`model_dump()`, not `.dict()`)
- All request bodies have a dedicated `*CreateRequest` or `*UpdateRequest` model
- All optional fields use `Optional[T] = None`
- Dates are strings (ISO 8601) — never Python `datetime` objects in models
- Never expose `password` in response models — create separate response schemas
- Use `Field(default=None)` for optional fields with metadata

```python
# Correct pattern
class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    status: str
    created_at: Optional[str] = None
    # password is NOT here
```

## helpers.py — Notification & Audit Functions

### create_notification(user_id, type, message, link=None)
- Always `await` it
- `type` must be one of: `finance`, `event`, `project`, `poll`, `wall`, `gallery`, `admin`, `system`
- `message` in Portuguese
- `link` is optional frontend route (e.g., `/projetos/123`)

### notify_users(user_ids, type, message, link=None)
- For bulk notifications to specific users
- Pass list of user ID strings

### notify_all_active_users(type, message, link=None)
- Broadcast to all active members
- Use sparingly — only for system-wide events

### notify_admins(type, message, link=None)
- Alerts only users with role `admin`
- Use for moderation alerts, system errors

### create_audit_log(action, user_id, details)
- MUST be called for every admin write action
- `action`: snake_case string (e.g., `create_user`, `delete_transaction`)
- `details`: dict with relevant IDs and changed fields
- Never skip this for admin operations

## email_service.py — Resend Integration

- All email functions are async — always `await`
- Available functions: `send_invite_email`, `send_password_reset_email`, `send_welcome_email`
- Emails use ACCTA HTML templates with brand colors
- **STOP CONDITION**: Never call email functions on real users without confirming with the user
- Test with dummy emails in development
