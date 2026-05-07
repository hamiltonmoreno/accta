"""
CI smoke tests — run in-process with FastAPI TestClient.
These verify that the app starts correctly and core endpoints respond as expected.
They do NOT require a live deployed server.
"""


def test_api_root(client):
    r = client.get("/api/")
    assert r.status_code == 200
    assert r.json().get("message") == "ACCTA Portal API v1.0"


def test_health_endpoint(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "database" in data


def test_login_missing_fields(client):
    r = client.post("/api/auth/login", json={})
    assert r.status_code == 422


def test_login_invalid_credentials(client):
    r = client.post("/api/auth/login", json={"email": "nobody@controlador.cv", "password": "wrong"})
    assert r.status_code == 401


def test_protected_endpoint_no_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_protected_endpoint_bad_token(client):
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert r.status_code == 401


def test_public_documents_endpoint(client):
    r = client.get("/api/documents/public")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_contact_missing_fields(client):
    r = client.post("/api/contact", json={"name": "Test"})
    assert r.status_code == 422


def test_contact_message_too_short(client):
    r = client.post("/api/contact", json={
        "name": "Test",
        "email": "test@controlador.cv",
        "subject": "geral",
        "message": "curto",
    })
    assert r.status_code == 400
