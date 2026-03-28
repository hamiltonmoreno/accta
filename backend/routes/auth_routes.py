from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List
from models import User, UserCreate, UserLogin, Token
from database import db
from auth import hash_password, verify_password, generate_qr_hash, create_access_token, get_current_user

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
