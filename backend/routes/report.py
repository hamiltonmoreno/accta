from fastapi import APIRouter, Depends
from database import db
from auth import get_current_user
from models import User

router = APIRouter(tags=["report"])


@router.get("/report/personal")
async def get_personal_report(current_user: User = Depends(get_current_user)):
    """Aggregate personal activity stats for the current user."""
    uid = current_user.id

    # Events attended
    events_attended = await db.events.count_documents({"attendees": uid})

    # Total events available
    total_events = await db.events.count_documents({"visibility": {"$in": ["publico", "socios"]}})

    # Polls voted in (votes guardados na coleção user_votes)
    polls_voted = await db.user_votes.count_documents({"user_id": uid})

    # Total polls
    total_polls = await db.polls.count_documents({"status": {"$in": ["aberta", "encerrada"]}})

    # Wall posts by user
    wall_posts = await db.wall_posts.count_documents({"user_id": uid, "approved": True})

    # Wall likes received
    likes_received = 0
    user_posts = db.wall_posts.find({"user_id": uid, "approved": True}, {"_id": 0, "likes": 1})
    async for p in user_posts:
        likes_received += len(p.get("likes", []))

    # Wall comments made
    wall_comments = await db.wall_comments.count_documents({"user_id": uid})

    # Project participations (member of team or task assigned)
    projects_member = await db.projects.count_documents({"team_members": uid})

    # Benefits used (count from validation log if exists, otherwise 0)
    benefits_used = await db.benefit_validations.count_documents({"user_id": uid})

    # Gallery photos submitted
    photos_submitted = await db.gallery_photos.count_documents({"uploaded_by": uid})
    photos_approved = await db.gallery_photos.count_documents({"uploaded_by": uid, "status": "approved"})

    # Documentos disponíveis para o utilizador (públicos + socios)
    documents_count = await db.documents.count_documents({"visibility": {"$in": ["publico", "socios"]}})

    # Documentos únicos a que o utilizador acedeu (deduplicado: abrir o mesmo
    # 5 vezes conta como 1). Total de eventos vai em document_access_events.
    pipeline = [
        {"$match": {"user_id": uid}},
        {"$group": {"_id": "$document_id"}},
        {"$count": "n"},
    ]
    unique_cursor = await db.document_accesses.aggregate(pipeline).to_list(1)
    documents_accessed = unique_cursor[0]["n"] if unique_cursor else 0
    document_access_events = await db.document_accesses.count_documents({"user_id": uid})

    return {
        "events_attended": events_attended,
        "total_events": total_events,
        "polls_voted": polls_voted,
        "total_polls": total_polls,
        "wall_posts": wall_posts,
        "likes_received": likes_received,
        "wall_comments": wall_comments,
        "projects_member": projects_member,
        "benefits_used": benefits_used,
        "photos_submitted": photos_submitted,
        "photos_approved": photos_approved,
        "documents_available": documents_count,
        "documents_accessed": documents_accessed,
        "document_access_events": document_access_events,
    }
