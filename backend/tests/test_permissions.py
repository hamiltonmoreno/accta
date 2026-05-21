"""Unit tests para backend/permissions.py — RBAC e elegibilidade de governança.

Aceita User Pydantic ou dict; órgão derivado do cargo (nunca do campo
denormalizado). Spec-governanca §8/§18. Puros, sem DB.
"""

import pytest

import permissions as p
from models import User


pytestmark = [pytest.mark.unit]


def _user(**over) -> User:
    base = {
        "name": "X", "email": "x@x.cv", "role": "socio", "status": "ativo",
        "cargo": "socio", "privileges": [], "account_type": "member",
        "member_category": "ordinario",
    }
    base.update(over)
    return User(**base)


class TestUserCan:
    def test_admin_pode_tudo(self):
        assert p.user_can(_user(role="admin"), "manage_finances") is True

    def test_privilegio_concede(self):
        assert p.user_can(_user(privileges=["manage_finances"]), "manage_finances") is True

    def test_sem_role_nem_privilegio_nega(self):
        assert p.user_can(_user(), "manage_finances") is False

    def test_aceita_dict(self):
        assert p.user_can({"role": "admin", "privileges": []}, "manage_users") is True


class TestOrgaoDetection:
    def test_mesa_ag(self):
        assert p.is_mesa_ag(_user(cargo="ag_presidente")) is True
        assert p.is_mesa_ag(_user(cargo="dir_presidente")) is False

    def test_mesa_ag_via_alias_legado(self):
        # deriva do cargo via normalize, aceita label histórico
        assert p.is_mesa_ag(_user(cargo="Presidente da Mesa")) is True

    def test_direcao(self):
        assert p.is_direcao(_user(cargo="dir_tesoureiro")) is True
        assert p.is_direcao(_user(cargo="cf_relator")) is False

    def test_conselho_fiscal(self):
        assert p.is_conselho_fiscal(_user(cargo="cf_relator")) is True
        assert p.is_conselho_fiscal(_user(cargo="dir_vogal")) is False

    def test_tesoureiro(self):
        assert p.is_tesoureiro(_user(cargo="dir_tesoureiro")) is True
        assert p.is_tesoureiro(_user(cargo="dir_presidente")) is False

    def test_socio_base_sem_orgao(self):
        u = _user(cargo="socio")
        assert p.is_mesa_ag(u) is False
        assert p.is_direcao(u) is False
        assert p.is_conselho_fiscal(u) is False


class TestConvene:
    def test_mesa_ag_convoca(self):
        assert p.can_convene_assembleia(_user(cargo="ag_presidente")) is True

    def test_admin_convoca(self):
        assert p.can_convene_assembleia(_user(role="admin")) is True

    def test_socio_comum_nao_convoca(self):
        assert p.can_convene_assembleia(_user()) is False


class TestEligibility:
    def test_ordinario_ativo_vota_e_elegivel(self):
        u = _user()
        assert p.is_voting_member(u) is True
        assert p.is_eligible_for_office(u) is True

    def test_honorario_nao_vota(self):
        assert p.is_voting_member(_user(member_category="honorario")) is False

    def test_inativo_nao_vota(self):
        assert p.is_voting_member(_user(status="inativo")) is False

    def test_suspenso_nao_vota_nem_elegivel(self):
        u = _user(rights_suspended_until="2027-01-01T00:00:00+00:00")
        assert p.is_voting_member(u, as_of="2026-06-01T00:00:00+00:00") is False
        assert p.is_eligible_for_office(u, as_of="2026-06-01T00:00:00+00:00") is False
