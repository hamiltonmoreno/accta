"""Testes do endpoint POST /comunicados/preview-audience (FR-002, RBAC FR-008)."""

import pytest
from unittest.mock import AsyncMock

import routes.comunicados as cmod
from models import AudiencePreviewRequest


@pytest.mark.asyncio
async def test_preview_forbidden_for_socio(mock_db, socio_user):
    payload = AudiencePreviewRequest(channels=["in_app"], audience_filter={"orgaos": ["direcao"]})
    with pytest.raises(Exception) as ei:
        await cmod.preview_audience(payload, current_user=socio_user)
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_preview_returns_count_and_sample(mock_db, admin_user, monkeypatch):
    monkeypatch.setattr(
        cmod.comunicados_service, "preview_audience",
        AsyncMock(return_value={"recipients_count": 7, "sample": ["Ana", "Bruno"],
                                "more": 5, "per_type_counts": {"orgaos": 7},
                                "intersected_count": 7, "warnings": []}),
    )
    payload = AudiencePreviewRequest(channels=["in_app", "email"], audience_filter={"orgaos": ["direcao"]})
    res = await cmod.preview_audience(payload, current_user=admin_user)
    assert res["recipients_count"] == 7
    assert res["more"] == 5
    assert res["sample"] == ["Ana", "Bruno"]


# ---------------------------------------------------------------------------
# US3 — status pendente_aprovacao alarga a base e avisa (resolução real)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_preview_pendente_aprovacao_widens_base_and_warns(mock_db, admin_user):
    users = [
        {"id": "a", "name": "Ativo", "email": "a@x.cv", "account_type": "member",
         "status": "ativo", "member_category": "ordinario", "cargo": "socio"},
        {"id": "p", "name": "Pend", "email": "p@x.cv", "account_type": "member",
         "status": "pendente_aprovacao", "member_category": "ordinario", "cargo": "socio"},
    ]
    mock_db.users.find.return_value.to_list = AsyncMock(return_value=users)
    payload = AudiencePreviewRequest(
        channels=["in_app"], audience_filter={"statuses": ["pendente_aprovacao"]})
    res = await cmod.preview_audience(payload, current_user=admin_user)
    # só o pendente; o ativo fica fora (a base passou a ser pendente_aprovacao)
    assert res["recipients_count"] == 1
    assert any(w["code"] == "includes_unapproved" for w in res["warnings"])
