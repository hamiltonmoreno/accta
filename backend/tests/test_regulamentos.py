"""Unit tests — Regulamentos internos versionados (spec-ciclo §6, Art. 31.j/56).

Cobre os endpoints de `routes/regulamentos.py` sem DB real (mock_db). As
colecções `regulamentos`, `regulamento_versoes` e `assembleia_deliberacoes` NÃO
estão pré-ligadas no `conftest.mock_db` — são ligadas em-teste por `_wire`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from models import (
    RegulamentoCreate,
    RegulamentoVersaoAprovar,
    RegulamentoVersaoCreate,
    RegulamentoVersaoRevogar,
    User,
)
from routes import regulamentos as reg_route

pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------- #
# Factories / wiring
# --------------------------------------------------------------------------- #


def _user(role="socio", cargo="socio", privileges=None, uid=None) -> User:
    return User(
        id=uid or str(uuid.uuid4()),
        name=f"Test {role}",
        email=f"{uuid.uuid4().hex[:6]}@example.cv",
        role=role,
        status="ativo",
        cargo=cargo,
        privileges=privileges or [],
        consent_data=True,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def _coll(find_one=None, find_list=None):
    coll = MagicMock()
    coll.find_one = AsyncMock(return_value=find_one)
    coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=find_list or [])
    cur.sort = MagicMock(return_value=cur)
    cur.limit = MagicMock(return_value=cur)
    coll.find = MagicMock(return_value=cur)
    return coll


def _wire(mock_db, *, reg=None, versao=None, versoes_list=None, delib=None, doc_exists=True):
    mock_db.regulamentos = _coll(find_one=reg)
    mock_db.regulamento_versoes = _coll(find_one=versao, find_list=versoes_list)
    mock_db.assembleia_deliberacoes = _coll(find_one=delib)
    mock_db.documents.find_one = AsyncMock(return_value=({"id": "doc1"} if doc_exists else None))
    return mock_db


def _reg(competencia="direcao", current_version_id=None, **kw):
    base = {
        "id": "r1",
        "slug": "regulamento-x",
        "titulo": "Regulamento X",
        "competencia_aprovacao": competencia,
        "current_version_id": current_version_id,
    }
    base.update(kw)
    return base


def _versao(status="em_aprovacao", vid="vnew", versao=2, **kw):
    base = {
        "id": vid,
        "regulamento_id": "r1",
        "versao": versao,
        "document_id": "doc1",
        "status": status,
    }
    base.update(kw)
    return base


# --------------------------------------------------------------------------- #
# Criar regulamento
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestCreateRegulamento:
    async def test_socio_403(self, mock_db):
        _wire(mock_db)
        with pytest.raises(HTTPException) as e:
            await reg_route.create_regulamento(
                RegulamentoCreate(slug="reg-novo", titulo="Reg Novo"), current_user=_user("socio")
            )
        assert e.value.status_code == 403

    async def test_slug_duplicado_400(self, mock_db):
        _wire(mock_db, reg=_reg())  # slug já existe
        with pytest.raises(HTTPException) as e:
            await reg_route.create_regulamento(
                RegulamentoCreate(slug="regulamento-x", titulo="Dup"), current_user=_user("admin")
            )
        assert e.value.status_code == 400

    async def test_admin_cria_ok(self, mock_db):
        _wire(mock_db, reg=None)
        out = await reg_route.create_regulamento(
            RegulamentoCreate(slug="reg-novo", titulo="Reg Novo", competencia_aprovacao="direcao"),
            current_user=_user("admin"),
        )
        assert out.slug == "reg-novo"
        mock_db.regulamentos.insert_one.assert_awaited_once()

    async def test_direcao_cria_ok(self, mock_db):
        _wire(mock_db, reg=None)
        out = await reg_route.create_regulamento(
            RegulamentoCreate(slug="reg-dir", titulo="Reg Dir"),
            current_user=_user("socio", "dir_secretario"),
        )
        assert out.slug == "reg-dir"


# --------------------------------------------------------------------------- #
# Criar versão
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestCreateVersao:
    async def test_documento_inexistente_400(self, mock_db):
        _wire(mock_db, reg=_reg(), doc_exists=False)
        with pytest.raises(HTTPException) as e:
            await reg_route.create_versao(
                "r1", RegulamentoVersaoCreate(document_id="doc-x"), current_user=_user("admin")
            )
        assert e.value.status_code == 400

    async def test_regulamento_inexistente_404(self, mock_db):
        _wire(mock_db, reg=None)
        with pytest.raises(HTTPException) as e:
            await reg_route.create_versao(
                "r1", RegulamentoVersaoCreate(document_id="doc1"), current_user=_user("admin")
            )
        assert e.value.status_code == 404

    async def test_proxima_versao_incrementa(self, mock_db):
        _wire(mock_db, reg=_reg(), versoes_list=[{"versao": 1}, {"versao": 2}])
        out = await reg_route.create_versao(
            "r1", RegulamentoVersaoCreate(document_id="doc1"), current_user=_user("admin")
        )
        assert out.versao == 3
        assert out.status == "rascunho"

    async def test_primeira_versao_e_1(self, mock_db):
        _wire(mock_db, reg=_reg(), versoes_list=[])
        out = await reg_route.create_versao(
            "r1", RegulamentoVersaoCreate(document_id="doc1"), current_user=_user("admin")
        )
        assert out.versao == 1


# --------------------------------------------------------------------------- #
# Submeter
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestSubmeter:
    async def test_rascunho_para_em_aprovacao(self, mock_db):
        _wire(mock_db, reg=_reg(), versao=_versao(status="rascunho"))
        out = await reg_route.submeter_versao("r1", "vnew", current_user=_user("admin"))
        assert out["status"] == "em_aprovacao"
        mock_db.regulamento_versoes.update_one.assert_awaited()

    async def test_nao_rascunho_400(self, mock_db):
        _wire(mock_db, reg=_reg(), versao=_versao(status="aprovado"))
        with pytest.raises(HTTPException) as e:
            await reg_route.submeter_versao("r1", "vnew", current_user=_user("admin"))
        assert e.value.status_code == 400


# --------------------------------------------------------------------------- #
# Aprovar
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestAprovar:
    async def test_direcao_aprova_e_revoga_anterior(self, mock_db):
        _wire(mock_db, reg=_reg(competencia="direcao", current_version_id="vold"), versao=_versao())
        await reg_route.aprovar_versao(
            "r1", "vnew", RegulamentoVersaoAprovar(), current_user=_user("socio", "dir_presidente")
        )
        calls = mock_db.regulamento_versoes.update_one.call_args_list
        revogou_anterior = any(
            c.args[0] == {"id": "vold"} and c.args[1]["$set"].get("status") == "revogado" for c in calls
        )
        aprovou_nova = any(
            c.args[0] == {"id": "vnew"} and c.args[1]["$set"].get("status") == "aprovado" for c in calls
        )
        assert revogou_anterior and aprovou_nova
        # regulamento aponta para a nova versão
        reg_update = mock_db.regulamentos.update_one.call_args.args[1]["$set"]
        assert reg_update["current_version_id"] == "vnew"

    async def test_versao_nao_em_aprovacao_400(self, mock_db):
        _wire(mock_db, reg=_reg(), versao=_versao(status="rascunho"))
        with pytest.raises(HTTPException) as e:
            await reg_route.aprovar_versao(
                "r1", "vnew", RegulamentoVersaoAprovar(), current_user=_user("socio", "dir_presidente")
            )
        assert e.value.status_code == 400

    async def test_competencia_ag_sem_deliberacao_400(self, mock_db):
        _wire(mock_db, reg=_reg(competencia="assembleia_geral"), versao=_versao())
        with pytest.raises(HTTPException) as e:
            await reg_route.aprovar_versao(
                "r1", "vnew", RegulamentoVersaoAprovar(), current_user=_user("socio", "ag_presidente")
            )
        assert e.value.status_code == 400

    async def test_competencia_ag_nao_mesa_403(self, mock_db):
        _wire(mock_db, reg=_reg(competencia="assembleia_geral"), versao=_versao())
        with pytest.raises(HTTPException) as e:
            await reg_route.aprovar_versao(
                "r1",
                "vnew",
                RegulamentoVersaoAprovar(deliberacao_id="d1"),
                current_user=_user("socio", "dir_presidente"),  # Direção, não Mesa AG
            )
        assert e.value.status_code == 403

    async def test_competencia_ag_deliberacao_nao_aprovada_400(self, mock_db):
        _wire(
            mock_db,
            reg=_reg(competencia="assembleia_geral"),
            versao=_versao(),
            delib={"id": "d1", "aprovado": False},
        )
        with pytest.raises(HTTPException) as e:
            await reg_route.aprovar_versao(
                "r1",
                "vnew",
                RegulamentoVersaoAprovar(deliberacao_id="d1"),
                current_user=_user("socio", "ag_presidente"),
            )
        assert e.value.status_code == 400

    async def test_competencia_ag_mesa_com_deliberacao_ok(self, mock_db):
        _wire(
            mock_db,
            reg=_reg(competencia="assembleia_geral"),
            versao=_versao(),
            delib={"id": "d1", "aprovado": True},
        )
        await reg_route.aprovar_versao(
            "r1",
            "vnew",
            RegulamentoVersaoAprovar(deliberacao_id="d1", assembleia_id="a1"),
            current_user=_user("socio", "ag_secretario"),
        )
        set_ = next(
            c.args[1]["$set"]
            for c in mock_db.regulamento_versoes.update_one.call_args_list
            if c.args[0] == {"id": "vnew"}
        )
        assert set_["status"] == "aprovado"
        assert set_["deliberacao_id"] == "d1"


# --------------------------------------------------------------------------- #
# Revogar
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestRevogar:
    async def test_revoga_e_limpa_current(self, mock_db):
        _wire(mock_db, reg=_reg(current_version_id="vnew"), versao=_versao(status="aprovado"))
        out = await reg_route.revogar_versao(
            "r1", "vnew", RegulamentoVersaoRevogar(motivo="obsoleto"), current_user=_user("admin")
        )
        assert out["status"] == "revogado"
        # como era a versão em vigor, current_version_id é limpo
        reg_update = mock_db.regulamentos.update_one.call_args.args[1]["$set"]
        assert reg_update["current_version_id"] is None

    async def test_ja_revogada_400(self, mock_db):
        _wire(mock_db, reg=_reg(), versao=_versao(status="revogado"))
        with pytest.raises(HTTPException) as e:
            await reg_route.revogar_versao(
                "r1", "vnew", RegulamentoVersaoRevogar(), current_user=_user("admin")
            )
        assert e.value.status_code == 400


# --------------------------------------------------------------------------- #
# Seed do Regimento da AG
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestSeed:
    async def test_idempotente_existente(self, mock_db):
        _wire(mock_db, reg={"id": "r1"})  # já existe
        await reg_route.seed_default_regulamentos()
        mock_db.regulamentos.insert_one.assert_not_awaited()

    async def test_cria_regimento_ag(self, mock_db):
        _wire(mock_db, reg=None)  # não existe
        await reg_route.seed_default_regulamentos()
        mock_db.regulamentos.insert_one.assert_awaited_once()
        doc = mock_db.regulamentos.insert_one.call_args.args[0]
        assert doc["slug"] == "regimento-ag"
        assert doc["competencia_aprovacao"] == "assembleia_geral"


# --------------------------------------------------------------------------- #
# Validador de slug (modelo)
# --------------------------------------------------------------------------- #


class TestSlugValidator:
    def test_rejeita_invalido(self):
        with pytest.raises(ValidationError):
            RegulamentoCreate(slug="Regimento AG", titulo="Regimento")

    def test_normaliza_maiusculas(self):
        assert RegulamentoCreate(slug="Regimento-AG", titulo="Regimento").slug == "regimento-ag"


# --------------------------------------------------------------------------- #
# Visibilidade para não-gestores (sócios comuns não veem rascunhos)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestVisibilidadeNaoGestor:
    async def test_list_oculta_rascunhos_a_socio(self, mock_db):
        # r1 tem versão em vigor aprovada (visível); r2 sem versão aprovada (oculto).
        mock_db.regulamentos = _coll(
            find_list=[
                _reg(id="r1", current_version_id="v-aprovada"),
                _reg(id="r2", current_version_id=None),
            ]
        )
        mock_db.regulamento_versoes = _coll(
            find_list=[{"id": "v-aprovada", "status": "aprovado"}]
        )
        out = await reg_route.list_regulamentos(current_user=_user("socio"))
        assert [r["id"] for r in out["items"]] == ["r1"]
        assert out["total"] == 1

    async def test_list_gestor_ve_tudo(self, mock_db):
        mock_db.regulamentos = _coll(
            find_list=[_reg(id="r1", current_version_id=None), _reg(id="r2", current_version_id=None)]
        )
        mock_db.regulamento_versoes = _coll()
        out = await reg_route.list_regulamentos(current_user=_user("socio", "dir_secretario"))
        assert {r["id"] for r in out["items"]} == {"r1", "r2"}
        assert out["total"] == 2

    async def test_get_socio_filtra_versoes_nao_aprovadas(self, mock_db):
        _wire(
            mock_db,
            reg=_reg(id="r1"),
            versoes_list=[
                _versao(status="aprovado", vid="v1", versao=1),
                _versao(status="rascunho", vid="v2", versao=2),
            ],
        )
        out = await reg_route.get_regulamento("r1", current_user=_user("socio"))
        assert [v["status"] for v in out["versoes"]] == ["aprovado"]

    async def test_get_socio_sem_versao_aprovada_404(self, mock_db):
        _wire(mock_db, reg=_reg(id="r1"), versoes_list=[_versao(status="rascunho", vid="v2", versao=2)])
        with pytest.raises(HTTPException) as e:
            await reg_route.get_regulamento("r1", current_user=_user("socio"))
        assert e.value.status_code == 404

    async def test_get_gestor_ve_rascunhos(self, mock_db):
        _wire(mock_db, reg=_reg(id="r1"), versoes_list=[_versao(status="rascunho", vid="v2", versao=2)])
        out = await reg_route.get_regulamento("r1", current_user=_user("socio", "dir_secretario"))
        assert [v["status"] for v in out["versoes"]] == ["rascunho"]
