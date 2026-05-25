# Plano — Segurança F0: Testes de Regressão

> **Para workers agênticos:** SUB-SKILL OBRIGATÓRIA — usar
> `superpowers:subagent-driven-development` (recomendado) ou
> `superpowers:executing-plans` para executar tarefa-a-tarefa. Os passos usam
> checkbox (`- [ ]`).

**Goal:** Escrever os 6 ficheiros de teste de regressão de segurança em falta
(§F0 de `tasks/spec-verificacao-seguranca-saas.md`), provando que os controlos
de segurança **já existentes** funcionam — sem alterar comportamento.

**Architecture:** Só `backend/tests/`. Estilo **unit in-process** (sem `import
requests`), padrão dominante do projeto. Três técnicas, conforme o controlo:
1. **Middleware** (headers, CSRF) → mini-app `FastAPI` com **só o middleware sob
   teste** montado + `TestClient` (sem `with` → sem startup/DB). As classes
   (`SecurityHeadersMiddleware`, `CSRFOriginCheckMiddleware`) importam-se de
   `server`.
2. **Rotas com DB** (IDOR, lockout) → chamada **direta à função de rota** com
   `mock_db` + `pytest.raises(HTTPException)`.
3. **Rate-limit** → `TestClient(app)` sem `with` + `mock_db` + limiter **ativo**.
4. **Funções de defesa puras** (SQLi) → `_WhereBuilder` e `_safe_search_regex`
   chamadas diretamente.

**Tech Stack:** pytest (`asyncio_mode=auto`), `fastapi.testclient.TestClient`,
fixtures de `tests/conftest.py` (`mock_db`, `socio_user`, role factories).

> **Inversão TDD:** são testes sobre código existente → cada teste deve ficar
> **VERDE imediatamente** (prova o controlo). VERMELHO = bug no teste OU
> vulnerabilidade real (parar e investigar; é um achado, não "implementar").

---

## Factos do código (verificados — usar verbatim)

- **Lockout**: `backend/helpers.py` → `LOCKOUT_THRESHOLD = 5`,
  `LOCKOUT_WINDOW_MINUTES = 15`; coleção **`login_attempts`** (NÃO
  `failed_logins`). Funções: `record_failed_login(email, ip=None)`,
  `reset_failed_logins(email)`, `is_account_locked(email) -> Optional[datetime]`.
  Login (`routes/auth_routes.py:50`) → `is_account_locked` ANTES do bcrypt; se
  bloqueado → **HTTP 423**.
- **Login**: `async def login(request: Request, response: Response, credentials: UserLogin)`,
  decorado `@limiter.limit("10/minute")`. `limiter` é instância local em
  `routes/auth_routes.py` (`Limiter(key_func=get_remote_address)`).
- **Middleware headers** (`server.py:24`): `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`,
  `Permissions-Policy`, CSP (omitido em `/docs|/redoc|/openapi.json`), HSTS só
  se `os.environ["ENVIRONMENT"] == "production"` (lido em runtime no `dispatch`).
- **Middleware CSRF** (`server.py:65`): só atua em métodos unsafe **com** cookie
  `accta_session` E `allowed_origins` não-vazio (com `CORS_ORIGINS="*"` →
  no-op). Origin não-permitido → 403; sem Origin/Referer (com cookie) → 403.
  `COOKIE_NAME = "accta_session"` (de `auth`).
- **`get_current_user`** devolve `models.User`; ao chamar rotas diretamente,
  passa-se `current_user=<fixture>` por keyword.
- **IDOR**:
  - `routes/notifications.py`: `get_notifications(skip, limit, type_filter, unread_only, current_user)` → `find({"user_id": current_user.id})`; `mark_notification_read(notification_id, current_user)` → `update_one({"id":…, "user_id": current_user.id})`; `delete_notification(notification_id, current_user)` → `delete_one({"id":…, "user_id": current_user.id})`, 404 se `deleted_count==0`.
  - `routes/projects.py`: `delete_comment(project_id, comment_id, current_user)` → 403 se `comment["user_id"] != current_user.id and role != "admin"`; `delete_expense`/`delete_milestone` → 403 se `not can_manage_project(user, project)` (`admin OR created_by OR responsible_id`).
  - `routes/wall.py`: `delete_wall_post(post_id, current_user)` → 403 se `not has_role_or_privilege(user, ("admin","moderador"), "moderate_content") and user.id != post["user_id"]`.
  - `routes/gallery.py`: `get_gallery_photos(album_id, status, current_user)` → não-admin força `query["status"]="approved"` (ignora `status` do cliente).
  - **Eleições**: NÃO existem endpoints de leitura de cédula/recibo → sem superfície IDOR (proteção arquitetural). Documentar, não testar.
- **SQLi**: `database._WhereBuilder()` → `.build(filt) -> str`; valores via
  `_ph()` (placeholders `$1,$2,…` em `self.params`); chave jsonb escapada em
  `_lit` (`'` → `''`). `routes/finances._safe_search_regex(s)` →
  `re.escape(s.strip()[:100])`.
- **conftest `mock_db`** pré-liga ~24 coleções (inclui `notifications`,
  `projects`, `wall_posts`, `gallery_photos`, `audit_logs`, `users`,
  `failed_logins`) — mas **NÃO** `login_attempts`, `project_comments`,
  `project_expenses`, `project_milestones` → ligar in-test.

---

## File Structure

| Ficheiro (criar) | Controlo provado |
|---|---|
| `backend/tests/test_security_headers.py` | §7 headers + CSP + HSTS |
| `backend/tests/test_csrf_middleware.py` | §5.3 CSRF Origin-check |
| `backend/tests/test_rate_limit.py` | §4 rate-limit 10/min no login |
| `backend/tests/test_lockout_integration.py` | §4 lockout 5/15min → 423 |
| `backend/tests/test_idor.py` | §6.2 IDOR ≥8 pares |
| `backend/tests/test_sql_injection_fuzz.py` | §5.1 parametrização + ReDoS |

---

### Task 1: test_security_headers.py

**Files:**
- Create: `backend/tests/test_security_headers.py`

- [ ] **Step 1: Escrever o ficheiro completo**

```python
"""Regressão de segurança — headers HTTP (§7 de spec-verificacao-seguranca-saas).

Prova que SecurityHeadersMiddleware injeta os headers OWASP esperados, que o
CSP é omitido em /openapi.json, e que HSTS só aparece em produção. Testa o
middleware isolado (mini-app) → sem DB/startup.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server import SecurityHeadersMiddleware

pytestmark = pytest.mark.unit


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/x")
    async def _x():
        return {"ok": True}

    return app


def test_base_security_headers_present():
    r = TestClient(_app()).get("/x")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "geolocation=(self)" in r.headers["Permissions-Policy"]
    assert "camera=()" in r.headers["Permissions-Policy"]


def test_csp_present_and_restrictive_on_api():
    csp = TestClient(_app()).get("/x").headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'self'" in csp


def test_csp_absent_on_openapi():
    # FastAPI serve /openapi.json por defeito; o middleware exclui esse caminho.
    r = TestClient(_app()).get("/openapi.json")
    assert r.status_code == 200
    assert "Content-Security-Policy" not in r.headers


def test_hsts_only_in_production(monkeypatch):
    client = TestClient(_app())
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    assert "Strict-Transport-Security" not in client.get("/x").headers
    monkeypatch.setenv("ENVIRONMENT", "production")
    hsts = client.get("/x").headers["Strict-Transport-Security"]
    assert "max-age=31536000" in hsts
    assert "includeSubDomains" in hsts
```

- [ ] **Step 2: Correr e confirmar VERDE**

Run: `cd backend && pytest tests/test_security_headers.py -v`
Expected: 4 passed (controlos confirmados).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_security_headers.py
git commit -m "test(seguranca): regressao de security headers + CSP + HSTS (F0 §7)"
```

---

### Task 2: test_csrf_middleware.py

**Files:**
- Create: `backend/tests/test_csrf_middleware.py`

- [ ] **Step 1: Escrever o ficheiro completo**

```python
"""Regressão CSRF — CSRFOriginCheckMiddleware (§5.3).

Com cookie + Origin não-permitido → 403; com cookie + sem Origin/Referer →
403; com cookie + Origin permitido (ou Referer) → passa; sem cookie (Bearer)
→ passa mesmo com Origin hostil. Instancia o middleware com origens
explícitas (com CORS=* o check é no-op por design).
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth import COOKIE_NAME
from server import CSRFOriginCheckMiddleware

pytestmark = pytest.mark.unit

ALLOWED = "https://app.accta.cv"


def _client() -> TestClient:
    app = FastAPI()
    app.add_middleware(CSRFOriginCheckMiddleware, allowed_origins=[ALLOWED])

    @app.post("/x")
    async def _x():
        return {"ok": True}

    return TestClient(app)


def test_cookie_plus_bad_origin_blocked():
    c = _client()
    c.cookies.set(COOKIE_NAME, "fake-session")
    r = c.post("/x", headers={"Origin": "https://attacker.com"})
    assert r.status_code == 403
    assert "CSRF" in r.json()["detail"]


def test_cookie_without_origin_or_referer_blocked():
    c = _client()
    c.cookies.set(COOKIE_NAME, "fake-session")
    r = c.post("/x")
    assert r.status_code == 403


def test_cookie_plus_allowed_origin_passes():
    c = _client()
    c.cookies.set(COOKIE_NAME, "fake-session")
    r = c.post("/x", headers={"Origin": ALLOWED})
    assert r.status_code == 200


def test_referer_fallback_allowed_origin_passes():
    c = _client()
    c.cookies.set(COOKIE_NAME, "fake-session")
    r = c.post("/x", headers={"Referer": f"{ALLOWED}/alguma/pagina"})
    assert r.status_code == 200


def test_no_cookie_bearer_client_bypasses_csrf():
    # Sem cookie → mesmo com Origin hostil passa (atacante não lê o Bearer).
    r = _client().post(
        "/x", headers={"Origin": "https://attacker.com", "Authorization": "Bearer xyz"}
    )
    assert r.status_code == 200
```

- [ ] **Step 2: Correr e confirmar VERDE**

Run: `cd backend && pytest tests/test_csrf_middleware.py -v`
Expected: 5 passed. (Se algum POST sem Origin não devolver 403, verificar se o
`TestClient`/httpx injeta um header `Origin` automático — se injetar, removê-lo
explicitamente com `headers={"Origin": ""}` não resolve; usar `c.post("/x",
headers={"origin": None})` não é válido. Nesse caso, o comportamento do
middleware mantém-se correto e o teste deve afirmar 403 quando Origin ausente —
confirmar lendo o request recebido.)

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_csrf_middleware.py
git commit -m "test(seguranca): regressao do middleware CSRF (Origin-check, F0 §5.3)"
```

---

### Task 3: test_rate_limit.py

**Files:**
- Create: `backend/tests/test_rate_limit.py`

- [ ] **Step 1: Escrever o ficheiro completo**

```python
"""Regressão rate-limit — slowapi em /api/auth/login (§4).

O 11.º POST a /api/auth/login dentro de 1 min → 429. TestClient sem `with`
(sem startup/DB) + mock_db (login não toca DB real) + limiter ATIVO (ao
contrário dos outros testes). Reset do storage do limiter para isolamento.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

import routes.auth_routes as auth_routes  # presente em sys.modules p/ mock_db
from server import app

pytestmark = pytest.mark.unit


def _reset_limiter():
    storage = getattr(auth_routes.limiter, "_storage", None)
    if storage is not None and hasattr(storage, "reset"):
        storage.reset()
    elif storage is not None and hasattr(storage, "storage"):
        storage.storage.clear()


@pytest.fixture
def reset_limiter():
    _reset_limiter()
    yield
    _reset_limiter()


def test_login_rate_limited_after_10(mock_db, reset_limiter):
    # login com utilizador inexistente → 401 a cada vez, até o 11.º → 429.
    mock_db.login_attempts = MagicMock()
    mock_db.login_attempts.count_documents = AsyncMock(return_value=0)
    mock_db.login_attempts.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    mock_db.users.find_one = AsyncMock(return_value=None)

    client = TestClient(app)  # sem `with` → sem startup/DB
    body = {"email": "x@accta.cv", "password": "errada"}
    codes = [client.post("/api/auth/login", json=body).status_code for _ in range(11)]
    assert codes[:10] == [401] * 10
    assert codes[10] == 429
```

- [ ] **Step 2: Correr e confirmar VERDE**

Run: `cd backend && pytest tests/test_rate_limit.py -v`
Expected: 1 passed. Se o reset do limiter falhar (atributo `_storage`
diferente na versão instalada de slowapi), inspecionar `dir(auth_routes.limiter)`
e ajustar `_reset_limiter()` para o atributo de storage correto (continua a ser
uma verificação de ambiente, não lógica).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_rate_limit.py
git commit -m "test(seguranca): regressao de rate-limit no login (429, F0 §4)"
```

---

### Task 4: test_lockout_integration.py

**Files:**
- Create: `backend/tests/test_lockout_integration.py`

- [ ] **Step 1: Escrever o ficheiro completo**

```python
"""Regressão lockout — máquina de estado + 423 no login (§4).

5 falhas na janela → bloqueado; fora da janela → desbloqueado;
reset_failed_logins limpa; login devolve 423 quando bloqueado. Usa um fake
stateful de `login_attempts` (a coleção real que helpers usa).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request

import helpers
import routes.auth_routes as auth_routes
from helpers import LOCKOUT_THRESHOLD, LOCKOUT_WINDOW_MINUTES
from models import UserLogin

pytestmark = pytest.mark.unit


class _FakeLoginAttempts:
    """Emula db.login_attempts com estado em memória (subset usado por helpers)."""

    def __init__(self):
        self.docs: list[dict] = []

    async def insert_one(self, doc):
        self.docs.append(dict(doc))

    async def delete_many(self, filt):
        email = filt["email"]
        before = len(self.docs)
        self.docs = [d for d in self.docs if d.get("email") != email]
        return type("R", (), {"deleted_count": before - len(self.docs)})()

    def _in_window(self, filt):
        email = filt["email"]
        gte = filt["attempted_at"]["$gte"]
        return [d for d in self.docs if d.get("email") == email and d["attempted_at"] >= gte]

    async def count_documents(self, filt):
        return len(self._in_window(filt))

    async def find_one(self, filt, sort=None):
        cands = self._in_window(filt)
        return min(cands, key=lambda d: d["attempted_at"]) if cands else None


@pytest.fixture
def fake_attempts(monkeypatch):
    fake = _FakeLoginAttempts()
    db = type("DB", (), {"login_attempts": fake})()
    monkeypatch.setattr(helpers, "db", db)
    return fake


@pytest.mark.asyncio
async def test_locks_after_threshold_failures(fake_attempts):
    email = "alvo@accta.cv"
    for _ in range(LOCKOUT_THRESHOLD - 1):
        await helpers.record_failed_login(email)
    assert await helpers.is_account_locked(email) is None  # 4 < 5
    await helpers.record_failed_login(email)  # 5.ª
    locked_until = await helpers.is_account_locked(email)
    assert locked_until is not None
    assert locked_until > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_unlocks_after_window(fake_attempts):
    email = "alvo@accta.cv"
    old = datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_WINDOW_MINUTES + 1)
    for _ in range(LOCKOUT_THRESHOLD):
        fake_attempts.docs.append({"email": email, "ip": None, "attempted_at": old})
    assert await helpers.is_account_locked(email) is None  # tudo fora da janela


@pytest.mark.asyncio
async def test_reset_clears_lockout(fake_attempts):
    email = "alvo@accta.cv"
    for _ in range(LOCKOUT_THRESHOLD):
        await helpers.record_failed_login(email)
    assert await helpers.is_account_locked(email) is not None
    await helpers.reset_failed_logins(email)
    assert await helpers.is_account_locked(email) is None


@pytest.mark.asyncio
async def test_login_route_returns_423_when_locked(mock_db, monkeypatch):
    # Login wireado ao lockout: conta bloqueada → 423 (limiter desativado para
    # poder chamar a função decorada diretamente — ver CLAUDE.md).
    monkeypatch.setattr(auth_routes.limiter, "enabled", False)
    locked_dt = datetime.now(timezone.utc) + timedelta(minutes=10)
    monkeypatch.setattr(auth_routes, "is_account_locked", AsyncMock(return_value=locked_dt))

    scope = {
        "type": "http", "method": "POST", "path": "/api/auth/login",
        "headers": [], "client": ("test", 1), "query_string": b"",
    }
    with pytest.raises(HTTPException) as exc:
        await auth_routes.login(
            Request(scope), Response(), UserLogin(email="x@accta.cv", password="y")
        )
    assert exc.value.status_code == 423
```

- [ ] **Step 2: Correr e confirmar VERDE**

Run: `cd backend && pytest tests/test_lockout_integration.py -v`
Expected: 4 passed. Se `UserLogin` tiver nomes de campo diferentes de
`email`/`password`, ler `models.py::UserLogin` e ajustar. Se
`auth_routes.is_account_locked` não existir como atributo do módulo (import
diferente), confirmar a linha de import no topo de `auth_routes.py` e fazer
patch do alvo correto.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_lockout_integration.py
git commit -m "test(seguranca): regressao de lockout (5/15min -> 423, F0 §4)"
```

---

### Task 5: test_idor.py

**Files:**
- Create: `backend/tests/test_idor.py`

- [ ] **Step 1: Escrever o ficheiro completo**

```python
"""Regressão IDOR — B não acede a recursos de A (§6.2).

≥8 pares recurso×verbo via chamada direta às funções de rota com mock_db.
NOTA: eleições não têm endpoint de leitura de cédula/recibo — proteção
arquitetural (ballots sem user_id; recibos por HMAC voter_hash nunca
expostos), logo sem superfície IDOR a testar aí.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

import routes.gallery as gallery
import routes.notifications as notifications
import routes.projects as projects
import routes.wall as wall

pytestmark = pytest.mark.unit


# ---- notifications: scoping por user_id ------------------------------------
@pytest.mark.asyncio
async def test_delete_notification_scoped_to_owner(mock_db, socio_user):
    mock_db.notifications.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
    with pytest.raises(HTTPException) as exc:
        await notifications.delete_notification("notif-de-A", current_user=socio_user)
    assert exc.value.status_code == 404
    assert mock_db.notifications.delete_one.call_args.args[0]["user_id"] == socio_user.id


@pytest.mark.asyncio
async def test_mark_read_scoped_to_owner(mock_db, socio_user):
    mock_db.notifications.update_one = AsyncMock(return_value=MagicMock(modified_count=0))
    await notifications.mark_notification_read("notif-de-A", current_user=socio_user)
    assert mock_db.notifications.update_one.call_args.args[0]["user_id"] == socio_user.id


@pytest.mark.asyncio
async def test_list_notifications_scoped_to_caller(mock_db, socio_user):
    await notifications.get_notifications(
        skip=0, limit=50, type_filter=None, unread_only=False, current_user=socio_user
    )
    assert mock_db.notifications.find.call_args.args[0]["user_id"] == socio_user.id


# ---- projetos --------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_comment_of_other_forbidden(mock_db, socio_user):
    mock_db.project_comments = MagicMock()
    mock_db.project_comments.find_one = AsyncMock(
        return_value={"id": "c1", "project_id": "p1", "user_id": "outro-user"}
    )
    mock_db.project_comments.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    with pytest.raises(HTTPException) as exc:
        await projects.delete_comment("p1", "c1", current_user=socio_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_expense_non_manager_forbidden(mock_db, socio_user):
    mock_db.projects.find_one = AsyncMock(
        return_value={"id": "p1", "created_by": "dono-A", "responsible_id": "dono-A"}
    )
    mock_db.project_expenses = MagicMock()
    mock_db.project_expenses.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    with pytest.raises(HTTPException) as exc:
        await projects.delete_expense("p1", "e1", current_user=socio_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_milestone_non_manager_forbidden(mock_db, socio_user):
    mock_db.projects.find_one = AsyncMock(
        return_value={"id": "p1", "created_by": "dono-A", "responsible_id": "dono-A"}
    )
    mock_db.project_milestones = MagicMock()
    mock_db.project_milestones.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    with pytest.raises(HTTPException) as exc:
        await projects.delete_milestone("p1", "m1", current_user=socio_user)
    assert exc.value.status_code == 403


# ---- mural -----------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_wall_post_of_other_forbidden(mock_db, socio_user):
    mock_db.wall_posts.find_one = AsyncMock(return_value={"id": "w1", "user_id": "outro-user"})
    with pytest.raises(HTTPException) as exc:
        await wall.delete_wall_post("w1", current_user=socio_user)
    assert exc.value.status_code == 403


# ---- galeria: não-admin só vê aprovadas ------------------------------------
@pytest.mark.asyncio
async def test_non_admin_cannot_query_pending_photos(mock_db, socio_user):
    await gallery.get_gallery_photos(album_id=None, status="pending", current_user=socio_user)
    assert mock_db.gallery_photos.find.call_args.args[0]["status"] == "approved"
```

- [ ] **Step 2: Correr e confirmar VERDE**

Run: `cd backend && pytest tests/test_idor.py -v`
Expected: 8 passed. Se alguma assinatura de rota diferir (nº/ordem de
parâmetros), ler a função em `routes/<modulo>.py` e ajustar a chamada direta
(manter `current_user=` por keyword). Se `get_notifications` rejeitar
`type_filter=` (nome do parâmetro), usar o nome real do parâmetro Python.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_idor.py
git commit -m "test(seguranca): regressao IDOR (8 pares recurso x verbo, F0 §6.2)"
```

---

### Task 6: test_sql_injection_fuzz.py

**Files:**
- Create: `backend/tests/test_sql_injection_fuzz.py`

- [ ] **Step 1: Escrever o ficheiro completo**

```python
"""Regressão SQLi — payloads tratados como literais parametrizados (§5.1).

(a) _WhereBuilder coloca valores de filtro em parâmetros ($1,$2,…), nunca
interpolados no SQL; (b) _safe_search_regex escapa metacaracteres e trunca a
100 chars (anti-ReDoS). Sem DB — testa as funções de defesa diretamente.
"""
from __future__ import annotations

import re

import pytest

from database import _WhereBuilder
from routes.finances import _safe_search_regex

pytestmark = pytest.mark.unit

PAYLOADS = [
    "' OR 1=1 --",
    "'; DROP TABLE users; --",
    "1) OR ('a'='a",
    "admin'--",
    '" OR ""="',
]


@pytest.mark.parametrize("payload", PAYLOADS)
def test_equality_filter_value_is_parametrized(payload):
    wb = _WhereBuilder()
    sql = wb.build({"email": payload})
    assert any(payload in str(p) for p in wb.params)  # viaja como parâmetro
    assert payload not in sql                          # nunca no texto SQL
    assert "DROP TABLE" not in sql.upper()
    assert "$1" in sql                                 # placeholders posicionais


@pytest.mark.parametrize("payload", PAYLOADS)
def test_regex_filter_value_is_parametrized(payload):
    wb = _WhereBuilder()
    sql = wb.build({"description": {"$regex": payload, "$options": "i"}})
    assert payload in wb.params
    assert payload not in sql
    assert "~*" in sql  # regex case-insensitive → operador ~*, valor em $1


def test_jsonb_key_is_quote_escaped():
    # _lit escapa aspas simples na chave jsonb (defesa em profundidade).
    sql = _WhereBuilder().build({"ev'il": "x"})
    assert "ev''il" in sql


def test_safe_search_regex_escapes_metachars():
    assert _safe_search_regex(".*+[](){}") == re.escape(".*+[](){}")
    assert _safe_search_regex("'; DROP--") == re.escape("'; DROP--")


def test_safe_search_regex_truncates_before_escape():
    out = _safe_search_regex("a" * 250)
    assert out == "a" * 100  # trunca o bruto a 100 antes de escapar
```

- [ ] **Step 2: Correr e confirmar VERDE**

Run: `cd backend && pytest tests/test_sql_injection_fuzz.py -v`
Expected: 13 passed (5+5 parametrizados + 3). Se `_to_scalar_text` transformar
o valor (raro para `str`), a asserção `any(payload in str(p) …)` continua a
cobrir; ajustar só se `_WhereBuilder` mudou de API.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_sql_injection_fuzz.py
git commit -m "test(seguranca): regressao SQLi (parametrizacao + ReDoS, F0 §5.1)"
```

---

## Verificação final (após as 6 tarefas)

- [ ] **Suite completa verde** (sem regressões noutros testes):
  `cd backend && pytest tests/test_security_headers.py tests/test_csrf_middleware.py tests/test_rate_limit.py tests/test_lockout_integration.py tests/test_idor.py tests/test_sql_injection_fuzz.py -v`
- [ ] **Lint**: `cd backend && ruff check tests/test_security_headers.py tests/test_csrf_middleware.py tests/test_rate_limit.py tests/test_lockout_integration.py tests/test_idor.py tests/test_sql_injection_fuzz.py` → 0 erros (imports no topo — E402 NÃO está nos per-file-ignores de `tests/*`).
- [ ] **Atualizar o spec**: marcar em `tasks/spec-verificacao-seguranca-saas.md`
  §15 Review o checkbox "F0 concluída" e a checklist §13 P0 dos 6 testes novos.
- [ ] Não tocar comportamento de produção (só `tests/` + uma linha de review no
  spec).

## Review (preencher ao concluir)

- _(resumo: nº de testes verdes, achados se algum teste vier VERMELHO, e
  confirmação de que nenhum controlo existente foi alterado)_
