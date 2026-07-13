"""Dashboard universal (spec 020).

Endpoint `GET /api/dashboard/overview` agregador — universal para qualquer
utilizador autenticado. Devolve apenas dados **agregados**; a tripwire
`test_overview_no_pii` garante que nunca aparecem `email`/`name`/`member_id`
ou outros identificadores pessoais no payload.

Reutiliza as funções `compute_financial_summary` e `compute_dre_report` de
`routes/finances.py` — os endpoints antigos (`/finances/summary`, `/dre`,
`/stats`) continuam gated pelos seus checks originais e não são alterados.
"""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from auth import get_current_user
from database import db
from models import (
    AssembleiasOverview,
    AtosOverview,
    DashboardOverview,
    FinanceOverview,
    MonthlyPoint,
    ProximaAssembleia,
    SociosOverview,
    UltimaVotacao,
    User,
    VotacoesOverview,
)
from routes.finances import compute_dre_report, compute_financial_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# Membro real (não técnica) — mesmo filtro canónico de routes/stats.py, users.py,
# ranking.py, assembleias.py. Contas técnicas não entram nas contagens do painel.
_MEMBER_FILTER = {"$or": [{"account_type": "member"}, {"account_type": {"$exists": False}}]}

# Categorias que podem votar (governance.VOTING_CATEGORIES). Duplicado aqui como
# filtro Mongo — o helper `is_voting_member` é por-documento, mas o Dashboard
# precisa de um count. A margem de erro é apenas nos "direitos suspensos" (raro,
# temporário) — aceitável num KPI de exibição.
_VOTING_CATEGORIES = ["fundador", "ordinario"]


@router.get("/overview", response_model=DashboardOverview)
async def get_overview(current_user: User = Depends(get_current_user)) -> DashboardOverview:
    now = datetime.now(timezone.utc)
    year = now.year

    # ----- FINANCE (US1) -----
    # Resumo total (saldo actual) — janela aberta, todas as transacções.
    total_summary = await compute_financial_summary()
    saldo_atual = total_summary["resultado_liquido"]

    # DRE do ano em curso (monthly + categorias + totais)
    dre = await compute_dre_report(year)

    monthly: list[MonthlyPoint] = [
        MonthlyPoint(month=m, receitas=v["receitas"], despesas=v["despesas"]) for m, v in sorted(dre["monthly"].items())
    ]

    # Mês corrente e mês anterior — cada um em janela isolada
    month_curr = now.month
    year_prev, month_prev = (year - 1, 12) if month_curr == 1 else (year, month_curr - 1)
    curr = await compute_financial_summary(year=year, month=month_curr)
    prev = await compute_financial_summary(year=year_prev, month=month_prev)

    # Quotas do mês em curso — mesma janela do mês corrente, filtrada por categoria.
    start_mes = f"{year}-{month_curr:02d}-01T00:00:00"
    end_mes = f"{year + 1}-01-01T00:00:00" if month_curr == 12 else f"{year}-{month_curr + 1:02d}-01T00:00:00"
    quotas_mes_rows = await db.transactions.find(
        {"date": {"$gte": start_mes, "$lt": end_mes}, "type": "receita", "category": "quota"},
        {"_id": 0, "amount": 1},
    ).to_list(None)
    quotas_mes = sum((r.get("amount") or 0) for r in quotas_mes_rows)

    finance = FinanceOverview(
        saldo_atual=saldo_atual,
        receitas_ano=dre["total_receitas"],
        despesas_ano=dre["total_despesas"],
        resultado_ano=dre["resultado_liquido"],
        quotas_mes=quotas_mes,
        monthly=monthly,
        despesas_por_categoria=dre["despesas_por_categoria"],
        mes_atual={"receitas": curr["total_receitas"], "despesas": curr["total_despesas"]},
        mes_anterior={"receitas": prev["total_receitas"], "despesas": prev["total_despesas"]},
    )

    # ----- SÓCIOS (US3 — A.1, A.2) -----
    ativos = await db.users.count_documents({"$and": [{"status": "ativo"}, _MEMBER_FILTER]})
    since_90d = (now - timedelta(days=90)).isoformat()
    novos_90d = await db.users.count_documents({"$and": [{"created_at": {"$gte": since_90d}}, _MEMBER_FILTER]})
    socios = SociosOverview(ativos=ativos, novos_90d=novos_90d)

    # ----- ATOS (US3 — A.5) -----
    pendentes = await db.atos.count_documents({"status": "pendente"})
    atos = AtosOverview(pendentes=pendentes)

    # ----- VOTAÇÕES (US3 — A.7) -----
    abertas = await db.polls.count_documents({"status": "aberta"})
    # Última fechada: sort por end_date desc (Poll não tem closed_at).
    last_closed = (
        await db.polls.find({"status": "fechada"}, {"_id": 0, "id": 1, "title": 1, "end_date": 1})
        .sort("end_date", -1)
        .limit(1)
        .to_list(1)
    )
    ultima_fechada = None
    if last_closed:
        poll = last_closed[0]
        votos = await db.user_votes.count_documents({"poll_id": poll["id"]})
        eligible = await db.users.count_documents(
            {
                "$and": [
                    {"status": "ativo"},
                    {"member_category": {"$in": _VOTING_CATEGORIES}},
                    _MEMBER_FILTER,
                ]
            }
        )
        pct = round((votos / eligible) * 100) if eligible else 0
        ultima_fechada = UltimaVotacao(
            id=poll["id"],
            titulo=poll["title"],
            participacao_pct=pct,
            fechada_em=poll.get("end_date", ""),
        )
    votacoes = VotacoesOverview(abertas=abertas, ultima_fechada=ultima_fechada)

    # ----- ASSEMBLEIAS (US3 — A.3) -----
    hoje = date.today().isoformat()
    proximas_rows = (
        await db.assembleias.find(
            {
                "status": {"$in": ["convocada", "em_curso"]},
                "data": {"$gte": hoje},
            },
            {"_id": 0, "id": 1, "titulo": 1, "data": 1, "tipo": 1},
        )
        .sort("data", 1)
        .limit(3)
        .to_list(3)
    )
    assembleias = AssembleiasOverview(
        proximas=[
            ProximaAssembleia(id=r["id"], titulo=r["titulo"], data=r["data"], tipo=r["tipo"]) for r in proximas_rows
        ]
    )

    return DashboardOverview(
        finance=finance,
        socios=socios,
        atos=atos,
        votacoes=votacoes,
        assembleias=assembleias,
    )
