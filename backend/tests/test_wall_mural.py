"""
ACCTA Portal - Wall (Mural) API Tests
Tests for wall posts: create, filter by category, like/unlike, pin/unpin, approve/reject, comments, delete
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SOCIO_EMAIL = "socio1@controlador.cv"
SOCIO_PASSWORD = "socio123"
ADMIN_EMAIL = "admin@controlador.cv"
ADMIN_PASSWORD = "admin123"

# Store test data for cleanup
TEST_POST_IDS = []
TEST_COMMENT_IDS = []


@pytest.fixture(scope="module")
def socio_token():
    """Get socio auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SOCIO_EMAIL,
        "password": SOCIO_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Socio authentication failed")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def socio_headers(socio_token):
    """Headers with socio auth token"""
    return {"Authorization": f"Bearer {socio_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Headers with admin auth token"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestWallGetPosts:
    """Test GET /api/wall - Get approved wall posts"""
    
    def test_get_wall_posts_success(self, socio_headers):
        """Test getting approved wall posts"""
        response = requests.get(f"{BASE_URL}/api/wall", headers=socio_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/wall - Retrieved {len(data)} approved posts")
        
        # Check post structure if any posts exist
        if len(data) > 0:
            post = data[0]
            assert "id" in post
            assert "content" in post
            assert "user_name" in post
            assert "category" in post
            assert "likes" in post
            assert "comment_count" in post
            print(f"  - Sample post: {post['content'][:50]}... (category: {post['category']})")
    
    def test_get_wall_posts_filter_by_category(self, socio_headers):
        """Test filtering wall posts by category"""
        categories = ['geral', 'sugestao', 'discussao', 'aviso']
        for cat in categories:
            response = requests.get(f"{BASE_URL}/api/wall", params={"category": cat}, headers=socio_headers)
            assert response.status_code == 200, f"Expected 200 for category {cat}, got {response.status_code}"
            data = response.json()
            # All returned posts should have the requested category
            for post in data:
                assert post.get('category') == cat, f"Post category mismatch: expected {cat}, got {post.get('category')}"
            print(f"✓ GET /api/wall?category={cat} - Retrieved {len(data)} posts")
    
    def test_wall_requires_auth(self):
        """Test wall endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/wall")
        assert response.status_code in [401, 403]
        print("✓ GET /api/wall correctly requires authentication")


class TestWallPendingPosts:
    """Test GET /api/wall/pending - Get pending posts (admin/moderator only)"""
    
    def test_get_pending_posts_admin(self, admin_headers):
        """Admin can get pending posts"""
        response = requests.get(f"{BASE_URL}/api/wall/pending", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/wall/pending (admin) - Retrieved {len(data)} pending posts")
    
    def test_get_pending_posts_socio_forbidden(self, socio_headers):
        """Socio cannot get pending posts"""
        response = requests.get(f"{BASE_URL}/api/wall/pending", headers=socio_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ GET /api/wall/pending - Socio correctly forbidden (403)")


class TestWallCreatePost:
    """Test POST /api/wall - Create wall post"""
    
    def test_create_post_admin_auto_approved(self, admin_headers):
        """Admin posts are auto-approved"""
        post_data = {
            "content": "TEST_Admin post - auto approved",
            "category": "aviso"
        }
        response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["approved"] == True, "Admin post should be auto-approved"
        assert data["category"] == "aviso"
        assert "TEST_Admin post" in data["content"]
        TEST_POST_IDS.append(data["id"])
        print(f"✓ POST /api/wall (admin) - Post auto-approved: {data['id']}")
    
    def test_create_post_socio_pending(self, socio_headers):
        """Socio posts require approval"""
        post_data = {
            "content": "TEST_Socio post - needs approval",
            "category": "sugestao"
        }
        response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=socio_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["approved"] == False, "Socio post should require approval"
        assert data["category"] == "sugestao"
        TEST_POST_IDS.append(data["id"])
        print(f"✓ POST /api/wall (socio) - Post pending approval: {data['id']}")
    
    def test_create_post_all_categories(self, admin_headers):
        """Test creating posts with all category types"""
        categories = ['geral', 'sugestao', 'discussao', 'aviso']
        for cat in categories:
            post_data = {
                "content": f"TEST_Category test - {cat}",
                "category": cat
            }
            response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
            assert response.status_code == 200, f"Failed to create post with category {cat}"
            data = response.json()
            assert data["category"] == cat
            TEST_POST_IDS.append(data["id"])
            print(f"✓ POST /api/wall - Created post with category: {cat}")


class TestWallApprovePost:
    """Test PATCH /api/wall/{id}/approve - Approve pending post"""
    
    def test_approve_post_admin(self, admin_headers, socio_headers):
        """Admin can approve pending posts"""
        # First create a pending post as socio
        post_data = {"content": "TEST_Post to approve", "category": "geral"}
        create_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=socio_headers)
        assert create_response.status_code == 200
        post_id = create_response.json()["id"]
        TEST_POST_IDS.append(post_id)
        
        # Approve as admin
        response = requests.patch(f"{BASE_URL}/api/wall/{post_id}/approve", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ PATCH /api/wall/{post_id}/approve - Post approved by admin")
        
        # Verify post is now in approved list
        wall_response = requests.get(f"{BASE_URL}/api/wall", headers=socio_headers)
        approved_posts = wall_response.json()
        approved_ids = [p["id"] for p in approved_posts]
        assert post_id in approved_ids, "Approved post should appear in wall"
        print(f"✓ Verified post {post_id} now appears in approved wall posts")
    
    def test_approve_post_socio_forbidden(self, socio_headers, admin_headers):
        """Socio cannot approve posts"""
        # Create a pending post
        post_data = {"content": "TEST_Post socio cannot approve", "category": "geral"}
        create_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=socio_headers)
        post_id = create_response.json()["id"]
        TEST_POST_IDS.append(post_id)
        
        # Try to approve as socio
        response = requests.patch(f"{BASE_URL}/api/wall/{post_id}/approve", headers=socio_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ PATCH /api/wall/{id}/approve - Socio correctly forbidden (403)")


class TestWallLikePost:
    """Test PATCH /api/wall/{id}/like - Like/unlike post"""
    
    def test_like_post(self, socio_headers, admin_headers):
        """Test liking a post"""
        # Get an approved post
        wall_response = requests.get(f"{BASE_URL}/api/wall", headers=socio_headers)
        posts = wall_response.json()
        if len(posts) == 0:
            # Create one if none exist
            post_data = {"content": "TEST_Post for like test", "category": "geral"}
            create_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
            post_id = create_response.json()["id"]
            TEST_POST_IDS.append(post_id)
        else:
            post_id = posts[0]["id"]
        
        # Like the post
        response = requests.patch(f"{BASE_URL}/api/wall/{post_id}/like", headers=socio_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "liked" in data
        assert "like_count" in data
        print(f"✓ PATCH /api/wall/{post_id}/like - Liked: {data['liked']}, Count: {data['like_count']}")
    
    def test_unlike_post(self, socio_headers, admin_headers):
        """Test unliking a post (toggle)"""
        # Create a post and like it
        post_data = {"content": "TEST_Post for unlike test", "category": "geral"}
        create_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
        post_id = create_response.json()["id"]
        TEST_POST_IDS.append(post_id)
        
        # Like it first
        like_response = requests.patch(f"{BASE_URL}/api/wall/{post_id}/like", headers=socio_headers)
        assert like_response.json()["liked"] == True
        
        # Unlike it (toggle)
        unlike_response = requests.patch(f"{BASE_URL}/api/wall/{post_id}/like", headers=socio_headers)
        assert unlike_response.status_code == 200
        data = unlike_response.json()
        assert data["liked"] == False, "Second like should toggle to unlike"
        print(f"✓ PATCH /api/wall/{post_id}/like (toggle) - Unliked successfully")


class TestWallPinPost:
    """Test PATCH /api/wall/{id}/pin - Pin/unpin post (admin only)"""
    
    def test_pin_post_admin(self, admin_headers):
        """Admin can pin posts"""
        # Create a post
        post_data = {"content": "TEST_Post for pin test", "category": "aviso"}
        create_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
        post_id = create_response.json()["id"]
        TEST_POST_IDS.append(post_id)
        
        # Pin the post
        response = requests.patch(f"{BASE_URL}/api/wall/{post_id}/pin", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["pinned"] == True
        print(f"✓ PATCH /api/wall/{post_id}/pin - Post pinned")
        
        # Unpin (toggle)
        unpin_response = requests.patch(f"{BASE_URL}/api/wall/{post_id}/pin", headers=admin_headers)
        assert unpin_response.status_code == 200
        assert unpin_response.json()["pinned"] == False
        print(f"✓ PATCH /api/wall/{post_id}/pin (toggle) - Post unpinned")
    
    def test_pin_post_socio_forbidden(self, socio_headers, admin_headers):
        """Socio cannot pin posts"""
        # Create a post
        post_data = {"content": "TEST_Post socio cannot pin", "category": "geral"}
        create_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
        post_id = create_response.json()["id"]
        TEST_POST_IDS.append(post_id)
        
        # Try to pin as socio
        response = requests.patch(f"{BASE_URL}/api/wall/{post_id}/pin", headers=socio_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ PATCH /api/wall/{id}/pin - Socio correctly forbidden (403)")


class TestWallComments:
    """Test wall post comments endpoints"""
    
    def test_create_comment(self, socio_headers, admin_headers):
        """Test creating a comment on a post"""
        # Create a post
        post_data = {"content": "TEST_Post for comment test", "category": "discussao"}
        create_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
        post_id = create_response.json()["id"]
        TEST_POST_IDS.append(post_id)
        
        # Create a comment
        comment_data = {"content": "TEST_Comment on post"}
        response = requests.post(f"{BASE_URL}/api/wall/{post_id}/comments", json=comment_data, headers=socio_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["content"] == "TEST_Comment on post"
        assert data["post_id"] == post_id
        TEST_COMMENT_IDS.append((post_id, data["id"]))
        print(f"✓ POST /api/wall/{post_id}/comments - Comment created: {data['id']}")
    
    def test_get_comments(self, socio_headers, admin_headers):
        """Test getting comments for a post"""
        # Create a post with comments
        post_data = {"content": "TEST_Post for get comments test", "category": "geral"}
        create_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
        post_id = create_response.json()["id"]
        TEST_POST_IDS.append(post_id)
        
        # Add a comment
        comment_data = {"content": "TEST_Comment to retrieve"}
        requests.post(f"{BASE_URL}/api/wall/{post_id}/comments", json=comment_data, headers=socio_headers)
        
        # Get comments
        response = requests.get(f"{BASE_URL}/api/wall/{post_id}/comments", headers=socio_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        print(f"✓ GET /api/wall/{post_id}/comments - Retrieved {len(data)} comments")
    
    def test_delete_comment_owner(self, socio_headers, admin_headers):
        """Comment owner can delete their comment"""
        # Create a post
        post_data = {"content": "TEST_Post for delete comment test", "category": "geral"}
        create_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
        post_id = create_response.json()["id"]
        TEST_POST_IDS.append(post_id)
        
        # Create a comment as socio
        comment_data = {"content": "TEST_Comment to delete"}
        comment_response = requests.post(f"{BASE_URL}/api/wall/{post_id}/comments", json=comment_data, headers=socio_headers)
        comment_id = comment_response.json()["id"]
        
        # Delete comment as socio (owner)
        response = requests.delete(f"{BASE_URL}/api/wall/{post_id}/comments/{comment_id}", headers=socio_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ DELETE /api/wall/{post_id}/comments/{comment_id} - Comment deleted by owner")
    
    def test_delete_comment_admin(self, socio_headers, admin_headers):
        """Admin can delete any comment"""
        # Create a post
        post_data = {"content": "TEST_Post for admin delete comment", "category": "geral"}
        create_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
        post_id = create_response.json()["id"]
        TEST_POST_IDS.append(post_id)
        
        # Create a comment as socio
        comment_data = {"content": "TEST_Comment admin will delete"}
        comment_response = requests.post(f"{BASE_URL}/api/wall/{post_id}/comments", json=comment_data, headers=socio_headers)
        comment_id = comment_response.json()["id"]
        
        # Delete comment as admin
        response = requests.delete(f"{BASE_URL}/api/wall/{post_id}/comments/{comment_id}", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ DELETE /api/wall/{post_id}/comments/{comment_id} - Comment deleted by admin")


class TestWallDeletePost:
    """Test DELETE /api/wall/{id} - Delete wall post"""
    
    def test_delete_post_owner(self, socio_headers, admin_headers):
        """Post owner can delete their post"""
        # Create a post as socio (will be pending)
        post_data = {"content": "TEST_Post owner will delete", "category": "geral"}
        create_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=socio_headers)
        post_id = create_response.json()["id"]
        
        # Delete as owner
        response = requests.delete(f"{BASE_URL}/api/wall/{post_id}", headers=socio_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ DELETE /api/wall/{post_id} - Post deleted by owner")
    
    def test_delete_post_admin(self, admin_headers):
        """Admin can delete any post"""
        # Create a post
        post_data = {"content": "TEST_Post admin will delete", "category": "geral"}
        create_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
        post_id = create_response.json()["id"]
        
        # Delete as admin
        response = requests.delete(f"{BASE_URL}/api/wall/{post_id}", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ DELETE /api/wall/{post_id} - Post deleted by admin")
    
    def test_delete_post_not_found(self, admin_headers):
        """Deleting non-existent post returns 404"""
        response = requests.delete(f"{BASE_URL}/api/wall/non-existent-id", headers=admin_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ DELETE /api/wall/non-existent-id - Returns 404")


class TestWallPinnedPostsOrder:
    """Test that pinned posts appear first"""
    
    def test_pinned_posts_first(self, admin_headers, socio_headers):
        """Pinned posts should appear before non-pinned posts"""
        # Create a regular post
        post_data = {"content": "TEST_Regular post for order test", "category": "geral"}
        regular_response = requests.post(f"{BASE_URL}/api/wall", json=post_data, headers=admin_headers)
        regular_id = regular_response.json()["id"]
        TEST_POST_IDS.append(regular_id)
        
        # Create and pin another post
        pinned_data = {"content": "TEST_Pinned post for order test", "category": "aviso"}
        pinned_response = requests.post(f"{BASE_URL}/api/wall", json=pinned_data, headers=admin_headers)
        pinned_id = pinned_response.json()["id"]
        TEST_POST_IDS.append(pinned_id)
        
        # Pin the second post
        requests.patch(f"{BASE_URL}/api/wall/{pinned_id}/pin", headers=admin_headers)
        
        # Get wall posts
        wall_response = requests.get(f"{BASE_URL}/api/wall", headers=socio_headers)
        posts = wall_response.json()
        
        # Find positions
        pinned_posts = [p for p in posts if p.get("pinned")]
        non_pinned_posts = [p for p in posts if not p.get("pinned")]
        
        if pinned_posts and non_pinned_posts:
            # All pinned posts should come before non-pinned
            pinned_indices = [posts.index(p) for p in pinned_posts]
            non_pinned_indices = [posts.index(p) for p in non_pinned_posts]
            assert max(pinned_indices) < min(non_pinned_indices), "Pinned posts should appear first"
            print("✓ Pinned posts correctly appear before non-pinned posts")
        else:
            print("✓ Order test skipped (not enough posts to compare)")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_posts(self, admin_headers):
        """Clean up TEST_ prefixed posts"""
        # Get all posts
        wall_response = requests.get(f"{BASE_URL}/api/wall", headers=admin_headers)
        posts = wall_response.json()
        
        # Also get pending posts
        pending_response = requests.get(f"{BASE_URL}/api/wall/pending", headers=admin_headers)
        pending_posts = pending_response.json()
        
        all_posts = posts + pending_posts
        deleted_count = 0
        
        for post in all_posts:
            if post.get("content", "").startswith("TEST_"):
                try:
                    requests.delete(f"{BASE_URL}/api/wall/{post['id']}", headers=admin_headers)
                    deleted_count += 1
                except:
                    pass
        
        print(f"✓ Cleanup: Deleted {deleted_count} test posts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
