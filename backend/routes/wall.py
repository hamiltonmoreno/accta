from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional
from models import User, WallPost, WallPostCreate, WallComment, WallCommentCreate
from database import db
from auth import get_current_user
from helpers import create_audit_log, create_notification

router = APIRouter(tags=["wall"])


@router.get("/wall")
async def get_wall_posts(category: Optional[str] = None, current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Sem permissão")

    query = {"approved": True}
    if category and category != "todos":
        query["category"] = category

    posts = await db.wall_posts.find(query, {"_id": 0}).sort([("pinned", -1), ("created_at", -1)]).to_list(100)
    for p in posts:
        if isinstance(p.get("created_at"), str):
            p["created_at"] = datetime.fromisoformat(p["created_at"])
        p.setdefault("likes", [])
        p.setdefault("comment_count", 0)
        p.setdefault("category", "geral")
        p.setdefault("pinned", False)

    return posts


@router.get("/wall/pending")
async def get_pending_wall_posts(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "moderador"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    posts = await db.wall_posts.find({"approved": False}, {"_id": 0}).sort("created_at", -1).to_list(100)
    for p in posts:
        if isinstance(p.get("created_at"), str):
            p["created_at"] = datetime.fromisoformat(p["created_at"])
        p.setdefault("likes", [])
        p.setdefault("comment_count", 0)
        p.setdefault("category", "geral")
    return posts


@router.post("/wall")
async def create_wall_post(post_data: WallPostCreate, current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Apenas sócios ativos podem postar")

    auto_approve = current_user.role in ["admin", "moderador"]

    post = WallPost(
        user_id=current_user.id, user_name=current_user.name, approved=auto_approve, **post_data.model_dump()
    )
    post_dict = post.model_dump()
    post_dict["created_at"] = post_dict["created_at"].isoformat()

    await db.wall_posts.insert_one(post_dict)

    if not auto_approve:
        admins = await db.users.find({"role": {"$in": ["admin", "moderador"]}}, {"_id": 0, "id": 1}).to_list(100)
        for admin in admins:
            await create_notification(
                admin["id"],
                "wall_post_pending",
                "Post Pendente",
                f"{current_user.name} publicou uma mensagem que aguarda aprovação.",
                "/mural",
            )

    post_dict.pop("_id", None)
    return post_dict


@router.patch("/wall/{post_id}/approve")
async def approve_wall_post(post_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "moderador"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    post = await db.wall_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    await db.wall_posts.update_one({"id": post_id}, {"$set": {"approved": True}})
    await create_audit_log(current_user.id, f"Aprovou post do mural {post_id}", post_id)
    await create_notification(
        post["user_id"],
        "wall_post_approved",
        "Post Aprovado",
        "Sua mensagem no mural foi aprovada e já está visível.",
        "/mural",
    )
    return {"message": "Post aprovado"}


@router.delete("/wall/{post_id}")
async def delete_wall_post(post_id: str, current_user: User = Depends(get_current_user)):
    post = await db.wall_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    if current_user.role not in ["admin", "moderador"] and current_user.id != post["user_id"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    await db.wall_posts.delete_one({"id": post_id})
    await db.wall_comments.delete_many({"post_id": post_id})
    await create_audit_log(current_user.id, f"Removeu post do mural {post_id}", post_id)
    return {"message": "Post removido"}


@router.patch("/wall/{post_id}/pin")
async def pin_wall_post(post_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "moderador"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    post = await db.wall_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    new_pinned = not post.get("pinned", False)
    await db.wall_posts.update_one({"id": post_id}, {"$set": {"pinned": new_pinned}})
    await create_audit_log(
        current_user.id,
        f"{'Fixou' if new_pinned else 'Desfixou'} post do mural {post_id}",
        post_id,
    )
    return {"message": "Post fixado" if new_pinned else "Post desfixado", "pinned": new_pinned}


@router.patch("/wall/{post_id}/like")
async def toggle_like_wall_post(post_id: str, current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Sem permissão")

    post = await db.wall_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    likes = post.get("likes", [])
    if current_user.id in likes:
        await db.wall_posts.update_one({"id": post_id}, {"$pull": {"likes": current_user.id}})
        liked = False
    else:
        await db.wall_posts.update_one({"id": post_id}, {"$push": {"likes": current_user.id}})
        liked = True

    updated = await db.wall_posts.find_one({"id": post_id}, {"_id": 0, "likes": 1})
    return {"liked": liked, "like_count": len(updated.get("likes", []))}


# COMMENTS


@router.get("/wall/{post_id}/comments")
async def get_wall_comments(post_id: str, current_user: User = Depends(get_current_user)):
    comments = await db.wall_comments.find({"post_id": post_id}, {"_id": 0}).sort("created_at", 1).to_list(100)
    for c in comments:
        if isinstance(c.get("created_at"), str):
            c["created_at"] = datetime.fromisoformat(c["created_at"])
    return comments


@router.post("/wall/{post_id}/comments")
async def create_wall_comment(
    post_id: str, comment_data: WallCommentCreate, current_user: User = Depends(get_current_user)
):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Apenas sócios ativos podem comentar")

    post = await db.wall_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    comment = WallComment(
        post_id=post_id, user_id=current_user.id, user_name=current_user.name, **comment_data.model_dump()
    )
    comment_dict = comment.model_dump()
    comment_dict["created_at"] = comment_dict["created_at"].isoformat()

    await db.wall_comments.insert_one(comment_dict)
    await db.wall_posts.update_one({"id": post_id}, {"$inc": {"comment_count": 1}})

    if post["user_id"] != current_user.id:
        await create_notification(
            post["user_id"],
            "wall_comment",
            "Novo Comentário",
            f"{current_user.name} comentou na sua publicação.",
            "/mural",
        )

    comment_dict.pop("_id", None)
    return comment_dict


@router.delete("/wall/{post_id}/comments/{comment_id}")
async def delete_wall_comment(post_id: str, comment_id: str, current_user: User = Depends(get_current_user)):
    comment = await db.wall_comments.find_one({"id": comment_id, "post_id": post_id}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comentário não encontrado")

    if current_user.role not in ["admin", "moderador"] and current_user.id != comment["user_id"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    await db.wall_comments.delete_one({"id": comment_id})
    await db.wall_posts.update_one({"id": post_id}, {"$inc": {"comment_count": -1}})
    return {"message": "Comentário removido"}
