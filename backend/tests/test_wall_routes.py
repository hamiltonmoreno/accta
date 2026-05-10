"""Unit tests for routes/wall.py — moderation, posts, likes, comments."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import wall as wall_route


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _approve_cursor(items):
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


def _make_inactive(user_dict):
    """Cria User com status inativo para testar guards."""
    from models import User

    return User(**{**user_dict, "status": "inativo"})


# --------------------------------------------------------------------------- #
# GET /wall — only ativos
# --------------------------------------------------------------------------- #


class TestGetWallPosts:
    async def test_inactive_user_403(self, mock_db, socio_user_dict):
        with pytest.raises(HTTPException) as exc:
            await wall_route.get_wall_posts(current_user=_make_inactive(socio_user_dict))
        assert exc.value.status_code == 403

    async def test_active_user_can_list(self, mock_db, socio_user):
        mock_db.wall_posts.find = MagicMock(return_value=_approve_cursor([]))
        result = await wall_route.get_wall_posts(current_user=socio_user)
        assert result == []

    async def test_filters_only_approved(self, mock_db, socio_user):
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _approve_cursor([])

        mock_db.wall_posts.find = find
        await wall_route.get_wall_posts(current_user=socio_user)
        assert captured["approved"] is True

    async def test_category_filter_passed_through(self, mock_db, socio_user):
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _approve_cursor([])

        mock_db.wall_posts.find = find
        await wall_route.get_wall_posts(category="aviso", current_user=socio_user)
        assert captured["category"] == "aviso"

    async def test_category_todos_omitted(self, mock_db, socio_user):
        """'todos' e sentinel UI — nao deve adicionar filtro."""
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _approve_cursor([])

        mock_db.wall_posts.find = find
        await wall_route.get_wall_posts(category="todos", current_user=socio_user)
        assert "category" not in captured


# --------------------------------------------------------------------------- #
# GET /wall/pending — admin/moderador
# --------------------------------------------------------------------------- #


class TestGetPending:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await wall_route.get_pending_wall_posts(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_financeiro_403(self, mock_db, financeiro_user):
        """financeiro nao modera mural."""
        with pytest.raises(HTTPException) as exc:
            await wall_route.get_pending_wall_posts(current_user=financeiro_user)
        assert exc.value.status_code == 403

    async def test_admin_can_list_pending(self, mock_db, admin_user):
        mock_db.wall_posts.find = MagicMock(return_value=_approve_cursor([]))
        result = await wall_route.get_pending_wall_posts(current_user=admin_user)
        assert result == []

    async def test_moderador_can_list_pending(self, mock_db, moderador_user):
        mock_db.wall_posts.find = MagicMock(return_value=_approve_cursor([]))
        result = await wall_route.get_pending_wall_posts(current_user=moderador_user)
        assert result == []


# --------------------------------------------------------------------------- #
# POST /wall — auto-approve para staff
# --------------------------------------------------------------------------- #


class TestCreateWallPost:
    async def test_inactive_403(self, mock_db, socio_user_dict):
        from models import WallPostCreate

        with pytest.raises(HTTPException) as exc:
            await wall_route.create_wall_post(
                post_data=WallPostCreate(content="hi", category="geral"),
                current_user=_make_inactive(socio_user_dict),
            )
        assert exc.value.status_code == 403

    async def test_socio_post_pending_approval(self, mock_db, socio_user):
        from models import WallPostCreate

        mock_db.users.find = MagicMock(return_value=_approve_cursor([]))
        result = await wall_route.create_wall_post(
            post_data=WallPostCreate(content="ola", category="geral"),
            current_user=socio_user,
        )
        assert result["approved"] is False

    async def test_admin_post_auto_approved(self, mock_db, admin_user):
        from models import WallPostCreate

        result = await wall_route.create_wall_post(
            post_data=WallPostCreate(content="anuncio", category="aviso"),
            current_user=admin_user,
        )
        assert result["approved"] is True

    async def test_moderador_post_auto_approved(self, mock_db, moderador_user):
        from models import WallPostCreate

        result = await wall_route.create_wall_post(
            post_data=WallPostCreate(content="info", category="geral"),
            current_user=moderador_user,
        )
        assert result["approved"] is True


# --------------------------------------------------------------------------- #
# PATCH /wall/{id}/approve
# --------------------------------------------------------------------------- #


class TestApprove:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await wall_route.approve_wall_post(post_id="any", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_404_when_not_found(self, mock_db, admin_user):
        mock_db.wall_posts.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await wall_route.approve_wall_post(post_id="missing", current_user=admin_user)
        assert exc.value.status_code == 404

    async def test_admin_approves(self, mock_db, admin_user):
        mock_db.wall_posts.find_one = AsyncMock(return_value={"id": "p1", "user_id": "author1"})
        result = await wall_route.approve_wall_post(post_id="p1", current_user=admin_user)
        assert "aprovado" in result["message"].lower()
        mock_db.wall_posts.update_one.assert_awaited_with(
            {"id": "p1"}, {"$set": {"approved": True}}
        )


# --------------------------------------------------------------------------- #
# DELETE /wall/{id} — author OR staff
# --------------------------------------------------------------------------- #


class TestDeletePost:
    async def test_404_when_not_found(self, mock_db, socio_user):
        mock_db.wall_posts.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await wall_route.delete_wall_post(post_id="missing", current_user=socio_user)
        assert exc.value.status_code == 404

    async def test_author_can_delete_own(self, mock_db, socio_user):
        mock_db.wall_posts.find_one = AsyncMock(return_value={"id": "p1", "user_id": socio_user.id})
        # Garantir que wall_comments existe no fake_db
        mock_db.wall_comments = MagicMock()
        mock_db.wall_comments.delete_many = AsyncMock()
        result = await wall_route.delete_wall_post(post_id="p1", current_user=socio_user)
        assert "removido" in result["message"].lower()

    async def test_socio_cannot_delete_others(self, mock_db, socio_user):
        mock_db.wall_posts.find_one = AsyncMock(return_value={"id": "p1", "user_id": "outro-user"})
        with pytest.raises(HTTPException) as exc:
            await wall_route.delete_wall_post(post_id="p1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_admin_can_delete_any(self, mock_db, admin_user):
        mock_db.wall_posts.find_one = AsyncMock(return_value={"id": "p1", "user_id": "outro"})
        mock_db.wall_comments = MagicMock()
        mock_db.wall_comments.delete_many = AsyncMock()
        result = await wall_route.delete_wall_post(post_id="p1", current_user=admin_user)
        assert "removido" in result["message"].lower()


# --------------------------------------------------------------------------- #
# PATCH /wall/{id}/like
# --------------------------------------------------------------------------- #


class TestLike:
    async def test_inactive_403(self, mock_db, socio_user_dict):
        with pytest.raises(HTTPException) as exc:
            await wall_route.toggle_like_wall_post(
                post_id="p1", current_user=_make_inactive(socio_user_dict)
            )
        assert exc.value.status_code == 403

    async def test_404_when_not_found(self, mock_db, socio_user):
        mock_db.wall_posts.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await wall_route.toggle_like_wall_post(post_id="missing", current_user=socio_user)
        assert exc.value.status_code == 404

    async def test_first_like_adds(self, mock_db, socio_user):
        # find_one chamado 2x — antes (likes=[]) e depois (likes=[user.id]).
        call_count = {"n": 0}

        async def find_one(_q, _proj):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return {"id": "p1", "likes": []}
            return {"id": "p1", "likes": [socio_user.id]}

        mock_db.wall_posts.find_one = find_one
        result = await wall_route.toggle_like_wall_post(post_id="p1", current_user=socio_user)
        assert result["liked"] is True
        assert result["like_count"] == 1

    async def test_second_like_removes(self, mock_db, socio_user):
        call_count = {"n": 0}

        async def find_one(_q, _proj):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return {"id": "p1", "likes": [socio_user.id]}
            return {"id": "p1", "likes": []}

        mock_db.wall_posts.find_one = find_one
        result = await wall_route.toggle_like_wall_post(post_id="p1", current_user=socio_user)
        assert result["liked"] is False
        assert result["like_count"] == 0


# --------------------------------------------------------------------------- #
# Comments
# --------------------------------------------------------------------------- #


class TestComments:
    async def test_inactive_cannot_comment(self, mock_db, socio_user_dict):
        from models import WallCommentCreate

        with pytest.raises(HTTPException) as exc:
            await wall_route.create_wall_comment(
                post_id="p1",
                comment_data=WallCommentCreate(content="hi"),
                current_user=_make_inactive(socio_user_dict),
            )
        assert exc.value.status_code == 403

    async def test_create_404_when_post_missing(self, mock_db, socio_user):
        from models import WallCommentCreate

        mock_db.wall_posts.find_one = AsyncMock(return_value=None)
        # wall_comments collection
        mock_db.wall_comments = MagicMock()
        mock_db.wall_comments.insert_one = AsyncMock()
        with pytest.raises(HTTPException) as exc:
            await wall_route.create_wall_comment(
                post_id="missing",
                comment_data=WallCommentCreate(content="hi"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 404

    async def test_delete_comment_author_can_delete(self, mock_db, socio_user):
        mock_db.wall_comments = MagicMock()
        mock_db.wall_comments.find_one = AsyncMock(
            return_value={"id": "c1", "user_id": socio_user.id, "post_id": "p1"}
        )
        mock_db.wall_comments.delete_one = AsyncMock()
        result = await wall_route.delete_wall_comment(
            post_id="p1", comment_id="c1", current_user=socio_user
        )
        assert "removido" in result["message"].lower()

    async def test_delete_comment_socio_cannot_delete_others(self, mock_db, socio_user):
        mock_db.wall_comments = MagicMock()
        mock_db.wall_comments.find_one = AsyncMock(
            return_value={"id": "c1", "user_id": "outro-user", "post_id": "p1"}
        )
        with pytest.raises(HTTPException) as exc:
            await wall_route.delete_wall_comment(
                post_id="p1", comment_id="c1", current_user=socio_user
            )
        assert exc.value.status_code == 403

    async def test_delete_comment_moderador_can_delete_others(self, mock_db, moderador_user):
        mock_db.wall_comments = MagicMock()
        mock_db.wall_comments.find_one = AsyncMock(
            return_value={"id": "c1", "user_id": "outro", "post_id": "p1"}
        )
        mock_db.wall_comments.delete_one = AsyncMock()
        result = await wall_route.delete_wall_comment(
            post_id="p1", comment_id="c1", current_user=moderador_user
        )
        assert "removido" in result["message"].lower()
