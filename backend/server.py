from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from auth import COOKIE_NAME
from database import client, db, UPLOAD_DIR, ensure_indexes
from routes import api_router
import os
import logging
import uuid
import hashlib
from datetime import datetime, timezone

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Defense-in-depth: adiciona headers HTTP recomendados pelo OWASP."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # Apenas em respostas HTML ou JSON da nossa API. Static files do Mount
        # já são servidos pelo nginx em prod, mas não custa duplicar aqui.
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(self), camera=(), microphone=(), interest-cohort=()",
        )
        # HSTS só em produção (atrás de TLS) — assumimos que ENVIRONMENT=production.
        if os.environ.get("ENVIRONMENT") == "production":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response


class CSRFOriginCheckMiddleware(BaseHTTPMiddleware):
    """CSRF protection para cookie-based auth (Sprint 10).

    Codex P2 #25 flagged: com SameSite=None+Secure, browsers enviam o cookie
    de sessao em requests cross-site (incluindo POST/DELETE de attacker.com).
    Validamos Origin/Referer contra CORS_ORIGINS — browsers nao deixam JS
    forjar Origin, logo CSRF e bloqueado.

    So aplica a:
    - Metodos unsafe (POST/PUT/PATCH/DELETE)
    - Requests com cookie de sessao (clientes header-only sao seguros porque
      o atacante nao consegue ler o token de outra origem)
    """

    UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

    def __init__(self, app, allowed_origins):
        super().__init__(app)
        self.allowed_origins = set(allowed_origins)

    async def dispatch(self, request, call_next):
        if request.method in self.UNSAFE_METHODS and request.cookies.get(COOKIE_NAME) and self.allowed_origins:
            origin = request.headers.get("origin")
            if not origin:
                # Fallback para Referer — extrai scheme://host[:port]
                referer = request.headers.get("referer", "")
                if referer:
                    parts = referer.split("/", 3)
                    origin = "/".join(parts[:3]) if len(parts) >= 3 else None
            if origin and origin not in self.allowed_origins:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF: Origin nao permitido"},
                )
            # Sem Origin nem Referer + cookie presente: provavelmente non-browser
            # mal configurado. Bloquear para defesa em profundidade.
            if not origin:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF: Origin/Referer ausente em request com cookie"},
                )
        return await call_next(request)


app.add_middleware(SecurityHeadersMiddleware)


@api_router.get("/")
async def root():
    return {"message": "ACCTA Portal API v1.0"}


@api_router.get("/health")
async def health_check():
    try:
        await client.admin.command("ping")
        return {"status": "ok", "database": "connected"}
    except Exception:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Database unavailable")


# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(api_router)

cors_origins_raw = os.environ.get("CORS_ORIGINS", "")
cors_origins = (
    [o.strip() for o in cors_origins_raw.split(",") if o.strip()]
    if cors_origins_raw and cors_origins_raw != "*"
    else []
)

# Em producao, recusamos arrancar com CORS=* (security misconfig).
if not cors_origins and os.environ.get("ENVIRONMENT") == "production":
    raise RuntimeError(
        "CORS_ORIGINS must be an explicit list in production. "
        "Set CORS_ORIGINS=https://your.domain (separe por virgulas para varias)."
    )

app.add_middleware(
    CORSMiddleware,
    allow_credentials=len(cors_origins) > 0,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# CSRF middleware corre ANTES da resolucao do route — protege todos os
# endpoints state-changing que usem cookie auth.
app.add_middleware(CSRFOriginCheckMiddleware, allowed_origins=cors_origins)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _validate_runtime_config():
    if not os.environ.get("RESEND_API_KEY"):
        logger.warning(
            "RESEND_API_KEY is not set - invite/reset/welcome emails will be skipped silently. Set it in production."
        )
    if not os.environ.get("FRONTEND_URL"):
        logger.warning(
            "FRONTEND_URL is not set - invite and password-reset links will fall back to the request Origin header. Set FRONTEND_URL=https://your.domain"
        )
    if not cors_origins and cors_origins_raw != "*":
        logger.warning("CORS_ORIGINS is empty - defaulting to '*'. Set an explicit list in production for security.")


async def _bootstrap_admin_if_requested():
    """Create initial admin from env vars if BOOTSTRAP_ADMIN_EMAIL/PASSWORD are set
    and the email does not already exist. Idempotent. Remove env vars after first run.
    """
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL")
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")
    name = os.environ.get("BOOTSTRAP_ADMIN_NAME", "Administrador ACCTA")
    if not email or not password:
        return
    try:
        existing = await db.users.find_one({"email": email})
        if existing:
            logger.info(f"BOOTSTRAP_ADMIN: user {email} already exists - skipping.")
            return
        from auth import hash_password

        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        admin_doc = {
            "id": user_id,
            "name": name,
            "email": email,
            "password": hash_password(password),
            "role": "admin",
            "status": "ativo",
            "cargo": "Administrador",
            "member_id": "ACCTA-ADMIN",
            "license_number": "",
            "department": "Direcao",
            "phone_number": "",
            "admission_date": now,
            "privileges": [
                "manage_users",
                "manage_finances",
                "manage_events",
                "manage_documents",
                "moderate_content",
                "manage_benefits",
                "view_audit_logs",
            ],
            "consent_data": True,
            "qr_code_hash": hashlib.sha256(f"accta-wallet-{user_id}".encode()).hexdigest(),
            "last_login_at": None,
            "created_at": now,
            "bio": "",
            "photo_url": "",
        }
        await db.users.insert_one(admin_doc)
        logger.info(
            f"BOOTSTRAP_ADMIN: created admin user {email} (id={user_id}). Remove BOOTSTRAP_ADMIN_* env vars now."
        )
    except Exception as e:
        logger.error(f"BOOTSTRAP_ADMIN: failed to create admin - {e}")


@app.on_event("startup")
async def startup_event():
    _validate_runtime_config()
    await ensure_indexes()
    await _bootstrap_admin_if_requested()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
