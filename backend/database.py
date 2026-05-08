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
    """Create production-grade MongoDB indexes. Idempotent (safe to re-run).

    Em colecoes pre-existentes pode ser preciso `db.<col>.dropIndex(...)` se
    um indice antigo entrar em conflito (e.g., wall_posts antigo sobre
    `status` que era schema errado — agora reusamos para o campo correcto).
    """
    try:
        # ---- users ----
        await db.users.create_index("email", unique=True)
        await db.users.create_index("invite_token", sparse=True)
        await db.users.create_index("id")
        # find({"status": "ativo"}) é frequente em quotas / notify_all_active_users.
        await db.users.create_index("status")
        # find({"role": "admin"}) usado em notify_admins.
        await db.users.create_index("role")

        # ---- auth ----
        await db.password_resets.create_index("token")
        await db.password_resets.create_index("email")

        # ---- notifications ----
        await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
        await db.notifications.create_index([("user_id", 1), ("read", 1)])

        # ---- wall ----
        # approved + ordenacao usados em GET /wall e GET /wall/pending.
        await db.wall_posts.create_index([("approved", 1), ("pinned", -1), ("created_at", -1)])
        await db.wall_posts.create_index([("user_id", 1), ("approved", 1)])
        await db.wall_comments.create_index([("post_id", 1), ("created_at", -1)])

        # ---- transactions ----
        await db.transactions.create_index([("date", -1)])
        # generate_quotas filtra por (category, date).
        await db.transactions.create_index([("category", 1), ("date", -1)])
        await db.transactions.create_index([("user_id", 1), ("date", -1)])
        await db.transactions.create_index("type")

        # ---- events ----
        await db.events.create_index([("date", 1)])
        # GET /events/featured filtra por (visibility, date>=now).
        await db.events.create_index([("visibility", 1), ("date", 1)])
        # Multikey index para count_documents({"attendees": uid}).
        await db.events.create_index("attendees")

        # ---- projects ----
        await db.projects.create_index([("status", 1), ("created_at", -1)])
        await db.projects.create_index("team_members")  # multikey
        await db.projects.create_index("created_by")
        await db.project_comments.create_index([("project_id", 1), ("created_at", -1)])
        await db.project_milestones.create_index([("project_id", 1), ("status", 1)])

        # ---- polls / votes ----
        await db.polls.create_index([("status", 1), ("created_at", -1)])
        # count_documents({"user_id": uid}) em report.py. Nao unique para nao
        # falhar se houver dados legados duplicados — adicionar uniqueness e
        # PR separado depois de validar a coleccao.
        await db.user_votes.create_index([("user_id", 1), ("poll_id", 1)])
        await db.user_votes.create_index("poll_id")

        # ---- gallery ----
        await db.gallery_photos.create_index([("album_id", 1), ("status", 1)])
        await db.gallery_photos.create_index([("status", 1), ("created_at", -1)])
        await db.gallery_photos.create_index("uploaded_by")

        # ---- documents / posts ----
        await db.documents.create_index("visibility")
        await db.posts.create_index([("visibility", 1), ("created_at", -1)])

        # ---- invoices ----
        await db.invoices.create_index([("user_id", 1), ("status", 1)])
        await db.invoices.create_index([("status", 1), ("created_at", -1)])

        # ---- audit ----
        await db.audit_logs.create_index([("created_at", -1)])
        # audit log enrichment: queries por actor + por target em incidentes.
        await db.audit_logs.create_index([("user_id", 1), ("created_at", -1)])
        await db.audit_logs.create_index([("target_id", 1), ("created_at", -1)])
        await db.audit_logs.create_index([("action", 1), ("created_at", -1)])

        # ---- document accesses / benefits ----
        await db.document_accesses.create_index([("user_id", 1), ("accessed_at", -1)])
        await db.document_accesses.create_index([("user_id", 1), ("document_id", 1)])
        await db.benefit_validations.create_index([("user_id", 1), ("validated_at", -1)])

        logger.info("MongoDB indexes ensured")
    except Exception as e:
        logger.warning(f"Index creation warning (non-fatal): {e}")
