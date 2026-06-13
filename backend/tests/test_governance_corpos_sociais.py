"""Endpoint público GET /api/governance/corpos-sociais (spec-sobre §3)."""

from unittest.mock import MagicMock

import pytest

from routes import governance  # importa p/ o patch de db do conftest aterrar


class _Cursor:
    """Cursor mínimo compatível com o DAO: find(...).to_list(n)."""

    def __init__(self, docs):
        self._docs = docs

    async def to_list(self, n):
        return self._docs[:n]


def _wire_holders(mock_db, holders_by_cargo):
    """Configura users.find p/ devolver titulares por cargo.

    Pedir a fixture `mock_db` garante que o conftest já fez o patch de
    `routes.governance.db` -> mock_db (senão `governance.db` seria o DAO real).
    """

    def _find(filtro, projection=None):
        cargo = filtro.get("cargo")
        return _Cursor(list(holders_by_cargo.get(cargo, [])))

    mock_db.users.find = MagicMock(side_effect=_find)


@pytest.mark.asyncio
async def test_estrutura_completa_mesmo_sem_titulares(mock_db):
    _wire_holders(mock_db, {})
    res = await governance.get_corpos_sociais()
    data = res.model_dump()

    ids = [o["id"] for o in data["orgaos"]]
    assert ids == ["assembleia_geral", "direcao", "conselho_fiscal"]
    # AG mostra-se como "Mesa da Assembleia Geral"
    assert data["orgaos"][0]["nome"] == "Mesa da Assembleia Geral"
    # todos os cargos presentes, todos "Vago" (titulares == [])
    for orgao in data["orgaos"]:
        assert orgao["cargos"], f"órgão {orgao['id']} sem cargos"
        for cargo in orgao["cargos"]:
            assert cargo["titulares"] == []


@pytest.mark.asyncio
async def test_titular_ativo_aparece_sem_campos_sensiveis(mock_db):
    _wire_holders(mock_db, {"dir_presidente": [{"name": "Ana Silva", "photo_url": "/uploads/avatars/ana.jpg"}]})
    res = await governance.get_corpos_sociais()
    data = res.model_dump()

    direcao = next(o for o in data["orgaos"] if o["id"] == "direcao")
    pres = next(c for c in direcao["cargos"] if c["key"] == "dir_presidente")
    assert pres["titulares"] == [{"name": "Ana Silva", "photo_url": "/uploads/avatars/ana.jpg"}]
    # nenhum campo sensível na serialização
    assert set(pres["titulares"][0].keys()) == {"name", "photo_url"}


@pytest.mark.asyncio
async def test_filtro_so_membros_ativos_estatutarios(mock_db):
    """O endpoint filtra por cargo+status+membro; o teste confirma o filtro."""
    capturado = {}

    def _find(filtro, projection=None):
        capturado.update(filtro)
        return _Cursor([])

    mock_db.users.find = MagicMock(side_effect=_find)
    await governance.get_corpos_sociais()

    assert capturado.get("status") == "ativo"
    assert "$or" in capturado  # _MEMBER_FILTER (account_type member/ausente)
    assert capturado["$or"] == [
        {"account_type": "member"},
        {"account_type": {"$exists": False}},
    ]


@pytest.mark.asyncio
async def test_cargos_ordenados_por_ordem(mock_db):
    _wire_holders(mock_db, {})
    res = await governance.get_corpos_sociais()
    data = res.model_dump()
    for orgao in data["orgaos"]:
        ordens = [c["ordem"] for c in orgao["cargos"]]
        assert ordens == sorted(ordens)
