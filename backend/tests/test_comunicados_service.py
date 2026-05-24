import pytest
from pydantic import ValidationError
from models import ComunicadoCreate, ComunicadoSegment, RecipientsCountRequest


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
