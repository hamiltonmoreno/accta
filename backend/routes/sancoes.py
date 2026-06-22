"""Rotas do regime disciplinar (spec-governanca-estatutaria §13).

Advertência / multa / perda de direitos: competência da Direcção. Expulsão:
proposta pela Direcção, decidida pela AG (exige deliberação ligada). Comissão
de Inquérito de 3 elementos, prazo de 30 dias. Multa <= 3x quota mensal.
Dados disciplinares são sensíveis: ocultados a quem não tem permissão.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import get_current_user
from database import db
from helpers import create_audit_log, notify_users
from models import (
    COMISSAO_INQUERITO_MEMBROS,
    INQUERITO_PRAZO_DIAS,
    MULTA_MAX_QUOTAS,
    Sancao,
    SancaoComissao,
    SancaoCreate,
    SancaoDecidir,
    SancaoRecurso,
    Transaction,
    User,
)
from permissions import is_direcao

router = APIRouter(prefix="/sancoes", tags=["sancoes"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _close_active(history, fim: str) -> list:
    return [({**m, "fim": fim} if m.get("fim") is None else m) for m in (history or [])]


def _can_manage(user: User) -> bool:
    return user.role == "admin" or is_direcao(user)


def _require_disciplina(current_user: User):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Direcção ou admin gerem processos disciplinares")


async def _quota_amount() -> float:
    fs = await db.finance_settings.find_one({"id": "finance_settings"}, {"_id": 0, "quota_amount": 1})
    return float(fs["quota_amount"]) if fs and fs.get("quota_amount") else 2000.0


def _redact(s: dict) -> dict:
    """Vista limitada para o próprio visado (oculta inquérito/fundamentações)."""
    decisao = s.get("decisao") or None
    return {
        "id": s["id"],
        "user_id": s["user_id"],
        "tipo": s["tipo"],
        "status": s["status"],
        "motivo": s.get("motivo"),
        "perda_direitos_ate": s.get("perda_direitos_ate"),
        "created_at": s.get("created_at"),
        "decisao": {"aprovado": decisao.get("aprovado")} if decisao else None,
    }


async def _get_sancao(sancao_id: str) -> dict:
    s = await db.sancoes.find_one({"id": sancao_id}, {"_id": 0})
    if not s:
        raise HTTPException(status_code=404, detail="Processo disciplinar não encontrado")
    return s


@router.post("")
async def create_sancao(request: Request, data: SancaoCreate, current_user: User = Depends(get_current_user)):
    """Propõe uma sanção. Multa <= 3x quota; perda de direitos exige data-limite."""
    _require_disciplina(current_user)
    target = await db.users.find_one({"id": data.user_id}, {"_id": 0, "id": 1, "name": 1})
    if not target:
        raise HTTPException(status_code=404, detail="Membro visado não encontrado")

    if data.tipo == "multa":
        if data.multa_valor is None:
            raise HTTPException(status_code=400, detail="multa_valor é obrigatório para multa")
        limite = MULTA_MAX_QUOTAS * await _quota_amount()
        if data.multa_valor > limite:
            raise HTTPException(
                status_code=400,
                detail=f"A multa não pode exceder {MULTA_MAX_QUOTAS}x a quota mensal ({limite:.0f} CVE)",
            )
    if data.tipo == "perda_direitos" and not data.perda_direitos_ate:
        raise HTTPException(status_code=400, detail="perda_direitos_ate é obrigatório para perda de direitos")

    sancao = Sancao(
        user_id=data.user_id,
        tipo=data.tipo,
        motivo=data.motivo,
        artigo_violado=data.artigo_violado,
        status="proposta",
        proposta_por=current_user.id,
        multa_valor=data.multa_valor if data.tipo == "multa" else None,
        perda_direitos_ate=data.perda_direitos_ate if data.tipo == "perda_direitos" else None,
    )
    doc = sancao.model_dump()
    await db.sancoes.insert_one(doc)
    await create_audit_log(
        current_user.id,
        "sancao_proposta",
        doc["id"],
        request=request,
        details={"user_id": data.user_id, "tipo": data.tipo},
    )
    return doc


@router.get("")
async def list_sancoes(
    current_user: User = Depends(get_current_user), status: str = "", tipo: str = "", user_id: str = ""
):
    _require_disciplina(current_user)
    query: dict = {}
    if status:
        query["status"] = status
    if tipo:
        query["tipo"] = tipo
    if user_id:
        query["user_id"] = user_id
    rows = await db.sancoes.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {"sancoes": rows}


@router.get("/{sancao_id}")
async def get_sancao(sancao_id: str, current_user: User = Depends(get_current_user)):
    s = await _get_sancao(sancao_id)
    if _can_manage(current_user):
        return s
    if current_user.id == s["user_id"]:
        return _redact(s)
    raise HTTPException(status_code=403, detail="Sem permissão para ver este processo")


@router.post("/{sancao_id}/comissao")
async def set_comissao(
    sancao_id: str,
    request: Request,
    data: SancaoComissao,
    current_user: User = Depends(get_current_user),
):
    """Nomeia a Comissão de Inquérito (3 elementos) e abre prazo de 30 dias."""
    _require_disciplina(current_user)
    s = await _get_sancao(sancao_id)
    if s["status"] not in ("proposta", "inquerito"):
        raise HTTPException(status_code=400, detail="A comissão só se nomeia antes da decisão")
    if len(set(data.membros)) != COMISSAO_INQUERITO_MEMBROS:
        raise HTTPException(
            status_code=400, detail=f"A Comissão de Inquérito tem {COMISSAO_INQUERITO_MEMBROS} elementos distintos"
        )
    if s["user_id"] in data.membros:
        raise HTTPException(
            status_code=400, detail="O visado não pode integrar a Comissão de Inquérito que o investiga"
        )

    prazo = (datetime.now(timezone.utc) + timedelta(days=data.prazo_dias or INQUERITO_PRAZO_DIAS)).isoformat()
    await db.sancoes.update_one(
        {"id": sancao_id},
        {
            "$set": {
                "comissao_inquerito": [{"user_id": m} for m in data.membros],
                "inquerito_prazo": prazo,
                "conclusoes_document_id": data.conclusoes_document_id,
                "status": "inquerito",
            }
        },
    )
    await create_audit_log(
        current_user.id,
        "sancao_comissao",
        sancao_id,
        request=request,
        details={"membros": data.membros, "prazo": prazo},
    )
    return {"message": "Comissão de Inquérito nomeada.", "inquerito_prazo": prazo}


@router.post("/{sancao_id}/decidir")
async def decidir_sancao(
    sancao_id: str,
    request: Request,
    data: SancaoDecidir,
    current_user: User = Depends(get_current_user),
):
    """Regista a decisão. Expulsão exige assembleia_id + deliberação APROVADA da AG."""
    _require_disciplina(current_user)
    s = await _get_sancao(sancao_id)
    if s["status"] not in ("proposta", "inquerito", "recurso"):
        raise HTTPException(status_code=400, detail="A sanção não está num estado decidível")

    set_fields: dict = {}
    if s["tipo"] == "expulsao":
        if not (data.assembleia_id and data.deliberacao_id):
            raise HTTPException(status_code=400, detail="A expulsão exige deliberação da Assembleia Geral")
        delib = await db.assembleia_deliberacoes.find_one(
            {"id": data.deliberacao_id, "assembleia_id": data.assembleia_id}, {"_id": 0, "aprovado": 1}
        )
        if not delib:
            raise HTTPException(status_code=404, detail="Deliberação da AG não encontrada")
        if not delib.get("aprovado"):
            raise HTTPException(status_code=400, detail="A deliberação de expulsão não foi aprovada")
        set_fields["assembleia_id"] = data.assembleia_id
        set_fields["deliberacao_id"] = data.deliberacao_id

    set_fields["decisao"] = {
        "aprovado": data.aprovado,
        "fundamentacao": data.fundamentacao,
        "por": current_user.id,
        "em": _now_iso(),
    }
    set_fields["status"] = "decidida"
    await db.sancoes.update_one({"id": sancao_id}, {"$set": set_fields})
    await create_audit_log(
        current_user.id,
        "sancao_decidida",
        sancao_id,
        request=request,
        details={"aprovado": data.aprovado, "tipo": s["tipo"]},
    )
    return {"message": "Decisão registada.", "status": "decidida"}


@router.post("/{sancao_id}/recurso")
async def recurso_sancao(
    sancao_id: str,
    request: Request,
    data: SancaoRecurso,
    current_user: User = Depends(get_current_user),
):
    """Recurso do visado à AG (15 dias) para multa / perda de direitos."""
    s = await _get_sancao(sancao_id)
    if current_user.id != s["user_id"] and not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Só o visado pode recorrer da sua sanção")
    if s["tipo"] not in ("multa", "perda_direitos"):
        raise HTTPException(status_code=400, detail="Só multa ou perda de direitos têm recurso à AG")
    if s["status"] != "decidida":
        raise HTTPException(status_code=400, detail="Só se recorre de uma decisão")

    await db.sancoes.update_one(
        {"id": sancao_id},
        {
            "$set": {
                "recurso": {"fundamentacao": data.fundamentacao, "por": current_user.id, "em": _now_iso()},
                "status": "recurso",
            }
        },
    )
    await create_audit_log(current_user.id, "sancao_recurso", sancao_id, request=request, details={})
    return {"message": "Recurso submetido.", "status": "recurso"}


@router.post("/{sancao_id}/aplicar")
async def aplicar_sancao(sancao_id: str, request: Request, current_user: User = Depends(get_current_user)):
    """Aplica os efeitos: perda de direitos suspende voto/elegibilidade (mantém
    ativo); expulsão encerra mandato e inactiva a conta (exige deliberação)."""
    _require_disciplina(current_user)
    s = await _get_sancao(sancao_id)
    if s["status"] != "decidida":
        raise HTTPException(status_code=400, detail="A sanção só se aplica após a decisão")
    if not (s.get("decisao") or {}).get("aprovado"):
        raise HTTPException(status_code=400, detail="A decisão não foi aprovada")

    tipo = s["tipo"]
    if tipo == "expulsao" and not (s.get("assembleia_id") and s.get("deliberacao_id")):
        raise HTTPException(status_code=400, detail="A expulsão exige deliberação da Assembleia Geral")

    now = _now_iso()
    # Aplica primeiro os efeitos (idempotentes: perda_direitos grava valores
    # fixos; expulsão usa _close_active, que não fecha duas vezes um mandato já
    # fechado), e só DEPOIS marca "aplicada" via CAS. Assim, se uma escrita de
    # efeito falhar, o estado permanece "decidida" e a operação é re-tentável;
    # o CAS final (decidida->aplicada) garante exactamente-uma-vez sob
    # concorrência sem deixar a sanção "aplicada" sem os efeitos persistidos.
    if tipo == "perda_direitos":
        await db.users.update_one(
            {"id": s["user_id"]},
            {
                "$set": {
                    "rights_suspended_until": s.get("perda_direitos_ate"),
                    "rights_suspension_reason": s.get("motivo"),
                }
            },
        )
    elif tipo == "expulsao":
        user = await db.users.find_one({"id": s["user_id"]}, {"_id": 0, "cargo_history": 1})
        hist = _close_active((user or {}).get("cargo_history"), now)
        await db.users.update_one(
            {"id": s["user_id"]},
            {
                "$set": {
                    "status": "inativo",
                    "role": "socio",
                    "cargo": "socio",
                    "orgao": None,
                    "privileges": [],
                    "cargo_history": hist,
                }
            },
        )

    # Multa → caixa (spec-eventos-multas-caixa): cria a receita ANTES do CAS,
    # junto dos efeitos idempotentes. Guarda por sancao_id ⇒ exactly-once em
    # re-tentativa sequencial. Categoria "extraordinarias" (sem categorias novas).
    # `multa_tx_id` rastreia se ESTA chamada criou a receita, para o ramo de
    # compensação abaixo (janela de concorrência).
    multa_tx_id = None
    if tipo == "multa" and (s.get("multa_valor") or 0) > 0:
        existing_tx = await db.transactions.find_one(
            {"sancao_id": sancao_id, "type": "receita"}, {"_id": 0, "id": 1}
        )
        if not existing_tx:
            socio = await db.users.find_one({"id": s["user_id"]}, {"_id": 0, "name": 1})
            nome = (socio or {}).get("name")
            multa_tx = Transaction(
                type="receita",
                category="extraordinarias",
                description=f"Multa - {nome}" if nome else "Multa",
                amount=float(s["multa_valor"]),
                date=now,
                sancao_id=sancao_id,
                user_id=s["user_id"],
                created_by=current_user.id,
            )
            await db.transactions.insert_one(multa_tx.model_dump())
            multa_tx_id = multa_tx.id

    # CAS final: só agora (efeitos já persistidos) marca "aplicada". Se outra
    # chamada concorrente já fechou a transição, modified_count==0 e abortamos
    # sem duplicar a notificação/audit (os efeitos idempotentes já correram).
    claimed = await db.sancoes.update_one(
        {"id": sancao_id, "status": "decidida"},
        {"$set": {"status": "aplicada", "aplicada_em": now}},
    )
    if claimed.modified_count == 0:
        # Perdemos a corrida do CAS: se ESTA chamada inseriu a receita (janela de
        # concorrência em que o find_one não viu a inserção da chamada vencedora),
        # remove-a para não deixar uma receita de multa duplicada no caixa.
        if multa_tx_id:
            await db.transactions.delete_one({"id": multa_tx_id})
        raise HTTPException(status_code=409, detail="A sanção já foi aplicada.")

    await create_audit_log(
        current_user.id,
        "sancao_aplicada",
        sancao_id,
        request=request,
        details={"user_id": s["user_id"], "tipo": tipo},
    )
    await notify_users(
        [s["user_id"]],
        "system",
        "Sanção disciplinar aplicada",
        "Foi aplicada uma sanção ao seu processo. Consulte os detalhes no perfil.",
        "/perfil",
    )
    return {"message": "Sanção aplicada.", "status": "aplicada"}


# GET /api/users/{id}/sancoes — exposto pelo router de users (spec §13), reusa
# `_redact` e `_can_manage` daqui para a vista do próprio visado.
