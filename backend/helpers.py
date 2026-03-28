from typing import Optional
from database import db
from models import AuditLog, Notification


async def create_audit_log(user_id: str, action: str, target_id: Optional[str] = None):
    log = AuditLog(user_id=user_id, action=action, target_id=target_id)
    log_dict = log.model_dump()
    log_dict['created_at'] = log_dict['created_at'].isoformat()
    await db.audit_logs.insert_one(log_dict)


async def create_notification(user_id: str, type: str, title: str, message: str, link: Optional[str] = None):
    notification = Notification(user_id=user_id, type=type, title=title, message=message, link=link)
    notif_dict = notification.model_dump()
    notif_dict['created_at'] = notif_dict['created_at'].isoformat()
    await db.notifications.insert_one(notif_dict)


async def notify_all_active_users(type: str, title: str, message: str, link: Optional[str] = None):
    users = await db.users.find({"status": "ativo"}, {"_id": 0, "id": 1}).to_list(1000)
    if not users:
        return
    notifications = []
    for user in users:
        notification = Notification(user_id=user['id'], type=type, title=title, message=message, link=link)
        notif_dict = notification.model_dump()
        notif_dict['created_at'] = notif_dict['created_at'].isoformat()
        notifications.append(notif_dict)
    if notifications:
        await db.notifications.insert_many(notifications)
