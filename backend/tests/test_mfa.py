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


# ====================== Task 2 — modelos ======================
def test_userbase_mfa_enabled_defaults_false():
    from models import User, UserBase

    assert UserBase(name="X", email="x@accta.cv").mfa_enabled is False
    # doc legado sem mfa_enabled → default, sem erro
    assert User(name="X", email="x@accta.cv", id="1").mfa_enabled is False


def test_userlogin_otp_optional():
    from models import UserLogin

    assert UserLogin(email="x@accta.cv", password="p").otp is None
    assert UserLogin(email="x@accta.cv", password="p", otp="123456").otp == "123456"


def test_token_mfa_setup_required_default_false():
    from models import Token, User

    u = User(name="X", email="x@accta.cv", id="1")
    assert Token(access_token="a", token_type="bearer", user=u).mfa_setup_required is False


def test_user_drops_mfa_secret_fields():
    from models import User

    u = User(name="X", email="x@accta.cv", id="1", mfa_secret="leak", mfa_backup_codes=["h"])
    dumped = u.model_dump()
    assert "mfa_secret" not in dumped
    assert "mfa_backup_codes" not in dumped


def test_mfa_request_models():
    from models import MfaDisableRequest, MfaVerifyRequest

    assert MfaVerifyRequest(otp="123456").otp == "123456"
    assert MfaDisableRequest(password="pw").password == "pw"


# ====================== Task 3 — endpoints ======================
def _http_request(path="/api/auth/mfa/setup"):
    from starlette.requests import Request

    return Request({"type": "http", "method": "POST", "path": path,
                    "headers": [], "client": ("t", 1), "query_string": b""})


@pytest.mark.asyncio
async def test_mfa_setup_stores_pending_and_returns_uri(mock_db, socio_user, monkeypatch):
    import routes.auth_routes as auth_routes
    from mfa import decrypt_secret

    monkeypatch.setattr(auth_routes.limiter, "enabled", False)
    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    resp = await auth_routes.mfa_setup(_http_request(), current_user=socio_user)

    assert resp["otpauth_uri"].startswith("otpauth://totp/")
    setdoc = mock_db.users.update_one.call_args.args[1]["$set"]
    assert decrypt_secret(setdoc["mfa_pending_secret"]) == resp["secret"]


@pytest.mark.asyncio
async def test_mfa_verify_activates_and_returns_backup_codes(mock_db, socio_user):
    import routes.auth_routes as auth_routes
    from mfa import encrypt_secret, generate_totp_secret, hash_backup_code
    from models import MfaVerifyRequest

    secret = generate_totp_secret()
    pending = encrypt_secret(secret)
    mock_db.users.find_one = AsyncMock(return_value={"id": socio_user.id, "mfa_pending_secret": pending})
    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    resp = await auth_routes.mfa_verify(MfaVerifyRequest(otp=pyotp.TOTP(secret).now()), current_user=socio_user)

    assert len(resp["backup_codes"]) == 10
    setdoc = mock_db.users.update_one.call_args.args[1]["$set"]
    assert setdoc["mfa_enabled"] is True
    assert setdoc["mfa_secret"] == pending
    assert hash_backup_code(resp["backup_codes"][0]) in setdoc["mfa_backup_codes"]


@pytest.mark.asyncio
async def test_mfa_verify_wrong_code_400(mock_db, socio_user):
    import routes.auth_routes as auth_routes
    from mfa import encrypt_secret, generate_totp_secret
    from models import MfaVerifyRequest

    secret = generate_totp_secret()
    mock_db.users.find_one = AsyncMock(return_value={"id": socio_user.id, "mfa_pending_secret": encrypt_secret(secret)})
    bad = "000000" if pyotp.TOTP(secret).now() != "000000" else "111111"
    with pytest.raises(HTTPException) as exc:
        await auth_routes.mfa_verify(MfaVerifyRequest(otp=bad), current_user=socio_user)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_mfa_verify_no_pending_400(mock_db, socio_user):
    import routes.auth_routes as auth_routes
    from models import MfaVerifyRequest

    mock_db.users.find_one = AsyncMock(return_value={"id": socio_user.id})
    with pytest.raises(HTTPException) as exc:
        await auth_routes.mfa_verify(MfaVerifyRequest(otp="123456"), current_user=socio_user)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_mfa_disable_requires_correct_password(mock_db, socio_user):
    import routes.auth_routes as auth_routes
    from auth import hash_password
    from models import MfaDisableRequest

    mock_db.users.find_one = AsyncMock(return_value={"id": socio_user.id, "password": hash_password("correct")})
    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    with pytest.raises(HTTPException) as exc:
        await auth_routes.mfa_disable(MfaDisableRequest(password="errada"), current_user=socio_user)
    assert exc.value.status_code == 403

    resp = await auth_routes.mfa_disable(MfaDisableRequest(password="correct"), current_user=socio_user)
    assert "message" in resp
    upd = mock_db.users.update_one.call_args.args[1]
    assert upd["$set"]["mfa_enabled"] is False
    assert "mfa_secret" in upd["$unset"]


@pytest.mark.asyncio
async def test_mfa_status(mock_db, admin_user):
    import routes.auth_routes as auth_routes

    mock_db.users.find_one = AsyncMock(
        return_value={"id": admin_user.id, "mfa_enabled": True, "mfa_backup_codes": ["a", "b"]}
    )
    resp = await auth_routes.mfa_status(current_user=admin_user)
    assert resp == {"enabled": True, "mandatory": True, "backup_codes_remaining": 2}
