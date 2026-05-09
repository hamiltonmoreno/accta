"""
Unit tests for auth.py — JWT creation/validation, password hashing,
and the get_current_user dependency.

These tests do NOT require a running backend or live MongoDB:
- DB calls are mocked via the `mock_db` fixture in conftest.py
- JWT signing/verification uses the SECRET_KEY env var set in conftest.py
"""
from __future__ import annotations

import os
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

import auth


pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------- #
# Password hashing
# --------------------------------------------------------------------------- #

class TestPasswordHashing:
    def test_hash_password_produces_bcrypt_string(self):
        hashed = auth.hash_password("Password123!")
        assert hashed.startswith("$2") and len(hashed) > 30

    def test_hash_password_is_non_deterministic(self):
        h1 = auth.hash_password("same-password")
        h2 = auth.hash_password("same-password")
        assert h1 != h2, "bcrypt should salt each hash differently"

    def test_verify_password_accepts_correct_password(self):
        hashed = auth.hash_password("CorrectHorseBatteryStaple")
        assert auth.verify_password("CorrectHorseBatteryStaple", hashed) is True

    def test_verify_password_rejects_wrong_password(self):
        hashed = auth.hash_password("right")
        assert auth.verify_password("wrong", hashed) is False

    def test_verify_password_rejects_empty_string(self):
        hashed = auth.hash_password("something")
        assert auth.verify_password("", hashed) is False


# --------------------------------------------------------------------------- #
# QR code hash
# --------------------------------------------------------------------------- #

class TestQrHash:
    def test_qr_hash_is_64_char_hex(self):
        h = auth.generate_qr_hash("user-123")
        assert len(h) == 64
        int(h, 16)  # raises if not hex

    def test_qr_hash_is_unique_per_call(self):
        a = auth.generate_qr_hash("user-123")
        b = auth.generate_qr_hash("user-123")
        assert a != b, "QR hash must include random component to prevent forgery"


# --------------------------------------------------------------------------- #
# JWT creation
# --------------------------------------------------------------------------- #

class TestCreateAccessToken:
    def test_token_contains_sub_and_exp(self):
        token = auth.create_access_token({"sub": "user-abc"})
        payload = jwt.decode(token, os.environ["SECRET_KEY"], algorithms=["HS256"])
        assert payload["sub"] == "user-abc"
        assert "exp" in payload

    def test_token_includes_extra_claims(self):
        token = auth.create_access_token({"sub": "u1", "role": "admin"})
        payload = jwt.decode(token, os.environ["SECRET_KEY"], algorithms=["HS256"])
        assert payload["role"] == "admin"

    def test_token_signed_with_app_secret_only(self):
        token = auth.create_access_token({"sub": "u1"})
        with pytest.raises(Exception):
            jwt.decode(token, "wrong-secret", algorithms=["HS256"])


# --------------------------------------------------------------------------- #
# get_current_user dependency
# --------------------------------------------------------------------------- #

def _bearer(token: str):
    """Mock Request com Authorization header — Sprint 10 changed
    get_current_user(credentials) -> get_current_user(request). Helper
    construi um request fake compativel com _extract_token."""

    class _MockRequest:
        def __init__(self, header_token=None, cookie_token=None):
            self.headers = {"Authorization": f"Bearer {header_token}"} if header_token else {}
            self.cookies = {"accta_session": cookie_token} if cookie_token else {}

    return _MockRequest(header_token=token)


def _cookie(token: str):
    """Mock Request com cookie httpOnly — testa o path Sprint 10."""

    class _MockRequest:
        def __init__(self, cookie_token):
            self.headers = {}
            self.cookies = {"accta_session": cookie_token}

    return _MockRequest(token)


class TestGetCurrentUser:
    async def test_valid_token_returns_user(self, mock_db, admin_user_dict, make_token):
        mock_db.users.find_one.return_value = admin_user_dict
        token = make_token(admin_user_dict["id"])
        user = await auth.get_current_user(_bearer(token))
        assert user.id == admin_user_dict["id"]
        assert user.role == "admin"

    async def test_expired_token_returns_401(self, mock_db, admin_user_dict, make_token):
        token = make_token(admin_user_dict["id"], expires_delta=timedelta(seconds=-10))
        with pytest.raises(HTTPException) as exc_info:
            await auth.get_current_user(_bearer(token))
        assert exc_info.value.status_code == 401

    async def test_malformed_token_returns_401(self, mock_db):
        with pytest.raises(HTTPException) as exc_info:
            await auth.get_current_user(_bearer("not-a-jwt"))
        assert exc_info.value.status_code == 401

    async def test_token_signed_with_wrong_secret_returns_401(self, mock_db):
        bad = jwt.encode({"sub": "u1"}, "different-secret", algorithm="HS256")
        with pytest.raises(HTTPException) as exc_info:
            await auth.get_current_user(_bearer(bad))
        assert exc_info.value.status_code == 401

    async def test_token_with_wrong_algorithm_returns_401(self, mock_db):
        # 'none' algorithm tokens must never be accepted (HS256 is enforced).
        unsigned = jwt.encode({"sub": "u1"}, "", algorithm="HS256")
        # Tamper with the header to fake 'none' alg — the server should still reject.
        parts = unsigned.split(".")
        import base64
        fake_header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode()
        forged = ".".join([fake_header, parts[1], ""])
        with pytest.raises(HTTPException) as exc_info:
            await auth.get_current_user(_bearer(forged))
        assert exc_info.value.status_code == 401

    async def test_missing_sub_claim_returns_401(self, mock_db):
        token = jwt.encode({"foo": "bar"}, os.environ["SECRET_KEY"], algorithm="HS256")
        with pytest.raises(HTTPException) as exc_info:
            await auth.get_current_user(_bearer(token))
        assert exc_info.value.status_code == 401

    async def test_unknown_user_returns_401(self, mock_db, make_token):
        mock_db.users.find_one.return_value = None
        token = make_token("ghost-user-id")
        with pytest.raises(HTTPException) as exc_info:
            await auth.get_current_user(_bearer(token))
        assert exc_info.value.status_code == 401


# --------------------------------------------------------------------------- #
# get_user_from_token (SSE helper)
# --------------------------------------------------------------------------- #

class TestGetUserFromToken:
    async def test_valid_token_returns_user(self, mock_db, socio_user_dict, make_token):
        mock_db.users.find_one.return_value = socio_user_dict
        token = make_token(socio_user_dict["id"])
        user = await auth.get_user_from_token(token)
        assert user is not None and user.id == socio_user_dict["id"]

    async def test_invalid_token_returns_none(self, mock_db):
        # SSE helper returns None instead of raising — connections close gracefully.
        result = await auth.get_user_from_token("garbage")
        assert result is None

    async def test_expired_token_returns_none(self, mock_db, make_token):
        token = make_token("u1", expires_delta=timedelta(seconds=-1))
        result = await auth.get_user_from_token(token)
        assert result is None

    async def test_unknown_user_returns_none(self, mock_db, make_token):
        mock_db.users.find_one.return_value = None
        token = make_token("ghost")
        result = await auth.get_user_from_token(token)
        assert result is None
