"""Regressão lockout — máquina de estado + 423 no login (§4).

5 falhas na janela → bloqueado; fora da janela → desbloqueado;
reset_failed_logins limpa; login devolve 423 quando bloqueado. Usa um fake
stateful de `login_attempts` (a coleção real que helpers usa).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request

import helpers
import routes.auth_routes as auth_routes
from helpers import LOCKOUT_THRESHOLD, LOCKOUT_WINDOW_MINUTES
from models import UserLogin

pytestmark = pytest.mark.unit


class _FakeLoginAttempts:
    """Emula db.login_attempts com estado em memória (subset usado por helpers)."""

    def __init__(self):
        self.docs: list[dict] = []

    async def insert_one(self, doc):
        self.docs.append(dict(doc))

    async def delete_many(self, filt):
        email = filt["email"]
        before = len(self.docs)
        self.docs = [d for d in self.docs if d.get("email") != email]
        return type("R", (), {"deleted_count": before - len(self.docs)})()

    @staticmethod
    def _as_dt(value):
        """Mirror do DAO real: `attempted_at` está em `_DATETIME_FIELDS`, logo é
        guardado como string ISO e REHIDRATADO para datetime na leitura. O fake
        faz o mesmo aqui para aceitar tanto strings (record_failed_login) como
        datetimes (docs injetados pelos testes)."""
        return datetime.fromisoformat(value) if isinstance(value, str) else value

    def _in_window(self, filt):
        email = filt["email"]
        gte = filt["attempted_at"]["$gte"]
        return [
            d for d in self.docs
            if d.get("email") == email and self._as_dt(d["attempted_at"]) >= gte
        ]

    async def count_documents(self, filt):
        return len(self._in_window(filt))

    async def find_one(self, filt, sort=None):
        cands = self._in_window(filt)
        return min(cands, key=lambda d: self._as_dt(d["attempted_at"])) if cands else None


@pytest.fixture
def fake_attempts(monkeypatch):
    fake = _FakeLoginAttempts()
    db = type("DB", (), {"login_attempts": fake})()
    monkeypatch.setattr(helpers, "db", db)
    return fake


@pytest.mark.asyncio
async def test_locks_after_threshold_failures(fake_attempts):
    email = "alvo@accta.cv"
    for _ in range(LOCKOUT_THRESHOLD - 1):
        await helpers.record_failed_login(email)
    assert await helpers.is_account_locked(email) is None  # 4 < 5
    await helpers.record_failed_login(email)  # 5.ª
    locked_until = await helpers.is_account_locked(email)
    assert locked_until is not None
    assert locked_until > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_unlocks_after_window(fake_attempts):
    email = "alvo@accta.cv"
    old = datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_WINDOW_MINUTES + 1)
    for _ in range(LOCKOUT_THRESHOLD):
        fake_attempts.docs.append({"email": email, "ip": None, "attempted_at": old})
    assert await helpers.is_account_locked(email) is None  # tudo fora da janela


@pytest.mark.asyncio
async def test_reset_clears_lockout(fake_attempts):
    email = "alvo@accta.cv"
    for _ in range(LOCKOUT_THRESHOLD):
        await helpers.record_failed_login(email)
    assert await helpers.is_account_locked(email) is not None
    await helpers.reset_failed_logins(email)
    assert await helpers.is_account_locked(email) is None


@pytest.mark.asyncio
async def test_login_route_returns_423_when_locked(mock_db, monkeypatch):
    # Login wireado ao lockout: conta bloqueada → 423 (limiter desativado para
    # poder chamar a função decorada diretamente — ver CLAUDE.md).
    monkeypatch.setattr(auth_routes.limiter, "enabled", False)
    locked_dt = datetime.now(timezone.utc) + timedelta(minutes=10)
    monkeypatch.setattr(auth_routes, "is_account_locked", AsyncMock(return_value=locked_dt))

    scope = {
        "type": "http", "method": "POST", "path": "/api/auth/login",
        "headers": [], "client": ("test", 1), "query_string": b"",
    }
    with pytest.raises(HTTPException) as exc:
        await auth_routes.login(
            Request(scope), Response(), UserLogin(email="x@accta.cv", password="y")
        )
    assert exc.value.status_code == 423
