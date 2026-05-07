"""
ACCTA Portal - Member Profile CRUD Tests
Tests for user profile management, admin user updates, cargo/privileges management
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@controlador.cv"
ADMIN_PASSWORD = "admin123"
SOCIO_EMAIL = "socio1@controlador.cv"
SOCIO_PASSWORD = "socio123"

# Valid cargos and privileges from backend
VALID_CARGOS = ["Presidente", "Vice-Presidente", "Secretário-Geral", "Tesoureiro", "Vogal", "Membro da Direção", "Sócio"]
VALID_PRIVILEGES = ["manage_users", "manage_finances", "manage_events", "manage_documents", "moderate_content", "manage_benefits", "view_audit_logs"]


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
def admin_headers(admin_token):
    """Headers with admin auth token"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture
def socio_headers(socio_token):
    """Headers with socio auth token"""
    return {"Authorization": f"Bearer {socio_token}", "Content-Type": "application/json"}


class TestMetaEndpoints:
    """Tests for metadata endpoints (cargos and privileges)"""
    
    def test_get_cargos_returns_list(self):
        """GET /api/users/meta/cargos returns list of available cargos"""
        response = requests.get(f"{BASE_URL}/api/users/meta/cargos")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "cargos" in data
        assert isinstance(data["cargos"], list)
        assert len(data["cargos"]) == 7
        assert "Presidente" in data["cargos"]
        assert "Vice-Presidente" in data["cargos"]
        assert "Sócio" in data["cargos"]
        print(f"✓ GET /api/users/meta/cargos returns {len(data['cargos'])} cargos")
    
    def test_get_privileges_returns_list(self):
        """GET /api/users/meta/privileges returns list of available privileges"""
        response = requests.get(f"{BASE_URL}/api/users/meta/privileges")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "privileges" in data
        assert isinstance(data["privileges"], list)
        assert len(data["privileges"]) == 7
        assert "manage_users" in data["privileges"]
        assert "manage_finances" in data["privileges"]
        assert "view_audit_logs" in data["privileges"]
        print(f"✓ GET /api/users/meta/privileges returns {len(data['privileges'])} privileges")


class TestUserListWithFilters:
    """Tests for user list endpoint with search and filters"""
    
    def test_search_users_by_name(self, admin_headers):
        """GET /api/users?search=Carlos returns filtered users"""
        response = requests.get(f"{BASE_URL}/api/users?search=Carlos", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Verify Carlos Mendes is in results
        carlos = next((u for u in data if "Carlos" in u.get("name", "")), None)
        assert carlos is not None, "Carlos not found in search results"
        assert "cargo" in carlos
        assert "privileges" in carlos
        print(f"✓ Search for 'Carlos' returned {len(data)} user(s) with cargo and privileges fields")
    
    def test_filter_users_by_role_admin(self, admin_headers):
        """GET /api/users?role=admin returns only admin users"""
        response = requests.get(f"{BASE_URL}/api/users?role=admin", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # All returned users should be admin
        for user in data:
            assert user["role"] == "admin", f"Expected role=admin, got {user['role']}"
        print(f"✓ Filter by role=admin returned {len(data)} admin user(s)")
    
    def test_filter_users_by_status(self, admin_headers):
        """GET /api/users?status=ativo returns only active users"""
        response = requests.get(f"{BASE_URL}/api/users?status=ativo", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for user in data:
            assert user["status"] == "ativo"
        print(f"✓ Filter by status=ativo returned {len(data)} active user(s)")
    
    def test_users_list_requires_admin_or_financeiro(self, socio_headers):
        """GET /api/users requires admin or financeiro role"""
        response = requests.get(f"{BASE_URL}/api/users", headers=socio_headers)
        assert response.status_code == 403
        print("✓ GET /api/users correctly requires admin/financeiro role")


class TestSelfProfileUpdate:
    """Tests for self-profile update endpoint"""
    
    def test_update_own_profile_name_phone_bio(self, socio_headers):
        """PATCH /api/users/me/profile - self-edit name, phone, bio works"""
        # Update profile
        update_data = {
            "name": "Carlos Mendes",
            "phone_number": "+238 9111111",
            "bio": "Controlador de tráfego aéreo experiente"
        }
        response = requests.patch(f"{BASE_URL}/api/users/me/profile", json=update_data, headers=socio_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["phone_number"] == update_data["phone_number"]
        assert data["bio"] == update_data["bio"]
        print(f"✓ Self-profile update successful: name={data['name']}, phone={data['phone_number']}")
    
    def test_update_own_profile_empty_returns_400(self, socio_headers):
        """PATCH /api/users/me/profile with no fields returns 400"""
        response = requests.patch(f"{BASE_URL}/api/users/me/profile", json={}, headers=socio_headers)
        assert response.status_code == 400
        print("✓ Empty profile update correctly returns 400")
    
    def test_update_own_profile_requires_auth(self):
        """PATCH /api/users/me/profile requires authentication"""
        response = requests.patch(f"{BASE_URL}/api/users/me/profile", json={"name": "Test"})
        assert response.status_code in [401, 403]
        print("✓ Profile update correctly requires authentication")


class TestAdminUserUpdate:
    """Tests for admin user update endpoint"""
    
    def test_admin_update_user_role_cargo_privileges(self, admin_headers):
        """PATCH /api/users/{userId} (admin) - update user role, cargo, privileges works"""
        # Get a user to update (Carlos Mendes)
        response = requests.get(f"{BASE_URL}/api/users?search=Carlos", headers=admin_headers)
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 1
        user_id = users[0]["id"]
        
        # Update user
        update_data = {
            "role": "socio",
            "cargo": "Vogal",
            "privileges": ["manage_events", "moderate_content"]
        }
        response = requests.patch(f"{BASE_URL}/api/users/{user_id}", json=update_data, headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["role"] == "socio"
        assert data["cargo"] == "Vogal"
        assert "manage_events" in data["privileges"]
        assert "moderate_content" in data["privileges"]
        print(f"✓ Admin update successful: role={data['role']}, cargo={data['cargo']}, privileges={data['privileges']}")
    
    def test_admin_update_invalid_cargo_returns_400(self, admin_headers):
        """PATCH /api/users/{userId} (admin) - invalid cargo returns 400 error"""
        # Get a user to update
        response = requests.get(f"{BASE_URL}/api/users?search=Carlos", headers=admin_headers)
        users = response.json()
        user_id = users[0]["id"]
        
        # Try invalid cargo
        response = requests.patch(f"{BASE_URL}/api/users/{user_id}", json={"cargo": "InvalidCargo"}, headers=admin_headers)
        assert response.status_code == 400
        assert "Cargo inválido" in response.json().get("detail", "")
        print("✓ Invalid cargo correctly returns 400 with error message")
    
    def test_admin_update_invalid_privileges_returns_400(self, admin_headers):
        """PATCH /api/users/{userId} (admin) - invalid privileges returns 400 error"""
        # Get a user to update
        response = requests.get(f"{BASE_URL}/api/users?search=Carlos", headers=admin_headers)
        users = response.json()
        user_id = users[0]["id"]
        
        # Try invalid privilege
        response = requests.patch(f"{BASE_URL}/api/users/{user_id}", json={"privileges": ["invalid_privilege"]}, headers=admin_headers)
        assert response.status_code == 400
        assert "Privilégios inválidos" in response.json().get("detail", "")
        print("✓ Invalid privileges correctly returns 400 with error message")
    
    def test_admin_update_invalid_role_returns_400(self, admin_headers):
        """PATCH /api/users/{userId} (admin) - invalid role returns 400 error"""
        # Get a user to update
        response = requests.get(f"{BASE_URL}/api/users?search=Carlos", headers=admin_headers)
        users = response.json()
        user_id = users[0]["id"]
        
        # Try invalid role
        response = requests.patch(f"{BASE_URL}/api/users/{user_id}", json={"role": "invalid_role"}, headers=admin_headers)
        assert response.status_code == 400
        assert "Role inválido" in response.json().get("detail", "")
        print("✓ Invalid role correctly returns 400 with error message")
    
    def test_admin_update_requires_admin_role(self, socio_headers):
        """PATCH /api/users/{userId} requires admin role"""
        # Try to update as socio
        response = requests.patch(f"{BASE_URL}/api/users/some-id", json={"role": "admin"}, headers=socio_headers)
        assert response.status_code == 403
        print("✓ Admin update correctly requires admin role")


class TestDeleteUser:
    """Tests for user deletion endpoint"""
    
    def test_cannot_delete_own_account(self, admin_headers, admin_token):
        """DELETE /api/users/self - cannot delete own account returns 400"""
        # Get admin's own ID
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers)
        admin_id = response.json()["id"]
        
        # Try to delete own account
        response = requests.delete(f"{BASE_URL}/api/users/{admin_id}", headers=admin_headers)
        assert response.status_code == 400
        assert "própria conta" in response.json().get("detail", "")
        print("✓ Cannot delete own account - correctly returns 400")
    
    def test_delete_user_requires_admin(self, socio_headers):
        """DELETE /api/users/{userId} requires admin role"""
        response = requests.delete(f"{BASE_URL}/api/users/some-id", headers=socio_headers)
        assert response.status_code == 403
        print("✓ Delete user correctly requires admin role")
    
    def test_delete_nonexistent_user_returns_404(self, admin_headers):
        """DELETE /api/users/{userId} - nonexistent user returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/api/users/{fake_id}", headers=admin_headers)
        assert response.status_code == 404
        print("✓ Delete nonexistent user correctly returns 404")


class TestGetSingleUser:
    """Tests for getting single user endpoint"""
    
    def test_get_user_by_id(self, admin_headers):
        """GET /api/users/{userId} returns user details"""
        # Get a user ID first
        response = requests.get(f"{BASE_URL}/api/users?search=Carlos", headers=admin_headers)
        users = response.json()
        user_id = users[0]["id"]
        
        # Get single user
        response = requests.get(f"{BASE_URL}/api/users/{user_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert "name" in data
        assert "email" in data
        assert "cargo" in data
        assert "privileges" in data
        print(f"✓ GET /api/users/{user_id} returns user with all fields")
    
    def test_get_nonexistent_user_returns_404(self, admin_headers):
        """GET /api/users/{userId} - nonexistent user returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/users/{fake_id}", headers=admin_headers)
        assert response.status_code == 404
        print("✓ GET nonexistent user correctly returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
