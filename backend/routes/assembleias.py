"""Rotas da Assembleia Geral (spec-governanca-estatutaria §11).

Convocação, presenças/representação, quórum, deliberações e encerramento.
Leitura: qualquer membro autenticado. Escrita: Mesa da AG ou admin.

Quórum e maiorias são SEMPRE calculados pelos helpers de `governance.py`
(testados), nunca à mão. O poder de voto presente é a soma de `voting_power`
das presenças (1 por votante próprio + 1 por cada representado votante).
"""

import asyncio
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

import comunicados_service
from auth import SECRET_KEY, _extract_token, get_current_user, get_user_from_token
from database import cast_assembleia_ballot, db
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
    AssembleiaContagem,
    AssembleiaCreate,
    AssembleiaDeliberacao,
    AssembleiaDeliberacaoAbrir,
    AssembleiaDeliberacaoCreate,
    AssembleiaFaseUpdate,
    AssembleiaPresenca,
    AssembleiaPresencaCreate,
    AssembleiaDocumentoAttach,
    AssembleiaVoto,
    AssembleiaVotoBallot,
    AssembleiaVotoCast,
    AssembleiaVotoReceipt,
    Convidado,
    ConvidadoCreate,
    ExpedienteCreate,
    ExpedienteEntry,
    MAX_REPRESENTADOS,
    MocaoColocarVoto,
    MocaoCreate,
    MocaoSessao,
    PALAVRA_DURACOES,
    PalavraConvidadoCreate,
    PalavraCreate,
    PalavraIniciar,
    PalavraOrdenar,
    PalavraRequest,
    User,
)
from permissions import can_convene_assembleia, is_mesa_ag

router = APIRouter(prefix="/assembleias", tags=["assembleias"])

# Janela de validade do código de check-in (reforço anti-proxy — D1).
CHECK_IN_CODE_TTL_MIN = 30
# Fases em que o check-in está aberto (não em fechada/encerramento).
_CHECKIN_OPEN_PHASES = ("checkin", "antes_ot", "ordem_trabalhos")
# Antecedência mínima dos documentos da sessão (Art. 20). Anexos com <3 dias
# de antecedência são aceites mas marcados como tardios na auditoria.
MIN_DOC_ANTECEDENCIA_DIAS = 3

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


async def _is_present(assembleia_id: str, user_id: str) -> bool:
    """O membro tem presença própria registada nesta assembleia?"""
    p = await db.assembleia_presencas.find_one(
        {"assembleia_id": assembleia_id, "user_id": user_id}, {"_id": 0, "id": 1}
    )
    return p is not None


async def _session_snapshot(assembleia_id: str) -> dict | None:
    """Snapshot emitido pelo SSE (§2.2). Inclui quórum (F1) e fila de palavra (F2)."""
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        return None
    eligible = a.get("eligible_voters_count", 0)
    present_count, present_power = await _present_voting_power(assembleia_id)
    required = required_quorum(eligible, a.get("chamada_actual", 1))
    a_falar = await db.assembleia_palavra.find_one({"assembleia_id": assembleia_id, "status": "a_falar"}, {"_id": 0})
    fila = await db.assembleia_palavra.find(
        {"assembleia_id": assembleia_id, "status": "inscrito"}, {"_id": 0, "id": 1}
    ).to_list(None)
    # Deliberação aberta (F3): a consola da Mesa puxa o detalhe/tally por GET /{did}.
    open_delib = await db.assembleia_deliberacoes.find_one(
        {"assembleia_id": assembleia_id, "status": "aberta"}, {"_id": 0, "id": 1, "voting_mode": 1, "ponto": 1}
    )
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
        "speaking": {
            "current": (
                {
                    "qid": a_falar["id"],
                    "user_id": a_falar["user_id"],
                    "tipo": a_falar["tipo"],
                    "ends_at": a_falar.get("ends_at"),
                }
                if a_falar
                else None
            ),
            "queue_len": len(fila),
        },
        "open_vote": (
            {
                "deliberacao_id": open_delib["id"],
                "voting_mode": open_delib.get("voting_mode"),
                "ponto": open_delib.get("ponto"),
            }
            if open_delib
            else None
        ),
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
    try:
        await db.assembleia_presencas.insert_one(doc)
    except asyncpg.UniqueViolationError:
        # Corrida de dois check-ins simultâneos do mesmo sócio: o índice UNIQUE
        # (ux_assembpres_assemb_user) é o backstop atómico à guarda aplicacional.
        raise HTTPException(status_code=409, detail="A presença já está registada.")
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
    # O código de check-in é reforço anti-proxy (D1): só a Mesa/admin o vê. Expô-lo
    # a qualquer sócio anulava o mecanismo (review F0/F1, I4).
    if not can_convene_assembleia(current_user):
        a = {k: v for k, v in a.items() if k not in ("check_in_code", "check_in_code_expires_at")}
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


# ===== F2 — Fila de uso da palavra (spec-sessao-assembleia §4) =====


async def _get_palavra(assembleia_id: str, qid: str) -> dict:
    p = await db.assembleia_palavra.find_one({"id": qid, "assembleia_id": assembleia_id}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Pedido de palavra não encontrado")
    return p


@router.post("/{assembleia_id}/palavra")
async def pedir_palavra(
    assembleia_id: str,
    request: Request,
    data: PalavraCreate,
    current_user: User = Depends(get_current_user),
):
    """Um membro presente inscreve-se para usar a palavra (Art. 27)."""
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if a.get("status") != "em_curso":
        raise HTTPException(status_code=400, detail="A sessão não está a decorrer.")
    if not await _is_present(assembleia_id, current_user.id):
        raise HTTPException(status_code=403, detail="Tem de estar presente para pedir a palavra.")
    # Uma inscrição activa por membro (evita fila duplicada).
    ativo = await db.assembleia_palavra.find_one(
        {"assembleia_id": assembleia_id, "user_id": current_user.id, "status": {"$in": ["inscrito", "a_falar"]}},
        {"_id": 0, "id": 1},
    )
    if ativo:
        raise HTTPException(status_code=409, detail="Já tem um pedido de palavra activo.")

    p = PalavraRequest(
        assembleia_id=assembleia_id,
        item_id=data.item_id or a.get("current_item_id"),
        user_id=current_user.id,
        tipo=data.tipo,
        duration_limit_s=PALAVRA_DURACOES[data.tipo],
    )
    doc = p.model_dump()
    await db.assembleia_palavra.insert_one(doc)
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id, "palavra_pedida", assembleia_id, request=request, details={"tipo": data.tipo, "qid": doc["id"]}
    )
    return doc


@router.delete("/{assembleia_id}/palavra/{qid}")
async def retirar_palavra(
    assembleia_id: str,
    qid: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """O próprio retira o seu pedido; a Mesa pode retirar qualquer um."""
    p = await _get_palavra(assembleia_id, qid)
    if p["user_id"] != current_user.id and not can_convene_assembleia(current_user):
        raise HTTPException(status_code=403, detail="Só o próprio ou a Mesa podem retirar o pedido.")
    if p["status"] not in ("inscrito", "a_falar"):
        raise HTTPException(status_code=400, detail="O pedido já não está activo.")
    await db.assembleia_palavra.update_one({"id": qid}, {"$set": {"status": "retirado"}})
    await _bump_session(assembleia_id)
    await create_audit_log(current_user.id, "palavra_retirada", assembleia_id, request=request, details={"qid": qid})
    return {"id": qid, "status": "retirado"}


@router.post("/{assembleia_id}/palavra/{qid}/ordenar")
async def ordenar_palavra(
    assembleia_id: str,
    qid: str,
    request: Request,
    data: PalavraOrdenar,
    current_user: User = Depends(get_current_user),
):
    """A Mesa atribui a posição na fila."""
    _require_convene(current_user)
    await _get_palavra(assembleia_id, qid)
    await db.assembleia_palavra.update_one({"id": qid}, {"$set": {"ordem": data.ordem}})
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id, "palavra_ordenada", assembleia_id, request=request, details={"qid": qid, "ordem": data.ordem}
    )
    return {"id": qid, "ordem": data.ordem}


@router.post("/{assembleia_id}/palavra/{qid}/iniciar")
async def iniciar_palavra(
    assembleia_id: str,
    qid: str,
    request: Request,
    data: PalavraIniciar,
    current_user: User = Depends(get_current_user),
):
    """A Mesa concede a palavra: arranca o cronómetro (`ends_at`). Chamar de novo
    estende o tempo (recalcula `ends_at` a partir de agora)."""
    _require_convene(current_user)
    p = await _get_palavra(assembleia_id, qid)
    if p["status"] in ("concluido", "retirado", "negado"):
        raise HTTPException(status_code=400, detail="O pedido já foi encerrado.")
    dur = data.duration_s or p.get("duration_limit_s") or PALAVRA_DURACOES[p["tipo"]]
    now = datetime.now(timezone.utc)
    ends_at = (now + timedelta(seconds=dur)).isoformat()
    update = {
        "status": "a_falar",
        "started_at": p.get("started_at") or now.isoformat(),
        "ends_at": ends_at,
        "duration_limit_s": dur,
    }
    await db.assembleia_palavra.update_one({"id": qid}, {"$set": update})
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id, "palavra_iniciada", assembleia_id, request=request, details={"qid": qid, "duration_s": dur}
    )
    return {"id": qid, **update}


@router.post("/{assembleia_id}/palavra/{qid}/terminar")
async def terminar_palavra(
    assembleia_id: str,
    qid: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """A Mesa encerra a intervenção em curso."""
    _require_convene(current_user)
    p = await _get_palavra(assembleia_id, qid)
    if p["status"] != "a_falar":
        raise HTTPException(status_code=400, detail="Este pedido não está em uso da palavra.")
    ended_at = _now_iso()
    await db.assembleia_palavra.update_one({"id": qid}, {"$set": {"status": "concluido", "ended_at": ended_at}})
    await _bump_session(assembleia_id)
    await create_audit_log(current_user.id, "palavra_terminada", assembleia_id, request=request, details={"qid": qid})
    return {"id": qid, "status": "concluido", "ended_at": ended_at}


@router.get("/{assembleia_id}/palavra")
async def list_palavra(assembleia_id: str, current_user: User = Depends(get_current_user)):
    """Lista a fila (qualquer membro autenticado). Ordenada por `ordem` (Mesa) e,
    em empate/ausência, por ordem de inscrição."""
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "id": 1})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    rows = await db.assembleia_palavra.find({"assembleia_id": assembleia_id}, {"_id": 0}).to_list(None)
    rows.sort(key=lambda r: (r.get("ordem") if r.get("ordem") is not None else 10**9, r.get("requested_at", "")))
    return {"palavra": rows}


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


# ===== F3 — Modos de votação ao vivo (spec-sessao-assembleia §7) =====
#
# Ciclo ADITIVO ao one-shot `register_deliberacao` (que mantém o disparo de
# comunicado na criação): abrir → votar/registar-contagem → apurar. O comunicado
# oficial dispara SÓ no apurar (não duplicar). Modos:
#   - braco_no_ar: a Mesa regista o agregado (D5); sem votos individuais.
#   - nominal: cada votante presente vota; apura-se com o peso de voto da presença.
#   - secreto: par recibo/boletim anónimo (cast_assembleia_ballot); apoio
#     administrativo (D6). Para preservar o anonimato, o voto secreto é
#     UM-membro-UM-boletim (o peso de representação NÃO se aplica) — a base é a
#     contagem de votantes presentes não-excluídos. Confirmar com o Regimento.


def _voter_hash(deliberacao_id: str, user_id: str) -> str:
    """HMAC-SHA256 (igual às eleições): o recibo prova que o membro votou sem ser
    reversível para o user_id sem o segredo do servidor."""
    return hmac.new(SECRET_KEY.encode(), f"{deliberacao_id}:{user_id}".encode(), hashlib.sha256).hexdigest()


async def _get_deliberacao(assembleia_id: str, did: str) -> dict:
    d = await db.assembleia_deliberacoes.find_one({"id": did, "assembleia_id": assembleia_id}, {"_id": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Deliberação não encontrada")
    return d


async def _load_presencas(assembleia_id: str) -> list[dict]:
    return await db.assembleia_presencas.find(
        {"assembleia_id": assembleia_id}, {"_id": 0, "user_id": 1, "voting_power": 1, "can_vote": 1}
    ).to_list(None)


def _threshold_and_base(tipo_maioria: str, present_base: int, eligible: int) -> tuple[int, int]:
    """(base, threshold) pela maioria aplicável — mesmos helpers do one-shot."""
    if tipo_maioria == "qualificada_3_4_universo":
        return eligible, required_three_quarters(eligible)
    if tipo_maioria == "qualificada_3_4_presentes":
        return present_base, required_three_quarters(present_base)
    if tipo_maioria == "qualificada_2_3":
        return present_base, required_two_thirds(present_base)
    return present_base, required_absolute_majority(present_base)


@router.post("/{assembleia_id}/deliberacoes/abrir")
async def abrir_deliberacao(
    assembleia_id: str,
    request: Request,
    data: AssembleiaDeliberacaoAbrir,
    current_user: User = Depends(get_current_user),
):
    """A Mesa abre uma deliberação para votação ao vivo (status=aberta). NÃO
    dispara comunicado — isso só acontece no apuramento."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if a["status"] != "em_curso":
        raise HTTPException(status_code=400, detail="A sessão não está a decorrer.")
    eligible = a.get("eligible_voters_count", 0)
    _, present_power = await _present_voting_power(assembleia_id)
    if present_power < required_quorum(eligible, 2):
        raise HTTPException(status_code=400, detail="Sem quórum para deliberar")

    delib = AssembleiaDeliberacao(
        assembleia_id=assembleia_id,
        ponto=data.ponto,
        descricao=data.descricao,
        tipo_maioria=data.tipo_maioria,
        voting_mode=data.voting_mode,
        item_id=data.item_id or a.get("current_item_id"),
        subitem=data.subitem,
        conflitos_excluidos=data.conflitos_excluidos,
        status="aberta",
        source_article=data.source_article,
        registado_por=current_user.id,
    )
    doc = delib.model_dump()
    await db.assembleia_deliberacoes.insert_one(doc)
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id,
        "assembleia_deliberacao_abrir",
        assembleia_id,
        request=request,
        details={"deliberacao_id": doc["id"], "voting_mode": data.voting_mode, "ponto": data.ponto},
    )
    return doc


@router.post("/{assembleia_id}/deliberacoes/{did}/votar")
async def votar_deliberacao(
    assembleia_id: str,
    did: str,
    request: Request,
    data: AssembleiaVotoCast,
    current_user: User = Depends(get_current_user),
):
    """Um votante presente e não-excluído vota numa deliberação aberta
    (nominal ou secreto). O braço no ar não aceita votos individuais."""
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "id": 1, "status": 1})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if a.get("status") != "em_curso":
        raise HTTPException(status_code=400, detail="A sessão não está a decorrer.")
    d = await _get_deliberacao(assembleia_id, did)
    if d.get("status") != "aberta":
        raise HTTPException(status_code=400, detail="A deliberação não está aberta a votos.")
    mode = d.get("voting_mode", "braco_no_ar")
    if mode == "braco_no_ar":
        raise HTTPException(status_code=400, detail="Esta deliberação é por braço no ar (sem votos individuais).")

    pres = await db.assembleia_presencas.find_one(
        {"assembleia_id": assembleia_id, "user_id": current_user.id}, {"_id": 0, "can_vote": 1}
    )
    if not pres:
        raise HTTPException(status_code=403, detail="Tem de estar presente para votar.")
    if not pres.get("can_vote"):
        raise HTTPException(status_code=403, detail="Não tem direito de voto.")
    if current_user.id in set(d.get("conflitos_excluidos", [])):
        raise HTTPException(status_code=403, detail="Está excluído desta votação por conflito de interesses.")

    if mode == "nominal":
        existing = await db.assembleia_votos.find_one(
            {"deliberacao_id": did, "user_id": current_user.id}, {"_id": 0, "id": 1}
        )
        if existing:
            raise HTTPException(status_code=409, detail="Já votou nesta deliberação.")
        voto = AssembleiaVoto(
            deliberacao_id=did, assembleia_id=assembleia_id, user_id=current_user.id, escolha=data.escolha
        )
        try:
            await db.assembleia_votos.insert_one(voto.model_dump())
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Já votou nesta deliberação.")
        # Nominal: o sentido fica registado por nome — pode constar da auditoria.
        await create_audit_log(
            current_user.id,
            "assembleia_voto",
            assembleia_id,
            request=request,
            details={"deliberacao_id": did, "escolha": data.escolha},
        )
    else:  # secreto
        vh = _voter_hash(did, current_user.id)
        receipt = AssembleiaVotoReceipt(deliberacao_id=did, voter_hash=vh).model_dump()
        ballot = AssembleiaVotoBallot(deliberacao_id=did, escolha=data.escolha).model_dump()
        try:
            await cast_assembleia_ballot(did, vh, receipt, ballot)
        except ValueError:
            raise HTTPException(status_code=409, detail="Já votou nesta deliberação.")
        # Secreto: NUNCA registar o sentido ligado ao eleitor (só que votou).
        await create_audit_log(
            current_user.id,
            "assembleia_voto_secreto",
            assembleia_id,
            request=request,
            details={"deliberacao_id": did},
        )

    await _bump_session(assembleia_id)
    return {"deliberacao_id": did, "status": "registado", "voting_mode": mode}


@router.post("/{assembleia_id}/deliberacoes/{did}/registar-contagem")
async def registar_contagem(
    assembleia_id: str,
    did: str,
    request: Request,
    data: AssembleiaContagem,
    current_user: User = Depends(get_current_user),
):
    """A Mesa regista a contagem agregada do braço no ar (D5)."""
    _require_convene(current_user)
    await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "id": 1})
    d = await _get_deliberacao(assembleia_id, did)
    if d.get("status") != "aberta":
        raise HTTPException(status_code=400, detail="A deliberação não está aberta.")
    if d.get("voting_mode", "braco_no_ar") != "braco_no_ar":
        raise HTTPException(status_code=400, detail="Contagem agregada só se aplica ao braço no ar.")

    presencas = await _load_presencas(assembleia_id)
    excluded = set(d.get("conflitos_excluidos", []))
    present_power = sum(int(p.get("voting_power", 0)) for p in presencas)
    excluded_power = sum(int(p.get("voting_power", 0)) for p in presencas if p["user_id"] in excluded)
    present_base = present_power - excluded_power
    total = data.votos_favor + data.votos_contra + data.abstencoes
    if total > present_base:
        raise HTTPException(status_code=400, detail="Contagem excede o poder de voto presente (excluídos os conflitos).")

    update = {"votos_favor": data.votos_favor, "votos_contra": data.votos_contra, "abstencoes": data.abstencoes}
    await db.assembleia_deliberacoes.update_one({"id": did}, {"$set": update})
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id, "assembleia_contagem", assembleia_id, request=request, details={"deliberacao_id": did, **update}
    )
    return {"deliberacao_id": did, **update}


@router.post("/{assembleia_id}/deliberacoes/{did}/apurar")
async def apurar_deliberacao(
    assembleia_id: str,
    did: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """A Mesa fecha a votação e apura o resultado pela maioria aplicável. SÓ aqui
    se dispara o comunicado oficial (in-app + email a todos os activos)."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    d = await _get_deliberacao(assembleia_id, did)
    if d.get("status") != "aberta":
        raise HTTPException(status_code=400, detail="A deliberação já foi apurada ou anulada.")

    eligible = a.get("eligible_voters_count", 0)
    presencas = await _load_presencas(assembleia_id)
    excluded = set(d.get("conflitos_excluidos", []))
    mode = d.get("voting_mode", "braco_no_ar")

    if mode == "secreto":
        # Um-membro-um-boletim (anonimato): base = contagem de votantes presentes
        # não-excluídos; cada boletim conta 1 (peso de representação não se aplica).
        present_base = sum(1 for p in presencas if p.get("can_vote") and p["user_id"] not in excluded)
        ballots = await db.assembleia_voto_ballots.find(
            {"deliberacao_id": did}, {"_id": 0, "escolha": 1}
        ).to_list(None)
        favor = sum(1 for b in ballots if b.get("escolha") == "favor")
        contra = sum(1 for b in ballots if b.get("escolha") == "contra")
        abst = sum(1 for b in ballots if b.get("escolha") == "abstencao")
    else:
        power_by_user = {p["user_id"]: int(p.get("voting_power", 0)) for p in presencas}
        present_power = sum(power_by_user.values())
        excluded_power = sum(power_by_user.get(uid, 0) for uid in excluded)
        present_base = present_power - excluded_power
        if mode == "nominal":
            # Apura com o peso de voto da presença (representação incluída).
            votos = await db.assembleia_votos.find(
                {"deliberacao_id": did}, {"_id": 0, "user_id": 1, "escolha": 1}
            ).to_list(None)
            favor = sum(power_by_user.get(v["user_id"], 0) for v in votos if v.get("escolha") == "favor")
            contra = sum(power_by_user.get(v["user_id"], 0) for v in votos if v.get("escolha") == "contra")
            abst = sum(power_by_user.get(v["user_id"], 0) for v in votos if v.get("escolha") == "abstencao")
        else:  # braco_no_ar — agregado já registado pela Mesa
            favor = int(d.get("votos_favor", 0))
            contra = int(d.get("votos_contra", 0))
            abst = int(d.get("abstencoes", 0))

    base, threshold = _threshold_and_base(d["tipo_maioria"], present_base, eligible)
    aprovado = favor >= threshold
    update = {
        "status": "encerrada",
        "base_calculo": base,
        "votos_favor": favor,
        "votos_contra": contra,
        "abstencoes": abst,
        "threshold": threshold,
        "aprovado": aprovado,
        "apurado_em": _now_iso(),
    }
    await db.assembleia_deliberacoes.update_one({"id": did}, {"$set": update})
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id,
        "assembleia_deliberacao_apurar",
        assembleia_id,
        request=request,
        details={"deliberacao_id": did, "tipo_maioria": d["tipo_maioria"], "aprovado": aprovado, "voting_mode": mode},
    )
    # Comunicado OFICIAL — só no apuramento (não duplicar o one-shot), fire-and-forget.
    background_tasks.add_task(
        comunicados_service.dispatch_oficial_auto,
        subject=f"Deliberações — {a.get('titulo', 'Assembleia Geral')}",
        body=("Foi apurada uma deliberação da Assembleia Geral.\n\nConsulte o detalhe e a ata no Portal ACCTA."),
        cta_label="Ver deliberações",
        cta_url=f"/assembleias/{assembleia_id}",
        source_kind="assembleia_deliberacao",
        ref_id=did,
    )
    return {"id": did, **update}


@router.get("/{assembleia_id}/deliberacoes/{did}")
async def get_deliberacao(assembleia_id: str, did: str, current_user: User = Depends(get_current_user)):
    """Detalhe de uma deliberação. Em modo nominal a Mesa vê a lista de votos; em
    secreto expõe-se apenas quantos votaram (NUNCA o sentido por eleitor)."""
    d = await _get_deliberacao(assembleia_id, did)
    out = dict(d)
    mode = d.get("voting_mode", "braco_no_ar")
    if mode == "nominal":
        votos = await db.assembleia_votos.find(
            {"deliberacao_id": did}, {"_id": 0, "user_id": 1, "escolha": 1}
        ).to_list(None)
        out["votes_cast"] = len(votos)
        if can_convene_assembleia(current_user):
            out["votos"] = votos
    elif mode == "secreto":
        receipts = await db.assembleia_voto_receipts.find({"deliberacao_id": did}, {"_id": 0, "id": 1}).to_list(None)
        out["votes_cast"] = len(receipts)
    return out


# ===== F4 — Moções, requerimentos e recomendações (spec §5; Art. 6, 26) =====
#
# Qualquer membro presente submete. A Mesa coloca a voto criando uma deliberação
# do ciclo F3 (status=aberta). Requerimento (Art. 6, 26) salta a discussão
# (`votacao_imediata=True`) — a Mesa coloca-o a voto sem fase de discussão.


async def _get_mocao(assembleia_id: str, mid: str) -> dict:
    m = await db.assembleia_mocoes.find_one({"id": mid, "assembleia_id": assembleia_id}, {"_id": 0})
    if not m:
        raise HTTPException(status_code=404, detail="Moção não encontrada")
    return m


@router.post("/{assembleia_id}/mocoes")
async def submeter_mocao(
    assembleia_id: str,
    request: Request,
    data: MocaoCreate,
    current_user: User = Depends(get_current_user),
):
    """Um membro presente submete uma moção, requerimento ou recomendação."""
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if a.get("status") != "em_curso":
        raise HTTPException(status_code=400, detail="A sessão não está a decorrer.")
    if not await _is_present(assembleia_id, current_user.id):
        raise HTTPException(status_code=403, detail="Tem de estar presente para submeter.")

    m = MocaoSessao(
        assembleia_id=assembleia_id,
        item_id=data.item_id or a.get("current_item_id"),
        tipo=data.tipo,
        titulo=data.titulo,
        texto=data.texto,
        proposta_por=current_user.id,
        # Requerimento: Art. 6/26 — vai a voto imediato sem discussão.
        votacao_imediata=(data.tipo == "requerimento"),
    )
    doc = m.model_dump()
    await db.assembleia_mocoes.insert_one(doc)
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id,
        "mocao_submetida",
        assembleia_id,
        request=request,
        details={"mocao_id": doc["id"], "tipo": data.tipo},
    )
    return doc


@router.post("/{assembleia_id}/mocoes/{mid}/colocar-a-voto")
async def colocar_mocao_a_voto(
    assembleia_id: str,
    mid: str,
    request: Request,
    data: MocaoColocarVoto,
    current_user: User = Depends(get_current_user),
):
    """A Mesa aceita a moção e cria a deliberação (F3) — para `requerimento`
    isto acontece sem fase de discussão (a Mesa decide o timing)."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if a.get("status") != "em_curso":
        raise HTTPException(status_code=400, detail="A sessão não está a decorrer.")
    m = await _get_mocao(assembleia_id, mid)
    if m.get("status") not in ("submetida", "em_discussao"):
        raise HTTPException(status_code=400, detail="A moção já não pode ser colocada a voto.")
    eligible = a.get("eligible_voters_count", 0)
    _, present_power = await _present_voting_power(assembleia_id)
    if present_power < required_quorum(eligible, 2):
        raise HTTPException(status_code=400, detail="Sem quórum para deliberar")

    # Cria a deliberação ligada à moção. O título da moção alimenta o `ponto` e o
    # texto a `descricao`, para a ata ficar coerente.
    delib = AssembleiaDeliberacao(
        assembleia_id=assembleia_id,
        ponto=m["titulo"],
        descricao=m["texto"],
        tipo_maioria=data.tipo_maioria,
        voting_mode=data.voting_mode,
        item_id=m.get("item_id") or a.get("current_item_id"),
        subitem=data.subitem,
        conflitos_excluidos=data.conflitos_excluidos,
        status="aberta",
        source_article=m.get("source_article"),
        registado_por=current_user.id,
    )
    delib_doc = delib.model_dump()
    await db.assembleia_deliberacoes.insert_one(delib_doc)
    await db.assembleia_mocoes.update_one(
        {"id": mid}, {"$set": {"status": "em_votacao", "deliberacao_id": delib_doc["id"]}}
    )
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id,
        "mocao_a_voto",
        assembleia_id,
        request=request,
        details={
            "mocao_id": mid,
            "tipo": m["tipo"],
            "deliberacao_id": delib_doc["id"],
            "voting_mode": data.voting_mode,
            "votacao_imediata": m.get("votacao_imediata", False),
        },
    )
    return {"mocao_id": mid, "deliberacao_id": delib_doc["id"], "status": "em_votacao"}


@router.post("/{assembleia_id}/mocoes/{mid}/retirar")
async def retirar_mocao(
    assembleia_id: str,
    mid: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """O proponente ou a Mesa retira a moção (só enquanto não está em votação)."""
    m = await _get_mocao(assembleia_id, mid)
    if m["proposta_por"] != current_user.id and not can_convene_assembleia(current_user):
        raise HTTPException(status_code=403, detail="Só o proponente ou a Mesa podem retirar a moção.")
    if m.get("status") not in ("submetida", "em_discussao"):
        raise HTTPException(status_code=400, detail="A moção já não pode ser retirada.")
    await db.assembleia_mocoes.update_one({"id": mid}, {"$set": {"status": "retirada"}})
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id, "mocao_retirada", assembleia_id, request=request, details={"mocao_id": mid}
    )
    return {"mocao_id": mid, "status": "retirada"}


@router.get("/{assembleia_id}/mocoes")
async def list_mocoes(assembleia_id: str, current_user: User = Depends(get_current_user)):
    """Lista as moções da assembleia (qualquer membro autenticado)."""
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "id": 1})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    rows = (
        await db.assembleia_mocoes.find({"assembleia_id": assembleia_id}, {"_id": 0})
        .sort("created_at", 1)
        .to_list(None)
    )
    return {"mocoes": rows}


# ===== F5 — Período "antes da ordem de trabalhos" (spec §6; Art. 14) =====
#
# A fase `antes_ot` e o `antes_ot_aberto_em` já vêm da F0. O limite soft de 30 min
# é client-side (D4 — aviso visual; a Mesa encerra/estende). Aqui ficam só os
# registos de expediente: correspondência + votos de louvor/congratulação/pesar.


@router.post("/{assembleia_id}/expediente")
async def registar_expediente(
    assembleia_id: str,
    request: Request,
    data: ExpedienteCreate,
    current_user: User = Depends(get_current_user),
):
    """A Mesa regista correspondência ou votos de louvor/congratulação/pesar.
    Votos de louvor/etc são tipicamente aprovados por aclamação — o sinalizador
    `aprovado_por_aclamacao` regista isso na ata (não é uma deliberação F3)."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "id": 1})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    entry = ExpedienteEntry(
        assembleia_id=assembleia_id,
        tipo=data.tipo,
        texto=data.texto,
        aprovado_por_aclamacao=data.aprovado_por_aclamacao,
        registado_por=current_user.id,
    )
    doc = entry.model_dump()
    await db.assembleia_expediente.insert_one(doc)
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id,
        "expediente_registado",
        assembleia_id,
        request=request,
        details={"tipo": data.tipo, "expediente_id": doc["id"]},
    )
    return doc


@router.get("/{assembleia_id}/expediente")
async def list_expediente(assembleia_id: str, current_user: User = Depends(get_current_user)):
    """Lista o expediente registado (qualquer membro autenticado)."""
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "id": 1})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    rows = (
        await db.assembleia_expediente.find({"assembleia_id": assembleia_id}, {"_id": 0})
        .sort("created_at", 1)
        .to_list(None)
    )
    return {"expediente": rows}


# ===== F6 — Documentos da sessão + convidados (spec §8; Art. 20, 36) =====
#
# Documentos: lista `documentos: list[str]` (document_ids) no doc da assembleia,
# sem colecção nova. A validação Art. 20 ≥3 dias é soft — anexo tardio é aceite
# mas marcado `documento_anexado_tardio` na auditoria (configurável depois).
# Convidados: não-membros que assistem/intervêm; NÃO contam p/ quórum nem votam.


def _is_tardio(assembleia_data: str | None) -> bool:
    """O anexo é tardio (<MIN_DOC_ANTECEDENCIA_DIAS dias antes da sessão)?"""
    dt = _parse_dt(assembleia_data or "")
    if dt is None:
        return False
    delta = dt - datetime.now(timezone.utc)
    return delta.total_seconds() < MIN_DOC_ANTECEDENCIA_DIAS * 86400


@router.post("/{assembleia_id}/documentos")
async def anexar_documento(
    assembleia_id: str,
    request: Request,
    data: AssembleiaDocumentoAttach,
    current_user: User = Depends(get_current_user),
):
    """A Mesa anexa um documento à sessão. Anexar com <3 dias de antecedência
    (Art. 20) é aceite mas fica marcado como tardio na auditoria."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")

    doc = await db.documents.find_one({"id": data.document_id}, {"_id": 0, "id": 1, "title": 1})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    if data.document_id in (a.get("documentos") or []):
        raise HTTPException(status_code=409, detail="Documento já anexado a esta assembleia.")

    tardio = _is_tardio(a.get("data"))
    await db.assembleias.update_one({"id": assembleia_id}, {"$push": {"documentos": data.document_id}})
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id,
        "documento_anexado_tardio" if tardio else "documento_anexado",
        assembleia_id,
        request=request,
        details={"document_id": data.document_id, "tardio": tardio, "title": doc.get("title")},
    )
    return {"document_id": data.document_id, "tardio": tardio, "title": doc.get("title")}


@router.get("/{assembleia_id}/documentos")
async def list_documentos(assembleia_id: str, current_user: User = Depends(get_current_user)):
    """Lista os documentos anexados à sessão (qualquer membro autenticado).
    Resolve os ids contra `documents` para devolver título/url."""
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "documentos": 1})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    ids = a.get("documentos") or []
    if not ids:
        return {"documentos": []}
    docs = await db.documents.find({"id": {"$in": ids}}, {"_id": 0}).to_list(None)
    return {"documentos": docs}


@router.post("/{assembleia_id}/convidados")
async def adicionar_convidado(
    assembleia_id: str,
    request: Request,
    data: ConvidadoCreate,
    current_user: User = Depends(get_current_user),
):
    """A Mesa convida um não-membro (Art. 36). NÃO envia email automático —
    isso é stop condition em utilizadores reais."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "id": 1})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    conv = Convidado(
        assembleia_id=assembleia_id,
        nome=data.nome,
        email=data.email,
        can_speak=data.can_speak,
        motivo=data.motivo,
        invited_by=current_user.id,
    )
    doc = conv.model_dump()
    await db.assembleia_convidados.insert_one(doc)
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id,
        "convidado_adicionado",
        assembleia_id,
        request=request,
        details={"convidado_id": doc["id"], "can_speak": data.can_speak},
    )
    return doc


@router.get("/{assembleia_id}/convidados")
async def list_convidados(assembleia_id: str, current_user: User = Depends(get_current_user)):
    """Lista os convidados da sessão (Mesa/admin — gestão da sala)."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "id": 1})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    rows = (
        await db.assembleia_convidados.find({"assembleia_id": assembleia_id}, {"_id": 0})
        .sort("created_at", 1)
        .to_list(None)
    )
    return {"convidados": rows}


@router.post("/{assembleia_id}/convidados/{cid}/checkin")
async def checkin_convidado(
    assembleia_id: str,
    cid: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """A Mesa marca o convidado como presente (não conta p/ quórum nem vota)."""
    _require_convene(current_user)
    conv = await db.assembleia_convidados.find_one(
        {"id": cid, "assembleia_id": assembleia_id}, {"_id": 0, "id": 1}
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Convidado não encontrado")
    await db.assembleia_convidados.update_one({"id": cid}, {"$set": {"checked_in": True}})
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id, "convidado_checkin", assembleia_id, request=request, details={"convidado_id": cid}
    )
    return {"convidado_id": cid, "checked_in": True}


@router.post("/{assembleia_id}/palavra/convidado")
async def pedir_palavra_convidado(
    assembleia_id: str,
    request: Request,
    data: PalavraConvidadoCreate,
    current_user: User = Depends(get_current_user),
):
    """A Mesa põe um convidado autorizado (`can_speak=True` e presente) na fila
    de palavra (F2). Convidados não votam — só pedem a palavra através da Mesa."""
    _require_convene(current_user)
    a = await db.assembleias.find_one({"id": assembleia_id}, {"_id": 0, "id": 1, "status": 1, "current_item_id": 1})
    if not a:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada")
    if a.get("status") != "em_curso":
        raise HTTPException(status_code=400, detail="A sessão não está a decorrer.")
    conv = await db.assembleia_convidados.find_one(
        {"id": data.convidado_id, "assembleia_id": assembleia_id}, {"_id": 0}
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Convidado não encontrado")
    if not conv.get("can_speak"):
        raise HTTPException(status_code=400, detail="Este convidado não está autorizado a intervir.")
    if not conv.get("checked_in"):
        raise HTTPException(status_code=400, detail="O convidado tem de estar presente (check-in pela Mesa).")
    # Uma inscrição activa por convidado, igual aos membros.
    ativo = await db.assembleia_palavra.find_one(
        {
            "assembleia_id": assembleia_id,
            "convidado_id": data.convidado_id,
            "status": {"$in": ["inscrito", "a_falar"]},
        },
        {"_id": 0, "id": 1},
    )
    if ativo:
        raise HTTPException(status_code=409, detail="O convidado já tem um pedido de palavra activo.")

    p = PalavraRequest(
        assembleia_id=assembleia_id,
        item_id=a.get("current_item_id"),
        user_id=None,
        convidado_id=data.convidado_id,
        tipo=data.tipo,
        duration_limit_s=PALAVRA_DURACOES[data.tipo],
    )
    doc = p.model_dump()
    await db.assembleia_palavra.insert_one(doc)
    await _bump_session(assembleia_id)
    await create_audit_log(
        current_user.id,
        "palavra_pedida_convidado",
        assembleia_id,
        request=request,
        details={"convidado_id": data.convidado_id, "tipo": data.tipo, "qid": doc["id"]},
    )
    return doc


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
