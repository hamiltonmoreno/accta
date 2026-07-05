"""Voz e participação do sócio (spec-voz-participacao-socio).

Módulo único das funcionalidades da Categoria 1. Segue o esqueleto da casa
(ver routes/polls.py): RBAC explícito, audit log em toda a escrita, notificação
ao destinatário. Colecções separadas por domínio.
"""

import math
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from auth import generate_qr_hash, get_current_user, is_admin
from database import db, next_member_id
from email_service import send_invite_email
from helpers import (
    count_voting_members,
    create_audit_log,
    members_of_orgao,
    notify_admins,
    notify_users,
    resolve_link_base,
    voting_member_ids,
)
from models import (
    Esclarecimento,
    EsclarecimentoCreate,
    HonorarioCreate,
    HonorarioLigar,
    HonorarioNomination,
    Peticao,
    PeticaoCreate,
    PeticaoEncaminhar,
    PropostaAG,
    PropostaAGCreate,
    PropostaIncluir,
    PropostaTriagem,
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
# 1.3 — Petição para AG extraordinária (Art. 9.f, 19.2.d)
# --------------------------------------------------------------------------- #


def _peticao_enriched(p: dict, signature_count: int, viewer_has_signed: bool) -> dict:
    """Shape único da petição enriquecida — usado pela listagem (batch) e pelo
    detalhe (_peticao_view), para os dois endpoints não divergirem."""
    return {**p, "signature_count": signature_count, "viewer_has_signed": viewer_has_signed}


async def _peticao_view(p: dict, user_id: str) -> dict:
    count = await db.peticao_assinaturas.count_documents({"peticao_id": p["id"]})
    signed = await db.peticao_assinaturas.find_one({"peticao_id": p["id"], "user_id": user_id}, {"_id": 0, "id": 1})
    return _peticao_enriched(p, count, signed is not None)


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
    if not rows:
        return []
    # Uma query para as assinaturas de toda a página (antes: 2 queries POR
    # petição via _peticao_view — 200 petições = 400 queries).
    ids = [p["id"] for p in rows]
    assinaturas = await db.peticao_assinaturas.find(
        {"peticao_id": {"$in": ids}}, {"_id": 0, "peticao_id": 1, "user_id": 1}
    ).to_list(None)
    counts: dict[str, int] = {}
    signed_by_viewer: set[str] = set()
    for a in assinaturas:
        pid = a.get("peticao_id")
        counts[pid] = counts.get(pid, 0) + 1
        if a.get("user_id") == current_user.id:
            signed_by_viewer.add(pid)
    return [_peticao_enriched(p, counts.get(p["id"], 0), p["id"] in signed_by_viewer) for p in rows]


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
    if not (is_admin(current_user) or is_mesa_ag(current_user)):
        raise HTTPException(status_code=403, detail="Apenas a Mesa da AG ou admin podem encaminhar")
    p = await db.peticoes.find_one({"id": peticao_id}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Petição não encontrada")
    if p.get("status") != "atingida":
        raise HTTPException(status_code=409, detail="Só petições que atingiram o limiar podem ser encaminhadas")
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
    if not (is_admin(current_user) or is_direcao(current_user)):
        raise HTTPException(status_code=403, detail="Apenas a Direcção (ou admin) pode responder")
    r = await db.reclamacoes.find_one({"id": rec_id}, {"_id": 0})
    if not r:
        raise HTTPException(status_code=404, detail="Reclamação não encontrada")
    if r.get("status") in ("resolvida", "recurso", "encerrada"):
        raise HTTPException(status_code=409, detail="Esta reclamação já não pode ser respondida")
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
    if r.get("status") in ("recurso", "encerrada"):
        raise HTTPException(status_code=409, detail="Esta reclamação já não aceita novo recurso")
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
    if not (is_admin(current_user) or is_mesa_ag(current_user)):
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


# --------------------------------------------------------------------------- #
# 1.4 — Propostas e temas para a ordem de trabalhos (Art. 9.g, 9.h)
# --------------------------------------------------------------------------- #

# Estados que qualquer membro pode ver mesmo não sendo o autor (transparência da
# ordem de trabalhos); os restantes (submetida/em_triagem/recusada/arquivada) só
# para o autor e para quem tria.
_PROPOSTA_PUBLICAS = {"aceite", "incluida"}


def _can_triage_propostas(user) -> bool:
    return getattr(user, "role", None) == "admin" or is_mesa_ag(user) or is_direcao(user)


@router.post("/propostas-ag", response_model=PropostaAG)
async def criar_proposta(data: PropostaAGCreate, request: Request, current_user: User = Depends(get_current_user)):
    pr = PropostaAG(
        titulo=data.titulo,
        descricao=data.descricao,
        tipo=data.tipo,
        created_by=current_user.id,
        created_at=_now(),
    )
    await db.propostas_ag.insert_one(pr.model_dump())
    await create_audit_log(current_user.id, "proposta_submetida", pr.id, request=request)
    # Triagem cabe à Mesa da AG e à Direcção (Art. 9.g/9.h).
    dest = list({*(await members_of_orgao("mesa_ag")), *(await members_of_orgao("direcao"))})
    await notify_users(
        dest,
        "system",
        "Nova proposta para a ordem de trabalhos",
        f"{current_user.name} submeteu uma proposta «{pr.titulo}» (Art. 9.g).",
        link="/participacao/propostas",
    )
    return pr


@router.get("/propostas-ag")
async def listar_propostas(status: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"status": status} if status else {}
    rows = await db.propostas_ag.find(query, {"_id": 0}).sort("created_at", -1).to_list(300)
    if _can_triage_propostas(current_user):
        return rows
    # Membro comum: as próprias + as aceites/incluídas.
    return [r for r in rows if r.get("created_by") == current_user.id or r.get("status") in _PROPOSTA_PUBLICAS]


@router.get("/propostas-ag/{proposta_id}")
async def obter_proposta(proposta_id: str, current_user: User = Depends(get_current_user)):
    pr = await db.propostas_ag.find_one({"id": proposta_id}, {"_id": 0})
    if not pr:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    if not (
        _can_triage_propostas(current_user)
        or pr.get("created_by") == current_user.id
        or pr.get("status") in _PROPOSTA_PUBLICAS
    ):
        raise HTTPException(status_code=403, detail="Sem permissão")
    return pr


@router.post("/propostas-ag/{proposta_id}/triagem", response_model=PropostaAG)
async def triar_proposta(
    proposta_id: str, data: PropostaTriagem, request: Request, current_user: User = Depends(get_current_user)
):
    if not _can_triage_propostas(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Mesa da AG, a Direcção (ou admin) podem triar propostas")
    pr = await db.propostas_ag.find_one({"id": proposta_id}, {"_id": 0})
    if not pr:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    if pr.get("status") not in ("submetida", "em_triagem"):
        raise HTTPException(status_code=409, detail="Esta proposta já não está em triagem")
    upd = {
        "status": data.decisao,
        "reviewer_id": current_user.id,
        "reviewed_at": _now(),
        "decisao_motivo": data.decisao_motivo,
    }
    await db.propostas_ag.update_one({"id": proposta_id}, {"$set": upd})
    await create_audit_log(current_user.id, "proposta_triada", proposta_id, request=request)
    if pr.get("created_by"):
        verbo = "aceite" if data.decisao == "aceite" else "recusada"
        await notify_users(
            [pr["created_by"]],
            "system",
            "Proposta triada",
            f"A sua proposta «{pr.get('titulo')}» foi {verbo}.",
            link="/participacao/propostas",
        )
    return await db.propostas_ag.find_one({"id": proposta_id}, {"_id": 0})


@router.post("/propostas-ag/{proposta_id}/incluir", response_model=PropostaAG)
async def incluir_proposta(
    proposta_id: str, data: PropostaIncluir, request: Request, current_user: User = Depends(get_current_user)
):
    if not (is_admin(current_user) or is_mesa_ag(current_user)):
        raise HTTPException(
            status_code=403, detail="Apenas a Mesa da AG (ou admin) podem incluir na ordem de trabalhos"
        )
    pr = await db.propostas_ag.find_one({"id": proposta_id}, {"_id": 0})
    if not pr:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    if pr.get("status") != "aceite":
        raise HTTPException(status_code=409, detail="Só propostas aceites podem ser incluídas na ordem de trabalhos")
    upd = {"status": "incluida"}
    if data.assembleia_id is not None:
        upd["assembleia_id"] = data.assembleia_id
    if data.ordem_index is not None:
        upd["ordem_index"] = data.ordem_index
    await db.propostas_ag.update_one({"id": proposta_id}, {"$set": upd})
    await create_audit_log(current_user.id, "proposta_incluida", proposta_id, request=request)
    if pr.get("created_by"):
        await notify_users(
            [pr["created_by"]],
            "system",
            "Proposta incluída na ordem de trabalhos",
            f"A sua proposta «{pr.get('titulo')}» foi incluída na ordem de trabalhos.",
            link="/participacao/propostas",
        )
    return await db.propostas_ag.find_one({"id": proposta_id}, {"_id": 0})


# --------------------------------------------------------------------------- #
# 1.2 — Membros honorários (Art. 8.4): Direcção nomeia → AG vota → 2/3 elege.
# A votação reusa polls/user_votes (sem colecção nova). Interim em participacao.py
# (spec §2.1/§14.8); migra para governança quando o módulo Assembleia existir.
# --------------------------------------------------------------------------- #

# Voto de honorário: opções fixas (apuramento sobre votos válidos = favor+contra).
_HONORARIO_POLL_OPTIONS = [
    {"id": 1, "text": "A favor"},
    {"id": 2, "text": "Contra"},
    {"id": 3, "text": "Abstenção"},
]
# Janela ampla: o fecho autoritativo é o /apurar manual da Mesa, não o end_date.
_HONORARIO_VOTE_WINDOW_DAYS = 30
_INVITE_TTL_DAYS = 7  # alinhado com routes/admin.py


def _can_nominate_honorario(user) -> bool:
    """Nomear: Direcção ou admin (spec §4.5)."""
    return getattr(user, "role", None) == "admin" or is_direcao(user)


def _can_manage_honorarios(user) -> bool:
    """Abrir/apurar votação: Mesa da AG ou admin (spec §4.5)."""
    return getattr(user, "role", None) == "admin" or is_mesa_ag(user)


def _can_see_honorarios(user) -> bool:
    return _can_nominate_honorario(user) or _can_manage_honorarios(user)


@router.post("/honorarios", response_model=HonorarioNomination)
async def nomear_honorario(data: HonorarioCreate, request: Request, current_user: User = Depends(get_current_user)):
    if not _can_nominate_honorario(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Direcção (ou admin) pode nomear membros honorários")
    # Eleva membro existente → validar que é um sócio real.
    if data.nominee_user_id:
        u = await db.users.find_one({"id": data.nominee_user_id}, {"_id": 0, "id": 1, "account_type": 1})
        if not u or (u.get("account_type") or "member") != "member":
            raise HTTPException(status_code=422, detail="O nomeado interno não é um sócio válido")
    nom = HonorarioNomination(
        nominee_name=data.nominee_name,
        nominee_user_id=data.nominee_user_id,
        nominee_email=data.nominee_email,
        justificacao=data.justificacao,
        proposta_por=current_user.id,
        created_at=_now(),
    )
    await db.honorarios_nominations.insert_one(nom.model_dump())
    await create_audit_log(current_user.id, "honorario_nomeado", nom.id, request=request)
    # A Mesa da AG é quem abre a votação → notificá-la.
    mesa = await members_of_orgao("mesa_ag")
    await notify_users(
        mesa,
        "system",
        "Nova nomeação de membro honorário",
        f"A Direcção nomeou «{nom.nominee_name}» como membro honorário (Art. 8.4).",
        link="/governanca/honorarios",
    )
    return nom


@router.get("/honorarios")
async def listar_honorarios(status: Optional[str] = None, current_user: User = Depends(get_current_user)):
    if not _can_see_honorarios(current_user):
        raise HTTPException(status_code=403, detail="Sem permissão")
    query = {"status": status} if status else {}
    return await db.honorarios_nominations.find(query, {"_id": 0}).sort("created_at", -1).to_list(300)


@router.get("/honorarios/{nom_id}", response_model=HonorarioNomination)
async def obter_honorario(nom_id: str, current_user: User = Depends(get_current_user)):
    if not _can_see_honorarios(current_user):
        raise HTTPException(status_code=403, detail="Sem permissão")
    nom = await db.honorarios_nominations.find_one({"id": nom_id}, {"_id": 0})
    if not nom:
        raise HTTPException(status_code=404, detail="Nomeação não encontrada")
    return nom


@router.post("/honorarios/{nom_id}/abrir-votacao", response_model=HonorarioNomination)
async def abrir_votacao_honorario(nom_id: str, request: Request, current_user: User = Depends(get_current_user)):
    if not _can_manage_honorarios(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Mesa da AG (ou admin) pode abrir a votação")
    nom = await db.honorarios_nominations.find_one({"id": nom_id}, {"_id": 0})
    if not nom:
        raise HTTPException(status_code=404, detail="Nomeação não encontrada")
    if nom["status"] != "proposta":
        raise HTTPException(status_code=409, detail="Só nomeações em «proposta» podem ir a votação")
    now = datetime.now(timezone.utc)
    poll_id = str(uuid.uuid4())
    poll_doc = {
        "id": poll_id,
        "title": f"Membro honorário: {nom['nominee_name']}",
        "description": (f"Votação de membro honorário (Art. 8.4) — maioria de 2/3. {nom['justificacao']}")[:2000],
        "options": _HONORARIO_POLL_OPTIONS,
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=_HONORARIO_VOTE_WINDOW_DAYS)).isoformat(),
        "status": "aberta",
        "result_visibility": "socios",
        "created_at": now.isoformat(),
    }
    await db.polls.insert_one(poll_doc)
    await db.honorarios_nominations.update_one({"id": nom_id}, {"$set": {"status": "em_votacao", "poll_id": poll_id}})
    await create_audit_log(current_user.id, "honorario_votacao_aberta", nom_id, request=request)
    # Notifica os votantes (honorários/técnicos/inactivos/suspensos não votam — §2.2).
    voters = await voting_member_ids()
    await notify_users(
        voters,
        "poll",
        "Votação de membro honorário",
        f"Está aberta a votação para eleger «{nom['nominee_name']}» como membro honorário (2/3).",
        link="/votacoes",
    )
    return await db.honorarios_nominations.find_one({"id": nom_id}, {"_id": 0})


@router.post("/honorarios/{nom_id}/apurar", response_model=HonorarioNomination)
async def apurar_honorario(
    nom_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    if not _can_manage_honorarios(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Mesa da AG (ou admin) pode apurar a votação")
    nom = await db.honorarios_nominations.find_one({"id": nom_id}, {"_id": 0})
    if not nom:
        raise HTTPException(status_code=404, detail="Nomeação não encontrada")
    if nom["status"] != "em_votacao":
        raise HTTPException(status_code=409, detail="Esta nomeação não está em votação")
    poll_id = nom.get("poll_id")
    # Lê os votos ANTES de fechar o poll: fechar primeiro abria uma janela em que o
    # poll estava "encerrada" mas o apuramento ainda não tinha lido os votos.
    votes = await db.user_votes.find({"poll_id": poll_id}, {"_id": 0, "vote_option": 1}).to_list(None)
    # Fecha o poll (idempotente — não falha se já encerrado/inexistente).
    if poll_id:
        await db.polls.update_one({"id": poll_id}, {"$set": {"status": "encerrada"}})
    favor = sum(1 for v in votes if v.get("vote_option") == 1)
    contra = sum(1 for v in votes if v.get("vote_option") == 2)
    base = favor + contra  # decisão do dono: votos válidos (abstenções fora)
    aprovado = base > 0 and favor >= math.ceil(2 / 3 * base)
    new_status = "eleito" if aprovado else "rejeitado"
    # CAS: fecha a nomeação atomicamente. Se uma chamada concorrente já apurou,
    # aborta ANTES dos efeitos (elevação de membro / convite + email) para não
    # os disparar duas vezes — o email é uma STOP-condition.
    res = await db.honorarios_nominations.update_one(
        {"id": nom_id, "status": "em_votacao"},
        {"$set": {"status": new_status, "votos_favor": favor, "votos_total_base": base}},
    )
    if res.modified_count == 0:
        raise HTTPException(status_code=409, detail="Esta nomeação já foi apurada")
    await create_audit_log(
        current_user.id,
        "honorario_apurado",
        nom_id,
        request=request,
        details={"favor": favor, "contra": contra, "base": base, "aprovado": aprovado},
    )
    if aprovado:
        await _aplicar_honorario_eleito(nom, request, background_tasks)
        await notify_admins(
            "system",
            "Membro honorário eleito",
            f"«{nom['nominee_name']}» foi eleito membro honorário (2/3 — Art. 8.4).",
            link="/governanca/honorarios",
        )
    else:
        mesa = await members_of_orgao("mesa_ag")
        await notify_users(
            mesa,
            "system",
            "Votação de honorário apurada",
            f"A nomeação de «{nom['nominee_name']}» não atingiu os 2/3 ({favor}/{base}).",
            link="/governanca/honorarios",
        )
    return await db.honorarios_nominations.find_one({"id": nom_id}, {"_id": 0})


@router.post("/honorarios/{nom_id}/ligar-assembleia", response_model=HonorarioNomination)
async def ligar_honorario_assembleia(
    nom_id: str, data: HonorarioLigar, request: Request, current_user: User = Depends(get_current_user)
):
    """Reconciliação manual com a Assembleia (spec-voz §2.4, F6): a Mesa liga uma
    nomeação apurada à deliberação da AG que a ratificou. Apenas referência — não
    recria nem altera a votação 2/3 por poll (F5)."""
    if not _can_manage_honorarios(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Mesa da AG (ou admin) pode ligar a deliberação")
    nom = await db.honorarios_nominations.find_one({"id": nom_id}, {"_id": 0})
    if not nom:
        raise HTTPException(status_code=404, detail="Nomeação não encontrada")
    if nom["status"] not in ("eleito", "rejeitado"):
        raise HTTPException(status_code=409, detail="Só nomeações já apuradas podem ser ligadas a uma deliberação")
    # A assembleia tem de existir (evita ligar a um id inválido).
    if not await db.assembleias.find_one({"id": data.assembleia_id}, {"_id": 0, "id": 1}):
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    await db.honorarios_nominations.update_one(
        {"id": nom_id}, {"$set": {"assembleia_id": data.assembleia_id, "deliberacao_id": data.deliberacao_id}}
    )
    await create_audit_log(
        current_user.id,
        "honorario_ligado_assembleia",
        nom_id,
        request=request,
        details={"assembleia_id": data.assembleia_id, "deliberacao_id": data.deliberacao_id},
    )
    return await db.honorarios_nominations.find_one({"id": nom_id}, {"_id": 0})


async def _aplicar_honorario_eleito(
    nom: dict, request: Request, background_tasks: BackgroundTasks
) -> None:
    """Efeitos da eleição. O email é identificador universal:
    - nomeado interno (`nominee_user_id`) OU email de um sócio já existente →
      eleva (`member_category=honorario`);
    - email de pessoa nova → cria utilizador `pendente_convite` + convite
      (reusa send_invite_email). STOP: email real — spec §13 (validar inbox dev);
    - sem identificador → fica registado como eleito, sem conta.

    O envio do convite vai por BackgroundTask depois do CAS irrevogável: se o
    email falhar, o sócio fica criado/convidado em DB e o estado de governança
    persiste — o convite reenvia-se, não se perde a eleição num 500."""
    user_id = nom.get("nominee_user_id")
    if not user_id and nom.get("nominee_email"):
        existing = await db.users.find_one({"email": nom["nominee_email"]}, {"_id": 0, "id": 1})
        if existing:
            user_id = existing["id"]
    if user_id:
        await db.users.update_one({"id": user_id}, {"$set": {"member_category": "honorario"}})
        if not nom.get("nominee_user_id"):
            # Resolvido por email → liga a nomeação ao sócio elevado.
            await db.honorarios_nominations.update_one({"id": nom["id"]}, {"$set": {"nominee_user_id": user_id}})
        await notify_users(
            [user_id],
            "system",
            "Foi eleito membro honorário",
            "A Assembleia Geral elegeu-o membro honorário da ACCTA (Art. 8.4).",
            link="/dashboard",
        )
        return
    if not nom.get("nominee_email"):
        return  # sem identificador: fica registado como eleito, sem conta
    now = datetime.now(timezone.utc)
    new_user_id = str(uuid.uuid4())
    invite_token = secrets.token_urlsafe(32)
    user_doc = {
        "id": new_user_id,
        "name": nom["nominee_name"],
        "email": nom["nominee_email"],
        "password": "",
        "role": "socio",
        "status": "pendente_convite",
        "cargo": "socio",
        "orgao": None,
        "account_type": "member",
        "member_category": "honorario",
        "member_id": await next_member_id(),
        "license_number": "",
        "department": "",
        "phone_number": "",
        "admission_date": now.isoformat(),
        "privileges": [],
        "consent_data": False,
        "qr_code_hash": generate_qr_hash(new_user_id),
        "last_login_at": None,
        "created_at": now.isoformat(),
        "invite_token": invite_token,
        "invite_token_expires_at": (now + timedelta(days=_INVITE_TTL_DAYS)).isoformat(),
    }
    await db.users.insert_one(user_doc)
    # Liga a nomeação ao utilizador recém-criado.
    await db.honorarios_nominations.update_one({"id": nom["id"]}, {"$set": {"nominee_user_id": new_user_id}})
    origin = resolve_link_base(request)
    setup_url = f"{origin}/setup-account?token={invite_token}" if origin else ""
    # Fire-and-forget: o estado já persistiu; um email falhado não dá 500.
    background_tasks.add_task(send_invite_email, nom["nominee_name"], nom["nominee_email"], setup_url)
