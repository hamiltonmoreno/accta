from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import List, Optional
from models import User, Notification, NotificationCreate, AuditLog
from database import db
from auth import _extract_token, get_current_user, get_user_from_token, has_role_or_privilege
from helpers import create_audit_log, notify_all_active_users
import asyncio
import json

router = APIRouter(tags=["notifications"])


@router.get("/notifications")
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    type_filter: Optional[str] = Query(None, alias="type"),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
):
    query = {"user_id": current_user.id}
    if type_filter:
        query["type"] = type_filter
    if unread_only:
        query["read"] = False

    total = await db.notifications.count_documents(query)
    notifications = (
        await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    )

    for notif in notifications:
        if isinstance(notif.get("created_at"), str):
            notif["created_at"] = datetime.fromisoformat(notif["created_at"])

    return {"items": notifications, "total": total}


@router.get("/notifications/unread/count")
async def get_unread_count(current_user: User = Depends(get_current_user)):
    count = await db.notifications.count_documents({"user_id": current_user.id, "read": False})
    return {"count": count}


@router.get("/notifications/stream")
async def notification_stream(request: Request, token: Optional[str] = Query(None)):
    """Server-Sent Events stream para count de nao-lidas em tempo-real.

    Auth: cookie httpOnly (Sprint 10) ou Authorization header (clientes
    browser usam EventSource com {withCredentials: true}); fallback para
    `?token=` query param para clientes legados — sera removido em v2.
    """
    extracted = _extract_token(request)
    final_token = extracted or token
    if not final_token:
        raise HTTPException(status_code=401, detail="Nao autenticado")
    user = await get_user_from_token(final_token)
    if not user:
        raise HTTPException(status_code=401, detail="Token invalido")

    async def event_generator():
        last_count = -1
        try:
            while True:
                if await request.is_disconnected():
                    break
                count = await db.notifications.count_documents({"user_id": user.id, "read": False})
                if count != last_count:
                    last_count = count
                    yield f"data: {json.dumps({'count': count})}\n\n"
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: User = Depends(get_current_user)):
    await db.notifications.update_one({"id": notification_id, "user_id": current_user.id}, {"$set": {"read": True}})
    return {"message": "Notificacao marcada como lida"}


@router.patch("/notifications/mark-all-read")
async def mark_all_notifications_read(current_user: User = Depends(get_current_user)):
    result = await db.notifications.update_many({"user_id": current_user.id, "read": False}, {"$set": {"read": True}})
    return {"message": f"{result.modified_count} notificacoes marcadas como lidas"}


@router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str, current_user: User = Depends(get_current_user)):
    result = await db.notifications.delete_one({"id": notification_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notificacao nao encontrada")
    return {"message": "Notificacao removida"}


@router.delete("/notifications/clear/all")
async def clear_all_notifications(current_user: User = Depends(get_current_user)):
    result = await db.notifications.delete_many({"user_id": current_user.id, "read": True})
    return {"message": f"{result.deleted_count} notificacoes lidas removidas"}


@router.post("/notifications/broadcast")
async def broadcast_notification(notif_data: NotificationCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissao")

    await notify_all_active_users(
        type=notif_data.type, title=notif_data.title, message=notif_data.message, link=notif_data.link
    )
    await create_audit_log(current_user.id, f"Enviou notificacao broadcast: {notif_data.title}")
    return {"message": "Notificacao enviada a todos os socios ativos"}


@router.post("/notifications", response_model=Notification)
async def create_notification_route(notif_data: NotificationCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissao")

    notification = Notification(**notif_data.model_dump())
    notif_dict = notification.model_dump()
    notif_dict["created_at"] = notif_dict["created_at"].isoformat()

    await db.notifications.insert_one(notif_dict)
    await create_audit_log(
        current_user.id,
        f"Criou notificação manual para {notif_data.user_id}",
        notif_data.user_id,
    )
    return notification


@router.get("/notifications/types")
async def get_notification_types(current_user: User = Depends(get_current_user)):
    return {
        "types": [
            {"value": "geral", "label": "Geral"},
            {"value": "financeiro", "label": "Financeiro"},
            {"value": "evento", "label": "Evento"},
            {"value": "projeto", "label": "Projeto"},
            {"value": "mural", "label": "Mural"},
            {"value": "votacao", "label": "Votacao"},
            {"value": "documento", "label": "Documento"},
            {"value": "sistema", "label": "Sistema"},
        ]
    }


# AUDIT LOGS
@router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin",), "view_audit_logs"):
        raise HTTPException(status_code=403, detail="Sem permissao")

    logs = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    for log in logs:
        if isinstance(log.get("created_at"), str):
            log["created_at"] = datetime.fromisoformat(log["created_at"])
    return logs
