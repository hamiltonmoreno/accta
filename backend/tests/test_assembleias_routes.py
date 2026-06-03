"""Unit tests para rotas da Assembleia Geral (spec-governanca §11/§18).

Invoca as rotas directamente com mock_db. As colecções de governança não estão
pré-ligadas no conftest — ligam-se aqui com AsyncMock. RBAC, convocatória,
representação (max 3, Mesa não representa), quórum e maiorias.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import asyncpg
import pytest
from fastapi import BackgroundTasks, HTTPException
from pydantic import ValidationError

from routes import assembleias as a_route
from models import (
    Assembleia,
    AssembleiaCreate,
    AssembleiaDeliberacaoCreate,
    AssembleiaFaseUpdate,
    AssembleiaPresencaCreate,
    PalavraRequest,
    User,
)


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

FUTURE = "2030-01-01T10:00:00+00:00"  # bem no futuro → antecedência alta


def _request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


def _cursor(items):
    cur = MagicMock()
    cur.sort.return_value = cur
    cur.skip.return_value = cur
    cur.limit.return_value = cur
    cur.to_list = AsyncMock(return_value=items)
    return cur


def _coll(**methods):
    c = MagicMock()
    c.find_one = AsyncMock(return_value=None)
    c.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    c.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    c.find = MagicMock(return_value=_cursor([]))
    for k, v in methods.items():
        setattr(c, k, v)
    return c


def _mesa_ag(**over) -> User:
    base = {
        "name": "Mesa",
        "email": "mesa@x.cv",
        "role": "socio",
        "status": "ativo",
        "cargo": "ag_presidente",
        "account_type": "member",
        "member_category": "ordinario",
    }
    base.update(over)
    return User(**base)


def _voters(n: int) -> list[dict]:
    return [
        {"id": f"v{i}", "account_type": "member", "status": "ativo", "member_category": "ordinario"} for i in range(n)
    ]


@pytest.fixture
def gov_env(mock_db, monkeypatch):
    mock_db.assembleias = _coll()
    mock_db.assembleia_presencas = _coll()
    mock_db.assembleia_deliberacoes = _coll()
    mock_db.assembleia_palavra = _coll()  # F2 — não pré-ligada no conftest
    # F3 — voto ao vivo (nominal/secreto): não pré-cabladas no conftest
    mock_db.assembleia_votos = _coll()
    mock_db.assembleia_voto_receipts = _coll()
    mock_db.assembleia_voto_ballots = _coll()
    # F4 — moções/requerimentos/recomendações
    mock_db.assembleia_mocoes = _coll()
    # F5 — expediente do antes-OT
    mock_db.assembleia_expediente = _coll()
    # F6 — convidados não-membros
    mock_db.assembleia_convidados = _coll()
    monkeypatch.setattr(a_route, "create_audit_log", AsyncMock())
    monkeypatch.setattr(a_route, "notify_all_active_users", AsyncMock())
    monkeypatch.setattr(a_route, "cast_assembleia_ballot", AsyncMock())
    # Voto nominal passou para DAO helper (TOCTOU fix) — default success.
    monkeypatch.setattr(a_route, "cast_assembleia_nominal_vote", AsyncMock())
    return mock_db


# --------------------------------------------------------------------------- #
# POST /assembleias  (convocar)
# --------------------------------------------------------------------------- #


class TestConvocar:
    async def test_socio_comum_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.create_assembleia(
                request=_request(),
                data=AssembleiaCreate(tipo="ordinaria", titulo="AGO 2030", data=FUTURE, local="Sede"),
                background_tasks=BackgroundTasks(),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_mesa_ag_convoca(self, gov_env):
        gov_env.users.find = MagicMock(return_value=_cursor(_voters(10)))
        captured = {}
        gov_env.assembleias.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await a_route.create_assembleia(
            request=_request(),
            data=AssembleiaCreate(tipo="ordinaria", titulo="AGO 2030", data=FUTURE, local="Sede"),
            background_tasks=BackgroundTasks(),
            current_user=_mesa_ag(),
        )
        assert result["status"] == "convocada"
        assert result["eligible_voters_count"] == 10
        assert result["quorum_required"] == 6  # floor(10/2)+1
        a_route.notify_all_active_users.assert_awaited()

    async def test_admin_convoca(self, gov_env, admin_user):
        gov_env.users.find = MagicMock(return_value=_cursor(_voters(3)))
        result = await a_route.create_assembleia(
            request=_request(),
            data=AssembleiaCreate(tipo="ordinaria", titulo="Reunião", data=FUTURE, local="Sede"),
            background_tasks=BackgroundTasks(),
            current_user=admin_user,
        )
        assert result["eligible_voters_count"] == 3

    async def test_antecedencia_insuficiente_400(self, gov_env):
        with pytest.raises(HTTPException) as exc:
            await a_route.create_assembleia(
                request=_request(),
                data=AssembleiaCreate(
                    tipo="ordinaria", titulo="Reunião", data=FUTURE, local="Sede", antecedencia_dias=5
                ),
                background_tasks=BackgroundTasks(),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_eleitoral_exige_20_dias(self, gov_env):
        gov_env.users.find = MagicMock(return_value=_cursor(_voters(5)))
        with pytest.raises(HTTPException) as exc:
            await a_route.create_assembleia(
                request=_request(),
                data=AssembleiaCreate(
                    tipo="eleitoral", titulo="Eleições", data=FUTURE, local="Sede", antecedencia_dias=15
                ),
                background_tasks=BackgroundTasks(),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_extraordinaria_exige_requerente(self, gov_env):
        gov_env.users.find = MagicMock(return_value=_cursor(_voters(5)))
        with pytest.raises(HTTPException) as exc:
            await a_route.create_assembleia(
                request=_request(),
                data=AssembleiaCreate(tipo="extraordinaria", titulo="AGE", data=FUTURE, local="Sede"),
                background_tasks=BackgroundTasks(),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400


# --------------------------------------------------------------------------- #
# Presenças / representação
# --------------------------------------------------------------------------- #


class TestPresencas:
    def _assembleia(self, **over):
        base = {"id": "a1", "status": "convocada", "quorum_required": 6, "eligible_voters_count": 10}
        base.update(over)
        return base

    async def test_max_3_representados_no_model(self):
        # O próprio modelo impede mais de 3 representados.
        with pytest.raises(ValidationError):
            AssembleiaPresencaCreate(user_id="u1", representados=["a", "b", "c", "d"])

    async def test_mesa_ag_nao_representa(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=self._assembleia())
        gov_env.users.find_one = AsyncMock(
            return_value={
                "id": "u1",
                "account_type": "member",
                "status": "ativo",
                "member_category": "ordinario",
                "cargo": "ag_presidente",
            }
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.register_presenca(
                assembleia_id="a1",
                request=_request(),
                data=AssembleiaPresencaCreate(user_id="u1", representados=["r1"]),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_self_represent_400(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=self._assembleia())
        with pytest.raises(HTTPException) as exc:
            await a_route.register_presenca(
                assembleia_id="a1",
                request=_request(),
                data=AssembleiaPresencaCreate(user_id="u1", representados=["u1"]),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_voting_power_conta_votantes(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=self._assembleia())
        gov_env.users.find_one = AsyncMock(
            return_value={
                "id": "u1",
                "account_type": "member",
                "status": "ativo",
                "member_category": "ordinario",
                "cargo": "socio",
            }
        )
        # 2 representados: 1 votante + 1 honorário (não vota) → power = 1 + 1 = 2
        gov_env.users.find = MagicMock(
            return_value=_cursor(
                [
                    {"id": "r1", "account_type": "member", "status": "ativo", "member_category": "ordinario"},
                    {"id": "r2", "account_type": "member", "status": "ativo", "member_category": "honorario"},
                ]
            )
        )
        captured = {}
        gov_env.assembleia_presencas.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))

        # `find` serve 2 queries: existentes (user_id/representados) e poder de voto.
        def _pres_find(query, proj=None):
            if proj and "voting_power" in proj:
                return _cursor([{"voting_power": 2}])
            return _cursor([])  # sem presenças prévias

        gov_env.assembleia_presencas.find = MagicMock(side_effect=_pres_find)
        result = await a_route.register_presenca(
            assembleia_id="a1",
            request=_request(),
            data=AssembleiaPresencaCreate(user_id="u1", representados=["r1", "r2"]),
            current_user=_mesa_ag(),
        )
        assert captured["voting_power"] == 2
        assert captured["tipo"] == "representacao"
        assert result["present_voting_power"] == 2

    async def test_ja_registado_409(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=self._assembleia())
        gov_env.users.find_one = AsyncMock(
            return_value={
                "id": "u1",
                "account_type": "member",
                "status": "ativo",
                "member_category": "ordinario",
                "cargo": "socio",
            }
        )
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"user_id": "u1", "representados": []}]))
        with pytest.raises(HTTPException) as exc:
            await a_route.register_presenca(
                assembleia_id="a1",
                request=_request(),
                data=AssembleiaPresencaCreate(user_id="u1"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 409


# --------------------------------------------------------------------------- #
# Quórum
# --------------------------------------------------------------------------- #


class TestQuorum:
    async def test_quorum_primeira_e_segunda_chamada(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(
            return_value={"id": "a1", "eligible_voters_count": 10, "quorum_required": 6, "chamada_actual": 1}
        )
        gov_env.assembleia_presencas.find = MagicMock(
            return_value=_cursor([{"voting_power": 2}, {"voting_power": 2}])  # poder = 4
        )
        result = await a_route.get_quorum(assembleia_id="a1", current_user=socio_user)
        assert result["present_voting_power"] == 4
        assert result["quorum_required_primeira"] == 6
        assert result["quorum_required_segunda"] == 4  # ceil(10/3)
        assert result["quorum_met"] is False  # 4 < 6
        assert result["pode_deliberar"] is True  # 4 >= 4


# --------------------------------------------------------------------------- #
# Deliberações
# --------------------------------------------------------------------------- #


class TestDeliberacoes:
    def _assembleia(self, **over):
        base = {"id": "a1", "status": "convocada", "eligible_voters_count": 10}
        base.update(over)
        return base

    async def test_sem_quorum_400(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=self._assembleia())
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 2}]))  # < 4
        with pytest.raises(HTTPException) as exc:
            await a_route.register_deliberacao(
                assembleia_id="a1",
                request=_request(),
                data=AssembleiaDeliberacaoCreate(
                    ponto="1",
                    descricao="Aprovar contas",
                    tipo_maioria="absoluta",
                    votos_favor=2,
                    votos_contra=0,
                    abstencoes=0,
                ),
                background_tasks=BackgroundTasks(),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_contagem_acima_do_poder_presente_400(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=self._assembleia())
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 8}]))
        with pytest.raises(HTTPException) as exc:
            await a_route.register_deliberacao(
                assembleia_id="a1",
                request=_request(),
                data=AssembleiaDeliberacaoCreate(
                    ponto="1",
                    descricao="Aprovar contas",
                    tipo_maioria="absoluta",
                    votos_favor=8,
                    votos_contra=1,
                    abstencoes=0,
                ),
                background_tasks=BackgroundTasks(),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400
        gov_env.assembleia_deliberacoes.insert_one.assert_not_awaited()

    async def test_maioria_absoluta_aprovada(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=self._assembleia())
        # poder presente = 8 → absoluta = floor(8/2)+1 = 5
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 8}]))
        captured = {}
        gov_env.assembleia_deliberacoes.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await a_route.register_deliberacao(
            assembleia_id="a1",
            request=_request(),
            data=AssembleiaDeliberacaoCreate(
                ponto="1",
                descricao="Aprovar contas",
                tipo_maioria="absoluta",
                votos_favor=6,
                votos_contra=2,
                abstencoes=0,
            ),
            background_tasks=BackgroundTasks(),
            current_user=_mesa_ag(),
        )
        assert result["base_calculo"] == 8
        assert result["threshold"] == 5
        assert result["aprovado"] is True

    async def test_tres_quartos_universo_reprovada(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=self._assembleia())
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 8}]))
        captured = {}
        gov_env.assembleia_deliberacoes.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await a_route.register_deliberacao(
            assembleia_id="a1",
            request=_request(),
            data=AssembleiaDeliberacaoCreate(
                ponto="2",
                descricao="Alterar estatutos",
                tipo_maioria="qualificada_3_4_universo",
                votos_favor=6,
                votos_contra=0,
                abstencoes=0,
            ),
            background_tasks=BackgroundTasks(),
            current_user=_mesa_ag(),
        )
        # base = universo (10) → 3/4 = ceil(7.5) = 8; 6 < 8 → reprovada
        assert result["base_calculo"] == 10
        assert result["threshold"] == 8
        assert result["aprovado"] is False

    async def test_dois_tercos_presentes_honorario(self, gov_env):
        # Eleição de membro honorário (Art. 8.4): 2/3 dos presentes — F6.
        gov_env.assembleias.find_one = AsyncMock(return_value=self._assembleia())
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 9}]))
        captured = {}
        gov_env.assembleia_deliberacoes.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await a_route.register_deliberacao(
            assembleia_id="a1",
            request=_request(),
            data=AssembleiaDeliberacaoCreate(
                ponto="3",
                descricao="Eleição de membro honorário",
                tipo_maioria="qualificada_2_3",
                votos_favor=6,
                votos_contra=3,
                abstencoes=0,
                source_article="8.4",
            ),
            background_tasks=BackgroundTasks(),
            current_user=_mesa_ag(),
        )
        # base = presentes (9) → 2/3 = ceil(6.0) = 6; 6 >= 6 → aprovada
        assert result["base_calculo"] == 9
        assert result["threshold"] == 6
        assert result["aprovado"] is True


# --------------------------------------------------------------------------- #
# Camada "ao vivo" (spec-sessao-assembleia-ao-vivo) — F0
# --------------------------------------------------------------------------- #


class TestBumpSession:
    async def test_incrementa_e_aplica_extra(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value={"id": "a1", "session_version": 4})
        captured = {}
        gov_env.assembleias.update_one = AsyncMock(side_effect=lambda flt, upd: captured.update(upd["$set"]))
        v = await a_route._bump_session("a1", {"session_phase": "checkin"})
        assert v == 5
        assert captured["session_version"] == 5
        assert captured["session_phase"] == "checkin"

    async def test_arranca_do_zero(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value={"id": "a1"})  # sem session_version
        gov_env.assembleias.update_one = AsyncMock()
        assert await a_route._bump_session("a1") == 1


class TestSnapshot:
    async def test_reflete_fase_e_quorum(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(
            return_value={
                "id": "a1",
                "session_version": 7,
                "session_phase": "ordem_trabalhos",
                "status": "em_curso",
                "chamada_actual": 1,
                "current_item_id": "ot-3",
                "eligible_voters_count": 10,
            }
        )
        gov_env.assembleia_presencas.find = MagicMock(
            return_value=_cursor([{"voting_power": 4}, {"voting_power": 3}])  # poder = 7
        )
        snap = await a_route._session_snapshot("a1")
        assert snap["version"] == 7
        assert snap["phase"] == "ordem_trabalhos"
        assert snap["chamada"] == 1
        assert snap["current_item_id"] == "ot-3"
        assert snap["quorum"]["present_power"] == 7
        assert snap["quorum"]["required"] == 6  # floor(10/2)+1
        assert snap["quorum"]["met"] is True

    async def test_inexistente_none(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=None)
        assert await a_route._session_snapshot("nope") is None

    async def test_me_present_para_viewer(self, gov_env):
        # Os participantes não vêem /presencas (Mesa-only); o snapshot dá-lhes
        # o próprio estado em `me` para a UI saber se já estão presentes.
        gov_env.assembleias.find_one = AsyncMock(
            return_value={"id": "a1", "session_version": 1, "session_phase": "checkin", "status": "em_curso"}
        )
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 1}]))
        gov_env.assembleia_presencas.find_one = AsyncMock(return_value={"can_vote": True})
        snap = await a_route._session_snapshot("a1", viewer_user_id="v1")
        assert snap["me"] == {"present": True, "can_vote": True}

    async def test_me_ausente_e_anonimo(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(
            return_value={"id": "a1", "session_version": 1, "session_phase": "checkin", "status": "em_curso"}
        )
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([]))
        gov_env.assembleia_presencas.find_one = AsyncMock(return_value=None)
        # viewer não presente → present/can_vote False (não rebenta com None).
        snap_v = await a_route._session_snapshot("a1", viewer_user_id="v9")
        assert snap_v["me"] == {"present": False, "can_vote": False}
        # sem viewer (SSE pré-auth/legado) → me ausente.
        snap_anon = await a_route._session_snapshot("a1")
        assert snap_anon["me"] is None


class TestFase:
    def _assembleia(self, **over):
        base = {
            "id": "a1",
            "status": "convocada",
            "session_phase": "fechada",
            "session_version": 0,
            "eligible_voters_count": 10,
            "chamada_actual": 1,
        }
        base.update(over)
        return base

    async def test_socio_comum_403(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=self._assembleia())
        with pytest.raises(HTTPException) as exc:
            await a_route.transicao_fase(
                assembleia_id="a1",
                request=_request(),
                data=AssembleiaFaseUpdate(session_phase="checkin"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_mesa_avanca_e_marca_em_curso(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=self._assembleia())
        captured = {}
        gov_env.assembleias.update_one = AsyncMock(side_effect=lambda flt, upd: captured.update(upd["$set"]))
        result = await a_route.transicao_fase(
            assembleia_id="a1",
            request=_request(),
            data=AssembleiaFaseUpdate(session_phase="checkin"),
            current_user=_mesa_ag(),
        )
        assert result["session_phase"] == "checkin"
        assert result["session_version"] == 1
        assert result["status"] == "em_curso"
        assert captured["session_phase"] == "checkin"
        assert captured["status"] == "em_curso"
        a_route.create_audit_log.assert_awaited()

    async def test_nao_recua_fase(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(
            return_value=self._assembleia(session_phase="ordem_trabalhos", status="em_curso")
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.transicao_fase(
                assembleia_id="a1",
                request=_request(),
                data=AssembleiaFaseUpdate(session_phase="checkin"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_antes_ot_regista_abertura(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(
            return_value=self._assembleia(session_phase="checkin", status="em_curso")
        )
        captured = {}
        gov_env.assembleias.update_one = AsyncMock(side_effect=lambda flt, upd: captured.update(upd["$set"]))
        await a_route.transicao_fase(
            assembleia_id="a1",
            request=_request(),
            data=AssembleiaFaseUpdate(session_phase="antes_ot"),
            current_user=_mesa_ag(),
        )
        assert captured["session_phase"] == "antes_ot"
        assert "antes_ot_aberto_em" in captured  # limite soft de 30 min (Art. 14)

    async def test_encerrada_400(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=self._assembleia(status="encerrada"))
        with pytest.raises(HTTPException) as exc:
            await a_route.transicao_fase(
                assembleia_id="a1",
                request=_request(),
                data=AssembleiaFaseUpdate(session_phase="checkin"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400


class TestStream:
    async def test_sem_token_401(self, gov_env, monkeypatch):
        monkeypatch.setattr(a_route, "_extract_token", lambda r: None)
        with pytest.raises(HTTPException) as exc:
            await a_route.assembleia_stream(assembleia_id="a1", request=_request())
        assert exc.value.status_code == 401

    async def test_assembleia_inexistente_404(self, gov_env, monkeypatch):
        monkeypatch.setattr(a_route, "_extract_token", lambda r: "tok")
        monkeypatch.setattr(a_route, "get_user_from_token", AsyncMock(return_value=MagicMock(id="u1")))
        gov_env.assembleias.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await a_route.assembleia_stream(assembleia_id="nope", request=_request())
        assert exc.value.status_code == 404

    async def test_token_invalido_401(self, gov_env, monkeypatch):
        # I2 (review F0/F1): token presente mas inválido/expirado/bloquelisted →
        # get_user_from_token devolve None → 401 (não 500 nem ligação aberta).
        monkeypatch.setattr(a_route, "_extract_token", lambda r: "tok")
        monkeypatch.setattr(a_route, "get_user_from_token", AsyncMock(return_value=None))
        with pytest.raises(HTTPException) as exc:
            await a_route.assembleia_stream(assembleia_id="a1", request=_request())
        assert exc.value.status_code == 401

    async def test_emite_snapshot_uma_vez(self, gov_env, monkeypatch):
        monkeypatch.setattr(a_route, "_extract_token", lambda r: "tok")
        monkeypatch.setattr(a_route, "get_user_from_token", AsyncMock(return_value=MagicMock(id="u1")))
        monkeypatch.setattr(a_route.asyncio, "sleep", AsyncMock())  # sem espera real
        doc = {
            "id": "a1",
            "session_version": 3,
            "session_phase": "checkin",
            "status": "em_curso",
            "chamada_actual": 1,
            "current_item_id": None,
            "eligible_voters_count": 4,
        }
        gov_env.assembleias.find_one = AsyncMock(return_value=doc)
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 2}]))

        class _Req:
            def __init__(self):
                self._calls = 0

            async def is_disconnected(self):
                self._calls += 1
                return self._calls > 1  # liga na 1ª iteração, desliga na 2ª

        resp = await a_route.assembleia_stream(assembleia_id="a1", request=_Req())
        chunks = [c async for c in resp.body_iterator]
        assert len(chunks) == 1  # emite uma vez (version mudou de -1 p/ 3)
        assert '"version": 3' in chunks[0]
        assert "checkin" in chunks[0]


# --------------------------------------------------------------------------- #
# F1 — Check-in ao vivo + quórum em tempo real
# --------------------------------------------------------------------------- #


def _sess(**over):
    base = {
        "id": "a1",
        "titulo": "AGO 2030",
        "status": "em_curso",
        "session_phase": "checkin",
        "quorum_required": 6,
        "eligible_voters_count": 10,
        "chamada_actual": 1,
        "session_version": 0,
    }
    base.update(over)
    return base


def _voter_doc(uid, **over):
    base = {"id": uid, "account_type": "member", "status": "ativo", "member_category": "ordinario", "cargo": "socio"}
    base.update(over)
    return base


def _pres_find(existing=None, power=None):
    """side_effect p/ assembleia_presencas.find: distingue a query de existentes
    (user_id/representados) da de poder de voto (voting_power)."""
    existing = existing or []
    power = power or []

    def _f(query, proj=None):
        if proj and "voting_power" in proj:
            return _cursor(power)
        return _cursor(existing)

    return _f


class TestSelfCheckin:
    async def test_fora_de_janela_400(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess(session_phase="fechada"))
        with pytest.raises(HTTPException) as exc:
            await a_route.self_checkin(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaCheckinRequest(),
                current_user=socio_user,
            )
        assert exc.value.status_code == 400

    async def test_self_checkin_ok(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.users.find_one = AsyncMock(return_value=_voter_doc(socio_user.id))
        gov_env.assembleia_presencas.find = MagicMock(side_effect=_pres_find(existing=[], power=[{"voting_power": 1}]))
        captured = {}
        gov_env.assembleia_presencas.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await a_route.self_checkin(
            assembleia_id="a1",
            request=_request(),
            data=a_route.AssembleiaCheckinRequest(method="join_click"),
            current_user=socio_user,
        )
        assert captured["user_id"] == socio_user.id
        assert captured["method"] == "join_click"
        assert captured["can_vote"] is True
        assert captured["voting_power"] == 1
        assert captured["checked_in_at"] is not None
        assert result["present_voting_power"] == 1
        a_route.create_audit_log.assert_awaited()

    async def test_honorario_nao_vota_power_0(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.users.find_one = AsyncMock(return_value=_voter_doc(socio_user.id, member_category="honorario"))
        gov_env.assembleia_presencas.find = MagicMock(side_effect=_pres_find(existing=[], power=[{"voting_power": 0}]))
        captured = {}
        gov_env.assembleia_presencas.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        await a_route.self_checkin(
            assembleia_id="a1",
            request=_request(),
            data=a_route.AssembleiaCheckinRequest(),
            current_user=socio_user,
        )
        assert captured["can_vote"] is False
        assert captured["voting_power"] == 0

    async def test_codigo_invalido_400(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess(check_in_code="ABC123"))
        with pytest.raises(HTTPException) as exc:
            await a_route.self_checkin(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaCheckinRequest(method="self_code", code="WRONG1"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 400

    async def test_codigo_expirado_400(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(
            return_value=_sess(check_in_code="ABC123", check_in_code_expires_at="2000-01-01T00:00:00+00:00")
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.self_checkin(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaCheckinRequest(method="self_code", code="ABC123"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 400

    async def test_ja_presente_409(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.users.find_one = AsyncMock(return_value=_voter_doc(socio_user.id))
        gov_env.assembleia_presencas.find = MagicMock(
            side_effect=_pres_find(existing=[{"user_id": socio_user.id, "representados": []}])
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.self_checkin(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaCheckinRequest(),
                current_user=socio_user,
            )
        assert exc.value.status_code == 409

    async def test_conta_tecnica_400(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.users.find_one = AsyncMock(return_value=_voter_doc(socio_user.id, account_type="technical"))
        with pytest.raises(HTTPException) as exc:
            await a_route.self_checkin(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaCheckinRequest(),
                current_user=socio_user,
            )
        assert exc.value.status_code == 400


class TestCheckinScan:
    async def test_socio_comum_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.checkin_scan(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaCheckinScan(qr_hash="hash-1234"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_resolve_user_por_qr(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.users.find_one = AsyncMock(return_value=_voter_doc("scanned1"))
        gov_env.assembleia_presencas.find = MagicMock(side_effect=_pres_find(existing=[], power=[{"voting_power": 1}]))
        captured = {}
        gov_env.assembleia_presencas.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await a_route.checkin_scan(
            assembleia_id="a1",
            request=_request(),
            data=a_route.AssembleiaCheckinScan(qr_hash="hash-1234"),
            current_user=_mesa_ag(),
        )
        assert captured["user_id"] == "scanned1"
        assert captured["method"] == "qr_scan"
        assert result["present_voting_power"] == 1

    async def test_qr_desconhecido_404(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await a_route.checkin_scan(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaCheckinScan(qr_hash="hash-xxxx"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 404

    async def test_fora_de_janela_400(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess(session_phase="fechada"))
        with pytest.raises(HTTPException) as exc:
            await a_route.checkin_scan(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaCheckinScan(qr_hash="hash-1234"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400


class TestAbrirFecharCheckin:
    async def test_socio_comum_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.abrir_checkin(assembleia_id="a1", request=_request(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_abrir_gera_codigo_e_marca_em_curso(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess(status="convocada", session_phase="fechada"))
        captured = {}
        gov_env.assembleias.update_one = AsyncMock(side_effect=lambda flt, upd: captured.update(upd["$set"]))
        result = await a_route.abrir_checkin(assembleia_id="a1", request=_request(), current_user=_mesa_ag())
        assert len(result["check_in_code"]) == 6
        assert result["session_phase"] == "checkin"
        assert captured["check_in_code"] == result["check_in_code"]
        assert captured["session_phase"] == "checkin"
        assert captured["status"] == "em_curso"
        a_route.notify_all_active_users.assert_awaited()

    async def test_fechar_invalida_codigo(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess(check_in_code="ABC123"))
        captured = {}
        gov_env.assembleias.update_one = AsyncMock(side_effect=lambda flt, upd: captured.update(upd["$set"]))
        await a_route.fechar_checkin(assembleia_id="a1", request=_request(), current_user=_mesa_ag())
        assert captured["check_in_code"] is None
        assert captured["check_in_code_expires_at"] is None


class TestSegundaConvocatoria:
    async def test_socio_comum_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.segunda_convocatoria(assembleia_id="a1", request=_request(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_recalcula_quorum_um_terco(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess(eligible_voters_count=10))
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 4}]))
        captured = {}
        gov_env.assembleias.update_one = AsyncMock(side_effect=lambda flt, upd: captured.update(upd["$set"]))
        result = await a_route.segunda_convocatoria(assembleia_id="a1", request=_request(), current_user=_mesa_ag())
        assert result["chamada_actual"] == 2
        assert result["quorum_required"] == 4  # ceil(10/3)
        assert result["quorum_met"] is True  # poder 4 >= 4
        assert captured["chamada_actual"] == 2

    async def test_ja_em_segunda_400(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess(chamada_actual=2))
        with pytest.raises(HTTPException) as exc:
            await a_route.segunda_convocatoria(assembleia_id="a1", request=_request(), current_user=_mesa_ag())
        assert exc.value.status_code == 400


class TestListPresencas:
    async def test_socio_comum_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.list_presencas(assembleia_id="a1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_mesa_lista(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"user_id": "u1", "method": "join_click"}]))
        result = await a_route.list_presencas(assembleia_id="a1", current_user=_mesa_ag())
        assert len(result["presencas"]) == 1
        assert result["presencas"][0]["method"] == "join_click"


# --------------------------------------------------------------------------- #
# F2 — Fila de uso da palavra
# --------------------------------------------------------------------------- #


def _palavra(**over):
    base = {
        "id": "q1",
        "assembleia_id": "a1",
        "user_id": "u1",
        "tipo": "intervencao",
        "status": "inscrito",
        "duration_limit_s": 180,
        "requested_at": "2030-01-01T10:00:00+00:00",
    }
    base.update(over)
    return base


class TestPedirPalavra:
    async def test_presente_pede(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_presencas.find_one = AsyncMock(return_value={"id": "p1"})  # presente
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value=None)  # sem pedido activo
        captured = {}
        gov_env.assembleia_palavra.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await a_route.pedir_palavra(
            assembleia_id="a1",
            request=_request(),
            data=a_route.PalavraCreate(tipo="intervencao"),
            current_user=socio_user,
        )
        assert captured["user_id"] == socio_user.id
        assert captured["tipo"] == "intervencao"
        assert captured["duration_limit_s"] == 180
        assert result["status"] == "inscrito"

    async def test_protesto_duracao_60(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_presencas.find_one = AsyncMock(return_value={"id": "p1"})
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value=None)
        captured = {}
        gov_env.assembleia_palavra.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        await a_route.pedir_palavra(
            assembleia_id="a1",
            request=_request(),
            data=a_route.PalavraCreate(tipo="protesto"),
            current_user=socio_user,
        )
        assert captured["duration_limit_s"] == 60

    async def test_nao_presente_403(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_presencas.find_one = AsyncMock(return_value=None)  # ausente
        with pytest.raises(HTTPException) as exc:
            await a_route.pedir_palavra(
                assembleia_id="a1",
                request=_request(),
                data=a_route.PalavraCreate(),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_sessao_nao_em_curso_400(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess(status="convocada"))
        with pytest.raises(HTTPException) as exc:
            await a_route.pedir_palavra(
                assembleia_id="a1",
                request=_request(),
                data=a_route.PalavraCreate(),
                current_user=socio_user,
            )
        assert exc.value.status_code == 400

    async def test_pedido_duplicado_409(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_presencas.find_one = AsyncMock(return_value={"id": "p1"})
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value={"id": "q0"})  # já tem activo
        with pytest.raises(HTTPException) as exc:
            await a_route.pedir_palavra(
                assembleia_id="a1",
                request=_request(),
                data=a_route.PalavraCreate(),
                current_user=socio_user,
            )
        assert exc.value.status_code == 409


class TestRetirarPalavra:
    async def test_owner_retira(self, gov_env, socio_user):
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value=_palavra(user_id=socio_user.id))
        result = await a_route.retirar_palavra(
            assembleia_id="a1", qid="q1", request=_request(), current_user=socio_user
        )
        assert result["status"] == "retirado"

    async def test_outro_socio_403(self, gov_env, socio_user):
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value=_palavra(user_id="outro"))
        with pytest.raises(HTTPException) as exc:
            await a_route.retirar_palavra(assembleia_id="a1", qid="q1", request=_request(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_mesa_retira_qualquer(self, gov_env):
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value=_palavra(user_id="outro"))
        result = await a_route.retirar_palavra(
            assembleia_id="a1", qid="q1", request=_request(), current_user=_mesa_ag()
        )
        assert result["status"] == "retirado"

    async def test_ja_concluido_400(self, gov_env, socio_user):
        gov_env.assembleia_palavra.find_one = AsyncMock(
            return_value=_palavra(user_id=socio_user.id, status="concluido")
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.retirar_palavra(assembleia_id="a1", qid="q1", request=_request(), current_user=socio_user)
        assert exc.value.status_code == 400


class TestOrdenarPalavra:
    async def test_socio_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.ordenar_palavra(
                assembleia_id="a1",
                qid="q1",
                request=_request(),
                data=a_route.PalavraOrdenar(ordem=1),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_mesa_ordena(self, gov_env):
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value=_palavra())
        captured = {}
        gov_env.assembleia_palavra.update_one = AsyncMock(side_effect=lambda flt, upd: captured.update(upd["$set"]))
        result = await a_route.ordenar_palavra(
            assembleia_id="a1",
            qid="q1",
            request=_request(),
            data=a_route.PalavraOrdenar(ordem=3),
            current_user=_mesa_ag(),
        )
        assert result["ordem"] == 3
        assert captured["ordem"] == 3


class TestIniciarPalavra:
    async def test_socio_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.iniciar_palavra(
                assembleia_id="a1",
                qid="q1",
                request=_request(),
                data=a_route.PalavraIniciar(),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_mesa_inicia_arranca_cronometro(self, gov_env):
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value=_palavra())
        captured = {}
        gov_env.assembleia_palavra.update_one = AsyncMock(side_effect=lambda flt, upd: captured.update(upd["$set"]))
        result = await a_route.iniciar_palavra(
            assembleia_id="a1",
            qid="q1",
            request=_request(),
            data=a_route.PalavraIniciar(),
            current_user=_mesa_ag(),
        )
        assert result["status"] == "a_falar"
        assert result["ends_at"] is not None
        assert result["started_at"] is not None
        assert captured["duration_limit_s"] == 180

    async def test_override_duracao(self, gov_env):
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value=_palavra())
        captured = {}
        gov_env.assembleia_palavra.update_one = AsyncMock(side_effect=lambda flt, upd: captured.update(upd["$set"]))
        await a_route.iniciar_palavra(
            assembleia_id="a1",
            qid="q1",
            request=_request(),
            data=a_route.PalavraIniciar(duration_s=60),
            current_user=_mesa_ag(),
        )
        assert captured["duration_limit_s"] == 60

    async def test_ja_concluido_400(self, gov_env):
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value=_palavra(status="concluido"))
        with pytest.raises(HTTPException) as exc:
            await a_route.iniciar_palavra(
                assembleia_id="a1",
                qid="q1",
                request=_request(),
                data=a_route.PalavraIniciar(),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400


class TestTerminarPalavra:
    async def test_mesa_termina(self, gov_env):
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value=_palavra(status="a_falar"))
        result = await a_route.terminar_palavra(
            assembleia_id="a1", qid="q1", request=_request(), current_user=_mesa_ag()
        )
        assert result["status"] == "concluido"
        assert result["ended_at"] is not None

    async def test_nao_a_falar_400(self, gov_env):
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value=_palavra(status="inscrito"))
        with pytest.raises(HTTPException) as exc:
            await a_route.terminar_palavra(assembleia_id="a1", qid="q1", request=_request(), current_user=_mesa_ag())
        assert exc.value.status_code == 400

    async def test_socio_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.terminar_palavra(assembleia_id="a1", qid="q1", request=_request(), current_user=socio_user)
        assert exc.value.status_code == 403


class TestListPalavra:
    async def test_lista_ordenada_por_ordem(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_palavra.find = MagicMock(
            return_value=_cursor(
                [
                    {"id": "a", "ordem": 2, "requested_at": "t1"},
                    {"id": "b", "ordem": 1, "requested_at": "t2"},
                    {"id": "c", "ordem": None, "requested_at": "t0"},
                ]
            )
        )
        result = await a_route.list_palavra(assembleia_id="a1", current_user=socio_user)
        assert [r["id"] for r in result["palavra"]] == ["b", "a", "c"]


# --------------------------------------------------------------------------- #
# F3 — Modos de voto + conflito + voto separado (spec §7)
# --------------------------------------------------------------------------- #


def _delib(**over):
    """Doc de uma deliberação aberta (ciclo F3)."""
    base = {
        "id": "d1",
        "assembleia_id": "a1",
        "ponto": "P1",
        "descricao": "Aprovar X",
        "tipo_maioria": "absoluta",
        "voting_mode": "nominal",
        "status": "aberta",
        "conflitos_excluidos": [],
        "votos_favor": 0,
        "votos_contra": 0,
        "abstencoes": 0,
    }
    base.update(over)
    return base


def _pres_rows(rows):
    """Side-effect para assembleia_presencas.find: devolve sempre `rows`
    (a projecção varia mas os campos relevantes existem)."""

    def _f(query, proj=None):
        return _cursor(rows)

    return _f


class TestAbrirDeliberacao:
    async def test_socio_comum_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.abrir_deliberacao(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaDeliberacaoAbrir(ponto="P1", descricao="Aprovar X"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_sessao_nao_em_curso_400(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess(status="convocada"))
        with pytest.raises(HTTPException) as exc:
            await a_route.abrir_deliberacao(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaDeliberacaoAbrir(ponto="P1", descricao="Aprovar X"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_sem_quorum_400(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        # eligible=10 → 2.ª chamada = ceil(10/3)=4; poder presente 2 < 4 → bloqueia.
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 2}]))
        with pytest.raises(HTTPException) as exc:
            await a_route.abrir_deliberacao(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaDeliberacaoAbrir(ponto="P1", descricao="Aprovar X"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400
        gov_env.assembleia_deliberacoes.insert_one.assert_not_awaited()

    async def test_mesa_abre_status_aberta(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 6}]))
        captured = {}
        gov_env.assembleia_deliberacoes.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await a_route.abrir_deliberacao(
            assembleia_id="a1",
            request=_request(),
            data=a_route.AssembleiaDeliberacaoAbrir(
                ponto="P1",
                descricao="Aprovar X",
                voting_mode="nominal",
                conflitos_excluidos=["u9"],
                subitem="a",
            ),
            current_user=_mesa_ag(),
        )
        assert captured["status"] == "aberta"
        assert captured["voting_mode"] == "nominal"
        assert captured["conflitos_excluidos"] == ["u9"]
        assert captured["subitem"] == "a"
        assert result["status"] == "aberta"

    async def test_voto_separado_duas_deliberacoes(self, gov_env):
        # Voto separado: o mesmo `ponto` aceita várias deliberações (subitens
        # diferentes); o ciclo de abrir não impõe unicidade por ponto.
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 6}]))
        inserted = []
        gov_env.assembleia_deliberacoes.insert_one = AsyncMock(side_effect=lambda d: inserted.append(d))
        for sub in ("a", "b"):
            await a_route.abrir_deliberacao(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaDeliberacaoAbrir(ponto="P1", descricao="X", subitem=sub),
                current_user=_mesa_ag(),
            )
        assert {d["subitem"] for d in inserted} == {"a", "b"}
        assert all(d["ponto"] == "P1" and d["status"] == "aberta" for d in inserted)


class TestVotarNominal:
    async def _setup(self, gov_env, *, presence=None, conflitos=None):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(
            return_value=_delib(voting_mode="nominal", conflitos_excluidos=conflitos or [])
        )
        gov_env.assembleia_presencas.find_one = AsyncMock(return_value=presence)
        gov_env.assembleia_votos.find_one = AsyncMock(return_value=None)

    async def test_nao_presente_403(self, gov_env, socio_user):
        await self._setup(gov_env, presence=None)
        with pytest.raises(HTTPException) as exc:
            await a_route.votar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaVotoCast(escolha="favor"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_sem_direito_voto_403(self, gov_env, socio_user):
        await self._setup(gov_env, presence={"can_vote": False})
        with pytest.raises(HTTPException) as exc:
            await a_route.votar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaVotoCast(escolha="favor"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_excluido_por_conflito_403(self, gov_env, socio_user):
        await self._setup(gov_env, presence={"can_vote": True}, conflitos=[socio_user.id])
        with pytest.raises(HTTPException) as exc:
            await a_route.votar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaVotoCast(escolha="favor"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_braco_no_ar_400(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(return_value=_delib(voting_mode="braco_no_ar"))
        with pytest.raises(HTTPException) as exc:
            await a_route.votar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaVotoCast(escolha="favor"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 400

    async def test_voto_duplicado_409(self, gov_env, socio_user, monkeypatch):
        await self._setup(gov_env, presence={"can_vote": True})
        monkeypatch.setattr(
            a_route, "cast_assembleia_nominal_vote",
            AsyncMock(side_effect=ValueError("duplicate")),
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.votar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaVotoCast(escolha="favor"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 409

    async def test_helper_not_open_400(self, gov_env, socio_user, monkeypatch):
        # Race TOCTOU: o status-check de fast-path passa (status="aberta" no
        # find_one outer), mas o helper DAO, sob lock, vê a deliberação já
        # encerrada por `apurar`. Tem de devolver 400, não 5xx.
        await self._setup(gov_env, presence={"can_vote": True})
        monkeypatch.setattr(
            a_route, "cast_assembleia_nominal_vote",
            AsyncMock(side_effect=ValueError("not_open")),
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.votar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaVotoCast(escolha="favor"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 400
        # Não escreve audit em rejeição (vote nunca aconteceu).
        a_route.create_audit_log.assert_not_awaited()

    async def test_helper_not_found_404(self, gov_env, socio_user, monkeypatch):
        await self._setup(gov_env, presence={"can_vote": True})
        monkeypatch.setattr(
            a_route, "cast_assembleia_nominal_vote",
            AsyncMock(side_effect=ValueError("not_found")),
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.votar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaVotoCast(escolha="favor"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 404

    async def test_lock_timeout_503(self, gov_env, socio_user, monkeypatch):
        await self._setup(gov_env, presence={"can_vote": True})
        monkeypatch.setattr(
            a_route, "cast_assembleia_nominal_vote",
            AsyncMock(side_effect=asyncpg.exceptions.LockNotAvailableError()),
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.votar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaVotoCast(escolha="favor"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 503

    async def test_unique_violation_409_belt_and_braces(self, gov_env, socio_user, monkeypatch):
        # Mesmo se o helper falhasse o check in-tx, o índice único do schema
        # (ux_assembvoto_delib_user) ainda salvaguarda → 409.
        await self._setup(gov_env, presence={"can_vote": True})
        monkeypatch.setattr(
            a_route, "cast_assembleia_nominal_vote",
            AsyncMock(side_effect=asyncpg.UniqueViolationError()),
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.votar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaVotoCast(escolha="favor"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 409

    async def test_voto_registado_e_audita_escolha(self, gov_env, socio_user, monkeypatch):
        await self._setup(gov_env, presence={"can_vote": True})
        captured = {}

        async def _fake_cast(did, user_id, voto_doc):
            captured.update({"did": did, "user_id": user_id, **voto_doc})

        monkeypatch.setattr(a_route, "cast_assembleia_nominal_vote", _fake_cast)
        result = await a_route.votar_deliberacao(
            assembleia_id="a1",
            did="d1",
            request=_request(),
            data=a_route.AssembleiaVotoCast(escolha="favor"),
            current_user=socio_user,
        )
        assert captured["user_id"] == socio_user.id
        assert captured["escolha"] == "favor"
        assert captured["did"] == "d1"
        assert result["status"] == "registado"
        # Nominal: a auditoria inclui o sentido do voto (atribuível).
        a_route.create_audit_log.assert_awaited()
        last_call = a_route.create_audit_log.await_args
        assert last_call.kwargs["details"]["escolha"] == "favor"


class TestVotarSecreto:
    async def _setup(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(return_value=_delib(voting_mode="secreto"))
        gov_env.assembleia_presencas.find_one = AsyncMock(return_value={"can_vote": True})

    async def test_boletim_sem_user_id_e_recibo_com_hash(self, gov_env, socio_user, monkeypatch):
        await self._setup(gov_env)
        captured = {}

        async def _fake_cast(did, vh, receipt, ballot):
            captured.update({"did": did, "vh": vh, "receipt": receipt, "ballot": ballot})

        monkeypatch.setattr(a_route, "cast_assembleia_ballot", _fake_cast)
        await a_route.votar_deliberacao(
            assembleia_id="a1",
            did="d1",
            request=_request(),
            data=a_route.AssembleiaVotoCast(escolha="contra"),
            current_user=socio_user,
        )
        assert "user_id" not in captured["ballot"]
        assert "voter_hash" not in captured["ballot"]
        assert captured["ballot"]["escolha"] == "contra"
        assert captured["receipt"]["voter_hash"] == captured["vh"]
        assert "user_id" not in captured["receipt"]
        assert len(captured["vh"]) == 64  # SHA-256 hex

    async def test_voto_duplicado_409(self, gov_env, socio_user, monkeypatch):
        await self._setup(gov_env)
        monkeypatch.setattr(
            a_route, "cast_assembleia_ballot",
            AsyncMock(side_effect=ValueError("duplicate")),
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.votar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaVotoCast(escolha="favor"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 409

    async def test_helper_not_open_400(self, gov_env, socio_user, monkeypatch):
        # Secreto: mesma race que nominal. O helper DAO, sob lock, recusa.
        await self._setup(gov_env)
        monkeypatch.setattr(
            a_route, "cast_assembleia_ballot",
            AsyncMock(side_effect=ValueError("not_open")),
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.votar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaVotoCast(escolha="favor"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 400
        a_route.create_audit_log.assert_not_awaited()

    async def test_helper_not_found_404(self, gov_env, socio_user, monkeypatch):
        await self._setup(gov_env)
        monkeypatch.setattr(
            a_route, "cast_assembleia_ballot",
            AsyncMock(side_effect=ValueError("not_found")),
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.votar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaVotoCast(escolha="favor"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 404

    async def test_lock_timeout_503(self, gov_env, socio_user, monkeypatch):
        await self._setup(gov_env)
        monkeypatch.setattr(
            a_route, "cast_assembleia_ballot",
            AsyncMock(side_effect=asyncpg.exceptions.LockNotAvailableError()),
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.votar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaVotoCast(escolha="favor"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 503

    async def test_audit_nao_inclui_escolha(self, gov_env, socio_user):
        await self._setup(gov_env)
        await a_route.votar_deliberacao(
            assembleia_id="a1",
            did="d1",
            request=_request(),
            data=a_route.AssembleiaVotoCast(escolha="favor"),
            current_user=socio_user,
        )
        a_route.create_audit_log.assert_awaited()
        last_call = a_route.create_audit_log.await_args
        # Secreto: nunca ligar sentido↔eleitor (nem via audit).
        assert "escolha" not in last_call.kwargs["details"]
        assert last_call.args[1] == "assembleia_voto_secreto"


class TestRegistarContagem:
    async def test_socio_comum_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.registar_contagem(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaContagem(votos_favor=1, votos_contra=0, abstencoes=0),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_modo_errado_400(self, gov_env):
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(return_value=_delib(voting_mode="nominal"))
        with pytest.raises(HTTPException) as exc:
            await a_route.registar_contagem(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaContagem(votos_favor=1, votos_contra=0, abstencoes=0),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_excede_base_400(self, gov_env):
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(return_value=_delib(voting_mode="braco_no_ar"))
        # base = present_power=2 - excluded_power=0 = 2; total 3 > 2.
        gov_env.assembleia_presencas.find = MagicMock(side_effect=_pres_rows([{"user_id": "u1", "voting_power": 2}]))
        with pytest.raises(HTTPException) as exc:
            await a_route.registar_contagem(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaContagem(votos_favor=2, votos_contra=1, abstencoes=0),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_mesa_regista(self, gov_env):
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(return_value=_delib(voting_mode="braco_no_ar"))
        gov_env.assembleia_presencas.find = MagicMock(side_effect=_pres_rows([{"user_id": "u1", "voting_power": 5}]))
        captured = {}
        gov_env.assembleia_deliberacoes.update_one = AsyncMock(side_effect=_capturing_update(captured))
        result = await a_route.registar_contagem(
            assembleia_id="a1",
            did="d1",
            request=_request(),
            data=a_route.AssembleiaContagem(votos_favor=3, votos_contra=1, abstencoes=1),
            current_user=_mesa_ag(),
        )
        assert captured == {"votos_favor": 3, "votos_contra": 1, "abstencoes": 1}
        assert result["votos_favor"] == 3

    async def test_409_se_encerrada(self, gov_env):
        # CAS: se a deliberação já foi apurada entre o find_one e o update_one,
        # o filtro status="aberta" impede a sobrescrita e devolvemos 409.
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(return_value=_delib(voting_mode="braco_no_ar"))
        gov_env.assembleia_presencas.find = MagicMock(side_effect=_pres_rows([{"user_id": "u1", "voting_power": 5}]))
        gov_env.assembleia_deliberacoes.update_one = AsyncMock(return_value=MagicMock(modified_count=0))
        with pytest.raises(HTTPException) as exc:
            await a_route.registar_contagem(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                data=a_route.AssembleiaContagem(votos_favor=1, votos_contra=0, abstencoes=0),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 409


def _capturing_update(captured):
    """side_effect p/ `update_one` que capta o `$set` e devolve um resultado com
    `modified_count=1` — o pre-close (CAS) do apurar lê `result.modified_count`
    directamente, por isso o mock tem de o expor (não pode devolver None)."""

    def _f(flt, upd):
        captured.update(upd["$set"])
        return MagicMock(modified_count=1)

    return _f


class TestApurar:
    async def test_socio_comum_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.apurar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                background_tasks=BackgroundTasks(),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_nao_aberta_400(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(return_value=_delib(status="encerrada"))
        with pytest.raises(HTTPException) as exc:
            await a_route.apurar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                background_tasks=BackgroundTasks(),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_nominal_pondera_pelo_voting_power(self, gov_env):
        # u1 (power 3, favor) + u2 (power 2, favor) + u3 (power 1, contra, excluído).
        # base = 6 - 1 = 5; favor ponderado = 5; absoluta → threshold = floor(5/2)+1 = 3 → aprovado.
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(
            return_value=_delib(voting_mode="nominal", conflitos_excluidos=["u3"])
        )
        gov_env.assembleia_presencas.find = MagicMock(
            side_effect=_pres_rows(
                [
                    {"user_id": "u1", "voting_power": 3, "can_vote": True},
                    {"user_id": "u2", "voting_power": 2, "can_vote": True},
                    {"user_id": "u3", "voting_power": 1, "can_vote": True},
                ]
            )
        )
        gov_env.assembleia_votos.find = MagicMock(
            return_value=_cursor(
                [
                    {"user_id": "u1", "escolha": "favor"},
                    {"user_id": "u2", "escolha": "favor"},
                ]
            )
        )
        captured = {}
        gov_env.assembleia_deliberacoes.update_one = AsyncMock(side_effect=_capturing_update(captured))
        bg = BackgroundTasks()
        result = await a_route.apurar_deliberacao(
            assembleia_id="a1",
            did="d1",
            request=_request(),
            background_tasks=bg,
            current_user=_mesa_ag(),
        )
        assert captured["base_calculo"] == 5  # excluído sai da base
        assert captured["votos_favor"] == 5  # ponderado pelo voting_power
        assert captured["threshold"] == 3
        assert captured["aprovado"] is True
        assert captured["status"] == "encerrada"
        assert result["apurado_em"]
        # Comunicado oficial dispara UMA vez no apurar.
        assert len(bg.tasks) == 1

    async def test_secreto_headcount_um_membro_um_boletim(self, gov_env):
        # 4 votantes presentes; 1 excluído; base = 3 (headcount, não power).
        # Boletins: 2 favor, 1 abstencao; absoluta → threshold = floor(3/2)+1 = 2 → aprovado.
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(
            return_value=_delib(voting_mode="secreto", conflitos_excluidos=["u4"])
        )
        gov_env.assembleia_presencas.find = MagicMock(
            side_effect=_pres_rows(
                [
                    {"user_id": "u1", "voting_power": 1, "can_vote": True},
                    {"user_id": "u2", "voting_power": 1, "can_vote": True},
                    {"user_id": "u3", "voting_power": 1, "can_vote": True},
                    {"user_id": "u4", "voting_power": 1, "can_vote": True},  # excluído
                ]
            )
        )
        gov_env.assembleia_voto_ballots.find = MagicMock(
            return_value=_cursor(
                [{"escolha": "favor"}, {"escolha": "favor"}, {"escolha": "abstencao"}]
            )
        )
        captured = {}
        gov_env.assembleia_deliberacoes.update_one = AsyncMock(side_effect=_capturing_update(captured))
        await a_route.apurar_deliberacao(
            assembleia_id="a1",
            did="d1",
            request=_request(),
            background_tasks=BackgroundTasks(),
            current_user=_mesa_ag(),
        )
        assert captured["base_calculo"] == 3
        assert captured["votos_favor"] == 2  # cada boletim = 1, sem pesos
        assert captured["abstencoes"] == 1
        assert captured["threshold"] == 2
        assert captured["aprovado"] is True

    async def test_braco_no_ar_usa_agregado_registado(self, gov_env):
        # Mesa registou 4-1-0; base com excluído u9 (power 2) tira 2 → 6.
        # absoluta → threshold = floor(6/2)+1 = 4; favor 4 >= 4 → aprovado.
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(
            return_value=_delib(
                voting_mode="braco_no_ar",
                conflitos_excluidos=["u9"],
                votos_favor=4,
                votos_contra=1,
                abstencoes=0,
            )
        )
        gov_env.assembleia_presencas.find = MagicMock(
            side_effect=_pres_rows(
                [
                    {"user_id": "u1", "voting_power": 6, "can_vote": True},
                    {"user_id": "u9", "voting_power": 2, "can_vote": True},
                ]
            )
        )
        captured = {}
        gov_env.assembleia_deliberacoes.update_one = AsyncMock(side_effect=_capturing_update(captured))
        await a_route.apurar_deliberacao(
            assembleia_id="a1",
            did="d1",
            request=_request(),
            background_tasks=BackgroundTasks(),
            current_user=_mesa_ag(),
        )
        assert captured["base_calculo"] == 6  # 8 - 2 excluído
        assert captured["votos_favor"] == 4
        assert captured["aprovado"] is True

    async def test_apurar_concorrente_devolve_409(self, gov_env):
        # CAS: o pre-close fecha a janela com WHERE status="aberta". Se outra
        # sessão da Mesa já fechou (modified_count=0), apurar é idempotente → 409
        # em vez de re-apurar/re-disparar comunicado.
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(return_value=_delib(voting_mode="nominal"))
        gov_env.assembleia_deliberacoes.update_one = AsyncMock(return_value=MagicMock(modified_count=0))
        bg = BackgroundTasks()
        with pytest.raises(HTTPException) as exc:
            await a_route.apurar_deliberacao(
                assembleia_id="a1",
                did="d1",
                request=_request(),
                background_tasks=bg,
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 409
        assert len(bg.tasks) == 0  # nenhum comunicado disparado

    async def test_base_zero_nao_aprova(self, gov_env):
        # qualificada_3_4_presentes com o único votante presente excluído por
        # conflito → base=0 e threshold=0. `favor>=threshold` (0>=0) aprovaria
        # com zero votos; a guarda `base>0` impede a falsa aprovação.
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(
            return_value=_delib(
                voting_mode="nominal",
                tipo_maioria="qualificada_3_4_presentes",
                conflitos_excluidos=["u1"],
            )
        )
        gov_env.assembleia_presencas.find = MagicMock(
            side_effect=_pres_rows([{"user_id": "u1", "voting_power": 3, "can_vote": True}])
        )
        gov_env.assembleia_votos.find = MagicMock(return_value=_cursor([]))
        captured = {}
        gov_env.assembleia_deliberacoes.update_one = AsyncMock(side_effect=_capturing_update(captured))
        await a_route.apurar_deliberacao(
            assembleia_id="a1",
            did="d1",
            request=_request(),
            background_tasks=BackgroundTasks(),
            current_user=_mesa_ag(),
        )
        assert captured["base_calculo"] == 0
        assert captured["aprovado"] is False


class TestGetDeliberacao:
    async def test_nominal_mesa_ve_votos_socio_so_count(self, gov_env, socio_user):
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(return_value=_delib(voting_mode="nominal"))
        gov_env.assembleia_votos.find = MagicMock(
            return_value=_cursor([{"user_id": "u1", "escolha": "favor"}, {"user_id": "u2", "escolha": "contra"}])
        )
        # Mesa vê a lista nominal.
        mesa_view = await a_route.get_deliberacao(assembleia_id="a1", did="d1", current_user=_mesa_ag())
        assert mesa_view["votes_cast"] == 2
        assert len(mesa_view["votos"]) == 2

        # Sócio vê só a contagem (não-Mesa não recebe a lista nominal).
        gov_env.assembleia_votos.find = MagicMock(
            return_value=_cursor([{"user_id": "u1", "escolha": "favor"}, {"user_id": "u2", "escolha": "contra"}])
        )
        socio_view = await a_route.get_deliberacao(assembleia_id="a1", did="d1", current_user=socio_user)
        assert socio_view["votes_cast"] == 2
        assert "votos" not in socio_view

    async def test_secreto_nunca_expoe_boletins(self, gov_env, socio_user):
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(return_value=_delib(voting_mode="secreto"))
        gov_env.assembleia_voto_receipts.find = MagicMock(return_value=_cursor([{"id": "r1"}, {"id": "r2"}]))
        view = await a_route.get_deliberacao(assembleia_id="a1", did="d1", current_user=_mesa_ag())
        assert view["votes_cast"] == 2
        # Secreto: NUNCA expõe a escolha por eleitor — mesmo à Mesa.
        assert "votos" not in view
        assert "ballots" not in view


# --------------------------------------------------------------------------- #
# Review F0/F1 — remediação (I1 corrida UNIQUE, I4 leak de check_in_code)
# --------------------------------------------------------------------------- #


class TestCheckinRaceUnique:
    async def test_corrida_unique_devolve_409(self, gov_env, socio_user):
        # I1: dois check-ins simultâneos do mesmo sócio passam a guarda aplicacional;
        # o índice UNIQUE rejeita o segundo e o handler traduz para 409 limpo.
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.users.find_one = AsyncMock(return_value=_voter_doc(socio_user.id))
        gov_env.assembleia_presencas.find = MagicMock(side_effect=_pres_find(existing=[], power=[{"voting_power": 1}]))
        gov_env.assembleia_presencas.insert_one = AsyncMock(side_effect=asyncpg.UniqueViolationError("duplicate"))
        with pytest.raises(HTTPException) as exc:
            await a_route.self_checkin(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaCheckinRequest(),
                current_user=socio_user,
            )
        assert exc.value.status_code == 409


class TestGetAssembleiaLeak:
    async def test_socio_nao_ve_check_in_code(self, gov_env, socio_user):
        # I4: expor `check_in_code` a qualquer autenticado anula o mecanismo anti-proxy.
        gov_env.assembleias.find_one = AsyncMock(
            return_value={
                "id": "a1",
                "check_in_code": "ABC123",
                "check_in_code_expires_at": "2099-01-01T00:00:00+00:00",
                "titulo": "AGO",
            }
        )
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([]))
        out = await a_route.get_assembleia(assembleia_id="a1", current_user=socio_user)
        assert "check_in_code" not in out
        assert "check_in_code_expires_at" not in out
        assert out["titulo"] == "AGO"

    async def test_mesa_ve_check_in_code(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(
            return_value={
                "id": "a1",
                "check_in_code": "ABC123",
                "check_in_code_expires_at": "2099-01-01T00:00:00+00:00",
                "titulo": "AGO",
            }
        )
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([]))
        out = await a_route.get_assembleia(assembleia_id="a1", current_user=_mesa_ag())
        assert out["check_in_code"] == "ABC123"


# --------------------------------------------------------------------------- #
# I3 — validação de meeting_link (review F0/F1)
# --------------------------------------------------------------------------- #


class TestMeetingLinkValidation:
    async def test_javascript_rejeitado(self):
        with pytest.raises(ValidationError):
            AssembleiaCreate(
                tipo="ordinaria",
                titulo="AGO 2030",
                data=FUTURE,
                local="Sede",
                meeting_link="javascript:alert(1)",
            )

    async def test_https_aceite(self):
        a = AssembleiaCreate(
            tipo="ordinaria",
            titulo="AGO 2030",
            data=FUTURE,
            local="Sede",
            meeting_link="https://meet.google.com/abc-defg-hij",
        )
        assert a.meeting_link.startswith("https://")

    async def test_none_aceite(self):
        a = AssembleiaCreate(tipo="ordinaria", titulo="AGO 2030", data=FUTURE, local="Sede")
        assert a.meeting_link is None


# --------------------------------------------------------------------------- #
# F4 — Moções/requerimentos/recomendações (spec §5; Art. 6, 26)
# --------------------------------------------------------------------------- #


def _mocao(**over):
    base = {
        "id": "m1",
        "assembleia_id": "a1",
        "tipo": "mocao",
        "titulo": "Titulo",
        "texto": "Texto",
        "proposta_por": "u1",
        "status": "submetida",
        "votacao_imediata": False,
    }
    base.update(over)
    return base


class TestSubmeterMocao:
    async def test_nao_em_curso_400(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess(status="convocada"))
        with pytest.raises(HTTPException) as exc:
            await a_route.submeter_mocao(
                assembleia_id="a1",
                request=_request(),
                data=a_route.MocaoCreate(titulo="Aprovar isto", texto="x"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 400

    async def test_nao_presente_403(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_presencas.find_one = AsyncMock(return_value=None)  # ausente
        with pytest.raises(HTTPException) as exc:
            await a_route.submeter_mocao(
                assembleia_id="a1",
                request=_request(),
                data=a_route.MocaoCreate(titulo="Aprovar isto", texto="x"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_presente_submete_mocao_simples(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_presencas.find_one = AsyncMock(return_value={"id": "p1"})
        captured = {}
        gov_env.assembleia_mocoes.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await a_route.submeter_mocao(
            assembleia_id="a1",
            request=_request(),
            data=a_route.MocaoCreate(tipo="mocao", titulo="Aprovar isto", texto="razões"),
            current_user=socio_user,
        )
        assert captured["proposta_por"] == socio_user.id
        assert captured["tipo"] == "mocao"
        assert captured["status"] == "submetida"
        # Moção: NÃO é votação imediata (vai a discussão antes).
        assert captured["votacao_imediata"] is False
        assert result["votacao_imediata"] is False

    async def test_requerimento_marca_votacao_imediata(self, gov_env, socio_user):
        # Art. 6, 26: requerimento salta a discussão.
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_presencas.find_one = AsyncMock(return_value={"id": "p1"})
        captured = {}
        gov_env.assembleia_mocoes.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        await a_route.submeter_mocao(
            assembleia_id="a1",
            request=_request(),
            data=a_route.MocaoCreate(tipo="requerimento", titulo="Encerrar debate", texto="já"),
            current_user=socio_user,
        )
        assert captured["votacao_imediata"] is True

    async def test_recomendacao_nao_imediata(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_presencas.find_one = AsyncMock(return_value={"id": "p1"})
        captured = {}
        gov_env.assembleia_mocoes.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        await a_route.submeter_mocao(
            assembleia_id="a1",
            request=_request(),
            data=a_route.MocaoCreate(tipo="recomendacao", titulo="Recomendar X", texto="y"),
            current_user=socio_user,
        )
        assert captured["votacao_imediata"] is False


class TestColocarMocaoAVoto:
    async def test_socio_comum_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.colocar_mocao_a_voto(
                assembleia_id="a1",
                mid="m1",
                request=_request(),
                data=a_route.MocaoColocarVoto(),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_mocao_inexistente_404(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_mocoes.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await a_route.colocar_mocao_a_voto(
                assembleia_id="a1",
                mid="m1",
                request=_request(),
                data=a_route.MocaoColocarVoto(),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 404

    async def test_mocao_ja_encerrada_400(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_mocoes.find_one = AsyncMock(return_value=_mocao(status="em_votacao"))
        with pytest.raises(HTTPException) as exc:
            await a_route.colocar_mocao_a_voto(
                assembleia_id="a1",
                mid="m1",
                request=_request(),
                data=a_route.MocaoColocarVoto(),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_sem_quorum_400(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_mocoes.find_one = AsyncMock(return_value=_mocao())
        # poder 2 < 2.ª chamada ceil(10/3)=4 → 400
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 2}]))
        with pytest.raises(HTTPException) as exc:
            await a_route.colocar_mocao_a_voto(
                assembleia_id="a1",
                mid="m1",
                request=_request(),
                data=a_route.MocaoColocarVoto(),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400
        gov_env.assembleia_deliberacoes.insert_one.assert_not_awaited()

    async def test_mesa_cria_deliberacao_e_marca_em_votacao(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_mocoes.find_one = AsyncMock(
            return_value=_mocao(titulo="Encerrar debate", texto="já", item_id="ot-1")
        )
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 6}]))
        delib_captured = {}
        gov_env.assembleia_deliberacoes.insert_one = AsyncMock(side_effect=lambda d: delib_captured.update(d))
        mocao_update = {}
        gov_env.assembleia_mocoes.update_one = AsyncMock(side_effect=lambda flt, upd: mocao_update.update(upd["$set"]))
        result = await a_route.colocar_mocao_a_voto(
            assembleia_id="a1",
            mid="m1",
            request=_request(),
            data=a_route.MocaoColocarVoto(voting_mode="nominal", subitem="b"),
            current_user=_mesa_ag(),
        )
        # Cria deliberação aberta ligada à moção pelo título/texto/item.
        assert delib_captured["status"] == "aberta"
        assert delib_captured["voting_mode"] == "nominal"
        assert delib_captured["ponto"] == "Encerrar debate"
        assert delib_captured["descricao"] == "já"
        assert delib_captured["item_id"] == "ot-1"
        assert delib_captured["subitem"] == "b"
        # Moção fica em_votacao com a ligação à deliberação.
        assert mocao_update["status"] == "em_votacao"
        assert mocao_update["deliberacao_id"] == delib_captured["id"]
        assert result["deliberacao_id"] == delib_captured["id"]

    async def test_falha_update_mocao_apaga_deliberacao(self, gov_env):
        # Se o $set da moção falhar após inserir a deliberação, a deliberação
        # `aberta` ficaria órfã (a Mesa não a consegue ligar). A compensação
        # apaga-a e a excepção propaga — listagens não divergem.
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_mocoes.find_one = AsyncMock(return_value=_mocao(titulo="X", texto="y"))
        gov_env.assembleia_presencas.find = MagicMock(return_value=_cursor([{"voting_power": 6}]))
        delib_captured = {}
        gov_env.assembleia_deliberacoes.insert_one = AsyncMock(side_effect=lambda d: delib_captured.update(d))
        gov_env.assembleia_mocoes.update_one = AsyncMock(side_effect=RuntimeError("db transient"))
        deleted = {}
        gov_env.assembleia_deliberacoes.delete_one = AsyncMock(side_effect=lambda flt: deleted.update(flt))
        with pytest.raises(RuntimeError):
            await a_route.colocar_mocao_a_voto(
                assembleia_id="a1",
                mid="m1",
                request=_request(),
                data=a_route.MocaoColocarVoto(),
                current_user=_mesa_ag(),
            )
        assert deleted.get("id") == delib_captured["id"]


class TestRetirarMocao:
    async def test_proponente_retira(self, gov_env, socio_user):
        gov_env.assembleia_mocoes.find_one = AsyncMock(return_value=_mocao(proposta_por=socio_user.id))
        captured = {}
        gov_env.assembleia_mocoes.update_one = AsyncMock(side_effect=lambda flt, upd: captured.update(upd["$set"]))
        result = await a_route.retirar_mocao(assembleia_id="a1", mid="m1", request=_request(), current_user=socio_user)
        assert result["status"] == "retirada"
        assert captured["status"] == "retirada"

    async def test_outro_socio_403(self, gov_env, socio_user):
        gov_env.assembleia_mocoes.find_one = AsyncMock(return_value=_mocao(proposta_por="outro"))
        with pytest.raises(HTTPException) as exc:
            await a_route.retirar_mocao(assembleia_id="a1", mid="m1", request=_request(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_mesa_retira_qualquer(self, gov_env):
        gov_env.assembleia_mocoes.find_one = AsyncMock(return_value=_mocao(proposta_por="outro"))
        await a_route.retirar_mocao(assembleia_id="a1", mid="m1", request=_request(), current_user=_mesa_ag())
        gov_env.assembleia_mocoes.update_one.assert_awaited()

    async def test_ja_em_votacao_400(self, gov_env, socio_user):
        gov_env.assembleia_mocoes.find_one = AsyncMock(
            return_value=_mocao(proposta_por=socio_user.id, status="em_votacao")
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.retirar_mocao(assembleia_id="a1", mid="m1", request=_request(), current_user=socio_user)
        assert exc.value.status_code == 400


class TestListMocoes:
    async def test_lista(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_mocoes.find = MagicMock(return_value=_cursor([_mocao(id="m1"), _mocao(id="m2")]))
        result = await a_route.list_mocoes(assembleia_id="a1", current_user=socio_user)
        assert [m["id"] for m in result["mocoes"]] == ["m1", "m2"]


# --------------------------------------------------------------------------- #
# F5 — Antes da ordem de trabalhos + expediente (Art. 14)
# --------------------------------------------------------------------------- #


class TestExpediente:
    async def test_socio_comum_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.registar_expediente(
                assembleia_id="a1",
                request=_request(),
                data=a_route.ExpedienteCreate(tipo="correspondencia", texto="Carta da Direcção"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_assembleia_inexistente_404(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await a_route.registar_expediente(
                assembleia_id="a1",
                request=_request(),
                data=a_route.ExpedienteCreate(tipo="correspondencia", texto="Carta"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 404

    async def test_mesa_regista_correspondencia(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        captured = {}
        gov_env.assembleia_expediente.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await a_route.registar_expediente(
            assembleia_id="a1",
            request=_request(),
            data=a_route.ExpedienteCreate(tipo="correspondencia", texto="Convite IFATCA"),
            current_user=_mesa_ag(),
        )
        assert captured["tipo"] == "correspondencia"
        assert captured["texto"] == "Convite IFATCA"
        assert captured["source_article"] == "14"
        assert result["id"] == captured["id"]

    async def test_voto_pesar_por_aclamacao(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        captured = {}
        gov_env.assembleia_expediente.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        await a_route.registar_expediente(
            assembleia_id="a1",
            request=_request(),
            data=a_route.ExpedienteCreate(
                tipo="voto_pesar", texto="Falecimento do sócio X", aprovado_por_aclamacao=True
            ),
            current_user=_mesa_ag(),
        )
        assert captured["tipo"] == "voto_pesar"
        assert captured["aprovado_por_aclamacao"] is True

    async def test_lista_expediente(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_expediente.find = MagicMock(
            return_value=_cursor([{"id": "e1", "tipo": "correspondencia"}, {"id": "e2", "tipo": "voto_louvor"}])
        )
        result = await a_route.list_expediente(assembleia_id="a1", current_user=socio_user)
        assert [e["id"] for e in result["expediente"]] == ["e1", "e2"]


# --------------------------------------------------------------------------- #
# F6 — Documentos da sessão + convidados (Art. 20, 36)
# --------------------------------------------------------------------------- #


def _now_iso():
    from datetime import datetime as _dt, timezone as _tz

    return _dt.now(_tz.utc).isoformat()


def _iso_in_days(days: float) -> str:
    from datetime import datetime as _dt, timedelta as _td, timezone as _tz

    return (_dt.now(_tz.utc) + _td(days=days)).isoformat()


class TestAnexarDocumento:
    async def test_socio_comum_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.anexar_documento(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaDocumentoAttach(document_id="doc12345"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_documento_inexistente_404(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value={"id": "a1", "data": FUTURE, "documentos": []})
        gov_env.documents.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await a_route.anexar_documento(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaDocumentoAttach(document_id="doc12345"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 404

    async def test_ja_anexado_409(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(
            return_value={"id": "a1", "data": FUTURE, "documentos": ["doc12345"]}
        )
        gov_env.documents.find_one = AsyncMock(return_value={"id": "doc12345", "title": "Acta"})
        with pytest.raises(HTTPException) as exc:
            await a_route.anexar_documento(
                assembleia_id="a1",
                request=_request(),
                data=a_route.AssembleiaDocumentoAttach(document_id="doc12345"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 409

    async def test_anexar_tempo_marca_nao_tardio(self, gov_env):
        # data a 10 dias → >3 dias → não tardio.
        gov_env.assembleias.find_one = AsyncMock(
            return_value={"id": "a1", "data": _iso_in_days(10), "documentos": []}
        )
        gov_env.documents.find_one = AsyncMock(return_value={"id": "doc12345", "title": "Relatório"})
        captured = {}
        gov_env.assembleias.update_one = AsyncMock(side_effect=lambda flt, upd: captured.update(upd))
        result = await a_route.anexar_documento(
            assembleia_id="a1",
            request=_request(),
            data=a_route.AssembleiaDocumentoAttach(document_id="doc12345"),
            current_user=_mesa_ag(),
        )
        assert result["tardio"] is False
        assert captured["$push"] == {"documentos": "doc12345"}
        # Audit: action = documento_anexado (não _tardio)
        last_call = a_route.create_audit_log.await_args
        assert last_call.args[1] == "documento_anexado"

    async def test_anexar_tardio_audita_tardio(self, gov_env):
        # data a 1 dia → <3 dias → tardio.
        gov_env.assembleias.find_one = AsyncMock(
            return_value={"id": "a1", "data": _iso_in_days(1), "documentos": []}
        )
        gov_env.documents.find_one = AsyncMock(return_value={"id": "doc12345", "title": "Anexo de última hora"})
        result = await a_route.anexar_documento(
            assembleia_id="a1",
            request=_request(),
            data=a_route.AssembleiaDocumentoAttach(document_id="doc12345"),
            current_user=_mesa_ag(),
        )
        assert result["tardio"] is True
        last_call = a_route.create_audit_log.await_args
        assert last_call.args[1] == "documento_anexado_tardio"


class TestListDocumentos:
    async def test_vazio(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value={"id": "a1", "documentos": []})
        result = await a_route.list_documentos(assembleia_id="a1", current_user=socio_user)
        assert result["documentos"] == []

    async def test_resolve_titles(self, gov_env, socio_user):
        gov_env.assembleias.find_one = AsyncMock(return_value={"id": "a1", "documentos": ["d1", "d2"]})
        gov_env.documents.find = MagicMock(
            return_value=_cursor([{"id": "d1", "title": "Relatório"}, {"id": "d2", "title": "Orçamento"}])
        )
        result = await a_route.list_documentos(assembleia_id="a1", current_user=socio_user)
        assert {d["id"] for d in result["documentos"]} == {"d1", "d2"}


class TestConvidados:
    async def test_socio_comum_403_adicionar(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.adicionar_convidado(
                assembleia_id="a1",
                request=_request(),
                data=a_route.ConvidadoCreate(nome="Convidado X", can_speak=True),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_mesa_adiciona_com_can_speak(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value={"id": "a1"})
        captured = {}
        gov_env.assembleia_convidados.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await a_route.adicionar_convidado(
            assembleia_id="a1",
            request=_request(),
            data=a_route.ConvidadoCreate(nome="João Visita", can_speak=True, motivo="Especialista"),
            current_user=_mesa_ag(),
        )
        assert captured["nome"] == "João Visita"
        assert captured["can_speak"] is True
        assert captured["motivo"] == "Especialista"
        # Convidados não votam nem entram no quórum: o doc não tem voting_power.
        assert "voting_power" not in captured
        assert captured["checked_in"] is False
        assert result["id"] == captured["id"]

    async def test_socio_comum_403_listar(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.list_convidados(assembleia_id="a1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_mesa_lista(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value={"id": "a1"})
        gov_env.assembleia_convidados.find = MagicMock(
            return_value=_cursor([{"id": "c1", "nome": "X"}, {"id": "c2", "nome": "Y"}])
        )
        result = await a_route.list_convidados(assembleia_id="a1", current_user=_mesa_ag())
        assert [c["id"] for c in result["convidados"]] == ["c1", "c2"]

    async def test_checkin_convidado_marca_presente(self, gov_env):
        gov_env.assembleia_convidados.find_one = AsyncMock(return_value={"id": "c1"})
        captured = {}
        gov_env.assembleia_convidados.update_one = AsyncMock(
            side_effect=lambda flt, upd: captured.update(upd["$set"])
        )
        result = await a_route.checkin_convidado(
            assembleia_id="a1", cid="c1", request=_request(), current_user=_mesa_ag()
        )
        assert captured["checked_in"] is True
        assert result["checked_in"] is True

    async def test_checkin_inexistente_404(self, gov_env):
        gov_env.assembleia_convidados.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await a_route.checkin_convidado(
                assembleia_id="a1", cid="c99", request=_request(), current_user=_mesa_ag()
            )
        assert exc.value.status_code == 404


class TestPalavraConvidado:
    async def test_socio_comum_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await a_route.pedir_palavra_convidado(
                assembleia_id="a1",
                request=_request(),
                data=a_route.PalavraConvidadoCreate(convidado_id="c1"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_convidado_inexistente_404(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_convidados.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await a_route.pedir_palavra_convidado(
                assembleia_id="a1",
                request=_request(),
                data=a_route.PalavraConvidadoCreate(convidado_id="c1"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 404

    async def test_can_speak_false_400(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_convidados.find_one = AsyncMock(
            return_value={"id": "c1", "can_speak": False, "checked_in": True}
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.pedir_palavra_convidado(
                assembleia_id="a1",
                request=_request(),
                data=a_route.PalavraConvidadoCreate(convidado_id="c1"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_nao_presente_400(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_convidados.find_one = AsyncMock(
            return_value={"id": "c1", "can_speak": True, "checked_in": False}
        )
        with pytest.raises(HTTPException) as exc:
            await a_route.pedir_palavra_convidado(
                assembleia_id="a1",
                request=_request(),
                data=a_route.PalavraConvidadoCreate(convidado_id="c1"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_duplicado_409(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_convidados.find_one = AsyncMock(
            return_value={"id": "c1", "can_speak": True, "checked_in": True}
        )
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value={"id": "q0"})
        with pytest.raises(HTTPException) as exc:
            await a_route.pedir_palavra_convidado(
                assembleia_id="a1",
                request=_request(),
                data=a_route.PalavraConvidadoCreate(convidado_id="c1"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 409

    async def test_mesa_inscreve_convidado(self, gov_env):
        gov_env.assembleias.find_one = AsyncMock(return_value=_sess())
        gov_env.assembleia_convidados.find_one = AsyncMock(
            return_value={"id": "c1", "can_speak": True, "checked_in": True}
        )
        gov_env.assembleia_palavra.find_one = AsyncMock(return_value=None)
        captured = {}
        gov_env.assembleia_palavra.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await a_route.pedir_palavra_convidado(
            assembleia_id="a1",
            request=_request(),
            data=a_route.PalavraConvidadoCreate(convidado_id="c1", tipo="intervencao"),
            current_user=_mesa_ag(),
        )
        assert captured["user_id"] is None
        assert captured["convidado_id"] == "c1"
        assert captured["tipo"] == "intervencao"
        assert captured["duration_limit_s"] == 180
        assert result["status"] == "inscrito"


class TestFaseAntesOTRegista:
    # Sanity check — a fase antes_ot regista `antes_ot_aberto_em` (já testada na F0
    # em TestFase.test_antes_ot_regista_abertura). Reafirmo aqui o contrato do F5.
    async def test_reentrar_mesma_fase_rejeitado(self, gov_env):
        # Re-entrar na fase actual é rejeitado com 400 — evita um bump de sessão e
        # um audit log redundantes a cada clique repetido. É essa rejeição que
        # agora garante que `antes_ot_aberto_em` nunca é re-escrito: a única
        # escrita do campo ocorre na 1.ª transição para antes_ot.
        gov_env.assembleias.find_one = AsyncMock(
            return_value={
                "id": "a1",
                "status": "em_curso",
                "session_phase": "antes_ot",
                "antes_ot_aberto_em": "2030-01-01T10:00:00+00:00",
                "eligible_voters_count": 10,
            }
        )
        update_mock = AsyncMock()
        gov_env.assembleias.update_one = update_mock
        with pytest.raises(HTTPException) as exc:
            await a_route.transicao_fase(
                assembleia_id="a1",
                request=_request(),
                data=AssembleiaFaseUpdate(session_phase="antes_ot"),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400
        assert "já está em" in exc.value.detail
        # Nada é escrito: sem rewrite de antes_ot_aberto_em, sem bump.
        update_mock.assert_not_called()


class TestPalavraRequestModelo:
    # O `PalavraRequest` é persistido e reconstruído em round-trips. Sem o
    # validador, um doc com ambos (ou nenhum) identificador de orador passava
    # silenciosamente — a F6 introduziu `convidado_id` ao lado de `user_id`.
    async def test_exige_exactamente_um_de_user_ou_convidado(self):
        # Membro: só user_id.
        PalavraRequest(assembleia_id="a1", user_id="u1", tipo="intervencao", duration_limit_s=180)
        # Convidado (F6): só convidado_id.
        PalavraRequest(assembleia_id="a1", convidado_id="c1", tipo="intervencao", duration_limit_s=180)
        # Ambos preenchidos → rejeitado.
        with pytest.raises(ValidationError):
            PalavraRequest(assembleia_id="a1", user_id="u1", convidado_id="c1", tipo="intervencao", duration_limit_s=180)
        # Nenhum → rejeitado.
        with pytest.raises(ValidationError):
            PalavraRequest(assembleia_id="a1", tipo="intervencao", duration_limit_s=180)

    async def test_duration_limit_fora_de_limites_rejeitado(self):
        with pytest.raises(ValidationError):
            PalavraRequest(assembleia_id="a1", user_id="u1", tipo="intervencao", duration_limit_s=4)
        with pytest.raises(ValidationError):
            PalavraRequest(assembleia_id="a1", user_id="u1", tipo="intervencao", duration_limit_s=99999)


class TestAssembleiaModelo:
    # O campo `documentos` (escrito via $push) tem de sobreviver a um round-trip
    # `Assembleia(**doc).model_dump()` — sem o campo declarado era descartado por
    # `extra="ignore"`.
    async def test_documentos_sobrevive_roundtrip(self):
        doc = {
            "tipo": "ordinaria",
            "titulo": "AGO 2030",
            "data": FUTURE,
            "local": "Sede",
            "convocada_por": "u1",
            "convocatoria_em": FUTURE,
            "antecedencia_dias": 15,
            "documentos": ["doc-1", "doc-2"],
        }
        a = Assembleia(**doc)
        assert a.documentos == ["doc-1", "doc-2"]
        assert a.model_dump()["documentos"] == ["doc-1", "doc-2"]

    async def test_documentos_default_vazio(self):
        a = Assembleia(
            tipo="ordinaria",
            titulo="AGO",
            data=FUTURE,
            local="Sede",
            convocada_por="u1",
            convocatoria_em=FUTURE,
            antecedencia_dias=15,
        )
        assert a.documentos == []
