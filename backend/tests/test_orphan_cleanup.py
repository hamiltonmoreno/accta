"""Limpeza de uploads órfãos:
• helpers.delete_upload_file — guard de path traversal + unlink real
• wiring reativo: delete_user (avatar), delete/update benefit (logo),
  delete_gallery_photo (foto) chamam o helper com a URL certa.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import helpers
from models import BenefitUpdate
from routes import benefits as benefits_route
from routes import gallery as gallery_route
from routes import users as users_route

# asyncio_mode=auto trata os testes async — sem marker asyncio (evita warning
# nos testes síncronos de filesystem desta suite).
pytestmark = [pytest.mark.unit]


# --------------------------------------------------------------------------- #
# helpers.delete_upload_file (filesystem puro)
# --------------------------------------------------------------------------- #


class TestDeleteUploadFile:
    @pytest.fixture
    def upload_root(self, tmp_path, monkeypatch):
        root = tmp_path / "uploads"
        (root / "avatars").mkdir(parents=True)
        monkeypatch.setattr(helpers, "UPLOAD_DIR", root)
        return root

    def test_deletes_real_file(self, upload_root):
        f = upload_root / "avatars" / "a.png"
        f.write_bytes(b"x")
        assert helpers.delete_upload_file("/uploads/avatars/a.png") is True
        assert not f.exists()

    @pytest.mark.parametrize("url", ["", None, "https://x/y.png", "/etc/passwd", "uploads/a.png"])
    def test_rejects_non_uploads(self, upload_root, url):
        assert helpers.delete_upload_file(url) is False

    def test_blocks_path_traversal(self, upload_root, tmp_path):
        secret = tmp_path / "secret.txt"
        secret.write_text("keep")
        assert helpers.delete_upload_file("/uploads/../secret.txt") is False
        assert secret.exists()

    def test_missing_file_is_false_not_error(self, upload_root):
        assert helpers.delete_upload_file("/uploads/avatars/ghost.png") is False


# --------------------------------------------------------------------------- #
# Wiring reativo
# --------------------------------------------------------------------------- #


class TestUserDeleteCleansAvatar:
    async def test_avatar_deleted_with_user(self, mock_db, admin_user):
        spy = MagicMock(return_value=True)
        target = {"id": "u-victim", "name": "Vitima", "photo_url": "/uploads/avatars/v.png"}
        mock_db.users.find_one = AsyncMock(return_value=target)

        import pytest as _pytest

        with _pytest.MonkeyPatch.context() as mp:
            mp.setattr(users_route, "delete_upload_file", spy)
            await users_route.delete_user("u-victim", current_user=admin_user)

        spy.assert_called_once_with("/uploads/avatars/v.png")
        mock_db.users.delete_one.assert_awaited_once()

    async def test_no_avatar_passes_empty_string(self, mock_db, admin_user):
        spy = MagicMock(return_value=False)
        mock_db.users.find_one = AsyncMock(return_value={"id": "u2", "name": "Sem foto"})

        import pytest as _pytest

        with _pytest.MonkeyPatch.context() as mp:
            mp.setattr(users_route, "delete_upload_file", spy)
            await users_route.delete_user("u2", current_user=admin_user)

        spy.assert_called_once_with("")


class TestBenefitLogoCleanup:
    async def test_logo_deleted_on_benefit_delete(self, mock_db, admin_user):
        spy = MagicMock(return_value=True)
        mock_db.benefits.find_one = AsyncMock(
            return_value={"id": "b1", "name": "Parceiro", "logo_url": "/uploads/logos/old.png"}
        )

        import pytest as _pytest

        with _pytest.MonkeyPatch.context() as mp:
            mp.setattr(benefits_route, "delete_upload_file", spy)
            await benefits_route.delete_benefit("b1", current_user=admin_user)

        spy.assert_called_once_with("/uploads/logos/old.png")

    async def test_old_logo_deleted_when_replaced(self, mock_db, admin_user):
        spy = MagicMock(return_value=True)
        mock_db.benefits.find_one = AsyncMock(
            return_value={"id": "b1", "name": "P", "logo_url": "/uploads/logos/old.png"}
        )

        import pytest as _pytest

        with _pytest.MonkeyPatch.context() as mp:
            mp.setattr(benefits_route, "delete_upload_file", spy)
            await benefits_route.update_benefit(
                "b1", BenefitUpdate(logo_url="/uploads/logos/new.png"), current_user=admin_user
            )

        spy.assert_called_once_with("/uploads/logos/old.png")

    async def test_logo_untouched_when_not_in_update(self, mock_db, admin_user):
        spy = MagicMock(return_value=True)
        mock_db.benefits.find_one = AsyncMock(
            return_value={"id": "b1", "name": "P", "logo_url": "/uploads/logos/old.png"}
        )

        import pytest as _pytest

        with _pytest.MonkeyPatch.context() as mp:
            mp.setattr(benefits_route, "delete_upload_file", spy)
            await benefits_route.update_benefit("b1", BenefitUpdate(name="Novo nome"), current_user=admin_user)

        spy.assert_not_called()


class TestGalleryStillWired:
    async def test_photo_file_deleted_on_delete(self, mock_db, admin_user):
        spy = MagicMock(return_value=True)
        mock_db.gallery_photos.find_one = AsyncMock(
            return_value={"id": "p1", "url": "/uploads/gallery/p1.jpg", "uploaded_by": "someone"}
        )

        import pytest as _pytest

        with _pytest.MonkeyPatch.context() as mp:
            mp.setattr(gallery_route, "delete_upload_file", spy)
            await gallery_route.delete_gallery_photo("p1", current_user=admin_user)

        spy.assert_called_once_with("/uploads/gallery/p1.jpg")
