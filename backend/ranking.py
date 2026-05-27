"""Pontuação de atuação do sócio (spec-ranking-socio).

`compute_member_score` é a **fonte única** do score: usada ao vivo
(`GET /api/ranking/me`) e em lote (`rebuild_scores`). A pontuação é **derivada**
de sinais já gravados (não event-sourcing) — soma ponderada de contagens sobre
colecções existentes + ajustes manuais. Pesos são configuráveis em
`ranking_settings`; os defaults vivem aqui.

Invariantes:
- Voto secreto preservado: da eleição usa-se só a **comparência** (recibo HMAC),
  nunca o boletim/sentido de voto (§3.3).
- Quotas/invoices NÃO entram no score (desconto em folha; §0).
- Datas no `doc` são ISO-8601 string → o filtro de período é comparação
  lexicográfica de strings (`$gte`/`$lt`).
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Optional

from database import db
from auth import SECRET_KEY

# Pesos default (§3.1) — validados pela Direcção; afináveis em ranking_settings.
DEFAULT_WEIGHTS: dict[str, float] = {
    "assembleia_presenca": 10,
    "eleicao_turnout": 8,
    "projeto_participacao": 6,
    "tarefa_concluida": 4,
    "votacao_voto": 5,
    "evento_presenca": 4,
    "mural_post": 3,
    "galeria_foto": 2,
    "mural_comentario": 1,
    "mural_like_recebido": 0.5,
}
MAX_LIKE_POINTS = 50
SIGNAL_KEYS: tuple[str, ...] = tuple(DEFAULT_WEIGHTS.keys())

# Configuração default (doc único `ranking_settings`; editável por admin na F4).
DEFAULT_SETTINGS: dict = {
    "max_like_points_per_period": MAX_LIKE_POINTS,
    "visibility": "all_members",  # all_members | direcao_only
    "top_n_dashboard": 5,
    "enabled": True,
}


async def load_settings() -> dict:
    """Configuração efetiva do ranking: o doc persistido fundido com os defaults
    (pesos sempre completos). Devolve defaults se ainda não houver doc."""
    doc = await db.ranking_settings.find_one({}, {"_id": 0}) or {}
    return {
        "weights": {**DEFAULT_WEIGHTS, **(doc.get("weights") or {})},
        "max_like_points_per_period": doc.get("max_like_points_per_period", MAX_LIKE_POINTS),
        "visibility": doc.get("visibility", "all_members"),
        "top_n_dashboard": doc.get("top_n_dashboard", 5),
        "enabled": doc.get("enabled", True),
        "last_rebuild_at": doc.get("last_rebuild_at"),
        "updated_at": doc.get("updated_at"),
        "updated_by": doc.get("updated_by"),
    }


def _period_bounds(period_key: Optional[str]) -> Optional[tuple[str, str]]:
    """(início, fim) ISO para um ano civil ("2026" → ["2026-01-01","2027-01-01"));
    None para "all"/vazio (sem filtro de data) ou chave não numérica."""
    if not period_key or period_key == "all":
        return None
    if not period_key.isdigit():
        return None
    year = int(period_key)
    return (f"{year:04d}-01-01", f"{year + 1:04d}-01-01")


def _date_match(field: str, period_key: Optional[str]) -> dict:
    bounds = _period_bounds(period_key)
    if not bounds:
        return {}
    return {field: {"$gte": bounds[0], "$lt": bounds[1]}}


def voter_hash(eleicao_id: str, user_id: str) -> str:
    """HMAC-SHA256(SECRET_KEY, "{eleicao_id}:{user_id}") — idêntico ao de
    `routes/eleicoes.py`. Determinístico a partir de (eleicao_id, user_id), logo
    permite confirmar a COMPARÊNCIA sem tocar no boletim anónimo (§3.3)."""
    return hmac.new(SECRET_KEY.encode(), f"{eleicao_id}:{user_id}".encode(), hashlib.sha256).hexdigest()


async def _count_elections_voted(uid: str, period_key: Optional[str]) -> int:
    """Nº de eleições do período em que o membro compareceu. Por eleição,
    recomputa o hash do membro e testa a existência do recibo — NUNCA cruza com
    `eleicao_ballots` (voto secreto)."""
    eleicoes = await db.eleicoes.find(_date_match("created_at", period_key), {"_id": 0, "id": 1}).to_list(1000)
    voted = 0
    for e in eleicoes:
        eid = e.get("id")
        if not eid:
            continue
        receipt = await db.eleicao_voter_receipts.find_one(
            {"eleicao_id": eid, "voter_hash": voter_hash(eid, uid)}, {"_id": 0, "id": 1}
        )
        if receipt:
            voted += 1
    return voted


async def gather_signal_counts(uid: str, period_key: Optional[str], *, include_turnout: bool = True) -> dict:
    """Contagens por sinal para um membro+período (sem pesos). Fonte de contagem
    partilhada por `report.personal` (período "all") e `compute_member_score`.

    `include_turnout=False` salta a comparência eleitoral (que itera recibos por
    eleição) — usado por `report.personal`, que não a exibe.
    """
    counts: dict = {}

    counts["assembleia_presenca"] = await db.assembleia_presencas.count_documents(
        {"user_id": uid, **_date_match("created_at", period_key)}
    )
    counts["votacao_voto"] = await db.user_votes.count_documents(
        {"user_id": uid, **_date_match("created_at", period_key)}
    )
    counts["evento_presenca"] = await db.events.count_documents(
        {"attendees": uid, **_date_match("date", period_key)}
    )
    counts["mural_post"] = await db.wall_posts.count_documents(
        {"user_id": uid, "approved": True, **_date_match("created_at", period_key)}
    )
    counts["galeria_foto"] = await db.gallery_photos.count_documents(
        {"uploaded_by": uid, "status": "approved", **_date_match("created_at", period_key)}
    )
    counts["mural_comentario"] = await db.wall_comments.count_documents(
        {"user_id": uid, **_date_match("created_at", period_key)}
    )
    counts["tarefa_concluida"] = await db.project_tasks.count_documents(
        {"assignee_id": uid, "status": "concluido", **_date_match("completed_at", period_key)}
    )

    # projeto_participacao: criou / é responsável / tem tarefa atribuída.
    assigned = await db.project_tasks.find({"assignee_id": uid}, {"_id": 0, "project_id": 1}).to_list(1000)
    assigned_ids = sorted({t.get("project_id") for t in assigned if t.get("project_id")})
    proj_or = [{"created_by": uid}, {"responsible_id": uid}]
    if assigned_ids:
        proj_or.append({"id": {"$in": assigned_ids}})
    counts["projeto_participacao"] = await db.projects.count_documents(
        {"$or": proj_or, **_date_match("created_at", period_key)}
    )

    # mural_like_recebido: soma dos likes nos posts aprovados do membro (sem cap;
    # o cap aplica-se só no score). Likes são array → tally em Python (bounded).
    liked_posts = await db.wall_posts.find(
        {"user_id": uid, "approved": True, **_date_match("created_at", period_key)},
        {"_id": 0, "likes": 1},
    ).to_list(None)  # unbounded: preserva o comportamento antigo de report.personal
    counts["mural_like_recebido"] = sum(len(p.get("likes") or []) for p in liked_posts)

    counts["eleicao_turnout"] = await _count_elections_voted(uid, period_key) if include_turnout else 0
    return counts


async def _adjustments_total(uid: str, period_key: str) -> float:
    rows = await db.ranking_ajustes.find(
        {"user_id": uid, "period_key": period_key}, {"_id": 0, "delta": 1}
    ).to_list(1000)
    return sum(float(r.get("delta", 0) or 0) for r in rows)


async def compute_member_score(
    uid: str,
    period_key: str,
    weights: Optional[dict] = None,
    max_like_points: int = MAX_LIKE_POINTS,
    *,
    counts: Optional[dict] = None,
    adjust_total: Optional[float] = None,
) -> dict:
    """Score ponderado + breakdown de um membro/período. **Fonte única** do score.

    Devolve `{"score": float, "breakdown": {chave: {"count", "points"}, "ajustes": {...}}}`.
    `counts`/`adjust_total` permitem ao rebuild injectar valores pré-agregados
    (lote) sem re-consultar a DB por membro.
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    if counts is None:
        counts = await gather_signal_counts(uid, period_key)

    breakdown: dict = {}
    total = 0.0
    for key in DEFAULT_WEIGHTS:
        count = counts.get(key, 0) or 0
        points = count * w.get(key, 0)
        if key == "mural_like_recebido":
            points = min(points, max_like_points)
        breakdown[key] = {"count": count, "points": round(points, 1)}
        total += points

    adj = adjust_total if adjust_total is not None else await _adjustments_total(uid, period_key)
    total += adj
    breakdown["ajustes"] = {"count": None, "points": round(adj, 1)}

    return {"score": round(total, 1), "breakdown": breakdown}
