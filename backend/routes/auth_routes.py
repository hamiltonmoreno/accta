from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from datetime import datetime, timezone, timedelta
from jose import JWTError, jwt
from models import (
    User,
    UserLogin,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
    SetupAccount,
    RegistrationRequest,
    Patrocinio,
    CARGOS_DECLARADOS,
)
from database import db, next_member_id
from auth import (
    ALGORITHM,
    SECRET_KEY,
    _extract_token,
    clear_session_cookie,
    create_access_token,
    generate_qr_hash,
    get_current_user,
    hash_password,
    revoke_token,
    set_session_cookie,
    verify_password,
)
from email_service import send_welcome_email, send_password_reset_email
from helpers import (
    LOCKOUT_WINDOW_MINUTES,
    alert_admins_account_locked,
    create_audit_log,
    is_account_locked,
    notify_admins,
    notify_users,
    record_failed_login,
    reset_failed_logins,
    resolve_link_base,
)
from permissions import is_voting_member
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid


router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, response: Response, credentials: UserLogin):
    # Account-level lockout — verifica antes de tudo (precede ate user lookup,
    # para que tentativas em emails inexistentes nao consigam confirmar
    # existencia indirectamente atraves do timing do bcrypt).
    locked_until = await is_account_locked(credentials.email)
    if locked_until is not None:
        await create_audit_log(
            "anonymous",
            "login_failed",
            request=request,
            details={"email": credentials.email, "reason": "account_locked"},
        )
        raise HTTPException(
            status_code=423,  # 423 Locked
            detail="Conta temporariamente bloqueada por excesso de tentativas. Tente novamente em alguns minutos.",
            headers={"Retry-After": str(LOCKOUT_WINDOW_MINUTES * 60)},
        )

    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc or not user_doc.get("password") or not verify_password(credentials.password, user_doc["password"]):
        # Conta tentativa falhada para futuro lockout (avaliado por is_account_locked).
        just_locked = await record_failed_login(credentials.email, ip=request.client.host if request.client else None)
        await create_audit_log(
            user_doc["id"] if user_doc else "anonymous",
            "login_failed",
            request=request,
            details={"email": credentials.email, "reason": "invalid_credentials"},
        )
        if just_locked:
            await alert_admins_account_locked(credentials.email)
        raise HTTPException(status_code=401, detail="Credenciais invalidas")

    # Só contas ATIVAS autenticam. Bloquear apenas pendente_convite deixava
    # pendente_aprovacao/rejeitado/inativo entrar: como forgot/reset-password
    # não filtram por status, essas contas podiam definir uma senha e contornar
    # a aprovação do admin ou a desativação. Allowlist explícita = fail-closed.
    status = user_doc.get("status")
    if status != "ativo":
        await create_audit_log(
            user_doc["id"], "login_failed", request=request, details={"reason": f"status_{status}"}
        )
        if status == "pendente_convite":
            raise HTTPException(
                status_code=403, detail="Conta pendente de ativacao. Use o link de convite para definir a sua senha."
            )
        raise HTTPException(status_code=403, detail="Conta inativa. Contacte a administracao.")

    # Login sucesso — limpa contador de falhas para que utilizador legitimo
    # nao seja afectado por tentativas anteriores erradas/atacante.
    await reset_failed_logins(credentials.email)
    await db.users.update_one(
        {"email": credentials.email}, {"$set": {"last_login_at": datetime.now(timezone.utc).isoformat()}}
    )
    await create_audit_log(user_doc["id"], "login_success", request=request)

    # Remove campos sensíveis antes de serializar (defensivo: o User ignora
    # extras, mas `password`/`invite_token` nunca devem sair no body).
    for _k in ("password", "invite_token"):
        user_doc.pop(_k, None)

    user = User(**user_doc)
    token = create_access_token({"sub": user.id})
    # Sprint 10 — set httpOnly cookie. Token ainda e devolvido no body para
    # compat com testes legados / clientes nao-browser. Frontend novo nao usa.
    set_session_cookie(response, token)
    return Token(access_token=token, token_type="bearer", user=user)


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    """Revoga o token actual adicionando o jti ao blocklist (tokens_revoked).
    Le token de cookie OR header (transition-friendly). Limpa cookie no fim.
    O token continua criptograficamente valido ate ao exp original, mas
    get_current_user passa a rejeita-lo. TTL index purga a entry depois do exp.
    """
    token = _extract_token(request)
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                try:
                    await revoke_token(jti, int(exp), current_user.id)
                except Exception:
                    pass  # duplicate jti (logout 2x): ignora
        except JWTError:
            pass  # token decode falhou — clear cookie de qualquer forma
    clear_session_cookie(response)
    await create_audit_log(current_user.id, "logout", request=request)
    return {"message": "Sessão encerrada"}


@router.get("/registration-options")
async def registration_options():
    """Opções públicas para o formulário de auto-registo (cargos declaráveis).
    Evita hardcode no frontend — fonte única em models.CARGOS_DECLARADOS."""
    return {"cargos": CARGOS_DECLARADOS}


@router.post("/register", status_code=201)
@limiter.limit("3/hour")
async def register(request: Request, data: RegistrationRequest):
    """Auto-registo público de sócio. Cria um pedido `pendente_aprovacao` —
    NÃO ativa a conta nem define password (isso só após aprovação do admin,
    via o fluxo `setup-account` existente). Anti-spam: rate-limit + honeypot.
    """
    # Honeypot: campo `website` é escondido no form. Bots preenchem-no →
    # devolvemos 201 falso e descartamos silenciosamente (não cria registo).
    if data.website:
        return {"message": "Pedido recebido. Receberá um email quando for analisado.", "request_id": str(uuid.uuid4())}

    if not data.consent_data:
        raise HTTPException(status_code=400, detail="É necessário consentir o tratamento dos seus dados.")

    if data.cargo_declarado not in CARGOS_DECLARADOS:
        raise HTTPException(status_code=422, detail="Cargo declarado inválido.")

    # Anti-enumeração: mensagens neutras, sem confirmar/desmentir além do necessário.
    existing = await db.users.find_one({"email": data.email}, {"_id": 0, "status": 1})
    if existing:
        status = existing.get("status")
        if status == "pendente_aprovacao":
            raise HTTPException(status_code=409, detail="Já existe um pedido em análise para este email.")
        if status == "rejeitado":
            raise HTTPException(status_code=409, detail="Não foi possível processar este pedido.")
        raise HTTPException(status_code=409, detail="Já existe uma conta com este email.")

    # Patrocínio de admissão (Art. 8.3): 2 padrinhos sócios activos distintos.
    # Mensagens neutras (anti-enumeração) — não revelam quem existe.
    sponsors = data.sponsors or []
    if len(sponsors) != 2:
        raise HTTPException(status_code=422, detail="Indique 2 padrinhos (sócios activos) — Art. 8.3.")
    resolved_sponsors = []
    for ident in sponsors:
        ident = (ident or "").strip()
        q = {"email": ident} if "@" in ident else {"member_id": ident}
        s = await db.users.find_one(
            {**q, "status": "ativo"},
            {
                "_id": 0,
                "id": 1,
                "member_id": 1,
                "account_type": 1,
                "status": 1,
                "member_category": 1,
                "rights_suspended_until": 1,
            },
        )
        if not s or not is_voting_member(s):
            raise HTTPException(status_code=422, detail="Padrinho inválido. Indique 2 sócios activos.")
        resolved_sponsors.append(s)
    if resolved_sponsors[0]["id"] == resolved_sponsors[1]["id"]:
        raise HTTPException(status_code=422, detail="Os 2 padrinhos têm de ser distintos.")

    user_id = str(uuid.uuid4())
    member_id = await next_member_id()
    now = datetime.now(timezone.utc).isoformat()

    user_doc = {
        "id": user_id,
        "name": data.name,
        "email": data.email,
        "password": "",  # definida só no setup-account, após aprovação
        "role": "socio",  # sempre socio no submit; admin decide o role ao aprovar
        "status": "pendente_aprovacao",
        "cargo_declarado": data.cargo_declarado,
        "cargo": data.cargo_declarado,  # campo legado; admin pode editar ao aprovar
        "member_id": member_id,  # sequencial e imutável
        "license_number": "",
        "department": data.department or "",
        "phone_number": data.phone_number or "",
        "admission_date": None,
        "privileges": [],
        "consent_data": True,
        "qr_code_hash": generate_qr_hash(user_id),
        "last_login_at": None,
        "created_at": now,
        "registration_request_at": now,
    }
    await db.users.insert_one(user_doc)

    # Cria 2 pedidos de patrocínio (pendente) e notifica cada padrinho (Art. 8.3).
    for s in resolved_sponsors:
        patrocinio = Patrocinio(
            candidate_id=user_id,
            sponsor_user_id=s["id"],
            sponsor_member_id=s.get("member_id"),
            created_at=now,
        )
        await db.patrocinios.insert_one(patrocinio.model_dump())
    await notify_users(
        [s["id"] for s in resolved_sponsors],
        "system",
        "Pedido de patrocínio",
        f"{data.name} indicou-o como padrinho de admissão (Art. 8.3). Confirme no portal.",
        link="/participacao/patrocinios",
    )

    await notify_admins(
        "system",
        "Novo pedido de inscrição",
        f"{data.name} ({data.cargo_declarado}) submeteu um pedido de inscrição.",
        "/admin/pedidos-inscricao",
    )
    # Actor é o próprio candidato (não há admin envolvido neste passo).
    await create_audit_log(
        user_id,
        "registration_requested",
        user_id,
        request=request,
        details={"cargo_declarado": data.cargo_declarado, "member_id": member_id},
    )

    return {"message": "Pedido recebido. Receberá um email quando for analisado.", "request_id": user_id}


@router.post("/setup-account")
@limiter.limit("5/minute")
async def setup_account(request: Request, response: Response, background_tasks: BackgroundTasks, data: SetupAccount):
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

    user_doc["password"] = ""
    user_doc["status"] = "ativo"
    user_doc.pop("invite_token", None)
    user_doc["last_login_at"] = datetime.now(timezone.utc).isoformat()

    user = User(**user_doc)
    token = create_access_token({"sub": user.id})

    await create_audit_log(user.id, "account_activated", request=request)

    # Send welcome email — realmente non-blocking: não atrasa a resposta de
    # activação se a Resend estiver lenta/indisponível.
    background_tasks.add_task(send_welcome_email, user.name, user.email)

    # Sprint 10 — auto-login via cookie apos setup.
    set_session_cookie(response, token)
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
    # Defesa-em-profundidade: só contas ativas recebem token de reset (o gate
    # real é no login). Resposta genérica mantém-se para não revelar o status.
    if not user or user.get("status") != "ativo":
        return generic_response

    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    await db.password_resets.delete_many({"email": data.email})
    await db.password_resets.insert_one(
        {"email": data.email, "token": token, "expires_at": expires_at.isoformat(), "used": False}
    )

    # Base segura: FRONTEND_URL ou Origin/Referer só se na allowlist CORS.
    # Sem origem confiável → reset_url vazio (não envia link envenenado).
    origin = resolve_link_base(request)
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
    # password_changed_at invalida tokens/sessões emitidos ANTES do reset
    # (auth.token_predates_password_change) — expulsa um intruso que mantenha
    # uma sessão aberta. O utilizador volta a entrar com a nova senha.
    await db.users.update_one(
        {"email": reset_doc["email"]},
        {"$set": {"password": hashed, "password_changed_at": datetime.now(timezone.utc).isoformat()}},
    )
    await db.password_resets.update_one({"token": data.token}, {"$set": {"used": True}})

    # Audit log da reset bem-sucedida — util para investigacao de account takeover.
    user_doc = await db.users.find_one({"email": reset_doc["email"]}, {"_id": 0, "id": 1})
    if user_doc:
        await create_audit_log(user_doc["id"], "password_reset_completed", request=request)

    return {"message": "Senha alterada com sucesso. Pode fazer login com a nova senha."}
