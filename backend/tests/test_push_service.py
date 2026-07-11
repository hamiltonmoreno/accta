"""SSRF do Web Push — DNS-guard + no-redirect (spec 019, WS-F / M-SSRF-*).

`dispatch_push` só envia se o endpoint é HTTPS público E resolve para IPs todos
públicos (defesa DNS-rebinding, fail-closed no erro de resolução), e usa uma
sessão `requests` que nunca segue redireções (uma redireção contornaria a guarda).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import push_service
from push_service import _endpoint_resolves_public, _ip_is_public, is_safe_push_endpoint

pytestmark = pytest.mark.unit


def test_ip_is_public_classification():
    assert _ip_is_public("8.8.8.8") is True
    for internal in ("10.0.0.1", "127.0.0.1", "169.254.169.254", "192.168.1.1", "::1"):
        assert _ip_is_public(internal) is False, internal


def test_is_safe_push_endpoint_static_rules():
    assert is_safe_push_endpoint("https://fcm.googleapis.com/fcm/send/x") is True
    assert is_safe_push_endpoint("http://fcm.googleapis.com/x") is False  # não-HTTPS
    assert is_safe_push_endpoint("https://169.254.169.254/latest/meta-data") is False  # IP literal interno
    assert is_safe_push_endpoint("https://localhost/x") is False


@pytest.mark.asyncio
async def test_resolves_public_true_for_public_host(monkeypatch):
    monkeypatch.setattr(
        push_service.socket, "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )
    assert await _endpoint_resolves_public("https://push.example.com/x") is True


@pytest.mark.asyncio
async def test_resolves_public_false_when_dns_points_internal(monkeypatch):
    # DNS-rebinding: hostname público que resolve para IP interno → bloqueado.
    monkeypatch.setattr(
        push_service.socket, "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("169.254.169.254", 443))],
    )
    assert await _endpoint_resolves_public("https://evil.example.com/x") is False


@pytest.mark.asyncio
async def test_resolves_public_fail_closed_on_resolution_error(monkeypatch):
    def _boom(*a, **k):
        raise OSError("no such host")

    monkeypatch.setattr(push_service.socket, "getaddrinfo", _boom)
    assert await _endpoint_resolves_public("https://nxdomain.example/x") is False


def test_no_redirect_session_forces_allow_redirects_false(monkeypatch):
    # Reset do singleton para reconstruir a sessão com o post original mockado.
    monkeypatch.setattr(push_service, "_session", None)
    import requests

    captured = {}
    orig_post = requests.Session.post

    def _spy_post(self, *args, **kwargs):
        captured["allow_redirects"] = kwargs.get("allow_redirects")
        resp = MagicMock()
        resp.status_code = 204
        return resp

    monkeypatch.setattr(requests.Session, "post", _spy_post)
    sess = push_service._no_redirect_session()
    sess.post("https://push.example.com/x", data=b"y")
    monkeypatch.setattr(requests.Session, "post", orig_post)
    assert captured["allow_redirects"] is False, "a sessão de push tem de forçar allow_redirects=False"


@pytest.mark.asyncio
async def test_dispatch_push_skips_internal_dns(monkeypatch):
    monkeypatch.setattr(push_service, "push_enabled", lambda: True)
    monkeypatch.setattr(push_service, "WebPushException", Exception, raising=False)
    fake_db = MagicMock()
    fake_db.push_subscriptions.find.return_value.to_list = AsyncMock(
        return_value=[{"endpoint": "https://evil.example.com/x", "p256dh": "a", "auth": "b"}]
    )
    monkeypatch.setattr(push_service, "db", fake_db)
    monkeypatch.setattr(
        push_service.socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("10.0.0.5", 443))]
    )
    sent = []
    monkeypatch.setattr(push_service, "_send_one", lambda *a, **k: sent.append(a))
    # Import lazy de WebPushException dentro de dispatch_push — garante presença.
    import sys
    sys.modules.setdefault("pywebpush", MagicMock(WebPushException=Exception))
    await push_service.dispatch_push(["u1"], "t", "b", "/x")
    assert sent == [], "não devia enviar para endpoint que resolve p/ IP interno"
