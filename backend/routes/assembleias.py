"""Rotas da Assembleia Geral (spec-governanca-estatutaria §11).

Convocação, presenças/representação, quórum, deliberações e encerramento.
Leitura: qualquer membro autenticado. Escrita: Mesa da AG ou admin.

Quórum e maiorias são SEMPRE calculados pelos helpers de `governance.py`
(testados), nunca à mão. O poder de voto presente é a soma de `voting_power`
das presenças (1 por votante próprio + 1 por cada representado votante).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import get_current_user
from database import db
from governance import (
    is_voting_member,
    required_absolute_majority,
    required_quorum,
    required_three_quarters,
)
from helpers import create_audit_log, notify_all_active_users
from models import (
    Assembleia,
    AssembleiaCreate,
    AssembleiaDeliberacao,
    AssembleiaDeliberacaoCreate,
    AssembleiaPresenca,
    AssembleiaPresencaCreate,
    MAX_REPRESENTADOS,
    User,
)
from permissions import can_convene_assembleia, is_mesa_ag

router = APIRouter(prefix="/assembleias", tags=["assembleias"])

# Sócios reais (account_type member ou ausente — retro-compat).
_MEMBER_FILTER = {"$or": [{"account_type": "member"}, {"account_type": {"$exists": False}}]}
_VOTER_PROJ = {
    "_id": 0,
    "id": 1,
    "account_type": 1,
    "status": 1,
    "member_category": 1,
    "rights_suspended_until": 1,
    "cargo": 1,
    "name": 1,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(value: str):
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError, TypeError):
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _require_convene(current_user: User):
    if not can_convene_assembleia(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Mesa da AG ou admin podem gerir assembleias")


async def _count_voting_members(as_of: str | None = None) -> int:
    members = await db.users.find({"status": "ativo", **_MEMBER_FILTER}, _VOTER_PROJ).to_list(None)
    return sum(1 for m in members if is_voting_member(m, as_of))


async def _present_voting_power(assembleia_id: str) -> tuple[int, int]:
    rows = await db.assembleia_presencas.find({"assembleia_id": assembleia_id}, {"_id": 0, "voting_power": 1}).to_list(
        None
    )
    return len(rows), sum(int(r.get("voting_power", 0)) for r in rows)


@router.post("")
async def create_assembleia(request: Request, data: AssembleiaCreate, current_user: User = Depends(get_current_user)):
    """Convoca uma assembleia. Convocatória: >=10 dias (geral) ou >=20 dias
    (eleitoral). Extraordinária exige requerente_tipo."""
    _require_convene(current_user)

    data_dt = _parse_dt(data.data)
    if not data_dt:
        raise HTTPException(status_code=400, detail="Data da assembleia inválida (ISO 8601)")

    now = datetime.now(timezone.utc)
    antecedencia = data.antecedencia_dias if data.antecedencia_dias is not None else (data_dt - now).days
    minimo = 20 if data.tipo == "eleitoral" else 10
    if antecedencia < minimo:
        raise HTTPException(
            status_code=400,
            detail=f"Convocatória exige antecedência mínima de {minimo} dias (tem {antecedencia}).",
        )
    if data.tipo == "extraordinaria" and not data.requerente_tipo:
        raise HTTPException(status_code=400, detail="Assembleia extraordinária exige requerente_tipo")

    eligible = await _count_voting_members(now.isoformat())
    assembleia = Assembleia(
        tipo=data.tipo,
        titulo=data.titulo,
        data=data.data,
        local=data.local,
        convocada_por=current_user.id,
        convocatoria_em=now.isoformat(),
        antecedencia_dias=antecedencia,
        requerente_tipo=data.requerente_tipo,
        requerentes=data.requerentes,
        ordem_trabalhos=data.ordem_trabalhos,
        status="convocada",
        eligible_voters_count=eligible,
        chamada_actual=1,
        quorum_required=required_quorum(eligible, 1),
        quorum_met=False,
    )
    doc = assembleia.model_dump()
    await db.assembleias.insert_one(doc)
    await create_audit_log(
        current_user.id,
        "assembleia_convocada",
        doc["id"],
        request=request,
        details={"tipo": data.tipo, "data": data.data, "eligible_voters": eligible},
    )
    await notify_all_active_users(
        "system",
        "Assembleia convocada",
        f"{data.titulo} — {data.data} ({data.local}).",
        f"/assembleias/{doc['id']}",
    )
    return doc


@router.get("")
async def list_assembleias(current_user: User = Depends(get_current_user), status: str = "", tipo: str = ""):
    query: dict = {}
    if status:
        query["status"] = status
    if tipo:
        query["tipo"] = tipo
    rows = await db.assembleias.find(query, {"_id": 0}).sort("data", -1).to_list(200)
    return {"assembleias": rows}


@router.get("/{assembleia_id}")
async def get_assembleia(assembleia_id: str, current_user: User = Depends(get_current_user)):
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    present_count, present_power = await _present_voting_power(assembleia_id)
    return {**a, "present_count": present_count, "present_voting_power": present_power}


@router.get("/{assembleia_id}/quorum")
async def get_quorum(assembleia_id: str, current_user: User = Depends(get_current_user)):
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    eligible = a.get("eligible_voters_count", 0)
    present_count, present_power = await _present_voting_power(assembleia_id)
    quorum_1 = required_quorum(eligible, 1)
    quorum_2 = required_quorum(eligible, 2)
    return {
        "eligible_voters_count": eligible,
        "present_count": present_count,
        "present_voting_power": present_power,
        "chamada_actual": a.get("chamada_actual", 1),
        "quorum_required_primeira": quorum_1,
        "quorum_required_segunda": quorum_2,
        "quorum_required": a.get("quorum_required", quorum_1),
        # 1.ª chamada satisfeita?
        "quorum_met": present_power >= quorum_1,
        # mínimo legal para deliberar (1/3, 2.ª chamada)
        "pode_deliberar": present_power >= quorum_2,
    }


@router.post("/{assembleia_id}/presencas")
async def register_presenca(
    assembleia_id: str,
    request: Request,
    data: AssembleiaPresencaCreate,
    current_user: User = Depends(get_current_user),
):
    """Regista presença própria ou com representação. Um membro representa no
    máximo 3 outros; os titulares da Mesa da AG não representam (Estatutos)."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if a["status"] not in ("convocada", "em_curso"):
        raise HTTPException(status_code=400, detail="Assembleia não está aberta a presenças")

    if len(data.representados) > MAX_REPRESENTADOS:
        raise HTTPException(status_code=400, detail=f"Máximo de {MAX_REPRESENTADOS} representados")
    if data.user_id in data.representados:
        raise HTTPException(status_code=400, detail="Um membro não pode representar-se a si próprio")
    if len(set(data.representados)) != len(data.representados):
        raise HTTPException(status_code=400, detail="Representados duplicados")

    present = await db.users.find_one({"id": data.user_id}, _VOTER_PROJ)
    if not present:
        raise HTTPException(status_code=404, detail="Membro presente não encontrado")
    if present.get("account_type", "member") != "member":
        raise HTTPException(status_code=400, detail="Conta técnica não participa em assembleias")
    if data.representados and is_mesa_ag(present):
        raise HTTPException(status_code=400, detail="Titulares da Mesa da AG não podem representar outros membros")

    # Ninguém pode ser registado duas vezes (presente ou representado).
    existing = await db.assembleia_presencas.find(
        {"assembleia_id": assembleia_id}, {"_id": 0, "user_id": 1, "representados": 1}
    ).to_list(None)
    already: set[str] = set()
    for e in existing:
        already.add(e["user_id"])
        already.update(e.get("representados", []))
    conflict = ({data.user_id} | set(data.representados)) & already
    if conflict:
        raise HTTPException(status_code=409, detail=f"Já registado(s): {', '.join(sorted(conflict))}")

    reps = []
    if data.representados:
        reps = await db.users.find({"id": {"$in": data.representados}}, _VOTER_PROJ).to_list(None)
        if len(reps) != len(set(data.representados)):
            raise HTTPException(status_code=404, detail="Representado não encontrado")

    power = (1 if is_voting_member(present) else 0) + sum(1 for r in reps if is_voting_member(r))
    presenca = AssembleiaPresenca(
        assembleia_id=assembleia_id,
        user_id=data.user_id,
        tipo="representacao" if data.representados else "propria",
        representados=data.representados,
        voting_power=power,
        documento_id=data.documento_id,
        registado_por=current_user.id,
    )
    doc = presenca.model_dump()
    await db.assembleia_presencas.insert_one(doc)

    present_count, present_power = await _present_voting_power(assembleia_id)
    quorum_met = present_power >= a.get("quorum_required", 0)
    await db.assembleias.update_one({"id": assembleia_id}, {"$set": {"quorum_met": quorum_met}})
    await create_audit_log(
        current_user.id,
        "assembleia_presenca",
        assembleia_id,
        request=request,
        details={"user_id": data.user_id, "representados": data.representados, "voting_power": power},
    )
    return {
        "presenca": doc,
        "present_count": present_count,
        "present_voting_power": present_power,
        "quorum_met": quorum_met,
    }


@router.post("/{assembleia_id}/deliberacoes")
async def register_deliberacao(
    assembleia_id: str,
    request: Request,
    data: AssembleiaDeliberacaoCreate,
    current_user: User = Depends(get_current_user),
):
    """Regista uma deliberação e calcula a aprovação pela maioria aplicável:
    absoluta / 3-4 dos presentes / 3-4 do universo de membros."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if a["status"] not in ("convocada", "em_curso"):
        raise HTTPException(status_code=400, detail="A assembleia não está em curso")

    eligible = a.get("eligible_voters_count", 0)
    _, present_power = await _present_voting_power(assembleia_id)
    # Mínimo legal para deliberar = quórum de 2.ª chamada (1/3 do universo).
    if present_power < required_quorum(eligible, 2):
        raise HTTPException(status_code=400, detail="Sem quórum para deliberar")

    if data.tipo_maioria == "qualificada_3_4_universo":
        base = eligible
        threshold = required_three_quarters(base)
    elif data.tipo_maioria == "qualificada_3_4_presentes":
        base = present_power
        threshold = required_three_quarters(base)
    else:  # absoluta
        base = present_power
        threshold = required_absolute_majority(base)
    aprovado = data.votos_favor >= threshold

    delib = AssembleiaDeliberacao(
        assembleia_id=assembleia_id,
        ponto=data.ponto,
        descricao=data.descricao,
        tipo_maioria=data.tipo_maioria,
        base_calculo=base,
        votos_favor=data.votos_favor,
        votos_contra=data.votos_contra,
        abstencoes=data.abstencoes,
        threshold=threshold,
        aprovado=aprovado,
        source_article=data.source_article,
        registado_por=current_user.id,
    )
    doc = delib.model_dump()
    await db.assembleia_deliberacoes.insert_one(doc)
    if a["status"] == "convocada":
        await db.assembleias.update_one({"id": assembleia_id}, {"$set": {"status": "em_curso"}})
    await create_audit_log(
        current_user.id,
        "assembleia_deliberacao",
        assembleia_id,
        request=request,
        details={"ponto": data.ponto, "tipo_maioria": data.tipo_maioria, "aprovado": aprovado},
    )
    return doc


@router.get("/{assembleia_id}/deliberacoes")
async def list_deliberacoes(assembleia_id: str, current_user: User = Depends(get_current_user)):
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "id": 1})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    rows = (
        await db.assembleia_deliberacoes.find({"assembleia_id": assembleia_id}, {"_id": 0})
        .sort("created_at", 1)
        .to_list(None)
    )
    return {"deliberacoes": rows}


@router.post("/{assembleia_id}/encerrar")
async def encerrar_assembleia(
    assembleia_id: str,
    request: Request,
    acta_document_id: str = "",
    current_user: User = Depends(get_current_user),
):
    """Encerra a assembleia. A acta deve ser anexada até 30 dias depois."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if a["status"] in ("encerrada", "anulada"):
        raise HTTPException(status_code=400, detail="Assembleia já encerrada ou anulada")

    update = {"status": "encerrada", "encerrada_em": _now_iso()}
    if acta_document_id:
        update["acta_document_id"] = acta_document_id
    await db.assembleias.update_one({"id": assembleia_id}, {"$set": update})
    await create_audit_log(
        current_user.id,
        "assembleia_encerrada",
        assembleia_id,
        request=request,
        details={"acta_document_id": acta_document_id or None},
    )
    return {"message": "Assembleia encerrada.", "status": "encerrada"}
