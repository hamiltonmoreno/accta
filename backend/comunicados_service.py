"""Core reutilizável de comunicados (spec-comunicados-email).

Resolve destinatários a partir de um segmento e faz o fan-out por canais
(in-app via helpers.notify_users; email via email_service.send_comunicado_batch).
Usado pelo endpoint manual (routes/comunicados.py) e pelos gatilhos automáticos
de governança.
"""
import logging
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from database import db
from email_service import comunicado_email_html, send_comunicado_batch
from helpers import notify_users, members_of_orgao

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


async def get_segment_counts() -> dict:
    """Contagens por segmento para o compositor — reusa a mesma base que
    resolve_recipients, para a rota não depender de _base_members (privado)."""
    members = await _base_members()
    roles = Counter(u.get("role") for u in members)
    cats = Counter(u.get("member_category") for u in members)
    orgaos = {o: len(await members_of_orgao(o))
              for o in ("mesa_ag", "direcao", "conselho_fiscal")}
    return {
        "all_active": len(members),
        "roles": dict(roles),
        "member_categories": dict(cats),
        "orgaos": orgaos,
    }


async def _persist_result(comunicado_id: str, *, status: str, inapp_created: int,
                          email_sent: int, email_failed: int, error: Optional[str]) -> None:
    """Grava o resultado final do dispatch. Tolerante a falhas: se a escrita
    falhar, regista mas não propaga (o dispatch nunca rebenta)."""
    # recipients_total: aproximação deliberada — em dual-canal um sócio pode
    # contar nos dois; usamos o maior fan-out, não a união exacta (spec §6).
    total = max(inapp_created, email_sent + email_failed)
    try:
        await db.comunicados.update_one({"id": comunicado_id}, {"$set": {
            "status": status,
            "inapp_created": inapp_created,
            "email_sent": email_sent,
            "email_failed": email_failed,
            "recipients_total": total,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "error": error,
        }})
    except Exception:  # noqa: BLE001 — persistência best-effort
        logger.exception("Falha ao persistir resultado do comunicado %s", comunicado_id)


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

    await _persist_result(
        comunicado_id, status=status, inapp_created=inapp_created,
        email_sent=email_sent, email_failed=email_failed, error=error,
    )
    return {"status": status, "inapp_created": inapp_created,
            "email_sent": email_sent, "email_failed": email_failed}


async def dispatch_oficial_auto(*, subject: str, body: str, cta_label: str = None,
                                cta_url: str = None, source_kind: str,
                                ref_id: str) -> Optional[str]:
    """Cria e dispara um comunicado OFICIAL (in-app + email, todos os activos),
    a partir de um gatilho de governança. Anti-duplicado por (source_kind,
    source_ref_id). Devolve o id criado, ou None se já existia."""
    existing = await db.comunicados.find_one(
        {"source_kind": source_kind, "source_ref_id": ref_id}, {"_id": 0, "id": 1})
    if existing:
        return None
    cid = str(uuid.uuid4())
    doc = {
        "id": cid, "subject": subject, "body": body,
        "cta_label": cta_label, "cta_url": cta_url,
        "tipo": "oficial", "channels": ["in_app", "email"],
        "segment": {"kind": "all_active", "value": None, "user_ids": None},
        "notification_type": "comunicado", "status": "a_enviar",
        "recipients_total": 0, "inapp_created": 0, "email_sent": 0, "email_failed": 0,
        "source_kind": source_kind, "source_ref_id": ref_id,
        "created_by": "system",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_at": None, "error": None,
    }
    await db.comunicados.insert_one(doc)
    await dispatch_comunicado(cid)
    return cid
