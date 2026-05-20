from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timedelta, timezone
from models import (
    User,
    InviteCreate,
    RegistrationApprove,
    RegistrationReject,
    PromoteUserRequest,
    DemoteUserRequest,
    TransferCargoRequest,
    CargoMandate,
    CARGOS,
    ROLES_VALID,
    PRIVILEGES,
    CARGO_DEFAULTS,
    CARGO_SEATS,
)
from database import db, transfer_cargo
from auth import get_current_user, generate_qr_hash, has_role_or_privilege
from helpers import create_audit_log, resolve_link_base, notify_users
from email_service import send_invite_email, send_registration_rejected_email
import uuid
import secrets

VALID_APPROVE_ROLES = ["socio", "financeiro", "moderador", "admin"]

router = APIRouter(prefix="/admin", tags=["admin"])

INVITE_TOKEN_TTL_DAYS = 7


@router.post("/invite")
async def invite_user(request: Request, data: InviteCreate, current_user: User = Depends(get_current_user)):
    """Admin creates a new user account and sends invite email."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem convidar utilizadores")

    existing = await db.users.find_one({"email": data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Este email ja esta registado no sistema")

    user_id = str(uuid.uuid4())
    invite_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=INVITE_TOKEN_TTL_DAYS)

    user_doc = {
        "id": user_id,
        "name": data.name,
        "email": data.email,
        "password": "",
        "role": data.role if data.role in ["socio", "financeiro", "moderador"] else "socio",
        "status": "pendente_convite",
        "cargo": data.cargo or "Socio",
        "member_id": data.member_id or f"ACCTA-{str(uuid.uuid4())[:4].upper()}",
        "license_number": data.license_number or "",
        "department": data.department or "",
        "phone_number": data.phone_number or "",
        "admission_date": now.isoformat(),
        "privileges": [],
        "consent_data": False,
        "qr_code_hash": generate_qr_hash(user_id),
        "last_login_at": None,
        "created_at": now.isoformat(),
        "invite_token": invite_token,
        "invite_token_expires_at": expires_at.isoformat(),
    }

    await db.users.insert_one(user_doc)

    await create_audit_log(
        current_user.id,
        "user_invited",
        user_id,
        request=request,
        details={"name": data.name, "email": data.email, "role": data.role, "cargo": data.cargo},
    )

    # Base segura: FRONTEND_URL ou Origin/Referer só se na allowlist CORS
    # (header forjado não pode envenenar o link do email com token válido).
    origin = resolve_link_base(request)
    setup_url = f"{origin}/setup-account?token={invite_token}" if origin else ""

    # Send invite email (non-blocking, don't fail if email fails)
    email_result = await send_invite_email(data.name, data.email, setup_url)

    # NOTA: invite_token NAO devolvido na resposta (nem no path) — evita leak
    # por logs/MITM/historial/APM. O token vai apenas no email ao convidado.
    return {
        "message": f"Convite criado para {data.name}",
        "user_id": user_id,
        "email": data.email,
        "setup_url": "/setup-account",
        "expires_at": expires_at.isoformat(),
        "email_sent": email_result.get("status") == "sent",
    }


@router.get("/invites/pending")
async def get_pending_invites(current_user: User = Depends(get_current_user)):
    """List all users with pending invites."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissao")

    users = await db.users.find({"status": "pendente_convite"}, {"_id": 0, "password": 0, "invite_token": 0}).to_list(
        100
    )

    for u in users:
        for field in ["created_at", "admission_date", "last_login_at"]:
            if u.get(field) and isinstance(u[field], str):
                u[field] = datetime.fromisoformat(u[field])

    return users


@router.delete("/invite/{user_id}")
async def revoke_invite(user_id: str, request: Request, current_user: User = Depends(get_current_user)):
    """Revoke a pending invite."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissao")

    user = await db.users.find_one({"id": user_id, "status": "pendente_convite"})
    if not user:
        raise HTTPException(status_code=404, detail="Convite nao encontrado ou ja aceite")

    await db.users.delete_one({"id": user_id})
    await create_audit_log(
        current_user.id,
        "invite_revoked",
        user_id,
        request=request,
        details={"name": user.get("name"), "email": user.get("email")},
    )

    return {"message": "Convite revogado"}


# ===== AUTO-REGISTO — gestão de pedidos de inscrição (spec-auto-registo) =====


@router.get("/registration-requests")
async def list_registration_requests(
    current_user: User = Depends(get_current_user),
    status: str = "pendente_aprovacao",
    limit: int = 100,
    skip: int = 0,
):
    """Lista pedidos de auto-registo. `status`: pendente_aprovacao (default) ou rejeitado."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissao")

    if status not in ("pendente_aprovacao", "rejeitado"):
        raise HTTPException(status_code=400, detail="Status invalido")

    requests = (
        await db.users.find(
            {"status": status},
            {"_id": 0, "password": 0, "invite_token": 0, "qr_code_hash": 0},
        )
        .sort("registration_request_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )
    return requests


@router.post("/registration-requests/{user_id}/approve")
async def approve_registration(
    user_id: str, request: Request, data: RegistrationApprove, current_user: User = Depends(get_current_user)
):
    """Aprova um pedido: gera invite e reusa o fluxo `setup-account` existente.
    NÃO ativa a conta directamente — o candidato define a password via o link."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem aprovar pedidos")

    if data.role not in VALID_APPROVE_ROLES:
        raise HTTPException(status_code=422, detail="Role invalido")

    user = await db.users.find_one({"id": user_id, "status": "pendente_aprovacao"}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado ou ja processado")

    invite_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=INVITE_TOKEN_TTL_DAYS)
    cargo_final = data.cargo or user.get("cargo_declarado") or user.get("cargo") or "Sócio"

    set_fields = {
        "status": "pendente_convite",
        "role": data.role,
        "cargo": cargo_final,
        "invite_token": invite_token,
        "invite_token_expires_at": expires_at.isoformat(),
        "registration_review_at": now.isoformat(),
        "registration_reviewer_id": current_user.id,
    }
    # spec-identidade-cargos: aprovar com cargo institucional (≠ Sócio) cria a
    # 1ª entrada no cargo_history. Cargo "Sócio" não gera mandato.
    if cargo_final != "Sócio" and cargo_final in CARGOS:
        mandate = CargoMandate(
            cargo=cargo_final,
            role=data.role,
            inicio=now.isoformat(),
            fim=None,
            elected_by=None,
            transitioned_by=current_user.id,
            notes="Atribuído na aprovação do auto-registo",
        ).model_dump()
        set_fields["cargo_history"] = [*(user.get("cargo_history") or []), mandate]

    await db.users.update_one({"id": user_id}, {"$set": set_fields})

    await create_audit_log(
        current_user.id,
        "registration_approved",
        user_id,
        request=request,
        details={"role": data.role, "cargo": cargo_final, "member_id": user.get("member_id")},
    )

    # Base segura: FRONTEND_URL ou Origin/Referer só se na allowlist CORS.
    origin = resolve_link_base(request)
    setup_url = f"{origin}/setup-account?token={invite_token}" if origin else ""
    email_result = await send_invite_email(user.get("name", ""), user.get("email", ""), setup_url)

    return {
        "message": "Pedido aprovado. Email de activação enviado.",
        "email_sent": email_result.get("status") == "sent",
    }


@router.post("/registration-requests/{user_id}/reject")
async def reject_registration(
    user_id: str, request: Request, data: RegistrationReject, current_user: User = Depends(get_current_user)
):
    """Rejeita um pedido: mantém o documento (auditoria + evita re-registo trivial)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem rejeitar pedidos")

    user = await db.users.find_one({"id": user_id, "status": "pendente_aprovacao"}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado ou ja processado")

    now = datetime.now(timezone.utc)
    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "status": "rejeitado",
                "registration_rejection_reason": data.reason or "",
                "registration_review_at": now.isoformat(),
                "registration_reviewer_id": current_user.id,
            }
        },
    )

    await create_audit_log(
        current_user.id,
        "registration_rejected",
        user_id,
        request=request,
        details={"reason": data.reason, "member_id": user.get("member_id")},
    )

    email_result = await send_registration_rejected_email(user.get("name", ""), user.get("email", ""), data.reason)

    return {"message": "Pedido rejeitado.", "email_sent": email_result.get("status") == "sent"}


# ===== CARGOS / MANDATOS (spec-identidade-cargos) =====
#
# RBAC: admin OU privilégio manage_users. Só contas account_type="member"
# participam em mandatos — contas técnicas nunca recebem cargo.

# Sócios reais: account_type "member" ou ausente (retro-compat).
_MEMBER_FILTER = {"$or": [{"account_type": "member"}, {"account_type": {"$exists": False}}]}


def _require_manage_users(current_user: User):
    if not has_role_or_privilege(current_user, ("admin",), "manage_users"):
        raise HTTPException(status_code=403, detail="Sem permissão para gerir cargos")


def _is_member(user: dict) -> bool:
    return user.get("account_type", "member") == "member"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _close_active_mandates(history, fim: str) -> list:
    """Fecha (set `fim`) todos os mandatos activos. Devolve nova lista (imutável)."""
    out = []
    for m in history or []:
        out.append({**m, "fim": fim} if m.get("fim") is None else m)
    return out


def _validate_cargo_role_privs(cargo: str, role: str, privileges):
    if cargo not in CARGOS:
        raise HTTPException(status_code=422, detail=f"Cargo inválido: {cargo}")
    if role not in ROLES_VALID:
        raise HTTPException(status_code=422, detail=f"Role inválido: {role}")
    if privileges is not None:
        invalid = [p for p in privileges if p not in PRIVILEGES]
        if invalid:
            raise HTTPException(status_code=422, detail=f"Privilégios inválidos: {', '.join(invalid)}")


def _resolve_privileges(cargo: str, provided):
    """Privilégios do request, ou os defaults de CARGO_DEFAULTS[cargo]."""
    if provided is not None:
        return list(provided)
    return list(CARGO_DEFAULTS.get(cargo, {}).get("privileges", []))


async def _count_cargo_holders(cargo: str, exclude_ids=()) -> int:
    holders = await db.users.find(
        {"cargo": cargo, "status": "ativo", **_MEMBER_FILTER}, {"_id": 0, "id": 1}
    ).to_list(None)
    return len([h for h in holders if h.get("id") not in set(exclude_ids)])


def _build_mandate(cargo, role, inicio, transitioned_by, elected_by=None, notes=None) -> dict:
    return CargoMandate(
        cargo=cargo,
        role=role,
        inicio=inicio,
        fim=None,
        elected_by=elected_by,
        transitioned_by=transitioned_by,
        notes=notes,
    ).model_dump()


@router.post("/users/{user_id}/promote")
async def promote_user(
    user_id: str, request: Request, data: PromoteUserRequest, current_user: User = Depends(get_current_user)
):
    """Atribui um cargo institucional a um sócio activo (abre novo mandato)."""
    _require_manage_users(current_user)
    _validate_cargo_role_privs(data.cargo, data.role, data.privileges)

    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    if not _is_member(user):
        raise HTTPException(status_code=400, detail="Conta técnica não pode receber cargo")
    if user.get("status") != "ativo":
        raise HTTPException(status_code=400, detail="Apenas sócios activos podem ser promovidos")

    seats = CARGO_SEATS.get(data.cargo, 0)
    if seats > 0 and await _count_cargo_holders(data.cargo, exclude_ids={user_id}) >= seats:
        raise HTTPException(
            status_code=409, detail=f"Cargo '{data.cargo}' já tem o número máximo de titulares ({seats})"
        )

    effective = data.effective_date or _now_iso()
    privileges = _resolve_privileges(data.cargo, data.privileges)
    history = _close_active_mandates(user.get("cargo_history"), effective)
    mandate = _build_mandate(data.cargo, data.role, effective, current_user.id, data.elected_by, data.notes)
    history.append(mandate)

    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": data.role, "cargo": data.cargo, "privileges": privileges, "cargo_history": history}},
    )
    await create_audit_log(
        current_user.id,
        "cargo_promote",
        user_id,
        request=request,
        details={"cargo": data.cargo, "role": data.role, "mandate_id": mandate["id"], "privileges": privileges},
    )
    await notify_users(
        [user_id], "system", "Novo cargo atribuído", f"Foi-lhe atribuído o cargo de {data.cargo}.", "/perfil"
    )
    return {"message": f"{user.get('name', 'Utilizador')} promovido a {data.cargo}.", "cargo_history": history}


@router.post("/users/{user_id}/demote")
async def demote_user(
    user_id: str, request: Request, data: DemoteUserRequest, current_user: User = Depends(get_current_user)
):
    """Encerra o mandato activo do sócio (fim de mandato sem substituto)."""
    _require_manage_users(current_user)

    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    if not _is_member(user):
        raise HTTPException(status_code=400, detail="Conta técnica não tem mandatos")

    effective = data.effective_date or _now_iso()
    history = _close_active_mandates(user.get("cargo_history"), effective)
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": "socio", "cargo": "Sócio", "privileges": [], "cargo_history": history}},
    )
    await create_audit_log(
        current_user.id,
        "cargo_demote",
        user_id,
        request=request,
        details={"previous_cargo": user.get("cargo"), "notes": data.notes},
    )
    await notify_users(
        [user_id], "system", "Fim de mandato", "O seu mandato foi encerrado. Passou a Sócio.", "/perfil"
    )
    return {"message": "Mandato encerrado.", "cargo_history": history}


@router.post("/cargos/transfer")
async def transfer_cargo_endpoint(
    request: Request, data: TransferCargoRequest, current_user: User = Depends(get_current_user)
):
    """Transição atómica de mandato de um sócio para outro (ex.: AGA elege novo
    presidente). Despromove `from_user` e promove `to_user` numa só transacção."""
    _require_manage_users(current_user)
    _validate_cargo_role_privs(data.cargo, data.role, data.privileges)
    if data.from_user_id == data.to_user_id:
        raise HTTPException(status_code=400, detail="Origem e destino têm de ser sócios diferentes")

    from_user = await db.users.find_one({"id": data.from_user_id}, {"_id": 0})
    to_user = await db.users.find_one({"id": data.to_user_id}, {"_id": 0})
    if not from_user or not to_user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    if not _is_member(from_user) or not _is_member(to_user):
        raise HTTPException(status_code=400, detail="Apenas contas de sócio podem transferir cargos")
    if to_user.get("status") != "ativo":
        raise HTTPException(status_code=400, detail="O sócio de destino tem de estar activo")
    if from_user.get("cargo") != data.cargo:
        raise HTTPException(status_code=400, detail=f"O sócio de origem não é titular de '{data.cargo}'")

    seats = CARGO_SEATS.get(data.cargo, 0)
    if seats > 0:
        count = await _count_cargo_holders(data.cargo, exclude_ids={data.from_user_id, data.to_user_id})
        if count + 1 > seats:
            raise HTTPException(
                status_code=409, detail=f"Cargo '{data.cargo}' excederia o máximo de titulares ({seats})"
            )

    effective = data.effective_date or _now_iso()
    transition_id = str(uuid.uuid4())
    privileges = _resolve_privileges(data.cargo, data.privileges)

    from_history = _close_active_mandates(from_user.get("cargo_history"), effective)
    from_set = {"role": "socio", "cargo": "Sócio", "privileges": [], "cargo_history": from_history}

    to_history = _close_active_mandates(to_user.get("cargo_history"), effective)
    mandate = _build_mandate(data.cargo, data.role, effective, current_user.id, data.elected_by, data.notes)
    mandate["transition_id"] = transition_id
    to_history.append(mandate)
    to_set = {"role": data.role, "cargo": data.cargo, "privileges": privileges, "cargo_history": to_history}

    await transfer_cargo(data.from_user_id, data.to_user_id, {"$set": from_set}, {"$set": to_set})

    await create_audit_log(
        current_user.id,
        "cargo_transfer_out",
        data.from_user_id,
        request=request,
        details={"cargo": data.cargo, "transition_id": transition_id, "to_user_id": data.to_user_id},
    )
    await create_audit_log(
        current_user.id,
        "cargo_transfer_in",
        data.to_user_id,
        request=request,
        details={
            "cargo": data.cargo,
            "transition_id": transition_id,
            "from_user_id": data.from_user_id,
            "mandate_id": mandate["id"],
        },
    )
    await notify_users(
        [data.from_user_id], "system", "Fim de mandato", f"O cargo de {data.cargo} foi transferido.", "/perfil"
    )
    await notify_users(
        [data.to_user_id], "system", "Novo cargo atribuído", f"Foi-lhe atribuído o cargo de {data.cargo}.", "/perfil"
    )
    return {"message": f"Cargo '{data.cargo}' transferido.", "transition_id": transition_id}


@router.get("/cargos")
async def list_cargos(current_user: User = Depends(get_current_user)):
    """Estado actual de cada cargo institucional: vagas + titulares activos."""
    _require_manage_users(current_user)
    members = await db.users.find(
        {"status": "ativo", **_MEMBER_FILTER},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "member_id": 1, "cargo": 1, "cargo_history": 1},
    ).to_list(None)

    by_cargo = {}
    for m in members:
        cargo = m.get("cargo")
        if cargo not in CARGOS or cargo == "Sócio":
            continue
        since = next(
            (md.get("inicio") for md in (m.get("cargo_history") or []) if md.get("cargo") == cargo and md.get("fim") is None),
            None,
        )
        by_cargo.setdefault(cargo, []).append(
            {
                "id": m["id"],
                "name": m.get("name"),
                "email": m.get("email"),
                "member_id": m.get("member_id"),
                "since": since,
            }
        )

    cargos = [
        {"cargo": c, "seats": CARGO_SEATS.get(c, 0), "holders": by_cargo.get(c, [])}
        for c in CARGOS
        if c != "Sócio"
    ]
    return {"cargos": cargos}


@router.get("/cargos/candidates")
async def list_cargo_candidates(
    current_user: User = Depends(get_current_user),
    q: str = "",
    status: str = "ativo",
    exclude_cargo: str = "",
    limit: int = 50,
):
    """Sócios elegíveis para atribuição/transferência. Nunca devolve contas técnicas."""
    _require_manage_users(current_user)
    candidates = await db.users.find(
        {"status": status, **_MEMBER_FILTER},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "member_id": 1, "cargo": 1},
    ).to_list(None)

    ql = q.strip().lower()
    out = []
    for c in candidates:
        if exclude_cargo and c.get("cargo") == exclude_cargo:
            continue
        if ql and ql not in f"{c.get('name', '')} {c.get('email', '')} {c.get('member_id', '')}".lower():
            continue
        out.append(c)
        if len(out) >= limit:
            break
    return {"candidates": out}
