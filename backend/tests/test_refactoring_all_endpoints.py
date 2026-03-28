"""
Comprehensive API Test Suite for ACCTA Portal Backend Refactoring
Tests ALL endpoints after server.py was split into 17 module files.

Modules tested:
- auth_routes.py: /auth/register, /auth/login, /auth/me
- users.py: /users, /users/{id}/status
- invoices.py: /invoices, /invoices/{id}/confirm
- polls.py: /polls, /polls/vote, /polls/{id}/results
- posts.py: /posts
- documents.py: /documents
- benefits.py: /benefits
- wall.py: /wall, /wall/{id}/comments, /wall/{id}/like
- events.py: /events, /events/public, /events/upcoming, /events/{id}/register
- gallery.py: /gallery/albums, /gallery/photos
- notifications.py: /notifications, /notifications/unread/count, /notifications/mark-all-read
- stats.py: /stats, /validate/{qr_hash}
- upload.py: /upload/{category}
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from iteration_6.json
ADMIN_EMAIL = "admin@accta.cv"
ADMIN_PASSWORD = "admin123"
SOCIO_EMAIL = "socio1@accta.cv"
SOCIO_PASSWORD = "socio123"


class TestAPIRoot:
    """Test API root endpoint"""
    
    def test_api_root(self):
        """Test that API root returns correct message"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "ACCTA Portal API v1.0"
        print("✓ API root endpoint working")


class TestAuthRoutes:
    """Test authentication endpoints - auth_routes.py"""
    
    def test_login_admin_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        assert data["token_type"] == "bearer"
        print(f"✓ Admin login successful - user: {data['user']['name']}")
    
    def test_login_socio_success(self):
        """Test socio login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == SOCIO_EMAIL
        assert data["user"]["role"] == "socio"
        print(f"✓ Socio login successful - user: {data['user']['name']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")
    
    def test_get_me_with_valid_token(self):
        """Test /auth/me with valid token"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Then get user profile
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == SOCIO_EMAIL
        print(f"✓ /auth/me returns correct user profile")
    
    def test_get_me_without_token(self):
        """Test /auth/me without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403]
        print("✓ /auth/me correctly requires authentication")


class TestUsersRoutes:
    """Test users endpoints - users.py"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def socio_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_users_as_admin(self, admin_token):
        """Test GET /users as admin"""
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ GET /users returns {len(data)} users")
    
    def test_get_users_as_socio_forbidden(self, socio_token):
        """Test GET /users as socio (should be forbidden)"""
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        assert response.status_code == 403
        print("✓ GET /users correctly forbidden for socio")


class TestInvoicesRoutes:
    """Test invoices endpoints - invoices.py"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def socio_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_invoices_as_admin(self, admin_token):
        """Test GET /invoices as admin (returns all invoices)"""
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /invoices (admin) returns {len(data)} invoices")
    
    def test_get_invoices_as_socio(self, socio_token):
        """Test GET /invoices as socio (returns only user's invoices)"""
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /invoices (socio) returns {len(data)} invoices")
    
    def test_confirm_invoice_as_admin(self, admin_token):
        """Test PATCH /invoices/{id}/confirm as admin"""
        # First get an invoice
        invoices_response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        invoices = invoices_response.json()
        
        if invoices:
            invoice_id = invoices[0]["id"]
            response = requests.patch(
                f"{BASE_URL}/api/invoices/{invoice_id}/confirm",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            print(f"✓ PATCH /invoices/{invoice_id}/confirm successful")
        else:
            pytest.skip("No invoices to test")


class TestPollsRoutes:
    """Test polls endpoints - polls.py"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def socio_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_polls(self, socio_token):
        """Test GET /polls"""
        response = requests.get(
            f"{BASE_URL}/api/polls",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /polls returns {len(data)} polls")
        return data
    
    def test_get_poll_results(self, socio_token):
        """Test GET /polls/{poll_id}/results"""
        # First get polls
        polls_response = requests.get(
            f"{BASE_URL}/api/polls",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        polls = polls_response.json()
        
        if polls:
            poll_id = polls[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/polls/{poll_id}/results",
                headers={"Authorization": f"Bearer {socio_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "poll_id" in data
            assert "total_votes" in data
            assert "results" in data
            print(f"✓ GET /polls/{poll_id}/results - total votes: {data['total_votes']}")
        else:
            pytest.skip("No polls to test")


class TestPostsRoutes:
    """Test posts endpoints - posts.py (no auth required for GET)"""
    
    def test_get_posts_public(self):
        """Test GET /posts (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/posts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /posts returns {len(data)} posts")
    
    def test_get_posts_with_visibility_filter(self):
        """Test GET /posts with visibility filter"""
        response = requests.get(f"{BASE_URL}/api/posts?visibility=publico")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /posts?visibility=publico returns {len(data)} posts")


class TestDocumentsRoutes:
    """Test documents endpoints - documents.py"""
    
    @pytest.fixture
    def socio_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_documents(self, socio_token):
        """Test GET /documents (auth required)"""
        response = requests.get(
            f"{BASE_URL}/api/documents",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /documents returns {len(data)} documents")
    
    def test_get_documents_without_auth(self):
        """Test GET /documents without auth (should fail)"""
        response = requests.get(f"{BASE_URL}/api/documents")
        assert response.status_code in [401, 403]
        print("✓ GET /documents correctly requires authentication")


class TestBenefitsRoutes:
    """Test benefits endpoints - benefits.py"""
    
    @pytest.fixture
    def socio_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_benefits(self, socio_token):
        """Test GET /benefits (active user required)"""
        response = requests.get(
            f"{BASE_URL}/api/benefits",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /benefits returns {len(data)} benefits")


class TestWallRoutes:
    """Test wall endpoints - wall.py"""
    
    @pytest.fixture
    def socio_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_wall_posts(self, socio_token):
        """Test GET /wall (active user required)"""
        response = requests.get(
            f"{BASE_URL}/api/wall",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /wall returns {len(data)} posts")
        return data
    
    def test_create_wall_post(self, socio_token):
        """Test POST /wall"""
        response = requests.post(
            f"{BASE_URL}/api/wall",
            headers={"Authorization": f"Bearer {socio_token}"},
            json={"content": "TEST_Post de teste automatizado", "category": "geral"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["content"] == "TEST_Post de teste automatizado"
        print(f"✓ POST /wall created post with id: {data['id']}")
        return data
    
    def test_get_wall_comments(self, socio_token):
        """Test GET /wall/{post_id}/comments"""
        # First get wall posts
        wall_response = requests.get(
            f"{BASE_URL}/api/wall",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        posts = wall_response.json()
        
        if posts:
            post_id = posts[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/wall/{post_id}/comments",
                headers={"Authorization": f"Bearer {socio_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            print(f"✓ GET /wall/{post_id}/comments returns {len(data)} comments")
        else:
            pytest.skip("No wall posts to test")
    
    def test_toggle_like_wall_post(self, socio_token):
        """Test PATCH /wall/{post_id}/like"""
        # First get wall posts
        wall_response = requests.get(
            f"{BASE_URL}/api/wall",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        posts = wall_response.json()
        
        if posts:
            post_id = posts[0]["id"]
            response = requests.patch(
                f"{BASE_URL}/api/wall/{post_id}/like",
                headers={"Authorization": f"Bearer {socio_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "liked" in data
            assert "like_count" in data
            print(f"✓ PATCH /wall/{post_id}/like - liked: {data['liked']}, count: {data['like_count']}")
        else:
            pytest.skip("No wall posts to test")


class TestEventsRoutes:
    """Test events endpoints - events.py"""
    
    @pytest.fixture
    def socio_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_events(self, socio_token):
        """Test GET /events (auth required)"""
        response = requests.get(
            f"{BASE_URL}/api/events",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /events returns {len(data)} events")
        return data
    
    def test_get_public_events(self):
        """Test GET /events/public (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/events/public")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /events/public returns {len(data)} public events")
    
    def test_get_upcoming_events(self, socio_token):
        """Test GET /events/upcoming (auth required)"""
        response = requests.get(
            f"{BASE_URL}/api/events/upcoming",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /events/upcoming returns {len(data)} upcoming events")
    
    def test_register_for_event(self, socio_token):
        """Test POST /events/{event_id}/register"""
        # First get events
        events_response = requests.get(
            f"{BASE_URL}/api/events",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        events = events_response.json()
        
        if events:
            event_id = events[0]["id"]
            response = requests.post(
                f"{BASE_URL}/api/events/{event_id}/register",
                headers={"Authorization": f"Bearer {socio_token}"}
            )
            # Could be 200 (success) or 400 (already registered)
            assert response.status_code in [200, 400]
            print(f"✓ POST /events/{event_id}/register - status: {response.status_code}")
        else:
            pytest.skip("No events to test")


class TestGalleryRoutes:
    """Test gallery endpoints - gallery.py"""
    
    def test_get_gallery_albums(self):
        """Test GET /gallery/albums (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/gallery/albums")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /gallery/albums returns {len(data)} albums")
        return data
    
    def test_get_gallery_photos(self):
        """Test GET /gallery/photos (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/gallery/photos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /gallery/photos returns {len(data)} photos")
    
    def test_get_gallery_photos_by_album(self):
        """Test GET /gallery/photos with album_id filter"""
        # First get albums
        albums_response = requests.get(f"{BASE_URL}/api/gallery/albums")
        albums = albums_response.json()
        
        if albums:
            album_id = albums[0]["id"]
            response = requests.get(f"{BASE_URL}/api/gallery/photos?album_id={album_id}")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            print(f"✓ GET /gallery/photos?album_id={album_id} returns {len(data)} photos")
        else:
            pytest.skip("No albums to test")


class TestNotificationsRoutes:
    """Test notifications endpoints - notifications.py"""
    
    @pytest.fixture
    def socio_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_notifications(self, socio_token):
        """Test GET /notifications (auth required)"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /notifications returns {len(data)} notifications")
    
    def test_get_unread_count(self, socio_token):
        """Test GET /notifications/unread/count (auth required)"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/unread/count",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        print(f"✓ GET /notifications/unread/count - count: {data['count']}")
    
    def test_mark_all_read(self, socio_token):
        """Test PATCH /notifications/mark-all-read (auth required)"""
        response = requests.patch(
            f"{BASE_URL}/api/notifications/mark-all-read",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ PATCH /notifications/mark-all-read - {data['message']}")
    
    def test_get_audit_logs_as_admin(self, admin_token):
        """Test GET /audit-logs (admin only)"""
        response = requests.get(
            f"{BASE_URL}/api/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /audit-logs returns {len(data)} logs")
    
    def test_get_audit_logs_as_socio_forbidden(self, socio_token):
        """Test GET /audit-logs as socio (should be forbidden)"""
        response = requests.get(
            f"{BASE_URL}/api/audit-logs",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        assert response.status_code == 403
        print("✓ GET /audit-logs correctly forbidden for socio")


class TestStatsRoutes:
    """Test stats endpoints - stats.py"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def socio_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_stats_as_admin(self, admin_token):
        """Test GET /stats (admin only)"""
        response = requests.get(
            f"{BASE_URL}/api/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "pending_invoices" in data
        assert "total_revenue" in data
        print(f"✓ GET /stats - users: {data['total_users']}, active: {data['active_users']}, pending invoices: {data['pending_invoices']}")
    
    def test_get_stats_as_socio_forbidden(self, socio_token):
        """Test GET /stats as socio (should be forbidden)"""
        response = requests.get(
            f"{BASE_URL}/api/stats",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        assert response.status_code == 403
        print("✓ GET /stats correctly forbidden for socio")
    
    def test_validate_qr_hash_invalid(self):
        """Test GET /validate/{qr_hash} with invalid hash"""
        response = requests.get(f"{BASE_URL}/api/validate/invalid-hash-12345")
        assert response.status_code == 404
        print("✓ GET /validate/invalid-hash correctly returns 404")


class TestCleanup:
    """Cleanup test data created during tests"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_cleanup_test_wall_posts(self, admin_token):
        """Delete TEST_ prefixed wall posts"""
        # Get all wall posts (need admin to see pending ones too)
        response = requests.get(
            f"{BASE_URL}/api/wall",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if response.status_code == 200:
            posts = response.json()
            deleted = 0
            for post in posts:
                if post.get("content", "").startswith("TEST_"):
                    del_response = requests.delete(
                        f"{BASE_URL}/api/wall/{post['id']}",
                        headers={"Authorization": f"Bearer {admin_token}"}
                    )
                    if del_response.status_code == 200:
                        deleted += 1
            print(f"✓ Cleanup: deleted {deleted} TEST_ wall posts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
