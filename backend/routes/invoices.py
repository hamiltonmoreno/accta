from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import List
from models import User, Invoice, InvoiceCreate
from database import db
from auth import can_manage_finances, can_view_finances, get_current_user
from helpers import create_audit_log

router = APIRouter(tags=["invoices"])


@router.get("/invoices", response_model=List[Invoice])
async def get_invoices(skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user)):
    limit = min(limit, 100)
    # RBAC coerente com o módulo de finanças: admin/financeiro OU privilégio
    # (view_finances_readonly do Conselho Fiscal / manage_finances) veem todos;
    # os restantes só os próprios. Antes era comparação crua de role e quem
    # tinha o privilégio ficava de fora.
    if can_view_finances(current_user):
        invoices = await db.invoices.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(None)
    else:
        invoices = (
            await db.invoices.find({"user_id": current_user.id}, {"_id": 0}).skip(skip).limit(limit).to_list(None)
        )

    return invoices


@router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice_data: InvoiceCreate, current_user: User = Depends(get_current_user)):
    if not can_manage_finances(current_user):
        raise HTTPException(status_code=403, detail="Sem permissão")

    invoice = Invoice(**invoice_data.model_dump())
    invoice_dict = invoice.model_dump()

    await db.invoices.insert_one(invoice_dict)
    await create_audit_log(
        current_user.id,
        f"Criou invoice {invoice.id}",
        invoice.id,
        details={"user_id": invoice.user_id, "amount": invoice.amount},
    )
    return invoice


@router.patch("/invoices/{invoice_id}/confirm")
async def confirm_invoice(invoice_id: str, current_user: User = Depends(get_current_user)):
    if not can_manage_finances(current_user):
        raise HTTPException(status_code=403, detail="Sem permissão")

    existing = await db.invoices.find_one({"id": invoice_id}, {"_id": 0, "id": 1, "status": 1, "user_id": 1, "amount": 1})
    if not existing:
        raise HTTPException(status_code=404, detail="Invoice não encontrado")
    if existing.get("status") == "pago":
        raise HTTPException(status_code=400, detail="Invoice já confirmado")

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
    # Audit com o contexto necessário para investigação (quem/quanto/de onde
    # veio o estado) — só o id não permitia reconstruir a ação financeira.
    await create_audit_log(
        current_user.id,
        f"Confirmou pagamento do invoice {invoice_id}",
        invoice_id,
        details={
            "user_id": existing.get("user_id"),
            "amount": existing.get("amount"),
            "previous_status": existing.get("status"),
        },
    )
    return {"message": "Invoice confirmado"}
