"""Unit tests para rotas do regime disciplinar (spec-governanca §13/§18).

Cobre: RBAC (Direcção/admin), multa <= 3x quota, expulsão exige deliberação da
AG, perda de direitos suspende voto, e ocultação de dados sensíveis ao visado.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import sancoes as s_route
from governance import is_voting_member
from models import (
    SancaoCreate,
    SancaoDecidir,
    User,
)


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


def _cursor(items):
    cur = MagicMock()
    cur.sort.return_value = cur
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


def _direcao(**over) -> User:
    base = {
        "name": "Dir",
        "email": "dir@x.cv",
        "role": "admin",
        "status": "ativo",
        "cargo": "dir_presidente",
        "account_type": "member",
        "member_category": "ordinario",
    }
    base.update(over)
    return User(**base)


@pytest.fixture
def gov_env(mock_db, monkeypatch):
    mock_db.sancoes = _coll()
    mock_db.assembleia_deliberacoes = _coll()
    mock_db.finance_settings.find_one = AsyncMock(return_value={"quota_amount": 2000.0})
    monkeypatch.setattr(s_route, "create_audit_log", AsyncMock())
    monkeypatch.setattr(s_route, "notify_users", AsyncMock())
    return mock_db


# --------------------------------------------------------------------------- #
# Criar / RBAC / multa
# --------------------------------------------------------------------------- #


class TestCreate:
    async def test_socio_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await s_route.create_sancao(
                request=_request(),
                data=SancaoCreate(user_id="u1", tipo="advertencia", motivo="Atraso reiterado"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_multa_acima_3x_quota_400(self, gov_env):
        gov_env.users.find_one = AsyncMock(return_value={"id": "u1", "name": "Ana"})
        with pytest.raises(HTTPException) as exc:
            await s_route.create_sancao(
                request=_request(),
                data=SancaoCreate(user_id="u1", tipo="multa", motivo="Falta grave", multa_valor=7000.0),
                current_user=_direcao(),
            )
        assert exc.value.status_code == 400  # 7000 > 3 * 2000

    async def test_multa_dentro_do_limite_ok(self, gov_env):
        gov_env.users.find_one = AsyncMock(return_value={"id": "u1", "name": "Ana"})
        captured = {}
        gov_env.sancoes.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await s_route.create_sancao(
            request=_request(),
            data=SancaoCreate(user_id="u1", tipo="multa", motivo="Falta", multa_valor=6000.0),
            current_user=_direcao(),
        )
        assert result["status"] == "proposta"
        assert captured["multa_valor"] == 6000.0

    async def test_perda_direitos_exige_data(self, gov_env):
        gov_env.users.find_one = AsyncMock(return_value={"id": "u1"})
        with pytest.raises(HTTPException) as exc:
            await s_route.create_sancao(
                request=_request(),
                data=SancaoCreate(user_id="u1", tipo="perda_direitos", motivo="Conduta"),
                current_user=_direcao(),
            )
        assert exc.value.status_code == 400


# --------------------------------------------------------------------------- #
# Decisão / expulsão exige AG
# --------------------------------------------------------------------------- #


class TestDecidir:
    async def test_expulsao_sem_deliberacao_400(self, gov_env):
        gov_env.sancoes.find_one = AsyncMock(
            return_value={"id": "s1", "user_id": "u1", "tipo": "expulsao", "status": "inquerito"}
        )
        with pytest.raises(HTTPException) as exc:
            await s_route.decidir_sancao(
                sancao_id="s1",
                request=_request(),
                data=SancaoDecidir(aprovado=True),
                current_user=_direcao(),
            )
        assert exc.value.status_code == 400

    async def test_expulsao_deliberacao_nao_aprovada_400(self, gov_env):
        gov_env.sancoes.find_one = AsyncMock(
            return_value={"id": "s1", "user_id": "u1", "tipo": "expulsao", "status": "inquerito"}
        )
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(return_value={"aprovado": False})
        with pytest.raises(HTTPException) as exc:
            await s_route.decidir_sancao(
                sancao_id="s1",
                request=_request(),
                data=SancaoDecidir(aprovado=True, assembleia_id="a1", deliberacao_id="d1"),
                current_user=_direcao(),
            )
        assert exc.value.status_code == 400

    async def test_expulsao_com_deliberacao_aprovada_ok(self, gov_env):
        gov_env.sancoes.find_one = AsyncMock(
            return_value={"id": "s1", "user_id": "u1", "tipo": "expulsao", "status": "inquerito"}
        )
        gov_env.assembleia_deliberacoes.find_one = AsyncMock(return_value={"aprovado": True})
        captured = {}
        gov_env.sancoes.update_one = AsyncMock(side_effect=lambda f, u: captured.update(u["$set"]))
        result = await s_route.decidir_sancao(
            sancao_id="s1",
            request=_request(),
            data=SancaoDecidir(aprovado=True, assembleia_id="a1", deliberacao_id="d1"),
            current_user=_direcao(),
        )
        assert result["status"] == "decidida"
        assert captured["deliberacao_id"] == "d1"


# --------------------------------------------------------------------------- #
# Aplicar efeitos
# --------------------------------------------------------------------------- #


class TestAplicar:
    async def test_perda_direitos_suspende_voto(self, gov_env):
        gov_env.sancoes.find_one = AsyncMock(
            return_value={
                "id": "s1",
                "user_id": "u1",
                "tipo": "perda_direitos",
                "status": "decidida",
                "decisao": {"aprovado": True},
                "perda_direitos_ate": "2027-01-01T00:00:00+00:00",
                "motivo": "Conduta",
            }
        )
        captured = {}
        gov_env.users.update_one = AsyncMock(side_effect=lambda f, u: captured.update(u["$set"]))
        await s_route.aplicar_sancao(sancao_id="s1", request=_request(), current_user=_direcao())
        assert captured["rights_suspended_until"] == "2027-01-01T00:00:00+00:00"
        # o membro deixa de poder votar enquanto vigente
        member = {
            "account_type": "member",
            "status": "ativo",
            "member_category": "ordinario",
            "rights_suspended_until": captured["rights_suspended_until"],
        }
        assert is_voting_member(member, as_of="2026-06-01T00:00:00+00:00") is False

    async def test_expulsao_sem_deliberacao_400(self, gov_env):
        gov_env.sancoes.find_one = AsyncMock(
            return_value={
                "id": "s1",
                "user_id": "u1",
                "tipo": "expulsao",
                "status": "decidida",
                "decisao": {"aprovado": True},
            }
        )
        with pytest.raises(HTTPException) as exc:
            await s_route.aplicar_sancao(sancao_id="s1", request=_request(), current_user=_direcao())
        assert exc.value.status_code == 400

    async def test_recurso_pendente_nao_aplica_400(self, gov_env):
        gov_env.sancoes.find_one = AsyncMock(
            return_value={
                "id": "s1",
                "user_id": "u1",
                "tipo": "perda_direitos",
                "status": "recurso",
                "decisao": {"aprovado": True},
            }
        )
        with pytest.raises(HTTPException) as exc:
            await s_route.aplicar_sancao(sancao_id="s1", request=_request(), current_user=_direcao())
        assert exc.value.status_code == 400
        gov_env.users.update_one.assert_not_awaited()

    async def test_expulsao_inactiva_e_encerra_mandato(self, gov_env):
        gov_env.sancoes.find_one = AsyncMock(
            return_value={
                "id": "s1",
                "user_id": "u1",
                "tipo": "expulsao",
                "status": "decidida",
                "decisao": {"aprovado": True},
                "assembleia_id": "a1",
                "deliberacao_id": "d1",
            }
        )
        gov_env.users.find_one = AsyncMock(
            return_value={"id": "u1", "cargo_history": [{"cargo": "dir_vogal", "fim": None, "inicio": "2024-01-01"}]}
        )
        captured = {}
        gov_env.users.update_one = AsyncMock(side_effect=lambda f, u: captured.update(u["$set"]))
        await s_route.aplicar_sancao(sancao_id="s1", request=_request(), current_user=_direcao())
        assert captured["status"] == "inativo"
        assert captured["cargo"] == "socio"
        assert captured["cargo_history"][0]["fim"] is not None  # mandato encerrado


# --------------------------------------------------------------------------- #
# Confidencialidade
# --------------------------------------------------------------------------- #


class TestConfidencialidade:
    async def test_visado_ve_versao_redigida(self, gov_env, socio_user):
        gov_env.sancoes.find_one = AsyncMock(
            return_value={
                "id": "s1",
                "user_id": socio_user.id,
                "tipo": "multa",
                "status": "decidida",
                "motivo": "Falta",
                "comissao_inquerito": [{"user_id": "x"}],
                "decisao": {"aprovado": True, "fundamentacao": "detalhe sensível", "por": "admin"},
                "created_at": "2026-01-01",
            }
        )
        result = await s_route.get_sancao(sancao_id="s1", current_user=socio_user)
        # versão redigida: sem comissão nem fundamentação
        assert "comissao_inquerito" not in result
        assert result["decisao"] == {"aprovado": True}

    async def test_terceiro_403(self, gov_env, socio_user):
        gov_env.sancoes.find_one = AsyncMock(
            return_value={
                "id": "s1",
                "user_id": "outro",
                "tipo": "multa",
                "status": "decidida",
            }
        )
        with pytest.raises(HTTPException) as exc:
            await s_route.get_sancao(sancao_id="s1", current_user=socio_user)
        assert exc.value.status_code == 403


# --------------------------------------------------------------------------- #
# Anotação multa_receita (PR #350 W1: faixa reflete o caixa real, não o estado)
# --------------------------------------------------------------------------- #


class TestListMultaReceita:
    async def test_anota_existencia_e_valor_real_do_caixa(self, gov_env):
        # 3 sanções: multa aplicada COM receita, multa aplicada SEM receita
        # (removida nas finanças), e advertência (não anotada).
        gov_env.sancoes.find = MagicMock(
            return_value=_cursor(
                [
                    {"id": "s1", "tipo": "multa", "status": "aplicada", "multa_valor": 5000},
                    {"id": "s2", "tipo": "multa", "status": "aplicada", "multa_valor": 8000},
                    {"id": "s3", "tipo": "advertencia", "status": "aplicada"},
                ]
            )
        )
        # No caixa só existe a receita de s1, e com valor corrigido (4500 != 5000).
        tx_find = MagicMock(return_value=_cursor([{"sancao_id": "s1", "amount": 4500.0}]))
        gov_env.transactions.find = tx_find

        resp = await s_route.list_sancoes(current_user=_direcao())
        by_id = {s["id"]: s for s in resp["sancoes"]}

        assert by_id["s1"]["multa_receita"] == {"exists": True, "amount": 4500.0}
        assert by_id["s2"]["multa_receita"] == {"exists": False, "amount": 0.0}
        assert "multa_receita" not in by_id["s3"]  # advertência não é anotada

        # Agregação numa só query (sem N+1): filtra por $in dos ids de multa aplicada.
        flt = tx_find.call_args.args[0]
        assert flt["type"] == "receita"
        assert set(flt["sancao_id"]["$in"]) == {"s1", "s2"}

    async def test_sem_multas_nao_consulta_transactions(self, gov_env):
        gov_env.sancoes.find = MagicMock(
            return_value=_cursor([{"id": "s9", "tipo": "advertencia", "status": "aplicada"}])
        )
        gov_env.transactions.find = MagicMock(side_effect=AssertionError("não devia consultar transactions"))
        resp = await s_route.list_sancoes(current_user=_direcao())
        assert resp["sancoes"][0].get("multa_receita") is None
