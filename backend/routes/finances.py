from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from typing import List, Optional
from models import (
    User, Transaction, TransactionCreate, TransactionUpdate,
    FinanceSettings, FinanceSettingsUpdate,
    TRANSACTION_TYPES, INCOME_CATEGORIES, EXPENSE_CATEGORIES
)
from database import db
from auth import get_current_user
from helpers import create_audit_log

router = APIRouter(prefix="/finances", tags=["finances"])


def require_finance_role(user: User):
    if user.role not in ["admin", "financeiro"]:
        raise HTTPException(status_code=403, detail="Sem permissao para gerir financas")


def serialize_transaction(t: dict) -> dict:
    for key in ["date", "created_at"]:
        if isinstance(t.get(key), str):
            t[key] = datetime.fromisoformat(t[key])
    return t


# ===== TRANSACTION ENDPOINTS =====

@router.get("/transactions")
async def list_transactions(
    type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    require_finance_role(current_user)
    limit = min(limit, 200)
    query = {}
    if type:
        query["type"] = type
    if category:
        query["category"] = category
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        query["date"] = date_filter

    transactions = await db.transactions.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(limit).to_list(None)
    for t in transactions:
        serialize_transaction(t)
    return transactions


@router.get("/transactions/count")
async def count_transactions(
    type: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    require_finance_role(current_user)
    query = {}
    if type:
        query["type"] = type
    if category:
        query["category"] = category
    count = await db.transactions.count_documents(query)
    return {"count": count}


@router.post("/transactions")
async def create_transaction(
    data: TransactionCreate,
    current_user: User = Depends(get_current_user),
):
    require_finance_role(current_user)

    if data.type not in TRANSACTION_TYPES:
        raise HTTPException(status_code=400, detail=f"Tipo invalido. Use: {TRANSACTION_TYPES}")

    valid_cats = INCOME_CATEGORIES if data.type == "receita" else EXPENSE_CATEGORIES
    if data.category not in valid_cats:
        raise HTTPException(status_code=400, detail=f"Categoria invalida para {data.type}. Use: {valid_cats}")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="O valor deve ser positivo")

    transaction = Transaction(**data.model_dump(), created_by=current_user.id)
    t_dict = transaction.model_dump()
    t_dict["date"] = t_dict["date"].isoformat()
    t_dict["created_at"] = t_dict["created_at"].isoformat()

    await db.transactions.insert_one(t_dict)
    await create_audit_log(current_user.id, f"Criou transacao {transaction.id} ({data.type}: {data.amount} CVE)", transaction.id)
    return transaction


@router.patch("/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
):
    require_finance_role(current_user)

    existing = await db.transactions.find_one({"id": transaction_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Transacao nao encontrada")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}

    if "type" in updates and updates["type"] not in TRANSACTION_TYPES:
        raise HTTPException(status_code=400, detail=f"Tipo invalido. Use: {TRANSACTION_TYPES}")

    if "category" in updates:
        tx_type = updates.get("type", existing["type"])
        valid_cats = INCOME_CATEGORIES if tx_type == "receita" else EXPENSE_CATEGORIES
        if updates["category"] not in valid_cats:
            raise HTTPException(status_code=400, detail=f"Categoria invalida. Use: {valid_cats}")

    if "amount" in updates and updates["amount"] <= 0:
        raise HTTPException(status_code=400, detail="O valor deve ser positivo")

    if "date" in updates:
        updates["date"] = updates["date"].isoformat()

    if updates:
        await db.transactions.update_one({"id": transaction_id}, {"$set": updates})
        await create_audit_log(current_user.id, f"Atualizou transacao {transaction_id}", transaction_id)

    updated = await db.transactions.find_one({"id": transaction_id}, {"_id": 0})
    serialize_transaction(updated)
    return updated


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
):
    require_finance_role(current_user)

    existing = await db.transactions.find_one({"id": transaction_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Transacao nao encontrada")

    await db.transactions.delete_one({"id": transaction_id})
    await create_audit_log(current_user.id, f"Removeu transacao {transaction_id}", transaction_id)
    return {"message": "Transacao removida"}


# ===== SUMMARY & DRE ENDPOINTS =====

@router.get("/summary")
async def get_financial_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    require_finance_role(current_user)

    query = {}
    if year:
        start = f"{year}-01-01T00:00:00"
        end = f"{year}-12-31T23:59:59"
        if month:
            start = f"{year}-{month:02d}-01T00:00:00"
            if month == 12:
                end = f"{year}-12-31T23:59:59"
            else:
                end = f"{year}-{month + 1:02d}-01T00:00:00"
        query["date"] = {"$gte": start, "$lt": end} if month else {"$gte": start, "$lte": end}

    transactions = await db.transactions.find(query, {"_id": 0}).to_list(None)

    total_receitas = sum(t["amount"] for t in transactions if t["type"] == "receita")
    total_despesas = sum(t["amount"] for t in transactions if t["type"] == "despesa")

    receitas_por_cat = {}
    despesas_por_cat = {}
    for t in transactions:
        if t["type"] == "receita":
            receitas_por_cat[t["category"]] = receitas_por_cat.get(t["category"], 0) + t["amount"]
        else:
            despesas_por_cat[t["category"]] = despesas_por_cat.get(t["category"], 0) + t["amount"]

    return {
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "resultado_liquido": total_receitas - total_despesas,
        "receitas_por_categoria": receitas_por_cat,
        "despesas_por_categoria": despesas_por_cat,
        "total_transacoes": len(transactions),
    }


@router.get("/dre")
async def get_dre_report(
    year: int = Query(..., description="Ano do relatorio"),
    current_user: User = Depends(get_current_user),
):
    require_finance_role(current_user)

    start = f"{year}-01-01T00:00:00"
    end = f"{year}-12-31T23:59:59"
    transactions = await db.transactions.find(
        {"date": {"$gte": start, "$lte": end}}, {"_id": 0}
    ).to_list(None)

    # Monthly breakdown
    monthly = {}
    for m in range(1, 13):
        monthly[m] = {"receitas": 0, "despesas": 0}

    receitas_cat = {}
    despesas_cat = {}

    for t in transactions:
        date_str = t.get("date", "")
        try:
            month = int(date_str[5:7])
        except (ValueError, IndexError):
            continue

        if t["type"] == "receita":
            monthly[month]["receitas"] += t["amount"]
            receitas_cat[t["category"]] = receitas_cat.get(t["category"], 0) + t["amount"]
        else:
            monthly[month]["despesas"] += t["amount"]
            despesas_cat[t["category"]] = despesas_cat.get(t["category"], 0) + t["amount"]

    total_receitas = sum(m["receitas"] for m in monthly.values())
    total_despesas = sum(m["despesas"] for m in monthly.values())

    return {
        "year": year,
        "monthly": monthly,
        "receitas_por_categoria": receitas_cat,
        "despesas_por_categoria": despesas_cat,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "resultado_liquido": total_receitas - total_despesas,
    }


# ===== SETTINGS ENDPOINTS =====

@router.get("/settings")
async def get_finance_settings(
    current_user: User = Depends(get_current_user),
):
    require_finance_role(current_user)
    settings = await db.finance_settings.find_one({"id": "finance_settings"}, {"_id": 0})
    if not settings:
        default = FinanceSettings()
        d = default.model_dump()
        d["updated_at"] = d["updated_at"].isoformat()
        await db.finance_settings.insert_one(d)
        return default
    if isinstance(settings.get("updated_at"), str):
        settings["updated_at"] = datetime.fromisoformat(settings["updated_at"])
    return FinanceSettings(**settings)


@router.patch("/settings")
async def update_finance_settings(
    data: FinanceSettingsUpdate,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar configuracoes")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhuma alteracao fornecida")

    if "quota_amount" in updates and updates["quota_amount"] <= 0:
        raise HTTPException(status_code=400, detail="O valor da quota deve ser positivo")

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    updates["updated_by"] = current_user.id

    existing = await db.finance_settings.find_one({"id": "finance_settings"})
    if not existing:
        default = FinanceSettings()
        d = default.model_dump()
        d.update(updates)
        d["updated_at"] = d["updated_at"] if isinstance(d["updated_at"], str) else d["updated_at"].isoformat()
        await db.finance_settings.insert_one(d)
    else:
        await db.finance_settings.update_one({"id": "finance_settings"}, {"$set": updates})

    await create_audit_log(current_user.id, f"Atualizou configuracoes financeiras: {updates}")
    return {"message": "Configuracoes atualizadas"}


# ===== GENERATE QUOTAS =====

@router.post("/generate-quotas")
async def generate_monthly_quotas(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(...),
    current_user: User = Depends(get_current_user),
):
    require_finance_role(current_user)

    # Get settings for quota amount
    settings = await db.finance_settings.find_one({"id": "finance_settings"}, {"_id": 0})
    quota_amount = settings["quota_amount"] if settings else 2000.0
    quota_desc = settings.get("quota_description", "Quota Mensal") if settings else "Quota Mensal"

    # Get all active members
    active_users = await db.users.find({"status": "ativo"}, {"_id": 0, "id": 1, "name": 1}).to_list(1000)

    # Check which users already have quota for this month
    date_prefix = f"{year}-{month:02d}"
    existing = await db.transactions.find(
        {"category": "quotas", "date": {"$regex": f"^{date_prefix}"}},
        {"_id": 0, "user_id": 1}
    ).to_list(None)
    existing_user_ids = {t["user_id"] for t in existing if t.get("user_id")}

    created_count = 0
    for user in active_users:
        if user["id"] in existing_user_ids:
            continue

        t = Transaction(
            type="receita",
            category="quotas",
            description=f"{quota_desc} - {month:02d}/{year} - {user.get('name', 'Socio')}",
            amount=quota_amount,
            date=datetime.fromisoformat(f"{year}-{month:02d}-15T00:00:00"),
            reference=f"FOLHA-{year}{month:02d}",
            user_id=user["id"],
            created_by=current_user.id,
        )
        t_dict = t.model_dump()
        t_dict["date"] = t_dict["date"].isoformat()
        t_dict["created_at"] = t_dict["created_at"].isoformat()
        await db.transactions.insert_one(t_dict)
        created_count += 1

    await create_audit_log(
        current_user.id,
        f"Gerou {created_count} quotas para {month:02d}/{year} ({quota_amount} CVE cada)"
    )
    return {
        "message": f"{created_count} quotas geradas para {month:02d}/{year}",
        "created": created_count,
        "skipped": len(existing_user_ids),
        "total_value": created_count * quota_amount,
    }


# ===== META ENDPOINTS =====

@router.get("/meta/categories")
async def get_finance_categories(current_user: User = Depends(get_current_user)):
    return {
        "income": INCOME_CATEGORIES,
        "expense": EXPENSE_CATEGORIES,
        "types": TRANSACTION_TYPES,
    }
