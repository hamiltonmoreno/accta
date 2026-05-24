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
