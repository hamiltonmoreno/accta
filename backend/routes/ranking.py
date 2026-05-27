"""Rotas do ranking de atuação do sócio (spec-ranking-socio).

F1: `GET /api/ranking/me` — score + breakdown calculados **ao vivo** para o
próprio (reusa `ranking.compute_member_score`, fonte única). O `rank`/`total`
são lidos do snapshot `member_scores` (preenchido pelo rebuild — F2); até lá
ficam `None` e o frontend mostra só o score+breakdown.

F2: `POST /api/ranking/rebuild` (recalcula o snapshot) e
`GET /api/ranking/leaderboard` (lê o snapshot, paginado, com a linha do próprio).
O breakdown detalhado fica fora das linhas públicas (§2.5 — privado ao próprio).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import get_current_user
from database import db
from helpers import create_audit_log
from models import User
from permissions import is_direcao
from ranking import compute_member_score, load_settings, rebuild_scores

router = APIRouter(tags=["ranking"])


def _current_period() -> str:
    return str(datetime.now(timezone.utc).year)


def _can_manage_ranking(user) -> bool:
    """Quem recalcula/configura o ranking. F2: admin ou Direcção. A F4 acrescenta
    o privilégio aditivo `manage_ranking` (concedível à Direcção sem dar admin)."""
    return getattr(user, "role", None) == "admin" or is_direcao(user)


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
            "period": period_key, "total": 0, "limit": 0, "offset": 0,
            "computed_at": None, "top_n_dashboard": settings["top_n_dashboard"],
            "visibility": settings["visibility"], "enabled": False,
            "entries": [], "me": None,
        }

    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    query = {"period_key": period_key}
    total = await db.member_scores.count_documents(query)
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
