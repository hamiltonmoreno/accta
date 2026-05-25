"""Regressão rate-limit — slowapi em /api/auth/login (§4).

O 11.º POST a /api/auth/login dentro de 1 min → 429. TestClient sem `with`
(sem startup/DB) + mock_db (login não toca DB real) + limiter ATIVO (ao
contrário dos outros testes). Reset do storage do limiter para isolamento.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

import routes.auth_routes as auth_routes  # presente em sys.modules p/ mock_db
from server import app

pytestmark = pytest.mark.unit


def _reset_limiter():
    storage = getattr(auth_routes.limiter, "_storage", None)
    if storage is not None and hasattr(storage, "reset"):
        storage.reset()
    elif storage is not None and hasattr(storage, "storage"):
        storage.storage.clear()


@pytest.fixture
def reset_limiter():
    _reset_limiter()
    yield
    _reset_limiter()


def test_login_rate_limited_after_10(mock_db, reset_limiter):
    # login com utilizador inexistente → 401 a cada vez, até o 11.º → 429.
    mock_db.login_attempts = MagicMock()
    mock_db.login_attempts.count_documents = AsyncMock(return_value=0)
    mock_db.login_attempts.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    mock_db.users.find_one = AsyncMock(return_value=None)

    client = TestClient(app)  # sem `with` → sem startup/DB
    body = {"email": "x@accta.cv", "password": "errada"}
    codes = [client.post("/api/auth/login", json=body).status_code for _ in range(11)]
    assert codes[:10] == [401] * 10
    assert codes[10] == 429


def test_forgot_password_rate_limited_after_3(mock_db, reset_limiter):
    # Email inexistente → 200 genérico (anti-enumeração) e NENHUM email enviado
    # (send_password_reset_email só corre quando o user existe). 4.º POST → 429.
    mock_db.users.find_one = AsyncMock(return_value=None)

    client = TestClient(app)  # sem `with` → sem startup/DB
    body = {"email": "ninguem@accta.cv"}
    codes = [client.post("/api/auth/forgot-password", json=body).status_code for _ in range(4)]
    assert codes[:3] == [200] * 3
    assert codes[3] == 429
