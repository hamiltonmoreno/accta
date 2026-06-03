"""Unit tests para o blog/notícias (spec-blog-noticias).

Cobre: visibilidade/status por role no GET lista; detalhe por slug e id;
ordenação pública por data efetiva (D9); CRUD com RBAC (403 p/ socio/financeiro/
anónimo); slug estável após publicação; published_at na transição; limpeza de
capa; audit log; e a categoria de upload `covers`.

Chamamos as funções de rota diretamente. As que usam `Query(...)` (get_posts)
recebem skip/limit explícitos — o default `Query()` é um FieldInfo, não um int.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import posts as p_route
from routes import upload as upload_route
from models import PostCreate, PostUpdate


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _cursor(items):
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=list(items))
    return cur


@pytest.fixture
def env(mock_db, monkeypatch):
    """posts já está pré-ligada no conftest; aqui mockamos os side-effects."""
    monkeypatch.setattr(p_route, "create_audit_log", AsyncMock())
    monkeypatch.setattr(p_route, "notify_all_active_users", AsyncMock())
    monkeypatch.setattr(p_route, "delete_upload_file", MagicMock(return_value=True))
    return mock_db


def _doc(**over):
    base = {
        "id": "p1",
        "title": "Título de Teste",
        "slug": "titulo-de-teste",
        "content": "conteúdo",
        "type": "noticia",
        "visibility": "publico",
        "status": "publicado",
        "tags": [],
        "created_at": "2026-01-01T00:00:00+00:00",
        "published_at": "2026-01-01T00:00:00+00:00",
    }
    base.update(over)
    return base


# --------------------------------------------------------------------------- #
# GET /posts — lista
# --------------------------------------------------------------------------- #


class TestListVisibility:
    async def test_anonimo_forca_publicado(self, env):
        env.posts.find = MagicMock(return_value=_cursor([_doc()]))
        await p_route.get_posts(skip=0, limit=100, current_user=None)
        query = env.posts.find.call_args[0][0]
        assert query["status"] == "publicado"
        assert query["visibility"] == "publico"

    async def test_socio_ve_publico_e_socios(self, env, socio_user):
        env.posts.find = MagicMock(return_value=_cursor([]))
        await p_route.get_posts(skip=0, limit=100, current_user=socio_user)
        query = env.posts.find.call_args[0][0]
        assert query["status"] == "publicado"
        assert query["visibility"] == {"$in": ["publico", "socios"]}

    async def test_staff_sem_filtro_ve_tudo(self, env, admin_user):
        env.posts.find = MagicMock(return_value=_cursor([]))
        await p_route.get_posts(skip=0, limit=100, current_user=admin_user)
        query = env.posts.find.call_args[0][0]
        assert "status" not in query  # staff vê rascunhos também
        assert "visibility" not in query

    async def test_anonimo_privado_403(self, env):
        with pytest.raises(HTTPException) as exc:
            await p_route.get_posts(visibility="privado", skip=0, limit=100, current_user=None)
        assert exc.value.status_code == 403

    async def test_anonimo_socios_401(self, env):
        with pytest.raises(HTTPException) as exc:
            await p_route.get_posts(visibility="socios", skip=0, limit=100, current_user=None)
        assert exc.value.status_code == 401

    async def test_ordena_por_data_efetiva_desc(self, env):
        # 'a' criado em Jan mas publicado em Maio; 'b' criado em Abril sem published_at.
        a = _doc(id="a", title="A", created_at="2026-01-01T00:00:00+00:00", published_at="2026-05-01T00:00:00+00:00")
        b = _doc(id="b", title="B", created_at="2026-04-01T00:00:00+00:00", published_at=None)
        env.posts.find = MagicMock(return_value=_cursor([b, a]))
        result = await p_route.get_posts(skip=0, limit=100, current_user=None)
        assert [p["id"] for p in result] == ["a", "b"]  # D9: a (publicado Maio) primeiro


# --------------------------------------------------------------------------- #
# GET /posts/{id_or_slug} — detalhe
# --------------------------------------------------------------------------- #


class TestDetail:
    async def test_resolve_por_slug(self, env):
        env.posts.find_one = AsyncMock(return_value=_doc(slug="minha-noticia"))
        result = await p_route.get_post("minha-noticia", current_user=None)
        assert result["slug"] == "minha-noticia"

    async def test_fallback_por_id(self, env):
        env.posts.find_one = AsyncMock(side_effect=[None, _doc(id="abc")])
        result = await p_route.get_post("abc", current_user=None)
        assert result["id"] == "abc"

    async def test_inexistente_404(self, env):
        env.posts.find_one = AsyncMock(side_effect=[None, None])
        with pytest.raises(HTTPException) as exc:
            await p_route.get_post("nada", current_user=None)
        assert exc.value.status_code == 404

    async def test_rascunho_escondido_do_publico_404(self, env):
        env.posts.find_one = AsyncMock(return_value=_doc(status="rascunho"))
        with pytest.raises(HTTPException) as exc:
            await p_route.get_post("titulo-de-teste", current_user=None)
        assert exc.value.status_code == 404

    async def test_socios_escondido_de_anonimo_404(self, env):
        env.posts.find_one = AsyncMock(return_value=_doc(visibility="socios"))
        with pytest.raises(HTTPException) as exc:
            await p_route.get_post("titulo-de-teste", current_user=None)
        assert exc.value.status_code == 404

    async def test_socios_visivel_a_socio(self, env, socio_user):
        env.posts.find_one = AsyncMock(return_value=_doc(visibility="socios"))
        result = await p_route.get_post("titulo-de-teste", current_user=socio_user)
        assert result["visibility"] == "socios"

    async def test_rascunho_visivel_a_staff(self, env, moderador_user):
        env.posts.find_one = AsyncMock(return_value=_doc(status="rascunho"))
        result = await p_route.get_post("titulo-de-teste", current_user=moderador_user)
        assert result["status"] == "rascunho"


# --------------------------------------------------------------------------- #
# POST /posts — criar
# --------------------------------------------------------------------------- #


class TestCreate:
    @pytest.mark.parametrize("user_fix", ["socio_user", "financeiro_user"])
    async def test_rbac_403(self, env, request, user_fix):
        user = request.getfixturevalue(user_fix)
        with pytest.raises(HTTPException) as exc:
            await p_route.create_post(PostCreate(title="Olá mundo", content="x"), current_user=user)
        assert exc.value.status_code == 403

    async def test_admin_cria_com_slug_autor_published_at(self, env, admin_user):
        env.posts.find_one = AsyncMock(return_value=None)  # slug único
        post = await p_route.create_post(
            PostCreate(title="Nova Rota Praia Sal", content="texto"), current_user=admin_user
        )
        assert post.slug == "nova-rota-praia-sal"
        assert post.author_id == admin_user.id
        assert post.author_name == admin_user.name
        assert post.published_at is not None  # nasce publicado
        env.posts.insert_one.assert_awaited()
        p_route.create_audit_log.assert_awaited()

    async def test_rascunho_nao_define_published_at(self, env, admin_user):
        env.posts.find_one = AsyncMock(return_value=None)
        post = await p_route.create_post(
            PostCreate(title="Em preparação", content="x", status="rascunho"), current_user=admin_user
        )
        assert post.published_at is None

    async def test_notify_socios_quando_publicado_socios(self, env, admin_user):
        env.posts.find_one = AsyncMock(return_value=None)
        await p_route.create_post(
            PostCreate(title="Aviso aos sócios", content="x", visibility="socios", notify_socios=True),
            current_user=admin_user,
        )
        p_route.notify_all_active_users.assert_awaited()

    async def test_sem_notify_por_omissao(self, env, moderador_user):
        env.posts.find_one = AsyncMock(return_value=None)
        await p_route.create_post(
            PostCreate(title="Notícia normal", content="x", visibility="socios"), current_user=moderador_user
        )
        p_route.notify_all_active_users.assert_not_awaited()


# --------------------------------------------------------------------------- #
# PATCH /posts/{id} — editar
# --------------------------------------------------------------------------- #


class TestUpdate:
    async def test_socio_403(self, env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await p_route.update_post("p1", PostUpdate(title="Novo título"), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_inexistente_404(self, env, admin_user):
        env.posts.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await p_route.update_post("p1", PostUpdate(title="Novo título"), current_user=admin_user)
        assert exc.value.status_code == 404

    async def test_define_updated_at(self, env, admin_user):
        captured = {}
        env.posts.find_one = AsyncMock(side_effect=[_doc(), _doc()])
        env.posts.update_one = AsyncMock(side_effect=lambda f, u: captured.update(u["$set"]))
        await p_route.update_post("p1", PostUpdate(title="Título Atualizado"), current_user=admin_user)
        assert "updated_at" in captured
        p_route.create_audit_log.assert_awaited()

    async def test_published_at_na_transicao(self, env, admin_user):
        captured = {}
        existing = _doc(status="rascunho", published_at=None)
        env.posts.find_one = AsyncMock(side_effect=[existing, _doc()])
        env.posts.update_one = AsyncMock(side_effect=lambda f, u: captured.update(u["$set"]))
        await p_route.update_post("p1", PostUpdate(status="publicado"), current_user=admin_user)
        assert "published_at" in captured

    async def test_slug_regenera_so_em_rascunho(self, env, admin_user):
        captured = {}
        existing = _doc(status="rascunho")
        env.posts.find_one = AsyncMock(side_effect=[existing, None, _doc()])  # existing, slug-check, final
        env.posts.update_one = AsyncMock(side_effect=lambda f, u: captured.update(u["$set"]))
        await p_route.update_post("p1", PostUpdate(title="Outro Título", regenerate_slug=True), current_user=admin_user)
        assert captured.get("slug") == "outro-titulo"

    async def test_slug_estavel_apos_publicado(self, env, admin_user):
        captured = {}
        existing = _doc(status="publicado")
        env.posts.find_one = AsyncMock(side_effect=[existing, _doc()])
        env.posts.update_one = AsyncMock(side_effect=lambda f, u: captured.update(u["$set"]))
        await p_route.update_post("p1", PostUpdate(title="Título Mudou", regenerate_slug=True), current_user=admin_user)
        assert "slug" not in captured  # publicado: slug não muda

    async def test_limpa_capa_antiga(self, env, admin_user):
        existing = _doc(cover_url="/uploads/covers/old.png")
        env.posts.find_one = AsyncMock(side_effect=[existing, _doc()])
        env.posts.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        await p_route.update_post("p1", PostUpdate(cover_url="/uploads/covers/new.png"), current_user=admin_user)
        p_route.delete_upload_file.assert_called_once_with("/uploads/covers/old.png")


# --------------------------------------------------------------------------- #
# DELETE /posts/{id} — eliminar
# --------------------------------------------------------------------------- #


class TestDelete:
    async def test_socio_403(self, env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await p_route.delete_post("p1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_inexistente_404(self, env, admin_user):
        env.posts.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await p_route.delete_post("p1", current_user=admin_user)
        assert exc.value.status_code == 404

    async def test_elimina_e_limpa_capa(self, env, admin_user):
        env.posts.find_one = AsyncMock(return_value=_doc(cover_url="/uploads/covers/x.png"))
        await p_route.delete_post("p1", current_user=admin_user)
        env.posts.delete_one.assert_awaited()
        p_route.delete_upload_file.assert_called_once_with("/uploads/covers/x.png")
        p_route.create_audit_log.assert_awaited()


# --------------------------------------------------------------------------- #
# Upload — categoria covers (§4.5)
# --------------------------------------------------------------------------- #


class TestCoversCategory:
    def test_config_covers(self):
        assert "covers" in upload_route.ALLOWED_EXTENSIONS
        assert upload_route.ALLOWED_EXTENSIONS["covers"] == [".png", ".jpg", ".jpeg"]
        assert ".svg" not in upload_route.ALLOWED_EXTENSIONS["covers"]  # SVG bloqueado (XSS)
        assert upload_route.MAX_FILE_SIZES["covers"] == 2 * 1024 * 1024

    async def test_socio_403(self, socio_user):
        # RBAC corre antes de tocar no ficheiro — file pode ser um stub.
        with pytest.raises(HTTPException) as exc:
            await upload_route.upload_file(category="covers", file=MagicMock(), current_user=socio_user)
        assert exc.value.status_code == 403
