"""
Test Activity Feed API - Recent Activity endpoint
Tests for GET /api/activity/recent endpoint that aggregates:
- Wall posts (approved)
- Project comments
- Events
- Transactions (admin/financeiro only)
- Project milestones (completed)
- Polls (open)
"""

import pytest
import requests
import os

# Default localhost: sem a env var, `.rstrip` em None rebentava na COLEÇÃO e
# derrubava a suite inteira (pytest interrompe). É teste de integração — sem
# servidor vivo falha por ConnectionRefused, como os restantes (esperado).
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001").rstrip("/")


class TestActivityFeedAPI:
    """Activity Feed endpoint tests"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as admin and socio"""
        # Admin login
        admin_response = requests.post(
            f"{BASE_URL}/api/auth/login", json={"email": "admin@controlador.cv", "password": "admin123"}
        )
        assert admin_response.status_code == 200, f"Admin login failed: {admin_response.text}"
        self.admin_token = admin_response.json()["access_token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Socio login
        socio_response = requests.post(
            f"{BASE_URL}/api/auth/login", json={"email": "socio1@controlador.cv", "password": "socio123"}
        )
        assert socio_response.status_code == 200, f"Socio login failed: {socio_response.text}"
        self.socio_token = socio_response.json()["access_token"]
        self.socio_headers = {"Authorization": f"Bearer {self.socio_token}"}

    # ===== BASIC ENDPOINT TESTS =====

    def test_activity_recent_returns_array(self):
        """GET /api/activity/recent returns an array (not paginated object)"""
        response = requests.get(f"{BASE_URL}/api/activity/recent", headers=self.admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert isinstance(data, list), f"Expected array, got {type(data)}"
        print(f"Activity feed returned {len(data)} items")

    def test_activity_requires_authentication(self):
        """GET /api/activity/recent requires authentication"""
        response = requests.get(f"{BASE_URL}/api/activity/recent")
        # API returns 403 (Forbidden) for unauthenticated requests
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"

    def test_activity_item_structure(self):
        """Activity items have correct structure (type, icon, title, description, link, created_at)"""
        response = requests.get(f"{BASE_URL}/api/activity/recent", headers=self.admin_headers)
        assert response.status_code == 200

        data = response.json()
        if len(data) > 0:
            item = data[0]
            required_fields = ["type", "icon", "title", "description", "link", "created_at"]
            for field in required_fields:
                assert field in item, f"Missing required field: {field}"

            # Validate type is one of expected values
            valid_types = ["mural", "projeto", "evento", "financeiro", "votacao"]
            assert item["type"] in valid_types, f"Invalid type: {item['type']}"

            # Validate icon is a string
            assert isinstance(item["icon"], str), f"Icon should be string, got {type(item['icon'])}"

            # Validate link starts with /
            assert item["link"].startswith("/"), f"Link should start with /, got {item['link']}"

            print(f"First activity item: type={item['type']}, title={item['title']}")
        else:
            print("No activity items returned - may need seed data")

    # ===== LIMIT PARAMETER TESTS =====

    def test_activity_default_limit(self):
        """Default limit is 15 items"""
        response = requests.get(f"{BASE_URL}/api/activity/recent", headers=self.admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data) <= 15, f"Default limit should be 15, got {len(data)} items"

    def test_activity_custom_limit(self):
        """Custom limit parameter works correctly"""
        response = requests.get(f"{BASE_URL}/api/activity/recent?limit=5", headers=self.admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data) <= 5, f"Limit 5 should return max 5 items, got {len(data)}"

    def test_activity_limit_max_50(self):
        """Limit parameter max is 50"""
        response = requests.get(f"{BASE_URL}/api/activity/recent?limit=100", headers=self.admin_headers)
        # Should either return 422 (validation error) or cap at 50
        if response.status_code == 200:
            data = response.json()
            assert len(data) <= 50, f"Max limit should be 50, got {len(data)}"
        else:
            assert response.status_code == 422, f"Expected 422 for invalid limit, got {response.status_code}"

    def test_activity_limit_min_1(self):
        """Limit parameter min is 1"""
        response = requests.get(f"{BASE_URL}/api/activity/recent?limit=0", headers=self.admin_headers)
        # Should return 422 (validation error)
        assert response.status_code == 422, f"Expected 422 for limit=0, got {response.status_code}"

    # ===== SORTING TESTS =====

    def test_activity_sorted_by_created_at_descending(self):
        """Items are sorted by created_at descending (newest first)"""
        response = requests.get(f"{BASE_URL}/api/activity/recent", headers=self.admin_headers)
        assert response.status_code == 200

        data = response.json()
        if len(data) >= 2:
            # Check that items are in descending order
            for i in range(len(data) - 1):
                current_date = data[i].get("created_at", "")
                next_date = data[i + 1].get("created_at", "")
                if current_date and next_date:
                    assert current_date >= next_date, f"Items not sorted: {current_date} should be >= {next_date}"
            print("Activity items are correctly sorted by created_at descending")
        else:
            print("Not enough items to verify sorting")

    # ===== ACTIVITY TYPE TESTS =====

    def test_activity_includes_wall_posts(self):
        """Activity includes wall posts (mural type)"""
        response = requests.get(f"{BASE_URL}/api/activity/recent?limit=50", headers=self.admin_headers)
        assert response.status_code == 200

        data = response.json()
        mural_items = [item for item in data if item["type"] == "mural"]
        print(f"Found {len(mural_items)} mural (wall post) items")

        if len(mural_items) > 0:
            item = mural_items[0]
            assert item["icon"] == "message-square", f"Mural icon should be message-square, got {item['icon']}"
            assert item["link"] == "/mural", f"Mural link should be /mural, got {item['link']}"

    def test_activity_includes_project_comments(self):
        """Activity includes project comments (projeto type)"""
        response = requests.get(f"{BASE_URL}/api/activity/recent?limit=50", headers=self.admin_headers)
        assert response.status_code == 200

        data = response.json()
        projeto_items = [item for item in data if item["type"] == "projeto"]
        print(f"Found {len(projeto_items)} projeto items")

        if len(projeto_items) > 0:
            item = projeto_items[0]
            assert item["icon"] in ["folder-kanban", "trophy"], (
                f"Projeto icon should be folder-kanban or trophy, got {item['icon']}"
            )
            assert item["link"].startswith("/projetos"), f"Projeto link should start with /projetos, got {item['link']}"

    def test_activity_includes_events(self):
        """Activity includes events (evento type)"""
        response = requests.get(f"{BASE_URL}/api/activity/recent?limit=50", headers=self.admin_headers)
        assert response.status_code == 200

        data = response.json()
        evento_items = [item for item in data if item["type"] == "evento"]
        print(f"Found {len(evento_items)} evento items")

        if len(evento_items) > 0:
            item = evento_items[0]
            assert item["icon"] == "calendar", f"Evento icon should be calendar, got {item['icon']}"
            assert item["link"] == "/eventos", f"Evento link should be /eventos, got {item['link']}"

    def test_activity_includes_polls(self):
        """Activity includes polls (votacao type)"""
        response = requests.get(f"{BASE_URL}/api/activity/recent?limit=50", headers=self.admin_headers)
        assert response.status_code == 200

        data = response.json()
        votacao_items = [item for item in data if item["type"] == "votacao"]
        print(f"Found {len(votacao_items)} votacao items")

        if len(votacao_items) > 0:
            item = votacao_items[0]
            assert item["icon"] == "vote", f"Votacao icon should be vote, got {item['icon']}"
            assert item["link"] == "/votacoes", f"Votacao link should be /votacoes, got {item['link']}"

    # ===== ADMIN-ONLY FINANCIAL TRANSACTIONS =====

    def test_admin_sees_financial_transactions(self):
        """Admin user sees financial transactions in activity feed"""
        response = requests.get(f"{BASE_URL}/api/activity/recent?limit=50", headers=self.admin_headers)
        assert response.status_code == 200

        data = response.json()
        financeiro_items = [item for item in data if item["type"] == "financeiro"]
        print(f"Admin sees {len(financeiro_items)} financeiro items")

        if len(financeiro_items) > 0:
            item = financeiro_items[0]
            assert item["icon"] == "dollar-sign", f"Financeiro icon should be dollar-sign, got {item['icon']}"
            assert item["link"] == "/financeiro", f"Financeiro link should be /financeiro, got {item['link']}"

    def test_socio_does_not_see_financial_transactions(self):
        """Regular socio user does NOT see financial transactions in activity feed"""
        response = requests.get(f"{BASE_URL}/api/activity/recent?limit=50", headers=self.socio_headers)
        assert response.status_code == 200

        data = response.json()
        financeiro_items = [item for item in data if item["type"] == "financeiro"]
        assert len(financeiro_items) == 0, f"Socio should not see financeiro items, but found {len(financeiro_items)}"
        print("Socio correctly does not see financial transactions")

    # ===== INTEGRATION TEST =====

    def test_activity_feed_full_flow(self):
        """Full integration test - verify activity feed works end-to-end"""
        # 1. Get activity feed
        response = requests.get(f"{BASE_URL}/api/activity/recent", headers=self.admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # 2. Verify all items have required structure
        for item in data:
            assert "type" in item
            assert "icon" in item
            assert "title" in item
            assert "description" in item
            assert "link" in item
            assert "created_at" in item

        # 3. Count items by type
        type_counts = {}
        for item in data:
            t = item["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        print(f"Activity feed summary: {type_counts}")
        print(f"Total items: {len(data)}")

        # 4. Verify with different limit
        response2 = requests.get(f"{BASE_URL}/api/activity/recent?limit=3", headers=self.admin_headers)
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2) <= 3

        print("Full activity feed flow test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
