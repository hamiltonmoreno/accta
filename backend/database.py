from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from dotenv import load_dotenv
import os
import logging

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env", override=False)

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)


async def ensure_indexes():
    """Create production-grade MongoDB indexes. Idempotent (safe to re-run)."""
    try:
        await db.users.create_index("email", unique=True)
        await db.users.create_index("invite_token", sparse=True)
        await db.users.create_index("id")
        await db.password_resets.create_index("token")
        await db.password_resets.create_index("email")
        await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
        await db.notifications.create_index([("user_id", 1), ("read", 1)])
        await db.wall_posts.create_index([("status", 1), ("created_at", -1)])
        await db.transactions.create_index([("date", -1)])
        await db.events.create_index([("date", 1)])
        await db.audit_logs.create_index([("created_at", -1)])
        await db.document_accesses.create_index([("user_id", 1), ("accessed_at", -1)])
        await db.document_accesses.create_index([("user_id", 1), ("document_id", 1)])
        await db.benefit_validations.create_index([("user_id", 1), ("validated_at", -1)])
        logger.info("MongoDB indexes ensured")
    except Exception as e:
        logger.warning(f"Index creation warning (non-fatal): {e}")
