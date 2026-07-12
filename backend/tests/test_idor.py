"""Regressão IDOR — B não acede a recursos de A (§6.2).

≥8 pares recurso×verbo via chamada direta às funções de rota com mock_db.
NOTA: eleições não têm endpoint de leitura de cédula/recibo — proteção
arquitetural (ballots sem user_id; recibos por HMAC voter_hash nunca
expostos), logo sem superfície IDOR a testar aí.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

import routes.atos as atos
import routes.gallery as gallery
import routes.notifications as notifications
import routes.projects as projects
import routes.sancoes as sancoes
import routes.wall as wall
from models import ProjectMilestoneUpdate

pytestmark = pytest.mark.unit


# ---- notifications: scoping por user_id ------------------------------------
@pytest.mark.asyncio
async def test_delete_notification_scoped_to_owner(mock_db, socio_user):
    mock_db.notifications.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
    with pytest.raises(HTTPException) as exc:
        await notifications.delete_notification("notif-de-A", current_user=socio_user)
    assert exc.value.status_code == 404
    assert mock_db.notifications.delete_one.call_args.args[0]["user_id"] == socio_user.id


@pytest.mark.asyncio
async def test_mark_read_scoped_to_owner(mock_db, socio_user):
    mock_db.notifications.update_one = AsyncMock(return_value=MagicMock(modified_count=0))
    await notifications.mark_notification_read("notif-de-A", current_user=socio_user)
    assert mock_db.notifications.update_one.call_args.args[0]["user_id"] == socio_user.id


@pytest.mark.asyncio
async def test_list_notifications_scoped_to_caller(mock_db, socio_user):
    await notifications.get_notifications(
        skip=0, limit=50, type_filter=None, unread_only=False, current_user=socio_user
    )
    assert mock_db.notifications.find.call_args.args[0]["user_id"] == socio_user.id


# ---- projetos --------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_comment_of_other_forbidden(mock_db, socio_user):
    mock_db.project_comments = MagicMock()
    mock_db.project_comments.find_one = AsyncMock(
        return_value={"id": "c1", "project_id": "p1", "user_id": "outro-user"}
    )
    mock_db.project_comments.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    with pytest.raises(HTTPException) as exc:
        await projects.delete_comment("p1", "c1", current_user=socio_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_expense_non_manager_forbidden(mock_db, socio_user):
    mock_db.projects.find_one = AsyncMock(
        return_value={"id": "p1", "created_by": "dono-A", "responsible_id": "dono-A"}
    )
    mock_db.project_expenses = MagicMock()
    mock_db.project_expenses.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    with pytest.raises(HTTPException) as exc:
        # delete_expense exige `request` (auditoria); o 403 dispara antes de ser usado.
        await projects.delete_expense("p1", "e1", MagicMock(), current_user=socio_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_milestone_non_manager_forbidden(mock_db, socio_user):
    mock_db.projects.find_one = AsyncMock(
        return_value={"id": "p1", "created_by": "dono-A", "responsible_id": "dono-A"}
    )
    mock_db.project_milestones = MagicMock()
    mock_db.project_milestones.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    with pytest.raises(HTTPException) as exc:
        await projects.delete_milestone("p1", "m1", current_user=socio_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_milestone_no_cross_project_disclosure(mock_db, socio_user):
    # IDOR de divulgação cruzada: gestor do projeto B faz PATCH de um milestone
    # que pertence ao projeto A. A autorização é feita pelo projeto da URL (B),
    # mas a re-leitura TEM de ser escopada por project_id — caso contrário
    # devolve o documento de A. O mock é fiel ao DAO: milestone-A só "aparece"
    # se a query NÃO estiver escopada ao projeto B (= o bug). Esperado: 404.
    manager = socio_user
    mock_db.projects.find_one = AsyncMock(
        return_value={"id": "project-B", "created_by": manager.id, "responsible_id": manager.id}
    )
    mock_db.project_milestones = MagicMock()
    mock_db.project_milestones.update_one = AsyncMock(return_value=MagicMock(modified_count=0))

    async def _find_one(filt, projection=None):
        if filt.get("project_id") in (None, "project-A"):
            return {"id": "milestone-A", "project_id": "project-A", "title": "Segredo de A"}
        return None

    mock_db.project_milestones.find_one = AsyncMock(side_effect=_find_one)

    with pytest.raises(HTTPException) as exc:
        await projects.update_milestone(
            "project-B", "milestone-A", ProjectMilestoneUpdate(title="hijack"), current_user=manager
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_milestone_cross_project_404(mock_db, socio_user):
    # Gestor do projeto B tenta apagar milestone do projeto A: delete escopado
    # por project_id não casa (deleted_count=0) → 404 (harmonizado com o PATCH).
    manager = socio_user
    mock_db.projects.find_one = AsyncMock(
        return_value={"id": "project-B", "created_by": manager.id, "responsible_id": manager.id}
    )
    mock_db.project_milestones = MagicMock()
    mock_db.project_milestones.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
    with pytest.raises(HTTPException) as exc:
        await projects.delete_milestone("project-B", "milestone-A", current_user=manager)
    assert exc.value.status_code == 404


# ---- mural -----------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_wall_post_of_other_forbidden(mock_db, socio_user):
    mock_db.wall_posts.find_one = AsyncMock(return_value={"id": "w1", "user_id": "outro-user"})
    with pytest.raises(HTTPException) as exc:
        await wall.delete_wall_post("w1", current_user=socio_user)
    assert exc.value.status_code == 403


# ---- galeria: não-admin só vê aprovadas ------------------------------------
@pytest.mark.asyncio
async def test_non_admin_cannot_query_pending_photos(mock_db, socio_user):
    await gallery.get_gallery_photos(album_id=None, status="pending", current_user=socio_user)
    assert mock_db.gallery_photos.find.call_args.args[0]["status"] == "approved"


# ---- spec 019 / T006: negativos owner adicionais (registados em test_idor_coverage) ----
@pytest.mark.asyncio
async def test_delete_gallery_photo_of_other_forbidden(mock_db, socio_user):
    # B (nem staff nem uploader) não apaga a foto de A (gallery.py: is_owner por uploaded_by).
    mock_db.gallery_photos.find_one = AsyncMock(
        return_value={"id": "ph1", "uploaded_by": "dono-A", "album_id": "al1", "url": "/uploads/gallery/x.jpg"}
    )
    with pytest.raises(HTTPException) as exc:
        await gallery.delete_gallery_photo("ph1", current_user=socio_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_wall_comment_of_other_forbidden(mock_db, socio_user):
    # B (nem moderador nem autor) não apaga o comentário de A (wall.py: user_id do comentário).
    mock_db.wall_comments.find_one = AsyncMock(return_value={"id": "c1", "post_id": "p1", "user_id": "dono-A"})
    with pytest.raises(HTTPException) as exc:
        await wall.delete_wall_comment("p1", "c1", current_user=socio_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_sancao_of_other_forbidden(mock_db, socio_user):
    # Um sócio que não é o visado nem tem poder disciplinar não vê o processo de A.
    mock_db.sancoes = MagicMock(name="sancoes")
    mock_db.sancoes.find_one = AsyncMock(
        return_value={"id": "s1", "user_id": "visado-A", "tipo": "multa", "status": "decidida"}
    )
    with pytest.raises(HTTPException) as exc:
        await sancoes.get_sancao("s1", current_user=socio_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_recurso_sancao_of_other_forbidden(mock_db, socio_user):
    # Só o visado (ou a Direcção) recorre — B não recorre da sanção de A.
    from models import SancaoRecurso

    mock_db.sancoes = MagicMock(name="sancoes")
    mock_db.sancoes.find_one = AsyncMock(
        return_value={"id": "s1", "user_id": "visado-A", "tipo": "multa", "status": "decidida"}
    )
    with pytest.raises(HTTPException) as exc:
        await sancoes.recurso_sancao(
            "s1", MagicMock(), SancaoRecurso(fundamentacao="Recurso à AG"), current_user=socio_user
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_cancel_ato_of_other_forbidden(mock_db, socio_user):
    # Só o proponente (ou admin) cancela — B não cancela o Ato proposto por A.
    mock_db.atos = MagicMock(name="atos")
    mock_db.atos.find_one = AsyncMock(return_value={"id": "at1", "created_by": "proponente-A", "status": "pendente"})
    with pytest.raises(HTTPException) as exc:
        await atos.cancel_ato("at1", MagicMock(), current_user=socio_user)
    assert exc.value.status_code == 403
