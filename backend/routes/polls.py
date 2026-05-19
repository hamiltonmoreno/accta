from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import List, Optional
from asyncpg.exceptions import UniqueViolationError
from models import User, Poll, PollCreate, PollStatusUpdate, UserVote, VoteCreate
from database import db
from auth import get_current_user
from helpers import create_audit_log, notify_all_active_users

router = APIRouter(tags=["polls"])

# Transições de ciclo de vida permitidas: rascunho -> aberta -> encerrada.
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "rascunho": {"aberta"},
    "aberta": {"encerrada"},
    "encerrada": set(),
}


def _parse_dt(value) -> Optional[datetime]:
    """ISO string (ou datetime) -> datetime tz-aware (assume UTC se naive)."""
    if value is None:
        return None
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _hydrate_poll_dates(p: dict) -> dict:
    for field in ("start_date", "end_date", "created_at"):
        if isinstance(p.get(field), str):
            p[field] = datetime.fromisoformat(p[field])
    return p


def _poll_option_ids(poll: dict) -> set[int]:
    return {option["id"] for option in poll.get("options", []) if isinstance(option, dict) and option.get("id") is not None}


@router.get("/polls", response_model=List[Poll])
async def get_polls(skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user)):
    limit = min(limit, 100)
    polls = await db.polls.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(None)
    for p in polls:
        _hydrate_poll_dates(p)
    return polls


@router.post("/polls", response_model=Poll)
async def create_poll(poll_data: PollCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    poll = Poll(**poll_data.model_dump())
    poll_dict = poll.model_dump()
    poll_dict['start_date'] = poll_dict['start_date'].isoformat()
    poll_dict['end_date'] = poll_dict['end_date'].isoformat()
    poll_dict['created_at'] = poll_dict['created_at'].isoformat()

    await db.polls.insert_one(poll_dict)
    await create_audit_log(current_user.id, f"Criou votação {poll.id}", poll.id)
    # Nota: votação nasce em "rascunho" — o broadcast "Nova Votação Aberta"
    # acontece na transição para "aberta" (PATCH /polls/{id}/status).
    return poll


@router.patch("/polls/{poll_id}/status", response_model=Poll)
async def update_poll_status(
    poll_id: str,
    data: PollStatusUpdate,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")

    poll = await db.polls.find_one({"id": poll_id}, {"_id": 0})
    if not poll:
        raise HTTPException(status_code=404, detail="Votação não encontrada")

    current_status = poll.get("status", "rascunho")
    if data.status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise HTTPException(
            status_code=400,
            detail=f"Transição inválida: {current_status} → {data.status}",
        )

    await db.polls.update_one({"id": poll_id}, {"$set": {"status": data.status}})
    await create_audit_log(
        current_user.id,
        f"Alterou status da votação {poll_id}: {current_status} → {data.status}",
        poll_id,
    )

    if data.status == "aberta":
        await notify_all_active_users(
            "poll_opened", "Nova Votação Aberta",
            f"{poll.get('title', 'Votação')} - Participe agora!", "/votacoes",
        )

    poll["status"] = data.status
    return _hydrate_poll_dates(poll)


@router.post("/polls/vote", response_model=UserVote)
async def vote(vote_data: VoteCreate, current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Apenas sócios ativos podem votar")

    poll = await db.polls.find_one({"id": vote_data.poll_id}, {"_id": 0})
    if not poll:
        raise HTTPException(status_code=404, detail="Votação não encontrada")
    if poll.get("status") != "aberta":
        raise HTTPException(status_code=400, detail="Esta votação não está aberta")

    now = datetime.now(timezone.utc)
    start = _parse_dt(poll.get("start_date"))
    end = _parse_dt(poll.get("end_date"))
    if (start and now < start) or (end and now > end):
        raise HTTPException(status_code=400, detail="Fora do período de votação")

    option_ids = _poll_option_ids(poll)
    if not option_ids or vote_data.vote_option not in option_ids:
        raise HTTPException(status_code=400, detail="Opcao de voto invalida")

    existing_vote = await db.user_votes.find_one(
        {"user_id": current_user.id, "poll_id": vote_data.poll_id}
    )
    if existing_vote:
        raise HTTPException(status_code=400, detail="Você já votou nesta votação")

    user_vote = UserVote(user_id=current_user.id, **vote_data.model_dump())
    vote_dict = user_vote.model_dump()
    vote_dict['created_at'] = vote_dict['created_at'].isoformat()

    try:
        await db.user_votes.insert_one(vote_dict)
    except UniqueViolationError:
        # Corrida: outra requisição inseriu o voto entre o check e o insert.
        # O índice único (user_id, poll_id) garante no máximo 1 voto.
        raise HTTPException(status_code=400, detail="Você já votou nesta votação")
    return user_vote


@router.get("/polls/{poll_id}/results")
async def get_poll_results(poll_id: str, current_user: User = Depends(get_current_user)):
    poll = await db.polls.find_one({"id": poll_id}, {"_id": 0})
    if not poll:
        raise HTTPException(status_code=404, detail="Votação não encontrada")

    votes = await db.user_votes.find({"poll_id": poll_id}, {"_id": 0}).to_list(1000)
    results = {}
    for v in votes:
        option = v['vote_option']
        results[option] = results.get(option, 0) + 1

    return {"poll_id": poll_id, "total_votes": len(votes), "results": results}
