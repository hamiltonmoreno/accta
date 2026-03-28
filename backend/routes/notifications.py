from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List
from models import User, Notification, NotificationCreate, AuditLog
from database import db
from auth import get_current_user

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=List[Notification])
async def get_notifications(current_user: User = Depends(get_current_user)):
    notifications = await db.notifications.find({"user_id": current_user.id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    for notif in notifications:
        if isinstance(notif.get('created_at'), str):
            notif['created_at'] = datetime.fromisoformat(notif['created_at'])
    return notifications


@router.get("/notifications/unread/count")
async def get_unread_count(current_user: User = Depends(get_current_user)):
    count = await db.notifications.count_documents({"user_id": current_user.id, "read": False})
    return {"count": count}


@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: User = Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user.id},
        {"$set": {"read": True}}
    )
    return {"message": "Notificação marcada como lida"}


@router.patch("/notifications/mark-all-read")
async def mark_all_notifications_read(current_user: User = Depends(get_current_user)):
    result = await db.notifications.update_many(
        {"user_id": current_user.id, "read": False},
        {"$set": {"read": True}}
    )
    return {"message": f"{result.modified_count} notificações marcadas como lidas"}


@router.post("/notifications", response_model=Notification)
async def create_notification_route(notif_data: NotificationCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    notification = Notification(**notif_data.model_dump())
    notif_dict = notification.model_dump()
    notif_dict['created_at'] = notif_dict['created_at'].isoformat()

    await db.notifications.insert_one(notif_dict)
    return notification


# AUDIT LOGS
@router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    logs = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    for log in logs:
        if isinstance(log.get('created_at'), str):
            log['created_at'] = datetime.fromisoformat(log['created_at'])
    return logs
