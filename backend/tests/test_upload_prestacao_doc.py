import io as _io

import pytest
from starlette.datastructures import Headers, UploadFile

import routes.prestacao_contas as pmod
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


def _upload(filename="relatorio.pdf", data=b"%PDF-1.4 conteudo"):
    return UploadFile(filename=filename, file=_io.BytesIO(data),
                      headers=Headers({"content-type": "application/pdf"}))


@pytest.fixture(autouse=True)
def _no_real_io(monkeypatch):
    # O endpoint não deve tocar no disco nos unit tests.
    async def _fake_save(category, contents, filename):
        return f"/uploads/{category}/fake-{filename}"
    monkeypatch.setattr(pmod, "save_validated_upload", _fake_save)


# --------------------------------------------------------------------------- #
# RBAC por kind (espelha a permissão da ação correspondente)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_upload_doc_forbidden_for_socio(mock_db, socio_user):
    # socio puro não é Direção/admin → 403 para relatorio.
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="relatorio",
                                              title=None, current_user=socio_user)
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_upload_doc_allowed_for_cf_privilege(mock_db, socio_user):
    # CF por overlay de privilégio: socio com `emit_cf_parecer` pode anexar parecer.
    cf_user = socio_user.model_copy(update={"privileges": ["emit_cf_parecer"]})
    res = await pmod.upload_prestacao_documento(
        file=_upload(), kind="parecer", title=None, current_user=cf_user
    )
    assert res["document_id"]
    # Rascunho NÃO-público — a publicação só acontece na ação.
    assert res["visibility"] == "direcao"
    mock_db.documents.insert_one.assert_awaited()


@pytest.mark.asyncio
async def test_upload_doc_allowed_for_direcao_cargo(mock_db, socio_user):
    # Direção por cargo: socio com a key canónica `dir_presidente` pode anexar relatorio.
    dir_user = socio_user.model_copy(update={"cargo": "dir_presidente"})
    res = await pmod.upload_prestacao_documento(
        file=_upload(), kind="relatorio", title=None, current_user=dir_user
    )
    assert res["document_id"]
    assert res["visibility"] == "direcao"
    mock_db.documents.insert_one.assert_awaited()


@pytest.mark.asyncio
async def test_upload_doc_invalid_kind(mock_db, financeiro_user):
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="galaxia",
                                              title=None, current_user=financeiro_user)
    assert getattr(ei.value, "status_code", None) == 400


# --------------------------------------------------------------------------- #
# Anti-falsificação cruzada de órgão (HIGH fix): cada kind exige o seu órgão.
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_upload_doc_relatorio_forbidden_for_financeiro(mock_db, financeiro_user):
    # manage_finances NÃO é Direção → não pode forjar 'Relatório e Contas'.
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="relatorio",
                                              title=None, current_user=financeiro_user)
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_upload_doc_orcamento_forbidden_for_financeiro(mock_db, financeiro_user):
    # orcamento é da Direção; manage_finances não basta.
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="orcamento",
                                              title=None, current_user=financeiro_user)
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_upload_doc_parecer_forbidden_for_manage_finances(mock_db, financeiro_user):
    # manage_finances a forjar 'Parecer do CF' → 403 (é exclusivo do CF).
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="parecer",
                                              title=None, current_user=financeiro_user)
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_upload_doc_relatorio_forbidden_for_cf_only(mock_db, socio_user):
    # CF (emit_cf_parecer, role socio) a forjar 'Relatório' → 403 (é da Direção).
    cf_user = socio_user.model_copy(update={"privileges": ["emit_cf_parecer"]})
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="relatorio",
                                              title=None, current_user=cf_user)
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_upload_doc_cf_cannot_upload_balancete(mock_db, socio_user):
    # CF (emit_cf_parecer, role socio) NÃO tem manage_finances → não pode forjar 'balancete'.
    cf_user = socio_user.model_copy(update={"privileges": ["emit_cf_parecer"]})
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="balancete",
                                              title=None, current_user=cf_user)
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_upload_doc_balancete_allowed_for_manage_finances(mock_db, financeiro_user):
    # balancete espelha manage_finances → permitido para financeiro.
    res = await pmod.upload_prestacao_documento(file=_upload(), kind="balancete",
                                                title=None, current_user=financeiro_user)
    assert res["document_id"]
    assert res["visibility"] == "direcao"  # rascunho
    mock_db.documents.insert_one.assert_awaited()


# --------------------------------------------------------------------------- #
# Rascunho NÃO-público no upload (HIGH fix): nunca publica.
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_upload_doc_creates_nonpublic_draft(mock_db, socio_user):
    dir_user = socio_user.model_copy(update={"cargo": "dir_presidente"})
    res = await pmod.upload_prestacao_documento(file=_upload(), kind="relatorio",
                                                title=None, current_user=dir_user)
    assert res["visibility"] == "direcao"  # NÃO publico
    assert res["title"] == "Relatório e Contas"
    assert res["kind"] == "relatorio"
    assert res["document_id"]
    mock_db.documents.insert_one.assert_awaited()
    mock_db.audit_logs.insert_one.assert_awaited()
    # O Document criado é não-público (visibility != publico/socios).
    inserted = mock_db.documents.insert_one.call_args.args[0]
    assert inserted["visibility"] == "direcao"


@pytest.mark.asyncio
async def test_upload_doc_orcamento_draft_title_override(mock_db, socio_user):
    dir_user = socio_user.model_copy(update={"cargo": "dir_presidente"})
    res = await pmod.upload_prestacao_documento(file=_upload(), kind="orcamento",
                                                title="Orçamento 2027", current_user=dir_user)
    assert res["visibility"] == "direcao"   # rascunho, NÃO 'socios'
    assert res["title"] == "Orçamento 2027"  # override respeitado


# --------------------------------------------------------------------------- #
# Rollback completo no upload (MEDIUM fix): falha de auditoria não deixa órfãos.
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_upload_doc_rollback_on_db_failure(mock_db, socio_user, monkeypatch):
    dir_user = socio_user.model_copy(update={"cargo": "dir_presidente"})
    mock_db.documents.insert_one.side_effect = RuntimeError("db down")
    deleted = {}
    monkeypatch.setattr(pmod, "delete_upload_file", lambda url: deleted.update(url=url) or True)
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="relatorio",
                                              title=None, current_user=dir_user)
    assert getattr(ei.value, "status_code", None) == 500
    assert deleted.get("url", "").startswith("/uploads/documents/")  # ficheiro limpo


@pytest.mark.asyncio
async def test_upload_doc_rollback_on_audit_failure(mock_db, socio_user, monkeypatch):
    # MEDIUM: a auditoria está DENTRO do try → falha rebobina ficheiro + registo.
    dir_user = socio_user.model_copy(update={"cargo": "dir_presidente"})
    mock_db.audit_logs.insert_one.side_effect = RuntimeError("audit down")
    deleted = {}
    monkeypatch.setattr(pmod, "delete_upload_file", lambda url: deleted.update(url=url) or True)
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="relatorio",
                                              title=None, current_user=dir_user)
    assert getattr(ei.value, "status_code", None) == 500
    assert deleted.get("url", "").startswith("/uploads/documents/")  # ficheiro limpo
    mock_db.documents.delete_one.assert_awaited()  # registo rebobinado (sem órfão)


# --------------------------------------------------------------------------- #
# Promoção (publicação) só acontece na ação — _publish_document.
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_publish_document_promotes_when_id_present(mock_db):
    await pmod._publish_document("doc1", "publico")
    mock_db.documents.update_one.assert_awaited_once()
    args = mock_db.documents.update_one.call_args.args
    # SEC: o filtro é ESCOPADO — só promove um RASCUNHO de prestação ('type'
    # prestacao_contas, 'visibility' direcao), nunca um documento arbitrário.
    assert args[0] == {"id": "doc1", "type": "prestacao_contas", "visibility": "direcao"}
    assert args[1] == {"$set": {"visibility": "publico"}}


@pytest.mark.asyncio
async def test_publish_document_noop_when_id_none(mock_db):
    await pmod._publish_document(None, "publico")
    mock_db.documents.update_one.assert_not_awaited()
