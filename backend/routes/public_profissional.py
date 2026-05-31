"""Superfícies públicas (sem autenticação) — Cat 5 F4.

spec-fins-profissionais §10/§11 (F4): a `ProfissaoPage` pública e a página de
Publicações expõem APENAS o conteúdo já marcado como público:

- defesa profissional: `status="publicado"` **e** `visibility="publico"`;
- relações externas:   `visibility="publico"`;
- publicações:         `visibility="publico"`;
- formações:           `visibility="publico"` **e** `ativo=true`.

O recorte é feito no próprio query do DAO (nunca depois) e as respostas usam
projeções de **exclusão** que removem campos internos (autoria, workflow de
aprovação, contactos, quota e preço). O download dos ficheiros faz-se por
`GET /api/documents/public/{document_id}/download`, que exige que o próprio
documento seja `visibility="publico"` — publicar o registo não expõe um
documento privado.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

from database import db
from models import (
    DEFESA_TIPOS,
    ESTADOS_FILIACAO,
    FORMACAO_TIPOS,
    PUBLICACAO_TIPOS,
    RELACAO_TIPOS,
)

router = APIRouter(prefix="/public", tags=["public-profissional"])

# Projeções de exclusão — nunca expor campos internos numa superfície pública.
_DEFESA_PUBLIC_FIELDS = {
    "_id": 0,
    "created_by": 0,
    "updated_at": 0,
    "submetido_em": 0,
    "submetido_por": 0,
    "aprovado_em": 0,
    "aprovado_por": 0,
    "motivo_rejeicao": 0,
    "arquivado_em": 0,
    "arquivado_por": 0,
}
_RELACAO_PUBLIC_FIELDS = {
    "_id": 0,
    "created_by": 0,
    "updated_at": 0,
    "contacto": 0,
    "quota_anual": 0,
}
# F5: `a_venda`/`preco` SÃO expostos publicamente — o catálogo público mostra o
# preço e suprime o download dos itens à venda (conteúdo pago).
_PUBLICACAO_PUBLIC_FIELDS = {
    "_id": 0,
    "created_by": 0,
    "updated_at": 0,
}
_FORMACAO_PUBLIC_FIELDS = {
    "_id": 0,
    "created_by": 0,
    "updated_at": 0,
}


# --- 5.2 Defesa profissional (publicada e pública) --------------------------


@router.get("/defesa-profissional")
async def public_list_defesa(tipo: Optional[str] = None, skip: int = 0, limit: int = 50):
    limit = min(limit, 100)
    if tipo is not None and tipo not in DEFESA_TIPOS:
        raise HTTPException(status_code=400, detail=f"Tipo invalido: {DEFESA_TIPOS}")

    query: dict = {"status": "publicado", "visibility": "publico"}
    if tipo:
        query["tipo"] = tipo

    total = await db.defesa_profissional.count_documents(query)
    items = (
        await db.defesa_profissional.find(query, _DEFESA_PUBLIC_FIELDS)
        .sort("data", -1)
        .skip(skip)
        .limit(limit)
        .to_list(None)
    )
    return {"items": items, "total": total}


@router.get("/defesa-profissional/{defesa_id}")
async def public_get_defesa(defesa_id: str):
    defesa = await db.defesa_profissional.find_one(
        {"id": defesa_id, "status": "publicado", "visibility": "publico"},
        _DEFESA_PUBLIC_FIELDS,
    )
    if not defesa:
        raise HTTPException(status_code=404, detail="Registo nao encontrado")
    return defesa


# --- 5.4 Relações externas / IFATCA (públicas) ------------------------------


@router.get("/relacoes-externas")
async def public_list_relacoes(
    tipo: Optional[str] = None,
    estado_filiacao: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    limit = min(limit, 100)
    if tipo is not None and tipo not in RELACAO_TIPOS:
        raise HTTPException(status_code=400, detail=f"Tipo invalido: {RELACAO_TIPOS}")
    if estado_filiacao is not None and estado_filiacao not in ESTADOS_FILIACAO:
        raise HTTPException(status_code=400, detail=f"Estado de filiacao invalido: {ESTADOS_FILIACAO}")

    query: dict = {"visibility": "publico"}
    if tipo:
        query["tipo"] = tipo
    if estado_filiacao:
        query["estado_filiacao"] = estado_filiacao

    total = await db.relacoes_externas.count_documents(query)
    items = (
        await db.relacoes_externas.find(query, _RELACAO_PUBLIC_FIELDS)
        .sort("nome", 1)
        .skip(skip)
        .limit(limit)
        .to_list(None)
    )
    return {"items": items, "total": total}


# --- 5.5 Publicações (públicas) ---------------------------------------------


@router.get("/publicacoes")
async def public_list_publicacoes(tipo: Optional[str] = None, skip: int = 0, limit: int = 50):
    limit = min(limit, 100)
    if tipo is not None and tipo not in PUBLICACAO_TIPOS:
        raise HTTPException(status_code=400, detail=f"Tipo invalido: {PUBLICACAO_TIPOS}")

    query: dict = {"visibility": "publico"}
    if tipo:
        query["tipo"] = tipo

    total = await db.publicacoes.count_documents(query)
    items = (
        await db.publicacoes.find(query, _PUBLICACAO_PUBLIC_FIELDS)
        .sort("data_publicacao", -1)
        .skip(skip)
        .limit(limit)
        .to_list(None)
    )
    return {"items": items, "total": total}


@router.get("/publicacoes/{publicacao_id}")
async def public_get_publicacao(publicacao_id: str):
    pub = await db.publicacoes.find_one({"id": publicacao_id, "visibility": "publico"}, _PUBLICACAO_PUBLIC_FIELDS)
    if not pub:
        raise HTTPException(status_code=404, detail="Publicacao nao encontrada")
    return pub


# --- 5.3 Formações (públicas e ativas) --------------------------------------


@router.get("/formacoes")
async def public_list_formacoes(tipo: Optional[str] = None, skip: int = 0, limit: int = 50):
    limit = min(limit, 100)
    if tipo is not None and tipo not in FORMACAO_TIPOS:
        raise HTTPException(status_code=400, detail=f"Tipo invalido: {FORMACAO_TIPOS}")

    query: dict = {"visibility": "publico", "ativo": True}
    if tipo:
        query["tipo"] = tipo

    total = await db.formacoes.count_documents(query)
    items = (
        await db.formacoes.find(query, _FORMACAO_PUBLIC_FIELDS)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(None)
    )
    return {"items": items, "total": total}
