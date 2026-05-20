from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timedelta, timezone
from models import User, InviteCreate, RegistrationApprove, RegistrationReject
from database import db
from auth import get_current_user, generate_qr_hash
from helpers import create_audit_log, resolve_link_base
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

    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "status": "pendente_convite",
                "role": data.role,
                "cargo": cargo_final,
                "invite_token": invite_token,
                "invite_token_expires_at": expires_at.isoformat(),
                "registration_review_at": now.isoformat(),
                "registration_reviewer_id": current_user.id,
            }
        },
    )

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
