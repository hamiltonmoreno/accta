"""Regressão rate-limit — slowapi em /api/auth/login (§4).

O 11.º POST a /api/auth/login dentro de 1 min → 429. TestClient sem `with`
(sem startup/DB) + mock_db (login não toca DB real) + limiter ATIVO (ao
contrário dos outros testes). Reset do storage do limiter para isolamento.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from slowapi.middleware import SlowAPIMiddleware

import routes.auth_routes as auth_routes  # presente em sys.modules p/ mock_db
from helpers import client_ip, rate_limit_key
from server import app, limiter

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


# --- spec 019 / T017: chave por-cliente real + middleware montado (H2/H3) ----
def _req(peer, xff=None):
    headers = {}
    if xff is not None:
        headers["x-forwarded-for"] = xff
    client = SimpleNamespace(host=peer) if peer is not None else None
    return SimpleNamespace(client=client, headers=headers)


def test_untrusted_peer_ignores_forged_xff():
    # Peer público a forjar XFF → usa o peer (senão brute-force distribuído era
    # indetetável — H3).
    assert rate_limit_key(_req("8.8.8.8", xff="1.2.3.4")) == "8.8.8.8"
    assert client_ip(_req("8.8.8.8", xff="1.2.3.4")) == "8.8.8.8"


def test_trusted_proxy_uses_first_forwarded_hop():
    # Peer em rede privada (Nginx/Docker) → 1.º hop do XFF = cliente real.
    assert rate_limit_key(_req("172.17.0.1", xff="203.0.113.7, 10.0.0.2")) == "203.0.113.7"
    assert rate_limit_key(_req("127.0.0.1", xff="203.0.113.7")) == "203.0.113.7"


def test_no_xff_uses_peer():
    assert rate_limit_key(_req("203.0.113.9")) == "203.0.113.9"


def test_clientless_request_falls_back():
    assert rate_limit_key(_req(None)) == "127.0.0.1"


def test_slowapi_middleware_mounted_and_default_wired():
    assert any(m.cls is SlowAPIMiddleware for m in app.user_middleware), "SlowAPIMiddleware ausente (H2)"
    assert app.state.limiter is limiter
    key_func = getattr(limiter, "_key_func", None) or getattr(limiter, "key_func", None)
    assert key_func is rate_limit_key, "limiter global não chaveia por rate_limit_key (H3)"
    assert getattr(limiter, "_default_limits", None), "default_limits vazio (H2)"
