"""Testes do ciclo de rascunho v2 + envio segmentado (FR-004/006/009/010/011).

Cobre: create→rascunho, /enviar (0-bloqueio, snapshot, audit comunicado_enviado),
dry-run não envia, DELETE só em rascunho, imutabilidade de terminais.
"""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from starlette.requests import Request
from fastapi import BackgroundTasks

import routes.comunicados as cmod
import comunicados_service as svc
from models import ComunicadoCreate


def _req():
    return Request({"type": "http", "headers": [], "method": "POST",
                    "path": "/api/comunicados", "query_string": b"", "client": ("test", 0)})


@pytest.fixture(autouse=True)
def _no_limit(monkeypatch):
    monkeypatch.setattr(cmod.limiter, "enabled", False)


def _ok_update(mock_db, modified=1):
    mock_db.comunicados.update_one = AsyncMock(return_value=SimpleNamespace(modified_count=modified))


# ---------------------------------------------------------------------------
# create → rascunho (caminho v2)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_v2_makes_draft(mock_db, admin_user):
    payload = ComunicadoCreate(subject="Reunião Direcção", body="corpo suficientemente longo",
                               channels=["in_app"], audience_filter={"orgaos": ["direcao"]})
    res = await cmod.create_comunicado(_req(), payload, BackgroundTasks(), current_user=admin_user)
    assert res["status"] == "rascunho"
    mock_db.comunicados.insert_one.assert_awaited()
    mock_db.audit_logs.insert_one.assert_awaited()


@pytest.mark.asyncio
async def test_create_v2_dry_run_rejected_in_prod(mock_db, admin_user, monkeypatch):
    monkeypatch.setattr(cmod, "IS_PROD", True)
    payload = ComunicadoCreate(subject="Reunião Direcção", body="corpo suficientemente longo",
                               channels=["in_app"], audience_filter={"orgaos": ["direcao"]}, dry_run=True)
    with pytest.raises(Exception) as ei:
        await cmod.create_comunicado(_req(), payload, BackgroundTasks(), current_user=admin_user)
    assert getattr(ei.value, "status_code", None) == 422


# ---------------------------------------------------------------------------
# /enviar
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enviar_blocks_zero_recipients(mock_db, admin_user, monkeypatch):
    mock_db.comunicados.find_one = AsyncMock(return_value={
        "id": "c1", "status": "rascunho", "tipo": "informativo", "channels": ["in_app"],
        "audience_filter": {"orgaos": ["direcao"]}})
    monkeypatch.setattr(svc, "preview_audience",
                        AsyncMock(return_value={"recipients_count": 0, "sample": []}))
    with pytest.raises(Exception) as ei:
        await cmod.enviar_comunicado("c1", _req(), current_user=admin_user)
    assert getattr(ei.value, "status_code", None) == 422


@pytest.mark.asyncio
async def test_enviar_happy_audits_comunicado_enviado(mock_db, admin_user, monkeypatch):
    mock_db.comunicados.find_one = AsyncMock(return_value={
        "id": "c1", "status": "rascunho", "tipo": "informativo", "channels": ["in_app"],
        "audience_filter": {"orgaos": ["direcao"]}})
    _ok_update(mock_db, modified=1)
    monkeypatch.setattr(svc, "preview_audience",
                        AsyncMock(return_value={"recipients_count": 3, "sample": ["Ana", "Bruno"]}))
    monkeypatch.setattr(svc, "dispatch_comunicado",
                        AsyncMock(return_value={"status": "enviado", "recipients_count": 3, "dry_run": False}))
    res = await cmod.enviar_comunicado("c1", _req(), current_user=admin_user)
    assert res["status"] == "enviado"
    # audit gravado com a acção comunicado_enviado (SC-003)
    args = mock_db.audit_logs.insert_one.await_args.args[0]
    assert args["action"] == "comunicado_enviado"
    assert args["details"]["recipients_count"] == 3


@pytest.mark.asyncio
async def test_enviar_rejects_non_draft(mock_db, admin_user):
    mock_db.comunicados.find_one = AsyncMock(return_value={"id": "c1", "status": "enviado"})
    with pytest.raises(Exception) as ei:
        await cmod.enviar_comunicado("c1", _req(), current_user=admin_user)
    assert getattr(ei.value, "status_code", None) == 409


# ---------------------------------------------------------------------------
# DELETE (cancelar rascunho)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_draft_cancels(mock_db, admin_user):
    mock_db.comunicados.find_one = AsyncMock(return_value={
        "id": "c1", "status": "rascunho", "created_by": admin_user.id})
    _ok_update(mock_db)
    res = await cmod.cancelar_comunicado("c1", _req(), current_user=admin_user)
    assert res["status"] == "cancelado"


@pytest.mark.asyncio
async def test_delete_terminal_is_409(mock_db, admin_user):
    mock_db.comunicados.find_one = AsyncMock(return_value={
        "id": "c1", "status": "enviado", "created_by": admin_user.id})
    with pytest.raises(Exception) as ei:
        await cmod.cancelar_comunicado("c1", _req(), current_user=admin_user)
    assert getattr(ei.value, "status_code", None) == 409


# ---------------------------------------------------------------------------
# dry-run no dispatch: não envia email nem notifica (FR-009)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_dry_run_does_not_send(mock_db, monkeypatch):
    doc = {"id": "c1", "status": "a_enviar", "tipo": "informativo", "channels": ["in_app", "email"],
           "audience_filter": {"statuses": ["ativo"]}, "dry_run": True, "subject": "x", "body": "y"}
    mock_db.comunicados.find_one = AsyncMock(return_value=doc)
    _ok_update(mock_db, modified=1)
    mock_db.users.find.return_value.to_list = AsyncMock(return_value=[
        {"id": "u1", "name": "Ana", "email": "ana@x.cv", "account_type": "member",
         "status": "ativo", "member_id": "ACCTA-0001"}])
    monkeypatch.setattr(svc, "IS_PROD", False)
    notify = AsyncMock()
    send = AsyncMock(return_value={"sent": 0, "failed": 0})
    monkeypatch.setattr(svc, "notify_users", notify)
    monkeypatch.setattr(svc, "send_comunicado_batch", send)
    res = await svc.dispatch_comunicado("c1")
    assert res["dry_run"] is True
    notify.assert_not_awaited()
    send.assert_not_awaited()
    # snapshot persistido com a audiência resolvida
    persisted = mock_db.comunicados.update_one.await_args.args[1]["$set"]
    assert persisted["audience_resolved"] == ["ACCTA-0001"]
    assert persisted["dry_run"] is True


# ---------------------------------------------------------------------------
# US2-AS3 — snapshot resolvido no ENVIO (FR-010) e estático (member_ids)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_snapshot_reflects_send_time_membership(mock_db, monkeypatch):
    """A audiência é re-resolvida no envio: uma mudança de cargo entre o preview
    e o envio reflecte-se no snapshot, que fica gravado como lista estática."""
    doc = {"id": "c1", "status": "a_enviar", "tipo": "informativo", "channels": ["in_app"],
           "audience_filter": {"orgaos": ["direcao"]}, "dry_run": True, "subject": "x", "body": "y"}
    mock_db.comunicados.find_one = AsyncMock(return_value=doc)
    _ok_update(mock_db, modified=1)
    # No momento do envio a Direcção tem dois titulares (alguém transitou para lá)
    monkeypatch.setattr(svc, "members_of_orgao", AsyncMock(return_value=["u1", "u2"]))
    mock_db.users.find.return_value.to_list = AsyncMock(return_value=[
        {"id": "u1", "name": "Ana", "email": "a@x.cv", "account_type": "member",
         "status": "ativo", "member_id": "ACCTA-0001", "cargo": "dir_presidente"},
        {"id": "u2", "name": "Bea", "email": "b@x.cv", "account_type": "member",
         "status": "ativo", "member_id": "ACCTA-0002", "cargo": "dir_tesoureiro"},
    ])
    monkeypatch.setattr(svc, "IS_PROD", False)
    monkeypatch.setattr(svc, "notify_users", AsyncMock())
    monkeypatch.setattr(svc, "send_comunicado_batch", AsyncMock(return_value={"sent": 0, "failed": 0}))
    res = await svc.dispatch_comunicado("c1")
    assert res["recipients_count"] == 2
    persisted = mock_db.comunicados.update_one.await_args.args[1]["$set"]
    assert sorted(persisted["audience_resolved"]) == ["ACCTA-0001", "ACCTA-0002"]


@pytest.mark.asyncio
async def test_preview_nominal_surfaces_not_found_and_technical(mock_db):
    """Lista nominal (FR-003): pedidos inexistentes → nominal_not_found; conta
    técnica → technical_excluded (e nunca incluída)."""
    mock_db.users.find.return_value.to_list = AsyncMock(side_effect=[
        [{"id": "u1", "name": "Ana", "email": "ana@x.cv", "account_type": "member",
          "status": "ativo", "member_id": "ACCTA-0001"}],  # _filter_base
        [{"id": "sys", "member_id": "ACCTA-9000", "email": "sys@x.cv",
          "account_type": "technical"}],  # _resolve_nominal
    ])
    prev = await svc.preview_audience(
        {"nominal_member_ids": ["ACCTA-9000", "ACCTA-9999"]}, tipo="oficial", channels=["in_app"])
    codes = {w["code"] for w in prev["warnings"]}
    assert {"nominal_not_found", "technical_excluded"} <= codes
    assert prev["recipients_count"] == 0
