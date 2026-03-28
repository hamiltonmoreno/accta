from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List
from models import User, Benefit, BenefitCreate
from database import db
from auth import get_current_user
from helpers import create_audit_log

router = APIRouter(tags=["benefits"])


@router.get("/benefits", response_model=List[Benefit])
async def get_benefits(current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Benefícios disponíveis apenas para sócios ativos")

    benefits = await db.benefits.find({"active": True}, {"_id": 0}).to_list(1000)
    for b in benefits:
        if isinstance(b.get('created_at'), str):
            b['created_at'] = datetime.fromisoformat(b['created_at'])
    return benefits


@router.post("/benefits", response_model=Benefit)
async def create_benefit(benefit_data: BenefitCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    benefit = Benefit(**benefit_data.model_dump())
    benefit_dict = benefit.model_dump()
    benefit_dict['created_at'] = benefit_dict['created_at'].isoformat()

    await db.benefits.insert_one(benefit_dict)
    await create_audit_log(current_user.id, f"Criou benefício {benefit.id}", benefit.id)
    return benefit
