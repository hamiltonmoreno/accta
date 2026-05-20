"""Unit tests para os endpoints de cargos/mandatos (Fase 3, spec-identidade-cargos).

Cobre /api/admin: promote, demote, cargos/transfer, cargos, cargos/candidates.
Invoca as rotas directamente com mock_db (sem TestClient) — mesmo padrão de
test_auto_registo.py. RBAC, validações, vagas (seats), atomicidade do transfer.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from fastapi import HTTPException

from routes import admin as admin_route
from routes import users as users_route
from models import PromoteUserRequest, DemoteUserRequest, TransferCargoRequest, CARGOS


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


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
def cargo_env(mock_db, monkeypatch):
    """Silencia audit/notify; mantém db mockado."""
    monkeypatch.setattr(admin_route, "create_audit_log", AsyncMock())
    monkeypatch.setattr(admin_route, "notify_users", AsyncMock())
    return mock_db


# --------------------------------------------------------------------------- #
# POST /admin/users/{id}/promote
# --------------------------------------------------------------------------- #


class TestPromote:
    async def test_socio_403(self, cargo_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.promote_user(
                user_id="u1", request=_admin_request(),
                data=PromoteUserRequest(cargo="Tesoureiro", role="financeiro"), current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_invalid_cargo_422(self, cargo_env, admin_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.promote_user(
                user_id="u1", request=_admin_request(),
                data=PromoteUserRequest(cargo="Imperador", role="admin"), current_user=admin_user,
            )
        assert exc.value.status_code == 422

    async def test_invalid_role_422(self, cargo_env, admin_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.promote_user(
                user_id="u1", request=_admin_request(),
                data=PromoteUserRequest(cargo="Tesoureiro", role="superuser"), current_user=admin_user,
            )
        assert exc.value.status_code == 422

    async def test_not_found_404(self, cargo_env, admin_user):
        cargo_env.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await admin_route.promote_user(
                user_id="u1", request=_admin_request(),
                data=PromoteUserRequest(cargo="Tesoureiro", role="financeiro"), current_user=admin_user,
            )
        assert exc.value.status_code == 404

    async def test_technical_account_400(self, cargo_env, admin_user):
        cargo_env.users.find_one = AsyncMock(
            return_value={"id": "u1", "account_type": "technical", "status": "ativo"}
        )
        with pytest.raises(HTTPException) as exc:
            await admin_route.promote_user(
                user_id="u1", request=_admin_request(),
                data=PromoteUserRequest(cargo="Tesoureiro", role="financeiro"), current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_not_ativo_400(self, cargo_env, admin_user):
        cargo_env.users.find_one = AsyncMock(return_value={"id": "u1", "status": "inativo"})
        with pytest.raises(HTTPException) as exc:
            await admin_route.promote_user(
                user_id="u1", request=_admin_request(),
                data=PromoteUserRequest(cargo="Tesoureiro", role="financeiro"), current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_seats_full_409(self, cargo_env, admin_user):
        # Presidente tem 1 vaga; já ocupada por outro sócio.
        cargo_env.users.find_one = AsyncMock(return_value={"id": "u1", "status": "ativo"})
        cargo_env.users.find = MagicMock(return_value=_cursor([{"id": "outro"}]))
        with pytest.raises(HTTPException) as exc:
            await admin_route.promote_user(
                user_id="u1", request=_admin_request(),
                data=PromoteUserRequest(cargo="Presidente", role="admin"), current_user=admin_user,
            )
        assert exc.value.status_code == 409

    async def test_happy_opens_mandate_and_defaults(self, cargo_env, admin_user):
        cargo_env.users.find_one = AsyncMock(
            return_value={
                "id": "u1", "name": "Ana", "status": "ativo",
                "cargo": "Sócio", "cargo_history": [],
            }
        )
        cargo_env.users.find = MagicMock(return_value=_cursor([]))  # sem titulares
        captured = {}

        async def capture_update(filt, update):
            captured.update(update["$set"])
            return MagicMock(modified_count=1)

        cargo_env.users.update_one = capture_update

        result = await admin_route.promote_user(
            user_id="u1", request=_admin_request(),
            data=PromoteUserRequest(cargo="Tesoureiro", role="financeiro"), current_user=admin_user,
        )
        assert captured["role"] == "financeiro"
        assert captured["cargo"] == "Tesoureiro"
        # privilégios default do Tesoureiro
        assert set(captured["privileges"]) == {"manage_finances", "view_audit_logs"}
        assert len(captured["cargo_history"]) == 1
        m = captured["cargo_history"][0]
        assert m["cargo"] == "Tesoureiro" and m["fim"] is None
        assert m["transitioned_by"] == admin_user.id
        assert result["cargo_history"] == captured["cargo_history"]
        admin_route.create_audit_log.assert_awaited()
        admin_route.notify_users.assert_awaited()

    async def test_happy_closes_previous_active_mandate(self, cargo_env, admin_user):
        cargo_env.users.find_one = AsyncMock(
            return_value={
                "id": "u1", "name": "Ana", "status": "ativo", "cargo": "Vogal da Direcção",
                "cargo_history": [{"id": "old", "cargo": "Vogal da Direcção", "role": "moderador",
                                   "inicio": "2024-01-01", "fim": None, "transitioned_by": "x"}],
            }
        )
        cargo_env.users.find = MagicMock(return_value=_cursor([]))
        captured = {}

        async def capture_update(filt, update):
            captured.update(update["$set"])
            return MagicMock(modified_count=1)

        cargo_env.users.update_one = capture_update

        await admin_route.promote_user(
            user_id="u1", request=_admin_request(),
            data=PromoteUserRequest(cargo="Presidente", role="admin", effective_date="2026-01-01"),
            current_user=admin_user,
        )
        hist = captured["cargo_history"]
        assert len(hist) == 2
        assert hist[0]["fim"] == "2026-01-01"  # mandato anterior fechado
        assert hist[1]["cargo"] == "Presidente" and hist[1]["fim"] is None


# --------------------------------------------------------------------------- #
# POST /admin/users/{id}/demote
# --------------------------------------------------------------------------- #


class TestDemote:
    async def test_socio_403(self, cargo_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.demote_user(
                user_id="u1", request=_admin_request(), data=DemoteUserRequest(), current_user=socio_user
            )
        assert exc.value.status_code == 403

    async def test_not_found_404(self, cargo_env, admin_user):
        cargo_env.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await admin_route.demote_user(
                user_id="u1", request=_admin_request(), data=DemoteUserRequest(), current_user=admin_user
            )
        assert exc.value.status_code == 404

    async def test_happy_resets_to_socio(self, cargo_env, admin_user):
        cargo_env.users.find_one = AsyncMock(
            return_value={
                "id": "u1", "name": "Ana", "status": "ativo", "cargo": "Tesoureiro",
                "cargo_history": [{"id": "m", "cargo": "Tesoureiro", "role": "financeiro",
                                   "inicio": "2024-01-01", "fim": None, "transitioned_by": "x"}],
            }
        )
        captured = {}

        async def capture_update(filt, update):
            captured.update(update["$set"])
            return MagicMock(modified_count=1)

        cargo_env.users.update_one = capture_update

        await admin_route.demote_user(
            user_id="u1", request=_admin_request(),
            data=DemoteUserRequest(effective_date="2026-02-01"), current_user=admin_user,
        )
        assert captured["role"] == "socio"
        assert captured["cargo"] == "Sócio"
        assert captured["privileges"] == []
        assert captured["cargo_history"][0]["fim"] == "2026-02-01"


# --------------------------------------------------------------------------- #
# POST /admin/cargos/transfer
# --------------------------------------------------------------------------- #


class TestTransfer:
    async def test_socio_403(self, cargo_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.transfer_cargo_endpoint(
                request=_admin_request(),
                data=TransferCargoRequest(from_user_id="a", to_user_id="b", cargo="Presidente", role="admin"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_same_user_400(self, cargo_env, admin_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.transfer_cargo_endpoint(
                request=_admin_request(),
                data=TransferCargoRequest(from_user_id="a", to_user_id="a", cargo="Presidente", role="admin"),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_from_not_holder_400(self, cargo_env, admin_user):
        async def find_one(filt, proj=None):
            uid = filt.get("id")
            if uid == "a":
                return {"id": "a", "cargo": "Sócio", "status": "ativo"}  # não é titular
            return {"id": "b", "cargo": "Sócio", "status": "ativo"}

        cargo_env.users.find_one = find_one
        with pytest.raises(HTTPException) as exc:
            await admin_route.transfer_cargo_endpoint(
                request=_admin_request(),
                data=TransferCargoRequest(from_user_id="a", to_user_id="b", cargo="Presidente", role="admin"),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_to_not_ativo_400(self, cargo_env, admin_user):
        async def find_one(filt, proj=None):
            uid = filt.get("id")
            if uid == "a":
                return {"id": "a", "cargo": "Presidente", "status": "ativo"}
            return {"id": "b", "cargo": "Sócio", "status": "inativo"}

        cargo_env.users.find_one = find_one
        with pytest.raises(HTTPException) as exc:
            await admin_route.transfer_cargo_endpoint(
                request=_admin_request(),
                data=TransferCargoRequest(from_user_id="a", to_user_id="b", cargo="Presidente", role="admin"),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_happy_atomic_transfer(self, cargo_env, admin_user, monkeypatch):
        async def find_one(filt, proj=None):
            uid = filt.get("id")
            if uid == "a":
                return {"id": "a", "name": "Velho", "cargo": "Presidente", "status": "ativo",
                        "cargo_history": [{"id": "m", "cargo": "Presidente", "role": "admin",
                                           "inicio": "2024-01-01", "fim": None, "transitioned_by": "x"}]}
            return {"id": "b", "name": "Novo", "cargo": "Sócio", "status": "ativo", "cargo_history": []}

        cargo_env.users.find_one = find_one
        transfer_mock = AsyncMock()
        monkeypatch.setattr(admin_route, "transfer_cargo", transfer_mock)

        result = await admin_route.transfer_cargo_endpoint(
            request=_admin_request(),
            data=TransferCargoRequest(
                from_user_id="a", to_user_id="b", cargo="Presidente", role="admin", elected_by="AGA 2026"
            ),
            current_user=admin_user,
        )
        assert "transition_id" in result
        transfer_mock.assert_awaited_once()
        args = transfer_mock.await_args.args
        assert args[0] == "a" and args[1] == "b"
        from_set = args[2]["$set"]
        to_set = args[3]["$set"]
        # from volta a Sócio; mandato fechado
        assert from_set["cargo"] == "Sócio" and from_set["role"] == "socio"
        assert from_set["cargo_history"][0]["fim"] is not None
        # to recebe Presidente com defaults (todos os privilégios) + transition_id
        assert to_set["cargo"] == "Presidente" and to_set["role"] == "admin"
        new_mandate = to_set["cargo_history"][-1]
        assert new_mandate["cargo"] == "Presidente" and new_mandate["fim"] is None
        assert new_mandate["transition_id"] == result["transition_id"]
        assert new_mandate["elected_by"] == "AGA 2026"


# --------------------------------------------------------------------------- #
# GET /admin/cargos  e  /admin/cargos/candidates
# --------------------------------------------------------------------------- #


class TestListCargos:
    async def test_socio_403(self, cargo_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.list_cargos(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_buckets_holders(self, cargo_env, admin_user):
        cargo_env.users.find = MagicMock(
            return_value=_cursor([
                {"id": "p", "name": "Pres", "email": "p@x.cv", "member_id": "ACCTA-0001",
                 "cargo": "Presidente",
                 "cargo_history": [{"cargo": "Presidente", "fim": None, "inicio": "2025-01-01"}]},
                {"id": "s", "name": "Soc", "email": "s@x.cv", "member_id": "ACCTA-0002", "cargo": "Sócio"},
            ])
        )
        result = await admin_route.list_cargos(current_user=admin_user)
        by = {c["cargo"]: c for c in result["cargos"]}
        assert "Sócio" not in by  # Sócio não é cargo institucional
        assert by["Presidente"]["seats"] == 1
        assert len(by["Presidente"]["holders"]) == 1
        assert by["Presidente"]["holders"][0]["since"] == "2025-01-01"
        assert by["Tesoureiro"]["holders"] == []  # vago


class TestCandidates:
    async def test_socio_403(self, cargo_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await admin_route.list_cargo_candidates(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_filters_q_and_excludes_technical(self, cargo_env, admin_user):
        captured = {}

        def find(query, proj):
            captured["query"] = query
            return _cursor([
                {"id": "1", "name": "Ana Silva", "email": "ana@x.cv", "member_id": "ACCTA-0001", "cargo": "Sócio"},
                {"id": "2", "name": "Bruno Costa", "email": "b@x.cv", "member_id": "ACCTA-0002", "cargo": "Tesoureiro"},
            ])

        cargo_env.users.find = find
        result = await admin_route.list_cargo_candidates(current_user=admin_user, q="ana")
        # filtro account_type member aplicado na query
        assert "$or" in captured["query"]
        assert captured["query"]["status"] == "ativo"
        assert [c["id"] for c in result["candidates"]] == ["1"]

    async def test_exclude_cargo(self, cargo_env, admin_user):
        cargo_env.users.find = MagicMock(
            return_value=_cursor([
                {"id": "1", "name": "Ana", "email": "a@x.cv", "member_id": "ACCTA-0001", "cargo": "Tesoureiro"},
                {"id": "2", "name": "Bruno", "email": "b@x.cv", "member_id": "ACCTA-0002", "cargo": "Sócio"},
            ])
        )
        result = await admin_route.list_cargo_candidates(current_user=admin_user, exclude_cargo="Tesoureiro")
        assert [c["id"] for c in result["candidates"]] == ["2"]


# --------------------------------------------------------------------------- #
# users.py: GET /users (filtro account_type), /users/meta/cargos, cargo-history
# --------------------------------------------------------------------------- #


class TestUsersMetadata:
    async def test_meta_cargos_completa(self):
        result = await users_route.get_cargos()
        assert result["cargos"] == CARGOS
        for key in ("cargos_orgaos_sociais", "privileges", "cargo_defaults", "cargo_seats"):
            assert key in result
        assert "view_finances_readonly" in result["privileges"]


class TestListUsersAccountType:
    async def test_default_oculta_tecnicas(self, mock_db, admin_user):
        captured = {}

        def find(query, proj):
            captured["query"] = query
            return _cursor([])

        mock_db.users.find = find
        await users_route.get_users(current_user=admin_user)
        # account_type member-or-missing por defeito (via $and -> $or)
        clause = captured["query"]["$and"][0]
        assert {"account_type": "member"} in clause["$or"]
        assert {"account_type": {"$exists": False}} in clause["$or"]

    async def test_include_technical_remove_filtro(self, mock_db, admin_user):
        captured = {}

        def find(query, proj):
            captured["query"] = query
            return _cursor([])

        mock_db.users.find = find
        await users_route.get_users(current_user=admin_user, include_technical=True)
        assert "$and" not in captured["query"]


class TestCargoHistory:
    async def test_self_pode_ver(self, mock_db, socio_user):
        mock_db.users.find_one = AsyncMock(
            return_value={"name": "Eu", "cargo_history": [{"cargo": "Sócio", "inicio": "2024-01-01"}]}
        )
        result = await users_route.get_cargo_history(user_id=socio_user.id, current_user=socio_user)
        assert len(result["cargo_history"]) == 1

    async def test_outro_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await users_route.get_cargo_history(user_id="outro-id", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_admin_ve_qualquer_e_ordena_desc(self, mock_db, admin_user):
        mock_db.users.find_one = AsyncMock(
            return_value={
                "name": "Ana",
                "cargo_history": [
                    {"cargo": "Vogal da Direcção", "inicio": "2022-01-01"},
                    {"cargo": "Presidente", "inicio": "2024-01-01"},
                ],
            }
        )
        result = await users_route.get_cargo_history(user_id="u1", current_user=admin_user)
        # mais recente primeiro
        assert result["cargo_history"][0]["cargo"] == "Presidente"

    async def test_not_found_404(self, mock_db, admin_user):
        mock_db.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await users_route.get_cargo_history(user_id="u1", current_user=admin_user)
        assert exc.value.status_code == 404
