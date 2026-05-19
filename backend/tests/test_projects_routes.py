"""Unit tests for routes/projects.py — Spec-2 S2-B2.

Covers the behaviour changes flagged on the fix/health-audit branch:
- Request bodies for comments/expenses/milestones are now Pydantic models
  (`data: dict` -> typed model => payload invalido = 422, nao TypeError/500).
- `update_project` / `update_task` enforce a per-role field allowlist
  (criador/responsavel nao mexe em status/budget; assignee so muda status).

Tests invoke the route functions directly with `mock_db` (no TestClient,
no real DB) — mesmo padrao de test_users_routes.py / test_polls_routes.py.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from routes import projects as projects_route


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _wire(mock_db, name: str, *, find_one=None):
    """conftest mock_db nao cria project_tasks/comments/expenses/milestones —
    monta a coleccao com metodos AsyncMock como o conftest faz para as outras."""
    coll = MagicMock(name=name)
    coll.find_one = AsyncMock(return_value=find_one)
    coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    coll.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    agg_cursor = MagicMock()
    agg_cursor.to_list = AsyncMock(return_value=[])
    coll.aggregate = MagicMock(return_value=agg_cursor)
    setattr(mock_db, name, coll)
    return coll


@pytest.fixture
def quiet_notifications(monkeypatch):
    """Isola os testes do fan-out de notificacao/audit (helpers ja testados
    noutro lado) — so queremos verificar RBAC/allowlist/validacao aqui."""
    for fn in ("notify_users", "notify_admins", "create_notification", "create_audit_log"):
        monkeypatch.setattr(projects_route, fn, AsyncMock())


def _project(owner_id: str, *, visibility="publico", **extra) -> dict:
    base = {
        "id": "proj-1",
        "title": "Projeto X",
        "created_by": owner_id,
        "responsible_id": owner_id,
        "visibility": visibility,
        "status": "aprovado",
        "budget": 10000.0,
    }
    base.update(extra)
    return base


# --------------------------------------------------------------------------- #
# Pydantic request models — payload invalido = 422 (ValidationError), nao 500
# --------------------------------------------------------------------------- #


class TestRequestModelsValidation:
    async def test_comment_requires_non_empty_content(self):
        from models import ProjectCommentCreate

        ProjectCommentCreate(content="ok")  # valido
        with pytest.raises(ValidationError):
            ProjectCommentCreate(content="")
        with pytest.raises(ValidationError):
            ProjectCommentCreate()  # campo obrigatorio em falta

    async def test_expense_requires_positive_amount(self):
        from models import ProjectExpenseCreate

        ProjectExpenseCreate(description="Catering", amount=1500)  # valido
        with pytest.raises(ValidationError):
            ProjectExpenseCreate(description="x", amount=0)  # gt=0
        with pytest.raises(ValidationError):
            ProjectExpenseCreate(description="x", amount=-5)
        with pytest.raises(ValidationError):
            ProjectExpenseCreate(description="", amount=10)  # min_length=1

    async def test_milestone_requires_title_and_date(self):
        from models import ProjectMilestoneCreate

        ProjectMilestoneCreate(title="Planeamento", date="2026-02-01")  # valido
        with pytest.raises(ValidationError):
            ProjectMilestoneCreate(title="", date="2026-02-01")
        with pytest.raises(ValidationError):
            ProjectMilestoneCreate(title="x")  # date obrigatorio


# --------------------------------------------------------------------------- #
# PATCH /projects/{id} — allowlist de campos por papel + validacao de valores
# --------------------------------------------------------------------------- #


class TestUpdateProjectAllowlist:
    async def test_404_when_project_missing(self, mock_db, admin_user):
        from models import ProjectUpdate

        mock_db.projects.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await projects_route.update_project(
                project_id="nope", data=ProjectUpdate(title="X"), current_user=admin_user
            )
        assert exc.value.status_code == 404

    async def test_non_manager_403(self, mock_db, socio_user):
        from models import ProjectUpdate

        mock_db.projects.find_one = AsyncMock(return_value=_project("someone-else"))
        with pytest.raises(HTTPException) as exc:
            await projects_route.update_project(
                project_id="proj-1", data=ProjectUpdate(title="X"), current_user=socio_user
            )
        assert exc.value.status_code == 403

    async def test_manager_cannot_change_strategic_fields(self, mock_db, socio_user):
        """Criador (nao-admin) nao altera status/budget/responsible_id."""
        from models import ProjectUpdate

        mock_db.projects.find_one = AsyncMock(return_value=_project(socio_user.id))
        for payload in (
            ProjectUpdate(status="concluido"),
            ProjectUpdate(budget=999.0),
            ProjectUpdate(responsible_id="other"),
            ProjectUpdate(visibility="privado"),
        ):
            with pytest.raises(HTTPException) as exc:
                await projects_route.update_project(
                    project_id="proj-1", data=payload, current_user=socio_user
                )
            assert exc.value.status_code == 403
        mock_db.projects.update_one.assert_not_awaited()

    async def test_manager_can_change_operational_fields(
        self, mock_db, socio_user, quiet_notifications
    ):
        from models import ProjectUpdate

        proj = _project(socio_user.id)
        mock_db.projects.find_one = AsyncMock(return_value=proj)
        await projects_route.update_project(
            project_id="proj-1",
            data=ProjectUpdate(title="Novo", description="d", progress=40),
            current_user=socio_user,
        )
        set_data = mock_db.projects.update_one.call_args[0][1]["$set"]
        assert set_data["title"] == "Novo" and set_data["progress"] == 40

    async def test_admin_can_change_strategic_fields(
        self, mock_db, admin_user, quiet_notifications
    ):
        from models import ProjectUpdate

        mock_db.projects.find_one = AsyncMock(return_value=_project("someone"))
        await projects_route.update_project(
            project_id="proj-1",
            data=ProjectUpdate(status="em_curso", budget=20000.0),
            current_user=admin_user,
        )
        set_data = mock_db.projects.update_one.call_args[0][1]["$set"]
        assert set_data["status"] == "em_curso" and set_data["budget"] == 20000.0

    @pytest.mark.parametrize(
        "payload_kwargs",
        [
            {"status": "arquivado"},      # nao em PROJECT_STATUSES
            {"visibility": "secreto"},    # nao em PROJECT_VISIBILITIES
            {"progress": 150},            # fora de 0..100
            {"budget": -1.0},             # negativo
        ],
    )
    async def test_admin_value_validation_400(self, mock_db, admin_user, payload_kwargs):
        from models import ProjectUpdate

        mock_db.projects.find_one = AsyncMock(return_value=_project("someone"))
        with pytest.raises(HTTPException) as exc:
            await projects_route.update_project(
                project_id="proj-1",
                data=ProjectUpdate(**payload_kwargs),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400
        mock_db.projects.update_one.assert_not_awaited()


# --------------------------------------------------------------------------- #
# PATCH /projects/{id}/tasks/{tid} — manager edita metadata, assignee so status
# --------------------------------------------------------------------------- #


class TestUpdateTaskAllowlist:
    async def test_assignee_can_only_update_status(self, mock_db, socio_user):
        from models import ProjectTaskUpdate

        mock_db.projects.find_one = AsyncMock(return_value=_project("admin-x"))
        _wire(mock_db, "project_tasks", find_one={"id": "t1", "assignee_id": socio_user.id})

        # title nao esta em TASK_ASSIGNEE_UPDATE_FIELDS -> 403
        with pytest.raises(HTTPException) as exc:
            await projects_route.update_task(
                project_id="proj-1",
                task_id="t1",
                data=ProjectTaskUpdate(title="Hackeado"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403
        mock_db.project_tasks.update_one.assert_not_awaited()

    async def test_assignee_status_update_passes(
        self, mock_db, socio_user, quiet_notifications
    ):
        from models import ProjectTaskUpdate

        mock_db.projects.find_one = AsyncMock(return_value=_project("admin-x"))
        _wire(mock_db, "project_tasks", find_one={"id": "t1", "assignee_id": socio_user.id})
        await projects_route.update_task(
            project_id="proj-1",
            task_id="t1",
            data=ProjectTaskUpdate(status="concluido"),
            current_user=socio_user,
        )
        set_data = mock_db.project_tasks.update_one.call_args[0][1]["$set"]
        assert set_data["status"] == "concluido"

    async def test_non_member_403(self, mock_db, moderador_user):
        from models import ProjectTaskUpdate

        mock_db.projects.find_one = AsyncMock(return_value=_project("admin-x"))
        _wire(mock_db, "project_tasks", find_one={"id": "t1", "assignee_id": "someone"})
        with pytest.raises(HTTPException) as exc:
            await projects_route.update_task(
                project_id="proj-1",
                task_id="t1",
                data=ProjectTaskUpdate(status="concluido"),
                current_user=moderador_user,
            )
        assert exc.value.status_code == 403

    async def test_manager_invalid_status_400(self, mock_db, admin_user):
        from models import ProjectTaskUpdate

        mock_db.projects.find_one = AsyncMock(return_value=_project("x"))
        _wire(mock_db, "project_tasks", find_one={"id": "t1", "assignee_id": "y"})
        with pytest.raises(HTTPException) as exc:
            await projects_route.update_task(
                project_id="proj-1",
                task_id="t1",
                data=ProjectTaskUpdate(status="inexistente"),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400


# --------------------------------------------------------------------------- #
# POST comments/expenses — Pydantic body em vez de dict cru
# --------------------------------------------------------------------------- #


class TestAddCommentExpense:
    async def test_add_comment_returns_clean_dict(
        self, mock_db, admin_user, quiet_notifications
    ):
        from models import ProjectCommentCreate

        mock_db.projects.find_one = AsyncMock(return_value=_project("admin-x"))
        _wire(mock_db, "project_comments")
        result = await projects_route.add_comment(
            project_id="proj-1",
            data=ProjectCommentCreate(content="  Bom trabalho  "),
            current_user=admin_user,
        )
        assert result["content"] == "Bom trabalho"  # .strip() aplicado
        assert "id" in result
        assert "_id" not in result

    async def test_add_comment_no_view_access_403(self, mock_db, socio_user):
        from models import ProjectCommentCreate

        mock_db.projects.find_one = AsyncMock(
            return_value=_project("outro", visibility="privado")
        )
        with pytest.raises(HTTPException) as exc:
            await projects_route.add_comment(
                project_id="proj-1",
                data=ProjectCommentCreate(content="oi"),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_add_expense_requires_manager(self, mock_db, socio_user):
        from models import ProjectExpenseCreate

        mock_db.projects.find_one = AsyncMock(return_value=_project("outro"))
        with pytest.raises(HTTPException) as exc:
            await projects_route.add_expense(
                project_id="proj-1",
                data=ProjectExpenseCreate(description="x", amount=10),
                current_user=socio_user,
            )
        assert exc.value.status_code == 403

    async def test_add_expense_manager_ok(self, mock_db, admin_user, quiet_notifications):
        from models import ProjectExpenseCreate

        mock_db.projects.find_one = AsyncMock(return_value=_project("admin-x"))
        _wire(mock_db, "project_expenses")
        result = await projects_route.add_expense(
            project_id="proj-1",
            data=ProjectExpenseCreate(description="Catering", amount=1500, date="2026-01-20"),
            current_user=admin_user,
        )
        assert result["amount"] == 1500
        assert result["description"] == "Catering"
        assert "_id" not in result
