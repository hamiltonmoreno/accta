"""Unit tests para a gestão da marca/logo (spec-gestao-logo-marca §11).

RBAC (admin+moderador escrevem; financeiro/socio 403), público devolve defaults
quando vazio, e semântica de "limpar" ("" repõe None; ausente mantém).
`brand_settings` não está pré-ligada no conftest — liga-se aqui.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import brand as br_route
from routes import upload as upload_route
from models import BrandSettingsUpdate


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


@pytest.fixture
def brand_env(mock_db, monkeypatch):
    coll = MagicMock(name="brand_settings")
    coll.find_one = AsyncMock(return_value=None)
    coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    mock_db.brand_settings = coll
    monkeypatch.setattr(br_route, "create_audit_log", AsyncMock())
    monkeypatch.setattr(br_route, "delete_upload_file", lambda *a, **k: True)
    return mock_db


class TestPublic:
    async def test_defaults_quando_vazio(self, brand_env):
        result = await br_route.get_brand_public()
        assert result["logo_light_url"] is None
        assert result["logo_dark_url"] is None
        assert result["favicon_url"] is None
        assert result["alt"] == "ACCTA Cabo Verde"

    async def test_devolve_favicon_gravado(self, brand_env):
        brand_env.brand_settings.find_one = AsyncMock(
            return_value={"id": "brand_settings", "favicon_url": "/uploads/brand/fav.png"}
        )
        result = await br_route.get_brand_public()
        assert result["favicon_url"] == "/uploads/brand/fav.png"

    async def test_devolve_logo_gravado(self, brand_env):
        brand_env.brand_settings.find_one = AsyncMock(
            return_value={"id": "brand_settings", "logo_light_url": "/uploads/brand/a.png", "alt": "Marca"}
        )
        result = await br_route.get_brand_public()
        assert result["logo_light_url"] == "/uploads/brand/a.png"
        assert result["alt"] == "Marca"


class TestUpdate:
    async def test_socio_403(self, brand_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await br_route.update_brand(
                request=_request(), data=BrandSettingsUpdate(logo_light_url="/uploads/brand/a.png"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_financeiro_403(self, brand_env, financeiro_user):
        with pytest.raises(HTTPException) as exc:
            await br_route.update_brand(
                request=_request(), data=BrandSettingsUpdate(logo_dark_url="/uploads/brand/d.png"),
                current_user=financeiro_user,
            )
        assert exc.value.status_code == 403

    async def test_sem_alteracao_400(self, brand_env, admin_user):
        with pytest.raises(HTTPException) as exc:
            await br_route.update_brand(
                request=_request(), data=BrandSettingsUpdate(), current_user=admin_user
            )
        assert exc.value.status_code == 400

    async def test_moderador_define_logo(self, brand_env, moderador_user):
        captured = {}
        brand_env.brand_settings.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        await br_route.update_brand(
            request=_request(),
            data=BrandSettingsUpdate(logo_light_url="/uploads/brand/a.png", alt="ACCTA"),
            current_user=moderador_user,
        )
        assert captured["logo_light_url"] == "/uploads/brand/a.png"
        assert captured["alt"] == "ACCTA"
        assert captured["updated_by"] == moderador_user.id
        br_route.create_audit_log.assert_awaited()

    async def test_limpar_repoe_none_e_apaga_upload(self, brand_env, admin_user, monkeypatch):
        brand_env.brand_settings.find_one = AsyncMock(
            return_value={"id": "brand_settings", "logo_light_url": "/uploads/brand/old.png"}
        )
        captured = {}
        brand_env.brand_settings.update_one = AsyncMock(side_effect=lambda f, u: captured.update(u["$set"]))
        deleted = {}
        monkeypatch.setattr(br_route, "delete_upload_file", lambda url: deleted.setdefault("url", url))
        # "" repõe default
        await br_route.update_brand(
            request=_request(), data=BrandSettingsUpdate(logo_light_url=""), current_user=admin_user
        )
        assert captured["logo_light_url"] is None  # voltou ao SVG fallback
        assert deleted["url"] == "/uploads/brand/old.png"  # upload antigo apagado

    async def test_define_favicon(self, brand_env, admin_user):
        captured = {}
        brand_env.brand_settings.insert_one = AsyncMock(side_effect=lambda d: captured.update(d))
        # _get_doc() relê via find_one após gravar → devolve o doc inserido.
        brand_env.brand_settings.find_one = AsyncMock(side_effect=lambda *a, **k: captured or None)
        result = await br_route.update_brand(
            request=_request(),
            data=BrandSettingsUpdate(favicon_url="/uploads/brand/fav.png"),
            current_user=admin_user,
        )
        assert captured["favicon_url"] == "/uploads/brand/fav.png"
        assert result["favicon_url"] == "/uploads/brand/fav.png"

    async def test_limpar_favicon_repoe_none_e_apaga_upload(self, brand_env, admin_user, monkeypatch):
        brand_env.brand_settings.find_one = AsyncMock(
            return_value={"id": "brand_settings", "favicon_url": "/uploads/brand/old-fav.png"}
        )
        captured = {}
        brand_env.brand_settings.update_one = AsyncMock(side_effect=lambda f, u: captured.update(u["$set"]))
        deleted = {}
        monkeypatch.setattr(br_route, "delete_upload_file", lambda url: deleted.setdefault("url", url))
        await br_route.update_brand(
            request=_request(), data=BrandSettingsUpdate(favicon_url=""), current_user=admin_user
        )
        assert captured["favicon_url"] is None
        assert deleted["url"] == "/uploads/brand/old-fav.png"

    async def test_ausente_mantem(self, brand_env, admin_user):
        # Só altera alt; logo_light_url ausente NÃO deve aparecer no $set.
        brand_env.brand_settings.find_one = AsyncMock(
            return_value={"id": "brand_settings", "logo_light_url": "/uploads/brand/keep.png"}
        )
        captured = {}
        brand_env.brand_settings.update_one = AsyncMock(side_effect=lambda f, u: captured.update(u["$set"]))
        await br_route.update_brand(
            request=_request(), data=BrandSettingsUpdate(alt="Novo Alt"), current_user=admin_user
        )
        assert captured["alt"] == "Novo Alt"
        assert "logo_light_url" not in captured  # mantido


class TestUploadCategory:
    async def test_brand_category_config(self):
        assert "brand" in upload_route.ALLOWED_EXTENSIONS
        assert ".svg" not in upload_route.ALLOWED_EXTENSIONS["brand"]  # SVG bloqueado
        assert ".png" in upload_route.ALLOWED_EXTENSIONS["brand"]
        assert upload_route.MAX_FILE_SIZES["brand"] == 2 * 1024 * 1024
