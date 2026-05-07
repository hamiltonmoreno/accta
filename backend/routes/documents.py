from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import List
from models import User, Document, DocumentCreate
from database import db
from auth import get_current_user
from helpers import create_audit_log

router = APIRouter(tags=["documents"])


@router.get("/documents/public")
async def get_public_documents():
    """Endpoint público — sem autenticação. Retorna apenas documentos com visibility='publico'."""
    docs = await db.documents.find({"visibility": "publico"}, {"_id": 0}).sort("created_at", -1).to_list(100)
    for d in docs:
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
    return docs


@router.get("/documents", response_model=List[Document])
async def get_documents(current_user: User = Depends(get_current_user)):
    if current_user.role in ["admin", "financeiro", "moderador"]:
        docs = await db.documents.find({}, {"_id": 0}).to_list(1000)
    else:
        docs = await db.documents.find({"visibility": {"$in": ["publico", "socios"]}}, {"_id": 0}).to_list(1000)

    for d in docs:
        if isinstance(d.get("created_at"), str):
            d["created_at"] = datetime.fromisoformat(d["created_at"])
    return docs


@router.post("/documents", response_model=Document)
async def create_document(doc_data: DocumentCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    doc = Document(**doc_data.model_dump())
    doc_dict = doc.model_dump()
    doc_dict["created_at"] = doc_dict["created_at"].isoformat()

    await db.documents.insert_one(doc_dict)
    await create_audit_log(current_user.id, f"Criou documento {doc.id}", doc.id)
    return doc


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

    visibility = doc.get("visibility", "socios")
    is_staff = current_user.role in ["admin", "financeiro", "moderador"]
    if visibility == "privado" and not is_staff:
        raise HTTPException(status_code=403, detail="Sem permissão para aceder a este documento")

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.document_accesses.insert_one(
        {
            "user_id": current_user.id,
            "document_id": document_id,
            "accessed_at": now_iso,
        }
    )
    return {"status": "recorded", "document_id": document_id, "accessed_at": now_iso}
