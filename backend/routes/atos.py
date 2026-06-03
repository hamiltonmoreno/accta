"""Co-aprovação / dupla assinatura de actos que vinculam a ACCTA (Art. 54;
spec-controlos-financeiros §4.1).

Um acto nasce `pendente` com os `requisitos` congelados pelo tipo. Cada membro
da Direcção assina (aprovar/rejeitar) uma vez; o estado é reapurado a cada
assinatura por `atos_rules.evaluate_status` (fonte única). Um pagamento aprovado
é `executar`-ado pelo Tesoureiro/admin, criando a despesa ligada (`ato_id`).

RBAC:
- criar:    admin ou membro da Direcção (inclui Tesoureiro)
- assinar:  membro da Direcção (Presidente/Tesoureiro incluídos)
- executar: Tesoureiro ou admin (só pagamentos aprovados)
- cancelar: proponente ou admin (só pendentes)
- ver:      quem vê finanças (admin/financeiro/CF) ou membro da Direcção
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import can_view_finances, get_current_user
from database import db
from helpers import create_audit_log, members_of_orgao, notify_users
from models import (
    ATO_DECISOES,
    ATO_TIPOS,
    Ato,
    AtoCreate,
    AtoExecute,
    AtoSign,
    EXPENSE_CATEGORIES,
    Transaction,
    User,
)
from permissions import is_direcao, is_tesoureiro
from atos_rules import evaluate_status, requisitos_for_tipo

router = APIRouter(prefix="/atos", tags=["atos"])

_LINK = "/financeiro/co-aprovacoes"


def _require_view(user: User):
    if not (can_view_finances(user) or is_direcao(user)):
        raise HTTPException(status_code=403, detail="Sem permissao para ver actos de co-aprovacao")


def _require_create(user: User):
    if not (user.role == "admin" or is_direcao(user)):
        raise HTTPException(status_code=403, detail="Apenas a Direccao ou admin pode criar actos")


def _require_sign(user: User):
    if not is_direcao(user):
        raise HTTPException(status_code=403, detail="Apenas membros da Direccao podem assinar")


def _require_execute(user: User):
    if not (user.role == "admin" or is_tesoureiro(user)):
        raise HTTPException(status_code=403, detail="Apenas o Tesoureiro ou admin pode executar")


def _has_signed(ato: dict, user_id: str) -> bool:
    return any(a.get("user_id") == user_id for a in (ato.get("assinaturas") or []))


@router.post("")
async def create_ato(data: AtoCreate, request: Request, current_user: User = Depends(get_current_user)):
    _require_create(current_user)

    if data.tipo not in ATO_TIPOS:
        raise HTTPException(status_code=400, detail=f"Tipo invalido. Use: {ATO_TIPOS}")
    if not (data.descricao or "").strip():
        raise HTTPException(status_code=400, detail="A descricao e obrigatoria")
    if data.tipo == "pagamento" and (data.valor is None or data.valor <= 0):
        raise HTTPException(status_code=400, detail="Um pagamento exige um valor positivo")
    if data.valor is not None and data.valor < 0:
        raise HTTPException(status_code=400, detail="O valor nao pode ser negativo")

    ato = Ato(
        tipo=data.tipo,
        descricao=data.descricao.strip(),
        valor=data.valor,
        beneficiario=data.beneficiario,
        requisitos=requisitos_for_tipo(data.tipo),
        created_by=current_user.id,
    )
    await db.atos.insert_one(ato.model_dump())
    await create_audit_log(
        current_user.id,
        f"Criou acto de co-aprovacao {ato.id} ({data.tipo})",
        ato.id,
        request=request,
        details={"tipo": data.tipo, "valor": data.valor},
    )

    # Notificar os assinantes requeridos (Direcção) — fallback p/ admins.
    signer_ids = await members_of_orgao("direcao")
    await notify_users(
        signer_ids,
        "financeiro",
        "Acto a aguardar assinatura",
        f"{current_user.name} criou um acto ({data.tipo}) que aguarda a sua co-aprovacao.",
        _LINK,
        exclude_id=current_user.id,
    )
    return ato


@router.get("")
async def list_atos(
    status: Optional[str] = None,
    tipo: Optional[str] = None,
    pendentes_para_mim: bool = False,
    current_user: User = Depends(get_current_user),
):
    _require_view(current_user)
    query = {}
    if status:
        query["status"] = status
    if tipo:
        query["tipo"] = tipo
    atos = await db.atos.find(query, {"_id": 0}).sort("created_at", -1).to_list(None)

    if pendentes_para_mim:
        can_sign = is_direcao(current_user)
        atos = [a for a in atos if a.get("status") == "pendente" and can_sign and not _has_signed(a, current_user.id)]
    return {"items": atos, "total": len(atos)}


@router.get("/{ato_id}")
async def get_ato(ato_id: str, current_user: User = Depends(get_current_user)):
    _require_view(current_user)
    ato = await db.atos.find_one({"id": ato_id}, {"_id": 0})
    if not ato:
        raise HTTPException(status_code=404, detail="Acto nao encontrado")
    return ato


@router.post("/{ato_id}/assinar")
async def sign_ato(ato_id: str, data: AtoSign, request: Request, current_user: User = Depends(get_current_user)):
    _require_sign(current_user)
    if data.decisao not in ATO_DECISOES:
        raise HTTPException(status_code=400, detail=f"Decisao invalida. Use: {ATO_DECISOES}")

    ato = await db.atos.find_one({"id": ato_id}, {"_id": 0})
    if not ato:
        raise HTTPException(status_code=404, detail="Acto nao encontrado")
    if ato.get("status") != "pendente":
        raise HTTPException(status_code=400, detail="O acto ja nao esta pendente")
    if _has_signed(ato, current_user.id):
        raise HTTPException(status_code=400, detail="Ja assinou este acto")

    assinatura = {
        "user_id": current_user.id,
        "cargo": current_user.cargo,
        "decisao": data.decisao,
        "signed_at": datetime.now(timezone.utc).isoformat(),
    }
    novas_assinaturas = (ato.get("assinaturas") or []) + [assinatura]
    novo_status = evaluate_status(novas_assinaturas, ato.get("requisitos") or {})

    await db.atos.update_one({"id": ato_id}, {"$set": {"assinaturas": novas_assinaturas, "status": novo_status}})
    await create_audit_log(
        current_user.id,
        f"Assinou acto {ato_id} ({data.decisao})",
        ato_id,
        request=request,
        details={"decisao": data.decisao, "status": novo_status},
    )

    if novo_status in ("aprovado", "rejeitado"):
        await create_audit_log(current_user.id, f"Acto {ato_id} {novo_status}", ato_id, request=request)
        label = "aprovado" if novo_status == "aprovado" else "rejeitado"
        await notify_users(
            [ato["created_by"]],
            "financeiro",
            f"Acto {label}",
            f"O acto que propos foi {label}.",
            _LINK,
            exclude_id=current_user.id,
        )

    return await db.atos.find_one({"id": ato_id}, {"_id": 0})


@router.post("/{ato_id}/executar")
async def execute_ato(ato_id: str, data: AtoExecute, request: Request, current_user: User = Depends(get_current_user)):
    _require_execute(current_user)

    ato = await db.atos.find_one({"id": ato_id}, {"_id": 0})
    if not ato:
        raise HTTPException(status_code=404, detail="Acto nao encontrado")
    if ato.get("tipo") != "pagamento":
        raise HTTPException(status_code=400, detail="So actos de pagamento podem ser executados")
    if ato.get("status") != "aprovado":
        raise HTTPException(status_code=400, detail="O acto nao esta aprovado")
    if ato.get("transaction_id"):
        raise HTTPException(status_code=400, detail="O acto ja foi executado")
    valor = ato.get("valor")
    if valor is None or valor <= 0:
        raise HTTPException(status_code=400, detail="O acto nao tem um valor valido a pagar")

    category = data.category or "operacional"
    if category not in EXPENSE_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Categoria invalida. Use: {EXPENSE_CATEGORIES}")
    date = data.date or datetime.now(timezone.utc).isoformat()

    transaction = Transaction(
        type="despesa",
        category=category,
        description=ato.get("descricao") or f"Pagamento (acto {ato_id})",
        amount=valor,
        date=date,
        reference=data.reference,
        ato_id=ato_id,
        created_by=current_user.id,
    )
    await db.transactions.insert_one(transaction.model_dump())
    await db.atos.update_one({"id": ato_id}, {"$set": {"status": "executado", "transaction_id": transaction.id}})
    await create_audit_log(
        current_user.id,
        f"Executou acto {ato_id} -> despesa {transaction.id} ({valor} CVE)",
        ato_id,
        request=request,
        details={"transaction_id": transaction.id, "amount": valor},
    )
    await notify_users(
        [ato["created_by"]],
        "financeiro",
        "Acto executado",
        f"O pagamento do acto que propos foi executado ({valor:,.0f} CVE).",
        _LINK,
        exclude_id=current_user.id,
    )
    return await db.atos.find_one({"id": ato_id}, {"_id": 0})


@router.post("/{ato_id}/cancelar")
async def cancel_ato(ato_id: str, request: Request, current_user: User = Depends(get_current_user)):
    ato = await db.atos.find_one({"id": ato_id}, {"_id": 0})
    if not ato:
        raise HTTPException(status_code=404, detail="Acto nao encontrado")
    if not (current_user.role == "admin" or ato.get("created_by") == current_user.id):
        raise HTTPException(status_code=403, detail="So o proponente ou admin pode cancelar")
    if ato.get("status") != "pendente":
        raise HTTPException(status_code=400, detail="So actos pendentes podem ser cancelados")

    await db.atos.update_one({"id": ato_id}, {"$set": {"status": "cancelado"}})
    await create_audit_log(current_user.id, f"Cancelou acto {ato_id}", ato_id, request=request)
    return await db.atos.find_one({"id": ato_id}, {"_id": 0})
