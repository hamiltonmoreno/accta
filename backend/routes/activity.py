from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone
from database import db
from auth import get_current_user
from models import User

router = APIRouter(tags=["activity"])


@router.get("/activity/recent")
async def get_recent_activity(limit: int = Query(15, ge=1, le=50), current_user: User = Depends(get_current_user)):
    is_financeiro = current_user.role in ("admin", "financeiro")
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

    # 2. Recent project updates (comments, status changes via audit logs)
    project_comments = (
        await db.project_comments.find(
            {}, {"_id": 0, "id": 1, "project_id": 1, "user_name": 1, "content": 1, "created_at": 1}
        )
        .sort("created_at", -1)
        .limit(5)
        .to_list(5)
    )

    for c in project_comments:
        proj = await db.projects.find_one({"id": c.get("project_id")}, {"_id": 0, "title": 1})
        proj_title = proj["title"] if proj else "Projeto"
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

    # 3. Recent events created
    events = (
        await db.events.find({}, {"_id": 0, "id": 1, "title": 1, "date": 1, "location": 1, "created_at": 1})
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
            {"status": "concluido"},
            {"_id": 0, "id": 1, "title": 1, "project_id": 1, "completed_at": 1, "created_at": 1},
        )
        .sort("created_at", -1)
        .limit(3)
        .to_list(3)
    )

    for m in milestones:
        activities.append(
            {
                "type": "projeto",
                "icon": "trophy",
                "title": "Marco Concluido",
                "description": m.get("title", ""),
                "link": f"/projetos/{m.get('project_id', '')}",
                "created_at": m.get("completed_at", m.get("created_at", "")),
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
            if isinstance(dt_str, datetime):
                return dt_str
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return datetime.min.replace(tzinfo=timezone.utc)

    activities.sort(key=parse_date, reverse=True)

    # Convert datetime objects to ISO strings for JSON serialization
    for a in activities:
        if isinstance(a.get("created_at"), datetime):
            a["created_at"] = a["created_at"].isoformat()

    return activities[:limit]
