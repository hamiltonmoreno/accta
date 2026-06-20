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
