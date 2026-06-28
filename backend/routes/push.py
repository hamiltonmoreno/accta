"""Web Push — subscrição/cancelamento de notificações no celular (PWA).

Todas as rotas exigem autenticação. A entrega em si vive em `push_service`
(`dispatch_push`), engatada nos helpers `create_notification`/`notify_*`.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

import push_service
from auth import get_current_user
from database import db
from models import PushSubscriptionRequest
from push_service import dispatch_push, is_safe_push_endpoint, push_enabled

router = APIRouter(prefix="/push", tags=["push"])


@router.get("/vapid-public-key")
async def get_vapid_public_key(current_user: dict = Depends(get_current_user)):
    """Chave pública VAPID para o browser subscrever (applicationServerKey).

    Servida pela API (não embebida no build) para distribuir a chave sem
    rebuild do frontend. 503 quando o push não está configurado.
    """
    if not push_enabled():
        raise HTTPException(status_code=503, detail="Notificações push não estão configuradas.")
    return {"publicKey": push_service.VAPID_PUBLIC_KEY}


@router.post("/subscribe")
async def subscribe(
    sub: PushSubscriptionRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Regista (ou atualiza) a subscrição deste dispositivo para o sócio.

    Upsert por `endpoint` (único): re-subscrever no mesmo browser substitui as
    chaves e re-aponta para o utilizador atual (ex.: troca de conta no device).
    """
    if not push_enabled():
        raise HTTPException(status_code=503, detail="Notificações push não estão configuradas.")
    if not is_safe_push_endpoint(sub.endpoint):
        raise HTTPException(status_code=400, detail="Endpoint de push inválido.")
    now = datetime.now(timezone.utc).isoformat()
    existing = await db.push_subscriptions.find_one({"endpoint": sub.endpoint}, {"_id": 0, "id": 1})
    doc = {
        "user_id": current_user["id"],
        "endpoint": sub.endpoint,
        "p256dh": sub.keys.p256dh,
        "auth": sub.keys.auth,
        "user_agent": (request.headers.get("user-agent") or "")[:255],
        "updated_at": now,
    }
    if existing:
        await db.push_subscriptions.update_one({"endpoint": sub.endpoint}, {"$set": doc})
    else:
        doc["id"] = str(uuid.uuid4())
        doc["created_at"] = now
        await db.push_subscriptions.insert_one(doc)
    return {"ok": True}


@router.post("/unsubscribe")
async def unsubscribe(sub: PushSubscriptionRequest, current_user: dict = Depends(get_current_user)):
    """Remove a subscrição deste dispositivo (só a do próprio utilizador)."""
    await db.push_subscriptions.delete_one({"endpoint": sub.endpoint, "user_id": current_user["id"]})
    return {"ok": True}


@router.post("/test")
async def test_push(current_user: dict = Depends(get_current_user)):
    """Envia um push de teste ao próprio — confirma a ativação ponta-a-ponta."""
    if not push_enabled():
        raise HTTPException(status_code=503, detail="Notificações push não estão configuradas.")
    count = await db.push_subscriptions.count_documents({"user_id": current_user["id"]})
    if not count:
        raise HTTPException(status_code=400, detail="Nenhum dispositivo subscrito para esta conta.")
    await dispatch_push(
        [current_user["id"]],
        "ACCTA — Notificações ativas",
        "As notificações no celular estão a funcionar.",
        "/carteira",
    )
    return {"ok": True, "devices": count}
