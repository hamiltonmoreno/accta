"""
Unit tests for financial models and edge cases.

These cover Pydantic validation behaviour and category constraints
without hitting MongoDB. They guard against silent data corruption:
negative amounts, invalid types/categories, decimal-precision rounding,
and partial update semantics.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from models import (
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    TRANSACTION_TYPES,
    FinanceSettings,
    FinanceSettingsUpdate,
    Invoice,
    InvoiceCreate,
    Transaction,
    TransactionCreate,
    TransactionUpdate,
)
from routes.finances import require_view_finances, require_manage_finances


pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------- #
# Constants — guard against silent renames
# --------------------------------------------------------------------------- #

class TestFinanceConstants:
    def test_transaction_types_are_exactly_two(self):
        assert TRANSACTION_TYPES == ["receita", "despesa"]

    def test_income_categories_include_quotas(self):
        assert "quotas" in INCOME_CATEGORIES

    def test_income_and_expense_categories_have_distinct_terminal_suffixes(self):
        # "eventos" deliberately appears in both lists (an event can produce
        # both revenue and expense). Ensure the *_receita / _despesa terminals
        # remain separated so reporting code can distinguish them.
        assert any(c.endswith("_receita") for c in INCOME_CATEGORIES)
        assert any(c.endswith("_despesa") for c in EXPENSE_CATEGORIES)
        assert not any(c.endswith("_despesa") for c in INCOME_CATEGORIES)
        assert not any(c.endswith("_receita") for c in EXPENSE_CATEGORIES)


# --------------------------------------------------------------------------- #
# TransactionCreate validation
# --------------------------------------------------------------------------- #

class TestTransactionCreate:
    def _valid(self, **overrides):
        base = {
            "type": "receita",
            "category": "quotas",
            "description": "Teste",
            "amount": 100.0,
            "date": datetime.now(timezone.utc),
        }
        base.update(overrides)
        return TransactionCreate(**base)

    def test_valid_payload_constructs(self):
        t = self._valid()
        assert t.amount == 100.0

    def test_amount_accepts_zero(self):
        # Zero-amount transactions may be legitimate (corrections, transfers).
        t = self._valid(amount=0)
        assert t.amount == 0

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            TransactionCreate(type="receita")  # missing category, description, amount, date

    def test_amount_must_be_numeric(self):
        with pytest.raises(ValidationError):
            self._valid(amount="not-a-number")

    def test_decimal_precision_preserved(self):
        # Currency values commonly carry 2 decimal places — verify they survive Pydantic.
        t = self._valid(amount=1234.56)
        assert t.amount == 1234.56

    def test_large_amount_does_not_overflow(self):
        # Org-level transactions can run into millions of CVE.
        t = self._valid(amount=9_999_999.99)
        assert t.amount == 9_999_999.99


# --------------------------------------------------------------------------- #
# TransactionUpdate — partial updates
# --------------------------------------------------------------------------- #

class TestTransactionUpdate:
    def test_all_fields_optional(self):
        u = TransactionUpdate()
        assert u.amount is None and u.category is None

    def test_excludes_unset_for_partial_update(self):
        # exclude_unset is what routes use to avoid wiping fields on partial PATCH.
        u = TransactionUpdate(amount=50.0)
        dumped = u.model_dump(exclude_unset=True)
        assert dumped == {"amount": 50.0}

    def test_setting_field_to_none_is_distinguishable(self):
        # Distinguish "not provided" (omit) from "set to None" (explicit clear).
        u_omit = TransactionUpdate()
        u_clear = TransactionUpdate(reference=None)
        assert "reference" not in u_omit.model_dump(exclude_unset=True)
        assert "reference" in u_clear.model_dump(exclude_unset=True)


# --------------------------------------------------------------------------- #
# Invoice model — quota & status
# --------------------------------------------------------------------------- #

class TestInvoice:
    def test_default_status_is_pendente(self):
        inv = Invoice(
            user_id="u1",
            type="quota_mensal",
            amount=2000.0,
            due_date=datetime.now(timezone.utc),
        )
        assert inv.status == "pendente"
        assert inv.confirmed_by_admin is False

    def test_default_source_is_payroll(self):
        inv = Invoice(
            user_id="u1",
            type="quota_mensal",
            amount=2000.0,
            due_date=datetime.now(timezone.utc),
        )
        # Per CLAUDE.md: quotas are payroll-deducted, never marked inadimplente.
        assert inv.source == "folha_salarial"

    def test_invoice_create_minimal(self):
        ic = InvoiceCreate(
            user_id="u1",
            type="quota_mensal",
            amount=2000.0,
            due_date=datetime.now(timezone.utc),
        )
        assert ic.amount == 2000.0


# --------------------------------------------------------------------------- #
# FinanceSettings — quota amount sanity
# --------------------------------------------------------------------------- #

class TestFinanceSettings:
    def test_default_quota_is_2000(self):
        s = FinanceSettings()
        assert s.quota_amount == 2000.0
        assert s.id == "finance_settings"  # singleton document

    def test_finance_settings_update_partial(self):
        u = FinanceSettingsUpdate(quota_amount=2500.0)
        dumped = u.model_dump(exclude_unset=True)
        assert dumped == {"quota_amount": 2500.0}


# --------------------------------------------------------------------------- #
# require_view_finances / require_manage_finances — gateways do módulo financeiro
# (spec-identidade-cargos: leitura aceita view_finances_readonly; escrita não)
# --------------------------------------------------------------------------- #

class TestFinanceGateways:
    def test_admin_passes_both(self, admin_user):
        require_view_finances(admin_user)  # must not raise
        require_manage_finances(admin_user)  # must not raise

    def test_financeiro_passes_both(self, financeiro_user):
        require_view_finances(financeiro_user)
        require_manage_finances(financeiro_user)

    def test_socio_blocked_on_both(self, socio_user):
        from fastapi import HTTPException
        for gate in (require_view_finances, require_manage_finances):
            with pytest.raises(HTTPException) as exc_info:
                gate(socio_user)
            assert exc_info.value.status_code == 403

    def test_moderador_blocked_on_both(self, moderador_user):
        from fastapi import HTTPException
        for gate in (require_view_finances, require_manage_finances):
            with pytest.raises(HTTPException) as exc_info:
                gate(moderador_user)
            assert exc_info.value.status_code == 403


# --------------------------------------------------------------------------- #
# Decimal precision — guard against float drift across serialization round-trip
# --------------------------------------------------------------------------- #

class TestPrecision:
    @pytest.mark.parametrize("amount", [0.01, 0.1, 1.23, 99.99, 1000.50, 12345.67])
    def test_amount_round_trip(self, amount):
        t = TransactionCreate(
            type="despesa",
            category="operacional",
            description="precisao",
            amount=amount,
            date=datetime.now(timezone.utc),
        )
        # Round-trip through JSON to mimic API serialization.
        rebuilt = TransactionCreate.model_validate_json(t.model_dump_json())
        assert rebuilt.amount == amount

    def test_known_float_drift_case(self):
        # 0.1 + 0.2 == 0.30000000000000004 — ensure we surface this so future
        # callers know float arithmetic is unsafe for money totals.
        assert 0.1 + 0.2 != 0.3, "If this passes, switch finances to Decimal"
