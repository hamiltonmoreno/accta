from typing import Optional, List
from datetime import datetime, timezone, timedelta
import ipaddress
import os
from fastapi import Request
from database import db
from models import AuditLog, Notification


# Redes de onde um proxy reverso legítimo (Nginx) liga-se ao backend.
# X-Forwarded-For só é confiável quando o peer TCP está numa destas — caso
# contrário a app está exposta directamente e o XFF é spoofável.
_TRUSTED_PROXY_NETS = [
    ipaddress.ip_network(n)
    for n in ("127.0.0.0/8", "::1/128", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "fc00::/7")
]


def _is_trusted_proxy(host: Optional[str]) -> bool:
    if not host:
        return False
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(ip in net for net in _TRUSTED_PROXY_NETS)


def resolve_link_base(request: Optional[Request]) -> str:
    """Base URL segura para links enviados por email (reset/convite).

    Prioriza FRONTEND_URL. Sem ele, só aceita o Origin/Referer da request
    se estiver na allowlist CORS_ORIGINS — impede que um header forjado
    transforme o email num link de phishing com token válido (fail-closed:
    devolve "" se não houver origem confiável).
    """
    frontend_url = os.environ.get("FRONTEND_URL", "").rstrip("/")
    if frontend_url:
        return frontend_url
    if request is None:
        return ""
    raw = os.environ.get("CORS_ORIGINS", "")
    allow = {o.strip().rstrip("/") for o in raw.split(",") if o.strip() and o.strip() != "*"}
    origin = (request.headers.get("origin") or "").rstrip("/")
    if not origin:
        referer = request.headers.get("referer", "")
        if referer:
            parts = referer.split("/", 3)
            origin = ("/".join(parts[:3]) if len(parts) >= 3 else "").rstrip("/")
    return origin if origin and origin in allow else ""


# === ACCOUNT LOCKOUT (Sprint 4) =====================================
# 5 falhas dentro de uma janela de 15min trancam a conta por 15min.
# Falhas sao guardadas em login_attempts (TTL 24h via index em database.py).
LOCKOUT_THRESHOLD = 5
LOCKOUT_WINDOW_MINUTES = 15


async def record_failed_login(email: str, ip: Optional[str] = None) -> None:
    """Insere uma entry de tentativa falhada. A contagem na janela é feita
    por `is_account_locked` quando necessário — não recontamos aqui (a
    contagem era descartada pelo call-site = query desperdiçada por falha).
    """
    now = datetime.now(timezone.utc)
    await db.login_attempts.insert_one({"email": email, "ip": ip, "attempted_at": now})


async def reset_failed_logins(email: str) -> None:
    """Limpa o historial de falhas — chamado em login bem-sucedido."""
    await db.login_attempts.delete_many({"email": email})


async def is_account_locked(email: str) -> Optional[datetime]:
    """Devolve o instante em que o lock expira, ou None se nao trancada.
    O lock e implicito: olha para login_attempts dentro da janela e verifica
    se atingiu o threshold. Apos a janela, attempts antigos saem por TTL e
    a contagem cai abaixo do threshold automaticamente.
    """
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
    count = await db.login_attempts.count_documents({"email": email, "attempted_at": {"$gte": window_start}})
    if count < LOCKOUT_THRESHOLD:
        return None
    # Tempo ate o attempt mais antigo na janela sair = "unlock at".
    oldest_in_window = await db.login_attempts.find_one(
        {"email": email, "attempted_at": {"$gte": window_start}},
        sort=[("attempted_at", 1)],
    )
    if oldest_in_window:
        return oldest_in_window["attempted_at"] + timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
    return now + timedelta(minutes=LOCKOUT_WINDOW_MINUTES)


def extract_request_meta(request: Optional[Request]) -> dict:
    """Extrai IP e User-Agent de uma Request. Honra X-Forwarded-For (atrás do nginx).
    Se request=None, devolve dict vazio (mantém backward-compat de call-sites antigos).
    """
    if request is None:
        return {}
    # X-Forwarded-For só é confiável se o peer TCP for um proxy reverso
    # legítimo (Nginx em loopback/rede privada). Exposto directamente, o
    # XFF é spoofável → usa-se o IP real da ligação.
    peer = request.client.host if request.client else None
    xff = request.headers.get("x-forwarded-for", "")
    if xff and _is_trusted_proxy(peer):
        ip = xff.split(",")[0].strip()
    else:
        ip = peer
    ua = request.headers.get("user-agent", "")[:500]  # cap UA length
    return {"ip": ip, "user_agent": ua or None}


async def create_audit_log(
    user_id: str,
    action: str,
    target_id: Optional[str] = None,
    *,
    request: Optional[Request] = None,
    details: Optional[dict] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Cria entrada de audit log. Backward-compat: kwargs opcionais.
    - Passar `request=request` extrai IP/UA automaticamente.
    - Para chamar de contextos sem Request, usar `ip=`/`user_agent=` directamente.
    - `details` aceita dict estruturado (e.g., campos alterados, before/after).
    """
    if request is not None:
        meta = extract_request_meta(request)
        ip = ip or meta.get("ip")
        user_agent = user_agent or meta.get("user_agent")

    log = AuditLog(
        user_id=user_id,
        action=action,
        target_id=target_id,
        ip=ip,
        user_agent=user_agent,
        details=details,
    )
    log_dict = log.model_dump()
    log_dict["created_at"] = log_dict["created_at"].isoformat()
    await db.audit_logs.insert_one(log_dict)


async def create_notification(user_id: str, type: str, title: str, message: str, link: Optional[str] = None):
    notification = Notification(user_id=user_id, type=type, title=title, message=message, link=link)
    notif_dict = notification.model_dump()
    notif_dict["created_at"] = notif_dict["created_at"].isoformat()
    await db.notifications.insert_one(notif_dict)


async def notify_users(
    user_ids: List[str],
    type: str,
    title: str,
    message: str,
    link: Optional[str] = None,
    exclude_id: Optional[str] = None,
):
    unique_ids = set(user_ids)
    if exclude_id:
        unique_ids.discard(exclude_id)
    if not unique_ids:
        return
    notifications = []
    for uid in unique_ids:
        notification = Notification(user_id=uid, type=type, title=title, message=message, link=link)
        notif_dict = notification.model_dump()
        notif_dict["created_at"] = notif_dict["created_at"].isoformat()
        notifications.append(notif_dict)
    await db.notifications.insert_many(notifications)


async def notify_all_active_users(type: str, title: str, message: str, link: Optional[str] = None):
    # Sem cap: um broadcast tem de atingir TODOS os sócios ativos (o limite
    # de 500 fazia desaparecer notificações silenciosamente).
    users = await db.users.find({"status": "ativo"}, {"_id": 0, "id": 1}).to_list(None)
    if not users:
        return
    notifications = []
    for user in users:
        notification = Notification(user_id=user["id"], type=type, title=title, message=message, link=link)
        notif_dict = notification.model_dump()
        notif_dict["created_at"] = notif_dict["created_at"].isoformat()
        notifications.append(notif_dict)
    if notifications:
        await db.notifications.insert_many(notifications)


async def notify_admins(
    type: str, title: str, message: str, link: Optional[str] = None, exclude_id: Optional[str] = None
):
    admins = await db.users.find({"role": "admin"}, {"_id": 0, "id": 1}).to_list(100)
    admin_ids = [a["id"] for a in admins]
    await notify_users(admin_ids, type, title, message, link, exclude_id)


def get_project_stakeholder_ids(project: dict) -> List[str]:
    ids = []
    if project.get("created_by"):
        ids.append(project["created_by"])
    if project.get("responsible_id"):
        ids.append(project["responsible_id"])
    return ids
