"""Backstop de projeção de segredos — spec 019, WS-B / H5 (+ FR-005, G5/FR-002).

Trip-wire estrutural: mesmo que o DAO devolva o documento inteiro, a SERIALIZAÇÃO
(response_model=User/Token) descarta password/MFA/invite_token; e o
`_user_projection` continua a ser o gate de PII sensível de terceiros (FR-005).
Reverter qualquer uma destas garantias deixa este ficheiro VERMELHO (SC-008).
"""
from __future__ import annotations

import pytest

from models import MFA_SECRET_FIELDS, Token, User
from routes.users import SENSITIVE_PROFILE_FIELDS, _user_projection
from server import app

pytestmark = pytest.mark.unit

SECRETS = ["password", "invite_token", *MFA_SECRET_FIELDS]


def _user_doc(**extra):
    doc = {
        "id": "u1",
        "name": "Sócio A",
        "email": "a@x.cv",
        "role": "socio",
        "status": "ativo",
        "cargo": "Sócio",
        "privileges": [],
        "consent_data": True,
        "created_at": "2026-01-01T00:00:00+00:00",
        # segredos injetados de propósito — NÃO devem sobreviver à serialização
        "password": "$2b$12$hashhashhashhashhashha",
        "invite_token": "raw-invite-token",
    }
    for f in MFA_SECRET_FIELDS:
        doc[f] = "segredo"
    doc.update(extra)
    return doc


def test_user_model_dump_drops_secrets():
    dumped = User(**_user_doc()).model_dump()
    for k in SECRETS:
        assert k not in dumped, f"User expôs {k!r} no dump"


def test_token_serialization_drops_secrets():
    tok = Token(access_token="jwt", token_type="bearer", user=User(**_user_doc()))
    dumped = tok.model_dump()
    flat = {**dumped, **(dumped.get("user") or {})}
    for k in SECRETS:
        assert k not in flat, f"Token expôs {k!r} (topo ou dentro de user)"


def _route(method: str, path: str):
    for r in app.routes:
        if getattr(r, "path", None) == path and method in (getattr(r, "methods", None) or set()):
            return r
    raise AssertionError(f"rota {method} {path} não encontrada no app")


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/users"),
        ("GET", "/api/users/{user_id}"),
        ("PATCH", "/api/users/me/profile"),
        ("GET", "/api/auth/me"),
        ("POST", "/api/auth/login"),
    ],
)
def test_user_returning_routes_declare_response_model(method, path):
    r = _route(method, path)
    assert getattr(r, "response_model", None) is not None, f"{method} {path} sem response_model (backstop H5)"


def test_user_projection_excludes_secrets_both_modes():
    for include in (True, False):
        proj = _user_projection(include)
        assert proj["password"] == 0
        for f in MFA_SECRET_FIELDS:
            assert proj[f] == 0, f"MFA {f} não excluído em _user_projection({include})"
    # PII sensível: o próprio (True) vê; terceiros (False) não
    self_proj = _user_projection(True)
    other_proj = _user_projection(False)
    for f in SENSITIVE_PROFILE_FIELDS:
        assert f not in self_proj, f"self não devia excluir {f}"
        assert other_proj[f] == 0, f"terceiros deviam excluir {f}"
