"""
Regression tests for iteration 26 (post production-readiness audit fixes).
Validates:
- Auth flows (login, logout, /me, rate limit)
- Invite-only flow (admin invite, validate, setup-account)
- Password recovery (forgot, reset)
- Notifications (list, unread count, read, SSE token)
- Mural (CRUD, like, pin, pending, delete)
- Events (list, featured)
- Finances (transactions list/create, DRE PDF after var removal fix)
- Projects (list)
- Activity feed (recent - after var removal fix)
- Personal report
- Gallery (albums)
- CORS / rate limiting sanity
"""
import os
import time
import secrets
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://traffic-portal-2.preview.emergentagent.com").rstrip("/")
ADMIN = {"email": "admin@controlador.cv", "password": "admin123"}
FIN = {"email": "financeiro@controlador.cv", "password": "fin123"}
SOCIO = {"email": "socio1@controlador.cv", "password": "socio123"}


# ----------------- fixtures -----------------
@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=10)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def fin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=FIN, timeout=10)
    if r.status_code != 200:
        pytest.skip(f"Financeiro login failed: {r.status_code}")
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def socio_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=SOCIO, timeout=10)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def hdr(tok):
    return {"Authorization": f"Bearer {tok}"}


# ----------------- AUTH -----------------
class TestAuth:
    def test_login_admin(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert "access_token" in d
        assert d["user"]["role"] == "admin"
        assert d["user"]["email"] == ADMIN["email"]

    def test_login_socio(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json=SOCIO, timeout=10)
        assert r.status_code == 200
        assert r.json()["user"]["role"] in ("socio", "member")

    def test_login_invalid(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": "x@x.com", "password": "wrong"}, timeout=10)
        assert r.status_code in (400, 401)

    def test_me_endpoint(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=hdr(admin_token), timeout=10)
        assert r.status_code == 200
        assert r.json()["email"] == ADMIN["email"]

    def test_me_unauth(self):
        r = requests.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert r.status_code in (401, 403)

    def test_no_public_register(self):
        # Public registration must NOT exist
        r = requests.post(f"{BASE_URL}/api/auth/register",
                          json={"email": "a@b.cv", "password": "abcdef"}, timeout=10)
        assert r.status_code in (404, 405)


# ----------------- INVITE FLOW -----------------
class TestInvite:
    def test_admin_can_invite(self, admin_token):
        rand = secrets.token_hex(4)
        payload = {
            "name": f"TEST_invitee_{rand}",
            "email": f"TEST_invitee_{rand}@controlador.cv",
            "role": "socio",
            "cargo": "Sócio",
        }
        r = requests.post(f"{BASE_URL}/api/admin/invite",
                          json=payload, headers=hdr(admin_token), timeout=15)
        assert r.status_code in (200, 201), r.text
        d = r.json()
        # Should return either invite_token or setup_url
        assert "invite_token" in d or "setup_url" in d or "user" in d
        # Save token for next test
        token = d.get("invite_token") or (d.get("setup_url", "").split("token=")[-1] if "setup_url" in d else None)
        TestInvite.last_token = token
        TestInvite.last_email = payload["email"]

    def test_socio_cannot_invite(self, socio_token):
        r = requests.post(f"{BASE_URL}/api/admin/invite",
                          json={"name": "X", "email": "x@x.cv", "role": "socio"},
                          headers=hdr(socio_token), timeout=10)
        assert r.status_code == 403

    def test_validate_invite(self, admin_token):
        token = getattr(TestInvite, "last_token", None)
        if not token:
            pytest.skip("No invite token available")
        r = requests.get(f"{BASE_URL}/api/auth/invite/validate",
                         params={"token": token}, timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "email" in d
        assert "name" in d

    def test_validate_invalid_invite(self):
        r = requests.get(f"{BASE_URL}/api/auth/invite/validate",
                         params={"token": "invalid_xxx"}, timeout=10)
        assert r.status_code in (400, 404)

    def test_setup_account(self):
        token = getattr(TestInvite, "last_token", None)
        if not token:
            pytest.skip("No invite token available")
        r = requests.post(f"{BASE_URL}/api/auth/setup-account",
                          json={"token": token, "password": "TestPass123!"},
                          timeout=15)
        assert r.status_code == 200, r.text
        assert "access_token" in r.json()


# ----------------- PASSWORD RECOVERY -----------------
class TestPasswordRecovery:
    def test_forgot_password_unknown(self):
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": "noexist_xyz@nowhere.cv"}, timeout=10)
        # Endpoint should exist and respond (not 404). 200 generic or 404 if it discloses
        assert r.status_code in (200, 404)

    def test_forgot_password_known(self):
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": ADMIN["email"]}, timeout=15)
        assert r.status_code == 200

    def test_reset_password_invalid(self):
        r = requests.post(f"{BASE_URL}/api/auth/reset-password",
                          json={"token": "invalid_xxx", "password": "abcdef12"}, timeout=10)
        assert r.status_code in (400, 404)


# ----------------- NOTIFICATIONS -----------------
class TestNotifications:
    def test_list(self, socio_token):
        r = requests.get(f"{BASE_URL}/api/notifications",
                         headers=hdr(socio_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))

    def test_unread_count(self, socio_token):
        r = requests.get(f"{BASE_URL}/api/notifications/unread/count",
                         headers=hdr(socio_token), timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert "count" in d or "unread" in d or isinstance(d, int)

    def test_sse_with_token_query(self, socio_token):
        # Just verify endpoint accepts token via query, do not stream long
        r = requests.get(f"{BASE_URL}/api/notifications/stream",
                         params={"token": socio_token},
                         timeout=3, stream=True)
        # 200 OK headers should arrive even for SSE
        assert r.status_code == 200
        r.close()


# ----------------- MURAL -----------------
class TestWall:
    def test_admin_create_auto_approved(self, admin_token):
        r = requests.post(f"{BASE_URL}/api/wall",
                          json={"content": "TEST_admin_post regression",
                                "category": "geral"},
                          headers=hdr(admin_token), timeout=10)
        assert r.status_code in (200, 201), r.text
        d = r.json()
        TestWall.admin_post_id = d.get("id")
        assert d.get("status") == "approved"

    def test_socio_create_pending(self, socio_token):
        r = requests.post(f"{BASE_URL}/api/wall",
                          json={"content": "TEST_socio_post regression",
                                "category": "geral"},
                          headers=hdr(socio_token), timeout=10)
        assert r.status_code in (200, 201), r.text
        d = r.json()
        TestWall.socio_post_id = d.get("id")
        assert d.get("status") == "pending"

    def test_get_wall(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/wall", headers=hdr(admin_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_pending_admin_only(self, admin_token, socio_token):
        r1 = requests.get(f"{BASE_URL}/api/wall/pending",
                          headers=hdr(admin_token), timeout=10)
        assert r1.status_code == 200
        r2 = requests.get(f"{BASE_URL}/api/wall/pending",
                          headers=hdr(socio_token), timeout=10)
        assert r2.status_code == 403

    def test_like(self, socio_token):
        pid = getattr(TestWall, "admin_post_id", None)
        if not pid:
            pytest.skip("No post id")
        r = requests.patch(f"{BASE_URL}/api/wall/{pid}/like",
                           headers=hdr(socio_token), timeout=10)
        assert r.status_code == 200

    def test_pin_admin(self, admin_token):
        pid = getattr(TestWall, "admin_post_id", None)
        if not pid:
            pytest.skip("No post id")
        r = requests.patch(f"{BASE_URL}/api/wall/{pid}/pin",
                           headers=hdr(admin_token), timeout=10)
        assert r.status_code == 200

    def test_delete(self, admin_token):
        for pid_attr in ("admin_post_id", "socio_post_id"):
            pid = getattr(TestWall, pid_attr, None)
            if pid:
                r = requests.delete(f"{BASE_URL}/api/wall/{pid}",
                                    headers=hdr(admin_token), timeout=10)
                assert r.status_code in (200, 204)


# ----------------- EVENTS -----------------
class TestEvents:
    def test_list_public(self):
        r = requests.get(f"{BASE_URL}/api/events", timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_featured_public(self):
        r = requests.get(f"{BASE_URL}/api/events/featured", timeout=10)
        assert r.status_code == 200


# ----------------- FINANCES (admin/financeiro) -----------------
class TestFinances:
    def test_list_transactions_admin(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/finances/transactions",
                         headers=hdr(admin_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_transactions_socio_forbidden(self, socio_token):
        r = requests.get(f"{BASE_URL}/api/finances/transactions",
                         headers=hdr(socio_token), timeout=10)
        assert r.status_code == 403

    def test_create_transaction(self, admin_token):
        payload = {
            "type": "income",
            "amount": 1000.0,
            "category": "quotas",
            "description": "TEST_regression_tx",
            "date": "2026-01-15",
        }
        r = requests.post(f"{BASE_URL}/api/finances/transactions",
                          json=payload, headers=hdr(admin_token), timeout=10)
        assert r.status_code in (200, 201), r.text
        TestFinances.tx_id = r.json().get("id")

    def test_dre_pdf_export(self, admin_token):
        # Critical test: PDF must still generate after cat_y variable removal
        r = requests.get(f"{BASE_URL}/api/finances/dre/pdf",
                         params={"year": 2026},
                         headers=hdr(admin_token), timeout=30)
        assert r.status_code == 200, f"PDF gen failed: {r.status_code} {r.text[:200]}"
        ct = r.headers.get("content-type", "")
        assert "pdf" in ct.lower(), f"Wrong content-type: {ct}"
        # Verify it's a real PDF
        assert r.content[:4] == b"%PDF", "Not a valid PDF file"
        assert len(r.content) > 1000, "PDF too small"


# ----------------- PROJECTS -----------------
class TestProjects:
    def test_list(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/projects",
                         headers=hdr(admin_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ----------------- ACTIVITY FEED -----------------
class TestActivity:
    def test_recent_admin(self, admin_token):
        # Critical: after is_admin var removal
        r = requests.get(f"{BASE_URL}/api/activity/recent",
                         headers=hdr(admin_token), timeout=10)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_recent_socio(self, socio_token):
        r = requests.get(f"{BASE_URL}/api/activity/recent",
                         headers=hdr(socio_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ----------------- PERSONAL REPORT -----------------
class TestReport:
    def test_personal(self, socio_token):
        r = requests.get(f"{BASE_URL}/api/report/personal",
                         headers=hdr(socio_token), timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, dict)


# ----------------- GALLERY -----------------
class TestGallery:
    def test_albums(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/gallery/albums",
                         headers=hdr(admin_token), timeout=10)
        assert r.status_code == 200


# ----------------- RATE LIMIT SANITY -----------------
class TestRateLimit:
    def test_login_rate_limit(self):
        # 10/min on /auth/login - send 12 quick invalid requests
        codes = []
        for _ in range(12):
            r = requests.post(f"{BASE_URL}/api/auth/login",
                              json={"email": "ratelimit_test@x.cv", "password": "x"},
                              timeout=5)
            codes.append(r.status_code)
        # We expect at least one 429 among the responses
        assert 429 in codes, f"No 429 received in 12 attempts: {codes}"


# ----------------- CORS -----------------
class TestCORS:
    def test_cors_no_wildcard_with_origin(self):
        r = requests.options(f"{BASE_URL}/api/auth/login",
                             headers={
                                 "Origin": "https://random-evil.example.com",
                                 "Access-Control-Request-Method": "POST",
                             }, timeout=10)
        # Either 200 or 400; check ACAO is not '*'
        acao = r.headers.get("Access-Control-Allow-Origin", "")
        # If wildcard present, system isn't restricting CORS
        # Note: many setups still respond with the origin echoed; '*' is the bad case
        assert acao != "*", f"CORS wildcard detected: {acao}"


# ----------------- CLEANUP -----------------
@pytest.fixture(scope="module", autouse=True)
def _cleanup_after(admin_token):
    yield
    # Best-effort cleanup TEST_ posts, transactions, invitees
    try:
        # Wall
        r = requests.get(f"{BASE_URL}/api/wall", headers=hdr(admin_token), timeout=10)
        if r.status_code == 200:
            for p in r.json():
                if "TEST_" in p.get("content", ""):
                    requests.delete(f"{BASE_URL}/api/wall/{p['id']}",
                                    headers=hdr(admin_token), timeout=5)
    except Exception:
        pass
    try:
        tx_id = getattr(TestFinances, "tx_id", None)
        if tx_id:
            requests.delete(f"{BASE_URL}/api/finances/transactions/{tx_id}",
                            headers=hdr(admin_token), timeout=5)
    except Exception:
        pass
