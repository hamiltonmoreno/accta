#!/usr/bin/env python3
"""Gera um par de chaves VAPID para as notificações Web Push.

Uso:
    python scripts/generate_vapid_keys.py

Cola a saída nas variáveis de ambiente do backend (NÃO commitar a privada):

    VAPID_PUBLIC_KEY=...
    VAPID_PRIVATE_KEY=...
    VAPID_SUBJECT=mailto:teu-email@dominio

A chave pública (base64url) é a `applicationServerKey` que o browser usa para
subscrever; é servida ao frontend por GET /api/push/vapid-public-key.
"""

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def main() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())

    # Privada: raw 32 bytes (formato esperado por pywebpush/py-vapid).
    private_value = private_key.private_numbers().private_value
    private_raw = private_value.to_bytes(32, "big")

    # Pública: ponto não comprimido (0x04 || X || Y), 65 bytes.
    public_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )

    print("VAPID_PUBLIC_KEY=" + _b64url(public_raw))
    print("VAPID_PRIVATE_KEY=" + _b64url(private_raw))
    print("VAPID_SUBJECT=mailto:admin@controlador.cv")


if __name__ == "__main__":
    main()
