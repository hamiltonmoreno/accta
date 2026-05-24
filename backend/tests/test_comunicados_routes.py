import pytest
from fastapi import BackgroundTasks
from starlette.requests import Request
import routes.comunicados as cmod


def _req():
    return Request({"type": "http", "headers": [], "method": "POST",
                    "path": "/api/comunicados", "query_string": b"", "client": ("test", 0)})


@pytest.fixture(autouse=True)
def _no_limit(monkeypatch):
    monkeypatch.setattr(cmod.limiter, "enabled", False)


def _payload(**over):
    base = dict(subject="Aviso", body="corpo longo o suficiente",
                tipo="informativo", channels=["in_app"], segment={"kind": "all_active"})
    base.update(over)
    return base


@pytest.mark.asyncio
async def test_create_forbidden_for_socio(mock_db, socio_user):
    from models import ComunicadoCreate
    with pytest.raises(Exception) as ei:
        await cmod.create_comunicado(_req(), ComunicadoCreate(**_payload()),
                                     BackgroundTasks(), current_user=socio_user)
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_create_admin_schedules_and_audits(mock_db, admin_user, monkeypatch):
    from models import ComunicadoCreate
    mock_db.users.find.return_value.to_list.return_value = [
        {"id": "u1", "email": "u1@x.cv", "role": "socio", "account_type": "member",
         "member_category": "ordinario"},
    ]
    bt = BackgroundTasks()
    res = await cmod.create_comunicado(_req(), ComunicadoCreate(**_payload()),
                                       bt, current_user=admin_user)
    assert res["status"] == "a_enviar"
    assert res["recipients_total"] == 1
    mock_db.comunicados.insert_one.assert_awaited()
    mock_db.audit_logs.insert_one.assert_awaited()
    assert len(bt.tasks) == 1


@pytest.mark.asyncio
async def test_email_preferences_updates_self(mock_db, socio_user):
    from models import EmailPreferencesUpdate
    res = await cmod.update_email_preferences(
        EmailPreferencesUpdate(email_opt_out_informativos=True), current_user=socio_user)
    assert res["email_opt_out_informativos"] is True
    mock_db.users.update_one.assert_awaited()


@pytest.mark.asyncio
async def test_get_comunicado_not_found(mock_db, admin_user):
    mock_db.comunicados.find_one.return_value = None
    with pytest.raises(Exception) as ei:
        await cmod.get_comunicado("nope", current_user=admin_user)
    assert getattr(ei.value, "status_code", None) == 404


@pytest.mark.asyncio
async def test_list_requires_guard(mock_db, socio_user):
    with pytest.raises(Exception) as ei:
        await cmod.list_comunicados(current_user=socio_user)
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_recipients_count_returns_dedup_total(mock_db, admin_user):
    from models import RecipientsCountRequest
    mock_db.users.find.return_value.to_list.return_value = [
        {"id": "u1", "email": "u1@x.cv", "role": "socio", "account_type": "member", "member_category": "ordinario"},
        {"id": "u2", "email": "u2@x.cv", "role": "socio", "account_type": "member", "member_category": "ordinario"},
    ]
    res = await cmod.count_recipients(
        RecipientsCountRequest(tipo="oficial", channels=["in_app", "email"], segment={"kind": "all_active"}),
        current_user=admin_user)
    assert res["in_app"] == 2 and res["email"] == 2
    assert res["total"] == 2     # união deduplicada, não 2+2


def test_user_model_roundtrips_email_optout():
    from models import User
    u = User(**{"id": "x", "name": "N", "email": "n@x.cv", "role": "socio",
                "status": "ativo", "email_opt_out_informativos": True})
    assert u.email_opt_out_informativos is True
    assert User(**{"id": "y", "name": "N", "email": "y@x.cv", "role": "socio",
                   "status": "ativo"}).email_opt_out_informativos is False
