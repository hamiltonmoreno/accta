from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List, Optional
from models import User, Post, PostCreate
from database import db
from auth import get_current_user, get_optional_user
from helpers import create_audit_log

router = APIRouter(tags=["posts"])


@router.get("/posts", response_model=List[Post])
async def get_posts(
    visibility: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_user),
):
    # Anonimos: apenas posts publicos. Socios autenticados: publicos + socios.
    # Staff (admin/moderador): tudo, ou filtra pela visibility pedida.
    is_staff = current_user is not None and current_user.role in ("admin", "moderador")
    is_authed = current_user is not None

    query = {}
    if visibility:
        if visibility == "privado" and not is_staff:
            raise HTTPException(status_code=403, detail="Sem permissão")
        if visibility == "socios" and not is_authed:
            raise HTTPException(status_code=401, detail="Autenticacao necessaria")
        query["visibility"] = visibility
    else:
        if is_staff:
            pass  # ve tudo
        elif is_authed:
            query["visibility"] = {"$in": ["publico", "socios"]}
        else:
            query["visibility"] = "publico"

    posts = await db.posts.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    for p in posts:
        if isinstance(p.get("created_at"), str):
            p["created_at"] = datetime.fromisoformat(p["created_at"])
    return posts


@router.post("/posts", response_model=Post)
async def create_post(post_data: PostCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "moderador"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    post = Post(**post_data.model_dump())
    post_dict = post.model_dump()
    post_dict["created_at"] = post_dict["created_at"].isoformat()

    await db.posts.insert_one(post_dict)
    await create_audit_log(current_user.id, f"Criou post {post.id}", post.id)
    return post
