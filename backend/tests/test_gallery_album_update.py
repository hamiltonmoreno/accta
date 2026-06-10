"""Regressão para o PATCH parcial de álbum de galeria (issue #194).

Antes: `update_gallery_album` fazia bind a `GalleryAlbumCreate` (`title`
obrigatório) e filtrava com `if v is not None`. Consequências:
  - um PATCH só de `order`/`visibility` dava 422 (exigia reenviar `title`);
  - era impossível limpar `description`/`cover_url` de volta a `""`.

Agora usa `GalleryAlbumUpdate` (tudo Optional) + `model_dump(exclude_unset=True)`,
distinguindo "não enviado" (mantém) de "enviado vazio" (limpa).
"""

import pytest
from fastapi import HTTPException

import routes.gallery as gallery_route
from models import GalleryAlbumUpdate


def _existing_album():
    return {
        "id": "alb-1",
        "title": "Original",
        "description": "desc original",
        "cover_url": "x.jpg",
        "order": 0,
        "visibility": "public",
    }


@pytest.mark.asyncio
async def test_patch_so_order_nao_exige_title(mock_db, moderador_user):
    """PATCH parcial só com `order` não dá 422 e só altera `order`."""
    mock_db.gallery_albums.find_one.return_value = _existing_album()

    await gallery_route.update_gallery_album(
        album_id="alb-1",
        album_data=GalleryAlbumUpdate(order=5),
        current_user=moderador_user,
    )

    update_arg = mock_db.gallery_albums.update_one.call_args.args[1]
    assert update_arg == {"$set": {"order": 5}}, (
        "PATCH parcial deve tocar só nos campos enviados — regressão #194"
    )


@pytest.mark.asyncio
async def test_patch_pode_limpar_description(mock_db, moderador_user):
    """Enviar `description=''` deve limpar o campo (exclude_unset inclui-o)."""
    mock_db.gallery_albums.find_one.return_value = _existing_album()

    await gallery_route.update_gallery_album(
        album_id="alb-1",
        album_data=GalleryAlbumUpdate(description=""),
        current_user=moderador_user,
    )

    update_arg = mock_db.gallery_albums.update_one.call_args.args[1]
    assert update_arg == {"$set": {"description": ""}}, (
        "description='' tem de entrar no $set para poder limpar o campo"
    )


@pytest.mark.asyncio
async def test_patch_vazio_da_400(mock_db, moderador_user):
    """Body sem campos => 400 (nada para atualizar), sem tocar na DB."""
    mock_db.gallery_albums.find_one.return_value = _existing_album()

    with pytest.raises(HTTPException) as exc:
        await gallery_route.update_gallery_album(
            album_id="alb-1",
            album_data=GalleryAlbumUpdate(),
            current_user=moderador_user,
        )

    assert exc.value.status_code == 400
    mock_db.gallery_albums.update_one.assert_not_called()


@pytest.mark.asyncio
async def test_patch_album_inexistente_da_404(mock_db, moderador_user):
    """Álbum inexistente continua a dar 404."""
    mock_db.gallery_albums.find_one.return_value = None

    with pytest.raises(HTTPException) as exc:
        await gallery_route.update_gallery_album(
            album_id="nope",
            album_data=GalleryAlbumUpdate(title="X"),
            current_user=moderador_user,
        )

    assert exc.value.status_code == 404
