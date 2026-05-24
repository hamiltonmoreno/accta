import io
import pytest
import routes.upload as upmod


@pytest.mark.asyncio
async def test_save_validated_upload_rejects_oversize(monkeypatch):
    # documents: 10MB. Passar 11MB tem de levantar 413.
    big = b"x" * (11 * 1024 * 1024)
    with pytest.raises(Exception) as ei:
        await upmod.save_validated_upload("documents", big, "x.pdf")
    assert getattr(ei.value, "status_code", None) == 413


@pytest.mark.asyncio
async def test_save_validated_upload_writes_and_returns_url(monkeypatch, tmp_path):
    # Evita validação de magic-bytes e I/O real: monkeypatch dos helpers internos.
    monkeypatch.setattr(upmod, "validate_file_content", lambda *a, **k: None)
    async def _fake_to_thread(fn, *a, **k):
        return None
    monkeypatch.setattr(upmod.asyncio, "to_thread", _fake_to_thread)
    url = await upmod.save_validated_upload("documents", b"%PDF-1.4 ...", "relatorio.pdf")
    assert url.startswith("/uploads/documents/") and url.endswith(".pdf")
