from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import List, Optional
from models import User, Event, EventCreate, EventUpdate
from database import db
from auth import get_current_user
from helpers import create_audit_log, create_notification, notify_all_active_users

router = APIRouter(tags=["events"])

VALID_EVENT_VISIBILITIES = {"publico", "socios", "direcao"}
MEMBER_EVENT_ROLES = {"socio", "financeiro", "moderador"}


def get_allowed_event_visibilities(user: User) -> set[str]:
    if user.role == "admin":
        return VALID_EVENT_VISIBILITIES
    if user.role in MEMBER_EVENT_ROLES:
        return {"publico", "socios"}
    return {"publico"}


def ensure_valid_event_visibility(visibility: str):
    if visibility not in VALID_EVENT_VISIBILITIES:
        raise HTTPException(status_code=400, detail="Visibilidade de evento invalida")


def ensure_can_view_event(user: User, event: dict):
    visibility = event.get("visibility", "publico")
    ensure_valid_event_visibility(visibility)
    if visibility not in get_allowed_event_visibilities(user):
        raise HTTPException(status_code=403, detail="Sem permissao para aceder a este evento")


def build_event_visibility_filter(user: User, requested_visibility: Optional[str] = None):
    allowed = get_allowed_event_visibilities(user)
    if requested_visibility:
        ensure_valid_event_visibility(requested_visibility)
        if requested_visibility not in allowed:
            raise HTTPException(status_code=403, detail="Sem permissao para esta visibilidade")
        return requested_visibility
    if user.role == "admin":
        return None
    if len(allowed) == 1:
        return next(iter(allowed))
    return {"$in": sorted(allowed)}


@router.get("/events", response_model=List[Event])
async def get_events(visibility: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {}
    visibility_filter = build_event_visibility_filter(current_user, visibility)
    if visibility_filter is not None:
        query["visibility"] = visibility_filter

    events = await db.events.find(query, {"_id": 0}).sort("date", 1).to_list(100)
    for e in events:
        if isinstance(e.get("date"), str):
            e["date"] = datetime.fromisoformat(e["date"])
        if isinstance(e.get("end_date"), str):
            e["end_date"] = datetime.fromisoformat(e["end_date"])
        if isinstance(e.get("created_at"), str):
            e["created_at"] = datetime.fromisoformat(e["created_at"])
    return events


@router.get("/events/public")
async def get_public_events():
    events = await db.events.find({"visibility": "publico"}, {"_id": 0}).sort("date", 1).to_list(100)
    for e in events:
        if isinstance(e.get("date"), str):
            e["date"] = datetime.fromisoformat(e["date"])
        if isinstance(e.get("end_date"), str):
            e["end_date"] = datetime.fromisoformat(e["end_date"])
        if isinstance(e.get("created_at"), str):
            e["created_at"] = datetime.fromisoformat(e["created_at"])
        e.pop("attendees", None)
    return events


@router.get("/events/featured")
async def get_featured_event():
    """Get the next upcoming public event for the homepage countdown."""
    now = datetime.now(timezone.utc).isoformat()
    event = await db.events.find_one(
        {"visibility": "publico", "date": {"$gte": now}, "status": {"$ne": "cancelado"}},
        {"_id": 0, "attendees": 0},
        sort=[("date", 1)],
    )
    if not event:
        return None
    if isinstance(event.get("date"), str):
        event["date"] = datetime.fromisoformat(event["date"])
    if isinstance(event.get("end_date"), str):
        event["end_date"] = datetime.fromisoformat(event["end_date"])
    if isinstance(event.get("created_at"), str):
        event["created_at"] = datetime.fromisoformat(event["created_at"])
    attendee_count = await db.events.find_one({"id": event["id"]}, {"_id": 0, "attendees": 1})
    event["attendee_count"] = len(attendee_count.get("attendees", [])) if attendee_count else 0
    return event


@router.get("/events/upcoming")
async def get_upcoming_events(current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    query = {"date": {"$gte": now}}
    visibility_filter = build_event_visibility_filter(current_user)
    if visibility_filter is not None:
        query["visibility"] = visibility_filter

    events = await db.events.find(query, {"_id": 0}).sort("date", 1).limit(5).to_list(None)
    for e in events:
        if isinstance(e.get("date"), str):
            e["date"] = datetime.fromisoformat(e["date"])
        if isinstance(e.get("end_date"), str):
            e["end_date"] = datetime.fromisoformat(e["end_date"])
        if isinstance(e.get("created_at"), str):
            e["created_at"] = datetime.fromisoformat(e["created_at"])
    return events


@router.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str, current_user: User = Depends(get_current_user)):
    event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    ensure_can_view_event(current_user, event)

    if isinstance(event.get("date"), str):
        event["date"] = datetime.fromisoformat(event["date"])
    if isinstance(event.get("end_date"), str):
        event["end_date"] = datetime.fromisoformat(event["end_date"])
    if isinstance(event.get("created_at"), str):
        event["created_at"] = datetime.fromisoformat(event["created_at"])
    return event


@router.post("/events", response_model=Event)
async def create_event(event_data: EventCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar eventos")
    ensure_valid_event_visibility(event_data.visibility)

    event = Event(created_by=current_user.id, **event_data.model_dump())
    event_dict = event.model_dump()
    event_dict["date"] = event_dict["date"].isoformat()
    if event_dict.get("end_date"):
        event_dict["end_date"] = event_dict["end_date"].isoformat()
    event_dict["created_at"] = event_dict["created_at"].isoformat()

    await db.events.insert_one(event_dict)
    await create_audit_log(current_user.id, f"Criou evento {event.title}", event.id)

    if event_data.visibility in ["publico", "socios"]:
        await notify_all_active_users("event_new", "Novo Evento", f"Novo evento: {event.title}", "/eventos")
    return event


@router.patch("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, event_data: EventUpdate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    update_data = {k: v for k, v in event_data.model_dump().items() if v is not None}
    if "visibility" in update_data:
        ensure_valid_event_visibility(update_data["visibility"])
    if "date" in update_data:
        update_data["date"] = update_data["date"].isoformat()
    if "end_date" in update_data:
        update_data["end_date"] = update_data["end_date"].isoformat()

    await db.events.update_one({"id": event_id}, {"$set": update_data})
    await create_audit_log(current_user.id, f"Atualizou evento {event_id}", event_id)

    updated_event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if isinstance(updated_event.get("date"), str):
        updated_event["date"] = datetime.fromisoformat(updated_event["date"])
    if isinstance(updated_event.get("end_date"), str):
        updated_event["end_date"] = datetime.fromisoformat(updated_event["end_date"])
    if isinstance(updated_event.get("created_at"), str):
        updated_event["created_at"] = datetime.fromisoformat(updated_event["created_at"])
    return updated_event


@router.delete("/events/{event_id}")
async def delete_event(event_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    result = await db.events.delete_one({"id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    await create_audit_log(current_user.id, f"Eliminou evento {event_id}", event_id)
    return {"message": "Evento eliminado"}


@router.post("/events/{event_id}/register")
async def register_for_event(event_id: str, current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Apenas sócios ativos podem inscrever-se")

    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    ensure_can_view_event(current_user, event)

    if current_user.id in event.get("attendees", []):
        raise HTTPException(status_code=400, detail="Já está inscrito neste evento")

    if event.get("max_attendees") and len(event.get("attendees", [])) >= event["max_attendees"]:
        raise HTTPException(status_code=400, detail="Evento já está lotado")

    await db.events.update_one({"id": event_id}, {"$push": {"attendees": current_user.id}})
    await create_notification(
        current_user.id,
        "event_registered",
        "Inscrição Confirmada",
        f"Sua inscrição no evento '{event['title']}' foi confirmada.",
        "/eventos",
    )
    return {"message": "Inscrição realizada com sucesso"}


@router.delete("/events/{event_id}/register")
async def unregister_from_event(event_id: str, current_user: User = Depends(get_current_user)):
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    ensure_can_view_event(current_user, event)

    if current_user.id not in event.get("attendees", []):
        raise HTTPException(status_code=400, detail="Não está inscrito neste evento")

    await db.events.update_one({"id": event_id}, {"$pull": {"attendees": current_user.id}})
    return {"message": "Inscrição cancelada"}


@router.get("/events/{event_id}/attendees")
async def get_event_attendees(event_id: str, current_user: User = Depends(get_current_user)):
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    ensure_can_view_event(current_user, event)

    if current_user.role != "admin" and current_user.id != event.get("created_by"):
        return {
            "count": len(event.get("attendees", [])),
            "is_registered": current_user.id in event.get("attendees", []),
            "attendees": [],
        }

    attendee_ids = event.get("attendees", [])
    if not attendee_ids:
        return {"count": 0, "is_registered": False, "attendees": []}

    attendees = await db.users.find(
        {"id": {"$in": attendee_ids}}, {"_id": 0, "id": 1, "name": 1, "email": 1, "member_id": 1}
    ).to_list(None)

    return {"count": len(attendees), "is_registered": current_user.id in attendee_ids, "attendees": attendees}
