import pytest
import email_service
from email_service import comunicado_email_html


def test_render_escapes_and_includes_subject():
    html = comunicado_email_html("Assunto <b>", "Linha 1\n\nLinha 2", tipo="oficial")
    assert "Assunto &lt;b&gt;" in html
    assert "Linha 1" in html and "Linha 2" in html
    html2 = comunicado_email_html("S", "Corpo <script>alert(1)</script> texto", tipo="oficial")
    assert "&lt;script&gt;" in html2
    assert "<script>" not in html2


def test_render_cta_only_when_label_and_url():
    sem = comunicado_email_html("S", "corpo longo o suficiente")
    assert "href=" not in sem
    com = comunicado_email_html("S", "corpo longo", cta_label="Ver", cta_url="https://x.cv/a")
    assert 'href="https://x.cv/a"' in com and ">Ver<" in com


def test_render_optout_note_only_informativo():
    inf = comunicado_email_html("S", "corpo longo", tipo="informativo")
    ofi = comunicado_email_html("S", "corpo longo", tipo="oficial")
    assert "desactivar" in inf.lower()
    assert "desactivar" not in ofi.lower()


@pytest.mark.asyncio
async def test_batch_without_api_key_counts_all_failed(monkeypatch):
    monkeypatch.setattr(email_service, "RESEND_API_KEY", None)
    res = await email_service.send_comunicado_batch(["a@x.cv", "b@x.cv"], "S", "<p>x</p>")
    assert res["sent"] == 0 and res["failed"] == 2


def test_render_blocks_non_http_cta():
    html = comunicado_email_html("S", "corpo longo o suficiente", cta_label="X", cta_url="javascript:alert(1)")
    assert "javascript:" not in html
    assert "href=" not in html   # CTA bloqueado quando o esquema não é http(s)


@pytest.mark.asyncio
async def test_batch_chunks_and_sends_all(monkeypatch):
    monkeypatch.setattr(email_service, "RESEND_API_KEY", "test-key")
    monkeypatch.setattr(email_service, "_BATCH_CHUNK_SIZE", 2)
    calls = []

    class _FakeBatch:
        @staticmethod
        def send(params):
            calls.append(len(params))

    monkeypatch.setattr(email_service, "resend", type("R", (), {"Batch": _FakeBatch}))
    res = await email_service.send_comunicado_batch(
        ["a@x.cv", "b@x.cv", "c@x.cv", "d@x.cv", "e@x.cv"], "S", "<p>x</p>")
    assert res["sent"] == 5 and res["failed"] == 0
    assert calls == [2, 2, 1]   # 3 chunks (2,2,1), um `to` por destinatário
