from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timezone
from models import User, InviteCreate
from database import db
from auth import get_current_user, generate_qr_hash
from helpers import create_audit_log
from email_service import send_invite_email
import uuid
import secrets

router = APIRouter(prefix="/admin", tags=["admin"])


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
    now = datetime.now(timezone.utc).isoformat()

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
        "admission_date": now,
        "privileges": [],
        "consent_data": False,
        "qr_code_hash": generate_qr_hash(user_id),
        "last_login_at": None,
        "created_at": now,
        "invite_token": invite_token,
    }

    await db.users.insert_one(user_doc)

    await create_audit_log(
        current_user.id,
        f"Convidou novo utilizador: {data.name} ({data.email}) como {data.role}",
        user_id
    )

    # Build full setup URL - prefer explicit FRONTEND_URL env (prod),
    # fallback to request origin (works when frontend+backend same domain)
    import os
    frontend_url = os.environ.get("FRONTEND_URL", "").rstrip("/")
    origin = frontend_url or request.headers.get("origin") or request.headers.get("referer", "").rstrip("/")
    setup_url = f"{origin}/setup-account?token={invite_token}"

    # Send invite email (non-blocking, don't fail if email fails)
    email_result = await send_invite_email(data.name, data.email, setup_url)

    return {
        "message": f"Convite criado para {data.name}",
        "user_id": user_id,
        "email": data.email,
        "invite_token": invite_token,
        "setup_url": f"/setup-account?token={invite_token}",
        "email_sent": email_result.get("status") == "sent",
    }


@router.get("/invites/pending")
async def get_pending_invites(current_user: User = Depends(get_current_user)):
    """List all users with pending invites."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissao")

    users = await db.users.find(
        {"status": "pendente_convite"},
        {"_id": 0, "password": 0, "invite_token": 0}
    ).to_list(100)

    for u in users:
        for field in ['created_at', 'admission_date', 'last_login_at']:
            if u.get(field) and isinstance(u[field], str):
                u[field] = datetime.fromisoformat(u[field])

    return users


@router.delete("/invite/{user_id}")
async def revoke_invite(user_id: str, current_user: User = Depends(get_current_user)):
    """Revoke a pending invite."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissao")

    user = await db.users.find_one({"id": user_id, "status": "pendente_convite"})
    if not user:
        raise HTTPException(status_code=404, detail="Convite nao encontrado ou ja aceite")

    await db.users.delete_one({"id": user_id})
    await create_audit_log(current_user.id, f"Revogou convite de {user.get('name', user_id)}", user_id)

    return {"message": "Convite revogado"}
