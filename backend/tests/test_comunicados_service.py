import pytest
from pydantic import ValidationError
from models import ComunicadoCreate, ComunicadoSegment, RecipientsCountRequest
import comunicados_service


def _valid_payload(**over):
    base = dict(
        subject="Convocatória AG",
        body="Corpo do comunicado com texto suficiente.",
        tipo="informativo",
        channels=["in_app", "email"],
        segment={"kind": "all_active"},
    )
    base.update(over)
    return base


def test_comunicado_create_valid():
    c = ComunicadoCreate(**_valid_payload())
    assert c.channels == ["in_app", "email"]
    assert c.notification_type == "comunicado"


def test_comunicado_create_dedupes_channels():
    c = ComunicadoCreate(**_valid_payload(channels=["email", "email"]))
    assert c.channels == ["email"]


@pytest.mark.parametrize("over", [
    {"channels": []},
    {"channels": ["sms"]},
    {"tipo": "spam"},
    {"body": "curto"},
    {"subject": "   "},
    {"cta_url": "javascript:alert(1)"},
    {"segment": {"kind": "role"}},          # value em falta
    {"segment": {"kind": "manual"}},        # user_ids em falta
    {"segment": {"kind": "galaxia"}},       # kind inválido
])
def test_comunicado_create_invalid(over):
    with pytest.raises(ValidationError):
        ComunicadoCreate(**_valid_payload(**over))


# --- novos testes do code review ---


@pytest.mark.parametrize("kwargs", [
    {"tipo": "spam", "channels": ["email"], "segment": {"kind": "all_active"}},
    {"tipo": "informativo", "channels": ["sms"], "segment": {"kind": "all_active"}},
    {"tipo": "informativo", "channels": ["email"], "segment": {"kind": "galaxia"}},
])
def test_recipients_count_request_invalid(kwargs):
    with pytest.raises(ValidationError):
        RecipientsCountRequest(**kwargs)


def test_recipients_count_request_valid():
    r = RecipientsCountRequest(tipo="oficial", channels=["in_app", "email"],
                               segment={"kind": "all_active"})
    assert r.tipo == "oficial"


def test_comunicado_body_is_stripped():
    c = ComunicadoCreate(**_valid_payload(body="   corpo com espacos   "))
    assert c.body == "corpo com espacos"


def test_comunicado_segment_kind_invalid_directly():
    with pytest.raises(ValidationError):
        ComunicadoSegment(kind="galaxia")


def test_recipients_count_request_rejects_empty_channels():
    with pytest.raises(ValidationError):
        RecipientsCountRequest(tipo="informativo", channels=[], segment={"kind": "all_active"})


def test_recipients_count_request_dedupes_channels():
    r = RecipientsCountRequest(tipo="informativo", channels=["email", "email"], segment={"kind": "all_active"})
    assert r.channels == ["email"]


# ---------------------------------------------------------------------------
# resolve_recipients tests (Task 4)
# ---------------------------------------------------------------------------


def _set_users(mock_db, users):
    mock_db.users.find.return_value.to_list.return_value = users


MEMBROS = [
    {"id": "u1", "name": "A", "email": "a@x.cv", "role": "socio",
     "member_category": "ordinario", "account_type": "member"},
    {"id": "u2", "name": "B", "email": "b@x.cv", "role": "socio",
     "member_category": "fundador", "account_type": "member",
     "email_opt_out_informativos": True},
    {"id": "u3", "name": "C", "email": None, "role": "financeiro",
     "member_category": "ordinario", "account_type": "member"},
    {"id": "sys", "name": "Sys", "email": "sys@x.cv", "role": "admin",
     "account_type": "technical"},
]


@pytest.mark.asyncio
async def test_resolve_all_active_excludes_technical(mock_db):
    _set_users(mock_db, MEMBROS)
    res = await comunicados_service.resolve_recipients(
        {"kind": "all_active"}, channel="in_app", tipo="informativo")
    ids = {u["id"] for u in res}
    assert ids == {"u1", "u2", "u3"}


@pytest.mark.asyncio
async def test_resolve_email_informativo_drops_optout_and_no_email(mock_db):
    _set_users(mock_db, MEMBROS)
    res = await comunicados_service.resolve_recipients(
        {"kind": "all_active"}, channel="email", tipo="informativo")
    ids = {u["id"] for u in res}
    assert ids == {"u1"}


@pytest.mark.asyncio
async def test_resolve_email_oficial_ignores_optout(mock_db):
    _set_users(mock_db, MEMBROS)
    res = await comunicados_service.resolve_recipients(
        {"kind": "all_active"}, channel="email", tipo="oficial")
    ids = {u["id"] for u in res}
    assert ids == {"u1", "u2"}


@pytest.mark.asyncio
async def test_resolve_role_and_category(mock_db):
    _set_users(mock_db, MEMBROS)
    by_role = await comunicados_service.resolve_recipients(
        {"kind": "role", "value": "financeiro"}, channel="in_app", tipo="oficial")
    assert {u["id"] for u in by_role} == {"u3"}
    by_cat = await comunicados_service.resolve_recipients(
        {"kind": "member_category", "value": "fundador"}, channel="in_app", tipo="oficial")
    assert {u["id"] for u in by_cat} == {"u2"}


@pytest.mark.asyncio
async def test_resolve_manual(mock_db):
    _set_users(mock_db, MEMBROS)
    res = await comunicados_service.resolve_recipients(
        {"kind": "manual", "user_ids": ["u2", "naoexiste"]}, channel="in_app", tipo="oficial")
    assert {u["id"] for u in res} == {"u2"}
