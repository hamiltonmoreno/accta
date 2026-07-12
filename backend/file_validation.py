"""Validacao de tipo real do conteudo de uploads (defense-in-depth contra
extensao spoofing). Para imagens usa Pillow.verify(); para outros formatos
inspecciona os primeiros bytes (magic numbers).

Limites: NAO substitui um scan AV. Polyglots (e.g., PDF + ZIP no mesmo
ficheiro) podem passar — para isso era preciso libmagic/python-magic ou
um servico AV separado. Esta camada bloqueia o caso comum de .exe
renomeado para .png.
"""

from io import BytesIO
from pathlib import Path
from typing import Iterable

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

_READ_CHUNK = 64 * 1024


async def read_upload_capped(file: UploadFile, max_size: int) -> bytes:
    """Lê um UploadFile em streaming, abortando com 413 assim que o total exceder
    `max_size` — nunca materializa mais de max_size+chunk em memória. Substitui o
    `await file.read()` que lia o corpo INTEIRO antes de qualquer check de tamanho
    (exaustão de memória; spec 019, FR-015)."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_READ_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > max_size:
            raise HTTPException(status_code=413, detail=f"Ficheiro excede o limite de {max_size // (1024 * 1024)} MB")
        chunks.append(chunk)
    return b"".join(chunks)


# Magic byte signatures por extensao. Cada entrada e uma lista de prefixos
# possiveis (para WEBP / WAV ha um prefixo RIFF + verificacao a posteriori).
_MAGIC_PREFIXES: dict[str, list[bytes]] = {
    ".pdf": [b"%PDF-"],
    ".doc": [b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"],  # OLE compound (legacy DOC)
    ".docx": [b"PK\x03\x04"],  # ZIP container
    ".jpg": [b"\xFF\xD8\xFF"],
    ".jpeg": [b"\xFF\xD8\xFF"],
    ".png": [b"\x89PNG\r\n\x1A\n"],
    ".webp": [b"RIFF"],  # mais validacao abaixo
    # .svg deliberadamente ausente: SVG e XML executavel (stored XSS) e nao
    # e aceite em nenhuma categoria de upload.
}

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _check_prefix(content: bytes, exts: Iterable[str]) -> bool:
    for ext in exts:
        for prefix in _MAGIC_PREFIXES.get(ext, []):
            if content.startswith(prefix):
                # WEBP: RIFF + 4 bytes size + "WEBP"
                if ext == ".webp":
                    return len(content) >= 12 and content[8:12] == b"WEBP"
                return True
    return False


def validate_file_content(content: bytes, filename: str, allowed_exts: Iterable[str]) -> None:
    """Valida que `content` corresponde a um dos `allowed_exts`. Raise 400
    se a magic byte / verify() falhar.
    """
    ext = Path(filename).suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo nao permitido. Permitidos: {', '.join(allowed_exts)}",
        )

    # Imagens: Pillow.verify() e o gold standard (deteca corruption + parsing
    # real). SVG nao passa por aqui (texto).
    if ext in _IMAGE_EXTS:
        try:
            with Image.open(BytesIO(content)) as img:
                img.verify()
        except (UnidentifiedImageError, OSError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Conteudo nao corresponde a uma imagem valida (extensao spoofada?)",
            )
        # Cross-check: o formato detectado tem que bater com a extensao.
        try:
            with Image.open(BytesIO(content)) as img:
                fmt = (img.format or "").lower()
        except Exception:
            raise HTTPException(status_code=400, detail="Imagem invalida")
        expected = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}[ext.lstrip(".")]
        if fmt != expected:
            raise HTTPException(
                status_code=400,
                detail=f"Formato real ({fmt}) nao corresponde a extensao ({ext})",
            )
        return

    # Nao-imagens: magic prefix.
    if not _check_prefix(content, [ext]):
        raise HTTPException(
            status_code=400,
            detail=f"Conteudo do ficheiro nao corresponde a extensao {ext}",
        )
