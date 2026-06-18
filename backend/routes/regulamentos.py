"""Regulamentos internos versionados (Art. 31.j, 56; spec-ciclo §6).

Repositório versionado: cada `Regulamento` tem N `RegulamentoVersao` (1, 2, 3…).
Uma versão percorre `rascunho → em_aprovacao → aprovado` (ou `revogado`). Aprovar
uma versão torna-a a `current_version_id` do regulamento e **revoga a anterior**
(o histórico é preservado). A competência decide quem aprova:

- `direcao` (maioria dos regulamentos, Art. 31.j): aprova internamente
  (admin/Direcção/`manage_documents`).
- `assembleia_geral` (ex.: Regimento da AG, Art. 56): exige uma **deliberação
  aprovada** da AG; aprova a Mesa da AG ou admin.

Aprovados ficam públicos pelo fluxo de documentos existente (o `document_id`).
"""

from datetime import datetime, timezone

from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from database import db
from helpers import create_audit_log, notify_all_active_users
from models import (
    Regulamento,
    RegulamentoCreate,
    RegulamentoVersao,
    RegulamentoVersaoAprovar,
    RegulamentoVersaoCreate,
    RegulamentoVersaoRevogar,
    User,
)
from permissions import is_direcao, is_mesa_ag, user_can

router = APIRouter(prefix="/regulamentos", tags=["regulamentos"])

_LINK = "/regulamentos"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _can_manage(user: User) -> bool:
    """Mesma verificação de role/privilégio do gate `_require_manage`, mas sem
    levantar exceção — usada para decidir o que um leitor pode ver."""
    return user.role == "admin" or is_direcao(user) or user_can(user, "manage_documents")


def _require_manage(user: User):
    if not _can_manage(user):
        raise HTTPException(status_code=403, detail="Apenas a Direccao ou admin pode gerir regulamentos")


async def _validate_document(document_id: str):
    doc = await db.documents.find_one({"id": document_id}, {"_id": 0, "id": 1})
    if not doc:
        raise HTTPException(status_code=400, detail="Documento associado nao encontrado")


async def _validate_deliberacao_aprovada(deliberacao_id: str) -> dict:
    delib = await db.assembleia_deliberacoes.find_one({"id": deliberacao_id}, {"_id": 0})
    if not delib:
        raise HTTPException(status_code=400, detail="Deliberacao da AG nao encontrada")
    if not delib.get("aprovado"):
        raise HTTPException(status_code=400, detail="A deliberacao da AG nao foi aprovada")
    return delib


async def _get_regulamento(regulamento_id: str) -> dict:
    reg = await db.regulamentos.find_one({"id": regulamento_id}, {"_id": 0})
    if not reg:
        raise HTTPException(status_code=404, detail="Regulamento nao encontrado")
    return reg


async def _get_versao(regulamento_id: str, versao_id: str) -> dict:
    versao = await db.regulamento_versoes.find_one(
        {"id": versao_id, "regulamento_id": regulamento_id}, {"_id": 0}
    )
    if not versao:
        raise HTTPException(status_code=404, detail="Versao nao encontrada")
    return versao


# --------------------------------------------------------------------------- #
# Regulamentos
# --------------------------------------------------------------------------- #


@router.post("")
async def create_regulamento(data: RegulamentoCreate, current_user: User = Depends(get_current_user)):
    _require_manage(current_user)
    existing = await db.regulamentos.find_one({"slug": data.slug}, {"_id": 0, "id": 1})
    if existing:
        raise HTTPException(status_code=400, detail="Ja existe um regulamento com esse slug")

    reg = Regulamento(
        slug=data.slug,
        titulo=data.titulo.strip(),
        descricao=(data.descricao.strip() if data.descricao else None),
        competencia_aprovacao=data.competencia_aprovacao,
        created_by=current_user.id,
    )
    await db.regulamentos.insert_one(reg.model_dump())
    await create_audit_log(
        current_user.id,
        f"Criou regulamento {reg.slug}",
        reg.id,
        details={"slug": reg.slug, "competencia": reg.competencia_aprovacao},
    )
    return reg


@router.get("")
async def list_regulamentos(current_user: User = Depends(get_current_user)):
    can_manage = _can_manage(current_user)
    regs = await db.regulamentos.find({}, {"_id": 0}).sort("created_at", -1).to_list(None)
    visible = []
    for r in regs:
        cur = None
        if r.get("current_version_id"):
            cur = await db.regulamento_versoes.find_one({"id": r["current_version_id"]}, {"_id": 0})
        # Sócios comuns só veem regulamentos com uma versão em vigor aprovada;
        # rascunhos/versões não aprovadas ficam ocultos. Gestores veem tudo.
        if not can_manage and (cur is None or cur.get("status") != "aprovado"):
            continue
        r["current_version"] = cur
        visible.append(r)
    return {"items": visible, "total": len(visible)}


@router.get("/{regulamento_id}")
async def get_regulamento(regulamento_id: str, current_user: User = Depends(get_current_user)):
    can_manage = _can_manage(current_user)
    reg = await _get_regulamento(regulamento_id)
    versoes = await db.regulamento_versoes.find(
        {"regulamento_id": regulamento_id}, {"_id": 0}
    ).to_list(None)
    # Sócios comuns só veem versões aprovadas; rascunhos/em_aprovação ficam ocultos.
    # Sem qualquer versão aprovada, o regulamento não é público (404 — não revela
    # a existência de um repositório só com rascunhos). Gestores veem tudo.
    if not can_manage:
        versoes = [v for v in versoes if v.get("status") == "aprovado"]
        if not versoes:
            raise HTTPException(status_code=404, detail="Regulamento nao encontrado")
    versoes.sort(key=lambda v: v.get("versao", 0), reverse=True)
    reg["versoes"] = versoes
    return reg


# --------------------------------------------------------------------------- #
# Versões
# --------------------------------------------------------------------------- #


@router.post("/{regulamento_id}/versoes")
async def create_versao(
    regulamento_id: str, data: RegulamentoVersaoCreate, current_user: User = Depends(get_current_user)
):
    _require_manage(current_user)
    reg = await _get_regulamento(regulamento_id)
    await _validate_document(data.document_id)

    # Próxima versão = max + 1 (calculado em Python — não depende da ordenação
    # lexical/numérica do jsonb). O índice único (regulamento_id, versao) fecha a
    # corrida entre duas criações concorrentes: em conflito, recalcula e reinsere.
    for _ in range(5):
        existentes = await db.regulamento_versoes.find(
            {"regulamento_id": regulamento_id}, {"_id": 0, "versao": 1}
        ).to_list(None)
        next_versao = max((v.get("versao", 0) for v in existentes), default=0) + 1
        versao = RegulamentoVersao(
            regulamento_id=regulamento_id,
            versao=next_versao,
            document_id=data.document_id,
            changelog=(data.changelog.strip() if data.changelog else None),
            created_by=current_user.id,
        )
        try:
            await db.regulamento_versoes.insert_one(versao.model_dump())
            break
        except UniqueViolationError:
            continue
    else:
        raise HTTPException(
            status_code=409, detail="Conflito ao numerar a versao; tente novamente"
        )
    await create_audit_log(
        current_user.id,
        f"Criou versao {next_versao} do regulamento {reg['slug']}",
        versao.id,
        details={"regulamento_id": regulamento_id, "versao": next_versao},
    )
    return versao


@router.post("/{regulamento_id}/versoes/{versao_id}/submeter")
async def submeter_versao(
    regulamento_id: str, versao_id: str, current_user: User = Depends(get_current_user)
):
    _require_manage(current_user)
    await _get_regulamento(regulamento_id)
    versao = await _get_versao(regulamento_id, versao_id)
    if versao.get("status") != "rascunho":
        raise HTTPException(status_code=400, detail="So um rascunho pode ser submetido a aprovacao")

    await db.regulamento_versoes.update_one({"id": versao_id}, {"$set": {"status": "em_aprovacao"}})
    await create_audit_log(
        current_user.id,
        f"Submeteu versao {versao.get('versao')} do regulamento a aprovacao",
        versao_id,
        details={"regulamento_id": regulamento_id},
    )
    return {"id": versao_id, "status": "em_aprovacao"}


@router.post("/{regulamento_id}/versoes/{versao_id}/aprovar")
async def aprovar_versao(
    regulamento_id: str,
    versao_id: str,
    data: RegulamentoVersaoAprovar,
    current_user: User = Depends(get_current_user),
):
    reg = await _get_regulamento(regulamento_id)
    competencia = reg.get("competencia_aprovacao", "direcao")

    # RBAC por competência (antes de mexer na versão).
    if competencia == "assembleia_geral":
        if not (current_user.role == "admin" or is_mesa_ag(current_user)):
            raise HTTPException(
                status_code=403, detail="Competencia da AG: apenas a Mesa da AG ou admin aprova"
            )
        if not data.deliberacao_id:
            raise HTTPException(
                status_code=400, detail="Aprovacao por competencia da AG exige deliberacao_id"
            )
        await _validate_deliberacao_aprovada(data.deliberacao_id)
    else:
        _require_manage(current_user)

    versao = await _get_versao(regulamento_id, versao_id)
    if versao.get("status") != "em_aprovacao":
        raise HTTPException(status_code=400, detail="A versao tem de estar em aprovacao")

    update = {
        "status": "aprovado",
        "approved_by": current_user.id,
        "effective_from": data.effective_from or _now(),
    }
    if competencia == "assembleia_geral":
        update["deliberacao_id"] = data.deliberacao_id
        update["assembleia_id"] = data.assembleia_id

    # Revoga a versão em vigor anterior (histórico mantém-se).
    prev_id = reg.get("current_version_id")
    if prev_id and prev_id != versao_id:
        await db.regulamento_versoes.update_one({"id": prev_id}, {"$set": {"status": "revogado"}})

    await db.regulamento_versoes.update_one({"id": versao_id}, {"$set": update})
    await db.regulamentos.update_one(
        {"id": regulamento_id}, {"$set": {"current_version_id": versao_id}}
    )
    await create_audit_log(
        current_user.id,
        f"Aprovou versao {versao.get('versao')} do regulamento {reg['slug']}",
        versao_id,
        details={
            "regulamento_id": regulamento_id,
            "competencia": competencia,
            "deliberacao_id": data.deliberacao_id,
        },
    )

    # Sócios: novo regulamento em vigor.
    await notify_all_active_users(
        "system",
        "Regulamento em vigor",
        f"Entrou em vigor uma nova versao do regulamento \"{reg['titulo']}\".",
        _LINK,
    )
    return {"id": versao_id, "status": "aprovado", "current_version_id": versao_id}


@router.post("/{regulamento_id}/versoes/{versao_id}/revogar")
async def revogar_versao(
    regulamento_id: str,
    versao_id: str,
    data: RegulamentoVersaoRevogar,
    current_user: User = Depends(get_current_user),
):
    _require_manage(current_user)
    reg = await _get_regulamento(regulamento_id)
    versao = await _get_versao(regulamento_id, versao_id)
    if versao.get("status") == "revogado":
        raise HTTPException(status_code=400, detail="A versao ja esta revogada")

    await db.regulamento_versoes.update_one({"id": versao_id}, {"$set": {"status": "revogado"}})
    # Se era a versão em vigor, o regulamento fica sem versão corrente.
    if reg.get("current_version_id") == versao_id:
        await db.regulamentos.update_one({"id": regulamento_id}, {"$set": {"current_version_id": None}})

    await create_audit_log(
        current_user.id,
        f"Revogou versao {versao.get('versao')} do regulamento {reg['slug']}",
        versao_id,
        details={"regulamento_id": regulamento_id, "motivo": data.motivo},
    )
    return {"id": versao_id, "status": "revogado"}


# --------------------------------------------------------------------------- #
# Seed idempotente (chamado no arranque, após ensure_schema)
# --------------------------------------------------------------------------- #


async def seed_default_regulamentos() -> None:
    """Garante o Regimento da AG (competência AG) — Art. 56. Idempotente."""
    existing = await db.regulamentos.find_one({"slug": "regimento-ag"}, {"_id": 0, "id": 1})
    if existing:
        return
    reg = Regulamento(
        slug="regimento-ag",
        titulo="Regimento da Assembleia Geral",
        descricao="Regimento interno que regula o funcionamento da Assembleia Geral (Art. 56).",
        competencia_aprovacao="assembleia_geral",
        source_article="56",
    )
    await db.regulamentos.insert_one(reg.model_dump())
