"""Unit tests para os banners de página (spec-padronizacao-banners §11).

RBAC (admin+moderador escrevem; financeiro/socio 403), chave inválida 400,
e o público vê defaults+docs fundidos sem auth. `page_banners` não está
pré-ligada no conftest — liga-se aqui.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import banners as b_route
from routes import upload as upload_route
from models import PageBannerUpdate


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


def _cursor(items):
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=items)
    return cur


@pytest.fixture
def ban_env(mock_db, monkeypatch):
    coll = MagicMock(name="page_banners")
    coll.find_one = AsyncMock(return_value=None)
    coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    coll.find = MagicMock(return_value=_cursor([]))
    mock_db.page_banners = coll
    monkeypatch.setattr(b_route, "create_audit_log", AsyncMock())
    monkeypatch.setattr(b_route, "delete_upload_file", lambda *a, **k: True)
    return mock_db


class TestPublic:
    async def test_funde_defaults_sem_auth(self, ban_env):
        # 1 doc gravado por cima; restantes usam default.
        ban_env.page_banners.find = MagicMock(
            return_value=_cursor([{"key": "sobre", "image_url": "/uploads/banners/x.jpg", "alt": "Equipa"}])
        )
        result = await b_route.get_banners_public()
        assert set(result.keys()) == set(b_route.BANNER_KEYS)  # todas as chaves
        assert result["sobre"]["image_url"] == "/uploads/banners/x.jpg"
        assert result["sobre"]["alt"] == "Equipa"
        # chave sem doc → default embebido
        assert result["home"]["image_url"] == b_route.BANNER_DEFAULTS["home"]


class TestGetManage:
    async def test_socio_403(self, ban_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await b_route.get_banners(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_moderador_ve_metadados(self, ban_env, moderador_user):
        result = await b_route.get_banners(current_user=moderador_user)
        assert "banners" in result and "keys" in result
        assert result["banners"]["home"]["is_home"] is True
        assert result["banners"]["sobre"]["is_default"] is True  # sem doc


class TestUpdate:
    async def test_financeiro_403(self, ban_env, financeiro_user):
        with pytest.raises(HTTPException) as exc:
            await b_route.update_banner(
                key="sobre", request=_request(),
                data=PageBannerUpdate(image_url="/uploads/banners/y.jpg"), current_user=financeiro_user,
            )
        assert exc.value.status_code == 403

    async def test_chave_invalida_400(self, ban_env, admin_user):
        with pytest.raises(HTTPException) as exc:
            await b_route.update_banner(
                key="inexistente", request=_request(),
                data=PageBannerUpdate(image_url="/uploads/banners/y.jpg"), current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_admin_insert_novo(self, ban_env, admin_user):
        captured = {}
        ban_env.page_banners.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        result = await b_route.update_banner(
            key="noticias", request=_request(),
            data=PageBannerUpdate(image_url="/uploads/banners/n.jpg", alt="Notícias"), current_user=admin_user,
        )
        assert result["key"] == "noticias"
        assert captured["image_url"] == "/uploads/banners/n.jpg"
        assert captured["alt"] == "Notícias"
        assert captured["updated_by"] == admin_user.id
        b_route.create_audit_log.assert_awaited()

    async def test_moderador_substitui_e_limpa_antigo(self, ban_env, moderador_user, monkeypatch):
        ban_env.page_banners.find_one = AsyncMock(
            return_value={"key": "sobre", "image_url": "/uploads/banners/old.jpg"}
        )
        deleted = {}
        monkeypatch.setattr(b_route, "delete_upload_file", lambda url: deleted.setdefault("url", url))
        await b_route.update_banner(
            key="sobre", request=_request(),
            data=PageBannerUpdate(image_url="/uploads/banners/new.jpg"), current_user=moderador_user,
        )
        # imagem anterior (upload local) é apagada
        assert deleted["url"] == "/uploads/banners/old.jpg"


class TestUploadCategory:
    async def test_banners_category_aceita_admin_moderador(self):
        assert "banners" in upload_route.ALLOWED_EXTENSIONS
        assert ".webp" in upload_route.ALLOWED_EXTENSIONS["banners"]
        assert upload_route.MAX_FILE_SIZES["banners"] == 4 * 1024 * 1024
