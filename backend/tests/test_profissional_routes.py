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

    async def test_document_id_inexistente_400(self, wired_formacoes, direcao_user, quiet_audit, mock_db):
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
        wired_formacoes.find_one = AsyncMock(return_value={"id": "f1", "tipo": "formacao", "titulo": "X"})
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
                    titulo="Revista 2026",
                    tipo="revista",
                    document_id="doc-1",
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

    async def test_a_venda_true_bloqueado_400(self, wired_publicacoes, direcao_user, quiet_audit, wired_documents):
        from models import PublicacaoCreate

        with pytest.raises(HTTPException) as exc:
            await prof_route.create_publicacao(
                data=PublicacaoCreate(
                    titulo="X",
                    tipo="revista",
                    document_id="doc-1",
                    data_publicacao="2026-05-01",
                    a_venda=True,
                    preco=1000,
                ),
                current_user=direcao_user,
            )
        assert exc.value.status_code == 400
        assert "FASE 2" in exc.value.detail

    async def test_document_id_inexistente_400(self, wired_publicacoes, direcao_user, quiet_audit, mock_db):
        from models import PublicacaoCreate

        mock_db.documents.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await prof_route.create_publicacao(
                data=PublicacaoCreate(
                    titulo="X",
                    tipo="revista",
                    document_id="doc-x",
                    data_publicacao="2026-05-01",
                ),
                current_user=direcao_user,
            )
        assert exc.value.status_code == 400

    async def test_tipo_invalido_422(self):
        from models import PublicacaoCreate

        with pytest.raises(ValidationError):
            PublicacaoCreate(titulo="X", tipo="invalido", document_id="doc-1", data_publicacao="2026-05-01")

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
        wired_publicacoes.find_one = AsyncMock(return_value={"id": "p1", "titulo": "X", "tipo": "revista"})
        result = await prof_route.delete_publicacao(publicacao_id="p1", current_user=direcao_user)
        assert "removida" in result["message"].lower()


# ============================================================================
# Cat 5 F3 — 5.2 Defesa Profissional (workflow com aprovacao da Direccao)
# ============================================================================


@pytest.fixture
def wired_defesa(mock_db):
    return _wire(mock_db, "defesa_profissional")


@pytest.fixture
def wired_relacoes(mock_db):
    return _wire(mock_db, "relacoes_externas")


@pytest.fixture
def quiet_notify(monkeypatch):
    """Notificacoes assincronas — silencia em testes."""
    monkeypatch.setattr(prof_route, "create_notification", AsyncMock())


@pytest.fixture
def direcao_user_2():
    """Segundo membro da Direccao (criador != aprovador na segregacao)."""
    from conftest import _make_user_dict
    from models import User

    d = _make_user_dict("socio", cargo="dir_secretario")
    d["id"] = "direcao-2"
    d["email"] = "secretario@accta.cv"
    return User(**d)


class TestDefesaCreate:
    async def test_socio_comum_403(self, wired_defesa, socio_user, quiet_audit):
        from models import DefesaProfissionalCreate

        with pytest.raises(HTTPException) as exc:
            await prof_route.create_defesa(
                data=DefesaProfissionalCreate(titulo="Posicao X", tipo="tomada_posicao", data="2026-05-29"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_direcao_cria_rascunho(self, wired_defesa, direcao_user, quiet_audit):
        from models import DefesaProfissionalCreate

        result = await prof_route.create_defesa(
            data=DefesaProfissionalCreate(
                titulo="Posicao sobre escalas",
                tipo="tomada_posicao",
                data="2026-05-29",
                descricao="Defesa do regime de escalas atual.",
            ),
            current_user=direcao_user,
        )
        assert result["status"] == "rascunho"
        assert result["created_by"] == direcao_user.id
        assert result["submetido_em"] is None
        wired_defesa.insert_one.assert_awaited_once()

    async def test_tipo_invalido_422(self):
        from models import DefesaProfissionalCreate

        with pytest.raises(ValidationError):
            DefesaProfissionalCreate(titulo="X", tipo="invalido", data="2026-05-29")

    async def test_titulo_vazio_422(self):
        from models import DefesaProfissionalCreate

        with pytest.raises(ValidationError):
            DefesaProfissionalCreate(titulo="", tipo="comunicado", data="2026-05-29")


class TestDefesaList:
    async def test_socio_so_ve_publicado_e_seus(self, wired_defesa, socio_user):
        await prof_route.list_defesa(current_user=socio_user)
        call_args = wired_defesa.find.call_args[0][0]
        # Sócio comum vê publicado OU criado por si.
        assert "$or" in call_args
        assert {"status": "publicado"} in call_args["$or"]
        assert {"created_by": socio_user.id} in call_args["$or"]

    async def test_direcao_ve_tudo(self, wired_defesa, direcao_user):
        await prof_route.list_defesa(current_user=direcao_user)
        call_args = wired_defesa.find.call_args[0][0]
        assert "$or" not in call_args

    async def test_status_invalido_400(self, wired_defesa, direcao_user):
        with pytest.raises(HTTPException) as exc:
            await prof_route.list_defesa(status="rascunhx", current_user=direcao_user)
        assert exc.value.status_code == 400


class TestDefesaGet:
    async def test_404(self, wired_defesa, socio_user):
        wired_defesa.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await prof_route.get_defesa(defesa_id="x", current_user=socio_user)
        assert exc.value.status_code == 404

    async def test_socio_nao_ve_rascunho_alheio(self, wired_defesa, socio_user):
        wired_defesa.find_one = AsyncMock(
            return_value={
                "id": "d1",
                "status": "rascunho",
                "created_by": "outro",
                "titulo": "X",
            }
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.get_defesa(defesa_id="d1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_socio_ve_publicado(self, wired_defesa, socio_user):
        wired_defesa.find_one = AsyncMock(
            return_value={
                "id": "d1",
                "status": "publicado",
                "created_by": "outro",
                "titulo": "X",
            }
        )
        result = await prof_route.get_defesa(defesa_id="d1", current_user=socio_user)
        assert result["status"] == "publicado"


class TestDefesaUpdate:
    async def test_edita_rascunho(self, wired_defesa, direcao_user, quiet_audit):
        from models import DefesaProfissionalUpdate

        first = {"id": "d1", "status": "rascunho", "titulo": "X", "tipo": "comunicado"}
        wired_defesa.find_one = AsyncMock(side_effect=[first, {**first, "titulo": "Novo"}])
        result = await prof_route.update_defesa(
            defesa_id="d1",
            data=DefesaProfissionalUpdate(titulo="Novo"),
            current_user=direcao_user,
        )
        assert result["titulo"] == "Novo"

    async def test_nao_edita_submetido(self, wired_defesa, direcao_user, quiet_audit):
        from models import DefesaProfissionalUpdate

        wired_defesa.find_one = AsyncMock(
            return_value={"id": "d1", "status": "submetido", "titulo": "X", "tipo": "comunicado"}
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.update_defesa(
                defesa_id="d1",
                data=DefesaProfissionalUpdate(titulo="Novo"),
                current_user=direcao_user,
            )
        assert exc.value.status_code == 400

    async def test_nao_edita_publicado(self, wired_defesa, direcao_user, quiet_audit):
        from models import DefesaProfissionalUpdate

        wired_defesa.find_one = AsyncMock(
            return_value={"id": "d1", "status": "publicado", "titulo": "X", "tipo": "comunicado"}
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.update_defesa(
                defesa_id="d1",
                data=DefesaProfissionalUpdate(titulo="Novo"),
                current_user=direcao_user,
            )
        assert exc.value.status_code == 400


class TestDefesaSubmeter:
    async def test_so_autor_ou_direcao_submete(self, wired_defesa, socio_user, quiet_audit):
        wired_defesa.find_one = AsyncMock(
            return_value={"id": "d1", "status": "rascunho", "created_by": "outro", "titulo": "X"}
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.submeter_defesa(defesa_id="d1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_so_rascunho_submetido(self, wired_defesa, direcao_user, quiet_audit):
        wired_defesa.find_one = AsyncMock(
            return_value={
                "id": "d1",
                "status": "submetido",
                "created_by": direcao_user.id,
                "titulo": "X",
            }
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.submeter_defesa(defesa_id="d1", current_user=direcao_user)
        assert exc.value.status_code == 400

    async def test_autor_submete(self, wired_defesa, direcao_user, quiet_audit):
        first = {
            "id": "d1",
            "status": "rascunho",
            "created_by": direcao_user.id,
            "titulo": "X",
            "tipo": "tomada_posicao",
        }
        after = {**first, "status": "submetido", "submetido_por": direcao_user.id}
        wired_defesa.find_one = AsyncMock(side_effect=[first, after])
        result = await prof_route.submeter_defesa(defesa_id="d1", current_user=direcao_user)
        assert result["status"] == "submetido"


class TestDefesaAprovar:
    async def test_so_direcao_aprova(self, wired_defesa, socio_user, quiet_audit):
        with pytest.raises(HTTPException) as exc:
            await prof_route.aprovar_defesa(defesa_id="d1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_segregacao_autor_nao_aprova(self, wired_defesa, direcao_user, quiet_audit, quiet_notify):
        wired_defesa.find_one = AsyncMock(
            return_value={
                "id": "d1",
                "status": "submetido",
                "created_by": direcao_user.id,
                "titulo": "X",
                "tipo": "tomada_posicao",
            }
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.aprovar_defesa(defesa_id="d1", current_user=direcao_user)
        assert exc.value.status_code == 403
        assert "segregacao" in exc.value.detail.lower() or "autor" in exc.value.detail.lower()

    async def test_so_submetido_aprovado(self, wired_defesa, direcao_user, direcao_user_2, quiet_audit, quiet_notify):
        wired_defesa.find_one = AsyncMock(
            return_value={
                "id": "d1",
                "status": "rascunho",
                "created_by": direcao_user.id,
                "titulo": "X",
                "tipo": "tomada_posicao",
            }
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.aprovar_defesa(defesa_id="d1", current_user=direcao_user_2)
        assert exc.value.status_code == 400

    async def test_aprovacao_publica_e_notifica(
        self, wired_defesa, direcao_user, direcao_user_2, quiet_audit, monkeypatch
    ):
        first = {
            "id": "d1",
            "status": "submetido",
            "created_by": direcao_user.id,
            "titulo": "X",
            "tipo": "tomada_posicao",
        }
        after = {**first, "status": "publicado", "aprovado_por": direcao_user_2.id}
        wired_defesa.find_one = AsyncMock(side_effect=[first, after])
        notify_mock = AsyncMock()
        monkeypatch.setattr(prof_route, "create_notification", notify_mock)

        result = await prof_route.aprovar_defesa(defesa_id="d1", current_user=direcao_user_2)
        assert result["status"] == "publicado"
        notify_mock.assert_awaited_once()
        kwargs = notify_mock.call_args.kwargs
        assert kwargs["user_id"] == direcao_user.id
        assert "aprovada" in kwargs["message"].lower()


class TestDefesaRejeitar:
    async def test_so_direcao_rejeita(self, wired_defesa, socio_user, quiet_audit):
        from models import DefesaRejeicao

        with pytest.raises(HTTPException) as exc:
            await prof_route.rejeitar_defesa(
                defesa_id="d1",
                payload=DefesaRejeicao(motivo="nao alinhado"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_segregacao_autor_nao_rejeita(self, wired_defesa, direcao_user, quiet_audit, quiet_notify):
        from models import DefesaRejeicao

        wired_defesa.find_one = AsyncMock(
            return_value={
                "id": "d1",
                "status": "submetido",
                "created_by": direcao_user.id,
                "titulo": "X",
                "tipo": "tomada_posicao",
            }
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.rejeitar_defesa(
                defesa_id="d1",
                payload=DefesaRejeicao(motivo="x"),
                current_user=direcao_user,
            )
        assert exc.value.status_code == 403

    async def test_motivo_obrigatorio_422(self):
        from models import DefesaRejeicao

        with pytest.raises(ValidationError):
            DefesaRejeicao(motivo="")

    async def test_rejeicao_volta_a_rascunho_com_motivo(
        self, wired_defesa, direcao_user, direcao_user_2, quiet_audit, monkeypatch
    ):
        from models import DefesaRejeicao

        first = {
            "id": "d1",
            "status": "submetido",
            "created_by": direcao_user.id,
            "titulo": "X",
            "tipo": "tomada_posicao",
        }
        after = {**first, "status": "rascunho", "motivo_rejeicao": "Falta base legal"}
        wired_defesa.find_one = AsyncMock(side_effect=[first, after])
        notify_mock = AsyncMock()
        monkeypatch.setattr(prof_route, "create_notification", notify_mock)

        result = await prof_route.rejeitar_defesa(
            defesa_id="d1",
            payload=DefesaRejeicao(motivo="Falta base legal"),
            current_user=direcao_user_2,
        )
        assert result["status"] == "rascunho"
        assert result["motivo_rejeicao"] == "Falta base legal"
        notify_mock.assert_awaited_once()


class TestDefesaArquivar:
    async def test_so_direcao_arquiva(self, wired_defesa, socio_user, quiet_audit):
        with pytest.raises(HTTPException) as exc:
            await prof_route.arquivar_defesa(defesa_id="d1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_direcao_arquiva(self, wired_defesa, direcao_user, quiet_audit):
        first = {
            "id": "d1",
            "status": "publicado",
            "created_by": "x",
            "titulo": "X",
            "tipo": "comunicado",
        }
        after = {**first, "status": "arquivado", "arquivado_por": direcao_user.id}
        wired_defesa.find_one = AsyncMock(side_effect=[first, after])
        result = await prof_route.arquivar_defesa(defesa_id="d1", current_user=direcao_user)
        assert result["status"] == "arquivado"

    async def test_nao_re_arquiva(self, wired_defesa, direcao_user, quiet_audit):
        wired_defesa.find_one = AsyncMock(
            return_value={"id": "d1", "status": "arquivado", "titulo": "X", "tipo": "comunicado"}
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.arquivar_defesa(defesa_id="d1", current_user=direcao_user)
        assert exc.value.status_code == 400

    async def test_nao_arquiva_submetido(self, wired_defesa, direcao_user, quiet_audit):
        # Arquivar so a partir de publicado: um submetido nao salta a aprovacao.
        wired_defesa.find_one = AsyncMock(
            return_value={"id": "d1", "status": "submetido", "titulo": "X", "tipo": "comunicado"}
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.arquivar_defesa(defesa_id="d1", current_user=direcao_user)
        assert exc.value.status_code == 400

    async def test_nao_arquiva_rascunho(self, wired_defesa, direcao_user, quiet_audit):
        wired_defesa.find_one = AsyncMock(
            return_value={"id": "d1", "status": "rascunho", "titulo": "X", "tipo": "comunicado"}
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.arquivar_defesa(defesa_id="d1", current_user=direcao_user)
        assert exc.value.status_code == 400


class TestDefesaDelete:
    async def test_socio_comum_403(self, wired_defesa, socio_user, quiet_audit):
        with pytest.raises(HTTPException) as exc:
            await prof_route.delete_defesa(defesa_id="d1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_nao_remove_publicado(self, wired_defesa, direcao_user, quiet_audit):
        wired_defesa.find_one = AsyncMock(
            return_value={"id": "d1", "status": "publicado", "titulo": "X", "tipo": "comunicado"}
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.delete_defesa(defesa_id="d1", current_user=direcao_user)
        assert exc.value.status_code == 400

    async def test_direcao_remove_rascunho(self, wired_defesa, direcao_user, quiet_audit):
        wired_defesa.find_one = AsyncMock(
            return_value={"id": "d1", "status": "rascunho", "titulo": "X", "tipo": "comunicado"}
        )
        result = await prof_route.delete_defesa(defesa_id="d1", current_user=direcao_user)
        assert "removido" in result["message"].lower()


# ============================================================================
# Cat 5 F3 — 5.4 Relacoes Externas / IFATCA
# ============================================================================


class TestRelacaoCreate:
    async def test_socio_comum_403(self, wired_relacoes, socio_user, quiet_audit):
        from models import RelacaoExternaCreate

        with pytest.raises(HTTPException) as exc:
            await prof_route.create_relacao(
                data=RelacaoExternaCreate(nome="X", tipo="parceiro"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_direcao_cria(self, wired_relacoes, direcao_user, quiet_audit):
        from models import RelacaoExternaCreate

        result = await prof_route.create_relacao(
            data=RelacaoExternaCreate(
                nome="Eurocontrol",
                tipo="parceiro",
                website="https://eurocontrol.int",
                estado_filiacao="em_negociacao",
            ),
            current_user=direcao_user,
        )
        assert result["nome"] == "Eurocontrol"
        assert result["estado_filiacao"] == "em_negociacao"
        assert result["created_by"] == direcao_user.id
        wired_relacoes.insert_one.assert_awaited_once()

    async def test_tipo_invalido_422(self):
        from models import RelacaoExternaCreate

        with pytest.raises(ValidationError):
            RelacaoExternaCreate(nome="X", tipo="inexistente")

    async def test_estado_invalido_422(self):
        from models import RelacaoExternaCreate

        with pytest.raises(ValidationError):
            RelacaoExternaCreate(nome="X", tipo="parceiro", estado_filiacao="x")


class TestRelacaoList:
    async def test_filtro_estado(self, wired_relacoes, socio_user):
        await prof_route.list_relacoes(estado_filiacao="filiado", current_user=socio_user)
        assert wired_relacoes.find.call_args[0][0]["estado_filiacao"] == "filiado"

    async def test_filtro_tipo(self, wired_relacoes, socio_user):
        await prof_route.list_relacoes(tipo="federacao_internacional", current_user=socio_user)
        assert wired_relacoes.find.call_args[0][0]["tipo"] == "federacao_internacional"


class TestRelacaoUpdate:
    async def test_socio_comum_403(self, wired_relacoes, socio_user, quiet_audit):
        from models import RelacaoExternaUpdate

        with pytest.raises(HTTPException) as exc:
            await prof_route.update_relacao(
                relacao_id="r1",
                data=RelacaoExternaUpdate(estado_filiacao="filiado"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_direcao_atualiza_estado(self, wired_relacoes, direcao_user, quiet_audit):
        from models import RelacaoExternaUpdate

        first = {"id": "r1", "nome": "IFATCA", "tipo": "federacao_internacional"}
        after = {**first, "estado_filiacao": "filiado", "desde": "2026-05-01"}
        wired_relacoes.find_one = AsyncMock(side_effect=[first, after])

        result = await prof_route.update_relacao(
            relacao_id="r1",
            data=RelacaoExternaUpdate(estado_filiacao="filiado", desde="2026-05-01"),
            current_user=direcao_user,
        )
        assert result["estado_filiacao"] == "filiado"


class TestRelacaoDelete:
    async def test_socio_comum_403(self, wired_relacoes, socio_user, quiet_audit):
        with pytest.raises(HTTPException) as exc:
            await prof_route.delete_relacao(relacao_id="r1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_direcao_remove(self, wired_relacoes, direcao_user, quiet_audit):
        wired_relacoes.find_one = AsyncMock(return_value={"id": "r1", "nome": "X"})
        result = await prof_route.delete_relacao(relacao_id="r1", current_user=direcao_user)
        assert "removida" in result["message"].lower()


# ============================================================================
# Seed idempotente IFATCA
# ============================================================================


class TestSeedIfatca:
    async def test_seed_insere_se_ausente(self, wired_relacoes):
        wired_relacoes.find_one = AsyncMock(return_value=None)
        await prof_route.seed_ifatca()
        wired_relacoes.insert_one.assert_awaited_once()
        inserted = wired_relacoes.insert_one.await_args[0][0]
        assert inserted["nome"] == "IFATCA"
        assert inserted["tipo"] == "federacao_internacional"
        assert inserted["visibility"] == "publico"
        assert inserted["estado_filiacao"] == "nao_filiado"

    async def test_seed_idempotente(self, wired_relacoes):
        wired_relacoes.find_one = AsyncMock(return_value={"id": "existente"})
        await prof_route.seed_ifatca()
        wired_relacoes.insert_one.assert_not_awaited()


# ============================================================================
# Cat 5 F3 — reforço pós-review: atomicidade (CAS/409), 404, audit, $set
# ============================================================================


class TestDefesaTransicaoConflito:
    """Compare-and-swap: se o estado muda entre o find_one e o update_one,
    matched_count==0 e a transição devolve 409 (sem publicar nem notificar)."""

    async def test_submeter_conflito_409(self, wired_defesa, direcao_user, quiet_audit):
        wired_defesa.find_one = AsyncMock(
            return_value={
                "id": "d1",
                "status": "rascunho",
                "created_by": direcao_user.id,
                "titulo": "X",
                "tipo": "tomada_posicao",
            }
        )
        wired_defesa.update_one = AsyncMock(return_value=MagicMock(matched_count=0))
        with pytest.raises(HTTPException) as exc:
            await prof_route.submeter_defesa(defesa_id="d1", current_user=direcao_user)
        assert exc.value.status_code == 409

    async def test_aprovar_conflito_409(self, wired_defesa, direcao_user, direcao_user_2, quiet_audit, quiet_notify):
        wired_defesa.find_one = AsyncMock(
            return_value={
                "id": "d1",
                "status": "submetido",
                "created_by": direcao_user.id,
                "titulo": "X",
                "tipo": "tomada_posicao",
            }
        )
        wired_defesa.update_one = AsyncMock(return_value=MagicMock(matched_count=0))
        with pytest.raises(HTTPException) as exc:
            await prof_route.aprovar_defesa(defesa_id="d1", current_user=direcao_user_2)
        assert exc.value.status_code == 409

    async def test_rejeitar_conflito_409(self, wired_defesa, direcao_user, direcao_user_2, quiet_audit, quiet_notify):
        from models import DefesaRejeicao

        wired_defesa.find_one = AsyncMock(
            return_value={
                "id": "d1",
                "status": "submetido",
                "created_by": direcao_user.id,
                "titulo": "X",
                "tipo": "tomada_posicao",
            }
        )
        wired_defesa.update_one = AsyncMock(return_value=MagicMock(matched_count=0))
        with pytest.raises(HTTPException) as exc:
            await prof_route.rejeitar_defesa(
                defesa_id="d1", payload=DefesaRejeicao(motivo="x"), current_user=direcao_user_2
            )
        assert exc.value.status_code == 409

    async def test_arquivar_conflito_409(self, wired_defesa, direcao_user, quiet_audit):
        wired_defesa.find_one = AsyncMock(
            return_value={
                "id": "d1",
                "status": "publicado",
                "created_by": "x",
                "titulo": "X",
                "tipo": "comunicado",
            }
        )
        wired_defesa.update_one = AsyncMock(return_value=MagicMock(matched_count=0))
        with pytest.raises(HTTPException) as exc:
            await prof_route.arquivar_defesa(defesa_id="d1", current_user=direcao_user)
        assert exc.value.status_code == 409


class TestDefesaTransicao404:
    """Transição sobre registo inexistente -> 404 (utilizador autorizado)."""

    async def test_submeter_404(self, wired_defesa, direcao_user, quiet_audit):
        wired_defesa.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await prof_route.submeter_defesa(defesa_id="x", current_user=direcao_user)
        assert exc.value.status_code == 404

    async def test_aprovar_404(self, wired_defesa, direcao_user_2, quiet_audit, quiet_notify):
        wired_defesa.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await prof_route.aprovar_defesa(defesa_id="x", current_user=direcao_user_2)
        assert exc.value.status_code == 404

    async def test_rejeitar_404(self, wired_defesa, direcao_user_2, quiet_audit, quiet_notify):
        from models import DefesaRejeicao

        wired_defesa.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await prof_route.rejeitar_defesa(
                defesa_id="x", payload=DefesaRejeicao(motivo="x"), current_user=direcao_user_2
            )
        assert exc.value.status_code == 404

    async def test_arquivar_404(self, wired_defesa, direcao_user, quiet_audit):
        wired_defesa.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await prof_route.arquivar_defesa(defesa_id="x", current_user=direcao_user)
        assert exc.value.status_code == 404


class TestDefesaAuditEConteudo:
    """Rede de segurança para 'audit em cada escrita' e para o conteúdo do $set."""

    async def test_submeter_regista_audit(self, wired_defesa, direcao_user, monkeypatch):
        first = {
            "id": "d1",
            "status": "rascunho",
            "created_by": direcao_user.id,
            "titulo": "X",
            "tipo": "tomada_posicao",
        }
        wired_defesa.find_one = AsyncMock(side_effect=[first, {**first, "status": "submetido"}])
        audit_mock = AsyncMock()
        monkeypatch.setattr(prof_route, "create_audit_log", audit_mock)
        await prof_route.submeter_defesa(defesa_id="d1", current_user=direcao_user)
        audit_mock.assert_awaited_once()
        assert audit_mock.call_args[0][2] == "d1"  # resource_id

    async def test_rejeitar_limpa_submetido_e_grava_motivo(
        self, wired_defesa, direcao_user, direcao_user_2, quiet_audit, quiet_notify
    ):
        from models import DefesaRejeicao

        first = {
            "id": "d1",
            "status": "submetido",
            "created_by": direcao_user.id,
            "titulo": "X",
            "tipo": "tomada_posicao",
        }
        wired_defesa.find_one = AsyncMock(side_effect=[first, {**first, "status": "rascunho"}])
        await prof_route.rejeitar_defesa(
            defesa_id="d1",
            payload=DefesaRejeicao(motivo="Falta base legal"),
            current_user=direcao_user_2,
        )
        set_data = wired_defesa.update_one.call_args[0][1]["$set"]
        assert set_data["status"] == "rascunho"
        assert set_data["motivo_rejeicao"] == "Falta base legal"
        assert set_data["submetido_em"] is None
        assert set_data["submetido_por"] is None

    async def test_arquiva_publicado_grava_metadados(self, wired_defesa, direcao_user, quiet_audit):
        first = {
            "id": "d1",
            "status": "publicado",
            "created_by": "x",
            "titulo": "X",
            "tipo": "comunicado",
        }
        wired_defesa.find_one = AsyncMock(side_effect=[first, {**first, "status": "arquivado"}])
        result = await prof_route.arquivar_defesa(defesa_id="d1", current_user=direcao_user)
        assert result["status"] == "arquivado"
        set_data = wired_defesa.update_one.call_args[0][1]["$set"]
        assert set_data["status"] == "arquivado"
        assert set_data["arquivado_por"] == direcao_user.id
        assert "arquivado_em" in set_data


class TestDefesaVisibilityGate:
    """Visibility='publico' não contorna o gate de status: um rascunho público
    alheio continua invisível para o sócio comum."""

    async def test_rascunho_publico_alheio_403(self, wired_defesa, socio_user):
        wired_defesa.find_one = AsyncMock(
            return_value={
                "id": "d1",
                "status": "rascunho",
                "visibility": "publico",
                "created_by": "outro",
                "titulo": "X",
            }
        )
        with pytest.raises(HTTPException) as exc:
            await prof_route.get_defesa(defesa_id="d1", current_user=socio_user)
        assert exc.value.status_code == 403


class TestRelacaoVisibility:
    async def test_default_visibility_socios(self, wired_relacoes, direcao_user, quiet_audit):
        from models import RelacaoExternaCreate

        result = await prof_route.create_relacao(
            data=RelacaoExternaCreate(nome="Org", tipo="parceiro"),
            current_user=direcao_user,
        )
        assert result["visibility"] == "socios"

    async def test_visibility_publico_persistido(self, wired_relacoes, direcao_user, quiet_audit):
        from models import RelacaoExternaCreate

        result = await prof_route.create_relacao(
            data=RelacaoExternaCreate(nome="Org", tipo="parceiro", visibility="publico"),
            current_user=direcao_user,
        )
        assert result["visibility"] == "publico"
