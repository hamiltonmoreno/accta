"""Funções personalizadas (spec 017) — pacotes nomeados de privilégios.

O admin cria funções (ex.: «Coordenador de Eventos») com um conjunto de
privilégios do catálogo canónico e aplica-as a sócios (via PATCH /users/{id}).
Ligação viva: editar os privilégios da função propaga a todos os sócios que a
têm (update_many) — o RBAC em runtime continua a ler `user.privileges`.
Gestão exclusiva de admin (sem overlay manage_users) e 100% auditada.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import get_current_user, is_admin
from database import db
from helpers import create_audit_log, create_notification
from models import CustomRole, CustomRoleCreate, CustomRoleUpdate, User

router = APIRouter(prefix="/admin/custom-roles", tags=["custom-roles"])

# Nomes reservados: keys e rótulos PT das 4 funções fixas (comparação normalizada).
_RESERVED_NAMES = {
    "admin",
    "administracao",
    "administração",
    "administrador",
    "financeiro",
    "moderador",
    "socio",
    "sócio",
}


def _require_admin(user: User):
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Apenas administradores podem gerir funções personalizadas")


def _norm(name: str) -> str:
    return " ".join(name.split()).casefold()


async def _check_name_available(name: str, exclude_id: str | None = None):
    norm = _norm(name)
    if norm in _RESERVED_NAMES:
        raise HTTPException(status_code=400, detail="Já existe uma função com este nome")
    existing = await db.custom_roles.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(None)
    for other in existing:
        if other.get("id") != exclude_id and _norm(other.get("name", "")) == norm:
            raise HTTPException(status_code=400, detail="Já existe uma função com este nome")


async def _user_counts() -> dict:
    """Contagem de utilizadores por função personalizada (1 query, sem N+1)."""
    rows = await db.users.find({}, {"_id": 0, "custom_role_id": 1}).to_list(None)
    counts: dict = {}
    for r in rows:
        crid = r.get("custom_role_id")
        if crid:
            counts[crid] = counts.get(crid, 0) + 1
    return counts


@router.get("")
async def list_custom_roles(current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    roles = await db.custom_roles.find({}, {"_id": 0}).to_list(None)
    counts = await _user_counts()
    for r in roles:
        r["user_count"] = counts.get(r["id"], 0)
    roles.sort(key=lambda r: _norm(r.get("name", "")))
    return {"custom_roles": roles}


@router.post("")
async def create_custom_role(
    data: CustomRoleCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    await _check_name_available(data.name)

    role = CustomRole(
        name=data.name,
        description=data.description,
        privileges=data.privileges,
        created_by=current_user.id,
    )
    doc = role.model_dump()
    await db.custom_roles.insert_one(doc)

    await create_audit_log(
        current_user.id,
        "custom_role_created",
        role.id,
        request=request,
        details={"name": role.name, "privileges": role.privileges},
    )
    doc.pop("_id", None)
    doc["user_count"] = 0
    return doc


@router.patch("/{role_id}")
async def update_custom_role(
    role_id: str,
    data: CustomRoleUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    existing = await db.custom_roles.find_one({"id": role_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Função não encontrada")

    update = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    if "name" in update:
        await _check_name_available(update["name"], exclude_id=role_id)

    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.custom_roles.update_one({"id": role_id}, {"$set": update})

    # Ligação viva (FR-005): privilégios alterados propagam a todos os sócios
    # com esta função, num único update_many, e cada afetado é notificado.
    propagated_to = 0
    if "privileges" in update and update["privileges"] != existing.get("privileges"):
        holders = await db.users.find({"custom_role_id": role_id}, {"_id": 0, "id": 1}).to_list(None)
        if holders:
            await db.users.update_many(
                {"custom_role_id": role_id},
                {"$set": {"privileges": update["privileges"]}},
            )
            for h in holders:
                await create_notification(
                    h["id"],
                    "profile_updated",
                    "Perfil Atualizado",
                    f"A sua função «{update.get('name', existing['name'])}» foi atualizada por um administrador.",
                    "/perfil",
                )
        propagated_to = len(holders)

    await create_audit_log(
        current_user.id,
        "custom_role_updated",
        role_id,
        request=request,
        details={
            "before": {k: existing.get(k) for k in update if k != "updated_at"},
            "after": {k: v for k, v in update.items() if k != "updated_at"},
            "propagated_to": propagated_to,
        },
    )

    updated = await db.custom_roles.find_one({"id": role_id}, {"_id": 0})
    updated["propagated_to"] = propagated_to
    return updated


@router.delete("/{role_id}")
async def delete_custom_role(
    role_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    existing = await db.custom_roles.find_one({"id": role_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Função não encontrada")

    in_use = await db.users.count_documents({"custom_role_id": role_id})
    if in_use:
        raise HTTPException(
            status_code=409,
            detail=f"Função atribuída a {in_use} sócio(s). Retire a função antes de eliminar.",
        )

    await db.custom_roles.delete_one({"id": role_id})
    await create_audit_log(
        current_user.id,
        "custom_role_deleted",
        role_id,
        request=request,
        details={"name": existing.get("name")},
    )
    return {"message": "Função eliminada"}
