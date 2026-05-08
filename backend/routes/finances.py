from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from typing import Optional
import re
from models import (
    User,
    Transaction,
    TransactionCreate,
    TransactionUpdate,
    FinanceSettings,
    FinanceSettingsUpdate,
    TRANSACTION_TYPES,
    INCOME_CATEGORIES,
    EXPENSE_CATEGORIES,
)
from database import db
from auth import get_current_user
from helpers import create_audit_log, notify_admins, notify_all_active_users
from fpdf import FPDF
import io


def _safe_search_regex(s: str) -> str:
    """Escape regex metachars + cap length to prevent ReDoS."""
    return re.escape(s.strip())[:100]


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
    search: Optional[str] = None,
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
    if search:
        query["description"] = {"$regex": _safe_search_regex(search), "$options": "i"}

    total = await db.transactions.count_documents(query)
    transactions = await db.transactions.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(limit).to_list(None)
    for t in transactions:
        serialize_transaction(t)
    return {"items": transactions, "total": total, "skip": skip, "limit": limit}


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
    await create_audit_log(
        current_user.id, f"Criou transacao {transaction.id} ({data.type}: {data.amount} CVE)", transaction.id
    )

    # Notify admins about new transaction (if creator is financeiro, not admin)
    tipo_label = "Receita" if data.type == "receita" else "Despesa"
    await notify_admins(
        "financeiro",
        f"Nova {tipo_label}: {data.amount:,.0f} CVE",
        f"{current_user.name} registou: {data.description}",
        "/financeiro",
        exclude_id=current_user.id,
    )

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

    transactions = (
        await db.transactions.find(
            query, {"_id": 0, "type": 1, "amount": 1, "category": 1, "description": 1, "date": 1}
        )
        .limit(5000)
        .to_list(5000)
    )

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
    transactions = (
        await db.transactions.find(
            {"date": {"$gte": start, "$lte": end}}, {"_id": 0, "date": 1, "type": 1, "amount": 1, "category": 1}
        )
        .limit(5000)
        .to_list(5000)
    )

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

    # Notify admins about settings change
    if "quota_amount" in updates:
        await notify_admins(
            "financeiro",
            "Valor da Quota Atualizado",
            f"{current_user.name} alterou o valor da quota mensal para {updates['quota_amount']:,.0f} CVE.",
            "/financeiro",
            exclude_id=current_user.id,
        )

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

    # Check which users already have quota for this month — usar range query
    # ($gte/$lt) em vez de $regex, melhor para o indice composto (category, date).
    month_start = f"{year}-{month:02d}-01"
    next_month_start = f"{year + 1}-01-01" if month == 12 else f"{year}-{month + 1:02d}-01"
    existing = await db.transactions.find(
        {"category": "quotas", "date": {"$gte": month_start, "$lt": next_month_start}},
        {"_id": 0, "user_id": 1},
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
        current_user.id, f"Gerou {created_count} quotas para {month:02d}/{year} ({quota_amount} CVE cada)"
    )

    # Notify all active users that quotas were generated
    if created_count > 0:
        MONTH_NAMES_SHORT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        mes_label = MONTH_NAMES_SHORT[month - 1]
        await notify_all_active_users(
            "financeiro",
            f"Quotas de {mes_label}/{year} Geradas",
            f"As quotas mensais de {mes_label}/{year} ({quota_amount:,.0f} CVE) foram geradas e serao descontadas em folha de pagamento.",
            "/financeiro",
        )

    return {
        "message": f"{created_count} quotas geradas para {month:02d}/{year}",
        "created": created_count,
        "skipped": len(existing_user_ids),
        "total_value": created_count * quota_amount,
    }


CATEGORY_LABELS = {
    "quotas": "Quotas de Socios",
    "patrocinios": "Patrocinios",
    "doacoes": "Doacoes",
    "eventos": "Eventos",
    "outros_receita": "Outras Receitas",
    "operacional": "Operacional",
    "juridico": "Juridico",
    "comunicacao": "Comunicacao",
    "viagens": "Viagens",
    "outros_despesa": "Outras Despesas",
}

CATEGORY_LABELS_CSV = CATEGORY_LABELS

MONTH_NAMES = [
    "Janeiro",
    "Fevereiro",
    "Marco",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


# ===== CSV EXPORT =====


@router.get("/transactions/csv")
async def export_transactions_csv(
    type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    require_finance_role(current_user)

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
    if search:
        query["description"] = {"$regex": _safe_search_regex(search), "$options": "i"}

    transactions = await db.transactions.find(query, {"_id": 0}).sort("date", -1).limit(5000).to_list(None)

    import csv

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Data", "Tipo", "Categoria", "Descricao", "Valor (CVE)", "Referencia"])
    for t in transactions:
        date_str = t.get("date", "")[:10] if t.get("date") else ""
        writer.writerow(
            [
                date_str,
                "Receita" if t["type"] == "receita" else "Despesa",
                CATEGORY_LABELS_CSV.get(t.get("category", ""), t.get("category", "")),
                t.get("description", ""),
                f"{t['amount']:.2f}",
                t.get("reference", "") or "",
            ]
        )

    csv_bytes = buf.getvalue().encode("utf-8-sig")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=Fluxo_Caixa_ACCTA.csv"},
    )


# ===== PDF EXPORT =====


@router.get("/dre/pdf")
async def export_dre_pdf(
    year: int = Query(..., description="Ano do relatorio"),
    current_user: User = Depends(get_current_user),
):
    require_finance_role(current_user)

    start = f"{year}-01-01T00:00:00"
    end = f"{year}-12-31T23:59:59"
    transactions = (
        await db.transactions.find({"date": {"$gte": start, "$lte": end}}, {"_id": 0}).limit(10000).to_list(None)
    )

    monthly = {}
    for m in range(1, 13):
        monthly[m] = {"receitas": 0, "despesas": 0}

    receitas_cat = {}
    despesas_cat = {}

    for t in transactions:
        date_str = t.get("date", "")
        try:
            m = int(date_str[5:7])
        except (ValueError, IndexError):
            continue
        if t["type"] == "receita":
            monthly[m]["receitas"] += t["amount"]
            receitas_cat[t["category"]] = receitas_cat.get(t["category"], 0) + t["amount"]
        else:
            monthly[m]["despesas"] += t["amount"]
            despesas_cat[t["category"]] = despesas_cat.get(t["category"], 0) + t["amount"]

    total_receitas = sum(v["receitas"] for v in monthly.values())
    total_despesas = sum(v["despesas"] for v in monthly.values())
    resultado = total_receitas - total_despesas

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- Header ---
    pdf.set_fill_color(199, 32, 47)  # Carmesim
    pdf.rect(0, 0, 210, 40, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_y(10)
    pdf.cell(0, 10, "ACCTA - Cabo Verde", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Demonstracao do Resultado do Exercicio - {year}", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(58, 58, 58)  # Grafite
    pdf.set_y(48)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(
        0,
        5,
        f"Gerado em {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC",
        align="R",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)

    # --- Summary Box ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Resumo Anual", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    box_w = 58
    box_h = 22
    x_start = pdf.get_x()
    y_start = pdf.get_y()

    # Receitas box
    pdf.set_fill_color(240, 253, 244)
    pdf.rect(x_start, y_start, box_w, box_h, "F")
    pdf.set_xy(x_start + 3, y_start + 3)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(box_w - 6, 4, "TOTAL RECEITAS")
    pdf.set_xy(x_start + 3, y_start + 10)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(22, 163, 74)
    pdf.cell(box_w - 6, 8, f"{total_receitas:,.0f} CVE".replace(",", "."))

    # Despesas box
    pdf.set_fill_color(254, 242, 242)
    pdf.rect(x_start + box_w + 3, y_start, box_w, box_h, "F")
    pdf.set_xy(x_start + box_w + 6, y_start + 3)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(box_w - 6, 4, "TOTAL DESPESAS")
    pdf.set_xy(x_start + box_w + 6, y_start + 10)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(220, 38, 38)
    pdf.cell(box_w - 6, 8, f"{total_despesas:,.0f} CVE".replace(",", "."))

    # Resultado box
    is_positive = resultado >= 0
    pdf.set_fill_color(243, 244, 246)
    pdf.rect(x_start + 2 * (box_w + 3), y_start, box_w, box_h, "F")
    pdf.set_xy(x_start + 2 * (box_w + 3) + 3, y_start + 3)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(box_w - 6, 4, "RESULTADO LIQUIDO")
    pdf.set_xy(x_start + 2 * (box_w + 3) + 3, y_start + 10)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(58, 58, 58) if is_positive else pdf.set_text_color(234, 88, 12)
    pdf.cell(box_w - 6, 8, f"{resultado:,.0f} CVE".replace(",", "."))

    pdf.set_y(y_start + box_h + 10)

    # --- Monthly Table ---
    pdf.set_text_color(58, 58, 58)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Evolucao Mensal", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    col_w = [45, 45, 45, 45]
    # Table header
    pdf.set_fill_color(199, 32, 47)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    headers = ["Mes", "Receitas (CVE)", "Despesas (CVE)", "Saldo (CVE)"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 8, h, border=0, fill=True, align="C")
    pdf.ln()

    pdf.set_text_color(58, 58, 58)
    pdf.set_font("Helvetica", "", 9)
    for m in range(1, 13):
        d = monthly[m]
        saldo = d["receitas"] - d["despesas"]
        bg = m % 2 == 0
        if bg:
            pdf.set_fill_color(249, 250, 251)
        pdf.cell(col_w[0], 7, MONTH_NAMES[m - 1], border=0, fill=bg, align="C")
        pdf.cell(col_w[1], 7, f"{d['receitas']:,.0f}".replace(",", "."), border=0, fill=bg, align="R")
        pdf.cell(col_w[2], 7, f"{d['despesas']:,.0f}".replace(",", "."), border=0, fill=bg, align="R")

        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(col_w[3], 7, f"{saldo:,.0f}".replace(",", "."), border=0, fill=bg, align="R")
        pdf.set_font("Helvetica", "", 9)
        pdf.ln()

    # Totals row
    pdf.set_fill_color(58, 58, 58)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(col_w[0], 8, "TOTAL", border=0, fill=True, align="C")
    pdf.cell(col_w[1], 8, f"{total_receitas:,.0f}".replace(",", "."), border=0, fill=True, align="R")
    pdf.cell(col_w[2], 8, f"{total_despesas:,.0f}".replace(",", "."), border=0, fill=True, align="R")
    pdf.cell(col_w[3], 8, f"{resultado:,.0f}".replace(",", "."), border=0, fill=True, align="R")
    pdf.ln(12)

    # --- Category Breakdown ---
    pdf.set_text_color(58, 58, 58)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Detalhamento por Categoria", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    half_w = 88

    # Income categories
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(22, 163, 74)
    pdf.cell(half_w, 7, "(+) Receitas", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(58, 58, 58)
    if receitas_cat:
        for cat, val in sorted(receitas_cat.items(), key=lambda x: -x[1]):
            label = CATEGORY_LABELS.get(cat, cat)
            pct = (val / total_receitas * 100) if total_receitas > 0 else 0
            pdf.cell(half_w - 30, 6, f"    {label}", border=0)
            pdf.cell(30, 6, f"{val:,.0f} ({pct:.0f}%)".replace(",", "."), border=0, align="R")
            pdf.ln()
    else:
        pdf.cell(half_w, 6, "    Sem receitas registradas")
        pdf.ln()

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(22, 163, 74)
    pdf.cell(half_w, 6, f"    Total Receitas: {total_receitas:,.0f} CVE".replace(",", "."))
    pdf.ln(8)

    # Expense categories
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(220, 38, 38)
    pdf.cell(half_w, 7, "(-) Despesas", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(58, 58, 58)
    if despesas_cat:
        for cat, val in sorted(despesas_cat.items(), key=lambda x: -x[1]):
            label = CATEGORY_LABELS.get(cat, cat)
            pct = (val / total_despesas * 100) if total_despesas > 0 else 0
            pdf.cell(half_w - 30, 6, f"    {label}", border=0)
            pdf.cell(30, 6, f"{val:,.0f} ({pct:.0f}%)".replace(",", "."), border=0, align="R")
            pdf.ln()
    else:
        pdf.cell(half_w, 6, "    Sem despesas registradas")
        pdf.ln()

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(220, 38, 38)
    pdf.cell(half_w, 6, f"    Total Despesas: {total_despesas:,.0f} CVE".replace(",", "."))
    pdf.ln(10)

    # Final result
    pdf.set_draw_color(199, 32, 47)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(58, 58, 58)
    label = "RESULTADO LIQUIDO DO EXERCICIO"
    pdf.cell(120, 10, label)
    color = (22, 163, 74) if resultado >= 0 else (234, 88, 12)
    pdf.set_text_color(*color)
    pdf.cell(60, 10, f"{resultado:,.0f} CVE".replace(",", "."), align="R")
    pdf.ln(14)

    # Footer
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(160, 160, 160)
    pdf.cell(
        0,
        5,
        "Associacao dos Controladores de Trafego Aereo de Cabo Verde (ACCTA)",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.cell(0, 5, "Documento gerado automaticamente pelo Portal ACCTA. Nao requer assinatura.", align="C")

    # Output
    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)

    filename = f"DRE_ACCTA_{year}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ===== META ENDPOINTS =====


@router.get("/meta/categories")
async def get_finance_categories(current_user: User = Depends(get_current_user)):
    return {
        "income": INCOME_CATEGORIES,
        "expense": EXPENSE_CATEGORIES,
        "types": TRANSACTION_TYPES,
    }
