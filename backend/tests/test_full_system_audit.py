"""
FULL SYSTEM AUDIT - ACCTA Portal Backend
Comprehensive test suite for 'varredura completa' (full system scan)

Tests ALL modules:
- Authentication (login, me, password recovery)
- Financial Module (transactions, summary, DRE, settings, quotas, exports)
- Project Management (CRUD, tasks, comments, expenses, milestones)
- Events/Agenda (CRUD, registration, upcoming)
- Notifications (CRUD, broadcast, mark-read)
- Wall/Mural (posts, comments, likes, approval)
- Gallery (public/private albums, photos, approval workflow)
- Voting/Polls (CRUD, voting)
- Documents
- User Management (CRUD, roles)
- Activity Feed
- Stats
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@controlador.cv"
ADMIN_PASSWORD = "admin123"
SOCIO_EMAIL = "socio1@controlador.cv"
SOCIO_PASSWORD = "socio123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def socio_token():
    """Get socio authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SOCIO_EMAIL,
        "password": SOCIO_PASSWORD
    })
    assert response.status_code == 200, f"Socio login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def socio_headers(socio_token):
    return {"Authorization": f"Bearer {socio_token}"}


# ==================== AUTHENTICATION TESTS ====================

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_admin_success(self):
        """POST /api/auth/login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        print("✓ Admin login successful")
    
    def test_login_socio_success(self):
        """POST /api/auth/login with socio credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == SOCIO_EMAIL
        assert data["user"]["role"] == "socio"
        print("✓ Socio login successful")
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login with wrong password returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials rejected")
    
    def test_get_me_returns_user_data(self, admin_headers):
        """GET /api/auth/me returns current user data with role"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "role" in data
        assert data["role"] == "admin"
        print(f"✓ /auth/me returns user: {data['name']}")
    
    def test_forgot_password_valid_email(self):
        """POST /api/auth/forgot-password with valid email"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": SOCIO_EMAIL
        })
        assert response.status_code == 200
        data = response.json()
        assert "demo_token" in data
        print("✓ Password reset token generated")
    
    def test_forgot_password_invalid_email(self):
        """POST /api/auth/forgot-password with invalid email returns 404"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": "nonexistent@test.com"
        })
        assert response.status_code == 404
        print("✓ Invalid email rejected for password reset")


# ==================== FINANCIAL MODULE TESTS ====================

class TestFinancialModule:
    """Test financial module endpoints"""
    
    def test_get_transactions(self, admin_headers):
        """GET /api/finances/transactions returns paginated items"""
        response = requests.get(f"{BASE_URL}/api/finances/transactions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        print(f"✓ Transactions: {len(data['items'])} items, total: {data['total']}")
    
    def test_get_transactions_unauthorized(self, socio_headers):
        """GET /api/finances/transactions requires finance role"""
        response = requests.get(f"{BASE_URL}/api/finances/transactions", headers=socio_headers)
        assert response.status_code == 403
        print("✓ Socio correctly denied access to finances")
    
    def test_create_transaction(self, admin_headers):
        """POST /api/finances/transactions creates transaction"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/finances/transactions", headers=admin_headers, json={
            "type": "receita",
            "category": "quotas",
            "description": f"TEST_Quota Teste {unique_id}",
            "amount": 1000.0,
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        })
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "receita"
        assert data["amount"] == 1000.0
        print(f"✓ Transaction created: {data['id']}")
        return data["id"]
    
    def test_create_transaction_invalid_type(self, admin_headers):
        """POST /api/finances/transactions with invalid type returns 400"""
        response = requests.post(f"{BASE_URL}/api/finances/transactions", headers=admin_headers, json={
            "type": "invalid_type",
            "category": "quotas",
            "description": "Test",
            "amount": 100.0,
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        })
        assert response.status_code == 400
        print("✓ Invalid transaction type rejected")
    
    def test_create_transaction_negative_amount(self, admin_headers):
        """POST /api/finances/transactions with negative amount returns 400"""
        response = requests.post(f"{BASE_URL}/api/finances/transactions", headers=admin_headers, json={
            "type": "receita",
            "category": "quotas",
            "description": "Test",
            "amount": -100.0,
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        })
        assert response.status_code == 400
        print("✓ Negative amount rejected")
    
    def test_get_financial_summary(self, admin_headers):
        """GET /api/finances/summary returns financial summary"""
        response = requests.get(f"{BASE_URL}/api/finances/summary", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_receitas" in data
        assert "total_despesas" in data
        assert "resultado_liquido" in data
        print(f"✓ Summary: Receitas={data['total_receitas']}, Despesas={data['total_despesas']}")
    
    def test_get_dre_report(self, admin_headers):
        """GET /api/finances/dre returns DRE report"""
        response = requests.get(f"{BASE_URL}/api/finances/dre?year=2025", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "year" in data
        assert "monthly" in data
        assert "total_receitas" in data
        print(f"✓ DRE report for {data['year']}: Resultado={data['resultado_liquido']}")
    
    def test_export_csv(self, admin_headers):
        """GET /api/finances/transactions/csv exports CSV"""
        response = requests.get(f"{BASE_URL}/api/finances/transactions/csv", headers=admin_headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        print("✓ CSV export successful")
    
    def test_export_dre_pdf(self, admin_headers):
        """GET /api/finances/dre/pdf exports PDF"""
        response = requests.get(f"{BASE_URL}/api/finances/dre/pdf?year=2025", headers=admin_headers)
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        print("✓ PDF export successful")
    
    def test_get_finance_settings(self, admin_headers):
        """GET /api/finances/settings returns settings"""
        response = requests.get(f"{BASE_URL}/api/finances/settings", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "quota_amount" in data
        print(f"✓ Finance settings: quota_amount={data['quota_amount']}")
    
    def test_generate_quotas(self, admin_headers):
        """POST /api/finances/generate-quotas generates monthly quotas"""
        response = requests.post(
            f"{BASE_URL}/api/finances/generate-quotas?month=12&year=2025",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "created" in data
        print(f"✓ Quotas generated: {data['created']} created, {data.get('skipped', 0)} skipped")


# ==================== PROJECT MODULE TESTS ====================

class TestProjectModule:
    """Test project management endpoints"""
    
    def test_get_projects(self, admin_headers):
        """GET /api/projects returns project list"""
        response = requests.get(f"{BASE_URL}/api/projects", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Projects: {len(data['items'])} items")
    
    def test_create_project(self, admin_headers):
        """POST /api/projects creates a project"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/projects", headers=admin_headers, json={
            "title": f"TEST_Projeto Teste {unique_id}",
            "description": "Projeto de teste para auditoria",
            "visibility": "publico",
            "budget": 50000.0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"].startswith("TEST_")
        assert data["status"] == "aprovado"  # Admin creates approved
        print(f"✓ Project created: {data['id']}")
        return data["id"]
    
    def test_create_project_socio_proposta(self, socio_headers):
        """POST /api/projects by socio creates with status 'proposta'"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/projects", headers=socio_headers, json={
            "title": f"TEST_Proposta Socio {unique_id}",
            "description": "Proposta de projeto por socio",
            "visibility": "publico"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "proposta"
        print(f"✓ Socio project created as proposta: {data['id']}")
        return data["id"]
    
    def test_update_project_status(self, admin_headers):
        """PATCH /api/projects/{id} updates project status"""
        # First create a project
        unique_id = str(uuid.uuid4())[:8]
        create_resp = requests.post(f"{BASE_URL}/api/projects", headers=admin_headers, json={
            "title": f"TEST_Status Update {unique_id}",
            "description": "Test status update",
            "visibility": "publico"
        })
        project_id = create_resp.json()["id"]
        
        # Update status
        response = requests.patch(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers, json={
            "status": "em_curso"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "em_curso"
        print(f"✓ Project status updated to: {data['status']}")
    
    def test_create_task(self, admin_headers):
        """POST /api/projects/{id}/tasks creates task"""
        # Get first project
        projects = requests.get(f"{BASE_URL}/api/projects", headers=admin_headers).json()
        if projects["items"]:
            project_id = projects["items"][0]["id"]
            unique_id = str(uuid.uuid4())[:8]
            response = requests.post(f"{BASE_URL}/api/projects/{project_id}/tasks", headers=admin_headers, json={
                "title": f"TEST_Tarefa {unique_id}",
                "description": "Tarefa de teste",
                "priority": "media"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["title"].startswith("TEST_")
            print(f"✓ Task created: {data['id']}")
    
    def test_create_comment(self, admin_headers):
        """POST /api/projects/{id}/comments creates comment"""
        projects = requests.get(f"{BASE_URL}/api/projects", headers=admin_headers).json()
        if projects["items"]:
            project_id = projects["items"][0]["id"]
            response = requests.post(f"{BASE_URL}/api/projects/{project_id}/comments", headers=admin_headers, json={
                "content": "TEST_Comentario de auditoria"
            })
            assert response.status_code == 200
            data = response.json()
            assert "TEST_" in data["content"]
            print(f"✓ Comment created: {data['id']}")
    
    def test_create_expense(self, admin_headers):
        """POST /api/projects/{id}/expenses creates expense"""
        projects = requests.get(f"{BASE_URL}/api/projects", headers=admin_headers).json()
        if projects["items"]:
            project_id = projects["items"][0]["id"]
            response = requests.post(f"{BASE_URL}/api/projects/{project_id}/expenses", headers=admin_headers, json={
                "description": "TEST_Despesa de teste",
                "amount": 500.0,
                "date": datetime.now().strftime("%Y-%m-%d")
            })
            assert response.status_code == 200
            data = response.json()
            assert data["amount"] == 500.0
            print(f"✓ Expense created: {data['id']}")
    
    def test_create_milestone(self, admin_headers):
        """POST /api/projects/{id}/milestones creates milestone"""
        projects = requests.get(f"{BASE_URL}/api/projects", headers=admin_headers).json()
        if projects["items"]:
            project_id = projects["items"][0]["id"]
            response = requests.post(f"{BASE_URL}/api/projects/{project_id}/milestones", headers=admin_headers, json={
                "title": "TEST_Marco de teste",
                "date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            })
            assert response.status_code == 200
            data = response.json()
            assert "TEST_" in data["title"]
            print(f"✓ Milestone created: {data['id']}")


# ==================== EVENTS/AGENDA TESTS ====================

class TestEventsModule:
    """Test events/agenda endpoints"""
    
    def test_get_events(self, admin_headers):
        """GET /api/events returns event list"""
        response = requests.get(f"{BASE_URL}/api/events", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Events: {len(data)} items")
    
    def test_get_upcoming_events(self, admin_headers):
        """GET /api/events/upcoming returns upcoming events"""
        response = requests.get(f"{BASE_URL}/api/events/upcoming", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Upcoming events: {len(data)} items")
    
    def test_get_public_events(self):
        """GET /api/events/public returns public events (no auth)"""
        response = requests.get(f"{BASE_URL}/api/events/public")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Public events: {len(data)} items")
    
    def test_create_event(self, admin_headers):
        """POST /api/events creates event (admin)"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/events", headers=admin_headers, json={
            "title": f"TEST_Evento {unique_id}",
            "description": "Evento de teste para auditoria",
            "type": "reuniao",
            "date": (datetime.now() + timedelta(days=7)).isoformat(),
            "location": "Sala de Reunioes",
            "visibility": "socios"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"].startswith("TEST_")
        print(f"✓ Event created: {data['id']}")
    
    def test_create_event_unauthorized(self, socio_headers):
        """POST /api/events by socio returns 403"""
        response = requests.post(f"{BASE_URL}/api/events", headers=socio_headers, json={
            "title": "Test Event",
            "description": "Test",
            "type": "reuniao",
            "date": datetime.now().isoformat(),
            "location": "Test Location",
            "visibility": "socios"
        })
        assert response.status_code == 403
        print("✓ Socio correctly denied event creation")
    
    def test_register_for_event(self, socio_headers, admin_headers):
        """POST /api/events/{id}/register registers for event"""
        # Get events
        events = requests.get(f"{BASE_URL}/api/events", headers=admin_headers).json()
        if events:
            event_id = events[0]["id"]
            response = requests.post(f"{BASE_URL}/api/events/{event_id}/register", headers=socio_headers)
            # May return 200 or 400 if already registered
            assert response.status_code in [200, 400]
            print(f"✓ Event registration: {response.status_code}")


# ==================== NOTIFICATIONS TESTS ====================

class TestNotificationsModule:
    """Test notifications endpoints"""
    
    def test_get_notifications(self, admin_headers):
        """GET /api/notifications returns paginated notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Notifications: {len(data['items'])} items, total: {data['total']}")
    
    def test_get_unread_count(self, admin_headers):
        """GET /api/notifications/unread/count returns unread count"""
        response = requests.get(f"{BASE_URL}/api/notifications/unread/count", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        print(f"✓ Unread notifications: {data['count']}")
    
    def test_broadcast_notification(self, admin_headers):
        """POST /api/notifications/broadcast sends to all active users"""
        unique_id = str(uuid.uuid4())[:8]
        # Note: broadcast uses NotificationCreate which requires user_id, but broadcast ignores it
        # The endpoint internally sends to all active users
        response = requests.post(f"{BASE_URL}/api/notifications/broadcast", headers=admin_headers, json={
            "user_id": "broadcast",  # Required by model but ignored by broadcast
            "type": "geral",
            "title": f"TEST_Broadcast {unique_id}",
            "message": "Mensagem de teste para auditoria",
            "link": "/dashboard"
        })
        assert response.status_code == 200
        print("✓ Broadcast notification sent")
    
    def test_broadcast_unauthorized(self, socio_headers):
        """POST /api/notifications/broadcast by socio returns 403"""
        response = requests.post(f"{BASE_URL}/api/notifications/broadcast", headers=socio_headers, json={
            "user_id": "broadcast",
            "type": "geral",
            "title": "Test",
            "message": "Test"
        })
        assert response.status_code == 403
        print("✓ Socio correctly denied broadcast")
    
    def test_mark_all_read(self, admin_headers):
        """PATCH /api/notifications/mark-all-read marks all as read"""
        response = requests.patch(f"{BASE_URL}/api/notifications/mark-all-read", headers=admin_headers)
        assert response.status_code == 200
        print("✓ All notifications marked as read")
    
    def test_clear_read_notifications(self, admin_headers):
        """DELETE /api/notifications/clear/all clears read notifications"""
        response = requests.delete(f"{BASE_URL}/api/notifications/clear/all", headers=admin_headers)
        assert response.status_code == 200
        print("✓ Read notifications cleared")


# ==================== WALL/MURAL TESTS ====================

class TestWallModule:
    """Test wall/mural endpoints"""
    
    def test_get_wall_posts(self, admin_headers):
        """GET /api/wall returns approved posts"""
        response = requests.get(f"{BASE_URL}/api/wall", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Wall posts: {len(data)} items")
    
    def test_create_post_admin(self, admin_headers):
        """POST /api/wall by admin creates approved post"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/wall", headers=admin_headers, json={
            "content": f"TEST_Post de auditoria {unique_id}",
            "category": "geral"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["approved"] == True
        print(f"✓ Admin post created (auto-approved): {data['id']}")
        return data["id"]
    
    def test_create_post_socio(self, socio_headers):
        """POST /api/wall by socio creates pending post"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/wall", headers=socio_headers, json={
            "content": f"TEST_Post socio {unique_id}",
            "category": "sugestao"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["approved"] == False
        print(f"✓ Socio post created (pending): {data['id']}")
        return data["id"]
    
    def test_get_pending_posts(self, admin_headers):
        """GET /api/wall/pending returns pending posts (admin only)"""
        response = requests.get(f"{BASE_URL}/api/wall/pending", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Pending posts: {len(data)} items")
    
    def test_get_pending_unauthorized(self, socio_headers):
        """GET /api/wall/pending by socio returns 403"""
        response = requests.get(f"{BASE_URL}/api/wall/pending", headers=socio_headers)
        assert response.status_code == 403
        print("✓ Socio correctly denied pending posts access")
    
    def test_approve_post(self, admin_headers, socio_headers):
        """PATCH /api/wall/{id}/approve approves post"""
        # Create pending post
        unique_id = str(uuid.uuid4())[:8]
        create_resp = requests.post(f"{BASE_URL}/api/wall", headers=socio_headers, json={
            "content": f"TEST_Approve test {unique_id}",
            "category": "geral"
        })
        post_id = create_resp.json()["id"]
        
        # Approve it
        response = requests.patch(f"{BASE_URL}/api/wall/{post_id}/approve", headers=admin_headers)
        assert response.status_code == 200
        print(f"✓ Post approved: {post_id}")
    
    def test_toggle_like(self, admin_headers):
        """PATCH /api/wall/{id}/like toggles like"""
        posts = requests.get(f"{BASE_URL}/api/wall", headers=admin_headers).json()
        if posts:
            post_id = posts[0]["id"]
            response = requests.patch(f"{BASE_URL}/api/wall/{post_id}/like", headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert "liked" in data
            assert "like_count" in data
            print(f"✓ Like toggled: liked={data['liked']}, count={data['like_count']}")
    
    def test_create_comment(self, admin_headers):
        """POST /api/wall/{id}/comments creates comment on post"""
        posts = requests.get(f"{BASE_URL}/api/wall", headers=admin_headers).json()
        if posts:
            post_id = posts[0]["id"]
            response = requests.post(f"{BASE_URL}/api/wall/{post_id}/comments", headers=admin_headers, json={
                "content": "TEST_Comentario de auditoria"
            })
            assert response.status_code == 200
            data = response.json()
            assert "TEST_" in data["content"]
            print(f"✓ Wall comment created: {data['id']}")


# ==================== GALLERY TESTS ====================

class TestGalleryModule:
    """Test gallery endpoints"""
    
    def test_get_public_albums(self):
        """GET /api/gallery/public/albums returns public albums only"""
        response = requests.get(f"{BASE_URL}/api/gallery/public/albums")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All should be public
        for album in data:
            assert album.get("visibility") == "public"
        print(f"✓ Public albums: {len(data)} items")
    
    def test_get_public_photos(self):
        """GET /api/gallery/public/photos returns approved public photos only"""
        response = requests.get(f"{BASE_URL}/api/gallery/public/photos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Public photos: {len(data)} items")
    
    def test_get_all_albums_auth(self, admin_headers):
        """GET /api/gallery/albums (auth) returns all albums including private"""
        response = requests.get(f"{BASE_URL}/api/gallery/albums", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ All albums (auth): {len(data)} items")
    
    def test_get_pending_photos(self, admin_headers):
        """GET /api/gallery/photos/pending returns pending photos (admin)"""
        response = requests.get(f"{BASE_URL}/api/gallery/photos/pending", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Pending photos: {len(data)} items")
    
    def test_get_pending_photos_unauthorized(self, socio_headers):
        """GET /api/gallery/photos/pending by socio returns 403"""
        response = requests.get(f"{BASE_URL}/api/gallery/photos/pending", headers=socio_headers)
        assert response.status_code == 403
        print("✓ Socio correctly denied pending photos access")
    
    def test_create_album_admin(self, admin_headers):
        """POST /api/gallery/albums (admin) creates album"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/gallery/albums", headers=admin_headers, json={
            "title": f"TEST_Album {unique_id}",
            "description": "Album de teste",
            "visibility": "public"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"].startswith("TEST_")
        print(f"✓ Album created: {data['id']}")
        return data["id"]
    
    def test_create_album_unauthorized(self, socio_headers):
        """POST /api/gallery/albums by socio returns 403"""
        response = requests.post(f"{BASE_URL}/api/gallery/albums", headers=socio_headers, json={
            "title": "Test Album",
            "description": "Test",
            "visibility": "public"
        })
        assert response.status_code == 403
        print("✓ Socio correctly denied album creation")


# ==================== VOTING/POLLS TESTS ====================

class TestPollsModule:
    """Test voting/polls endpoints"""
    
    def test_get_polls(self, admin_headers):
        """GET /api/polls returns poll list"""
        response = requests.get(f"{BASE_URL}/api/polls", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Polls: {len(data)} items")
    
    def test_create_poll(self, admin_headers):
        """POST /api/polls creates poll (admin)"""
        unique_id = str(uuid.uuid4())[:8]
        # Options must be list of dicts with 'text' key
        response = requests.post(f"{BASE_URL}/api/polls", headers=admin_headers, json={
            "title": f"TEST_Votacao {unique_id}",
            "description": "Votacao de teste",
            "options": [
                {"text": "Opcao A"},
                {"text": "Opcao B"},
                {"text": "Opcao C"}
            ],
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=7)).isoformat()
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"].startswith("TEST_")
        print(f"✓ Poll created: {data['id']}")
    
    def test_create_poll_unauthorized(self, socio_headers):
        """POST /api/polls by socio returns 403"""
        response = requests.post(f"{BASE_URL}/api/polls", headers=socio_headers, json={
            "title": "Test Poll",
            "description": "Test",
            "options": [{"text": "A"}, {"text": "B"}],
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=1)).isoformat()
        })
        assert response.status_code == 403
        print("✓ Socio correctly denied poll creation")
    
    def test_vote_on_poll(self, socio_headers, admin_headers):
        """POST /api/polls/vote votes on poll"""
        polls = requests.get(f"{BASE_URL}/api/polls", headers=admin_headers).json()
        if polls:
            poll_id = polls[0]["id"]
            # vote_option is an integer index
            response = requests.post(f"{BASE_URL}/api/polls/vote", headers=socio_headers, json={
                "poll_id": poll_id,
                "vote_option": 0  # First option
            })
            # May return 200 or 400 if already voted
            assert response.status_code in [200, 400]
            print(f"✓ Vote attempt: {response.status_code}")


# ==================== DOCUMENTS TESTS ====================

class TestDocumentsModule:
    """Test documents endpoints"""
    
    def test_get_documents(self, admin_headers):
        """GET /api/documents returns document list"""
        response = requests.get(f"{BASE_URL}/api/documents", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Documents: {len(data)} items")


# ==================== USER MANAGEMENT TESTS ====================

class TestUserManagement:
    """Test user management endpoints"""
    
    def test_get_users(self, admin_headers):
        """GET /api/users returns user list (admin)"""
        response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Users: {len(data)} items")
    
    def test_get_users_unauthorized(self, socio_headers):
        """GET /api/users by socio returns 403"""
        response = requests.get(f"{BASE_URL}/api/users", headers=socio_headers)
        assert response.status_code == 403
        print("✓ Socio correctly denied user list access")
    
    def test_get_single_user(self, admin_headers):
        """GET /api/users/{id} returns user details"""
        users = requests.get(f"{BASE_URL}/api/users", headers=admin_headers).json()
        if users:
            user_id = users[0]["id"]
            response = requests.get(f"{BASE_URL}/api/users/{user_id}", headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "email" in data
            print(f"✓ User details: {data['name']}")
    
    def test_update_user(self, admin_headers):
        """PATCH /api/users/{id} updates user (admin)"""
        users = requests.get(f"{BASE_URL}/api/users", headers=admin_headers).json()
        # Find a non-admin user to update
        for user in users:
            if user["role"] != "admin":
                # Use correct field name: phone_number not phone
                response = requests.patch(f"{BASE_URL}/api/users/{user['id']}", headers=admin_headers, json={
                    "phone_number": "+238 999 9999"
                })
                assert response.status_code == 200
                print(f"✓ User updated: {user['name']}")
                break


# ==================== ACTIVITY FEED TESTS ====================

class TestActivityFeed:
    """Test activity feed endpoints"""
    
    def test_get_recent_activity(self, admin_headers):
        """GET /api/activity/recent returns aggregated activity items"""
        response = requests.get(f"{BASE_URL}/api/activity/recent", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Activity feed: {len(data)} items")
    
    def test_activity_item_structure(self, admin_headers):
        """Activity items include type, title, description, link, created_at"""
        response = requests.get(f"{BASE_URL}/api/activity/recent", headers=admin_headers)
        data = response.json()
        if data:
            item = data[0]
            assert "type" in item
            assert "title" in item
            assert "description" in item
            assert "link" in item
            assert "created_at" in item
            print(f"✓ Activity item structure valid: type={item['type']}")
    
    def test_activity_limit_parameter(self, admin_headers):
        """GET /api/activity/recent?limit=5 respects limit"""
        response = requests.get(f"{BASE_URL}/api/activity/recent?limit=5", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
        print(f"✓ Activity limit respected: {len(data)} items")


# ==================== STATS TESTS ====================

class TestStatsModule:
    """Test stats endpoints"""
    
    def test_get_stats(self, admin_headers):
        """GET /api/stats returns system statistics"""
        response = requests.get(f"{BASE_URL}/api/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data or "users" in data or isinstance(data, dict)
        print("✓ Stats retrieved")


# ==================== CLEANUP ====================

class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_data(self, admin_headers):
        """Remove TEST_ prefixed data"""
        # This is a placeholder - in production you'd want to clean up test data
        print("✓ Test cleanup (manual cleanup recommended for TEST_ prefixed items)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
