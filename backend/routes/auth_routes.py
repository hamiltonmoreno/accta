from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone, timedelta
from typing import List
from models import User, UserCreate, UserLogin, Token, PasswordResetRequest, PasswordResetConfirm
from database import db
from auth import hash_password, verify_password, generate_qr_hash, create_access_token, get_current_user
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email já registrado")

    user = User(**user_data.model_dump(exclude={"password"}))
    user.qr_code_hash = generate_qr_hash(user.id)

    user_dict = user.model_dump()
    user_dict['password'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    if user_dict.get('admission_date'):
        user_dict['admission_date'] = user_dict['admission_date'].isoformat()
    if user_dict.get('last_login_at'):
        user_dict['last_login_at'] = user_dict['last_login_at'].isoformat()

    await db.users.insert_one(user_dict)
    return user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    from datetime import timezone
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc or not verify_password(credentials.password, user_doc['password']):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    await db.users.update_one(
        {"email": credentials.email},
        {"$set": {"last_login_at": datetime.now(timezone.utc).isoformat()}}
    )

    user_doc.pop('password', None)
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    if user_doc.get('admission_date') and isinstance(user_doc['admission_date'], str):
        user_doc['admission_date'] = datetime.fromisoformat(user_doc['admission_date'])
    if user_doc.get('last_login_at') and isinstance(user_doc['last_login_at'], str):
        user_doc['last_login_at'] = datetime.fromisoformat(user_doc['last_login_at'])

    user = User(**user_doc)
    token = create_access_token({"sub": user.id})
    return Token(access_token=token, token_type="bearer", user=user)


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
async def forgot_password(data: PasswordResetRequest):
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Email não encontrado no sistema")

    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    await db.password_resets.delete_many({"email": data.email})
    await db.password_resets.insert_one({
        "email": data.email,
        "token": token,
        "expires_at": expires_at.isoformat(),
        "used": False
    })

    # NOTE: Em produção, enviar email com o link de reset.
    # Para demonstração, o token é retornado na resposta.
    return {
        "message": "Token de recuperação gerado com sucesso",
        "demo_token": token,
        "expires_in": "1 hora"
    }


@router.post("/reset-password")
async def reset_password(data: PasswordResetConfirm):
    reset_doc = await db.password_resets.find_one({"token": data.token, "used": False})
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Token inválido ou já utilizado")

    expires_at = datetime.fromisoformat(reset_doc['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Token expirado. Solicite um novo.")

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 6 caracteres")

    hashed = hash_password(data.new_password)
    await db.users.update_one({"email": reset_doc['email']}, {"$set": {"password": hashed}})
    await db.password_resets.update_one({"token": data.token}, {"$set": {"used": True}})

    return {"message": "Senha alterada com sucesso. Pode fazer login com a nova senha."}
