"""Serving de comprovativos (proofs) atrás de RBAC — spec 019, WS-A / H1.

Prova que os `proofs` (comprovativos financeiros) deixaram de ser públicos:
- o mount estático 404-a `proofs/` (defesa-em-profundidade), tal como `documents/`;
- só saem por `GET /api/finances/transactions/{id}/proof` sob `require_view_finances`,
  autorizados pelo id da transação e resolvidos com traversal guard sob UPLOAD_DIR/proofs.
"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

import routes.finances as finances
from database import UPLOAD_DIR
from server import UploadsStaticFiles

pytestmark = pytest.mark.unit


# --- mount estático: proofs e documents 404 (defesa-em-profundidade) --------
@pytest.mark.asyncio
async def test_static_mount_blocks_proofs_and_documents():
    sf = UploadsStaticFiles(directory=str(UPLOAD_DIR))
    for blocked in ("proofs", "proofs/x.pdf", "documents", "documents/y.pdf"):
        resp = await sf.get_response(blocked, {"type": "http"})
        assert resp.status_code == 404, f"{blocked} devia ser 404 no mount"
    assert "proofs" in UploadsStaticFiles._PROTECTED_PREFIXES
    assert "documents" in UploadsStaticFiles._PROTECTED_PREFIXES


# --- endpoint gated -----------------------------------------------------------
@pytest.mark.asyncio
async def test_proof_forbidden_for_socio(mock_db, socio_user):
    # require_view_finances dispara ANTES de qualquer leitura → 403 sem tocar na BD.
    with pytest.raises(HTTPException) as exc:
        await finances.get_transaction_proof("tx1", current_user=socio_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_proof_404_when_tx_missing(mock_db, admin_user):
    mock_db.transactions.find_one = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await finances.get_transaction_proof("tx1", current_user=admin_user)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_proof_404_when_no_proof_url(mock_db, admin_user):
    mock_db.transactions.find_one = AsyncMock(return_value={"id": "tx1", "proof_url": ""})
    with pytest.raises(HTTPException) as exc:
        await finances.get_transaction_proof("tx1", current_user=admin_user)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_proof_404_on_non_proofs_prefix(mock_db, admin_user):
    # proof_url que aponta para fora de /uploads/proofs/ (ex.: documents) → 404.
    mock_db.transactions.find_one = AsyncMock(
        return_value={"id": "tx1", "proof_url": "/uploads/documents/segredo.pdf"}
    )
    with pytest.raises(HTTPException) as exc:
        await finances.get_transaction_proof("tx1", current_user=admin_user)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_proof_traversal_stays_in_proofs_dir(mock_db, admin_user):
    # Path-traversal no filename nunca escapa a UPLOAD_DIR/proofs (usa só .name).
    mock_db.transactions.find_one = AsyncMock(
        return_value={"id": "tx1", "proof_url": "/uploads/proofs/../../server.py"}
    )
    with pytest.raises(HTTPException) as exc:
        await finances.get_transaction_proof("tx1", current_user=admin_user)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_proof_200_and_no_store(mock_db, admin_user, tmp_path):
    # Com um ficheiro real sob UPLOAD_DIR/proofs, admin recebe 200 + no-store.
    proofs_dir = UPLOAD_DIR / "proofs"
    proofs_dir.mkdir(parents=True, exist_ok=True)
    fname = "unittest_proof_019.pdf"
    fpath = proofs_dir / fname
    fpath.write_bytes(b"%PDF-1.4 test")
    try:
        mock_db.transactions.find_one = AsyncMock(
            return_value={"id": "tx1", "proof_url": f"/uploads/proofs/{fname}"}
        )
        resp = await finances.get_transaction_proof("tx1", current_user=admin_user)
        assert isinstance(resp, FileResponse)
        assert resp.status_code == 200
        assert resp.headers["Cache-Control"] == "no-store"
    finally:
        fpath.unlink(missing_ok=True)
