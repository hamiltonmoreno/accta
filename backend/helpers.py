from typing import Optional, List
from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import ipaddress
import json
import os
import re
from fastapi import Request
from slowapi.util import get_remote_address
from database import db, UPLOAD_DIR, _json_default
from governance import LEGACY_ROLE_SEEDS
from models import AuditLog, CustomRole, Notification
from push_service import dispatch_push


async def resolve_legacy_role(role: Optional[str]) -> Optional[dict]:
    """spec 018 D4 (release de transição): se `role` é um nível legado
    (financeiro/moderador), devolve o doc da função personalizada seed
    equivalente — criando-a on-demand se ainda não existir (janela
    deploy→migração: a tradução nunca falha por ordem de operações).
    Devolve None para níveis não-legados (admin/socio/desconhecidos)."""
    seed_def = LEGACY_ROLE_SEEDS.get(role or "")
    if not seed_def:
        return None
    doc = await db.custom_roles.find_one({"name": seed_def["name"]}, {"_id": 0})
    if doc:
        return doc
    doc = CustomRole(
        name=seed_def["name"],
        description="Função seed da transição do modelo de acessos (spec 018)",
        privileges=list(seed_def["privileges"]),
        created_by="system",
    ).model_dump()
    try:
        await db.custom_roles.insert_one(doc)
        doc.pop("_id", None)
        return doc
    except Exception:  # noqa: BLE001
        # Corrida com outro pedido concorrente: o índice único ux_custom_roles_name
        # rejeitou o 2.º insert — re-lê o vencedor em vez de rebentar (a seed
        # existe agora, garantidamente).
        existing = await db.custom_roles.find_one({"name": seed_def["name"]}, {"_id": 0})
        if existing:
            return existing
        raise


async def coaprovacao_limiar() -> float:
    """Limiar de co-aprovação em vigor (spec-controlos §4.1, Art. 54). 0.0 (default)
    = gate desligado: o lançamento directo de despesas mantém-se. Acima de um limiar
    positivo, despesas exigem um Ato de pagamento aprovado.

    Vive aqui (módulo leaf) para ser partilhada por `routes/finances.py` e
    `routes/projects.py` sem risco de import circular (#307). Leitura defensiva —
    tolera ausência de settings / mock_db (find_one→None)."""
    s = await db.finance_settings.find_one({"id": "finance_settings"}, {"_id": 0})
    if not isinstance(s, dict):
        return 0.0
    try:
        return float(s.get("coaprovacao_limiar") or 0.0)
    except (TypeError, ValueError):
        return 0.0


async def enrich_author_photos(docs, id_field: str = "user_id", out_field: str = "user_photo_url"):
    """Injeta a foto ATUAL do autor em cada doc de uma listagem, resolvida na
    leitura (sempre fresca e cobre conteúdo antigo, sem denormalizar nem migrar).

    Custo: 1 query agregada por listagem (`find {id: {$in: [...]}}`). Tolerante —
    autor sem foto ou inexistente → `out_field=None` (fallback iniciais no UI).
    Muta os dicts in-place e devolve a mesma lista.
    """
    if not docs:
        return docs
    ids = {d.get(id_field) for d in docs if d.get(id_field)}
    if not ids:
        for d in docs:
            d[out_field] = None
        return docs
    rows = await db.users.find({"id": {"$in": list(ids)}}, {"_id": 0, "id": 1, "photo_url": 1}).to_list(len(ids))
    photo_by_id = {r["id"]: r.get("photo_url") for r in rows}
    for d in docs:
        d[out_field] = photo_by_id.get(d.get(id_field))
    return docs


def delete_upload_file(url: str) -> bool:
    """Apaga o ficheiro físico associado a um URL `/uploads/...`, com guard de
    path traversal. Devolve True se apagou. Falha silenciosa (False) em URLs
    vazias, fora de `/uploads/`, que escapem a UPLOAD_DIR ou inexistentes — não
    expõe estado do filesystem nem rebenta o handler quando o ficheiro já não lá está.
    """
    if not url or not url.startswith("/uploads/"):
        return False
    upload_root = UPLOAD_DIR.resolve()
    fp = (UPLOAD_DIR.parent / url.lstrip("/")).resolve()
    if not fp.is_relative_to(upload_root):
        return False  # tentativa de escapar de uploads/
    if not fp.exists() or not fp.is_file():
        return False
    fp.unlink()
    return True


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


def client_ip(request: Optional[Request]) -> Optional[str]:
    """IP real do cliente. Honra X-Forwarded-For SÓ se o peer TCP for um proxy
    reverso confiável (senão o XFF é spoofável). Cap a 64 chars. Fonte ÚNICA do
    IP para auditoria (extract_request_meta) e para o rate-limit (rate_limit_key)."""
    if request is None or request.client is None:
        return None
    peer = request.client.host
    xff = request.headers.get("x-forwarded-for", "")
    ip = xff.split(",")[0].strip() if (xff and _is_trusted_proxy(peer)) else peer
    return ip[:64] if ip else None


def rate_limit_key(request: Request) -> str:
    """key_func do slowapi — chaveia o rate-limit no IP REAL do cliente, não no
    IP do proxy (que colapsaria todos os clientes atrás do edge num só balde e
    tornaria o brute-force distribuído indetetável — H3). Fallback para
    get_remote_address quando a request não tem cliente (ex.: testes)."""
    return client_ip(request) or get_remote_address(request)


def safe_search_regex(s: str) -> str:
    """Fonte ÚNICA de padrões `$regex` seguros (spec 019, FR-013). Trunca ANTES de
    escapar (cap 100) — truncar depois podia cortar a meio uma sequência escapada
    (`\\x..`) e produzir um padrão inválido; o cap limita o custo de matching
    (ReDoS defensivo). TODO call site de `$regex` de pesquisa passa por aqui
    (guardado por `test_regex_call_sites_are_safe`)."""
    return re.escape((s or "").strip()[:100])


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


async def record_failed_login(email: str, ip: Optional[str] = None) -> bool:
    """Insere uma entry de tentativa falhada e devolve `True` se ESTA falha
    acabou de **cruzar** o threshold de lockout (count == LOCKOUT_THRESHOLD na
    janela) — para os call-sites alertarem os admins **uma vez** na transição
    para trancada (F3 §8.2.a). Falhas subsequentes já-trancadas devolvem `False`
    (count > threshold) e não re-alertam. Aditivo: callers que ignoram o retorno
    mantêm-se válidos (a contagem extra é index-backed e o login é rate-limited).
    """
    now = datetime.now(timezone.utc)
    # attempted_at como string ISO-8601 (convenção do projeto). O DAO rehidrata-o
    # de volta para datetime na leitura (_DATETIME_FIELDS), e a query $gte abaixo
    # serializa o datetime para a mesma forma ISO — comparação consistente.
    await db.login_attempts.insert_one({"email": email, "ip": ip, "attempted_at": now.isoformat()})
    window_start = now - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
    count = await db.login_attempts.count_documents({"email": email, "attempted_at": {"$gte": window_start}})
    return count == LOCKOUT_THRESHOLD


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
        oldest = oldest_in_window["attempted_at"]
        # Defesa: uma linha legada/malformada pode ter ficado como str (a
        # rehidratação do DAO é best-effort). Coage antes de somar timedelta
        # para não rebentar o login com TypeError.
        if isinstance(oldest, str):
            try:
                oldest = datetime.fromisoformat(oldest)
            except ValueError:
                return now + timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
        return oldest + timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
    return now + timedelta(minutes=LOCKOUT_WINDOW_MINUTES)


def extract_request_meta(request: Optional[Request]) -> dict:
    """Extrai IP e User-Agent de uma Request para auditoria. O IP vem de
    `client_ip` (honra X-Forwarded-For só atrás de proxy confiável, cap 64).
    Se request=None, devolve dict vazio (backward-compat de call-sites antigos).
    """
    if request is None:
        return {}
    ua = request.headers.get("user-agent", "")[:500]  # cap UA length
    return {"ip": client_ip(request), "user_agent": ua or None}


# === AUDIT LOG TAMPER-EVIDENCE (spec-verificacao-seguranca-saas §8.1, F4) ====
# Cada entrada leva um HMAC-SHA256 do seu conteúdo imutável. A chave é derivada
# do SECRET_KEY — que vive no env da app, NUNCA na BD. Logo quem tenha escrita
# direta na BD (mas não o SECRET_KEY) não consegue FORJAR o HMAC: uma alteração
# que mantenha o hash antigo é apanhada pelo /verify. Essa pessoa pode REMOVER o
# hash ao alterar a linha — aí a entrada fica "não verificável" (o /verify
# reflete-o e nega o `ok`), e a resistência completa a remoção/apagamento fica
# no role do Postgres: revogar UPDATE/DELETE em audit_logs ao role da app
# (runbook/F5). A app já é append-only por construção.
_AUDIT_HASH_FIELDS = ("id", "user_id", "action", "target_id", "ip", "user_agent", "details", "created_at")


def _audit_hmac_key() -> bytes:
    # Chave dedicada e namespaced, derivada do SECRET_KEY (não o reutiliza cru).
    return hashlib.sha256(b"accta-audit-integrity:" + os.environ.get("SECRET_KEY", "").encode()).digest()


def audit_entry_hash(doc: dict) -> str:
    """HMAC-SHA256 determinístico do conteúdo imutável da entrada (exclui o
    próprio entry_hash). Normaliza pela MESMA via que a BD serializa (jsonb)
    para casar no round-trip, depois ordena/compacta.

    Nota (round-trip): casa o intervalo de valores realista deste domínio
    (strings, datas ISO, montantes em CVE, contagens, índices). Floats de
    magnitude ≥ ~1e16 em `details` (que o Python serializa em notação
    exponencial mas o jsonb expande para decimal e relê como int) NÃO são
    round-trip-estáveis e dariam um falso `tampered` — fora do alcance dos
    dados de auditoria do ACCTA."""
    payload = {k: doc.get(k) for k in _AUDIT_HASH_FIELDS}
    normalized = json.loads(json.dumps(payload, default=_json_default))
    canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hmac.new(_audit_hmac_key(), canonical.encode(), hashlib.sha256).hexdigest()


def verify_audit_entry(doc: dict) -> bool:
    """True se o entry_hash guardado bate com o recomputado (entrada íntegra).
    False se foi adulterada. Entradas legadas sem entry_hash → False aqui; o
    chamador deve classificá-las como 'não verificáveis' antes de chamar."""
    stored = doc.get("entry_hash")
    if not stored:
        return False
    return hmac.compare_digest(stored, audit_entry_hash(doc))


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
    log_dict["entry_hash"] = audit_entry_hash(log_dict)
    await db.audit_logs.insert_one(log_dict)


async def create_notification(user_id: str, type: str, title: str, message: str, link: Optional[str] = None):
    notification = Notification(user_id=user_id, type=type, title=title, message=message, link=link)
    notif_dict = notification.model_dump()
    await db.notifications.insert_one(notif_dict)
    await dispatch_push([user_id], title, message, link)


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
        notifications.append(notif_dict)
    await db.notifications.insert_many(notifications)
    await dispatch_push(list(unique_ids), title, message, link)


async def notify_all_active_users(type: str, title: str, message: str, link: Optional[str] = None):
    # Sem cap: um broadcast tem de atingir TODOS os sócios ativos (o limite
    # de 500 fazia desaparecer notificações silenciosamente). Exclui contas
    # técnicas (account_type="technical", ex.: admin@controlador.cv) — não são
    # sócios reais (consistente com _base_members em comunicados_service).
    users = await db.users.find({"status": "ativo", "account_type": {"$ne": "technical"}}, {"_id": 0, "id": 1}).to_list(
        None
    )
    if not users:
        return
    notifications = []
    for user in users:
        notification = Notification(user_id=user["id"], type=type, title=title, message=message, link=link)
        notif_dict = notification.model_dump()
        notifications.append(notif_dict)
    if notifications:
        await db.notifications.insert_many(notifications)
        await dispatch_push([u["id"] for u in users], title, message, link)


async def notify_admins(
    type: str, title: str, message: str, link: Optional[str] = None, exclude_id: Optional[str] = None
):
    admins = await db.users.find({"role": "admin"}, {"_id": 0, "id": 1}).to_list(None)
    admin_ids = [a["id"] for a in admins]
    await notify_users(admin_ids, type, title, message, link, exclude_id)


# --------------------------------------------------------------------------- #
# Alertas de anomalia de segurança (spec-verificacao-seguranca-saas §8.2, F3).
# Canal in-app/SSE via `notify_admins` (sem email — defesa-em-profundidade de
# baixo ruído, evita a stop condition de emails reais). Só (a) lockout e (c)
# escalada de privilégio; (b) IPs distintos e (d) picos 4xx/429 ficam diferidos.
# --------------------------------------------------------------------------- #

# spec 018 R8: os níveis financeiro/moderador deixaram de existir — a
# sensibilidade vive nos PRIVILÉGIOS (incl. atribuídos via função
# personalizada), não no role. Substitui o antigo _ELEVATED_ROLES.
_SENSITIVE_PRIVILEGES = frozenset({"manage_users", "manage_finances", "view_audit_logs"})


async def alert_admins_account_locked(email: str) -> None:
    """Alerta os admins quando uma conta é trancada por excesso de tentativas
    de login (§8.2.a). Chamado só na transição (ver `record_failed_login`)."""
    await notify_admins(
        "system",
        "Conta bloqueada por tentativas de login",
        f"A conta {email} atingiu {LOCKOUT_THRESHOLD} tentativas falhadas em "
        f"{LOCKOUT_WINDOW_MINUTES} min e foi bloqueada. Verifique os registos de auditoria.",
        "/admin",
    )


async def alert_admins_privilege_escalation(
    actor_id: str,
    target_name: str,
    old_role: Optional[str],
    new_role: Optional[str],
    old_privileges: Optional[List[str]] = None,
    new_privileges: Optional[List[str]] = None,
) -> None:
    """Alerta os admins (exceto o ator) quando uma conta GANHA acesso elevado —
    role `admin` novo OU novos privilégios sensíveis (§8.2.c, redefinido pela
    spec 018 R8). Defesa contra escalada (admin comprometido a promover
    cúmplice; abuso de poder). De-escalada (demote/expulsão) não alerta."""
    gained = sorted(set(new_privileges or []) - set(old_privileges or []))
    gained_sensitive = [p for p in gained if p in _SENSITIVE_PRIVILEGES]
    role_up = new_role != old_role and new_role == "admin"
    if not role_up and not gained_sensitive:
        return
    parts = []
    if role_up:
        parts.append(f"role {old_role or 'socio'} → {new_role}")
    if gained:
        parts.append("privilégios +" + ", ".join(gained))
    await notify_admins(
        "system",
        "Escalada de privilégio",
        f"{target_name} recebeu acesso elevado ({'; '.join(parts)}).",
        "/admin",
        exclude_id=actor_id,
    )


def get_project_stakeholder_ids(project: dict) -> List[str]:
    ids = []
    if project.get("created_by"):
        ids.append(project["created_by"])
    if project.get("responsible_id"):
        ids.append(project["responsible_id"])
    return ids


# --------------------------------------------------------------------------- #
# Participação do sócio (spec-voz-participacao-socio §2.3) — contagem de
# elegíveis e resolução de membros de um órgão. Import local de permissions
# para evitar qualquer ciclo no import-order (helpers é carregado cedo).
# --------------------------------------------------------------------------- #


async def voting_member_ids() -> List[str]:
    """IDs dos sócios com direito a voto (fundador/ordinário, activo, sem direitos
    suspensos). Avalia em Python via `is_voting_member` para respeitar a regra
    time-based de suspensão. Base para notificar votantes (ex.: abertura de
    votação de honorário) e para a contagem de elegíveis."""
    from permissions import is_voting_member

    users = await db.users.find(
        {"status": "ativo"},
        {
            "_id": 0,
            "id": 1,
            "account_type": 1,
            "status": 1,
            "member_category": 1,
            "rights_suspended_until": 1,
            "cargo": 1,
        },
    ).to_list(None)
    return [u["id"] for u in users if is_voting_member(u)]


async def count_voting_members() -> int:
    """Nº de sócios com direito a voto. Base de limiares (petição 1/4) e maiorias."""
    return len(await voting_member_ids())


async def members_of_orgao(orgao: str) -> List[str]:
    """IDs de utilizadores activos com cargo no órgão (`direcao`/`mesa_ag`/
    `conselho_fiscal`). Fallback: se nenhum titular estiver definido, devolve os
    admins activos — para não perder notificações antes da governança estar
    povoada. Nunca falha silenciosamente."""
    from permissions import is_conselho_fiscal, is_direcao, is_mesa_ag

    matcher = {"direcao": is_direcao, "mesa_ag": is_mesa_ag, "conselho_fiscal": is_conselho_fiscal}.get(orgao)
    if matcher is not None:
        users = await db.users.find(
            {"status": "ativo", "account_type": "member"}, {"_id": 0, "id": 1, "cargo": 1}
        ).to_list(None)
        matched = [u["id"] for u in users if matcher(u)]
        if matched:
            return matched
    admins = await db.users.find({"role": "admin", "status": "ativo"}, {"_id": 0, "id": 1}).to_list(None)
    return [a["id"] for a in admins]
