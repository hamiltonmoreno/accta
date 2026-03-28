from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from datetime import datetime
from typing import Optional
from pathlib import Path
from models import User, GalleryAlbum, GalleryAlbumCreate, GalleryPhoto
from database import db, UPLOAD_DIR
from auth import get_current_user
import uuid
import shutil

router = APIRouter(prefix="/gallery", tags=["gallery"])


@router.get("/albums")
async def get_gallery_albums():
    albums = await db.gallery_albums.find({}, {"_id": 0}).sort("order", 1).to_list(50)
    for a in albums:
        if isinstance(a.get('created_at'), str):
            a['created_at'] = datetime.fromisoformat(a['created_at'])
    return albums


@router.get("/albums/{album_id}")
async def get_gallery_album(album_id: str):
    album = await db.gallery_albums.find_one({"id": album_id}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Álbum não encontrado")
    return album


@router.post("/albums")
async def create_gallery_album(album_data: GalleryAlbumCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores")
    album = GalleryAlbum(**album_data.model_dump())
    album_dict = album.model_dump()
    album_dict['created_at'] = album_dict['created_at'].isoformat()
    await db.gallery_albums.insert_one(album_dict)
    album_dict.pop('_id', None)
    return album_dict


@router.patch("/albums/{album_id}")
async def update_gallery_album(album_id: str, album_data: GalleryAlbumCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores")
    existing = await db.gallery_albums.find_one({"id": album_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Álbum não encontrado")
    update_data = {k: v for k, v in album_data.model_dump().items() if v is not None}
    await db.gallery_albums.update_one({"id": album_id}, {"$set": update_data})
    return {"message": "Álbum atualizado"}


@router.delete("/albums/{album_id}")
async def delete_gallery_album(album_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores")
    await db.gallery_albums.delete_one({"id": album_id})
    await db.gallery_photos.delete_many({"album_id": album_id})
    return {"message": "Álbum e fotos removidos"}


@router.get("/photos")
async def get_gallery_photos(album_id: Optional[str] = None):
    query = {}
    if album_id:
        query["album_id"] = album_id
    photos = await db.gallery_photos.find(query, {"_id": 0}).sort("order", 1).to_list(200)
    return photos


@router.post("/photos/upload")
async def upload_gallery_photo(
    album_id: str,
    caption: str = "",
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores")

    album = await db.gallery_albums.find_one({"id": album_id}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Álbum não encontrado")

    ext = Path(file.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Formato não suportado. Use JPG, PNG ou WEBP")

    gallery_dir = UPLOAD_DIR / "gallery"
    gallery_dir.mkdir(exist_ok=True)
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = gallery_dir / unique_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    photo_url = f"/uploads/gallery/{unique_filename}"
    count = await db.gallery_photos.count_documents({"album_id": album_id})

    photo = GalleryPhoto(
        album_id=album_id, url=photo_url, caption=caption,
        order=count, uploaded_by=current_user.id,
    )
    photo_dict = photo.model_dump()
    photo_dict['created_at'] = photo_dict['created_at'].isoformat()
    await db.gallery_photos.insert_one(photo_dict)
    photo_dict.pop('_id', None)

    await db.gallery_albums.update_one(
        {"id": album_id},
        {"$inc": {"photo_count": 1}, "$set": {"cover_url": photo_url} if count == 0 else {}}
    )
    if count == 0:
        await db.gallery_albums.update_one({"id": album_id}, {"$set": {"cover_url": photo_url}})

    return photo_dict


@router.delete("/photos/{photo_id}")
async def delete_gallery_photo(photo_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores")
    photo = await db.gallery_photos.find_one({"id": photo_id}, {"_id": 0})
    if not photo:
        raise HTTPException(status_code=404, detail="Foto não encontrada")

    if photo['url'].startswith("/uploads/"):
        from database import ROOT_DIR
        file_path = ROOT_DIR / photo['url'].lstrip("/")
        if file_path.exists():
            file_path.unlink()

    await db.gallery_photos.delete_one({"id": photo_id})
    await db.gallery_albums.update_one({"id": photo['album_id']}, {"$inc": {"photo_count": -1}})
    return {"message": "Foto removida"}
