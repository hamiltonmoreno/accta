"""Unit tests for routes/auth_routes.py — Spec-2 setup-account hardening.

Branch fix/health-audit mudou o fluxo de activacao de conta:
- `setup_account` ganhou `background_tasks`: o welcome email passa a ser
  agendado (BackgroundTasks) em vez de `await` inline -> a resposta de
  activacao nao bloqueia/atrasa se a Resend estiver lenta ou indisponivel.
- A senha minima e 6, aplicada pelo proprio modelo Pydantic
  (`SetupAccount.password = Field(min_length=6)`), idem PasswordResetConfirm.

setup_account tem `@limiter.limit` (slowapi) que exige um Request real e
faz a sua propria verificacao; desligamos o limiter no teste e passamos um
starlette.Request minimo, invocando a rota directamente (sem TestClient,
que abriria ligacao ao DB no startup).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import BackgroundTasks, Response
from starlette.requests import Request

from routes import auth_routes


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/auth/setup-account",
            "headers": [],
            "client": ("127.0.0.1", 1234),
            "query_string": b"",
        }
    )


def _pending_user(**extra) -> dict:
    base = {
        "id": "u1",
        "name": "Maria Convidada",
        "email": "maria@controlador.cv",
        "role": "socio",
        "status": "pendente_convite",
        "cargo": "Sócio",
        "privileges": [],
        "consent_data": True,
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    base.update(extra)
    return base


@pytest.fixture
def setup_env(mock_db, monkeypatch):
    """mock_db ja faz patch de routes.auth_routes.db. Aqui isolamos o resto:
    welcome email observavel, audit/cookie no-op, limiter desligado."""
    welcome = AsyncMock()
    monkeypatch.setattr(auth_routes, "send_welcome_email", welcome)
    monkeypatch.setattr(auth_routes, "create_audit_log", AsyncMock())
    monkeypatch.setattr(auth_routes, "set_session_cookie", lambda resp, tok: None)
    monkeypatch.setattr(auth_routes.limiter, "enabled", False)
    return welcome


# --------------------------------------------------------------------------- #
# Pydantic: senha minima de 6 aplicada no modelo
# --------------------------------------------------------------------------- #


class TestPasswordMinLengthModels:
    async def test_setup_account_rejects_short_password(self):
        from pydantic import ValidationError
        from models import SetupAccount

        SetupAccount(token="t", password="abcd1234")  # 8 -> ok
        with pytest.raises(ValidationError):
            SetupAccount(token="t", password="abc1234")  # 7 -> rejeitado

    async def test_password_reset_confirm_rejects_short_password(self):
        from pydantic import ValidationError
        from models import PasswordResetConfirm

        PasswordResetConfirm(token="t", new_password="abcd1234")
        with pytest.raises(ValidationError):
            PasswordResetConfirm(token="t", new_password="1234567")  # 7 -> rejeitado


# --------------------------------------------------------------------------- #
# setup_account — welcome email non-blocking via BackgroundTasks
# --------------------------------------------------------------------------- #


class TestSetupAccount:
    async def test_welcome_email_is_scheduled_not_awaited(self, mock_db, setup_env):
        from models import SetupAccount

        welcome = setup_env
        mock_db.users.find_one = AsyncMock(return_value=_pending_user())
        bt = BackgroundTasks()

        result = await auth_routes.setup_account(
            request=_request(),
            response=Response(),
            background_tasks=bt,
            data=SetupAccount(token="valid-token", password="abcd1234"),
        )

        assert result["message"] == "Conta ativada com sucesso!"
        assert result["access_token"]
        # NAO enviado inline — a resposta nao espera pela Resend.
        welcome.assert_not_awaited()
        # Agendado como background task com (name, email) do utilizador.
        assert [t.func for t in bt.tasks] == [welcome]
        assert bt.tasks[0].args == ("Maria Convidada", "maria@controlador.cv")

    async def test_invalid_or_used_token_400(self, mock_db, setup_env):
        from models import SetupAccount

        mock_db.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(Exception) as exc:
            await auth_routes.setup_account(
                request=_request(),
                response=Response(),
                background_tasks=BackgroundTasks(),
                data=SetupAccount(token="bad", password="abcd1234"),
            )
        assert getattr(exc.value, "status_code", None) == 400

    async def test_expired_invite_token_400(self, mock_db, setup_env):
        from models import SetupAccount

        mock_db.users.find_one = AsyncMock(
            return_value=_pending_user(invite_token_expires_at="2020-01-01T00:00:00+00:00")
        )
        bt = BackgroundTasks()
        with pytest.raises(Exception) as exc:
            await auth_routes.setup_account(
                request=_request(),
                response=Response(),
                background_tasks=bt,
                data=SetupAccount(token="expired", password="abcd1234"),
            )
        assert getattr(exc.value, "status_code", None) == 400
        # Conta nao activada -> nenhum welcome agendado.
        assert bt.tasks == []
