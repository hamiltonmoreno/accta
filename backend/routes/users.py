from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List, Optional
import re
from models import User, UserProfileUpdate, UserAdminUpdate, CARGOS, PRIVILEGES
from database import db
from auth import get_current_user
from helpers import create_audit_log, create_notification

router = APIRouter(tags=["users"])


def parse_user_dates(u: dict):
    """Parse ISO date strings to datetime objects."""
    for field in ["created_at", "admission_date", "last_login_at"]:
        if u.get(field) and isinstance(u[field], str):
            u[field] = datetime.fromisoformat(u[field])


# ===== LIST USERS =====
@router.get("/users", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    cargo: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["admin", "financeiro"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    query = {}
    if search:
        # re.escape impede metacaracteres ($, ., *, etc.) — input vira literal,
        # bloqueando ReDoS e bypass de filtros via regex injection.
        safe = re.escape(search.strip())[:100]  # limita comprimento (ReDoS guard)
        query["$or"] = [
            {"name": {"$regex": safe, "$options": "i"}},
            {"email": {"$regex": safe, "$options": "i"}},
            {"member_id": {"$regex": safe, "$options": "i"}},
        ]
    if role:
        query["role"] = role
    if status:
        query["status"] = status
    if cargo:
        query["cargo"] = cargo

    limit = min(limit, 100)
    users = await db.users.find(query, {"_id": 0, "password": 0}).skip(skip).limit(limit).to_list(limit)
    for u in users:
        parse_user_dates(u)
    return users


# ===== GET SINGLE USER =====
@router.get("/users/{user_id}")
async def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    # Self ou staff (admin/financeiro) — restantes não veem PII de terceiros
    is_self = current_user.id == user_id
    is_staff = current_user.role in ("admin", "financeiro")
    if not (is_self or is_staff):
        raise HTTPException(status_code=403, detail="Sem permissão")

    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    parse_user_dates(user_doc)
    return user_doc


# ===== UPDATE OWN PROFILE =====
@router.patch("/users/me/profile")
async def update_own_profile(data: UserProfileUpdate, current_user: User = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    await db.users.update_one({"id": current_user.id}, {"$set": update_data})

    # Return updated user
    updated = await db.users.find_one({"id": current_user.id}, {"_id": 0, "password": 0})
    parse_user_dates(updated)
    await create_audit_log(current_user.id, "Atualizou o próprio perfil")
    return updated


# ===== ADMIN UPDATE USER =====
@router.patch("/users/{user_id}")
async def admin_update_user(user_id: str, data: UserAdminUpdate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem editar utilizadores")

    existing = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    # Validate cargo
    if "cargo" in update_data and update_data["cargo"] not in CARGOS:
        raise HTTPException(status_code=400, detail=f"Cargo inválido. Opções: {', '.join(CARGOS)}")

    # Validate privileges
    if "privileges" in update_data:
        invalid = [p for p in update_data["privileges"] if p not in PRIVILEGES]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Privilégios inválidos: {', '.join(invalid)}")

    # Validate role
    valid_roles = ["admin", "socio", "financeiro", "moderador"]
    if "role" in update_data and update_data["role"] not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role inválido. Opções: {', '.join(valid_roles)}")

    await db.users.update_one({"id": user_id}, {"$set": update_data})

    changes = ", ".join([f"{k}={v}" for k, v in update_data.items()])
    await create_audit_log(current_user.id, f"Editou utilizador {existing.get('name', user_id)}: {changes}", user_id)

    # Notify user of role/cargo changes
    notify_fields = {"role", "cargo", "privileges", "status"}
    if notify_fields & set(update_data.keys()):
        await create_notification(
            user_id,
            "profile_updated",
            "Perfil Atualizado",
            "O seu perfil foi atualizado por um administrador. Verifique as alterações.",
            "/perfil",
        )

    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    parse_user_dates(updated)
    return updated


# ===== UPDATE USER STATUS (legacy, kept for backwards compat) =====
@router.patch("/users/{user_id}/status")
async def update_user_status(user_id: str, status: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    await db.users.update_one({"id": user_id}, {"$set": {"status": status}})
    await create_audit_log(current_user.id, f"Alterou status de {user_id} para {status}", user_id)
    return {"message": "Status atualizado"}


# ===== DELETE USER =====
@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem remover utilizadores")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Não pode remover a própria conta")

    existing = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")

    await db.users.delete_one({"id": user_id})
    await create_audit_log(current_user.id, f"Removeu utilizador {existing.get('name', user_id)}", user_id)
    return {"message": "Utilizador removido com sucesso"}


# ===== METADATA ENDPOINTS =====
@router.get("/users/meta/cargos")
async def get_cargos():
    return {"cargos": CARGOS}


@router.get("/users/meta/privileges")
async def get_privileges():
    return {"privileges": PRIVILEGES}
