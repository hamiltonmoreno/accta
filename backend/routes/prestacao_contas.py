"""Ciclo anual de prestação de contas (spec-ciclo §4–5; Art. 19.1/31.k/34/37).

F2 — Balancetes: o Tesoureiro publica balancetes periódicos / balanço anual,
**congelando** o snapshot de `/finances/summary` no momento (auditabilidade — os
números não mudam depois); o Conselho Fiscal audita ao nível do período
(`cf_audit`: conferido + observações, decisão §12.3).

F3 — Exercícios (ciclo guiado: relatório/orçamento/plano + parecer CF +
aprovação da AG) é acrescentado neste mesmo módulo.

RBAC:
- publicar balancete: `manage_finances` (inclui o Tesoureiro — role `financeiro`)
- auditar balancete:  Conselho Fiscal (`can_emit_parecer_cf`) — NÃO escreve transacções
- ver balancetes:     `can_view_finances`; o PDF público segue o fluxo de documentos
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from auth import can_manage_finances, can_view_finances, get_current_user
from database import db
from helpers import create_audit_log, members_of_orgao, notify_users
from models import Balancete, BalanceteAuditar, BalanceteCreate, User
from permissions import can_emit_parecer_cf
from routes.finances import compute_financial_summary

router = APIRouter(tags=["prestacao-contas"])

_LINK_BAL = "/financeiro/balancetes"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_manage_finances(user: User):
    if not can_manage_finances(user):
        raise HTTPException(status_code=403, detail="Sem permissao para publicar balancetes")


def _require_view_finances(user: User):
    if not can_view_finances(user):
        raise HTTPException(status_code=403, detail="Sem permissao para ver balancetes")


def _require_cf(user: User):
    if not can_emit_parecer_cf(user):
        raise HTTPException(status_code=403, detail="Apenas o Conselho Fiscal pode auditar")


async def _validate_document(document_id: str):
    doc = await db.documents.find_one({"id": document_id}, {"_id": 0, "id": 1})
    if not doc:
        raise HTTPException(status_code=400, detail="Documento associado nao encontrado")


# --------------------------------------------------------------------------- #
# Balancetes (F2 — Art. 34, 37)
# --------------------------------------------------------------------------- #


@router.post("/balancetes")
async def publish_balancete(data: BalanceteCreate, current_user: User = Depends(get_current_user)):
    _require_manage_finances(current_user)
    if data.document_id:
        await _validate_document(data.document_id)

    # Congela o snapshot no momento da publicação (não recalcular depois).
    if data.date_inicio or data.date_fim:
        snapshot = await compute_financial_summary(date_gte=data.date_inicio, date_lt=data.date_fim)
    elif data.month:
        snapshot = await compute_financial_summary(year=data.exercicio_ano, month=data.month)
    else:
        snapshot = await compute_financial_summary(year=data.exercicio_ano)

    bal = Balancete(
        tipo=data.tipo,
        periodo=data.periodo,
        exercicio_ano=data.exercicio_ano,
        snapshot=snapshot,
        document_id=data.document_id,
        visibility=data.visibility,
        published=True,
        published_by=current_user.id,
        published_at=_now(),
    )
    await db.balancetes.insert_one(bal.model_dump())
    await create_audit_log(
        current_user.id,
        f"Publicou balancete {data.periodo}",
        bal.id,
        details={"tipo": data.tipo, "periodo": data.periodo, "exercicio_ano": data.exercicio_ano},
    )
    cf_ids = await members_of_orgao("conselho_fiscal")
    await notify_users(
        cf_ids,
        "finance",
        "Balancete publicado",
        f"Foi publicado o balancete {data.periodo} para auditoria do Conselho Fiscal.",
        _LINK_BAL,
        exclude_id=current_user.id,
    )
    return bal


@router.get("/balancetes")
async def list_balancetes(
    exercicio_ano: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    _require_view_finances(current_user)
    query = {}
    if exercicio_ano:
        query["exercicio_ano"] = exercicio_ano
    items = await db.balancetes.find(query, {"_id": 0}).sort("created_at", -1).to_list(None)
    return {"items": items, "total": len(items)}


@router.get("/balancetes/{balancete_id}")
async def get_balancete(balancete_id: str, current_user: User = Depends(get_current_user)):
    _require_view_finances(current_user)
    bal = await db.balancetes.find_one({"id": balancete_id}, {"_id": 0})
    if not bal:
        raise HTTPException(status_code=404, detail="Balancete nao encontrado")
    return bal


@router.post("/balancetes/{balancete_id}/auditar")
async def auditar_balancete(
    balancete_id: str, data: BalanceteAuditar, current_user: User = Depends(get_current_user)
):
    _require_cf(current_user)
    bal = await db.balancetes.find_one({"id": balancete_id}, {"_id": 0})
    if not bal:
        raise HTTPException(status_code=404, detail="Balancete nao encontrado")

    cf_audit = {
        "audited_by": current_user.id,
        "audited_at": _now(),
        "conferido": data.conferido,
        "observacoes": (data.observacoes.strip() if data.observacoes else None),
    }
    await db.balancetes.update_one({"id": balancete_id}, {"$set": {"cf_audit": cf_audit}})
    await create_audit_log(
        current_user.id,
        f"Auditou balancete {bal.get('periodo')} "
        f"({'conferido' if data.conferido else 'com observacoes'})",
        balancete_id,
        details={"conferido": data.conferido},
    )
    publisher = bal.get("published_by")
    if publisher:
        await notify_users(
            [publisher],
            "finance",
            "Balancete auditado",
            f"O Conselho Fiscal auditou o balancete {bal.get('periodo')}.",
            _LINK_BAL,
            exclude_id=current_user.id,
        )
    return {"id": balancete_id, "cf_audit": cf_audit}
