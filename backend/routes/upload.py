from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pathlib import Path
from models import User
from database import UPLOAD_DIR
from auth import get_current_user
from helpers import create_audit_log
import uuid
import shutil

router = APIRouter(tags=["upload"])

ALLOWED_EXTENSIONS = {
    "documents": [".pdf", ".doc", ".docx"],
    "proofs": [".pdf", ".jpg", ".jpeg", ".png"],
    "logos": [".png", ".jpg", ".jpeg", ".svg"],
    "avatars": [".jpg", ".jpeg", ".png"],
}

MAX_FILE_SIZES = {
    "documents": 10 * 1024 * 1024,   # 10 MB
    "proofs": 5 * 1024 * 1024,        # 5 MB
    "logos": 2 * 1024 * 1024,          # 2 MB
    "avatars": 2 * 1024 * 1024,        # 2 MB
}


def validate_file(file: UploadFile, category: str) -> None:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS.get(category, []):
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo não permitido. Permitidos: {', '.join(ALLOWED_EXTENSIONS[category])}"
        )


@router.post("/upload/{category}")
async def upload_file(
    category: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if category not in ["documents", "proofs", "logos", "avatars"]:
        raise HTTPException(status_code=400, detail="Categoria inválida")

    if category in ["documents", "logos"] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    validate_file(file, category)

    # Check file size
    max_size = MAX_FILE_SIZES.get(category, 5 * 1024 * 1024)
    contents = await file.read()
    if len(contents) > max_size:
        max_mb = max_size / (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"Arquivo excede o limite de {max_mb:.0f} MB")
    await file.seek(0)

    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / category / unique_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_url = f"/uploads/{category}/{unique_filename}"
        await create_audit_log(current_user.id, f"Upload de arquivo: {file.filename}", unique_filename)

        return {
            "filename": file.filename,
            "file_url": file_url,
            "size": file_path.stat().st_size,
            "category": category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")


@router.delete("/upload/{category}/{filename}")
async def delete_file(
    category: str,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    file_path = UPLOAD_DIR / category / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    try:
        file_path.unlink()
        await create_audit_log(current_user.id, f"Deletou arquivo: {filename}", filename)
        return {"message": "Arquivo deletado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar arquivo: {str(e)}")
