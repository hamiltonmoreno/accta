"""Unit tests for routes/finances.py — RBAC, transaction CRUD, summary calc."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import finances as finances_route


pytestmark = pytest.mark.unit


def _cursor(items, limit_supports=True):  # noqa: ARG001
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


# --------------------------------------------------------------------------- #
# require_finance_role
# --------------------------------------------------------------------------- #


class TestRequireFinanceRole:
    def test_admin_passes(self, admin_user):
        finances_route.require_finance_role(admin_user)  # no raise

    def test_financeiro_passes(self, financeiro_user):
        finances_route.require_finance_role(financeiro_user)

    def test_socio_403(self, socio_user):
        with pytest.raises(HTTPException) as exc:
            finances_route.require_finance_role(socio_user)
        assert exc.value.status_code == 403

    def test_moderador_403(self, moderador_user):
        with pytest.raises(HTTPException) as exc:
            finances_route.require_finance_role(moderador_user)
        assert exc.value.status_code == 403


# --------------------------------------------------------------------------- #
# GET /transactions — list (admin/financeiro)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestListTransactions:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await finances_route.list_transactions(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_admin_can_list(self, mock_db, admin_user):
        mock_db.transactions.find = MagicMock(return_value=_cursor([]))
        mock_db.transactions.count_documents = AsyncMock(return_value=0)
        result = await finances_route.list_transactions(current_user=admin_user)
        assert result == {"items": [], "total": 0, "skip": 0, "limit": 100}

    async def test_limit_capped_at_200(self, mock_db, admin_user):
        captured = {}

        def find(_q, _proj):
            cursor = MagicMock()
            cursor.sort = MagicMock(return_value=cursor)
            cursor.skip = MagicMock(return_value=cursor)

            def lim(n):
                captured["limit"] = n
                return cursor

            cursor.limit = lim
            cursor.to_list = AsyncMock(return_value=[])
            return cursor

        mock_db.transactions.find = find
        mock_db.transactions.count_documents = AsyncMock(return_value=0)
        await finances_route.list_transactions(limit=10000, current_user=admin_user)
        assert captured["limit"] == 200

    async def test_search_uses_safe_regex_escape(self, mock_db, admin_user):
        """Sprint 3 fix — search escapa regex metachars."""
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _cursor([])

        mock_db.transactions.find = find
        mock_db.transactions.count_documents = AsyncMock(return_value=0)
        await finances_route.list_transactions(search=".*", current_user=admin_user)
        # Expected: re.escape('.*') = '\\.\\*'
        assert captured["description"]["$regex"] == "\\.\\*"


# --------------------------------------------------------------------------- #
# POST /transactions — create
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestCreateTransaction:
    async def test_socio_403(self, mock_db, socio_user):
        from models import TransactionCreate

        data = TransactionCreate(
            type="receita", category="quotas", description="x",
            amount=100, date=datetime.now(timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await finances_route.create_transaction(data=data, current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_negative_amount_400(self, mock_db, admin_user):
        from models import TransactionCreate

        data = TransactionCreate(
            type="receita", category="quotas", description="x",
            amount=-50, date=datetime.now(timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await finances_route.create_transaction(data=data, current_user=admin_user)
        assert exc.value.status_code == 400

    async def test_zero_amount_400(self, mock_db, admin_user):
        from models import TransactionCreate

        data = TransactionCreate(
            type="receita", category="quotas", description="x",
            amount=0, date=datetime.now(timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await finances_route.create_transaction(data=data, current_user=admin_user)
        assert exc.value.status_code == 400

    async def test_invalid_category_for_type_400(self, mock_db, admin_user):
        """receita com categoria de despesa -> 400."""
        from models import TransactionCreate

        data = TransactionCreate(
            type="receita", category="operacional",  # operacional e categoria de despesa
            description="x", amount=100, date=datetime.now(timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await finances_route.create_transaction(data=data, current_user=admin_user)
        assert exc.value.status_code == 400

    async def test_admin_creates_valid_receita(self, mock_db, admin_user):
        from models import TransactionCreate

        # find users for notify_admins
        mock_db.users.find = MagicMock(return_value=_cursor([]))
        data = TransactionCreate(
            type="receita", category="quotas", description="quota mar/2026",
            amount=5000, date=datetime.now(timezone.utc),
        )
        result = await finances_route.create_transaction(data=data, current_user=admin_user)
        assert result.type == "receita"
        assert result.amount == 5000
        mock_db.transactions.insert_one.assert_awaited_once()


# --------------------------------------------------------------------------- #
# DELETE /transactions/{id}
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestDeleteTransaction:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await finances_route.delete_transaction(
                transaction_id="any", current_user=socio_user
            )
        assert exc.value.status_code == 403

    async def test_404_not_found(self, mock_db, admin_user):
        mock_db.transactions.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await finances_route.delete_transaction(
                transaction_id="missing", current_user=admin_user
            )
        assert exc.value.status_code == 404

    async def test_admin_deletes(self, mock_db, admin_user):
        mock_db.transactions.find_one = AsyncMock(return_value={"id": "tx1"})
        result = await finances_route.delete_transaction(
            transaction_id="tx1", current_user=admin_user
        )
        assert "removida" in result["message"].lower()
        mock_db.transactions.delete_one.assert_awaited_with({"id": "tx1"})


# --------------------------------------------------------------------------- #
# GET /summary — calculation correctness
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestSummary:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await finances_route.get_financial_summary(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_calculates_totals_correctly(self, mock_db, admin_user):
        txs = [
            {"type": "receita", "amount": 1000, "category": "quotas", "date": "2026-01-15T00:00:00"},
            {"type": "receita", "amount": 500, "category": "doacoes", "date": "2026-02-01T00:00:00"},
            {"type": "despesa", "amount": 300, "category": "operacional", "date": "2026-01-20T00:00:00"},
        ]
        mock_db.transactions.find = MagicMock(return_value=_cursor(txs))
        result = await finances_route.get_financial_summary(year=2026, current_user=admin_user)
        assert result["total_receitas"] == 1500
        assert result["total_despesas"] == 300
        assert result["resultado_liquido"] == 1200
        assert result["receitas_por_categoria"]["quotas"] == 1000
        assert result["receitas_por_categoria"]["doacoes"] == 500
        assert result["despesas_por_categoria"]["operacional"] == 300
        assert result["total_transacoes"] == 3

    async def test_empty_returns_zeros(self, mock_db, admin_user):
        mock_db.transactions.find = MagicMock(return_value=_cursor([]))
        result = await finances_route.get_financial_summary(current_user=admin_user)
        assert result["total_receitas"] == 0
        assert result["total_despesas"] == 0
        assert result["resultado_liquido"] == 0


# --------------------------------------------------------------------------- #
# GET /dre — monthly breakdown
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestDRE:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await finances_route.get_dre_report(year=2026, current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_groups_by_month_correctly(self, mock_db, admin_user):
        txs = [
            {"type": "receita", "amount": 1000, "category": "quotas", "date": "2026-01-15T00:00:00"},
            {"type": "receita", "amount": 500, "category": "quotas", "date": "2026-01-30T00:00:00"},
            {"type": "despesa", "amount": 200, "category": "operacional", "date": "2026-03-10T00:00:00"},
        ]
        mock_db.transactions.find = MagicMock(return_value=_cursor(txs))
        result = await finances_route.get_dre_report(year=2026, current_user=admin_user)
        assert result["monthly"][1]["receitas"] == 1500
        assert result["monthly"][1]["despesas"] == 0
        assert result["monthly"][3]["despesas"] == 200
        assert result["monthly"][6]["receitas"] == 0  # mes sem transacoes
        assert result["total_receitas"] == 1500
        assert result["total_despesas"] == 200

    async def test_skips_invalid_dates_silently(self, mock_db, admin_user):
        txs = [
            {"type": "receita", "amount": 1000, "category": "quotas", "date": "invalid"},
            {"type": "receita", "amount": 500, "category": "quotas", "date": "2026-02-01T00:00:00"},
        ]
        mock_db.transactions.find = MagicMock(return_value=_cursor(txs))
        result = await finances_route.get_dre_report(year=2026, current_user=admin_user)
        # So a tx valida foi contabilizada.
        assert result["total_receitas"] == 500


# --------------------------------------------------------------------------- #
# Settings endpoints
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestFinanceSettings:
    async def test_get_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await finances_route.get_finance_settings(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_update_socio_403(self, mock_db, socio_user):
        from models import FinanceSettingsUpdate

        with pytest.raises(HTTPException) as exc:
            await finances_route.update_finance_settings(
                data=FinanceSettingsUpdate(quota_amount=5000), current_user=socio_user
            )
        assert exc.value.status_code == 403
