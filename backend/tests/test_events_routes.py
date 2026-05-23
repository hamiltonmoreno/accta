"""Unit tests for routes/events.py — RBAC, registration logic, attendees."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import events as events_route


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _cursor(items):
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


def _make_inactive(user_dict):
    from models import User

    return User(**{**user_dict, "status": "inativo"})


# --------------------------------------------------------------------------- #
# GET /events — visibility-based RBAC
# --------------------------------------------------------------------------- #


class TestGetEvents:
    async def test_admin_sees_all(self, mock_db, admin_user):
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _cursor([])

        mock_db.events.find = find
        await events_route.get_events(current_user=admin_user)
        # Admin nao tem visibility filter (pass branch).
        assert "visibility" not in captured

    async def test_socio_filtered_to_publico_socios(self, mock_db, socio_user):
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _cursor([])

        mock_db.events.find = find
        await events_route.get_events(current_user=socio_user)
        assert captured["visibility"] == {"$in": ["publico", "socios"]}

    async def test_explicit_visibility_param_overrides(self, mock_db, admin_user):
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _cursor([])

        mock_db.events.find = find
        await events_route.get_events(visibility="direcao", current_user=admin_user)
        assert captured["visibility"] == "direcao"


# --------------------------------------------------------------------------- #
# GET /events/featured — public, no auth
# --------------------------------------------------------------------------- #


class TestGetFeatured:
    async def test_returns_none_when_no_event(self, mock_db):
        mock_db.events.find_one = AsyncMock(return_value=None)
        result = await events_route.get_featured_event()
        assert result is None

    async def test_returns_event_with_attendee_count(self, mock_db):
        # First find_one: actual event. Second find_one: attendee count.
        responses = [
            {"id": "e1", "title": "X", "date": "2030-01-01T00:00:00", "visibility": "publico"},
            {"attendees": ["u1", "u2"]},
        ]
        call_count = {"n": 0}

        async def find_one(*args, **kwargs):
            r = responses[call_count["n"]]
            call_count["n"] += 1
            return r

        mock_db.events.find_one = find_one
        result = await events_route.get_featured_event()
        assert result["attendee_count"] == 2


# --------------------------------------------------------------------------- #
# GET /events/{id}
# --------------------------------------------------------------------------- #


class TestGetEvent:
    async def test_404_when_not_found(self, mock_db, socio_user):
        mock_db.events.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await events_route.get_event(event_id="missing", current_user=socio_user)
        assert exc.value.status_code == 404

    async def test_socio_blocked_from_direcao_event(self, mock_db, socio_user):
        mock_db.events.find_one = AsyncMock(return_value={"id": "e1", "visibility": "direcao"})
        with pytest.raises(HTTPException) as exc:
            await events_route.get_event(event_id="e1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_admin_sees_direcao(self, mock_db, admin_user):
        mock_db.events.find_one = AsyncMock(
            return_value={"id": "e1", "visibility": "direcao", "date": "2026-01-01T00:00:00"}
        )
        result = await events_route.get_event(event_id="e1", current_user=admin_user)
        assert result["id"] == "e1"


# --------------------------------------------------------------------------- #
# POST /events — admin only
# --------------------------------------------------------------------------- #


class TestCreateEvent:
    async def test_socio_403(self, mock_db, socio_user):
        from models import EventCreate

        data = EventCreate(
            title="Test",
            description="x",
            type="reuniao",
            date=datetime.now(timezone.utc),
            location="Praia",
            visibility="publico",
        )
        with pytest.raises(HTTPException) as exc:
            await events_route.create_event(event_data=data, current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_admin_creates(self, mock_db, admin_user):
        from models import EventCreate

        # users.find for notify_all_active_users
        mock_db.users.find = MagicMock(return_value=_cursor([]))
        data = EventCreate(
            title="Assembleia",
            description="anual",
            type="assembleia",
            date=datetime.now(timezone.utc),
            location="Sede",
            visibility="socios",
        )
        result = await events_route.create_event(event_data=data, current_user=admin_user)
        assert result.title == "Assembleia"
        mock_db.events.insert_one.assert_awaited_once()


# --------------------------------------------------------------------------- #
# DELETE /events/{id}
# --------------------------------------------------------------------------- #


class TestDeleteEvent:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await events_route.delete_event(event_id="any", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_404_when_not_found(self, mock_db, admin_user):
        mock_db.events.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        with pytest.raises(HTTPException) as exc:
            await events_route.delete_event(event_id="missing", current_user=admin_user)
        assert exc.value.status_code == 404

    async def test_admin_deletes(self, mock_db, admin_user):
        mock_db.events.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        result = await events_route.delete_event(event_id="e1", current_user=admin_user)
        assert "eliminado" in result["message"].lower()


# --------------------------------------------------------------------------- #
# POST /events/{id}/register
# --------------------------------------------------------------------------- #


class TestRegisterForEvent:
    async def test_inactive_403(self, mock_db, socio_user_dict):
        with pytest.raises(HTTPException) as exc:
            await events_route.register_for_event(event_id="e1", current_user=_make_inactive(socio_user_dict))
        assert exc.value.status_code == 403

    async def test_404_when_event_missing(self, mock_db, socio_user):
        mock_db.events.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await events_route.register_for_event(event_id="missing", current_user=socio_user)
        assert exc.value.status_code == 404

    async def test_already_registered_400(self, mock_db, socio_user):
        mock_db.events.find_one = AsyncMock(return_value={"id": "e1", "title": "X", "attendees": [socio_user.id]})
        with pytest.raises(HTTPException) as exc:
            await events_route.register_for_event(event_id="e1", current_user=socio_user)
        assert exc.value.status_code == 400
        assert "ja" in exc.value.detail.lower() or "já" in exc.value.detail.lower()

    async def test_event_full_400(self, mock_db, socio_user):
        mock_db.events.find_one = AsyncMock(
            return_value={
                "id": "e1",
                "title": "X",
                "max_attendees": 2,
                "attendees": ["u1", "u2"],
            }
        )
        with pytest.raises(HTTPException) as exc:
            await events_route.register_for_event(event_id="e1", current_user=socio_user)
        assert exc.value.status_code == 400
        assert "lotado" in exc.value.detail.lower()

    async def test_past_event_400(self, mock_db, socio_user):
        mock_db.events.find_one = AsyncMock(
            return_value={
                "id": "e1",
                "title": "X",
                "date": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                "attendees": [],
            }
        )
        with pytest.raises(HTTPException) as exc:
            await events_route.register_for_event(event_id="e1", current_user=socio_user)
        assert exc.value.status_code == 400
        assert "terminou" in exc.value.detail.lower()

    async def test_successful_registration(self, mock_db, socio_user, monkeypatch):
        register = AsyncMock(return_value="registered")
        monkeypatch.setattr(events_route, "register_event_attendee", register)
        mock_db.events.find_one = AsyncMock(return_value={"id": "e1", "title": "X", "attendees": []})
        result = await events_route.register_for_event(event_id="e1", current_user=socio_user)
        assert "sucesso" in result["message"].lower()
        register.assert_awaited_once_with("e1", socio_user.id)

    async def test_atomic_registration_rechecks_capacity(self, mock_db, socio_user, monkeypatch):
        monkeypatch.setattr(events_route, "register_event_attendee", AsyncMock(return_value="full"))
        mock_db.events.find_one = AsyncMock(
            return_value={"id": "e1", "title": "X", "max_attendees": 2, "attendees": ["u1"]}
        )
        with pytest.raises(HTTPException) as exc:
            await events_route.register_for_event(event_id="e1", current_user=socio_user)
        assert exc.value.status_code == 400
        assert "lotado" in exc.value.detail.lower()


# --------------------------------------------------------------------------- #
# DELETE /events/{id}/register (unregister)
# --------------------------------------------------------------------------- #


class TestUnregister:
    async def test_404_when_event_missing(self, mock_db, socio_user):
        mock_db.events.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await events_route.unregister_from_event(event_id="missing", current_user=socio_user)
        assert exc.value.status_code == 404

    async def test_not_registered_400(self, mock_db, socio_user):
        mock_db.events.find_one = AsyncMock(return_value={"id": "e1", "attendees": []})
        with pytest.raises(HTTPException) as exc:
            await events_route.unregister_from_event(event_id="e1", current_user=socio_user)
        assert exc.value.status_code == 400

    async def test_successful_unregister(self, mock_db, socio_user):
        mock_db.events.find_one = AsyncMock(return_value={"id": "e1", "attendees": [socio_user.id]})
        result = await events_route.unregister_from_event(event_id="e1", current_user=socio_user)
        assert "cancelada" in result["message"].lower()


# --------------------------------------------------------------------------- #
# GET /events/{id}/attendees — privacy semantics
# --------------------------------------------------------------------------- #


class TestGetAttendees:
    async def test_404_when_missing(self, mock_db, socio_user):
        mock_db.events.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await events_route.get_event_attendees(event_id="missing", current_user=socio_user)
        assert exc.value.status_code == 404

    async def test_socio_sees_only_count_not_pii(self, mock_db, socio_user):
        """Privacy: socios so veem count + is_registered, nao a lista de PII."""
        mock_db.events.find_one = AsyncMock(
            return_value={"id": "e1", "attendees": ["u1", socio_user.id, "u3"], "created_by": "outro"}
        )
        result = await events_route.get_event_attendees(event_id="e1", current_user=socio_user)
        assert result["count"] == 3
        assert result["is_registered"] is True
        assert result["attendees"] == []  # PII vazia para socio

    async def test_admin_sees_full_list(self, mock_db, admin_user):
        mock_db.events.find_one = AsyncMock(return_value={"id": "e1", "attendees": ["u1"], "created_by": "outro"})
        mock_db.users.find = MagicMock(return_value=_cursor([{"id": "u1", "name": "User", "email": "u@x.com"}]))
        result = await events_route.get_event_attendees(event_id="e1", current_user=admin_user)
        assert result["count"] == 1
        assert len(result["attendees"]) == 1

    async def test_creator_sees_full_list(self, mock_db, socio_user):
        """Creator do evento (mesmo nao-admin) ve lista completa."""
        mock_db.events.find_one = AsyncMock(return_value={"id": "e1", "attendees": ["u1"], "created_by": socio_user.id})
        mock_db.users.find = MagicMock(return_value=_cursor([{"id": "u1", "name": "User", "email": "u@x.com"}]))
        result = await events_route.get_event_attendees(event_id="e1", current_user=socio_user)
        assert len(result["attendees"]) == 1
