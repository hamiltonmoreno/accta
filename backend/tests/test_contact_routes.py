"""Unit tests for routes/contact.py — Spec-2 S2-C2.

Branch fix/health-audit endureceu o formulario de contacto:
- `_email_header_text` colapsa CRLF/quebras de linha -> impede header
  injection (Bcc:/CC: forjado via `name`/`subject` no Subject do email).
- `_contact_email_html` faz HTML-escape de name/email/subject/message ->
  impede HTML/“XSS” no corpo do email recebido pelo secretariado.

Sao funcoes puras — testadas directamente, sem TestClient (que abriria
ligacao ao DB no startup) nem o decorator slowapi.
"""
from __future__ import annotations

import pytest

from routes.contact import _contact_email_html, _email_header_text


pytestmark = [pytest.mark.unit]


# --------------------------------------------------------------------------- #
# _email_header_text — anti header-injection no Subject
# --------------------------------------------------------------------------- #


class TestEmailHeaderText:
    @pytest.mark.parametrize(
        "raw",
        [
            "Vitima\r\nBcc: attacker@evil.com",
            "Vitima\nCc: attacker@evil.com",
            "Linha1\r\n\r\nCorpo injectado",
            "a\rb\nc",
        ],
    )
    def test_strips_crlf(self, raw):
        out = _email_header_text(raw)
        assert "\r" not in out
        assert "\n" not in out
        # nao deve sobrar nenhum cabecalho injectado numa nova linha
        assert out == " ".join(raw.splitlines()).strip()

    def test_plain_value_unchanged(self):
        assert _email_header_text("  João Silva  ") == "João Silva"

    def test_accepts_non_str(self):
        # str() defensivo — nunca rebenta com tipo inesperado
        assert _email_header_text(123) == "123"


# --------------------------------------------------------------------------- #
# _contact_email_html — HTML escape de todos os campos do utilizador
# --------------------------------------------------------------------------- #


class TestContactEmailHtml:
    def test_escapes_html_in_all_fields(self):
        html = _contact_email_html(
            name="<script>alert('xss')</script>",
            email="evil@x.com",
            subject="<b>imprensa</b>",
            message="<img src=x onerror=alert(1)> & \"aspas\"",
        )
        # payloads crus NAO aparecem
        assert "<script>" not in html
        assert "<img src=x onerror=alert(1)>" not in html
        # versao escapada aparece
        assert "&lt;script&gt;" in html
        assert "&lt;img src=x onerror=alert(1)&gt;" in html
        assert "&amp;" in html

    def test_known_subject_label_is_used_and_safe(self):
        html = _contact_email_html("Ana", "ana@x.com", "parcerias", "mensagem normal aqui")
        assert "Parcerias" in html  # label mapeado
        assert "<script>" not in html

    def test_plain_content_survives_readable(self):
        html = _contact_email_html("Ana", "ana@x.com", "geral", "Olá, gostava de ajudar.")
        assert "Ana" in html
        assert "Olá, gostava de ajudar." in html
