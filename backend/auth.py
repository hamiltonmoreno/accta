from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timezone, timedelta
from typing import Optional
from database import db
import os
import uuid
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
security = HTTPBearer()
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required. Set it in backend/.env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_qr_hash(user_id: str) -> str:
    return hashlib.sha256(f"accta-cv-{user_id}-{uuid.uuid4()}".encode()).hexdigest()


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # jti = identificador unico do token, usado pelo blocklist em /auth/logout.
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def is_token_revoked(jti: Optional[str]) -> bool:
    """True se o jti foi adicionado ao blocklist (logout). False se jti=None
    (tokens legados sem jti — backward-compat: consideram-se validos)."""
    if not jti:
        return False
    found = await db.tokens_revoked.find_one({"jti": jti}, {"_id": 1})
    return found is not None


async def revoke_token(jti: str, exp_unix: int, user_id: str):
    """Adiciona jti ao blocklist. `exp_unix` e usado pelo TTL index da
    coleccao para auto-purge depois do token expirar naturalmente."""
    await db.tokens_revoked.insert_one(
        {
            "jti": jti,
            "user_id": user_id,
            "expires_at": datetime.fromtimestamp(exp_unix, tz=timezone.utc),
            "revoked_at": datetime.now(timezone.utc).isoformat(),
        }
    )


async def revoke_token_from_credentials(
    credentials: HTTPAuthorizationCredentials, user_id: str
) -> None:
    """Decodifica o token e adiciona o jti ao blocklist. Usado por /auth/logout."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        try:
            await revoke_token(jti, int(exp), user_id)
        except Exception:
            # Duplicate jti (logout duas vezes): ignora silenciosamente.
            pass


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from models import User

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        # Blocklist check: token revogado por logout / forced-revoke pelo admin.
        if await is_token_revoked(payload.get("jti")):
            raise HTTPException(status_code=401, detail="Sessão expirada. Faça login novamente.")
        user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user_doc is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return User(**user_doc)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


_optional_security = HTTPBearer(auto_error=False)


async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(_optional_security)):
    """Auth opcional: devolve User se token valido, None se nao houver token ou for invalido.
    Para endpoints que servem conteudo publico mas que ajustam o output quando autenticados.
    """
    if credentials is None:
        return None
    try:
        return await get_user_from_token(credentials.credentials)
    except Exception:
        return None


async def get_user_from_token(token: str):
    """Validate a JWT token string and return the user. Used by SSE endpoints."""
    from models import User

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        # Honra blocklist para consistencia com get_current_user.
        if await is_token_revoked(payload.get("jti")):
            return None
        user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user_doc:
            return None
        return User(**user_doc)
    except JWTError:
        return None
