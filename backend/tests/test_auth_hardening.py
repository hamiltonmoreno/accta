"""Unit tests for Sprint 4 auth hardening: JWT blocklist + account lockout.
Sem MongoDB nem backend a correr — usa o mock_db fixture do conftest.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

import auth
import helpers


pytestmark = pytest.mark.unit


# ============================================================
# JWT blocklist (jti)
# ============================================================


def test_create_access_token_includes_jti():
    """Tokens novos devem ter jti claim para suportar blocklist."""
    token = auth.create_access_token({"sub": "user-123"})
    payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    assert "jti" in payload
    assert payload["jti"]
    assert "exp" in payload
    assert payload["sub"] == "user-123"


def test_create_access_token_unique_jti_per_token():
    """Cada token tem o seu proprio jti (nao reutilizado)."""
    t1 = auth.create_access_token({"sub": "user-A"})
    t2 = auth.create_access_token({"sub": "user-A"})
    j1 = jwt.decode(t1, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])["jti"]
    j2 = jwt.decode(t2, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])["jti"]
    assert j1 != j2


@pytest.mark.asyncio
async def test_is_token_revoked_returns_false_for_unknown_jti(mock_db):
    mock_db.tokens_revoked = MagicMock()
    mock_db.tokens_revoked.find_one = AsyncMock(return_value=None)
    assert await auth.is_token_revoked("some-jti") is False


@pytest.mark.asyncio
async def test_is_token_revoked_returns_true_for_known_jti(mock_db):
    mock_db.tokens_revoked = MagicMock()
    mock_db.tokens_revoked.find_one = AsyncMock(return_value={"_id": 1, "jti": "abc"})
    assert await auth.is_token_revoked("abc") is True


@pytest.mark.asyncio
async def test_is_token_revoked_treats_missing_jti_as_revoked(mock_db):
    """Sem jti não há como verificar a blocklist: tratado como revogado.
    Todos os tokens emitidos agora incluem jti; os legados pré-jti expiram em <=24h."""
    assert await auth.is_token_revoked(None) is True


@pytest.mark.asyncio
async def test_get_current_user_rejects_revoked_token(mock_db):
    """get_current_user devolve 401 se jti estiver no blocklist."""
    mock_db.tokens_revoked = MagicMock()
    mock_db.tokens_revoked.find_one = AsyncMock(return_value={"_id": 1, "jti": "revoked-jti"})
    mock_db.users.find_one = AsyncMock(return_value={
        "id": "u1", "email": "x@y.com", "name": "X", "role": "socio", "status": "ativo",
    })

    token = auth.create_access_token({"sub": "u1"})
    # Forge um token com o jti que esta no blocklist:
    payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    payload["jti"] = "revoked-jti"
    revoked = jwt.encode(payload, auth.SECRET_KEY, algorithm=auth.ALGORITHM)

    # Sprint 10: get_current_user agora recebe Request em vez de credentials.
    class _MockRequest:
        headers = {"Authorization": f"Bearer {revoked}"}
        cookies = {}

    with pytest.raises(HTTPException) as exc:
        await auth.get_current_user(_MockRequest())
    assert exc.value.status_code == 401
    assert "Sessão" in exc.value.detail or "expirada" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_revoke_token_inserts_with_expires_at(mock_db):
    """revoke_token insere doc com expires_at (BSON Date) para o TTL index."""
    mock_db.tokens_revoked = MagicMock()
    mock_db.tokens_revoked.insert_one = AsyncMock()
    exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())

    await auth.revoke_token("jti-1", exp, "user-X")

    mock_db.tokens_revoked.insert_one.assert_awaited_once()
    doc = mock_db.tokens_revoked.insert_one.call_args[0][0]
    assert doc["jti"] == "jti-1"
    assert doc["user_id"] == "user-X"
    assert isinstance(doc["expires_at"], datetime)


# ============================================================
# Account lockout (5 falhas em 15min)
# ============================================================


@pytest.mark.asyncio
async def test_lockout_threshold_is_5(mock_db):
    """Confirma constante — se mudar futuramente, lembra de actualizar docs."""
    assert helpers.LOCKOUT_THRESHOLD == 5
    assert helpers.LOCKOUT_WINDOW_MINUTES == 15


@pytest.mark.asyncio
async def test_is_account_locked_returns_none_below_threshold(mock_db):
    mock_db.login_attempts = MagicMock()
    mock_db.login_attempts.count_documents = AsyncMock(return_value=4)  # < 5
    result = await helpers.is_account_locked("user@example.com")
    assert result is None


@pytest.mark.asyncio
async def test_is_account_locked_returns_unlock_at_above_threshold(mock_db):
    mock_db.login_attempts = MagicMock()
    mock_db.login_attempts.count_documents = AsyncMock(return_value=5)  # = threshold
    oldest = datetime.now(timezone.utc) - timedelta(minutes=5)
    mock_db.login_attempts.find_one = AsyncMock(return_value={"attempted_at": oldest})

    result = await helpers.is_account_locked("user@example.com")

    assert result is not None
    # unlock-at = oldest + janela (15min)
    expected = oldest + timedelta(minutes=helpers.LOCKOUT_WINDOW_MINUTES)
    assert abs((result - expected).total_seconds()) < 1


@pytest.mark.asyncio
async def test_record_failed_login_inserts_attempt_and_returns_none(mock_db):
    """record_failed_login agora só insere a tentativa. A contagem na janela
    é responsabilidade de is_account_locked — não recontamos no call-site
    (a query de count era descartada = desperdício por cada falha)."""
    mock_db.login_attempts = MagicMock()
    mock_db.login_attempts.insert_one = AsyncMock()
    mock_db.login_attempts.count_documents = AsyncMock(return_value=3)

    result = await helpers.record_failed_login("user@example.com", ip="1.2.3.4")

    assert result is None
    # Não desperdiça uma query de count que ninguém usava.
    mock_db.login_attempts.count_documents.assert_not_called()
    mock_db.login_attempts.insert_one.assert_awaited_once()
    doc = mock_db.login_attempts.insert_one.call_args[0][0]
    assert doc["email"] == "user@example.com"
    assert doc["ip"] == "1.2.3.4"
    assert isinstance(doc["attempted_at"], datetime)


@pytest.mark.asyncio
async def test_reset_failed_logins_deletes_all_for_email(mock_db):
    mock_db.login_attempts = MagicMock()
    mock_db.login_attempts.delete_many = AsyncMock()

    await helpers.reset_failed_logins("user@example.com")

    mock_db.login_attempts.delete_many.assert_awaited_once_with({"email": "user@example.com"})
