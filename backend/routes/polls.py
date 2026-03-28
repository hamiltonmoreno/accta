from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List
from models import User, Poll, PollCreate, UserVote, VoteCreate
from database import db
from auth import get_current_user
from helpers import create_audit_log, notify_all_active_users

router = APIRouter(tags=["polls"])


@router.get("/polls", response_model=List[Poll])
async def get_polls(skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user)):
    limit = min(limit, 100)
    polls = await db.polls.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(None)
    for p in polls:
        if isinstance(p.get('start_date'), str):
            p['start_date'] = datetime.fromisoformat(p['start_date'])
        if isinstance(p.get('end_date'), str):
            p['end_date'] = datetime.fromisoformat(p['end_date'])
        if isinstance(p.get('created_at'), str):
            p['created_at'] = datetime.fromisoformat(p['created_at'])
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
    await notify_all_active_users(
        "poll_opened", "Nova Votação Aberta",
        f"{poll.title} - Participe agora!", "/votacoes"
    )
    return poll


@router.post("/polls/vote", response_model=UserVote)
async def vote(vote_data: VoteCreate, current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Apenas sócios ativos podem votar")

    existing_vote = await db.user_votes.find_one({"user_id": current_user.id, "poll_id": vote_data.poll_id})
    if existing_vote:
        raise HTTPException(status_code=400, detail="Você já votou nesta votação")

    user_vote = UserVote(user_id=current_user.id, **vote_data.model_dump())
    vote_dict = user_vote.model_dump()
    vote_dict['created_at'] = vote_dict['created_at'].isoformat()

    await db.user_votes.insert_one(vote_dict)
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
