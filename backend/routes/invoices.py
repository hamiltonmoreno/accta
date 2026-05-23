from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import List
from models import User, Invoice, InvoiceCreate
from database import db
from auth import get_current_user
from helpers import create_audit_log

router = APIRouter(tags=["invoices"])


@router.get("/invoices", response_model=List[Invoice])
async def get_invoices(skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user)):
    limit = min(limit, 100)
    if current_user.role in ["admin", "financeiro"]:
        invoices = await db.invoices.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(None)
    else:
        invoices = (
            await db.invoices.find({"user_id": current_user.id}, {"_id": 0}).skip(skip).limit(limit).to_list(None)
        )

    return invoices


@router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice_data: InvoiceCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "financeiro"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    invoice = Invoice(**invoice_data.model_dump())
    invoice_dict = invoice.model_dump()

    await db.invoices.insert_one(invoice_dict)
    await create_audit_log(current_user.id, f"Criou invoice {invoice.id}", invoice.id)
    return invoice


@router.patch("/invoices/{invoice_id}/confirm")
async def confirm_invoice(invoice_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "financeiro"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    existing = await db.invoices.find_one({"id": invoice_id}, {"_id": 0, "id": 1})
    if not existing:
        raise HTTPException(status_code=404, detail="Invoice não encontrado")

    await db.invoices.update_one(
        {"id": invoice_id},
        {
            "$set": {
                "status": "pago",
                "confirmed_by_admin": True,
                "confirmed_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    await create_audit_log(current_user.id, f"Confirmou pagamento do invoice {invoice_id}", invoice_id)
    return {"message": "Invoice confirmado"}
