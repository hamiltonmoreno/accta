"""Unit tests for routes/polls.py — RBAC, vote dedup, results aggregation."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import polls as polls_route


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


def _open_poll(poll_id: str = "p1") -> dict:
    """Votação 'aberta' com janela de datas válida (agora dentro do período)."""
    now = datetime.now(timezone.utc)
    return {
        "id": poll_id,
        "title": "Estatutos 2026",
        "status": "aberta",
        "start_date": (now - timedelta(days=1)).isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
    }


# --------------------------------------------------------------------------- #
# GET /polls
# --------------------------------------------------------------------------- #


class TestGetPolls:
    async def test_socio_can_list(self, mock_db, socio_user):
        mock_db.polls.find = MagicMock(return_value=_cursor([]))
        result = await polls_route.get_polls(current_user=socio_user)
        assert result == []

    async def test_limit_capped_at_100(self, mock_db, socio_user):
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

        mock_db.polls.find = find
        await polls_route.get_polls(limit=10000, current_user=socio_user)
        assert captured["limit"] == 100


# --------------------------------------------------------------------------- #
# POST /polls — admin only
# --------------------------------------------------------------------------- #


class TestCreatePoll:
    async def test_socio_403(self, mock_db, socio_user):
        from models import PollCreate

        data = PollCreate(
            title="Q1",
            description="d",
            options=[{"id": 1, "text": "Yes"}, {"id": 2, "text": "No"}],
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=7),
        )
        with pytest.raises(HTTPException) as exc:
            await polls_route.create_poll(poll_data=data, current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_financeiro_403(self, mock_db, financeiro_user):
        from models import PollCreate

        data = PollCreate(
            title="Q1",
            description="d",
            options=[{"id": 1, "text": "A"}, {"id": 2, "text": "B"}],
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=7),
        )
        with pytest.raises(HTTPException) as exc:
            await polls_route.create_poll(poll_data=data, current_user=financeiro_user)
        assert exc.value.status_code == 403

    async def test_admin_creates(self, mock_db, admin_user):
        from models import PollCreate

        # users.find for notify_all_active_users
        mock_db.users.find = MagicMock(return_value=_cursor([]))
        data = PollCreate(
            title="Estatutos 2026",
            description="Aprovacao das alteracoes",
            options=[{"id": 1, "text": "Aprovar"}, {"id": 2, "text": "Rejeitar"}],
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=7),
        )
        result = await polls_route.create_poll(poll_data=data, current_user=admin_user)
        assert result.title == "Estatutos 2026"
        mock_db.polls.insert_one.assert_awaited_once()


# --------------------------------------------------------------------------- #
# POST /polls/vote
# --------------------------------------------------------------------------- #


class TestVote:
    async def test_inactive_403(self, mock_db, socio_user_dict):
        from models import VoteCreate

        with pytest.raises(HTTPException) as exc:
            await polls_route.vote(
                vote_data=VoteCreate(poll_id="p1", vote_option=1),
                current_user=_make_inactive(socio_user_dict),
            )
        assert exc.value.status_code == 403

    async def test_double_vote_400(self, mock_db, socio_user):
        """Dedup: socio nao pode votar 2x na mesma poll."""
        from models import VoteCreate

        mock_db.polls.find_one = AsyncMock(return_value=_open_poll())
        mock_db.user_votes.find_one = AsyncMock(
            return_value={"user_id": socio_user.id, "poll_id": "p1", "vote_option": 1}
        )
        with pytest.raises(HTTPException) as exc:
            await polls_route.vote(
                vote_data=VoteCreate(poll_id="p1", vote_option=2),
                current_user=socio_user,
            )
        assert exc.value.status_code == 400

    async def test_first_vote_inserts(self, mock_db, socio_user):
        from models import VoteCreate

        mock_db.polls.find_one = AsyncMock(return_value=_open_poll())
        mock_db.user_votes.find_one = AsyncMock(return_value=None)
        result = await polls_route.vote(
            vote_data=VoteCreate(poll_id="p1", vote_option=1),
            current_user=socio_user,
        )
        assert result.user_id == socio_user.id
        assert result.poll_id == "p1"
        mock_db.user_votes.insert_one.assert_awaited_once()

    async def test_poll_missing_404(self, mock_db, socio_user):
        from models import VoteCreate

        mock_db.polls.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await polls_route.vote(
                vote_data=VoteCreate(poll_id="nope", vote_option=1),
                current_user=socio_user,
            )
        assert exc.value.status_code == 404

    async def test_poll_not_open_400(self, mock_db, socio_user):
        from models import VoteCreate

        mock_db.polls.find_one = AsyncMock(
            return_value={**_open_poll(), "status": "rascunho"}
        )
        with pytest.raises(HTTPException) as exc:
            await polls_route.vote(
                vote_data=VoteCreate(poll_id="p1", vote_option=1),
                current_user=socio_user,
            )
        assert exc.value.status_code == 400

    async def test_vote_outside_window_400(self, mock_db, socio_user):
        from models import VoteCreate

        now = datetime.now(timezone.utc)
        ended = {
            **_open_poll(),
            "start_date": (now - timedelta(days=10)).isoformat(),
            "end_date": (now - timedelta(days=1)).isoformat(),
        }
        mock_db.polls.find_one = AsyncMock(return_value=ended)
        with pytest.raises(HTTPException) as exc:
            await polls_route.vote(
                vote_data=VoteCreate(poll_id="p1", vote_option=1),
                current_user=socio_user,
            )
        assert exc.value.status_code == 400

    async def test_race_unique_violation_400(self, mock_db, socio_user):
        """C2: insert que viola o índice único vira 400 (não 500)."""
        from models import VoteCreate
        from asyncpg.exceptions import UniqueViolationError

        mock_db.polls.find_one = AsyncMock(return_value=_open_poll())
        mock_db.user_votes.find_one = AsyncMock(return_value=None)
        mock_db.user_votes.insert_one = AsyncMock(side_effect=UniqueViolationError())
        with pytest.raises(HTTPException) as exc:
            await polls_route.vote(
                vote_data=VoteCreate(poll_id="p1", vote_option=1),
                current_user=socio_user,
            )
        assert exc.value.status_code == 400


# --------------------------------------------------------------------------- #
# GET /polls/{id}/results — aggregation
# --------------------------------------------------------------------------- #


class TestGetResults:
    async def test_404_when_poll_missing(self, mock_db, socio_user):
        mock_db.polls.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await polls_route.get_poll_results(poll_id="missing", current_user=socio_user)
        assert exc.value.status_code == 404

    async def test_aggregates_votes_per_option(self, mock_db, socio_user):
        mock_db.polls.find_one = AsyncMock(return_value={"id": "p1"})
        votes = [
            {"vote_option": 1},
            {"vote_option": 1},
            {"vote_option": 2},
            {"vote_option": 1},
        ]
        mock_db.user_votes.find = MagicMock(return_value=_cursor(votes))
        result = await polls_route.get_poll_results(poll_id="p1", current_user=socio_user)
        assert result["total_votes"] == 4
        assert result["results"][1] == 3
        assert result["results"][2] == 1

    async def test_empty_returns_empty_results(self, mock_db, socio_user):
        mock_db.polls.find_one = AsyncMock(return_value={"id": "p1"})
        mock_db.user_votes.find = MagicMock(return_value=_cursor([]))
        result = await polls_route.get_poll_results(poll_id="p1", current_user=socio_user)
        assert result["total_votes"] == 0
        assert result["results"] == {}


# --------------------------------------------------------------------------- #
# PATCH /polls/{id}/status — C1 ciclo de vida
# --------------------------------------------------------------------------- #


class TestUpdatePollStatus:
    async def test_socio_403(self, mock_db, socio_user):
        from models import PollStatusUpdate

        with pytest.raises(HTTPException) as exc:
            await polls_route.update_poll_status(
                poll_id="p1",
                data=PollStatusUpdate(status="aberta"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_poll_missing_404(self, mock_db, admin_user):
        from models import PollStatusUpdate

        mock_db.polls.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await polls_route.update_poll_status(
                poll_id="nope",
                data=PollStatusUpdate(status="aberta"),
                current_user=admin_user,
            )
        assert exc.value.status_code == 404

    async def test_admin_opens_draft_and_broadcasts(self, mock_db, admin_user):
        from models import PollStatusUpdate

        mock_db.polls.find_one = AsyncMock(
            return_value={**_open_poll(), "status": "rascunho"}
        )
        mock_db.users.find = MagicMock(return_value=_cursor([]))
        result = await polls_route.update_poll_status(
            poll_id="p1",
            data=PollStatusUpdate(status="aberta"),
            current_user=admin_user,
        )
        assert result["status"] == "aberta"
        mock_db.polls.update_one.assert_awaited_once()
        mock_db.audit_logs.insert_one.assert_awaited()

    async def test_invalid_transition_400(self, mock_db, admin_user):
        """encerrada -> aberta não é permitido."""
        from models import PollStatusUpdate

        mock_db.polls.find_one = AsyncMock(
            return_value={**_open_poll(), "status": "encerrada"}
        )
        with pytest.raises(HTTPException) as exc:
            await polls_route.update_poll_status(
                poll_id="p1",
                data=PollStatusUpdate(status="aberta"),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_close_open_poll(self, mock_db, admin_user):
        from models import PollStatusUpdate

        mock_db.polls.find_one = AsyncMock(return_value=_open_poll())
        result = await polls_route.update_poll_status(
            poll_id="p1",
            data=PollStatusUpdate(status="encerrada"),
            current_user=admin_user,
        )
        assert result["status"] == "encerrada"
