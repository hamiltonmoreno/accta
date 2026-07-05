from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from models import User, WallPost, WallPostCreate, WallComment, WallCommentCreate
from database import db
from auth import get_current_user, has_role_or_privilege
from helpers import create_audit_log, create_notification, enrich_author_photos

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
        p.setdefault("likes", [])
        p.setdefault("comment_count", 0)
        p.setdefault("category", "geral")
        p.setdefault("pinned", False)

    await enrich_author_photos(posts)
    return posts


@router.get("/wall/pending")
async def get_pending_wall_posts(current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin",), "moderate_content"):
        raise HTTPException(status_code=403, detail="Sem permissão")

    posts = await db.wall_posts.find({"approved": False}, {"_id": 0}).sort("created_at", -1).to_list(100)
    for p in posts:
        p.setdefault("likes", [])
        p.setdefault("comment_count", 0)
        p.setdefault("category", "geral")
    await enrich_author_photos(posts)
    return posts


@router.post("/wall")
async def create_wall_post(post_data: WallPostCreate, current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Apenas sócios ativos podem postar")

    auto_approve = has_role_or_privilege(current_user, ("admin",), "moderate_content")

    post = WallPost(
        user_id=current_user.id, user_name=current_user.name, approved=auto_approve, **post_data.model_dump()
    )
    post_dict = post.model_dump()

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
    if not has_role_or_privilege(current_user, ("admin",), "moderate_content"):
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

    if (
        not has_role_or_privilege(current_user, ("admin",), "moderate_content")
        and current_user.id != post["user_id"]
    ):
        raise HTTPException(status_code=403, detail="Sem permissão")

    await db.wall_posts.delete_one({"id": post_id})
    await db.wall_comments.delete_many({"post_id": post_id})
    await create_audit_log(current_user.id, f"Removeu post do mural {post_id}", post_id)
    return {"message": "Post removido"}


@router.patch("/wall/{post_id}/pin")
async def pin_wall_post(post_id: str, current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin",), "moderate_content"):
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

    # Não permitir like em conteúdo invisível: posts ainda em moderação (não
    # aprovados) só são visíveis ao staff de moderação e ao próprio autor, tal
    # como em `create_wall_comment`. Para o sócio comum o post não existe (404).
    if not post.get("approved"):
        is_staff = has_role_or_privilege(current_user, ("admin",), "moderate_content")
        is_author = post.get("user_id") == current_user.id
        if not is_staff and not is_author:
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
    post = await db.wall_posts.find_one({"id": post_id}, {"_id": 0, "approved": 1})
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    is_staff = has_role_or_privilege(current_user, ("admin",), "moderate_content")
    if not post.get("approved") and not is_staff:
        raise HTTPException(status_code=403, detail="Sem permissão")
    comments = await db.wall_comments.find({"post_id": post_id}, {"_id": 0}).sort("created_at", 1).to_list(100)
    await enrich_author_photos(comments)
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

    # Não permitir comentar posts ainda em moderação (não aprovados): o sócio
    # comum nem sequer os consegue ler, e isto incrementava comment_count e
    # notificava o autor de comentários que ficariam órfãos se o post fosse
    # rejeitado. Staff de moderação (role OU privilégio moderate_content, igual
    # ao resto da rota) pode comentar no âmbito da moderação.
    if not post.get("approved") and not has_role_or_privilege(current_user, ("admin",), "moderate_content"):
        raise HTTPException(status_code=403, detail="Não é possível comentar um post em moderação")

    comment = WallComment(
        post_id=post_id, user_id=current_user.id, user_name=current_user.name, **comment_data.model_dump()
    )
    comment_dict = comment.model_dump()

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

    if (
        not has_role_or_privilege(current_user, ("admin",), "moderate_content")
        and current_user.id != comment["user_id"]
    ):
        raise HTTPException(status_code=403, detail="Sem permissão")

    await db.wall_comments.delete_one({"id": comment_id})
    # Recomputa em vez de $inc -1 (sem floor, podia ficar negativo em
    # legados/double-delete).
    remaining = await db.wall_comments.count_documents({"post_id": post_id})
    await db.wall_posts.update_one({"id": post_id}, {"$set": {"comment_count": remaining}})
    await create_audit_log(current_user.id, "wall_comment_deleted", comment_id, details={"post_id": post_id})
    return {"message": "Comentário removido"}
