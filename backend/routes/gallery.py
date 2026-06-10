from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import Optional
from pathlib import Path
from models import User, GalleryAlbum, GalleryAlbumCreate, GalleryPhoto
from database import db, UPLOAD_DIR
from auth import get_current_user, has_role_or_privilege
from helpers import notify_admins, create_notification, create_audit_log, delete_upload_file
from file_validation import validate_file_content
import asyncio
import uuid

GALLERY_ALLOWED_EXTS = [".jpg", ".jpeg", ".png", ".webp"]
GALLERY_MAX_SIZE = 10 * 1024 * 1024  # 10 MB

router = APIRouter(prefix="/gallery", tags=["gallery"])

GALLERY_DIR = UPLOAD_DIR / "gallery"
GALLERY_DIR.mkdir(exist_ok=True)


async def _recompute_cover_if_needed(album_id: str, removed_url: str) -> None:
    """Se a foto removida/rejeitada era a capa do álbum, recalcula a capa para a
    foto aprovada mais recente (ou limpa-a). Sem isto, `cover_url` ficava a
    apontar para um ficheiro já apagado."""
    album = await db.gallery_albums.find_one({"id": album_id}, {"_id": 0, "cover_url": 1})
    if not album or album.get("cover_url") != removed_url:
        return
    remaining = await db.gallery_photos.find(
        {"album_id": album_id, "status": "approved"}, {"_id": 0, "url": 1, "created_at": 1}
    ).to_list(None)
    new_cover = ""
    if remaining:
        remaining.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        new_cover = remaining[0].get("url", "")
    await db.gallery_albums.update_one({"id": album_id}, {"$set": {"cover_url": new_cover}})


# ===== PUBLIC ENDPOINTS (no auth) =====


@router.get("/public/albums")
async def get_public_albums():
    albums = await db.gallery_albums.find({"visibility": "public"}, {"_id": 0}).sort("order", 1).to_list(50)

    # Batch count approved photos per album
    album_ids = [a["id"] for a in albums]
    pipeline = [
        {"$match": {"album_id": {"$in": album_ids}, "status": "approved"}},
        {"$group": {"_id": "$album_id", "count": {"$sum": 1}}},
    ]
    counts = await db.gallery_photos.aggregate(pipeline).to_list(None)
    count_map = {c["_id"]: c["count"] for c in counts}

    for a in albums:
        a["photo_count"] = count_map.get(a["id"], 0)
    return [a for a in albums if a["photo_count"] > 0]


@router.get("/public/photos")
async def get_public_photos(album_id: Optional[str] = None):
    query = {"status": "approved"}
    if album_id:
        album = await db.gallery_albums.find_one({"id": album_id, "visibility": "public"}, {"_id": 0})
        if not album:
            raise HTTPException(status_code=404, detail="Album nao encontrado")
        query["album_id"] = album_id
    else:
        public_albums = await db.gallery_albums.find({"visibility": "public"}, {"_id": 0, "id": 1}).to_list(100)
        public_ids = [a["id"] for a in public_albums]
        query["album_id"] = {"$in": public_ids}

    photos = await db.gallery_photos.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return photos


# ===== AUTHENTICATED ENDPOINTS =====


@router.get("/albums")
async def get_gallery_albums(current_user: User = Depends(get_current_user)):
    albums = await db.gallery_albums.find({}, {"_id": 0}).sort("order", 1).to_list(50)

    # Batch count approved photos per album
    album_ids = [a["id"] for a in albums]
    pipeline = [
        {"$match": {"album_id": {"$in": album_ids}, "status": "approved"}},
        {"$group": {"_id": "$album_id", "count": {"$sum": 1}}},
    ]
    counts = await db.gallery_photos.aggregate(pipeline).to_list(None)
    count_map = {c["_id"]: c["count"] for c in counts}

    for a in albums:
        a["photo_count"] = count_map.get(a["id"], 0)
    return albums


@router.get("/albums/{album_id}")
async def get_gallery_album(album_id: str, current_user: User = Depends(get_current_user)):
    album = await db.gallery_albums.find_one({"id": album_id}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Album nao encontrado")
    return album


@router.post("/albums")
async def create_gallery_album(album_data: GalleryAlbumCreate, current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin", "moderador"), "moderate_content"):
        raise HTTPException(status_code=403, detail="Sem permissão para moderar conteúdo")
    album = GalleryAlbum(**album_data.model_dump())
    album_dict = album.model_dump()
    await db.gallery_albums.insert_one(album_dict)
    await create_audit_log(current_user.id, f"Criou álbum de galeria {album.id}", album.id)
    return album_dict


@router.patch("/albums/{album_id}")
async def update_gallery_album(
    album_id: str, album_data: GalleryAlbumCreate, current_user: User = Depends(get_current_user)
):
    if not has_role_or_privilege(current_user, ("admin", "moderador"), "moderate_content"):
        raise HTTPException(status_code=403, detail="Sem permissão para moderar conteúdo")
    existing = await db.gallery_albums.find_one({"id": album_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Album nao encontrado")
    update_data = {k: v for k, v in album_data.model_dump().items() if v is not None}
    await db.gallery_albums.update_one({"id": album_id}, {"$set": update_data})
    await create_audit_log(current_user.id, f"Atualizou álbum de galeria {album_id}", album_id)
    return {"message": "Album atualizado"}


@router.delete("/albums/{album_id}")
async def delete_gallery_album(album_id: str, current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin", "moderador"), "moderate_content"):
        raise HTTPException(status_code=403, detail="Sem permissão para moderar conteúdo")

    photos = await db.gallery_photos.find({"album_id": album_id}, {"_id": 0, "url": 1}).to_list(None)
    for photo in photos:
        delete_upload_file(photo.get("url", ""))

    await db.gallery_albums.delete_one({"id": album_id})
    await db.gallery_photos.delete_many({"album_id": album_id})
    await create_audit_log(
        current_user.id,
        f"Removeu álbum de galeria {album_id} ({len(photos)} fotos)",
        album_id,
    )
    return {"message": "Album e fotos removidos"}


# ===== PHOTOS =====


@router.get("/photos")
async def get_gallery_photos(
    album_id: Optional[str] = None, status: Optional[str] = Query(None), current_user: User = Depends(get_current_user)
):
    query = {}
    if album_id:
        query["album_id"] = album_id

    # Staff de moderação (role OU privilégio moderate_content) pode filtrar por
    # status — antes só `admin` podia, e o moderador que listava fotos de um
    # álbum não via as pendentes que lhe compete moderar (incoerente com
    # /photos/pending, que já aceita moderador).
    is_staff = has_role_or_privilege(current_user, ("admin", "moderador"), "moderate_content")
    if status and is_staff:
        query["status"] = status
    elif not is_staff:
        query["status"] = "approved"

    photos = await db.gallery_photos.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return photos


@router.get("/photos/pending")
async def get_pending_photos(current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin", "moderador"), "moderate_content"):
        raise HTTPException(status_code=403, detail="Sem permissão para moderar conteúdo")
    photos = await db.gallery_photos.find({"status": "pending"}, {"_id": 0}).sort("created_at", -1).to_list(200)

    # Batch fetch album titles to avoid N+1
    album_ids = list(set(p.get("album_id") for p in photos if p.get("album_id")))
    albums = await db.gallery_albums.find({"id": {"$in": album_ids}}, {"_id": 0, "id": 1, "title": 1}).to_list(200)
    album_map = {a["id"]: a.get("title", "?") for a in albums}

    for p in photos:
        p["album_title"] = album_map.get(p.get("album_id"), "?")
    return photos


@router.post("/photos/upload")
async def upload_gallery_photo(
    album_id: str, caption: str = "", file: UploadFile = File(...), current_user: User = Depends(get_current_user)
):
    if current_user.status != "ativo" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas socios ativos podem submeter fotos")

    album = await db.gallery_albums.find_one({"id": album_id}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Album nao encontrado")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome de ficheiro em falta")

    contents = await file.read()
    if len(contents) > GALLERY_MAX_SIZE:
        raise HTTPException(status_code=413, detail="Arquivo excede o limite de 10 MB")

    # Defense-in-depth: Pillow.verify() bloqueia .exe -> .png e tambem
    # cross-checks que o formato real bate com a extensao.
    validate_file_content(contents, file.filename, GALLERY_ALLOWED_EXTS)

    ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = GALLERY_DIR / unique_filename

    # I/O off-loaded para thread — não bloquear o event loop com até 10 MB.
    await asyncio.to_thread(file_path.write_bytes, contents)

    photo_url = f"/uploads/gallery/{unique_filename}"
    is_admin = current_user.role == "admin"

    photo = GalleryPhoto(
        album_id=album_id,
        url=photo_url,
        caption=caption,
        status="approved" if is_admin else "pending",
        uploaded_by=current_user.id,
        uploaded_by_name=current_user.name,
    )
    photo_dict = photo.model_dump()
    await db.gallery_photos.insert_one(photo_dict)

    if is_admin:
        count = await db.gallery_photos.count_documents({"album_id": album_id, "status": "approved"})
        if count == 1:
            await db.gallery_albums.update_one({"id": album_id}, {"$set": {"cover_url": photo_url}})
    else:
        await notify_admins(
            "geral",
            "Nova Foto para Aprovacao",
            f"{current_user.name} submeteu uma foto no album '{album['title']}'.",
            "/galeria-admin",
        )

    return photo_dict


@router.patch("/photos/{photo_id}/approve")
async def approve_photo(photo_id: str, current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin", "moderador"), "moderate_content"):
        raise HTTPException(status_code=403, detail="Sem permissão para moderar conteúdo")
    photo = await db.gallery_photos.find_one({"id": photo_id}, {"_id": 0})
    if not photo:
        raise HTTPException(status_code=404, detail="Foto nao encontrada")

    await db.gallery_photos.update_one({"id": photo_id}, {"$set": {"status": "approved"}})

    album = await db.gallery_albums.find_one({"id": photo["album_id"]}, {"_id": 0})
    approved_count = await db.gallery_photos.count_documents({"album_id": photo["album_id"], "status": "approved"})
    if approved_count == 1 and album:
        await db.gallery_albums.update_one({"id": photo["album_id"]}, {"$set": {"cover_url": photo["url"]}})

    if photo.get("uploaded_by"):
        await create_notification(
            photo["uploaded_by"],
            "geral",
            "Foto Aprovada!",
            f"A sua foto no album '{album['title'] if album else '?'}' foi aprovada e esta visivel na galeria.",
            "/galeria",
        )

    await create_audit_log(current_user.id, f"Aprovou foto da galeria {photo_id}", photo_id)
    return {"message": "Foto aprovada"}


@router.patch("/photos/{photo_id}/reject")
async def reject_photo(photo_id: str, current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin", "moderador"), "moderate_content"):
        raise HTTPException(status_code=403, detail="Sem permissão para moderar conteúdo")
    photo = await db.gallery_photos.find_one({"id": photo_id}, {"_id": 0})
    if not photo:
        raise HTTPException(status_code=404, detail="Foto nao encontrada")

    delete_upload_file(photo.get("url", ""))

    await db.gallery_photos.delete_one({"id": photo_id})
    await _recompute_cover_if_needed(photo["album_id"], photo.get("url", ""))

    if photo.get("uploaded_by"):
        await create_notification(
            photo["uploaded_by"],
            "geral",
            "Foto Rejeitada",
            "A sua submissao de foto na galeria foi rejeitada pelo administrador.",
            None,
        )

    await create_audit_log(current_user.id, f"Rejeitou foto da galeria {photo_id}", photo_id)
    return {"message": "Foto rejeitada e removida"}


@router.delete("/photos/{photo_id}")
async def delete_gallery_photo(photo_id: str, current_user: User = Depends(get_current_user)):
    photo = await db.gallery_photos.find_one({"id": photo_id}, {"_id": 0})
    if not photo:
        raise HTTPException(status_code=404, detail="Foto nao encontrada")

    is_staff = has_role_or_privilege(current_user, ("admin", "moderador"), "moderate_content")
    is_owner = photo.get("uploaded_by") == current_user.id
    if not is_staff and not is_owner:
        raise HTTPException(status_code=403, detail="Sem permissao")

    delete_upload_file(photo.get("url", ""))

    await db.gallery_photos.delete_one({"id": photo_id})
    await _recompute_cover_if_needed(photo["album_id"], photo.get("url", ""))
    await create_audit_log(current_user.id, "gallery_photo_deleted", photo_id)
    return {"message": "Foto removida"}
