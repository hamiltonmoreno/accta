"""Regressão CSRF — CSRFOriginCheckMiddleware (§5.3).

Com cookie + Origin não-permitido → 403; com cookie + sem Origin/Referer →
403; com cookie + Origin permitido (ou Referer) → passa; sem cookie (Bearer)
→ passa mesmo com Origin hostil. Instancia o middleware com origens
explícitas (com CORS=* o check é no-op por design).
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth import COOKIE_NAME
from server import CSRFOriginCheckMiddleware

pytestmark = pytest.mark.unit

ALLOWED = "https://app.accta.cv"


def _client() -> TestClient:
    app = FastAPI()
    app.add_middleware(CSRFOriginCheckMiddleware, allowed_origins=[ALLOWED])

    @app.post("/x")
    async def _x():
        return {"ok": True}

    return TestClient(app)


def test_cookie_plus_bad_origin_blocked():
    c = _client()
    c.cookies.set(COOKIE_NAME, "fake-session")
    r = c.post("/x", headers={"Origin": "https://attacker.com"})
    assert r.status_code == 403
    assert "CSRF" in r.json()["detail"]


def test_cookie_without_origin_or_referer_blocked():
    c = _client()
    c.cookies.set(COOKIE_NAME, "fake-session")
    r = c.post("/x")
    assert r.status_code == 403


def test_cookie_plus_allowed_origin_passes():
    c = _client()
    c.cookies.set(COOKIE_NAME, "fake-session")
    r = c.post("/x", headers={"Origin": ALLOWED})
    assert r.status_code == 200


def test_referer_fallback_allowed_origin_passes():
    c = _client()
    c.cookies.set(COOKIE_NAME, "fake-session")
    r = c.post("/x", headers={"Referer": f"{ALLOWED}/alguma/pagina"})
    assert r.status_code == 200


def test_no_cookie_bearer_client_bypasses_csrf():
    # Sem cookie → mesmo com Origin hostil passa (atacante não lê o Bearer).
    r = _client().post(
        "/x", headers={"Origin": "https://attacker.com", "Authorization": "Bearer xyz"}
    )
    assert r.status_code == 200
