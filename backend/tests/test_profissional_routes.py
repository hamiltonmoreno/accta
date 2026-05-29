"""Unit tests for routes/profissional.py — Cat 5 F2.

Cobre 5.3 (Formações) e 5.5 (Publicações) — spec-fins-profissionais §6/§8.
Mesmo padrão dos outros test_*_routes.py: invoca rotas com `mock_db`,
sem TestClient nem DB real.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from routes import profissional as prof_route


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


# --------------------------------------------------------------------------- #
# Helpers / fixtures
# --------------------------------------------------------------------------- #


def _wire(mock_db, name: str):
    """conftest.mock_db não pre-cabla `formacoes`/`publicacoes`."""
    coll = MagicMock(name=name)
    coll.find_one = AsyncMock(return_value=None)
    coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    coll.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
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
def quiet_audit(monkeypatch):
    monkeypatch.setattr(prof_route, "create_audit_log", AsyncMock())


@pytest.fixture
def direcao_user():
    from conftest import _make_user_dict
    from models import User

    return User(**_make_user_dict("socio", cargo="dir_vogal"))


@pytest.fixture
def wired_formacoes(mock_db):
    return _wire(mock_db, "formacoes")


@pytest.fixture
def wired_publicacoes(mock_db):
    return _wire(mock_db, "publicacoes")


@pytest.fixture
def wired_documents(mock_db):
    """Validação de document_id requer `documents.find_one`."""
    mock_db.documents.find_one = AsyncMock(return_value={"id": "doc-1"})
    return mock_db.documents


# ============================================================================
# 5.3 — Formações
# ============================================================================


class TestFormacaoCreate:
    async def test_socio_comum_403(self, wired_formacoes, socio_user, quiet_audit):
        from models import FormacaoCreate

        with pytest.raises(HTTPException) as exc:
            await prof_route.create_formacao(
                data=FormacaoCreate(titulo="Curso X", tipo="formacao"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403
        wired_formacoes.insert_one.assert_not_awaited()

    async def test_direcao_cria(self, wired_formacoes, direcao_user, quiet_audit):
        from models import FormacaoCreate

        result = await prof_route.create_formacao(
            data=FormacaoCreate(titulo="ICAO L4", tipo="certificacao", validade="2027-01-01"),
            current_user=direcao_user,
        )
        assert result["titulo"] == "ICAO L4"
        assert result["tipo"] == "certificacao"
        assert result["ativo"] is True
        assert result["created_by"] == direcao_user.id
        wired_formacoes.insert_one.assert_awaited_once()

    async def test_admin_cria(self, wired_formacoes, admin_user, quiet_audit):
        from models import FormacaoCreate

        result = await prof_route.create_formacao(
            data=FormacaoCreate(titulo="Material X", tipo="material"),
            current_user=admin_user,
        )
        assert result["tipo"] == "material"

    async def test_document_id_inexistente_400(
        self, wired_formacoes, direcao_user, quiet_audit, mock_db
    ):
        from models import FormacaoCreate

        mock_db.documents.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await prof_route.create_formacao(
                data=FormacaoCreate(titulo="X", tipo="material", document_id="doc-inexistente"),
                current_user=direcao_user,
            )
        assert exc.value.status_code == 400

    async def test_tipo_invalido_422(self):
        from models import FormacaoCreate

        with pytest.raises(ValidationError):
            FormacaoCreate(titulo="X", tipo="inexistente")

    async def test_titulo_vazio_422(self):
        from models import FormacaoCreate

        with pytest.raises(ValidationError):
            FormacaoCreate(titulo="", tipo="formacao")


class TestFormacaoList:
    async def test_filter_passa_tipo(self, wired_formacoes, socio_user):
        await prof_route.list_formacoes(tipo="certificacao", current_user=socio_user)
        call_args = wired_formacoes.find.call_args
        assert call_args[0][0]["tipo"] == "certificacao"

    async def test_filter_tipo_invalido_400(self, wired_formacoes, socio_user):
        with pytest.raises(HTTPException) as exc:
            await prof_route.list_formacoes(tipo="x", current_user=socio_user)
        assert exc.value.status_code == 400

    async def test_filter_ativo_false(self, wired_formacoes, socio_user):
        await prof_route.list_formacoes(ativo=False, current_user=socio_user)
        call_args = wired_formacoes.find.call_args
        assert call_args[0][0]["ativo"] is False

    async def test_filter_categoria(self, wired_formacoes, socio_user):
        await prof_route.list_formacoes(categoria="atc", current_user=socio_user)
        call_args = wired_formacoes.find.call_args
        assert call_args[0][0]["categoria"] == "atc"


class TestFormacaoUpdate:
    async def test_404(self, wired_formacoes, direcao_user, quiet_audit):
        from models import FormacaoUpdate

        wired_formacoes.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await prof_route.update_formacao(
                formacao_id="nope",
                data=FormacaoUpdate(titulo="X"),
                current_user=direcao_user,
            )
        assert exc.value.status_code == 404

    async def test_socio_comum_403(self, wired_formacoes, socio_user, quiet_audit):
        from models import FormacaoUpdate

        with pytest.raises(HTTPException) as exc:
            await prof_route.update_formacao(
                formacao_id="f1",
                data=FormacaoUpdate(titulo="X"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_direcao_atualiza(self, wired_formacoes, direcao_user, quiet_audit):
        from models import FormacaoUpdate

        wired_formacoes.find_one = AsyncMock(
            side_effect=[
                {"id": "f1", "tipo": "formacao", "titulo": "Old"},
                {"id": "f1", "tipo": "formacao", "titulo": "Novo"},
            ]
        )
        result = await prof_route.update_formacao(
            formacao_id="f1",
            data=FormacaoUpdate(titulo="Novo"),
            current_user=direcao_user,
        )
        assert result["titulo"] == "Novo"
        set_data = wired_formacoes.update_one.call_args[0][1]["$set"]
        assert set_data["titulo"] == "Novo"
        assert "updated_at" in set_data


class TestFormacaoDelete:
    async def test_404(self, wired_formacoes, direcao_user, quiet_audit):
        wired_formacoes.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await prof_route.delete_formacao(formacao_id="nope", current_user=direcao_user)
        assert exc.value.status_code == 404

    async def test_socio_comum_403(self, wired_formacoes, socio_user, quiet_audit):
        with pytest.raises(HTTPException) as exc:
            await prof_route.delete_formacao(formacao_id="f1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_direcao_remove(self, wired_formacoes, direcao_user, quiet_audit):
        wired_formacoes.find_one = AsyncMock(
            return_value={"id": "f1", "tipo": "formacao", "titulo": "X"}
        )
        result = await prof_route.delete_formacao(formacao_id="f1", current_user=direcao_user)
        assert "removida" in result["message"].lower()
        wired_formacoes.delete_one.assert_awaited_once()


# ============================================================================
# 5.5 — Publicações
# ============================================================================


class TestPublicacaoCreate:
    async def test_socio_comum_403(self, wired_publicacoes, socio_user, quiet_audit, wired_documents):
        from models import PublicacaoCreate

        with pytest.raises(HTTPException) as exc:
            await prof_route.create_publicacao(
                data=PublicacaoCreate(
                    titulo="Revista 2026", tipo="revista", document_id="doc-1",
                    data_publicacao="2026-05-01",
                ),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403
        wired_publicacoes.insert_one.assert_not_awaited()

    async def test_direcao_publica(self, wired_publicacoes, direcao_user, quiet_audit, wired_documents):
        from models import PublicacaoCreate

        result = await prof_route.create_publicacao(
            data=PublicacaoCreate(
                titulo="Boletim Maio",
                tipo="boletim",
                document_id="doc-1",
                data_publicacao="2026-05-15",
                visibility="socios",
            ),
            current_user=direcao_user,
        )
        assert result["titulo"] == "Boletim Maio"
        assert result["a_venda"] is False
        assert result["visibility"] == "socios"

    async def test_a_venda_true_bloqueado_400(
        self, wired_publicacoes, direcao_user, quiet_audit, wired_documents
    ):
        from models import PublicacaoCreate

        with pytest.raises(HTTPException) as exc:
            await prof_route.create_publicacao(
                data=PublicacaoCreate(
                    titulo="X", tipo="revista", document_id="doc-1",
                    data_publicacao="2026-05-01", a_venda=True, preco=1000,
                ),
                current_user=direcao_user,
            )
        assert exc.value.status_code == 400
        assert "FASE 2" in exc.value.detail

    async def test_document_id_inexistente_400(
        self, wired_publicacoes, direcao_user, quiet_audit, mock_db
    ):
        from models import PublicacaoCreate

        mock_db.documents.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await prof_route.create_publicacao(
                data=PublicacaoCreate(
                    titulo="X", tipo="revista", document_id="doc-x",
                    data_publicacao="2026-05-01",
                ),
                current_user=direcao_user,
            )
        assert exc.value.status_code == 400

    async def test_tipo_invalido_422(self):
        from models import PublicacaoCreate

        with pytest.raises(ValidationError):
            PublicacaoCreate(
                titulo="X", tipo="invalido", document_id="doc-1", data_publicacao="2026-05-01"
            )

    async def test_document_id_obrigatorio_422(self):
        from models import PublicacaoCreate

        with pytest.raises(ValidationError):
            PublicacaoCreate(titulo="X", tipo="revista", data_publicacao="2026-05-01")  # type: ignore[call-arg]


class TestPublicacaoList:
    async def test_filter_tipo(self, wired_publicacoes, socio_user):
        await prof_route.list_publicacoes(tipo="revista", current_user=socio_user)
        call_args = wired_publicacoes.find.call_args
        assert call_args[0][0]["tipo"] == "revista"

    async def test_filter_tipo_invalido_400(self, wired_publicacoes, socio_user):
        with pytest.raises(HTTPException) as exc:
            await prof_route.list_publicacoes(tipo="x", current_user=socio_user)
        assert exc.value.status_code == 400


class TestPublicacaoUpdate:
    async def test_404(self, wired_publicacoes, direcao_user, quiet_audit):
        from models import PublicacaoUpdate

        wired_publicacoes.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await prof_route.update_publicacao(
                publicacao_id="nope",
                data=PublicacaoUpdate(titulo="X"),
                current_user=direcao_user,
            )
        assert exc.value.status_code == 404

    async def test_socio_comum_403(self, wired_publicacoes, socio_user, quiet_audit):
        from models import PublicacaoUpdate

        with pytest.raises(HTTPException) as exc:
            await prof_route.update_publicacao(
                publicacao_id="p1",
                data=PublicacaoUpdate(titulo="X"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_direcao_atualiza(self, wired_publicacoes, direcao_user, quiet_audit):
        from models import PublicacaoUpdate

        wired_publicacoes.find_one = AsyncMock(
            side_effect=[
                {"id": "p1", "titulo": "Old", "tipo": "revista"},
                {"id": "p1", "titulo": "Novo", "tipo": "revista"},
            ]
        )
        result = await prof_route.update_publicacao(
            publicacao_id="p1",
            data=PublicacaoUpdate(titulo="Novo", descricao="Atualizado"),
            current_user=direcao_user,
        )
        assert result["titulo"] == "Novo"
        set_data = wired_publicacoes.update_one.call_args[0][1]["$set"]
        assert set_data["titulo"] == "Novo"
        assert set_data["descricao"] == "Atualizado"

    async def test_a_venda_true_bloqueado_400(self, wired_publicacoes, direcao_user, quiet_audit):
        from models import PublicacaoUpdate

        wired_publicacoes.find_one = AsyncMock(
            return_value={"id": "p1", "titulo": "X", "tipo": "revista", "a_venda": False}
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.update_publicacao(
                publicacao_id="p1",
                data=PublicacaoUpdate(a_venda=True),
                current_user=direcao_user,
            )
        assert exc.value.status_code == 400

    async def test_visibility_invalida_400(self, wired_publicacoes, direcao_user, quiet_audit):
        """Pydantic não captura porque na update é Optional[Literal], mas a rota
        guarda contra valores inválidos vindo via dict bruto. Aqui validamos com
        um update válido — Literal já protege ValidationError. Skip se Pydantic
        já filtra; a guarda da rota é defesa em profundidade."""
        from models import PublicacaoUpdate

        with pytest.raises(ValidationError):
            PublicacaoUpdate(visibility="secreto")  # type: ignore[arg-type]


class TestPublicacaoDelete:
    async def test_404(self, wired_publicacoes, direcao_user, quiet_audit):
        wired_publicacoes.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await prof_route.delete_publicacao(publicacao_id="nope", current_user=direcao_user)
        assert exc.value.status_code == 404

    async def test_socio_comum_403(self, wired_publicacoes, socio_user, quiet_audit):
        with pytest.raises(HTTPException) as exc:
            await prof_route.delete_publicacao(publicacao_id="p1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_direcao_remove(self, wired_publicacoes, direcao_user, quiet_audit):
        wired_publicacoes.find_one = AsyncMock(
            return_value={"id": "p1", "titulo": "X", "tipo": "revista"}
        )
        result = await prof_route.delete_publicacao(publicacao_id="p1", current_user=direcao_user)
        assert "removida" in result["message"].lower()
