"""Unit tests para os models/constantes de identidade e governança.

Puros — só validam Pydantic + constantes re-exportadas de governance.py, sem
DB nem servidor. Taxonomia canónica (spec-governanca-estatutaria §5/§19):
keys canónicas, 3 órgãos sociais, Relator e Secretário (sem "-Geral").
"""

import pytest
from pydantic import ValidationError

from models import (
    ACCOUNT_TYPES,
    CARGO_DEFAULTS,
    CARGO_KEYS,
    CARGO_SEATS,
    CARGOS,
    CARGOS_ORGAOS_SOCIAIS,
    MEMBER_CATEGORIES,
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

    def test_catalogo_tem_12_cargos_canonicos(self):
        # 3 Mesa AG + 5 Direcção + 3 Conselho Fiscal + Sócio (base).
        assert len(CARGO_KEYS) == 12
        assert len(CARGOS) == 12
        assert len(CARGO_KEYS) == len(set(CARGO_KEYS))

    def test_keys_canonicas_esperadas(self):
        for key in (
            "ag_presidente", "ag_vice_presidente", "ag_secretario",
            "dir_presidente", "dir_vice_presidente", "dir_secretario",
            "dir_tesoureiro", "dir_vogal",
            "cf_presidente", "cf_relator", "cf_vogal", "socio",
        ):
            assert key in CARGO_KEYS

    def test_conselho_fiscal_inclui_relator(self):
        assert "cf_relator" in CARGO_KEYS

    def test_nao_existe_secretario_geral_nem_coordenacoes(self):
        # "Secretário-Geral", Coordenações e Comissões deixaram de ser cargos.
        labels_lower = " ".join(CARGOS).lower()
        assert "geral" not in labels_lower
        assert "coordenador" not in labels_lower
        assert "comissão" not in labels_lower

    def test_orgaos_sociais_sao_tres(self):
        assert set(CARGOS_ORGAOS_SOCIAIS) == {
            "Assembleia Geral", "Direcção", "Conselho Fiscal", "Base"
        }

    def test_member_categories(self):
        assert MEMBER_CATEGORIES == ["fundador", "ordinario", "honorario"]

    def test_privileges_inclui_view_finances_readonly(self):
        assert "view_finances_readonly" in PRIVILEGES
        assert len(PRIVILEGES) == 8
        assert len(PRIVILEGES) == len(set(PRIVILEGES))

    def test_cargo_defaults_e_seats_keyed_by_key(self):
        assert set(CARGO_DEFAULTS) == set(CARGO_KEYS)
        assert set(CARGO_SEATS) == set(CARGO_KEYS)

    def test_cargo_defaults_roles_e_privilegios_validos(self):
        for cargo, default in CARGO_DEFAULTS.items():
            assert default["role"] in ROLES_VALID, f"{cargo}: role inválido"
            for priv in default["privileges"]:
                assert priv in PRIVILEGES, f"{cargo}: privilégio {priv} inválido"

    def test_presidente_direcao_tem_todos_os_privilegios(self):
        assert set(CARGO_DEFAULTS["dir_presidente"]["privileges"]) == set(PRIVILEGES)
        assert CARGO_DEFAULTS["dir_presidente"]["role"] == "admin"

    def test_conselho_fiscal_e_readonly_em_financas(self):
        # Separação de poderes: audita finanças (leitura) sem poder gerir.
        cf = CARGO_DEFAULTS["cf_presidente"]
        assert cf["role"] == "socio"
        assert "view_finances_readonly" in cf["privileges"]
        assert "manage_finances" not in cf["privileges"]

    def test_socio_e_o_default_sem_privilegios(self):
        assert CARGO_DEFAULTS["socio"] == {"role": "socio", "privileges": []}
        assert CARGO_SEATS["socio"] == 0  # estado base, sem limite de vagas

    def test_cargos_singulares_tem_uma_vaga(self):
        for cargo in ("dir_presidente", "dir_tesoureiro", "dir_secretario"):
            assert CARGO_SEATS[cargo] == 1
        assert CARGO_SEATS["dir_vogal"] == 3  # 1 base + 2 fora da sede


# ---------- UserBase ----------


class TestUserBase:
    def test_defaults_account_type_e_cargo_history(self):
        u = UserBase(name="Ana", email="ana@x.cv")
        assert u.account_type == "member"
        assert u.cargo_history == []
        assert u.cargo == "socio"  # key canónica

    def test_defaults_governanca(self):
        u = UserBase(name="Ana", email="ana@x.cv")
        assert u.member_category == "ordinario"
        assert u.orgao is None
        assert u.rights_suspended_until is None
        assert u.residence_island is None

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
        upd = UserAdminUpdate(name="Novo Nome")
        assert "member_id" not in upd.model_dump()


# ---------- CargoMandate ----------


class TestCargoMandate:
    def test_mandato_minimo_valido(self):
        m = CargoMandate(
            cargo="dir_presidente",
            role="admin",
            inicio="2026-01-01T00:00:00+00:00",
            transitioned_by="admin-id",
        )
        assert m.fim is None  # mandato activo
        assert m.id  # uuid gerado
        assert m.elected_by is None
        assert m.suplente is False

    def test_campos_estatutarios_opcionais(self):
        m = CargoMandate(
            cargo="dir_vogal", role="moderador", inicio="2026-01-01",
            transitioned_by="x", orgao="direcao", label="Vogal da Direcção",
            suplente=True, seat_index=2, eleicao_id="e1",
        )
        assert m.orgao == "direcao" and m.seat_index == 2 and m.suplente is True

    def test_transitioned_by_obrigatorio(self):
        with pytest.raises(ValidationError):
            CargoMandate(cargo="dir_presidente", role="admin", inicio="2026-01-01")


# ---------- PromoteUserRequest / DemoteUserRequest / TransferCargoRequest ----------


class TestRequests:
    def test_promote_minimo(self):
        r = PromoteUserRequest(cargo="dir_tesoureiro", role="financeiro")
        assert r.privileges is None  # → usa defaults do cargo na rota
        assert r.effective_date is None

    def test_demote_vazio_valido(self):
        r = DemoteUserRequest()
        assert r.effective_date is None

    def test_transfer_exige_ambos_os_users(self):
        with pytest.raises(ValidationError):
            TransferCargoRequest(cargo="dir_presidente", role="admin", to_user_id="b")

    def test_transfer_valido(self):
        r = TransferCargoRequest(
            from_user_id="a", to_user_id="b", cargo="dir_presidente", role="admin"
        )
        assert r.from_user_id == "a"
        assert r.to_user_id == "b"
