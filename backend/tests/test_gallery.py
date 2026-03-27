"""
Gallery API Tests - Testing photo gallery feature with albums
Tests: GET albums, GET photos, admin CRUD operations
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


class TestGalleryPublicEndpoints:
    """Test public gallery endpoints (no auth required)"""
    
    def test_get_albums_returns_list(self):
        """GET /api/gallery/albums should return list of albums"""
        response = requests.get(f"{BASE_URL}/api/gallery/albums")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: GET /api/gallery/albums returned {len(data)} albums")
        return data
    
    def test_get_albums_has_expected_seed_data(self):
        """GET /api/gallery/albums should return 4 seeded albums"""
        response = requests.get(f"{BASE_URL}/api/gallery/albums")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 4, f"Expected at least 4 albums, got {len(data)}"
        
        # Check expected album IDs
        album_ids = [a['id'] for a in data]
        expected_ids = ['album-aeroportos', 'album-torre-controlo', 'album-cabo-verde', 'album-equipa']
        
        for expected_id in expected_ids:
            assert expected_id in album_ids, f"Missing expected album: {expected_id}"
        
        print(f"PASS: All 4 expected albums found: {expected_ids}")
    
    def test_album_structure(self):
        """Albums should have correct structure"""
        response = requests.get(f"{BASE_URL}/api/gallery/albums")
        assert response.status_code == 200
        
        data = response.json()
        if len(data) > 0:
            album = data[0]
            required_fields = ['id', 'title', 'cover_url', 'photo_count']
            for field in required_fields:
                assert field in album, f"Album missing field: {field}"
            print(f"PASS: Album structure correct with fields: {list(album.keys())}")
    
    def test_get_photos_by_album(self):
        """GET /api/gallery/photos?album_id=X should return photos for album"""
        # First get albums
        albums_response = requests.get(f"{BASE_URL}/api/gallery/albums")
        assert albums_response.status_code == 200
        albums = albums_response.json()
        
        if len(albums) > 0:
            album_id = albums[0]['id']
            response = requests.get(f"{BASE_URL}/api/gallery/photos", params={"album_id": album_id})
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            photos = response.json()
            assert isinstance(photos, list), "Response should be a list"
            print(f"PASS: GET /api/gallery/photos?album_id={album_id} returned {len(photos)} photos")
    
    def test_get_photos_aeroportos_album(self):
        """GET /api/gallery/photos?album_id=album-aeroportos should return photos"""
        response = requests.get(f"{BASE_URL}/api/gallery/photos", params={"album_id": "album-aeroportos"})
        assert response.status_code == 200
        
        photos = response.json()
        assert len(photos) >= 1, f"Expected at least 1 photo in aeroportos album, got {len(photos)}"
        
        # Check photo structure
        if len(photos) > 0:
            photo = photos[0]
            assert 'id' in photo, "Photo missing id"
            assert 'url' in photo, "Photo missing url"
            assert 'album_id' in photo, "Photo missing album_id"
            assert photo['album_id'] == 'album-aeroportos', "Photo album_id mismatch"
        
        print(f"PASS: album-aeroportos has {len(photos)} photos with correct structure")
    
    def test_get_single_album(self):
        """GET /api/gallery/albums/{album_id} should return single album"""
        response = requests.get(f"{BASE_URL}/api/gallery/albums/album-aeroportos")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        album = response.json()
        assert album['id'] == 'album-aeroportos', "Album ID mismatch"
        assert 'title' in album, "Album missing title"
        print(f"PASS: GET single album returned: {album['title']}")
    
    def test_get_nonexistent_album_returns_404(self):
        """GET /api/gallery/albums/{invalid_id} should return 404"""
        response = requests.get(f"{BASE_URL}/api/gallery/albums/nonexistent-album-xyz")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Nonexistent album returns 404")


class TestGalleryAdminEndpoints:
    """Test admin-only gallery endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        return response.json()['access_token']
    
    @pytest.fixture
    def socio_token(self):
        """Get socio auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SOCIO_EMAIL,
            "password": SOCIO_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Socio login failed: {response.text}")
        return response.json()['access_token']
    
    def test_create_album_requires_admin(self, socio_token):
        """POST /api/gallery/albums should require admin role"""
        headers = {"Authorization": f"Bearer {socio_token}"}
        response = requests.post(
            f"{BASE_URL}/api/gallery/albums",
            json={"title": "Test Album", "description": "Test"},
            headers=headers
        )
        assert response.status_code == 403, f"Expected 403 for socio, got {response.status_code}"
        print("PASS: Create album requires admin (socio gets 403)")
    
    def test_admin_can_create_album(self, admin_token):
        """Admin should be able to create album"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        album_data = {
            "title": "TEST_Album_Pytest",
            "description": "Test album created by pytest",
            "cover_url": "https://example.com/test.jpg",
            "order": 99
        }
        response = requests.post(
            f"{BASE_URL}/api/gallery/albums",
            json=album_data,
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        created = response.json()
        assert created['title'] == album_data['title'], "Title mismatch"
        assert 'id' in created, "Created album missing id"
        
        print(f"PASS: Admin created album: {created['id']}")
        
        # Cleanup - delete the test album
        delete_response = requests.delete(
            f"{BASE_URL}/api/gallery/albums/{created['id']}",
            headers=headers
        )
        assert delete_response.status_code == 200, f"Cleanup failed: {delete_response.text}"
        print("PASS: Test album cleaned up")
    
    def test_delete_album_requires_admin(self, socio_token):
        """DELETE /api/gallery/albums/{id} should require admin"""
        headers = {"Authorization": f"Bearer {socio_token}"}
        response = requests.delete(
            f"{BASE_URL}/api/gallery/albums/album-aeroportos",
            headers=headers
        )
        assert response.status_code == 403, f"Expected 403 for socio, got {response.status_code}"
        print("PASS: Delete album requires admin (socio gets 403)")
    
    def test_delete_photo_requires_admin(self, socio_token):
        """DELETE /api/gallery/photos/{id} should require admin"""
        headers = {"Authorization": f"Bearer {socio_token}"}
        response = requests.delete(
            f"{BASE_URL}/api/gallery/photos/some-photo-id",
            headers=headers
        )
        assert response.status_code == 403, f"Expected 403 for socio, got {response.status_code}"
        print("PASS: Delete photo requires admin (socio gets 403)")


class TestGalleryPhotoUpload:
    """Test photo upload functionality"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        return response.json()['access_token']
    
    def test_upload_photo_requires_admin(self):
        """POST /api/gallery/photos/upload should require admin"""
        # Without auth
        response = requests.post(
            f"{BASE_URL}/api/gallery/photos/upload",
            params={"album_id": "album-aeroportos", "caption": "Test"}
        )
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"
        print("PASS: Photo upload requires authentication")
    
    def test_upload_photo_invalid_album(self, admin_token):
        """Upload to nonexistent album should fail"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a simple test file
        files = {'file': ('test.jpg', b'fake image content', 'image/jpeg')}
        
        response = requests.post(
            f"{BASE_URL}/api/gallery/photos/upload",
            params={"album_id": "nonexistent-album", "caption": "Test"},
            headers=headers,
            files=files
        )
        assert response.status_code == 404, f"Expected 404 for invalid album, got {response.status_code}"
        print("PASS: Upload to nonexistent album returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
