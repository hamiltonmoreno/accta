"""Unit tests for turnstile.py + wiring nas rotas sensíveis.

A verificação Cloudflare Turnstile é anti-bot para login/registo/recuperação de
password/contacto. Pontos-chave testados:

- **Degradação graciosa**: sem `TURNSTILE_SECRET` a verificação é no-op (não
  bloqueia, não chama a rede) — garante que o deploy não parte o login antes de
  a secret ser configurada.
- **Quando ligada**: 403 com token ausente/rejeitado, 502 se a Cloudflare
  falhar, e o IP real (`cf-connecting-ip`) é reenviado no `remoteip`.
- **Wiring**: cada rota chama `verify_turnstile` ANTES de qualquer trabalho
  (DB / email), pelo que um token inválido corta o pedido na 1.ª linha.

Funções/rotas testadas directamente, sem TestClient (que abriria ligação ao DB
no startup) — os decoradores slowapi são desligados nos testes de rota.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request

import turnstile


# asyncio_mode=auto (pyproject) corre os testes async sem mark explícita; os dois
# testes sync de `turnstile_enabled` ficam sem warning.
pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------- #
# Fakes — substituem httpx.AsyncClient para não tocar na rede
# --------------------------------------------------------------------------- #


class _FakeResp:
    def __init__(self, data=None, json_exc=None):
        self._data = data
        self._json_exc = json_exc

    def json(self):
        if self._json_exc:
            raise self._json_exc
        return self._data


class _FakeClient:
    def __init__(self, *, resp=None, exc=None, captured=None):
        self._resp = resp
        self._exc = exc
        self._captured = captured

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_a):
        return False

    async def post(self, url, data=None):
        if self._captured is not None:
            self._captured["url"] = url
            self._captured["data"] = data
        if self._exc:
            raise self._exc
        return self._resp


def _client_factory(**kw):
    def factory(*_a, **_kw):
        return _FakeClient(**kw)

    return factory


def _request(headers=None, client=("1.2.3.4", 5678)):
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/auth/login",
        "headers": raw,
        "query_string": b"",
    }
    if client:
        scope["client"] = client
    return Request(scope)


@pytest.fixture
def no_network(monkeypatch):
    """Garante que nenhum teste 'disabled' toca acidentalmente na rede."""

    def _boom(*_a, **_kw):
        raise AssertionError("httpx.AsyncClient não deveria ser instanciado")

    monkeypatch.setattr(turnstile.httpx, "AsyncClient", _boom)


@pytest.fixture(autouse=True)
def _no_frontend_url(monkeypatch):
    """Por omissão a validação de hostname fica desligada (sem FRONTEND_URL), para
    isolar os testes que não a exercem. Os testes de hostname re-definem-no."""
    monkeypatch.delenv("FRONTEND_URL", raising=False)


# --------------------------------------------------------------------------- #
# turnstile_enabled / degradação graciosa
# --------------------------------------------------------------------------- #


class TestEnabledFlag:
    def test_disabled_without_secret(self, monkeypatch):
        monkeypatch.delenv("TURNSTILE_SECRET", raising=False)
        assert turnstile.turnstile_enabled() is False

    def test_enabled_with_secret(self, monkeypatch):
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        assert turnstile.turnstile_enabled() is True


class TestDisabledIsNoop:
    async def test_noop_even_with_empty_token(self, monkeypatch, no_network):
        monkeypatch.delenv("TURNSTILE_SECRET", raising=False)
        # Não levanta e não chama a rede (no_network rebenta se chamar).
        await turnstile.verify_turnstile("", _request())

    async def test_noop_with_any_token(self, monkeypatch, no_network):
        monkeypatch.delenv("TURNSTILE_SECRET", raising=False)
        await turnstile.verify_turnstile("qualquer-coisa", _request())


# --------------------------------------------------------------------------- #
# Verificação ligada (secret configurada)
# --------------------------------------------------------------------------- #


class TestEnabledVerification:
    async def test_empty_token_403_before_network(self, monkeypatch, no_network):
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        # no_network garante que falha em 403 ANTES de chamar a Cloudflare.
        with pytest.raises(HTTPException) as exc:
            await turnstile.verify_turnstile("", _request())
        assert exc.value.status_code == 403

    async def test_success_passes(self, monkeypatch):
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        monkeypatch.setattr(turnstile.httpx, "AsyncClient", _client_factory(resp=_FakeResp({"success": True})))
        await turnstile.verify_turnstile("tok", _request())  # não levanta

    async def test_rejected_token_403(self, monkeypatch):
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        monkeypatch.setattr(
            turnstile.httpx,
            "AsyncClient",
            _client_factory(resp=_FakeResp({"success": False, "error-codes": ["invalid-input-response"]})),
        )
        with pytest.raises(HTTPException) as exc:
            await turnstile.verify_turnstile("tok", _request())
        assert exc.value.status_code == 403

    async def test_network_error_502(self, monkeypatch):
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        monkeypatch.setattr(
            turnstile.httpx,
            "AsyncClient",
            _client_factory(exc=httpx.ConnectError("boom")),
        )
        with pytest.raises(HTTPException) as exc:
            await turnstile.verify_turnstile("tok", _request())
        assert exc.value.status_code == 502

    async def test_bad_json_502(self, monkeypatch):
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        monkeypatch.setattr(
            turnstile.httpx,
            "AsyncClient",
            _client_factory(resp=_FakeResp(json_exc=ValueError("not json"))),
        )
        with pytest.raises(HTTPException) as exc:
            await turnstile.verify_turnstile("tok", _request())
        assert exc.value.status_code == 502

    async def test_uses_cf_connecting_ip_behind_trusted_proxy(self, monkeypatch):
        # Atrás de um proxy reverso de confiança (peer em loopback/RFC-1918) o
        # cf-connecting-ip é honrado como IP real do visitante.
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        captured = {}
        monkeypatch.setattr(
            turnstile.httpx,
            "AsyncClient",
            _client_factory(resp=_FakeResp({"success": True}), captured=captured),
        )
        await turnstile.verify_turnstile(
            "tok", _request(headers={"cf-connecting-ip": "9.9.9.9"}, client=("127.0.0.1", 1))
        )
        assert captured["data"]["secret"] == "0xSECRET"
        assert captured["data"]["response"] == "tok"
        assert captured["data"]["remoteip"] == "9.9.9.9"  # header honrado atrás do proxy

    async def test_untrusted_peer_ignores_spoofed_cf_header(self, monkeypatch):
        # Exposto directamente (peer = IP público, não-proxy), o cf-connecting-ip
        # é spoofável → ignora-se e usa-se o IP real da ligação (anti-spoof,
        # alinhado com helpers._is_trusted_proxy).
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        captured = {}
        monkeypatch.setattr(
            turnstile.httpx,
            "AsyncClient",
            _client_factory(resp=_FakeResp({"success": True}), captured=captured),
        )
        await turnstile.verify_turnstile(
            "tok", _request(headers={"cf-connecting-ip": "9.9.9.9"}, client=("5.6.7.8", 1))
        )
        assert captured["data"]["remoteip"] == "5.6.7.8"  # header forjado descartado

    async def test_falls_back_to_client_host(self, monkeypatch):
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        captured = {}
        monkeypatch.setattr(
            turnstile.httpx,
            "AsyncClient",
            _client_factory(resp=_FakeResp({"success": True}), captured=captured),
        )
        await turnstile.verify_turnstile("tok", _request(client=("5.6.7.8", 1)))
        assert captured["data"]["remoteip"] == "5.6.7.8"

    async def test_non_dict_json_403(self, monkeypatch):
        # JSON válido mas não-objeto (ex.: null numa falha de infra da CF) → 403,
        # nunca 500 por chamar `.get` num não-dict.
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        monkeypatch.setattr(turnstile.httpx, "AsyncClient", _client_factory(resp=_FakeResp(None)))
        with pytest.raises(HTTPException) as exc:
            await turnstile.verify_turnstile("tok", _request())
        assert exc.value.status_code == 403


# --------------------------------------------------------------------------- #
# Validação de hostname (defesa-em-profundidade — site key é pública)
# --------------------------------------------------------------------------- #


class TestHostnameValidation:
    async def test_hostname_match_passes(self, monkeypatch):
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        monkeypatch.setenv("FRONTEND_URL", "https://controlador.cv")
        monkeypatch.setattr(
            turnstile.httpx,
            "AsyncClient",
            _client_factory(resp=_FakeResp({"success": True, "hostname": "controlador.cv"})),
        )
        await turnstile.verify_turnstile("tok", _request())  # não levanta

    async def test_hostname_www_normalized_passes(self, monkeypatch):
        # www.<host> normaliza para <host> dos dois lados → coincide.
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        monkeypatch.setenv("FRONTEND_URL", "https://controlador.cv")
        monkeypatch.setattr(
            turnstile.httpx,
            "AsyncClient",
            _client_factory(resp=_FakeResp({"success": True, "hostname": "www.controlador.cv"})),
        )
        await turnstile.verify_turnstile("tok", _request())  # não levanta

    async def test_hostname_mismatch_403(self, monkeypatch):
        # Token resolvido noutro domínio com a mesma site key pública → rejeitado.
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        monkeypatch.setenv("FRONTEND_URL", "https://controlador.cv")
        monkeypatch.setattr(
            turnstile.httpx,
            "AsyncClient",
            _client_factory(resp=_FakeResp({"success": True, "hostname": "attacker.example"})),
        )
        with pytest.raises(HTTPException) as exc:
            await turnstile.verify_turnstile("tok", _request())
        assert exc.value.status_code == 403

    async def test_no_frontend_url_skips_hostname(self, monkeypatch):
        # Sem FRONTEND_URL (autouse limpa-o) não há por onde comparar → o token
        # com success passa, mesmo com hostname não coincidente.
        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        monkeypatch.setattr(
            turnstile.httpx,
            "AsyncClient",
            _client_factory(resp=_FakeResp({"success": True, "hostname": "qualquer.dominio"})),
        )
        await turnstile.verify_turnstile("tok", _request())  # não levanta


# --------------------------------------------------------------------------- #
# Wiring nas rotas — verify_turnstile corre ANTES de DB/email
# --------------------------------------------------------------------------- #


class TestRouteWiring:
    """Com a secret configurada e token vazio, cada rota deve devolver 403 sem
    chegar a tocar no DB / enviar email (verify_turnstile é a 1.ª linha)."""

    async def test_login_blocks_before_db(self, mock_db, monkeypatch):
        from routes import auth_routes
        from models import UserLogin

        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        monkeypatch.setattr(auth_routes.limiter, "enabled", False)
        mock_db.users.find_one = AsyncMock()

        with pytest.raises(HTTPException) as exc:
            await auth_routes.login(
                _request(), Response(), UserLogin(email="x@y.cv", password="segredo123", turnstile_token="")
            )
        assert exc.value.status_code == 403
        mock_db.users.find_one.assert_not_awaited()

    async def test_register_blocks_before_db(self, mock_db, monkeypatch):
        from routes import auth_routes
        from models import RegistrationRequest

        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        monkeypatch.setattr(auth_routes.limiter, "enabled", False)
        mock_db.users.find_one = AsyncMock()

        with pytest.raises(HTTPException) as exc:
            await auth_routes.register(
                _request(),
                RegistrationRequest(name="Ana Bot", email="a@b.cv", consent_data=True, turnstile_token=""),
            )
        assert exc.value.status_code == 403
        mock_db.users.find_one.assert_not_awaited()

    async def test_forgot_password_blocks_before_db(self, mock_db, monkeypatch):
        from routes import auth_routes
        from models import PasswordResetRequest

        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        monkeypatch.setattr(auth_routes.limiter, "enabled", False)
        mock_db.users.find_one = AsyncMock()

        with pytest.raises(HTTPException) as exc:
            await auth_routes.forgot_password(_request(), PasswordResetRequest(email="x@y.cv", turnstile_token=""))
        assert exc.value.status_code == 403
        mock_db.users.find_one.assert_not_awaited()

    async def test_contact_blocks_before_email(self, monkeypatch):
        from routes import contact
        from routes.contact import ContactRequest

        monkeypatch.setenv("TURNSTILE_SECRET", "0xSECRET")
        monkeypatch.setattr(contact.limiter, "enabled", False)
        send = AsyncMock()
        monkeypatch.setattr(contact, "send_email", send)

        with pytest.raises(HTTPException) as exc:
            await contact.submit_contact(
                _request(),
                ContactRequest(
                    name="Ana", email="a@b.cv", message="mensagem suficientemente longa", turnstile_token=""
                ),
            )
        assert exc.value.status_code == 403
        send.assert_not_awaited()

    async def test_disabled_lets_request_through(self, monkeypatch):
        """Sem secret, contacto com token vazio deve seguir e enviar email
        (regressão: a degradação graciosa não pode partir os formulários)."""
        from routes import contact
        from routes.contact import ContactRequest

        monkeypatch.delenv("TURNSTILE_SECRET", raising=False)
        monkeypatch.setattr(contact.limiter, "enabled", False)
        send = AsyncMock(return_value={"status": "sent"})
        monkeypatch.setattr(contact, "send_email", send)

        result = await contact.submit_contact(
            _request(),
            ContactRequest(name="Ana", email="a@b.cv", message="mensagem suficientemente longa", turnstile_token=""),
        )
        assert result["message"] == "Mensagem enviada com sucesso"
        send.assert_awaited_once()
