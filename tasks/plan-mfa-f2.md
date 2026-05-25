# Plano — MFA (TOTP) · F2 backend

> **Para workers agênticos:** SUB-SKILL OBRIGATÓRIA — usar
> `superpowers:subagent-driven-development` para executar tarefa-a-tarefa.
> Passos com checkbox (`- [ ]`).

**Goal:** Implementar MFA TOTP no backend (enroll/verify/disable/status + gate no
login + auto-enrolment sinalizado) conforme `tasks/spec-mfa-f2.md`.

**Architecture:** Novo módulo `backend/mfa.py` (cripto Fernet + TOTP via `pyotp` +
backup codes + política de obrigatoriedade). Endpoints em `routes/auth_routes.py`
sob `/api/auth/mfa/*` + alteração mínima no `POST /auth/login`. Campos novos só no
`doc` jsonb (segredos nunca em respostas — `User` tem `extra="ignore"`).

**Tech Stack:** FastAPI, `pyotp` (novo), `cryptography` (já transitivo via
`python-jose[cryptography]`), pytest (`asyncio_mode=auto`), `mock_db`.

> **TDD real** (código novo): por tarefa — escrever teste → correr (falha) →
> implementar → correr (passa) → commit. `test_mfa.py` cresce incrementalmente.

---

## Decisões fechadas (do spec §0)
- MFA obrigatório p/ `admin`+`financeiro`; opt-in p/ `moderador`+`socio`.
- Segredo TOTP cifrado em repouso (Fernet, chave derivada do `SECRET_KEY`).
- Âmbito = backend (frontend é PR2).

## File Structure
| Ficheiro | Ação |
|---|---|
| `backend/requirements.txt` | + `pyotp==2.9.0` |
| `backend/mfa.py` | **criar** — cripto/TOTP/backup/política |
| `backend/models.py` | + `mfa_enabled`, `otp`, `mfa_setup_required`, `MfaVerifyRequest`, `MfaDisableRequest` |
| `backend/routes/auth_routes.py` | + 4 endpoints MFA + gate no login |
| `backend/tests/test_mfa.py` | **criar** — cresce nas Tasks 1-4 |

---

### Task 1: Dependência + `mfa.py` + testes das primitivas

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/mfa.py`
- Create: `backend/tests/test_mfa.py`

- [ ] **Step 1: Garantir dependências**

Acrescentar a `backend/requirements.txt` (após a linha `qrcode==7.4.2`):
```
pyotp==2.9.0
```
`cryptography` já é fornecido por `python-jose[cryptography]==3.5.0` (transitivo).
Verificar no env: `cd backend && python -c "import pyotp; from cryptography.fernet import Fernet; print('ok')"`.
Se faltar: `pip install pyotp==2.9.0` (e, se `cryptography` não importar, `pip install cryptography`).

- [ ] **Step 2: Criar `backend/mfa.py`**

```python
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
```

- [ ] **Step 3: Escrever os testes das primitivas em `backend/tests/test_mfa.py`**

```python
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
```

- [ ] **Step 4: Correr e confirmar VERDE**

Run: `cd backend && pytest tests/test_mfa.py -v` → 7 passed.
Run: `cd backend && ruff check mfa.py tests/test_mfa.py` → limpo.

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/mfa.py backend/tests/test_mfa.py
git commit -m "feat(mfa): modulo mfa.py (Fernet+TOTP+backup codes) + testes (F2)"
```

---

### Task 2: Modelos aditivos

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/tests/test_mfa.py`

- [ ] **Step 1: Escrever os testes dos modelos (append em `test_mfa.py`)**

```python
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
```

- [ ] **Step 2: Correr e confirmar que FALHA**

Run: `cd backend && pytest tests/test_mfa.py -k "mfa_enabled or otp_optional or setup_required or drops_mfa or request_models" -v`
Expected: FAIL (campos/modelos ainda não existem).

- [ ] **Step 3: Implementar em `backend/models.py`**

Em `UserBase`, acrescentar (após `email_opt_out_informativos`):
```python
    # MFA TOTP (spec-mfa-f2). Só a flag é exposta; segredo/backup vivem no doc
    # jsonb e nunca em modelos (User tem extra="ignore").
    mfa_enabled: bool = False
```

Em `UserLogin`, acrescentar o campo `otp`:
```python
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    otp: Optional[str] = None
```

Em `Token`, acrescentar a flag:
```python
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User
    mfa_setup_required: bool = False
```

Acrescentar os request models (junto aos outros de auth, ex. após `Token`):
```python
class MfaVerifyRequest(BaseModel):
    otp: str


class MfaDisableRequest(BaseModel):
    password: str
```

- [ ] **Step 4: Correr e confirmar VERDE**

Run: `cd backend && pytest tests/test_mfa.py -v` → 12 passed.
Run: `cd backend && ruff check models.py` → limpo.

- [ ] **Step 5: Commit**

```bash
git add backend/models.py backend/tests/test_mfa.py
git commit -m "feat(mfa): campos aditivos (mfa_enabled/otp/mfa_setup_required) + request models (F2)"
```

---

### Task 3: Endpoints `/auth/mfa/*`

**Files:**
- Modify: `backend/routes/auth_routes.py`
- Modify: `backend/tests/test_mfa.py`

- [ ] **Step 1: Escrever os testes dos endpoints (append em `test_mfa.py`)**

```python
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
```

- [ ] **Step 2: Correr e confirmar que FALHA** (endpoints ainda não existem)

Run: `cd backend && pytest tests/test_mfa.py -k "mfa_setup or mfa_verify or mfa_disable or mfa_status" -v` → FAIL/erros de atributo.

- [ ] **Step 3: Implementar os endpoints em `backend/routes/auth_routes.py`**

Acrescentar ao import de `models` os novos modelos (`MfaVerifyRequest`, `MfaDisableRequest`) e adicionar um import de `mfa` no topo do ficheiro:
```python
from mfa import (
    consume_backup_code,
    decrypt_secret,
    encrypt_secret,
    generate_backup_codes,
    generate_totp_secret,
    hash_backup_code,
    is_mfa_mandatory,
    provisioning_uri,
    verify_totp,
)
```

Adicionar os endpoints (ex. a seguir ao `logout`, antes de `registration-options`):
```python
@router.post("/mfa/setup")
@limiter.limit("5/minute")
async def mfa_setup(request: Request, current_user: User = Depends(get_current_user)):
    """Inicia enrolment: gera segredo TOTP, guarda-o cifrado como PENDING
    (não mexe no ativo) e devolve segredo + otpauth URI para o QR."""
    secret = generate_totp_secret()
    await db.users.update_one(
        {"id": current_user.id}, {"$set": {"mfa_pending_secret": encrypt_secret(secret)}}
    )
    await create_audit_log(current_user.id, "mfa_setup_initiated", request=request)
    return {"secret": secret, "otpauth_uri": provisioning_uri(secret, current_user.email)}


@router.post("/mfa/verify")
async def mfa_verify(data: MfaVerifyRequest, current_user: User = Depends(get_current_user)):
    """Confirma o primeiro OTP, ativa o MFA e devolve os backup codes (1x)."""
    doc = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    pending = (doc or {}).get("mfa_pending_secret")
    if not pending:
        raise HTTPException(status_code=400, detail="Inicie a configuracao de MFA primeiro")
    if not verify_totp(decrypt_secret(pending), data.otp):
        raise HTTPException(status_code=400, detail="Codigo invalido")
    codes = generate_backup_codes()
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "mfa_secret": pending,
                "mfa_enabled": True,
                "mfa_backup_codes": [hash_backup_code(c) for c in codes],
            },
            "$unset": {"mfa_pending_secret": ""},
        },
    )
    await create_audit_log(current_user.id, "mfa_enabled", request=None)
    return {"backup_codes": codes}


@router.post("/mfa/disable")
async def mfa_disable(data: MfaDisableRequest, current_user: User = Depends(get_current_user)):
    """Desativa MFA após re-autenticação por password."""
    doc = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    if not doc or not doc.get("password") or not verify_password(data.password, doc["password"]):
        raise HTTPException(status_code=403, detail="Password incorreta")
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {"mfa_enabled": False},
            "$unset": {"mfa_secret": "", "mfa_pending_secret": "", "mfa_backup_codes": ""},
        },
    )
    await create_audit_log(current_user.id, "mfa_disabled", request=None)
    return {"message": "MFA desativado"}


@router.get("/mfa/status")
async def mfa_status(current_user: User = Depends(get_current_user)):
    doc = await db.users.find_one({"id": current_user.id}, {"_id": 0}) or {}
    return {
        "enabled": bool(doc.get("mfa_enabled")),
        "mandatory": is_mfa_mandatory(current_user.role),
        "backup_codes_remaining": len(doc.get("mfa_backup_codes") or []),
    }
```

> Nota: `create_audit_log(..., request=None)` em verify/disable — confirmar a
> assinatura real de `create_audit_log` em `helpers.py`; se `request` for
> posicional/obrigatório, passar `request` adicionando-o à assinatura do
> endpoint (`request: Request`). O `mfa_setup` já recebe `request`.

- [ ] **Step 4: Correr e confirmar VERDE**

Run: `cd backend && pytest tests/test_mfa.py -v` → 18 passed.
Run: `cd backend && ruff check routes/auth_routes.py` → limpo.

- [ ] **Step 5: Commit**

```bash
git add backend/routes/auth_routes.py backend/tests/test_mfa.py
git commit -m "feat(mfa): endpoints setup/verify/disable/status (F2)"
```

---

### Task 4: Gate no login + auto-enrolment

**Files:**
- Modify: `backend/routes/auth_routes.py` (função `login`)
- Modify: `backend/tests/test_mfa.py`

- [ ] **Step 1: Escrever os testes do login (append em `test_mfa.py`)**

```python
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
    tok = await login_env.login(
        _login_request(), Response(), UserLogin(email="u@accta.cv", password="pw", otp="aaaa-bbbb")
    )
    assert tok.access_token
    consume_calls = [
        c for c in mock_db.users.update_one.call_args_list
        if "$set" in c.args[1] and "mfa_backup_codes" in c.args[1]["$set"]
    ]
    assert consume_calls, "esperava persistir a lista de backups reduzida"
    new_list = consume_calls[0].args[1]["$set"]["mfa_backup_codes"]
    assert hash_backup_code("aaaa-bbbb") not in new_list
    assert hash_backup_code("cccc-dddd") in new_list


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
```

- [ ] **Step 2: Correr e confirmar que FALHA** (gate ainda não existe)

Run: `cd backend && pytest tests/test_mfa.py -k "login_mfa or login_backup or login_admin or login_socio or login_response" -v` → FAIL.

- [ ] **Step 3: Implementar o gate em `backend/routes/auth_routes.py`**

Substituir o bloco de sucesso do `login` (de `# Login sucesso — limpa contador...`
até ao `return Token(...)`) por:
```python
    # MFA (spec-mfa-f2): se ativo, exige 2.º fator (TOTP ou backup code) antes
    # de emitir a sessão. OTP errado conta para o lockout (anti brute-force).
    if user_doc.get("mfa_enabled"):
        if not credentials.otp:
            await create_audit_log(user_doc["id"], "login_mfa_challenge", request=request)
            raise HTTPException(status_code=401, detail="mfa_required")
        new_backups = consume_backup_code(user_doc.get("mfa_backup_codes") or [], credentials.otp)
        if not verify_totp(decrypt_secret(user_doc["mfa_secret"]), credentials.otp) and new_backups is None:
            await record_failed_login(credentials.email, ip=request.client.host if request.client else None)
            await create_audit_log(user_doc["id"], "login_mfa_failed", request=request)
            raise HTTPException(status_code=401, detail="mfa_invalido")
        if new_backups is not None:
            await db.users.update_one({"id": user_doc["id"]}, {"$set": {"mfa_backup_codes": new_backups}})

    # Login sucesso — limpa contador de falhas para que utilizador legitimo
    # nao seja afectado por tentativas anteriores erradas/atacante.
    await reset_failed_logins(credentials.email)
    await db.users.update_one(
        {"email": credentials.email}, {"$set": {"last_login_at": datetime.now(timezone.utc).isoformat()}}
    )
    await create_audit_log(user_doc["id"], "login_success", request=request)

    mfa_setup_required = is_mfa_mandatory(user_doc["role"]) and not user_doc.get("mfa_enabled")
    for _k in ("password", "invite_token", "mfa_secret", "mfa_pending_secret", "mfa_backup_codes"):
        user_doc.pop(_k, None)

    user = User(**user_doc)
    token = create_access_token({"sub": user.id})
    set_session_cookie(response, token)
    return Token(access_token=token, token_type="bearer", user=user, mfa_setup_required=mfa_setup_required)
```

- [ ] **Step 4: Correr e confirmar VERDE**

Run: `cd backend && pytest tests/test_mfa.py -v` → 25 passed.
Run: `cd backend && ruff check routes/auth_routes.py` → limpo.

- [ ] **Step 5: Commit**

```bash
git add backend/routes/auth_routes.py backend/tests/test_mfa.py
git commit -m "feat(mfa): gate no login (TOTP/backup + lockout) + mfa_setup_required (F2)"
```

---

### Task 5: Verificação de regressão + fecho do spec

**Files:**
- Modify: `tasks/spec-mfa-f2.md` (secção Review)

- [ ] **Step 1: Suite de auth/segurança completa (sem regressão)**

Run:
```bash
cd backend && pytest tests/test_mfa.py tests/test_auth_routes.py tests/test_auth_hardening.py \
  tests/test_rate_limit.py tests/test_lockout_integration.py tests/test_permissions.py \
  tests/test_rbac_matrix.py tests/test_idor.py -q
```
Expected: tudo verde (o login alterado não pode partir os testes de auth/rate-limit/lockout existentes).

- [ ] **Step 2: Lint global dos ficheiros tocados**

Run: `cd backend && ruff check mfa.py models.py routes/auth_routes.py tests/test_mfa.py` → limpo.

- [ ] **Step 3: Fechar o spec** (`tasks/spec-mfa-f2.md` §11): marcar os checkboxes e
escrever a conclusão (nº de testes, nota de handoff p/ PR2 frontend).

- [ ] **Step 4: Commit**

```bash
git add tasks/spec-mfa-f2.md
git commit -m "docs(mfa): fechar spec F2 (backend) + handoff PR2"
```

---

## Verificação final (controlador)
- [ ] `test_mfa.py` 25 verdes; suite de auth/segurança sem regressão.
- [ ] `ruff` limpo; `pyotp` em requirements.
- [ ] Segredos não-expostos (teste dedicado verde).
- [ ] Revisão combinada spec+qualidade (opus) antes do PR → `develop`.
