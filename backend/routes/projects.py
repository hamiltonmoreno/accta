from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import Optional
from models import (
    User,
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectTask,
    ProjectTaskCreate,
    ProjectTaskUpdate,
    ProjectComment,
    ProjectCommentCreate,
    ProjectExpense,
    ProjectExpenseCreate,
    ProjectMilestone,
    ProjectMilestoneCreate,
    ProjectMilestoneUpdate,
    PROJECT_STATUSES,
    PROJECT_VISIBILITIES,
    TASK_PRIORITIES,
    TASK_STATUSES,
)
from database import db
from auth import get_current_user
from helpers import create_audit_log, notify_users, notify_admins, get_project_stakeholder_ids, create_notification

router = APIRouter(prefix="/projects", tags=["projects"])

ADMIN_PROJECT_UPDATE_FIELDS = {
    "title",
    "description",
    "status",
    "visibility",
    "category",
    "responsible_id",
    "budget",
    "start_date",
    "end_date",
    "progress",
}
PROJECT_MANAGER_UPDATE_FIELDS = {"title", "description", "category", "start_date", "end_date", "progress"}
TASK_MANAGER_UPDATE_FIELDS = {"title", "description", "assignee_id", "status", "priority", "due_date"}
TASK_ASSIGNEE_UPDATE_FIELDS = {"status"}


def reject_disallowed_fields(updates: dict, allowed_fields: set[str]):
    disallowed = sorted(set(updates) - allowed_fields)
    if disallowed:
        raise HTTPException(status_code=403, detail=f"Sem permissao para alterar: {', '.join(disallowed)}")


def can_manage_project(user: User, project: dict) -> bool:
    return user.role == "admin" or project.get("created_by") == user.id or project.get("responsible_id") == user.id


def can_view_project(user: User, project: dict) -> bool:
    if project.get("visibility") == "publico" and project.get("status") != "proposta":
        return True
    return user.role == "admin" or project.get("created_by") == user.id or project.get("responsible_id") == user.id


def serialize_doc(d: dict) -> dict:
    for k in ["created_at", "updated_at", "completed_at"]:
        v = d.get(k)
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


# ===== PROJECT CRUD =====


@router.get("")
async def list_projects(
    status: Optional[str] = None,
    visibility: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
):
    limit = min(limit, 100)
    query = {}
    if status:
        query["status"] = status
    if visibility:
        query["visibility"] = visibility

    # Non-admin: only see published public projects + own/responsible projects.
    if current_user.role != "admin":
        query["$or"] = [
            {"visibility": "publico", "status": {"$ne": "proposta"}},
            {"created_by": current_user.id},
            {"responsible_id": current_user.id},
        ]

    total = await db.projects.count_documents(query)
    projects = await db.projects.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(None)

    # Enrich with task counts using aggregation
    project_ids = [p["id"] for p in projects]
    pipeline = [
        {"$match": {"project_id": {"$in": project_ids}}},
        {
            "$group": {
                "_id": "$project_id",
                "total": {"$sum": 1},
                "done": {"$sum": {"$cond": [{"$eq": ["$status", "concluido"]}, 1, 0]}},
            }
        },
    ]
    task_counts = {r["_id"]: r async for r in db.project_tasks.aggregate(pipeline)}
    for p in projects:
        tc = task_counts.get(p["id"], {"total": 0, "done": 0})
        p["task_count"] = tc["total"]
        p["task_done"] = tc["done"]

    return {"items": projects, "total": total}


@router.post("")
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
):
    if current_user.status != "ativo" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas socios ativos podem propor projetos")

    if data.visibility not in PROJECT_VISIBILITIES:
        raise HTTPException(status_code=400, detail=f"Visibilidade invalida: {PROJECT_VISIBILITIES}")

    project = Project(
        **data.model_dump(),
        status="proposta" if current_user.role != "admin" else "aprovado",
        created_by=current_user.id,
        created_by_name=current_user.name,
    )
    p_dict = project.model_dump()
    p_dict["created_at"] = p_dict["created_at"].isoformat()
    p_dict["updated_at"] = p_dict["updated_at"].isoformat()

    await db.projects.insert_one(p_dict)
    await create_audit_log(current_user.id, f"Criou projeto '{project.title}'", project.id)

    # Auto-notifications
    link = f"/projetos/{project.id}"
    if current_user.role != "admin":
        await notify_admins(
            "projeto",
            "Nova Proposta de Projeto",
            f"{current_user.name} submeteu o projeto '{project.title}' para aprovacao.",
            link,
            exclude_id=current_user.id,
        )

    p_dict.pop("_id", None)
    return p_dict


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")
    if not can_view_project(current_user, project):
        raise HTTPException(status_code=403, detail="Sem acesso a este projeto")

    # Enrich
    tasks = await db.project_tasks.find({"project_id": project_id}, {"_id": 0}).sort("created_at", 1).to_list(500)
    comments = (
        await db.project_comments.find({"project_id": project_id}, {"_id": 0}).sort("created_at", -1).to_list(200)
    )
    expenses = await db.project_expenses.find({"project_id": project_id}, {"_id": 0}).sort("date", -1).to_list(200)
    milestones = await db.project_milestones.find({"project_id": project_id}, {"_id": 0}).sort("date", 1).to_list(100)

    project["tasks"] = tasks
    project["comments"] = comments
    project["expenses"] = expenses
    project["milestones"] = milestones
    project["spent"] = sum(e["amount"] for e in expenses)

    return project


@router.patch("/{project_id}")
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")
    if not can_manage_project(current_user, project):
        raise HTTPException(status_code=403, detail="Sem permissao para editar este projeto")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    allowed_fields = ADMIN_PROJECT_UPDATE_FIELDS if current_user.role == "admin" else PROJECT_MANAGER_UPDATE_FIELDS
    reject_disallowed_fields(updates, allowed_fields)

    if "status" in updates and updates["status"] not in PROJECT_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status invalido: {PROJECT_STATUSES}")
    if "visibility" in updates and updates["visibility"] not in PROJECT_VISIBILITIES:
        raise HTTPException(status_code=400, detail=f"Visibilidade invalida: {PROJECT_VISIBILITIES}")
    if "progress" in updates and not 0 <= updates["progress"] <= 100:
        raise HTTPException(status_code=400, detail="Progresso deve estar entre 0 e 100")
    if "budget" in updates and updates["budget"] < 0:
        raise HTTPException(status_code=400, detail="Orcamento nao pode ser negativo")

    if "responsible_id" in updates and updates["responsible_id"]:
        resp = await db.users.find_one({"id": updates["responsible_id"]}, {"_id": 0, "name": 1})
        if resp:
            updates["responsible_name"] = resp["name"]

    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.projects.update_one({"id": project_id}, {"$set": updates})

    # Notify stakeholders on status change
    if "status" in updates:
        STATUS_LABELS = {
            "proposta": "Proposta",
            "aprovado": "Aprovado",
            "em_curso": "Em Curso",
            "concluido": "Concluido",
            "cancelado": "Cancelado",
            "pausado": "Pausado",
        }
        new_status = STATUS_LABELS.get(updates["status"], updates["status"])
        link = f"/projetos/{project_id}"
        stakeholders = get_project_stakeholder_ids(project)
        await notify_users(
            stakeholders,
            "projeto",
            f"Projeto Atualizado: {project['title']}",
            f"O status mudou para '{new_status}'. Atualizado por {current_user.name}.",
            link,
            exclude_id=current_user.id,
        )

    # Notify new responsible
    if "responsible_id" in updates and updates["responsible_id"] and updates["responsible_id"] != current_user.id:
        link = f"/projetos/{project_id}"
        await create_notification(
            updates["responsible_id"],
            "projeto",
            "Projeto Atribuido",
            f"Foi designado responsavel pelo projeto '{project['title']}'.",
            link,
        )

    updated = await db.projects.find_one({"id": project_id}, {"_id": 0})
    return updated


@router.patch("/{project_id}/approve")
async def approve_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin pode aprovar projetos")

    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")

    await db.projects.update_one(
        {"id": project_id},
        {
            "$set": {
                "status": "aprovado",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    await create_audit_log(current_user.id, f"Aprovou projeto '{project['title']}'", project_id)

    link = f"/projetos/{project_id}"
    stakeholders = get_project_stakeholder_ids(project)
    await notify_users(
        stakeholders,
        "projeto",
        "Projeto Aprovado!",
        f"O projeto '{project['title']}' foi aprovado por {current_user.name}.",
        link,
        exclude_id=current_user.id,
    )

    return {"message": "Projeto aprovado"}


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin pode remover projetos")

    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")

    await db.projects.delete_one({"id": project_id})
    await db.project_tasks.delete_many({"project_id": project_id})
    await db.project_comments.delete_many({"project_id": project_id})
    await db.project_expenses.delete_many({"project_id": project_id})
    await db.project_milestones.delete_many({"project_id": project_id})
    await create_audit_log(current_user.id, f"Removeu projeto '{project['title']}'", project_id)
    return {"message": "Projeto removido"}


# ===== TASKS =====


@router.post("/{project_id}/tasks")
async def create_task(
    project_id: str,
    data: ProjectTaskCreate,
    current_user: User = Depends(get_current_user),
):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")
    if not can_manage_project(current_user, project):
        raise HTTPException(status_code=403, detail="Sem permissao")

    assignee_name = None
    if data.assignee_id:
        assignee = await db.users.find_one({"id": data.assignee_id}, {"_id": 0, "name": 1})
        assignee_name = assignee["name"] if assignee else None

    task = ProjectTask(
        **data.model_dump(),
        project_id=project_id,
        assignee_name=assignee_name,
    )
    t_dict = task.model_dump()
    t_dict["created_at"] = t_dict["created_at"].isoformat()
    await db.project_tasks.insert_one(t_dict)

    # Notify assignee
    if data.assignee_id and data.assignee_id != current_user.id:
        link = f"/projetos/{project_id}"
        await create_notification(
            data.assignee_id,
            "projeto",
            "Nova Tarefa Atribuida",
            f"'{task.title}' no projeto '{project['title']}'. Atribuida por {current_user.name}.",
            link,
        )

    t_dict.pop("_id", None)
    return t_dict


@router.patch("/{project_id}/tasks/{task_id}")
async def update_task(
    project_id: str,
    task_id: str,
    data: ProjectTaskUpdate,
    current_user: User = Depends(get_current_user),
):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")

    task = await db.project_tasks.find_one({"id": task_id, "project_id": project_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa nao encontrada")

    # Managers can edit task metadata; assignees can only update execution status.
    is_assignee = task.get("assignee_id") == current_user.id
    is_manager = can_manage_project(current_user, project)
    if not is_manager and not is_assignee:
        raise HTTPException(status_code=403, detail="Sem permissao")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    allowed_fields = TASK_MANAGER_UPDATE_FIELDS if is_manager else TASK_ASSIGNEE_UPDATE_FIELDS
    reject_disallowed_fields(updates, allowed_fields)

    if "status" in updates and updates["status"] not in TASK_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status invalido: {TASK_STATUSES}")
    if "priority" in updates and updates["priority"] not in TASK_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Prioridade invalida: {TASK_PRIORITIES}")

    if "assignee_id" in updates and updates["assignee_id"]:
        assignee = await db.users.find_one({"id": updates["assignee_id"]}, {"_id": 0, "name": 1})
        updates["assignee_name"] = assignee["name"] if assignee else None

    if "status" in updates and updates["status"] == "concluido":
        updates["completed_at"] = datetime.now(timezone.utc).isoformat()

    if updates:
        await db.project_tasks.update_one({"id": task_id}, {"$set": updates})

    # Notify stakeholders when task is completed
    if updates.get("status") == "concluido":
        link = f"/projetos/{project_id}"
        stakeholders = get_project_stakeholder_ids(project)
        await notify_users(
            stakeholders,
            "projeto",
            "Tarefa Concluida",
            f"A tarefa '{task.get('title', '')}' no projeto '{project['title']}' foi concluida por {current_user.name}.",
            link,
            exclude_id=current_user.id,
        )

    updated = await db.project_tasks.find_one({"id": task_id}, {"_id": 0})
    return updated


@router.delete("/{project_id}/tasks/{task_id}")
async def delete_task(
    project_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")
    if not can_manage_project(current_user, project):
        raise HTTPException(status_code=403, detail="Sem permissao")

    await db.project_tasks.delete_one({"id": task_id, "project_id": project_id})
    return {"message": "Tarefa removida"}


# ===== COMMENTS =====


@router.post("/{project_id}/comments")
async def add_comment(
    project_id: str,
    data: ProjectCommentCreate,
    current_user: User = Depends(get_current_user),
):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")
    if not can_view_project(current_user, project):
        raise HTTPException(status_code=403, detail="Sem acesso")

    content = data.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Comentario vazio")

    comment = ProjectComment(
        project_id=project_id,
        user_id=current_user.id,
        user_name=current_user.name,
        content=content,
    )
    c_dict = comment.model_dump()
    c_dict["created_at"] = c_dict["created_at"].isoformat()
    await db.project_comments.insert_one(c_dict)

    # Notify project stakeholders about the new comment
    link = f"/projetos/{project_id}"
    stakeholders = get_project_stakeholder_ids(project)
    await notify_users(
        stakeholders,
        "projeto",
        "Novo Comentario no Projeto",
        f"{current_user.name} comentou em '{project['title']}': \"{content[:80]}{'...' if len(content) > 80 else ''}\"",
        link,
        exclude_id=current_user.id,
    )

    return c_dict


@router.delete("/{project_id}/comments/{comment_id}")
async def delete_comment(
    project_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user),
):
    comment = await db.project_comments.find_one({"id": comment_id, "project_id": project_id}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comentario nao encontrado")
    if comment["user_id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissao")
    await db.project_comments.delete_one({"id": comment_id})
    return {"message": "Comentario removido"}


# ===== EXPENSES =====


@router.post("/{project_id}/expenses")
async def add_expense(
    project_id: str,
    data: ProjectExpenseCreate,
    current_user: User = Depends(get_current_user),
):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")
    if not can_manage_project(current_user, project):
        raise HTTPException(status_code=403, detail="Sem permissao")

    description = data.description.strip()
    amount = data.amount  # já validado > 0 pelo modelo
    date = data.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if not description:
        raise HTTPException(status_code=400, detail="Descricao e valor sao obrigatorios")

    expense = ProjectExpense(
        project_id=project_id,
        description=description,
        amount=float(amount),
        date=date,
        created_by=current_user.id,
        created_by_name=current_user.name,
    )
    e_dict = expense.model_dump()
    e_dict["created_at"] = e_dict["created_at"].isoformat()
    await db.project_expenses.insert_one(e_dict)

    # Update project spent — usa aggregation em vez de carregar todas as despesas para memoria
    spent_pipeline = [
        {"$match": {"project_id": project_id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    spent_res = await db.project_expenses.aggregate(spent_pipeline).to_list(1)
    new_spent = spent_res[0]["total"] if spent_res else 0
    await db.projects.update_one({"id": project_id}, {"$set": {"spent": new_spent}})

    # Notify stakeholders about the new expense
    link = f"/projetos/{project_id}"
    stakeholders = get_project_stakeholder_ids(project)
    await notify_users(
        stakeholders,
        "projeto",
        "Nova Despesa no Projeto",
        f"{current_user.name} registou despesa de {amount:,.0f} CVE em '{project['title']}': {description}.",
        link,
        exclude_id=current_user.id,
    )

    # Alert if budget exceeded
    budget = project.get("budget", 0)
    if budget > 0 and new_spent > budget:
        await notify_users(
            stakeholders,
            "projeto",
            "Orcamento Excedido!",
            f"O projeto '{project['title']}' excedeu o orcamento. Gasto: {new_spent:,.0f} CVE / Orcamento: {budget:,.0f} CVE.",
            link,
        )

    return e_dict


@router.delete("/{project_id}/expenses/{expense_id}")
async def delete_expense(
    project_id: str,
    expense_id: str,
    current_user: User = Depends(get_current_user),
):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")
    if not can_manage_project(current_user, project):
        raise HTTPException(status_code=403, detail="Sem permissao")

    await db.project_expenses.delete_one({"id": expense_id, "project_id": project_id})

    spent_pipeline = [
        {"$match": {"project_id": project_id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    spent_res = await db.project_expenses.aggregate(spent_pipeline).to_list(1)
    new_spent = spent_res[0]["total"] if spent_res else 0
    await db.projects.update_one({"id": project_id}, {"$set": {"spent": new_spent}})

    return {"message": "Despesa removida"}


# ===== MILESTONES =====


@router.post("/{project_id}/milestones")
async def add_milestone(
    project_id: str,
    data: ProjectMilestoneCreate,
    current_user: User = Depends(get_current_user),
):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")
    if not can_manage_project(current_user, project):
        raise HTTPException(status_code=403, detail="Sem permissao")

    title = data.title.strip()
    date = data.date.strip()
    if not title or not date:
        raise HTTPException(status_code=400, detail="Titulo e data obrigatorios")

    milestone = ProjectMilestone(
        project_id=project_id,
        title=title,
        date=date,
    )
    m_dict = milestone.model_dump()
    m_dict["created_at"] = m_dict["created_at"].isoformat()
    await db.project_milestones.insert_one(m_dict)
    return m_dict


@router.patch("/{project_id}/milestones/{milestone_id}")
async def update_milestone(
    project_id: str,
    milestone_id: str,
    data: ProjectMilestoneUpdate,
    current_user: User = Depends(get_current_user),
):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")
    if not can_manage_project(current_user, project):
        raise HTTPException(status_code=403, detail="Sem permissao")

    updates = {}
    if data.completed is not None:
        updates["completed"] = data.completed
    if data.title is not None:
        updates["title"] = data.title
    if data.date is not None:
        updates["date"] = data.date

    if updates:
        await db.project_milestones.update_one({"id": milestone_id, "project_id": project_id}, {"$set": updates})

    updated = await db.project_milestones.find_one({"id": milestone_id}, {"_id": 0})
    return updated


@router.delete("/{project_id}/milestones/{milestone_id}")
async def delete_milestone(
    project_id: str,
    milestone_id: str,
    current_user: User = Depends(get_current_user),
):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")
    if not can_manage_project(current_user, project):
        raise HTTPException(status_code=403, detail="Sem permissao")

    await db.project_milestones.delete_one({"id": milestone_id, "project_id": project_id})
    return {"message": "Milestone removido"}


# ===== MEMBERS LIST (for assignees) =====


@router.get("/meta/members")
async def get_members_list(
    current_user: User = Depends(get_current_user),
):
    members = await db.users.find({"status": "ativo"}, {"_id": 0, "id": 1, "name": 1}).to_list(100)
    return members
