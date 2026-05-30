"""Unit tests para routes/public_profissional.py — Cat 5 F4.

Superfícies públicas (sem auth). Verifica que o recorte de visibilidade é
aplicado no query do DAO e que a projeção exclui campos internos. Mesmo padrão
dos outros test_*_routes.py: invoca handlers com `mock_db`, sem TestClient/DB.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import public_profissional as public_route


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _wire(mock_db, name: str):
    coll = MagicMock(name=name)
    coll.find_one = AsyncMock(return_value=None)
    coll.count_documents = AsyncMock(return_value=0)
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[])
    coll.find = MagicMock(return_value=cursor)
    setattr(mock_db, name, coll)
    return coll


@pytest.fixture
def wired_defesa(mock_db):
    return _wire(mock_db, "defesa_profissional")


@pytest.fixture
def wired_relacoes(mock_db):
    return _wire(mock_db, "relacoes_externas")


@pytest.fixture
def wired_publicacoes(mock_db):
    return _wire(mock_db, "publicacoes")


@pytest.fixture
def wired_formacoes(mock_db):
    return _wire(mock_db, "formacoes")


# --------------------------------------------------------------------------- #
# Defesa profissional
# --------------------------------------------------------------------------- #


class TestPublicDefesa:
    async def test_so_publicado_e_publico(self, wired_defesa):
        await public_route.public_list_defesa()
        query = wired_defesa.find.call_args[0][0]
        assert query["status"] == "publicado"
        assert query["visibility"] == "publico"

    async def test_projecao_esconde_campos_internos(self, wired_defesa):
        await public_route.public_list_defesa()
        proj = wired_defesa.find.call_args[0][1]
        for hidden in ("created_by", "submetido_por", "aprovado_por", "motivo_rejeicao"):
            assert proj.get(hidden) == 0

    async def test_filtro_tipo(self, wired_defesa):
        await public_route.public_list_defesa(tipo="tomada_posicao")
        assert wired_defesa.find.call_args[0][0]["tipo"] == "tomada_posicao"

    async def test_tipo_invalido_400(self, wired_defesa):
        with pytest.raises(HTTPException) as exc:
            await public_route.public_list_defesa(tipo="xpto")
        assert exc.value.status_code == 400

    async def test_get_aplica_recorte(self, wired_defesa):
        wired_defesa.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await public_route.public_get_defesa(defesa_id="d1")
        assert exc.value.status_code == 404
        filt = wired_defesa.find_one.call_args[0][0]
        assert filt == {"id": "d1", "status": "publicado", "visibility": "publico"}

    async def test_get_devolve_quando_publico(self, wired_defesa):
        wired_defesa.find_one = AsyncMock(
            return_value={"id": "d1", "titulo": "X", "status": "publicado", "visibility": "publico"}
        )
        result = await public_route.public_get_defesa(defesa_id="d1")
        assert result["id"] == "d1"


# --------------------------------------------------------------------------- #
# Relações externas
# --------------------------------------------------------------------------- #


class TestPublicRelacoes:
    async def test_so_publico(self, wired_relacoes):
        await public_route.public_list_relacoes()
        assert wired_relacoes.find.call_args[0][0]["visibility"] == "publico"

    async def test_projecao_esconde_contacto_e_quota(self, wired_relacoes):
        await public_route.public_list_relacoes()
        proj = wired_relacoes.find.call_args[0][1]
        assert proj.get("contacto") == 0
        assert proj.get("quota_anual") == 0
        assert proj.get("created_by") == 0

    async def test_filtro_estado(self, wired_relacoes):
        await public_route.public_list_relacoes(estado_filiacao="filiado")
        assert wired_relacoes.find.call_args[0][0]["estado_filiacao"] == "filiado"

    async def test_estado_invalido_400(self, wired_relacoes):
        with pytest.raises(HTTPException) as exc:
            await public_route.public_list_relacoes(estado_filiacao="xpto")
        assert exc.value.status_code == 400


# --------------------------------------------------------------------------- #
# Publicações
# --------------------------------------------------------------------------- #


class TestPublicPublicacoes:
    async def test_so_publico(self, wired_publicacoes):
        await public_route.public_list_publicacoes()
        assert wired_publicacoes.find.call_args[0][0]["visibility"] == "publico"

    async def test_projecao_esconde_venda(self, wired_publicacoes):
        await public_route.public_list_publicacoes()
        proj = wired_publicacoes.find.call_args[0][1]
        assert proj.get("a_venda") == 0
        assert proj.get("preco") == 0

    async def test_get_aplica_recorte(self, wired_publicacoes):
        wired_publicacoes.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await public_route.public_get_publicacao(publicacao_id="p1")
        assert exc.value.status_code == 404
        assert wired_publicacoes.find_one.call_args[0][0] == {"id": "p1", "visibility": "publico"}

    async def test_tipo_invalido_400(self, wired_publicacoes):
        with pytest.raises(HTTPException) as exc:
            await public_route.public_list_publicacoes(tipo="xpto")
        assert exc.value.status_code == 400


# --------------------------------------------------------------------------- #
# Formações
# --------------------------------------------------------------------------- #


class TestPublicFormacoes:
    async def test_so_publico_e_ativo(self, wired_formacoes):
        await public_route.public_list_formacoes()
        query = wired_formacoes.find.call_args[0][0]
        assert query["visibility"] == "publico"
        assert query["ativo"] is True

    async def test_filtro_tipo(self, wired_formacoes):
        await public_route.public_list_formacoes(tipo="certificacao")
        assert wired_formacoes.find.call_args[0][0]["tipo"] == "certificacao"

    async def test_tipo_invalido_400(self, wired_formacoes):
        with pytest.raises(HTTPException) as exc:
            await public_route.public_list_formacoes(tipo="xpto")
        assert exc.value.status_code == 400
