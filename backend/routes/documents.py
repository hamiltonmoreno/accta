from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List
from models import User, Document, DocumentCreate
from database import db
from auth import get_current_user
from helpers import create_audit_log

router = APIRouter(tags=["documents"])


@router.get("/documents", response_model=List[Document])
async def get_documents(current_user: User = Depends(get_current_user)):
    if current_user.role in ["admin", "financeiro", "moderador"]:
        docs = await db.documents.find({}, {"_id": 0}).to_list(1000)
    else:
        docs = await db.documents.find({"visibility": {"$in": ["publico", "socios"]}}, {"_id": 0}).to_list(1000)

    for d in docs:
        if isinstance(d.get('created_at'), str):
            d['created_at'] = datetime.fromisoformat(d['created_at'])
    return docs


@router.post("/documents", response_model=Document)
async def create_document(doc_data: DocumentCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    doc = Document(**doc_data.model_dump())
    doc_dict = doc.model_dump()
    doc_dict['created_at'] = doc_dict['created_at'].isoformat()

    await db.documents.insert_one(doc_dict)
    await create_audit_log(current_user.id, f"Criou documento {doc.id}", doc.id)
    return doc
