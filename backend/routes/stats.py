from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from models import User, MFA_SECRET_FIELDS
from database import db
from auth import get_current_user, has_any_role

router = APIRouter(tags=["stats"])

# Sócios reais: account_type "member" ou ausente (retro-compat). Exclui contas
# técnicas/de sistema (account_type="technical", ex.: admin@controlador.cv) — não
# são sócios e não podem entrar nas contagens do painel. Mesmo filtro canónico de
# routes/users.py, routes/admin.py, ranking.py, assembleias.py.
_MEMBER_FILTER = {"$or": [{"account_type": "member"}, {"account_type": {"$exists": False}}]}


@router.get("/stats")
async def get_statistics(current_user: User = Depends(get_current_user)):
    if not has_any_role(current_user, "admin", "financeiro"):
        raise HTTPException(status_code=403, detail="Sem permissão")

    total_users = await db.users.count_documents(_MEMBER_FILTER)
    active_users = await db.users.count_documents({"$and": [{"status": "ativo"}, _MEMBER_FILTER]})
    # Event não tem campo "status" — "ativo" = evento ainda por acontecer.
    now_iso = datetime.now(timezone.utc).isoformat()
    active_events = await db.events.count_documents({"date": {"$gte": now_iso}})

    return {
        "total_users": total_users,
        "active_users": active_users,
        "active_events": active_events,
    }


# VALIDATOR (PUBLIC)
@router.get("/validate/{qr_hash}")
async def validate_wallet(qr_hash: str):
    user = await db.users.find_one(
        {"qr_code_hash": qr_hash}, {"_id": 0, "password": 0, **dict.fromkeys(MFA_SECRET_FIELDS, 0)}
    )
    if not user:
        raise HTTPException(status_code=404, detail="Carteira não encontrada")

    return {
        "valid": True,
        "name": user["name"],
        "member_id": user.get("member_id"),
        "status": user["status"],
        "admission_date": user.get("admission_date"),
    }
