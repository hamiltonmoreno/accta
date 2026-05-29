"""Rotas de fins profissionais e relações (Categoria 5).

spec-fins-profissionais §3.1: tudo o que NÃO é 5.1 (Grupos/Comissões — já em
`routes/projects.py` via `Project.tipo`) vive aqui.

F2 (este ficheiro hoje):
- 5.3 Formações / certificações / materiais — catálogo navegável por sócios,
  gestão pela Direcção/admin (decisão §14.2 — sem privilégio dedicado por já).
- 5.5 Publicações formais — distintas de notícias/blog. Distribuição via
  `visibility` (`socios`|`publico`); a venda é FASE 2 (F5, Cat. 4).

F3 (a adicionar mais tarde, ainda neste ficheiro): 5.2 defesa profissional e
5.4 relações externas/IFATCA.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from database import db
from helpers import create_audit_log
from models import (
    FORMACAO_TIPOS,
    Formacao,
    FormacaoCreate,
    FormacaoUpdate,
    PUBLICACAO_TIPOS,
    PUBLICACAO_VISIBILITIES,
    Publicacao,
    PublicacaoCreate,
    PublicacaoUpdate,
    User,
)
from permissions import is_direcao

router = APIRouter(tags=["profissional"])


def _can_manage(user: User) -> bool:
    """Direcção/admin podem gerir catálogo/publicações (spec §3.5, decisão §14.2)."""
    return user.role == "admin" or is_direcao(user)


async def _ensure_document_exists(document_id: Optional[str]) -> None:
    """Se o campo for fornecido, valida que aponta para um documento real."""
    if not document_id:
        return
    doc = await db.documents.find_one({"id": document_id}, {"_id": 0, "id": 1})
    if not doc:
        raise HTTPException(status_code=400, detail=f"Documento '{document_id}' nao encontrado")


# ============================================================================
# 5.3 — Formações / Certificações / Materiais
# ============================================================================


@router.post("/formacoes")
async def create_formacao(
    data: FormacaoCreate,
    current_user: User = Depends(get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Direcao ou admin pode gerir formacoes")
    await _ensure_document_exists(data.document_id)

    formacao = Formacao(**data.model_dump(), created_by=current_user.id)
    f_dict = formacao.model_dump()
    await db.formacoes.insert_one(f_dict)
    await create_audit_log(
        current_user.id,
        f"Criou {formacao.tipo} '{formacao.titulo}'",
        formacao.id,
    )
    f_dict.pop("_id", None)
    return f_dict


@router.get("/formacoes")
async def list_formacoes(
    tipo: Optional[str] = None,
    categoria: Optional[str] = None,
    ativo: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),  # noqa: ARG001 — só protege rota
):
    limit = min(limit, 100)
    if tipo is not None and tipo not in FORMACAO_TIPOS:
        raise HTTPException(status_code=400, detail=f"Tipo invalido: {FORMACAO_TIPOS}")

    query: dict = {}
    if tipo:
        query["tipo"] = tipo
    if categoria:
        query["categoria"] = categoria
    if ativo is not None:
        query["ativo"] = ativo

    total = await db.formacoes.count_documents(query)
    items = (
        await db.formacoes.find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(None)
    )
    return {"items": items, "total": total}


@router.get("/formacoes/{formacao_id}")
async def get_formacao(
    formacao_id: str,
    current_user: User = Depends(get_current_user),  # noqa: ARG001 — só protege rota
):
    formacao = await db.formacoes.find_one({"id": formacao_id}, {"_id": 0})
    if not formacao:
        raise HTTPException(status_code=404, detail="Formacao nao encontrada")
    return formacao


@router.patch("/formacoes/{formacao_id}")
async def update_formacao(
    formacao_id: str,
    data: FormacaoUpdate,
    current_user: User = Depends(get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Direcao ou admin pode gerir formacoes")

    formacao = await db.formacoes.find_one({"id": formacao_id}, {"_id": 0})
    if not formacao:
        raise HTTPException(status_code=404, detail="Formacao nao encontrada")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if "document_id" in updates:
        await _ensure_document_exists(updates["document_id"])

    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.formacoes.update_one({"id": formacao_id}, {"$set": updates})
        await create_audit_log(
            current_user.id,
            f"Atualizou {formacao['tipo']} '{formacao['titulo']}'",
            formacao_id,
        )

    return await db.formacoes.find_one({"id": formacao_id}, {"_id": 0})


@router.delete("/formacoes/{formacao_id}")
async def delete_formacao(
    formacao_id: str,
    current_user: User = Depends(get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Direcao ou admin pode gerir formacoes")

    formacao = await db.formacoes.find_one({"id": formacao_id}, {"_id": 0})
    if not formacao:
        raise HTTPException(status_code=404, detail="Formacao nao encontrada")

    await db.formacoes.delete_one({"id": formacao_id})
    await create_audit_log(
        current_user.id,
        f"Removeu {formacao['tipo']} '{formacao['titulo']}'",
        formacao_id,
    )
    return {"message": "Formacao removida"}


# ============================================================================
# 5.5 — Publicações formais
# ============================================================================


@router.post("/publicacoes")
async def create_publicacao(
    data: PublicacaoCreate,
    current_user: User = Depends(get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Direcao ou admin pode gerir publicacoes")
    if data.visibility not in PUBLICACAO_VISIBILITIES:
        raise HTTPException(status_code=400, detail=f"Visibilidade invalida: {PUBLICACAO_VISIBILITIES}")
    # F2 não suporta venda — fica bloqueada e desenhada para F5 (Cat. 4).
    if data.a_venda:
        raise HTTPException(
            status_code=400,
            detail="Venda de publicacoes esta em FASE 2 (F5) — usar a_venda=False",
        )
    await _ensure_document_exists(data.document_id)

    publicacao = Publicacao(**data.model_dump(), created_by=current_user.id)
    p_dict = publicacao.model_dump()
    await db.publicacoes.insert_one(p_dict)
    await create_audit_log(
        current_user.id,
        f"Publicou {publicacao.tipo} '{publicacao.titulo}'",
        publicacao.id,
    )
    p_dict.pop("_id", None)
    return p_dict


@router.get("/publicacoes")
async def list_publicacoes(
    tipo: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),  # noqa: ARG001 — só protege rota
):
    """Lista publicações que o utilizador autenticado pode ver.

    Não-admin: vê todas as `socios`+`publico` (autenticado). O recorte público
    sem auth é feito por outra rota futura na F4 (ProfissaoPage pública).
    """
    limit = min(limit, 100)
    if tipo is not None and tipo not in PUBLICACAO_TIPOS:
        raise HTTPException(status_code=400, detail=f"Tipo invalido: {PUBLICACAO_TIPOS}")

    query: dict = {}
    if tipo:
        query["tipo"] = tipo

    total = await db.publicacoes.count_documents(query)
    items = (
        await db.publicacoes.find(query, {"_id": 0})
        .sort("data_publicacao", -1)
        .skip(skip)
        .limit(limit)
        .to_list(None)
    )
    return {"items": items, "total": total}


@router.get("/publicacoes/{publicacao_id}")
async def get_publicacao(
    publicacao_id: str,
    current_user: User = Depends(get_current_user),  # noqa: ARG001 — só protege rota
):
    publicacao = await db.publicacoes.find_one({"id": publicacao_id}, {"_id": 0})
    if not publicacao:
        raise HTTPException(status_code=404, detail="Publicacao nao encontrada")
    return publicacao


@router.patch("/publicacoes/{publicacao_id}")
async def update_publicacao(
    publicacao_id: str,
    data: PublicacaoUpdate,
    current_user: User = Depends(get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Direcao ou admin pode gerir publicacoes")

    publicacao = await db.publicacoes.find_one({"id": publicacao_id}, {"_id": 0})
    if not publicacao:
        raise HTTPException(status_code=404, detail="Publicacao nao encontrada")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if "visibility" in updates and updates["visibility"] not in PUBLICACAO_VISIBILITIES:
        raise HTTPException(status_code=400, detail=f"Visibilidade invalida: {PUBLICACAO_VISIBILITIES}")
    if updates.get("a_venda") is True:
        raise HTTPException(
            status_code=400,
            detail="Venda de publicacoes esta em FASE 2 (F5) — usar a_venda=False",
        )
    if "document_id" in updates:
        await _ensure_document_exists(updates["document_id"])

    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.publicacoes.update_one({"id": publicacao_id}, {"$set": updates})
        await create_audit_log(
            current_user.id,
            f"Atualizou publicacao '{publicacao['titulo']}'",
            publicacao_id,
        )

    return await db.publicacoes.find_one({"id": publicacao_id}, {"_id": 0})


@router.delete("/publicacoes/{publicacao_id}")
async def delete_publicacao(
    publicacao_id: str,
    current_user: User = Depends(get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Direcao ou admin pode gerir publicacoes")

    publicacao = await db.publicacoes.find_one({"id": publicacao_id}, {"_id": 0})
    if not publicacao:
        raise HTTPException(status_code=404, detail="Publicacao nao encontrada")

    await db.publicacoes.delete_one({"id": publicacao_id})
    await create_audit_log(
        current_user.id,
        f"Removeu publicacao '{publicacao['titulo']}'",
        publicacao_id,
    )
    return {"message": "Publicacao removida"}
