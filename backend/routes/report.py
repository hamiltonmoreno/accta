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

    # Polls voted in
    polls_voted = 0
    polls_cursor = db.polls.find({"status": {"$in": ["aberta", "encerrada"]}}, {"_id": 0, "options": 1})
    async for poll in polls_cursor:
        for opt in poll.get("options", []):
            if uid in opt.get("voters", []):
                polls_voted += 1
                break

    # Total polls
    total_polls = await db.polls.count_documents({"status": {"$in": ["aberta", "encerrada"]}})

    # Wall posts by user
    wall_posts = await db.wall_posts.count_documents({"user_id": uid, "status": "approved"})

    # Wall likes received
    likes_received = 0
    user_posts = db.wall_posts.find({"user_id": uid, "status": "approved"}, {"_id": 0, "likes": 1})
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

    # Documents accessed (not tracked yet, placeholder)
    documents_count = await db.documents.count_documents({})

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
    }
