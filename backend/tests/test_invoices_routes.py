"""Unit tests for routes/invoices.py — user-scoped list, admin/financeiro CRUD.

Key invariant: sócios só veem as suas próprias invoices (privacy)."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import invoices as invoices_route


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _cursor(items):
    cursor = MagicMock()
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


# --------------------------------------------------------------------------- #
# GET /invoices — RBAC-based filter
# --------------------------------------------------------------------------- #


class TestGetInvoices:
    async def test_admin_sees_all(self, mock_db, admin_user):
        """Admin: query sem filter user_id."""
        captured = {}

        def find(query, _proj):
            captured["query"] = query
            return _cursor([])

        mock_db.invoices.find = find
        await invoices_route.get_invoices(current_user=admin_user)
        assert "user_id" not in captured["query"]

    async def test_financeiro_sees_all(self, mock_db, financeiro_user):
        captured = {}

        def find(query, _proj):
            captured["query"] = query
            return _cursor([])

        mock_db.invoices.find = find
        await invoices_route.get_invoices(current_user=financeiro_user)
        assert "user_id" not in captured["query"]

    async def test_socio_filtered_to_self(self, mock_db, socio_user):
        """Privacy invariant: sócio só vê as próprias invoices."""
        captured = {}

        def find(query, _proj):
            captured["query"] = query
            return _cursor([])

        mock_db.invoices.find = find
        await invoices_route.get_invoices(current_user=socio_user)
        assert captured["query"]["user_id"] == socio_user.id

    async def test_moderador_filtered_to_self(self, mock_db, moderador_user):
        """Moderador modera content — nao tem acesso a invoices de terceiros."""
        captured = {}

        def find(query, _proj):
            captured["query"] = query
            return _cursor([])

        mock_db.invoices.find = find
        await invoices_route.get_invoices(current_user=moderador_user)
        assert captured["query"]["user_id"] == moderador_user.id

    async def test_limit_capped_at_100(self, mock_db, admin_user):
        captured = {}

        def find(_q, _proj):
            cursor = MagicMock()
            cursor.skip = MagicMock(return_value=cursor)

            def lim(n):
                captured["limit"] = n
                return cursor

            cursor.limit = lim
            cursor.to_list = AsyncMock(return_value=[])
            return cursor

        mock_db.invoices.find = find
        await invoices_route.get_invoices(limit=10000, current_user=admin_user)
        assert captured["limit"] == 100


# --------------------------------------------------------------------------- #
# POST /invoices — admin/financeiro
# --------------------------------------------------------------------------- #


class TestCreateInvoice:
    async def test_socio_403(self, mock_db, socio_user):
        from models import InvoiceCreate

        with pytest.raises(HTTPException) as exc:
            await invoices_route.create_invoice(
                invoice_data=InvoiceCreate(
                    user_id="u1", type="quota", amount=5000, due_date=datetime.now(timezone.utc)
                ),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_moderador_403(self, mock_db, moderador_user):
        from models import InvoiceCreate

        with pytest.raises(HTTPException) as exc:
            await invoices_route.create_invoice(
                invoice_data=InvoiceCreate(
                    user_id="u1", type="quota", amount=5000, due_date=datetime.now(timezone.utc)
                ),
                current_user=moderador_user,
            )
        assert exc.value.status_code == 403

    async def test_admin_creates(self, mock_db, admin_user):
        from models import InvoiceCreate

        result = await invoices_route.create_invoice(
            invoice_data=InvoiceCreate(
                user_id="u1", type="quota", amount=5000, due_date=datetime.now(timezone.utc)
            ),
            current_user=admin_user,
        )
        assert result.user_id == "u1"
        assert result.amount == 5000
        mock_db.invoices.insert_one.assert_awaited_once()

    async def test_financeiro_creates(self, mock_db, financeiro_user):
        from models import InvoiceCreate

        result = await invoices_route.create_invoice(
            invoice_data=InvoiceCreate(
                user_id="u1", type="quota", amount=5000, due_date=datetime.now(timezone.utc)
            ),
            current_user=financeiro_user,
        )
        assert result.user_id == "u1"


# --------------------------------------------------------------------------- #
# PATCH /invoices/{id}/confirm
# --------------------------------------------------------------------------- #


class TestConfirmInvoice:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await invoices_route.confirm_invoice(
                invoice_id="inv1", current_user=socio_user
            )
        assert exc.value.status_code == 403

    async def test_admin_confirms_sets_pago_status(self, mock_db, admin_user):
        mock_db.invoices.find_one = AsyncMock(return_value={"id": "inv1"})
        captured = {}

        async def update_one(filter_q, update_op):
            captured["filter"] = filter_q
            captured["update"] = update_op
            return MagicMock(modified_count=1)

        mock_db.invoices.update_one = update_one
        result = await invoices_route.confirm_invoice(
            invoice_id="inv1", current_user=admin_user
        )
        assert "confirmado" in result["message"].lower()
        assert captured["filter"] == {"id": "inv1"}
        set_data = captured["update"]["$set"]
        assert set_data["status"] == "pago"
        assert set_data["confirmed_by_admin"] is True
        assert "confirmed_at" in set_data

    async def test_financeiro_confirms(self, mock_db, financeiro_user):
        mock_db.invoices.find_one = AsyncMock(return_value={"id": "inv1"})
        mock_db.invoices.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        result = await invoices_route.confirm_invoice(
            invoice_id="inv1", current_user=financeiro_user
        )
        assert "confirmado" in result["message"].lower()

    async def test_404_when_invoice_missing(self, mock_db, admin_user):
        mock_db.invoices.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await invoices_route.confirm_invoice(invoice_id="ghost", current_user=admin_user)
        assert exc.value.status_code == 404
