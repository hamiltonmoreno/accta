"""
RBAC matrix tests — verify each protected endpoint denies callers with
the wrong role with a 403 (or 401 when unauthenticated).

Strategy:
- Mount the FastAPI app once (with mocked DB)
- Override `get_current_user` per test to inject a chosen role
- Send a minimal valid body so the role check is reached (otherwise FastAPI
  short-circuits with 422 before the handler runs)
- Assert the response status is 401/403 for unauthorized roles

We focus on DENY semantics — the highest-severity bug class.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------- #
# App + test client fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture
def app(mock_db):
    """
    Build the FastAPI app with a mocked DB. The mock_db fixture from conftest
    patches database.db, auth.db, helpers.db before this fixture runs.
    """
    from server import app as fastapi_app
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    # raise_server_exceptions=False so unhandled errors return 500 instead of
    # propagating into the test — we only care about the auth-gate response code.
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def as_role(app):
    """Return a callable that overrides get_current_user to return the given user."""
    from auth import get_current_user

    def _set(user):
        app.dependency_overrides[get_current_user] = lambda: user

    return _set


# --------------------------------------------------------------------------- #
# Endpoint catalogue
#
# Each entry: (method, path, allowed_roles, body)
# - allowed_roles: roles that should pass the auth gate (not 403)
# - body: minimal valid JSON to bypass Pydantic validation and reach the gate
# --------------------------------------------------------------------------- #

ENDPOINTS = [
    # Admin-only
    ("POST", "/api/admin/invite", ["admin"], {"name": "X", "email": "x@example.com"}),
    ("GET", "/api/admin/invites/pending", ["admin"], None),
    ("POST", "/api/benefits", ["admin"], {"name": "X", "description": "Y", "discount_percent": 10.0}),
    ("PATCH", "/api/benefits/test-id", ["admin"], {"name": "Updated"}),
    ("DELETE", "/api/benefits/test-id", ["admin"], None),
    ("POST", "/api/polls", ["admin"], {
        "title": "T", "description": "D",
        "options": [{"text": "A"}, {"text": "B"}],
        "start_date": "2026-01-01T00:00:00+00:00",
        "end_date": "2026-12-31T00:00:00+00:00",
    }),
    # Finance
    ("GET", "/api/finances/transactions", ["admin", "financeiro"], None),
    ("GET", "/api/stats", ["admin", "financeiro"], None),
    ("POST", "/api/invoices", ["admin", "financeiro"], {
        "user_id": "u1", "type": "quota_mensal", "amount": 100.0,
        "due_date": "2026-01-01T00:00:00+00:00",
    }),
    # Moderation
    ("GET", "/api/wall/pending", ["admin", "moderador"], None),
    # Authenticated, any role (status=ativo via fixtures)
    ("POST", "/api/documents/test-id/access", ["admin", "socio", "financeiro", "moderador"], None),
    ("POST", "/api/benefits/test-id/validate", ["admin", "socio", "financeiro", "moderador"], None),
]

# Public endpoints (no auth) — must respond without forcing 401/403.
PUBLIC_ENDPOINTS = [
    ("GET", "/api/documents/public", None),
    ("GET", "/api/benefits/public", None),
]

ALL_ROLES = ["admin", "socio", "financeiro", "moderador"]


@pytest.fixture
def role_users(admin_user, socio_user, financeiro_user, moderador_user):
    return {
        "admin": admin_user,
        "socio": socio_user,
        "financeiro": financeiro_user,
        "moderador": moderador_user,
    }


# --------------------------------------------------------------------------- #
# 1) Anonymous access — every protected endpoint must require auth
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("method,path,_allowed,body", ENDPOINTS)
def test_anonymous_request_is_rejected(client, method, path, _allowed, body):
    kwargs = {"json": body} if body is not None else {}
    response = client.request(method, path, **kwargs)
    # 401 from missing bearer token, 403 from FastAPI's HTTPBearer when auto_error=True.
    assert response.status_code in (401, 403), (
        f"{method} {path} returned {response.status_code} for anonymous caller — "
        f"expected 401/403"
    )


# --------------------------------------------------------------------------- #
# 2) Wrong-role denial matrix — must return 403
# --------------------------------------------------------------------------- #

def _build_deny_matrix():
    cases = []
    for method, path, allowed, body in ENDPOINTS:
        for role in ALL_ROLES:
            if role not in allowed:
                cases.append((method, path, role, allowed, body))
    return cases


@pytest.mark.parametrize("method,path,role,allowed,body", _build_deny_matrix())
def test_wrong_role_is_denied(client, as_role, role_users, method, path, role, allowed, body):
    """A user with a role not in `allowed` must receive 403."""
    as_role(role_users[role])
    kwargs = {"json": body} if body is not None else {}
    response = client.request(method, path, **kwargs)
    assert response.status_code == 403, (
        f"{method} {path} with role={role} returned {response.status_code}, "
        f"expected 403 (allowed={allowed})\nBody: {response.text[:200]}"
    )


# --------------------------------------------------------------------------- #
# 3) Allowed roles must NOT be blocked by the auth gate
# --------------------------------------------------------------------------- #

def _build_allow_matrix():
    cases = []
    for method, path, allowed, body in ENDPOINTS:
        for role in allowed:
            cases.append((method, path, role, body))
    return cases


@pytest.mark.parametrize("method,path,role,body", _build_allow_matrix())
def test_allowed_role_passes_auth_gate(client, as_role, role_users, method, path, role, body):
    """
    Allowed roles must not receive 403 from the role gate. They MAY receive
    200/4xx/5xx because the request body or DB state is incomplete in unit
    tests — we only assert the auth gate did not reject them.
    """
    as_role(role_users[role])
    kwargs = {"json": body} if body is not None else {}
    response = client.request(method, path, **kwargs)
    assert response.status_code != 403, (
        f"{method} {path} with role={role} unexpectedly returned 403 "
        f"(should be allowed past the auth gate)\nBody: {response.text[:200]}"
    )


# --------------------------------------------------------------------------- #
# 4) Public endpoints — must respond without authentication
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("method,path,body", PUBLIC_ENDPOINTS)
def test_public_endpoint_anonymous_access(client, method, path, body):
    """
    Anonymous callers (no token) must be able to reach public endpoints.
    Acceptable: 2xx (success), 4xx (validation/not-found) — NOT 401/403.
    """
    kwargs = {"json": body} if body is not None else {}
    response = client.request(method, path, **kwargs)
    assert response.status_code not in (401, 403), (
        f"{method} {path} returned {response.status_code} for anonymous caller "
        f"— public endpoint must not require auth"
    )
