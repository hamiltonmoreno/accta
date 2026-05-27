"""Unit tests for ranking.py (F0) — fonte única do score + não-regressão de
report.personal. Sem DB real: mock_db (conftest) + injeção de contagens.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import ranking
from routes import report as report_route
from routes import ranking as ranking_route

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _coll(count=0, find_list=None, find_one_ret=None):
    """MagicMock de colecção com count_documents/find/find_one/aggregate assíncronos."""
    c = MagicMock()
    c.count_documents = AsyncMock(return_value=count)
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=find_list or [])
    cur.sort = MagicMock(return_value=cur)
    cur.skip = MagicMock(return_value=cur)
    cur.limit = MagicMock(return_value=cur)
    c.find = MagicMock(return_value=cur)
    c.find_one = AsyncMock(return_value=find_one_ret)
    agg = MagicMock()
    agg.to_list = AsyncMock(return_value=[])
    c.aggregate = MagicMock(return_value=agg)
    return c


def _wire_signals(mock_db):
    """Cabla a zero/vazio todas as colecções que compute_member_score toca."""
    for name in (
        "assembleia_presencas", "user_votes", "events", "wall_posts",
        "gallery_photos", "wall_comments", "project_tasks", "projects",
        "eleicoes", "eleicao_voter_receipts", "ranking_ajustes",
        "member_scores", "ranking_settings",
    ):
        setattr(mock_db, name, _coll())


# --------------------------------------------------------------------------- #
# Funções de período (puras)
# --------------------------------------------------------------------------- #


class TestPeriod:
    def test_year_bounds(self):
        assert ranking._period_bounds("2026") == ("2026-01-01", "2027-01-01")

    def test_all_and_invalid_have_no_bounds(self):
        assert ranking._period_bounds("all") is None
        assert ranking._period_bounds("") is None
        assert ranking._period_bounds(None) is None
        assert ranking._period_bounds("abc") is None

    def test_date_match(self):
        assert ranking._date_match("created_at", "2026") == {
            "created_at": {"$gte": "2026-01-01", "$lt": "2027-01-01"}
        }
        assert ranking._date_match("created_at", "all") == {}


# --------------------------------------------------------------------------- #
# compute_member_score — lógica de pontuação (contagens injetadas, sem DB)
# --------------------------------------------------------------------------- #


class TestComputeScore:
    async def test_weighted_sum_and_breakdown(self):
        counts = dict.fromkeys(ranking.SIGNAL_KEYS, 0)
        counts["assembleia_presenca"] = 2  # 2 × 10 = 20
        counts["mural_post"] = 3  # 3 × 3 = 9
        res = await ranking.compute_member_score("u1", "2026", counts=counts, adjust_total=0)
        assert res["breakdown"]["assembleia_presenca"] == {"count": 2, "points": 20}
        assert res["breakdown"]["mural_post"] == {"count": 3, "points": 9}
        assert res["score"] == 29

    async def test_like_cap_applied(self):
        counts = dict.fromkeys(ranking.SIGNAL_KEYS, 0)
        counts["mural_like_recebido"] = 200  # 200 × 0.5 = 100, cap 50
        res = await ranking.compute_member_score("u1", "2026", counts=counts, adjust_total=0)
        assert res["breakdown"]["mural_like_recebido"]["points"] == 50
        assert res["score"] == 50

    async def test_adjustments_added(self):
        counts = dict.fromkeys(ranking.SIGNAL_KEYS, 0)
        counts["votacao_voto"] = 1  # 5
        res = await ranking.compute_member_score("u1", "2026", counts=counts, adjust_total=7.5)
        assert res["score"] == 12.5
        assert res["breakdown"]["ajustes"]["points"] == 7.5

    async def test_negative_adjustment(self):
        counts = dict.fromkeys(ranking.SIGNAL_KEYS, 0)
        counts["assembleia_presenca"] = 1  # 10
        res = await ranking.compute_member_score("u1", "2026", counts=counts, adjust_total=-4)
        assert res["score"] == 6

    async def test_custom_weights_override_default(self):
        counts = dict.fromkeys(ranking.SIGNAL_KEYS, 0)
        counts["mural_post"] = 2
        res = await ranking.compute_member_score(
            "u1", "2026", weights={"mural_post": 10}, counts=counts, adjust_total=0
        )
        assert res["score"] == 20


# --------------------------------------------------------------------------- #
# gather_signal_counts — contagem + filtro de período + comparência eleitoral
# --------------------------------------------------------------------------- #


class TestGatherSignalCounts:
    async def test_aggregates_counts(self, mock_db):
        mock_db.assembleia_presencas = _coll(count=2)
        mock_db.user_votes = _coll(count=3)
        mock_db.events = _coll(count=4)
        mock_db.wall_posts = _coll(count=5, find_list=[{"likes": ["a", "b"]}, {"likes": ["c"]}])
        mock_db.gallery_photos = _coll(count=1)
        mock_db.wall_comments = _coll(count=6)
        mock_db.project_tasks = _coll(count=2, find_list=[{"project_id": "p1"}])
        mock_db.projects = _coll(count=1)
        mock_db.eleicoes = _coll(find_list=[])  # sem eleições → turnout 0

        counts = await ranking.gather_signal_counts("u1", "2026")
        assert counts["assembleia_presenca"] == 2
        assert counts["votacao_voto"] == 3
        assert counts["evento_presenca"] == 4
        assert counts["mural_post"] == 5
        assert counts["mural_like_recebido"] == 3  # 2 + 1 likes
        assert counts["mural_comentario"] == 6
        assert counts["tarefa_concluida"] == 2
        assert counts["projeto_participacao"] == 1
        assert counts["galeria_foto"] == 1
        assert counts["eleicao_turnout"] == 0

    async def test_period_filter_passed_to_query(self, mock_db):
        captured = {}

        def cap_count(q):
            captured.update(q)
            return 0

        mock_db.user_votes = _coll()
        mock_db.user_votes.count_documents = AsyncMock(side_effect=lambda q: cap_count(q) or 0)
        # restantes a zero
        for name in ("assembleia_presencas", "events", "wall_posts", "gallery_photos",
                     "wall_comments", "project_tasks", "projects", "eleicoes"):
            setattr(mock_db, name, _coll())

        await ranking.gather_signal_counts("u1", "2026")
        assert captured.get("created_at") == {"$gte": "2026-01-01", "$lt": "2027-01-01"}

    async def test_election_turnout_counts_via_hash_without_ballots(self, mock_db):
        """Conta a comparência recomputando o hash; nunca toca eleicao_ballots."""
        for name in ("assembleia_presencas", "user_votes", "events", "wall_posts",
                     "gallery_photos", "wall_comments", "project_tasks", "projects"):
            setattr(mock_db, name, _coll())
        mock_db.eleicoes = _coll(find_list=[{"id": "e1"}, {"id": "e2"}])

        # Só a e1 tem recibo para o membro (hash determinístico).
        async def receipt_find_one(q, proj=None):
            if q.get("voter_hash") == ranking.voter_hash("e1", "u1"):
                return {"id": "r1"}
            return None

        mock_db.eleicao_voter_receipts = MagicMock()
        mock_db.eleicao_voter_receipts.find_one = receipt_find_one

        counts = await ranking.gather_signal_counts("u1", "2026")
        assert counts["eleicao_turnout"] == 1
        # invariante: nunca consultou os boletins
        assert not hasattr(mock_db.eleicao_ballots, "find") or not mock_db.eleicao_ballots.find.called

    async def test_include_turnout_false_skips_elections(self, mock_db):
        for name in ("assembleia_presencas", "user_votes", "events", "wall_posts",
                     "gallery_photos", "wall_comments", "project_tasks", "projects"):
            setattr(mock_db, name, _coll())
        mock_db.eleicoes = _coll(find_list=[{"id": "e1"}])
        mock_db.eleicao_voter_receipts = MagicMock(find_one=AsyncMock(return_value={"id": "r"}))

        counts = await ranking.gather_signal_counts("u1", "2026", include_turnout=False)
        assert counts["eleicao_turnout"] == 0
        mock_db.eleicoes.find.assert_not_called()


class TestAdjustmentsTotal:
    async def test_sums_deltas(self, mock_db):
        mock_db.ranking_ajustes = _coll(find_list=[{"delta": 5}, {"delta": -2}, {"delta": 1.5}])
        assert await ranking._adjustments_total("u1", "2026") == 4.5

    async def test_empty_is_zero(self, mock_db):
        mock_db.ranking_ajustes = _coll(find_list=[])
        assert await ranking._adjustments_total("u1", "2026") == 0


# --------------------------------------------------------------------------- #
# report.personal — NÃO-REGRESSÃO (contrato inalterado; reusa o helper)
# --------------------------------------------------------------------------- #


class TestReportPersonalContract:
    EXPECTED_KEYS = {
        "events_attended", "total_events", "polls_voted", "total_polls",
        "wall_posts", "likes_received", "wall_comments", "projects_member",
        "benefits_used", "photos_submitted", "photos_approved",
        "documents_available", "documents_accessed", "document_access_events",
    }

    def _wire(self, mock_db):
        # cabla TODAS as colecções que report + gather tocam (turnout off →
        # sem eleições), independentemente do que o mock_db pré-cabla.
        for name in (
            "assembleia_presencas", "user_votes", "events", "wall_posts",
            "gallery_photos", "wall_comments", "project_tasks", "projects",
            "polls", "benefit_validations", "documents", "document_accesses",
        ):
            setattr(mock_db, name, _coll())

    async def test_keys_unchanged(self, mock_db, socio_user):
        self._wire(mock_db)
        result = await report_route.get_personal_report(current_user=socio_user)
        assert set(result.keys()) == self.EXPECTED_KEYS

    async def test_signal_mapping(self, mock_db, socio_user):
        """user_votes → polls_voted (mapeamento via gather_signal_counts)."""
        self._wire(mock_db)
        mock_db.user_votes = _coll(count=3)
        result = await report_route.get_personal_report(current_user=socio_user)
        assert result["polls_voted"] == 3


# --------------------------------------------------------------------------- #
# GET /ranking/me — F1 (score ao vivo; rank/total do snapshot quando existir)
# --------------------------------------------------------------------------- #


class TestRankingMe:
    async def test_live_score_no_snapshot(self, mock_db, socio_user):
        _wire_signals(mock_db)
        mock_db.assembleia_presencas = _coll(count=1)  # 1 × 10 = 10
        res = await ranking_route.get_my_ranking(period="2026", current_user=socio_user)
        assert res["period"] == "2026"
        assert res["score"] == 10
        assert "assembleia_presenca" in res["breakdown"]
        # sem rebuild ainda → sem posição
        assert res["rank"] is None
        assert res["total_members"] is None
        assert res["enabled"] is True

    async def test_rank_from_snapshot(self, mock_db, socio_user):
        _wire_signals(mock_db)
        mock_db.member_scores = _coll(count=142, find_one_ret={"rank": 7, "computed_at": "2026-05-26T10:00:00+00:00"})
        res = await ranking_route.get_my_ranking(period="2026", current_user=socio_user)
        assert res["rank"] == 7
        assert res["total_members"] == 142
        assert res["computed_at"] == "2026-05-26T10:00:00+00:00"

    async def test_default_period_is_current_year(self, mock_db, socio_user):
        from datetime import datetime, timezone

        _wire_signals(mock_db)
        res = await ranking_route.get_my_ranking(current_user=socio_user)
        assert res["period"] == str(datetime.now(timezone.utc).year)

    async def test_weights_from_settings_doc(self, mock_db, socio_user):
        """Pesos do doc ranking_settings sobrepõem os defaults."""
        _wire_signals(mock_db)
        mock_db.wall_posts = _coll(count=2)  # sinal mural_post = 2
        mock_db.ranking_settings = _coll(find_one_ret={"weights": {"mural_post": 100}})
        res = await ranking_route.get_my_ranking(period="2026", current_user=socio_user)
        assert res["breakdown"]["mural_post"]["points"] == 200
