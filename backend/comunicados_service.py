"""Core reutilizável de comunicados (spec-comunicados-email).

Resolve destinatários a partir de um segmento e faz o fan-out por canais
(in-app via helpers.notify_users; email via email_service.send_comunicado_batch).
Usado pelo endpoint manual (routes/comunicados.py) e pelos gatilhos automáticos
de governança.
"""
import logging
import uuid  # noqa: F401
from datetime import datetime, timezone  # noqa: F401
from typing import Optional  # noqa: F401

from database import db
from email_service import comunicado_email_html, send_comunicado_batch
from helpers import notify_users, members_of_orgao  # noqa: F401

logger = logging.getLogger(__name__)

_MEMBER_PROJECTION = {
    "_id": 0, "id": 1, "name": 1, "email": 1, "role": 1,
    "account_type": 1, "member_category": 1, "cargo": 1,
    "email_opt_out_informativos": 1,
}


async def _base_members() -> list[dict]:
    """Sócios activos, excluindo contas técnicas."""
    users = await db.users.find({"status": "ativo"}, _MEMBER_PROJECTION).to_list(None)
    return [u for u in users if u.get("account_type") != "technical"]


async def resolve_recipients(segment: dict, *, channel: str, tipo: str) -> list[dict]:
    """Lista de destinatários `{id,name,email,...}` para um canal.

    - exclui contas técnicas (sempre);
    - canal `email` + tipo `informativo`: exclui quem fez opt-out;
    - canal `email`: exclui quem não tem email;
    - tipo `oficial`: ignora o opt-out (dever estatutário).
    """
    members = await _base_members()
    kind = segment.get("kind")
    value = segment.get("value")
    if kind == "all_active":
        sel = members
    elif kind == "role":
        sel = [u for u in members if u.get("role") == value]
    elif kind == "member_category":
        sel = [u for u in members if u.get("member_category") == value]
    elif kind == "orgao":
        ids = set(await members_of_orgao(value))
        sel = [u for u in members if u.get("id") in ids]
    elif kind == "manual":
        wanted = set(segment.get("user_ids") or [])
        sel = [u for u in members if u["id"] in wanted]
    else:
        sel = []
    if channel == "email":
        if tipo == "informativo":
            sel = [u for u in sel if not u.get("email_opt_out_informativos")]
        sel = [u for u in sel if u.get("email")]
    return sel


async def dispatch_comunicado(comunicado_id: str) -> dict:
    """Fan-out de um comunicado em `a_enviar`. Idempotente: só corre uma vez
    (transição a_enviar→enviando). Nunca rebenta — falhas viram estado."""
    doc = await db.comunicados.find_one({"id": comunicado_id}, {"_id": 0})
    if not doc or doc.get("status") != "a_enviar":
        return {"skipped": True}
    await db.comunicados.update_one({"id": comunicado_id}, {"$set": {"status": "enviando"}})

    channels = doc.get("channels", [])
    tipo = doc.get("tipo", "informativo")
    segment = doc.get("segment", {})
    inapp_created = email_sent = email_failed = 0
    error = None
    try:
        if "in_app" in channels:
            recips = await resolve_recipients(segment, channel="in_app", tipo=tipo)
            ids = [u["id"] for u in recips]
            if ids:
                await notify_users(
                    ids, type=doc.get("notification_type", "comunicado"),
                    title=doc["subject"], message=(doc.get("body") or "")[:280],
                    link=doc.get("cta_url"),
                )
                inapp_created = len(ids)
        if "email" in channels:
            recips = await resolve_recipients(segment, channel="email", tipo=tipo)
            emails = [u["email"] for u in recips]
            if emails:
                html = comunicado_email_html(
                    doc["subject"], doc.get("body") or "",
                    doc.get("cta_label"), doc.get("cta_url"), tipo=tipo,
                )
                res = await send_comunicado_batch(emails, doc["subject"], html)
                email_sent = res.get("sent", 0)
                email_failed = res.get("failed", 0)
        if "email" in channels and email_failed and not email_sent:
            status = "falhado"
        elif email_failed:
            status = "parcial"
        else:
            status = "enviado"
    except Exception as e:  # noqa: BLE001 — falha de envio nunca propaga
        logger.exception("dispatch_comunicado %s falhou", comunicado_id)
        status = "falhado"
        error = str(e)

    total = max(inapp_created, email_sent + email_failed)
    await db.comunicados.update_one({"id": comunicado_id}, {"$set": {
        "status": status,
        "inapp_created": inapp_created,
        "email_sent": email_sent,
        "email_failed": email_failed,
        "recipients_total": total,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "error": error,
    }})
    return {"status": status, "inapp_created": inapp_created,
            "email_sent": email_sent, "email_failed": email_failed}
