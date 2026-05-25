"""MFA TOTP — cripto, geração/validação de OTP e backup codes (spec-mfa-f2).

Segredo TOTP cifrado em repouso com Fernet (chave derivada do SECRET_KEY).
Backup codes guardados como hash sha256. Mantém auth.py enxuto.
"""
from __future__ import annotations

import base64
import hashlib
import secrets

import pyotp
from cryptography.fernet import Fernet, InvalidToken

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


def verify_totp_encrypted(encrypted_secret: str, code: str) -> bool:
    """Verifica um OTP contra um segredo TOTP CIFRADO. Falha FECHADO (False) se
    o token estiver corrompido ou o SECRET_KEY tiver sido rodado (InvalidToken),
    em vez de propagar 500 no caminho de login/verify."""
    try:
        secret = decrypt_secret(encrypted_secret)
    except InvalidToken:
        return False
    return verify_totp(secret, code)


def generate_backup_codes(n: int = BACKUP_CODE_COUNT) -> list[str]:
    return ["-".join(secrets.token_hex(2) for _ in range(5)) for _ in range(n)]


def hash_backup_code(code: str) -> str:
    return hashlib.sha256((code or "").strip().encode()).hexdigest()


def is_mfa_mandatory(role: str) -> bool:
    return role in MFA_MANDATORY_ROLES
