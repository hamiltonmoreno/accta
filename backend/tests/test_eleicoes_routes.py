"""Unit tests para rotas de eleições (spec-governanca §12/§18).

Cobre: lista incompleta/duplicada/comissão-candidata rejeitadas, elegibilidade,
voto SECRETO (boletim sem user_id/voter_hash), voto duplo bloqueado, apuramento
(brancos/nulos fora dos válidos, empate) e proclamação (cria mandatos).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import eleicoes as e_route
from governance import election_slots
from models import (
    EleicaoCreate,
    EleicaoListaCreate,
    VotarRequest,
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
    cur.skip.return_value = cur
    cur.limit.return_value = cur
    cur.to_list = AsyncMock(return_value=items)
    return cur


def _coll(**methods):
    c = MagicMock()
    c.find_one = AsyncMock(return_value=None)
    c.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    c.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    c.count_documents = AsyncMock(return_value=0)
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


def _eligible(ids):
    return [{"id": i, "account_type": "member", "status": "ativo", "member_category": "ordinario"} for i in ids]


def _full_candidatos(prefix="u"):
    return [{"slot_key": s["slot_key"], "user_id": f"{prefix}{i}"} for i, s in enumerate(election_slots(5))]


@pytest.fixture
def gov_env(mock_db, monkeypatch):
    mock_db.eleicoes = _coll()
    mock_db.eleicao_listas = _coll()
    mock_db.eleicao_voter_receipts = _coll()
    mock_db.eleicao_ballots = _coll()
    monkeypatch.setattr(e_route, "create_audit_log", AsyncMock())
    monkeypatch.setattr(e_route, "notify_users", AsyncMock())
    return mock_db


def _eleicao(**over):
    base = {
        "id": "el1",
        "ano": 2030,
        "status": "candidaturas",
        "direcao_titulares": 5,
        "comissao_eleitoral": [],
        "mesa_voto": [],
        "mandato_inicio": "2030-04-01",
        "mandato_fim": "2033-04-01",
        "assembleia_id": None,
    }
    base.update(over)
    return base


# --------------------------------------------------------------------------- #
# Criação (RBAC)
# --------------------------------------------------------------------------- #


class TestCreate:
    async def test_socio_403(self, gov_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await e_route.create_eleicao(
                request=_request(),
                data=EleicaoCreate(ano=2030, mandato_inicio="2030-04-01", mandato_fim="2033-04-01"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_mesa_ag_cria_em_candidaturas(self, gov_env):
        result = await e_route.create_eleicao(
            request=_request(),
            data=EleicaoCreate(ano=2030, mandato_inicio="2030-04-01", mandato_fim="2033-04-01"),
            current_user=_mesa_ag(),
        )
        assert result["status"] == "candidaturas"
        assert result["direcao_titulares"] == 5


# --------------------------------------------------------------------------- #
# Listas
# --------------------------------------------------------------------------- #


class TestListas:
    async def test_incompleta_400(self, gov_env):
        gov_env.eleicoes.find_one = AsyncMock(return_value=_eleicao())
        candidatos = _full_candidatos()[:-1]  # falta 1 slot
        with pytest.raises(HTTPException) as exc:
            await e_route.submit_lista(
                eleicao_id="el1",
                request=_request(),
                data=EleicaoListaCreate(letra="A", candidatos=candidatos),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_candidato_duplicado_400(self, gov_env):
        gov_env.eleicoes.find_one = AsyncMock(return_value=_eleicao())
        candidatos = _full_candidatos()
        candidatos[1]["user_id"] = candidatos[0]["user_id"]  # mesmo user em 2 slots
        with pytest.raises(HTTPException) as exc:
            await e_route.submit_lista(
                eleicao_id="el1",
                request=_request(),
                data=EleicaoListaCreate(letra="A", candidatos=candidatos),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_comissao_candidata_400(self, gov_env):
        candidatos = _full_candidatos()
        gov_env.eleicoes.find_one = AsyncMock(return_value=_eleicao(comissao_eleitoral=[candidatos[0]["user_id"]]))
        with pytest.raises(HTTPException) as exc:
            await e_route.submit_lista(
                eleicao_id="el1",
                request=_request(),
                data=EleicaoListaCreate(letra="A", candidatos=candidatos),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_inelegivel_400(self, gov_env):
        gov_env.eleicoes.find_one = AsyncMock(return_value=_eleicao())
        candidatos = _full_candidatos()
        ids = [c["user_id"] for c in candidatos]
        users = _eligible(ids)
        users[3]["member_category"] = "honorario"  # não elegível
        gov_env.users.find = MagicMock(return_value=_cursor(users))
        with pytest.raises(HTTPException) as exc:
            await e_route.submit_lista(
                eleicao_id="el1",
                request=_request(),
                data=EleicaoListaCreate(letra="A", candidatos=candidatos),
                current_user=_mesa_ag(),
            )
        assert exc.value.status_code == 400

    async def test_happy_normaliza_cargo(self, gov_env):
        gov_env.eleicoes.find_one = AsyncMock(return_value=_eleicao())
        candidatos = _full_candidatos()
        ids = [c["user_id"] for c in candidatos]
        gov_env.users.find = MagicMock(return_value=_cursor(_eligible(ids)))
        captured = {}
        gov_env.eleicao_listas.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await e_route.submit_lista(
            eleicao_id="el1",
            request=_request(),
            data=EleicaoListaCreate(letra="a", candidatos=candidatos),
            current_user=_mesa_ag(),
        )
        assert result["letra"] == "A"  # uppercased
        assert result["estado"] == "submetida"
        # cada candidato tem cargo derivado do slot
        assert all("cargo" in c and "suplente" in c for c in captured["candidatos"])


# --------------------------------------------------------------------------- #
# Voto secreto
# --------------------------------------------------------------------------- #


class TestVoto:
    async def test_nao_eleitor_403(self, gov_env):
        gov_env.eleicoes.find_one = AsyncMock(return_value=_eleicao(status="votacao"))
        honorario = User(
            name="H",
            email="h@x.cv",
            role="socio",
            status="ativo",
            cargo="socio",
            account_type="member",
            member_category="honorario",
        )
        with pytest.raises(HTTPException) as exc:
            await e_route.votar(
                eleicao_id="el1",
                request=_request(),
                data=VotarRequest(voto="branco"),
                current_user=honorario,
            )
        assert exc.value.status_code == 403

    async def test_boletim_anonimo(self, gov_env, socio_user, monkeypatch):
        gov_env.eleicoes.find_one = AsyncMock(return_value=_eleicao(status="votacao"))
        gov_env.eleicao_listas.find_one = AsyncMock(return_value={"estado": "aceite"})
        captured = {}

        async def fake_cast(eleicao_id, voter_hash, receipt_doc, ballot_doc):
            captured["receipt"] = receipt_doc
            captured["ballot"] = ballot_doc

        monkeypatch.setattr(e_route, "cast_ballot", AsyncMock(side_effect=fake_cast))
        await e_route.votar(
            eleicao_id="el1",
            request=_request(),
            data=VotarRequest(voto="L1"),
            current_user=socio_user,
        )
        # boletim NUNCA liga ao eleitor
        assert "user_id" not in captured["ballot"]
        assert "voter_hash" not in captured["ballot"]
        assert captured["ballot"]["voto"] == "L1"
        # recibo prova participação por hash, sem o sentido de voto
        assert captured["receipt"]["voter_hash"]
        assert "voto" not in captured["receipt"]
        assert "user_id" not in captured["receipt"]

    async def test_voto_duplo_409(self, gov_env, socio_user, monkeypatch):
        gov_env.eleicoes.find_one = AsyncMock(return_value=_eleicao(status="votacao"))
        monkeypatch.setattr(e_route, "cast_ballot", AsyncMock(side_effect=ValueError("voto duplicado")))
        with pytest.raises(HTTPException) as exc:
            await e_route.votar(
                eleicao_id="el1",
                request=_request(),
                data=VotarRequest(voto="branco"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 409


# --------------------------------------------------------------------------- #
# Apuramento
# --------------------------------------------------------------------------- #


class TestApurar:
    async def test_maioria_simples(self, gov_env):
        gov_env.eleicoes.find_one = AsyncMock(return_value=_eleicao(status="votacao"))
        ballots = [{"voto": "L1"}] * 5 + [{"voto": "L2"}] * 3 + [{"voto": "branco"}] * 2 + [{"voto": "nulo"}] * 1
        gov_env.eleicao_ballots.find = MagicMock(return_value=_cursor(ballots))
        result = await e_route.apurar(eleicao_id="el1", request=_request(), current_user=_mesa_ag())
        assert result["vencedora"] == "L1"
        assert result["empate"] is False
        assert result["brancos"] == 2 and result["nulos"] == 1
        assert result["total_validos"] == 8  # brancos/nulos excluídos

    async def test_empate_marca_nova_eleicao(self, gov_env):
        gov_env.eleicoes.find_one = AsyncMock(return_value=_eleicao(status="votacao"))
        gov_env.eleicao_ballots.find = MagicMock(return_value=_cursor([{"voto": "L1"}] * 4 + [{"voto": "L2"}] * 4))
        result = await e_route.apurar(eleicao_id="el1", request=_request(), current_user=_mesa_ag())
        assert result["empate"] is True
        assert result["vencedora"] is None
        assert "nova_eleicao_ate" in result


# --------------------------------------------------------------------------- #
# Proclamação
# --------------------------------------------------------------------------- #


class TestProclamar:
    async def test_empate_400(self, gov_env):
        gov_env.eleicoes.find_one = AsyncMock(
            return_value=_eleicao(status="apurada", resultado={"empate": True, "vencedora": None})
        )
        with pytest.raises(HTTPException) as exc:
            await e_route.proclamar(eleicao_id="el1", request=_request(), current_user=_mesa_ag())
        assert exc.value.status_code == 400

    async def test_happy_cria_mandatos(self, gov_env):
        gov_env.eleicoes.find_one = AsyncMock(
            return_value=_eleicao(status="apurada", resultado={"empate": False, "vencedora": "L1"})
        )
        lista = {
            "id": "L1",
            "letra": "A",
            "eleicao_id": "el1",
            "candidatos": [
                {
                    "slot_key": "dir_presidente",
                    "cargo": "dir_presidente",
                    "user_id": "p1",
                    "suplente": False,
                    "seat_index": 1,
                },
                {
                    "slot_key": "dir_suplente_1",
                    "cargo": "dir_vogal",
                    "user_id": "s1",
                    "suplente": True,
                    "seat_index": 1,
                },
            ],
        }
        gov_env.eleicao_listas.find_one = AsyncMock(return_value=lista)
        gov_env.users.find = MagicMock(return_value=_cursor([]))  # sem cessantes

        async def find_user(filt, proj=None):
            return {"id": filt["id"], "cargo": "socio", "cargo_history": []}

        gov_env.users.find_one = find_user
        updates = {}

        async def cap_update(filt, update):
            updates[filt["id"]] = update["$set"]
            return MagicMock(modified_count=1)

        gov_env.users.update_one = cap_update

        result = await e_route.proclamar(eleicao_id="el1", request=_request(), current_user=_mesa_ag())
        assert {p["user_id"] for p in result["proclaimed"]} == {"p1", "s1"}
        # titular recebe o cargo + órgão
        assert updates["p1"]["cargo"] == "dir_presidente"
        assert updates["p1"]["orgao"] == "direcao"
        assert updates["p1"]["cargo_history"][-1]["eleicao_id"] == "el1"
        assert updates["p1"]["cargo_history"][-1]["suplente"] is False
        # suplente: só history, cargo activo não muda
        assert "cargo" not in updates["s1"]
        assert updates["s1"]["cargo_history"][-1]["suplente"] is True
