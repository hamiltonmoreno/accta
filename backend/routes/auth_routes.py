from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timezone, timedelta
from models import User, UserLogin, Token, PasswordResetRequest, PasswordResetConfirm, SetupAccount
from database import db
from auth import hash_password, verify_password, create_access_token, get_current_user
from email_service import send_welcome_email, send_password_reset_email
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin):
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc or not user_doc.get("password") or not verify_password(credentials.password, user_doc["password"]):
        raise HTTPException(status_code=401, detail="Credenciais invalidas")

    if user_doc.get("status") == "pendente_convite":
        raise HTTPException(
            status_code=403, detail="Conta pendente de ativacao. Use o link de convite para definir a sua senha."
        )

    await db.users.update_one(
        {"email": credentials.email}, {"$set": {"last_login_at": datetime.now(timezone.utc).isoformat()}}
    )

    user_doc.pop("password", None)
    user_doc.pop("invite_token", None)
    if isinstance(user_doc.get("created_at"), str):
        user_doc["created_at"] = datetime.fromisoformat(user_doc["created_at"])
    if user_doc.get("admission_date") and isinstance(user_doc["admission_date"], str):
        user_doc["admission_date"] = datetime.fromisoformat(user_doc["admission_date"])
    if user_doc.get("last_login_at") and isinstance(user_doc["last_login_at"], str):
        user_doc["last_login_at"] = datetime.fromisoformat(user_doc["last_login_at"])

    user = User(**user_doc)
    token = create_access_token({"sub": user.id})
    return Token(access_token=token, token_type="bearer", user=user)


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/setup-account")
@limiter.limit("5/minute")
async def setup_account(request: Request, data: SetupAccount):
    """Invited user sets their password and activates their account."""
    user_doc = await db.users.find_one({"invite_token": data.token, "status": "pendente_convite"}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=400, detail="Token de convite invalido ou conta ja ativada")

    # Valida expiry do token (convites criados antes do TTL ainda funcionam — sem expires_at = legado)
    expires_at_raw = user_doc.get("invite_token_expires_at")
    if expires_at_raw:
        try:
            expires_at = datetime.fromisoformat(expires_at_raw) if isinstance(expires_at_raw, str) else expires_at_raw
            if datetime.now(timezone.utc) > expires_at:
                raise HTTPException(status_code=400, detail="Token de convite expirado. Solicite um novo convite.")
        except (ValueError, TypeError):
            pass  # Token sem formato válido — trata como legado

    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 6 caracteres")

    hashed = hash_password(data.password)
    now = datetime.now(timezone.utc).isoformat()

    await db.users.update_one(
        {"id": user_doc["id"]},
        {
            "$set": {
                "password": hashed,
                "status": "ativo",
                "invite_token": None,
                "last_login_at": now,
            }
        },
    )

    # Parse dates for Token response
    user_doc["password"] = ""
    user_doc["status"] = "ativo"
    user_doc.pop("invite_token", None)
    for field in ["created_at", "admission_date", "last_login_at"]:
        if user_doc.get(field) and isinstance(user_doc[field], str):
            user_doc[field] = datetime.fromisoformat(user_doc[field])
    user_doc["last_login_at"] = datetime.now(timezone.utc)

    user = User(**user_doc)
    token = create_access_token({"sub": user.id})

    # Send welcome email (non-blocking)
    await send_welcome_email(user.name, user.email)

    return {
        "message": "Conta ativada com sucesso!",
        "access_token": token,
        "token_type": "bearer",
        "user": user.model_dump(),
    }


@router.get("/invite/validate")
async def validate_invite(token: str):
    """Check if an invite token is valid and return the invited user's name/email."""
    user_doc = await db.users.find_one(
        {"invite_token": token, "status": "pendente_convite"},
        {"_id": 0, "name": 1, "email": 1, "invite_token_expires_at": 1},
    )
    if not user_doc:
        raise HTTPException(status_code=404, detail="Token de convite invalido ou expirado")

    # Mesma validacao de TTL que setup-account — resposta consistente entre os dois.
    expires_at_raw = user_doc.get("invite_token_expires_at")
    if expires_at_raw:
        try:
            expires_at = datetime.fromisoformat(expires_at_raw) if isinstance(expires_at_raw, str) else expires_at_raw
            if datetime.now(timezone.utc) > expires_at:
                raise HTTPException(status_code=404, detail="Token de convite invalido ou expirado")
        except (ValueError, TypeError):
            pass  # Token sem formato valido — trata como legado

    return {"name": user_doc["name"], "email": user_doc["email"]}


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, data: PasswordResetRequest):
    # Resposta genérica em todos os casos para evitar user enumeration.
    generic_response = {
        "message": "Se o email existir, instrucoes de recuperacao serao enviadas",
        "expires_in": "1 hora",
    }

    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user:
        return generic_response

    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    await db.password_resets.delete_many({"email": data.email})
    await db.password_resets.insert_one(
        {"email": data.email, "token": token, "expires_at": expires_at.isoformat(), "used": False}
    )

    # Build reset URL - prefer explicit FRONTEND_URL env, fallback to request origin
    import os

    frontend_url = os.environ.get("FRONTEND_URL", "").rstrip("/")
    origin = frontend_url or request.headers.get("origin") or request.headers.get("referer", "").rstrip("/")
    reset_url = f"{origin}/reset-password?token={token}" if origin else ""
    await send_password_reset_email(user.get("name", ""), data.email, reset_url, token)

    # Resposta IDENTICA ao caso de email-nao-existe (anti-enumeration por response body).
    return generic_response


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, data: PasswordResetConfirm):
    reset_doc = await db.password_resets.find_one({"token": data.token, "used": False})
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Token invalido ou ja utilizado")

    expires_at = datetime.fromisoformat(reset_doc["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Token expirado. Solicite um novo.")

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 6 caracteres")

    hashed = hash_password(data.new_password)
    await db.users.update_one({"email": reset_doc["email"]}, {"$set": {"password": hashed}})
    await db.password_resets.update_one({"token": data.token}, {"$set": {"used": True}})

    return {"message": "Senha alterada com sucesso. Pode fazer login com a nova senha."}
