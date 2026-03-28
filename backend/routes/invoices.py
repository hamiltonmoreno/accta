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
        invoices = await db.invoices.find({"user_id": current_user.id}, {"_id": 0}).skip(skip).limit(limit).to_list(None)

    for inv in invoices:
        if isinstance(inv.get('due_date'), str):
            inv['due_date'] = datetime.fromisoformat(inv['due_date'])
        if isinstance(inv.get('created_at'), str):
            inv['created_at'] = datetime.fromisoformat(inv['created_at'])
        if inv.get('confirmed_at') and isinstance(inv['confirmed_at'], str):
            inv['confirmed_at'] = datetime.fromisoformat(inv['confirmed_at'])
    return invoices


@router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice_data: InvoiceCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "financeiro"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    invoice = Invoice(**invoice_data.model_dump())
    invoice_dict = invoice.model_dump()
    invoice_dict['due_date'] = invoice_dict['due_date'].isoformat()
    invoice_dict['created_at'] = invoice_dict['created_at'].isoformat()
    if invoice_dict.get('confirmed_at'):
        invoice_dict['confirmed_at'] = invoice_dict['confirmed_at'].isoformat()

    await db.invoices.insert_one(invoice_dict)
    await create_audit_log(current_user.id, f"Criou invoice {invoice.id}", invoice.id)
    return invoice


@router.patch("/invoices/{invoice_id}/confirm")
async def confirm_invoice(invoice_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "financeiro"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {
            "status": "pago",
            "confirmed_by_admin": True,
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    await create_audit_log(current_user.id, f"Confirmou pagamento do invoice {invoice_id}", invoice_id)
    return {"message": "Invoice confirmado"}
