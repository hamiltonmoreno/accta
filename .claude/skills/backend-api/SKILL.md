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
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.get("/")
async def list_items(current_user: dict = Depends(get_current_user)):
    items = await db["collection"].find().sort("created_at", -1).to_list(100)
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
        "_id": str(ObjectId()),
        **data.model_dump(),
        "created_by": current_user["id"],
        "created_at": datetime.utcnow().isoformat(),
    }
    await db["collection"].insert_one(doc)

    # Audit log for admin actions
    await create_audit_log(
        action="create_item",
        user_id=current_user["id"],
        details={"item_id": doc["_id"]}
    )

    # Notify relevant users
    await create_notification(
        user_id=current_user["id"],
        type="admin",
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

## MongoDB Patterns

```python
# Find one by ID
doc = await db["collection"].find_one({"_id": item_id})
if not doc:
    raise HTTPException(status_code=404, detail="Não encontrado")

# Paginated list
skip = (page - 1) * limit
items = await db["collection"].find(filter).skip(skip).limit(limit).to_list(limit)
total = await db["collection"].count_documents(filter)

# Update
await db["collection"].update_one(
    {"_id": item_id},
    {"$set": {**updates, "updated_at": datetime.utcnow().isoformat()}}
)

# Delete with check
result = await db["collection"].delete_one({"_id": item_id})
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

## Register Router in server.py

```python
from routes.feature import router as feature_router
app.include_router(feature_router, prefix="/api/feature", tags=["feature"])
```

## Add Index in database.py

```python
await db["collection"].create_index([("user_id", 1), ("created_at", -1)])
await db["collection"].create_index("field", unique=True)
```
