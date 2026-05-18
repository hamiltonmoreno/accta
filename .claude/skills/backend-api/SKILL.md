---
name: backend-api
description: Scaffold correct FastAPI endpoints for ACCTA with auth, RBAC, audit, and notifications boilerplate.
user-invocable: true
---

# ACCTA Backend API Patterns

## Route File Boilerplate

```python
from fastapi import APIRouter, Depends, HTTPException
from database import db
from auth import get_current_user
from helpers import create_audit_log, create_notification, notify_admins
from models import FeatureModel, FeatureCreateRequest
from datetime import datetime, timezone
import uuid

router = APIRouter()

@router.get("/")
async def list_items(current_user: dict = Depends(get_current_user)):
    items = await db.collection.find().sort("created_at", -1).to_list(100)
    return items

@router.post("/")
async def create_item(
    data: FeatureCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    # Role check
    if current_user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    doc = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.collection.insert_one(doc)

    # Audit log for admin actions
    await create_audit_log(
        user_id=current_user["id"],
        action="create_item",
        details={"item_id": doc["id"]}
    )

    # Notify relevant users
    await create_notification(
        user_id=current_user["id"],
        type="admin",
        title="Item criado",
        message="Item criado com sucesso."
    )

    return doc
```

## Auth Patterns

```python
# Any authenticated user
current_user: dict = Depends(get_current_user)

# Admin only
if current_user["role"] != "admin":
    raise HTTPException(status_code=403, detail="Apenas administradores")

# Admin or financeiro
if current_user["role"] not in ["admin", "financeiro"]:
    raise HTTPException(status_code=403, detail="Acesso restrito")

# Own resource or admin
if doc["user_id"] != current_user["id"] and current_user["role"] != "admin":
    raise HTTPException(status_code=403, detail="Acesso negado")
```

## Data layer (Mongo-compatible DAO over PostgreSQL/Supabase)

```python
# Find one by ID ({"_id": 0} is a harmless legacy projection no-op)
doc = await db.collection.find_one({"id": item_id}, {"_id": 0})
if not doc:
    raise HTTPException(status_code=404, detail="Não encontrado")

# Paginated list
skip = (page - 1) * limit
items = await db.collection.find(filter).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
total = await db.collection.count_documents(filter)

# Update
await db.collection.update_one(
    {"id": item_id},
    {"$set": {**updates, "updated_at": datetime.now(timezone.utc).isoformat()}}
)

# Delete with check
result = await db.collection.delete_one({"id": item_id})
if result.deleted_count == 0:
    raise HTTPException(status_code=404, detail="Não encontrado")
```

## Notification Types
- `finance` — financial events
- `event` — calendar events
- `project` — project updates
- `poll` — new/closing polls
- `wall` — post approved/rejected
- `gallery` — photo approved/rejected
- `admin` — admin actions
- `system` — system messages

## Register Router in routes/__init__.py

New routers are wired in `backend/routes/__init__.py` (the shared `api_router`
already has `prefix="/api"`; `server.py` only does `app.include_router(api_router)`):

```python
# backend/routes/__init__.py
from routes.feature import router as feature_router
api_router.include_router(feature_router)
```

## Indexes in database.py

Indexes are NOT added via `create_index` in routes. They are declared in
`backend/database.py` inside `ensure_schema()`, which runs on startup and issues
the SQL `CREATE INDEX` statements (expression / partial / GIN on the `doc` jsonb
column) that mirror the original Mongo indexes. Add new index definitions there.
