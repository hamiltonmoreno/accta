"""MFA TOTP — cripto, geração/validação de OTP e backup codes (spec-mfa-f2).

Segredo TOTP cifrado em repouso com Fernet (chave derivada do SECRET_KEY).
Backup codes guardados como hash sha256. Mantém auth.py enxuto.
"""
from __future__ import annotations

import base64
import hashlib
import secrets
from typing import Optional

import pyotp
from cryptography.fernet import Fernet

from auth import SECRET_KEY

MFA_MANDATORY_ROLES = {"admin", "financeiro"}
ISSUER = "Portal ACCTA"
BACKUP_CODE_COUNT = 10


def _fernet() -> Fernet:
    # Chave Fernet determinística a partir do SECRET_KEY (32 bytes urlsafe-b64).
    key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
    return Fernet(key)


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_secret(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)


def verify_totp(secret: str, code: str) -> bool:
    # valid_window=1 tolera +-30s de drift de relógio.
    return pyotp.TOTP(secret).verify((code or "").strip(), valid_window=1)


def generate_backup_codes(n: int = BACKUP_CODE_COUNT) -> list[str]:
    return [f"{secrets.token_hex(2)}-{secrets.token_hex(2)}" for _ in range(n)]


def hash_backup_code(code: str) -> str:
    return hashlib.sha256((code or "").strip().encode()).hexdigest()


def consume_backup_code(stored_hashes: list[str], code: str) -> Optional[list[str]]:
    """Se `code` (em claro) casar um hash em `stored_hashes`, devolve a lista
    SEM esse hash (uso único). Caso contrário, None."""
    h = hash_backup_code(code)
    codes = stored_hashes or []
    return [c for c in codes if c != h] if h in codes else None


def is_mfa_mandatory(role: str) -> bool:
    return role in MFA_MANDATORY_ROLES
