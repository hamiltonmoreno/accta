"""
ACCTA Portal API Tests
Tests for authentication, invoices, polls, documents, benefits, wall, notifications
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SOCIO_EMAIL = "socio1@accta.cv"
SOCIO_PASSWORD = "socio123"
ADMIN_EMAIL = "admin@accta.cv"
ADMIN_PASSWORD = "admin123"

class TestHealthAndRoot:
    """Basic API health tests"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ API root responding: {data['message']}")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_socio_success(self):
        """Test socio login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == SOCIO_EMAIL
        assert data["user"]["role"] == "socio"
        print(f"✓ Socio login successful: {data['user']['name']}")
    
    def test_login_admin_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful: {data['user']['name']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected with 401")
    
    def test_auth_me_requires_token(self):
        """Test /auth/me requires authorization"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403]
        print("✓ /auth/me correctly requires authentication")


@pytest.fixture
def socio_token():
    """Get socio auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SOCIO_EMAIL,
        "password": SOCIO_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Socio authentication failed")

@pytest.fixture
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Admin authentication failed")

@pytest.fixture
def socio_headers(socio_token):
    """Headers with socio auth token"""
    return {"Authorization": f"Bearer {socio_token}"}

@pytest.fixture
def admin_headers(admin_token):
    """Headers with admin auth token"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestAuthMe:
    """Test authenticated user endpoint"""
    
    def test_auth_me_with_socio_token(self, socio_headers):
        """Test /auth/me returns user data for socio"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == SOCIO_EMAIL
        assert data["role"] == "socio"
        print(f"✓ Auth/me returns correct socio user: {data['name']}")
    
    def test_auth_me_with_admin_token(self, admin_headers):
        """Test /auth/me returns user data for admin"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        print(f"✓ Auth/me returns correct admin user: {data['name']}")


class TestInvoices:
    """Invoice endpoint tests"""
    
    def test_get_invoices_socio(self, socio_headers):
        """Socio can get their own invoices"""
        response = requests.get(f"{BASE_URL}/api/invoices", headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Socio invoices retrieved: {len(data)} invoices")
    
    def test_get_invoices_admin(self, admin_headers):
        """Admin can get all invoices"""
        response = requests.get(f"{BASE_URL}/api/invoices", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin invoices retrieved: {len(data)} invoices")
    
    def test_invoices_requires_auth(self):
        """Invoices endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/invoices")
        assert response.status_code in [401, 403]
        print("✓ Invoices correctly requires authentication")


class TestPolls:
    """Poll/Voting endpoint tests"""
    
    def test_get_polls(self, socio_headers):
        """Test getting polls list"""
        response = requests.get(f"{BASE_URL}/api/polls", headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Polls retrieved: {len(data)} polls")
        
        # Check poll structure if any polls exist
        if len(data) > 0:
            poll = data[0]
            assert "id" in poll
            assert "title" in poll
            assert "status" in poll
            print(f"  - Sample poll: {poll['title']} (status: {poll['status']})")
    
    def test_polls_requires_auth(self):
        """Polls endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/polls")
        assert response.status_code in [401, 403]
        print("✓ Polls correctly requires authentication")


class TestDocuments:
    """Document endpoint tests"""
    
    def test_get_documents(self, socio_headers):
        """Test getting documents list"""
        response = requests.get(f"{BASE_URL}/api/documents", headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Documents retrieved: {len(data)} documents")
    
    def test_documents_requires_auth(self):
        """Documents endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/documents")
        assert response.status_code in [401, 403]
        print("✓ Documents correctly requires authentication")


class TestBenefits:
    """Benefits endpoint tests"""
    
    def test_get_benefits(self, socio_headers):
        """Test getting benefits list"""
        response = requests.get(f"{BASE_URL}/api/benefits", headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Benefits retrieved: {len(data)} benefits")
    
    def test_benefits_requires_auth(self):
        """Benefits endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/benefits")
        assert response.status_code in [401, 403]
        print("✓ Benefits correctly requires authentication")


class TestWall:
    """Wall/Mural endpoint tests"""
    
    def test_get_wall_posts(self, socio_headers):
        """Test getting wall posts"""
        response = requests.get(f"{BASE_URL}/api/wall", headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Wall posts retrieved: {len(data)} posts")
    
    def test_wall_requires_auth(self):
        """Wall endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/wall")
        assert response.status_code in [401, 403]
        print("✓ Wall correctly requires authentication")


class TestNotifications:
    """Notifications endpoint tests"""
    
    def test_get_notifications(self, socio_headers):
        """Test getting notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Notifications retrieved: {len(data)} notifications")
    
    def test_get_unread_count(self, socio_headers):
        """Test getting unread notification count"""
        response = requests.get(f"{BASE_URL}/api/notifications/unread/count", headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        print(f"✓ Unread notifications count: {data['count']}")
    
    def test_notifications_requires_auth(self):
        """Notifications endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/notifications")
        assert response.status_code in [401, 403]
        print("✓ Notifications correctly requires authentication")


class TestAdminEndpoints:
    """Admin-only endpoint tests"""
    
    def test_get_users_admin(self, admin_headers):
        """Admin can get all users"""
        response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should have at least admin and socio
        print(f"✓ Admin retrieved {len(data)} users")
    
    def test_get_users_socio_forbidden(self, socio_headers):
        """Socio cannot get all users"""
        response = requests.get(f"{BASE_URL}/api/users", headers=socio_headers)
        assert response.status_code == 403
        print("✓ Socio correctly forbidden from users list")
    
    def test_get_audit_logs_admin(self, admin_headers):
        """Admin can get audit logs"""
        response = requests.get(f"{BASE_URL}/api/audit-logs", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin retrieved {len(data)} audit logs")
    
    def test_get_audit_logs_socio_forbidden(self, socio_headers):
        """Socio cannot get audit logs"""
        response = requests.get(f"{BASE_URL}/api/audit-logs", headers=socio_headers)
        assert response.status_code == 403
        print("✓ Socio correctly forbidden from audit logs")
    
    def test_get_stats_admin(self, admin_headers):
        """Admin can get statistics"""
        response = requests.get(f"{BASE_URL}/api/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        print(f"✓ Admin stats: {data['total_users']} total users, {data['active_users']} active")
    
    def test_get_stats_socio_forbidden(self, socio_headers):
        """Socio cannot get statistics"""
        response = requests.get(f"{BASE_URL}/api/stats", headers=socio_headers)
        assert response.status_code == 403
        print("✓ Socio correctly forbidden from statistics")


class TestPublicEndpoints:
    """Public (no auth) endpoint tests"""
    
    def test_public_posts(self):
        """Test getting public posts (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/posts", params={"visibility": "publico"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Public posts retrieved: {len(data)} posts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
