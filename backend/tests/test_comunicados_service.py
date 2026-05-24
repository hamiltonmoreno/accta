import pytest
from pydantic import ValidationError
from models import ComunicadoCreate, ComunicadoSegment


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
