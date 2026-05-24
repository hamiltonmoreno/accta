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
from helpers import notify_users, members_of_orgao  # noqa: F401
# NOTA: comunicado_email_html / send_comunicado_batch são importados no topo
# numa task posterior (dispatch), depois de existirem no email_service.

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
