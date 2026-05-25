"""Regressão de segurança — headers HTTP (§7 de spec-verificacao-seguranca-saas).

Prova que SecurityHeadersMiddleware injeta os headers OWASP esperados, que o
CSP é omitido em /openapi.json, e que HSTS só aparece em produção. Testa o
middleware isolado (mini-app) → sem DB/startup.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server import SecurityHeadersMiddleware

pytestmark = pytest.mark.unit


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/x")
    async def _x():
        return {"ok": True}

    return app


def test_base_security_headers_present():
    r = TestClient(_app()).get("/x")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "geolocation=(self)" in r.headers["Permissions-Policy"]
    assert "camera=()" in r.headers["Permissions-Policy"]


def test_csp_present_and_restrictive_on_api():
    csp = TestClient(_app()).get("/x").headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'self'" in csp


def test_csp_absent_on_openapi():
    # FastAPI serve /openapi.json por defeito; o middleware exclui esse caminho.
    r = TestClient(_app()).get("/openapi.json")
    assert r.status_code == 200
    assert "Content-Security-Policy" not in r.headers


def test_hsts_only_in_production(monkeypatch):
    client = TestClient(_app())
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    assert "Strict-Transport-Security" not in client.get("/x").headers
    monkeypatch.setenv("ENVIRONMENT", "production")
    hsts = client.get("/x").headers["Strict-Transport-Security"]
    assert "max-age=31536000" in hsts
    assert "includeSubDomains" in hsts
