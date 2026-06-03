from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from models import User, MFA_SECRET_FIELDS
from database import db
from auth import get_current_user

router = APIRouter(tags=["stats"])


@router.get("/stats")
async def get_statistics(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "financeiro"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"status": "ativo"})
    # Event não tem campo "status" — "ativo" = evento ainda por acontecer.
    now_iso = datetime.now(timezone.utc).isoformat()
    active_events = await db.events.count_documents({"date": {"$gte": now_iso}})
    total_revenue = await db.invoices.aggregate(
        [{"$match": {"status": "pago"}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    ).to_list(1)

    return {
        "total_users": total_users,
        "active_users": active_users,
        "active_events": active_events,
        "total_revenue": total_revenue[0]["total"] if total_revenue else 0,
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
