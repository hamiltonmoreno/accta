"""Unit tests for routes/users.py — RBAC, profile updates, admin operations.

Tests directly invoke route functions (no TestClient) so they're fast +
no real DB. mock_db fixture provides AsyncMock collections.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import users as users_route


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


# --------------------------------------------------------------------------- #
# GET /users — list (admin/financeiro only)
# --------------------------------------------------------------------------- #


class TestListUsers:
    async def test_admin_can_list(self, mock_db, admin_user):
        mock_db.users.find().skip().limit().to_list = AsyncMock(return_value=[])
        result = await users_route.get_users(current_user=admin_user)
        assert result == []

    async def test_financeiro_can_list(self, mock_db, financeiro_user):
        mock_db.users.find().skip().limit().to_list = AsyncMock(return_value=[])
        result = await users_route.get_users(current_user=financeiro_user)
        assert result == []

    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await users_route.get_users(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_moderador_403(self, mock_db, moderador_user):
        with pytest.raises(HTTPException) as exc:
            await users_route.get_users(current_user=moderador_user)
        assert exc.value.status_code == 403

    async def test_search_escapes_regex_metachars(self, mock_db, admin_user):
        """Sprint 3 fix — input com . * + etc nao deve gerar ReDoS."""
        captured_query = {}

        def capture_find(query, _proj):
            captured_query.update(query)
            cursor = MagicMock()
            cursor.skip = MagicMock(return_value=cursor)
            cursor.limit = MagicMock(return_value=cursor)
            cursor.to_list = AsyncMock(return_value=[])
            return cursor

        mock_db.users.find = capture_find
        await users_route.get_users(search=".*+?[]{}()", current_user=admin_user)
        # Cada metachar deve aparecer escapado (\\) no regex.
        regex = captured_query["$or"][0]["name"]["$regex"]
        assert "\\.\\*\\+\\?\\[\\]\\{\\}\\(\\)" == regex

    async def test_search_truncated_to_100_chars(self, mock_db, admin_user):
        captured_query = {}

        def capture_find(query, _proj):
            captured_query.update(query)
            cursor = MagicMock()
            cursor.skip = MagicMock(return_value=cursor)
            cursor.limit = MagicMock(return_value=cursor)
            cursor.to_list = AsyncMock(return_value=[])
            return cursor

        mock_db.users.find = capture_find
        long_input = "a" * 500
        await users_route.get_users(search=long_input, current_user=admin_user)
        regex = captured_query["$or"][0]["name"]["$regex"]
        # 100 'a' chars (re.escape de 'a' = 'a').
        assert len(regex) == 100

    async def test_limit_capped_at_100(self, mock_db, admin_user):
        """Defensive — passar limit=10000 nao puxa 10k docs do DB."""
        recorded = {}

        def capture_find(_q, _proj):
            cursor = MagicMock()
            cursor.skip = MagicMock(return_value=cursor)

            def lim(n):
                recorded["limit"] = n
                return cursor

            cursor.limit = lim
            cursor.to_list = AsyncMock(return_value=[])
            return cursor

        mock_db.users.find = capture_find
        await users_route.get_users(limit=10000, current_user=admin_user)
        assert recorded["limit"] == 100


# --------------------------------------------------------------------------- #
# GET /users/{id} — self ou staff
# --------------------------------------------------------------------------- #


class TestGetUser:
    async def test_self_can_view_own(self, mock_db, socio_user_dict):
        from models import User

        socio = User(**socio_user_dict)
        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        result = await users_route.get_user(user_id=socio.id, current_user=socio)
        assert result["id"] == socio.id

    async def test_admin_can_view_other(self, mock_db, admin_user, socio_user_dict):
        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        result = await users_route.get_user(user_id="other-id", current_user=admin_user)
        assert result is not None

    async def test_financeiro_can_view_other(self, mock_db, financeiro_user, socio_user_dict):
        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        result = await users_route.get_user(user_id="other-id", current_user=financeiro_user)
        assert result is not None

    async def test_socio_cannot_view_other(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await users_route.get_user(user_id="other-id", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_moderador_cannot_view_other(self, mock_db, moderador_user):
        """Moderador modera content, nao tem acesso a PII completa."""
        with pytest.raises(HTTPException) as exc:
            await users_route.get_user(user_id="other-id", current_user=moderador_user)
        assert exc.value.status_code == 403

    async def test_404_when_user_not_found(self, mock_db, admin_user):
        mock_db.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await users_route.get_user(user_id="nonexistent", current_user=admin_user)
        assert exc.value.status_code == 404


# --------------------------------------------------------------------------- #
# PATCH /users/me/profile — self update
# --------------------------------------------------------------------------- #


class TestUpdateOwnProfile:
    async def test_updates_allowed_fields(self, mock_db, socio_user, socio_user_dict):
        from models import UserProfileUpdate

        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        update = UserProfileUpdate(name="Novo Nome", phone_number="+238 555 1234", bio="bio")
        result = await users_route.update_own_profile(data=update, current_user=socio_user)
        # update_one foi chamado com $set apenas dos campos preenchidos.
        call_args = mock_db.users.update_one.call_args
        assert call_args[0][0] == {"id": socio_user.id}
        set_data = call_args[0][1]["$set"]
        assert "name" in set_data and "phone_number" in set_data and "bio" in set_data

    async def test_400_when_no_fields_provided(self, mock_db, socio_user):
        from models import UserProfileUpdate

        update = UserProfileUpdate()  # tudo None
        with pytest.raises(HTTPException) as exc:
            await users_route.update_own_profile(data=update, current_user=socio_user)
        assert exc.value.status_code == 400


# --------------------------------------------------------------------------- #
# PATCH /users/{id} — admin only
# --------------------------------------------------------------------------- #


def _mock_request():
    """Helper: Request fake suficiente para create_audit_log."""

    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test"}

    return _R()


class TestAdminUpdateUser:
    async def test_socio_403(self, mock_db, socio_user):
        from models import UserAdminUpdate

        with pytest.raises(HTTPException) as exc:
            await users_route.admin_update_user(
                user_id="any",
                data=UserAdminUpdate(name="X"),
                request=_mock_request(),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_financeiro_403(self, mock_db, financeiro_user):
        """Financeiro pode ler users mas nao editar — apenas admin."""
        from models import UserAdminUpdate

        with pytest.raises(HTTPException) as exc:
            await users_route.admin_update_user(
                user_id="any",
                data=UserAdminUpdate(name="X"),
                request=_mock_request(),
                current_user=financeiro_user,
            )
        assert exc.value.status_code == 403

    async def test_404_when_target_not_found(self, mock_db, admin_user):
        from models import UserAdminUpdate

        mock_db.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await users_route.admin_update_user(
                user_id="missing",
                data=UserAdminUpdate(name="X"),
                request=_mock_request(),
                current_user=admin_user,
            )
        assert exc.value.status_code == 404

    async def test_invalid_cargo_400(self, mock_db, admin_user, socio_user_dict):
        from models import UserAdminUpdate

        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        with pytest.raises(HTTPException) as exc:
            await users_route.admin_update_user(
                user_id="any",
                data=UserAdminUpdate(cargo="CargoQueNaoExiste"),
                request=_mock_request(),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_invalid_role_400(self, mock_db, admin_user, socio_user_dict):
        from models import UserAdminUpdate

        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        with pytest.raises(HTTPException) as exc:
            await users_route.admin_update_user(
                user_id="any",
                data=UserAdminUpdate(role="superadmin"),
                request=_mock_request(),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_invalid_privileges_400(self, mock_db, admin_user, socio_user_dict):
        from models import UserAdminUpdate

        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        with pytest.raises(HTTPException) as exc:
            await users_route.admin_update_user(
                user_id="any",
                data=UserAdminUpdate(privileges=["nonexistent_privilege"]),
                request=_mock_request(),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400


# --------------------------------------------------------------------------- #
# DELETE /users/{id}
# --------------------------------------------------------------------------- #


class TestDeleteUser:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await users_route.delete_user(user_id="any", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_admin_cannot_delete_self(self, mock_db, admin_user):
        with pytest.raises(HTTPException) as exc:
            await users_route.delete_user(user_id=admin_user.id, current_user=admin_user)
        assert exc.value.status_code == 400

    async def test_404_when_target_not_found(self, mock_db, admin_user):
        mock_db.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await users_route.delete_user(user_id="missing", current_user=admin_user)
        assert exc.value.status_code == 404

    async def test_admin_deletes_other(self, mock_db, admin_user, socio_user_dict):
        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        result = await users_route.delete_user(
            user_id=socio_user_dict["id"], current_user=admin_user
        )
        assert "removido" in result["message"].lower()
        mock_db.users.delete_one.assert_awaited_once_with({"id": socio_user_dict["id"]})


# --------------------------------------------------------------------------- #
# PATCH /users/{id}/status (legacy endpoint)
# --------------------------------------------------------------------------- #


class TestUpdateUserStatus:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await users_route.update_user_status(
                user_id="any", status="inativo", current_user=socio_user
            )
        assert exc.value.status_code == 403

    async def test_admin_updates_status(self, mock_db, admin_user):
        result = await users_route.update_user_status(
            user_id="some-id", status="inativo", current_user=admin_user
        )
        assert "atualizado" in result["message"].lower()
        mock_db.users.update_one.assert_awaited_with(
            {"id": "some-id"}, {"$set": {"status": "inativo"}}
        )


# --------------------------------------------------------------------------- #
# Metadata endpoints (no auth)
# --------------------------------------------------------------------------- #


class TestMeta:
    async def test_cargos_returns_list(self):
        result = await users_route.get_cargos()
        assert isinstance(result["cargos"], list) and len(result["cargos"]) > 0

    async def test_privileges_returns_list(self):
        result = await users_route.get_privileges()
        assert isinstance(result["privileges"], list) and len(result["privileges"]) > 0
