import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models import (
    User, ComunicadoCreate, ComunicadoUpdate, RecipientsCountRequest,
    AudiencePreviewRequest, EmailPreferencesUpdate,
)
from config import IS_PROD
from database import db
from auth import get_current_user, has_role_or_privilege
from permissions import can_comunicar_intra_orgao
from helpers import create_audit_log
import comunicados_service

router = APIRouter(tags=["comunicados"])
limiter = Limiter(key_func=get_remote_address)

# Órgãos a que um emissor restrito (só `comunicar_intra_orgao`) se pode dirigir
# (US4 U2). Espelha as keys aceites por helpers.members_of_orgao.
_INTRA_ORGAO_KEYS = {"direcao", "mesa_ag", "conselho_fiscal"}
_AF_NON_ORGAO_KEYS = ("cargos", "categorias", "statuses", "joined_after",
                      "joined_before", "nominal_member_ids", "nominal_emails")


def _is_full_sender(user: User) -> bool:
    """Emissor pleno: admin ou `send_comunicados` (sem restrição de âmbito)."""
    return has_role_or_privilege(user, ("admin",), "send_comunicados")


def _can_send(user: User) -> bool:
    """Acesso ao módulo: emissor pleno OU intra-órgão (US4/D1)."""
    return _is_full_sender(user) or can_comunicar_intra_orgao(user)


def _guard(user: User):
    if not _can_send(user):
        raise HTTPException(status_code=403, detail="Sem permissão")


def _guard_full(user: User):
    """Caminho `segment` legado + contagens: exige emissor pleno (US4 U2)."""
    if not _is_full_sender(user):
        raise HTTPException(status_code=403, detail="Sem permissão")


def _assert_owner_or_admin(doc: dict, user: User, action: str):
    """Só o autor do rascunho ou um admin pode editá-lo/enviá-lo/cancelá-lo —
    mesma regra do DELETE (evita que um emissor altere o rascunho de outro)."""
    if doc.get("created_by") != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail=f"Sem permissão para {action} este rascunho")


def _enforce_intra_orgao_scope(user: User, audience_filter: dict | None):
    """Âmbito restrito (US4 U2): um emissor que só tem `comunicar_intra_orgao`
    (sem `send_comunicados`/admin) só pode dirigir-se a órgãos sociais —
    `orgaos ⊆ {direcao, mesa_ag, conselho_fiscal}` e nenhum outro critério
    preenchido. Emissores plenos não têm esta restrição."""
    if _is_full_sender(user):
        return
    af = audience_filter or {}
    orgaos = af.get("orgaos") or []
    if (not orgaos
            or not set(orgaos) <= _INTRA_ORGAO_KEYS
            or any(af.get(k) for k in _AF_NON_ORGAO_KEYS)):
        raise HTTPException(
            status_code=403,
            detail="Só pode comunicar para órgãos sociais (Direcção, Mesa da AG, Conselho Fiscal)",
        )


# --- rotas estáticas ANTES de /comunicados/{id} (ordem importa no FastAPI) ---

@router.post("/comunicados/recipients/count")
async def count_recipients(payload: RecipientsCountRequest,
                           current_user: User = Depends(get_current_user)):
    _guard_full(current_user)
    seg = payload.segment.model_dump()
    inapp = (await comunicados_service.resolve_recipients(seg, channel="in_app", tipo=payload.tipo)
             if "in_app" in payload.channels else [])
    email = (await comunicados_service.resolve_recipients(seg, channel="email", tipo=payload.tipo)
             if "email" in payload.channels else [])
    total = len({u["id"] for u in inapp} | {u["id"] for u in email})
    return {"in_app": len(inapp), "email": len(email), "total": total}


@router.get("/comunicados/segments")
async def comunicado_segments(current_user: User = Depends(get_current_user)):
    _guard_full(current_user)  # contagens do caminho `segment` — só emissor pleno (US4 U2)
    return await comunicados_service.get_segment_counts()


@router.post("/comunicados/preview-audience")
async def preview_audience(payload: AudiencePreviewRequest,
                           current_user: User = Depends(get_current_user)):
    """Preview da audiência segmentada (FR-002/FR-014). Sem efeitos colaterais."""
    _guard(current_user)
    af = payload.audience_filter.model_dump()
    # Emissor restrito não pode sondar audiências fora do seu âmbito (info-leak).
    _enforce_intra_orgao_scope(current_user, af)
    return await comunicados_service.preview_audience(
        af, tipo=payload.tipo, channels=payload.channels
    )


@router.patch("/me/email-preferences")
async def update_email_preferences(payload: EmailPreferencesUpdate,
                                   current_user: User = Depends(get_current_user)):
    # Self-service: grava só as preferências enviadas (não None) do próprio
    # sócio. quota_reminder_opt_out = lembrete de quota in-app (spec-008).
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhuma preferência fornecida.")
    await db.users.update_one({"id": current_user.id}, {"$set": updates})
    return updates


@router.post("/comunicados")
@limiter.limit("10/minute")
async def create_comunicado(request: Request, payload: ComunicadoCreate,
                            background_tasks: BackgroundTasks,
                            current_user: User = Depends(get_current_user)):
    _guard(current_user)
    if payload.dry_run and IS_PROD:
        raise HTTPException(status_code=422, detail="Modo dry-run não é permitido em produção")
    cid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # --- Caminho v2: audiência segmentada → cria RASCUNHO (envio é explícito) ---
    if payload.audience_filter is not None:
        af = payload.audience_filter.model_dump()
        _enforce_intra_orgao_scope(current_user, af)
        doc = {
            "id": cid, "subject": payload.subject, "body": payload.body,
            "cta_label": payload.cta_label, "cta_url": payload.cta_url,
            "tipo": payload.tipo, "channels": payload.channels,
            "segment": None, "audience_filter": af,
            "audience_resolved": None, "recipients_count": 0, "failed_member_ids": [],
            "dry_run": payload.dry_run,
            "notification_type": payload.notification_type, "status": "rascunho",
            "recipients_total": 0, "inapp_created": 0, "email_sent": 0, "email_failed": 0,
            "source_kind": None, "source_ref_id": None,
            "created_by": current_user.id, "created_at": now, "sent_at": None, "error": None,
        }
        await db.comunicados.insert_one(doc)
        await create_audit_log(
            current_user.id, "criar_rascunho_comunicado", cid, request=request,
            details={"tipo": payload.tipo, "channels": payload.channels, "audience_filter": af},
        )
        return {"id": cid, "status": "rascunho"}

    # --- Caminho legado (segment): envio imediato (comportamento v1 inalterado) ---
    _guard_full(current_user)  # emissor restrito não usa o caminho `segment` (US4 U2)
    seg = payload.segment.model_dump()
    ids = set()
    for ch in payload.channels:
        recips = await comunicados_service.resolve_recipients(seg, channel=ch, tipo=payload.tipo)
        ids.update(u["id"] for u in recips)
    doc = {
        "id": cid, "subject": payload.subject, "body": payload.body,
        "cta_label": payload.cta_label, "cta_url": payload.cta_url,
        "tipo": payload.tipo, "channels": payload.channels, "segment": seg,
        "notification_type": payload.notification_type, "status": "a_enviar",
        "recipients_total": len(ids), "inapp_created": 0, "email_sent": 0, "email_failed": 0,
        "source_kind": None, "source_ref_id": None,
        "created_by": current_user.id,
        "created_at": now,
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


@router.patch("/comunicados/{comunicado_id}")
async def update_comunicado(comunicado_id: str, payload: ComunicadoUpdate, request: Request,
                            current_user: User = Depends(get_current_user)):
    """Edita um rascunho (FR-011). Só comunicados em `rascunho` são editáveis."""
    _guard(current_user)
    doc = await db.comunicados.find_one({"id": comunicado_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Comunicado não encontrado")
    if doc.get("status") != "rascunho":
        raise HTTPException(status_code=409, detail="Apenas rascunhos podem ser editados")
    _assert_owner_or_admin(doc, current_user, "editar")
    if payload.dry_run and IS_PROD:
        raise HTTPException(status_code=422, detail="Modo dry-run não é permitido em produção")
    changes = payload.model_dump(exclude_none=True)
    if "audience_filter" in changes:
        changes["audience_filter"] = payload.audience_filter.model_dump()
    # Âmbito restrito (US4 U2): valida o filtro efectivo após a edição.
    _enforce_intra_orgao_scope(
        current_user, changes.get("audience_filter") or doc.get("audience_filter"))
    if changes:
        await db.comunicados.update_one({"id": comunicado_id}, {"$set": changes})
    return {"id": comunicado_id, "status": "rascunho"}


@router.post("/comunicados/{comunicado_id}/enviar")
async def enviar_comunicado(comunicado_id: str, request: Request,
                            current_user: User = Depends(get_current_user)):
    """Envia um rascunho segmentado: resolve no envio (FR-010), bloqueia 0
    destinatários (FR-006), persiste snapshot + audit `comunicado_enviado`."""
    _guard(current_user)
    doc = await db.comunicados.find_one({"id": comunicado_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Comunicado não encontrado")
    if doc.get("status") != "rascunho":
        raise HTTPException(status_code=409, detail="Apenas rascunhos podem ser enviados")
    _assert_owner_or_admin(doc, current_user, "enviar")
    af = doc.get("audience_filter")
    _enforce_intra_orgao_scope(current_user, af)  # âmbito restrito no envio (US4 U2)
    sample: list = []
    if af:
        prev = await comunicados_service.preview_audience(af, tipo=doc["tipo"], channels=doc["channels"])
        if prev["recipients_count"] == 0:
            raise HTTPException(status_code=422,
                                detail="Filtro não selecciona nenhum sócio — revê os critérios")
        sample = prev["sample"]
    # rascunho → a_enviar (a CAS a_enviar→enviando vive no dispatch)
    claimed = await db.comunicados.update_one(
        {"id": comunicado_id, "status": "rascunho"}, {"$set": {"status": "a_enviar"}}
    )
    if claimed.modified_count == 0:
        raise HTTPException(status_code=409, detail="Comunicado já não está em rascunho")
    result = await comunicados_service.dispatch_comunicado(comunicado_id)
    await create_audit_log(
        current_user.id, "comunicado_enviado", comunicado_id, request=request,
        details={
            "comunicado_id": comunicado_id, "audience_filter": af,
            "recipients_count": result.get("recipients_count"),
            "recipients_sample": sample, "dry_run": result.get("dry_run", False),
        },
    )
    return result


@router.delete("/comunicados/{comunicado_id}")
async def cancelar_comunicado(comunicado_id: str, request: Request,
                              current_user: User = Depends(get_current_user)):
    """Cancela (soft) um rascunho → `cancelado` (FR-011). Terminais são imutáveis.
    Só o autor ou um admin pode cancelar."""
    _guard(current_user)
    doc = await db.comunicados.find_one({"id": comunicado_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Comunicado não encontrado")
    if doc.get("status") != "rascunho":
        raise HTTPException(status_code=409, detail="Comunicado já enviado — imutável")
    _assert_owner_or_admin(doc, current_user, "cancelar")
    await db.comunicados.update_one({"id": comunicado_id}, {"$set": {"status": "cancelado"}})
    await create_audit_log(current_user.id, "cancelar_comunicado", comunicado_id, request=request)
    return {"id": comunicado_id, "status": "cancelado"}


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
