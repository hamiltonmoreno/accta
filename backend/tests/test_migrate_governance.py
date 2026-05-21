"""Unit tests para a transformação pura da migração de governança (Fase M2).

Testa `plan_user_changes` de scripts/migrate_governance_cargos.py sem DB:
normalização de cargo->key, órgão denormalizado, defaults, cargo_history e
idempotência. Contas técnicas ficam fora do catálogo.
"""

import importlib.util
import pathlib

import pytest

_SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "migrate_governance_cargos.py"
_spec = importlib.util.spec_from_file_location("migrate_governance_cargos", _SCRIPT)
mig = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mig)

pytestmark = [pytest.mark.unit]


class TestPlanUserChanges:
    def test_legacy_label_para_key_e_orgao(self):
        c = mig.plan_user_changes({"email": "p@x.cv", "cargo": "Presidente"})
        assert c["cargo"] == "dir_presidente"
        assert c["orgao"] == "direcao"
        assert c["account_type"] == "member"
        assert c["member_category"] == "ordinario"

    def test_secretario_geral_para_dir_secretario(self):
        c = mig.plan_user_changes({"account_type": "member", "member_category": "ordinario", "cargo": "Secretário-Geral"})
        assert c["cargo"] == "dir_secretario"
        assert c["orgao"] == "direcao"
        assert "account_type" not in c  # já presente
        assert "member_category" not in c  # já presente

    def test_socio_canonico_sem_alteracoes(self):
        doc = {
            "account_type": "member", "member_category": "ordinario",
            "cargo": "socio", "orgao": None, "cargo_history": [],
        }
        assert mig.plan_user_changes(doc) == {}

    def test_conta_tecnica_intacta(self):
        doc = {
            "account_type": "technical", "cargo": "Técnico de Sistema", "cargo_history": [],
        }
        c = mig.plan_user_changes(doc)
        # cargo livre não vira key estatutária, sem member_category/orgão.
        assert c == {}

    def test_account_type_ausente_vira_member(self):
        c = mig.plan_user_changes({"cargo": "socio"})
        assert c["account_type"] == "member"
        assert c["member_category"] == "ordinario"

    def test_cargo_history_normalizado(self):
        doc = {
            "account_type": "member", "member_category": "ordinario", "cargo": "socio", "orgao": None,
            "cargo_history": [{"cargo": "Tesoureiro", "role": "financeiro", "inicio": "2024-01-01", "fim": None}],
        }
        c = mig.plan_user_changes(doc)
        assert "cargo_history" in c
        m = c["cargo_history"][0]
        assert m["cargo"] == "dir_tesoureiro"
        assert m["label"] == "Tesoureiro"
        assert m["orgao"] == "direcao"
        assert m["inicio"] == "2024-01-01"  # preserva os restantes campos

    def test_idempotente(self):
        doc = {"email": "p@x.cv", "cargo": "Presidente",
               "cargo_history": [{"cargo": "Vogal", "inicio": "2023-01-01", "fim": None}]}
        changes = mig.plan_user_changes(doc)
        doc2 = {**doc, **changes}
        # 2ª passagem não muda mais nada.
        assert mig.plan_user_changes(doc2) == {}
