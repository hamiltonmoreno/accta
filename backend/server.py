from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from database import client, UPLOAD_DIR
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


# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(api_router)

cors_origins_raw = os.environ.get('CORS_ORIGINS', '')
cors_origins = [o.strip() for o in cors_origins_raw.split(',') if o.strip()] if cors_origins_raw and cors_origins_raw != '*' else []

app.add_middleware(
    CORSMiddleware,
    allow_credentials=len(cors_origins) > 0,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
