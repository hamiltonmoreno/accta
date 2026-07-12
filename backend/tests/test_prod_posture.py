"""Postura de produção não-degradável + SECRET_KEY — spec 019, WS-E (H4, FR-007).

`_looks_like_production()` deteta um deploy HTTPS público; combinado com o boot
gate, o backend RECUSA arrancar se ENVIRONMENT!=production ou SECRET_KEY<32 —
fail-closed em vez de degradar silenciosamente cookie/HSTS/docs/CORS.
Os testes de arranque correm `import server` num subprocesso com env controlado.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from server import _looks_like_production

pytestmark = pytest.mark.unit

BACKEND = Path(__file__).resolve().parent.parent
GOOD_KEY = "x" * 40


def test_looks_like_production_true_for_https_public(monkeypatch):
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    monkeypatch.setenv("CORS_ORIGINS", "https://app.controlador.cv")
    assert _looks_like_production() is True


def test_looks_like_production_via_frontend_url(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://controlador.cv")
    monkeypatch.setenv("CORS_ORIGINS", "*")
    assert _looks_like_production() is True


@pytest.mark.parametrize(
    "cors", ["*", "", "http://localhost:3000", "https://localhost:3000", "http://127.0.0.1:8000"]
)
def test_looks_like_production_false_for_local_or_star(monkeypatch, cors):
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    monkeypatch.setenv("CORS_ORIGINS", cors)
    assert _looks_like_production() is False


def _boot(**env_overrides) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("ENVIRONMENT", None)
    env.pop("FRONTEND_URL", None)
    env.pop("CORS_ORIGINS", None)
    env["PYTHONPATH"] = str(BACKEND)
    env.setdefault("DATABASE_URL", "postgresql://p:p@localhost:5432/t")
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", "import server"], cwd=str(BACKEND), env=env, capture_output=True, text=True
    )


def test_boot_refuses_https_public_without_production_env():
    r = _boot(SECRET_KEY=GOOD_KEY, CORS_ORIGINS="https://app.controlador.cv")
    assert r.returncode != 0
    assert "produ" in r.stderr.lower(), r.stderr


def test_boot_ok_when_production_env_set():
    r = _boot(SECRET_KEY=GOOD_KEY, CORS_ORIGINS="https://app.controlador.cv", ENVIRONMENT="production")
    assert r.returncode == 0, r.stderr


def test_boot_refuses_short_secret_key():
    r = _boot(SECRET_KEY="short", CORS_ORIGINS="*")
    assert r.returncode != 0
    assert "SECRET_KEY" in r.stderr, r.stderr


def test_boot_ok_local_dev():
    r = _boot(SECRET_KEY=GOOD_KEY, CORS_ORIGINS="http://localhost:3000")
    assert r.returncode == 0, r.stderr


# --- spec 019 / W2: fecha o edge-case do heurístico do H4 -------------------
# Com FRONTEND_URL e CORS_ORIGINS ambos ausentes, `_looks_like_production()` não
# consegue detetar produção e o app arrancaria em modo degradado (cookie
# non-Secure, docs abertos, CORS=*). Exigir ENVIRONMENT explícito.
def test_boot_refuses_blank_env_without_explicit_environment():
    r = _boot(SECRET_KEY=GOOD_KEY)  # sem FRONTEND_URL, sem CORS_ORIGINS, sem ENVIRONMENT
    assert r.returncode != 0
    assert "FRONTEND_URL" in r.stderr and "CORS_ORIGINS" in r.stderr, r.stderr


def test_boot_ok_blank_env_with_explicit_development():
    r = _boot(SECRET_KEY=GOOD_KEY, ENVIRONMENT="development")
    assert r.returncode == 0, r.stderr
