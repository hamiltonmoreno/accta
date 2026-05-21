"""Voz e participação do sócio (spec-voz-participacao-socio).

Módulo único das funcionalidades da Categoria 1. Segue o esqueleto da casa
(ver routes/polls.py): RBAC explícito, audit log em toda a escrita, notificação
ao destinatário. Colecções separadas por domínio.

F1 — Patrocínio de admissão (Art. 8.3): confirmação/recusa dos padrinhos e inbox.
A criação dos pedidos de patrocínio vive no fluxo de registo (routes/auth_routes).
"""

import math
import uuid
from datetime import datetime, timedelta, timezone

from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, Depends, HTTPException, Request

from auth import get_current_user
from database import db
from helpers import count_voting_members, create_audit_log, members_of_orgao, notify_admins, notify_users
from models import (
    Esclarecimento,
    EsclarecimentoCreate,
    PatrocinioRespond,
    Peticao,
    PeticaoCreate,
    PeticaoEncaminhar,
    Reclamacao,
    ReclamacaoCreate,
    ReclamacaoResponder,
    RecursoDecisao,
    RespostaTexto,
    User,
)
from permissions import is_conselho_fiscal, is_direcao, is_mesa_ag, is_voting_member

router = APIRouter(tags=["participacao"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# 1.1 — Patrocínio de admissão (Art. 8.3)
# --------------------------------------------------------------------------- #


@router.get("/participacao/patrocinios/pendentes")
async def patrocinios_pendentes(current_user: User = Depends(get_current_user)):
    """Candidatos à espera da MINHA confirmação de patrocínio."""
    rows = await db.patrocinios.find({"sponsor_user_id": current_user.id, "status": "pendente"}, {"_id": 0}).to_list(
        200
    )
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


# --------------------------------------------------------------------------- #
# 1.3 — Petição para AG extraordinária (Art. 9.f, 19.2.d)
# --------------------------------------------------------------------------- #


async def _peticao_view(p: dict, user_id: str) -> dict:
    count = await db.peticao_assinaturas.count_documents({"peticao_id": p["id"]})
    signed = await db.peticao_assinaturas.find_one({"peticao_id": p["id"], "user_id": user_id}, {"_id": 0, "id": 1})
    return {**p, "signature_count": count, "viewer_has_signed": signed is not None}


@router.post("/peticoes", response_model=Peticao)
async def criar_peticao(data: PeticaoCreate, request: Request, current_user: User = Depends(get_current_user)):
    if not is_voting_member(current_user):
        raise HTTPException(status_code=403, detail="Apenas sócios com direito a voto podem criar petições")
    p = Peticao(titulo=data.titulo, fundamentacao=data.fundamentacao, created_by=current_user.id, created_at=_now())
    await db.peticoes.insert_one(p.model_dump())
    await create_audit_log(current_user.id, "peticao_criada", p.id, request=request)
    return p


@router.get("/peticoes")
async def listar_peticoes(current_user: User = Depends(get_current_user)):
    rows = await db.peticoes.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return [await _peticao_view(p, current_user.id) for p in rows]


@router.get("/peticoes/{peticao_id}")
async def obter_peticao(peticao_id: str, current_user: User = Depends(get_current_user)):
    p = await db.peticoes.find_one({"id": peticao_id}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Petição não encontrada")
    return await _peticao_view(p, current_user.id)


@router.post("/peticoes/{peticao_id}/assinar")
async def assinar_peticao(peticao_id: str, request: Request, current_user: User = Depends(get_current_user)):
    if not is_voting_member(current_user):
        raise HTTPException(status_code=403, detail="Apenas sócios com direito a voto podem assinar")
    p = await db.peticoes.find_one({"id": peticao_id}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Petição não encontrada")
    if p["status"] not in ("aberta", "atingida"):
        raise HTTPException(status_code=409, detail="Esta petição já não aceita assinaturas")
    try:
        await db.peticao_assinaturas.insert_one(
            {"id": str(uuid.uuid4()), "peticao_id": peticao_id, "user_id": current_user.id, "created_at": _now()}
        )
    except UniqueViolationError:
        raise HTTPException(status_code=400, detail="Já assinou esta petição")
    await create_audit_log(current_user.id, "peticao_assinada", peticao_id, request=request)

    # Recontar + limiar 1/4 dos votantes (idempotente — só dispara uma vez).
    count = await db.peticao_assinaturas.count_documents({"peticao_id": peticao_id})
    target = max(1, math.ceil((await count_voting_members()) * p.get("threshold_fraction", 0.25)))
    if p["status"] == "aberta" and count >= target:
        await db.peticoes.update_one(
            {"id": peticao_id}, {"$set": {"status": "atingida", "met_at": _now(), "target_count": target}}
        )
        await create_audit_log(current_user.id, "peticao_atingiu_limiar", peticao_id, request=request)
        mesa = await members_of_orgao("mesa_ag")
        await notify_users(
            mesa,
            "system",
            "Petição atingiu o limiar",
            f"A petição «{p['titulo']}» atingiu 1/4 dos membros votantes (Art. 19.2.d).",
            link="/participacao/peticoes",
        )
    return {"peticao_id": peticao_id, "signature_count": count, "target_count": target}


@router.delete("/peticoes/{peticao_id}/assinar")
async def retirar_assinatura(peticao_id: str, request: Request, current_user: User = Depends(get_current_user)):
    p = await db.peticoes.find_one({"id": peticao_id}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Petição não encontrada")
    if p["status"] != "aberta":
        raise HTTPException(status_code=409, detail="Só pode retirar a assinatura enquanto a petição está aberta")
    res = await db.peticao_assinaturas.delete_one({"peticao_id": peticao_id, "user_id": current_user.id})
    await create_audit_log(current_user.id, "peticao_assinatura_retirada", peticao_id, request=request)
    return {"peticao_id": peticao_id, "removed": getattr(res, "deleted_count", 0)}


@router.post("/peticoes/{peticao_id}/encaminhar")
async def encaminhar_peticao(
    peticao_id: str, data: PeticaoEncaminhar, request: Request, current_user: User = Depends(get_current_user)
):
    if not (current_user.role == "admin" or is_mesa_ag(current_user)):
        raise HTTPException(status_code=403, detail="Apenas a Mesa da AG ou admin podem encaminhar")
    p = await db.peticoes.find_one({"id": peticao_id}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Petição não encontrada")
    upd = {"status": "encaminhada"}
    if data.assembleia_id:
        upd["assembleia_id"] = data.assembleia_id
    await db.peticoes.update_one({"id": peticao_id}, {"$set": upd})
    await create_audit_log(current_user.id, "peticao_encaminhada", peticao_id, request=request)
    return {"peticao_id": peticao_id, "status": "encaminhada"}


# --------------------------------------------------------------------------- #
# 1.6 — Pedidos de esclarecimento (Art. 9.j)
# --------------------------------------------------------------------------- #

_ORGAO_CHECK = {"direcao": is_direcao, "mesa_ag": is_mesa_ag, "conselho_fiscal": is_conselho_fiscal}


def _can_answer_orgao(user, orgao: str) -> bool:
    if getattr(user, "role", None) == "admin":
        return True
    check = _ORGAO_CHECK.get(orgao)
    return bool(check and check(user))


@router.post("/esclarecimentos", response_model=Esclarecimento)
async def criar_esclarecimento(
    data: EsclarecimentoCreate, request: Request, current_user: User = Depends(get_current_user)
):
    e = Esclarecimento(
        orgao_destino=data.orgao_destino,
        assunto=data.assunto,
        pergunta=data.pergunta,
        created_by=current_user.id,
        created_at=_now(),
    )
    await db.esclarecimentos.insert_one(e.model_dump())
    await create_audit_log(current_user.id, "esclarecimento_submetido", e.id, request=request)
    dest = await members_of_orgao(data.orgao_destino)
    await notify_users(
        dest,
        "system",
        "Novo pedido de esclarecimento",
        f"{current_user.name} fez uma pergunta ao órgão (Art. 9.j).",
        link="/participacao/esclarecimentos",
    )
    return e


@router.get("/esclarecimentos")
async def listar_esclarecimentos(current_user: User = Depends(get_current_user)):
    rows = await db.esclarecimentos.find({}, {"_id": 0}).sort("created_at", -1).to_list(300)
    # Autor vê os próprios; membro do órgão vê os endereçados ao seu órgão; admin tudo.
    return [
        e
        for e in rows
        if e.get("created_by") == current_user.id or _can_answer_orgao(current_user, e.get("orgao_destino", ""))
    ]


@router.get("/esclarecimentos/{esc_id}")
async def obter_esclarecimento(esc_id: str, current_user: User = Depends(get_current_user)):
    e = await db.esclarecimentos.find_one({"id": esc_id}, {"_id": 0})
    if not e:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if e.get("created_by") != current_user.id and not _can_answer_orgao(current_user, e.get("orgao_destino", "")):
        raise HTTPException(status_code=403, detail="Sem permissão")
    return e


@router.post("/esclarecimentos/{esc_id}/responder", response_model=Esclarecimento)
async def responder_esclarecimento(
    esc_id: str, data: RespostaTexto, request: Request, current_user: User = Depends(get_current_user)
):
    e = await db.esclarecimentos.find_one({"id": esc_id}, {"_id": 0})
    if not e:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if not _can_answer_orgao(current_user, e.get("orgao_destino", "")):
        raise HTTPException(status_code=403, detail="Apenas o órgão destinatário (ou admin) pode responder")
    resposta = {"by": current_user.id, "at": _now(), "text": data.texto}
    await db.esclarecimentos.update_one({"id": esc_id}, {"$set": {"resposta": resposta, "status": "respondido"}})
    await create_audit_log(current_user.id, "esclarecimento_respondido", esc_id, request=request)
    if e.get("created_by"):
        await notify_users(
            [e["created_by"]],
            "system",
            "Esclarecimento respondido",
            f"O órgão respondeu ao seu pedido «{e.get('assunto')}».",
            link="/participacao/esclarecimentos",
        )
    return await db.esclarecimentos.find_one({"id": esc_id}, {"_id": 0})


# --------------------------------------------------------------------------- #
# 1.5 — Reclamações e recursos (Art. 9.i) — genérico, NÃO disciplinar
# --------------------------------------------------------------------------- #

_RECLAMACAO_SLA_DAYS = 15  # decisão do dono


def _can_see_reclamacao(user, r: dict) -> bool:
    return (
        r.get("created_by") == getattr(user, "id", None) or getattr(user, "role", None) == "admin" or is_direcao(user)
    )


@router.post("/reclamacoes", response_model=Reclamacao)
async def criar_reclamacao(data: ReclamacaoCreate, request: Request, current_user: User = Depends(get_current_user)):
    prazo = (datetime.now(timezone.utc) + timedelta(days=_RECLAMACAO_SLA_DAYS)).isoformat()
    r = Reclamacao(
        assunto=data.assunto,
        descricao=data.descricao,
        created_by=current_user.id,
        created_at=_now(),
        prazo_resposta=prazo,
    )
    await db.reclamacoes.insert_one(r.model_dump())
    await create_audit_log(current_user.id, "reclamacao_submetida", r.id, request=request)
    direcao = await members_of_orgao("direcao")
    await notify_users(
        direcao,
        "system",
        "Nova reclamação",
        f"{current_user.name} submeteu uma reclamação (Art. 9.i).",
        link="/participacao/reclamacoes",
    )
    return r


@router.get("/reclamacoes")
async def listar_reclamacoes(current_user: User = Depends(get_current_user)):
    rows = await db.reclamacoes.find({}, {"_id": 0}).sort("created_at", -1).to_list(300)
    return [r for r in rows if _can_see_reclamacao(current_user, r)]


@router.get("/reclamacoes/{rec_id}")
async def obter_reclamacao(rec_id: str, current_user: User = Depends(get_current_user)):
    r = await db.reclamacoes.find_one({"id": rec_id}, {"_id": 0})
    if not r:
        raise HTTPException(status_code=404, detail="Reclamação não encontrada")
    if not _can_see_reclamacao(current_user, r):
        raise HTTPException(status_code=403, detail="Sem permissão")
    return r


@router.post("/reclamacoes/{rec_id}/responder", response_model=Reclamacao)
async def responder_reclamacao(
    rec_id: str, data: ReclamacaoResponder, request: Request, current_user: User = Depends(get_current_user)
):
    if not (current_user.role == "admin" or is_direcao(current_user)):
        raise HTTPException(status_code=403, detail="Apenas a Direcção (ou admin) pode responder")
    r = await db.reclamacoes.find_one({"id": rec_id}, {"_id": 0})
    if not r:
        raise HTTPException(status_code=404, detail="Reclamação não encontrada")
    resposta = {"by": current_user.id, "at": _now(), "text": data.texto}
    new_status = "resolvida" if data.resolvida else "respondida"
    await db.reclamacoes.update_one(
        {"id": rec_id}, {"$set": {"direcao_resposta": resposta, "resolvida": data.resolvida, "status": new_status}}
    )
    await create_audit_log(current_user.id, "reclamacao_respondida", rec_id, request=request)
    if r.get("created_by"):
        await notify_users(
            [r["created_by"]],
            "system",
            "Reclamação respondida",
            f"A Direcção respondeu à sua reclamação «{r.get('assunto')}».",
            link="/participacao/reclamacoes",
        )
    return await db.reclamacoes.find_one({"id": rec_id}, {"_id": 0})


@router.post("/reclamacoes/{rec_id}/recurso", response_model=Reclamacao)
async def abrir_recurso(rec_id: str, request: Request, current_user: User = Depends(get_current_user)):
    r = await db.reclamacoes.find_one({"id": rec_id}, {"_id": 0})
    if not r:
        raise HTTPException(status_code=404, detail="Reclamação não encontrada")
    if r.get("created_by") != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o autor pode recorrer")
    # Só após resposta da Direcção OU após o prazo expirar.
    answered = r.get("direcao_resposta") is not None
    expired = bool(r.get("prazo_resposta") and r["prazo_resposta"] < _now())
    if not (answered or expired):
        raise HTTPException(
            status_code=409, detail="Só pode recorrer após resposta da Direcção ou após o prazo expirar"
        )
    recurso = {"opened_at": _now(), "by": current_user.id, "status": "aberto"}
    await db.reclamacoes.update_one({"id": rec_id}, {"$set": {"status": "recurso", "recurso": recurso}})
    await create_audit_log(current_user.id, "reclamacao_recurso", rec_id, request=request)
    mesa = await members_of_orgao("mesa_ag")
    await notify_users(
        mesa,
        "system",
        "Recurso de reclamação",
        "Foi aberto recurso à AG sobre uma reclamação (Art. 9.i).",
        link="/participacao/reclamacoes",
    )
    return await db.reclamacoes.find_one({"id": rec_id}, {"_id": 0})


@router.post("/reclamacoes/{rec_id}/decidir-recurso", response_model=Reclamacao)
async def decidir_recurso(
    rec_id: str, data: RecursoDecisao, request: Request, current_user: User = Depends(get_current_user)
):
    if not (current_user.role == "admin" or is_mesa_ag(current_user)):
        raise HTTPException(status_code=403, detail="Apenas a Mesa da AG (ou admin) pode decidir o recurso")
    r = await db.reclamacoes.find_one({"id": rec_id}, {"_id": 0})
    if not r:
        raise HTTPException(status_code=404, detail="Reclamação não encontrada")
    if r.get("status") != "recurso":
        raise HTTPException(status_code=409, detail="Esta reclamação não está em recurso")
    recurso = {
        **(r.get("recurso") or {}),
        "status": "decidido",
        "decisao": data.decisao,
        "assembleia_id": data.assembleia_id,
        "deliberacao_id": data.deliberacao_id,
        "decided_at": _now(),
        "decided_by": current_user.id,
    }
    await db.reclamacoes.update_one({"id": rec_id}, {"$set": {"recurso": recurso, "status": "encerrada"}})
    await create_audit_log(current_user.id, "reclamacao_decidida", rec_id, request=request)
    if r.get("created_by"):
        await notify_users(
            [r["created_by"]],
            "system",
            "Recurso decidido",
            "A AG decidiu o seu recurso.",
            link="/participacao/reclamacoes",
        )
    return await db.reclamacoes.find_one({"id": rec_id}, {"_id": 0})
