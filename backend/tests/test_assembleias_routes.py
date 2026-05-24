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
