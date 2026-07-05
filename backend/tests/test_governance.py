"""Unit tests para backend/governance.py — fonte única de governança estatutária.

Cobre normalização de cargos, expansão de privilégios, órgãos/vagas,
elegibilidade/voto, quórum/maiorias, slots eleitorais e o shape da estrutura
(spec-governanca-estatutaria §18). Puros, sem DB nem servidor.
"""

import pytest

import governance as g
from routes import governance as gov_route


pytestmark = [pytest.mark.unit]


# --------------------------------------------------------------------------- #
# normalize_cargo / cargo_info
# --------------------------------------------------------------------------- #


class TestNormalizeCargo:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("Presidente", "dir_presidente"),
            ("Secretário-Geral", "dir_secretario"),
            ("Secretario-Geral", "dir_secretario"),
            ("Tesoureiro", "dir_tesoureiro"),
            ("Vogal", "dir_vogal"),
            ("Vogal da Direcção", "dir_vogal"),
            ("Vogal da Direção", "dir_vogal"),
            ("Presidente da Mesa", "ag_presidente"),
            ("Secretário da Mesa", "ag_secretario"),
            ("Relator do Conselho Fiscal", "cf_relator"),
            ("Sócio", "socio"),
            ("Socio", "socio"),
            # já canónico → idempotente
            ("dir_tesoureiro", "dir_tesoureiro"),
            ("socio", "socio"),
        ],
    )
    def test_aliases_e_labels_para_keys(self, value, expected):
        assert g.normalize_cargo(value) == expected

    def test_desconhecido_devolve_inalterado(self):
        assert g.normalize_cargo("Imperador") == "Imperador"
        # labels técnicos não mapeiam para cargo estatutário
        assert g.normalize_cargo("Administrador") == "Administrador"

    def test_cargo_info_inclui_relator_e_secretario(self):
        assert g.cargo_info("cf_relator")["label"] == "Relator do Conselho Fiscal"
        # Secretário (sem "-Geral") existe na Direcção e na Mesa
        assert g.cargo_info("dir_secretario")["label"] == "Secretário da Direcção"
        assert g.cargo_info("ag_secretario")["label"] == "Secretário da Mesa da AG"


# --------------------------------------------------------------------------- #
# privilégios / role / órgão / vagas
# --------------------------------------------------------------------------- #


class TestCargoAttributes:
    def test_privileges_all_expande(self):
        privs = g.privileges_for_cargo("dir_presidente")
        assert set(privs) == set(g.PRIVILEGES)

    def test_privileges_lista_explicita(self):
        assert set(g.privileges_for_cargo("dir_tesoureiro")) == {"manage_finances", "view_audit_logs"}

    def test_privileges_cargo_desconhecido_vazio(self):
        assert g.privileges_for_cargo("xpto") == []

    def test_role_for_cargo(self):
        # spec 018 D3: cargos deixam de conceder nível elevado — só
        # Presidente/Vice da Direcção mantêm admin; o resto é socio+privilégios.
        assert g.role_for_cargo("dir_tesoureiro") == "socio"
        assert g.role_for_cargo("dir_presidente") == "admin"
        assert g.role_for_cargo("dir_vice_presidente") == "admin"
        assert g.role_for_cargo("dir_secretario") == "socio"
        assert g.role_for_cargo("dir_vogal") == "socio"
        assert g.role_for_cargo("xpto") == "socio"

    def test_orgao_of_cargo(self):
        assert g.orgao_of_cargo("dir_vogal") == g.DIRECAO
        assert g.orgao_of_cargo("cf_relator") == g.CONSELHO_FISCAL
        assert g.orgao_of_cargo("ag_presidente") == g.ASSEMBLEIA_GERAL
        assert g.orgao_of_cargo("socio") is None

    def test_seats_for_cargo(self):
        assert g.seats_for_cargo("dir_vogal") == 3  # 1 base + 2 fora da sede
        assert g.seats_for_cargo("dir_presidente") == 1
        assert g.seats_for_cargo("socio") == 0

    def test_is_estatutary_cargo(self):
        assert g.is_estatutary_cargo("dir_presidente") is True
        assert g.is_estatutary_cargo("cf_relator") is True
        assert g.is_estatutary_cargo("socio") is False  # estado base, não mandato
        assert g.is_estatutary_cargo("xpto") is False


# --------------------------------------------------------------------------- #
# voto / elegibilidade (spec §8)
# --------------------------------------------------------------------------- #


class TestVotingMember:
    def _member(self, **over):
        base = {"account_type": "member", "status": "ativo", "member_category": "ordinario"}
        base.update(over)
        return base

    def test_ordinario_ativo_vota(self):
        assert g.is_voting_member(self._member()) is True
        assert g.is_eligible_for_office(self._member()) is True

    def test_fundador_vota(self):
        assert g.is_voting_member(self._member(member_category="fundador")) is True

    def test_honorario_nao_vota(self):
        assert g.is_voting_member(self._member(member_category="honorario")) is False

    def test_inactivo_nao_vota(self):
        assert g.is_voting_member(self._member(status="inativo")) is False

    def test_tecnico_nao_vota(self):
        assert g.is_voting_member(self._member(account_type="technical")) is False

    def test_categoria_ausente_assume_ordinario(self):
        m = {"account_type": "member", "status": "ativo"}
        assert g.is_voting_member(m) is True

    def test_direitos_suspensos_bloqueiam_voto(self):
        m = self._member(rights_suspended_until="2026-12-31T00:00:00+00:00")
        assert g.is_voting_member(m, as_of="2026-06-01T00:00:00+00:00") is False
        assert g.is_eligible_for_office(m, as_of="2026-06-01T00:00:00+00:00") is False

    def test_suspensao_expirada_volta_a_votar(self):
        m = self._member(rights_suspended_until="2026-01-01T00:00:00+00:00")
        assert g.is_voting_member(m, as_of="2026-06-01T00:00:00+00:00") is True


# --------------------------------------------------------------------------- #
# quórum / maiorias (spec §11)
# --------------------------------------------------------------------------- #


class TestQuorumMajorities:
    def test_quorum_primeira_chamada_maioria(self):
        assert g.required_quorum(10, 1) == 6  # floor(10/2)+1
        assert g.required_quorum(11, 1) == 6  # floor(11/2)+1

    def test_quorum_segunda_chamada_um_terco(self):
        assert g.required_quorum(10, 2) == 4  # ceil(10/3)
        assert g.required_quorum(9, 2) == 3  # ceil(9/3)

    def test_maioria_absoluta(self):
        assert g.required_absolute_majority(7) == 4
        assert g.required_absolute_majority(8) == 5

    def test_tres_quartos(self):
        assert g.required_three_quarters(10) == 8  # ceil(7.5)
        assert g.required_three_quarters(8) == 6
        assert g.required_three_quarters(4) == 3

    def test_dois_tercos(self):
        # Maioria de 2/3 (eleição de membro honorário — Art. 8.4).
        assert g.required_two_thirds(9) == 6
        assert g.required_two_thirds(10) == 7  # ceil(6.67)
        assert g.required_two_thirds(3) == 2
        assert g.required_two_thirds(4) == 3  # ceil(2.67)


# --------------------------------------------------------------------------- #
# slots eleitorais (spec §12)
# --------------------------------------------------------------------------- #


class TestElectionSlots:
    def test_direcao_5_titulares(self):
        slots = g.election_slots(5)
        # 3 AG + 1 sup + 5 dir + 2 sup + 3 CF + 1 sup = 15
        assert len(slots) == 15
        vogais = [s for s in slots if s["cargo"] == "dir_vogal" and not s["suplente"]]
        assert len(vogais) == 1

    def test_direcao_7_titulares(self):
        slots = g.election_slots(7)
        assert len(slots) == 17
        vogais = [s for s in slots if s["cargo"] == "dir_vogal" and not s["suplente"]]
        assert len(vogais) == 3

    def test_suplentes_por_orgao(self):
        slots = g.election_slots(5)
        suplentes = [s["slot_key"] for s in slots if s["suplente"]]
        assert suplentes == ["ag_suplente_1", "dir_suplente_1", "dir_suplente_2", "cf_suplente_1"]

    def test_slot_keys_unicas(self):
        slots = g.election_slots(7)
        keys = [s["slot_key"] for s in slots]
        assert len(keys) == len(set(keys))


# --------------------------------------------------------------------------- #
# governance_structure / endpoint
# --------------------------------------------------------------------------- #


class TestStructure:
    def test_shape_completo(self):
        st = g.governance_structure()
        for key in (
            "orgaos",
            "cargos",
            "funcoes_operacionais",
            "member_categories",
            "privileges",
            "roles",
            "mandato_anos",
            "election_slots",
        ):
            assert key in st
        assert st["mandato_anos"] == 3
        assert len(st["orgaos"]) == 3
        assert len(st["cargos"]) == 12

    def test_cargos_sem_labels_duplicados(self):
        st = g.governance_structure()
        labels = [c["label"] for c in st["cargos"]]
        assert len(labels) == len(set(labels))

    def test_cargo_inclui_role_e_privileges_default(self):
        st = g.governance_structure()
        tes = next(c for c in st["cargos"] if c["key"] == "dir_tesoureiro")
        # spec 018 D3: Tesoureiro deixa de conceder nível — socio + privilégios
        assert tes["role_default"] == "socio"
        assert set(tes["privileges_default"]) == {"manage_finances", "view_audit_logs"}
        assert tes["orgao"] == "direcao"

    def test_member_categories_marcam_voto(self):
        st = g.governance_structure()
        votos = {m["key"]: m["vota"] for m in st["member_categories"]}
        assert votos == {"fundador": True, "ordinario": True, "honorario": False}

    @pytest.mark.asyncio
    async def test_endpoint_devolve_estrutura(self, socio_user):
        # Autenticado leve — qualquer membro autenticado lê a estrutura.
        result = await gov_route.get_governance_structure(current_user=socio_user)
        assert result["mandato_anos"] == 3
        assert len(result["cargos"]) == 12
