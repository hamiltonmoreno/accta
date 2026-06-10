from fastapi import APIRouter, Depends
from database import db
from auth import get_current_user
from models import User
from ranking import gather_signal_counts

router = APIRouter(tags=["report"])


@router.get("/report/personal")
async def get_personal_report(current_user: User = Depends(get_current_user)):
    """Aggregate personal activity stats for the current user."""
    uid = current_user.id

    # Sinais de atuação partilhados com o ranking — fonte única de contagem
    # (`ranking.gather_signal_counts`), período "all" = histórico completo. A
    # comparência eleitoral fica de fora (não é exibida aqui). O contrato de
    # saída deste endpoint mantém-se EXACTAMENTE igual (o dashboard usa-o).
    signals = await gather_signal_counts(uid, "all", include_turnout=False)

    # Denominadores e sinais não pontuados (locais — não fazem parte do score).
    # O denominador inclui os eventos que o utilizador podia ver (publico/socios)
    # MAIS qualquer evento restrito (direcao/privado) em que esteve presente —
    # senão `events_attended` (que conta presenças em qualquer visibilidade)
    # podia exceder `total_events` e dar um rácio > 100%.
    total_events = await db.events.count_documents(
        {"$or": [{"visibility": {"$in": ["publico", "socios"]}}, {"attendees": uid}]}
    )
    total_polls = await db.polls.count_documents({"status": {"$in": ["aberta", "encerrada"]}})
    benefits_used = await db.benefit_validations.count_documents({"user_id": uid})
    photos_submitted = await db.gallery_photos.count_documents({"uploaded_by": uid})

    # Documentos disponíveis para o utilizador.
    document_visibilities = ["publico", "socios"]
    if current_user.role == "admin" or "manage_documents" in (current_user.privileges or []):
        document_visibilities.extend(["direcao", "privado"])
    documents_count = await db.documents.count_documents({"visibility": {"$in": document_visibilities}})

    # Documentos únicos a que o utilizador acedeu (deduplicado: abrir o mesmo
    # 5 vezes conta como 1). Total de eventos vai em document_access_events.
    pipeline = [
        {"$match": {"user_id": uid}},
        {"$group": {"_id": "$document_id"}},
        {"$count": "n"},
    ]
    unique_cursor = await db.document_accesses.aggregate(pipeline).to_list(1)
    documents_accessed = unique_cursor[0]["n"] if unique_cursor else 0
    document_access_events = await db.document_accesses.count_documents({"user_id": uid})

    return {
        "events_attended": signals["evento_presenca"],
        "total_events": total_events,
        "polls_voted": signals["votacao_voto"],
        "total_polls": total_polls,
        "wall_posts": signals["mural_post"],
        "likes_received": signals["mural_like_recebido"],
        "wall_comments": signals["mural_comentario"],
        "projects_member": signals["projeto_participacao"],
        "benefits_used": benefits_used,
        "photos_submitted": photos_submitted,
        "photos_approved": signals["galeria_foto"],
        "documents_available": documents_count,
        "documents_accessed": documents_accessed,
        "document_access_events": document_access_events,
    }
