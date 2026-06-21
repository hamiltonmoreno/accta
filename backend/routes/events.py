from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timezone
from typing import List, Optional
from models import (
    User,
    Event,
    EventCreate,
    EventUpdate,
    EventExpenseCreate,
    EventReceitaCreate,
    Transaction,
    EXPENSE_CATEGORIES,
)
from database import db, register_event_attendee
from auth import get_current_user, has_role_or_privilege
from helpers import coaprovacao_limiar, create_audit_log, create_notification, notify_all_active_users

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


def _event_datetime(value) -> Optional[datetime]:
    if value is None:
        return None
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def event_registration_has_ended(event: dict) -> bool:
    event_end = _event_datetime(event.get("end_date") or event.get("date"))
    return event_end is not None and event_end <= datetime.now(timezone.utc)


# ===== FINANÇAS DE EVENTO (spec-eventos-multas-caixa) =====
# Despesa/receita de evento = Transaction com event_id (fonte única). Resultado
# do evento derivado por agregação. Mesmo guard de gestão do evento.


def _require_manage_events(user: User):
    if not has_role_or_privilege(user, ("admin",), "manage_events"):
        raise HTTPException(status_code=403, detail="Sem permissão para gerir eventos")


async def _event_result(event_id: str) -> dict:
    """Resultado financeiro do evento: receitas, despesas e resultado (= receitas −
    despesas), agregado das transações com este event_id."""
    pipeline = [
        {"$match": {"event_id": event_id}},
        {"$group": {"_id": "$type", "total": {"$sum": "$amount"}}},
    ]
    receitas = despesas = 0.0
    async for row in db.transactions.aggregate(pipeline):
        if row.get("_id") == "receita":
            receitas = row.get("total") or 0.0
        elif row.get("_id") == "despesa":
            despesas = row.get("total") or 0.0
    return {"receitas": receitas, "despesas": despesas, "resultado": receitas - despesas}


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
    return events


@router.get("/events/public")
async def get_public_events():
    events = await db.events.find({"visibility": "publico"}, {"_id": 0}).sort("date", 1).to_list(100)
    for e in events:
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
    return events


@router.get("/events/{event_id}")
async def get_event(event_id: str, current_user: User = Depends(get_current_user)):
    # NB: sem response_model=Event — anexamos `resultado_financeiro` derivado
    # (spec-eventos-multas-caixa); Event tem extra="ignore" e removeria o campo.
    event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    ensure_can_view_event(current_user, event)
    event["resultado_financeiro"] = await _event_result(event_id)
    return event


@router.post("/events", response_model=Event)
async def create_event(event_data: EventCreate, current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin",), "manage_events"):
        raise HTTPException(status_code=403, detail="Sem permissão para gerir eventos")
    ensure_valid_event_visibility(event_data.visibility)

    event = Event(created_by=current_user.id, **event_data.model_dump())
    event_dict = event.model_dump()

    await db.events.insert_one(event_dict)
    await create_audit_log(current_user.id, f"Criou evento {event.title}", event.id)

    if event_data.visibility in ["publico", "socios"]:
        await notify_all_active_users("event_new", "Novo Evento", f"Novo evento: {event.title}", "/eventos")
    return event


@router.patch("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, event_data: EventUpdate, current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin",), "manage_events"):
        raise HTTPException(status_code=403, detail="Sem permissão para gerir eventos")

    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    update_data = {k: v for k, v in event_data.model_dump().items() if v is not None}
    if "visibility" in update_data:
        ensure_valid_event_visibility(update_data["visibility"])

    await db.events.update_one({"id": event_id}, {"$set": update_data})
    await create_audit_log(current_user.id, f"Atualizou evento {event_id}", event_id)

    updated_event = await db.events.find_one({"id": event_id}, {"_id": 0})
    return updated_event


@router.delete("/events/{event_id}")
async def delete_event(event_id: str, current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin",), "manage_events"):
        raise HTTPException(status_code=403, detail="Sem permissão para gerir eventos")

    # Movimentos de evento são transações no caixa (spec-eventos-multas-caixa):
    # não se apaga o evento deixando registos financeiros órfãos. Bloqueia (409)
    # enquanto existirem; o gestor remove os movimentos primeiro (os de Ato
    # seguem as regras do Ato). Espelha delete_project da ronda 1.
    tx_count = await db.transactions.count_documents({"event_id": event_id})
    if tx_count > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                f"O evento tem {tx_count} movimento(s) no caixa. "
                "Remova os movimentos antes de apagar o evento."
            ),
        )

    result = await db.events.delete_one({"id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    await create_audit_log(current_user.id, f"Eliminou evento {event_id}", event_id)
    return {"message": "Evento eliminado"}


# ===== ENDPOINTS DE FINANÇAS DE EVENTO =====


async def _get_event_or_404(event_id: str) -> dict:
    event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return event


@router.post("/events/{event_id}/expenses")
async def add_event_expense(
    event_id: str,
    data: EventExpenseCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Regista uma despesa do evento COMO transação no caixa. Passa pelo gate de
    co-aprovação (Art. 54): acima do limiar exige um Ato de pagamento."""
    _require_manage_events(current_user)
    event = await _get_event_or_404(event_id)

    description = data.description.strip()
    amount = float(data.amount)
    date = data.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not description:
        raise HTTPException(status_code=400, detail="Descricao e valor sao obrigatorios")

    category = data.category or "eventos"
    if category not in EXPENSE_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Categoria invalida. Use: {EXPENSE_CATEGORIES}")

    limiar = await coaprovacao_limiar()
    if limiar > 0 and amount > limiar:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Despesa de {amount:,.0f} CVE excede o limiar de co-aprovacao "
                f"({limiar:,.0f} CVE). Crie um Acto de pagamento (evento associado) "
                f"e execute-o apos aprovacao."
            ),
        )

    transaction = Transaction(
        type="despesa",
        category=category,
        description=description,
        amount=amount,
        date=date,
        event_id=event_id,
        created_by=current_user.id,
    )
    t_dict = transaction.model_dump()
    await db.transactions.insert_one(t_dict)
    await create_audit_log(
        current_user.id,
        f"Registou despesa de evento {transaction.id} ({amount:,.0f} CVE) em '{event['title']}'",
        event_id,
        request=request,
        details={"transaction_id": transaction.id, "amount": amount, "category": category},
    )
    return t_dict


@router.post("/events/{event_id}/receitas")
async def add_event_receita(
    event_id: str,
    data: EventReceitaCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Regista uma receita do evento (inscrições/patrocínios) COMO transação no
    caixa, categoria 'extraordinarias' (sem categorias de receita novas)."""
    _require_manage_events(current_user)
    event = await _get_event_or_404(event_id)

    description = data.description.strip()
    amount = float(data.amount)
    date = data.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not description:
        raise HTTPException(status_code=400, detail="Descricao e valor sao obrigatorios")

    transaction = Transaction(
        type="receita",
        category="extraordinarias",
        description=description,
        amount=amount,
        date=date,
        event_id=event_id,
        created_by=current_user.id,
    )
    t_dict = transaction.model_dump()
    await db.transactions.insert_one(t_dict)
    await create_audit_log(
        current_user.id,
        f"Registou receita de evento {transaction.id} ({amount:,.0f} CVE) em '{event['title']}'",
        event_id,
        request=request,
        details={"transaction_id": transaction.id, "amount": amount},
    )
    return t_dict


@router.get("/events/{event_id}/expenses")
async def list_event_expenses(event_id: str, current_user: User = Depends(get_current_user)):
    event = await _get_event_or_404(event_id)
    ensure_can_view_event(current_user, event)
    items = (
        await db.transactions.find({"event_id": event_id, "type": "despesa"}, {"_id": 0})
        .sort("date", -1)
        .to_list(500)
    )
    return {"items": items}


@router.get("/events/{event_id}/receitas")
async def list_event_receitas(event_id: str, current_user: User = Depends(get_current_user)):
    event = await _get_event_or_404(event_id)
    ensure_can_view_event(current_user, event)
    items = (
        await db.transactions.find({"event_id": event_id, "type": "receita"}, {"_id": 0})
        .sort("date", -1)
        .to_list(500)
    )
    return {"items": items}


async def _delete_event_movement(event_id: str, tx_id: str, tipo: str, request: Request, current_user: User):
    _require_manage_events(current_user)
    await _get_event_or_404(event_id)
    tx = await db.transactions.find_one({"id": tx_id, "event_id": event_id, "type": tipo}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Movimento nao encontrado")
    if tx.get("ato_id"):
        raise HTTPException(
            status_code=400, detail="Movimento originado por um Acto executado; reverta pelo Acto."
        )
    await db.transactions.delete_one({"id": tx_id, "event_id": event_id})
    await create_audit_log(
        current_user.id, f"Removeu movimento de evento {tx_id} de evento {event_id}", event_id, request=request
    )
    return {"message": "Movimento removido"}


@router.delete("/events/{event_id}/expenses/{tx_id}")
async def delete_event_expense(
    event_id: str, tx_id: str, request: Request, current_user: User = Depends(get_current_user)
):
    return await _delete_event_movement(event_id, tx_id, "despesa", request, current_user)


@router.delete("/events/{event_id}/receitas/{tx_id}")
async def delete_event_receita(
    event_id: str, tx_id: str, request: Request, current_user: User = Depends(get_current_user)
):
    return await _delete_event_movement(event_id, tx_id, "receita", request, current_user)


@router.post("/events/{event_id}/register")
async def register_for_event(event_id: str, current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Apenas sócios ativos podem inscrever-se")

    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    ensure_can_view_event(current_user, event)

    if event_registration_has_ended(event):
        raise HTTPException(status_code=400, detail="Evento ja terminou")

    if current_user.id in event.get("attendees", []):
        raise HTTPException(status_code=400, detail="Já está inscrito neste evento")

    if event.get("max_attendees") and len(event.get("attendees", [])) >= event["max_attendees"]:
        raise HTTPException(status_code=400, detail="Evento já está lotado")

    registration = await register_event_attendee(event_id, current_user.id)
    if registration == "missing":
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    if registration == "already_registered":
        raise HTTPException(status_code=400, detail="Já está inscrito neste evento")
    if registration == "full":
        raise HTTPException(status_code=400, detail="Evento já está lotado")

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

    if not has_role_or_privilege(current_user, ("admin",), "manage_events") and current_user.id != event.get(
        "created_by"
    ):
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
