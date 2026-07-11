"""Unit tests for file_validation.validate_file_content (defense-in-depth
contra extension spoofing). Sem MongoDB nem backend a correr.
"""

from __future__ import annotations

from io import BytesIO

import pytest
from fastapi import HTTPException
from PIL import Image

from file_validation import validate_file_content, read_upload_capped


pytestmark = pytest.mark.unit


# ---------- spec 019 / T027: cap de upload em streaming (413 antes de buffrar) ----------
class _FakeUploadFile:
    """UploadFile falso que devolve `total` bytes em pedaços de `chunk` — conta
    quantos bytes foram efetivamente lidos (prova que abortamos cedo)."""

    def __init__(self, total: int, chunk: int = 64 * 1024):
        self._left = total
        self._chunk = chunk
        self.bytes_read = 0

    async def read(self, size: int = -1) -> bytes:
        if self._left <= 0:
            return b""
        n = self._left if size in (-1, None) else min(size, self._left)
        self._left -= n
        self.bytes_read += n
        return b"x" * n


@pytest.mark.asyncio
async def test_read_upload_capped_accepts_within_limit():
    f = _FakeUploadFile(total=1000)
    data = await read_upload_capped(f, max_size=5000)
    assert len(data) == 1000


@pytest.mark.asyncio
async def test_read_upload_capped_aborts_over_limit_without_buffering():
    max_size = 256 * 1024
    f = _FakeUploadFile(total=50 * 1024 * 1024)  # 50 MB "stream"
    with pytest.raises(HTTPException) as exc:
        await read_upload_capped(f, max_size=max_size)
    assert exc.value.status_code == 413
    # Nunca materializou o corpo inteiro: parou pouco depois de exceder o limite.
    assert f.bytes_read <= max_size + 64 * 1024


def _png_bytes(size=(10, 10), color=(255, 0, 0)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _jpeg_bytes() -> bytes:
    img = Image.new("RGB", (10, 10), (0, 255, 0))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _pdf_bytes() -> bytes:
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< >>\nendobj\n"


# ---------- validos ----------


def test_png_bytes_accepted_with_png_ext():
    validate_file_content(_png_bytes(), "photo.png", [".png", ".jpg"])


def test_jpeg_bytes_accepted_with_jpg_ext():
    validate_file_content(_jpeg_bytes(), "photo.jpg", [".jpg", ".jpeg"])


def test_pdf_bytes_accepted_with_pdf_ext():
    validate_file_content(_pdf_bytes(), "doc.pdf", [".pdf"])


# ---------- ataques bloqueados ----------


def test_exe_renamed_to_png_rejected():
    """O caso classico: .exe renomeado para .png — magic byte / Pillow rejeita."""
    fake = b"MZ\x90\x00\x03" + b"\x00" * 100  # MZ = PE/EXE header
    with pytest.raises(HTTPException) as exc:
        validate_file_content(fake, "malware.png", [".png"])
    assert exc.value.status_code == 400


def test_random_bytes_with_png_ext_rejected():
    with pytest.raises(HTTPException):
        validate_file_content(b"not a real image at all", "x.png", [".png"])


def test_pdf_bytes_with_png_ext_rejected():
    """Cross-check: bytes de PDF com extensao .png — formato real != extensao."""
    with pytest.raises(HTTPException):
        validate_file_content(_pdf_bytes(), "fake.png", [".png", ".pdf"])


def test_png_bytes_with_jpg_ext_rejected():
    """Cross-check: PNG real mas extensao .jpg deve falhar."""
    with pytest.raises(HTTPException):
        validate_file_content(_png_bytes(), "fake.jpg", [".jpg"])


def test_extension_not_in_allowlist_rejected():
    with pytest.raises(HTTPException) as exc:
        validate_file_content(_png_bytes(), "x.gif", [".png", ".jpg"])
    assert exc.value.status_code == 400


def test_random_bytes_with_pdf_ext_rejected():
    with pytest.raises(HTTPException):
        validate_file_content(b"this is not a pdf", "fake.pdf", [".pdf"])
