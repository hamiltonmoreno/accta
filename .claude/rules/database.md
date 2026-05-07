---
paths:
  - "backend/database.py"
  - "backend/models.py"
  - "scripts/**/*.py"
---

# Database Rules — ACCTA Portal (MongoDB)

## Connection
- Async Motor driver via `database.py`
- Database name from `DB_NAME` env variable (default: accta_portal)
- Connection string from `MONGO_URL` env variable

## Collections & Schema
- **users**: email (unique), role, status, invite_token, qr_code_hash
- **transactions**: type (receita/despesa), amount, date, category, user_id
- **projects**: title, status, tasks[], milestones[], expenses[], comments[]
- **events**: title, date, location, attendees[], visibility
- **wall_posts**: content, author_id, status (pending/approved), likes[], comments[]
- **notifications**: user_id, type, message, read, created_at
- **polls**: title, options[], user_votes{}, status
- **invoices**: user_id, amount, status, period
- **gallery_albums**: title, visibility (public/private)
- **gallery_photos**: album_id, url, status (pending/approved/rejected)
- **audit_logs**: action, user_id, details, created_at
- **password_resets**: email, token, used, expires_at
- **finance_settings**: quota_amount, categories

## Indexes (defined in database.py)
- Always add indexes for fields used in queries
- Compound indexes for (user_id, created_at) patterns
- Sparse indexes for optional unique fields (invite_token)
- Descending indexes for date-sorted queries

## Conventions
- Use `str(ObjectId())` for document IDs (stored as string, not ObjectId)
- Dates as ISO 8601 strings (datetime.utcnow().isoformat())
- Embedded documents for sub-items (tasks in projects, comments in posts)
- Never store passwords in plain text — always bcrypt hash
- Soft delete where appropriate (status change, not actual deletion)

## Business Rules
- No "inadimplente" status — quotas are payroll-deducted
- User statuses: ativo, inativo, pendente_convite
- Gallery photos require admin approval before visibility
- Wall posts require moderation (status: pending → approved/rejected)
