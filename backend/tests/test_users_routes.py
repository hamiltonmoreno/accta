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


def _search_regex(query: dict) -> str:
    search_clause = next(clause for clause in query["$and"] if "name" in clause.get("$or", [{}])[0])
    return search_clause["$or"][0]["name"]["$regex"]


class TestListUsers:
    async def test_admin_can_list(self, mock_db, admin_user):
        mock_db.users.find().skip().limit().to_list = AsyncMock(return_value=[])
        result = await users_route.get_users(current_user=admin_user)
        assert result == []

    async def test_financeiro_role_403(self, mock_db, financeiro_user):
        # spec 018: o role legado deixou de conceder listagem — o acesso do
        # ex-financeiro vem da seed «Financeiro» (manage_users), ver matriz.
        with pytest.raises(HTTPException) as exc:
            await users_route.get_users(current_user=financeiro_user)
        assert exc.value.status_code == 403

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
        regex = _search_regex(captured_query)
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
        regex = _search_regex(captured_query)
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

    async def test_financeiro_role_cannot_view_other(self, mock_db, financeiro_user):
        # spec 018: PII de terceiros passa a exigir manage_users (a seed
        # «Financeiro» inclui-o; o role legado sozinho já não).
        with pytest.raises(HTTPException) as exc:
            await users_route.get_user(user_id="other-id", current_user=financeiro_user)
        assert exc.value.status_code == 403

    async def test_manage_users_privilege_can_view_other(self, mock_db, socio_user_dict):
        from models import User

        staff = User(**{**socio_user_dict, "privileges": ["manage_users"]})
        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        result = await users_route.get_user(user_id="other-id", current_user=staff)
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
# PII sensível do perfil — minimização de dados (feature/perfil)
# --------------------------------------------------------------------------- #


class TestProfilePIIProjection:
    """Tipo sanguíneo, NIF, morada e contacto de emergência não saem em
    listagens nem para terceiros (staff) — só o próprio os recebe."""

    async def test_list_excludes_sensitive_fields(self, mock_db, admin_user):
        captured = {}

        def capture_find(query, proj):
            captured["proj"] = proj
            cursor = MagicMock()
            cursor.skip = MagicMock(return_value=cursor)
            cursor.limit = MagicMock(return_value=cursor)
            cursor.to_list = AsyncMock(return_value=[])
            return cursor

        mock_db.users.find = capture_find
        await users_route.get_users(current_user=admin_user)
        assert captured["proj"]["password"] == 0
        for f in users_route.SENSITIVE_PROFILE_FIELDS:
            assert captured["proj"].get(f) == 0

    async def test_self_detail_includes_sensitive_fields(self, mock_db, socio_user, socio_user_dict):
        captured = {}

        async def capture_find_one(q, proj):
            captured["proj"] = proj
            return socio_user_dict

        mock_db.users.find_one = capture_find_one
        await users_route.get_user(user_id=socio_user.id, current_user=socio_user)
        # O próprio vê tudo — sem exclusões de PII.
        for f in users_route.SENSITIVE_PROFILE_FIELDS:
            assert f not in captured["proj"]

    async def test_staff_detail_excludes_sensitive_fields(self, mock_db, admin_user, socio_user_dict):
        captured = {}

        async def capture_find_one(q, proj):
            captured["proj"] = proj
            return socio_user_dict

        mock_db.users.find_one = capture_find_one
        await users_route.get_user(user_id="outro-id", current_user=admin_user)
        # Staff a ver terceiro recebe a vista reduzida (PII oculta).
        for f in users_route.SENSITIVE_PROFILE_FIELDS:
            assert captured["proj"].get(f) == 0


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

    async def test_persists_extended_profile_fields(self, mock_db, socio_user, socio_user_dict):
        """feature/perfil — campos pessoais estendidos chegam ao $set."""
        from models import UserProfileUpdate

        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        update = UserProfileUpdate(
            date_of_birth="1990-05-22",
            blood_type="o+",  # normalizado para O+
            address="Rua Direita, 12",
            city="Praia",
            residence_island="Santiago",
            emergency_contact_name="Maria",
            emergency_contact_phone="+238 991 0000",
            emergency_contact_relationship="Cônjuge",
            profession="Contabilista",
            license_number="ACCTA-CC-001",
            license_expiry_date="2027-01-31",
        )
        await users_route.update_own_profile(data=update, current_user=socio_user)
        set_data = mock_db.users.update_one.call_args[0][1]["$set"]
        assert set_data["date_of_birth"] == "1990-05-22"
        assert set_data["blood_type"] == "O+"  # validator normaliza
        assert set_data["address"] == "Rua Direita, 12"
        assert set_data["emergency_contact_name"] == "Maria"
        assert set_data["license_expiry_date"] == "2027-01-31"
        # Campos não enviados não entram no $set (route filtra None).
        assert "gender" not in set_data


# --------------------------------------------------------------------------- #
# Validação dos modelos de escrita de perfil (_EditableProfileFields)
# --------------------------------------------------------------------------- #


class TestProfileFieldValidation:
    """field_validators vivem nos modelos de escrita; entradas inválidas dão
    ValidationError (→ 422 via FastAPI) antes de chegar ao route."""

    def test_invalid_blood_type_rejected(self):
        from pydantic import ValidationError
        from models import UserProfileUpdate

        with pytest.raises(ValidationError):
            UserProfileUpdate(blood_type="Z+")

    def test_blood_type_normalized_uppercase(self):
        from models import UserProfileUpdate

        assert UserProfileUpdate(blood_type="ab-").blood_type == "AB-"

    def test_invalid_date_format_rejected(self):
        from pydantic import ValidationError
        from models import UserProfileUpdate

        with pytest.raises(ValidationError):
            UserProfileUpdate(date_of_birth="22/05/1990")

    def test_future_date_of_birth_rejected(self):
        from pydantic import ValidationError
        from models import UserProfileUpdate

        with pytest.raises(ValidationError):
            UserProfileUpdate(date_of_birth="3000-01-01")

    def test_future_license_expiry_allowed(self):
        from models import UserProfileUpdate

        assert UserProfileUpdate(license_expiry_date="3000-01-01").license_expiry_date == "3000-01-01"

    def test_blank_name_rejected(self):
        from pydantic import ValidationError
        from models import UserProfileUpdate

        with pytest.raises(ValidationError):
            UserProfileUpdate(name="   ")

    def test_empty_string_clears_field(self):
        """ "" é permitido (= limpar); o route grava-o (só filtra None)."""
        from models import UserProfileUpdate

        m = UserProfileUpdate(blood_type="", date_of_birth="")
        assert m.blood_type == "" and m.date_of_birth == ""

    def test_photo_url_rejects_external(self):
        """photo_url só aceita /uploads/avatars/… — bloqueia URL externa (beacon)."""
        from pydantic import ValidationError
        from models import UserProfileUpdate

        with pytest.raises(ValidationError):
            UserProfileUpdate(photo_url="https://tracker.externo.com/pixel.png")
        with pytest.raises(ValidationError):
            UserProfileUpdate(photo_url="/uploads/documents/x.pdf")

    def test_photo_url_accepts_own_upload_blank_none(self):
        from models import UserProfileUpdate

        assert UserProfileUpdate(photo_url="/uploads/avatars/x.jpg").photo_url == "/uploads/avatars/x.jpg"
        assert UserProfileUpdate(photo_url="").photo_url == ""
        assert UserProfileUpdate(photo_url=None).photo_url is None

    def test_admin_update_inherits_personal_fields(self):
        """UserAdminUpdate herda os campos pessoais + valida-os."""
        from pydantic import ValidationError
        from models import UserAdminUpdate

        ok = UserAdminUpdate(blood_type="a+", role="admin")
        assert ok.blood_type == "A+" and ok.role == "admin"
        with pytest.raises(ValidationError):
            UserAdminUpdate(date_of_birth="not-a-date")


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

    async def test_invalid_status_400(self, mock_db, admin_user, socio_user_dict):
        """Spec-2: status fora de USER_STATUSES e rejeitado. Invariante de
        negocio: NAO existe 'inadimplente' (quotas descontadas em folha)."""
        from models import UserAdminUpdate

        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        with pytest.raises(HTTPException) as exc:
            await users_route.admin_update_user(
                user_id="any",
                data=UserAdminUpdate(status="inadimplente"),
                request=_mock_request(),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400
        mock_db.users.update_one.assert_not_awaited()

    async def test_valid_status_passes(self, mock_db, admin_user, socio_user_dict):
        from models import UserAdminUpdate

        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        await users_route.admin_update_user(
            user_id="any",
            data=UserAdminUpdate(status="inativo"),
            request=_mock_request(),
            current_user=admin_user,
        )
        set_data = mock_db.users.update_one.call_args[0][1]["$set"]
        assert set_data["status"] == "inativo"


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
        result = await users_route.delete_user(user_id=socio_user_dict["id"], current_user=admin_user)
        assert "removido" in result["message"].lower()
        mock_db.users.delete_one.assert_awaited_once_with({"id": socio_user_dict["id"]})


# --------------------------------------------------------------------------- #
# PATCH /users/{id}/status (legacy endpoint)
# --------------------------------------------------------------------------- #


class TestUpdateUserStatus:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await users_route.update_user_status(user_id="any", status="inativo", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_admin_updates_status(self, mock_db, admin_user):
        # Existência verificada antes de atualizar (404 se inexistente) — wire o find_one.
        mock_db.users.find_one = AsyncMock(return_value={"id": "some-id"})
        result = await users_route.update_user_status(user_id="some-id", status="inativo", current_user=admin_user)
        assert "atualizado" in result["message"].lower()
        mock_db.users.update_one.assert_awaited_with({"id": "some-id"}, {"$set": {"status": "inativo"}})

    async def test_admin_status_user_not_found_404(self, mock_db, admin_user):
        mock_db.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await users_route.update_user_status(user_id="ghost", status="inativo", current_user=admin_user)
        assert exc.value.status_code == 404
        mock_db.users.update_one.assert_not_awaited()

    @pytest.mark.parametrize("status", ["ativo", "inativo", "pendente_convite"])
    async def test_admin_accepts_every_valid_status(self, mock_db, admin_user, status):
        from models import USER_STATUSES

        assert status in USER_STATUSES
        mock_db.users.find_one = AsyncMock(return_value={"id": "some-id"})
        await users_route.update_user_status(user_id="some-id", status=status, current_user=admin_user)
        mock_db.users.update_one.assert_awaited_with({"id": "some-id"}, {"$set": {"status": status}})

    @pytest.mark.parametrize("bad_status", ["inadimplente", "banido", "", "ATIVO"])
    async def test_admin_rejects_invalid_status(self, mock_db, admin_user, bad_status):
        """Spec-2: update_user_status valida o status. 'inadimplente' nunca
        e aceite — quotas sao descontadas em folha (invariante do projeto)."""
        with pytest.raises(HTTPException) as exc:
            await users_route.update_user_status(user_id="some-id", status=bad_status, current_user=admin_user)
        assert exc.value.status_code == 400
        mock_db.users.update_one.assert_not_awaited()


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


# --------------------------------------------------------------------------- #
# Foto de perfil — auto-serviço (PATCH /users/me/profile) — spec-foto-de-perfil
# --------------------------------------------------------------------------- #


class TestOwnProfilePhoto:
    async def test_set_new_photo_persists_and_deletes_old(self, mock_db, monkeypatch, socio_user):
        from models import UserProfileUpdate

        deleted = MagicMock()
        monkeypatch.setattr(users_route, "delete_upload_file", deleted)
        mock_db.users.find_one = AsyncMock(
            return_value={"id": socio_user.id, "photo_url": "/uploads/avatars/old.jpg"}
        )
        await users_route.update_own_profile(
            data=UserProfileUpdate(photo_url="/uploads/avatars/new.jpg"), current_user=socio_user
        )
        set_data = mock_db.users.update_one.call_args[0][1]["$set"]
        assert set_data["photo_url"] == "/uploads/avatars/new.jpg"
        deleted.assert_called_once_with("/uploads/avatars/old.jpg")

    async def test_clear_photo_sets_none_and_deletes_old(self, mock_db, monkeypatch, socio_user):
        """photo_url == "" limpa (grava None), apaga o ficheiro e audita removed."""
        from models import UserProfileUpdate

        deleted = MagicMock()
        audited = AsyncMock()
        monkeypatch.setattr(users_route, "delete_upload_file", deleted)
        monkeypatch.setattr(users_route, "create_audit_log", audited)
        mock_db.users.find_one = AsyncMock(
            return_value={"id": socio_user.id, "photo_url": "/uploads/avatars/old.jpg"}
        )
        await users_route.update_own_profile(data=UserProfileUpdate(photo_url=""), current_user=socio_user)
        set_data = mock_db.users.update_one.call_args[0][1]["$set"]
        assert set_data["photo_url"] is None
        deleted.assert_called_once_with("/uploads/avatars/old.jpg")
        assert audited.await_args[0][1] == "profile_photo_removed"

    async def test_set_photo_only_audits_specific(self, mock_db, monkeypatch, socio_user):
        from models import UserProfileUpdate

        monkeypatch.setattr(users_route, "delete_upload_file", MagicMock())
        audited = AsyncMock()
        monkeypatch.setattr(users_route, "create_audit_log", audited)
        mock_db.users.find_one = AsyncMock(return_value={"id": socio_user.id, "photo_url": None})
        await users_route.update_own_profile(
            data=UserProfileUpdate(photo_url="/uploads/avatars/new.jpg"), current_user=socio_user
        )
        assert audited.await_args[0][1] == "profile_photo_updated"

    async def test_photo_omitted_keeps_value_and_no_delete(self, mock_db, monkeypatch, socio_user, socio_user_dict):
        from models import UserProfileUpdate

        deleted = MagicMock()
        monkeypatch.setattr(users_route, "delete_upload_file", deleted)
        mock_db.users.find_one = AsyncMock(return_value=socio_user_dict)
        await users_route.update_own_profile(data=UserProfileUpdate(name="Novo"), current_user=socio_user)
        set_data = mock_db.users.update_one.call_args[0][1]["$set"]
        assert "photo_url" not in set_data
        deleted.assert_not_called()

    async def test_mixed_edit_with_photo_audits_generic(self, mock_db, monkeypatch, socio_user):
        """Edição mista (foto + outros campos) usa o audit genérico do perfil."""
        from models import UserProfileUpdate

        monkeypatch.setattr(users_route, "delete_upload_file", MagicMock())
        audited = AsyncMock()
        monkeypatch.setattr(users_route, "create_audit_log", audited)
        mock_db.users.find_one = AsyncMock(return_value={"id": socio_user.id, "photo_url": None})
        await users_route.update_own_profile(
            data=UserProfileUpdate(name="Novo", photo_url="/uploads/avatars/new.jpg"),
            current_user=socio_user,
        )
        assert audited.await_args[0][1] == "Atualizou o próprio perfil"
        set_data = mock_db.users.update_one.call_args[0][1]["$set"]
        assert set_data["photo_url"] == "/uploads/avatars/new.jpg" and set_data["name"] == "Novo"


# --------------------------------------------------------------------------- #
# DELETE /users/{id}/photo — moderação reativa (admin + moderador)
# --------------------------------------------------------------------------- #


class TestRemoveUserPhoto:
    async def test_admin_removes(self, mock_db, monkeypatch, admin_user):
        deleted = MagicMock()
        audited = AsyncMock()
        notified = AsyncMock()
        monkeypatch.setattr(users_route, "delete_upload_file", deleted)
        monkeypatch.setattr(users_route, "create_audit_log", audited)
        monkeypatch.setattr(users_route, "create_notification", notified)
        mock_db.users.find_one = AsyncMock(
            return_value={"id": "u1", "photo_url": "/uploads/avatars/x.jpg", "name": "Zé"}
        )
        result = await users_route.remove_user_photo(user_id="u1", request=_mock_request(), current_user=admin_user)
        set_data = mock_db.users.update_one.call_args[0][1]["$set"]
        assert set_data["photo_url"] is None
        deleted.assert_called_once_with("/uploads/avatars/x.jpg")
        assert audited.await_args[0][1] == "profile_photo_removed"
        notified.assert_awaited_once()
        assert "removida" in result["message"].lower()

    async def test_moderador_removes(self, mock_db, monkeypatch, moderador_user):
        monkeypatch.setattr(users_route, "delete_upload_file", MagicMock())
        monkeypatch.setattr(users_route, "create_audit_log", AsyncMock())
        monkeypatch.setattr(users_route, "create_notification", AsyncMock())
        mock_db.users.find_one = AsyncMock(return_value={"id": "u1", "photo_url": None, "name": "Zé"})
        result = await users_route.remove_user_photo(user_id="u1", request=_mock_request(), current_user=moderador_user)
        assert "removida" in result["message"].lower()

    async def test_financeiro_403(self, mock_db, financeiro_user):
        with pytest.raises(HTTPException) as exc:
            await users_route.remove_user_photo(user_id="u1", request=_mock_request(), current_user=financeiro_user)
        assert exc.value.status_code == 403

    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await users_route.remove_user_photo(user_id="u1", request=_mock_request(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_404_when_not_found(self, mock_db, admin_user):
        mock_db.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await users_route.remove_user_photo(user_id="missing", request=_mock_request(), current_user=admin_user)
        assert exc.value.status_code == 404


# --------------------------------------------------------------------------- #
# enrich_author_photos (helpers) — resolução da foto do autor na leitura
# --------------------------------------------------------------------------- #


class TestEnrichAuthorPhotos:
    async def test_injects_current_photo(self, mock_db):
        from helpers import enrich_author_photos

        mock_db.users.find.return_value.to_list = AsyncMock(
            return_value=[{"id": "u1", "photo_url": "/uploads/avatars/a.jpg"}, {"id": "u2", "photo_url": None}]
        )
        docs = [{"user_id": "u1"}, {"user_id": "u2"}]
        await enrich_author_photos(docs)
        assert docs[0]["user_photo_url"] == "/uploads/avatars/a.jpg"
        assert docs[1]["user_photo_url"] is None

    async def test_missing_author_is_none(self, mock_db):
        from helpers import enrich_author_photos

        mock_db.users.find.return_value.to_list = AsyncMock(return_value=[])
        docs = [{"user_id": "ghost"}]
        await enrich_author_photos(docs)
        assert docs[0]["user_photo_url"] is None

    async def test_empty_docs_noop(self, mock_db):
        from helpers import enrich_author_photos

        assert await enrich_author_photos([]) == []

    async def test_docs_without_id_get_none(self, mock_db):
        from helpers import enrich_author_photos

        docs = [{"text": "sem autor"}]
        await enrich_author_photos(docs)
        assert docs[0]["user_photo_url"] is None
