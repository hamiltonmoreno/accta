# Backend Copilot Instructions — ACCTA Portal FastAPI Server

## Quick Start

Run the backend development server:
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

---

## Architecture Overview

### Project Structure

```
backend/
├── server.py                 # FastAPI app setup, middleware, CORS
├── database.py               # asyncpg (PostgreSQL/Supabase) connection pool + Mongo-compatible DAO, UPLOAD_DIR, utilities
├── models.py                 # Pydantic models (User, Invoice, Poll, etc.)
├── auth.py                   # JWT creation/validation, password hashing
├── helpers.py                # Shared utilities (email, QR, PDF generation)
├── requirements.txt          # Python dependencies
│
├── routes/                   # FastAPI routers (organized by feature)
│   ├── __init__.py           # Router aggregation (includes all module routers)
│   ├── auth_routes.py        # /api/auth/* (login, register, token refresh)
│   ├── users.py              # /api/users/* (CRUD, profile, admin mgmt)
│   ├── invoices.py           # /api/invoices/* (billing, PDF/CSV export)
│   ├── polls.py              # /api/polls/* (voting)
│   ├── posts.py              # /api/posts/* (social posts)
│   ├── documents.py          # /api/documents/* (institutional docs)
│   ├── benefits.py           # /api/benefits/* (club benefits, QR validation)
│   ├── wall.py               # /api/wall/* (mural de comunicação)
│   ├── events.py             # /api/events/* (events, calendar, registration)
│   ├── gallery.py            # /api/gallery/* (photos, albums, approval workflow)
│   ├── notifications.py      # /api/notifications/* (central, broadcast, triggers)
│   ├── finances.py           # /api/finances/* (DRE, cash flow, analytics)
│   ├── projects.py           # /api/projects/* (CRUD, tasks, milestones, budget)
│   ├── activity.py           # /api/activity/* (activity feed)
│   ├── report.py             # /api/report/* (export reports)
│   ├── stats.py              # /api/stats/* (public transparency stats)
│   └── upload.py             # /api/upload/* (file handling)
│
├── tests/                    # Test suite (pytest)
│   ├── test_accta_portal.py
│   ├── test_auth_*.py
│   ├── test_finances.py
│   ├── test_gallery*.py
│   └── ...
│
└── uploads/                  # User-uploaded files (local storage)
    └── documents/
```

---

## Core Patterns

### 1. Models (Pydantic)

**Pattern:**
```python
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime, timezone
from typing import Optional, List
import uuid

# Base model (shared fields)
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "socio"
    status: str = "ativo"
    phone_number: Optional[str] = None
    privileges: List[str] = []

# Create model (input validation)
class UserCreate(UserBase):
    password: str

# Update model (partial updates)
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None

# Full model (database representation)
class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qr_code_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Key Rules:**
- Always use `Field(default_factory=...)` for dynamic defaults
- Use `timezone.utc` for all timestamps
- Separate Base/Create/Update/Read models
- Use `ConfigDict(extra="ignore")` to ignore unexpected fields

### 2. Routes (FastAPI)

**Pattern:**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from database import db
from auth import get_current_user, require_admin
from models import User, UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

# GET all (public or authorized)
@router.get("/")
async def list_users(skip: int = 0, limit: int = 100):
    users = await db.users.find().skip(skip).limit(limit).to_list(limit)
    return users

# GET by ID
@router.get("/{user_id}")
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# POST create (admin only)
@router.post("/", status_code=201)
async def create_user(
    user: UserCreate,
    current_user: dict = Depends(require_admin),
):
    # Validate
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Hash password
    from auth import hash_password
    import uuid
    user_dict = user.model_dump()
    user_dict["id"] = str(uuid.uuid4())
    user_dict["password_hash"] = hash_password(user.password)
    del user_dict["password"]
    
    # Insert
    await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"id": user_dict["id"]}, {"_id": 0})
    return created_user

# PUT update (admin only)
@router.put("/{user_id}")
async def update_user(
    user_id: str,
    update: UserUpdate,
    current_user: dict = Depends(require_admin),
):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update.model_dump(exclude_unset=True)}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    return updated_user

# DELETE
@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
):
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return None
```

**Key Rules:**
- Prefix router with feature name: `APIRouter(prefix="/feature")`
- Use `Depends(get_current_user)` for auth checks
- Use `Depends(require_admin)` for admin-only routes
- Always validate before insert/update
- Use `raise HTTPException(status_code=..., detail="...")` for errors
- Documents use an app-generated UUID string `id` (`str(uuid.uuid4())`) — there is no Mongo `_id`; filter/lookup by the domain `id` field. The legacy `{"_id": 0}` projection is a harmless no-op

### 3. Database (PostgreSQL/Supabase via the Mongo-compatible DAO)

`database.py` is an async `asyncpg` connection pool that exposes a Mongo-compatible DAO,
so call sites keep using `find_one`, `insert_one`, `update_one({"$set": ...})`,
`aggregate([...])` and cursor chaining. Documents carry an app-generated UUID string
`id` (there is no Mongo `_id`); filter by the domain `id` field.

**Pattern:**
```python
from database import db
from datetime import datetime, timezone
import uuid

# Find all
async def get_all_items():
    return await db.items.find().to_list(None)

# Find by ID
async def get_item(item_id: str):
    return await db.items.find_one({"id": item_id}, {"_id": 0})

# Insert
async def create_item(item_data: dict):
    item_data['id'] = str(uuid.uuid4())
    item_data['created_at'] = datetime.now(timezone.utc).isoformat()
    await db.items.insert_one(item_data)
    return await db.items.find_one({"id": item_data["id"]}, {"_id": 0})

# Update
async def update_item(item_id: str, update_data: dict):
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    result = await db.items.update_one(
        {"id": item_id},
        {"$set": update_data}
    )
    return result.modified_count > 0

# Delete
async def delete_item(item_id: str):
    result = await db.items.delete_one({"id": item_id})
    return result.deleted_count > 0

# Find with filter
async def find_items(query: dict, skip: int = 0, limit: int = 100):
    return await db.items.find(query).skip(skip).limit(limit).to_list(limit)

# Aggregate (pipeline)
async def get_stats():
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    return await db.items.aggregate(pipeline).to_list(None)
```

### 4. Authentication (JWT)

**Pattern:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from auth import decode_token, get_current_user, require_admin

# Basic dependency (logged-in user required)
async def get_current_user(credentials: HTTPAuthCredentials = Depends(HTTPBearer())):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

# Admin-only dependency
async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Usage in routes
@router.post("/admin-action")
async def admin_action(current_user: dict = Depends(require_admin)):
    # Only admins can access this
    return {"message": "Admin action completed"}

# For specific privileges
@router.post("/manage-finances")
async def manage_finances(current_user: dict = Depends(get_current_user)):
    if "manage_finances" not in current_user.get("privileges", []):
        raise HTTPException(status_code=403, detail="Permission denied")
    return {"message": "Finance action"}
```

---

## Common Tasks

### File Upload
```python
from fastapi import UploadFile, File
from pathlib import Path
from database import UPLOAD_DIR

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = Path(UPLOAD_DIR) / "documents" / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"url": f"/uploads/documents/{file.filename}"}
```

### QR Code Generation
```python
from helpers import generate_qr_code

@router.get("/qr/{user_id}")
async def get_qr(user_id: str):
    data = f"ACCTA-{user_id}"
    qr_url = generate_qr_code(data)
    return {"qr_url": qr_url}
```

### Export PDF
```python
from fpdf import FPDF
from datetime import datetime

@router.get("/export/pdf/{invoice_id}")
async def export_invoice(invoice_id: str):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Invoice {invoice_id}", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Amount: ${invoice['amount']}", ln=True)
    
    pdf_path = f"./uploads/invoices/{invoice_id}.pdf"
    pdf.output(pdf_path)
    return FileResponse(pdf_path)
```

### Email Notification
```python
from helpers import send_email

@router.post("/notify/{user_id}")
async def notify_user(user_id: str, message: str):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    await send_email(
        to=user['email'],
        subject="ACCTA Notification",
        body=message
    )
    return {"status": "sent"}
```

---

## Error Handling

**Standard HTTP Status Codes:**
```python
# 200 OK
return {"data": result}

# 201 Created
@router.post("/", status_code=201)
async def create(...):
    return new_item

# 400 Bad Request
raise HTTPException(status_code=400, detail="Invalid input")

# 401 Unauthorized
raise HTTPException(status_code=401, detail="Please log in")

# 403 Forbidden
raise HTTPException(status_code=403, detail="Admin access required")

# 404 Not Found
raise HTTPException(status_code=404, detail="Item not found")

# 500 Internal Server Error
raise HTTPException(status_code=500, detail="Error processing request")
```

---

## Testing (Pytest)

**Pattern:**
```python
import pytest
from fastapi.testclient import TestClient
from server import app
from database import db

client = TestClient(app)

@pytest.fixture
async def sample_user():
    import uuid
    user = {
        "id": str(uuid.uuid4()),
        "name": "John Doe",
        "email": "john@example.com",
        "password": "secret123",
        "role": "socio"
    }
    await db.users.insert_one(user)
    yield user
    await db.users.delete_one({"id": user["id"]})

def test_list_users():
    response = client.get("/api/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_user():
    response = client.post("/api/users/", json={
        "name": "Jane",
        "email": "jane@example.com",
        "password": "secret",
        "role": "socio"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "jane@example.com"

def test_unauthorized():
    response = client.post("/api/admin-action")
    assert response.status_code == 401
```

**Run tests:**
```bash
cd backend
pytest tests/ -v
pytest tests/test_users.py -v
pytest tests/ --cov  # Coverage report
```

---

## Environment Variables

**`backend/.env`**:
```
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
JWT_SECRET=your-super-secret-key-change-this
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
UPLOAD_DIR=./uploads
S3_BUCKET=your-bucket
S3_REGION=us-east-1
S3_ACCESS_KEY=xxx
S3_SECRET_KEY=xxx
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

---

## Rate Limiting

Default: 200 requests/minute

**Check/adjust in `server.py`:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

@router.get("/expensive-operation")
@limiter.limit("1/minute")  # Override for specific endpoint
async def expensive_op(request: Request):
    return {"result": "done"}
```

---

## Debugging Tips

1. **Database not connecting?** Is `DATABASE_URL` valid? Is the Supabase pooler reachable on port 6543 (transaction mode)? Is `statement_cache_size=0` set for pgbouncer? The backend raises `RuntimeError` at startup if `DATABASE_URL` is missing
2. **CORS errors?** Update `CORS_ORIGINS` env var and restart server
3. **JWT expired?** Token TTL is 24h by default; implement refresh token rotations
4. **File upload fails?** Ensure `UPLOAD_DIR` path exists and is writable
5. **Tests failing?** Check database state; use fixtures to clean up after tests

---

## Recommended Copilot Prompts

- "Add a new endpoint to export users as CSV"
- "Create a database migration to add a new field to User model"
- "Implement rate limiting for the login endpoint"
- "Fix the JWT refresh token logic"
- "Add automatic email notifications when invoices are due"

---

**Last Updated**: April 2, 2026  
**Version**: 1.0
