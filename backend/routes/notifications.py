from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
from models import User, Notification, NotificationCreate, AuditLog
from database import db
from auth import _extract_token, get_current_user, get_user_from_token, has_role_or_privilege
from helpers import create_audit_log, notify_all_active_users, verify_audit_entry
import asyncio
import json
import time
import uuid

router = APIRouter(tags=["notifications"])

# Streams SSE ativos por utilizador (in-memory, por worker). Cada stream faz um
# count à BD a cada 5s para sempre — sem um tecto, N tabs × M utilizadores
# drenam o pool asyncpg. 3 chega para multi-tab legítimo; acima disso o cliente
# recebe 429 e o NotificationContext cai para polling.
#
# Cada slot guarda um heartbeat (renovado a cada iteração do loop) e expira ao
# fim de _SSE_SLOT_TTL sem renovação: se o generator nunca chegar a ser iterado
# (disconnect antes do 1.º chunk, erro de middleware após a reserva), o
# `finally` nunca corre e, sem TTL, o slot ficava preso para sempre — 3 leaks e
# o utilizador levava 429 até ao restart do worker.
_SSE_MAX_PER_USER = 3
_SSE_SLOT_TTL = 20.0  # segundos; 4× o intervalo de poll (5s) dá folga a jitter
_sse_active: dict[str, dict[str, float]] = {}  # user_id -> {slot_id: heartbeat}


def _sse_live_slots(user_id: str) -> dict[str, float]:
    """Slots vivos do utilizador, descartando os expirados (auto-limpeza)."""
    now = time.monotonic()
    slots = {sid: ts for sid, ts in _sse_active.get(user_id, {}).items() if now - ts < _SSE_SLOT_TTL}
    if slots:
        _sse_active[user_id] = slots
    else:
        _sse_active.pop(user_id, None)
    return slots


def _sse_release(user_id: str, slot_id: str) -> None:
    slots = _sse_active.get(user_id)
    if slots is not None:
        slots.pop(slot_id, None)
        if not slots:
            _sse_active.pop(user_id, None)


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

    return {"items": notifications, "total": total}


@router.get("/notifications/unread/count")
async def get_unread_count(current_user: User = Depends(get_current_user)):
    count = await db.notifications.count_documents({"user_id": current_user.id, "read": False})
    return {"count": count}


@router.get("/notifications/stream")
async def notification_stream(request: Request):
    """Server-Sent Events stream para count de nao-lidas em tempo-real.

    Auth: cookie httpOnly (Sprint 10) ou Authorization header — o browser usa
    EventSource com {withCredentials: true}. O fallback `?token=` foi removido
    (o token aparecia em logs de Nginx/proxy); clientes usam cookie/header.
    """
    final_token = _extract_token(request)
    if not final_token:
        raise HTTPException(status_code=401, detail="Nao autenticado")
    user = await get_user_from_token(final_token)
    if not user:
        raise HTTPException(status_code=401, detail="Token invalido")

    if len(_sse_live_slots(user.id)) >= _SSE_MAX_PER_USER:
        raise HTTPException(
            status_code=429,
            detail="Demasiadas ligações de notificações em simultâneo. Feche outras abas.",
        )
    # Reserva o slot JÁ, sincronamente (sem await entre o check e a reserva):
    # o generator só começa a correr quando o Starlette itera o body, DEPOIS de
    # devolvermos a resposta — reservar lá dentro deixava N connects
    # concorrentes do mesmo utilizador passar o check todos juntos e exceder o
    # cap. Libertado no finally do generator; se este nunca correr, o TTL trata.
    slot_id = uuid.uuid4().hex
    _sse_active.setdefault(user.id, {})[slot_id] = time.monotonic()

    async def event_generator():
        last_count = -1
        try:
            while True:
                if await request.is_disconnected():
                    break
                _sse_active.setdefault(user.id, {})[slot_id] = time.monotonic()  # heartbeat
                count = await db.notifications.count_documents({"user_id": user.id, "read": False})
                if count != last_count:
                    last_count = count
                    yield f"data: {json.dumps({'count': count})}\n\n"
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass
        finally:
            _sse_release(user.id, slot_id)

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
            {"value": "comunicado", "label": "Comunicado"},
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
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
):
    if not has_role_or_privilege(current_user, ("admin",), "view_audit_logs"):
        raise HTTPException(status_code=403, detail="Sem permissao")

    logs = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return logs


@router.get("/audit-logs/verify")
async def verify_audit_logs(current_user: User = Depends(get_current_user)):
    """Reverifica o tamper-evidence (HMAC) das entradas de audit log (F4 §8.1).

    A chave HMAC deriva do SECRET_KEY (fora da BD): quem tem escrita na BD mas
    não o SECRET_KEY **não consegue forjar** um hash válido, logo uma entrada
    alterada que mantenha o hash antigo é apanhada (`tampered`). Essa pessoa
    pode, porém, **remover** o `entry_hash` ao alterar a linha → a entrada passa
    a *não verificável* e cai em `legacy_unhashed`. Por isso `ok` exige **zero
    adulteradas E zero não-verificáveis**: numa instalação pós-F4
    `legacy_unhashed` devia ser 0; > 0 é sinal a reconciliar contra o baseline
    de entradas pré-F4. A resistência *completa* a remoção/apagamento fica no
    role do Postgres (revogar UPDATE/DELETE ao role da app — F5/operador).

    Itera em lotes: memória limitada + cede o event loop entre lotes (não
    bloquear os workers numa tabela de retenção indefinida).
    """
    if not has_role_or_privilege(current_user, ("admin",), "view_audit_logs"):
        raise HTTPException(status_code=403, detail="Sem permissao")

    BATCH = 1000
    total = legacy = 0
    tampered: List[str] = []
    offset = 0
    while True:
        rows = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", 1).skip(offset).limit(BATCH).to_list(BATCH)
        if not rows:
            break
        for log in rows:
            total += 1
            if not log.get("entry_hash"):
                legacy += 1
            elif not verify_audit_entry(log):
                tampered.append(log.get("id"))
        offset += len(rows)
        await asyncio.sleep(0)  # cede o event loop entre lotes

    return {
        "ok": len(tampered) == 0 and legacy == 0,
        "total": total,
        "verified": total - legacy,
        "legacy_unhashed": legacy,
        "tampered_count": len(tampered),
        "tampered_ids": tampered[:50],
    }
