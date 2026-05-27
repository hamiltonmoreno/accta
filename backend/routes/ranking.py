"""Rotas do ranking de atuação do sócio (spec-ranking-socio).

F1: `GET /api/ranking/me` — score + breakdown calculados **ao vivo** para o
próprio (reusa `ranking.compute_member_score`, fonte única). O `rank`/`total`
são lidos do snapshot `member_scores` (preenchido pelo rebuild — F2); até lá
ficam `None` e o frontend mostra só o score+breakdown.

F2: `POST /api/ranking/rebuild` (recalcula o snapshot) e
`GET /api/ranking/leaderboard` (lê o snapshot, paginado, com a linha do próprio).
O breakdown detalhado fica fora das linhas públicas (§2.5 — privado ao próprio).

F4: configuração (`GET`/`PUT /api/ranking/settings`) e ajustes manuais
(`POST`/`GET /api/ranking/adjustments`), gated a admin/Direcção/`manage_ranking`.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import get_current_user
from database import db
from helpers import create_audit_log, create_notification
from models import RankingAjusteCreate, RankingOptOut, RankingSettingsUpdate, User
from permissions import is_direcao, user_can
from ranking import DEFAULT_SETTINGS, DEFAULT_WEIGHTS, compute_member_score, load_settings, rebuild_scores

router = APIRouter(tags=["ranking"])


def _current_period() -> str:
    return str(datetime.now(timezone.utc).year)


def _can_manage_ranking(user) -> bool:
    """Quem recalcula/configura o ranking: admin, Direcção, ou o privilégio
    aditivo `manage_ranking` (concedível à Direcção sem dar admin; §7).
    `user_can` já cobre o admin."""
    return user_can(user, "manage_ranking") or is_direcao(user)


@router.get("/ranking/me")
async def get_my_ranking(period: str | None = None, current_user: User = Depends(get_current_user)):
    """Score+posição+breakdown do próprio (ao vivo). `period` default = ano civil."""
    period_key = period or _current_period()
    settings = await load_settings()
    result = await compute_member_score(
        current_user.id,
        period_key,
        settings["weights"],
        settings["max_like_points_per_period"],
    )

    # Posição lida do snapshot mais recente (se já houve rebuild); senão None.
    snap = await db.member_scores.find_one(
        {"user_id": current_user.id, "period_key": period_key},
        {"_id": 0, "rank": 1, "computed_at": 1},
    )
    total_members = await db.member_scores.count_documents({"period_key": period_key})

    return {
        "period": period_key,
        "score": result["score"],
        "breakdown": result["breakdown"],
        "rank": snap.get("rank") if snap else None,
        "total_members": total_members or None,
        "computed_at": snap.get("computed_at") if snap else None,
        "enabled": settings["enabled"],
    }


@router.get("/ranking/leaderboard")
async def get_leaderboard(
    period: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    """Lê o snapshot `member_scores` do período, ordenado por `rank` asc e
    paginado. Inclui sempre a linha do próprio (mesmo fora da página) e o total.

    O `breakdown` detalhado **não** sai nas linhas públicas (§2.5: só o próprio +
    admin); a linha `me` traz o seu próprio breakdown. A `visibility` (default
    `all_members`) só ganha enforcement `direcao_only` na F5.
    """
    period_key = period or _current_period()
    settings = await load_settings()

    # Feature desligada (`enabled=False`) → não serve o leaderboard a ninguém
    # (defesa server-side; o frontend já o esconde). O `/me` mantém-se acessível.
    if not settings["enabled"]:
        return {
            "period": period_key, "total": 0, "total_ranked": 0, "limit": 0, "offset": 0,
            "computed_at": None, "top_n_dashboard": settings["top_n_dashboard"],
            "visibility": settings["visibility"], "enabled": False,
            "entries": [], "me": None,
        }

    # `visibility=direcao_only` (§6): a lista pública é restrita à Direcção/admin.
    # O `/me` mantém-se sempre acessível ao próprio (endpoint separado).
    if settings["visibility"] == "direcao_only" and not _can_manage_ranking(current_user):
        raise HTTPException(status_code=403, detail="O ranking está restrito à Direcção")

    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    # Membros com opt-out são omitidos das LISTAS públicas (§2.5); o `me` é
    # devolvido sem este filtro, por isso o próprio vê sempre a sua posição.
    query = {"period_key": period_key, "ranking_opt_out": {"$ne": True}}
    total = await db.member_scores.count_documents(query)  # visíveis (sem opt-out) — paginação
    # `rank` é global (calculado sobre todos no rebuild), por isso o denominador
    # do "#N de M" usa a contagem completa do período, não a filtrada por opt-out.
    total_ranked = await db.member_scores.count_documents({"period_key": period_key})
    entries = (
        await db.member_scores.find(query, {"_id": 0, "breakdown": 0})
        .sort("rank", 1)
        .skip(offset)
        .limit(limit)
        .to_list(limit)
    )
    me = await db.member_scores.find_one(
        {"user_id": current_user.id, "period_key": period_key}, {"_id": 0}
    )
    computed_at = entries[0]["computed_at"] if entries else (me.get("computed_at") if me else None)

    return {
        "period": period_key,
        "total": total,
        "total_ranked": total_ranked,
        "limit": limit,
        "offset": offset,
        "computed_at": computed_at,
        "top_n_dashboard": settings["top_n_dashboard"],
        "visibility": settings["visibility"],
        "enabled": settings["enabled"],
        "entries": entries,
        "me": me,
    }


@router.post("/ranking/rebuild")
async def rebuild_ranking(
    request: Request,
    period: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """Recalcula o snapshot `member_scores` de um período (admin/Direcção)."""
    if not _can_manage_ranking(current_user):
        raise HTTPException(status_code=403, detail="Apenas a Direcção ou administração podem recalcular o ranking")
    period_key = period or _current_period()
    members = await rebuild_scores(period_key)
    await create_audit_log(
        user_id=current_user.id,
        action="ranking_rebuilt",
        request=request,
        details={"period": period_key, "members": members},
    )
    return {"period": period_key, "members": members}


# --------------------------------------------------------------------------- #
# F4 — Configuração (settings) e ajustes manuais
# --------------------------------------------------------------------------- #


@router.get("/ranking/settings")
async def get_ranking_settings(current_user: User = Depends(get_current_user)):
    """Configuração efetiva do ranking (pesos + defaults fundidos)."""
    if not _can_manage_ranking(current_user):
        raise HTTPException(status_code=403, detail="Sem permissão para gerir o ranking")
    return await load_settings()


@router.put("/ranking/settings")
async def update_ranking_settings(
    payload: RankingSettingsUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Edita pesos (merge parcial)/visibilidade/Top-N/cap de likes/ativação.
    Audita `ranking_settings_updated` com o diff dos campos alterados."""
    if not _can_manage_ranking(current_user):
        raise HTTPException(status_code=403, detail="Sem permissão para gerir o ranking")

    current = await load_settings()
    update: dict = {}
    changes: dict = {}

    if payload.weights is not None:
        invalid = [k for k in payload.weights if k not in DEFAULT_WEIGHTS]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Pesos desconhecidos: {', '.join(invalid)}")
        for k, v in payload.weights.items():
            if not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0:
                raise HTTPException(status_code=400, detail=f"Peso inválido para '{k}'")
        update["weights"] = {**current["weights"], **payload.weights}
        changes["weights"] = dict(payload.weights)

    for field in ("max_like_points_per_period", "visibility", "top_n_dashboard", "enabled"):
        val = getattr(payload, field)
        if val is not None and val != current.get(field):
            update[field] = val
            changes[field] = val

    if not update:
        return current  # nada mudou

    now = datetime.now(timezone.utc).isoformat()
    update["updated_at"] = now
    update["updated_by"] = current_user.id

    existing = await db.ranking_settings.find_one({}, {"_id": 0, "id": 1})
    if existing is not None:
        await db.ranking_settings.update_one({}, {"$set": update})
    else:
        await db.ranking_settings.insert_one({**DEFAULT_SETTINGS, "weights": dict(DEFAULT_WEIGHTS), **update})

    await create_audit_log(
        user_id=current_user.id,
        action="ranking_settings_updated",
        request=request,
        details={"changes": changes},
    )
    return await load_settings()


@router.post("/ranking/adjustments")
async def add_ranking_adjustment(
    payload: RankingAjusteCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Regista um ajuste manual (delta ±, motivo) ao score de um membro.
    Audita `ranking_adjustment_added` e notifica o membro (in-app; sem email).
    O delta só se reflecte na tabela após o próximo rebuild (o `/me` é ao vivo)."""
    if not _can_manage_ranking(current_user):
        raise HTTPException(status_code=403, detail="Sem permissão para gerir o ranking")

    member = await db.users.find_one({"id": payload.user_id}, {"_id": 0, "id": 1})
    if not member:
        raise HTTPException(status_code=404, detail="Membro não encontrado")

    doc = {
        "id": str(uuid.uuid4()),
        "user_id": payload.user_id,
        "period_key": payload.period_key,
        "delta": payload.delta,
        "reason": payload.reason,
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.ranking_ajustes.insert_one(doc)

    await create_audit_log(
        user_id=current_user.id,
        action="ranking_adjustment_added",
        request=request,
        details={"user_id": payload.user_id, "delta": payload.delta, "reason": payload.reason, "period": payload.period_key},
    )
    await create_notification(
        user_id=payload.user_id,
        type="system",
        title="Ajuste de pontuação",
        message=f"A Direcção registou {payload.delta:+g} pontos no teu ranking: {payload.reason}",
        link="/ranking",
    )
    return doc


@router.get("/ranking/adjustments")
async def list_ranking_adjustments(
    user_id: str | None = None,
    period: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """Lista ajustes. Gestores (admin/Direcção/`manage_ranking`) filtram por
    `user_id`/`period`; um membro comum vê apenas os seus próprios (transparência)."""
    query: dict = {}
    if _can_manage_ranking(current_user):
        if user_id:
            query["user_id"] = user_id
    else:
        query["user_id"] = current_user.id  # não-gestor só vê os seus
    if period:
        query["period_key"] = period

    return await db.ranking_ajustes.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)


@router.put("/ranking/opt-out")
async def set_ranking_opt_out(payload: RankingOptOut, current_user: User = Depends(get_current_user)):
    """O próprio membro decide se aparece nas LISTAS públicas do ranking (§2.5).
    Continua sempre a ver a sua posição em `/me`. Atualiza o `users` (fonte para
    o próximo rebuild) e sincroniza o snapshot de imediato (efeito instantâneo)."""
    await db.users.update_one({"id": current_user.id}, {"$set": {"ranking_opt_out": payload.opt_out}})
    await db.member_scores.update_many(
        {"user_id": current_user.id}, {"$set": {"ranking_opt_out": payload.opt_out}}
    )
    return {"opt_out": payload.opt_out}
