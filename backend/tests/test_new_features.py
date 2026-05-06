"""
Test cases for new features:
1. GET /api/events/featured - Featured event for homepage countdown (PUBLIC, no auth)
2. GET /api/report/personal - Personal activity report (requires auth)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@accta.cv"
ADMIN_PASSWORD = "admin123"
SOCIO_EMAIL = "socio1@accta.cv"
SOCIO_PASSWORD = "socio123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def socio_token():
    """Get socio authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SOCIO_EMAIL,
        "password": SOCIO_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Socio authentication failed")


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def socio_headers(socio_token):
    return {"Authorization": f"Bearer {socio_token}"}


class TestFeaturedEventEndpoint:
    """Tests for GET /api/events/featured - PUBLIC endpoint (no auth required)"""

    def test_featured_event_no_auth_required(self):
        """Featured event endpoint should work without authentication"""
        response = requests.get(f"{BASE_URL}/api/events/featured")
        # Should return 200 even without auth (public endpoint)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Featured event endpoint accessible without auth")

    def test_featured_event_returns_valid_structure(self):
        """Featured event should return valid event structure or null"""
        response = requests.get(f"{BASE_URL}/api/events/featured")
        assert response.status_code == 200
        
        data = response.json()
        # Can be null if no upcoming public events
        if data is None:
            print("✓ Featured event returned null (no upcoming public events)")
            return
        
        # If event exists, validate structure
        assert "id" in data, "Event should have 'id' field"
        assert "title" in data, "Event should have 'title' field"
        assert "date" in data, "Event should have 'date' field"
        assert "visibility" in data, "Event should have 'visibility' field"
        assert data["visibility"] == "publico", f"Featured event should be public, got {data['visibility']}"
        
        # Should not include attendees list (privacy)
        assert "attendees" not in data, "Featured event should not expose attendees list"
        
        # Should include attendee_count
        assert "attendee_count" in data, "Featured event should include attendee_count"
        assert isinstance(data["attendee_count"], int), "attendee_count should be integer"
        
        print(f"✓ Featured event structure valid: {data['title']}")
        print(f"  - Date: {data['date']}")
        print(f"  - Location: {data.get('location', 'N/A')}")
        print(f"  - Attendee count: {data['attendee_count']}")

    def test_featured_event_is_upcoming(self):
        """Featured event should be in the future"""
        from datetime import datetime, timezone
        
        response = requests.get(f"{BASE_URL}/api/events/featured")
        assert response.status_code == 200
        
        data = response.json()
        if data is None:
            print("✓ No featured event to check date")
            return
        
        event_date = datetime.fromisoformat(data["date"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        
        assert event_date > now, f"Featured event date {event_date} should be in the future"
        print(f"✓ Featured event is upcoming: {event_date}")


class TestPersonalReportEndpoint:
    """Tests for GET /api/report/personal - requires authentication"""

    def test_personal_report_requires_auth(self):
        """Personal report should require authentication"""
        response = requests.get(f"{BASE_URL}/api/report/personal")
        # Accept both 401 (Unauthorized) and 403 (Forbidden) as valid auth-required responses
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"✓ Personal report requires authentication (returns {response.status_code})")

    def test_personal_report_socio_access(self, socio_headers):
        """Socio should be able to access their personal report"""
        response = requests.get(f"{BASE_URL}/api/report/personal", headers=socio_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Validate all expected fields exist
        expected_fields = [
            "events_attended",
            "total_events",
            "polls_voted",
            "total_polls",
            "wall_posts",
            "likes_received",
            "wall_comments",
            "projects_member",
            "benefits_used",
            "photos_submitted",
            "photos_approved",
            "documents_available"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
            assert isinstance(data[field], int), f"Field {field} should be integer, got {type(data[field])}"
        
        print("✓ Personal report for socio has all required fields")
        print(f"  - Events attended: {data['events_attended']} / {data['total_events']}")
        print(f"  - Polls voted: {data['polls_voted']} / {data['total_polls']}")
        print(f"  - Wall posts: {data['wall_posts']}")
        print(f"  - Likes received: {data['likes_received']}")
        print(f"  - Wall comments: {data['wall_comments']}")
        print(f"  - Projects member: {data['projects_member']}")
        print(f"  - Benefits used: {data['benefits_used']}")
        print(f"  - Photos: {data['photos_approved']} approved / {data['photos_submitted']} submitted")
        print(f"  - Documents available: {data['documents_available']}")

    def test_personal_report_admin_access(self, admin_headers):
        """Admin should also be able to access their personal report"""
        response = requests.get(f"{BASE_URL}/api/report/personal", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "events_attended" in data
        assert "polls_voted" in data
        print("✓ Admin can access personal report")

    def test_personal_report_data_consistency(self, socio_headers):
        """Personal report data should be consistent with actual user activity"""
        response = requests.get(f"{BASE_URL}/api/report/personal", headers=socio_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Logical consistency checks
        assert data["photos_approved"] <= data["photos_submitted"], \
            "Approved photos cannot exceed submitted photos"
        assert data["events_attended"] <= data["total_events"], \
            "Attended events cannot exceed total events"
        assert data["polls_voted"] <= data["total_polls"], \
            "Voted polls cannot exceed total polls"
        
        print("✓ Personal report data is logically consistent")


class TestAuthenticationFlow:
    """Verify authentication still works correctly"""

    def test_admin_login(self):
        """Admin login should work"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        print("✓ Admin login successful")

    def test_socio_login(self):
        """Socio login should work"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        assert response.status_code == 200, f"Socio login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        print("✓ Socio login successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
