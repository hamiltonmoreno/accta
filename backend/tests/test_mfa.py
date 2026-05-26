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


def test_verify_totp_encrypted_fails_closed_on_corrupt_token():
    from mfa import encrypt_secret, generate_totp_secret, verify_totp_encrypted

    secret = generate_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert verify_totp_encrypted(encrypt_secret(secret), code) is True
    # token corrompido / SECRET_KEY rodado → False (sem exceção, sem 500)
    assert verify_totp_encrypted("nao-e-token-fernet-valido", code) is False


def test_backup_codes_count_unique_and_hash():
    from mfa import BACKUP_CODE_COUNT, generate_backup_codes, hash_backup_code

    codes = generate_backup_codes()
    assert len(codes) == BACKUP_CODE_COUNT == len(set(codes))
    assert hash_backup_code(codes[0]) != codes[0]


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
    from fastapi import Response
    from mfa import encrypt_secret, generate_totp_secret, hash_backup_code
    from models import MfaVerifyRequest

    secret = generate_totp_secret()
    pending = encrypt_secret(secret)
    mock_db.users.find_one = AsyncMock(return_value={"id": socio_user.id, "mfa_pending_secret": pending})
    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    resp = await auth_routes.mfa_verify(
        _login_request(), MfaVerifyRequest(otp=pyotp.TOTP(secret).now()), Response(), current_user=socio_user
    )

    assert len(resp["backup_codes"]) == 10
    # FIX 1: verify faz upgrade da sessão para token completo (sem mfa_pending).
    assert resp["access_token"]
    setdoc = mock_db.users.update_one.call_args.args[1]["$set"]
    assert setdoc["mfa_enabled"] is True
    assert setdoc["mfa_secret"] == pending
    assert hash_backup_code(resp["backup_codes"][0]) in setdoc["mfa_backup_codes"]


@pytest.mark.asyncio
async def test_mfa_verify_wrong_code_400(mock_db, socio_user):
    import routes.auth_routes as auth_routes
    from fastapi import Response
    from mfa import encrypt_secret, generate_totp_secret
    from models import MfaVerifyRequest

    secret = generate_totp_secret()
    mock_db.users.find_one = AsyncMock(return_value={"id": socio_user.id, "mfa_pending_secret": encrypt_secret(secret)})
    bad = "000000" if pyotp.TOTP(secret).now() != "000000" else "111111"
    with pytest.raises(HTTPException) as exc:
        await auth_routes.mfa_verify(_login_request(), MfaVerifyRequest(otp=bad), Response(), current_user=socio_user)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_mfa_verify_no_pending_400(mock_db, socio_user):
    import routes.auth_routes as auth_routes
    from fastapi import Response
    from models import MfaVerifyRequest

    mock_db.users.find_one = AsyncMock(return_value={"id": socio_user.id})
    with pytest.raises(HTTPException) as exc:
        await auth_routes.mfa_verify(_login_request(), MfaVerifyRequest(otp="123456"), Response(), current_user=socio_user)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_mfa_disable_requires_correct_password(mock_db, socio_user):
    import routes.auth_routes as auth_routes
    from auth import hash_password
    from models import MfaDisableRequest

    mock_db.users.find_one = AsyncMock(return_value={"id": socio_user.id, "password": hash_password("correct")})
    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    with pytest.raises(HTTPException) as exc:
        await auth_routes.mfa_disable(_login_request(), MfaDisableRequest(password="errada"), current_user=socio_user)
    assert exc.value.status_code == 403

    resp = await auth_routes.mfa_disable(_login_request(), MfaDisableRequest(password="correct"), current_user=socio_user)
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


# ====================== Task 4 — gate no login ======================
def _login_request():
    from starlette.requests import Request

    return Request({"type": "http", "method": "POST", "path": "/api/auth/login",
                    "headers": [], "client": ("t", 1), "query_string": b""})


def _user_doc(role="socio", mfa_enabled=False, secret=None, backups=None):
    from auth import hash_password

    doc = {
        "id": "u1", "name": "U", "email": "u@accta.cv", "role": role, "status": "ativo",
        "cargo": "socio", "privileges": [], "consent_data": True, "password": hash_password("pw"),
    }
    if mfa_enabled:
        from mfa import encrypt_secret

        doc["mfa_enabled"] = True
        doc["mfa_secret"] = encrypt_secret(secret)
        doc["mfa_backup_codes"] = backups or []
    return doc


@pytest.fixture
def login_env(mock_db, monkeypatch):
    import routes.auth_routes as auth_routes

    monkeypatch.setattr(auth_routes.limiter, "enabled", False)
    mock_db.login_attempts = MagicMock()
    mock_db.login_attempts.count_documents = AsyncMock(return_value=0)
    mock_db.login_attempts.insert_one = AsyncMock()
    mock_db.login_attempts.delete_many = AsyncMock()
    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    return auth_routes


@pytest.mark.asyncio
async def test_login_mfa_required_without_otp(login_env, mock_db):
    from fastapi import Response
    from mfa import generate_totp_secret
    from models import UserLogin

    mock_db.users.find_one = AsyncMock(return_value=_user_doc(mfa_enabled=True, secret=generate_totp_secret()))
    with pytest.raises(HTTPException) as exc:
        await login_env.login(_login_request(), Response(), UserLogin(email="u@accta.cv", password="pw"))
    assert exc.value.status_code == 401
    assert exc.value.detail == "mfa_required"


@pytest.mark.asyncio
async def test_login_mfa_invalid_otp_counts_failure(login_env, mock_db):
    from fastapi import Response
    from mfa import generate_totp_secret
    from models import UserLogin

    secret = generate_totp_secret()
    mock_db.users.find_one = AsyncMock(return_value=_user_doc(mfa_enabled=True, secret=secret))
    # OTP errado não é um backup code → o $pull atómico não casa (modified_count=0).
    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=0))
    bad = "000000" if pyotp.TOTP(secret).now() != "000000" else "111111"
    with pytest.raises(HTTPException) as exc:
        await login_env.login(_login_request(), Response(), UserLogin(email="u@accta.cv", password="pw", otp=bad))
    assert exc.value.status_code == 401
    assert exc.value.detail == "mfa_invalido"
    mock_db.login_attempts.insert_one.assert_awaited()


@pytest.mark.asyncio
async def test_login_mfa_totp_ok_issues_token(login_env, mock_db):
    from fastapi import Response
    from mfa import generate_totp_secret
    from models import UserLogin

    secret = generate_totp_secret()
    mock_db.users.find_one = AsyncMock(return_value=_user_doc(mfa_enabled=True, secret=secret))
    tok = await login_env.login(
        _login_request(), Response(), UserLogin(email="u@accta.cv", password="pw", otp=pyotp.TOTP(secret).now())
    )
    assert tok.access_token
    assert tok.user.mfa_enabled is True


@pytest.mark.asyncio
async def test_login_backup_code_consumed(login_env, mock_db):
    from fastapi import Response
    from mfa import generate_totp_secret, hash_backup_code
    from models import UserLogin

    secret = generate_totp_secret()
    backups = [hash_backup_code("aaaa-bbbb"), hash_backup_code("cccc-dddd")]
    mock_db.users.find_one = AsyncMock(return_value=_user_doc(mfa_enabled=True, secret=secret, backups=backups))
    # TOTP falha para o backup code; o $pull atómico simula sucesso (modified_count=1).
    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    tok = await login_env.login(
        _login_request(), Response(), UserLogin(email="u@accta.cv", password="pw", otp="aaaa-bbbb")
    )
    assert tok.access_token
    # Consumo atómico via $pull condicional. O filtro é SÓ por `id` (escalar): o DAO
    # Mongo-compatível NÃO emula pertença em array, logo o filtro NÃO pode conter
    # `mfa_backup_codes` (ver test_login_backup_code_works_against_dao_semantics).
    consume_calls = [
        c for c in mock_db.users.update_one.call_args_list
        if "$pull" in c.args[1] and "mfa_backup_codes" in c.args[1]["$pull"]
    ]
    assert consume_calls, "esperava um $pull atómico do hash do backup code"
    filt = consume_calls[0].args[0]
    assert "mfa_backup_codes" not in filt, "filtro não pode depender de pertença em array (não suportada pelo DAO)"
    assert filt == {"id": "u1"}
    assert consume_calls[0].args[1] == {"$pull": {"mfa_backup_codes": hash_backup_code("aaaa-bbbb")}}


class _FakeUsersDAO:
    """DAO de utilizadores fiel à semântica do DAO real para este caso: um filtro
    {campo_array: escalar} NÃO casa (o DAO Mongo-compatível não emula pertença em
    array) e o $pull só altera modified_count se o valor estava mesmo no array.
    Com isto, o filtro bugado de array-membership devolve modified_count=0 → o teste
    abaixo falharia com o código antigo e passa com o fix (filtro por `id`)."""

    def __init__(self, doc):
        self.doc = doc

    async def find_one(self, *_a, **_k):
        return dict(self.doc)

    async def update_one(self, filt, update):
        for key, want in filt.items():
            cur = self.doc.get(key)
            if isinstance(cur, list) and not isinstance(want, list):
                return MagicMock(modified_count=0)  # pertença em array: não suportada
            if not isinstance(cur, list) and cur != want:
                return MagicMock(modified_count=0)
        changed = False
        for field, val in (update.get("$pull") or {}).items():
            arr = self.doc.get(field, [])
            if val in arr:
                arr.remove(val)
                self.doc[field] = arr
                changed = True
        if update.get("$set"):
            self.doc.update(update["$set"])
            changed = True
        return MagicMock(modified_count=1 if changed else 0)


@pytest.mark.asyncio
async def test_login_backup_code_works_against_dao_semantics(login_env, mock_db):
    """Regressão: login por backup code contra um DAO que emula o Postgres real.
    Apanha o bug que o mock_db genérico (modified_count fixo) escondia."""
    from fastapi import Response
    from mfa import generate_totp_secret, hash_backup_code
    from models import UserLogin

    secret = generate_totp_secret()
    h_used, h_other = hash_backup_code("aaaa-bbbb"), hash_backup_code("cccc-dddd")
    doc = _user_doc(mfa_enabled=True, secret=secret, backups=[h_used, h_other])
    fake = _FakeUsersDAO(doc)
    mock_db.users.find_one = fake.find_one
    mock_db.users.update_one = fake.update_one

    tok = await login_env.login(
        _login_request(), Response(), UserLogin(email="u@accta.cv", password="pw", otp="aaaa-bbbb")
    )
    assert tok.access_token  # falha com filtro de array-membership (modified_count=0 → mfa_invalido)
    assert h_used not in doc["mfa_backup_codes"], "o backup code usado tem de ser consumido"
    assert h_other in doc["mfa_backup_codes"], "os restantes backup codes mantêm-se"


@pytest.mark.asyncio
async def test_login_admin_unenrolled_flags_setup_required(login_env, mock_db):
    from fastapi import Response
    from models import UserLogin

    mock_db.users.find_one = AsyncMock(return_value=_user_doc(role="admin", mfa_enabled=False))
    tok = await login_env.login(_login_request(), Response(), UserLogin(email="u@accta.cv", password="pw"))
    assert tok.mfa_setup_required is True


@pytest.mark.asyncio
async def test_login_socio_unenrolled_no_setup_required(login_env, mock_db):
    from fastapi import Response
    from models import UserLogin

    mock_db.users.find_one = AsyncMock(return_value=_user_doc(role="socio", mfa_enabled=False))
    tok = await login_env.login(_login_request(), Response(), UserLogin(email="u@accta.cv", password="pw"))
    assert tok.mfa_setup_required is False


@pytest.mark.asyncio
async def test_login_response_hides_mfa_secret(login_env, mock_db):
    from fastapi import Response
    from mfa import generate_totp_secret
    from models import UserLogin

    secret = generate_totp_secret()
    mock_db.users.find_one = AsyncMock(return_value=_user_doc(mfa_enabled=True, secret=secret, backups=["h"]))
    tok = await login_env.login(
        _login_request(), Response(), UserLogin(email="u@accta.cv", password="pw", otp=pyotp.TOTP(secret).now())
    )
    dumped = tok.user.model_dump()
    assert "mfa_secret" not in dumped
    assert "mfa_backup_codes" not in dumped
    assert "password" not in dumped


# ====================== FIX 1 — enforcement de MFA obrigatório ======================
def _bearer_request(token: str, path: str):
    """Request real com Authorization Bearer + path — get_current_user lê
    request.url.path para o gate mfa_pending."""
    from starlette.requests import Request

    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": [(b"authorization", f"Bearer {token}".encode())],
            "query_string": b"",
        }
    )


@pytest.mark.asyncio
async def test_login_admin_unenrolled_token_is_mfa_pending(login_env, mock_db):
    """Admin obrigatório-sem-MFA → o token de login carrega a claim mfa_pending
    (sessão limitada). Sócio sem MFA não a carrega."""
    from fastapi import Response
    from jose import jwt
    from models import UserLogin

    import auth

    mock_db.users.find_one = AsyncMock(return_value=_user_doc(role="admin", mfa_enabled=False))
    tok = await login_env.login(_login_request(), Response(), UserLogin(email="u@accta.cv", password="pw"))
    payload = jwt.decode(tok.access_token, auth.SECRET_KEY, algorithms=["HS256"])
    assert payload.get("mfa_pending") is True

    mock_db.users.find_one = AsyncMock(return_value=_user_doc(role="socio", mfa_enabled=False))
    tok2 = await login_env.login(_login_request(), Response(), UserLogin(email="u@accta.cv", password="pw"))
    payload2 = jwt.decode(tok2.access_token, auth.SECRET_KEY, algorithms=["HS256"])
    assert "mfa_pending" not in payload2


@pytest.mark.asyncio
async def test_get_current_user_blocks_mfa_pending_on_protected_path(mock_db, make_token):
    """Uma sessão mfa_pending só pode tocar endpoints de enrolment/sessão.
    Caminho protegido → 403 mfa_setup_required; caminho de setup → passa."""
    import auth
    from models import User

    mock_db.tokens_revoked = MagicMock()
    mock_db.tokens_revoked.find_one = AsyncMock(return_value=None)
    mock_db.users.find_one = AsyncMock(
        return_value={"id": "adm", "email": "a@accta.cv", "name": "A", "role": "admin", "status": "ativo"}
    )
    token = make_token("adm", extra_claims={"mfa_pending": True})

    # Caminho não-enrolment → bloqueado com 403 mfa_setup_required.
    with pytest.raises(HTTPException) as exc:
        await auth.get_current_user(_bearer_request(token, "/api/users"))
    assert exc.value.status_code == 403
    assert exc.value.detail == "mfa_setup_required"

    # Caminho de enrolment → permitido (devolve o User).
    user = await auth.get_current_user(_bearer_request(token, "/api/auth/mfa/setup"))
    assert isinstance(user, User)
    assert user.id == "adm"


# ====================== FIX 2 — campos MFA nunca expostos ======================
@pytest.mark.asyncio
async def test_get_user_projection_excludes_mfa_fields(mock_db, admin_user):
    """A rota PEDE explicitamente a exclusão dos campos MFA na projeção
    (o mock_db não aplica projeções — testa-se o pedido)."""
    import routes.users as users_routes

    mock_db.users.find_one = AsyncMock(return_value={"id": "outro-id", "name": "X"})
    await users_routes.get_user("outro-id", current_user=admin_user)
    proj = mock_db.users.find_one.call_args.args[1]
    assert proj.get("password") == 0
    assert proj.get("mfa_secret") == 0
    assert proj.get("mfa_pending_secret") == 0
    assert proj.get("mfa_backup_codes") == 0


@pytest.mark.asyncio
async def test_update_own_profile_projection_excludes_mfa_fields(mock_db, socio_user):
    import routes.users as users_routes
    from models import UserProfileUpdate

    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    mock_db.users.find_one = AsyncMock(return_value={"id": socio_user.id, "name": "X"})
    await users_routes.update_own_profile(UserProfileUpdate(phone_number="999"), current_user=socio_user)
    proj = mock_db.users.find_one.call_args.args[1]
    assert proj.get("mfa_secret") == 0
    assert proj.get("mfa_pending_secret") == 0
    assert proj.get("mfa_backup_codes") == 0


@pytest.mark.asyncio
async def test_admin_update_user_projection_excludes_mfa_fields(mock_db, admin_user):
    import routes.users as users_routes
    from models import UserAdminUpdate

    # 1.ª find_one = leitura do existente; depois update; 2.ª find_one = leitura final.
    mock_db.users.find_one = AsyncMock(
        side_effect=[{"id": "alvo", "name": "X"}, {"id": "alvo", "name": "X"}]
    )
    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    await users_routes.admin_update_user(
        "alvo", UserAdminUpdate(status="ativo"), _http_request(), current_user=admin_user
    )
    proj = mock_db.users.find_one.call_args.args[1]  # a última chamada = leitura final
    assert proj.get("mfa_secret") == 0
    assert proj.get("mfa_pending_secret") == 0
    assert proj.get("mfa_backup_codes") == 0
