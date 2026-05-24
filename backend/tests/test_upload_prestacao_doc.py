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


import io as _io
from starlette.datastructures import UploadFile, Headers
import routes.prestacao_contas as pmod


def _upload(filename="relatorio.pdf", data=b"%PDF-1.4 conteudo"):
    return UploadFile(filename=filename, file=_io.BytesIO(data),
                      headers=Headers({"content-type": "application/pdf"}))


@pytest.fixture(autouse=True)
def _no_real_io(monkeypatch):
    # O endpoint não deve tocar no disco nos unit tests.
    async def _fake_save(category, contents, filename):
        return f"/uploads/{category}/fake-{filename}"
    monkeypatch.setattr(pmod, "save_validated_upload", _fake_save)


@pytest.mark.asyncio
async def test_upload_doc_forbidden_for_socio(mock_db, socio_user):
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="relatorio",
                                              title=None, current_user=socio_user)
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_upload_doc_invalid_kind(mock_db, financeiro_user):
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="galaxia",
                                              title=None, current_user=financeiro_user)
    assert getattr(ei.value, "status_code", None) == 400


@pytest.mark.asyncio
async def test_upload_doc_relatorio_publico_creates_document(mock_db, financeiro_user):
    res = await pmod.upload_prestacao_documento(file=_upload(), kind="relatorio",
                                                title=None, current_user=financeiro_user)
    assert res["visibility"] == "publico"
    assert res["title"] == "Relatório e Contas"
    assert res["document_id"]
    mock_db.documents.insert_one.assert_awaited()
    mock_db.audit_logs.insert_one.assert_awaited()


@pytest.mark.asyncio
async def test_upload_doc_orcamento_socios(mock_db, financeiro_user):
    res = await pmod.upload_prestacao_documento(file=_upload(), kind="orcamento",
                                                title="Orçamento 2027", current_user=financeiro_user)
    assert res["visibility"] == "socios"
    assert res["title"] == "Orçamento 2027"   # override respeitado


@pytest.mark.asyncio
async def test_upload_doc_rollback_on_db_failure(mock_db, financeiro_user, monkeypatch):
    mock_db.documents.insert_one.side_effect = RuntimeError("db down")
    deleted = {}
    monkeypatch.setattr(pmod, "delete_upload_file", lambda url: deleted.update(url=url) or True)
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="relatorio",
                                              title=None, current_user=financeiro_user)
    assert getattr(ei.value, "status_code", None) == 500
    assert deleted.get("url", "").startswith("/uploads/documents/")  # ficheiro limpo
