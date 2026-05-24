import uuid
from datetime import datetime, timezone
from collections import Counter

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models import User, ComunicadoCreate, RecipientsCountRequest, EmailPreferencesUpdate
from database import db
from auth import get_current_user, has_role_or_privilege
from helpers import create_audit_log, members_of_orgao
import comunicados_service

router = APIRouter(tags=["comunicados"])
limiter = Limiter(key_func=get_remote_address)


def _can_send(user: User) -> bool:
    return has_role_or_privilege(user, ("admin",), "send_comunicados")


def _guard(user: User):
    if not _can_send(user):
        raise HTTPException(status_code=403, detail="Sem permissão")


# --- rotas estáticas ANTES de /comunicados/{id} (ordem importa no FastAPI) ---

@router.post("/comunicados/recipients/count")
async def count_recipients(payload: RecipientsCountRequest,
                           current_user: User = Depends(get_current_user)):
    _guard(current_user)
    seg = payload.segment.model_dump()
    inapp = (await comunicados_service.resolve_recipients(seg, channel="in_app", tipo=payload.tipo)
             if "in_app" in payload.channels else [])
    email = (await comunicados_service.resolve_recipients(seg, channel="email", tipo=payload.tipo)
             if "email" in payload.channels else [])
    return {"in_app": len(inapp), "email": len(email)}


@router.get("/comunicados/segments")
async def comunicado_segments(current_user: User = Depends(get_current_user)):
    _guard(current_user)
    members = await comunicados_service._base_members()
    roles = Counter(u.get("role") for u in members)
    cats = Counter(u.get("member_category") for u in members)
    orgaos = {}
    for o in ("mesa_ag", "direcao", "conselho_fiscal"):
        orgaos[o] = len(await members_of_orgao(o))
    return {
        "all_active": len(members),
        "roles": dict(roles),
        "member_categories": dict(cats),
        "orgaos": orgaos,
    }


@router.patch("/me/email-preferences")
async def update_email_preferences(payload: EmailPreferencesUpdate,
                                   current_user: User = Depends(get_current_user)):
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"email_opt_out_informativos": payload.email_opt_out_informativos}},
    )
    return {"email_opt_out_informativos": payload.email_opt_out_informativos}


@router.post("/comunicados")
@limiter.limit("10/minute")
async def create_comunicado(request: Request, payload: ComunicadoCreate,
                            background_tasks: BackgroundTasks,
                            current_user: User = Depends(get_current_user)):
    _guard(current_user)
    seg = payload.segment.model_dump()
    ids = set()
    for ch in payload.channels:
        recips = await comunicados_service.resolve_recipients(seg, channel=ch, tipo=payload.tipo)
        ids.update(u["id"] for u in recips)
    cid = str(uuid.uuid4())
    doc = {
        "id": cid, "subject": payload.subject, "body": payload.body,
        "cta_label": payload.cta_label, "cta_url": payload.cta_url,
        "tipo": payload.tipo, "channels": payload.channels, "segment": seg,
        "notification_type": payload.notification_type, "status": "a_enviar",
        "recipients_total": len(ids), "inapp_created": 0, "email_sent": 0, "email_failed": 0,
        "source_kind": None, "source_ref_id": None,
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_at": None, "error": None,
    }
    await db.comunicados.insert_one(doc)
    await create_audit_log(
        current_user.id, "enviar_comunicado", cid, request=request,
        details={"tipo": payload.tipo, "channels": payload.channels,
                 "segment": seg, "recipients_total": len(ids)},
    )
    background_tasks.add_task(comunicados_service.dispatch_comunicado, cid)
    return {"id": cid, "status": "a_enviar", "recipients_total": len(ids)}


@router.get("/comunicados")
async def list_comunicados(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                           current_user: User = Depends(get_current_user)):
    _guard(current_user)
    total = await db.comunicados.count_documents({})
    items = (await db.comunicados.find({}, {"_id": 0}).sort("created_at", -1)
             .skip(skip).limit(limit).to_list(limit))
    return {"items": items, "total": total}


@router.get("/comunicados/{comunicado_id}")
async def get_comunicado(comunicado_id: str, current_user: User = Depends(get_current_user)):
    _guard(current_user)
    doc = await db.comunicados.find_one({"id": comunicado_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Comunicado não encontrado")
    return doc
