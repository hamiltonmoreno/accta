"""Unit tests para os helpers de autorização aditiva (Fase 2, RBAC granular).

Puros — testam auth.has_privilege / has_role_or_privilege / can_view_finances /
can_manage_finances com utilizadores fake (duck-typed: só .role e .privileges).
"""

from types import SimpleNamespace

import pytest

from auth import (
    can_manage_finances,
    can_view_finances,
    has_privilege,
    has_role_or_privilege,
)


def user(role, privileges=None):
    return SimpleNamespace(role=role, privileges=privileges or [])


# ---------- has_privilege ----------


class TestHasPrivilege:
    def test_true_quando_tem(self):
        assert has_privilege(user("socio", ["manage_events"]), "manage_events")

    def test_false_quando_nao_tem(self):
        assert not has_privilege(user("socio", ["manage_events"]), "manage_finances")

    def test_privileges_none_ou_ausente_nao_rebenta(self):
        assert not has_privilege(SimpleNamespace(role="socio", privileges=None), "x")
        assert not has_privilege(SimpleNamespace(role="socio"), "x")


# ---------- has_role_or_privilege ----------


class TestHasRoleOrPrivilege:
    def test_passa_por_role(self):
        assert has_role_or_privilege(user("admin"), ("admin",), "manage_events")

    def test_passa_por_privilegio(self):
        assert has_role_or_privilege(user("socio", ["manage_events"]), ("admin",), "manage_events")

    def test_nega_sem_role_nem_privilegio(self):
        assert not has_role_or_privilege(user("socio"), ("admin",), "manage_events")

    def test_aditivo_nao_remove_acesso_existente(self):
        # quem já tinha por role continua igual (zero regressão), com privileges vazio.
        for role in ("admin", "moderador"):
            assert has_role_or_privilege(user(role), ("admin", "moderador"), "moderate_content")


# ---------- finanças: view vs manage ----------


class TestFinanceAccess:
    @pytest.mark.parametrize("role", ["admin", "financeiro"])
    def test_admin_e_financeiro_veem_e_gerem(self, role):
        u = user(role)
        assert can_view_finances(u)
        assert can_manage_finances(u)

    def test_socio_sem_privilegio_nao_acede(self):
        u = user("socio")
        assert not can_view_finances(u)
        assert not can_manage_finances(u)

    def test_view_finances_readonly_ve_mas_nao_gere(self):
        # Conselho Fiscal: separação de poderes preservada.
        u = user("socio", ["view_finances_readonly"])
        assert can_view_finances(u)
        assert not can_manage_finances(u)

    def test_manage_finances_ve_e_gere(self):
        u = user("socio", ["manage_finances"])
        assert can_view_finances(u)
        assert can_manage_finances(u)
