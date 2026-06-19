"""Rotas de fins profissionais e relações (Categoria 5).

spec-fins-profissionais §3.1: tudo o que NÃO é 5.1 (Grupos/Comissões — já em
`routes/projects.py` via `Project.tipo`) vive aqui.

F2 (5.3 Formações + 5.5 Publicações) já em develop (PR #135).

F3 (este PR):
- 5.2 Defesa profissional — registo + workflow com aprovação da Direcção
  (decisão dono 2026-05-29: rascunho → submetido → publicado | rascunho;
  segregação criador ≠ aprovador) → arquivado.
- 5.4 Cooperação e filiação IFATCA — diretório de relações externas com
  estado de filiação; IFATCA semeada em arranque (público por defeito).
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from database import db
from helpers import create_audit_log, create_notification
from models import (
    DEFESA_STATUSES,
    DEFESA_TIPOS,
    DEFESA_VISIBILITIES,
    DefesaProfissional,
    DefesaProfissionalCreate,
    DefesaProfissionalUpdate,
    DefesaRejeicao,
    ESTADOS_FILIACAO,
    FORMACAO_TIPOS,
    Formacao,
    FormacaoCreate,
    FormacaoUpdate,
    PUBLICACAO_TIPOS,
    PUBLICACAO_VISIBILITIES,
    Publicacao,
    PublicacaoCreate,
    PublicacaoUpdate,
    RELACAO_TIPOS,
    RELACAO_VISIBILITIES,
    RelacaoExterna,
    RelacaoExternaCreate,
    RelacaoExternaUpdate,
    User,
)
from permissions import is_direcao

logger = logging.getLogger(__name__)

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
    items = await db.formacoes.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
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
    # F5: venda permitida. Exige preço positivo quando a_venda; a receita externa
    # regista-se em Cat. 4 (category="venda_publicacoes"); sócios descarregam grátis.
    if data.a_venda and (data.preco is None or data.preco <= 0):
        raise HTTPException(
            status_code=400,
            detail="Publicacao a venda exige um preco positivo (CVE)",
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
    current_user: User = Depends(get_current_user),
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
    # Não-admin só vê publicações destinadas a sócios ou ao público; as `privado`
    # ficam reservadas à Direcção/admin (a listagem não filtrava de todo).
    if not _can_manage(current_user):
        query["visibility"] = {"$in": ["publico", "socios"]}

    total = await db.publicacoes.count_documents(query)
    items = (
        await db.publicacoes.find(query, {"_id": 0}).sort("data_publicacao", -1).skip(skip).limit(limit).to_list(None)
    )
    return {"items": items, "total": total}


@router.get("/publicacoes/{publicacao_id}")
async def get_publicacao(
    publicacao_id: str,
    current_user: User = Depends(get_current_user),
):
    publicacao = await db.publicacoes.find_one({"id": publicacao_id}, {"_id": 0})
    if not publicacao:
        raise HTTPException(status_code=404, detail="Publicacao nao encontrada")
    # Mesma restrição de visibilidade que `list_publicacoes`: o não-gestor só
    # acede a publicações `publico`/`socios`. As `privado` ficam reservadas à
    # Direcção/admin e ao autor — devolve 404 (não 403) para não revelar a sua
    # existência (mitiga IDOR).
    if not _can_manage(current_user):
        visivel = publicacao.get("visibility") in ("publico", "socios")
        autor = publicacao.get("created_by") == current_user.id
        if not visivel and not autor:
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
    # F5: venda permitida. Valida o estado efetivo após o merge — uma publicação
    # que fica a_venda tem de ter um preço positivo.
    efetivo_a_venda = updates.get("a_venda", publicacao.get("a_venda", False))
    efetivo_preco = updates.get("preco", publicacao.get("preco"))
    if efetivo_a_venda and (efetivo_preco is None or efetivo_preco <= 0):
        raise HTTPException(
            status_code=400,
            detail="Publicacao a venda exige um preco positivo (CVE)",
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


# ============================================================================
# 5.2 — Defesa profissional (workflow com aprovação da Direcção)
# Fluxo: rascunho → submetido → publicado | rascunho (rejeitado) → arquivado.
# Segregação: criador != aprovador para o passo `aprovar`.
# ============================================================================


def _can_see_defesa(user: User, defesa: dict) -> bool:
    """Quem pode ler uma defesa profissional:
    - Direcção/admin: tudo.
    - Autor: o que criou (qualquer status).
    - Sócios autenticados: `publicado` (qualquer visibility).
    O recorte público sem auth é feito por outra rota futura (F4)."""
    if _can_manage(user) or defesa.get("created_by") == user.id:
        return True
    return defesa.get("status") == "publicado"


def _defesa_visible_query(user: User) -> dict:
    """Filtro de listagem para sócios comuns (vêem só publicado + as suas)."""
    if _can_manage(user):
        return {}
    return {"$or": [{"status": "publicado"}, {"created_by": user.id}]}


@router.post("/defesa-profissional")
async def create_defesa(
    data: DefesaProfissionalCreate,
    current_user: User = Depends(get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(
            status_code=403,
            detail="Apenas a Direcao ou admin pode criar registos de defesa profissional",
        )
    if data.visibility not in DEFESA_VISIBILITIES:
        raise HTTPException(status_code=400, detail=f"Visibilidade invalida: {DEFESA_VISIBILITIES}")
    await _ensure_document_exists(data.document_id)

    defesa = DefesaProfissional(**data.model_dump(), created_by=current_user.id)
    d_dict = defesa.model_dump()
    await db.defesa_profissional.insert_one(d_dict)
    await create_audit_log(
        current_user.id,
        f"Criou {defesa.tipo} '{defesa.titulo}' (rascunho)",
        defesa.id,
    )
    d_dict.pop("_id", None)
    return d_dict


@router.get("/defesa-profissional")
async def list_defesa(
    tipo: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
):
    limit = min(limit, 100)
    if tipo is not None and tipo not in DEFESA_TIPOS:
        raise HTTPException(status_code=400, detail=f"Tipo invalido: {DEFESA_TIPOS}")
    if status is not None and status not in DEFESA_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status invalido: {DEFESA_STATUSES}")

    query: dict = dict(_defesa_visible_query(current_user))
    if tipo:
        query["tipo"] = tipo
    if status:
        query["status"] = status

    total = await db.defesa_profissional.count_documents(query)
    items = (
        await db.defesa_profissional.find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(None)
    )
    return {"items": items, "total": total}


@router.get("/defesa-profissional/{defesa_id}")
async def get_defesa(
    defesa_id: str,
    current_user: User = Depends(get_current_user),
):
    defesa = await db.defesa_profissional.find_one({"id": defesa_id}, {"_id": 0})
    if not defesa:
        raise HTTPException(status_code=404, detail="Registo nao encontrado")
    if not _can_see_defesa(current_user, defesa):
        raise HTTPException(status_code=403, detail="Sem permissao para ver este registo")
    return defesa


@router.patch("/defesa-profissional/{defesa_id}")
async def update_defesa(
    defesa_id: str,
    data: DefesaProfissionalUpdate,
    current_user: User = Depends(get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Direcao ou admin pode editar")

    defesa = await db.defesa_profissional.find_one({"id": defesa_id}, {"_id": 0})
    if not defesa:
        raise HTTPException(status_code=404, detail="Registo nao encontrado")
    # Editar so em rascunho: garante que o conteudo aprovado e o que foi submetido
    # (a aprovacao nao pode incidir sobre conteudo alterado apos a submissao).
    # Para alterar um submetido: rejeitar (volta a rascunho) -> editar -> re-submeter.
    if defesa["status"] != "rascunho":
        raise HTTPException(
            status_code=400,
            detail=f"So e possivel editar enquanto rascunho (status actual: {defesa['status']})",
        )

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if "visibility" in updates and updates["visibility"] not in DEFESA_VISIBILITIES:
        raise HTTPException(status_code=400, detail=f"Visibilidade invalida: {DEFESA_VISIBILITIES}")
    if "document_id" in updates:
        await _ensure_document_exists(updates["document_id"])

    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.defesa_profissional.update_one({"id": defesa_id}, {"$set": updates})
        await create_audit_log(
            current_user.id,
            f"Atualizou {defesa['tipo']} '{defesa['titulo']}'",
            defesa_id,
        )

    return await db.defesa_profissional.find_one({"id": defesa_id}, {"_id": 0})


@router.delete("/defesa-profissional/{defesa_id}")
async def delete_defesa(
    defesa_id: str,
    current_user: User = Depends(get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Direcao ou admin pode remover")

    defesa = await db.defesa_profissional.find_one({"id": defesa_id}, {"_id": 0})
    if not defesa:
        raise HTTPException(status_code=404, detail="Registo nao encontrado")
    if defesa["status"] == "publicado":
        raise HTTPException(
            status_code=400,
            detail="Nao remover registos publicados — arquive primeiro",
        )

    await db.defesa_profissional.delete_one({"id": defesa_id})
    await create_audit_log(
        current_user.id,
        f"Removeu {defesa['tipo']} '{defesa['titulo']}'",
        defesa_id,
    )
    return {"message": "Registo removido"}


# --- Transições do workflow -------------------------------------------------


@router.post("/defesa-profissional/{defesa_id}/submeter")
async def submeter_defesa(
    defesa_id: str,
    current_user: User = Depends(get_current_user),
):
    """O autor (ou Direcção) submete um rascunho para aprovação."""
    defesa = await db.defesa_profissional.find_one({"id": defesa_id}, {"_id": 0})
    if not defesa:
        raise HTTPException(status_code=404, detail="Registo nao encontrado")
    if defesa["status"] != "rascunho":
        raise HTTPException(
            status_code=400,
            detail=f"So rascunhos podem ser submetidos (status: {defesa['status']})",
        )
    if defesa["created_by"] != current_user.id and not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="So o autor ou a Direcao pode submeter")

    now = datetime.now(timezone.utc).isoformat()
    # Compare-and-swap: o status esperado entra no filtro para tornar a
    # transicao atomica (evita a janela TOCTOU entre o find_one e o update).
    result = await db.defesa_profissional.update_one(
        {"id": defesa_id, "status": "rascunho"},
        {
            "$set": {
                "status": "submetido",
                "submetido_em": now,
                "submetido_por": current_user.id,
                "updated_at": now,
            }
        },
    )
    if not result.matched_count:
        raise HTTPException(
            status_code=409,
            detail="O estado mudou entretanto; recarregue e tente de novo",
        )
    await create_audit_log(
        current_user.id,
        f"Submeteu para aprovacao: {defesa['tipo']} '{defesa['titulo']}'",
        defesa_id,
    )
    return await db.defesa_profissional.find_one({"id": defesa_id}, {"_id": 0})


@router.post("/defesa-profissional/{defesa_id}/aprovar")
async def aprovar_defesa(
    defesa_id: str,
    current_user: User = Depends(get_current_user),
):
    """A Direcção aprova (publica). Segregação: aprovador != criador."""
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="So a Direcao ou admin pode aprovar")

    defesa = await db.defesa_profissional.find_one({"id": defesa_id}, {"_id": 0})
    if not defesa:
        raise HTTPException(status_code=404, detail="Registo nao encontrado")
    if defesa["status"] != "submetido":
        raise HTTPException(
            status_code=400,
            detail=f"So submetidos podem ser aprovados (status: {defesa['status']})",
        )
    if defesa["created_by"] == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="O autor nao pode aprovar a propria submissao (segregacao de funcoes)",
        )

    now = datetime.now(timezone.utc).isoformat()
    # Compare-and-swap: garante que so se publica se ainda estiver 'submetido'
    # no momento da escrita (evita dupla-publicacao em pedidos concorrentes).
    result = await db.defesa_profissional.update_one(
        {"id": defesa_id, "status": "submetido"},
        {
            "$set": {
                "status": "publicado",
                "aprovado_em": now,
                "aprovado_por": current_user.id,
                "motivo_rejeicao": None,
                "updated_at": now,
            }
        },
    )
    if not result.matched_count:
        raise HTTPException(
            status_code=409,
            detail="O estado mudou entretanto; recarregue e tente de novo",
        )
    await create_audit_log(
        current_user.id,
        f"Aprovou e publicou: {defesa['tipo']} '{defesa['titulo']}'",
        defesa_id,
    )
    # Notifica o autor (best-effort).
    try:
        await create_notification(
            user_id=defesa["created_by"],
            type="admin",
            title="Submissao aprovada",
            message=f"A sua submissao '{defesa['titulo']}' foi aprovada e publicada.",
            link=f"/defesa-profissional/{defesa_id}",
        )
    except Exception as e:  # noqa: BLE001 - notificacao non-fatal
        logger.warning("notify autor (aprovar defesa) falhou: %s", e)
    return await db.defesa_profissional.find_one({"id": defesa_id}, {"_id": 0})


@router.post("/defesa-profissional/{defesa_id}/rejeitar")
async def rejeitar_defesa(
    defesa_id: str,
    payload: DefesaRejeicao,
    current_user: User = Depends(get_current_user),
):
    """A Direcção rejeita a submissão (volta a rascunho com motivo)."""
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="So a Direcao ou admin pode rejeitar")

    defesa = await db.defesa_profissional.find_one({"id": defesa_id}, {"_id": 0})
    if not defesa:
        raise HTTPException(status_code=404, detail="Registo nao encontrado")
    if defesa["status"] != "submetido":
        raise HTTPException(
            status_code=400,
            detail=f"So submetidos podem ser rejeitados (status: {defesa['status']})",
        )
    if defesa["created_by"] == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="O autor nao pode rejeitar a propria submissao (segregacao de funcoes)",
        )

    now = datetime.now(timezone.utc).isoformat()
    # Compare-and-swap: so rejeita se ainda estiver 'submetido' (atomicidade).
    result = await db.defesa_profissional.update_one(
        {"id": defesa_id, "status": "submetido"},
        {
            "$set": {
                "status": "rascunho",
                "motivo_rejeicao": payload.motivo,
                "submetido_em": None,
                "submetido_por": None,
                "updated_at": now,
            }
        },
    )
    if not result.matched_count:
        raise HTTPException(
            status_code=409,
            detail="O estado mudou entretanto; recarregue e tente de novo",
        )
    await create_audit_log(
        current_user.id,
        f"Rejeitou submissao: {defesa['tipo']} '{defesa['titulo']}' (motivo: {payload.motivo[:80]})",
        defesa_id,
    )
    try:
        await create_notification(
            user_id=defesa["created_by"],
            type="admin",
            title="Submissao rejeitada",
            message=f"A sua submissao '{defesa['titulo']}' foi rejeitada. Motivo: {payload.motivo}",
            link=f"/defesa-profissional/{defesa_id}",
        )
    except Exception as e:  # noqa: BLE001 - notificacao non-fatal
        logger.warning("notify autor (rejeitar defesa) falhou: %s", e)
    return await db.defesa_profissional.find_one({"id": defesa_id}, {"_id": 0})


@router.post("/defesa-profissional/{defesa_id}/arquivar")
async def arquivar_defesa(
    defesa_id: str,
    current_user: User = Depends(get_current_user),
):
    """A Direcção arquiva um registo publicado (ou retira de produção)."""
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="So a Direcao ou admin pode arquivar")

    defesa = await db.defesa_profissional.find_one({"id": defesa_id}, {"_id": 0})
    if not defesa:
        raise HTTPException(status_code=404, detail="Registo nao encontrado")
    # So registos publicados sao arquivados (publicado -> arquivado): evita que um
    # unico membro da Direccao descarte uma submissao pendente sem o 2.o aprovador.
    # rascunho descarta-se via delete; submetido rejeita-se (volta a rascunho).
    if defesa["status"] != "publicado":
        raise HTTPException(
            status_code=400,
            detail=f"So registos publicados podem ser arquivados (status: {defesa['status']})",
        )

    now = datetime.now(timezone.utc).isoformat()
    # Compare-and-swap: so arquiva se ainda estiver 'publicado' (atomicidade).
    result = await db.defesa_profissional.update_one(
        {"id": defesa_id, "status": "publicado"},
        {
            "$set": {
                "status": "arquivado",
                "arquivado_em": now,
                "arquivado_por": current_user.id,
                "updated_at": now,
            }
        },
    )
    if not result.matched_count:
        raise HTTPException(
            status_code=409,
            detail="O estado mudou entretanto; recarregue e tente de novo",
        )
    await create_audit_log(
        current_user.id,
        f"Arquivou {defesa['tipo']} '{defesa['titulo']}'",
        defesa_id,
    )
    return await db.defesa_profissional.find_one({"id": defesa_id}, {"_id": 0})


# ============================================================================
# 5.4 — Cooperação e filiação IFATCA / Relações externas
# ============================================================================


async def _ensure_documentos_existem(documentos: list[str]) -> None:
    """Valida que cada document_id aponta para um documento real."""
    for doc_id in documentos or []:
        await _ensure_document_exists(doc_id)


@router.post("/relacoes-externas")
async def create_relacao(
    data: RelacaoExternaCreate,
    current_user: User = Depends(get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="So a Direcao ou admin pode criar relacoes")
    if data.visibility not in RELACAO_VISIBILITIES:
        raise HTTPException(status_code=400, detail=f"Visibilidade invalida: {RELACAO_VISIBILITIES}")
    if data.estado_filiacao not in ESTADOS_FILIACAO:
        raise HTTPException(status_code=400, detail=f"Estado de filiacao invalido: {ESTADOS_FILIACAO}")
    await _ensure_documentos_existem(data.documentos)

    relacao = RelacaoExterna(**data.model_dump(), created_by=current_user.id)
    r_dict = relacao.model_dump()
    await db.relacoes_externas.insert_one(r_dict)
    await create_audit_log(
        current_user.id,
        f"Criou relacao externa '{relacao.nome}' ({relacao.tipo})",
        relacao.id,
    )
    r_dict.pop("_id", None)
    return r_dict


@router.get("/relacoes-externas")
async def list_relacoes(
    tipo: Optional[str] = None,
    estado_filiacao: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),  # noqa: ARG001 — só protege rota
):
    limit = min(limit, 100)
    if tipo is not None and tipo not in RELACAO_TIPOS:
        raise HTTPException(status_code=400, detail=f"Tipo invalido: {RELACAO_TIPOS}")
    if estado_filiacao is not None and estado_filiacao not in ESTADOS_FILIACAO:
        raise HTTPException(status_code=400, detail=f"Estado de filiacao invalido: {ESTADOS_FILIACAO}")

    query: dict = {}
    if tipo:
        query["tipo"] = tipo
    if estado_filiacao:
        query["estado_filiacao"] = estado_filiacao

    total = await db.relacoes_externas.count_documents(query)
    items = await db.relacoes_externas.find(query, {"_id": 0}).sort("nome", 1).skip(skip).limit(limit).to_list(None)
    return {"items": items, "total": total}


@router.get("/relacoes-externas/{relacao_id}")
async def get_relacao(
    relacao_id: str,
    current_user: User = Depends(get_current_user),  # noqa: ARG001 — só protege rota
):
    relacao = await db.relacoes_externas.find_one({"id": relacao_id}, {"_id": 0})
    if not relacao:
        raise HTTPException(status_code=404, detail="Relacao nao encontrada")
    return relacao


@router.patch("/relacoes-externas/{relacao_id}")
async def update_relacao(
    relacao_id: str,
    data: RelacaoExternaUpdate,
    current_user: User = Depends(get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="So a Direcao ou admin pode editar")

    relacao = await db.relacoes_externas.find_one({"id": relacao_id}, {"_id": 0})
    if not relacao:
        raise HTTPException(status_code=404, detail="Relacao nao encontrada")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if "visibility" in updates and updates["visibility"] not in RELACAO_VISIBILITIES:
        raise HTTPException(status_code=400, detail=f"Visibilidade invalida: {RELACAO_VISIBILITIES}")
    if "estado_filiacao" in updates and updates["estado_filiacao"] not in ESTADOS_FILIACAO:
        raise HTTPException(status_code=400, detail=f"Estado de filiacao invalido: {ESTADOS_FILIACAO}")
    if "documentos" in updates:
        await _ensure_documentos_existem(updates["documentos"])

    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.relacoes_externas.update_one({"id": relacao_id}, {"$set": updates})
        await create_audit_log(
            current_user.id,
            f"Atualizou relacao externa '{relacao['nome']}'",
            relacao_id,
        )

    return await db.relacoes_externas.find_one({"id": relacao_id}, {"_id": 0})


@router.delete("/relacoes-externas/{relacao_id}")
async def delete_relacao(
    relacao_id: str,
    current_user: User = Depends(get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="So a Direcao ou admin pode remover")

    relacao = await db.relacoes_externas.find_one({"id": relacao_id}, {"_id": 0})
    if not relacao:
        raise HTTPException(status_code=404, detail="Relacao nao encontrada")

    await db.relacoes_externas.delete_one({"id": relacao_id})
    await create_audit_log(
        current_user.id,
        f"Removeu relacao externa '{relacao['nome']}'",
        relacao_id,
    )
    return {"message": "Relacao removida"}


# ============================================================================
# Seed idempotente da IFATCA (spec-fins-profissionais §7.1)
# ============================================================================


async def seed_ifatca() -> None:
    """Semeia a IFATCA como `federacao_internacional` no diretório de relações.
    Idempotente: corre em cada startup mas insere apenas se não existir."""
    existing = await db.relacoes_externas.find_one({"nome": "IFATCA"}, {"id": 1})
    if existing:
        return
    relacao = RelacaoExterna(
        nome="IFATCA",
        tipo="federacao_internacional",
        descricao=(
            "International Federation of Air Traffic Controllers' Associations — "
            "federacao internacional das associacoes de controladores de trafego "
            "aereo. A ACCTA acompanha o seu trabalho normativo e participa em "
            "eventos relevantes (Art. 2.f, 31.g, 53)."
        ),
        website="https://www.ifatca.org",
        estado_filiacao="nao_filiado",
        visibility="publico",
        created_by="system",
    )
    await db.relacoes_externas.insert_one(relacao.model_dump())
    logger.info("seed: IFATCA inserida em relacoes_externas (status inicial: nao_filiado)")
