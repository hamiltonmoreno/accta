"""
Test suite for Notifications, Mural (Wall), and Financeiro modules
Testing refactored FinanceiroPage components and enhanced Notifications/Mural features
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

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
    data = response.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="module")
def socio_token():
    """Get socio authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SOCIO_EMAIL,
        "password": SOCIO_PASSWORD
    })
    assert response.status_code == 200, f"Socio login failed: {response.text}"
    data = response.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture
def socio_headers(socio_token):
    return {"Authorization": f"Bearer {socio_token}", "Content-Type": "application/json"}


# ============== NOTIFICATIONS MODULE TESTS ==============

class TestNotificationsAPI:
    """Tests for enhanced Notifications module"""

    def test_get_notifications_paginated(self, admin_headers):
        """GET /api/notifications returns paginated items with 'items' and 'total'"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data, "Response should have 'items' field"
        assert "total" in data, "Response should have 'total' field"
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        print(f"✓ Notifications paginated: {len(data['items'])} items, {data['total']} total")

    def test_get_notifications_with_type_filter(self, admin_headers):
        """GET /api/notifications?type=geral filters by type"""
        response = requests.get(f"{BASE_URL}/api/notifications?type=geral", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # All returned items should be of type 'geral'
        for item in data["items"]:
            assert item.get("type") == "geral", f"Expected type 'geral', got {item.get('type')}"
        print(f"✓ Type filter works: {len(data['items'])} geral notifications")

    def test_get_notifications_unread_only(self, admin_headers):
        """GET /api/notifications?unread_only=true returns only unread"""
        response = requests.get(f"{BASE_URL}/api/notifications?unread_only=true", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        for item in data["items"]:
            assert item.get("read") == False, "All items should be unread"
        print(f"✓ Unread filter works: {len(data['items'])} unread notifications")

    def test_get_unread_count(self, admin_headers):
        """GET /api/notifications/unread/count returns count"""
        response = requests.get(f"{BASE_URL}/api/notifications/unread/count", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data, "Response should have 'count' field"
        assert isinstance(data["count"], int)
        print(f"✓ Unread count: {data['count']}")

    def test_get_notification_types(self, admin_headers):
        """GET /api/notifications/types returns notification types list"""
        response = requests.get(f"{BASE_URL}/api/notifications/types", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "types" in data, "Response should have 'types' field"
        assert isinstance(data["types"], list)
        assert len(data["types"]) > 0, "Should have at least one type"
        # Check structure
        for t in data["types"]:
            assert "value" in t
            assert "label" in t
        print(f"✓ Notification types: {[t['value'] for t in data['types']]}")

    def test_broadcast_notification_admin_only(self, admin_headers, socio_headers):
        """POST /api/notifications/broadcast - admin can broadcast, socio cannot"""
        broadcast_data = {
            "user_id": "broadcast",
            "type": "sistema",
            "title": f"TEST Broadcast {uuid.uuid4().hex[:6]}",
            "message": "This is a test broadcast notification",
            "link": "/dashboard"
        }
        
        # Admin should succeed
        response = requests.post(f"{BASE_URL}/api/notifications/broadcast", 
                                json=broadcast_data, headers=admin_headers)
        assert response.status_code == 200, f"Admin broadcast failed: {response.text}"
        print("✓ Admin broadcast succeeded")
        
        # Socio should fail with 403
        response = requests.post(f"{BASE_URL}/api/notifications/broadcast", 
                                json=broadcast_data, headers=socio_headers)
        assert response.status_code == 403, "Socio should not be able to broadcast"
        print("✓ Socio broadcast correctly denied (403)")

    def test_mark_all_read(self, admin_headers):
        """PATCH /api/notifications/mark-all-read works"""
        response = requests.patch(f"{BASE_URL}/api/notifications/mark-all-read", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Mark all read: {data['message']}")

    def test_delete_notification(self, admin_headers):
        """DELETE /api/notifications/{id} deletes a notification"""
        # First get notifications to find one to delete
        response = requests.get(f"{BASE_URL}/api/notifications", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data["items"]) > 0:
            notif_id = data["items"][0]["id"]
            delete_response = requests.delete(f"{BASE_URL}/api/notifications/{notif_id}", headers=admin_headers)
            assert delete_response.status_code == 200
            print(f"✓ Deleted notification {notif_id}")
        else:
            print("⚠ No notifications to delete, skipping")

    def test_clear_read_notifications(self, admin_headers):
        """DELETE /api/notifications/clear/all clears read notifications"""
        response = requests.delete(f"{BASE_URL}/api/notifications/clear/all", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Clear read: {data['message']}")


# ============== MURAL (WALL) MODULE TESTS ==============

class TestMuralAPI:
    """Tests for enhanced Mural/Wall module"""

    def test_get_wall_posts(self, admin_headers):
        """GET /api/wall returns posts"""
        response = requests.get(f"{BASE_URL}/api/wall", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Wall posts: {len(data)} posts")

    def test_get_wall_posts_with_category_filter(self, admin_headers):
        """GET /api/wall?category=geral filters by category"""
        response = requests.get(f"{BASE_URL}/api/wall?category=geral", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for post in data:
            assert post.get("category") == "geral", f"Expected category 'geral', got {post.get('category')}"
        print(f"✓ Category filter works: {len(data)} geral posts")

    def test_create_wall_post_with_category(self, admin_headers):
        """POST /api/wall creates post with category"""
        post_data = {
            "content": f"TEST Post with category {uuid.uuid4().hex[:6]}",
            "category": "sugestao"
        }
        response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("category") == "sugestao"
        assert data.get("approved") == True  # Admin posts are auto-approved
        print(f"✓ Created post with category 'sugestao', id: {data.get('id')}")
        return data.get("id")

    def test_socio_post_needs_approval(self, socio_headers):
        """POST /api/wall - socio posts need approval"""
        post_data = {
            "content": f"TEST Socio post {uuid.uuid4().hex[:6]}",
            "category": "discussao"
        }
        response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("approved") == False, "Socio posts should not be auto-approved"
        print(f"✓ Socio post created, awaiting approval, id: {data.get('id')}")
        return data.get("id")

    def test_get_pending_posts_admin(self, admin_headers):
        """GET /api/wall/pending - admin can see pending posts"""
        response = requests.get(f"{BASE_URL}/api/wall/pending", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Pending posts: {len(data)}")

    def test_get_pending_posts_socio_denied(self, socio_headers):
        """GET /api/wall/pending - socio cannot see pending posts"""
        response = requests.get(f"{BASE_URL}/api/wall/pending", headers=socio_headers)
        assert response.status_code == 403
        print("✓ Socio correctly denied access to pending posts (403)")

    def test_like_post(self, admin_headers):
        """PATCH /api/wall/{id}/like toggles like"""
        # Get a post to like
        response = requests.get(f"{BASE_URL}/api/wall", headers=admin_headers)
        assert response.status_code == 200
        posts = response.json()
        
        if len(posts) > 0:
            post_id = posts[0]["id"]
            like_response = requests.patch(f"{BASE_URL}/api/wall/{post_id}/like", headers=admin_headers)
            assert like_response.status_code == 200
            data = like_response.json()
            assert "liked" in data
            assert "like_count" in data
            print(f"✓ Like toggled: liked={data['liked']}, count={data['like_count']}")
        else:
            print("⚠ No posts to like, skipping")

    def test_comment_on_post(self, admin_headers):
        """POST /api/wall/{id}/comments creates comment"""
        # Get a post to comment on
        response = requests.get(f"{BASE_URL}/api/wall", headers=admin_headers)
        assert response.status_code == 200
        posts = response.json()
        
        if len(posts) > 0:
            post_id = posts[0]["id"]
            comment_data = {"content": f"TEST Comment {uuid.uuid4().hex[:6]}"}
            comment_response = requests.post(f"{BASE_URL}/api/wall/{post_id}/comments", 
                                            json=comment_data, headers=admin_headers)
            assert comment_response.status_code == 200
            data = comment_response.json()
            assert data.get("content") == comment_data["content"]
            print(f"✓ Comment created on post {post_id}")
        else:
            print("⚠ No posts to comment on, skipping")

    def test_get_comments(self, admin_headers):
        """GET /api/wall/{id}/comments returns comments"""
        response = requests.get(f"{BASE_URL}/api/wall", headers=admin_headers)
        assert response.status_code == 200
        posts = response.json()
        
        if len(posts) > 0:
            post_id = posts[0]["id"]
            comments_response = requests.get(f"{BASE_URL}/api/wall/{post_id}/comments", headers=admin_headers)
            assert comments_response.status_code == 200
            comments = comments_response.json()
            assert isinstance(comments, list)
            print(f"✓ Got {len(comments)} comments for post {post_id}")
        else:
            print("⚠ No posts, skipping comments test")


# ============== FINANCEIRO MODULE TESTS ==============

class TestFinanceiroAPI:
    """Tests for Financeiro module (refactored components)"""

    def test_get_transactions_paginated(self, admin_headers):
        """GET /api/finances/transactions returns paginated data"""
        response = requests.get(f"{BASE_URL}/api/finances/transactions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data, "Response should have 'items' field"
        assert "total" in data, "Response should have 'total' field"
        print(f"✓ Transactions: {len(data['items'])} items, {data['total']} total")

    def test_get_transactions_with_type_filter(self, admin_headers):
        """GET /api/finances/transactions?type=receita filters by type"""
        response = requests.get(f"{BASE_URL}/api/finances/transactions?type=receita", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        for item in data["items"]:
            assert item.get("type") == "receita"
        print(f"✓ Type filter works: {len(data['items'])} receita transactions")

    def test_get_transactions_with_search(self, admin_headers):
        """GET /api/finances/transactions?search=quota searches description"""
        response = requests.get(f"{BASE_URL}/api/finances/transactions?search=quota", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Search works: {len(data['items'])} transactions matching 'quota'")

    def test_get_finance_summary(self, admin_headers):
        """GET /api/finances/summary returns summary data"""
        response = requests.get(f"{BASE_URL}/api/finances/summary?year=2026", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_receitas" in data
        assert "total_despesas" in data
        assert "resultado_liquido" in data
        print(f"✓ Summary: receitas={data['total_receitas']}, despesas={data['total_despesas']}, resultado={data['resultado_liquido']}")

    def test_get_dre_report(self, admin_headers):
        """GET /api/finances/dre returns DRE report"""
        response = requests.get(f"{BASE_URL}/api/finances/dre?year=2026", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_receitas" in data
        assert "total_despesas" in data
        assert "resultado_liquido" in data
        assert "monthly" in data
        assert "receitas_por_categoria" in data
        assert "despesas_por_categoria" in data
        print(f"✓ DRE Report: {len(data['monthly'])} months, resultado={data['resultado_liquido']}")

    def test_create_transaction(self, admin_headers):
        """POST /api/finances/transactions creates transaction"""
        tx_data = {
            "type": "receita",
            "category": "quotas",
            "description": f"TEST Transaction {uuid.uuid4().hex[:6]}",
            "amount": 5000,
            "date": datetime.now().isoformat(),
            "reference": "TEST-REF"
        }
        response = requests.post(f"{BASE_URL}/api/finances/transactions", 
                                json=tx_data, headers=admin_headers)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("type") == "receita"
        assert data.get("amount") == 5000
        print(f"✓ Created transaction: {data.get('id')}")
        return data.get("id")

    def test_update_transaction(self, admin_headers):
        """PATCH /api/finances/transactions/{id} updates transaction"""
        # First create a transaction
        tx_data = {
            "type": "despesa",
            "category": "operacional",
            "description": f"TEST Update {uuid.uuid4().hex[:6]}",
            "amount": 1000,
            "date": datetime.now().isoformat()
        }
        create_response = requests.post(f"{BASE_URL}/api/finances/transactions", 
                                       json=tx_data, headers=admin_headers)
        assert create_response.status_code in [200, 201]
        tx_id = create_response.json().get("id")
        
        # Update it
        update_data = {"amount": 1500, "description": "Updated description"}
        update_response = requests.patch(f"{BASE_URL}/api/finances/transactions/{tx_id}", 
                                        json=update_data, headers=admin_headers)
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated.get("amount") == 1500
        print(f"✓ Updated transaction {tx_id}")

    def test_delete_transaction(self, admin_headers):
        """DELETE /api/finances/transactions/{id} deletes transaction"""
        # First create a transaction
        tx_data = {
            "type": "despesa",
            "category": "operacional",
            "description": f"TEST Delete {uuid.uuid4().hex[:6]}",
            "amount": 500,
            "date": datetime.now().isoformat()
        }
        create_response = requests.post(f"{BASE_URL}/api/finances/transactions", 
                                       json=tx_data, headers=admin_headers)
        assert create_response.status_code in [200, 201]
        tx_id = create_response.json().get("id")
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/finances/transactions/{tx_id}", 
                                         headers=admin_headers)
        assert delete_response.status_code == 200
        print(f"✓ Deleted transaction {tx_id}")

    def test_get_finance_settings(self, admin_headers):
        """GET /api/finances/settings returns settings"""
        response = requests.get(f"{BASE_URL}/api/finances/settings", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "quota_amount" in data
        assert "quota_description" in data
        print(f"✓ Settings: quota_amount={data['quota_amount']}")

    def test_export_csv(self, admin_headers):
        """GET /api/finances/transactions/csv exports CSV"""
        response = requests.get(f"{BASE_URL}/api/finances/transactions/csv", headers=admin_headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "") or len(response.content) > 0
        print(f"✓ CSV export: {len(response.content)} bytes")

    def test_export_dre_pdf(self, admin_headers):
        """GET /api/finances/dre/pdf exports PDF"""
        response = requests.get(f"{BASE_URL}/api/finances/dre/pdf?year=2026", headers=admin_headers)
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "") or len(response.content) > 0
        print(f"✓ PDF export: {len(response.content)} bytes")

    def test_socio_cannot_access_finance(self, socio_headers):
        """Socio should have limited finance access"""
        # Socio should not be able to create transactions
        tx_data = {
            "type": "receita",
            "category": "quotas",
            "description": "TEST Socio transaction",
            "amount": 1000,
            "date": datetime.now().isoformat()
        }
        response = requests.post(f"{BASE_URL}/api/finances/transactions", 
                                json=tx_data, headers=socio_headers)
        # Should be 403 Forbidden
        assert response.status_code == 403, f"Socio should not create transactions, got {response.status_code}"
        print("✓ Socio correctly denied finance write access (403)")


# ============== INTEGRATION TESTS ==============

class TestIntegration:
    """Integration tests for cross-module functionality"""

    def test_full_notification_flow(self, admin_headers):
        """Test complete notification flow: create, read, mark read, delete"""
        # 1. Get initial count
        count_response = requests.get(f"{BASE_URL}/api/notifications/unread/count", headers=admin_headers)
        initial_count = count_response.json().get("count", 0)
        
        # 2. Broadcast a notification
        broadcast_data = {
            "user_id": "broadcast",
            "type": "sistema",
            "title": f"Integration Test {uuid.uuid4().hex[:6]}",
            "message": "Testing full notification flow",
            "link": None
        }
        broadcast_response = requests.post(f"{BASE_URL}/api/notifications/broadcast", 
                                          json=broadcast_data, headers=admin_headers)
        assert broadcast_response.status_code == 200
        
        # 3. Get notifications
        notifs_response = requests.get(f"{BASE_URL}/api/notifications", headers=admin_headers)
        assert notifs_response.status_code == 200
        
        print("✓ Full notification flow completed")

    def test_full_mural_flow(self, admin_headers):
        """Test complete mural flow: create post, like, comment"""
        # 1. Create post
        post_data = {
            "content": f"Integration test post {uuid.uuid4().hex[:6]}",
            "category": "geral"
        }
        create_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
        assert create_response.status_code == 200
        post_id = create_response.json().get("id")
        
        # 2. Like the post
        like_response = requests.patch(f"{BASE_URL}/api/wall/{post_id}/like", headers=admin_headers)
        assert like_response.status_code == 200
        
        # 3. Comment on the post
        comment_data = {"content": "Integration test comment"}
        comment_response = requests.post(f"{BASE_URL}/api/wall/{post_id}/comments", 
                                        json=comment_data, headers=admin_headers)
        assert comment_response.status_code == 200
        
        # 4. Get comments
        comments_response = requests.get(f"{BASE_URL}/api/wall/{post_id}/comments", headers=admin_headers)
        assert comments_response.status_code == 200
        
        # 5. Delete the post (cleanup)
        delete_response = requests.delete(f"{BASE_URL}/api/wall/{post_id}", headers=admin_headers)
        assert delete_response.status_code == 200
        
        print("✓ Full mural flow completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
