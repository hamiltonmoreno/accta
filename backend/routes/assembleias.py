"""Rotas da Assembleia Geral (spec-governanca-estatutaria §11).

Convocação, presenças/representação, quórum, deliberações e encerramento.
Leitura: qualquer membro autenticado. Escrita: Mesa da AG ou admin.

Quórum e maiorias são SEMPRE calculados pelos helpers de `governance.py`
(testados), nunca à mão. O poder de voto presente é a soma de `voting_power`
das presenças (1 por votante próprio + 1 por cada representado votante).
"""

import asyncio
import json
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

import comunicados_service
from auth import _extract_token, get_current_user, get_user_from_token
from database import db
from governance import (
    is_voting_member,
    required_absolute_majority,
    required_quorum,
    required_three_quarters,
    required_two_thirds,
)
from helpers import create_audit_log, notify_all_active_users
from models import (
    Assembleia,
    AssembleiaCheckinRequest,
    AssembleiaCheckinScan,
    AssembleiaCreate,
    AssembleiaDeliberacao,
    AssembleiaDeliberacaoCreate,
    AssembleiaFaseUpdate,
    AssembleiaPresenca,
    AssembleiaPresencaCreate,
    MAX_REPRESENTADOS,
    User,
)
from permissions import can_convene_assembleia, is_mesa_ag

router = APIRouter(prefix="/assembleias", tags=["assembleias"])

# Janela de validade do código de check-in (reforço anti-proxy — D1).
CHECK_IN_CODE_TTL_MIN = 30
# Fases em que o check-in está aberto (não em fechada/encerramento).
_CHECKIN_OPEN_PHASES = ("checkin", "antes_ot", "ordem_trabalhos")

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


# Ordem linear das fases finas da sessão ao vivo (transições só pela Mesa).
PHASE_ORDER = ["fechada", "checkin", "antes_ot", "ordem_trabalhos", "encerramento"]


async def _bump_session(assembleia_id: str, extra: dict | None = None) -> int:
    """Incrementa `session_version` (base do SSE) e aplica `extra` na mesma escrita.

    Chamado por TODA a mutação de sessão. O valor exacto não importa para o SSE —
    só que mude; a leitura-e-escrita não é transaccional (ok para ~150 presentes,
    coerente com a simplicidade do resto do código)."""
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "session_version": 1})
    new_version = int((a or {}).get("session_version", 0)) + 1
    update = {"session_version": new_version}
    if extra:
        update.update(extra)
    await db.assembleias.update_one({"id": assembleia_id}, {"$set": update})
    return new_version


async def _session_snapshot(assembleia_id: str) -> dict | None:
    """Snapshot emitido pelo SSE (§2.2). Mínimo na F0 — fila/voto entram depois."""
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        return None
    eligible = a.get("eligible_voters_count", 0)
    present_count, present_power = await _present_voting_power(assembleia_id)
    required = required_quorum(eligible, a.get("chamada_actual", 1))
    return {
        "version": int(a.get("session_version", 0)),
        "phase": a.get("session_phase", "fechada"),
        "status": a.get("status"),
        "chamada": a.get("chamada_actual", 1),
        "current_item_id": a.get("current_item_id"),
        "quorum": {
            "required": required,
            "present_power": present_power,
            "present_count": present_count,
            "met": present_power >= required,
        },
    }


def _gen_check_in_code() -> str:
    """Código curto (6 chars), sem caracteres ambíguos, para self check-in."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sem I/O/0/1
    return "".join(secrets.choice(alphabet) for _ in range(6))


def _checkin_open(a: dict) -> bool:
    """A janela de check-in está aberta? (sessão a decorrer, fase não-fechada)."""
    return a.get("status") in ("convocada", "em_curso") and a.get("session_phase") in _CHECKIN_OPEN_PHASES


def _code_valid(a: dict, code: str | None) -> bool:
    """Valida o código de sessão (se a Mesa o exigir e o membro o enviar)."""
    if not code:
        return True  # código é reforço opcional (D1) — ausência não bloqueia
    expected = a.get("check_in_code")
    if not expected or code.strip().upper() != expected:
        return False
    expires = _parse_dt(a.get("check_in_code_expires_at") or "")
    return expires is None or expires > datetime.now(timezone.utc)


async def _existing_present_ids(assembleia_id: str) -> set[str]:
    """Todos os ids já presentes ou representados (anti-duplicado)."""
    rows = await db.assembleia_presencas.find(
        {"assembleia_id": assembleia_id}, {"_id": 0, "user_id": 1, "representados": 1}
    ).to_list(None)
    ids: set[str] = set()
    for r in rows:
        ids.add(r["user_id"])
        ids.update(r.get("representados", []))
    return ids


async def _finalize_checkin(a: dict, presenca: AssembleiaPresenca) -> dict:
    """Insere a presença, recalcula o quórum, faz bump de sessão (SSE) e devolve
    o snapshot de contagem. Partilhado por todos os caminhos de check-in."""
    doc = presenca.model_dump()
    await db.assembleia_presencas.insert_one(doc)
    present_count, present_power = await _present_voting_power(a["id"])
    quorum_met = present_power >= a.get("quorum_required", 0)
    await _bump_session(a["id"], {"quorum_met": quorum_met})
    return {
        "presenca": doc,
        "present_count": present_count,
        "present_voting_power": present_power,
        "quorum_met": quorum_met,
    }


@router.post("")
async def create_assembleia(
    request: Request,
    data: AssembleiaCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
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
        modo=data.modo,
        meeting_link=data.meeting_link,
        meeting_provider=data.meeting_provider,
        meeting_notes=data.meeting_notes,
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
    # Comunicado OFICIAL (in-app + email a todos os activos), fire-and-forget.
    background_tasks.add_task(
        comunicados_service.dispatch_oficial_auto,
        subject=f"Convocatória — {doc['titulo']}",
        body=(
            f"Fica convocada a {doc['titulo']}.\n\n"
            f"Data: {doc.get('data', '')}\n"
            "Consulte a convocatória e a ordem de trabalhos no Portal ACCTA."
        ),
        cta_label="Ver convocatória",
        cta_url=f"/assembleias/{doc['id']}",
        source_kind="assembleia_convocatoria",
        ref_id=doc["id"],
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
        method="mesa_manual",
        can_vote=is_voting_member(present),
        checked_in_at=_now_iso(),
    )
    result = await _finalize_checkin(a, presenca)
    await create_audit_log(
        current_user.id,
        "assembleia_presenca",
        assembleia_id,
        request=request,
        details={"user_id": data.user_id, "representados": data.representados, "voting_power": power},
    )
    return result


@router.post("/{assembleia_id}/checkin")
async def self_checkin(
    assembleia_id: str,
    request: Request,
    data: AssembleiaCheckinRequest,
    current_user: User = Depends(get_current_user),
):
    """Self check-in do próprio membro (online): clique em "Entrar na reunião" /
    QR da reunião / código de sessão. Atribuível e datado (= assinar a folha — D1).
    Representação NÃO entra aqui: é registada pela Mesa em `POST /presencas` (D9)."""
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if not _checkin_open(a):
        raise HTTPException(status_code=400, detail="O check-in não está aberto.")
    if not _code_valid(a, data.code):
        raise HTTPException(status_code=400, detail="Código de sessão inválido ou expirado.")

    present = await db.users.find_one({"id": current_user.id}, _VOTER_PROJ)
    if not present or present.get("account_type", "member") != "member":
        raise HTTPException(status_code=400, detail="Apenas sócios participam em assembleias.")
    if current_user.id in await _existing_present_ids(assembleia_id):
        raise HTTPException(status_code=409, detail="A sua presença já está registada.")

    can_vote = is_voting_member(present)
    presenca = AssembleiaPresenca(
        assembleia_id=assembleia_id,
        user_id=current_user.id,
        tipo="propria",
        voting_power=1 if can_vote else 0,
        registado_por=current_user.id,
        method=data.method,
        can_vote=can_vote,
        checked_in_at=_now_iso(),
    )
    result = await _finalize_checkin(a, presenca)
    await create_audit_log(
        current_user.id,
        "assembleia_checkin",
        assembleia_id,
        request=request,
        details={"method": data.method, "can_vote": can_vote},
    )
    return result


@router.post("/{assembleia_id}/checkin/scan")
async def checkin_scan(
    assembleia_id: str,
    request: Request,
    data: AssembleiaCheckinScan,
    current_user: User = Depends(get_current_user),
):
    """A Mesa lê o QR pessoal da carteira de um sócio (presencial) e regista a
    presença desse sócio. Resolve `qr_code_hash → user` (igual a `/stats/validate`)."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if not _checkin_open(a):
        raise HTTPException(status_code=400, detail="O check-in não está aberto.")

    present = await db.users.find_one({"qr_code_hash": data.qr_hash}, _VOTER_PROJ)
    if not present:
        raise HTTPException(status_code=404, detail="QR não corresponde a nenhum sócio.")
    if present.get("account_type", "member") != "member":
        raise HTTPException(status_code=400, detail="Conta técnica não participa em assembleias.")
    if present["id"] in await _existing_present_ids(assembleia_id):
        raise HTTPException(status_code=409, detail="Presença já registada.")

    can_vote = is_voting_member(present)
    presenca = AssembleiaPresenca(
        assembleia_id=assembleia_id,
        user_id=present["id"],
        tipo="propria",
        voting_power=1 if can_vote else 0,
        registado_por=current_user.id,
        method="qr_scan",
        can_vote=can_vote,
        checked_in_at=_now_iso(),
    )
    result = await _finalize_checkin(a, presenca)
    await create_audit_log(
        current_user.id,
        "assembleia_checkin_scan",
        assembleia_id,
        request=request,
        details={"user_id": present["id"], "can_vote": can_vote},
    )
    return result


@router.post("/{assembleia_id}/checkin/abrir")
async def abrir_checkin(
    assembleia_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """A Mesa abre a janela de check-in e gera/roda o código de sessão."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if a["status"] in ("encerrada", "anulada"):
        raise HTTPException(status_code=400, detail="Assembleia encerrada ou anulada.")

    code = _gen_check_in_code()
    expires = (datetime.now(timezone.utc) + timedelta(minutes=CHECK_IN_CODE_TTL_MIN)).isoformat()
    extra: dict = {"check_in_code": code, "check_in_code_expires_at": expires}
    if a.get("session_phase", "fechada") == "fechada":
        extra["session_phase"] = "checkin"
    if a["status"] == "convocada":
        extra["status"] = "em_curso"
    await _bump_session(assembleia_id, extra)
    await create_audit_log(current_user.id, "assembleia_checkin_abrir", assembleia_id, request=request, details={})
    await notify_all_active_users(
        "event",
        "Check-in aberto",
        f"O check-in da {a.get('titulo', 'Assembleia Geral')} está aberto.",
        f"/assembleias/{assembleia_id}",
    )
    return {
        "check_in_code": code,
        "check_in_code_expires_at": expires,
        "session_phase": extra.get("session_phase", a.get("session_phase", "fechada")),
    }


@router.post("/{assembleia_id}/checkin/fechar")
async def fechar_checkin(
    assembleia_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """A Mesa fecha a janela: invalida o código (a fase mantém-se)."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "id": 1})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    await _bump_session(assembleia_id, {"check_in_code": None, "check_in_code_expires_at": None})
    await create_audit_log(current_user.id, "assembleia_checkin_fechar", assembleia_id, request=request, details={})
    return {"message": "Check-in fechado; código invalidado."}


@router.post("/{assembleia_id}/segunda-convocatoria")
async def segunda_convocatoria(
    assembleia_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """A Mesa declara a 2.ª convocatória: o quórum exigido passa a 1/3 do universo."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if a["status"] in ("encerrada", "anulada"):
        raise HTTPException(status_code=400, detail="Assembleia encerrada ou anulada.")
    if a.get("chamada_actual", 1) == 2:
        raise HTTPException(status_code=400, detail="Já está em segunda convocatória.")

    eligible = a.get("eligible_voters_count", 0)
    new_required = required_quorum(eligible, 2)
    _, present_power = await _present_voting_power(assembleia_id)
    quorum_met = present_power >= new_required
    await _bump_session(assembleia_id, {"chamada_actual": 2, "quorum_required": new_required, "quorum_met": quorum_met})
    await create_audit_log(
        current_user.id,
        "assembleia_segunda_convocatoria",
        assembleia_id,
        request=request,
        details={"quorum_required": new_required},
    )
    return {
        "chamada_actual": 2,
        "quorum_required": new_required,
        "present_voting_power": present_power,
        "quorum_met": quorum_met,
    }


@router.get("/{assembleia_id}/presencas")
async def list_presencas(assembleia_id: str, current_user: User = Depends(get_current_user)):
    """Lista as presenças da assembleia (folha de presenças — só Mesa/admin)."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "id": 1})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    rows = (
        await db.assembleia_presencas.find({"assembleia_id": assembleia_id}, {"_id": 0})
        .sort("created_at", 1)
        .to_list(None)
    )
    return {"presencas": rows}


@router.post("/{assembleia_id}/deliberacoes")
async def register_deliberacao(
    assembleia_id: str,
    request: Request,
    data: AssembleiaDeliberacaoCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Regista uma deliberação e calcula a aprovação pela maioria aplicável:
    absoluta / 2-3 dos presentes / 3-4 dos presentes / 3-4 do universo de membros."""
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
    total_votes = data.votos_favor + data.votos_contra + data.abstencoes
    if total_votes > present_power:
        raise HTTPException(status_code=400, detail="Contagem de votos excede o poder de voto presente")

    if data.tipo_maioria == "qualificada_3_4_universo":
        base = eligible
        threshold = required_three_quarters(base)
    elif data.tipo_maioria == "qualificada_3_4_presentes":
        base = present_power
        threshold = required_three_quarters(base)
    elif data.tipo_maioria == "qualificada_2_3":
        # 2/3 dos presentes (eleição de membro honorário — Art. 8.4).
        base = present_power
        threshold = required_two_thirds(base)
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
    # Comunicado OFICIAL (in-app + email a todos os activos), fire-and-forget.
    background_tasks.add_task(
        comunicados_service.dispatch_oficial_auto,
        subject=f"Deliberações — {a.get('titulo', 'Assembleia Geral')}",
        body=(
            "Foram publicadas novas deliberações da Assembleia Geral.\n\n"
            "Consulte o detalhe e a ata no Portal ACCTA."
        ),
        cta_label="Ver deliberações",
        cta_url=f"/assembleias/{assembleia_id}",
        source_kind="assembleia_deliberacao",
        ref_id=doc["id"],
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


# ===== Camada "ao vivo" (spec-sessao-assembleia-ao-vivo) — F0 =====


@router.get("/{assembleia_id}/stream")
async def assembleia_stream(assembleia_id: str, request: Request):
    """SSE da sessão ao vivo: faz poll do snapshot a cada ~3s e emite quando
    `session_version` muda. Qualquer membro autenticado pode subscrever.

    Auth por cookie/header via `_extract_token` (igual ao `notifications/stream`);
    NÃO usa `?token=` (removido por segurança — token aparecia em logs de proxy)."""
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido")
    exists = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "id": 1})
    if not exists:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")

    async def event_generator():
        last_version = -1
        try:
            while True:
                if await request.is_disconnected():
                    break
                snap = await _session_snapshot(assembleia_id)
                if snap is None:
                    break
                if snap["version"] != last_version:
                    last_version = snap["version"]
                    yield f"data: {json.dumps(snap)}\n\n"
                await asyncio.sleep(3)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/{assembleia_id}/fase")
async def transicao_fase(
    assembleia_id: str,
    request: Request,
    data: AssembleiaFaseUpdate,
    current_user: User = Depends(get_current_user),
):
    """Transita a fase fina da sessão (só Mesa/admin). Ordem linear, sem recuar:
    fechada → checkin → antes_ot → ordem_trabalhos → encerramento."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if a["status"] in ("encerrada", "anulada"):
        raise HTTPException(status_code=400, detail="Assembleia encerrada ou anulada")

    current = a.get("session_phase", "fechada")
    target = data.session_phase
    if PHASE_ORDER.index(target) < PHASE_ORDER.index(current):
        raise HTTPException(status_code=400, detail=f"Não é possível recuar de '{current}' para '{target}'")

    extra: dict = {"session_phase": target}
    if data.current_item_id is not None:
        extra["current_item_id"] = data.current_item_id
    # Entrar em antes_ot regista a abertura (limite soft de 30 min — Art. 14).
    if target == "antes_ot" and not a.get("antes_ot_aberto_em"):
        extra["antes_ot_aberto_em"] = _now_iso()
    # A partir do check-in a assembleia está, de facto, em curso.
    if target != "fechada" and a["status"] == "convocada":
        extra["status"] = "em_curso"

    new_version = await _bump_session(assembleia_id, extra)
    await create_audit_log(
        current_user.id,
        "assembleia_fase",
        assembleia_id,
        request=request,
        details={"de": current, "para": target},
    )
    return {
        "session_phase": target,
        "session_version": new_version,
        "status": extra.get("status", a["status"]),
        "current_item_id": extra.get("current_item_id", a.get("current_item_id")),
    }
