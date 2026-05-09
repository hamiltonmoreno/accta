"""Unit tests for file_validation.validate_file_content (defense-in-depth
contra extension spoofing). Sem MongoDB nem backend a correr.
"""

from __future__ import annotations

from io import BytesIO

import pytest
from fastapi import HTTPException
from PIL import Image

from file_validation import validate_file_content


pytestmark = pytest.mark.unit


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
