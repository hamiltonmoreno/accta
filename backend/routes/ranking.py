"""Rotas do ranking de atuação do sócio (spec-ranking-socio).

F1: `GET /api/ranking/me` — score + breakdown calculados **ao vivo** para o
próprio (reusa `ranking.compute_member_score`, fonte única). O `rank`/`total`
são lidos do snapshot `member_scores` (preenchido pelo rebuild — F2); até lá
ficam `None` e o frontend mostra só o score+breakdown.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from auth import get_current_user
from database import db
from models import User
from ranking import compute_member_score, load_settings

router = APIRouter(tags=["ranking"])


def _current_period() -> str:
    return str(datetime.now(timezone.utc).year)


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
