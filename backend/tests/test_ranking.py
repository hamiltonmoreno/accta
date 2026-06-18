"""Unit tests for ranking.py (F0) — fonte única do score + não-regressão de
report.personal. Sem DB real: mock_db (conftest) + injeção de contagens.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

import ranking
from models import RankingAjusteCreate, RankingOptOut, RankingSettingsUpdate
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


# --------------------------------------------------------------------------- #
# rebuild_scores — F2 (ranking de competição, idempotência, elegibilidade)
# --------------------------------------------------------------------------- #


def _wcoll(**kw):
    """Como _coll mas com métodos de escrita (insert/delete/update) AsyncMock.
    `find_one`/`count_documents`/`find` são herdados de _coll (já AsyncMock)."""
    c = _coll(**kw)
    c.insert_one = AsyncMock()
    c.insert_many = AsyncMock()
    c.delete_many = AsyncMock()
    c.update_one = AsyncMock()
    c.update_many = AsyncMock()
    return c


def _wire_replace(monkeypatch):
    """Substitui `ranking.replace_period_scores` (DAO atómico delete+insert) por um
    AsyncMock fiel ao contrato (devolve len(docs)). O snapshot deixou de ser
    `member_scores.delete_many`+`insert_many` para fechar a janela de leaderboard
    vazio (database.replace_period_scores) — os testes asseguram o snapshot via
    este mock. Devolve o mock; `.call_args.args == (period_key, docs)`."""

    async def _fake(period_key, docs):
        return len(docs)

    mock = AsyncMock(side_effect=_fake)
    monkeypatch.setattr(ranking, "replace_period_scores", mock)
    return mock


def _members(*specs):
    """specs: (id, name) → docs de membro elegível para rebuild."""
    return [
        {"id": i, "name": n, "status": "ativo", "member_id": None, "cargo": None, "photo_url": None}
        for i, n in specs
    ]


class TestRebuildScores:
    async def test_ranks_desc_with_shared_ties(self, mock_db, monkeypatch):
        mock_db.users = _coll(find_list=_members(("a", "Ana"), ("b", "Bruno"), ("c", "Carla"), ("d", "Duarte")))
        mock_db.member_scores = _wcoll()
        mock_db.ranking_settings = _wcoll(find_one_ret=None)
        replace = _wire_replace(monkeypatch)

        scores = {"a": 30.0, "b": 20.0, "c": 20.0, "d": 5.0}

        async def fake_compute(uid, period, weights=None, max_like=50):
            return {"score": scores[uid], "breakdown": {"x": {"count": 1, "points": scores[uid]}}}

        monkeypatch.setattr(ranking, "compute_member_score", AsyncMock(side_effect=fake_compute))

        n = await ranking.rebuild_scores("2026")
        assert n == 4
        period_key, docs = replace.call_args.args
        by_user = {d["user_id"]: d for d in docs}
        assert by_user["a"]["rank"] == 1
        # empate em 20.0 partilha a rank 2 (desempate estável por nome: Bruno < Carla)
        assert by_user["b"]["rank"] == 2
        assert by_user["c"]["rank"] == 2
        # próxima salta para 4 (ranking de competição padrão)
        assert by_user["d"]["rank"] == 4
        # cada doc do snapshot tem os campos de display
        assert by_user["a"]["member_name"] == "Ana"
        assert by_user["a"]["period_key"] == "2026"

    async def test_idempotent_replaces_snapshot(self, mock_db, monkeypatch):
        mock_db.users = _coll(find_list=_members(("a", "Ana"), ("b", "Bruno")))
        mock_db.member_scores = _wcoll()
        mock_db.ranking_settings = _wcoll(find_one_ret={"id": "s1"})  # settings já existe
        replace = _wire_replace(monkeypatch)
        monkeypatch.setattr(
            ranking, "compute_member_score", AsyncMock(return_value={"score": 10.0, "breakdown": {}})
        )

        await ranking.rebuild_scores("2026")
        await ranking.rebuild_scores("2026")
        # cada rebuild substitui o snapshot do período atomicamente → idempotente
        assert replace.await_count == 2
        assert replace.call_args.args[0] == "2026"
        # settings já existia → update_one (nunca insert duplicado)
        assert mock_db.ranking_settings.update_one.await_count == 2
        mock_db.ranking_settings.insert_one.assert_not_called()

    async def test_settings_created_when_absent(self, mock_db, monkeypatch):
        mock_db.users = _coll(find_list=_members(("a", "Ana")))
        mock_db.member_scores = _wcoll()
        mock_db.ranking_settings = _wcoll(find_one_ret=None)  # sem doc de settings
        _wire_replace(monkeypatch)
        monkeypatch.setattr(
            ranking, "compute_member_score", AsyncMock(return_value={"score": 1.0, "breakdown": {}})
        )

        await ranking.rebuild_scores("2026")
        mock_db.ranking_settings.insert_one.assert_awaited_once()
        created = mock_db.ranking_settings.insert_one.call_args.args[0]
        assert "last_rebuild_at" in created and created["weights"]  # doc bem formado

    async def test_eligibility_filter_excludes_pendentes_and_technical(self, mock_db, monkeypatch):
        mock_db.users = _coll(find_list=[])
        mock_db.member_scores = _wcoll()
        mock_db.ranking_settings = _wcoll(find_one_ret=None)
        _wire_replace(monkeypatch)
        monkeypatch.setattr(
            ranking, "compute_member_score", AsyncMock(return_value={"score": 0, "breakdown": {}})
        )

        await ranking.rebuild_scores("2026")
        q = mock_db.users.find.call_args.args[0]
        assert q["status"] == {"$in": ["ativo", "inativo"]}
        assert {"account_type": "member"} in q["$or"]
        assert {"account_type": {"$exists": False}} in q["$or"]

    async def test_empty_members_no_insert(self, mock_db, monkeypatch):
        mock_db.users = _coll(find_list=[])
        mock_db.member_scores = _wcoll()
        mock_db.ranking_settings = _wcoll(find_one_ret=None)
        replace = _wire_replace(monkeypatch)
        monkeypatch.setattr(
            ranking, "compute_member_score", AsyncMock(return_value={"score": 0, "breakdown": {}})
        )
        n = await ranking.rebuild_scores("2026")
        assert n == 0
        # substitui o snapshot mesmo quando vazio (apaga o período, insere 0)
        replace.assert_awaited_once_with("2026", [])


# --------------------------------------------------------------------------- #
# GET /ranking/leaderboard — F2 (snapshot, paginação, linha do próprio, privacidade)
# --------------------------------------------------------------------------- #


class TestLeaderboard:
    async def test_returns_entries_total_and_me(self, mock_db, socio_user):
        entries = [
            {"user_id": "a", "rank": 1, "score": 30, "member_name": "Ana", "computed_at": "2026-05-26T10:00:00+00:00"},
            {"user_id": "b", "rank": 2, "score": 20, "member_name": "Bruno", "computed_at": "2026-05-26T10:00:00+00:00"},
        ]
        me = {
            "user_id": socio_user.id, "rank": 5, "score": 8,
            "breakdown": {"x": {"count": 1, "points": 8}}, "computed_at": "2026-05-26T10:00:00+00:00",
        }
        mock_db.member_scores = _coll(count=142, find_list=entries, find_one_ret=me)
        mock_db.ranking_settings = _coll(find_one_ret=None)

        res = await ranking_route.get_leaderboard(period="2026", current_user=socio_user)
        assert res["total"] == 142
        assert res["entries"] == entries
        assert res["me"] == me  # a própria linha traz breakdown
        assert res["computed_at"] == "2026-05-26T10:00:00+00:00"
        assert res["top_n_dashboard"] == 5

    async def test_breakdown_excluded_from_public_list(self, mock_db, socio_user):
        mock_db.member_scores = _coll(count=0, find_list=[], find_one_ret=None)
        mock_db.ranking_settings = _coll(find_one_ret=None)
        await ranking_route.get_leaderboard(period="2026", current_user=socio_user)
        proj = mock_db.member_scores.find.call_args.args[1]
        assert proj.get("breakdown") == 0  # §2.5: breakdown é privado

    async def test_pagination_clamped(self, mock_db, socio_user):
        mock_db.member_scores = _coll(count=0, find_list=[], find_one_ret=None)
        mock_db.ranking_settings = _coll(find_one_ret=None)
        await ranking_route.get_leaderboard(period="2026", limit=999, offset=-5, current_user=socio_user)
        cur = mock_db.member_scores.find.return_value
        cur.skip.assert_called_with(0)
        cur.limit.assert_called_with(100)

    async def test_disabled_returns_empty(self, mock_db, socio_user):
        """`enabled=False` → não serve o snapshot (defesa server-side)."""
        mock_db.member_scores = _coll(count=99, find_list=[{"user_id": "a"}], find_one_ret={"user_id": socio_user.id})
        mock_db.ranking_settings = _coll(find_one_ret={"enabled": False})
        res = await ranking_route.get_leaderboard(period="2026", current_user=socio_user)
        assert res["enabled"] is False
        assert res["entries"] == []
        assert res["me"] is None
        assert res["total"] == 0
        mock_db.member_scores.find.assert_not_called()  # short-circuit: nem consulta o snapshot


# --------------------------------------------------------------------------- #
# POST /ranking/rebuild — RBAC + auditoria (F2)
# --------------------------------------------------------------------------- #


def _req():
    return Request(
        {"type": "http", "headers": [], "client": ("127.0.0.1", 0), "method": "POST", "path": "/api/ranking/rebuild"}
    )


class TestRebuildRoute:
    async def test_socio_forbidden(self, socio_user, monkeypatch):
        rb = AsyncMock(return_value=3)
        monkeypatch.setattr(ranking_route, "rebuild_scores", rb)
        with pytest.raises(HTTPException) as ei:
            await ranking_route.rebuild_ranking(request=_req(), period="2026", current_user=socio_user)
        assert ei.value.status_code == 403
        rb.assert_not_called()

    async def test_admin_allowed_and_audits(self, admin_user, monkeypatch):
        rb = AsyncMock(return_value=7)
        audit = AsyncMock()
        monkeypatch.setattr(ranking_route, "rebuild_scores", rb)
        monkeypatch.setattr(ranking_route, "create_audit_log", audit)
        res = await ranking_route.rebuild_ranking(request=_req(), period="2026", current_user=admin_user)
        assert res == {"period": "2026", "members": 7}
        rb.assert_awaited_once_with("2026")
        audit.assert_awaited_once()
        assert audit.await_args.kwargs["action"] == "ranking_rebuilt"
        assert audit.await_args.kwargs["details"] == {"period": "2026", "members": 7}

    async def test_direcao_allowed(self, socio_user, monkeypatch):
        direcao = socio_user.model_copy(update={"cargo": "dir_tesoureiro"})
        rb = AsyncMock(return_value=1)
        monkeypatch.setattr(ranking_route, "rebuild_scores", rb)
        monkeypatch.setattr(ranking_route, "create_audit_log", AsyncMock())
        res = await ranking_route.rebuild_ranking(request=_req(), period="2026", current_user=direcao)
        assert res["members"] == 1
        rb.assert_awaited_once()

    async def test_financeiro_and_moderador_forbidden(self, financeiro_user, moderador_user, monkeypatch):
        """Financeiro/moderador não gerem o ranking (nem admin nem Direcção) → 403."""
        rb = AsyncMock(return_value=1)
        monkeypatch.setattr(ranking_route, "rebuild_scores", rb)
        for u in (financeiro_user, moderador_user):
            with pytest.raises(HTTPException) as ei:
                await ranking_route.rebuild_ranking(request=_req(), period="2026", current_user=u)
            assert ei.value.status_code == 403
        rb.assert_not_called()


# --------------------------------------------------------------------------- #
# F4 — GET/PUT /ranking/settings
# --------------------------------------------------------------------------- #


class TestSettingsRoutes:
    async def test_get_forbidden_for_socio(self, mock_db, socio_user):
        mock_db.ranking_settings = _coll(find_one_ret=None)
        with pytest.raises(HTTPException) as ei:
            await ranking_route.get_ranking_settings(current_user=socio_user)
        assert ei.value.status_code == 403

    async def test_get_returns_merged_settings(self, mock_db, admin_user):
        mock_db.ranking_settings = _coll(find_one_ret={"visibility": "direcao_only"})
        res = await ranking_route.get_ranking_settings(current_user=admin_user)
        assert res["visibility"] == "direcao_only"
        assert res["weights"]["assembleia_presenca"] == 10  # defaults fundidos

    async def test_put_merges_weights_and_audits(self, mock_db, admin_user, monkeypatch):
        mock_db.ranking_settings = _wcoll(find_one_ret={"id": "s1"})  # já existe → update
        audit = AsyncMock()
        monkeypatch.setattr(ranking_route, "create_audit_log", audit)
        payload = RankingSettingsUpdate(weights={"mural_post": 9}, top_n_dashboard=10)
        await ranking_route.update_ranking_settings(payload=payload, request=_req(), current_user=admin_user)

        upd = mock_db.ranking_settings.update_one.call_args.args[1]["$set"]
        assert upd["weights"]["mural_post"] == 9
        assert upd["weights"]["assembleia_presenca"] == 10  # merge preserva os outros
        assert upd["top_n_dashboard"] == 10
        assert upd["updated_by"] == admin_user.id
        changes = audit.await_args.kwargs["details"]["changes"]
        assert audit.await_args.kwargs["action"] == "ranking_settings_updated"
        assert changes["top_n_dashboard"] == 10
        assert changes["weights"] == {"mural_post": 9}  # diff só dos pesos enviados

    async def test_manage_ranking_privilege_grants_access(self, mock_db, socio_user):
        """Sócio comum + privilégio `manage_ranking` → acede às definições (sem ser admin/Direcção)."""
        mgr = socio_user.model_copy(update={"privileges": ["manage_ranking"]})
        mock_db.ranking_settings = _coll(find_one_ret=None)
        res = await ranking_route.get_ranking_settings(current_user=mgr)
        assert "weights" in res

    async def test_put_creates_settings_when_absent(self, mock_db, admin_user, monkeypatch):
        mock_db.ranking_settings = _wcoll(find_one_ret=None)  # sem doc → insert
        monkeypatch.setattr(ranking_route, "create_audit_log", AsyncMock())
        await ranking_route.update_ranking_settings(
            payload=RankingSettingsUpdate(enabled=False), request=_req(), current_user=admin_user
        )
        mock_db.ranking_settings.insert_one.assert_awaited_once()

    async def test_put_invalid_weight_key_400(self, mock_db, admin_user):
        mock_db.ranking_settings = _wcoll(find_one_ret=None)
        with pytest.raises(HTTPException) as ei:
            await ranking_route.update_ranking_settings(
                payload=RankingSettingsUpdate(weights={"bogus": 5}), request=_req(), current_user=admin_user
            )
        assert ei.value.status_code == 400

    async def test_put_forbidden_for_socio(self, mock_db, socio_user):
        mock_db.ranking_settings = _wcoll(find_one_ret=None)
        with pytest.raises(HTTPException) as ei:
            await ranking_route.update_ranking_settings(
                payload=RankingSettingsUpdate(enabled=False), request=_req(), current_user=socio_user
            )
        assert ei.value.status_code == 403


# --------------------------------------------------------------------------- #
# F4 — POST/GET /ranking/adjustments
# --------------------------------------------------------------------------- #


class TestAdjustmentsRoutes:
    async def test_add_forbidden_for_socio(self, socio_user):
        with pytest.raises(HTTPException) as ei:
            await ranking_route.add_ranking_adjustment(
                payload=RankingAjusteCreate(user_id="u9", period_key="2026", delta=5, reason="x"),
                request=_req(), current_user=socio_user,
            )
        assert ei.value.status_code == 403

    async def test_add_ghost_member_404(self, mock_db, admin_user, monkeypatch):
        mock_db.users = _coll(find_one_ret=None)
        mock_db.ranking_ajustes = _wcoll()
        monkeypatch.setattr(ranking_route, "create_audit_log", AsyncMock())
        monkeypatch.setattr(ranking_route, "create_notification", AsyncMock())
        with pytest.raises(HTTPException) as ei:
            await ranking_route.add_ranking_adjustment(
                payload=RankingAjusteCreate(user_id="ghost", period_key="2026", delta=5, reason="x"),
                request=_req(), current_user=admin_user,
            )
        assert ei.value.status_code == 404
        mock_db.ranking_ajustes.insert_one.assert_not_called()

    async def test_add_success_audits_and_notifies(self, mock_db, admin_user, monkeypatch):
        mock_db.users = _coll(find_one_ret={"id": "u9", "name": "Ana"})
        mock_db.ranking_ajustes = _wcoll()
        audit = AsyncMock()
        notif = AsyncMock()
        monkeypatch.setattr(ranking_route, "create_audit_log", audit)
        monkeypatch.setattr(ranking_route, "create_notification", notif)
        res = await ranking_route.add_ranking_adjustment(
            payload=RankingAjusteCreate(user_id="u9", period_key="2026", delta=-3.5, reason="atraso"),
            request=_req(), current_user=admin_user,
        )
        assert res["user_id"] == "u9" and res["delta"] == -3.5 and res["created_by"] == admin_user.id
        mock_db.ranking_ajustes.insert_one.assert_awaited_once()
        assert audit.await_args.kwargs["action"] == "ranking_adjustment_added"
        notif.assert_awaited_once()
        assert notif.await_args.kwargs["user_id"] == "u9"
        assert notif.await_args.kwargs["type"] == "system"

    async def test_list_member_sees_only_own(self, mock_db, socio_user):
        mock_db.ranking_ajustes = _coll(find_list=[{"id": "a1", "user_id": socio_user.id}])
        await ranking_route.list_ranking_adjustments(user_id="alguem_outro", current_user=socio_user)
        q = mock_db.ranking_ajustes.find.call_args.args[0]
        assert q["user_id"] == socio_user.id  # ignora o param, força ao próprio

    async def test_list_manager_filters_by_user_and_period(self, mock_db, admin_user):
        mock_db.ranking_ajustes = _coll(find_list=[])
        await ranking_route.list_ranking_adjustments(user_id="u9", period="2026", current_user=admin_user)
        q = mock_db.ranking_ajustes.find.call_args.args[0]
        assert q == {"user_id": "u9", "period_key": "2026"}


# --------------------------------------------------------------------------- #
# F5 — visibility=direcao_only + opt-out
# --------------------------------------------------------------------------- #


class TestVisibilityAndOptOut:
    async def test_direcao_only_forbids_socio(self, mock_db, socio_user):
        mock_db.member_scores = _coll(count=0, find_list=[], find_one_ret=None)
        mock_db.ranking_settings = _coll(find_one_ret={"visibility": "direcao_only"})
        with pytest.raises(HTTPException) as ei:
            await ranking_route.get_leaderboard(period="2026", current_user=socio_user)
        assert ei.value.status_code == 403

    async def test_direcao_only_allows_admin(self, mock_db, admin_user):
        mock_db.member_scores = _coll(
            count=3, find_list=[{"user_id": "a", "rank": 1, "computed_at": "2026-05-27T00:00:00+00:00"}], find_one_ret=None
        )
        mock_db.ranking_settings = _coll(find_one_ret={"visibility": "direcao_only"})
        res = await ranking_route.get_leaderboard(period="2026", current_user=admin_user)
        assert res["visibility"] == "direcao_only"
        assert res["entries"]  # serviu a lista a um gestor

    async def test_leaderboard_query_excludes_opt_out(self, mock_db, socio_user):
        mock_db.member_scores = _coll(count=0, find_list=[], find_one_ret=None)
        mock_db.ranking_settings = _coll(find_one_ret=None)  # all_members
        await ranking_route.get_leaderboard(period="2026", current_user=socio_user)
        q = mock_db.member_scores.find.call_args.args[0]
        assert q["period_key"] == "2026"
        assert q["ranking_opt_out"] == {"$ne": True}

    async def test_me_returned_even_when_opted_out(self, mock_db, socio_user):
        me_doc = {"user_id": socio_user.id, "rank": 4, "score": 7, "ranking_opt_out": True}
        mock_db.member_scores = _coll(count=0, find_list=[], find_one_ret=me_doc)
        mock_db.ranking_settings = _coll(find_one_ret=None)
        res = await ranking_route.get_leaderboard(period="2026", current_user=socio_user)
        assert res["me"] == me_doc  # o próprio vê sempre a sua posição
        me_q = mock_db.member_scores.find_one.call_args.args[0]
        assert "ranking_opt_out" not in me_q  # a query do `me` não filtra opt-out

    async def test_opt_out_syncs_user_and_snapshot(self, mock_db, socio_user):
        mock_db.users = _wcoll()
        mock_db.member_scores = _wcoll()

        class _R:
            client = type("C", (), {"host": "127.0.0.1"})
            headers = {"User-Agent": "test", "origin": "https://accta.cv"}

        res = await ranking_route.set_ranking_opt_out(
            payload=RankingOptOut(opt_out=True), request=_R(), current_user=socio_user,
        )
        assert res == {"opt_out": True}
        assert mock_db.users.update_one.call_args.args[1]["$set"]["ranking_opt_out"] is True
        # sincroniza o snapshot de imediato (sem esperar rebuild)
        mock_db.member_scores.update_many.assert_awaited_once()
        assert mock_db.member_scores.update_many.call_args.args[0] == {"user_id": socio_user.id}

    async def test_rebuild_denormalizes_opt_out(self, mock_db, monkeypatch):
        mock_db.users = _coll(find_list=[{"id": "a", "name": "Ana", "status": "ativo", "ranking_opt_out": True}])
        mock_db.member_scores = _wcoll()
        mock_db.ranking_settings = _wcoll(find_one_ret=None)
        replace = _wire_replace(monkeypatch)
        monkeypatch.setattr(ranking, "compute_member_score", AsyncMock(return_value={"score": 5, "breakdown": {}}))
        await ranking.rebuild_scores("2026")
        doc = replace.call_args.args[1][0]
        assert doc["ranking_opt_out"] is True
