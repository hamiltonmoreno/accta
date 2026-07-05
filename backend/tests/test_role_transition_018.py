"""Transição do modelo de acessos — spec 018 (D1/D4/R6/R8).

Cobre a release de transição: roles legados (financeiro/moderador) aceites nas
superfícies de escrita e TRADUZIDOS para socio + função personalizada seed
(criada on-demand — finding M1), com audit `legacy_role_translated`; e o
alerta de escalada redefinido (role admin novo OU privilégios sensíveis).
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

import helpers
import routes.admin as admin_route
import routes.users as users_route
from governance import LEGACY_ROLE_SEEDS
from helpers import resolve_legacy_role
from models import InviteCreate, UserAdminUpdate

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _mock_request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


def _existing_socio(**overrides) -> dict:
    base = {
        "id": str(uuid.uuid4()),
        "name": "Alvo",
        "email": "alvo@x.cv",
        "role": "socio",
        "status": "ativo",
        "privileges": [],
        "custom_role_id": None,
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# resolve_legacy_role (helpers) — seed on-demand (M1)
# --------------------------------------------------------------------------- #


class TestResolveLegacyRole:
    async def test_creates_seed_on_demand(self, mock_db):
        mock_db.custom_roles.find_one = AsyncMock(return_value=None)
        doc = await resolve_legacy_role("financeiro")
        assert doc["name"] == "Financeiro"
        assert doc["privileges"] == LEGACY_ROLE_SEEDS["financeiro"]["privileges"]
        assert doc["created_by"] == "system"
        mock_db.custom_roles.insert_one.assert_awaited_once()

    async def test_reuses_existing_seed(self, mock_db):
        seed = {"id": "seed-mod", "name": "Moderador", "privileges": ["moderate_content"]}
        mock_db.custom_roles.find_one = AsyncMock(return_value=seed)
        doc = await resolve_legacy_role("moderador")
        assert doc is seed
        mock_db.custom_roles.insert_one.assert_not_awaited()

    @pytest.mark.parametrize("role", ["admin", "socio", "xpto", "", None])
    async def test_none_for_non_legacy(self, mock_db, role):
        assert await resolve_legacy_role(role) is None
        mock_db.custom_roles.find_one.assert_not_awaited()


# --------------------------------------------------------------------------- #
# POST /admin/invite — tradução D4
# --------------------------------------------------------------------------- #


class TestInviteLegacyRole:
    async def _invite(self, mock_db, admin_user, monkeypatch, role):
        mock_db.users.find_one = AsyncMock(return_value=None)
        mock_db.custom_roles.find_one = AsyncMock(return_value=None)
        monkeypatch.setattr(admin_route, "next_member_id", AsyncMock(return_value="ACCTA-9990"))
        monkeypatch.setattr(admin_route, "send_invite_email", AsyncMock(return_value={"status": "sent"}))
        audit = AsyncMock()
        monkeypatch.setattr(admin_route, "create_audit_log", audit)
        data = InviteCreate(name="Novo", email="novo@x.cv", role=role)
        await admin_route.invite_user(request=_mock_request(), data=data, current_user=admin_user)
        (inserted,), _ = mock_db.users.insert_one.await_args
        return inserted, audit

    async def test_financeiro_translates_to_socio_plus_seed(self, mock_db, admin_user, monkeypatch):
        inserted, audit = await self._invite(mock_db, admin_user, monkeypatch, "financeiro")
        assert inserted["role"] == "socio"
        assert inserted["privileges"] == LEGACY_ROLE_SEEDS["financeiro"]["privileges"]
        assert inserted["custom_role_id"]
        details = audit.await_args.kwargs["details"]
        assert details["legacy_role_translated"] == "financeiro"
        assert details["custom_role"] == "Financeiro"

    async def test_moderador_translates(self, mock_db, admin_user, monkeypatch):
        inserted, _ = await self._invite(mock_db, admin_user, monkeypatch, "moderador")
        assert inserted["role"] == "socio"
        assert inserted["privileges"] == ["moderate_content"]

    async def test_new_levels_untouched(self, mock_db, admin_user, monkeypatch):
        inserted, audit = await self._invite(mock_db, admin_user, monkeypatch, "socio")
        assert inserted["role"] == "socio"
        assert inserted["privileges"] == []
        assert inserted["custom_role_id"] is None
        assert "legacy_role_translated" not in audit.await_args.kwargs["details"]

    async def test_unknown_role_422(self, mock_db, admin_user):
        mock_db.users.find_one = AsyncMock(return_value=None)
        data = InviteCreate(name="Novo", email="novo@x.cv", role="gestor")
        with pytest.raises(HTTPException) as exc:
            await admin_route.invite_user(request=_mock_request(), data=data, current_user=admin_user)
        assert exc.value.status_code == 422


# --------------------------------------------------------------------------- #
# PATCH /users/{id} — tradução D4
# --------------------------------------------------------------------------- #


class TestPatchLegacyRole:
    async def _patch(self, mock_db, admin_user, monkeypatch, existing, **fields):
        mock_db.users.find_one = AsyncMock(side_effect=[existing, {**existing, **fields}])
        mock_db.custom_roles.find_one = AsyncMock(return_value=None)
        captured = {}

        async def capture_update(filt, update):
            captured.update(update["$set"])
            return MagicMock(modified_count=1)

        mock_db.users.update_one = capture_update
        audit = AsyncMock()
        monkeypatch.setattr(users_route, "create_audit_log", audit)
        monkeypatch.setattr(users_route, "alert_admins_privilege_escalation", AsyncMock())
        await users_route.admin_update_user(
            existing["id"], UserAdminUpdate(**fields), _mock_request(), current_user=admin_user
        )
        return captured, audit

    async def test_role_financeiro_translates(self, mock_db, admin_user, monkeypatch):
        captured, audit = await self._patch(mock_db, admin_user, monkeypatch, _existing_socio(), role="financeiro")
        assert captured["role"] == "socio"
        assert captured["privileges"] == LEGACY_ROLE_SEEDS["financeiro"]["privileges"]
        assert captured["custom_role_id"]
        assert audit.await_args.kwargs["details"]["legacy_role_translated"] == "financeiro"

    async def test_role_moderador_translates_and_overrides_destaque(self, mock_db, admin_user, monkeypatch):
        existing = _existing_socio(custom_role_id="outra-funcao")
        captured, _ = await self._patch(mock_db, admin_user, monkeypatch, existing, role="moderador")
        assert captured["role"] == "socio"
        assert captured["privileges"] == ["moderate_content"]
        # a tradução liga à seed (não fica destacado)
        assert captured["custom_role_id"] not in (None, "outra-funcao")

    async def test_role_admin_untouched(self, mock_db, admin_user, monkeypatch):
        captured, audit = await self._patch(mock_db, admin_user, monkeypatch, _existing_socio(), role="admin")
        assert captured["role"] == "admin"
        assert "custom_role_id" not in captured
        assert "legacy_role_translated" not in audit.await_args.kwargs["details"]

    async def test_unknown_role_400(self, mock_db, admin_user):
        mock_db.users.find_one = AsyncMock(return_value=_existing_socio())
        with pytest.raises(HTTPException) as exc:
            await users_route.admin_update_user(
                "u1", UserAdminUpdate(role="gestor"), _mock_request(), current_user=admin_user
            )
        assert exc.value.status_code == 400

    async def test_manage_users_priv_cannot_write_role(self, mock_db, socio_user_dict, monkeypatch):
        # spec 018 W1: quem tem manage_users (ex.: seed «Financeiro», Secretário)
        # mas NÃO é admin não pode escrever role/privileges/custom_role_id —
        # senão promovia-se a admin contornando D3.
        from models import User

        actor = User(**{**socio_user_dict, "privileges": ["manage_users"]})
        mock_db.users.find_one = AsyncMock(return_value=_existing_socio())
        with pytest.raises(HTTPException) as exc:
            await users_route.admin_update_user(
                "u1", UserAdminUpdate(role="admin"), _mock_request(), current_user=actor
            )
        assert exc.value.status_code == 403

    async def test_manage_users_priv_can_edit_profile_fields(self, mock_db, socio_user_dict, monkeypatch):
        # …mas continua a poder editar dados/estado do perfil (não é escalada)
        from models import User

        actor = User(**{**socio_user_dict, "privileges": ["manage_users"]})
        existing = _existing_socio()
        mock_db.users.find_one = AsyncMock(side_effect=[existing, {**existing, "status": "inativo"}])
        captured = {}

        async def capture_update(filt, update):
            captured.update(update["$set"])
            return None

        mock_db.users.update_one = capture_update
        monkeypatch.setattr(users_route, "create_audit_log", AsyncMock())
        await users_route.admin_update_user(
            existing["id"], UserAdminUpdate(status="inativo"), _mock_request(), current_user=actor
        )
        assert captured["status"] == "inativo"

    async def test_patch_role_fires_escalation_alert(self, mock_db, admin_user, monkeypatch):
        existing = _existing_socio()
        mock_db.users.find_one = AsyncMock(side_effect=[existing, {**existing, "role": "admin"}])
        monkeypatch.setattr(users_route, "create_audit_log", AsyncMock())
        alert = AsyncMock()
        monkeypatch.setattr(users_route, "alert_admins_privilege_escalation", alert)
        await users_route.admin_update_user(
            existing["id"], UserAdminUpdate(role="admin"), _mock_request(), current_user=admin_user
        )
        alert.assert_awaited_once()
        args = alert.await_args.args
        assert args[3] == "admin"  # new_role


# --------------------------------------------------------------------------- #
# Alerta de escalada (R8): admin novo OU privilégios sensíveis
# --------------------------------------------------------------------------- #


class TestEscalationAlertR8:
    async def test_sensitive_privilege_gain_alerts(self, mock_db, monkeypatch):
        notify = AsyncMock()
        monkeypatch.setattr(helpers, "notify_admins", notify)
        await helpers.alert_admins_privilege_escalation("a", "Bob", "socio", "socio", [], ["manage_finances"])
        notify.assert_awaited_once()

    async def test_non_sensitive_gain_does_not_alert(self, mock_db, monkeypatch):
        # R8: ganhar só manage_events deixa de alertar (não é sensível)
        notify = AsyncMock()
        monkeypatch.setattr(helpers, "notify_admins", notify)
        await helpers.alert_admins_privilege_escalation("a", "Bob", "socio", "socio", [], ["manage_events"])
        notify.assert_not_awaited()

    async def test_role_admin_alerts(self, mock_db, monkeypatch):
        notify = AsyncMock()
        monkeypatch.setattr(helpers, "notify_admins", notify)
        await helpers.alert_admins_privilege_escalation("a", "Bob", "socio", "admin", [], [])
        notify.assert_awaited_once()

    async def test_seed_assignment_alerts_via_sensitive(self, mock_db, monkeypatch):
        # atribuir a função seed «Financeiro» (via PATCH) materializa
        # manage_finances/manage_users → alerta (equivalente ao antigo
        # alerta de role→financeiro)
        notify = AsyncMock()
        monkeypatch.setattr(helpers, "notify_admins", notify)
        await helpers.alert_admins_privilege_escalation(
            "a", "Bob", "socio", "socio", [], list(LEGACY_ROLE_SEEDS["financeiro"]["privileges"])
        )
        notify.assert_awaited_once()
