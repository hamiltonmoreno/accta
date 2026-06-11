from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from urllib.parse import urlparse
from models import User, Document, DocumentCreate
from database import UPLOAD_DIR, db
from auth import get_current_user, has_role_or_privilege
from helpers import create_audit_log

router = APIRouter(tags=["documents"])

VALID_DOCUMENT_VISIBILITIES = {"publico", "socios", "direcao", "privado"}
RESTRICTED_DOCUMENT_VISIBILITIES = {"direcao", "privado"}


def can_access_restricted_documents(user: User) -> bool:
    return user.role == "admin" or "manage_documents" in (user.privileges or [])


def get_allowed_document_visibilities(user: User) -> set[str]:
    allowed = {"publico", "socios"}
    if can_access_restricted_documents(user):
        allowed.update(RESTRICTED_DOCUMENT_VISIBILITIES)
    return allowed


def ensure_valid_document_visibility(visibility: str):
    if visibility not in VALID_DOCUMENT_VISIBILITIES:
        raise HTTPException(status_code=400, detail="Visibilidade de documento invalida")


def ensure_can_access_document(user: User, doc: dict):
    visibility = doc.get("visibility", "socios")
    ensure_valid_document_visibility(visibility)
    if visibility not in get_allowed_document_visibilities(user):
        raise HTTPException(status_code=403, detail="Sem permissao para aceder a este documento")


async def record_document_access(user_id: str, document_id: str):
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.document_accesses.insert_one(
        {
            "user_id": user_id,
            "document_id": document_id,
            "accessed_at": now_iso,
        }
    )
    return now_iso


def get_document_file_path(doc: dict) -> Path:
    file_url = doc.get("file_url", "")
    parsed_path = urlparse(file_url).path
    expected_prefix = "/uploads/documents/"
    if not parsed_path.startswith(expected_prefix):
        raise HTTPException(status_code=404, detail="Ficheiro do documento nao encontrado")

    filename = Path(parsed_path).name
    file_path = (UPLOAD_DIR / "documents" / filename).resolve()
    documents_dir = (UPLOAD_DIR / "documents").resolve()
    if not file_path.is_relative_to(documents_dir):
        raise HTTPException(status_code=400, detail="Caminho de documento invalido")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Ficheiro do documento nao encontrado")
    return file_path


def file_download_name(doc: dict, file_path: Path) -> str:
    title = str(doc.get("title") or "").strip()
    if not title:
        return file_path.name
    safe_title = "".join(c if c.isalnum() or c in (" ", "-", "_", ".") else "_" for c in title).strip()
    return f"{safe_title}{file_path.suffix}" if safe_title else file_path.name


@router.get("/documents/public")
async def get_public_documents():
    """Endpoint público — sem autenticação. Retorna apenas documentos com visibility='publico'."""
    docs = await db.documents.find({"visibility": "publico"}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return docs


@router.get("/documents/public/{document_id}/download")
async def download_public_document(document_id: str):
    doc = await db.documents.find_one({"id": document_id, "visibility": "publico"}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")

    file_path = get_document_file_path(doc)
    response = FileResponse(file_path, filename=file_download_name(doc, file_path))
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/documents", response_model=List[Document])
async def get_documents(current_user: User = Depends(get_current_user)):
    query = {}
    if not can_access_restricted_documents(current_user):
        query["visibility"] = {"$in": sorted(get_allowed_document_visibilities(current_user))}

    docs = await db.documents.find(query, {"_id": 0}).to_list(1000)
    return docs


@router.post("/documents", response_model=Document)
async def create_document(doc_data: DocumentCreate, current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin",), "manage_documents"):
        raise HTTPException(status_code=403, detail="Sem permissão para gerir documentos")
    ensure_valid_document_visibility(doc_data.visibility)

    doc = Document(**doc_data.model_dump())
    doc_dict = doc.model_dump()

    await db.documents.insert_one(doc_dict)
    await create_audit_log(current_user.id, f"Criou documento {doc.id}", doc.id)
    return doc


@router.get("/documents/{document_id}/download")
async def download_document(document_id: str, current_user: User = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": document_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    ensure_can_access_document(current_user, doc)

    # Resolve o ficheiro ANTES de registar o acesso: se faltar em disco (404),
    # não queremos um document_accesses para um download que falhou.
    file_path = get_document_file_path(doc)
    accessed_at = await record_document_access(current_user.id, document_id)
    response = FileResponse(file_path, filename=file_download_name(doc, file_path))
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Document-Accessed-At"] = accessed_at
    return response


@router.post("/documents/{document_id}/access")
async def register_document_access(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Record that the current user opened/downloaded a document.

    The frontend calls this when a member clicks the download/view link so the
    personal report reflects real engagement instead of placeholder counts.
    Members may only register access to documents they're allowed to see.
    """
    doc = await db.documents.find_one({"id": document_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    ensure_can_access_document(current_user, doc)

    now_iso = await record_document_access(current_user.id, document_id)
    return {"status": "recorded", "document_id": document_id, "accessed_at": now_iso}
