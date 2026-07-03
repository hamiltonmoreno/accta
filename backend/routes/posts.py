import re
import unicodedata
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from auth import get_current_user, has_any_role, get_optional_user
from database import db
from helpers import create_audit_log, delete_upload_file, notify_all_active_users
from models import POST_TYPES, Post, PostCreate, PostUpdate, User

router = APIRouter(tags=["posts"])


# --------------------------------------------------------------------------- #
# Slug helpers (spec-blog-noticias §4.3) — sem dependência nova.
# --------------------------------------------------------------------------- #


def slugify(text: str) -> str:
    """Minúsculas, sem acentos, [^a-z0-9]+ -> '-', trim de '-'."""
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "post"


async def _unique_slug(base: str, exclude_id: Optional[str] = None) -> str:
    """Garante unicidade do slug, sufixando -2, -3… em caso de colisão."""
    slug = base
    n = 2
    while True:
        existing = await db.posts.find_one({"slug": slug}, {"_id": 0, "id": 1})
        if not existing or (exclude_id and existing.get("id") == exclude_id):
            return slug
        slug = f"{base}-{n}"
        n += 1


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #


@router.get("/posts", response_model=List[Post])
async def get_posts(
    visibility: Optional[str] = None,
    type_: Optional[str] = Query(None, alias="type"),
    status: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: Optional[User] = Depends(get_optional_user),
):
    # Anónimos: apenas posts publicos+publicados. Socios autenticados: publicos +
    # socios (publicados). Staff (admin/moderador): tudo, incluindo rascunhos.
    is_staff = current_user is not None and has_any_role(current_user, "admin", "moderador")
    is_authed = current_user is not None

    query: dict = {}

    if visibility:
        if visibility == "privado" and not is_staff:
            raise HTTPException(status_code=403, detail="Sem permissão")
        if visibility == "socios" and not is_authed:
            raise HTTPException(status_code=401, detail="Autenticacao necessaria")
        query["visibility"] = visibility
    elif is_staff:
        pass  # ve tudo
    elif is_authed:
        query["visibility"] = {"$in": ["publico", "socios"]}
    else:
        query["visibility"] = "publico"

    # Status: não-staff nunca veem rascunhos; staff pode filtrar por status.
    if not is_staff:
        query["status"] = "publicado"
    elif status in ("rascunho", "publicado"):
        query["status"] = status

    if type_ in POST_TYPES:
        query["type"] = type_

    if q:
        query["title"] = {"$regex": re.escape(q), "$options": "i"}

    # Ordenação + paginação no DB por data efetiva (COALESCE published_at→
    # created_at — um rascunho antigo publicado hoje aparece como recente):
    # evita o teto silencioso de 1000 que tornava o 1001.º+ post inacessível.
    posts = (
        await db.posts.find(query, {"_id": 0})
        .sort([(("published_at", "created_at"), -1)])
        .skip(skip)
        .limit(limit)
        .to_list(None)
    )
    return posts


@router.get("/posts/{id_or_slug}", response_model=Post)
async def get_post(id_or_slug: str, current_user: Optional[User] = Depends(get_optional_user)):
    is_staff = current_user is not None and has_any_role(current_user, "admin", "moderador")
    is_authed = current_user is not None

    post = await db.posts.find_one({"slug": id_or_slug}, {"_id": 0})
    if not post:
        post = await db.posts.find_one({"id": id_or_slug}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    # Mesma regra de visibilidade do GET /posts. 404 (não 403) p/ não revelar
    # a existência de conteúdo restrito a quem não pode vê-lo.
    if not is_staff:
        if post.get("status") != "publicado":
            raise HTTPException(status_code=404, detail="Post não encontrado")
        vis = post.get("visibility", "publico")
        if vis == "privado":
            raise HTTPException(status_code=404, detail="Post não encontrado")
        if vis == "socios" and not is_authed:
            raise HTTPException(status_code=404, detail="Post não encontrado")

    return post


@router.post("/posts", response_model=Post)
async def create_post(post_data: PostCreate, current_user: User = Depends(get_current_user)):
    if not has_any_role(current_user, "admin", "moderador"):
        raise HTTPException(status_code=403, detail="Sem permissão")

    data = post_data.model_dump()
    notify_socios = data.pop("notify_socios", False)

    post = Post(**data)
    post.author_id = current_user.id
    post.author_name = current_user.name
    post.slug = await _unique_slug(slugify(post.title))
    if post.status == "publicado":
        post.published_at = datetime.now(timezone.utc).isoformat()

    post_dict = post.model_dump()

    await db.posts.insert_one(post_dict)
    await create_audit_log(current_user.id, f"Criou post {post.id}", post.id)

    # D5 — notificação in-app (não email) opcional ao publicar para sócios.
    if notify_socios and post.status == "publicado" and post.visibility == "socios":
        await notify_all_active_users(
            "system",
            "Nova notícia para sócios",
            post.title,
            link=f"/noticias/{post.slug or post.id}",
        )

    return post


@router.patch("/posts/{post_id}", response_model=Post)
async def update_post(post_id: str, payload: PostUpdate, current_user: User = Depends(get_current_user)):
    if not has_any_role(current_user, "admin", "moderador"):
        raise HTTPException(status_code=403, detail="Sem permissão")

    existing = await db.posts.find_one({"id": post_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    update_data = payload.model_dump(exclude_unset=True)
    regenerate_slug = update_data.pop("regenerate_slug", False)

    # Limpeza da capa antiga se for trocada (evita ficheiros órfãos).
    new_cover = update_data.get("cover_url")
    old_cover = existing.get("cover_url")
    if "cover_url" in update_data and old_cover and old_cover != new_cover:
        delete_upload_file(old_cover)

    # published_at: definir na 1ª transição para publicado.
    new_status = update_data.get("status", existing.get("status"))
    if new_status == "publicado" and not existing.get("published_at"):
        update_data["published_at"] = datetime.now(timezone.utc).isoformat()

    # Slug estável: só regenerar enquanto rascunho e a pedido explícito.
    if regenerate_slug and existing.get("status") == "rascunho":
        title = update_data.get("title", existing.get("title", ""))
        update_data["slug"] = await _unique_slug(slugify(title), exclude_id=post_id)

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.posts.update_one({"id": post_id}, {"$set": update_data})
    await create_audit_log(current_user.id, f"Editou post {post_id}", post_id)

    return await db.posts.find_one({"id": post_id}, {"_id": 0})


@router.delete("/posts/{post_id}")
async def delete_post(post_id: str, current_user: User = Depends(get_current_user)):
    if not has_any_role(current_user, "admin", "moderador"):
        raise HTTPException(status_code=403, detail="Sem permissão")

    existing = await db.posts.find_one({"id": post_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    cover = existing.get("cover_url")
    if cover and cover.startswith("/uploads/covers/"):
        delete_upload_file(cover)

    await db.posts.delete_one({"id": post_id})
    await create_audit_log(current_user.id, f"Eliminou post {post_id}", post_id)

    return {"message": "Post eliminado com sucesso"}
