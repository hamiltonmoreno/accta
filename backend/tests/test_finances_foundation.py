"""Unit tests para a fundação F0 das finanças estatutárias.

Cobre os campos aditivos (Transaction/FinanceSettings/UserBase), as categorias
de receita canónicas (Art. 5), o helper `is_presidente`, e a transformação pura
da migração de categorias (scripts/migrate_income_categories.py) — tudo sem DB.
"""

import importlib.util
import pathlib

import pytest

from models import (
    INCOME_CATEGORIES,
    INCOME_CATEGORY_LABELS,
    LEGACY_INCOME_ALIASES,
    FinanceSettings,
    Transaction,
    User,
    canonical_income_category,
)
from permissions import is_presidente

_SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "migrate_income_categories.py"
_spec = importlib.util.spec_from_file_location("migrate_income_categories", _SCRIPT)
mig = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mig)

pytestmark = [pytest.mark.unit]


class TestAdditiveFields:
    def test_transaction_accepts_controls_fields(self):
        t = Transaction(
            type="despesa",
            category="operacional",
            description="Pagamento",
            amount=10000.0,
            date="2026-01-01T00:00:00",
            created_by="admin",
            ato_id="ato-1",
            proof_url="/uploads/proofs/x.pdf",
            conferido=True,
        )
        assert t.ato_id == "ato-1"
        assert t.proof_url == "/uploads/proofs/x.pdf"
        assert t.conferido is True

    def test_transaction_controls_fields_default_none(self):
        t = Transaction(
            type="receita",
            category="quotas",
            description="Quota",
            amount=2000.0,
            date="2026-01-01T00:00:00",
            created_by="admin",
        )
        assert t.ato_id is None and t.proof_url is None and t.conferido is None

    def test_finance_settings_coaprovacao_limiar_default_zero(self):
        s = FinanceSettings()
        assert s.coaprovacao_limiar == 0.0

    def test_user_accepts_joia_fields(self):
        u = User(
            name="Sócio Teste",
            email="socio@controlador.cv",
            cta_qualified_since="2020-01-01",
            joia_devida=4000.0,
            joia_isento=False,
        )
        assert u.cta_qualified_since == "2020-01-01"
        assert u.joia_devida == 4000.0
        assert u.joia_isento is False

    def test_user_joia_fields_default_none(self):
        u = User(name="X", email="x@controlador.cv")
        assert u.cta_qualified_since is None
        assert u.joia_devida is None
        assert u.joia_isento is None


class TestStatutoryCategories:
    def test_income_categories_are_statutory(self):
        assert INCOME_CATEGORIES == [
            "quotas",
            "joias",
            "subvencoes",
            "donativos",
            "venda_publicacoes",
            "juros",
            "extraordinarias",
        ]

    def test_legacy_income_categories_removed(self):
        for legacy in ("patrocinios", "doacoes", "outros_receita"):
            assert legacy not in INCOME_CATEGORIES

    def test_labels_cover_every_income_category(self):
        assert set(INCOME_CATEGORY_LABELS) == set(INCOME_CATEGORIES)
        assert INCOME_CATEGORY_LABELS["joias"] == "Jóias"


class TestCanonicalIncomeCategory:
    def test_aliases_map_to_statutory(self):
        assert canonical_income_category("patrocinios") == "extraordinarias"
        assert canonical_income_category("doacoes") == "donativos"
        assert canonical_income_category("eventos") == "extraordinarias"
        assert canonical_income_category("outros_receita") == "extraordinarias"

    def test_canonical_is_idempotent(self):
        for cat in INCOME_CATEGORIES:
            assert canonical_income_category(cat) == cat

    def test_unknown_passthrough(self):
        assert canonical_income_category("desconhecida") == "desconhecida"

    def test_alias_map_matches_owner_decision(self):
        # patrocinios → extraordinarias (decisão do dono, não donativos).
        assert LEGACY_INCOME_ALIASES["patrocinios"] == "extraordinarias"


class TestMigrationPlan:
    def test_receita_legacy_renamed(self):
        assert mig.plan_transaction_change({"type": "receita", "category": "patrocinios"}) == "extraordinarias"
        assert mig.plan_transaction_change({"type": "receita", "category": "doacoes"}) == "donativos"

    def test_despesa_eventos_not_renamed(self):
        # "eventos" é categoria de DESPESA válida — não deve ser renomeada.
        assert mig.plan_transaction_change({"type": "despesa", "category": "eventos"}) is None

    def test_receita_canonical_idempotent(self):
        assert mig.plan_transaction_change({"type": "receita", "category": "quotas"}) is None
        assert mig.plan_transaction_change({"type": "receita", "category": "donativos"}) is None

    def test_missing_category_ignored(self):
        assert mig.plan_transaction_change({"type": "receita"}) is None


class TestIsPresidente:
    def test_true_for_dir_presidente(self):
        assert is_presidente({"cargo": "dir_presidente"}) is True

    def test_false_for_other_cargos(self):
        assert is_presidente({"cargo": "dir_tesoureiro"}) is False
        assert is_presidente({"cargo": "socio"}) is False
        assert is_presidente({"cargo": ""}) is False
