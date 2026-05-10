"""Unit tests for routes/benefits.py — public list (no auth), admin CRUD,
validate (active members only)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import benefits as benefits_route


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _cursor(items):
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


def _make_inactive(user_dict):
    from models import User
    return User(**{**user_dict, "status": "inativo"})


# --------------------------------------------------------------------------- #
# GET /benefits/public — sem auth, so active
# --------------------------------------------------------------------------- #


class TestPublicBenefits:
    async def test_filters_only_active(self, mock_db):
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _cursor([])

        mock_db.benefits.find = find
        result = await benefits_route.get_public_benefits()
        assert result == []
        assert captured["active"] is True


# --------------------------------------------------------------------------- #
# GET /benefits — sócios ativos
# --------------------------------------------------------------------------- #


class TestGetBenefits:
    async def test_inactive_user_403(self, mock_db, socio_user_dict):
        with pytest.raises(HTTPException) as exc:
            await benefits_route.get_benefits(current_user=_make_inactive(socio_user_dict))
        assert exc.value.status_code == 403

    async def test_active_socio_sees(self, mock_db, socio_user):
        mock_db.benefits.find = MagicMock(return_value=_cursor([]))
        result = await benefits_route.get_benefits(current_user=socio_user)
        assert result == []

    async def test_filters_only_active(self, mock_db, socio_user):
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _cursor([])

        mock_db.benefits.find = find
        await benefits_route.get_benefits(current_user=socio_user)
        assert captured["active"] is True


# --------------------------------------------------------------------------- #
# POST /benefits — admin only
# --------------------------------------------------------------------------- #


class TestCreateBenefit:
    async def test_socio_403(self, mock_db, socio_user):
        from models import BenefitCreate

        with pytest.raises(HTTPException) as exc:
            await benefits_route.create_benefit(
                benefit_data=BenefitCreate(name="X", description="d", discount_percent=10.0),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_financeiro_403(self, mock_db, financeiro_user):
        from models import BenefitCreate

        with pytest.raises(HTTPException) as exc:
            await benefits_route.create_benefit(
                benefit_data=BenefitCreate(name="X", description="d", discount_percent=10.0),
                current_user=financeiro_user,
            )
        assert exc.value.status_code == 403

    async def test_admin_creates(self, mock_db, admin_user):
        from models import BenefitCreate

        result = await benefits_route.create_benefit(
            benefit_data=BenefitCreate(
                name="Hotel ACCTA", description="20% desconto", discount_percent=20.0,
            ),
            current_user=admin_user,
        )
        assert result.name == "Hotel ACCTA"
        assert result.discount_percent == 20.0
        mock_db.benefits.insert_one.assert_awaited_once()


# --------------------------------------------------------------------------- #
# PATCH /benefits/{id}
# --------------------------------------------------------------------------- #


class TestUpdateBenefit:
    async def test_socio_403(self, mock_db, socio_user):
        from models import BenefitUpdate

        with pytest.raises(HTTPException) as exc:
            await benefits_route.update_benefit(
                benefit_id="any",
                update=BenefitUpdate(name="X"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_404_when_missing(self, mock_db, admin_user):
        from models import BenefitUpdate

        mock_db.benefits.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await benefits_route.update_benefit(
                benefit_id="missing",
                update=BenefitUpdate(name="X"),
                current_user=admin_user,
            )
        assert exc.value.status_code == 404

    async def test_empty_update_400(self, mock_db, admin_user):
        from models import BenefitUpdate

        mock_db.benefits.find_one = AsyncMock(return_value={"id": "b1"})
        with pytest.raises(HTTPException) as exc:
            await benefits_route.update_benefit(
                benefit_id="b1",
                update=BenefitUpdate(),  # nada setado
                current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_admin_updates_partial(self, mock_db, admin_user):
        from models import BenefitUpdate

        # Mock initial fetch + post-update fetch.
        responses = [{"id": "b1", "name": "Old", "active": True}, {"id": "b1", "name": "New", "active": True}]
        call_count = {"n": 0}

        async def find_one(*args, **kwargs):
            r = responses[call_count["n"]]
            call_count["n"] += 1
            return r

        mock_db.benefits.find_one = find_one
        result = await benefits_route.update_benefit(
            benefit_id="b1",
            update=BenefitUpdate(name="New"),
            current_user=admin_user,
        )
        assert result["name"] == "New"
        mock_db.benefits.update_one.assert_awaited_with({"id": "b1"}, {"$set": {"name": "New"}})


# --------------------------------------------------------------------------- #
# DELETE /benefits/{id}
# --------------------------------------------------------------------------- #


class TestDeleteBenefit:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await benefits_route.delete_benefit(benefit_id="any", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_404_when_missing(self, mock_db, admin_user):
        mock_db.benefits.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await benefits_route.delete_benefit(benefit_id="missing", current_user=admin_user)
        assert exc.value.status_code == 404

    async def test_admin_deletes(self, mock_db, admin_user):
        mock_db.benefits.find_one = AsyncMock(return_value={"id": "b1", "name": "Hotel"})
        result = await benefits_route.delete_benefit(benefit_id="b1", current_user=admin_user)
        assert result["status"] == "deleted"
        mock_db.benefits.delete_one.assert_awaited_with({"id": "b1"})


# --------------------------------------------------------------------------- #
# POST /benefits/{id}/validate — active members only
# --------------------------------------------------------------------------- #


class TestValidateBenefit:
    async def test_inactive_403(self, mock_db, socio_user_dict):
        with pytest.raises(HTTPException) as exc:
            await benefits_route.validate_benefit_use(
                benefit_id="b1", current_user=_make_inactive(socio_user_dict)
            )
        assert exc.value.status_code == 403

    async def test_404_when_inactive_benefit(self, mock_db, socio_user):
        # Query filtra active:True — benefit inativo retorna None.
        mock_db.benefits.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await benefits_route.validate_benefit_use(benefit_id="b1", current_user=socio_user)
        assert exc.value.status_code == 404

    async def test_active_socio_validates(self, mock_db, socio_user):
        mock_db.benefits.find_one = AsyncMock(return_value={"id": "b1", "name": "Hotel", "active": True})
        result = await benefits_route.validate_benefit_use(
            benefit_id="b1", current_user=socio_user
        )
        assert result["status"] == "validated"
        assert result["benefit_id"] == "b1"
        # Counter increment + audit log via inserts.
        mock_db.benefit_validations.insert_one.assert_awaited_once()
        mock_db.benefits.update_one.assert_awaited_with(
            {"id": "b1"}, {"$inc": {"validation_count": 1}}
        )

    async def test_validates_filters_only_active_benefit(self, mock_db, socio_user):
        captured = {}

        async def find_one(query, _proj=None):
            captured.update(query)
            return None  # not found

        mock_db.benefits.find_one = find_one
        with pytest.raises(HTTPException):
            await benefits_route.validate_benefit_use(benefit_id="b1", current_user=socio_user)
        assert captured["active"] is True
