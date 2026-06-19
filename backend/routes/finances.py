from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from datetime import date, datetime, timezone
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
    INCOME_CATEGORY_LABELS,
    EXPENSE_CATEGORY_LABELS,
    MFA_SECRET_FIELDS,
)
from finance_joia import joia_status
from database import db, insert_quotas_atomic
from auth import get_current_user, can_view_finances, can_manage_finances
from helpers import create_audit_log, notify_admins, notify_all_active_users
from fpdf import FPDF
import io
import uuid

# Maiorias qualificadas de 3/4 que legitimam a fixação de quota/jóia (spec §14).
_QUOTA_MAJORIAS = ("qualificada_3_4_presentes", "qualificada_3_4_universo")


def _safe_search_regex(s: str) -> str:
    """Escape regex metachars + cap length to prevent ReDoS.
    Trunca o input bruto antes do escape — escapar primeiro e cortar depois
    podia partir uma sequencia '\\X' a meio e produzir regex invalida.
    """
    return re.escape(s.strip()[:100])


router = APIRouter(prefix="/finances", tags=["finances"])


def require_view_finances(user: User):
    """Leitura do módulo financeiro (GET). Aceita admin/financeiro,
    view_finances_readonly (Conselho Fiscal) ou manage_finances."""
    if not can_view_finances(user):
        raise HTTPException(status_code=403, detail="Sem permissao para ver financas")


def require_manage_finances(user: User):
    """Escrita no módulo financeiro (POST/PATCH/DELETE/quotas). view_finances_readonly
    NÃO basta — só admin/financeiro ou manage_finances."""
    if not can_manage_finances(user):
        raise HTTPException(status_code=403, detail="Sem permissao para gerir financas")


async def _coaprovacao_limiar() -> float:
    """Limiar de co-aprovação em vigor (spec-controlos §4.1). 0.0 (default) = gate
    desligado: o lançamento directo de despesas mantém-se. Acima de um limiar
    positivo, despesas exigem um Ato de pagamento aprovado (via /atos/executar).
    Leitura defensiva — tolera ausência de settings / mock_db (find_one→None)."""
    s = await db.finance_settings.find_one({"id": "finance_settings"}, {"_id": 0})
    if not isinstance(s, dict):
        return 0.0
    try:
        return float(s.get("coaprovacao_limiar") or 0.0)
    except (TypeError, ValueError):
        return 0.0


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
    require_view_finances(current_user)
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
    return {"items": transactions, "total": total, "skip": skip, "limit": limit}


@router.get("/transactions/count")
async def count_transactions(
    type: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    require_view_finances(current_user)
    query = {}
    if type:
        query["type"] = type
    if category:
        query["category"] = category
    count = await db.transactions.count_documents(query)
    return {"count": count}


@router.get("/me/quotas")
async def list_my_quotas(current_user: User = Depends(get_current_user)):
    """Vista self-service do sócio sobre os SEUS lançamentos de quota/jóia.

    NÃO exige view_finances: qualquer utilizador autenticado vê apenas os seus
    (filtro fixo por user_id). As quotas reais vivem em `transactions` (lançadas
    via geração mensal/folha); não há estado pendente/pago — todos os lançamentos
    listados são efetivos. Substitui o antigo módulo `invoices`.
    """
    query = {
        "user_id": current_user.id,
        "type": "receita",
        "category": {"$in": ["quotas", "joias"]},
    }
    items = await db.transactions.find(query, {"_id": 0}).sort("date", -1).to_list(None)

    def _amount(t: dict) -> float:
        # Coerção defensiva: tolera amount ausente/None/string mal-formada em
        # docs legados sem rebentar o endpoint (não há validação na leitura).
        try:
            return float(t.get("amount") or 0)
        except (TypeError, ValueError):
            return 0.0

    total_pago = sum(_amount(t) for t in items)
    return {"items": items, "total_pago": total_pago}


@router.post("/transactions")
async def create_transaction(
    data: TransactionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    require_manage_finances(current_user)

    if data.type not in TRANSACTION_TYPES:
        raise HTTPException(status_code=400, detail=f"Tipo invalido. Use: {TRANSACTION_TYPES}")

    valid_cats = INCOME_CATEGORIES if data.type == "receita" else EXPENSE_CATEGORIES
    if data.category not in valid_cats:
        raise HTTPException(status_code=400, detail=f"Categoria invalida para {data.type}. Use: {valid_cats}")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="O valor deve ser positivo")

    # Gate de co-aprovação (Art. 54): despesas acima do limiar só entram via um
    # Ato de pagamento aprovado e executado (que cria a despesa com `ato_id`),
    # não pelo lançamento directo. Limiar 0 = desligado (não-quebra).
    if data.type == "despesa":
        limiar = await _coaprovacao_limiar()
        if limiar > 0 and data.amount > limiar:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Despesa de {data.amount:,.0f} CVE excede o limiar de co-aprovacao "
                    f"({limiar:,.0f} CVE). Crie um Acto de pagamento e execute-o apos aprovacao."
                ),
            )

    transaction = Transaction(**data.model_dump(), created_by=current_user.id)
    t_dict = transaction.model_dump()

    await db.transactions.insert_one(t_dict)
    await create_audit_log(
        current_user.id,
        f"Criou transacao {transaction.id} ({data.type}: {data.amount} CVE)",
        transaction.id,
        request=request,
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
    request: Request,
    current_user: User = Depends(get_current_user),
):
    require_manage_finances(current_user)

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

    # Gate de co-aprovação (Art. 54) — espelha create_transaction. Sem isto,
    # lançava-se uma despesa abaixo do limiar e inflava-se por PATCH, contornando
    # a dupla assinatura. Só barra quando o valor/tipo muda (edições de metadados
    # ficam livres) e isenta despesas já co-aprovadas por um Acto (ato_id).
    if ("amount" in updates or "type" in updates) and not existing.get("ato_id"):
        eff_type = updates.get("type", existing["type"])
        eff_amount = updates.get("amount", existing.get("amount") or 0)
        if eff_type == "despesa":
            limiar = await _coaprovacao_limiar()
            if limiar > 0 and eff_amount > limiar:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Despesa de {eff_amount:,.0f} CVE excede o limiar de co-aprovacao "
                        f"({limiar:,.0f} CVE). Crie um Acto de pagamento e execute-o apos aprovacao."
                    ),
                )

    if updates:
        await db.transactions.update_one({"id": transaction_id}, {"$set": updates})
        await create_audit_log(
            current_user.id, f"Atualizou transacao {transaction_id}", transaction_id, request=request
        )

    updated = await db.transactions.find_one({"id": transaction_id}, {"_id": 0})
    return updated


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    require_manage_finances(current_user)

    existing = await db.transactions.find_one({"id": transaction_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Transacao nao encontrada")

    await db.transactions.delete_one({"id": transaction_id})
    await create_audit_log(current_user.id, f"Removeu transacao {transaction_id}", transaction_id, request=request)
    return {"message": "Transacao removida"}


# ===== SUMMARY & DRE ENDPOINTS =====


async def compute_financial_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
    date_gte: Optional[str] = None,
    date_lt: Optional[str] = None,
) -> dict:
    """Computa o resumo financeiro (totais + por categoria) para uma janela.

    Fonte única reutilizada pelo endpoint `/finances/summary` e pelo snapshot
    dos balancetes (spec-ciclo §5 — "reusar os números existentes, não
    recalcular noutro sítio"). Janela: `date_gte`/`date_lt` (range explícito,
    p/ trimestres) tem precedência; senão `year` (+ `month`); senão tudo.
    """
    query = {}
    if date_gte or date_lt:
        rng = {}
        if date_gte:
            rng["$gte"] = date_gte
        if date_lt:
            rng["$lt"] = date_lt
        query["date"] = rng
    elif year:
        # Limite superior sempre exclusivo (início do período seguinte): datas
        # são guardadas com offset/microssegundos (ex. ...T23:59:59+00:00), que
        # ordenam lexicamente acima de "...T23:59:59" — um `$lte` no fim do ano
        # deixava cair transações do último segundo do exercício.
        start = f"{year}-01-01T00:00:00"
        end = f"{year + 1}-01-01T00:00:00"
        if month:
            start = f"{year}-{month:02d}-01T00:00:00"
            if month == 12:
                end = f"{year + 1}-01-01T00:00:00"
            else:
                end = f"{year}-{month + 1:02d}-01T00:00:00"
        query["date"] = {"$gte": start, "$lt": end}

    # Sem teto: um cap de 5000 truncava silenciosamente os totais acima de 5000
    # transações na janela (paridade com as restantes agregações, que usam
    # to_list(None)).
    transactions = await db.transactions.find(
        query, {"_id": 0, "type": 1, "amount": 1, "category": 1, "description": 1, "date": 1}
    ).to_list(None)

    # .get() defensivo: documentos legados/migrados podem não ter todos os
    # campos — antes um KeyError virava 500.
    total_receitas = sum((t.get("amount") or 0) for t in transactions if t.get("type") == "receita")
    total_despesas = sum((t.get("amount") or 0) for t in transactions if t.get("type") == "despesa")

    receitas_por_cat = {}
    despesas_por_cat = {}
    for t in transactions:
        cat = t.get("category") or "Sem categoria"
        amount = t.get("amount") or 0
        if t.get("type") == "receita":
            receitas_por_cat[cat] = receitas_por_cat.get(cat, 0) + amount
        else:
            despesas_por_cat[cat] = despesas_por_cat.get(cat, 0) + amount

    return {
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "resultado_liquido": total_receitas - total_despesas,
        "receitas_por_categoria": receitas_por_cat,
        "despesas_por_categoria": despesas_por_cat,
        "total_transacoes": len(transactions),
    }


@router.get("/summary")
async def get_financial_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    require_view_finances(current_user)
    return await compute_financial_summary(year=year, month=month)


async def compute_dre_report(year: int) -> dict:
    """Computa o DRE anual (mensal + por categoria). Fonte única reutilizada pelo
    endpoint `/finances/dre` e pelo `dre_snapshot` congelado no Relatório e Contas
    (spec-ciclo §4.1) — os números não mudam depois da submissão."""
    # Meia-aberto [start, end) — ver compute_financial_summary: um end fechado
    # "{ano}-12-31T23:59:59" perdia timestamps com fracção de segundo.
    start = f"{year}-01-01T00:00:00"
    end = f"{year + 1}-01-01T00:00:00"  # exclusivo: ver nota em compute_financial_summary
    # Sem limite: alinhado com compute_financial_summary (to_list(None)). Um teto
    # (antes 5000) truncava o DRE em silêncio e divergia do resumo à escala.
    transactions = await db.transactions.find(
        {"date": {"$gte": start, "$lt": end}}, {"_id": 0, "date": 1, "type": 1, "amount": 1, "category": 1}
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

        cat = t.get("category") or "Sem categoria"
        amount = t.get("amount") or 0
        if t.get("type") == "receita":
            monthly[month]["receitas"] += amount
            receitas_cat[cat] = receitas_cat.get(cat, 0) + amount
        else:
            monthly[month]["despesas"] += amount
            despesas_cat[cat] = despesas_cat.get(cat, 0) + amount

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


@router.get("/dre")
async def get_dre_report(
    year: int = Query(..., description="Ano do relatorio"),
    current_user: User = Depends(get_current_user),
):
    require_view_finances(current_user)
    return await compute_dre_report(year)


# ===== SETTINGS ENDPOINTS =====


@router.get("/settings")
async def get_finance_settings(
    current_user: User = Depends(get_current_user),
):
    require_view_finances(current_user)
    settings = await db.finance_settings.find_one({"id": "finance_settings"}, {"_id": 0})
    if not settings:
        default = FinanceSettings()
        d = default.model_dump()
        await db.finance_settings.insert_one(d)
        return default
    return FinanceSettings(**settings)


@router.patch("/settings")
async def update_finance_settings(
    data: FinanceSettingsUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar configuracoes")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhuma alteracao fornecida")

    if "quota_amount" in updates and updates["quota_amount"] <= 0:
        raise HTTPException(status_code=400, detail="O valor da quota deve ser positivo")

    # Inputs de governança (não são colunas de settings directas).
    assembleia_id = updates.pop("assembleia_id", None)
    deliberacao_id = updates.pop("deliberacao_id", None)
    effective_from = updates.pop("effective_from", None)

    # Alterações monetárias (quota/jóia) exigem deliberação de AG por 3/4 e
    # registam a versão anterior em finance_settings_history (spec §14).
    monetary = {k for k in ("quota_amount", "joia_multiplier", "joia_amount") if k in updates}

    existing = await db.finance_settings.find_one({"id": "finance_settings"})
    now_iso = datetime.now(timezone.utc).isoformat()

    if monetary:
        if not (assembleia_id and deliberacao_id):
            raise HTTPException(
                status_code=400,
                detail="Alterar quota/jóia exige referência a deliberação de AG (maioria 3/4)",
            )
        delib = await db.assembleia_deliberacoes.find_one(
            {"id": deliberacao_id, "assembleia_id": assembleia_id},
            {"_id": 0, "aprovado": 1, "tipo_maioria": 1},
        )
        if not delib:
            raise HTTPException(status_code=404, detail="Deliberação da AG não encontrada")
        if not delib.get("aprovado"):
            raise HTTPException(status_code=400, detail="A deliberação não foi aprovada")
        if delib.get("tipo_maioria") not in _QUOTA_MAJORIAS:
            raise HTTPException(status_code=400, detail="A fixação de quota/jóia exige deliberação por maioria de 3/4")
        # Snapshot da versão anterior.
        if existing:
            snapshot = {
                k: existing.get(k)
                for k in (
                    "quota_amount",
                    "quota_description",
                    "joia_multiplier",
                    "joia_amount",
                    "quota_fixed_by_assembleia_id",
                    "quota_fixed_by_deliberacao_id",
                    "effective_from",
                )
            }
            snapshot.update(
                {
                    "id": str(uuid.uuid4()),
                    "replaced_at": now_iso,
                    "replaced_by": current_user.id,
                    "assembleia_id": assembleia_id,
                    "deliberacao_id": deliberacao_id,
                }
            )
            await db.finance_settings_history.insert_one(snapshot)
        updates["quota_fixed_by_assembleia_id"] = assembleia_id
        updates["quota_fixed_by_deliberacao_id"] = deliberacao_id
        updates["effective_from"] = effective_from or now_iso
        # Resolve a jóia: explícita, ou multiplicador * quota.
        if "joia_amount" not in updates:
            new_quota = updates.get("quota_amount", (existing or {}).get("quota_amount", 2000.0))
            new_mult = updates.get("joia_multiplier", (existing or {}).get("joia_multiplier", 2.0))
            updates["joia_amount"] = new_mult * new_quota

    updates["updated_at"] = now_iso
    updates["updated_by"] = current_user.id

    if not existing:
        default = FinanceSettings()
        d = default.model_dump()
        d.update(updates)
        await db.finance_settings.insert_one(d)
    else:
        await db.finance_settings.update_one({"id": "finance_settings"}, {"$set": updates})

    await create_audit_log(
        current_user.id, f"Atualizou configuracoes financeiras: {updates}", request=request
    )

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


@router.get("/settings/history")
async def get_finance_settings_history(current_user: User = Depends(get_current_user)):
    """Histórico de alterações de quota/jóia (cada uma ligada a uma deliberação
    de AG). Leitura do módulo financeiro (inclui Conselho Fiscal)."""
    require_view_finances(current_user)
    rows = await db.finance_settings_history.find({}, {"_id": 0}).sort("replaced_at", -1).to_list(200)
    return {"history": rows}


# ===== GENERATE QUOTAS =====


@router.post("/generate-quotas")
async def generate_monthly_quotas(
    request: Request,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(...),
    current_user: User = Depends(get_current_user),
):
    require_manage_finances(current_user)

    # Get settings for quota amount
    settings = await db.finance_settings.find_one({"id": "finance_settings"}, {"_id": 0})
    quota_amount = settings.get("quota_amount", 2000.0) if settings else 2000.0
    quota_desc = settings.get("quota_description", "Quota Mensal") if settings else "Quota Mensal"

    # Get all active members. Legacy member documents may not have account_type.
    # Sem teto (antes 1000): acima do limite, sócios excedentes ficavam sem quota
    # gerada em silêncio. A dedup/inserção por mês é atómica em insert_quotas_atomic.
    active_users = await db.users.find(
        {"status": "ativo", "$or": [{"account_type": "member"}, {"account_type": {"$exists": False}}]},
        {"_id": 0, "id": 1, "name": 1},
    ).to_list(None)

    # Constrói um candidato por sócio activo. A deduplicação por mês (saltar
    # quem já tem quota) e a inserção acontecem ATOMICAMENTE em
    # insert_quotas_atomic, sob advisory lock por (ano, mês): serializa
    # execuções concorrentes do gerador e fecha a race check-then-insert (dois
    # admins a gerar o mesmo mês em simultâneo já não duplicam).
    candidate_docs = [
        Transaction(
            type="receita",
            category="quotas",
            description=f"{quota_desc} - {month:02d}/{year} - {user.get('name', 'Socio')}",
            amount=quota_amount,
            date=datetime(year, month, 15, tzinfo=timezone.utc).isoformat(),
            reference=f"FOLHA-{year}{month:02d}",
            user_id=user["id"],
            created_by=current_user.id,
        ).model_dump()
        for user in active_users
    ]
    created_count = await insert_quotas_atomic(year, month, candidate_docs)

    await create_audit_log(
        current_user.id,
        f"Gerou {created_count} quotas para {month:02d}/{year} ({quota_amount} CVE cada)",
        request=request,
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
        "skipped": len(active_users) - created_count,
        "total_value": created_count * quota_amount,
    }


# Labels ASCII-safe para CSV/DRE-PDF (FPDF/latin-1 rebenta com acentos). As
# receitas estatutárias (Art. 5) + as legadas (mantidas até a migração correr,
# para docs ainda não migrados renderizarem com nome em vez da key crua).
CATEGORY_LABELS = {
    # Receitas estatutárias (Art. 5).
    "quotas": "Quotas de Socios",
    "joias": "Joias",
    "subvencoes": "Subvencoes",
    "donativos": "Donativos",
    "venda_publicacoes": "Venda de Publicacoes",
    "juros": "Juros",
    "extraordinarias": "Receitas Extraordinarias",
    # Legadas (até migrate_income_categories.py --apply correr).
    "patrocinios": "Patrocinios",
    "doacoes": "Doacoes",
    "outros_receita": "Outras Receitas",
    # Despesas ("eventos" continua válida como despesa).
    "eventos": "Eventos",
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
    require_view_finances(current_user)

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

    # Sem limite: alinhado com o resumo/DRE. Um teto (antes 5000) truncava o
    # export em silêncio, omitindo lançamentos sem qualquer aviso.
    transactions = await db.transactions.find(query, {"_id": 0}).sort("date", -1).to_list(None)

    import csv

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Data", "Tipo", "Categoria", "Descricao", "Valor (CVE)", "Referencia"])
    for t in transactions:
        date_str = t.get("date", "")[:10] if t.get("date") else ""
        writer.writerow(
            [
                date_str,
                "Receita" if t.get("type") == "receita" else "Despesa",
                CATEGORY_LABELS_CSV.get(t.get("category", ""), t.get("category", "")),
                t.get("description", ""),
                f"{(t.get('amount') or 0):.2f}",
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
    require_view_finances(current_user)

    # Reutiliza a fonte única do DRE (mesma janela/limite que /finances/dre) em
    # vez de recalcular — antes divergia (limite 10000 vs 5000, range $lte vs
    # $lt) e um bug corrigido aqui não chegava ao endpoint JSON.
    dre = await compute_dre_report(year)
    monthly = dre["monthly"]
    receitas_cat = dre["receitas_por_categoria"]
    despesas_cat = dre["despesas_por_categoria"]
    total_receitas = dre["total_receitas"]
    total_despesas = dre["total_despesas"]
    resultado = dre["resultado_liquido"]

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
    require_view_finances(current_user)
    return {
        "income": INCOME_CATEGORIES,
        "expense": EXPENSE_CATEGORIES,
        "types": TRANSACTION_TYPES,
        "labels": {**INCOME_CATEGORY_LABELS, **EXPENSE_CATEGORY_LABELS},
    }


@router.get("/joia/preview")
async def preview_joia(
    user_id: str,
    cta_qualified_since: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Pré-visualiza a jóia (Art. 6) de um membro/candidato SEM gravar — para o
    modal de aprovação. `cta_qualified_since` (opcional) sobrepõe o valor do doc,
    para o admin ver o efeito da data que vai introduzir."""
    require_view_finances(current_user)
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0, **dict.fromkeys(MFA_SECRET_FIELDS, 0)})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador nao encontrado")
    if cta_qualified_since is not None:
        # Valida o override: data ISO-8601 e não-futura. Sem isto, uma data
        # futura produzia uma qualificação/jóia enganosa no modal de aprovação.
        # joia_status interpreta a qualificação como `date` (AAAA-MM-DD).
        try:
            since_date = date.fromisoformat(cta_qualified_since.strip()[:10])
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="cta_qualified_since deve ser uma data ISO-8601 valida")
        if since_date > datetime.now(timezone.utc).date():
            raise HTTPException(status_code=422, detail="cta_qualified_since nao pode ser uma data futura")
        user = {**user, "cta_qualified_since": cta_qualified_since}
    settings = await db.finance_settings.find_one({"id": "finance_settings"}, {"_id": 0})
    if not isinstance(settings, dict):
        settings = FinanceSettings().model_dump()
    return joia_status(user, settings)
