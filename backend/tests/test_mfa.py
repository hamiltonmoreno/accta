"""Testes do F2 MFA (spec-mfa-f2). Unit in-process; cripto/TOTP sem DB,
endpoints/login com mock_db.
"""
from __future__ import annotations

import re
from unittest.mock import AsyncMock, MagicMock

import pyotp
import pytest
from fastapi import HTTPException

pytestmark = pytest.mark.unit


# ====================== Task 1 — primitivas (mfa.py) ======================
def test_encrypt_decrypt_roundtrip():
    from mfa import decrypt_secret, encrypt_secret, generate_totp_secret

    s = generate_totp_secret()
    token = encrypt_secret(s)
    assert token != s
    assert decrypt_secret(token) == s


def test_generate_totp_secret_is_base32():
    from mfa import generate_totp_secret

    s = generate_totp_secret()
    assert len(s) >= 16
    assert re.fullmatch(r"[A-Z2-7]+", s)


def test_provisioning_uri_has_issuer():
    from mfa import generate_totp_secret, provisioning_uri

    uri = provisioning_uri(generate_totp_secret(), "x@accta.cv")
    assert uri.startswith("otpauth://totp/")
    assert "issuer=Portal%20ACCTA" in uri


def test_verify_totp_accepts_current_rejects_wrong():
    from mfa import generate_totp_secret, verify_totp

    s = generate_totp_secret()
    code = pyotp.TOTP(s).now()
    assert verify_totp(s, code) is True
    wrong = "000000" if code != "000000" else "111111"
    assert verify_totp(s, wrong) is False


def test_backup_codes_count_unique_and_hash():
    from mfa import BACKUP_CODE_COUNT, generate_backup_codes, hash_backup_code

    codes = generate_backup_codes()
    assert len(codes) == BACKUP_CODE_COUNT == len(set(codes))
    assert hash_backup_code(codes[0]) != codes[0]


def test_consume_backup_code():
    from mfa import consume_backup_code, hash_backup_code

    plain = "aaaa-bbbb"
    stored = [hash_backup_code(plain), hash_backup_code("other")]
    new = consume_backup_code(stored, plain)
    assert new == [hash_backup_code("other")]
    assert consume_backup_code(stored, "nao-existe") is None


def test_is_mfa_mandatory():
    from mfa import is_mfa_mandatory

    assert is_mfa_mandatory("admin") is True
    assert is_mfa_mandatory("financeiro") is True
    assert is_mfa_mandatory("socio") is False
    assert is_mfa_mandatory("moderador") is False
