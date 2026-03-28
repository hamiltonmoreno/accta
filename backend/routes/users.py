from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List
from models import User
from database import db
from auth import get_current_user
from helpers import create_audit_log

router = APIRouter(tags=["users"])


@router.get("/users", response_model=List[User])
async def get_users(skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "financeiro"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    limit = min(limit, 100)
    users = await db.users.find({}, {"_id": 0, "password": 0}).skip(skip).limit(limit).to_list(None)
    for u in users:
        if isinstance(u.get('created_at'), str):
            u['created_at'] = datetime.fromisoformat(u['created_at'])
        if u.get('admission_date') and isinstance(u['admission_date'], str):
            u['admission_date'] = datetime.fromisoformat(u['admission_date'])
        if u.get('last_login_at') and isinstance(u['last_login_at'], str):
            u['last_login_at'] = datetime.fromisoformat(u['last_login_at'])
    return users


@router.patch("/users/{user_id}/status")
async def update_user_status(user_id: str, status: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    await db.users.update_one({"id": user_id}, {"$set": {"status": status}})
    await create_audit_log(current_user.id, f"Alterou status do usuário {user_id} para {status}", user_id)
    return {"message": "Status atualizado"}
