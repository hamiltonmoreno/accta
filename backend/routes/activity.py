from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone
from database import db
from auth import get_current_user, has_role_or_privilege
from models import User
from routes.events import get_allowed_event_visibilities
from routes.projects import can_view_project

router = APIRouter(tags=["activity"])


async def _visible_projects(proj_ids: list, user: User) -> dict:
    """Map id->projeto, apenas os que o utilizador pode ver (filtra o feed)."""
    if not proj_ids:
        return {}
    projects = await db.projects.find(
        {"id": {"$in": proj_ids}},
        {"_id": 0, "id": 1, "title": 1, "visibility": 1, "status": 1, "created_by": 1, "responsible_id": 1},
    ).to_list(len(proj_ids))
    return {p["id"]: p for p in projects if can_view_project(user, p)}


@router.get("/activity/recent")
async def get_recent_activity(limit: int = Query(15, ge=1, le=50), current_user: User = Depends(get_current_user)):
    is_financeiro = has_role_or_privilege(current_user, ("admin",), "manage_finances")
    activities = []

    # 1. Recent wall posts (approved, public)
    wall_posts = (
        await db.wall_posts.find(
            {"approved": True}, {"_id": 0, "id": 1, "user_name": 1, "content": 1, "category": 1, "created_at": 1}
        )
        .sort("created_at", -1)
        .limit(8)
        .to_list(8)
    )

    for p in wall_posts:
        activities.append(
            {
                "type": "mural",
                "icon": "message-square",
                "title": p.get("user_name", "Membro"),
                "description": (
                    p.get("content", "")[:100] + "..." if len(p.get("content", "")) > 100 else p.get("content", "")
                ),
                "category": p.get("category", "geral"),
                "link": "/mural",
                "created_at": p.get("created_at", ""),
            }
        )

    # 2. Recent project updates (comments). Resolve titulos com 1 query batch
    # em vez de N find_one (N+1 -> 1+1).
    project_comments = (
        await db.project_comments.find(
            {}, {"_id": 0, "id": 1, "project_id": 1, "user_name": 1, "content": 1, "created_at": 1}
        )
        .sort("created_at", -1)
        .limit(5)
        .to_list(5)
    )

    visible_projects = await _visible_projects(
        list({c.get("project_id") for c in project_comments if c.get("project_id")}), current_user
    )

    for c in project_comments:
        proj = visible_projects.get(c.get("project_id"))
        if proj is None:  # sócio sem acesso ao projeto não vê os comentários no feed
            continue
        proj_title = proj.get("title", "Projeto")
        activities.append(
            {
                "type": "projeto",
                "icon": "folder-kanban",
                "title": f"{c.get('user_name', 'Membro')} comentou",
                "description": f"em '{proj_title}': {c.get('content', '')[:80]}",
                "link": f"/projetos/{c.get('project_id', '')}",
                "created_at": c.get("created_at", ""),
            }
        )

    # 3. Recent events created (apenas visibilidades permitidas ao utilizador)
    allowed_vis = list(get_allowed_event_visibilities(current_user))
    events = (
        await db.events.find(
            {"visibility": {"$in": allowed_vis}},
            {"_id": 0, "id": 1, "title": 1, "date": 1, "location": 1, "created_at": 1},
        )
        .sort("created_at", -1)
        .limit(3)
        .to_list(3)
    )

    for e in events:
        activities.append(
            {
                "type": "evento",
                "icon": "calendar",
                "title": "Novo Evento",
                "description": e.get("title", ""),
                "link": "/eventos",
                "created_at": e.get("created_at", e.get("date", "")),
            }
        )

    # 4. Recent transactions (only for admin/financeiro)
    if is_financeiro:
        transactions = (
            await db.transactions.find(
                {}, {"_id": 0, "id": 1, "type": 1, "description": 1, "amount": 1, "created_at": 1}
            )
            .sort("created_at", -1)
            .limit(5)
            .to_list(5)
        )

        for t in transactions:
            tipo = "Receita" if t.get("type") == "receita" else "Despesa"
            activities.append(
                {
                    "type": "financeiro",
                    "icon": "dollar-sign",
                    "title": f"{tipo}: {t.get('amount', 0):,.0f} CVE",
                    "description": t.get("description", ""),
                    "link": "/financeiro",
                    "created_at": t.get("created_at", ""),
                }
            )

    # 5. Recent project milestones completed
    milestones = (
        await db.project_milestones.find(
            {"completed": True},
            {"_id": 0, "id": 1, "title": 1, "project_id": 1, "date": 1, "created_at": 1},
        )
        .sort("date", -1)
        .limit(3)
        .to_list(3)
    )

    milestone_projects = await _visible_projects(
        list({m.get("project_id") for m in milestones if m.get("project_id")}), current_user
    )
    for m in milestones:
        if m.get("project_id") not in milestone_projects:  # marco de projeto sem acesso
            continue
        activities.append(
            {
                "type": "projeto",
                "icon": "trophy",
                "title": "Marco Concluido",
                "description": m.get("title", ""),
                "link": f"/projetos/{m.get('project_id', '')}",
                "created_at": m.get("date", m.get("created_at", "")),
            }
        )

    # 6. Recent polls opened
    polls = (
        await db.polls.find({"status": "aberta"}, {"_id": 0, "id": 1, "title": 1, "created_at": 1})
        .sort("created_at", -1)
        .limit(3)
        .to_list(3)
    )

    for p in polls:
        activities.append(
            {
                "type": "votacao",
                "icon": "vote",
                "title": "Nova Votacao",
                "description": p.get("title", ""),
                "link": "/votacoes",
                "created_at": p.get("created_at", ""),
            }
        )

    # Sort all activities by created_at descending
    def parse_date(item):
        dt_str = item.get("created_at", "")
        if not dt_str:
            return datetime.min.replace(tzinfo=timezone.utc)
        try:
            dt = dt_str if isinstance(dt_str, datetime) else datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return datetime.min.replace(tzinfo=timezone.utc)
        # Eventos/milestones podem trazer datas naive (ex. "2026-01-15"); sem
        # isto, o sort compara naive vs aware e rebenta com TypeError.
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    activities.sort(key=parse_date, reverse=True)

    return activities[:limit]
