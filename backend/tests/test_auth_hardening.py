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
# Revogação de sessões no reset de password (password_changed_at + iat)
# ============================================================


def test_create_access_token_includes_iat():
    """Tokens novos trazem iat (emissão) para comparar com password_changed_at."""
    token = auth.create_access_token({"sub": "u1"})
    payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    assert isinstance(payload.get("iat"), int)
    assert payload["iat"] <= payload["exp"]


def test_token_predates_password_change_no_field_is_fresh():
    # Utilizador que nunca fez reset → nunca é considerado obsoleto.
    assert auth.token_predates_password_change({"iat": 1000}, {}) is False


def test_token_predates_password_change_older_token_is_stale():
    changed = datetime.now(timezone.utc)
    iat = int((changed - timedelta(minutes=5)).timestamp())  # emitido antes do reset
    assert auth.token_predates_password_change({"iat": iat}, {"password_changed_at": changed.isoformat()}) is True


def test_token_predates_password_change_newer_token_is_fresh():
    changed = datetime.now(timezone.utc)
    iat = int((changed + timedelta(minutes=5)).timestamp())  # emitido após o reset
    assert auth.token_predates_password_change({"iat": iat}, {"password_changed_at": changed.isoformat()}) is False


def test_token_predates_password_change_missing_iat_after_reset_is_stale():
    # Token legado sem iat, mas o utilizador já fez reset → necessariamente antigo.
    changed = datetime.now(timezone.utc).isoformat()
    assert auth.token_predates_password_change({}, {"password_changed_at": changed}) is True


def _mock_request_for(token: str):
    class _MockRequest:
        headers = {"Authorization": f"Bearer {token}"}
        cookies = {}

    return _MockRequest()


@pytest.mark.asyncio
async def test_get_current_user_rejects_token_issued_before_password_change(mock_db):
    mock_db.tokens_revoked = MagicMock()
    mock_db.tokens_revoked.find_one = AsyncMock(return_value=None)  # não revogado
    future_change = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    mock_db.users.find_one = AsyncMock(
        return_value={
            "id": "u1", "email": "x@y.com", "name": "X", "role": "socio",
            "status": "ativo", "password_changed_at": future_change,
        }
    )
    token = auth.create_access_token({"sub": "u1"})  # iat = agora < future_change
    with pytest.raises(HTTPException) as exc:
        await auth.get_current_user(_mock_request_for(token))
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_accepts_token_issued_after_password_change(mock_db):
    mock_db.tokens_revoked = MagicMock()
    mock_db.tokens_revoked.find_one = AsyncMock(return_value=None)
    past_change = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    mock_db.users.find_one = AsyncMock(
        return_value={
            "id": "u1", "email": "x@y.com", "name": "X", "role": "socio",
            "status": "ativo", "password_changed_at": past_change,
        }
    )
    token = auth.create_access_token({"sub": "u1"})  # iat = agora > past_change
    user = await auth.get_current_user(_mock_request_for(token))
    assert user.id == "u1"


@pytest.mark.parametrize("bad_status", ["inativo", "rejeitado", "pendente_convite", "pendente_aprovacao"])
@pytest.mark.asyncio
async def test_get_current_user_rejects_non_active_account(mock_db, bad_status):
    """Conta desativada/sancionada/rejeitada APÓS o login -> a sessão existente
    é morta no próximo pedido (allowlist fail-closed, igual ao login)."""
    mock_db.tokens_revoked = MagicMock()
    mock_db.tokens_revoked.find_one = AsyncMock(return_value=None)  # não revogado por logout
    mock_db.users.find_one = AsyncMock(
        return_value={
            "id": "u1", "email": "x@y.com", "name": "X", "role": "socio",
            "status": bad_status,
        }
    )
    token = auth.create_access_token({"sub": "u1"})  # token criptograficamente válido
    with pytest.raises(HTTPException) as exc:
        await auth.get_current_user(_mock_request_for(token))
    assert exc.value.status_code == 401


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
async def test_record_failed_login_inserts_attempt_and_signals_threshold(mock_db):
    """record_failed_login insere a tentativa e devolve True só quando ESTA falha
    cruza o threshold de lockout (count == LOCKOUT_THRESHOLD) — para alertar os
    admins uma vez na transição (F3 §8.2.a). Abaixo do threshold → False."""
    mock_db.login_attempts = MagicMock()
    mock_db.login_attempts.insert_one = AsyncMock()
    mock_db.login_attempts.count_documents = AsyncMock(return_value=3)  # < 5

    result = await helpers.record_failed_login("user@example.com", ip="1.2.3.4")

    assert result is False  # ainda não trancou
    mock_db.login_attempts.insert_one.assert_awaited_once()
    doc = mock_db.login_attempts.insert_one.call_args[0][0]
    assert doc["email"] == "user@example.com"
    assert doc["ip"] == "1.2.3.4"

    # A falha que cruza o threshold sinaliza a transição.
    mock_db.login_attempts.count_documents = AsyncMock(return_value=helpers.LOCKOUT_THRESHOLD)
    assert await helpers.record_failed_login("user@example.com") is True
    assert isinstance(doc["attempted_at"], datetime)


@pytest.mark.asyncio
async def test_reset_failed_logins_deletes_all_for_email(mock_db):
    mock_db.login_attempts = MagicMock()
    mock_db.login_attempts.delete_many = AsyncMock()

    await helpers.reset_failed_logins("user@example.com")

    mock_db.login_attempts.delete_many.assert_awaited_once_with({"email": "user@example.com"})
