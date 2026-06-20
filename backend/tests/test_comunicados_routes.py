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


# ---------------------------------------------------------------------------
# US4 — Conselho Fiscal dirige-se à Direcção (privilege `comunicar_intra_orgao`)
# ---------------------------------------------------------------------------

def _intra_user():
    """Sócio do CF com a overlay aditiva `comunicar_intra_orgao` (sem send)."""
    from models import User
    return User(id="cf1", name="Relator CF", email="cf@x.cv", role="socio",
                status="ativo", privileges=["comunicar_intra_orgao"], cargo="cf_relator")


def _full_priv_user():
    """Emissor pleno por privilégio granular `send_comunicados` (não admin)."""
    from models import User
    return User(id="s1", name="Secretaria", email="s@x.cv", role="socio",
                status="ativo", privileges=["send_comunicados"])


@pytest.mark.asyncio
async def test_intra_orgao_creates_draft_for_orgao(mock_db):
    """CF com `comunicar_intra_orgao` cria rascunho para órgão interno; audit identifica autor."""
    from models import ComunicadoCreate
    user = _intra_user()
    payload = ComunicadoCreate(subject="Parecer CF", body="corpo suficientemente longo",
                               channels=["in_app"], audience_filter={"orgaos": ["direcao"]})
    res = await cmod.create_comunicado(_req(), payload, BackgroundTasks(), current_user=user)
    assert res["status"] == "rascunho"
    assert mock_db.comunicados.insert_one.await_args.args[0]["created_by"] == "cf1"
    assert mock_db.audit_logs.insert_one.await_args.args[0]["user_id"] == "cf1"


@pytest.mark.asyncio
async def test_intra_orgao_can_send_to_orgao(mock_db, monkeypatch):
    """CF com `comunicar_intra_orgao` passa o guard e envia para órgão interno."""
    import comunicados_service as svc
    from unittest.mock import AsyncMock
    mock_db.comunicados.find_one = AsyncMock(return_value={
        "id": "c1", "status": "rascunho", "tipo": "informativo", "channels": ["in_app"],
        "audience_filter": {"orgaos": ["direcao"]}})
    mock_db.comunicados.update_one = AsyncMock(
        return_value=type("R", (), {"modified_count": 1})())
    monkeypatch.setattr(svc, "preview_audience",
                        AsyncMock(return_value={"recipients_count": 5, "sample": ["Ana"]}))
    monkeypatch.setattr(svc, "dispatch_comunicado",
                        AsyncMock(return_value={"status": "enviado", "recipients_count": 5, "dry_run": False}))
    res = await cmod.enviar_comunicado("c1", _req(), current_user=_intra_user())
    assert res["status"] == "enviado"


@pytest.mark.asyncio
async def test_intra_orgao_rejects_non_orgao_filter(mock_db):
    """Âmbito restrito: critério fora de órgãos (categorias) → 403 (US4 U2)."""
    from models import ComunicadoCreate
    payload = ComunicadoCreate(subject="x", body="corpo suficientemente longo",
                               channels=["in_app"], audience_filter={"categorias": ["ordinario"]})
    with pytest.raises(Exception) as ei:
        await cmod.create_comunicado(_req(), payload, BackgroundTasks(), current_user=_intra_user())
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_intra_orgao_rejects_orgao_plus_extra_criterion(mock_db):
    """Âmbito restrito: órgão + qualquer outro tipo preenchido → 403 (US4 U2)."""
    from models import ComunicadoCreate
    payload = ComunicadoCreate(subject="x", body="corpo suficientemente longo", channels=["in_app"],
                               audience_filter={"orgaos": ["direcao"], "statuses": ["ativo"]})
    with pytest.raises(Exception) as ei:
        await cmod.create_comunicado(_req(), payload, BackgroundTasks(), current_user=_intra_user())
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_intra_orgao_cannot_use_segment_path(mock_db):
    """Emissor restrito não pode usar o caminho `segment` legado → 403 (US4 U2)."""
    from models import ComunicadoCreate
    with pytest.raises(Exception) as ei:
        await cmod.create_comunicado(_req(), ComunicadoCreate(**_payload()),
                                     BackgroundTasks(), current_user=_intra_user())
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_no_send_privilege_is_403(mock_db, socio_user):
    """Sem `send_comunicados` nem `comunicar_intra_orgao` → 403."""
    from models import ComunicadoCreate
    payload = ComunicadoCreate(subject="x", body="corpo suficientemente longo",
                               channels=["in_app"], audience_filter={"orgaos": ["direcao"]})
    with pytest.raises(Exception) as ei:
        await cmod.create_comunicado(_req(), payload, BackgroundTasks(), current_user=socio_user)
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_full_sender_has_no_scope_restriction(mock_db):
    """Emissor pleno (`send_comunicados`) pode usar qualquer filtro (sem âmbito)."""
    from models import ComunicadoCreate
    payload = ComunicadoCreate(subject="x", body="corpo suficientemente longo",
                               channels=["in_app"], audience_filter={"categorias": ["ordinario"]})
    res = await cmod.create_comunicado(_req(), payload, BackgroundTasks(), current_user=_full_priv_user())
    assert res["status"] == "rascunho"


def test_user_model_roundtrips_email_optout():
    from models import User
    u = User(**{"id": "x", "name": "N", "email": "n@x.cv", "role": "socio",
                "status": "ativo", "email_opt_out_informativos": True})
    assert u.email_opt_out_informativos is True
    assert User(**{"id": "y", "name": "N", "email": "y@x.cv", "role": "socio",
                   "status": "ativo"}).email_opt_out_informativos is False
