"""Unit tests for routes/admin.py — invite flow, RBAC."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import admin as admin_route


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _cursor(items):
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


def _mock_request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


# --------------------------------------------------------------------------- #
# POST /admin/invite
# --------------------------------------------------------------------------- #


class TestInviteUser:
    async def test_socio_403(self, mock_db, socio_user, monkeypatch):
        from models import InviteCreate

        with pytest.raises(HTTPException) as exc:
            await admin_route.invite_user(
                request=_mock_request(),
                data=InviteCreate(name="X", email="x@y.com"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_financeiro_403(self, mock_db, financeiro_user):
        from models import InviteCreate

        with pytest.raises(HTTPException) as exc:
            await admin_route.invite_user(
                request=_mock_request(),
                data=InviteCreate(name="X", email="x@y.com"),
                current_user=financeiro_user,
            )
        assert exc.value.status_code == 403

    async def test_email_already_registered_400(self, mock_db, admin_user):
        from models import InviteCreate

        mock_db.users.find_one = AsyncMock(return_value={"id": "existing", "email": "x@y.com"})
        with pytest.raises(HTTPException) as exc:
            await admin_route.invite_user(
                request=_mock_request(),
                data=InviteCreate(name="X", email="x@y.com"),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_admin_creates_invite(self, mock_db, admin_user, monkeypatch):
        from models import InviteCreate

        mock_db.users.find_one = AsyncMock(return_value=None)

        # Mock send_invite_email to avoid trying to send.
        async def fake_send(*args, **kwargs):
            return {"status": "sent"}

        monkeypatch.setattr(admin_route, "send_invite_email", fake_send)
        monkeypatch.setattr(admin_route, "next_member_id", AsyncMock(return_value="ACCTA-0042"))

        data = InviteCreate(name="João Silva", email="joao@x.cv", role="socio", cargo="Sócio")
        result = await admin_route.invite_user(request=_mock_request(), data=data, current_user=admin_user)

        # Spec-2 fix: invite_token NAO devolvido na response NEM no path —
        # o token segue apenas no email ao convidado (evita leak por
        # logs/MITM/historial/APM). setup_url e agora um path estatico.
        assert "invite_token" not in result
        assert result["email"] == "joao@x.cv"
        assert result["setup_url"] == "/setup-account"
        assert "token" not in result["setup_url"]
        assert "expires_at" in result
        mock_db.users.insert_one.assert_awaited_once()

    async def test_invalid_role_falls_back_to_socio(self, mock_db, admin_user, monkeypatch):
        """Role 'admin' NAO pode ser convidado via invite — fallback para socio."""
        from models import InviteCreate

        mock_db.users.find_one = AsyncMock(return_value=None)

        captured_doc = {}

        async def capture_insert(doc):
            captured_doc.update(doc)
            return MagicMock(inserted_id="x")

        mock_db.users.insert_one = capture_insert

        async def fake_send(*args, **kwargs):
            return {"status": "sent"}

        monkeypatch.setattr(admin_route, "send_invite_email", fake_send)
        monkeypatch.setattr(admin_route, "next_member_id", AsyncMock(return_value="ACCTA-0042"))

        data = InviteCreate(name="X", email="x@y.com", role="admin")
        await admin_route.invite_user(request=_mock_request(), data=data, current_user=admin_user)
        # role admin nao consta na whitelist [socio/financeiro/moderador] -> fallback socio
        assert captured_doc["role"] == "socio"

    async def test_direct_invite_rejects_statutory_cargo(self, mock_db, admin_user, monkeypatch):
        from models import InviteCreate

        mock_db.users.find_one = AsyncMock(return_value=None)
        monkeypatch.setattr(admin_route, "next_member_id", AsyncMock(return_value="ACCTA-0042"))
        with pytest.raises(HTTPException) as exc:
            await admin_route.invite_user(
                request=_mock_request(),
                data=InviteCreate(name="X", email="x@y.com", cargo="Tesoureiro"),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400
        mock_db.users.insert_one.assert_not_awaited()

    async def test_invite_token_has_expiry(self, mock_db, admin_user, monkeypatch):
        """Sprint 1+2 fix: invite_token tem TTL 7 dias."""
        from models import InviteCreate

        mock_db.users.find_one = AsyncMock(return_value=None)

        captured_doc = {}

        async def capture_insert(doc):
            captured_doc.update(doc)
            return MagicMock(inserted_id="x")

        mock_db.users.insert_one = capture_insert

        async def fake_send(*args, **kwargs):
            return {"status": "sent"}

        monkeypatch.setattr(admin_route, "send_invite_email", fake_send)
        monkeypatch.setattr(admin_route, "next_member_id", AsyncMock(return_value="ACCTA-0042"))

        data = InviteCreate(name="X", email="x@y.com")
        await admin_route.invite_user(request=_mock_request(), data=data, current_user=admin_user)
        assert "invite_token_expires_at" in captured_doc
        assert captured_doc["invite_token_expires_at"]


# --------------------------------------------------------------------------- #
# GET /admin/invites/pending
# --------------------------------------------------------------------------- #


class TestGetPendingInvites:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.get_pending_invites(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_admin_lists_pending(self, mock_db, admin_user):
        captured = {}

        def find(query, proj):
            captured["query"] = query
            captured["proj"] = proj
            return _cursor([])

        mock_db.users.find = find
        result = await admin_route.get_pending_invites(current_user=admin_user)
        assert result == []
        assert captured["query"] == {"status": "pendente_convite"}
        # Sprint 1+2 fix: password e invite_token excluidos do projection.
        assert captured["proj"]["password"] == 0
        assert captured["proj"]["invite_token"] == 0


# --------------------------------------------------------------------------- #
# DELETE /admin/invite/{user_id}
# --------------------------------------------------------------------------- #


class TestRevokeInvite:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.revoke_invite(user_id="any", request=_mock_request(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_404_when_already_active(self, mock_db, admin_user):
        """find_one com filter status:pendente_convite — se utilizador ja
        activou, query retorna None."""
        mock_db.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await admin_route.revoke_invite(user_id="active-user", request=_mock_request(), current_user=admin_user)
        assert exc.value.status_code == 404

    async def test_admin_revokes(self, mock_db, admin_user):
        mock_db.users.find_one = AsyncMock(
            return_value={"id": "u1", "name": "X", "email": "x@y.com", "status": "pendente_convite"}
        )
        result = await admin_route.revoke_invite(user_id="u1", request=_mock_request(), current_user=admin_user)
        assert "revogado" in result["message"].lower()
        mock_db.users.delete_one.assert_awaited_with({"id": "u1"})
