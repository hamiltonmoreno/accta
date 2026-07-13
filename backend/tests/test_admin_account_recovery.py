"""Unit tests — recuperação de conta pelo admin + fixes do fluxo de reset.

Cobre:
- Bug A: o email de reset passa a ter um LINK clicável (antes só mostrava um
  "código" que a página /reset-password não sabe receber).
- Bug B: `reset_password` limpa `login_attempts` — quem redefine a senha deixa
  de ficar preso no lockout de 15 min.
- Feature: `POST /admin/users/{id}/unlock` e `/send-reset` (admin/manage_users).

Endpoints admin não têm @limiter → chamada directa com request fake (padrão de
test_admin_routes.py). `reset_password` tem @limiter → Request real + limiter off
(padrão de test_auth_routes.py).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from routes import admin as admin_route
from routes import auth_routes
from email_service import password_reset_email_html


# asyncio_mode=auto (pyproject) trata os testes async sem mark explícito; assim
# os 2 testes síncronos do template não herdam um mark asyncio inaplicável.
pytestmark = [pytest.mark.unit]


def _mock_request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test"}

    return _R()


def _real_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/auth/reset-password",
            "headers": [],
            "client": ("127.0.0.1", 1234),
            "query_string": b"",
        }
    )


@pytest.fixture
def wire_login_attempts(mock_db):
    """`login_attempts` não está pré-ligada no conftest — liga delete_many aqui.
    Também liga password_resets.delete_many (o conftest só liga delete_one)."""
    mock_db.login_attempts = MagicMock(name="login_attempts")
    mock_db.login_attempts.delete_many = AsyncMock()
    mock_db.password_resets.delete_many = AsyncMock()
    return mock_db


# --------------------------------------------------------------------------- #
# Bug A — email de reset tem link clicável
# --------------------------------------------------------------------------- #


class TestPasswordResetEmailHasLink:
    def test_contains_clickable_link(self):
        url = "https://controlador.cv/reset-password?token=abc123"
        html = password_reset_email_html("Maria", url)
        assert f'href="{url}"' in html
        assert "reset-password?token=abc123" in html

    def test_no_url_degrades_without_poisoned_link(self):
        # Sem base confiável (reset_url="") não deve inventar um link.
        html = password_reset_email_html("Maria", "")
        assert "href=" not in html


# --------------------------------------------------------------------------- #
# Bug B — reset_password limpa o lockout
# --------------------------------------------------------------------------- #


class TestResetPasswordClearsLockout:
    async def test_clears_login_attempts(self, wire_login_attempts, monkeypatch):
        from models import PasswordResetConfirm

        mock_db = wire_login_attempts
        monkeypatch.setattr(auth_routes.limiter, "enabled", False)
        monkeypatch.setattr(auth_routes, "create_audit_log", AsyncMock())

        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        mock_db.password_resets.find_one = AsyncMock(
            return_value={"email": "kiso@x.cv", "token": "tok", "used": False, "expires_at": future}
        )
        mock_db.users.find_one = AsyncMock(return_value={"id": "u1"})

        data = PasswordResetConfirm(token="tok", new_password="novasenha")
        await auth_routes.reset_password(_real_request(), data)

        mock_db.login_attempts.delete_many.assert_awaited_once_with({"email": "kiso@x.cv"})


# --------------------------------------------------------------------------- #
# POST /admin/users/{id}/unlock
# --------------------------------------------------------------------------- #


class TestUnlockUser:
    async def test_socio_403(self, wire_login_attempts, socio_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.unlock_user("u1", _mock_request(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_not_found_404(self, wire_login_attempts, admin_user):
        wire_login_attempts.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await admin_route.unlock_user("nope", _mock_request(), current_user=admin_user)
        assert exc.value.status_code == 404

    async def test_admin_clears_attempts_and_audits(self, wire_login_attempts, admin_user, monkeypatch):
        mock_db = wire_login_attempts
        mock_db.users.find_one = AsyncMock(return_value={"id": "u1", "name": "Kiso", "email": "kiso@x.cv"})
        audit = AsyncMock()
        monkeypatch.setattr(admin_route, "create_audit_log", audit)

        res = await admin_route.unlock_user("u1", _mock_request(), current_user=admin_user)

        mock_db.login_attempts.delete_many.assert_awaited_once_with({"email": "kiso@x.cv"})
        audit.assert_awaited_once()
        assert audit.await_args.args[1] == "account_unlocked"
        assert "desbloqueada" in res["message"].lower()


# --------------------------------------------------------------------------- #
# POST /admin/users/{id}/send-reset
# --------------------------------------------------------------------------- #


class TestAdminSendReset:
    async def test_socio_403(self, wire_login_attempts, socio_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.admin_send_password_reset("u1", _mock_request(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_not_found_404(self, wire_login_attempts, admin_user):
        wire_login_attempts.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await admin_route.admin_send_password_reset("nope", _mock_request(), current_user=admin_user)
        assert exc.value.status_code == 404

    async def test_inactive_account_400(self, wire_login_attempts, admin_user):
        wire_login_attempts.users.find_one = AsyncMock(
            return_value={"id": "u1", "name": "Kiso", "email": "kiso@x.cv", "status": "inativo"}
        )
        with pytest.raises(HTTPException) as exc:
            await admin_route.admin_send_password_reset("u1", _mock_request(), current_user=admin_user)
        assert exc.value.status_code == 400

    async def test_active_sends_email_and_audits(self, wire_login_attempts, admin_user, monkeypatch):
        mock_db = wire_login_attempts
        mock_db.users.find_one = AsyncMock(
            return_value={"id": "u1", "name": "Kiso", "email": "kiso@x.cv", "status": "ativo"}
        )
        send = AsyncMock()
        audit = AsyncMock()
        # issue_password_reset resolve estes nomes no namespace auth_routes.
        monkeypatch.setattr(auth_routes, "send_password_reset_email", send)
        monkeypatch.setattr(admin_route, "create_audit_log", audit)

        res = await admin_route.admin_send_password_reset("u1", _mock_request(), current_user=admin_user)

        mock_db.password_resets.insert_one.assert_awaited_once()
        send.assert_awaited_once()
        assert send.await_args.args[1] == "kiso@x.cv"  # (name, email, reset_url, token)
        audit.assert_awaited_once()
        assert audit.await_args.args[1] == "password_reset_sent_by_admin"
        assert "kiso@x.cv" in res["message"]
