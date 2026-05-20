"""Unit tests para os models/constantes de identidade e cargos (Fase 1).

Puros — só validam Pydantic + constantes, sem DB nem servidor.
"""

import pytest
from pydantic import ValidationError

from models import (
    ACCOUNT_TYPES,
    CARGO_DEFAULTS,
    CARGO_SEATS,
    CARGOS,
    CARGOS_ORGAOS_SOCIAIS,
    PRIVILEGES,
    ROLES_VALID,
    CargoMandate,
    DemoteUserRequest,
    PromoteUserRequest,
    TransferCargoRequest,
    UserAdminUpdate,
    UserBase,
)


# ---------- constantes ----------


class TestConstantes:
    def test_account_types(self):
        assert ACCOUNT_TYPES == ["member", "technical"]

    def test_roles_valid(self):
        assert set(ROLES_VALID) == {"admin", "financeiro", "moderador", "socio"}

    def test_cargos_derivado_dos_orgaos(self):
        # CARGOS é a concatenação plana de CARGOS_ORGAOS_SOCIAIS, sem duplicados.
        flat = [c for grupo in CARGOS_ORGAOS_SOCIAIS.values() for c in grupo]
        assert CARGOS == flat
        assert len(CARGOS) == len(set(CARGOS))

    def test_cargos_tem_15_entradas_e_inclui_sentinela(self):
        assert len(CARGOS) == 15
        assert "Presidente" in CARGOS
        assert "Tesoureiro" in CARGOS
        assert "Presidente do Conselho Fiscal" in CARGOS
        assert "Sócio" in CARGOS

    def test_privileges_inclui_view_finances_readonly(self):
        assert "view_finances_readonly" in PRIVILEGES
        assert len(PRIVILEGES) == 8
        assert len(PRIVILEGES) == len(set(PRIVILEGES))

    def test_cargo_defaults_cobre_todos_os_cargos(self):
        assert set(CARGO_DEFAULTS) == set(CARGOS)

    def test_cargo_seats_cobre_todos_os_cargos(self):
        assert set(CARGO_SEATS) == set(CARGOS)

    def test_cargo_defaults_roles_e_privilegios_validos(self):
        for cargo, default in CARGO_DEFAULTS.items():
            assert default["role"] in ROLES_VALID, f"{cargo}: role inválido"
            for priv in default["privileges"]:
                assert priv in PRIVILEGES, f"{cargo}: privilégio {priv} inválido"

    def test_presidente_tem_todos_os_privilegios(self):
        assert set(CARGO_DEFAULTS["Presidente"]["privileges"]) == set(PRIVILEGES)
        assert CARGO_DEFAULTS["Presidente"]["role"] == "admin"

    def test_conselho_fiscal_e_readonly_em_financas(self):
        # Separação de poderes: audita finanças (leitura) sem poder gerir.
        cf = CARGO_DEFAULTS["Presidente do Conselho Fiscal"]
        assert cf["role"] == "socio"
        assert "view_finances_readonly" in cf["privileges"]
        assert "manage_finances" not in cf["privileges"]

    def test_socio_e_o_default_sem_privilegios(self):
        assert CARGO_DEFAULTS["Sócio"] == {"role": "socio", "privileges": []}
        assert CARGO_SEATS["Sócio"] == 0  # estado base, sem limite de vagas

    def test_cargos_singulares_tem_uma_vaga(self):
        for cargo in ("Presidente", "Tesoureiro", "Secretário-Geral"):
            assert CARGO_SEATS[cargo] == 1


# ---------- UserBase ----------


class TestUserBase:
    def test_defaults_account_type_e_cargo_history(self):
        u = UserBase(name="Ana", email="ana@x.cv")
        assert u.account_type == "member"
        assert u.cargo_history == []
        assert u.cargo == "Sócio"

    def test_account_type_technical_aceite(self):
        u = UserBase(name="Sistema", email="admin@controlador.cv", account_type="technical")
        assert u.account_type == "technical"

    def test_account_type_invalido_rejeitado(self):
        with pytest.raises(ValidationError):
            UserBase(name="X", email="x@x.cv", account_type="robot")


# ---------- UserAdminUpdate ----------


class TestUserAdminUpdate:
    def test_member_id_nao_e_editavel(self):
        # member_id é imutável: não deve existir no model de update admin.
        assert "member_id" not in UserAdminUpdate.model_fields

    def test_member_id_e_ignorado_no_dump(self):
        # extra ignorado por defeito no Pydantic v2 → member_id nunca chega ao $set.
        upd = UserAdminUpdate(name="Novo Nome")
        assert "member_id" not in upd.model_dump()


# ---------- CargoMandate ----------


class TestCargoMandate:
    def test_mandato_minimo_valido(self):
        m = CargoMandate(
            cargo="Presidente",
            role="admin",
            inicio="2026-01-01T00:00:00+00:00",
            transitioned_by="admin-id",
        )
        assert m.fim is None  # mandato activo
        assert m.id  # uuid gerado
        assert m.elected_by is None

    def test_transitioned_by_obrigatorio(self):
        with pytest.raises(ValidationError):
            CargoMandate(cargo="Presidente", role="admin", inicio="2026-01-01")


# ---------- PromoteUserRequest / DemoteUserRequest / TransferCargoRequest ----------


class TestRequests:
    def test_promote_minimo(self):
        r = PromoteUserRequest(cargo="Tesoureiro", role="financeiro")
        assert r.privileges is None  # → usa CARGO_DEFAULTS na rota
        assert r.effective_date is None

    def test_demote_vazio_valido(self):
        r = DemoteUserRequest()
        assert r.effective_date is None

    def test_transfer_exige_ambos_os_users(self):
        with pytest.raises(ValidationError):
            TransferCargoRequest(cargo="Presidente", role="admin", to_user_id="b")

    def test_transfer_valido(self):
        r = TransferCargoRequest(
            from_user_id="a", to_user_id="b", cargo="Presidente", role="admin"
        )
        assert r.from_user_id == "a"
        assert r.to_user_id == "b"
