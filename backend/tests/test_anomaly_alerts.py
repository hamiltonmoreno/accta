"""Testes do F3 — alertas de anomalia (spec-verificacao-seguranca-saas §8.2) +
itens de hardening herdados do F2. Unit in-process com mock_db.

Cobre: (a) alerta de lockout na transição (5.ª falha), e não antes; falha de OTP
que cruza o threshold; (c) alerta de escalada de role/privilégio (exclui o ator);
e os itens herdados: get_user_from_token nega sessão mfa_pending; record_failed_login
sinaliza a transição. (O item "OTP conta para o lockout" já estava feito — ver
test_mfa.test_login_mfa_invalid_otp_counts_failure.)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pyotp
import pytest
from fastapi import HTTPException

pytestmark = pytest.mark.unit


# ----------------------------- helpers locais ----------------------------- #
def _login_request():
    from starlette.requests import Request

    return Request({"type": "http", "method": "POST", "path": "/api/auth/login",
                    "headers": [], "client": ("t", 1), "query_string": b""})


def _user_doc(role="socio", mfa_enabled=False, secret=None):
    from auth import hash_password

    doc = {
        "id": "u1", "name": "U", "email": "u@accta.cv", "role": role, "status": "ativo",
        "cargo": "socio", "privileges": [], "consent_data": True, "password": hash_password("pw"),
    }
    if mfa_enabled:
        from mfa import encrypt_secret

        doc["mfa_enabled"] = True
        doc["mfa_secret"] = encrypt_secret(secret)
        doc["mfa_backup_codes"] = []
    return doc


@pytest.fixture
def login_env(mock_db, monkeypatch):
    import routes.auth_routes as auth_routes

    monkeypatch.setattr(auth_routes.limiter, "enabled", False)
    mock_db.login_attempts = MagicMock()
    mock_db.login_attempts.insert_one = AsyncMock()
    mock_db.login_attempts.delete_many = AsyncMock()
    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    return auth_routes


# ===================== (a) Alerta de lockout =============================== #
@pytest.mark.asyncio
async def test_fifth_failed_login_alerts_admins(login_env, mock_db, monkeypatch):
    """A 5.ª falha (transição para trancada) alerta os admins, uma vez."""
    from fastapi import Response
    from models import UserLogin

    alert = AsyncMock()
    monkeypatch.setattr(login_env, "alert_admins_account_locked", alert)
    mock_db.users.find_one = AsyncMock(return_value=_user_doc())
    # is_account_locked vê 4 (não trancada) → prossegue; record_failed_login vê 5.
    mock_db.login_attempts.count_documents = AsyncMock(side_effect=[4, 5])
    with pytest.raises(HTTPException) as exc:
        await login_env.login(_login_request(), Response(), UserLogin(email="u@accta.cv", password="errada"))
    assert exc.value.status_code == 401
    alert.assert_awaited_once_with("u@accta.cv")


@pytest.mark.asyncio
async def test_fourth_failed_login_does_not_alert(login_env, mock_db, monkeypatch):
    """Antes do threshold (4.ª falha) não há alerta — só na transição."""
    from fastapi import Response
    from models import UserLogin

    alert = AsyncMock()
    monkeypatch.setattr(login_env, "alert_admins_account_locked", alert)
    mock_db.users.find_one = AsyncMock(return_value=_user_doc())
    mock_db.login_attempts.count_documents = AsyncMock(side_effect=[3, 4])
    with pytest.raises(HTTPException):
        await login_env.login(_login_request(), Response(), UserLogin(email="u@accta.cv", password="errada"))
    alert.assert_not_awaited()


@pytest.mark.asyncio
async def test_already_locked_does_not_realert(login_env, mock_db, monkeypatch):
    """Conta já trancada (is_account_locked vê 5) → 423 antes de tudo, sem re-alertar."""
    from fastapi import Response
    from models import UserLogin

    alert = AsyncMock()
    monkeypatch.setattr(login_env, "alert_admins_account_locked", alert)
    mock_db.users.find_one = AsyncMock(return_value=_user_doc())
    # is_account_locked: count=5 → trancada; depois find_one(oldest) p/ "unlock at".
    mock_db.login_attempts.count_documents = AsyncMock(return_value=5)
    mock_db.login_attempts.find_one = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await login_env.login(_login_request(), Response(), UserLogin(email="u@accta.cv", password="errada"))
    assert exc.value.status_code == 423
    alert.assert_not_awaited()


@pytest.mark.asyncio
async def test_mfa_failure_crossing_threshold_alerts(login_env, mock_db, monkeypatch):
    """Falha de OTP que cruza o threshold também alerta (lockout partilhado)."""
    from fastapi import Response
    from mfa import generate_totp_secret
    from models import UserLogin

    alert = AsyncMock()
    monkeypatch.setattr(login_env, "alert_admins_account_locked", alert)
    secret = generate_totp_secret()
    mock_db.users.find_one = AsyncMock(return_value=_user_doc(mfa_enabled=True, secret=secret))
    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=0))  # backup não casa
    mock_db.login_attempts.count_documents = AsyncMock(side_effect=[4, 5])
    bad = "000000" if pyotp.TOTP(secret).now() != "000000" else "111111"
    with pytest.raises(HTTPException) as exc:
        await login_env.login(_login_request(), Response(), UserLogin(email="u@accta.cv", password="pw", otp=bad))
    assert exc.value.detail == "mfa_invalido"
    alert.assert_awaited_once_with("u@accta.cv")


# ===================== record_failed_login sinaliza ======================= #
@pytest.mark.asyncio
async def test_record_failed_login_signals_only_on_transition(mock_db):
    import helpers

    mock_db.login_attempts = MagicMock()
    mock_db.login_attempts.insert_one = AsyncMock()

    mock_db.login_attempts.count_documents = AsyncMock(return_value=5)  # == threshold
    assert await helpers.record_failed_login("x@accta.cv", "1.2.3.4") is True
    mock_db.login_attempts.count_documents = AsyncMock(return_value=4)  # antes
    assert await helpers.record_failed_login("x@accta.cv") is False
    mock_db.login_attempts.count_documents = AsyncMock(return_value=6)  # já trancada
    assert await helpers.record_failed_login("x@accta.cv") is False


# ===================== (c) Escalada de privilégio ========================= #
@pytest.mark.asyncio
async def test_escalation_alert_on_role_up(monkeypatch):
    import helpers

    spy = AsyncMock()
    monkeypatch.setattr(helpers, "notify_admins", spy)
    await helpers.alert_admins_privilege_escalation("actor", "Bob", "socio", "admin", [], [])
    spy.assert_awaited_once()
    assert spy.await_args.kwargs.get("exclude_id") == "actor"  # alerta exclui o ator


@pytest.mark.asyncio
async def test_escalation_alert_on_privilege_gain(monkeypatch):
    import helpers

    spy = AsyncMock()
    monkeypatch.setattr(helpers, "notify_admins", spy)
    await helpers.alert_admins_privilege_escalation("a", "Bob", "socio", "socio", [], ["view_audit_logs"])
    spy.assert_awaited_once()


@pytest.mark.asyncio
async def test_no_alert_on_no_change_or_deescalation(monkeypatch):
    import helpers

    spy = AsyncMock()
    monkeypatch.setattr(helpers, "notify_admins", spy)
    await helpers.alert_admins_privilege_escalation("a", "Bob", "socio", "socio", ["x"], ["x"])  # sem mudança
    await helpers.alert_admins_privilege_escalation("a", "Bob", "admin", "socio", ["view_audit_logs"], [])  # de-escalada
    spy.assert_not_awaited()


# ===================== item herdado #1 — mfa_pending no SSE =============== #
@pytest.mark.asyncio
async def test_get_user_from_token_denies_mfa_pending_session(mock_db, make_token):
    import auth

    mock_db.users.find_one = AsyncMock(return_value=_user_doc(role="admin"))
    full = make_token("u1")
    assert await auth.get_user_from_token(full) is not None  # sessão completa → User
    pending = make_token("u1", extra_claims={"mfa_pending": True})
    assert await auth.get_user_from_token(pending) is None  # sessão limitada → sem SSE
