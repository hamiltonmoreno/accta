"""Unit tests for auto-registo (spec-auto-registo).

Cobre:
- POST /api/auth/register (auth_routes): honeypot, consent, cargo inválido,
  duplicados (3 variantes), happy path (member_id sequencial, status,
  notify_admins, sem password).
- /api/admin/registration-requests {list,approve,reject} (admin): RBAC,
  validação de role, 404, happy paths (approve gera invite + email; reject
  marca rejeitado + email).

register tem `@limiter.limit` (slowapi): desligamos o limiter e passamos um
starlette.Request mínimo, invocando a rota directamente (sem TestClient, que
abriria ligação ao DB no startup) — mesmo padrão de test_auth_routes.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from routes import auth_routes
from routes import admin as admin_route
from models import RegistrationRequest, RegistrationApprove, RegistrationReject


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/auth/register",
            "headers": [],
            "client": ("127.0.0.1", 1234),
            "query_string": b"",
        }
    )


def _admin_request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


def _cursor(items):
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


@pytest.fixture
def reg_env(mock_db, monkeypatch):
    """Isola o register: limiter off, member_id determinístico, notify/audit no-op."""
    monkeypatch.setattr(auth_routes.limiter, "enabled", False)
    monkeypatch.setattr(auth_routes, "next_member_id", AsyncMock(return_value="ACCTA-0001"))
    monkeypatch.setattr(auth_routes, "notify_admins", AsyncMock())
    monkeypatch.setattr(auth_routes, "create_audit_log", AsyncMock())
    return mock_db


# --------------------------------------------------------------------------- #
# POST /api/auth/register
# --------------------------------------------------------------------------- #


class TestRegister:
    async def test_honeypot_discards_silently(self, reg_env):
        """Campo `website` preenchido (bot) → 201 falso, NÃO cria registo."""
        data = RegistrationRequest(name="Bot", email="bot@x.cv", consent_data=True, website="http://spam")
        result = await auth_routes.register(request=_request(), data=data)
        assert "request_id" in result
        reg_env.users.insert_one.assert_not_awaited()

    async def test_consent_required_400(self, reg_env):
        data = RegistrationRequest(name="Ana", email="ana@x.cv", consent_data=False)
        with pytest.raises(HTTPException) as exc:
            await auth_routes.register(request=_request(), data=data)
        assert exc.value.status_code == 400

    async def test_invalid_cargo_422(self, reg_env):
        data = RegistrationRequest(name="Ana", email="ana@x.cv", consent_data=True, cargo_declarado="Imperador")
        with pytest.raises(HTTPException) as exc:
            await auth_routes.register(request=_request(), data=data)
        assert exc.value.status_code == 422

    @pytest.mark.parametrize(
        "status,fragment",
        [
            ("ativo", "conta"),
            ("pendente_aprovacao", "análise"),
            ("rejeitado", "processar"),
        ],
    )
    async def test_duplicate_email_409(self, reg_env, status, fragment):
        reg_env.users.find_one = AsyncMock(return_value={"id": "ex", "status": status})
        data = RegistrationRequest(name="Ana", email="ana@x.cv", consent_data=True)
        with pytest.raises(HTTPException) as exc:
            await auth_routes.register(request=_request(), data=data)
        assert exc.value.status_code == 409
        assert fragment in exc.value.detail.lower()

    async def test_happy_path_creates_pending_request(self, reg_env):
        reg_env.users.find_one = AsyncMock(return_value=None)
        captured = {}

        async def capture_insert(doc):
            captured.update(doc)
            return MagicMock(inserted_id="x")

        reg_env.users.insert_one = capture_insert

        data = RegistrationRequest(
            name="João Candidato",
            email="joao@x.cv",
            consent_data=True,
            cargo_declarado="Tesoureiro",
            phone_number="999",
            department="Torre",
        )
        result = await auth_routes.register(request=_request(), data=data)

        assert result["request_id"] == captured["id"]
        assert captured["status"] == "pendente_aprovacao"
        assert captured["role"] == "socio"  # nunca escala no submit
        assert captured["member_id"] == "ACCTA-0001"  # sequencial do servidor
        assert captured["cargo_declarado"] == "Tesoureiro"
        assert captured["password"] == ""  # password só no setup-account
        assert "invite_token" not in captured
        assert captured["consent_data"] is True
        auth_routes.notify_admins.assert_awaited_once()


# --------------------------------------------------------------------------- #
# GET /api/admin/registration-requests
# --------------------------------------------------------------------------- #


class TestListRegistrationRequests:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.list_registration_requests(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_invalid_status_400(self, mock_db, admin_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.list_registration_requests(current_user=admin_user, status="ativo")
        assert exc.value.status_code == 400

    async def test_admin_lists_pending(self, mock_db, admin_user):
        captured = {}

        def find(query, proj):
            captured["query"] = query
            captured["proj"] = proj
            return _cursor([{"id": "r1", "name": "Ana"}])

        mock_db.users.find = find
        result = await admin_route.list_registration_requests(current_user=admin_user)
        assert result == [{"id": "r1", "name": "Ana"}]
        assert captured["query"] == {"status": "pendente_aprovacao"}
        assert captured["proj"]["password"] == 0
        assert captured["proj"]["invite_token"] == 0


# --------------------------------------------------------------------------- #
# POST /api/admin/registration-requests/{id}/approve
# --------------------------------------------------------------------------- #


class TestApproveRegistration:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.approve_registration(
                user_id="r1", request=_admin_request(), data=RegistrationApprove(), current_user=socio_user
            )
        assert exc.value.status_code == 403

    async def test_invalid_role_422(self, mock_db, admin_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.approve_registration(
                user_id="r1",
                request=_admin_request(),
                data=RegistrationApprove(role="superuser"),
                current_user=admin_user,
            )
        assert exc.value.status_code == 422

    async def test_not_found_404(self, mock_db, admin_user):
        mock_db.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await admin_route.approve_registration(
                user_id="r1", request=_admin_request(), data=RegistrationApprove(), current_user=admin_user
            )
        assert exc.value.status_code == 404

    async def test_approve_generates_invite(self, mock_db, admin_user, monkeypatch):
        mock_db.users.find_one = AsyncMock(
            return_value={
                "id": "r1",
                "name": "Ana",
                "email": "ana@x.cv",
                "status": "pendente_aprovacao",
                "cargo_declarado": "Tesoureiro",
                "member_id": "ACCTA-0007",
            }
        )
        captured = {}

        async def capture_update(filt, update):
            captured.update(update["$set"])
            return MagicMock(modified_count=1)

        mock_db.users.update_one = capture_update
        monkeypatch.setattr(admin_route, "send_invite_email", AsyncMock(return_value={"status": "sent"}))

        result = await admin_route.approve_registration(
            user_id="r1",
            request=_admin_request(),
            data=RegistrationApprove(role="financeiro"),
            current_user=admin_user,
        )
        assert captured["status"] == "pendente_convite"
        assert captured["role"] == "financeiro"  # admin escala no approve
        # herda o cargo_declarado ("Tesoureiro"), normalizado p/ key canónica
        assert captured["cargo"] == "dir_tesoureiro"
        assert captured["orgao"] == "direcao"
        # cargo estatutário cria a 1ª entrada de mandato
        assert captured["cargo_history"][-1]["cargo"] == "dir_tesoureiro"
        assert captured["invite_token"]
        assert "invite_token_expires_at" in captured
        assert captured["registration_reviewer_id"] == admin_user.id
        assert result["email_sent"] is True
        admin_route.send_invite_email.assert_awaited_once()


# --------------------------------------------------------------------------- #
# POST /api/admin/registration-requests/{id}/reject
# --------------------------------------------------------------------------- #


class TestRejectRegistration:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.reject_registration(
                user_id="r1", request=_admin_request(), data=RegistrationReject(), current_user=socio_user
            )
        assert exc.value.status_code == 403

    async def test_not_found_404(self, mock_db, admin_user):
        mock_db.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await admin_route.reject_registration(
                user_id="r1", request=_admin_request(), data=RegistrationReject(), current_user=admin_user
            )
        assert exc.value.status_code == 404

    async def test_reject_sets_status_and_emails(self, mock_db, admin_user, monkeypatch):
        mock_db.users.find_one = AsyncMock(
            return_value={"id": "r1", "name": "Ana", "email": "ana@x.cv", "status": "pendente_aprovacao"}
        )
        captured = {}

        async def capture_update(filt, update):
            captured.update(update["$set"])
            return MagicMock(modified_count=1)

        mock_db.users.update_one = capture_update
        sent = AsyncMock(return_value={"status": "sent"})
        monkeypatch.setattr(admin_route, "send_registration_rejected_email", sent)

        result = await admin_route.reject_registration(
            user_id="r1",
            request=_admin_request(),
            data=RegistrationReject(reason="Fora de âmbito"),
            current_user=admin_user,
        )
        assert captured["status"] == "rejeitado"
        assert captured["registration_rejection_reason"] == "Fora de âmbito"
        assert captured["registration_reviewer_id"] == admin_user.id
        assert result["message"] == "Pedido rejeitado."
        sent.assert_awaited_once_with("Ana", "ana@x.cv", "Fora de âmbito")
