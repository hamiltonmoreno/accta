"""
Shared pytest fixtures for the ACCTA backend test suite.

Provides:
- `client` (session-scoped TestClient) for in-process smoke tests against
  the real app + real DB connection.
- `mock_db` for unit tests that need a fake MongoDB without hitting Mongo.
- Role factories (admin, socio, financeiro, moderador) returning Pydantic
  User instances ready for `dependency_overrides`.
- A token factory (`make_token`) for forging JWTs with custom claims/expiry.
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Ensure backend modules are importable when pytest is run from repo root.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Defaults so unit tests can import auth/database without a real .env.
# The asyncpg pool is created lazily — no socket is opened until a query
# runs, so a placeholder URL is safe for tests that mock all DB calls.
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/accta_test")
os.environ.setdefault("SECRET_KEY", "unit-test-secret-key-do-not-use-in-prod")
os.environ.setdefault("CORS_ORIGINS", "*")


# --------------------------------------------------------------------------- #
# Smoke-test fixture (preserved from main)
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="session")
def client():
    """In-process TestClient for smoke tests. Hits the real app + real DB."""
    from fastapi.testclient import TestClient
    from server import app

    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------- #
# User factories
# --------------------------------------------------------------------------- #


def _make_user_dict(role: str, **overrides) -> dict:
    base = {
        "id": str(uuid.uuid4()),
        "name": f"Test {role.title()}",
        "email": f"{role}-{uuid.uuid4().hex[:6]}@example.com",
        "role": role,
        "status": "ativo",
        "cargo": "Sócio",
        "privileges": [],
        "consent_data": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    base.update(overrides)
    return base


@pytest.fixture
def admin_user_dict():
    return _make_user_dict("admin", privileges=["manage_users", "manage_finances"])


@pytest.fixture
def socio_user_dict():
    return _make_user_dict("socio")


@pytest.fixture
def financeiro_user_dict():
    return _make_user_dict("financeiro", privileges=["manage_finances"])


@pytest.fixture
def moderador_user_dict():
    return _make_user_dict("moderador", privileges=["moderate_content"])


@pytest.fixture
def admin_user(admin_user_dict):
    from models import User

    return User(**admin_user_dict)


@pytest.fixture
def socio_user(socio_user_dict):
    from models import User

    return User(**socio_user_dict)


@pytest.fixture
def financeiro_user(financeiro_user_dict):
    from models import User

    return User(**financeiro_user_dict)


@pytest.fixture
def moderador_user(moderador_user_dict):
    from models import User

    return User(**moderador_user_dict)


# --------------------------------------------------------------------------- #
# JWT factory
# --------------------------------------------------------------------------- #


@pytest.fixture
def make_token():
    """Return a callable that produces a JWT for a given user_id with custom expiry."""
    import uuid

    from jose import jwt

    secret = os.environ["SECRET_KEY"]

    def _make(user_id: str, expires_delta: timedelta | None = None, extra_claims: dict | None = None) -> str:
        now = datetime.now(timezone.utc)
        exp = now + (expires_delta if expires_delta is not None else timedelta(minutes=60))
        # jti por defeito: tokens reais (create_access_token) sempre o incluem.
        payload = {"sub": user_id, "exp": exp, "jti": str(uuid.uuid4())}
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, secret, algorithm="HS256")

    return _make


# --------------------------------------------------------------------------- #
# Mock DB
# --------------------------------------------------------------------------- #


@pytest.fixture
def mock_db(monkeypatch):
    """
    Patch `database.db` and `auth.db` with AsyncMock collections.

    Use `mock_db.users.find_one.return_value = ...` to set per-test behaviour.
    """
    fake_db = MagicMock(name="db")
    for collection in (
        "users",
        "transactions",
        "audit_logs",
        "notifications",
        "password_resets",
        "posts",
        "wall_posts",
        "wall_comments",
        "invoices",
        "polls",
        "user_votes",
        "events",
        "projects",
        "documents",
        "document_accesses",
        "gallery_albums",
        "gallery_photos",
        "finance_settings",
        "benefits",
        "benefit_validations",
        "benefit_partners",
        "tokens_revoked",
        "failed_logins",
        "comunicados",
    ):
        coll = MagicMock(name=collection)
        coll.find_one = AsyncMock(return_value=None)
        coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="mock_id"))
        coll.insert_many = AsyncMock(return_value=MagicMock(inserted_ids=["mock_id"]))
        coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        coll.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        coll.count_documents = AsyncMock(return_value=0)
        find_cursor = MagicMock()
        find_cursor.to_list = AsyncMock(return_value=[])
        find_cursor.sort = MagicMock(return_value=find_cursor)
        find_cursor.limit = MagicMock(return_value=find_cursor)
        find_cursor.skip = MagicMock(return_value=find_cursor)
        coll.find = MagicMock(return_value=find_cursor)
        # aggregate cursor — needs to_list as well
        agg_cursor = MagicMock()
        agg_cursor.to_list = AsyncMock(return_value=[])
        coll.aggregate = MagicMock(return_value=agg_cursor)
        setattr(fake_db, collection, coll)

    import database
    import auth
    import helpers

    monkeypatch.setattr(database, "db", fake_db)
    monkeypatch.setattr(auth, "db", fake_db)
    monkeypatch.setattr(helpers, "db", fake_db)

    # comunicados_service faz `from database import db` no topo — patch explícito
    if "comunicados_service" in sys.modules:
        monkeypatch.setattr(sys.modules["comunicados_service"], "db", fake_db)

    # routes/*.py fazem `from database import db` no top-level — referencia
    # ja foi capturada antes do monkeypatch. Patch cada module ja importado
    # individualmente. Iterar em sys.modules apanha apenas os modulos ja
    # carregados (testes que importam mais routes pegam fixture novamente).
    for mod_name, module in list(sys.modules.items()):
        if mod_name.startswith("routes.") and hasattr(module, "db"):
            monkeypatch.setattr(module, "db", fake_db)
    return fake_db
