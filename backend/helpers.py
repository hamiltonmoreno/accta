from typing import Optional, List
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


async def notify_users(user_ids: List[str], type: str, title: str, message: str, link: Optional[str] = None, exclude_id: Optional[str] = None):
    unique_ids = set(user_ids)
    if exclude_id:
        unique_ids.discard(exclude_id)
    if not unique_ids:
        return
    notifications = []
    for uid in unique_ids:
        notification = Notification(user_id=uid, type=type, title=title, message=message, link=link)
        notif_dict = notification.model_dump()
        notif_dict['created_at'] = notif_dict['created_at'].isoformat()
        notifications.append(notif_dict)
    await db.notifications.insert_many(notifications)


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


async def notify_admins(type: str, title: str, message: str, link: Optional[str] = None, exclude_id: Optional[str] = None):
    admins = await db.users.find({"role": "admin"}, {"_id": 0, "id": 1}).to_list(100)
    admin_ids = [a['id'] for a in admins]
    await notify_users(admin_ids, type, title, message, link, exclude_id)


def get_project_stakeholder_ids(project: dict) -> List[str]:
    ids = []
    if project.get("created_by"):
        ids.append(project["created_by"])
    if project.get("responsible_id"):
        ids.append(project["responsible_id"])
    return ids
