"""Unit tests para rotas da Assembleia Geral (spec-governanca §11/§18).

Invoca as rotas directamente com mock_db. As colecções de governança não estão
pré-ligadas no conftest — ligam-se aqui com AsyncMock. RBAC, convocatória,
representação (max 3, Mesa não representa), quórum e maiorias.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import BackgroundTasks, HTTPException
from pydantic import ValidationError

from routes import assembleias as a_route
from models import (
    AssembleiaCreate,
    AssembleiaDeliberacaoCreate,
    AssembleiaFaseUpdate,
    AssembleiaPresencaCreate,
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
    monkeypatch.setattr(a_route, "create_audit_log", AsyncMock())
    monkeypatch.setattr(a_route, "notify_all_active_users", AsyncMock())
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
