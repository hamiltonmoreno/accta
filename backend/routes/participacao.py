"""Voz e participação do sócio (spec-voz-participacao-socio).

Módulo único das funcionalidades da Categoria 1. Segue o esqueleto da casa
(ver routes/polls.py): RBAC explícito, audit log em toda a escrita, notificação
ao destinatário. Colecções separadas por domínio.

F1 — Patrocínio de admissão (Art. 8.3): confirmação/recusa dos padrinhos e inbox.
A criação dos pedidos de patrocínio vive no fluxo de registo (routes/auth_routes).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import get_current_user
from database import db
from helpers import create_audit_log, notify_admins
from models import PatrocinioRespond, User
from permissions import is_voting_member

router = APIRouter(tags=["participacao"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# 1.1 — Patrocínio de admissão (Art. 8.3)
# --------------------------------------------------------------------------- #


@router.get("/participacao/patrocinios/pendentes")
async def patrocinios_pendentes(current_user: User = Depends(get_current_user)):
    """Candidatos à espera da MINHA confirmação de patrocínio."""
    rows = await db.patrocinios.find(
        {"sponsor_user_id": current_user.id, "status": "pendente"}, {"_id": 0}
    ).to_list(200)
    # Desnormaliza o nome/member_id do candidato para apresentação.
    out = []
    for r in rows:
        cand = await db.users.find_one({"id": r["candidate_id"]}, {"_id": 0, "name": 1, "member_id": 1, "email": 1})
        out.append(
            {
                "candidate_id": r["candidate_id"],
                "candidate_name": (cand or {}).get("name"),
                "candidate_member_id": (cand or {}).get("member_id"),
                "status": r["status"],
                "created_at": r.get("created_at"),
            }
        )
    return out


async def _respond_patrocinio(candidate_id: str, current_user: User, new_status: str, note, request: Request):
    patrocinio = await db.patrocinios.find_one(
        {"candidate_id": candidate_id, "sponsor_user_id": current_user.id}, {"_id": 0}
    )
    if not patrocinio:
        # Não é padrinho nomeado deste candidato → não revela existência.
        raise HTTPException(status_code=403, detail="Sem permissão para responder a este patrocínio")
    if patrocinio["status"] != "pendente":
        raise HTTPException(status_code=409, detail="Este patrocínio já foi respondido")

    update = {"status": new_status, "responded_at": _now()}
    if note:
        update["note"] = note
    await db.patrocinios.update_one(
        {"candidate_id": candidate_id, "sponsor_user_id": current_user.id}, {"$set": update}
    )
    action = "patrocinio_confirmado" if new_status == "confirmado" else "patrocinio_recusado"
    await create_audit_log(current_user.id, action, candidate_id, request=request)

    if new_status == "confirmado":
        confirmados = await db.patrocinios.count_documents({"candidate_id": candidate_id, "status": "confirmado"})
        if confirmados >= 2:
            cand = await db.users.find_one({"id": candidate_id}, {"_id": 0, "name": 1})
            nome = (cand or {}).get("name", candidate_id)
            await notify_admins(
                "system",
                "Patrocínio completo",
                f"O candidato {nome} já tem 2 patrocínios confirmados (Art. 8.3).",
                link="/admin/pedidos-inscricao",
            )
    return {"candidate_id": candidate_id, "status": new_status}


@router.post("/participacao/patrocinios/{candidate_id}/confirmar")
async def confirmar_patrocinio(
    candidate_id: str,
    request: Request,
    data: PatrocinioRespond = PatrocinioRespond(),
    current_user: User = Depends(get_current_user),
):
    if not is_voting_member(current_user):
        raise HTTPException(status_code=403, detail="Apenas sócios com direito a voto podem patrocinar")
    return await _respond_patrocinio(candidate_id, current_user, "confirmado", data.note, request)


@router.post("/participacao/patrocinios/{candidate_id}/recusar")
async def recusar_patrocinio(
    candidate_id: str,
    request: Request,
    data: PatrocinioRespond = PatrocinioRespond(),
    current_user: User = Depends(get_current_user),
):
    if not is_voting_member(current_user):
        raise HTTPException(status_code=403, detail="Apenas sócios com direito a voto podem patrocinar")
    return await _respond_patrocinio(candidate_id, current_user, "recusado", data.note, request)
