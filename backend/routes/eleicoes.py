"""Rotas de eleições (spec-governanca-estatutaria §12).

Ciclo: preparação → candidaturas → (campanha) → votação → apuramento →
proclamação. Voto SECRETO: o recibo do eleitor (HMAC) e o boletim são gravados
em colecções separadas, numa transação atómica (`database.cast_ballot`); o
boletim nunca contém `user_id` nem `voter_hash`.

Escrita: Mesa da AG, Comissão Eleitoral/Mesa de Voto ou admin. Voto: eleitores
(is_voting_member). Proclamação cria mandatos via serviço interno comum.
"""

import hashlib
import hmac
from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

import comunicados_service
from auth import SECRET_KEY, get_current_user
from database import cast_ballot, db
from governance import (
    cargo_label,
    election_slots,
    orgao_of_cargo,
    privileges_for_cargo,
    role_for_cargo,
)
from helpers import create_audit_log, notify_users
from models import (
    CargoMandate,
    Eleicao,
    EleicaoBallot,
    EleicaoCreate,
    EleicaoLista,
    EleicaoListaCreate,
    EleicaoListaValidar,
    EleicaoVoterReceipt,
    VOTO_BRANCO,
    VOTO_NULO,
    VotarRequest,
    VotoCorrespondenciaRequest,
    User,
)
from permissions import is_eligible_for_office, is_mesa_ag, is_voting_member

router = APIRouter(prefix="/eleicoes", tags=["eleicoes"])

_MEMBER_FILTER = {"$or": [{"account_type": "member"}, {"account_type": {"$exists": False}}]}
_VOTER_PROJ = {
    "_id": 0,
    "id": 1,
    "account_type": 1,
    "status": 1,
    "member_category": 1,
    "rights_suspended_until": 1,
    "name": 1,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _voter_hash(eleicao_id: str, user_id: str) -> str:
    """HMAC-SHA256 — nunca um hash simples (spec §7), para que o recibo não seja
    reversível para o user_id sem o segredo do servidor."""
    return hmac.new(SECRET_KEY.encode(), f"{eleicao_id}:{user_id}".encode(), hashlib.sha256).hexdigest()


def _close_active(history, fim: str) -> list:
    return [({**m, "fim": fim} if m.get("fim") is None else m) for m in (history or [])]


def _is_comissao(user: User, eleicao: dict) -> bool:
    uid = user.id
    return uid in (eleicao.get("comissao_eleitoral") or []) or uid in (eleicao.get("mesa_voto") or [])


def _require_create(current_user: User):
    if not (current_user.role == "admin" or is_mesa_ag(current_user)):
        raise HTTPException(status_code=403, detail="Apenas a Mesa da AG ou admin podem criar eleições")


def _require_manage(current_user: User, eleicao: dict):
    if current_user.role == "admin" or is_mesa_ag(current_user) or _is_comissao(current_user, eleicao):
        return
    raise HTTPException(status_code=403, detail="Sem permissão para gerir esta eleição")


async def _get_eleicao(eleicao_id: str) -> dict:
    e = await db.eleicoes.find_one({"id": eleicao_id}, {"_id": 0})
    if not e:
        raise HTTPException(status_code=404, detail="Eleição não encontrada")
    return e


# --------------------------------------------------------------------------- #
# Eleição
# --------------------------------------------------------------------------- #


@router.post("")
async def create_eleicao(request: Request, data: EleicaoCreate, current_user: User = Depends(get_current_user)):
    """Cria a eleição já em fase de candidaturas (a criação abre candidaturas)."""
    _require_create(current_user)
    eleicao = Eleicao(
        ano=data.ano,
        mandato_inicio=data.mandato_inicio,
        mandato_fim=data.mandato_fim,
        status="candidaturas",
        calendario=data.calendario,
        assembleia_id=data.assembleia_id,
        comissao_eleitoral=data.comissao_eleitoral,
        mesa_voto=data.mesa_voto,
        modo_votacao=data.modo_votacao,
        direcao_titulares=data.direcao_titulares,
        created_by=current_user.id,
    )
    doc = eleicao.model_dump()
    await db.eleicoes.insert_one(doc)
    await create_audit_log(
        current_user.id,
        "eleicao_criada",
        doc["id"],
        request=request,
        details={"ano": data.ano, "direcao_titulares": data.direcao_titulares},
    )
    return doc


@router.get("")
async def list_eleicoes(current_user: User = Depends(get_current_user), status: str = ""):
    query: dict = {}
    if status:
        query["status"] = status
    rows = await db.eleicoes.find(query, {"_id": 0}).sort("ano", -1).to_list(200)
    return {"eleicoes": rows}


@router.get("/{eleicao_id}")
async def get_eleicao(eleicao_id: str, current_user: User = Depends(get_current_user)):
    e = await _get_eleicao(eleicao_id)
    e["slots"] = election_slots(e.get("direcao_titulares", 5))
    return e


# --------------------------------------------------------------------------- #
# Listas
# --------------------------------------------------------------------------- #


@router.post("/{eleicao_id}/listas")
async def submit_lista(
    eleicao_id: str,
    request: Request,
    data: EleicaoListaCreate,
    current_user: User = Depends(get_current_user),
):
    """Submete uma lista. Tem de preencher TODOS os slots; sem candidato
    repetido; membros da Comissão/Mesa de Voto não podem ser candidatos; todos
    os candidatos têm de ser elegíveis."""
    eleicao = await _get_eleicao(eleicao_id)
    if eleicao["status"] != "candidaturas":
        raise HTTPException(status_code=400, detail="As candidaturas não estão abertas")

    slots = election_slots(eleicao.get("direcao_titulares", 5))
    slot_by_key = {s["slot_key"]: s for s in slots}
    given_keys = {c.get("slot_key") for c in data.candidatos}
    if given_keys != set(slot_by_key):
        raise HTTPException(status_code=400, detail="Lista incompleta: preencha todos os slots")

    user_ids = [c.get("user_id") for c in data.candidatos]
    if any(not uid for uid in user_ids):
        raise HTTPException(status_code=400, detail="Candidato sem user_id")
    if len(set(user_ids)) != len(user_ids):
        raise HTTPException(status_code=400, detail="Um candidato não pode ocupar mais de um slot")

    barred = set(eleicao.get("comissao_eleitoral") or []) | set(eleicao.get("mesa_voto") or [])
    overlap = barred & set(user_ids)
    if overlap:
        raise HTTPException(status_code=400, detail="Comissão Eleitoral / Mesa de Voto não podem ser candidatos")

    candidatos_users = await db.users.find({"id": {"$in": user_ids}}, _VOTER_PROJ).to_list(None)
    by_id = {u["id"]: u for u in candidatos_users}
    for uid in user_ids:
        u = by_id.get(uid)
        if not u or not is_eligible_for_office(u):
            raise HTTPException(status_code=400, detail=f"Candidato inelegível: {uid}")

    # Normaliza cada candidato a partir do slot (não confia no cliente).
    candidatos = []
    for c in data.candidatos:
        s = slot_by_key[c["slot_key"]]
        candidatos.append(
            {
                "slot_key": s["slot_key"],
                "cargo": s["cargo"],
                "orgao": s["orgao"],
                "suplente": s["suplente"],
                "seat_index": s["seat_index"],
                "user_id": c["user_id"],
            }
        )

    lista = EleicaoLista(
        eleicao_id=eleicao_id,
        letra=data.letra.upper(),
        nome=data.nome,
        candidatos=candidatos,
        programa_document_id=data.programa_document_id,
        estado="submetida",
        submetida_por=current_user.id,
    )
    doc = lista.model_dump()
    existing = await db.eleicao_listas.find_one({"eleicao_id": eleicao_id, "letra": doc["letra"]}, {"_id": 0, "id": 1})
    if existing:
        raise HTTPException(status_code=409, detail=f"Já existe a lista {doc['letra']}")
    await db.eleicao_listas.insert_one(doc)
    await create_audit_log(
        current_user.id,
        "eleicao_lista_submetida",
        doc["id"],
        request=request,
        details={"eleicao_id": eleicao_id, "letra": doc["letra"]},
    )
    return doc


@router.get("/{eleicao_id}/listas")
async def list_listas(eleicao_id: str, current_user: User = Depends(get_current_user)):
    await _get_eleicao(eleicao_id)
    rows = await db.eleicao_listas.find({"eleicao_id": eleicao_id}, {"_id": 0}).to_list(None)
    return {"listas": rows}


@router.post("/{eleicao_id}/listas/{lista_id}/validar")
async def validar_lista(
    eleicao_id: str,
    lista_id: str,
    request: Request,
    data: EleicaoListaValidar,
    current_user: User = Depends(get_current_user),
):
    eleicao = await _get_eleicao(eleicao_id)
    _require_manage(current_user, eleicao)
    if eleicao["status"] != "candidaturas":
        raise HTTPException(status_code=400, detail="As candidaturas não estão abertas")
    lista = await db.eleicao_listas.find_one({"id": lista_id, "eleicao_id": eleicao_id}, {"_id": 0})
    if not lista:
        raise HTTPException(status_code=404, detail="Lista não encontrada")
    estado = "aceite" if data.aceite else "rejeitada"
    await db.eleicao_listas.update_one(
        {"id": lista_id}, {"$set": {"estado": estado, "rejeicao_motivo": data.motivo if not data.aceite else None}}
    )
    await create_audit_log(
        current_user.id,
        "eleicao_lista_validada",
        lista_id,
        request=request,
        details={"eleicao_id": eleicao_id, "estado": estado, "motivo": data.motivo},
    )
    return {"message": f"Lista {lista['letra']} {estado}.", "estado": estado}


# --------------------------------------------------------------------------- #
# Votação
# --------------------------------------------------------------------------- #


@router.post("/{eleicao_id}/abrir-votacao")
async def abrir_votacao(
    eleicao_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    eleicao = await _get_eleicao(eleicao_id)
    _require_manage(current_user, eleicao)
    if eleicao["status"] not in ("candidaturas", "campanha"):
        raise HTTPException(status_code=400, detail="A votação não pode ser aberta neste estado")
    aceites = await db.eleicao_listas.count_documents({"eleicao_id": eleicao_id, "estado": "aceite"})
    if aceites < 1:
        raise HTTPException(status_code=400, detail="Não há listas aceites para votar")
    await db.eleicoes.update_one({"id": eleicao_id}, {"$set": {"status": "votacao"}})
    await create_audit_log(current_user.id, "eleicao_votacao_aberta", eleicao_id, request=request, details={})
    # Comunicado OFICIAL (in-app + email a todos os activos), fire-and-forget.
    ano = eleicao.get("ano")
    titulo = f"Eleições {ano}" if ano else "Eleições"
    background_tasks.add_task(
        comunicados_service.dispatch_oficial_auto,
        subject=f"Abertura de votação — {titulo}",
        body=(
            "A votação está aberta. A sua participação é importante.\n\n"
            "Aceda ao Portal ACCTA para votar dentro do prazo."
        ),
        cta_label="Votar agora",
        cta_url=f"/eleicoes/{eleicao_id}",
        source_kind="eleicao_abertura",
        ref_id=eleicao_id,
    )
    return {"message": "Votação aberta.", "status": "votacao"}


async def _validate_voto(eleicao_id: str, voto: str):
    if voto in (VOTO_BRANCO, VOTO_NULO):
        return
    lista = await db.eleicao_listas.find_one({"id": voto, "eleicao_id": eleicao_id}, {"_id": 0, "estado": 1})
    if not lista or lista.get("estado") != "aceite":
        raise HTTPException(status_code=400, detail="Lista inválida ou não aceite")


@router.post("/{eleicao_id}/votar")
async def votar(
    eleicao_id: str,
    request: Request,
    data: VotarRequest,
    current_user: User = Depends(get_current_user),
):
    """Voto digital do próprio eleitor. Recibo + boletim atómicos; o boletim não
    tem ligação ao eleitor."""
    eleicao = await _get_eleicao(eleicao_id)
    if eleicao["status"] != "votacao":
        raise HTTPException(status_code=400, detail="A votação não está aberta")
    if not is_voting_member(current_user):
        raise HTTPException(status_code=403, detail="Não é eleitor (sócio votante activo)")
    await _validate_voto(eleicao_id, data.voto)

    vh = _voter_hash(eleicao_id, current_user.id)
    receipt = EleicaoVoterReceipt(eleicao_id=eleicao_id, voter_hash=vh, modo="digital").model_dump()
    ballot = EleicaoBallot(eleicao_id=eleicao_id, voto=data.voto, modo="digital").model_dump()
    try:
        await cast_ballot(eleicao_id, vh, receipt, ballot)
    except ValueError:
        raise HTTPException(status_code=409, detail="Já votou nesta eleição")
    # Auditoria regista PARTICIPAÇÃO, nunca o sentido de voto.
    await create_audit_log(
        current_user.id, "eleicao_voto_registado", eleicao_id, request=request, details={"modo": "digital"}
    )
    return {"message": "Voto registado."}


@router.post("/{eleicao_id}/voto-correspondencia")
async def voto_correspondencia(
    eleicao_id: str,
    request: Request,
    data: VotoCorrespondenciaRequest,
    current_user: User = Depends(get_current_user),
):
    """Voto por correspondência registado pela Comissão/Mesa/admin, com
    justificação obrigatória."""
    eleicao = await _get_eleicao(eleicao_id)
    _require_manage(current_user, eleicao)
    if eleicao["status"] != "votacao":
        raise HTTPException(status_code=400, detail="A votação não está aberta")
    voter = await db.users.find_one({"id": data.user_id}, _VOTER_PROJ)
    if not voter:
        raise HTTPException(status_code=404, detail="Eleitor não encontrado")
    if not is_voting_member(voter):
        raise HTTPException(status_code=400, detail="O membro indicado não é eleitor")
    await _validate_voto(eleicao_id, data.voto)

    vh = _voter_hash(eleicao_id, data.user_id)
    receipt = EleicaoVoterReceipt(
        eleicao_id=eleicao_id,
        voter_hash=vh,
        modo="correspondencia",
        justificacao=data.justificacao,
        registado_por=current_user.id,
    ).model_dump()
    ballot = EleicaoBallot(eleicao_id=eleicao_id, voto=data.voto, modo="correspondencia").model_dump()
    try:
        await cast_ballot(eleicao_id, vh, receipt, ballot)
    except ValueError:
        raise HTTPException(status_code=409, detail="Este eleitor já votou")
    await create_audit_log(
        current_user.id,
        "eleicao_voto_correspondencia",
        eleicao_id,
        request=request,
        details={"modo": "correspondencia"},
    )
    return {"message": "Voto por correspondência registado."}


# --------------------------------------------------------------------------- #
# Apuramento e proclamação
# --------------------------------------------------------------------------- #


@router.post("/{eleicao_id}/apurar")
async def apurar(eleicao_id: str, request: Request, current_user: User = Depends(get_current_user)):
    """Apura os boletins. Brancos/nulos excluídos dos votos válidos; maioria
    simples vence; empate marca nova eleição em 15 dias."""
    eleicao = await _get_eleicao(eleicao_id)
    _require_manage(current_user, eleicao)
    if eleicao["status"] != "votacao":
        raise HTTPException(status_code=400, detail="Só se apura após a votação")

    ballots = await db.eleicao_ballots.find({"eleicao_id": eleicao_id}, {"_id": 0, "voto": 1}).to_list(None)
    counts = Counter(b.get("voto") for b in ballots)
    brancos = counts.pop(VOTO_BRANCO, 0)
    nulos = counts.pop(VOTO_NULO, 0)
    total_validos = sum(counts.values())

    vencedora = None
    empate = False
    if counts:
        top = max(counts.values())
        leaders = [lid for lid, v in counts.items() if v == top]
        if len(leaders) == 1:
            vencedora = leaders[0]
        else:
            empate = True

    resultado = {
        "por_lista": dict(counts),
        "brancos": brancos,
        "nulos": nulos,
        "total_validos": total_validos,
        "total_boletins": len(ballots),
        "vencedora": vencedora,
        "empate": empate,
    }
    if empate:
        resultado["nova_eleicao_ate"] = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()

    await db.eleicoes.update_one({"id": eleicao_id}, {"$set": {"status": "apurada", "resultado": resultado}})
    await create_audit_log(
        current_user.id,
        "eleicao_apurada",
        eleicao_id,
        request=request,
        details={"vencedora": vencedora, "empate": empate, "total_validos": total_validos},
    )
    return resultado


async def _proclaim_list(eleicao: dict, lista: dict, by_id: str) -> tuple[str, list[dict]]:
    """Serviço comum de criação de mandatos na posse. Cessantes (titulares dos
    cargos eleitos que não foram reeleitos) são encerrados aqui — na posse, não
    no apuramento. Suplentes ficam registados sem alterar o cargo activo.
    Devolve (posse_iso, proclaimed) para o chamador reutilizar o mesmo instante."""
    posse = _now_iso()
    titulares = [c for c in lista.get("candidatos", []) if not c.get("suplente")]
    suplentes = [c for c in lista.get("candidatos", []) if c.get("suplente")]
    incoming_ids = {c["user_id"] for c in titulares}
    titular_cargos = {c["cargo"] for c in titulares}
    proclaimed: list[dict] = []

    # 1. Encerra cessantes (titulares actuais não reeleitos) dos cargos eleitos.
    for cargo_key in titular_cargos:
        holders = await db.users.find(
            {"cargo": cargo_key, "status": "ativo", **_MEMBER_FILTER},
            {"_id": 0, "id": 1, "cargo_history": 1},
        ).to_list(None)
        for h in holders:
            if h["id"] in incoming_ids:
                continue
            hist = _close_active(h.get("cargo_history"), posse)
            await db.users.update_one(
                {"id": h["id"]},
                {"$set": {"role": "socio", "cargo": "socio", "orgao": None, "privileges": [], "cargo_history": hist}},
            )

    # 2. Promove titulares eleitos.
    for c in titulares:
        user = await db.users.find_one({"id": c["user_id"]}, {"_id": 0})
        if not user:
            continue
        cargo_key = c["cargo"]
        hist = _close_active(user.get("cargo_history"), posse)
        mandate = CargoMandate(
            cargo=cargo_key,
            label=cargo_label(cargo_key),
            role=role_for_cargo(cargo_key),
            orgao=orgao_of_cargo(cargo_key),
            inicio=posse,
            posse_em=posse,
            mandato_inicio=eleicao["mandato_inicio"],
            mandato_fim=eleicao["mandato_fim"],
            suplente=False,
            seat_index=c.get("seat_index"),
            elected_by=f"Eleição {eleicao['ano']}",
            eleicao_id=eleicao["id"],
            assembleia_id=eleicao.get("assembleia_id"),
            transitioned_by=by_id,
        ).model_dump()
        hist.append(mandate)
        await db.users.update_one(
            {"id": c["user_id"]},
            {
                "$set": {
                    "role": role_for_cargo(cargo_key),
                    "cargo": cargo_key,
                    "orgao": orgao_of_cargo(cargo_key),
                    "privileges": privileges_for_cargo(cargo_key),
                    "cargo_history": hist,
                }
            },
        )
        proclaimed.append({"user_id": c["user_id"], "cargo": cargo_key, "suplente": False})

    # 3. Suplentes: registo de mandato (suplente) sem ocupar assento activo.
    for c in suplentes:
        user = await db.users.find_one({"id": c["user_id"]}, {"_id": 0, "cargo_history": 1})
        if not user:
            continue
        cargo_key = c["cargo"]
        mandate = CargoMandate(
            cargo=cargo_key,
            label=cargo_label(cargo_key),
            role=role_for_cargo(cargo_key),
            orgao=orgao_of_cargo(cargo_key),
            inicio=posse,
            posse_em=posse,
            mandato_inicio=eleicao["mandato_inicio"],
            mandato_fim=eleicao["mandato_fim"],
            suplente=True,
            seat_index=c.get("seat_index"),
            elected_by=f"Eleição {eleicao['ano']} (suplente)",
            eleicao_id=eleicao["id"],
            assembleia_id=eleicao.get("assembleia_id"),
            transitioned_by=by_id,
        ).model_dump()
        hist = [*(user.get("cargo_history") or []), mandate]
        await db.users.update_one({"id": c["user_id"]}, {"$set": {"cargo_history": hist}})
        proclaimed.append({"user_id": c["user_id"], "cargo": cargo_key, "suplente": True})

    return posse, proclaimed


@router.post("/{eleicao_id}/proclamar")
async def proclamar(eleicao_id: str, request: Request, current_user: User = Depends(get_current_user)):
    """Proclama a lista vencedora e cria os mandatos (posse)."""
    eleicao = await _get_eleicao(eleicao_id)
    if not (current_user.role == "admin" or is_mesa_ag(current_user)):
        raise HTTPException(status_code=403, detail="Apenas a Mesa da AG ou admin proclamam")
    if eleicao["status"] != "apurada":
        raise HTTPException(status_code=400, detail="Só se proclama após o apuramento")
    resultado = eleicao.get("resultado") or {}
    if resultado.get("empate") or not resultado.get("vencedora"):
        raise HTTPException(status_code=400, detail="Sem lista vencedora (empate exige nova eleição)")

    lista = await db.eleicao_listas.find_one({"id": resultado["vencedora"], "eleicao_id": eleicao_id}, {"_id": 0})
    if not lista:
        raise HTTPException(status_code=404, detail="Lista vencedora não encontrada")

    posse, proclaimed = await _proclaim_list(eleicao, lista, current_user.id)
    await db.eleicoes.update_one(
        {"id": eleicao_id},
        {"$set": {"status": "proclamada", "resultado": {**resultado, "posse_em": posse, "proclaimed": proclaimed}}},
    )
    await create_audit_log(
        current_user.id,
        "eleicao_proclamada",
        eleicao_id,
        request=request,
        details={"lista": lista.get("letra"), "proclaimed": len(proclaimed)},
    )
    for p in proclaimed:
        await notify_users(
            [p["user_id"]],
            "system",
            "Mandato proclamado",
            f"Foi eleito para {cargo_label(p['cargo'])}.",
            "/perfil",
        )
    return {"message": "Eleição proclamada.", "posse_em": posse, "proclaimed": proclaimed}
