from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from database import client, UPLOAD_DIR, ensure_indexes
from routes import api_router
import os
import logging

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


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

app.add_middleware(
    CORSMiddleware,
    allow_credentials=len(cors_origins) > 0,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _validate_runtime_config():
    """
    Surface misconfigured environment variables loudly on startup.

    SECRET_KEY is enforced as required by auth.py (raises on import).
    The variables here cause silent runtime failures (emails not sent,
    invite/reset links broken) so we log them at WARNING level instead
    of failing — local dev often runs without email.
    """
    if not os.environ.get("RESEND_API_KEY"):
        logger.warning(
            "RESEND_API_KEY is not set — invite/reset/welcome emails will be skipped silently. Set it in production."
        )
    if not os.environ.get("FRONTEND_URL"):
        logger.warning(
            "FRONTEND_URL is not set — invite and password-reset links will "
            "fall back to the request Origin header. Set FRONTEND_URL=https://your.domain"
        )
    if not cors_origins and cors_origins_raw != "*":
        logger.warning("CORS_ORIGINS is empty — defaulting to '*'. Set an explicit list in production for security.")


@app.on_event("startup")
async def startup_event():
    _validate_runtime_config()
    await ensure_indexes()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
