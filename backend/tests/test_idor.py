"""Regressão IDOR — B não acede a recursos de A (§6.2).

≥8 pares recurso×verbo via chamada direta às funções de rota com mock_db.
NOTA: eleições não têm endpoint de leitura de cédula/recibo — proteção
arquitetural (ballots sem user_id; recibos por HMAC voter_hash nunca
expostos), logo sem superfície IDOR a testar aí.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

import routes.gallery as gallery
import routes.notifications as notifications
import routes.projects as projects
import routes.wall as wall

pytestmark = pytest.mark.unit


# ---- notifications: scoping por user_id ------------------------------------
@pytest.mark.asyncio
async def test_delete_notification_scoped_to_owner(mock_db, socio_user):
    mock_db.notifications.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
    with pytest.raises(HTTPException) as exc:
        await notifications.delete_notification("notif-de-A", current_user=socio_user)
    assert exc.value.status_code == 404
    assert mock_db.notifications.delete_one.call_args.args[0]["user_id"] == socio_user.id


@pytest.mark.asyncio
async def test_mark_read_scoped_to_owner(mock_db, socio_user):
    mock_db.notifications.update_one = AsyncMock(return_value=MagicMock(modified_count=0))
    await notifications.mark_notification_read("notif-de-A", current_user=socio_user)
    assert mock_db.notifications.update_one.call_args.args[0]["user_id"] == socio_user.id


@pytest.mark.asyncio
async def test_list_notifications_scoped_to_caller(mock_db, socio_user):
    await notifications.get_notifications(
        skip=0, limit=50, type_filter=None, unread_only=False, current_user=socio_user
    )
    assert mock_db.notifications.find.call_args.args[0]["user_id"] == socio_user.id


# ---- projetos --------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_comment_of_other_forbidden(mock_db, socio_user):
    mock_db.project_comments = MagicMock()
    mock_db.project_comments.find_one = AsyncMock(
        return_value={"id": "c1", "project_id": "p1", "user_id": "outro-user"}
    )
    mock_db.project_comments.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    with pytest.raises(HTTPException) as exc:
        await projects.delete_comment("p1", "c1", current_user=socio_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_expense_non_manager_forbidden(mock_db, socio_user):
    mock_db.projects.find_one = AsyncMock(
        return_value={"id": "p1", "created_by": "dono-A", "responsible_id": "dono-A"}
    )
    mock_db.project_expenses = MagicMock()
    mock_db.project_expenses.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    with pytest.raises(HTTPException) as exc:
        await projects.delete_expense("p1", "e1", current_user=socio_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_milestone_non_manager_forbidden(mock_db, socio_user):
    mock_db.projects.find_one = AsyncMock(
        return_value={"id": "p1", "created_by": "dono-A", "responsible_id": "dono-A"}
    )
    mock_db.project_milestones = MagicMock()
    mock_db.project_milestones.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    with pytest.raises(HTTPException) as exc:
        await projects.delete_milestone("p1", "m1", current_user=socio_user)
    assert exc.value.status_code == 403


# ---- mural -----------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_wall_post_of_other_forbidden(mock_db, socio_user):
    mock_db.wall_posts.find_one = AsyncMock(return_value={"id": "w1", "user_id": "outro-user"})
    with pytest.raises(HTTPException) as exc:
        await wall.delete_wall_post("w1", current_user=socio_user)
    assert exc.value.status_code == 403


# ---- galeria: não-admin só vê aprovadas ------------------------------------
@pytest.mark.asyncio
async def test_non_admin_cannot_query_pending_photos(mock_db, socio_user):
    await gallery.get_gallery_photos(album_id=None, status="pending", current_user=socio_user)
    assert mock_db.gallery_photos.find.call_args.args[0]["status"] == "approved"
