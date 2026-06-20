"""Core reutilizável de comunicados (spec-comunicados-email).

Resolve destinatários a partir de um segmento e faz o fan-out por canais
(in-app via helpers.notify_users; email via email_service.send_comunicado_batch).
Usado pelo endpoint manual (routes/comunicados.py) e pelos gatilhos automáticos
de governança.
"""

import logging
import os
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from config import IS_PROD
from database import db
from email_service import comunicado_email_html, send_comunicado_batch
from governance import cargo_label
from helpers import notify_users, members_of_orgao

logger = logging.getLogger(__name__)

_MEMBER_PROJECTION = {
    "_id": 0,
    "id": 1,
    "name": 1,
    "email": 1,
    "role": 1,
    "account_type": 1,
    "member_category": 1,
    "cargo": 1,
    "status": 1,
    "member_id": 1,
    "admission_date": 1,
    "email_opt_out_informativos": 1,
}

# Estados que NÃO são membros aprovados/activos — usado para o aviso
# `includes_unapproved` quando o filtro alcança contas ainda não aprovadas.
_UNAPPROVED_STATUSES = {"pendente_aprovacao", "pendente_convite", "rejeitado"}


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
    orgaos = {o: len(await members_of_orgao(o)) for o in ("mesa_ag", "direcao", "conselho_fiscal")}
    return {
        "all_active": len(members),
        "roles": dict(roles),
        "member_categories": dict(cats),
        "orgaos": orgaos,
    }


# ===== Audiência segmentada (spec-comunicados-segmentados) =====

_ORGAO_LABELS = {
    "direcao": "Direcção",
    "mesa_ag": "Mesa da Assembleia Geral",
    "conselho_fiscal": "Conselho Fiscal",
}


async def _filter_base(statuses: Optional[list] = None) -> list[dict]:
    """Base de membros (exclui `technical`) com status em `statuses`.

    `statuses` vazio/None ⇒ default `["ativo"]`. Mesma exclusão incondicional de
    contas técnicas que `_base_members`, mas com status parametrizável (FR-003).
    """
    wanted = set(statuses or ["ativo"])
    users = await db.users.find({"status": {"$in": list(wanted)}}, _MEMBER_PROJECTION).to_list(None)
    # Re-checa o status em Python: a query já restringe na BD (índice), mas a
    # re-checagem garante o mesmo resultado quando a query não filtra (testes).
    return [u for u in users if u.get("account_type") != "technical" and u.get("status") in wanted]


def _matches_period(u: dict, joined_after: Optional[str], joined_before: Optional[str]) -> bool:
    """Casa o intervalo de filiação por `admission_date` (string ISO).

    Sem `admission_date` ⇒ NÃO casa um critério de período (conservador, R6):
    não se notifica quem não tem data conhecida quando o autor pediu um intervalo.
    """
    adm = u.get("admission_date")
    if not adm:
        return False
    if joined_after and adm < joined_after:
        return False
    if joined_before and adm > joined_before:
        return False
    return True


async def _resolve_nominal(member_ids: list, emails: list, base: list[dict]):
    """Resolve a lista nominal contra a `base`. Devolve (matched_ids, not_found,
    technical). Classifica os pedidos que não casam a base: `technical` (conta
    técnica, excluída por FR-003) vs `not_found` (não existe de todo). Quem
    existe mas está fora da base por status é descartado pelo AND, sem aviso."""
    base_by_mid = {u.get("member_id"): u["id"] for u in base if u.get("member_id")}
    base_by_email = {u.get("email"): u["id"] for u in base if u.get("email")}
    req_mid = list(dict.fromkeys(member_ids or []))
    req_email = list(dict.fromkeys(emails or []))

    found_mid: dict = {}
    found_email: dict = {}
    if req_mid or req_email:
        ors = []
        if req_mid:
            ors.append({"member_id": {"$in": req_mid}})
        if req_email:
            ors.append({"email": {"$in": req_email}})
        rows = await db.users.find(
            {"$or": ors}, {"_id": 0, "id": 1, "member_id": 1, "email": 1, "account_type": 1}
        ).to_list(None)
        for r in rows:
            if r.get("member_id"):
                found_mid[r["member_id"]] = r
            if r.get("email"):
                found_email[r["email"]] = r

    matched: set = set()
    not_found: list = []
    technical: list = []
    for mid in req_mid:
        if mid in base_by_mid:
            matched.add(base_by_mid[mid])
        elif mid in found_mid and found_mid[mid].get("account_type") == "technical":
            technical.append(mid)
        elif mid in found_mid:
            pass  # existe mas fora da base (status) → AND drop
        else:
            not_found.append(mid)
    for em in req_email:
        if em in base_by_email:
            matched.add(base_by_email[em])
        elif em in found_email and found_email[em].get("account_type") == "technical":
            technical.append(em)
        elif em in found_email:
            pass
        else:
            not_found.append(em)
    return matched, not_found, technical


async def _resolve_audience_core(af: dict) -> dict:
    """Resolve um `AudienceFilter` (dict). OR dentro do tipo, AND entre tipos
    (FR-014). Exclui `technical` (FR-003). Devolve
    `{recipients, per_type, warnings}` — partilhado por envio e preview."""
    base = await _filter_base(af.get("statuses"))
    by_id = {u["id"]: u for u in base}
    type_sets: list[set] = []
    per_type: dict = {}
    warnings: list = []

    if af.get("cargos"):
        want = set(af["cargos"])
        s = {u["id"] for u in base if u.get("cargo") in want}
        type_sets.append(s)
        per_type["cargos"] = len(s)
    if af.get("orgaos"):
        ids: set = set()
        for o in af["orgaos"]:
            ids.update(await members_of_orgao(o))
        s = {u["id"] for u in base if u["id"] in ids}
        type_sets.append(s)
        per_type["orgaos"] = len(s)
    if af.get("categorias"):
        want = set(af["categorias"])
        s = {u["id"] for u in base if u.get("member_category") in want}
        type_sets.append(s)
        per_type["categorias"] = len(s)
    if af.get("statuses"):
        # o status já restringe a base; o "tipo status" é a própria base
        s = set(by_id.keys())
        type_sets.append(s)
        per_type["statuses"] = len(s)
    if af.get("joined_after") or af.get("joined_before"):
        ja, jb = af.get("joined_after"), af.get("joined_before")
        s = {u["id"] for u in base if _matches_period(u, ja, jb)}
        type_sets.append(s)
        per_type["periodo"] = len(s)
    if af.get("nominal_member_ids") or af.get("nominal_emails"):
        s, not_found, technical = await _resolve_nominal(
            af.get("nominal_member_ids") or [], af.get("nominal_emails") or [], base
        )
        type_sets.append(s)
        per_type["nominal"] = len(s)
        if not_found:
            warnings.append({"code": "nominal_not_found", "values": not_found})
        if technical:
            warnings.append({"code": "technical_excluded", "member_ids": technical})

    matched = set.intersection(*type_sets) if type_sets else set()
    recipients = [by_id[i] for i in matched]

    if per_type and len(matched) < min(per_type.values()):
        smallest = min(per_type, key=per_type.get)
        warnings.append({"code": "intersection_reduced", "below": smallest})

    incl = sorted(_UNAPPROVED_STATUSES.intersection(set(af.get("statuses") or [])))
    if incl:
        warnings.append({"code": "includes_unapproved", "statuses": incl})

    return {"recipients": recipients, "per_type": per_type, "warnings": warnings}


async def resolve_audience(audience_filter: dict, *, channel: str, tipo: str) -> list[dict]:
    """Destinatários finais de um `AudienceFilter` para um canal. Mesmos filtros
    de canal que `resolve_recipients` (opt-out informativo, sem email)."""
    core = await _resolve_audience_core(audience_filter)
    sel = core["recipients"]
    if channel == "email":
        if tipo == "informativo":
            sel = [u for u in sel if not u.get("email_opt_out_informativos")]
        sel = [u for u in sel if u.get("email")]
    return sel


async def preview_audience(audience_filter: dict, *, tipo: str, channels: list) -> dict:
    """Preview da audiência (FR-002/FR-014): contagem, amostra (≤5), "…mais N",
    contagem por tipo, contagem após intersecção e avisos. Sem efeitos colaterais."""
    core = await _resolve_audience_core(audience_filter)
    recips = core["recipients"]
    count = len(recips)
    sample = [(u.get("name") or u.get("email") or u["id"]) for u in recips[:5]]
    return {
        "recipients_count": count,
        "sample": sample,
        "more": max(0, count - len(sample)),
        "per_type_counts": core["per_type"],
        "intersected_count": count,
        "warnings": core["warnings"],
    }


def describe_audience(audience_filter: dict) -> str:
    """Rótulo PT legível do filtro para o email (FR-007) — critério, não emails."""
    af = audience_filter or {}
    parts: list = []
    if af.get("orgaos"):
        parts.append(", ".join(_ORGAO_LABELS.get(o, o) for o in af["orgaos"]))
    if af.get("cargos"):
        parts.append("cargos: " + ", ".join(cargo_label(c) for c in af["cargos"]))
    if af.get("categorias"):
        parts.append("categoria " + ", ".join(af["categorias"]))
    if af.get("statuses"):
        parts.append("status " + ", ".join(af["statuses"]))
    ja, jb = af.get("joined_after"), af.get("joined_before")
    if ja and jb:
        parts.append(f"admitidos entre {ja} e {jb}")
    elif ja:
        parts.append(f"admitidos depois de {ja}")
    elif jb:
        parts.append(f"admitidos antes de {jb}")
    if af.get("nominal_member_ids") or af.get("nominal_emails"):
        parts.append("lista nominal")
    return " · ".join(parts) if parts else "audiência personalizada"


async def _persist_result(
    comunicado_id: str, *, status: str, inapp_created: int, email_sent: int, email_failed: int,
    error: Optional[str], snapshot: Optional[dict] = None,
) -> None:
    """Grava o resultado final do dispatch. Tolerante a falhas: se a escrita
    falhar, regista mas não propaga (o dispatch nunca rebenta).

    `snapshot` (caminho v2) acrescenta `audience_resolved` (member_ids),
    `recipients_count`, `failed_member_ids` e `dry_run` (FR-004)."""
    # recipients_total: aproximação deliberada — em dual-canal um sócio pode
    # contar nos dois; usamos o maior fan-out, não a união exacta (spec §6).
    total = max(inapp_created, email_sent + email_failed)
    update = {
        "status": status,
        "inapp_created": inapp_created,
        "email_sent": email_sent,
        "email_failed": email_failed,
        "recipients_total": total,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "error": error,
    }
    if snapshot is not None:
        update.update(snapshot)
    try:
        await db.comunicados.update_one({"id": comunicado_id}, {"$set": update})
    except Exception:  # noqa: BLE001 — persistência best-effort
        logger.exception("Falha ao persistir resultado do comunicado %s", comunicado_id)


async def _resolve_for_doc(doc: dict, *, channel: str, tipo: str) -> list[dict]:
    """Resolve destinatários de um doc, escolhendo o caminho v2
    (`audience_filter`) ou o legado (`segment`)."""
    af = doc.get("audience_filter")
    if af:
        return await resolve_audience(af, channel=channel, tipo=tipo)
    return await resolve_recipients(doc.get("segment", {}), channel=channel, tipo=tipo)


async def dispatch_comunicado(comunicado_id: str) -> dict:
    """Fan-out de um comunicado em `a_enviar`. Idempotente: só corre uma vez
    (transição a_enviar→enviando). Nunca rebenta — falhas viram estado."""
    doc = await db.comunicados.find_one({"id": comunicado_id}, {"_id": 0})
    if not doc or doc.get("status") != "a_enviar":
        return {"skipped": True}
    # CAS: a transição a_enviar→enviando tem de ser atómica. Sem o filtro de
    # status, dois workers/dois cliques simultâneos liam ambos "a_enviar" e
    # disparavam o fan-out duas vezes (email duplicado a todos). Se modified==0,
    # outro processo já reivindicou o envio.
    claimed = await db.comunicados.update_one(
        {"id": comunicado_id, "status": "a_enviar"}, {"$set": {"status": "enviando"}}
    )
    if claimed.modified_count == 0:
        return {"skipped": True}

    channels = doc.get("channels", [])
    tipo = doc.get("tipo", "informativo")
    has_af = bool(doc.get("audience_filter"))
    # dry-run só existe fora de produção (R7/C1): em prod a flag é ignorada à
    # força (o /enviar já a recusa, isto é defesa-em-profundidade).
    effective_dry_run = bool(doc.get("dry_run")) and not IS_PROD
    inapp_created = email_sent = email_failed = 0
    error = None
    resolved: dict = {}  # id -> user (união dos canais, para o snapshot)
    try:
        inapp_recips = await _resolve_for_doc(doc, channel="in_app", tipo=tipo) if "in_app" in channels else []
        email_recips = await _resolve_for_doc(doc, channel="email", tipo=tipo) if "email" in channels else []
        for u in inapp_recips:
            resolved[u["id"]] = u
        for u in email_recips:
            resolved[u["id"]] = u

        if effective_dry_run:
            # não notifica nem envia; conta o que TERIA sido enviado
            inapp_created = len(inapp_recips)
            email_sent = len(email_recips)
            status = "enviado"
        else:
            if inapp_recips:
                await notify_users(
                    [u["id"] for u in inapp_recips],
                    type=doc.get("notification_type", "comunicado"),
                    title=doc["subject"],
                    message=(doc.get("body") or "")[:280],
                    link=doc.get("cta_url"),
                )
                inapp_created = len(inapp_recips)
            if email_recips:
                body = doc.get("body") or ""
                if has_af:
                    # FR-007: mostrar o critério legível, não a lista de emails
                    body = f"Para: {describe_audience(doc['audience_filter'])}\n\n{body}"
                html = comunicado_email_html(
                    doc["subject"],
                    body,
                    doc.get("cta_label"),
                    doc.get("cta_url"),
                    tipo=tipo,
                )
                res = await send_comunicado_batch([u["email"] for u in email_recips], doc["subject"], html)
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
        resolved = {}

    # snapshot da audiência resolvida (só caminho v2, FR-004). member_id quando
    # existe; fallback para o id interno (ex.: contas sem member_id atribuído).
    # Nota: o mapeamento por-destinatário dos emails falhados exigiria um retorno
    # por-recipiente de send_comunicado_batch — a re-tentativa está fora de
    # escopo desta spec, por isso `failed_member_ids` fica vazio (a contagem
    # email_failed reflecte o estado `parcial`/`falhado`).
    snapshot = None
    if has_af:
        snapshot = {
            "audience_resolved": [u.get("member_id") or u["id"] for u in resolved.values()],
            "recipients_count": len(resolved),
            "failed_member_ids": [],
            "dry_run": effective_dry_run,
        }

    await _persist_result(
        comunicado_id,
        status=status,
        inapp_created=inapp_created,
        email_sent=email_sent,
        email_failed=email_failed,
        error=error,
        snapshot=snapshot,
    )
    return {
        "status": status, "inapp_created": inapp_created, "email_sent": email_sent,
        "email_failed": email_failed, "recipients_count": len(resolved), "dry_run": effective_dry_run,
    }


async def dispatch_oficial_auto(
    *, subject: str, body: str, cta_label: str = None, cta_url: str = None, source_kind: str, ref_id: str
) -> Optional[str]:
    """Cria e dispara um comunicado OFICIAL (in-app + email, todos os activos),
    a partir de um gatilho de governança. Anti-duplicado por (source_kind,
    source_ref_id). Devolve o id criado, ou None se já existia."""
    existing = await db.comunicados.find_one({"source_kind": source_kind, "source_ref_id": ref_id}, {"_id": 0, "id": 1})
    if existing:
        return None
    # CTA relativo (ex. /assembleias/{id}) só vira botão se FRONTEND_URL existir
    # (ver comunicado_email_html). Sem base, o comunicado OFICIAL sai SEM botão de
    # acção — sinaliza-o em vez de o suprimir em silêncio (config em falta).
    if cta_label and cta_url and cta_url.startswith("/") and not os.environ.get("FRONTEND_URL", "").strip():
        logger.warning(
            "Comunicado oficial (%s/%s) será enviado SEM botão de acção: cta_url relativo '%s' "
            "exige FRONTEND_URL, que não está definido.",
            source_kind,
            ref_id,
            cta_url,
        )
    cid = str(uuid.uuid4())
    doc = {
        "id": cid,
        "subject": subject,
        "body": body,
        "cta_label": cta_label,
        "cta_url": cta_url,
        "tipo": "oficial",
        "channels": ["in_app", "email"],
        "segment": {"kind": "all_active", "value": None, "user_ids": None},
        "notification_type": "comunicado",
        "status": "a_enviar",
        "recipients_total": 0,
        "inapp_created": 0,
        "email_sent": 0,
        "email_failed": 0,
        "source_kind": source_kind,
        "source_ref_id": ref_id,
        "created_by": "system",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_at": None,
        "error": None,
    }
    try:
        await db.comunicados.insert_one(doc)
    except Exception:  # noqa: BLE001
        # Race vs outra tarefa concorrente (mesmo source_kind/ref_id): o UNIQUE
        # parcial ux_comunicados_source_ref bloqueia ao nível da BD. Tratamos
        # como no-op idempotente — o vencedor da corrida já enviou o email.
        # Re-confirma via find_one para distinguir UniqueViolation de outras
        # falhas (DB indisponível, payload inválido) que devem propagar.
        loser = await db.comunicados.find_one(
            {"source_kind": source_kind, "source_ref_id": ref_id}, {"_id": 0, "id": 1}
        )
        if loser:
            return None
        raise
    await dispatch_comunicado(cid)
    return cid
