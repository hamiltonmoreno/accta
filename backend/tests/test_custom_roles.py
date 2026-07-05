"""Unit tests for funções personalizadas (spec 017).

Cobre:
- US1 (T006): CRUD de /api/admin/custom-roles + RBAC + validações + audit.
- US2 (T012): atribuição/destaque em PATCH /users/{id} + convite +
              destaque via promote de cargo estatutário.
- US3 (T015): propagação de privilégios via update_many + notificações,
              e propagated_to=0 quando privileges não muda.

`mock_db.custom_roles` NÃO está pré-wired no conftest — wire em-teste.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import custom_roles as cr_route
from routes import users as users_route
from routes import admin as admin_route


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _mock_request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


def _wire_custom_roles(mock_db, existing=None, users_with_role=None):
    """Instala mock_db.custom_roles + comportamento útil (find/find_one/insert/update/delete/count)."""
    coll = MagicMock(name="custom_roles")
    existing = list(existing or [])

    def find(query=None, projection=None):
        cursor = MagicMock()
        cursor.to_list = AsyncMock(return_value=list(existing))
        cursor.sort = MagicMock(return_value=cursor)
        cursor.limit = MagicMock(return_value=cursor)
        return cursor

    async def find_one(query, projection=None):
        rid = query.get("id")
        for r in existing:
            if r.get("id") == rid:
                return dict(r)
        return None

    async def count_documents(query):
        rid = query.get("custom_role_id")
        return sum(1 for u in (users_with_role or []) if u.get("custom_role_id") == rid)

    coll.find = MagicMock(side_effect=find)
    coll.find_one = AsyncMock(side_effect=find_one)
    coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="mock_id"))
    coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    coll.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    coll.count_documents = AsyncMock(side_effect=count_documents)
    mock_db.custom_roles = coll

    # Contagem por-função vem de db.users.find(...).to_list — deixamos o cursor
    # devolver as linhas simuladas de users_with_role.
    users_cursor = MagicMock()
    users_cursor.to_list = AsyncMock(return_value=list(users_with_role or []))
    mock_db.users.find = MagicMock(return_value=users_cursor)
    mock_db.users.count_documents = AsyncMock(
        side_effect=lambda q: sum(
            1 for u in (users_with_role or []) if u.get("custom_role_id") == q.get("custom_role_id")
        )
    )
    return coll


# --------------------------------------------------------------------------- #
# US1 — CRUD /api/admin/custom-roles
# --------------------------------------------------------------------------- #


class TestListCustomRoles:
    async def test_admin_lists_with_user_count(self, mock_db, admin_user):
        _wire_custom_roles(
            mock_db,
            existing=[{"id": "r1", "name": "Coordenador de Eventos", "privileges": ["manage_events"]}],
            users_with_role=[{"custom_role_id": "r1"}, {"custom_role_id": "r1"}, {"custom_role_id": None}],
        )
        result = await cr_route.list_custom_roles(current_user=admin_user)
        assert len(result["custom_roles"]) == 1
        assert result["custom_roles"][0]["user_count"] == 2

    @pytest.mark.parametrize("role_fx", ["socio_user", "financeiro_user", "moderador_user"])
    async def test_non_admin_403(self, mock_db, request, role_fx):
        _wire_custom_roles(mock_db)
        user = request.getfixturevalue(role_fx)
        with pytest.raises(HTTPException) as exc:
            await cr_route.list_custom_roles(current_user=user)
        assert exc.value.status_code == 403


class TestCreateCustomRole:
    async def test_admin_creates(self, mock_db, admin_user):
        from models import CustomRoleCreate

        _wire_custom_roles(mock_db)
        data = CustomRoleCreate(name="Coordenador de Eventos", privileges=["manage_events"])
        doc = await cr_route.create_custom_role(data=data, request=_mock_request(), current_user=admin_user)
        assert doc["name"] == "Coordenador de Eventos"
        assert doc["user_count"] == 0
        mock_db.custom_roles.insert_one.assert_awaited_once()

    async def test_socio_403(self, mock_db, socio_user):
        from models import CustomRoleCreate

        _wire_custom_roles(mock_db)
        with pytest.raises(HTTPException) as exc:
            await cr_route.create_custom_role(
                data=CustomRoleCreate(name="X", privileges=["manage_events"]),
                request=_mock_request(),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_duplicate_name_400(self, mock_db, admin_user):
        from models import CustomRoleCreate

        _wire_custom_roles(
            mock_db,
            existing=[{"id": "r1", "name": "Coordenador"}],
        )
        with pytest.raises(HTTPException) as exc:
            await cr_route.create_custom_role(
                data=CustomRoleCreate(name="  coordenador  ", privileges=["manage_events"]),
                request=_mock_request(),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400

    # spec 018: níveis de acesso + NOMES das funções seed de transição
    # («Financeiro»/«Moderador» são a identidade que resolve_legacy_role resolve
    # por nome) ficam reservados — impede uma homónima que a tradução D4
    # captaria em vez da seed (corrige a janela pré-seed da R5 original).
    @pytest.mark.parametrize("reserved", ["Administração", "admin", "Sócio", "Financeiro", "moderador", "FINANCEIRO"])
    async def test_collision_with_fixed_400(self, mock_db, admin_user, reserved):
        from models import CustomRoleCreate

        _wire_custom_roles(mock_db)
        with pytest.raises(HTTPException) as exc:
            await cr_route.create_custom_role(
                data=CustomRoleCreate(name=reserved, privileges=["manage_events"]),
                request=_mock_request(),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400

    def test_empty_privileges_422(self):
        from models import CustomRoleCreate

        with pytest.raises(ValueError):
            CustomRoleCreate(name="X", privileges=[])

    def test_duplicate_privileges_422(self):
        from models import CustomRoleCreate

        with pytest.raises(ValueError):
            CustomRoleCreate(name="X", privileges=["manage_events", "manage_events"])

    def test_unknown_privilege_422(self):
        from models import CustomRoleCreate

        with pytest.raises(ValueError):
            CustomRoleCreate(name="X", privileges=["nope"])


class TestUpdateCustomRole:
    async def test_admin_edits_name(self, mock_db, admin_user):
        from models import CustomRoleUpdate

        _wire_custom_roles(
            mock_db,
            existing=[{"id": "r1", "name": "Antigo", "privileges": ["manage_events"]}],
        )
        result = await cr_route.update_custom_role(
            role_id="r1",
            data=CustomRoleUpdate(name="Novo"),
            request=_mock_request(),
            current_user=admin_user,
        )
        mock_db.custom_roles.update_one.assert_awaited()
        # Só mudou o nome → propagated_to fica em 0.
        assert result.get("propagated_to") == 0

    async def test_404_when_missing(self, mock_db, admin_user):
        from models import CustomRoleUpdate

        _wire_custom_roles(mock_db)
        with pytest.raises(HTTPException) as exc:
            await cr_route.update_custom_role(
                role_id="ghost",
                data=CustomRoleUpdate(name="X"),
                request=_mock_request(),
                current_user=admin_user,
            )
        assert exc.value.status_code == 404


class TestDeleteCustomRole:
    async def test_admin_deletes_when_unused(self, mock_db, admin_user):
        _wire_custom_roles(mock_db, existing=[{"id": "r1", "name": "X"}], users_with_role=[])
        result = await cr_route.delete_custom_role(role_id="r1", request=_mock_request(), current_user=admin_user)
        assert "eliminada" in result["message"].lower()
        mock_db.custom_roles.delete_one.assert_awaited_once()

    async def test_409_when_in_use(self, mock_db, admin_user):
        _wire_custom_roles(
            mock_db,
            existing=[{"id": "r1", "name": "X"}],
            users_with_role=[{"custom_role_id": "r1"}, {"custom_role_id": "r1"}],
        )
        with pytest.raises(HTTPException) as exc:
            await cr_route.delete_custom_role(role_id="r1", request=_mock_request(), current_user=admin_user)
        assert exc.value.status_code == 409
        assert "2" in exc.value.detail
        mock_db.custom_roles.delete_one.assert_not_awaited()

    async def test_404_when_missing(self, mock_db, admin_user):
        _wire_custom_roles(mock_db)
        with pytest.raises(HTTPException) as exc:
            await cr_route.delete_custom_role(role_id="ghost", request=_mock_request(), current_user=admin_user)
        assert exc.value.status_code == 404


# --------------------------------------------------------------------------- #
# US3 — propagação por edição de privilégios
# --------------------------------------------------------------------------- #


class TestPropagation:
    async def test_privileges_change_propagates_and_notifies(self, mock_db, admin_user, monkeypatch):
        from models import CustomRoleUpdate

        _wire_custom_roles(
            mock_db,
            existing=[
                {"id": "r1", "name": "Coord Eventos", "privileges": ["manage_events"]},
            ],
        )
        # 2 sócios com a função — cursor sob db.users.find(custom_role_id=r1)
        holders_cursor = MagicMock()
        holders_cursor.to_list = AsyncMock(return_value=[{"id": "u1"}, {"id": "u2"}])
        mock_db.users.find = MagicMock(return_value=holders_cursor)
        mock_db.users.update_many = AsyncMock(return_value=MagicMock(modified_count=2))

        notified = []

        async def fake_notify(user_id, ntype, title, body, link=None):
            notified.append((user_id, ntype, title))

        monkeypatch.setattr(cr_route, "create_notification", fake_notify)

        result = await cr_route.update_custom_role(
            role_id="r1",
            data=CustomRoleUpdate(privileges=["manage_events", "manage_documents"]),
            request=_mock_request(),
            current_user=admin_user,
        )

        mock_db.users.update_many.assert_awaited_once()
        args, _ = mock_db.users.update_many.await_args
        assert args[0] == {"custom_role_id": "r1"}
        assert args[1] == {"$set": {"privileges": ["manage_events", "manage_documents"]}}
        assert {u for (u, _t, _tt) in notified} == {"u1", "u2"}
        assert result["propagated_to"] == 2

    async def test_no_privilege_change_no_propagation(self, mock_db, admin_user, monkeypatch):
        from models import CustomRoleUpdate

        _wire_custom_roles(
            mock_db,
            existing=[{"id": "r1", "name": "Coord", "privileges": ["manage_events"]}],
        )
        mock_db.users.update_many = AsyncMock()
        monkeypatch.setattr(cr_route, "create_notification", AsyncMock())

        result = await cr_route.update_custom_role(
            role_id="r1",
            data=CustomRoleUpdate(description="apenas descrição"),
            request=_mock_request(),
            current_user=admin_user,
        )
        mock_db.users.update_many.assert_not_awaited()
        assert result["propagated_to"] == 0


# --------------------------------------------------------------------------- #
# US2 — atribuição em PATCH /users/{id}
# --------------------------------------------------------------------------- #


class TestAssignmentViaUserPatch:
    async def test_custom_role_id_materializes_role_and_privileges(self, mock_db, admin_user, socio_user_dict):
        from models import UserAdminUpdate

        socio_user_dict["custom_role_id"] = None
        socio_user_dict["role"] = "socio"
        socio_user_dict["privileges"] = []
        _wire_custom_roles(
            mock_db,
            existing=[{"id": "r1", "name": "Coord", "privileges": ["manage_events", "manage_documents"]}],
        )
        # find_one em db.users devolve o utilizador
        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)

        await users_route.admin_update_user(
            user_id=socio_user_dict["id"],
            data=UserAdminUpdate(custom_role_id="r1"),
            request=_mock_request(),
            current_user=admin_user,
        )
        mock_db.users.update_one.assert_awaited()
        _, kwargs = mock_db.users.update_one.await_args
        args, _ = mock_db.users.update_one.await_args
        update = args[1]["$set"]
        assert update["role"] == "socio"
        assert update["privileges"] == ["manage_events", "manage_documents"]
        assert update["custom_role_id"] == "r1"

    async def test_missing_custom_role_400(self, mock_db, admin_user, socio_user_dict):
        from models import UserAdminUpdate

        _wire_custom_roles(mock_db, existing=[])
        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        with pytest.raises(HTTPException) as exc:
            await users_route.admin_update_user(
                user_id=socio_user_dict["id"],
                data=UserAdminUpdate(custom_role_id="ghost"),
                request=_mock_request(),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_explicit_role_or_privs_unlinks_custom_role(self, mock_db, admin_user, socio_user_dict):
        """Escrita explícita de role ou privileges destaca (limpa) a função."""
        from models import UserAdminUpdate

        socio_user_dict["custom_role_id"] = "r1"
        socio_user_dict["privileges"] = ["manage_events"]
        _wire_custom_roles(mock_db, existing=[{"id": "r1", "name": "X", "privileges": ["manage_events"]}])
        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)

        await users_route.admin_update_user(
            user_id=socio_user_dict["id"],
            data=UserAdminUpdate(privileges=["manage_documents"]),
            request=_mock_request(),
            current_user=admin_user,
        )
        args, _ = mock_db.users.update_one.await_args
        update = args[1]["$set"]
        assert update["privileges"] == ["manage_documents"]
        assert update["custom_role_id"] is None

    async def test_precedence_over_role_in_same_payload(self, mock_db, admin_user, socio_user_dict):
        """Se `custom_role_id` está no payload, ele ganha sobre `role`/`privileges` explícitos."""
        from models import UserAdminUpdate

        socio_user_dict["custom_role_id"] = None
        _wire_custom_roles(
            mock_db,
            existing=[{"id": "r1", "name": "X", "privileges": ["manage_events"]}],
        )
        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)

        await users_route.admin_update_user(
            user_id=socio_user_dict["id"],
            data=UserAdminUpdate(
                custom_role_id="r1",
                role="admin",
                privileges=["manage_documents"],
            ),
            request=_mock_request(),
            current_user=admin_user,
        )
        args, _ = mock_db.users.update_one.await_args
        update = args[1]["$set"]
        assert update["role"] == "socio"
        assert update["privileges"] == ["manage_events"]
        assert update["custom_role_id"] == "r1"


# --------------------------------------------------------------------------- #
# US2 — convite com custom_role_id
# --------------------------------------------------------------------------- #


class TestInviteWithCustomRole:
    async def test_invite_materializes_socio_plus_privileges(self, mock_db, admin_user, monkeypatch):
        from models import InviteCreate

        _wire_custom_roles(
            mock_db,
            existing=[{"id": "r1", "name": "Coord", "privileges": ["manage_events"]}],
        )
        mock_db.users.find_one = AsyncMock(return_value=None)
        monkeypatch.setattr(admin_route, "next_member_id", AsyncMock(return_value="ACCTA-9998"))

        async def fake_send(*_a, **_kw):
            return {"status": "sent"}

        monkeypatch.setattr(admin_route, "send_invite_email", fake_send)

        data = InviteCreate(
            name="Novo",
            email="novo@x.cv",
            role="admin",  # deve ser sobreposto por causa da função personalizada
            custom_role_id="r1",
        )
        await admin_route.invite_user(request=_mock_request(), data=data, current_user=admin_user)

        mock_db.users.insert_one.assert_awaited_once()
        (inserted,), _ = mock_db.users.insert_one.await_args
        assert inserted["role"] == "socio"
        assert inserted["privileges"] == ["manage_events"]
        assert inserted["custom_role_id"] == "r1"

    async def test_invite_missing_custom_role_400(self, mock_db, admin_user, monkeypatch):
        from models import InviteCreate

        _wire_custom_roles(mock_db, existing=[])
        mock_db.users.find_one = AsyncMock(return_value=None)
        monkeypatch.setattr(admin_route, "next_member_id", AsyncMock(return_value="ACCTA-9997"))

        data = InviteCreate(name="Novo", email="novo@x.cv", custom_role_id="ghost")
        with pytest.raises(HTTPException) as exc:
            await admin_route.invite_user(request=_mock_request(), data=data, current_user=admin_user)
        assert exc.value.status_code == 400


# --------------------------------------------------------------------------- #
# US2 — destaque por cargo estatutário (promote)
# --------------------------------------------------------------------------- #


class TestPromoteClearsCustomRoleId:
    async def test_promote_writes_custom_role_id_none(self, mock_db, admin_user, socio_user_dict, monkeypatch):
        from models import PromoteUserRequest

        socio_user_dict["custom_role_id"] = "r1"
        socio_user_dict["status"] = "ativo"
        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        # holders para _count_cargo_holders
        holders_cursor = MagicMock()
        holders_cursor.to_list = AsyncMock(return_value=[])
        mock_db.users.find = MagicMock(return_value=holders_cursor)

        # Silenciar helpers laterais
        monkeypatch.setattr(admin_route, "alert_admins_privilege_escalation", AsyncMock())
        monkeypatch.setattr(admin_route, "notify_users", AsyncMock())

        data = PromoteUserRequest(cargo="dir_tesoureiro", role="financeiro")
        await admin_route.promote_user(
            user_id=socio_user_dict["id"],
            request=_mock_request(),
            data=data,
            current_user=admin_user,
        )
        args, _ = mock_db.users.update_one.await_args
        update = args[1]["$set"]
        assert update["custom_role_id"] is None
