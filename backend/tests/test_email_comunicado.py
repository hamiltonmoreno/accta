import pytest
import email_service
from email_service import comunicado_email_html


def test_render_escapes_and_includes_subject():
    html = comunicado_email_html("Assunto <b>", "Linha 1\n\nLinha 2", tipo="oficial")
    assert "Assunto &lt;b&gt;" in html
    assert "Linha 1" in html and "Linha 2" in html


def test_render_cta_only_when_label_and_url():
    sem = comunicado_email_html("S", "corpo longo o suficiente")
    assert "href=" not in sem.split("Cabo Verde")[0] or "Aceder" not in sem
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
