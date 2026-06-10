"""Unit tests for routes/notifications.py — user-scoped list, mark read,
delete, broadcast (admin), audit logs.

SSE stream endpoint nao testado aqui (precisa integration test + EventSource
client). Restante endpoints sao standard query/mutation routes."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import notifications as notif_route


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _cursor(items):
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


# --------------------------------------------------------------------------- #
# GET /notifications/stream — cap de ligações SSE por utilizador
# --------------------------------------------------------------------------- #


class TestSSEConnectionCap:
    async def test_rejects_429_when_user_at_cap(self, mock_db, socio_user, monkeypatch):
        from starlette.requests import Request

        monkeypatch.setattr(notif_route, "_extract_token", lambda _r: "tok")
        monkeypatch.setattr(notif_route, "get_user_from_token", AsyncMock(return_value=socio_user))
        monkeypatch.setattr(
            notif_route, "_sse_active", {socio_user.id: notif_route._SSE_MAX_PER_USER}
        )
        req = Request({"type": "http", "method": "GET", "path": "/x", "headers": [], "query_string": b""})
        with pytest.raises(HTTPException) as exc:
            await notif_route.notification_stream(req)
        assert exc.value.status_code == 429

    async def test_allows_below_cap(self, mock_db, socio_user, monkeypatch):
        from starlette.requests import Request

        monkeypatch.setattr(notif_route, "_extract_token", lambda _r: "tok")
        monkeypatch.setattr(notif_route, "get_user_from_token", AsyncMock(return_value=socio_user))
        monkeypatch.setattr(
            notif_route, "_sse_active", {socio_user.id: notif_route._SSE_MAX_PER_USER - 1}
        )
        req = Request({"type": "http", "method": "GET", "path": "/x", "headers": [], "query_string": b""})
        resp = await notif_route.notification_stream(req)
        assert resp.media_type == "text/event-stream"


# --------------------------------------------------------------------------- #
# GET /notifications — user-scoped list
# --------------------------------------------------------------------------- #


class TestGetNotifications:
    async def test_filters_by_current_user_id(self, mock_db, socio_user):
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _cursor([])

        mock_db.notifications.find = find
        mock_db.notifications.count_documents = AsyncMock(return_value=0)
        await notif_route.get_notifications(current_user=socio_user)
        # Critical: user nunca ve notifications de outro user.
        assert captured["user_id"] == socio_user.id

    async def test_type_filter_applied(self, mock_db, socio_user):
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _cursor([])

        mock_db.notifications.find = find
        mock_db.notifications.count_documents = AsyncMock(return_value=0)
        await notif_route.get_notifications(type_filter="financeiro", current_user=socio_user)
        assert captured["type"] == "financeiro"

    async def test_unread_only_filter(self, mock_db, socio_user):
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _cursor([])

        mock_db.notifications.find = find
        mock_db.notifications.count_documents = AsyncMock(return_value=0)
        await notif_route.get_notifications(unread_only=True, current_user=socio_user)
        assert captured["read"] is False

    async def test_returns_items_and_total(self, mock_db, socio_user):
        items = [{"id": "n1", "user_id": socio_user.id, "read": False}]
        mock_db.notifications.find = MagicMock(return_value=_cursor(items))
        mock_db.notifications.count_documents = AsyncMock(return_value=42)
        result = await notif_route.get_notifications(current_user=socio_user)
        assert len(result["items"]) == 1
        assert result["total"] == 42


# --------------------------------------------------------------------------- #
# GET /notifications/unread/count
# --------------------------------------------------------------------------- #


class TestUnreadCount:
    async def test_returns_count_scoped_to_user(self, mock_db, socio_user):
        captured = {}

        async def count(query):
            captured.update(query)
            return 5

        mock_db.notifications.count_documents = count
        result = await notif_route.get_unread_count(current_user=socio_user)
        assert result == {"count": 5}
        assert captured["user_id"] == socio_user.id
        assert captured["read"] is False


# --------------------------------------------------------------------------- #
# PATCH /notifications/{id}/read
# --------------------------------------------------------------------------- #


class TestMarkRead:
    async def test_filters_by_id_and_user(self, mock_db, socio_user):
        """Update query inclui user_id — previne user marcar notifs de outro."""
        captured = {}

        async def update(filter_q, _set):
            captured.update(filter_q)
            return MagicMock(modified_count=1)

        mock_db.notifications.update_one = update
        await notif_route.mark_notification_read(notification_id="n1", current_user=socio_user)
        assert captured["id"] == "n1"
        assert captured["user_id"] == socio_user.id


# --------------------------------------------------------------------------- #
# PATCH /notifications/mark-all-read
# --------------------------------------------------------------------------- #


class TestMarkAllRead:
    async def test_only_marks_current_user_unread(self, mock_db, socio_user):
        captured = {}

        async def update_many(filter_q, _set):
            captured.update(filter_q)
            return MagicMock(modified_count=3)

        mock_db.notifications.update_many = update_many
        result = await notif_route.mark_all_notifications_read(current_user=socio_user)
        assert "3" in result["message"]
        assert captured["user_id"] == socio_user.id
        assert captured["read"] is False


# --------------------------------------------------------------------------- #
# DELETE /notifications/{id}
# --------------------------------------------------------------------------- #


class TestDeleteNotification:
    async def test_404_when_not_owned_or_missing(self, mock_db, socio_user):
        """delete_one com filter user_id — se nao bate, deleted_count=0 -> 404."""
        mock_db.notifications.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        with pytest.raises(HTTPException) as exc:
            await notif_route.delete_notification(notification_id="x", current_user=socio_user)
        assert exc.value.status_code == 404

    async def test_success_returns_message(self, mock_db, socio_user):
        mock_db.notifications.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        result = await notif_route.delete_notification(
            notification_id="n1", current_user=socio_user
        )
        assert "removida" in result["message"].lower()


# --------------------------------------------------------------------------- #
# DELETE /notifications/clear/all
# --------------------------------------------------------------------------- #


class TestClearAll:
    async def test_deletes_only_read_and_current_user(self, mock_db, socio_user):
        captured = {}

        async def delete_many(filter_q):
            captured.update(filter_q)
            return MagicMock(deleted_count=7)

        mock_db.notifications.delete_many = delete_many
        result = await notif_route.clear_all_notifications(current_user=socio_user)
        assert "7" in result["message"]
        assert captured["user_id"] == socio_user.id
        # Critical: NAO deve apagar non-read notifications.
        assert captured["read"] is True


# --------------------------------------------------------------------------- #
# POST /notifications/broadcast — admin only
# --------------------------------------------------------------------------- #


class TestBroadcast:
    async def test_socio_403(self, mock_db, socio_user):
        from models import NotificationCreate

        with pytest.raises(HTTPException) as exc:
            await notif_route.broadcast_notification(
                notif_data=NotificationCreate(
                    user_id="broadcast", type="geral", title="X", message="m"
                ),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_financeiro_403(self, mock_db, financeiro_user):
        from models import NotificationCreate

        with pytest.raises(HTTPException) as exc:
            await notif_route.broadcast_notification(
                notif_data=NotificationCreate(
                    user_id="broadcast", type="geral", title="X", message="m"
                ),
                current_user=financeiro_user,
            )
        assert exc.value.status_code == 403

    async def test_admin_broadcasts(self, mock_db, admin_user):
        from models import NotificationCreate

        mock_db.users.find = MagicMock(return_value=_cursor([]))
        result = await notif_route.broadcast_notification(
            notif_data=NotificationCreate(
                user_id="broadcast", type="geral", title="Aviso", message="msg"
            ),
            current_user=admin_user,
        )
        assert "enviada" in result["message"].lower()


# --------------------------------------------------------------------------- #
# POST /notifications — admin only (create one)
# --------------------------------------------------------------------------- #


class TestCreateNotification:
    async def test_socio_403(self, mock_db, socio_user):
        from models import NotificationCreate

        with pytest.raises(HTTPException) as exc:
            await notif_route.create_notification_route(
                notif_data=NotificationCreate(
                    user_id="u1", type="geral", title="X", message="m"
                ),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_admin_creates(self, mock_db, admin_user):
        from models import NotificationCreate

        result = await notif_route.create_notification_route(
            notif_data=NotificationCreate(
                user_id="u1", type="geral", title="X", message="m"
            ),
            current_user=admin_user,
        )
        assert result.user_id == "u1"
        mock_db.notifications.insert_one.assert_awaited_once()


# --------------------------------------------------------------------------- #
# GET /notifications/types — metadata
# --------------------------------------------------------------------------- #


class TestGetTypes:
    async def test_returns_list(self, mock_db, socio_user):
        result = await notif_route.get_notification_types(current_user=socio_user)
        assert isinstance(result["types"], list)
        assert len(result["types"]) > 0
        # Cada item tem value + label.
        assert all("value" in t and "label" in t for t in result["types"])


# --------------------------------------------------------------------------- #
# GET /audit-logs — admin only
# --------------------------------------------------------------------------- #


class TestAuditLogs:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await notif_route.get_audit_logs(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_financeiro_403(self, mock_db, financeiro_user):
        """Audit logs sao sensitive — so admin (nao financeiro)."""
        with pytest.raises(HTTPException) as exc:
            await notif_route.get_audit_logs(current_user=financeiro_user)
        assert exc.value.status_code == 403

    async def test_admin_lists(self, mock_db, admin_user):
        mock_db.audit_logs.find = MagicMock(return_value=_cursor([]))
        result = await notif_route.get_audit_logs(current_user=admin_user)
        assert result == []
