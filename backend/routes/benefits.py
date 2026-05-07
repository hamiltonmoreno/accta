from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import List
from models import User, Benefit, BenefitCreate, BenefitUpdate
from database import db
from auth import get_current_user
from helpers import create_audit_log

router = APIRouter(tags=["benefits"])


def _serialize_benefit(b: dict) -> dict:
    if isinstance(b.get("created_at"), str):
        b["created_at"] = datetime.fromisoformat(b["created_at"])
    return b


@router.get("/benefits/public", response_model=List[Benefit])
async def get_public_benefits():
    """Public preview of active benefits — no auth required."""
    benefits = await db.benefits.find({"active": True}, {"_id": 0}).to_list(200)
    for b in benefits:
        _serialize_benefit(b)
    return benefits


@router.get("/benefits", response_model=List[Benefit])
async def get_benefits(current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Benefícios disponíveis apenas para sócios ativos")

    benefits = await db.benefits.find({"active": True}, {"_id": 0}).to_list(1000)
    for b in benefits:
        _serialize_benefit(b)
    return benefits


@router.post("/benefits", response_model=Benefit)
async def create_benefit(benefit_data: BenefitCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    benefit = Benefit(**benefit_data.model_dump())
    benefit_dict = benefit.model_dump()
    benefit_dict["created_at"] = benefit_dict["created_at"].isoformat()

    await db.benefits.insert_one(benefit_dict)
    await create_audit_log(current_user.id, f"Criou benefício {benefit.id}", benefit.id)
    return benefit


@router.patch("/benefits/{benefit_id}", response_model=Benefit)
async def update_benefit(
    benefit_id: str,
    update: BenefitUpdate,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    existing = await db.benefits.find_one({"id": benefit_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Benefício não encontrado")

    changes = update.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Sem alterações a aplicar")

    await db.benefits.update_one({"id": benefit_id}, {"$set": changes})
    await create_audit_log(
        current_user.id,
        f"Atualizou benefício {benefit_id}: {sorted(changes.keys())}",
        benefit_id,
    )

    updated = await db.benefits.find_one({"id": benefit_id}, {"_id": 0})
    _serialize_benefit(updated)
    return updated


@router.delete("/benefits/{benefit_id}")
async def delete_benefit(benefit_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    existing = await db.benefits.find_one({"id": benefit_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Benefício não encontrado")

    await db.benefits.delete_one({"id": benefit_id})
    await create_audit_log(
        current_user.id,
        f"Removeu benefício {existing.get('name', benefit_id)}",
        benefit_id,
    )
    return {"status": "deleted", "id": benefit_id}


@router.post("/benefits/{benefit_id}/validate")
async def validate_benefit_use(
    benefit_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Record that the current user used a benefit.

    Inserts into `benefit_validations` (the source of truth) and audit-logs the
    event. The denormalized `benefits.validation_count` counter is updated as a
    convenience for UI display, but `benefit_validations.count_documents` is
    authoritative for analytics — counter drift is recoverable.
    """
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Apenas sócios ativos podem validar benefícios")

    benefit = await db.benefits.find_one({"id": benefit_id, "active": True}, {"_id": 0})
    if not benefit:
        raise HTTPException(status_code=404, detail="Benefício não encontrado ou inativo")

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.benefit_validations.insert_one(
        {
            "user_id": current_user.id,
            "benefit_id": benefit_id,
            "validated_at": now_iso,
        }
    )
    await db.benefits.update_one({"id": benefit_id}, {"$inc": {"validation_count": 1}})
    # Audit-log even though this is a member action — useful for fraud detection.
    await create_audit_log(
        current_user.id,
        f"Validou benefício {benefit.get('name', benefit_id)}",
        benefit_id,
    )
    return {"status": "validated", "benefit_id": benefit_id, "validated_at": now_iso}
