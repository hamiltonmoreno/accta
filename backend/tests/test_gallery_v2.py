"""
Gallery API Tests v2 - Comprehensive testing for Photo Gallery module
Tests: Public vs Private galleries, approval workflow, visibility, CRUD operations
Categories: Aeroportos, Eventos, Equipa, Formacoes
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@accta.cv"
ADMIN_PASSWORD = "admin123"
SOCIO_EMAIL = "socio1@accta.cv"
SOCIO_PASSWORD = "socio123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.text}")
    return response.json()['access_token']


@pytest.fixture(scope="module")
def socio_token():
    """Get socio auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SOCIO_EMAIL,
        "password": SOCIO_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Socio login failed: {response.text}")
    return response.json()['access_token']


class TestPublicGalleryEndpoints:
    """Test PUBLIC gallery endpoints (no auth required) - /api/gallery/public/*"""
    
    def test_public_albums_returns_only_public(self):
        """GET /api/gallery/public/albums should return ONLY public albums (not private 'A Nossa Equipa')"""
        response = requests.get(f"{BASE_URL}/api/gallery/public/albums")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        albums = response.json()
        assert isinstance(albums, list), "Response should be a list"
        
        # Check that private album 'A Nossa Equipa' (album-equipa) is NOT in public list
        album_ids = [a['id'] for a in albums]
        album_titles = [a['title'] for a in albums]
        
        # album-equipa should be private and NOT appear in public list
        assert 'album-equipa' not in album_ids, "Private album 'album-equipa' should NOT be in public albums"
        
        # Check visibility field
        for album in albums:
            assert album.get('visibility') == 'public', f"Album {album['id']} should have visibility='public'"
        
        print(f"PASS: GET /api/gallery/public/albums returned {len(albums)} public albums: {album_ids}")
        print(f"PASS: Private album 'album-equipa' correctly excluded from public list")
    
    def test_public_albums_have_photo_count(self):
        """Public albums should have photo_count field"""
        response = requests.get(f"{BASE_URL}/api/gallery/public/albums")
        assert response.status_code == 200
        
        albums = response.json()
        for album in albums:
            assert 'photo_count' in album, f"Album {album['id']} missing photo_count"
            assert album['photo_count'] > 0, f"Album {album['id']} has 0 photos (should be filtered out)"
        
        print(f"PASS: All public albums have photo_count > 0")
    
    def test_public_photos_returns_approved_only(self):
        """GET /api/gallery/public/photos should return ONLY approved photos from public albums"""
        response = requests.get(f"{BASE_URL}/api/gallery/public/photos")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        photos = response.json()
        assert isinstance(photos, list), "Response should be a list"
        
        # All photos should be approved
        for photo in photos:
            assert photo.get('status') == 'approved', f"Photo {photo['id']} should have status='approved'"
        
        print(f"PASS: GET /api/gallery/public/photos returned {len(photos)} approved photos")
    
    def test_public_photos_by_album(self):
        """GET /api/gallery/public/photos?album_id=X should return photos for specific public album"""
        # First get public albums
        albums_response = requests.get(f"{BASE_URL}/api/gallery/public/albums")
        assert albums_response.status_code == 200
        albums = albums_response.json()
        
        if len(albums) > 0:
            album_id = albums[0]['id']
            response = requests.get(f"{BASE_URL}/api/gallery/public/photos", params={"album_id": album_id})
            assert response.status_code == 200
            
            photos = response.json()
            for photo in photos:
                assert photo['album_id'] == album_id, f"Photo album_id mismatch"
                assert photo['status'] == 'approved', f"Photo should be approved"
            
            print(f"PASS: GET /api/gallery/public/photos?album_id={album_id} returned {len(photos)} photos")
    
    def test_public_photos_private_album_returns_404(self):
        """GET /api/gallery/public/photos?album_id=album-equipa should return 404 (private album)"""
        response = requests.get(f"{BASE_URL}/api/gallery/public/photos", params={"album_id": "album-equipa"})
        assert response.status_code == 404, f"Expected 404 for private album, got {response.status_code}"
        print("PASS: Accessing private album via public endpoint returns 404")


class TestPrivateGalleryEndpoints:
    """Test PRIVATE gallery endpoints (auth required) - /api/gallery/*"""
    
    def test_private_albums_requires_auth(self):
        """GET /api/gallery/albums should require authentication"""
        response = requests.get(f"{BASE_URL}/api/gallery/albums")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: GET /api/gallery/albums requires authentication")
    
    def test_private_albums_returns_all_including_private(self, admin_token):
        """GET /api/gallery/albums (auth) should return ALL albums including private ones"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/gallery/albums", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        albums = response.json()
        album_ids = [a['id'] for a in albums]
        
        # Should include private album 'album-equipa'
        assert 'album-equipa' in album_ids, "Private album 'album-equipa' should be in authenticated albums list"
        
        # Check we have both public and private albums
        visibilities = set(a.get('visibility', 'public') for a in albums)
        assert 'private' in visibilities, "Should have at least one private album"
        assert 'public' in visibilities, "Should have at least one public album"
        
        print(f"PASS: GET /api/gallery/albums (auth) returned {len(albums)} albums including private")
    
    def test_private_photos_returns_approved_for_socio(self, socio_token):
        """GET /api/gallery/photos (socio) should return only approved photos"""
        headers = {"Authorization": f"Bearer {socio_token}"}
        response = requests.get(f"{BASE_URL}/api/gallery/photos", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        photos = response.json()
        for photo in photos:
            assert photo.get('status') == 'approved', f"Socio should only see approved photos"
        
        print(f"PASS: GET /api/gallery/photos (socio) returned {len(photos)} approved photos")
    
    def test_private_photos_admin_can_filter_by_status(self, admin_token):
        """GET /api/gallery/photos?status=pending (admin) should filter by status"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/gallery/photos", params={"status": "approved"}, headers=headers)
        assert response.status_code == 200
        
        photos = response.json()
        for photo in photos:
            assert photo.get('status') == 'approved', f"Filter by status should work"
        
        print(f"PASS: Admin can filter photos by status")


class TestAlbumCRUD:
    """Test Album CRUD operations (admin only)"""
    
    def test_create_album_requires_admin(self, socio_token):
        """POST /api/gallery/albums should require admin role"""
        headers = {"Authorization": f"Bearer {socio_token}"}
        response = requests.post(
            f"{BASE_URL}/api/gallery/albums",
            json={"title": "Test Album", "description": "Test", "visibility": "public"},
            headers=headers
        )
        assert response.status_code == 403, f"Expected 403 for socio, got {response.status_code}"
        print("PASS: Create album requires admin (socio gets 403)")
    
    def test_admin_create_album_with_visibility(self, admin_token):
        """Admin should be able to create album with visibility field"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        album_data = {
            "title": "TEST_Album_Visibility",
            "description": "Test album with visibility",
            "visibility": "private",
            "order": 99
        }
        response = requests.post(
            f"{BASE_URL}/api/gallery/albums",
            json=album_data,
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        created = response.json()
        assert created['title'] == album_data['title']
        assert created['visibility'] == 'private', "Visibility should be 'private'"
        
        print(f"PASS: Admin created album with visibility='private': {created['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/gallery/albums/{created['id']}", headers=headers)
    
    def test_update_album_requires_admin(self, socio_token):
        """PATCH /api/gallery/albums/{id} should require admin"""
        headers = {"Authorization": f"Bearer {socio_token}"}
        response = requests.patch(
            f"{BASE_URL}/api/gallery/albums/album-aeroportos",
            json={"title": "Hacked Title"},
            headers=headers
        )
        assert response.status_code == 403, f"Expected 403 for socio, got {response.status_code}"
        print("PASS: Update album requires admin (socio gets 403)")
    
    def test_admin_update_album(self, admin_token):
        """Admin should be able to update album"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create test album first
        create_response = requests.post(
            f"{BASE_URL}/api/gallery/albums",
            json={"title": "TEST_Album_Update", "description": "Original", "visibility": "public"},
            headers=headers
        )
        assert create_response.status_code == 200
        album_id = create_response.json()['id']
        
        # Update it
        update_response = requests.patch(
            f"{BASE_URL}/api/gallery/albums/{album_id}",
            json={"title": "TEST_Album_Updated", "description": "Updated desc"},
            headers=headers
        )
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}"
        
        print(f"PASS: Admin updated album {album_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/gallery/albums/{album_id}", headers=headers)
    
    def test_delete_album_requires_admin(self, socio_token):
        """DELETE /api/gallery/albums/{id} should require admin"""
        headers = {"Authorization": f"Bearer {socio_token}"}
        response = requests.delete(
            f"{BASE_URL}/api/gallery/albums/album-aeroportos",
            headers=headers
        )
        assert response.status_code == 403, f"Expected 403 for socio, got {response.status_code}"
        print("PASS: Delete album requires admin (socio gets 403)")
    
    def test_admin_delete_album_and_photos(self, admin_token):
        """DELETE /api/gallery/albums/{id} should delete album and all photos"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create test album
        create_response = requests.post(
            f"{BASE_URL}/api/gallery/albums",
            json={"title": "TEST_Album_Delete", "description": "To be deleted", "visibility": "public"},
            headers=headers
        )
        assert create_response.status_code == 200
        album_id = create_response.json()['id']
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/gallery/albums/{album_id}", headers=headers)
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        
        # Verify it's gone
        get_response = requests.get(f"{BASE_URL}/api/gallery/albums/{album_id}", headers=headers)
        assert get_response.status_code == 404, "Deleted album should return 404"
        
        print(f"PASS: Admin deleted album {album_id} and verified it's gone")


class TestPhotoUploadAndApproval:
    """Test photo upload and approval workflow"""
    
    def test_admin_upload_auto_approved(self, admin_token):
        """POST /api/gallery/photos/upload as admin -> auto-approved (status='approved')"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a simple test image
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        files = {'file': ('test_admin.png', io.BytesIO(image_content), 'image/png')}
        
        response = requests.post(
            f"{BASE_URL}/api/gallery/photos/upload",
            params={"album_id": "album-aeroportos", "caption": "TEST_Admin_Upload"},
            headers=headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        photo = response.json()
        assert photo['status'] == 'approved', f"Admin upload should be auto-approved, got {photo['status']}"
        
        print(f"PASS: Admin upload auto-approved: {photo['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/gallery/photos/{photo['id']}", headers=headers)
    
    def test_socio_upload_pending(self, socio_token, admin_token):
        """POST /api/gallery/photos/upload as socio -> pending (status='pending')"""
        headers = {"Authorization": f"Bearer {socio_token}"}
        
        # Create a simple test image
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        files = {'file': ('test_socio.png', io.BytesIO(image_content), 'image/png')}
        
        response = requests.post(
            f"{BASE_URL}/api/gallery/photos/upload",
            params={"album_id": "album-aeroportos", "caption": "TEST_Socio_Upload"},
            headers=headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        photo = response.json()
        assert photo['status'] == 'pending', f"Socio upload should be pending, got {photo['status']}"
        
        print(f"PASS: Socio upload is pending: {photo['id']}")
        
        # Cleanup with admin token
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        requests.delete(f"{BASE_URL}/api/gallery/photos/{photo['id']}", headers=admin_headers)
    
    def test_get_pending_photos_admin_only(self, socio_token, admin_token):
        """GET /api/gallery/photos/pending should be admin only"""
        # Socio should get 403
        socio_headers = {"Authorization": f"Bearer {socio_token}"}
        socio_response = requests.get(f"{BASE_URL}/api/gallery/photos/pending", headers=socio_headers)
        assert socio_response.status_code == 403, f"Expected 403 for socio, got {socio_response.status_code}"
        
        # Admin should get 200
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        admin_response = requests.get(f"{BASE_URL}/api/gallery/photos/pending", headers=admin_headers)
        assert admin_response.status_code == 200, f"Expected 200 for admin, got {admin_response.status_code}"
        
        pending = admin_response.json()
        assert isinstance(pending, list), "Response should be a list"
        
        print(f"PASS: GET /api/gallery/photos/pending is admin-only, returned {len(pending)} pending photos")
    
    def test_approve_photo_admin_only(self, socio_token, admin_token):
        """PATCH /api/gallery/photos/{id}/approve should be admin only"""
        # First upload a photo as socio to get a pending photo
        socio_headers = {"Authorization": f"Bearer {socio_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        files = {'file': ('test_approve.png', io.BytesIO(image_content), 'image/png')}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/gallery/photos/upload",
            params={"album_id": "album-aeroportos", "caption": "TEST_Approve"},
            headers=socio_headers,
            files=files
        )
        assert upload_response.status_code == 200
        photo_id = upload_response.json()['id']
        
        # Socio should not be able to approve
        socio_approve = requests.patch(f"{BASE_URL}/api/gallery/photos/{photo_id}/approve", headers=socio_headers)
        assert socio_approve.status_code == 403, f"Expected 403 for socio approve, got {socio_approve.status_code}"
        
        # Admin should be able to approve
        admin_approve = requests.patch(f"{BASE_URL}/api/gallery/photos/{photo_id}/approve", headers=admin_headers)
        assert admin_approve.status_code == 200, f"Expected 200 for admin approve, got {admin_approve.status_code}"
        
        print(f"PASS: Approve photo is admin-only, photo {photo_id} approved")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/gallery/photos/{photo_id}", headers=admin_headers)
    
    def test_reject_photo_admin_only(self, socio_token, admin_token):
        """PATCH /api/gallery/photos/{id}/reject should be admin only and remove photo"""
        socio_headers = {"Authorization": f"Bearer {socio_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Upload a photo as socio
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        files = {'file': ('test_reject.png', io.BytesIO(image_content), 'image/png')}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/gallery/photos/upload",
            params={"album_id": "album-aeroportos", "caption": "TEST_Reject"},
            headers=socio_headers,
            files=files
        )
        assert upload_response.status_code == 200
        photo_id = upload_response.json()['id']
        
        # Socio should not be able to reject
        socio_reject = requests.patch(f"{BASE_URL}/api/gallery/photos/{photo_id}/reject", headers=socio_headers)
        assert socio_reject.status_code == 403, f"Expected 403 for socio reject, got {socio_reject.status_code}"
        
        # Admin should be able to reject
        admin_reject = requests.patch(f"{BASE_URL}/api/gallery/photos/{photo_id}/reject", headers=admin_headers)
        assert admin_reject.status_code == 200, f"Expected 200 for admin reject, got {admin_reject.status_code}"
        
        # Photo should be deleted after rejection
        get_response = requests.get(f"{BASE_URL}/api/gallery/photos", params={"album_id": "album-aeroportos"}, headers=admin_headers)
        photos = get_response.json()
        photo_ids = [p['id'] for p in photos]
        assert photo_id not in photo_ids, "Rejected photo should be deleted"
        
        print(f"PASS: Reject photo is admin-only, photo {photo_id} removed")


class TestPhotoDelete:
    """Test photo deletion permissions"""
    
    def test_delete_photo_admin_can_delete_any(self, admin_token):
        """DELETE /api/gallery/photos/{id} works for admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Upload a test photo
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        files = {'file': ('test_delete.png', io.BytesIO(image_content), 'image/png')}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/gallery/photos/upload",
            params={"album_id": "album-aeroportos", "caption": "TEST_Delete"},
            headers=headers,
            files=files
        )
        assert upload_response.status_code == 200
        photo_id = upload_response.json()['id']
        
        # Admin should be able to delete
        delete_response = requests.delete(f"{BASE_URL}/api/gallery/photos/{photo_id}", headers=headers)
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        
        print(f"PASS: Admin can delete photo {photo_id}")
    
    def test_delete_photo_owner_can_delete_own(self, socio_token, admin_token):
        """DELETE /api/gallery/photos/{id} works for owner"""
        socio_headers = {"Authorization": f"Bearer {socio_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Upload a test photo as socio
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        files = {'file': ('test_owner_delete.png', io.BytesIO(image_content), 'image/png')}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/gallery/photos/upload",
            params={"album_id": "album-aeroportos", "caption": "TEST_Owner_Delete"},
            headers=socio_headers,
            files=files
        )
        assert upload_response.status_code == 200
        photo_id = upload_response.json()['id']
        
        # Owner (socio) should be able to delete their own photo
        delete_response = requests.delete(f"{BASE_URL}/api/gallery/photos/{photo_id}", headers=socio_headers)
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        
        print(f"PASS: Owner can delete their own photo {photo_id}")


class TestGalleryIntegration:
    """Integration tests for full gallery workflow"""
    
    def test_full_workflow_admin(self, admin_token):
        """Test full admin workflow: create album -> upload photo -> delete"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 1. Create album
        album_data = {"title": "TEST_Integration_Album", "description": "Integration test", "visibility": "public"}
        create_album = requests.post(f"{BASE_URL}/api/gallery/albums", json=album_data, headers=headers)
        assert create_album.status_code == 200
        album_id = create_album.json()['id']
        print(f"Step 1: Created album {album_id}")
        
        # 2. Upload photo
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        files = {'file': ('test_integration.png', io.BytesIO(image_content), 'image/png')}
        upload = requests.post(
            f"{BASE_URL}/api/gallery/photos/upload",
            params={"album_id": album_id, "caption": "Integration test photo"},
            headers=headers,
            files=files
        )
        assert upload.status_code == 200
        photo = upload.json()
        assert photo['status'] == 'approved', "Admin upload should be auto-approved"
        print(f"Step 2: Uploaded photo {photo['id']} (auto-approved)")
        
        # 3. Verify album has photo
        get_photos = requests.get(f"{BASE_URL}/api/gallery/photos", params={"album_id": album_id}, headers=headers)
        assert get_photos.status_code == 200
        photos = get_photos.json()
        assert len(photos) == 1, f"Expected 1 photo, got {len(photos)}"
        print(f"Step 3: Verified album has 1 photo")
        
        # 4. Delete album (should delete photos too)
        delete_album = requests.delete(f"{BASE_URL}/api/gallery/albums/{album_id}", headers=headers)
        assert delete_album.status_code == 200
        print(f"Step 4: Deleted album and photos")
        
        print("PASS: Full admin workflow completed successfully")
    
    def test_full_workflow_socio_approval(self, socio_token, admin_token):
        """Test socio workflow: upload pending -> admin approves"""
        socio_headers = {"Authorization": f"Bearer {socio_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 1. Socio uploads photo (pending)
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        files = {'file': ('test_socio_workflow.png', io.BytesIO(image_content), 'image/png')}
        upload = requests.post(
            f"{BASE_URL}/api/gallery/photos/upload",
            params={"album_id": "album-aeroportos", "caption": "TEST_Socio_Workflow"},
            headers=socio_headers,
            files=files
        )
        assert upload.status_code == 200
        photo = upload.json()
        assert photo['status'] == 'pending', "Socio upload should be pending"
        photo_id = photo['id']
        print(f"Step 1: Socio uploaded pending photo {photo_id}")
        
        # 2. Admin sees pending photo
        pending = requests.get(f"{BASE_URL}/api/gallery/photos/pending", headers=admin_headers)
        assert pending.status_code == 200
        pending_photos = pending.json()
        pending_ids = [p['id'] for p in pending_photos]
        assert photo_id in pending_ids, "Photo should be in pending list"
        print(f"Step 2: Admin sees photo in pending list")
        
        # 3. Admin approves
        approve = requests.patch(f"{BASE_URL}/api/gallery/photos/{photo_id}/approve", headers=admin_headers)
        assert approve.status_code == 200
        print(f"Step 3: Admin approved photo")
        
        # 4. Photo now visible in public gallery
        public_photos = requests.get(f"{BASE_URL}/api/gallery/public/photos", params={"album_id": "album-aeroportos"})
        assert public_photos.status_code == 200
        public_ids = [p['id'] for p in public_photos.json()]
        assert photo_id in public_ids, "Approved photo should be in public gallery"
        print(f"Step 4: Photo visible in public gallery")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/gallery/photos/{photo_id}", headers=admin_headers)
        print("PASS: Full socio approval workflow completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
