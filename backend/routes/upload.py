from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pathlib import Path
from models import User
from database import UPLOAD_DIR
from auth import get_current_user
from helpers import create_audit_log
from file_validation import validate_file_content
import asyncio
import uuid

router = APIRouter(tags=["upload"])

ALLOWED_EXTENSIONS = {
    "documents": [".pdf", ".doc", ".docx"],
    "proofs": [".pdf", ".jpg", ".jpeg", ".png"],
    "logos": [".png", ".jpg", ".jpeg"],  # SVG bloqueado: risco de stored XSS
    "avatars": [".jpg", ".jpeg", ".png"],
    "banners": [".jpg", ".jpeg", ".png", ".webp"],  # hero wide (spec-padronizacao-banners)
    "brand": [".png", ".jpg", ".jpeg", ".webp"],  # logo da marca (spec-gestao-logo-marca); SVG bloqueado (XSS)
    "covers": [".png", ".jpg", ".jpeg"],  # capa de notícia (spec-blog-noticias); SVG bloqueado (XSS)
}

MAX_FILE_SIZES = {
    "documents": 10 * 1024 * 1024,  # 10 MB
    "proofs": 5 * 1024 * 1024,  # 5 MB
    "logos": 2 * 1024 * 1024,  # 2 MB
    "avatars": 2 * 1024 * 1024,  # 2 MB
    "banners": 4 * 1024 * 1024,  # 4 MB (hero wide)
    "brand": 2 * 1024 * 1024,  # 2 MB (logo)
    "covers": 2 * 1024 * 1024,  # 2 MB (capa de notícia)
}


@router.post("/upload/{category}")
async def upload_file(category: str, file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if category not in ["documents", "proofs", "logos", "avatars", "banners", "brand", "covers"]:
        raise HTTPException(status_code=400, detail="Categoria inválida")

    if category in ["documents", "logos"] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    # Banners, marca e capas de notícia: gestão de conteúdo (admin+moderador).
    if category in ("banners", "brand", "covers") and current_user.role not in ("admin", "moderador"):
        raise HTTPException(status_code=403, detail="Sem permissão")

    # Le tudo em memoria (limite por categoria, max 10MB) — necessario para
    # validacao de magic bytes / Pillow.verify().
    max_size = MAX_FILE_SIZES.get(category, 5 * 1024 * 1024)
    contents = await file.read()
    if len(contents) > max_size:
        max_mb = max_size / (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"Arquivo excede o limite de {max_mb:.0f} MB")

    # Valida extensao + conteudo real (defense-in-depth contra .exe -> .png).
    validate_file_content(contents, file.filename, ALLOWED_EXTENSIONS[category])

    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    category_dir = UPLOAD_DIR / category
    file_path = category_dir / unique_filename

    try:
        await asyncio.to_thread(category_dir.mkdir, parents=True, exist_ok=True)
        # Gravação off-loaded para thread: até 10 MB de I/O síncrono não pode
        # bloquear o event loop e parar requisições concorrentes do worker.
        await asyncio.to_thread(file_path.write_bytes, contents)

        file_url = f"/uploads/{category}/{unique_filename}"
        await create_audit_log(current_user.id, f"Upload de arquivo: {file.filename}", unique_filename)

        return {"filename": file.filename, "file_url": file_url, "size": len(contents), "category": category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")


@router.delete("/upload/{category}/{filename}")
async def delete_file(category: str, filename: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    if category not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Categoria inválida")

    file_path = (UPLOAD_DIR / category / filename).resolve()
    upload_root = UPLOAD_DIR.resolve()
    # Path traversal guard: resolved path must stay inside UPLOAD_DIR/<category>
    if not file_path.is_relative_to(upload_root / category):
        raise HTTPException(status_code=400, detail="Caminho inválido")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    try:
        file_path.unlink()
        await create_audit_log(current_user.id, f"Deletou arquivo: {filename}", filename)
        return {"message": "Arquivo deletado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar arquivo: {str(e)}")
